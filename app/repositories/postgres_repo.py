"""
Repository PostgreSQL
CRUD completo para Clube, Estádio e Partida.

PROTEÇÃO HISTÓRICA:
  Partidas com ID <= 8785 (dataset CSV 2014–2024) não podem ser
  deletadas nem ter seu placar/times alterados via API.
  A constante ULTIMO_ID_HISTORICO deve estar sincronizada com
  cassandra_repo.py e mongo_repo.py.
"""

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, extract, func
from typing import Optional, List, Tuple

from app.models.postgres_models import Clube, Estadio, Partida
from app.schemas.inputs import (
    ClubeCreate, ClubeUpdate,
    EstadioCreate, EstadioUpdate,
    PartidaCreate, PartidaUpdate,
)

ULTIMO_ID_HISTORICO = 8785


class HistoricalDataError(ValueError):
    """Lançada ao tentar modificar ou deletar uma partida histórica."""
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
# TEMPORADAS
# ════════════════════════════════════════════════════════

TEMPORADAS = {
    2014: (4607, 4986),
    2015: (4987, 5366),
    2016: (5367, 5745),
    2017: (5746, 6125),
    2018: (6126, 6505),
    2019: (6506, 6885),
    2020: (6886, 7265),
    2021: (7266, 7645),
    2022: (7646, 8025),
    2023: (8026, 8405),
    2024: (8406, 8785),
    2026: (9000, 9379),
}


def _filtrar_por_temporada(query, ano: int):
    if ano in TEMPORADAS:
        id_min, id_max = TEMPORADAS[ano]
        return query.filter(Partida.id >= id_min, Partida.id <= id_max)
    return query.filter(extract("year", Partida.data) == ano)


# ════════════════════════════════════════════════════════
# CLUBES — READ
# ════════════════════════════════════════════════════════

def get_all_clubes(session: Session) -> List[Clube]:
    return session.query(Clube).order_by(Clube.nome_oficial).all()


def get_clube_by_id(session: Session, clube_id: int) -> Optional[Clube]:
    return session.query(Clube).filter(Clube.id == clube_id).first()


def get_clube_by_nome(session: Session, nome: str) -> Optional[Clube]:
    return session.query(Clube).filter(
        Clube.nome_oficial.ilike(f"%{nome}%")
    ).first()


# ════════════════════════════════════════════════════════
# CLUBES — WRITE
# ════════════════════════════════════════════════════════

def create_clube(session: Session, dados: ClubeCreate) -> Clube:
    existente = session.query(Clube).filter(
        Clube.nome_oficial == dados.nome_oficial
    ).first()
    if existente:
        raise ValueError(
            f"Já existe um clube com nome '{dados.nome_oficial}' "
            f"(id={existente.id}). Use PUT /{existente.id} para atualizar."
        )
    clube = Clube(**dados.model_dump())
    session.add(clube)
    session.commit()
    session.refresh(clube)
    return clube


def update_clube(
    session: Session, clube_id: int, dados: ClubeUpdate
) -> Optional[Clube]:
    clube = get_clube_by_id(session, clube_id)
    if not clube:
        return None
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(clube, campo, valor)
    session.commit()
    session.refresh(clube)
    return clube


def delete_clube(session: Session, clube_id: int) -> bool:
    clube = get_clube_by_id(session, clube_id)
    if not clube:
        return False
    vinculadas = session.query(Partida).filter(
        or_(
            Partida.mandante_id == clube_id,
            Partida.visitante_id == clube_id,
            Partida.vencedor_id == clube_id,
        )
    ).count()
    if vinculadas > 0:
        raise ValueError(
            f"O clube '{clube.nome_oficial}' tem {vinculadas} partida(s) "
            "vinculada(s). Delete as partidas antes de remover o clube."
        )
    session.delete(clube)
    session.commit()
    return True


# ════════════════════════════════════════════════════════
# ESTÁDIOS — READ
# ════════════════════════════════════════════════════════

def get_all_estadios(session: Session) -> List[Estadio]:
    return session.query(Estadio).order_by(Estadio.nome).all()


def get_estadio_by_id(session: Session, estadio_id: int) -> Optional[Estadio]:
    return session.query(Estadio).filter(Estadio.id == estadio_id).first()


# ════════════════════════════════════════════════════════
# ESTÁDIOS — WRITE
# ════════════════════════════════════════════════════════

def create_estadio(session: Session, dados: EstadioCreate) -> Estadio:
    existente = session.query(Estadio).filter(
        Estadio.nome == dados.nome
    ).first()
    if existente:
        raise ValueError(
            f"Já existe um estádio com nome '{dados.nome}' "
            f"(id={existente.id}). Use PUT /{existente.id} para atualizar."
        )
    estadio = Estadio(**dados.model_dump())
    session.add(estadio)
    session.commit()
    session.refresh(estadio)
    return estadio


def update_estadio(
    session: Session, estadio_id: int, dados: EstadioUpdate
) -> Optional[Estadio]:
    estadio = get_estadio_by_id(session, estadio_id)
    if not estadio:
        return None
    for campo, valor in dados.model_dump(exclude_none=True).items():
        setattr(estadio, campo, valor)
    session.commit()
    session.refresh(estadio)
    return estadio


def delete_estadio(session: Session, estadio_id: int) -> bool:
    estadio = get_estadio_by_id(session, estadio_id)
    if not estadio:
        return False
    vinculadas = session.query(Partida).filter(
        Partida.estadio_id == estadio_id
    ).count()
    if vinculadas > 0:
        raise ValueError(
            f"O estádio '{estadio.nome}' tem {vinculadas} partida(s) "
            "vinculada(s). Delete as partidas antes de remover o estádio."
        )
    session.delete(estadio)
    session.commit()
    return True


