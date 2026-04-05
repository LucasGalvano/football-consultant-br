"""
Dependências FastAPI
Provê sessões de banco de dados via injeção de dependência.
"""

from functools import lru_cache
from sqlalchemy.orm import sessionmaker, Session
from pymongo.collection import Collection

from app.config.database import get_postgres_engine, get_mongo_db, get_astra_session


# ─── PostgreSQL ────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_session_factory():
    engine = get_postgres_engine()
    return sessionmaker(bind=engine)


def get_postgres_session() -> Session:
    SessionLocal = _get_session_factory()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


# ─── MongoDB ───────────────────────────────────────────────────────────────────

def get_mongo_collection() -> Collection:
    db = get_mongo_db()
    return db["partidas_estatisticas"]


# ─── Cassandra ─────────────────────────────────────────────────────────────────

_cassandra_session = None


def get_cassandra_session():
    global _cassandra_session
    if _cassandra_session is None:
        _cassandra_session = get_astra_session()
    return _cassandra_session