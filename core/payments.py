from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Mapping

from core.utils import clamp


@dataclass(frozen=True)
class PaymentResult:
    applied_penal: float
    applied_interest: float
    applied_principal: float
    remaining_amount: float


def apply_payment_waterfall(
    amount_cad: float,
    penal_due_cad: float,
    interest_due_cad: float,
    principal_due_cad: float,
) -> PaymentResult:
    amount = max(0.0, amount_cad)
    penal = min(amount, max(0.0, penal_due_cad))
    amount -= penal

    interest = min(amount, max(0.0, interest_due_cad))
    amount -= interest

    principal = min(amount, max(0.0, principal_due_cad))
    amount -= principal

    return PaymentResult(penal, interest, principal, amount)


def recommend_payment_allocations(
    available_cad: float,
    items: Iterable[Mapping[str, float]],
    strategy: str = "risk",
    min_emergency_savings_cad: float = 0.0,
) -> List[dict]:
    budget = clamp(available_cad - max(0.0, min_emergency_savings_cad), 0.0, available_cad)
    if budget <= 0:
        return []

    candidates = [item for item in items if item.get("balance_cad", 0.0) > 0]

    if strategy == "avalanche":
        key = lambda x: (x.get("interest_rate_annual", 0.0), x.get("balance_cad", 0.0))
        reverse = True
    elif strategy == "snowball":
        key = lambda x: (x.get("balance_cad", 0.0), x.get("interest_rate_annual", 0.0))
        reverse = False
    else:
        key = lambda x: (x.get("risk_score", 0.0), x.get("interest_rate_annual", 0.0))
        reverse = True

    allocations: List[dict] = []
    for item in sorted(candidates, key=key, reverse=reverse):
        if budget <= 0:
            break
        amount = min(budget, float(item["balance_cad"]))
        budget -= amount
        allocations.append(
            {
                "target_type": item["target_type"],
                "target_id": item["target_id"],
                "amount_cad": amount,
                "strategy": strategy,
            }
        )

    return allocations
