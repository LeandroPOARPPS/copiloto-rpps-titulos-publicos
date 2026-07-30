from __future__ import annotations

from pathlib import Path
import pandas as pd

from .utils import (
    clean_columns,
    convert_excel_dates,
    read_table,
    require_columns,
)


REQUIRED_COLUMNS = {
    "Data",
    "Título",
    "Vencimento",
    "PU_Mercado",
    "Taxa_Mercado",
    "VNA",
    "Duration_Dias_Uteis",
    "Indexador",
    "Tem_Cupom",
}


def load_market_rates(path: str | Path) -> pd.DataFrame:
    frame = clean_columns(read_table(path, sheet_name="Planilha1"))
    require_columns(frame, REQUIRED_COLUMNS, str(path))

    frame = frame.dropna(how="all").copy()
    frame["Data"] = convert_excel_dates(frame["Data"], allow_empty=False)
    frame["Vencimento"] = convert_excel_dates(
        frame["Vencimento"], allow_empty=False
    )

    numeric_columns = [
        "PU_Mercado",
        "Taxa_Mercado",
        "VNA",
        "Duration_Dias_Uteis",
        "Volatilidade_12m",
        "Cupom_Anual",
    ]
    for column in numeric_columns:
        if column in frame.columns:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")

    frame["Título"] = frame["Título"].astype(str).str.strip()
    frame["Indexador"] = frame["Indexador"].astype(str).str.strip()
    frame["Tem_Cupom"] = (
        frame["Tem_Cupom"].astype(str).str.strip().str.lower().eq("sim")
    )

    frame["ID_Titulo"] = (
        frame["Título"]
        + "_"
        + pd.to_datetime(frame["Vencimento"]).dt.strftime("%Y%m%d")
    )

    return frame.sort_values(
        ["Título", "Vencimento"]
    ).reset_index(drop=True)
