from __future__ import annotations

from datetime import date

from .calendario import (
    business_days_between,
    following_business_day,
    semiannual_dates,
)
from .metricas import calculate_metrics
from .modelos import BondResult, CashFlow
from .precificacao import present_value


def _coupon_month_days(maturity: date) -> tuple[tuple[int, int], tuple[int, int]]:
    if maturity.month == 8:
        return (2, 15), (8, 15)
    if maturity.month == 5:
        return (5, 15), (11, 15)
    raise ValueError(
        "Vencimento de NTN-B não reconhecido. "
        "São esperados vencimentos em 15/05 ou 15/08."
    )


def _average_coupon_interval_business_days(
    coupon_dates: list[date],
    holidays: set[date],
) -> float:
    intervals = [
        business_days_between(start, end, holidays)
        for start, end in zip(coupon_dates[:-1], coupon_dates[1:])
    ]
    if not intervals:
        raise ValueError(
            "São necessários pelo menos dois cupons para calcular "
            "automaticamente o divisor da convexidade."
        )
    return sum(intervals) / len(intervals)


def price_ntnb(
    *,
    holidays: set[date],
    settlement: date,
    maturity: date,
    yield_rate: float,
    vna: float,
    coupon_value: float,
    first_period_denominator: float | None = None,
    bond_name: str | None = None,
) -> BondResult:
    month_day_1, month_day_2 = _coupon_month_days(maturity)

    coupon_dates = semiannual_dates(
        settlement=settlement,
        maturity=maturity,
        month_day_1=month_day_1,
        month_day_2=month_day_2,
        holidays=holidays,
    )

    if first_period_denominator is None:
        first_period_denominator = _average_coupon_interval_business_days(
            coupon_dates, holidays
        )

    flows: list[CashFlow] = []

    for payment_date in coupon_dates:
        du = business_days_between(settlement, payment_date, holidays)
        pv = present_value(coupon_value, yield_rate, du)
        flows.append(
            CashFlow(
                payment_date=payment_date,
                flow_type="J",
                business_days=du,
                rate_percent=2.956,
                future_value=coupon_value,
                present_value=pv,
            )
        )

    maturity_payment = following_business_day(maturity, holidays)
    du_maturity = business_days_between(
        settlement, maturity_payment, holidays
    )
    pv_principal = present_value(vna, yield_rate, du_maturity)

    flows.append(
        CashFlow(
            payment_date=maturity_payment,
            flow_type="V",
            business_days=du_maturity,
            rate_percent=100.0,
            future_value=vna,
            present_value=pv_principal,
        )
    )

    (
        pu,
        duration_du,
        duration_years,
        modified_duration,
        convexity,
    ) = calculate_metrics(
        flows=flows,
        yield_rate=yield_rate,
        first_period_denominator=first_period_denominator,
    )

    return BondResult(
        bond=bond_name or f"NTN-B {maturity:%d/%m/%Y}",
        settlement=settlement,
        maturity=maturity,
        yield_rate=yield_rate,
        cash_flows=flows,
        pu=pu,
        duration_business_days=duration_du,
        duration_years=duration_years,
        modified_duration=modified_duration,
        convexity=convexity,
    )
