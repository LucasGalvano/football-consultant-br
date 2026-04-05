from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pymongo.collection import Collection
from typing import Optional, List

from app.dependencies import get_postgres_session, get_mongo_collection, get_cassandra_session
from app.repositories import postgres_repo, mongo_repo, cassandra_repo
from app.schemas.responses import PartidaResumo, PartidaDetalhe, PaginatedResponse

router = APIRouter(prefix="/partidas", tags=["Partidas"])


def _serializar_partida(p) -> dict:
    return {
        "id": p.id,
        "rodada": p.rodada,
        "data": p.data,
        "hora": p.hora,
        "mandante": p.mandante.nome_oficial,
        "visitante": p.visitante.nome_oficial,
        "placar_mandante": p.placar_mandante,
        "placar_visitante": p.placar_visitante,
        "estadio": p.estadio.nome,
        "vencedor": p.vencedor.nome_oficial if p.vencedor else None,
        "formacao_mandante": p.formacao_mandante,
        "formacao_visitante": p.formacao_visitante,
        "tecnico_mandante": p.tecnico_mandante,
        "tecnico_visitante": p.tecnico_visitante,
    }


@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="Lista partidas com filtros",
)
def listar_partidas(
    ano: Optional[int] = Query(None, description="Filtrar por ano (ex: 2022)"),
    rodada: Optional[int] = Query(None, description="Filtrar por rodada"),
    clube_id: Optional[int] = Query(None, description="Filtrar por clube (mandante ou visitante)"),
    estadio_id: Optional[int] = Query(None, description="Filtrar por estádio"),
    pagina: int = Query(1, ge=1, description="Número da página"),
    por_pagina: int = Query(20, ge=1, le=100, description="Resultados por página"),
    session: Session = Depends(get_postgres_session),
):
    total, partidas = postgres_repo.get_partidas(
        session, ano=ano, rodada=rodada,
        clube_id=clube_id, estadio_id=estadio_id,
        pagina=pagina, por_pagina=por_pagina,
    )
    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "dados": [_serializar_partida(p) for p in partidas],
    }


@router.get(
    "/{partida_id}",
    summary="Detalhe completo de uma partida",
    description="Retorna dados da partida + estatísticas (MongoDB) + gols e cartões (Cassandra).",
)
def get_partida_detalhe(
    partida_id: int,
    session: Session = Depends(get_postgres_session),
    mongo_col: Collection = Depends(get_mongo_collection),
    cassandra: object = Depends(get_cassandra_session),
):
    p = postgres_repo.get_partida_by_id(session, partida_id)
    if not p:
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    dados = _serializar_partida(p)

    # Enriquece com MongoDB
    stats = mongo_repo.get_estatisticas_partida(mongo_col, partida_id)
    dados["estatisticas"] = stats

    # Enriquece com Cassandra
    dados["gols"] = cassandra_repo.get_gols_partida(cassandra, partida_id)
    dados["cartoes"] = cassandra_repo.get_cartoes_partida(cassandra, partida_id)

    return dados


@router.get(
    "/{partida_id}/gols",
    summary="Gols de uma partida",
)
def get_gols_partida(
    partida_id: int,
    cassandra=Depends(get_cassandra_session),
    session: Session = Depends(get_postgres_session),
):
    p = postgres_repo.get_partida_by_id(session, partida_id)
    if not p:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return cassandra_repo.get_gols_partida(cassandra, partida_id)


@router.get(
    "/{partida_id}/cartoes",
    summary="Cartões de uma partida",
)
def get_cartoes_partida(
    partida_id: int,
    cassandra=Depends(get_cassandra_session),
    session: Session = Depends(get_postgres_session),
):
    p = postgres_repo.get_partida_by_id(session, partida_id)
    if not p:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return cassandra_repo.get_cartoes_partida(cassandra, partida_id)


@router.get(
    "/{partida_id}/estatisticas",
    summary="Estatísticas de uma partida (MongoDB)",
)
def get_estatisticas_partida(
    partida_id: int,
    mongo_col: Collection = Depends(get_mongo_collection),
    session: Session = Depends(get_postgres_session),
):
    p = postgres_repo.get_partida_by_id(session, partida_id)
    if not p:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    stats = mongo_repo.get_estatisticas_partida(mongo_col, partida_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Estatísticas não encontradas para esta partida")
    return stats