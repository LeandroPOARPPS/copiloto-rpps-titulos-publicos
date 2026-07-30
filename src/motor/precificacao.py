from __future__ import annotations

def present_value(future_value: float, yield_rate: float, business_days: int, business_days_per_year: int = 252) -> float:
    return future_value / (1.0 + yield_rate) ** (business_days / business_days_per_year)
