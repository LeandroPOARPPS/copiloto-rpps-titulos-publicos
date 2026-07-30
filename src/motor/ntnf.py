from __future__ import annotations
from datetime import date
from .calendario import business_days_between, following_business_day, semiannual_dates
from .metricas import calculate_metrics
from .modelos import BondResult, CashFlow
from .precificacao import present_value

def price_ntnf(*, holidays: set[date], settlement: date, maturity: date, yield_rate: float, face_value: float, coupon_value: float, first_period_denominator: float, bond_name: str | None = None) -> BondResult:
    coupon_dates = semiannual_dates(settlement, maturity, (1, 1), (7, 1), holidays)
    flows: list[CashFlow] = []
    for payment_date in coupon_dates:
        du = business_days_between(settlement, payment_date, holidays)
        flows.append(CashFlow(payment_date, "J", du, 4.881, coupon_value, present_value(coupon_value, yield_rate, du)))
    maturity_payment = following_business_day(maturity, holidays)
    du_maturity = business_days_between(settlement, maturity_payment, holidays)
    flows.append(CashFlow(maturity_payment, "V", du_maturity, 100.0, face_value, present_value(face_value, yield_rate, du_maturity)))
    pu, duration_du, duration_years, modified_duration, convexity = calculate_metrics(flows, yield_rate, first_period_denominator)
    return BondResult(bond_name or f"NTN-F {maturity:%d/%m/%Y}", settlement, maturity, yield_rate, flows, pu, duration_du, duration_years, modified_duration, convexity)
