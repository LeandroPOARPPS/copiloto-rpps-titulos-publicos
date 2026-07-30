from __future__ import annotations

from pathlib import Path

from .arquivos import DataFiles, locate_data_files
from .curvas import load_anbima_curves
from .feriados import load_holidays
from .fundos import (
    load_category_returns,
    load_category_volatility,
    load_fund_registry,
)
from .taxas import load_market_rates
from .vna import load_ipca_vna, load_selic_vna


class MarketDataService:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)
        self.files: DataFiles = locate_data_files(self.project_root)

    def load_all(self) -> dict:
        return {
            "arquivos": self.files,
            "feriados": load_holidays(self.files.holidays),
            "taxas_mercado": load_market_rates(self.files.market_rates),
            "curvas_anbima": load_anbima_curves(self.files.anbima_curves),
            "vna_ipca": load_ipca_vna(self.files.ipca_vna),
            "vna_selic": load_selic_vna(self.files.selic_vna),
            "fundos": load_fund_registry(self.files.fund_registry),
            "retornos_categorias": load_category_returns(
                self.files.category_returns
            ),
            "volatilidades_categorias": load_category_volatility(
                self.files.category_volatility
            ),
        }
