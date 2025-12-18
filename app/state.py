from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

import streamlit as st

from core.interest import (
    compute_credit_card_accrual,
    compute_credit_card_overdue_days,
    compute_debt_accrual,
    compute_debt_overdue_days,
)
from core.risk import compute_credit_card_risk, compute_debt_risk
from core.utils import format_date
from db.repository import Repository
from models.types import CreditCard, Debt


@dataclass(frozen=True)
class DebtSnapshot:
    debt: Debt
    interest_cad: float
    penal_cad: float
    overdue_days: int
    risk_score: float
    risk_reason: str


@dataclass(frozen=True)
class CardSnapshot:
    card: CreditCard
    interest_cad: float
    late_fee_cad: float
    overdue_days: int
    risk_score: float
    risk_reason: str


@st.cache_resource
def get_repo() -> Repository:
    root = Path(__file__).resolve().parents[1]
    db_path = root / "data" / "finance.db"
    return Repository(db_path)


def load_debt_snapshots(repo: Repository, as_of: date) -> List[DebtSnapshot]:
    debts = repo.list_debts(status="active")
    snapshots: List[DebtSnapshot] = []
    for debt in debts:
        last_event = debt.last_payment_date or debt.loan_start_date
        overdue_days = compute_debt_overdue_days(
            as_of=as_of,
            installment_due_day=debt.installment_due_day,
            last_payment_date=debt.last_payment_date,
            loan_start_date=debt.loan_start_date,
        )
        accrual = compute_debt_accrual(
            principal_outstanding_cad=debt.principal_outstanding_cad,
            interest_rate_annual=debt.interest_rate_annual,
            penal_rate_annual=debt.penal_rate_annual,
            last_event_date=last_event,
            as_of=as_of,
            overdue_days=overdue_days,
        )
        risk = compute_debt_risk(
            interest_rate_annual=debt.interest_rate_annual,
            overdue_days=overdue_days,
            has_penal=accrual.penal_cad > 0,
            original_currency=debt.original_currency,
        )
        snapshots.append(
            DebtSnapshot(
                debt=debt,
                interest_cad=accrual.interest_cad,
                penal_cad=accrual.penal_cad,
                overdue_days=overdue_days,
                risk_score=risk.score,
                risk_reason=risk.reason,
            )
        )
    return snapshots


def load_card_snapshots(repo: Repository, as_of: date) -> List[CardSnapshot]:
    cards = repo.list_credit_cards(status="active")
    snapshots: List[CardSnapshot] = []
    for card in cards:
        last_event = card.last_payment_date or card.statement_date
        accrual = compute_credit_card_accrual(
            statement_balance_cad=card.statement_balance_cad,
            interest_rate_annual=card.interest_rate_annual,
            last_event_date=last_event,
            as_of=as_of,
            due_date=card.due_date,
            flat_late_fee_cad=card.flat_late_fee_cad,
        )
        overdue_days = compute_credit_card_overdue_days(as_of, card.due_date)
        risk = compute_credit_card_risk(
            interest_rate_annual=card.interest_rate_annual,
            overdue_days=overdue_days,
            utilization=card.utilization,
            has_late_fee=accrual.late_fee_cad > 0,
        )
        snapshots.append(
            CardSnapshot(
                card=card,
                interest_cad=accrual.interest_cad,
                late_fee_cad=accrual.late_fee_cad,
                overdue_days=overdue_days,
                risk_score=risk.score,
                risk_reason=risk.reason,
            )
        )
    return snapshots


def compute_totals(debt_snapshots: List[DebtSnapshot], card_snapshots: List[CardSnapshot]) -> Dict[str, float]:
    total_debt = sum(
        d.debt.principal_outstanding_cad + d.interest_cad + d.penal_cad for d in debt_snapshots
    )
    total_card = sum(
        c.card.statement_balance_cad + c.interest_cad + c.late_fee_cad for c in card_snapshots
    )
    return {"total_debt_cad": total_debt + total_card}


def format_money(value: float) -> str:
    return f"{value:,.2f}"


def snapshot_label(as_of: date) -> str:
    return format_date(as_of)
