"""
Script de Seed para PostgreSQL
===============================
Popula as tabelas: clubes, estadios, partidas

Entrada: data/processed/full-limpo.csv
Saida: 34 clubes, 74 estadios, 4.179 partidas

Uso:
    python scripts/3_seed_postgres.py
"""

import pandas as pd
import sys
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import get_postgres_engine
from app.models.postgres_models import Base, Clube, Estadio, Partida, criar_tabelas
from app.utils import obter_info_clube

print("=" * 80)
print("SEED POSTGRESQL - Clubes, Estadios, Partidas")
print("=" * 80)

ARQUIVO_CSV = Path(__file__).parent.parent / "data" / "processed" / "full-limpo.csv"

if not ARQUIVO_CSV.exists():
    print(f"ERRO: Arquivo nao encontrado: {ARQUIVO_CSV}")
    print("Execute primeiro: python scripts/1_clean_datasets.py")
    sys.exit(1)

print(f"\nCarregando: {ARQUIVO_CSV}")
df = pd.read_csv(ARQUIVO_CSV)
print(f"Total de partidas no CSV: {len(df)}")

engine = get_postgres_engine()

print("\nCriando tabelas (se nao existirem)...")
criar_tabelas(engine, reset = True)

Session = sessionmaker(bind=engine)
session = Session()

print("\nETAPA 1: Inserir Clubes")
print("=" * 80)

clubes_unicos = set(df['mandante'].unique()) | set(df['visitante'].unique())
clubes_unicos = sorted(clubes_unicos)

print(f"Total de clubes unicos: {len(clubes_unicos)}")

clubes_map = {}

for i, nome in enumerate(clubes_unicos, 1):
    info = obter_info_clube(nome)
    
    clube = Clube(
        nome_oficial=info['nome_oficial'],
        sigla=info['sigla'],
        estado=info['estado']
    )
    
    session.add(clube)
    session.flush()
    
    clubes_map[nome] = clube.id
    
    if i % 10 == 0 or i == len(clubes_unicos):
        print(f"  Processados: {i}/{len(clubes_unicos)}")

session.commit()
print(f"Clubes inseridos: {len(clubes_unicos)}")

print("\nETAPA 2: Inserir Estadios")
print("=" * 80)

estadios_unicos = sorted(df['arena'].unique())
print(f"Total de estadios unicos: {len(estadios_unicos)}")

estadios_map = {}

for i, nome in enumerate(estadios_unicos, 1):
    estadio = Estadio(nome=nome)
    session.add(estadio)
    session.flush()
    
    estadios_map[nome] = estadio.id
    
    if i % 20 == 0 or i == len(estadios_unicos):
        print(f"  Processados: {i}/{len(estadios_unicos)}")

session.commit()
print(f"Estadios inseridos: {len(estadios_unicos)}")

print("\nETAPA 3: Inserir Partidas")
print("=" * 80)

df['data'] = pd.to_datetime(df['data'])

total_partidas = len(df)
print(f"Total de partidas a inserir: {total_partidas}")

partidas_inseridas = 0
batch_size = 100

for idx, row in df.iterrows():
    mandante_id = clubes_map[row['mandante']]
    visitante_id = clubes_map[row['visitante']]
    estadio_id = estadios_map[row['arena']]
    
    vencedor_id = None
    if row['vencedor'] and row['vencedor'] != '-':
        vencedor_id = clubes_map.get(row['vencedor'])
    
    hora = None
    if pd.notna(row['hora']):
        try:
            hora = datetime.strptime(row['hora'], '%H:%M').time()
        except:
            pass
    
    partida = Partida(
        id=row['partida_id'],
        rodada=row['rodada'],
        data=row['data'].date(),
        hora=hora,
        mandante_id=mandante_id,
        visitante_id=visitante_id,
        vencedor_id=vencedor_id,
        estadio_id=estadio_id,
        placar_mandante=row['mandante_Placar'],
        placar_visitante=row['visitante_Placar'],
        formacao_mandante=row['formacao_mandante'] if pd.notna(row['formacao_mandante']) else None,
        formacao_visitante=row['formacao_visitante'] if pd.notna(row['formacao_visitante']) else None,
        tecnico_mandante=row['tecnico_mandante'] if pd.notna(row['tecnico_mandante']) else None,
        tecnico_visitante=row['tecnico_visitante'] if pd.notna(row['tecnico_visitante']) else None
    )
    
    session.add(partida)
    partidas_inseridas += 1
    
    if partidas_inseridas % batch_size == 0:
        session.commit()
        print(f"  Processadas: {partidas_inseridas}/{total_partidas}")

session.commit()
print(f"Partidas inseridas: {partidas_inseridas}")

print("\nRESUMO FINAL")
print("=" * 80)

count_clubes = session.query(Clube).count()
count_estadios = session.query(Estadio).count()
count_partidas = session.query(Partida).count()

print(f"Clubes no banco: {count_clubes}")
print(f"Estadios no banco: {count_estadios}")
print(f"Partidas no banco: {count_partidas}")

session.close()

print("\n" + "=" * 80)
print("SEED POSTGRESQL CONCLUIDO COM SUCESSO")
print("=" * 80)
print("\nProximo passo: python scripts/4_seed_mongo.py")