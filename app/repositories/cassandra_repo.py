"""
Repository Cassandra / AstraDB
Camada de acesso a dados para gols e cartões.
"""

from cassandra.cluster import Session as CassandraSession
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict


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
    """Retorna o clube onde o atleta teve mais registros no período."""
    if not clubes_contagem:
        return ""
    return max(clubes_contagem, key=clubes_contagem.get)


# ─── GOLS ─────────────────────────────────────────────────────────────────────

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
    # atleta -> {total_gols, clubes: {clube: count}}
    contagem: dict = defaultdict(lambda: {"total_gols": 0, "clubes": defaultdict(int)})

    if partida_ids:
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
    else:
        rows = session.execute(
            "SELECT atleta, clube, tipo_gol FROM gols_por_partida ALLOW FILTERING"
        )
        for r in rows:
            if r.tipo_gol != "Gol Contra":
                contagem[r.atleta]["total_gols"] += 1
                contagem[r.atleta]["clubes"][r.clube] += 1

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


# ─── CARTÕES ──────────────────────────────────────────────────────────────────

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
    # atleta -> {amarelos, vermelhos, clubes: {clube: count}}
    contagem: dict = defaultdict(lambda: {"amarelos": 0, "vermelhos": 0, "clubes": defaultdict(int)})

    if partida_ids:
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
    else:
        rows = session.execute(
            "SELECT atleta, tipo_cartao, clube FROM cartoes_por_partida ALLOW FILTERING"
        )
        for r in rows:
            contagem[r.atleta]["clubes"][r.clube] += 1
            if r.tipo_cartao == "Amarelo":
                contagem[r.atleta]["amarelos"] += 1
            elif r.tipo_cartao == "Vermelho":
                contagem[r.atleta]["vermelhos"] += 1

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