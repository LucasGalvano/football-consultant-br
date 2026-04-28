# ⚽ Consultor do Futebol Brasileiro

API REST completa para análise e consulta do Campeonato Brasileiro (2014–2023), com dados distribuídos em três bancos de dados e um frontend React moderno.

---

## 🏗️ Arquitetura

```
┌──────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Vite)                   │
│              http://localhost:5173                                │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTP
┌──────────────────────────▼───────────────────────────────────────┐
│                    Backend (FastAPI)                              │
│              http://localhost:8000                                │
│                                                                  │
│  /clubes   /estadios   /partidas   /analises                     │
└────────────┬───────────────┬───────────────┬─────────────────────┘
             │               │               │
     ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────────┐
     │  PostgreSQL  │ │   MongoDB   │ │ Cassandra/     │
     │  (Docker)    │ │  (Docker)   │ │ AstraDB(Cloud) │
     │              │ │             │ │                │
     │ • Clubes     │ │ • Estatís-  │ │ • Gols         │
     │ • Estádios   │ │   ticas     │ │ • Cartões      │
     │ • Partidas   │ │   táticas   │ │   por partida  │
     └──────────────┘ └─────────────┘ └────────────────┘
```

### Por que três bancos?

| Banco | Tipo | Dados | Justificativa |
|-------|------|-------|---------------|
| **PostgreSQL** | Relacional | Clubes, Estádios, Partidas | Dados estruturados com relacionamentos (FK) |
| **MongoDB** | Documento | Estatísticas táticas | Campos variáveis por partida (nem todas têm todos os stats) |
| **Cassandra/AstraDB** | Wide-column | Gols e Cartões | Alto volume de eventos; consultas por `partida_id` ultra-rápidas |

---

## 📊 Dados

| Banco | Tabela/Collection | Registros |
|-------|------------------|-----------|
| PostgreSQL | `clubes` | 34 |
| PostgreSQL | `estadios` | 74 |
| PostgreSQL | `partidas` | 4.179 |
| MongoDB | `partidas_estatisticas` | 3.799 |
| Cassandra | `gols_por_partida` | 9.861 |
| Cassandra | `cartoes_por_partida` | 20.953 |

---

## 🚀 Setup Rápido

### Pré-requisitos

- **Python 3.11** (não use 3.12+)
- **Docker Desktop** (para PostgreSQL e MongoDB)
- **Node.js 16+** (para o frontend)
- Credenciais do **AstraDB** (arquivos `.zip` e `.json`)

### 1. Backend

```bash
# Clonar e entrar no projeto
git clone https://github.com/LucasGalvano/football-consultant-br
cd football_consultant_br

# Criar e ativar ambiente virtual
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
# source venv/bin/activate     # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
cp .env.example .env
```

> Edite o `.env` com as senhas corretas. Coloque os arquivos do AstraDB em `app/config/`:
> - `secure-connect-futebol-db.zip`
> - `futebol_db-token.json`

```bash
# Subir bancos locais
docker-compose up -d

# Testar conexões
python -m app.config.database

# Popular os bancos
python scripts/1_clean_datasets.py
python scripts/3_seed_postgres.py
python scripts/4_seed_mongo.py
python scripts/5_seed_cassandra.py

# Verificar integridade
python scripts/verificar_bancos.py

# Iniciar API
uvicorn app.main:app --reload
```

### 2. Frontend

```bash
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
| `GET` | `/partidas/` | Lista partidas (filtros: `ano`, `rodada`, `clube_id`, `estadio_id`) |
| `GET` | `/partidas/{id}` | Detalhe completo (PostgreSQL + MongoDB + Cassandra) |
| `GET` | `/partidas/{id}/gols` | Gols da partida (Cassandra) |
| `GET` | `/partidas/{id}/cartoes` | Cartões da partida (Cassandra) |
| `GET` | `/partidas/{id}/estatisticas` | Estatísticas táticas (MongoDB) |

### Análises
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/analises/anos` | Anos disponíveis no dataset |
| `GET` | `/analises/classificacao/{ano}` | Tabela de classificação |
| `GET` | `/analises/artilheiros` | Artilheiros (filtros: `ano`, `limite`) |
| `GET` | `/analises/ranking-cartoes` | Ranking de cartões (filtros: `ano`, `tipo`, `limite`) |
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
│   │   └── settings.py          # Variáveis de ambiente (Pydantic)
│   │
│   ├── models/
│   │   ├── postgres_models.py   # SQLAlchemy: Clube, Estadio, Partida
│   │   ├── mongo_schemas.py     # Pydantic: PartidaEstatisticas
│   │   └── cassandra_models.py  # CQL: gols_por_partida, cartoes_por_partida
│   │
│   ├── repositories/
│   │   ├── postgres_repo.py     # Queries SQLAlchemy
│   │   ├── mongo_repo.py        # Queries MongoDB
│   │   └── cassandra_repo.py    # Queries Cassandra
│   │
│   ├── routers/
│   │   ├── clubes.py
│   │   ├── estadios.py
│   │   ├── partidas.py
│   │   └── analises.py
│   │
│   ├── schemas/
│   │   └── responses.py         # Schemas de resposta Pydantic
│   │
│   ├── utils/
│   │   ├── cleaning_functions.py
│   │   └── clubes_normalizacao.py
│   │
│   ├── dependencies.py          # Injeção de dependências FastAPI
│   └── main.py                  # Aplicação principal
│
├── frontend/                    # React + Vite + Tailwind CSS
│   └── src/
│       ├── pages/               # Home, Clubes, Partidas, Classificacao...
│       ├── components/          # Layout, Header, Footer, Common
│       ├── services/api.js      # Axios centralizado
│       └── hooks/useApi.js      # Hook de requisições
│
├── scripts/
│   ├── 1_clean_datasets.py      # Limpeza dos CSVs brutos
│   ├── 2_validate_data.py       # Validação de integridade
│   ├── 3_seed_postgres.py       # Popula PostgreSQL
│   ├── 4_seed_mongo.py          # Popula MongoDB
│   ├── 5_seed_cassandra.py      # Popula AstraDB
│   └── verificar_bancos.py      # Checklist final
│
├── data/
│   ├── raw/                     # CSVs originais do Kaggle
│   └── processed/               # CSVs limpos (gerados pelo script 1)
│
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🐳 Docker

