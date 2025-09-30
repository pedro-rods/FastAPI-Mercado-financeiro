Perfeito 🚀 — vou estender o seu **README.md final** incluindo a seção **📬 Coleção de Requests** com os arquivos prontos (Postman, Thunder Client e VS Code REST Client) e um mini tutorial de importação.

---

# README.md (versão final com coleções incluídas)

```markdown
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
│   └── jobs/               # rotinas agendadas
├── migrations/             # alembic migrations
├── tests/                  # pytest + coverage
├── collections/            # 📬 coleções de requests (Postman, Thunder, REST Client)
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

```bash
docker-compose up --build
```

---

## 🧪 Testes e cobertura

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

## 📬 Coleção de Requests

Coleções prontas para testar a API:

* `collections/trading_api.postman_collection.json` → Importar no **Postman**
* `collections/trading_api.thunder-collection.json` → Importar no **Thunder Client** (VS Code)
* `collections/trading_api.http` → Usar no **VS Code REST Client**

### Como importar

* **Postman:** *Import* → cole JSON ou selecione arquivo.
* **Thunder Client (VS Code):** Sidebar → *Collections* → *Import* → selecione JSON.
* **VS Code REST Client:** abra `trading_api.http` e clique em *Send Request* sobre cada bloco.

---

## 📊 Visualização

### UI HTML

```
http://localhost:8000/ui/backtests/{id}
```

### Script local

```bash
python bin/viz_from_api.py 1
```

---

## 🔧 Variáveis de ambiente

`.env` (exemplo):

```
DATABASE_URL=postgresql+psycopg2://appuser:appsecret@localhost:5432/tradingdb
BT_DEBUG=0
USE_SQLITE=0
```

Se `USE_SQLITE=1`, o projeto roda em **modo dev com SQLite** (sem migrações, recria DB do zero).
Alternativamente, também é possível rodar o projeto localmente caso algo dê errado no processo: 
Utilizando os seguintes comandos:
```
pip install -r requirements.txt
$env:APP_MODE="dev"
uvicron app.main:app --reload  

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
