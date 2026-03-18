"""
Modelos CQL para Cassandra/AstraDB
===================================
Define as tabelas wide-column para armazenar eventos (gols e cartões).

Tabelas:
- gols_por_partida: Gols marcados em cada partida
- cartoes_por_partida: Cartões aplicados em cada partida

IMPORTANTE: Estas são statements CQL (Cassandra Query Language).
Execute-as no CQL Console do AstraDB ou via driver Python.
"""

# KEYSPACE (Namespace do Cassandra)

# No AstraDB, o keyspace já é criado automaticamente quando você cria o database.
# Se estivesse usando Cassandra local, precisaria criar assim:

CRIAR_KEYSPACE = """
CREATE KEYSPACE IF NOT EXISTS brasileirao
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};
"""

# Comentário: Em produção, usar 'NetworkTopologyStrategy' com RF >= 3


# TABELA 1: GOLS POR PARTIDA

CRIAR_TABELA_GOLS = """
CREATE TABLE IF NOT EXISTS gols_por_partida (
    partida_id INT,
    minuto INT,
    atleta TEXT,
    clube TEXT,
    tipo_gol TEXT,
    rodada INT,
    PRIMARY KEY (partida_id, minuto, atleta)
) WITH CLUSTERING ORDER BY (minuto ASC, atleta ASC)
  AND comment = 'Gols marcados em cada partida, ordenados por minuto';
"""

# Explicação da modelagem:
# 
# PARTITION KEY: partida_id
#   - Distribui dados entre nodes do cluster
#   - Query típica: "buscar todos os gols da partida X"
#   - Todos os gols de uma partida ficam no mesmo node (co-localização)
#
# CLUSTERING COLUMNS: minuto, atleta
#   - minuto: ordena gols cronologicamente (1', 15', 45+2', etc)
#   - atleta: desempate (se 2 gols no mesmo minuto)
#   - Dados já ficam ordenados fisicamente no disco
#
# VANTAGENS:
#   - Query "gols da partida X" é ultra rápida (1 partition key)
#   - Gols já vêm ordenados por minuto (sem ORDER BY)
#   - Ideal para timeline de gols


# Índice secundário (se necessário buscar por atleta)
CRIAR_INDICE_ATLETA_GOLS = """
CREATE INDEX IF NOT EXISTS idx_gols_atleta 
ON gols_por_partida (atleta);
"""

# Comentário: Use com cuidado! Índices secundários em Cassandra
# podem ter performance ruim. Melhor criar uma tabela separada
# se precisar buscar frequentemente por atleta.


# TABELA 2: CARTÕES POR PARTIDA

CRIAR_TABELA_CARTOES = """
CREATE TABLE IF NOT EXISTS cartoes_por_partida (
    partida_id INT,
    minuto INT,
    atleta TEXT,
    tipo_cartao TEXT,
    clube TEXT,
    posicao TEXT,
    rodada INT,
    PRIMARY KEY (partida_id, minuto, atleta, tipo_cartao)
) WITH CLUSTERING ORDER BY (minuto ASC, atleta ASC, tipo_cartao ASC)
  AND comment = 'Cartões aplicados em cada partida, ordenados por minuto';
"""

# Explicação:
#
# PARTITION KEY: partida_id
#   - Mesma lógica da tabela de gols
#   - Query: "cartões da partida X"
#
# CLUSTERING COLUMNS: minuto, atleta, tipo_cartao
#   - minuto: ordem cronológica
#   - atleta: desempate
#   - tipo_cartao: um atleta pode ter amarelo E vermelho
#   - Ex: Jogador leva amarelo no 45' e vermelho no 90'
#
# PRIMARY KEY completa garante unicidade:
#   - (partida 5000, min 45, Fagner, Amarelo) = 1 registro único


# TABELA 3 (OPCIONAL): ARTILHARIA POR TEMPORADA

# Esta tabela agregada facilita queries do tipo:
# "Quem foram os artilheiros do Flamengo em 2020?"

CRIAR_TABELA_ARTILHARIA = """
CREATE TABLE IF NOT EXISTS artilharia_temporada (
    ano INT,
    clube TEXT,
    atleta TEXT,
    total_gols COUNTER,
    PRIMARY KEY ((ano, clube), atleta)
) WITH CLUSTERING ORDER BY (atleta ASC)
  AND comment = 'Contagem de gols por atleta, clube e temporada';
"""

