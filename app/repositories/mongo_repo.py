"""
Repository MongoDB
Camada de acesso a dados para estatísticas de partidas.
Implementa CRUD completo na collection partidas_estatisticas.
"""

from pymongo.collection import Collection
from typing import Optional, List

from app.schemas.inputs import EstatisticasPartidaCreate


# ─── READ ──────────────────────────────────────────────────────────────────────

def get_estatisticas_partida(collection: Collection, partida_id: int) -> Optional[dict]:
    doc = collection.find_one({"partida_id": partida_id}, {"_id": 0})
    return doc


def get_estatisticas_multiplas(
    collection: Collection,
    partida_ids: List[int],
) -> List[dict]:
    return list(collection.find(
        {"partida_id": {"$in": partida_ids}},
        {"_id": 0}
    ))


def get_media_estatisticas_clube(
    collection: Collection,
    nome_clube: str,
    ano: Optional[int] = None,
) -> dict:
    """Retorna médias de estatísticas de um clube (mandante e visitante)."""

    # Filtro por ano via partida_ids pode ser passado pelo router quando necessário
    match_mandante: dict = {"mandante.nome": nome_clube}
    match_visitante: dict = {"visitante.nome": nome_clube}

    pipeline_mandante = [
        {"$match": match_mandante},
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
        {"$match": match_visitante},
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

    res_m = list(collection.aggregate(pipeline_mandante))
    res_v = list(collection.aggregate(pipeline_visitante))

    def arredondar(d: dict) -> dict:
        return {k: round(v, 2) if isinstance(v, float) else v
                for k, v in d.items() if k != "_id"}

    return {
        "clube": nome_clube,
        "como_mandante": arredondar(res_m[0]) if res_m else {},
        "como_visitante": arredondar(res_v[0]) if res_v else {},
    }


def get_confronto_direto_stats(
    collection: Collection,
    clube1: str,
    clube2: str,
) -> List[dict]:
    return list(collection.find(
        {
            "$or": [
                {"mandante.nome": clube1, "visitante.nome": clube2},
                {"mandante.nome": clube2, "visitante.nome": clube1},
            ]
        },
        {"_id": 0}
    ).sort("partida_id", -1))


# ─── WRITE ─────────────────────────────────────────────────────────────────────

def create_estatisticas(
    collection: Collection,
    partida_id: int,
    dados: EstatisticasPartidaCreate,
) -> dict:
    """
    Insere estatísticas de uma partida no MongoDB.
    Levanta ValueError se já existir documento para o partida_id.
    """
    if collection.find_one({"partida_id": partida_id}):
        raise ValueError(f"Já existem estatísticas para a partida {partida_id}. Use PUT para atualizar.")

    documento = {
        "partida_id": partida_id,
        "rodada": dados.rodada,
        "mandante": {
            "nome": dados.mandante_nome,
            "estatisticas": dados.mandante_stats.model_dump(exclude_none=True),
        },
        "visitante": {
            "nome": dados.visitante_nome,
            "estatisticas": dados.visitante_stats.model_dump(exclude_none=True),
        },
    }

    collection.insert_one(documento)
    # Retorna sem o _id (não serializável por padrão)
    return collection.find_one({"partida_id": partida_id}, {"_id": 0})


def update_estatisticas(
    collection: Collection,
    partida_id: int,
    dados: EstatisticasPartidaCreate,
) -> Optional[dict]:
    """
    Substitui o documento de estatísticas de uma partida (replace_one).
    Retorna None se não existir.
    """
    existente = collection.find_one({"partida_id": partida_id})
    if not existente:
        return None

    novo_documento = {
        "partida_id": partida_id,
        "rodada": dados.rodada,
        "mandante": {
            "nome": dados.mandante_nome,
            "estatisticas": dados.mandante_stats.model_dump(exclude_none=True),
        },
        "visitante": {
            "nome": dados.visitante_nome,
            "estatisticas": dados.visitante_stats.model_dump(exclude_none=True),
        },
    }

    collection.replace_one({"partida_id": partida_id}, novo_documento)
    return collection.find_one({"partida_id": partida_id}, {"_id": 0})


def delete_estatisticas(collection: Collection, partida_id: int) -> bool:
    """
    Remove o documento de estatísticas de uma partida.
    Retorna True se removeu, False se não encontrou.
    """
    result = collection.delete_one({"partida_id": partida_id})
    return result.deleted_count > 0