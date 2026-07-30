from __future__ import annotations
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True)
class CashFlow:
    payment_date: date
    flow_type: str
    business_days: int
    rate_percent: float
    future_value: float
    present_value: float

@dataclass(frozen=True)
class BondResult:
    bond: str
    settlement: date
    maturity: date
    yield_rate: float
    cash_flows: list[CashFlow]
    pu: float
    duration_business_days: float
    duration_years: float
    modified_duration: float
    convexity: float
