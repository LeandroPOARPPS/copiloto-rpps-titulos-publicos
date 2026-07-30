from datetime import date
from pathlib import Path

from src.mercado import (
    extract_date_from_filename,
    find_latest_file,
    interpolate_curve,
)


def test_extract_date_from_filename():
    assert extract_date_from_filename(
        "Taxas de Mercado Titulos Publicos_24072026.xlsx"
    ) == date(2026, 7, 24)


def test_find_latest_file(tmp_path: Path):
    older = tmp_path / "Taxas_10072026.xlsx"
    newer = tmp_path / "Taxas_24072026.xlsx"
    older.write_text("x", encoding="utf-8")
    newer.write_text("x", encoding="utf-8")

    found = find_latest_file(tmp_path, keywords=("taxas",))
    assert found.name == newer.name


def test_interpolate_curve():
    import pandas as pd

    curve = pd.DataFrame(
        {
            "Vertices_Dias_Uteis": [126, 252],
            "Taxa_IPCA": [8.0, 9.0],
        }
    )
    assert interpolate_curve(curve, 189) == 8.5
