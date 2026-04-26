"""
Consultor do Futebol Brasileiro — API
======================================
FastAPI + PostgreSQL + MongoDB + Cassandra/AstraDB

Endpoints:
  /clubes          → Lista e busca clubes
  /estadios        → Lista e busca estádios
  /partidas        → Lista, filtra e detalha partidas (dados dos 3 bancos)
  /analises        → Classificação, artilheiros, rankings, confrontos
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import clubes, estadios, partidas, analises

app = FastAPI(
    title="🇧🇷 Consultor do Futebol Brasileiro",
    description=(
        "API para consulta e análise do Campeonato Brasileiro (2014–2023).\n\n"
        "**Fontes de dados:**\n"
        "- **PostgreSQL** — clubes, estádios, partidas e resultados\n"
        "- **MongoDB** — estatísticas táticas por partida (posse, passes, chutes…)\n"
        "- **Cassandra/AstraDB** — gols e cartões evento a evento\n\n"
        "Use `/analises/classificacao/{ano}` para ver a tabela de um campeonato,\n"
        "`/partidas/{id}` para o detalhe completo de uma partida,\n"
        "ou `/analises/artilheiros` para os maiores goleadores."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(clubes.router)
app.include_router(estadios.router)
app.include_router(partidas.router)
app.include_router(analises.router)


@app.get("/", tags=["Health"])
def root():
    return {
        "status": "ok",
        "app": "Consultor do Futebol Brasileiro",
        "versao": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health():
    """Verifica conectividade com os três bancos de dados."""
    from app.config.database import (
        test_postgres_connection,
        test_mongo_connection,
        test_astra_connection,
    )
    import io, sys

    def _capturar(fn):
        buf = io.StringIO()
        sys.stdout = buf
        ok = fn()
        sys.stdout = sys.__stdout__
        return ok

    return {
        "postgres": _capturar(test_postgres_connection),
        "mongodb": _capturar(test_mongo_connection),
        "cassandra": _capturar(test_astra_connection),
    }