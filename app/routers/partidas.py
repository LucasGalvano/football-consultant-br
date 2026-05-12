"""
Router de Partidas
Integra PostgreSQL + MongoDB + Cassandra.

CORREÇÕES v2:
  - Gap 1: endpoint DELETE /partidas/{id}/gols/{minuto}/{atleta} exposto.
  - Gap 2: endpoints PUT para gol e cartão individual (delete + insert no Cassandra).
  - Gap 7: ThreadPoolExecutor com max_workers=3 no DELETE cascata.
  - Proteção histórica: HistoricalDataError mapeada para HTTP 403.
"""

import concurrent.futures
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pymongo.collection import Collection
from typing import Optional, List

from app.dependencies import get_postgres_session, get_mongo_collection, get_cassandra_session
from app.repositories import postgres_repo, mongo_repo, cassandra_repo
from app.repositories.cassandra_repo import HistoricalDataError as CassandraHistoricalError
from app.repositories.mongo_repo import HistoricalDataError as MongoHistoricalError
from app.repositories.postgres_repo import HistoricalDataError as PostgresHistoricalError
from app.schemas.responses import PaginatedResponse
from app.schemas.inputs import (
    PartidaCreate, PartidaUpdate,
    EstatisticasPartidaCreate,
    GolCreate, CartaoCreate,
)

router = APIRouter(prefix="/partidas", tags=["Partidas"])

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _serializar_partida(p) -> dict:
    return {
        "id":               p.id,
        "rodada":           p.rodada,
        "data":             p.data,
        "hora":             p.hora,
        "mandante":         p.mandante.nome_oficial,
        "visitante":        p.visitante.nome_oficial,
        "placar_mandante":  p.placar_mandante,
        "placar_visitante": p.placar_visitante,
        "estadio":          p.estadio.nome,
        "vencedor":         p.vencedor.nome_oficial if p.vencedor else None,
        "formacao_mandante":  p.formacao_mandante,
        "formacao_visitante": p.formacao_visitante,
        "tecnico_mandante":   p.tecnico_mandante,
        "tecnico_visitante":  p.tecnico_visitante,
    }


def _levantar_se_historico(exc: Exception) -> None:
    """Converte HistoricalDataError de qualquer repo em HTTP 403."""
    if isinstance(exc, (CassandraHistoricalError, MongoHistoricalError, PostgresHistoricalError)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))


# ─── READ ──────────────────────────────────────────────────────────────────────

@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="Lista partidas com filtros e paginação",
)
def listar_partidas(
    ano: Optional[int]      = Query(None, description="Filtrar por ano (ex: 2022)"),
    rodada: Optional[int]   = Query(None, description="Filtrar por rodada"),
    clube_id: Optional[int] = Query(None, description="Filtrar por clube (mandante ou visitante)"),
    estadio_id: Optional[int] = Query(None, description="Filtrar por estádio"),
    pagina: int             = Query(1, ge=1),
    por_pagina: int         = Query(20, ge=1, le=100),
    session: Session        = Depends(get_postgres_session),
):
    total, partidas = postgres_repo.get_partidas(
        session, ano=ano, rodada=rodada,
        clube_id=clube_id, estadio_id=estadio_id,
        pagina=pagina, por_pagina=por_pagina,
    )
    return {
        "total":      total,
        "pagina":     pagina,
        "por_pagina": por_pagina,
        "dados":      [_serializar_partida(p) for p in partidas],
    }