```bash
# Subir containers
docker-compose up -d

# Ver status
docker-compose ps

# Ver logs
docker-compose logs -f

# Parar
docker-compose stop
```

**Containers:**

| Container | Imagem | Porta |
|-----------|--------|-------|
| `futebol_postgres` | `postgres:15-alpine` | `5433:5432` |
| `futebol_mongo` | `mongo:7.0` | `27017:27017` |

> A porta do PostgreSQL é `5433` (não `5432`) para evitar conflito com instâncias locais.

---

## 🗄️ Modelagem dos Bancos

### PostgreSQL — Modelo Relacional

```
clubes          estadios
──────          ────────
id (PK)         id (PK)
nome_oficial    nome
sigla           cidade
estado          estado
                capacidade
        ↑               ↑
        │               │
        └──── partidas ──┘
              ──────────
              id (PK)
              rodada
              data / hora
              mandante_id (FK)
              visitante_id (FK)
              vencedor_id (FK)
              estadio_id (FK)
              placar_mandante
              placar_visitante
              formacao_mandante/visitante
              tecnico_mandante/visitante
```

### MongoDB — Documento

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
  "visitante": { ... }
}
```

### Cassandra — Wide-Column

```cql
-- Partition key: partida_id (co-localiza todos os gols de uma partida)
-- Clustering: minuto, atleta (ordena cronologicamente)

gols_por_partida
  PRIMARY KEY (partida_id, minuto, atleta)

cartoes_por_partida
  PRIMARY KEY (partida_id, minuto, atleta, tipo_cartao)
```

---

## 🖥️ Frontend

Páginas disponíveis:

| Página | Rota | Descrição |
|--------|------|-----------|
| Home | `/` | Cards de estatísticas e atalhos rápidos |
| Clubes | `/clubes` | Listagem com busca |
| Detalhe do Clube | `/clubes/:id` | Estatísticas táticas médias |
| Partidas | `/partidas` | Filtros por ano, rodada, clube |
| Detalhe da Partida | `/partidas/:id` | Placar, gols, cartões, estatísticas |
| Estádios | `/estadios` | Listagem com busca |
| Classificação | `/classificacao/:ano` | Tabela por temporada |
| Artilheiros | `/artilheiros` | Top goleadores + ranking de cartões |
| Confronto Direto | `/confronto` | Histórico entre dois clubes |

**Stack:** React 18 · React Router · Axios · Recharts · Tailwind CSS · Vite

---

## ⚙️ Variáveis de Ambiente

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=futebol_brasileiro
POSTGRES_USER=admin
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

---

## 🔧 Troubleshooting

**Porta `5432` em uso**
> A configuração já usa `5433`. Verifique se o `.env` tem `POSTGRES_PORT=5433`.

**`Unable to load a default connection class` (AstraDB)**
> Incompatibilidade com Python 3.12+. Use obrigatoriamente **Python 3.11**.

**`Keyspace does not exist` (Cassandra)**
> O `.env` precisa ter `ASTRA_DB_KEYSPACE=brasileirao` (exatamente assim).

**Containers não sobem**
```bash
docker-compose logs
docker-compose up -d --build --force-recreate
```

**Seed falha com duplicata**
```bash
python scripts/3_seed_postgres.py --reset
```

---

## 📦 Dependências Principais

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

## 📄 Licença

MIT — Livre para uso educacional e comercial.

---
