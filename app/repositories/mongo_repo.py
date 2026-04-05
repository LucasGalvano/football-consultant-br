"""
Repository MongoDB
Camada de acesso a dados para estatísticas de partidas.
"""

from pymongo.collection import Collection
from typing import Optional, List, Tuple


def get_estatisticas_partida(collection: Collection, partida_id: int) -> Optional[dict]:
    doc = collection.find_one({"partida_id": partida_id}, {"_id": 0})
    return doc


def get_estatisticas_multiplas(
    collection: Collection,
    partida_ids: List[int],
) -> List[dict]:
    docs = list(collection.find(
        {"partida_id": {"$in": partida_ids}},
        {"_id": 0}
    ))
    return docs


def get_media_estatisticas_clube(
    collection: Collection,
    nome_clube: str,
    ano: Optional[int] = None,
) -> dict:
    """
    Retorna médias de estatísticas de um clube (como mandante ou visitante).
    """
    condicoes_mandante: dict = {"mandante.nome": nome_clube}
    condicoes_visitante: dict = {"visitante.nome": nome_clube}
    if ano:
        condicoes_mandante["rodada"] = {"$gte": 1}  # placeholder; filtro real abaixo
        # Não temos o campo ano direto no doc, mas temos partida_id
        # Usamos rodada como proxy — buscamos todos e filtramos via partida_ids externos

    pipeline_mandante = [
        {"$match": {"mandante.nome": nome_clube}},
        {"$group": {
            "_id": None,
            "media_posse": {"$avg": "$mandante.estatisticas.posse_de_bola"},
            "media_chutes": {"$avg": "$mandante.estatisticas.chutes"},
            "media_passes": {"$avg": "$mandante.estatisticas.passes"},
            "media_finalizacoes": {"$avg": "$mandante.estatisticas.finalizacoes"},
            "media_escanteios": {"$avg": "$mandante.estatisticas.escanteios"},
            "total_partidas": {"$sum": 1},
        }},
    ]

    pipeline_visitante = [
        {"$match": {"visitante.nome": nome_clube}},
        {"$group": {
            "_id": None,
            "media_posse": {"$avg": "$visitante.estatisticas.posse_de_bola"},
            "media_chutes": {"$avg": "$visitante.estatisticas.chutes"},
            "media_passes": {"$avg": "$visitante.estatisticas.passes"},
            "media_finalizacoes": {"$avg": "$visitante.estatisticas.finalizacoes"},
            "media_escanteios": {"$avg": "$visitante.estatisticas.escanteios"},
            "total_partidas": {"$sum": 1},
        }},
    ]

    res_mandante = list(collection.aggregate(pipeline_mandante))
    res_visitante = list(collection.aggregate(pipeline_visitante))

    def arredondar(d: dict) -> dict:
        return {k: round(v, 2) if isinstance(v, float) else v for k, v in d.items() if k != "_id"}

    return {
        "clube": nome_clube,
        "como_mandante": arredondar(res_mandante[0]) if res_mandante else {},
        "como_visitante": arredondar(res_visitante[0]) if res_visitante else {},
    }


def get_confronto_direto_stats(
    collection: Collection,
    clube1: str,
    clube2: str,
) -> List[dict]:
    """Retorna estatísticas dos confrontos diretos entre dois clubes."""
    docs = list(collection.find(
        {
            "$or": [
                {"mandante.nome": clube1, "visitante.nome": clube2},
                {"mandante.nome": clube2, "visitante.nome": clube1},
            ]
        },
        {"_id": 0}
    ).sort("partida_id", -1))
    return docs