# Explicação:
#
# PARTITION KEY: (ano, clube) - compound key
#   - Distribui por ano + clube
#   - Query: "artilheiros do Flamengo em 2020"
#   - Uma partition = todos os artilheiros de um clube num ano
#
# CLUSTERING COLUMN: atleta
#   - Ordena alfabeticamente dentro da partition
#
# COUNTER:
#   - Tipo especial do Cassandra para incrementos
#   - UPDATE artilharia_temporada SET total_gols = total_gols + 1
#   - Não precisa ler antes de escrever


# QUERIES DE EXEMPLO

# Query 1: Buscar todos os gols de uma partida
QUERY_GOLS_PARTIDA = """
SELECT atleta, clube, minuto, tipo_gol
FROM gols_por_partida
WHERE partida_id = ?
ORDER BY minuto ASC;
"""

# Query 2: Buscar cartões de uma partida
QUERY_CARTOES_PARTIDA = """
SELECT atleta, clube, tipo_cartao, minuto
FROM cartoes_por_partida
WHERE partida_id = ?
ORDER BY minuto ASC;
"""

# Query 3: Artilheiros de um clube em uma temporada
QUERY_ARTILHEIROS = """
SELECT atleta, total_gols
FROM artilharia_temporada
WHERE ano = ? AND clube = ?
ORDER BY total_gols DESC;
"""

# Query 4: Gols de um atleta específico (requer índice)
QUERY_GOLS_ATLETA = """
SELECT partida_id, minuto, clube, tipo_gol
FROM gols_por_partida
WHERE atleta = ?
ALLOW FILTERING;
"""
# ATENÇÃO: ALLOW FILTERING é lento! Use apenas em consultas eventuais.


# FUNÇÃO AUXILIAR: EXECUTAR TODOS OS CREATES

def criar_tabelas_cassandra(session):
    """
    Cria todas as tabelas no Cassandra/AstraDB.
    
    Args:
        session: Cassandra session conectada ao keyspace
    """
    statements = [
        ("Tabela gols_por_partida", CRIAR_TABELA_GOLS),
        ("Tabela cartoes_por_partida", CRIAR_TABELA_CARTOES),
        ("Tabela artilharia_temporada", CRIAR_TABELA_ARTILHARIA),
        ("Índice atleta em gols", CRIAR_INDICE_ATLETA_GOLS),
    ]
    
    print("Criando tabelas no Cassandra/AstraDB...")
    
    for nome, statement in statements:
        try:
            session.execute(statement)
            print(f"{nome}")
        except Exception as e:
            print(f"{nome}: {e}")
    
    print(" Processo concluído!")


def listar_tabelas(session):
    """
    Lista todas as tabelas do keyspace atual.
    
    Args:
        session: Cassandra session conectada
    """
    keyspace = session.keyspace
    
    query = """
    SELECT table_name 
    FROM system_schema.tables 
    WHERE keyspace_name = %s
    """
    
    rows = session.execute(query, [keyspace])
    
    print(f"\nTabelas no keyspace '{keyspace}':")
    for row in rows:
        print(f"   - {row.table_name}")


# TESTE (executar apenas se rodar diretamente)

if __name__ == "__main__":
    from cassandra.cluster import Cluster
    from cassandra.auth import PlainTextAuthProvider
    from app.config.settings import settings
    import json
    
    print("=" * 80)
    print("TESTE DOS MODELOS CASSANDRA")
    print("=" * 80)
    
    try:
        # Conectar ao AstraDB
        print("\n🔌 Conectando ao AstraDB...")
        
        with open(settings.ASTRA_DB_TOKEN_PATH) as f:
            secrets = json.load(f)
        
        cloud_config = {
            'secure_connect_bundle': settings.ASTRA_DB_SECURE_BUNDLE_PATH
        }
        
        auth_provider = PlainTextAuthProvider(
            secrets["clientId"],
            secrets["secret"]
        )
        
        cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider)
        session = cluster.connect()
        session.set_keyspace(settings.ASTRA_DB_KEYSPACE)
        
        print(f" Conectado ao keyspace: {settings.ASTRA_DB_KEYSPACE}")
        
        # Criar tabelas
        criar_tabelas_cassandra(session)
        
        # Listar tabelas criadas
        listar_tabelas(session)
        
        # Fechar conexão
        cluster.shutdown()
        
        print("\n" + "=" * 80)
        print("Modelos prontos para uso!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n Erro: {e}")
        import traceback
        traceback.print_exc()
