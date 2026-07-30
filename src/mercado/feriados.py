from __future__ import annotations

from datetime import date
from pathlib import Path

from .utils import clean_columns, convert_excel_dates, read_table


def load_holidays(path: str | Path) -> set[date]:
    frame = clean_columns(read_table(path, sheet_name=0))

    if frame.empty:
        return set()

    dates = convert_excel_dates(frame.iloc[:, 0]).dropna()
    return set(dates.tolist())
