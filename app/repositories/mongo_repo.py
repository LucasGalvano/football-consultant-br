"""
Repository MongoDB
CRUD completo para a collection partidas_estatisticas.

PROTEÇÃO HISTÓRICA:
  Operações de escrita (create, update, delete) são bloqueadas para
  partidas com ID <= 8785 (dataset CSV 2014–2024).
"""

from pymongo.collection import Collection
from typing import Optional, List

from app.schemas.inputs import EstatisticasPartidaCreate

ULTIMO_ID_HISTORICO = 8785


class HistoricalDataError(ValueError):
    """Lançada ao tentar modificar estatísticas de uma partida histórica."""
    pass


def _verificar_protecao_historica(partida_id: int, operacao: str = "modificar") -> None:
    if partida_id <= ULTIMO_ID_HISTORICO:
        raise HistoricalDataError(
            f"Não é permitido {operacao} dados históricos. "
            f"A partida {partida_id} faz parte do dataset oficial (2014–2024, "
            f"IDs até {ULTIMO_ID_HISTORICO}). "
            "Apenas partidas criadas via API (ID >= 9000) podem ser alteradas."
        )


# ════════════════════════════════════════════════════════
# READ
# ════════════════════════════════════════════════════════

def get_estatisticas_partida(
    collection: Collection, partida_id: int
) -> Optional[dict]:
    return collection.find_one({"partida_id": partida_id}, {"_id": 0})


def get_estatisticas_multiplas(
    collection: Collection, partida_ids: List[int]
) -> List[dict]:
    return list(
        collection.find(
            {"partida_id": {"$in": partida_ids}},
            {"_id": 0},
        )
    )


def get_media_estatisticas_clube(
    collection: Collection,
    nome_clube: str,
) -> dict:
    def _pipeline(lado: str) -> list:
        campo = f"{lado}.nome"
        prefixo = f"${lado}.estatisticas"
        return [
            {"$match": {campo: nome_clube}},
            {"$group": {
                "_id": None,
                "media_posse":        {"$avg": f"{prefixo}.posse_de_bola"},
                "media_chutes":       {"$avg": f"{prefixo}.chutes"},
                "media_passes":       {"$avg": f"{prefixo}.passes"},
                "media_finalizacoes": {"$avg": f"{prefixo}.finalizacoes"},
                "media_escanteios":   {"$avg": f"{prefixo}.escanteios"},
                "total_partidas":     {"$sum": 1},
            }},
        ]

    def _arredondar(d: dict) -> dict:
        return {
            k: round(v, 2) if isinstance(v, float) else v
            for k, v in d.items()
            if k != "_id"
        }

    res_mandante  = list(collection.aggregate(_pipeline("mandante")))
    res_visitante = list(collection.aggregate(_pipeline("visitante")))

    return {
        "clube":          nome_clube,
        "como_mandante":  _arredondar(res_mandante[0])  if res_mandante  else {},
        "como_visitante": _arredondar(res_visitante[0]) if res_visitante else {},
    }


def get_confronto_direto_stats(
    collection: Collection,
    clube1: str,
    clube2: str,
) -> List[dict]:
    return list(
        collection.find(
            {
                "$or": [
                    {"mandante.nome": clube1, "visitante.nome": clube2},
                    {"mandante.nome": clube2, "visitante.nome": clube1},
                ]
            },
            {"_id": 0},
        ).sort("partida_id", -1)
    )


# ════════════════════════════════════════════════════════
# WRITE
# ════════════════════════════════════════════════════════

def _montar_documento(partida_id: int, dados: EstatisticasPartidaCreate) -> dict:
    return {
        "partida_id":  partida_id,
        "rodada":      dados.rodada,
        "mandante": {
            "nome":         dados.mandante_nome,
            "estatisticas": dados.mandante_stats.model_dump(exclude_none=True),
        },
        "visitante": {
            "nome":         dados.visitante_nome,
            "estatisticas": dados.visitante_stats.model_dump(exclude_none=True),
        },
    }


def create_estatisticas(
    collection: Collection,
    partida_id: int,
    dados: EstatisticasPartidaCreate,
) -> dict:
    """
    Insere estatísticas de uma partida.
    Bloqueado para partidas históricas.
    """
    _verificar_protecao_historica(partida_id, "adicionar estatísticas em")

    if collection.find_one({"partida_id": partida_id}):
        raise ValueError(
            f"Já existem estatísticas para a partida {partida_id}. "
            "Use PUT /partidas/{id}/estatisticas para atualizar."
        )
    doc = _montar_documento(partida_id, dados)
    collection.insert_one(doc)
    return collection.find_one({"partida_id": partida_id}, {"_id": 0})


def update_estatisticas(
    collection: Collection,
    partida_id: int,
    dados: EstatisticasPartidaCreate,
) -> Optional[dict]:
    """
    Substitui o documento de estatísticas (replace_one).
    Bloqueado para partidas históricas.
    """
    _verificar_protecao_historica(partida_id, "editar estatísticas de")

    if not collection.find_one({"partida_id": partida_id}):
        return None
    doc = _montar_documento(partida_id, dados)
    collection.replace_one({"partida_id": partida_id}, doc)
    return collection.find_one({"partida_id": partida_id}, {"_id": 0})


def delete_estatisticas(collection: Collection, partida_id: int) -> bool:
    """
    Remove as estatísticas de uma partida.
    Bloqueado para partidas históricas.
    """
    _verificar_protecao_historica(partida_id, "deletar estatísticas de")

    result = collection.delete_one({"partida_id": partida_id})
    return result.deleted_count > 0