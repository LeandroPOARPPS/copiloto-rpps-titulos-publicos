from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import json
import sys
import traceback

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.mercado import (  # noqa: E402
    locate_data_files,
    load_holidays,
    load_market_rates,
    load_anbima_curves,
    load_ipca_vna,
    load_selic_vna,
    latest_ipca_vna,
    latest_selic_vna,
    load_fund_registry,
    load_category_returns,
    load_category_volatility,
)


def format_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def safe_execute(name: str, function):
    try:
        value = function()
        return {
            "status": "OK",
            "value": value,
            "error": None,
        }
    except Exception as exc:
        return {
            "status": "ERRO",
            "value": None,
            "error": {
                "tipo": type(exc).__name__,
                "mensagem": str(exc),
                "rastreamento": traceback.format_exc(),
            },
        }


def dataframe_summary(frame):
    summary = {
        "linhas": int(len(frame)),
        "colunas": [str(column) for column in frame.columns],
    }

    if len(frame) > 0:
        summary["primeira_linha"] = {
            str(key): str(value)
            for key, value in frame.iloc[0].to_dict().items()
        }
        summary["ultima_linha"] = {
            str(key): str(value)
            for key, value in frame.iloc[-1].to_dict().items()
        }

    return summary


def main() -> int:
    print("=" * 72)
    print("DIAGNÓSTICO DO MÓDULO MERCADO — COPILOTO RPPS")
    print("=" * 72)
    print(f"Raiz do projeto: {PROJECT_ROOT}")
    print(f"Data/hora: {datetime.now():%d/%m/%Y %H:%M:%S}")
    print()

    report = {
        "projeto": str(PROJECT_ROOT),
        "data_hora": datetime.now().isoformat(),
        "etapas": {},
    }

    files_result = safe_execute(
        "Localização dos arquivos",
        lambda: locate_data_files(PROJECT_ROOT),
    )
    report["etapas"]["arquivos"] = {
        "status": files_result["status"],
        "erro": files_result["error"],
    }

    if files_result["status"] != "OK":
        print("[ERRO] Não foi possível localizar os arquivos.")
        print(files_result["error"]["mensagem"])
        save_report(report)
        return 1

    files = files_result["value"]
    report["arquivos_selecionados"] = {
        field: format_path(getattr(files, field))
        for field in files.__dataclass_fields__
    }

    print("ARQUIVOS SELECIONADOS")
    for field, path in report["arquivos_selecionados"].items():
        print(f"  {field:24s}: {path}")
    print()

    checks = [
        (
            "feriados",
            lambda: load_holidays(files.holidays),
            lambda value: {
                "quantidade": len(value),
                "primeiro": min(value).isoformat() if value else None,
                "ultimo": max(value).isoformat() if value else None,
            },
        ),
        (
            "taxas_mercado",
            lambda: load_market_rates(files.market_rates),
            dataframe_summary,
        ),
        (
            "curvas_anbima",
            lambda: load_anbima_curves(files.anbima_curves),
            lambda value: {
                key: dataframe_summary(frame)
                for key, frame in value.items()
            },
        ),
        (
            "vna_ipca",
            lambda: load_ipca_vna(files.ipca_vna),
            lambda value: {
                **{
                    key: dataframe_summary(frame)
                    for key, frame in value.items()
                },
                "ultimo_vna": latest_ipca_vna(files.ipca_vna),
            },
        ),
        (
            "vna_selic",
            lambda: load_selic_vna(files.selic_vna),
            lambda value: {
                **{
                    key: dataframe_summary(frame)
                    for key, frame in value.items()
                },
                "ultimo_vna": latest_selic_vna(files.selic_vna),
            },
        ),
        (
            "fundos",
            lambda: load_fund_registry(files.fund_registry),
            dataframe_summary,
        ),
        (
            "retornos_categorias",
            lambda: load_category_returns(files.category_returns),
            dataframe_summary,
        ),
        (
            "volatilidades_categorias",
            lambda: load_category_volatility(files.category_volatility),
            dataframe_summary,
        ),
    ]

    errors = 0

    for name, loader, summarizer in checks:
        print(f"TESTANDO: {name}")
        result = safe_execute(name, loader)

        if result["status"] == "OK":
            summary = summarizer(result["value"])
            report["etapas"][name] = {
                "status": "OK",
                "resumo": summary,
                "erro": None,
            }
            print("  [OK]")

            if name == "feriados":
                print(f"  Quantidade: {summary['quantidade']}")
                print(f"  Intervalo: {summary['primeiro']} até {summary['ultimo']}")

            elif name == "taxas_mercado":
                print(f"  Títulos encontrados: {summary['linhas']}")
                print(f"  Colunas: {', '.join(summary['colunas'])}")

            elif name == "curvas_anbima":
                for curve_name, curve_summary in summary.items():
                    print(
                        f"  {curve_name}: "
                        f"{curve_summary['linhas']} linhas"
                    )

            elif name in ("vna_ipca", "vna_selic"):
                print(f"  Último VNA: {summary['ultimo_vna']}")

            else:
                print(f"  Linhas: {summary['linhas']}")
                print(f"  Colunas: {len(summary['colunas'])}")

        else:
            errors += 1
            report["etapas"][name] = {
                "status": "ERRO",
                "resumo": None,
                "erro": result["error"],
            }
            print(f"  [ERRO] {result['error']['tipo']}")
            print(f"  {result['error']['mensagem']}")

        print()

    save_report(report)

    print("=" * 72)
    if errors == 0:
        print("RESULTADO: TODOS OS COMPONENTES FORAM CARREGADOS COM SUCESSO.")
        print("O módulo Mercado está pronto para alimentar a Etapa 3.")
    else:
        print(f"RESULTADO: {errors} COMPONENTE(S) APRESENTARAM ERRO.")
        print("Envie o arquivo diagnostico_mercado.json para ajustarmos o código.")
    print("=" * 72)
    print()
    input("Pressione ENTER para fechar...")

    return 0 if errors == 0 else 1


def save_report(report: dict) -> None:
    output = PROJECT_ROOT / "diagnostico_mercado.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"Relatório salvo em: {output}")
    print()


if __name__ == "__main__":
    raise SystemExit(main())
