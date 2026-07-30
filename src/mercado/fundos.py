from __future__ import annotations

from pathlib import Path
import pandas as pd

from .utils import clean_columns, convert_excel_dates, read_table, require_columns


def normalize_cnpj(value: object) -> str:
    digits = "".join(character for character in str(value) if character.isdigit())
    return digits.zfill(14) if digits else ""


def load_fund_registry(path: str | Path) -> pd.DataFrame:
    frame = clean_columns(read_table(path, sheet_name="Planilha1"))
    require_columns(
        frame,
        {"Nome", "CNPJ", "Classe Anbima", "Classificação Anbima"},
        str(path),
    )

    frame = frame.dropna(how="all").copy()
    frame["CNPJ"] = frame["CNPJ"].map(normalize_cnpj)

    for column in frame.select_dtypes(include="object").columns:
        frame[column] = frame[column].astype(str).str.strip()

    return frame.reset_index(drop=True)


def _load_category_panel(path: str | Path, sheet_name: str) -> pd.DataFrame:
    wide = clean_columns(read_table(path, sheet_name=sheet_name))
    wide = wide.dropna(how="all").copy()

    first = wide.columns[0]
    long = wide.melt(
        id_vars=[first],
        var_name="Data",
        value_name="Valor",
    ).rename(columns={first: "Classificação Anbima"})

    long["Data"] = convert_excel_dates(long["Data"])
    long["Valor"] = pd.to_numeric(long["Valor"], errors="coerce")

    return long.dropna(subset=["Data", "Valor"]).reset_index(drop=True)


def load_category_returns(path: str | Path) -> pd.DataFrame:
    frame = _load_category_panel(
        path,
        sheet_name="Retorno Medio Mensal em 12 m",
    )
    return frame.rename(columns={"Valor": "Retorno_Medio_12m"})


def load_category_volatility(path: str | Path) -> pd.DataFrame:
    frame = _load_category_panel(
        path,
        sheet_name="Vol anualizada ",
    )
    return frame.rename(columns={"Valor": "Volatilidade_Anualizada_12m"})
