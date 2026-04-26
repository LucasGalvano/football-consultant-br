"""
Repository PostgreSQL
Camada de acesso a dados para clubes, estádios e partidas.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, asc, and_, or_, extract
from typing import Optional, List, Tuple
from app.models.postgres_models import Clube, Estadio, Partida


# ─── CLUBES ───────────────────────────────────────────────────────────────────

def get_all_clubes(session: Session) -> List[Clube]:
    return session.query(Clube).order_by(Clube.nome_oficial).all()


def get_clube_by_id(session: Session, clube_id: int) -> Optional[Clube]:
    return session.query(Clube).filter(Clube.id == clube_id).first()


def get_clube_by_nome(session: Session, nome: str) -> Optional[Clube]:
    return session.query(Clube).filter(
        Clube.nome_oficial.ilike(f"%{nome}%")
    ).first()


# ─── ESTÁDIOS ─────────────────────────────────────────────────────────────────

def get_all_estadios(session: Session) -> List[Estadio]:
    return session.query(Estadio).order_by(Estadio.nome).all()


def get_estadio_by_id(session: Session, estadio_id: int) -> Optional[Estadio]:
    return session.query(Estadio).filter(Estadio.id == estadio_id).first()


# ─── PARTIDAS ─────────────────────────────────────────────────────────────────

def get_partidas(
    session: Session,
    ano: Optional[int] = None,
    rodada: Optional[int] = None,
    clube_id: Optional[int] = None,
    estadio_id: Optional[int] = None,
    pagina: int = 1,
    por_pagina: int = 20,
) -> Tuple[int, List[Partida]]:
    q = (
        session.query(Partida)
        .options(
            joinedload(Partida.mandante),
            joinedload(Partida.visitante),
            joinedload(Partida.vencedor),
            joinedload(Partida.estadio),
        )
        .order_by(Partida.data, Partida.id)
    )

    if ano:
        q = q.filter(extract("year", Partida.data) == ano)
    if rodada:
        q = q.filter(Partida.rodada == rodada)
    if clube_id:
        q = q.filter(
            or_(Partida.mandante_id == clube_id, Partida.visitante_id == clube_id)
        )
    if estadio_id:
        q = q.filter(Partida.estadio_id == estadio_id)

    total = q.count()
    dados = q.offset((pagina - 1) * por_pagina).limit(por_pagina).all()
    return total, dados


def get_partida_by_id(session: Session, partida_id: int) -> Optional[Partida]:
    return (
        session.query(Partida)
        .options(
            joinedload(Partida.mandante),
            joinedload(Partida.visitante),
            joinedload(Partida.vencedor),
            joinedload(Partida.estadio),
        )
        .filter(Partida.id == partida_id)
        .first()
    )


# ─── CLASSIFICAÇÃO ────────────────────────────────────────────────────────────

def get_classificacao(session: Session, ano: int) -> List[dict]:
    """
    Calcula a classificação do campeonato para um determinado ano.
    Retorna lista ordenada por pontos, saldo de gols e gols pró.
    """
    partidas = (
        session.query(Partida)
        .options(joinedload(Partida.mandante), joinedload(Partida.visitante))
        .filter(extract("year", Partida.data) == ano)
        .all()
    )

    tabela: dict[str, dict] = {}

    def iniciar_clube(nome: str):
        if nome not in tabela:
            tabela[nome] = dict(
                clube=nome, jogos=0, vitorias=0, empates=0,
                derrotas=0, gols_pro=0, gols_contra=0,
            )

    for p in partidas:
        m = p.mandante.nome_oficial
        v = p.visitante.nome_oficial
        iniciar_clube(m)
        iniciar_clube(v)

        tabela[m]["jogos"] += 1
        tabela[v]["jogos"] += 1
        tabela[m]["gols_pro"] += p.placar_mandante
        tabela[m]["gols_contra"] += p.placar_visitante
        tabela[v]["gols_pro"] += p.placar_visitante
        tabela[v]["gols_contra"] += p.placar_mandante

        if p.placar_mandante > p.placar_visitante:
            tabela[m]["vitorias"] += 1
            tabela[v]["derrotas"] += 1
        elif p.placar_mandante < p.placar_visitante:
            tabela[v]["vitorias"] += 1
            tabela[m]["derrotas"] += 1
        else:
            tabela[m]["empates"] += 1
            tabela[v]["empates"] += 1

    resultado = []
    for clube, d in tabela.items():
        d["pontos"] = d["vitorias"] * 3 + d["empates"]
        d["saldo_gols"] = d["gols_pro"] - d["gols_contra"]
        resultado.append(d)

    resultado.sort(key=lambda x: (-x["pontos"], -x["saldo_gols"], -x["gols_pro"]))

    for i, row in enumerate(resultado, 1):
        row["posicao"] = i

    return resultado


# ─── ANOS DISPONÍVEIS ─────────────────────────────────────────────────────────

def get_anos_disponiveis(session: Session) -> List[int]:
    rows = (
        session.query(extract("year", Partida.data).label("ano"))
        .distinct()
        .order_by(desc("ano"))
        .all()
    )
    return [int(r.ano) for r in rows]