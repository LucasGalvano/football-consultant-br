"""
Repository Cassandra / AstraDB
CRUD completo para gols_por_partida e cartoes_por_partida.

BUGS CORRIGIDOS:
- get_artilheiros e get_ranking_cartoes sem partida_ids usavam
  ALLOW FILTERING (full cluster scan em todo o cluster).
  Agora a função retorna lista vazia se partida_ids não for passado —
  o router é responsável por sempre fornecer a lista vinda do Postgres.

WRITES ADICIONADOS:
- create_gol / delete_gol / delete_gols_partida
- create_cartao / delete_cartoes_partida
"""

from cassandra.cluster import Session as CassandraSession
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from app.schemas.inputs import GolCreate, CartaoCreate


# ════════════════════════════════════════════════════════
# HELPERS INTERNOS
# ════════════════════════════════════════════════════════

def _buscar_gols_partida(session: CassandraSession, partida_id: int) -> List:
    """Busca gols de uma partida pela partition key — sem ALLOW FILTERING."""
    rows = session.execute(
        "SELECT atleta, clube, tipo_gol "
        "FROM gols_por_partida WHERE partida_id = %s",
        (partida_id,),
    )
    return list(rows)


def _buscar_cartoes_partida(session: CassandraSession, partida_id: int) -> List:
    """Busca cartões de uma partida pela partition key — sem ALLOW FILTERING."""
    rows = session.execute(
        "SELECT atleta, tipo_cartao, clube "
        "FROM cartoes_por_partida WHERE partida_id = %s",
        (partida_id,),
    )
    return list(rows)


def _clube_principal(clubes_contagem: dict) -> str:
    """Retorna o clube onde o atleta teve mais registros no período."""
    if not clubes_contagem:
        return ""
    return max(clubes_contagem, key=clubes_contagem.get)


# ════════════════════════════════════════════════════════
# GOLS — READ
# ════════════════════════════════════════════════════════

def get_gols_partida(
    session: CassandraSession, partida_id: int
) -> List[dict]:
    """Retorna todos os gols de uma partida, ordenados por minuto."""
    rows = session.execute(
        "SELECT partida_id, minuto, atleta, clube, tipo_gol, rodada "
        "FROM gols_por_partida WHERE partida_id = %s",
        (partida_id,),
    )
    return [dict(r._asdict()) for r in rows]


def get_artilheiros(
    session: CassandraSession,
    limite: int = 10,
    partida_ids: Optional[List[int]] = None,
) -> List[dict]:
    """
    Retorna os artilheiros ordenados por total de gols.
    Gols contra são excluídos da contagem.

    IMPORTANTE: partida_ids deve sempre ser fornecido pelo router
    (obtido do PostgreSQL). Se vier vazio ou None, retorna lista vazia
    em vez de fazer ALLOW FILTERING no cluster inteiro.

    Usa ThreadPoolExecutor para buscar múltiplas partitions em paralelo.
    """
    if not partida_ids:
        return []

    contagem: dict = defaultdict(
        lambda: {"total_gols": 0, "clubes": defaultdict(int)}
    )

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(_buscar_gols_partida, session, pid): pid
            for pid in partida_ids
        }
        for future in as_completed(futures):
            try:
                for r in future.result():
                    if r.tipo_gol != "Gol Contra":
                        contagem[r.atleta]["total_gols"] += 1
                        contagem[r.atleta]["clubes"][r.clube] += 1
            except Exception:
                pass  # partition indisponível não derruba o resultado todo

    resultado = [
        {
            "atleta":     atleta,
            "clube":      _clube_principal(dados["clubes"]),
            "total_gols": dados["total_gols"],
        }
        for atleta, dados in contagem.items()
    ]
    resultado.sort(key=lambda x: -x["total_gols"])
    return resultado[:limite]


def get_gols_clube_partidas(
    session: CassandraSession,
    clube: str,
    partida_ids: List[int],
) -> List[dict]:
    """Retorna gols de um clube específico num conjunto de partidas."""
    resultado = []
    for pid in partida_ids:
        rows = session.execute(
            "SELECT partida_id, minuto, atleta, clube, tipo_gol, rodada "
            "FROM gols_por_partida WHERE partida_id = %s",
            (pid,),
        )
        for r in rows:
            if r.clube == clube:
                resultado.append(dict(r._asdict()))
    return resultado


# ════════════════════════════════════════════════════════
# CARTÕES — READ
# ════════════════════════════════════════════════════════

def get_cartoes_partida(
    session: CassandraSession, partida_id: int
) -> List[dict]:
    """Retorna todos os cartões de uma partida, ordenados por minuto."""
    rows = session.execute(
        "SELECT partida_id, minuto, atleta, tipo_cartao, clube, posicao, rodada "
        "FROM cartoes_por_partida WHERE partida_id = %s",
        (partida_id,),
    )
    return [dict(r._asdict()) for r in rows]


