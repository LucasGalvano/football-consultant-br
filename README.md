# ⚽ Consultor do Futebol Brasileiro

API REST completa para análise do Campeonato Brasileiro (2014–2024), demonstrando **Polyglot Persistence** com três bancos de dados diferentes integrados em uma única aplicação.

> Projeto acadêmico — 5º Semestre · CCD410 - Performance e Tunning de Dados.

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────┐
│           Frontend (React + Vite)                │
│           http://localhost:5173                  │
└──────────────────────┬──────────────────────────┘
                       │ HTTP / REST
┌──────────────────────▼──────────────────────────┐
│              Backend (FastAPI)                   │
│              http://localhost:8000               │
│                                                  │
│   /clubes  /estadios  /partidas  /analises       │
└────────────┬──────────────┬──────────────┬───────┘
             │              │              │
    ┌────────▼──────┐ ┌─────▼──────┐ ┌───▼────────────┐
    │  PostgreSQL   │ │  MongoDB   │ │ Cassandra/     │
    │  (Docker)     │ │  (Docker)  │ │ AstraDB(Cloud) │
    │               │ │            │ │                │
    │ • Clubes      │ │ • Estatís- │ │ • Gols         │
    │ • Estádios    │ │   ticas    │ │ • Cartões      │
    │ • Partidas    │ │   táticas  │ │   por partida  │
    └───────────────┘ └────────────┘ └────────────────┘
```

### Por que três bancos?

| Banco | Tipo | Dados | Justificativa |
|-------|------|-------|---------------|
| **PostgreSQL** | Relacional | Clubes, Estádios, Partidas | Integridade referencial via FK, queries com JOIN, dados mestres estruturados |
| **MongoDB** | Documento | Estatísticas táticas | Schema flexível — nem todas as partidas têm todos os campos; dados hierárquicos (mandante/visitante aninhados) |
| **Cassandra/AstraDB** | Wide-column | Gols e Cartões | Alto volume (~30k eventos); partition key = `partida_id` co-localiza todos os eventos de uma partida no mesmo nó |

---

## 📊 Dados

| Banco | Tabela / Collection | Registros |
|-------|---------------------|-----------|
| PostgreSQL | `clubes` | 34 |
| PostgreSQL | `estadios` | 74 |
| PostgreSQL | `partidas` | 4.179 |
| MongoDB | `partidas_estatisticas` | 3.799 |
| Cassandra | `gols_por_partida` | 9.861 |
| Cassandra | `cartoes_por_partida` | 20.953 |

**Período:** 2014-04-19 a 2024-12-08

> **Nota sobre 2020/2021:** O Brasileirão 2020 foi interrompido pela pandemia e terminou em fevereiro de 2021. O sistema usa mapeamento por range de IDs (em vez de ano da data) para separar corretamente as temporadas.

---

## 🚀 Setup

### Pré-requisitos

- **Python 3.11** — obrigatório (3.12+ é incompatível com o driver Cassandra)
- **Docker Desktop** — para PostgreSQL e MongoDB
- **Node.js 16+** — para o frontend
- **Credenciais AstraDB** — arquivos `.zip` e `.json` (solicitar ao responsável)

---

### 1. Clonar e configurar o ambiente

```powershell
git clone https://github.com/LucasGalvano/football-consultant-br
cd football_consultant_br

# Criar ambiente virtual com Python 3.11
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
# source venv/bin/activate    # Linux/Mac

# Se der erro de permissão (Windows):
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Variáveis de ambiente

```powershell
cp .env.example .env
```

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=futebol_brasileiro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha

# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=admin123
MONGO_DB=futebol_brasileiro
MONGO_URI=mongodb://admin:admin123@localhost:27017/futebol_brasileiro?authSource=admin

# AstraDB (Cassandra)
ASTRA_DB_SECURE_BUNDLE_PATH=app/config/secure-connect-futebol-db.zip
ASTRA_DB_TOKEN_PATH=app/config/futebol_db-token.json
ASTRA_DB_KEYSPACE=brasileirao
```

### 3. Credenciais AstraDB

Coloque os dois arquivos em `app/config/`:
```
app/config/
├── secure-connect-futebol-db.zip
└── futebol_db-token.json
```

> ⚠️ Esses arquivos não estão no repositório por segurança.

### 4. Subir os bancos locais

```powershell
docker-compose up -d
docker-compose ps   # deve mostrar futebol_postgres e futebol_mongo como "healthy"
```

### 5. Testar conexões

```powershell
python -m app.config.database
```

Saída esperada:
```
PostgreSQL     OK
MongoDB        OK
AstraDB        OK
```

### 6. Pipeline ETL

```powershell
# Limpeza dos CSVs brutos
python scripts/1_clean_datasets.py

