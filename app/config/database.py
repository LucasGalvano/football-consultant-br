import json
from functools import lru_cache

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient, ASCENDING

from app.config.settings import settings


# ============== POSTGRESQL ==============

@lru_cache(maxsize=1)
def get_postgres_engine():
    """
    Retorna o engine do PostgreSQL (singleton via lru_cache).
    Inclui client_encoding=utf8 para suporte a caracteres especiais.

    BUG CORRIGIDO: havia duas definições da função; a segunda (sem
    client_encoding) sobrescrevia a primeira. Agora existe apenas uma,
    com o encoding correto e cacheada para evitar múltiplos pools.
    """
    DATABASE_URL = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        f"?client_encoding=utf8"
    )
    return create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)


# ============== MONGODB ==============

@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    """Retorna o cliente MongoDB (singleton)."""
    return MongoClient(settings.MONGO_URI)


def get_mongo_db():
    """Retorna o database MongoDB configurado."""
    return get_mongo_client()[settings.MONGO_DB]


def get_mongo_collection(nome: str = "partidas_estatisticas"):
    """
    Retorna uma collection do MongoDB garantindo que o índice em
    partida_id existe.

    BUG CORRIGIDO: ausência de índice em partida_id causava full
    collection scan em find_one({"partida_id": X}).
    """
    db = get_mongo_db()
    col = db[nome]
    # Cria índice único se ainda não existir (no-op se já existir)
    col.create_index([("partida_id", ASCENDING)], unique=True, background=True)
    return col


# ============== ASTRADB (CASSANDRA) ==============

def get_astra_session():
    """
    Conecta ao AstraDB usando Secure Connect Bundle e Token JSON.
    Não é cacheado aqui — o singleton fica em dependencies.py para
    permitir reset controlado.
    """
    with open(settings.ASTRA_DB_TOKEN_PATH) as f:
        secrets = json.load(f)

    cloud_config = {"secure_connect_bundle": settings.ASTRA_DB_SECURE_BUNDLE_PATH}
    auth_provider = PlainTextAuthProvider(secrets["clientId"], secrets["secret"])

    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect()
    session.set_keyspace(settings.ASTRA_DB_KEYSPACE)
    return session


# ============== TESTES DE CONEXÃO ==============

def test_postgres_connection() -> bool:
    try:
        engine = get_postgres_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT current_database(), current_user;"))
            db_name, user = result.fetchone()
            print(f"   PostgreSQL OK — db={db_name} user={user}")
        return True
    except Exception as e:
        print(f"   PostgreSQL ERRO: {e}")
        return False


def test_mongo_connection() -> bool:
    try:
        client = get_mongo_client()
        client.admin.command("ping")
        info = client.server_info()
        print(f"   MongoDB OK — versão {info['version']}")
        return True
    except Exception as e:
        print(f"   MongoDB ERRO: {e}")
        return False


def test_astra_connection() -> bool:
    try:
        session = get_astra_session()
        row = session.execute("SELECT release_version FROM system.local").one()
        print(f"   AstraDB OK — Cassandra {row.release_version}")
        session.cluster.shutdown()
        return True
    except Exception as e:
        print(f"   AstraDB ERRO: {e}")
        return False


def test_all_connections() -> bool:
    print("=" * 60)
    print("TESTANDO CONEXÕES")
    print("=" * 60)
    results = {
        "PostgreSQL": test_postgres_connection(),
        "MongoDB": test_mongo_connection(),
        "AstraDB": test_astra_connection(),
    }
    print("=" * 60)
    for db, ok in results.items():
        print(f"  {'OK' if ok else 'FALHOU':6}  {db}")
    return all(results.values())


if __name__ == "__main__":
    test_all_connections()