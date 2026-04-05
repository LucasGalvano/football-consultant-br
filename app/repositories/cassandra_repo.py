"""
Repository Cassandra / AstraDB
Camada de acesso a dados para gols e cartões.
"""

from cassandra.cluster import Session as CassandraSession
from typing import Optional, List


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
    """
    Retorna artilheiros calculando via ALLOW FILTERING ou por lista de partidas.
    Atenção: query pode ser lenta para grandes volumes.
    """
    if partida_ids:
        # Busca gols apenas das partidas do período desejado
        from collections import Counter
        contagem: Counter = Counter()
        clube_atleta: dict = {}

        for pid in partida_ids:
            rows = session.execute(
                "SELECT atleta, clube, tipo_gol FROM gols_por_partida WHERE partida_id = %s",
                (pid,),
            )
            for r in rows:
                if r.tipo_gol != "Gol Contra":  # Não conta gol contra
                    chave = (r.atleta, r.clube)
                    contagem[chave] += 1

        resultado = [
            {"atleta": k[0], "clube": k[1], "total_gols": v}
            for k, v in contagem.most_common(limite)
        ]
        return resultado

    # Sem filtro de partidas — usa ALLOW FILTERING (lento)
    rows = session.execute(
        "SELECT atleta, clube, tipo_gol FROM gols_por_partida ALLOW FILTERING LIMIT 50000"
    )
    from collections import Counter
    contagem: Counter = Counter()
    for r in rows:
        if r.tipo_gol != "Gol Contra":
            chave = (r.atleta, r.clube)
            contagem[chave] += 1

    return [
        {"atleta": k[0], "clube": k[1], "total_gols": v}
        for k, v in contagem.most_common(limite)
    ]


def get_gols_clube_partidas(
    session: CassandraSession,
    clube: str,
    partida_ids: List[int],
) -> List[dict]:
    """Gols de um clube específico em uma lista de partidas."""
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
    tipo: Optional[str] = None,  # "Amarelo" | "Vermelho" | None
) -> List[dict]:
    from collections import defaultdict

    contagem: dict = defaultdict(lambda: {"amarelos": 0, "vermelhos": 0, "clube": ""})

    ids_para_buscar = partida_ids or []
    if not ids_para_buscar:
        rows = session.execute(
            "SELECT partida_id, atleta, tipo_cartao, clube "
            "FROM cartoes_por_partida ALLOW FILTERING LIMIT 100000"
        )
        for r in rows:
            contagem[r.atleta]["clube"] = r.clube
            if r.tipo_cartao == "Amarelo":
                contagem[r.atleta]["amarelos"] += 1
            elif r.tipo_cartao == "Vermelho":
                contagem[r.atleta]["vermelhos"] += 1
    else:
        for pid in ids_para_buscar:
            rows = session.execute(
                "SELECT atleta, tipo_cartao, clube FROM cartoes_por_partida WHERE partida_id = %s",
                (pid,),
            )
            for r in rows:
                contagem[r.atleta]["clube"] = r.clube
                if r.tipo_cartao == "Amarelo":
                    contagem[r.atleta]["amarelos"] += 1
                elif r.tipo_cartao == "Vermelho":
                    contagem[r.atleta]["vermelhos"] += 1

    resultado = [
        {
            "atleta": atleta,
            "clube": dados["clube"],
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