# Validação de integridade — 31 checks
python scripts/2_validate_data.py

# Seed dos bancos
python scripts/3_seed_postgres.py
python scripts/4_seed_mongo.py
python scripts/5_seed_cassandra.py

# Dados extras: cidade/estado/capacidade dos estádios + ano de fundação dos clubes
python scripts/6_seed_extras.py

# Verificação final
python scripts/verificar_bancos.py
```

### 7. Rodar o backend

```powershell
# Da raiz do projeto
uvicorn app.main:app --reload
```

### 8. Rodar o frontend

```powershell
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

| Serviço | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |

---

## 🔌 Endpoints da API

### Clubes
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/clubes/` | Lista todos os clubes |
| `GET` | `/clubes/{id}` | Detalhe de um clube |

### Estádios
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/estadios/` | Lista todos os estádios |
| `GET` | `/estadios/{id}` | Detalhe de um estádio |

### Partidas
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/partidas/` | Lista partidas com filtros (`ano`, `rodada`, `clube_id`, `estadio_id`) |
| `GET` | `/partidas/{id}` | **Polyglot:** PostgreSQL + MongoDB + Cassandra em uma resposta |
| `GET` | `/partidas/{id}/gols` | Gols da partida (Cassandra) |
| `GET` | `/partidas/{id}/cartoes` | Cartões da partida (Cassandra) |
| `GET` | `/partidas/{id}/estatisticas` | Estatísticas táticas (MongoDB) |

### Análises
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/analises/anos` | Anos disponíveis no dataset |
| `GET` | `/analises/classificacao/{ano}` | Tabela de classificação da temporada |
| `GET` | `/analises/artilheiros` | Top goleadores (`ano`, `limite`) |
| `GET` | `/analises/ranking-cartoes` | Ranking de cartões (`ano`, `tipo`, `limite`) |
| `GET` | `/analises/clube/{id}/estatisticas` | Médias táticas de um clube (MongoDB) |
| `GET` | `/analises/confronto` | Confronto direto entre dois clubes |

---

## 🗂️ Estrutura do Projeto

```
football_consultant_br/
│
├── app/
│   ├── config/
│   │   ├── database.py          # Conexões PostgreSQL, MongoDB, AstraDB
│   │   └── settings.py          # Variáveis de ambiente (Pydantic Settings)
│   │
│   ├── models/
│   │   ├── postgres_models.py   # SQLAlchemy: Clube, Estadio, Partida
│   │   ├── mongo_schemas.py     # Pydantic: PartidaEstatisticas
│   │   └── cassandra_models.py  # CQL: gols_por_partida, cartoes_por_partida
│   │
│   ├── repositories/
│   │   ├── postgres_repo.py     # Queries SQLAlchemy + mapeamento de temporadas
│   │   ├── mongo_repo.py        # Aggregations MongoDB
│   │   └── cassandra_repo.py    # Queries paralelas com ThreadPoolExecutor
│   │
│   ├── routers/
│   │   ├── clubes.py
│   │   ├── estadios.py
│   │   ├── partidas.py          # Endpoint polyglot: junta os 3 bancos
│   │   └── analises.py
│   │
│   ├── schemas/responses.py     # Schemas de resposta Pydantic
│   ├── utils/                   # Limpeza e normalização de dados
│   ├── dependencies.py          # Injeção de dependências FastAPI
│   └── main.py
│
├── frontend/
│   └── src/
│       ├── pages/               # Home, Clubes, Partidas, Classificacao...
│       ├── components/          # Layout, Header, Footer, Common
│       ├── services/api.js      # Axios centralizado
│       └── hooks/useApi.js      # Hook de requisições
│
├── scripts/
│   ├── 1_clean_datasets.py      # Limpeza dos CSVs brutos
│   ├── 2_validate_data.py       # 31 validações de integridade
│   ├── 3_seed_postgres.py       # Popula PostgreSQL
│   ├── 4_seed_mongo.py          # Popula MongoDB
│   ├── 5_seed_cassandra.py      # Popula AstraDB
│   ├── 6_seed_extras.py         # Cidade/estado/capacidade/fundação
│   └── verificar_bancos.py      # Checklist de contagens
│
├── data/
│   ├── raw/                     # CSVs originais (Kaggle / GitHub)
│   └── processed/               # CSVs limpos (gerados pelo script 1)
│
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🗄️ Modelagem

### PostgreSQL

```
clubes                    estadios
──────                    ────────
id (PK)                   id (PK)
nome_oficial              nome
sigla                     cidade
estado                    estado
ano_fundacao              capacidade
        ↑                         ↑
        └──────── partidas ────────┘
                  ────────
                  id (PK)
                  rodada
                  data / hora
                  mandante_id  (FK → clubes)
                  visitante_id (FK → clubes)
                  vencedor_id  (FK → clubes)
                  estadio_id   (FK → estadios)
                  placar_mandante / placar_visitante
                  formacao_mandante / formacao_visitante
                  tecnico_mandante / tecnico_visitante
