from __future__ import annotations
from datetime import date, timedelta
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET

EXCEL_EPOCH = date(1899, 12, 30)
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

def excel_serial_to_date(value: int | float) -> date:
    return EXCEL_EPOCH + timedelta(days=int(value))

def load_holidays_from_xlsx(path: str | Path) -> set[date]:
    path = Path(path)
    holidays: set[date] = set()
    with zipfile.ZipFile(path) as archive:
        xml = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
        for cell in xml.iter(NS + "c"):
            reference = cell.attrib.get("r", "")
            if not reference.startswith("A") or reference == "A1":
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
    if end <= start:
        return 0
    count = 0
    current = start
    while current < end:
        if is_business_day(current, holidays):
            count += 1
        current += timedelta(days=1)
    return count

def semiannual_dates(settlement: date, maturity: date, month_day_1: tuple[int, int], month_day_2: tuple[int, int], holidays: set[date]) -> list[date]:
    dates: list[date] = []
    for year in range(settlement.year, maturity.year + 1):
        for month, day in (month_day_1, month_day_2):
            nominal = date(year, month, day)
            if settlement < nominal <= maturity:
                dates.append(following_business_day(nominal, holidays))
    return sorted(set(dates))
