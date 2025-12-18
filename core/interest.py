from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from core.utils import days_between, next_due_date


@dataclass(frozen=True)
class DebtAccrual:
    interest_cad: float
    penal_cad: float
    days_accrued: int
    overdue_days: int


@dataclass(frozen=True)
class CreditCardAccrual:
    interest_cad: float
    late_fee_cad: float
    days_accrued: int
    overdue_days: int


def _daily_rate(annual_rate: float) -> float:
    return max(0.0, annual_rate) / 365.0


def compute_debt_overdue_days(
    as_of: date,
    installment_due_day: Optional[int],
    last_payment_date: Optional[date],
    loan_start_date: date,
) -> int:
    if installment_due_day is None:
        return 0
    anchor = last_payment_date or loan_start_date
    due_date = next_due_date(anchor, installment_due_day)
    return max(0, days_between(due_date, as_of))


def compute_debt_accrual(
    principal_outstanding_cad: float,
    interest_rate_annual: float,
    penal_rate_annual: float,
    last_event_date: date,
    as_of: date,
    overdue_days: int,
) -> DebtAccrual:
    days = days_between(last_event_date, as_of)
    if days == 0 or principal_outstanding_cad <= 0:
        return DebtAccrual(0.0, 0.0, 0, overdue_days)

    interest = principal_outstanding_cad * _daily_rate(interest_rate_annual) * days
    penal_days = max(0, overdue_days)
    penal = principal_outstanding_cad * _daily_rate(penal_rate_annual) * penal_days
    return DebtAccrual(interest, penal, days, overdue_days)


def compute_credit_card_overdue_days(as_of: date, due_date: date) -> int:
    return max(0, days_between(due_date, as_of))


def compute_credit_card_accrual(
    statement_balance_cad: float,
    interest_rate_annual: float,
    last_event_date: date,
    as_of: date,
    due_date: date,
    flat_late_fee_cad: float,
) -> CreditCardAccrual:
    days = days_between(last_event_date, as_of)
    if days == 0 or statement_balance_cad <= 0:
        return CreditCardAccrual(0.0, 0.0, 0, compute_credit_card_overdue_days(as_of, due_date))

    interest = statement_balance_cad * _daily_rate(interest_rate_annual) * days
    overdue_days = compute_credit_card_overdue_days(as_of, due_date)
    late_fee = flat_late_fee_cad if overdue_days > 0 else 0.0
    return CreditCardAccrual(interest, late_fee, days, overdue_days)
