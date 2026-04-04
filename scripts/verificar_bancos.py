"""
Script de Verificação dos Bancos de Dados
==========================================
Verifica integridade e contagens em todos os bancos:
- PostgreSQL: clubes, estadios, partidas
- MongoDB: partidas_estatisticas
- Cassandra/AstraDB: gols_por_partida, cartoes_por_partida

Uso:
    python scripts/verificar_bancos.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

ESPERADO = {
    "clubes":                34,
    "estadios":              74,
    "partidas":            4179,
    "partidas_estatisticas": 3799,
    "gols":                9861,
    "cartoes":            20953,
}

resultados = {}

def status(label, encontrado, esperado):
    ok = encontrado == esperado
    mensagem = "Banco OK" if ok else "Erro no banco"
    print(f"  {mensagem} {label}: {encontrado} (esperado: {esperado})")
    return ok


print("=" * 80)
print("VERIFICAÇÃO DOS BANCOS DE DADOS")
print("=" * 80)


#  PostgreSQL 
print("\n[1/3] PostgreSQL")
print("-" * 40)
try:
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import desc
    from app.config.database import get_postgres_engine
    from app.models.postgres_models import Clube, Estadio, Partida

    engine = get_postgres_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    n_clubes   = session.query(Clube).count()
    n_estadios = session.query(Estadio).count()
    n_partidas = session.query(Partida).count()

    ok_c = status("Clubes",   n_clubes,   ESPERADO["clubes"])
    ok_e = status("Estádios", n_estadios, ESPERADO["estadios"])
    ok_p = status("Partidas", n_partidas, ESPERADO["partidas"])

    primeiro_clube = session.query(Clube).first()
    if primeiro_clube:
        print(f"\nAmostra — primeiro clube: {primeiro_clube.nome_oficial} ({primeiro_clube.sigla}) [{primeiro_clube.estado}]")

    ultima = session.query(Partida).order_by(desc(Partida.data)).first()
    if ultima:
        print(f"Amostra — última partida: ID {ultima.id} em {ultima.data}")

    resultados["postgres"] = ok_c and ok_e and ok_p
    session.close()

except Exception as e:
    print(f"Erro ao conectar ao PostgreSQL: {e}")
    resultados["postgres"] = False


# MongoDB 
print("\n[2/3] MongoDB")
print("-" * 40)
try:
    from app.config.database import get_mongo_db

    db = get_mongo_db()
    collection = db["partidas_estatisticas"]

    n_docs = collection.count_documents({})
    ok_m = status("Documentos", n_docs, ESPERADO["partidas_estatisticas"])

    amostra = collection.find_one()
    if amostra:
        print(f"\n  Amostra — partida ID {amostra['partida_id']}:")
        print(f"    Mandante:  {amostra['mandante']['nome']}")
        print(f"    Visitante: {amostra['visitante']['nome']}")
        print(f"    Stats:     {list(amostra['mandante']['estatisticas'].keys())}")

    anos = collection.distinct("rodada")
    print(f"  Rodadas cobertas: {min(anos)} a {max(anos)}")

    resultados["mongo"] = ok_m

except Exception as e:
    print(f"Erro ao conectar ao MongoDB: {e}")
    resultados["mongo"] = False


# Cassandra / AstraDB 
print("\n[3/3] Cassandra / AstraDB")
print("-" * 40)
try:
    from app.config.database import get_astra_session

    session = get_astra_session()

    try:
        n_gols = session.execute("SELECT COUNT(*) FROM gols_por_partida").one()[0]
        ok_g = status("Gols", n_gols, ESPERADO["gols"])
        resultados_cassandra_gols = ok_g
    except Exception as e:
        print(f"   Gols COUNT falhou: {e}")
        resultados_cassandra_gols = False

    try:
        n_cartoes = session.execute("SELECT COUNT(*) FROM cartoes_por_partida").one()[0]
        ok_cart = status("Cartões", n_cartoes, ESPERADO["cartoes"])
        resultados_cassandra_cartoes = ok_cart
    except Exception as e:
        print(f"Cartões COUNT falhou: {e}")
        resultados_cassandra_cartoes = False

    # Amostra leve
    amostra_gol = list(session.execute(
        "SELECT * FROM gols_por_partida WHERE partida_id = 7034 LIMIT 3"
    ))
    if amostra_gol:
        print(f"\n  Amostra — gols da partida 7034:")
        for r in amostra_gol:
            print(f"{r.atleta} ({r.clube}) — min {r.minuto}")

    resultados["cassandra"] = resultados_cassandra_gols and resultados_cassandra_cartoes
    session.cluster.shutdown()

except Exception as e:
    print(f"Erro ao conectar ao Cassandra: {e}")
    resultados["cassandra"] = False


# Resumo Final 
print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)

todos_ok = all(resultados.values())

for banco, ok in resultados.items():
    mensagem = "Banco OK" if ok else "Erro no banco"
    print(f"  {mensagem} {banco.upper()}")

print()
if todos_ok:
    print("Todos os bancos verificados com sucesso!")
else:
    falhos = [b for b, ok in resultados.items() if not ok]
    print(f" Bancos com problema: {', '.join(falhos)}")

print("=" * 80)