from __future__ import annotations

from datetime import date
from pathlib import Path
import pandas as pd


def read_table(path: str | Path, *, sheet_name=0, **kwargs) -> pd.DataFrame:
    path = Path(path)

    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, **kwargs)

    return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl", **kwargs)


def clean_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result.columns = [
        str(column).replace("\n", " ").strip()
        for column in result.columns
    ]
    return result


def convert_excel_dates(
    series: pd.Series,
    *,
    allow_empty: bool = True,
) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series).dt.date

    numeric = pd.to_numeric(series, errors="coerce")
    converted = pd.to_datetime(
        numeric,
        unit="D",
        origin="1899-12-30",
        errors="coerce",
    )

    text_dates = pd.to_datetime(series, dayfirst=True, errors="coerce")
    converted = converted.fillna(text_dates)

    if not allow_empty and converted.isna().any():
        invalid = series[converted.isna()].head(5).tolist()
        raise ValueError(f"Datas inválidas encontradas: {invalid}")

    return converted.dt.date


def require_columns(frame: pd.DataFrame, required: set[str], source: str) -> None:
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(
            f"Colunas ausentes em {source}: {sorted(missing)}. "
            f"Encontradas: {list(frame.columns)}"
        )
