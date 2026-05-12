"""
Dependências FastAPI — injeção de conexões via Depends().

CORREÇÕES:
- get_mongo_collection chama database.get_mongo_collection() que
  garante o índice único em partida_id.
- Cassandra singleton com threading.Lock para segurança em
  ambientes multi-worker (Gunicorn).
- get_postgres_session faz rollback automático em caso de exceção.
"""

import threading
from sqlalchemy.orm import sessionmaker, Session
from pymongo.collection import Collection

from app.config.database import (
    get_postgres_engine,
    get_mongo_collection as _db_get_col,
    get_astra_session,
)


# ────────────────────────────────────────────────────────────
# POSTGRESQL
# ────────────────────────────────────────────────────────────

def get_postgres_session() -> Session:
    """
    Generator que entrega a sessão SQLAlchemy e garante fechamento
    ao final de cada request, com rollback em caso de erro.
    """
    SessionLocal = sessionmaker(
        bind=get_postgres_engine(),
        autocommit=False,
        autoflush=False,
    )
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ────────────────────────────────────────────────────────────
# MONGODB
# ────────────────────────────────────────────────────────────

def get_mongo_collection() -> Collection:
    """
    Retorna a collection partidas_estatisticas.
    O índice único em partida_id é criado automaticamente (no-op
    se já existir) pela função de banco.
    """
    return _db_get_col("partidas_estatisticas")


# ────────────────────────────────────────────────────────────
# CASSANDRA
# ────────────────────────────────────────────────────────────

_cassandra_session = None
_cassandra_lock = threading.Lock()


def get_cassandra_session():
    """
    Singleton thread-safe para a sessão Cassandra.
    Double-checked locking evita criação duplicada em ambientes
    com múltiplas threads (Gunicorn workers).
    """
    global _cassandra_session
    if _cassandra_session is None:
        with _cassandra_lock:
            if _cassandra_session is None:
                _cassandra_session = get_astra_session()
    return _cassandra_session