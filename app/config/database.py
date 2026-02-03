import json
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pymongo import MongoClient
from app.config.settings import settings

# ============== POSTGRESQL ==============
def get_postgres_engine():
    DATABASE_URL = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    engine = create_engine(DATABASE_URL, echo=False)
    return engine

def get_postgres_engine():
    DATABASE_URL = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
        f"?client_encoding=utf8"
    )
    engine = create_engine(DATABASE_URL, echo=False)
    return engine


# ============== MONGODB ==============
def get_mongo_client():
    client = MongoClient(settings.MONGO_URI)
    return client

def get_mongo_db():
    client = get_mongo_client()
    return client[settings.MONGO_DB]


# ============== ASTRADB (CASSANDRA) ==============
def get_astra_session():
    """Conecta ao AstraDB usando Secure Connect Bundle e Token JSON"""
    
    # Carregar credenciais do JSON
    with open(settings.ASTRA_DB_TOKEN_PATH) as f:
        secrets = json.load(f)
    
    CLIENT_ID = secrets["clientId"]
    CLIENT_SECRET = secrets["secret"]
    
    # Configurar conexão
    cloud_config = {
        'secure_connect_bundle': settings.ASTRA_DB_SECURE_BUNDLE_PATH
    }
    
    auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
    
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
    session = cluster.connect()
    session.set_keyspace(settings.ASTRA_DB_KEYSPACE)
    
    return session


# ============== TESTE DE CONEXÕES ==============
def test_postgres_connection():
    """Testa conexão com PostgreSQL"""
    try:
        engine = get_postgres_engine()
        with engine.connect() as conn:
            # Apenas testa se consegue executar uma query
            result = conn.execute(text("SELECT current_database(), current_user;"))
            db_name, user = result.fetchone()
            
            print(f"   PostgreSQL conectado!")
            print(f"   Database: {db_name}")
            print(f"   Usuário: {user}")
            print(f"   Host: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
            
            return True
    except Exception as e:
        print(f"Erro ao conectar no PostgreSQL: {e}")
        return False


def test_mongo_connection():
    """Testa conexão com MongoDB"""
    try:
        client = get_mongo_client()
        # Testa a conexão
        client.admin.command('ping')
        
        # Pega informações do servidor
        server_info = client.server_info()
        print(f"   MongoDB conectado!")
        print(f"   Versão: {server_info['version']}")
        
        # Lista databases
        dbs = client.list_database_names()
        print(f"   Databases disponíveis: {dbs}")
        
        client.close()
        return True
    except Exception as e:
        print(f"Erro ao conectar no MongoDB: {e}")
        return False


def test_astra_connection():
    """Testa conexão com AstraDB"""
    try:
        session = get_astra_session()
        
        # Testa query simples
        row = session.execute("SELECT release_version FROM system.local").one()
        print(f"   AstraDB conectado!")
        print(f"   Versão do Cassandra: {row.release_version}")
        print(f"   Keyspace: {settings.ASTRA_DB_KEYSPACE}")
        
        # Lista tabelas do keyspace
        tables_query = f"""
            SELECT table_name 
            FROM system_schema.tables 
            WHERE keyspace_name = '{settings.ASTRA_DB_KEYSPACE}'
        """
        tables = session.execute(tables_query)
        table_names = [row.table_name for row in tables]
        
        if table_names:
            print(f"   Tabelas existentes: {table_names}")
        else:
            print(f"   Nenhuma tabela criada ainda no keyspace.")
        
        session.cluster.shutdown()
        return True
    except Exception as e:
        print(f"Erro ao conectar no AstraDB: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_connections():
    """Testa todas as conexões"""
    print("=" * 60)
    print("TESTANDO CONEXÕES COM OS BANCOS DE DADOS")
    print("=" * 60)
    print()
    
    results = {
        "PostgreSQL": test_postgres_connection(),
        "MongoDB": test_mongo_connection(),
        "AstraDB": test_astra_connection()
    }
    
    print()
    print("=" * 60)
    print("RESUMO DOS TESTES")
    print("=" * 60)
    
    for db, success in results.items():
        status = " OK" if success else "FALHOU"
        print(f"{db:15} {status}")
    
    all_ok = all(results.values())
    print()
    if all_ok:
        print("Todos os bancos estão conectados corretamente!")
    else:
        print("Alguns bancos apresentaram problemas de conexão.")
    
    return all_ok


# ============== EXECUÇÃO DIRETA ==============
if __name__ == "__main__":
    test_all_connections()