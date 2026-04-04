"""
Script de Seed para MongoDB
============================
Popula collection: partidas_estatisticas

Entrada: data/processed/estatisticas-limpo.csv
Saida: 3.799 documentos (partidas com estatisticas)

Uso:
    python scripts/4_seed_mongo.py
"""

import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import get_mongo_db

print("=" * 80)
print("SEED MONGODB - Partidas com Estatisticas")
print("=" * 80)

ARQUIVO_CSV = Path(__file__).parent.parent / "data" / "processed" / "estatisticas-limpo.csv"

if not ARQUIVO_CSV.exists():
    print(f"ERRO: Arquivo nao encontrado: {ARQUIVO_CSV}")
    print("Execute primeiro: python scripts/1_clean_datasets.py")
    sys.exit(1)

print(f"\nCarregando: {ARQUIVO_CSV}")
df = pd.read_csv(ARQUIVO_CSV)
print(f"Total de registros no CSV: {len(df)}")
print(f"Total de partidas unicas: {df['partida_id'].nunique()}")

db = get_mongo_db()
collection = db['partidas_estatisticas']

print("\nLimpando collection anterior (se existir)...")
collection.delete_many({})

print("\nETAPA 1: Agrupar linhas por partida_id")
print("=" * 80)

grupos = df.groupby('partida_id')
total_partidas = len(grupos)
print(f"Total de partidas a processar: {total_partidas}")

def criar_stats(linha):
    colunas_stats = [
        'chutes', 'chutes_no_alvo', 'posse_de_bola',
        'passes', 'precisao_passes', 'faltas',
        'cartao_amarelo', 'cartao_vermelho',
        'impedimentos', 'escanteios'
    ]
    stats = {}
    for col in colunas_stats:
        if col in linha and pd.notna(linha[col]):
            val = linha[col]
            # Converte numpy para tipo Python nativo
            if hasattr(val, 'item'):
                val = val.item()
            stats[col] = val
    return stats


documentos_inseridos = 0
batch = []
batch_size = 100

for partida_id, grupo in grupos:
    if len(grupo) != 2:
        print(f"  AVISO: Partida {partida_id} tem {len(grupo)} linhas (esperado: 2)")
        continue

    linha_mandante = grupo.iloc[0]
    linha_visitante = grupo.iloc[1]

    documento = {
        "partida_id": int(partida_id),
        "rodada": int(linha_mandante['rodada']),
        "mandante": {
            "nome": linha_mandante['clube'],
            "estatisticas": criar_stats(linha_mandante)
        },
        "visitante": {
            "nome": linha_visitante['clube'],
            "estatisticas": criar_stats(linha_visitante)
        }
    }

    batch.append(documento)
    documentos_inseridos += 1

    if len(batch) >= batch_size:
        collection.insert_many(batch)
        batch = []
        print(f"  Processadas: {documentos_inseridos}/{total_partidas}")

if batch:
    collection.insert_many(batch)

print(f"Documentos inseridos: {documentos_inseridos}")

print("\nRESUMO FINAL")
print("=" * 80)

count_docs = collection.count_documents({})
print(f"Documentos no banco: {count_docs}")

amostra = collection.find_one()
if amostra:
    print(f"\nExemplo de documento:")
    print(f"  Partida ID: {amostra['partida_id']}")
    print(f"  Rodada:     {amostra['rodada']}")
    print(f"  Mandante:   {amostra['mandante']['nome']}")
    print(f"  Visitante:  {amostra['visitante']['nome']}")
    print(f"  Stats:      {list(amostra['mandante']['estatisticas'].keys())}")

print("\n" + "=" * 80)
print("SEED MONGODB CONCLUIDO COM SUCESSO")
print("=" * 80)
print("\nProximo passo: python scripts/5_seed_cassandra.py")