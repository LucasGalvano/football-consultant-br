"""
Repository PostgreSQL
Camada de acesso a dados para clubes, estádios e partidas.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc, asc, and_, or_, extract
from typing import Optional, List, Tuple
from app.models.postgres_models import Clube, Estadio, Partida

# Mapeamento fixo de temporada → range de IDs
# Necessário porque 2020 foi interrompido pela pandemia e terminou em 2021,
# causando sobreposição de datas entre as temporadas 2020 e 2021.
TEMPORADAS = {
    2014: (4607,  4986),
    2015: (4987,  5366),
    2016: (5367,  5745),
    2017: (5746,  6125),
    2018: (6126,  6505),
    2019: (6506,  6885),
    2020: (6886,  7265),  # terminou em fev/2021 (pandemia) — rodadas 1-38
    2021: (7266,  7645),  # começou em mai/2021 — rodadas 1-38
    2022: (7646,  8025),
    2023: (8026,  8405),
    2024: (8406,  8785),
}


def _filtrar_por_temporada(q, ano: int):
    """Filtra query pelo range de IDs da temporada, não pela data."""
    if ano in TEMPORADAS:
        id_min, id_max = TEMPORADAS[ano]
        return q.filter(Partida.id >= id_min, Partida.id <= id_max)
    # Fallback: filtra por data (anos não mapeados)
    return q.filter(extract("year", Partida.data) == ano)


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
        q = _filtrar_por_temporada(q, ano)
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
    Calcula a classificação do campeonato para uma temporada.
    Usa range de IDs em vez de ano da data para evitar problemas
    com temporadas que cruzaram anos (ex: 2020 pandemia).
    """
    q = (
        session.query(Partida)
        .options(joinedload(Partida.mandante), joinedload(Partida.visitante))
    )
    partidas = _filtrar_por_temporada(q, ano).all()

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
    """Retorna os anos das temporadas conhecidas que têm partidas no banco."""
    anos = []
    for ano, (id_min, id_max) in sorted(TEMPORADAS.items(), reverse=True):
        existe = session.query(Partida).filter(
            Partida.id >= id_min, Partida.id <= id_max
        ).first()
        if existe:
            anos.append(ano)
    return anos