# ════════════════════════════════════════════════════════
# PARTIDAS — READ
# ════════════════════════════════════════════════════════

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


def get_todos_partida_ids(session: Session) -> List[int]:
    rows = session.query(Partida.id).order_by(Partida.id).all()
    return [r[0] for r in rows]


# ════════════════════════════════════════════════════════
# PARTIDAS — WRITE
# ════════════════════════════════════════════════════════

def _proximo_id_partida(session: Session) -> int:
    max_id = session.query(func.max(Partida.id)).scalar() or 8999
    return max(max_id + 1, 9000)


def _calcular_vencedor_id(
    placar_mandante: int,
    placar_visitante: int,
    mandante_id: int,
    visitante_id: int,
) -> Optional[int]:
    if placar_mandante > placar_visitante:
        return mandante_id
    if placar_visitante > placar_mandante:
        return visitante_id
    return None


def create_partida(session: Session, dados: PartidaCreate) -> Partida:
    if not get_clube_by_id(session, dados.mandante_id):
        raise ValueError(f"Clube mandante id={dados.mandante_id} não encontrado.")
    if not get_clube_by_id(session, dados.visitante_id):
        raise ValueError(f"Clube visitante id={dados.visitante_id} não encontrado.")
    if not get_estadio_by_id(session, dados.estadio_id):
        raise ValueError(f"Estádio id={dados.estadio_id} não encontrado.")

    vencedor_id = _calcular_vencedor_id(
        dados.placar_mandante,
        dados.placar_visitante,
        dados.mandante_id,
        dados.visitante_id,
    )
    partida = Partida(
        id=_proximo_id_partida(session),
        vencedor_id=vencedor_id,
        **dados.model_dump(),
    )
    session.add(partida)
    session.commit()
    session.refresh(partida)
    return get_partida_by_id(session, partida.id)


def update_partida(
    session: Session, partida_id: int, dados: PartidaUpdate
) -> Optional[Partida]:
    """
    Atualiza campos de uma partida.
    Bloqueado para partidas históricas (ID <= ULTIMO_ID_HISTORICO).
    """
    _verificar_protecao_historica(partida_id, "editar")

    partida = get_partida_by_id(session, partida_id)
    if not partida:
        return None

    campos = dados.model_dump(exclude_none=True)

    if "mandante_id" in campos and not get_clube_by_id(session, campos["mandante_id"]):
        raise ValueError(f"Clube mandante id={campos['mandante_id']} não encontrado.")
    if "visitante_id" in campos and not get_clube_by_id(session, campos["visitante_id"]):
        raise ValueError(f"Clube visitante id={campos['visitante_id']} não encontrado.")
    if "estadio_id" in campos and not get_estadio_by_id(session, campos["estadio_id"]):
        raise ValueError(f"Estádio id={campos['estadio_id']} não encontrado.")

    for campo, valor in campos.items():
        setattr(partida, campo, valor)

    campos_placar = {"placar_mandante", "placar_visitante", "mandante_id", "visitante_id"}
    if campos_placar & set(campos):
        partida.vencedor_id = _calcular_vencedor_id(
            partida.placar_mandante,
            partida.placar_visitante,
            partida.mandante_id,
            partida.visitante_id,
        )

    session.commit()
    return get_partida_by_id(session, partida_id)


def delete_partida(session: Session, partida_id: int) -> bool:
    """
    Remove uma partida do PostgreSQL.
    Bloqueado para partidas históricas (ID <= ULTIMO_ID_HISTORICO).
    """
    _verificar_protecao_historica(partida_id, "deletar")

    partida = session.query(Partida).filter(Partida.id == partida_id).first()
    if not partida:
        return False
    session.delete(partida)
    session.commit()
    return True


# ════════════════════════════════════════════════════════
# CLASSIFICAÇÃO
# ════════════════════════════════════════════════════════

def get_classificacao(session: Session, ano: int) -> List[dict]:
    q = (
        session.query(Partida)
        .options(joinedload(Partida.mandante), joinedload(Partida.visitante))
    )
    partidas = _filtrar_por_temporada(q, ano).all()
    tabela: dict[str, dict] = {}

    def _iniciar(nome: str):
        if nome not in tabela:
            tabela[nome] = dict(
                clube=nome,
                jogos=0, vitorias=0, empates=0, derrotas=0,
                gols_pro=0, gols_contra=0,
            )

    for p in partidas:
        m = p.mandante.nome_oficial
        v = p.visitante.nome_oficial
        _iniciar(m)
        _iniciar(v)
        tabela[m]["jogos"] += 1
        tabela[v]["jogos"] += 1
        tabela[m]["gols_pro"]    += p.placar_mandante
        tabela[m]["gols_contra"] += p.placar_visitante
        tabela[v]["gols_pro"]    += p.placar_visitante
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
    for d in tabela.values():
        d["pontos"]     = d["vitorias"] * 3 + d["empates"]
        d["saldo_gols"] = d["gols_pro"] - d["gols_contra"]
        resultado.append(d)

    resultado.sort(key=lambda x: (-x["pontos"], -x["saldo_gols"], -x["gols_pro"]))
    for i, row in enumerate(resultado, 1):
        row["posicao"] = i
    return resultado


# ════════════════════════════════════════════════════════
# ANOS DISPONÍVEIS
# ════════════════════════════════════════════════════════

def get_anos_disponiveis(session: Session) -> List[int]:
    anos = []
    for ano, (id_min, id_max) in sorted(TEMPORADAS.items(), reverse=True):
        existe = (
            session.query(Partida.id)
            .filter(Partida.id >= id_min, Partida.id <= id_max)
            .first()
        )
        if existe:
            anos.append(ano)
    return anos