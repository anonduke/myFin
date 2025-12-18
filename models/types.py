from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class Debt:
    id: int
    lender_name: str
    debt_type: str
    original_currency: str
    principal_original: float
    principal_outstanding_cad: float
    interest_rate_annual: float
    penal_rate_annual: float
    loan_start_date: date
    installment_amount: Optional[float]
    installment_due_day: Optional[int]
    last_payment_date: Optional[date]
    status: str


@dataclass(frozen=True)
class CreditCard:
    id: int
    bank_name: str
    card_name: str
    credit_limit_cad: float
    statement_balance_cad: float
    interest_rate_annual: float
    statement_date: date
    due_date: date
    last_payment_date: Optional[date]
    flat_late_fee_cad: float
    status: str

    @property
    def utilization(self) -> float:
        if self.credit_limit_cad <= 0:
            return 0.0
        return max(0.0, min(1.0, self.statement_balance_cad / self.credit_limit_cad))


@dataclass(frozen=True)
class FxRate:
    currency: str
    rate_to_cad: float
    last_updated: date
    source: str


@dataclass(frozen=True)
class SavingsAccount:
    id: int
    account_name: str
    currency: str
    balance_cad: float


@dataclass(frozen=True)
class PaymentAllocation:
    target_type: str
    target_id: int
    amount_cad: float
    strategy: str
