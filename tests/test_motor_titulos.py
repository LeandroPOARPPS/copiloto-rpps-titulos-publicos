from datetime import date
from pathlib import Path
from src.motor import load_holidays_from_xlsx, price_ntnb, price_ntnf

ROOT = Path(__file__).resolve().parents[1]
FERIADOS = ROOT / "dados" / "feriados" / "Feriados.xlsx"

def test_ntnb_2040():
    holidays = load_holidays_from_xlsx(FERIADOS)
    result = price_ntnb(holidays=holidays, settlement=date(2025,10,10), maturity=date(2040,8,15), yield_rate=0.07354, vna=4554.791158956359, coupon_value=134.653336, first_period_denominator=125.21, bond_name="NTN-B 15/08/2040")
    assert abs(result.pu - 4074.877140574073) < 1e-8
    assert abs(result.duration_business_days - 2416.8840187989144) < 1e-8
    assert abs(result.modified_duration - 8.933816717037) < 1e-8
    assert abs(result.convexity - 117.471160063138) < 1e-8

def test_ntnf_2035():
    holidays = load_holidays_from_xlsx(FERIADOS)
    result = price_ntnf(holidays=holidays, settlement=date(2025,10,10), maturity=date(2035,1,1), yield_rate=0.1402, face_value=1000.0, coupon_value=48.80885, first_period_denominator=123.5, bond_name="NTN-F 01/01/2035")
    assert abs(result.pu - 834.4481667747862) < 1e-8
    assert abs(result.duration_business_days - 1434.694091292004) < 1e-8
    assert abs(result.modified_duration - 4.993185863007) < 1e-8
