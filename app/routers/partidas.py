"""
Router de Partidas
Integra PostgreSQL + MongoDB + Cassandra.

MELHORIAS:
- CRUD completo (POST / PUT / DELETE) com escrita nos 3 bancos
- Queries paralelas no endpoint de detalhe (ThreadPoolExecutor)
  para evitar soma de latências sequenciais
- DELETE em cascata: remove partida do Postgres + stats do Mongo
  + gols/cartões do Cassandra numa única chamada
- Endpoints de escrita para gols e cartões (Cassandra direto)
"""

import concurrent.futures
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pymongo.collection import Collection
from typing import Optional, List

from app.dependencies import get_postgres_session, get_mongo_collection, get_cassandra_session
from app.repositories import postgres_repo, mongo_repo, cassandra_repo
from app.schemas.responses import PaginatedResponse
from app.schemas.inputs import (
    PartidaCreate, PartidaUpdate,
    EstatisticasPartidaCreate,
    GolCreate, CartaoCreate,
)

router = APIRouter(prefix="/partidas", tags=["Partidas"])


# ─── SERIALIZAÇÃO ──────────────────────────────────────────────────────────────

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


# ─── READ ──────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="Lista partidas com filtros e paginação",
)
def listar_partidas(
    ano: Optional[int] = Query(None, description="Filtrar por ano (ex: 2022)"),
    rodada: Optional[int] = Query(None, description="Filtrar por rodada"),
    clube_id: Optional[int] = Query(None, description="Filtrar por clube (mandante ou visitante)"),
    estadio_id: Optional[int] = Query(None, description="Filtrar por estádio"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(20, ge=1, le=100),
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
    summary="Detalhe completo de uma partida (3 bancos em paralelo)",
    description=(
        "Retorna dados estruturais (PostgreSQL) + estatísticas táticas (MongoDB) "
        "+ gols e cartões (Cassandra). As 3 queries são executadas em paralelo."
    ),
)
def get_partida_detalhe(
    partida_id: int,
    session: Session = Depends(get_postgres_session),
    mongo_col: Collection = Depends(get_mongo_collection),
    cassandra=Depends(get_cassandra_session),
):
    p = postgres_repo.get_partida_by_id(session, partida_id)
    if not p:
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    dados = _serializar_partida(p)

    # ── Queries paralelas nos 3 bancos ────────────────────────────────────────
    # MELHORIA: antes eram 3 queries sequenciais (soma de latências).
    # Agora executamos em paralelo com ThreadPoolExecutor.
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_stats   = ex.submit(mongo_repo.get_estatisticas_partida, mongo_col, partida_id)
        f_gols    = ex.submit(cassandra_repo.get_gols_partida, cassandra, partida_id)
        f_cartoes = ex.submit(cassandra_repo.get_cartoes_partida, cassandra, partida_id)

        # Aguarda os 3 e captura erros individuais sem derrubar a resposta
        try:
            dados["estatisticas"] = f_stats.result()
        except Exception:
            dados["estatisticas"] = None

        try:
            dados["gols"] = f_gols.result()
        except Exception:
            dados["gols"] = []

        try:
            dados["cartoes"] = f_cartoes.result()
        except Exception:
            dados["cartoes"] = []

    return dados


@router.get("/{partida_id}/gols", summary="Gols de uma partida (Cassandra)")
def get_gols_partida(
    partida_id: int,
    cassandra=Depends(get_cassandra_session),
    session: Session = Depends(get_postgres_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return cassandra_repo.get_gols_partida(cassandra, partida_id)


@router.get("/{partida_id}/cartoes", summary="Cartões de uma partida (Cassandra)")
def get_cartoes_partida(
    partida_id: int,
    cassandra=Depends(get_cassandra_session),
    session: Session = Depends(get_postgres_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return cassandra_repo.get_cartoes_partida(cassandra, partida_id)


@router.get("/{partida_id}/estatisticas", summary="Estatísticas táticas de uma partida (MongoDB)")
def get_estatisticas_partida(
    partida_id: int,
    mongo_col: Collection = Depends(get_mongo_collection),
    session: Session = Depends(get_postgres_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    stats = mongo_repo.get_estatisticas_partida(mongo_col, partida_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Estatísticas não encontradas para esta partida")
    return stats


# ─── WRITE — Partida (PostgreSQL) ──────────────────────────────────────────────

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova partida",
    description=(
        "Insere a partida no PostgreSQL. O campo `vencedor_id` é calculado "
        "automaticamente a partir do placar informado."
    ),
)
def criar_partida(
    dados: PartidaCreate,
    session: Session = Depends(get_postgres_session),
):
    try:
        partida = postgres_repo.create_partida(session, dados)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return _serializar_partida(partida)


@router.put(
    "/{partida_id}",
    summary="Atualiza dados de uma partida",
    description="Atualiza campos informados. Recalcula vencedor_id se placar mudar.",
)
def atualizar_partida(
    partida_id: int,
    dados: PartidaUpdate,
    session: Session = Depends(get_postgres_session),
):
    try:
        partida = postgres_repo.update_partida(session, partida_id, dados)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    if not partida:
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return _serializar_partida(partida)


@router.delete(
    "/{partida_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove uma partida (cascata nos 3 bancos)",
    description=(
        "Remove a partida do PostgreSQL e, em cascata, os documentos "
        "correspondentes no MongoDB (estatísticas) e Cassandra (gols e cartões). "
        "Retorna um resumo do que foi removido."
    ),
)
def deletar_partida(
    partida_id: int,
    session: Session = Depends(get_postgres_session),
    mongo_col: Collection = Depends(get_mongo_collection),
    cassandra=Depends(get_cassandra_session),
):
    # Verifica existência antes de qualquer remoção
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    # Remove nos 3 bancos (Mongo e Cassandra em paralelo, depois Postgres)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
        f_mongo    = ex.submit(mongo_repo.delete_estatisticas, mongo_col, partida_id)
        f_gols     = ex.submit(cassandra_repo.delete_gols_partida, cassandra, partida_id)
        f_cartoes  = ex.submit(cassandra_repo.delete_cartoes_partida, cassandra, partida_id)

        stats_removidas = f_mongo.result()
        gols_removidos  = f_gols.result()
        cartoes_removidos = f_cartoes.result()

    postgres_repo.delete_partida(session, partida_id)

    return {
        "partida_id": partida_id,
        "removido": True,
        "detalhes": {
            "postgres": "partida removida",
            "mongodb_estatisticas": "removido" if stats_removidas else "não existia",
            "cassandra_gols": f"{gols_removidos} gol(s) removido(s)",
            "cassandra_cartoes": f"{cartoes_removidos} cartão(ões) removido(s)",
        },
    }


# ─── WRITE — Estatísticas (MongoDB) ────────────────────────────────────────────

@router.post(
    "/{partida_id}/estatisticas",
    status_code=status.HTTP_201_CREATED,
    summary="Cria estatísticas táticas de uma partida (MongoDB)",
)
def criar_estatisticas(
    partida_id: int,
    dados: EstatisticasPartidaCreate,
    session: Session = Depends(get_postgres_session),
    mongo_col: Collection = Depends(get_mongo_collection),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada no PostgreSQL")
    try:
        return mongo_repo.create_estatisticas(mongo_col, partida_id, dados)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put(
    "/{partida_id}/estatisticas",
    summary="Atualiza (substitui) estatísticas de uma partida (MongoDB)",
)
def atualizar_estatisticas(
    partida_id: int,
    dados: EstatisticasPartidaCreate,
    session: Session = Depends(get_postgres_session),
    mongo_col: Collection = Depends(get_mongo_collection),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada no PostgreSQL")
    result = mongo_repo.update_estatisticas(mongo_col, partida_id, dados)
    if not result:
        raise HTTPException(status_code=404, detail="Estatísticas não encontradas. Use POST para criar.")
    return result


@router.delete(
    "/{partida_id}/estatisticas",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove estatísticas de uma partida (MongoDB)",
)
def deletar_estatisticas(
    partida_id: int,
    mongo_col: Collection = Depends(get_mongo_collection),
):
    removido = mongo_repo.delete_estatisticas(mongo_col, partida_id)
    if not removido:
        raise HTTPException(status_code=404, detail="Estatísticas não encontradas")


# ─── WRITE — Gols (Cassandra) ──────────────────────────────────────────────────

@router.post(
    "/{partida_id}/gols",
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona um gol a uma partida (Cassandra)",
)
def criar_gol(
    partida_id: int,
    dados: GolCreate,
    session: Session = Depends(get_postgres_session),
    cassandra=Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return cassandra_repo.create_gol(cassandra, partida_id, dados)


@router.delete(
    "/{partida_id}/gols",
    status_code=status.HTTP_200_OK,
    summary="Remove todos os gols de uma partida (Cassandra)",
)
def deletar_gols(
    partida_id: int,
    session: Session = Depends(get_postgres_session),
    cassandra=Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    count = cassandra_repo.delete_gols_partida(cassandra, partida_id)
    return {"partida_id": partida_id, "gols_removidos": count}


# ─── WRITE — Cartões (Cassandra) ───────────────────────────────────────────────

@router.post(
    "/{partida_id}/cartoes",
    status_code=status.HTTP_201_CREATED,
    summary="Adiciona um cartão a uma partida (Cassandra)",
)
def criar_cartao(
    partida_id: int,
    dados: CartaoCreate,
    session: Session = Depends(get_postgres_session),
    cassandra=Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return cassandra_repo.create_cartao(cassandra, partida_id, dados)


@router.delete(
    "/{partida_id}/cartoes",
    status_code=status.HTTP_200_OK,
    summary="Remove todos os cartões de uma partida (Cassandra)",
)
def deletar_cartoes(
    partida_id: int,
    session: Session = Depends(get_postgres_session),
    cassandra=Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    count = cassandra_repo.delete_cartoes_partida(cassandra, partida_id)
    return {"partida_id": partida_id, "cartoes_removidos": count}