from __future__ import annotations
from .modelos import CashFlow

def calculate_metrics(flows: list[CashFlow], yield_rate: float, first_period_denominator: float) -> tuple[float, float, float, float, float]:
    if not flows:
        raise ValueError("A lista de fluxos não pode estar vazia.")
    pu = sum(flow.present_value for flow in flows)
    duration_du = sum(flow.business_days * flow.present_value for flow in flows) / pu
    duration_years = duration_du / 252.0
    modified_duration = duration_years / (1.0 + yield_rate)
    first_du = flows[0].business_days
    t0 = first_du / first_period_denominator
    convexity_numerator = 0.0
    coupon_index = -1
    last_coupon_t = t0
    for flow in flows:
        if flow.flow_type == "J":
            coupon_index += 1
            t = t0 + coupon_index
            last_coupon_t = t
        else:
            t = last_coupon_t
        convexity_numerator += t * (t + 1.0) * flow.present_value
    convexity = convexity_numerator / (4.0 * pu * (1.0 + yield_rate / 2.0) ** 2)
    return pu, duration_du, duration_years, modified_duration, convexity
