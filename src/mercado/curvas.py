from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

from .utils import clean_columns, convert_excel_dates, read_table, require_columns


CURVE_SHEETS = {
    "ipca": ("ETTJIPCA", "Taxa_IPCA"),
    "prefixada": ("ETTJPre", "Taxa_Prefixada"),
    "selic": ("ETTJ_LFT_Selic", "Spread_LFT"),
}


def _load_curve(path: str | Path, sheet: str, rate_column: str) -> pd.DataFrame:
    frame = clean_columns(read_table(path, sheet_name=sheet))
    require_columns(
        frame,
        {"Vertices_Dias_Uteis", rate_column},
        f"{path} / {sheet}",
    )

    frame = frame[["Vertices_Dias_Uteis", rate_column]].dropna().copy()
    frame["Vertices_Dias_Uteis"] = pd.to_numeric(
        frame["Vertices_Dias_Uteis"], errors="raise"
    ).astype(int)
    frame[rate_column] = pd.to_numeric(frame[rate_column], errors="raise")

    return frame.sort_values("Vertices_Dias_Uteis").reset_index(drop=True)


def load_anbima_curves(path: str | Path) -> dict[str, pd.DataFrame]:
    result = {
        key: _load_curve(path, sheet, rate_column)
        for key, (sheet, rate_column) in CURVE_SHEETS.items()
    }

    betas = clean_columns(read_table(path, sheet_name="Betas"))
    betas = betas.dropna(how="all").copy()

    if not betas.empty:
        betas["Data"] = convert_excel_dates(betas["Data"])
        for column in ("Beta1", "Beta2", "Beta3", "Beta4", "Lambda1", "Lambda2"):
            if column in betas:
                betas[column] = pd.to_numeric(betas[column], errors="coerce")

    result["betas"] = betas.reset_index(drop=True)
    return result


def interpolate_curve(
    curve: pd.DataFrame,
    business_days: int | float,
    *,
    rate_column: str | None = None,
) -> float:
    if curve.empty:
        raise ValueError("A curva não pode estar vazia.")

    if rate_column is None:
        candidates = [
            column
            for column in curve.columns
            if column != "Vertices_Dias_Uteis"
        ]
        if len(candidates) != 1:
            raise ValueError("Informe rate_column para uma curva ambígua.")
        rate_column = candidates[0]

    x = curve["Vertices_Dias_Uteis"].to_numpy(dtype=float)
    y = curve[rate_column].to_numpy(dtype=float)

    return float(np.interp(float(business_days), x, y))
