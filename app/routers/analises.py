from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pymongo.collection import Collection
from typing import Optional, List

from app.dependencies import get_postgres_session, get_mongo_collection, get_cassandra_session
from app.repositories import postgres_repo, mongo_repo, cassandra_repo
from app.schemas.responses import ClassificacaoOut

router = APIRouter(prefix="/analises", tags=["Análises"])


@router.get(
    "/classificacao/{ano}",
    response_model=List[ClassificacaoOut],
    summary="Tabela de classificação de um ano",
)
def classificacao(ano: int, session: Session = Depends(get_postgres_session)):
    """Calcula a classificação completa do Brasileirão para o ano informado."""
    anos_disponiveis = postgres_repo.get_anos_disponiveis(session)
    if ano not in anos_disponiveis:
        raise HTTPException(
            status_code=404,
            detail=f"Ano {ano} não encontrado. Disponíveis: {anos_disponiveis}",
        )
    return postgres_repo.get_classificacao(session, ano)


@router.get(
    "/anos",
    summary="Anos disponíveis no dataset",
)
def anos_disponiveis(session: Session = Depends(get_postgres_session)):
    return {"anos": postgres_repo.get_anos_disponiveis(session)}


@router.get(
    "/artilheiros",
    summary="Artilheiros gerais ou por ano",
)
def artilheiros(
    ano: Optional[int] = Query(None, description="Filtrar por ano"),
    limite: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_postgres_session),
    cassandra=Depends(get_cassandra_session),
):
    partida_ids = None
    if ano:
        _, partidas = postgres_repo.get_partidas(session, ano=ano, por_pagina=10000)
        partida_ids = [p.id for p in partidas]
        print(f"DEBUG ano={ano} partida_ids count={len(partida_ids)} exemplo={partida_ids[:3]}")
        if not partida_ids:
            raise HTTPException(status_code=404, detail=f"Nenhuma partida encontrada para o ano {ano}")

    return cassandra_repo.get_artilheiros(cassandra, limite=limite, partida_ids=partida_ids)


@router.get(
    "/ranking-cartoes",
    summary="Ranking de jogadores com mais cartões",
)
def ranking_cartoes(
    ano: Optional[int] = Query(None),
    tipo: Optional[str] = Query(None, description="Amarelo ou Vermelho"),
    limite: int = Query(10, ge=1, le=50),
    session: Session = Depends(get_postgres_session),
    cassandra=Depends(get_cassandra_session),
):
    if tipo and tipo not in ("Amarelo", "Vermelho"):
        raise HTTPException(status_code=400, detail="Tipo deve ser 'Amarelo' ou 'Vermelho'")

    partida_ids = None
    if ano:
        _, partidas = postgres_repo.get_partidas(session, ano=ano, por_pagina=10000)
        partida_ids = [p.id for p in partidas]

    return cassandra_repo.get_ranking_cartoes(
        cassandra, limite=limite, partida_ids=partida_ids, tipo=tipo
    )


@router.get(
    "/clube/{clube_id}/estatisticas",
    summary="Médias de desempenho de um clube",
)
def estatisticas_clube(
    clube_id: int,
    session: Session = Depends(get_postgres_session),
    mongo_col: Collection = Depends(get_mongo_collection),
):
    clube = postgres_repo.get_clube_by_id(session, clube_id)
    if not clube:
        raise HTTPException(status_code=404, detail="Clube não encontrado")

    return mongo_repo.get_media_estatisticas_clube(mongo_col, clube.nome_oficial)


@router.get(
    "/confronto",
    summary="Histórico e estatísticas de confronto direto entre dois clubes",
)
def confronto_direto(
    clube1_id: int = Query(..., description="ID do primeiro clube"),
    clube2_id: int = Query(..., description="ID do segundo clube"),
    session: Session = Depends(get_postgres_session),
    mongo_col: Collection = Depends(get_mongo_collection),
):
    clube1 = postgres_repo.get_clube_by_id(session, clube1_id)
    clube2 = postgres_repo.get_clube_by_id(session, clube2_id)
    if not clube1:
        raise HTTPException(status_code=404, detail=f"Clube {clube1_id} não encontrado")
    if not clube2:
        raise HTTPException(status_code=404, detail=f"Clube {clube2_id} não encontrado")

    # Histórico de partidas
    from sqlalchemy import or_, extract
    from app.models.postgres_models import Partida
    from sqlalchemy.orm import joinedload

    partidas = (
        session.query(Partida)
        .options(joinedload(Partida.mandante), joinedload(Partida.visitante), joinedload(Partida.estadio))
        .filter(
            or_(
                (Partida.mandante_id == clube1.id) & (Partida.visitante_id == clube2.id),
                (Partida.mandante_id == clube2.id) & (Partida.visitante_id == clube1.id),
            )
        )
        .order_by(Partida.data.desc())
        .all()
    )

    vitórias_c1 = sum(
        1 for p in partidas
        if (p.mandante_id == clube1.id and p.placar_mandante > p.placar_visitante)
        or (p.visitante_id == clube1.id and p.placar_visitante > p.placar_mandante)
    )
    vitórias_c2 = sum(
        1 for p in partidas
        if (p.mandante_id == clube2.id and p.placar_mandante > p.placar_visitante)
        or (p.visitante_id == clube2.id and p.placar_visitante > p.placar_mandante)
    )
    empates = len(partidas) - vitórias_c1 - vitórias_c2

    historico = []
    for p in partidas[:20]:  # últimas 20
        historico.append({
            "id": p.id,
            "data": p.data,
            "mandante": p.mandante.nome_oficial,
            "visitante": p.visitante.nome_oficial,
            "placar": f"{p.placar_mandante}x{p.placar_visitante}",
            "estadio": p.estadio.nome,
        })

    # Estatísticas MongoDB
    stats = mongo_repo.get_confronto_direto_stats(
        mongo_col, clube1.nome_oficial, clube2.nome_oficial
    )

    return {
        "clube1": clube1.nome_oficial,
        "clube2": clube2.nome_oficial,
        "total_jogos": len(partidas),
        f"vitorias_{clube1.sigla}": vitórias_c1,
        f"vitorias_{clube2.sigla}": vitórias_c2,
        "empates": empates,
        "historico_recente": historico,
        "estatisticas_detalhadas": stats[:10],
    }