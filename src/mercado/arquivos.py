from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
import re
import unicodedata


_DATE_PATTERNS = (
    re.compile(r"(?<!\d)(\d{2})(\d{2})(\d{4})(?!\d)"),
    re.compile(r"(?<!\d)(\d{4})[-_]?(\d{2})[-_]?(\d{2})(?!\d)"),
)


def normalize_name(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch)).lower()


def extract_date_from_filename(path: str | Path) -> date | None:
    name = Path(path).stem

    match = _DATE_PATTERNS[0].search(name)
    if match:
        day, month, year = map(int, match.groups())
        return date(year, month, day)

    match = _DATE_PATTERNS[1].search(name)
    if match:
        year, month, day = map(int, match.groups())
        return date(year, month, day)

    return None


def find_latest_file(
    directory: str | Path,
    *,
    keywords: tuple[str, ...] = (),
    extensions: tuple[str, ...] = (".xlsx", ".xls", ".csv"),
) -> Path:
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {directory}")

    normalized_keywords = tuple(normalize_name(k) for k in keywords)
    candidates: list[Path] = []

    for path in directory.iterdir():
        if not path.is_file() or path.suffix.lower() not in extensions:
            continue

        normalized = normalize_name(path.name)
        if all(keyword in normalized for keyword in normalized_keywords):
            candidates.append(path)

    if not candidates:
        description = ", ".join(keywords) if keywords else "arquivos compatíveis"
        raise FileNotFoundError(
            f"Nenhum arquivo encontrado em {directory} para: {description}"
        )

    def ordering(path: Path) -> tuple[date, float]:
        embedded_date = extract_date_from_filename(path)
        fallback = datetime.fromtimestamp(path.stat().st_mtime).date()
        return embedded_date or fallback, path.stat().st_mtime

    return max(candidates, key=ordering)


@dataclass(frozen=True)
class DataFiles:
    holidays: Path
    ipca_vna: Path
    selic_vna: Path
    market_rates: Path
    anbima_curves: Path
    fund_registry: Path
    category_returns: Path
    category_volatility: Path


def locate_data_files(project_root: str | Path) -> DataFiles:
    root = Path(project_root)
    data = root / "dados"

    return DataFiles(
        holidays=find_latest_file(data / "feriados", keywords=("feriados",)),
        ipca_vna=find_latest_file(data / "vna", keywords=("vna", "ipca")),
        selic_vna=find_latest_file(data / "vna", keywords=("vna", "selic")),
        market_rates=find_latest_file(
            data / "taxas", keywords=("taxas", "mercado", "titulos")
        ),
        anbima_curves=find_latest_file(
            data / "curvas", keywords=("curvas", "anbima")
        ),
        fund_registry=find_latest_file(
            data / "fundos", keywords=("base", "fundos")
        ),
        category_returns=find_latest_file(
            data / "fundos", keywords=("retorno", "medio")
        ),
        category_volatility=find_latest_file(
            data / "fundos", keywords=("volatilidade",)
        ),
    )
