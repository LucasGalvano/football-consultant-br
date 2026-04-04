"""
Script de Seed para Cassandra/AstraDB
======================================
Popula tabelas: gols_por_partida, cartoes_por_partida

Entrada: data/processed/gols-limpo.csv, data/processed/cartoes-limpo.csv
Saida: 9.861 gols, 20.953 cartoes

Uso:
    python scripts/5_seed_cassandra.py
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import get_astra_session
from app.models.cassandra_models import criar_tabelas_cassandra

print("=" * 80)
print("SEED CASSANDRA - Gols e Cartoes")
print("=" * 80)

ARQUIVO_GOLS = Path("data/processed/gols-limpo.csv")
ARQUIVO_CARTOES = Path("data/processed/cartoes-limpo.csv")

if not ARQUIVO_GOLS.exists():
    print(f"ERRO: Arquivo nao encontrado: {ARQUIVO_GOLS}")
    print("Execute primeiro: python scripts/1_clean_datasets.py")
    sys.exit(1)

if not ARQUIVO_CARTOES.exists():
    print(f"ERRO: Arquivo nao encontrado: {ARQUIVO_CARTOES}")
    print("Execute primeiro: python scripts/1_clean_datasets.py")
    sys.exit(1)

print("\nConectando ao AstraDB...")
session = get_astra_session()
print("Conectado com sucesso!")

print("\nCriando tabelas (se nao existirem)...")
criar_tabelas_cassandra(session)

print("\nETAPA 1: Inserir Gols")
print("=" * 80)

print(f"Carregando: {ARQUIVO_GOLS}")
df_gols = pd.read_csv(ARQUIVO_GOLS)
print(f"Total de gols no CSV: {len(df_gols)}")

insert_gol = session.prepare("""
    INSERT INTO gols_por_partida 
    (partida_id, minuto, atleta, clube, tipo_gol, rodada)
    VALUES (?, ?, ?, ?, ?, ?)
""")

gols_inseridos = 0
batch_size = 50

for idx, row in df_gols.iterrows():
    minuto = row['minuto_numerico'] if pd.notna(row['minuto_numerico']) else 0
    tipo_gol = row['tipo_de_gol'] if pd.notna(row['tipo_de_gol']) else None
    
    session.execute(insert_gol, (
        int(row['partida_id']),
        int(minuto),
        str(row['atleta']),
        str(row['clube']),
        tipo_gol,
        int(row['rodada'])
    ))
    
    gols_inseridos += 1
    
    if gols_inseridos % batch_size == 0:
        print(f"  Processados: {gols_inseridos}/{len(df_gols)}")

print(f"Gols inseridos: {gols_inseridos}")

print("\nETAPA 2: Inserir Cartoes")
print("=" * 80)

print(f"Carregando: {ARQUIVO_CARTOES}")
df_cartoes = pd.read_csv(ARQUIVO_CARTOES)
print(f"Total de cartoes no CSV: {len(df_cartoes)}")

insert_cartao = session.prepare("""
    INSERT INTO cartoes_por_partida 
    (partida_id, minuto, atleta, tipo_cartao, clube, posicao, rodada)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""")

cartoes_inseridos = 0

for idx, row in df_cartoes.iterrows():
    minuto = row['minuto_numerico'] if pd.notna(row['minuto_numerico']) else 0
    posicao = row['posicao'] if pd.notna(row['posicao']) else None
    
    session.execute(insert_cartao, (
        int(row['partida_id']),
        int(minuto),
        str(row['atleta']),
        str(row['cartao']),
        str(row['clube']),
        posicao,
        int(row['rodada'])
    ))
    
    cartoes_inseridos += 1
    
    if cartoes_inseridos % batch_size == 0:
        print(f"  Processados: {cartoes_inseridos}/{len(df_cartoes)}")

print(f"Cartoes inseridos: {cartoes_inseridos}")

print("\nRESUMO FINAL")
print("=" * 80)

try:
    count_gols = session.execute("SELECT COUNT(*) FROM gols_por_partida").one()[0]
    print(f"Gols no banco: {count_gols}")
except:
    print("Gols no banco: (nao suportado pelo Cassandra)")

try:
    count_cartoes = session.execute("SELECT COUNT(*) FROM cartoes_por_partida").one()[0]
    print(f"Cartoes no banco: {count_cartoes}")
except:
    print("Cartoes no banco: (nao suportado pelo Cassandra)")

print("\nExemplo de query:")
print("SELECT * FROM gols_por_partida WHERE partida_id = 5000;")

session.cluster.shutdown()

print("\n" + "=" * 80)
print("SEED CASSANDRA CONCLUIDO COM SUCESSO")
print("=" * 80)
print("\nTodos os bancos foram populados com sucesso!")
print("Execute: python scripts/verificar_bancos.py")