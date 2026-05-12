"""
Dependências FastAPI
Provê sessões/conexões de banco via injeção de dependência.

CORREÇÕES:
- get_mongo_collection agora chama database.get_mongo_collection() que
  garante criação do índice em partida_id.
- Cassandra singleton com lock para ambientes multi-thread.
"""

import threading
from sqlalchemy.orm import sessionmaker, Session
from pymongo.collection import Collection

from app.config.database import get_postgres_engine, get_mongo_collection as _get_col, get_astra_session


# ─── PostgreSQL ────────────────────────────────────────────────────────────────

def _get_session_factory():
    # get_postgres_engine já é @lru_cache — sem custo extra chamar aqui
    return sessionmaker(bind=get_postgres_engine(), autocommit=False, autoflush=False)


def get_postgres_session() -> Session:
    """Generator que entrega e fecha a sessão ao final do request."""
    SessionLocal = _get_session_factory()
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ─── MongoDB ───────────────────────────────────────────────────────────────────

def get_mongo_collection() -> Collection:
    """
    Retorna a collection partidas_estatisticas com índice garantido.
    BUG CORRIGIDO: antes retornava db["partidas_estatisticas"] diretamente,
    sem criar o índice em partida_id.
    """
    return _get_col("partidas_estatisticas")


# ─── Cassandra ─────────────────────────────────────────────────────────────────

_cassandra_session = None
_cassandra_lock = threading.Lock()


def get_cassandra_session():
    """
    Singleton thread-safe para a sessão Cassandra.
    Usa lock para evitar criação dupla em ambientes multi-threaded (Gunicorn).
    """
    global _cassandra_session
    if _cassandra_session is None:
        with _cassandra_lock:
            if _cassandra_session is None:          # double-checked locking
                _cassandra_session = get_astra_session()
    return _cassandra_session