from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, Iterable, List, Optional, Tuple

from core.payments import apply_payment_waterfall, recommend_payment_allocations
from core.risk import compute_credit_card_risk, compute_debt_risk
from core.utils import clamp
from models.types import CreditCard, Debt


@dataclass
class SimulationRow:
    as_of: date
    total_debt_cad: float
    total_interest_paid_cad: float


@dataclass
class SimulationResult:
    strategy: str
    debt_free_date: Optional[date]
    total_interest_paid_cad: float
    months: int
    timeline: List[SimulationRow]


@dataclass
class _AccountState:
    target_type: str
    target_id: int
    balance_cad: float
    interest_rate_annual: float
    penal_rate_annual: float
    currency: str
    credit_limit_cad: float
    due_day: Optional[int]
    accrued_interest_cad: float = 0.0
    accrued_penal_cad: float = 0.0


def _first_of_month(value: date) -> date:
    return value.replace(day=1)


def _add_month(value: date) -> date:
    if value.month == 12:
        return date(value.year + 1, 1, 1)
    return date(value.year, value.month + 1, 1)


def _days_between(start: date, end: date) -> int:
    if end <= start:
        return 0
    return (end - start).days


def _daily_rate(annual_rate: float) -> float:
    return max(0.0, annual_rate) / 365.0


def _period_due_date(period_start: date, due_day: Optional[int]) -> Optional[date]:
    if due_day is None:
        return None
    day = int(clamp(float(due_day), 1.0, 28.0))
    return period_start.replace(day=day)


def _accrue_month(state: _AccountState, period_start: date, period_end: date) -> Tuple[int, int]:
    days = _days_between(period_start, period_end)
    if days <= 0 or state.balance_cad <= 0:
        return 0, 0

    interest = state.balance_cad * _daily_rate(state.interest_rate_annual) * days
    state.accrued_interest_cad += interest

    overdue_days = 0
    due_date = _period_due_date(period_start, state.due_day)
    if due_date and period_end > due_date:
        overdue_days = _days_between(due_date, period_end)

    if overdue_days > 0:
        if state.target_type == "loan":
            penal = state.balance_cad * _daily_rate(state.penal_rate_annual) * overdue_days
            state.accrued_penal_cad += penal
        else:
            state.accrued_penal_cad += state.penal_rate_annual

    return days, overdue_days


def _total_balance(states: Iterable[_AccountState]) -> float:
    return sum(s.balance_cad + s.accrued_interest_cad + s.accrued_penal_cad for s in states)


def simulate_payoff(
    debts: List[Debt],
    cards: List[CreditCard],
    start_date: date,
    monthly_payment_cad: float,
    strategy: str,
    max_months: int = 600,
) -> SimulationResult:
    states: List[_AccountState] = []
    for debt in debts:
        states.append(
            _AccountState(
                target_type="loan",
                target_id=debt.id,
                balance_cad=debt.principal_outstanding_cad,
                interest_rate_annual=debt.interest_rate_annual,
                penal_rate_annual=debt.penal_rate_annual,
                currency=debt.original_currency,
                credit_limit_cad=0.0,
                due_day=debt.installment_due_day,
            )
        )
    for card in cards:
        states.append(
            _AccountState(
                target_type="credit_card",
                target_id=card.id,
                balance_cad=card.statement_balance_cad,
                interest_rate_annual=card.interest_rate_annual,
                penal_rate_annual=card.flat_late_fee_cad,
                currency="CAD",
                credit_limit_cad=card.credit_limit_cad,
                due_day=card.due_date.day,
            )
        )

    timeline: List[SimulationRow] = []
    total_interest_paid = 0.0
    period_start = _first_of_month(start_date)

    for month_index in range(max_months):
        period_end = _add_month(period_start)
        overdue_by_account: Dict[int, int] = {}

        for state in states:
            _, overdue_days = _accrue_month(state, period_start, period_end)
            overdue_by_account[state.target_id] = overdue_days

        if _total_balance(states) <= 0:
            debt_free_date = period_start
            return SimulationResult(
                strategy=strategy,
                debt_free_date=debt_free_date,
                total_interest_paid_cad=total_interest_paid,
                months=month_index,
                timeline=timeline,
            )

        payment_budget = max(0.0, monthly_payment_cad)
        if payment_budget > 0:
            items = []
            for state in states:
                if state.balance_cad <= 0 and state.accrued_interest_cad <= 0 and state.accrued_penal_cad <= 0:
                    continue
                if state.target_type == "loan":
                    risk = compute_debt_risk(
                        interest_rate_annual=state.interest_rate_annual,
                        overdue_days=overdue_by_account.get(state.target_id, 0),
                        has_penal=state.accrued_penal_cad > 0,
                        original_currency=state.currency,
                    )
                    items.append(
                        {
                            "target_type": state.target_type,
                            "target_id": state.target_id,
                            "balance_cad": state.balance_cad,
                            "interest_rate_annual": state.interest_rate_annual,
                            "risk_score": risk.score,
                        }
                    )
                else:
                    util = 0.0
                    if state.credit_limit_cad > 0:
                        util = state.balance_cad / state.credit_limit_cad
                    risk = compute_credit_card_risk(
                        interest_rate_annual=state.interest_rate_annual,
                        overdue_days=overdue_by_account.get(state.target_id, 0),
                        utilization=util,
                        has_late_fee=state.accrued_penal_cad > 0,
                    )
                    items.append(
                        {
                            "target_type": state.target_type,
                            "target_id": state.target_id,
                            "balance_cad": state.balance_cad,
                            "interest_rate_annual": state.interest_rate_annual,
                            "risk_score": risk.score,
                        }
                    )

            allocations = recommend_payment_allocations(
                available_cad=payment_budget,
                items=items,
                strategy=strategy,
            )

            for allocation in allocations:
                state = next(
                    s
                    for s in states
                    if s.target_type == allocation["target_type"] and s.target_id == allocation["target_id"]
                )
                result = apply_payment_waterfall(
                    amount_cad=allocation["amount_cad"],
                    penal_due_cad=state.accrued_penal_cad,
                    interest_due_cad=state.accrued_interest_cad,
                    principal_due_cad=state.balance_cad,
                )
                total_interest_paid += result.applied_penal + result.applied_interest
                state.accrued_penal_cad = max(0.0, state.accrued_penal_cad - result.applied_penal)
                state.accrued_interest_cad = max(0.0, state.accrued_interest_cad - result.applied_interest)
                state.balance_cad = max(0.0, state.balance_cad - result.applied_principal)

        total_debt = _total_balance(states)
        timeline.append(
            SimulationRow(
                as_of=period_end - timedelta(days=1),
                total_debt_cad=total_debt,
                total_interest_paid_cad=total_interest_paid,
            )
        )

        period_start = period_end

    return SimulationResult(
        strategy=strategy,
        debt_free_date=None,
        total_interest_paid_cad=total_interest_paid,
        months=max_months,
        timeline=timeline,
    )
