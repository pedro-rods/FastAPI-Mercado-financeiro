# Trading API – Backtesting e Estratégias Algorítmicas

API em **FastAPI** para backtesting de estratégias quantitativas no mercado financeiro, com integração ao Yahoo Finance, execução em **Backtrader**, controle de versões de banco com **Alembic**, e visualizações básicas em HTML/Notebook.

---

## 🚀 Funcionalidades

- **Endpoints principais**
  - `POST /backtests/run` – dispara backtest (SMA, Donchian, Momentum)
  - `GET /backtests/{id}/results` – resultados (métricas, trades, curva de equity)
  - `GET /backtests` – lista backtests com filtros
  - `POST /data/indicators/update` – atualiza preços e indicadores
  - `GET /health` – health-check da API
  - `GET /ui/backtests/{id}` – visualização HTML (gráficos)

- **Estratégias disponíveis**
  - **SMA Cross** – cruzamento de médias móveis
  - **Donchian Breakout** – rompimento de máximas/mínimas
  - **Momentum** – força relativa em janela de lookback
  - ✅ Todas implementam **gestão de risco**:
    - Dimensionamento de posição (`position sizing`) com risco fixo (ex.: 1% do capital)
    - Stop baseado em **ATR** (volatilidade) ou média móvel

- **Gestão de risco**
  - Capital inicial configurável
  - Stop-loss técnico obrigatório
  - Tamanho da posição calculado para limitar perda máxima

- **Rotinas (cron jobs)**
  - `daily_indicators` – baixa OHLCV e recalcula indicadores diariamente
  - `health_check` – verifica conexão Postgres + latência do Yahoo

- **Banco de dados**
  - Postgres (via Docker)
  - Migrações gerenciadas com **Alembic**
  - Seed inicial de tickers

- **Visualização**
  - Gráficos de preço + sinais de compra/venda
  - Curva de equity
  - Distribuição de retornos
  - Série de drawdown
  - Disponível via `/ui/backtests/{id}` ou notebook/script (`bin/viz_from_api.py`)

---

## 📂 Estrutura do projeto

```

FastAPI-Mercado-financeiro/
├── app/
│   ├── main.py             # ponto de entrada FastAPI
│   ├── models.py           # SQLAlchemy ORM
│   ├── schemas.py          # Pydantic
│   ├── backtest_engine.py  # integração Backtrader
│   ├── strategies/         # estratégias (sma, donchian, momentum)
│   ├── services/           # serviços externos (Yahoo Finance)
│   └── ui.py               # rotas de visualização HTML
├── bin/
│   ├── seed.py             # cadastro inicial de tickers
│   ├── viz_from_api.py     # script para visualizar backtest
│   └── jobs/               # rotinas agendadas
├── migrations/             # alembic migrations
├── tests/                  # pytest + coverage
├── notebooks/              # (opcional) notebooks de exploração
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── alembic.ini
└── README.md

````

---

## ⚙️ Instalação e execução

### 1. Requisitos
- Python 3.11+
- Docker e Docker Compose

### 2. Clonar e instalar dependências
```bash
git clone https://github.com/seuusuario/fastapi-trading.git
cd fastapi-trading
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
pip install -r requirements.txt
````

### 3. Subir Postgres via Docker

```bash
docker-compose up -d
```

### 4. Migrações + seed

```bash
alembic upgrade head
python bin/seed.py
```

### 5. Rodar API

```bash
uvicorn app.main:app --reload
```

Acesse em:
👉 [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger)
👉 [http://localhost:8000/redoc](http://localhost:8000/redoc) (Redoc)
👉 [http://localhost:8000/ui/backtests/{id}](http://localhost:8000/ui/backtests/{id}) (UI HTML)

---

## 🐳 Execução com Docker

Build e run:

```bash
docker build -t trading-api .
docker run -p 8000:8000 trading-api
```

Ou diretamente:

```bash
docker-compose up --build
```

---

## 🧪 Testes e cobertura

Rodar testes com Pytest:

```bash
pytest --cov=app --cov-report=term-missing
```

Com HTML:

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

Meta: **≥70% de cobertura nos módulos core**

---

## 📡 Exemplos de requests

### Health

```http
GET http://localhost:8000/health
```

### Run Backtest SMA

```http
POST http://localhost:8000/backtests/run
Content-Type: application/json

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
    "atr_mult": 2.0,
    "lot_size": 1
  },
  "initial_cash": 100000,
  "commission": 0.001,
  "timeframe": "1d"
}
```

### Get Results

```http
GET http://localhost:8000/backtests/1/results
```

### Jobs

```http
POST http://localhost:8000/jobs/daily_indicators
["PETR4.SA","VALE3.SA","AAPL"]

POST http://localhost:8000/jobs/health_check
```

---

## 📊 Visualização

### UI HTML

Acesse:

```
http://localhost:8000/ui/backtests/{id}
```

### Script local

```bash
python bin/viz_from_api.py 1
```

Plota:

* Curva de Equity
* Retornos diários
* Drawdown

---

## 🔧 Variáveis de ambiente

Arquivo `.env` (exemplo):

```
DATABASE_URL=postgresql+psycopg2://appuser:appsecret@localhost:5432/tradingdb
BT_DEBUG=0
```

---

## 📌 Roadmap Futuro

* Estratégias adicionais (mean reversion, pairs trading)
* Execução live com integração corretora
* CI/CD com GitHub Actions
* Painel frontend React

---

## 📜 Licença

MIT License.