```

### MongoDB

```json
{
  "partida_id": 5000,
  "rodada": 10,
  "mandante": {
    "nome": "Flamengo",
    "estatisticas": {
      "chutes": 18,
      "passes": 512,
      "posse_de_bola": 65.5,
      "finalizacoes": 8,
      "escanteios": 7
    }
  },
  "visitante": { "..." }
}
```

### Cassandra

```cql
-- Partition key: partida_id
-- Todos os gols de uma partida ficam co-localizados no mesmo nó
-- Clustering por minuto garante ordenação cronológica sem ORDER BY

gols_por_partida
  PRIMARY KEY (partida_id, minuto, atleta)
  CLUSTERING ORDER BY (minuto ASC)

cartoes_por_partida
  PRIMARY KEY (partida_id, minuto, atleta, tipo_cartao)
  CLUSTERING ORDER BY (minuto ASC)
```

---

## 🖥️ Frontend

| Página | Rota | Fonte dos dados |
|--------|------|-----------------|
| Home | `/` | PostgreSQL + PostgreSQL |
| Clubes | `/clubes` | PostgreSQL |
| Detalhe do Clube | `/clubes/:id` | PostgreSQL + MongoDB |
| Partidas | `/partidas` | PostgreSQL |
| Detalhe da Partida | `/partidas/:id` | **PostgreSQL + MongoDB + Cassandra** |
| Estádios | `/estadios` | PostgreSQL |
| Classificação | `/classificacao/:ano` | PostgreSQL |
| Artilheiros | `/artilheiros` | PostgreSQL + Cassandra |
| Confronto Direto | `/confronto` | PostgreSQL + MongoDB |

**Stack:** React 18 · React Router v6 · Axios · Tailwind CSS · Vite

---

## 🐳 Docker

```powershell
docker-compose up -d      # Subir
docker-compose ps         # Status
docker-compose logs -f    # Logs em tempo real
docker-compose stop       # Parar (dados persistem)
docker-compose down -v    # Parar e remover volumes
```

| Container | Imagem | Porta local |
|-----------|--------|-------------|
| `futebol_postgres` | `postgres:15-alpine` | `5433` |
| `futebol_mongo` | `mongo:7.0` | `27017` |

> A porta do PostgreSQL é `5433` (não `5432`) para evitar conflito com instâncias locais.

---

## 🔍 Verificando os bancos manualmente

### PostgreSQL
```powershell
docker exec -it futebol_postgres psql -U postgres -d futebol_brasileiro
```
```sql
SELECT COUNT(*) FROM clubes;
SELECT COUNT(*) FROM estadios;
SELECT COUNT(*) FROM partidas;
\q
```

### MongoDB
```powershell
docker exec -it futebol_mongo mongosh -u admin -p admin123 --authenticationDatabase admin
```
```javascript
use futebol_brasileiro
db.partidas_estatisticas.countDocuments()
db.partidas_estatisticas.findOne()
exit
```

### Cassandra (AstraDB)
Acesse https://astra.datastax.com → seu database → **CQL Console**:
```cql
USE brasileirao;
SELECT COUNT(*) FROM gols_por_partida;
SELECT COUNT(*) FROM cartoes_por_partida;
SELECT * FROM gols_por_partida WHERE partida_id = 5000;
```

---

## 🔧 Troubleshooting

| Problema | Solução |
|----------|---------|
| `Unable to load a default connection class` | Use Python 3.11 (não 3.12+) |
| `Keyspace does not exist` | `.env` deve ter `ASTRA_DB_KEYSPACE=brasileirao` |
| `fe_sendauth: no password supplied` | Execute os scripts **da raiz do projeto**, não de dentro de `scripts/` |
| `Port already in use` | PostgreSQL usa porta `5433`, não `5432` |
| Containers não sobem | `docker-compose down -v && docker-compose up -d` |
| Seed falha com duplicata | Script já tem `reset=True` — rode novamente normalmente |

---

## 📦 Dependências principais

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
pymongo==4.6.1
cassandra-driver==3.29.1
pydantic==2.5.3
pydantic-settings==2.1.0
```

--- 
 ## Integrantes
- Gustavo Matias Félix - [🐈‍⬛ Github Profile](https://github.com/Gustavo-Matias19)
- Lucas Galvano de Paula - [🐈‍⬛ Github Profile](https://github.com/LucasGalvano)
- Vinicius Trivellato Pereira - [🐈‍⬛ Github Profile](https://github.com/primol)