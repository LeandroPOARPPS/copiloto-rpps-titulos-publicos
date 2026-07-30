# Módulo Mercado

O pacote `src/mercado` localiza e carrega automaticamente os dados mais
recentes do projeto.

## Uso básico

```python
from pathlib import Path
from src.mercado import MarketDataService

ROOT = Path(__file__).resolve().parent
mercado = MarketDataService(ROOT)
dados = mercado.load_all()

taxas = dados["taxas_mercado"]
curva_ipca = dados["curvas_anbima"]["ipca"]
feriados = dados["feriados"]
```

A seleção dos arquivos semanais é feita pela data existente no nome do
arquivo. Portanto, ao incluir uma nova curva ou nova planilha de taxas na
pasta correspondente, o aplicativo passa a usar automaticamente o arquivo
mais recente.