@router.get(
    "/{partida_id}",
    summary="Detalhe completo de uma partida (3 bancos em paralelo)",
)
def get_partida_detalhe(
    partida_id: int,
    session: Session          = Depends(get_postgres_session),
    mongo_col: Collection     = Depends(get_mongo_collection),
    cassandra                 = Depends(get_cassandra_session),
):
    p = postgres_repo.get_partida_by_id(session, partida_id)
    if not p:
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    dados = _serializar_partida(p)

    # Gap 7 corrigido: max_workers=3 para 3 futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_stats   = ex.submit(mongo_repo.get_estatisticas_partida, mongo_col, partida_id)
        f_gols    = ex.submit(cassandra_repo.get_gols_partida, cassandra, partida_id)
        f_cartoes = ex.submit(cassandra_repo.get_cartoes_partida, cassandra, partida_id)

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
    cassandra  = Depends(get_cassandra_session),
    session: Session = Depends(get_postgres_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return cassandra_repo.get_gols_partida(cassandra, partida_id)


@router.get(
    "/{partida_id}/gols/{minuto}/{atleta}",
    summary="Busca um gol específico pelo minuto e atleta (Cassandra)",
)
def get_gol_individual(
    partida_id: int,
    minuto: int,
    atleta: str,
    cassandra  = Depends(get_cassandra_session),
    session: Session = Depends(get_postgres_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    gol = cassandra_repo.get_gol_individual(cassandra, partida_id, minuto, atleta)
    if not gol:
        raise HTTPException(status_code=404, detail="Gol não encontrado")
    return gol


@router.get("/{partida_id}/cartoes", summary="Cartões de uma partida (Cassandra)")
def get_cartoes_partida(
    partida_id: int,
    cassandra  = Depends(get_cassandra_session),
    session: Session = Depends(get_postgres_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    return cassandra_repo.get_cartoes_partida(cassandra, partida_id)


@router.get(
    "/{partida_id}/cartoes/{minuto}/{atleta}/{tipo_cartao}",
    summary="Busca um cartão específico (Cassandra)",
)
def get_cartao_individual(
    partida_id: int,
    minuto: int,
    atleta: str,
    tipo_cartao: str,
    cassandra  = Depends(get_cassandra_session),
    session: Session = Depends(get_postgres_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    cartao = cassandra_repo.get_cartao_individual(
        cassandra, partida_id, minuto, atleta, tipo_cartao
    )
    if not cartao:
        raise HTTPException(status_code=404, detail="Cartão não encontrado")
    return cartao


@router.get(
    "/{partida_id}/estatisticas",
    summary="Estatísticas táticas de uma partida (MongoDB)",
)
def get_estatisticas_partida(
    partida_id: int,
    mongo_col: Collection = Depends(get_mongo_collection),
    session: Session      = Depends(get_postgres_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    stats = mongo_repo.get_estatisticas_partida(mongo_col, partida_id)
    if not stats:
        raise HTTPException(
            status_code=404,
            detail="Estatísticas não encontradas para esta partida",
        )
    return stats


# ─── WRITE — Partida (PostgreSQL) ──────────────────────────────────────────────

@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Cria uma nova partida",
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
    description=(
        "Atualiza campos informados. Bloqueado para partidas históricas "
        "(IDs até 8785 — dataset CSV 2014–2024)."
    ),
)
def atualizar_partida(
    partida_id: int,
    dados: PartidaUpdate,
    session: Session = Depends(get_postgres_session),
):
    try:
        partida = postgres_repo.update_partida(session, partida_id, dados)
    except (PostgresHistoricalError,) as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
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
        "correspondentes no MongoDB e Cassandra. "
        "Bloqueado para partidas históricas (IDs até 8785)."
    ),
)
def deletar_partida(
    partida_id: int,
    session: Session      = Depends(get_postgres_session),
    mongo_col: Collection = Depends(get_mongo_collection),
    cassandra             = Depends(get_cassandra_session),
):
    # Verifica existência antes de qualquer remoção
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")

    # Verifica proteção histórica antes de qualquer operação cross-banco
    try:
        postgres_repo._verificar_protecao_historica(partida_id, "deletar")
    except PostgresHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    # Gap 7 corrigido: max_workers=3 para garantir as 3 futures em paralelo
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:
        f_mongo   = ex.submit(mongo_repo.delete_estatisticas, mongo_col, partida_id)
        f_gols    = ex.submit(cassandra_repo.delete_gols_partida, cassandra, partida_id)
        f_cartoes = ex.submit(cassandra_repo.delete_cartoes_partida, cassandra, partida_id)

        # Aguarda os 3 — sem proteção histórica aqui pois já verificamos acima
        # Suprimimos HistoricalDataError (não deveria ocorrer após a verificação)
        try:
            stats_removidas = f_mongo.result()
        except Exception:
            stats_removidas = False

        try:
            gols_removidos = f_gols.result()
        except Exception:
            gols_removidos = 0

        try:
            cartoes_removidos = f_cartoes.result()
        except Exception:
            cartoes_removidos = 0

    postgres_repo.delete_partida(session, partida_id)

    return {
        "partida_id": partida_id,
        "removido":   True,
        "detalhes": {
            "postgres":             "partida removida",
            "mongodb_estatisticas": "removido" if stats_removidas else "não existia",
            "cassandra_gols":       f"{gols_removidos} gol(s) removido(s)",
            "cassandra_cartoes":    f"{cartoes_removidos} cartão(ões) removido(s)",
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
    session: Session      = Depends(get_postgres_session),
    mongo_col: Collection = Depends(get_mongo_collection),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada no PostgreSQL")
    try:
        return mongo_repo.create_estatisticas(mongo_col, partida_id, dados)
    except MongoHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.put(
    "/{partida_id}/estatisticas",
    summary="Atualiza (substitui) estatísticas de uma partida (MongoDB)",
)
def atualizar_estatisticas(
    partida_id: int,
    dados: EstatisticasPartidaCreate,
    session: Session      = Depends(get_postgres_session),
    mongo_col: Collection = Depends(get_mongo_collection),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada no PostgreSQL")
    try:
        result = mongo_repo.update_estatisticas(mongo_col, partida_id, dados)
    except MongoHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    if not result:
        raise HTTPException(
            status_code=404,
            detail="Estatísticas não encontradas. Use POST para criar.",
        )
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
    try:
        removido = mongo_repo.delete_estatisticas(mongo_col, partida_id)
    except MongoHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
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
    cassandra        = Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    try:
        return cassandra_repo.create_gol(cassandra, partida_id, dados)
    except CassandraHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put(
    "/{partida_id}/gols/{minuto}/{atleta}",
    summary="Atualiza um gol específico (Cassandra — delete + insert)",
    description=(
        "Localiza o gol pela chave (minuto, atleta) e o substitui pelos "
        "novos dados informados no body. Se minuto ou atleta mudarem, "
        "o registro antigo é removido e um novo é criado. "
        "Bloqueado para partidas históricas (IDs até 8785)."
    ),
)
def atualizar_gol(
    partida_id: int,
    minuto: int,
    atleta: str,
    dados: GolCreate,
    session: Session = Depends(get_postgres_session),
    cassandra        = Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    try:
        resultado = cassandra_repo.update_gol(
            cassandra, partida_id, minuto, atleta, dados
        )
    except CassandraHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=f"Gol não encontrado (partida={partida_id}, minuto={minuto}, atleta={atleta})",
        )
    return resultado


@router.delete(
    "/{partida_id}/gols/{minuto}/{atleta}",
    status_code=status.HTTP_200_OK,
    summary="Remove um gol específico de uma partida (Cassandra)",
    description=(
        "Remove exatamente o gol identificado por partida_id + minuto + atleta. "
        "Bloqueado para partidas históricas (IDs até 8785)."
    ),
)
def deletar_gol_individual(
    partida_id: int,
    minuto: int,
    atleta: str,
    session: Session = Depends(get_postgres_session),
    cassandra        = Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    try:
        removido = cassandra_repo.delete_gol(cassandra, partida_id, minuto, atleta)
    except CassandraHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    if not removido:
        raise HTTPException(
            status_code=404,
            detail=f"Gol não encontrado (partida={partida_id}, minuto={minuto}, atleta={atleta})",
        )
    return {
        "partida_id": partida_id,
        "minuto":     minuto,
        "atleta":     atleta,
        "removido":   True,
    }


@router.delete(
    "/{partida_id}/gols",
    status_code=status.HTTP_200_OK,
    summary="Remove todos os gols de uma partida (Cassandra)",
)
def deletar_gols(
    partida_id: int,
    session: Session = Depends(get_postgres_session),
    cassandra        = Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    try:
        count = cassandra_repo.delete_gols_partida(cassandra, partida_id)
    except CassandraHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
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
    cassandra        = Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    try:
        return cassandra_repo.create_cartao(cassandra, partida_id, dados)
    except CassandraHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


@router.put(
    "/{partida_id}/cartoes/{minuto}/{atleta}/{tipo_cartao}",
    summary="Atualiza um cartão específico (Cassandra — delete + insert)",
    description=(
        "Localiza o cartão pela chave (minuto, atleta, tipo_cartao) e o "
        "substitui pelos novos dados do body. "
        "Bloqueado para partidas históricas (IDs até 8785)."
    ),
)
def atualizar_cartao(
    partida_id: int,
    minuto: int,
    atleta: str,
    tipo_cartao: str,
    dados: CartaoCreate,
    session: Session = Depends(get_postgres_session),
    cassandra        = Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    try:
        resultado = cassandra_repo.update_cartao(
            cassandra, partida_id, minuto, atleta, tipo_cartao, dados
        )
    except CassandraHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    if resultado is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Cartão não encontrado "
                f"(partida={partida_id}, minuto={minuto}, "
                f"atleta={atleta}, tipo={tipo_cartao})"
            ),
        )
    return resultado


@router.delete(
    "/{partida_id}/cartoes/{minuto}/{atleta}/{tipo_cartao}",
    status_code=status.HTTP_200_OK,
    summary="Remove um cartão específico de uma partida (Cassandra)",
    description="Bloqueado para partidas históricas (IDs até 8785).",
)
def deletar_cartao_individual(
    partida_id: int,
    minuto: int,
    atleta: str,
    tipo_cartao: str,
    session: Session = Depends(get_postgres_session),
    cassandra        = Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    try:
        removido = cassandra_repo.delete_cartao_individual(
            cassandra, partida_id, minuto, atleta, tipo_cartao
        )
    except CassandraHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    if not removido:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Cartão não encontrado "
                f"(partida={partida_id}, minuto={minuto}, "
                f"atleta={atleta}, tipo={tipo_cartao})"
            ),
        )
    return {
        "partida_id": partida_id,
        "minuto":     minuto,
        "atleta":     atleta,
        "tipo_cartao": tipo_cartao,
        "removido":   True,
    }


@router.delete(
    "/{partida_id}/cartoes",
    status_code=status.HTTP_200_OK,
    summary="Remove todos os cartões de uma partida (Cassandra)",
)
def deletar_cartoes(
    partida_id: int,
    session: Session = Depends(get_postgres_session),
    cassandra        = Depends(get_cassandra_session),
):
    if not postgres_repo.get_partida_by_id(session, partida_id):
        raise HTTPException(status_code=404, detail="Partida não encontrada")
    try:
        count = cassandra_repo.delete_cartoes_partida(cassandra, partida_id)
    except CassandraHistoricalError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return {"partida_id": partida_id, "cartoes_removidos": count}