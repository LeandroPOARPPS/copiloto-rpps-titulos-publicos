
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import math
import zipfile
import xml.etree.ElementTree as ET

EXCEL_EPOCH = date(1899, 12, 30)
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


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


def excel_serial_to_date(value: int | float) -> date:
    return EXCEL_EPOCH + timedelta(days=int(value))


def load_holidays_from_xlsx(path: str | Path) -> set[date]:
    """Lê a primeira coluna da primeira planilha sem depender do Excel."""
    path = Path(path)
    holidays: set[date] = set()
    with zipfile.ZipFile(path) as archive:
        xml = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        for cell in xml.iter(NS + "c"):
            ref = cell.attrib.get("r", "")
            if not ref.startswith("A") or ref == "A1":
                continue
            value = cell.find(NS + "v")
            if value is not None and value.text:
                holidays.add(excel_serial_to_date(float(value.text)))
    return holidays


def is_business_day(day: date, holidays: set[date]) -> bool:
    return day.weekday() < 5 and day not in holidays


def following_business_day(day: date, holidays: set[date]) -> date:
    while not is_business_day(day, holidays):
        day += timedelta(days=1)
    return day


def business_days_between(start: date, end: date, holidays: set[date]) -> int:
    """
    Replica DIATRABALHOTOTAL.INTL usado na planilha:
    dias úteis depois da liquidação e antes da data do fluxo.
    Equivalentemente: conta [start, end), sendo start um dia útil.
    """
    if end <= start:
        return 0
    count = 0
    current = start
    while current < end:
        if is_business_day(current, holidays):
            count += 1
        current += timedelta(days=1)
    return count


def semiannual_dates(
    settlement: date,
    maturity: date,
    month_day_1: tuple[int, int],
    month_day_2: tuple[int, int],
    holidays: set[date],
) -> list[date]:
    """Gera datas nominais semestrais e aplica convenção 'following'."""
    dates: list[date] = []
    for year in range(settlement.year, maturity.year + 1):
        for month, day in (month_day_1, month_day_2):
            nominal = date(year, month, day)
            if settlement < nominal <= maturity:
                dates.append(following_business_day(nominal, holidays))
    return sorted(set(dates))


def metrics(
    flows: list[CashFlow],
    yield_rate: float,
    first_period_denominator: float,
) -> tuple[float, float, float, float, float]:
    pu = sum(flow.present_value for flow in flows)
    duration_du = sum(
        flow.business_days * flow.present_value for flow in flows
    ) / pu
    duration_years = duration_du / 252.0

    # É a fórmula efetivamente usada na planilha:
    modified_duration = duration_years / (1.0 + yield_rate)

    # Convexidade semestral reproduzindo a estrutura da planilha:
    # primeiro período fracionário = DU_1 / denominador;
    # os demais períodos avançam exatamente 1 semestre.
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

    convexity = (
        convexity_numerator
        / (4.0 * pu * (1.0 + yield_rate / 2.0) ** 2)
    )
    return pu, duration_du, duration_years, modified_duration, convexity


def price_ntnb_2040(
    holidays: set[date],
    settlement: date = date(2025, 10, 10),
    maturity: date = date(2040, 8, 15),
    yield_rate: float = 0.07354,
    vna: float = 4554.791158956359,
    coupon_value: float = 134.653336,
) -> BondResult:
    coupon_dates = semiannual_dates(
        settlement, maturity, (2, 15), (8, 15), holidays
    )
    flows: list[CashFlow] = []

    for payment_date in coupon_dates:
        du = business_days_between(settlement, payment_date, holidays)
        pv = coupon_value / (1.0 + yield_rate) ** (du / 252.0)
        flows.append(
            CashFlow(payment_date, "J", du, 2.956, coupon_value, pv)
        )

    maturity_payment = following_business_day(maturity, holidays)
    du_maturity = business_days_between(
        settlement, maturity_payment, holidays
    )
    pv_principal = vna / (1.0 + yield_rate) ** (du_maturity / 252.0)
    flows.append(
        CashFlow(maturity_payment, "V", du_maturity, 100.0, vna, pv_principal)
    )

    pu, duration_du, duration_years, mod_duration, convexity = metrics(
        flows, yield_rate, first_period_denominator=125.21
    )
    return BondResult(
        "NTN-B 15/08/2040",
        settlement,
        maturity,
        yield_rate,
        flows,
        pu,
        duration_du,
        duration_years,
        mod_duration,
        convexity,
    )


def price_ntnf_2035(
    holidays: set[date],
    settlement: date = date(2025, 10, 10),
    maturity: date = date(2035, 1, 1),
    yield_rate: float = 0.1402,
    face_value: float = 1000.0,
    coupon_value: float = 48.80885,
) -> BondResult:
    coupon_dates = semiannual_dates(
        settlement, maturity, (1, 1), (7, 1), holidays
    )
    flows: list[CashFlow] = []

    for payment_date in coupon_dates:
        du = business_days_between(settlement, payment_date, holidays)
        pv = coupon_value / (1.0 + yield_rate) ** (du / 252.0)
        flows.append(
            CashFlow(payment_date, "J", du, 4.881, coupon_value, pv)
        )

    maturity_payment = following_business_day(maturity, holidays)
    du_maturity = business_days_between(
        settlement, maturity_payment, holidays
    )
    pv_principal = face_value / (1.0 + yield_rate) ** (du_maturity / 252.0)
    flows.append(
        CashFlow(
            maturity_payment, "V", du_maturity, 100.0, face_value, pv_principal
        )
    )

    # Para a convexidade, o denominador é a média de DU por semestre
    # implícita na própria sequência até o vencimento.
    number_of_coupon_intervals = len(coupon_dates) - 1
    t0 = 0.5  # chute inicial apenas para derivar o denominador
    denominator = du_maturity / (number_of_coupon_intervals + t0)
    # Para o batimento de PU e duration este denominador não interfere.
    pu, duration_du, duration_years, mod_duration, convexity = metrics(
        flows, yield_rate, first_period_denominator=denominator
    )
    return BondResult(
        "NTN-F 01/01/2035",
        settlement,
        maturity,
        yield_rate,
        flows,
        pu,
        duration_du,
        duration_years,
        mod_duration,
        convexity,
    )
