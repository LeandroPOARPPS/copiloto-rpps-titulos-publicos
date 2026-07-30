from __future__ import annotations

from datetime import date
from pathlib import Path
import pandas as pd

from .utils import clean_columns, convert_excel_dates, read_table, require_columns


def load_ipca_vna(path: str | Path) -> dict[str, pd.DataFrame]:
    vna = clean_columns(read_table(path, sheet_name="VNAIPCA"))
    prorata = clean_columns(read_table(path, sheet_name="Prorata"))
    projections = clean_columns(read_table(path, sheet_name="Projeções"))

    require_columns(vna, {"Data_Mes", "VNA_IPCA_Dia_15"}, str(path))
    require_columns(
        prorata,
        {"Data", "IPCA", "Dias_Uteis_IPCA_Mes", "Pro_Rata_Diario_IPCA"},
        str(path),
    )

    vna = vna.dropna(how="all").copy()
    vna["Data_Mes"] = convert_excel_dates(vna["Data_Mes"])
    vna["VNA_IPCA_Dia_15"] = pd.to_numeric(
        vna["VNA_IPCA_Dia_15"], errors="coerce"
    )

    prorata = prorata.dropna(how="all").copy()
    prorata["Data"] = convert_excel_dates(prorata["Data"])
    for column in ("IPCA", "Dias_Uteis_IPCA_Mes", "Pro_Rata_Diario_IPCA"):
        prorata[column] = pd.to_numeric(prorata[column], errors="coerce")

    projections = projections.dropna(how="all").copy()
    if "Data" in projections:
        projections["Data"] = convert_excel_dates(projections["Data"])
    for column in (
        "Ano",
        "Mediana_IPCA_Focus",
        "IPCA_Mensal_Focus",
        "Projecao_IPCA_RPPS",
        "Projecao_IPCA_Mensal_RPPS",
    ):
        if column in projections:
            projections[column] = pd.to_numeric(
                projections[column], errors="coerce"
            )

    return {
        "vna": vna.reset_index(drop=True),
        "prorata": prorata.reset_index(drop=True),
        "projecoes": projections.reset_index(drop=True),
    }


def latest_ipca_vna(path: str | Path, reference_date: date | None = None) -> float:
    frame = load_ipca_vna(path)["vna"].dropna(
        subset=["Data_Mes", "VNA_IPCA_Dia_15"]
    )

    if reference_date is not None:
        frame = frame[frame["Data_Mes"] <= reference_date]

    if frame.empty:
        raise ValueError("Nenhum VNA IPCA disponível para a data solicitada.")

    latest = frame.sort_values("Data_Mes").iloc[-1]
    return float(latest["VNA_IPCA_Dia_15"])


def load_selic_vna(path: str | Path) -> dict[str, pd.DataFrame]:
    vna = clean_columns(read_table(path, sheet_name="VNASelic"))
    require_columns(
        vna,
        {"Data", "Selic Diária", "VNA Selic", "Taxa_Selic_Efetiva_aa"},
        str(path),
    )

    vna = vna.dropna(how="all").copy()
    vna["Data"] = convert_excel_dates(vna["Data"])
    for column in ("Selic Diária", "VNA Selic", "Taxa_Selic_Efetiva_aa"):
        vna[column] = pd.to_numeric(vna[column], errors="coerce")

    workbook = pd.ExcelFile(path, engine="openpyxl")
    calendar_sheet = next(
        (
            name
            for name in workbook.sheet_names
            if "copom" in name.lower() or "calendario" in name.lower()
        ),
        None,
    )

    calendar = pd.DataFrame()
    if calendar_sheet:
        calendar = clean_columns(
            pd.read_excel(path, sheet_name=calendar_sheet, engine="openpyxl")
        ).dropna(how="all")

        if not calendar.empty:
            first_column = calendar.columns[0]
            calendar[first_column] = convert_excel_dates(calendar[first_column])

    return {
        "vna": vna.reset_index(drop=True),
        "copom": calendar.reset_index(drop=True),
    }


def latest_selic_vna(path: str | Path, reference_date: date | None = None) -> float:
    frame = load_selic_vna(path)["vna"].dropna(
        subset=["Data", "VNA Selic"]
    )

    if reference_date is not None:
        frame = frame[frame["Data"] <= reference_date]

    if frame.empty:
        raise ValueError("Nenhum VNA Selic disponível para a data solicitada.")

    latest = frame.sort_values("Data").iloc[-1]
    return float(latest["VNA Selic"])
