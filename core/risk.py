from __future__ import annotations

from dataclasses import dataclass

from core.utils import clamp


@dataclass(frozen=True)
class RiskScore:
    score: float
    reason: str


def _interest_factor(interest_rate_annual: float, max_rate: float = 0.4, max_points: float = 40.0) -> float:
    rate = clamp(interest_rate_annual, 0.0, max_rate)
    return (rate / max_rate) * max_points


def _overdue_factor(overdue_days: int, cap_days: int = 60, max_points: float = 25.0) -> float:
    days = clamp(float(overdue_days), 0.0, float(cap_days))
    return (days / cap_days) * max_points


def _utilization_factor(utilization: float, max_points: float = 30.0) -> float:
    util = clamp(utilization, 0.0, 1.0)
    return util * max_points


def _currency_factor(original_currency: str, max_points: float = 5.0) -> float:
    return max_points if original_currency.upper() == "INR" else 0.0


def compute_debt_risk(
    interest_rate_annual: float,
    overdue_days: int,
    has_penal: bool,
    original_currency: str,
) -> RiskScore:
    score = 0.0
    score += _interest_factor(interest_rate_annual)
    score += _overdue_factor(overdue_days)
    score += 15.0 if has_penal else 0.0
    score += _currency_factor(original_currency)
    score = clamp(score, 0.0, 100.0)

    reason = "interest+overdue"
    if has_penal:
        reason += ", penal"
    if original_currency.upper() == "INR":
        reason += ", currency"

    return RiskScore(score, reason)


def compute_credit_card_risk(
    interest_rate_annual: float,
    overdue_days: int,
    utilization: float,
    has_late_fee: bool,
) -> RiskScore:
    score = 0.0
    score += _interest_factor(interest_rate_annual, max_rate=0.35, max_points=35.0)
    score += _overdue_factor(overdue_days, cap_days=45, max_points=20.0)
    score += _utilization_factor(utilization, max_points=30.0)
    score += 15.0 if has_late_fee else 0.0
    score = clamp(score, 0.0, 100.0)

    reason = "interest+utilization"
    if overdue_days > 0:
        reason += ", overdue"
    if has_late_fee:
        reason += ", late_fee"

    return RiskScore(score, reason)
