# 📈 Trading Algorítmico API (Case Dev Jr)

API em **FastAPI** para backtests de estratégias de trading com integração a dados do **Yahoo Finance**, execução de estratégias em **Backtrader**, métricas de performance, gestão de risco e visualização dos resultados.

---

## 🚀 Visão Geral

Este projeto demonstra:

- **API REST** para rodar e consultar backtests.
- **Estratégias de trend following** implementadas em Backtrader:
  - Cruzamento de Médias Móveis (SMA Cross)
  - Donchian Breakout
  - Momentum
- **Gestão de Risco**:
  - Stop-loss obrigatório (ATR, média móvel ou banda de suporte/resistência).
  - Dimensionamento de posição (`position sizing`) para limitar risco de cada trade a 1% do capital.
- **Banco de Dados**: SQLite por padrão, facilmente adaptável para Postgres.
- **Visualização**:
  - Gráficos de curva de equity, drawdowns, distribuição de retornos e preços com sinais de compra/venda.
  - Interface simples em `/ui/backtests/{id}` renderizando HTML+Plotly.
- **Extensível** para execução em tempo real (live trading).

---

## 🏗️ Arquitetura

```

FastAPI (endpoints)
│
├── app/main.py           # definição dos endpoints
├── app/schemas.py        # modelos Pydantic (request/response)
├── app/models.py         # tabelas SQLAlchemy
├── app/crud.py           # funções de banco
├── app/db.py             # setup do banco (SQLite / Postgres)
│
├── app/strategies/       # estratégias em Backtrader
│   ├── sma_cross.py
│   ├── donchian.py
│   ├── momentum.py
│   └── **init**.py       # registry + validação
│
├── app/services/         # integrações externas
│   └── yahoo.py          # fetch de dados do yfinance
│
├── app/backtest_engine.py # motor que conecta dados + estratégia + métricas
├── app/ui.py             # endpoints de visualização em HTML/Plotly
│
└── viz.py                # script/notebook para visualizações customizadas

````

---

## ⚙️ Instalação

1. Clone o repositório e crie ambiente virtual:

```bash
git clone <repo-url>
cd projeto
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
````

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

Dependências principais:

* `fastapi`
* `uvicorn`
* `sqlalchemy`
* `pydantic`
* `yfinance`
* `backtrader`
* `matplotlib`
* `plotly`
* `pandas`

3. Inicie o servidor:

```bash
uvicorn app.main:app --reload
```

API sobe em [http://127.0.0.1:8000](http://127.0.0.1:8000)
Docs automáticas: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 📡 Endpoints Principais

### Healthcheck

```
GET /health
```

### Rodar um backtest

```
POST /backtests/run
```

**Body exemplo**:

```json
{
  "ticker": "PETR4.SA",
  "start_date": "2021-01-01",
  "end_date": "2024-12-31",
  "strategy_type": "sma_cross",
  "strategy_params": {
    "fast": 20,
    "slow": 100,
    "risk_pct": 0.01,
    "stop_method": "atr",
    "atr_period": 14,
    "atr_mult": 2.0
  },
  "initial_cash": 100000,
  "commission": 0.001,
  "timeframe": "1d"
}
```

### Resultados de um backtest

```
GET /backtests/{id}/results
```

**Resposta exemplo**:

```json
{
  "backtest_id": 1,
  "metrics": {
    "total_return": 0.12,
    "sharpe": 1.05,
    "max_drawdown": -0.15,
    "win_rate": 0.55,
    "avg_trade_return": 0.02
  },
  "trades": [...],
  "daily_positions": [...],
  "equity_curve": [...]
}
```

### Listar backtests

```
GET /backtests
```

### Forçar atualização de indicadores

```
POST /data/indicators/update
```

### Listar estratégias disponíveis

```
GET /strategies
```

### Visualizar resultados (UI)

```
GET /ui/backtests/{id}
```

Renderiza uma página HTML com gráficos interativos de equity, drawdowns e retornos.
⚠️ Inclui correção para parâmetros legados (`threshold_pct → thresh`).

---

## 📊 Estratégias

### 1. SMA Cross

* Compra quando SMA(fast) cruza acima da SMA(slow).
* Venda quando cruza para baixo.
* Stop: ATR ou média lenta.
* Risk sizing: 1% do equity.

### 2. Donchian Breakout

* Compra quando preço rompe máxima dos últimos `n` períodos.
* Saída quando rompe mínima.
* Stop: ATR ou banda inferior.
* Risk sizing: 1% do equity.

### 3. Momentum

* Compra quando retorno acumulado em `lookback` períodos > `thresh`.
* Saída quando momentum ≤ 0.
* Stop: ATR ou média móvel.
* Risk sizing: 1% do equity.
* **Compatibilidade retroativa**: parâmetros antigos como `threshold_pct` são automaticamente normalizados.

---

## 🛡️ Gestão de Risco

* **Stop obrigatório**: definido em `strategy_params.stop_method`:

  * `"atr"` → stop = preço - ATR * mult
  * `"ma"`  → stop = média móvel
  * `"channel"` (Donchian) → banda inferior
* **Position sizing**:

  * Calcula o risco por ação = entrada - stop.
  * Define tamanho máximo tal que perda ≤ 1% do equity.
  * Respeita também limite de caixa disponível.
* **Parâmetros configuráveis**: `risk_pct`, `atr_period`, `atr_mult`, `lot_size`.

---

## 📌 Próximos Passos / Extensões

* Suporte a operações short.
* Integração com dados em tempo real para execução live.
* Deploy em Docker com Postgres.

---

## 👤 Autor - Pedro Rodrigues

Projeto desenvolvido como **case prático** de vaga para **Dev Jr - Mercado Financeiro**.

