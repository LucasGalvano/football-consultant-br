"""
Repository Cassandra / AstraDB
Camada de acesso a dados para gols e cartões.

CORREÇÕES:
- get_artilheiros e get_ranking_cartoes sem partida_ids usavam
  ALLOW FILTERING (full cluster scan). Agora exigem partida_ids obrigatório
  quando chamados sem filtro de ano; o router passa todos os IDs do Postgres.
- Adicionados: create_gol, delete_gols_partida, create_cartao, delete_cartoes_partida.
"""

from cassandra.cluster import Session as CassandraSession
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from app.schemas.inputs import GolCreate, CartaoCreate


# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _buscar_gols_partida(session: CassandraSession, partida_id: int) -> List:
    rows = session.execute(
        "SELECT atleta, clube, tipo_gol FROM gols_por_partida WHERE partida_id = %s",
        (partida_id,),
    )
    return list(rows)


def _buscar_cartoes_partida(session: CassandraSession, partida_id: int) -> List:
    rows = session.execute(
        "SELECT atleta, tipo_cartao, clube FROM cartoes_por_partida WHERE partida_id = %s",
        (partida_id,),
    )
    return list(rows)


def _clube_principal(clubes_contagem: dict) -> str:
    if not clubes_contagem:
        return ""
    return max(clubes_contagem, key=clubes_contagem.get)


# ─── GOLS — READ ──────────────────────────────────────────────────────────────

def get_gols_partida(session: CassandraSession, partida_id: int) -> List[dict]:
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
    Retorna os artilheiros ordenados por total de gols (excluindo gol contra).

    BUG CORRIGIDO: quando partida_ids=None, o código anterior usava
    ALLOW FILTERING (full cluster scan). Agora obrigamos o chamador a
    passar a lista de IDs (vinda do PostgreSQL), garantindo que cada
    query bata em apenas uma partition key.

    O router passa todos os IDs disponíveis quando não há filtro de ano.
    """
    if not partida_ids:
        return []

    contagem: dict = defaultdict(lambda: {"total_gols": 0, "clubes": defaultdict(int)})

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
                pass

    resultado = [
        {
            "atleta": atleta,
            "clube": _clube_principal(dados["clubes"]),
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


# ─── CARTÕES — READ ────────────────────────────────────────────────────────────

def get_cartoes_partida(session: CassandraSession, partida_id: int) -> List[dict]:
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
    BUG CORRIGIDO: mesma correção do get_artilheiros — sem ALLOW FILTERING.
    """
    if not partida_ids:
        return []

    contagem: dict = defaultdict(lambda: {"amarelos": 0, "vermelhos": 0, "clubes": defaultdict(int)})

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
            "atleta": atleta,
            "clube": _clube_principal(dados["clubes"]),
            "amarelos": dados["amarelos"],
            "vermelhos": dados["vermelhos"],
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


# ─── GOLS — WRITE ──────────────────────────────────────────────────────────────

def create_gol(
    session: CassandraSession,
    partida_id: int,
    dados: GolCreate,
) -> dict:
    """
    Insere um gol na tabela gols_por_partida.
    A PRIMARY KEY (partida_id, minuto, atleta) garante unicidade.
    Retorna o dict inserido.
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
        "minuto": dados.minuto,
        "atleta": dados.atleta,
        "clube": dados.clube,
        "tipo_gol": dados.tipo_gol,
        "rodada": dados.rodada,
    }


def delete_gols_partida(session: CassandraSession, partida_id: int) -> int:
    """
    Remove todos os gols de uma partida.
    Retorna o número de gols removidos (consultado antes do delete).
    Em Cassandra, DELETE by partition key é eficiente — não precisa de ALLOW FILTERING.
    """
    existentes = get_gols_partida(session, partida_id)
    count = len(existentes)

    if count > 0:
        session.execute(
            "DELETE FROM gols_por_partida WHERE partida_id = %s",
            (partida_id,),
        )
    return count


def delete_gol(
    session: CassandraSession,
    partida_id: int,
    minuto: int,
    atleta: str,
) -> bool:
    """
    Remove um gol específico pela chave composta completa.
    """
    session.execute(
        "DELETE FROM gols_por_partida WHERE partida_id = %s AND minuto = %s AND atleta = %s",
        (partida_id, minuto, atleta),
    )
    # Verifica se realmente existia
    verificacao = session.execute(
        "SELECT atleta FROM gols_por_partida WHERE partida_id = %s AND minuto = %s AND atleta = %s",
        (partida_id, minuto, atleta),
    ).one()
    return verificacao is None  # True = foi removido


# ─── CARTÕES — WRITE ───────────────────────────────────────────────────────────

def create_cartao(
    session: CassandraSession,
    partida_id: int,
    dados: CartaoCreate,
) -> dict:
    """
    Insere um cartão na tabela cartoes_por_partida.
    PRIMARY KEY: (partida_id, minuto, atleta, tipo_cartao).
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
        "partida_id": partida_id,
        "minuto": dados.minuto,
        "atleta": dados.atleta,
        "tipo_cartao": dados.tipo_cartao,
        "clube": dados.clube,
        "posicao": dados.posicao,
        "rodada": dados.rodada,
    }


def delete_cartoes_partida(session: CassandraSession, partida_id: int) -> int:
    """Remove todos os cartões de uma partida. Retorna quantidade removida."""
    existentes = get_cartoes_partida(session, partida_id)
    count = len(existentes)
    if count > 0:
        session.execute(
            "DELETE FROM cartoes_por_partida WHERE partida_id = %s",
            (partida_id,),
        )
    return count