def get_ranking_cartoes(
    session: CassandraSession,
    limite: int = 10,
    partida_ids: Optional[List[int]] = None,
    tipo: Optional[str] = None,
) -> List[dict]:
    """
    Retorna ranking de jogadores por cartões.

    Mesmo comportamento de get_artilheiros: partida_ids vem do Postgres,
    nunca usa ALLOW FILTERING.

    tipo: "Amarelo", "Vermelho" ou None (ordena por total).
    """
    if not partida_ids:
        return []

    contagem: dict = defaultdict(
        lambda: {"amarelos": 0, "vermelhos": 0, "clubes": defaultdict(int)}
    )

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(_buscar_cartoes_partida, session, pid): pid
            for pid in partida_ids
        }
        for future in as_completed(futures):
            try:
                for r in future.result():
                    contagem[r.atleta]["clubes"][r.clube] += 1
                    if r.tipo_cartao == "Amarelo":
                        contagem[r.atleta]["amarelos"] += 1
                    elif r.tipo_cartao == "Vermelho":
                        contagem[r.atleta]["vermelhos"] += 1
            except Exception:
                pass

    resultado = [
        {
            "atleta":       atleta,
            "clube":        _clube_principal(dados["clubes"]),
            "amarelos":     dados["amarelos"],
            "vermelhos":    dados["vermelhos"],
            "total_cartoes": dados["amarelos"] + dados["vermelhos"],
        }
        for atleta, dados in contagem.items()
    ]

    if tipo == "Amarelo":
        resultado.sort(key=lambda x: -x["amarelos"])
    elif tipo == "Vermelho":
        resultado.sort(key=lambda x: -x["vermelhos"])
    else:
        resultado.sort(key=lambda x: -x["total_cartoes"])

    return resultado[:limite]


# ════════════════════════════════════════════════════════
# GOLS — WRITE
# ════════════════════════════════════════════════════════

def create_gol(
    session: CassandraSession,
    partida_id: int,
    dados: GolCreate,
) -> dict:
    """
    Insere um gol na tabela gols_por_partida.

    PRIMARY KEY: (partida_id, minuto, atleta)
    Se o mesmo atleta marcar dois gols no mesmo minuto, o segundo
    sobrescreve o primeiro (limitação do modelo; minutos de acréscimo
    já somados evitam a maioria dos casos — 45+2 → informe 47).
    """
    stmt = session.prepare(
        "INSERT INTO gols_por_partida "
        "(partida_id, minuto, atleta, clube, tipo_gol, rodada) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )
    session.execute(stmt, (
        partida_id,
        dados.minuto,
        dados.atleta,
        dados.clube,
        dados.tipo_gol,
        dados.rodada,
    ))
    return {
        "partida_id": partida_id,
        "minuto":     dados.minuto,
        "atleta":     dados.atleta,
        "clube":      dados.clube,
        "tipo_gol":   dados.tipo_gol,
        "rodada":     dados.rodada,
    }


def delete_gol(
    session: CassandraSession,
    partida_id: int,
    minuto: int,
    atleta: str,
) -> bool:
    """
    Remove um gol específico pela chave composta (partida_id, minuto, atleta).
    Retorna True se havia o registro, False se não existia.
    """
    # Verifica existência antes de deletar (Cassandra não retorna affected rows)
    existia = session.execute(
        "SELECT atleta FROM gols_por_partida "
        "WHERE partida_id = %s AND minuto = %s AND atleta = %s",
        (partida_id, minuto, atleta),
    ).one()

    if not existia:
        return False

    session.execute(
        "DELETE FROM gols_por_partida "
        "WHERE partida_id = %s AND minuto = %s AND atleta = %s",
        (partida_id, minuto, atleta),
    )
    return True


def delete_gols_partida(
    session: CassandraSession, partida_id: int
) -> int:
    """
    Remove TODOS os gols de uma partida (DELETE by partition key).
    Retorna a quantidade de gols removidos.
    Operação eficiente — bate em apenas uma partition.
    """
    existentes = get_gols_partida(session, partida_id)
    count = len(existentes)
    if count > 0:
        session.execute(
            "DELETE FROM gols_por_partida WHERE partida_id = %s",
            (partida_id,),
        )
    return count


# ════════════════════════════════════════════════════════
# CARTÕES — WRITE
# ════════════════════════════════════════════════════════

def create_cartao(
    session: CassandraSession,
    partida_id: int,
    dados: CartaoCreate,
) -> dict:
    """
    Insere um cartão na tabela cartoes_por_partida.

    PRIMARY KEY: (partida_id, minuto, atleta, tipo_cartao)
    Suporta o caso de um jogador receber amarelo e vermelho na mesma
    partida (tipo_cartao entra na chave).
    """
    stmt = session.prepare(
        "INSERT INTO cartoes_por_partida "
        "(partida_id, minuto, atleta, tipo_cartao, clube, posicao, rodada) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    session.execute(stmt, (
        partida_id,
        dados.minuto,
        dados.atleta,
        dados.tipo_cartao,
        dados.clube,
        dados.posicao,
        dados.rodada,
    ))
    return {
        "partida_id":  partida_id,
        "minuto":      dados.minuto,
        "atleta":      dados.atleta,
        "tipo_cartao": dados.tipo_cartao,
        "clube":       dados.clube,
        "posicao":     dados.posicao,
        "rodada":      dados.rodada,
    }


def delete_cartoes_partida(
    session: CassandraSession, partida_id: int
) -> int:
    """
    Remove TODOS os cartões de uma partida.
    Retorna a quantidade removida.
    """
    existentes = get_cartoes_partida(session, partida_id)
    count = len(existentes)
    if count > 0:
        session.execute(
            "DELETE FROM cartoes_por_partida WHERE partida_id = %s",
            (partida_id,),
        )
    return count