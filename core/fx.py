from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable, Dict, Optional

from core.utils import days_between


Fetcher = Callable[[str], float]


@dataclass
class FxRateCache:
    rates_to_cad: Dict[str, float]
    last_updated: Dict[str, date]
    source: Dict[str, str]

    def get(self, currency: str) -> Optional[float]:
        return self.rates_to_cad.get(currency.upper())

    def set(self, currency: str, rate: float, updated: date, source: str) -> None:
        key = currency.upper()
        self.rates_to_cad[key] = rate
        self.last_updated[key] = updated
        self.source[key] = source


def convert_to_cad(amount: float, currency: str, rate_to_cad: float) -> float:
    if currency.upper() == "CAD":
        return amount
    return amount * rate_to_cad


def get_rate_to_cad(
    currency: str,
    cache: FxRateCache,
    as_of: date,
    max_age_days: int = 1,
    fetcher: Optional[Fetcher] = None,
) -> float:
    key = currency.upper()
    cached = cache.get(key)
    if key == "CAD":
        return 1.0

    if cached is not None:
        age = days_between(cache.last_updated.get(key, as_of), as_of)
        if age <= max_age_days:
            return cached

    if fetcher is None:
        raise ValueError(f"FX rate for {key} is stale or missing and no fetcher provided")

    rate = fetcher(key)
    cache.set(key, rate, as_of, source="api")
    return rate
