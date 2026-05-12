"""
Repository Cassandra / AstraDB
CRUD completo para gols_por_partida e cartoes_por_partida.

PROTEÇÃO HISTÓRICA:
  Partidas com ID <= 8785 (temporadas até 2024, vindas dos CSVs) são
  imutáveis — delete e update são bloqueados com HistoricalDataError.
  Apenas partidas criadas via API (ID >= 9000) podem ser modificadas.

ALTERAÇÕES v2:
  - Gap 1 corrigido: delete_gol individual agora exposto via função pública.
  - Gap 2 adicionado: update_gol e update_cartao (delete + insert).
  - Constante ULTIMO_ID_HISTORICO centraliza o limite de proteção.
"""

from cassandra.cluster import Session as CassandraSession
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from app.schemas.inputs import GolCreate, CartaoCreate


# ════════════════════════════════════════════════════════
# PROTEÇÃO DE DADOS HISTÓRICOS
# ════════════════════════════════════════════════════════

# IDs vindos dos CSVs do dataset público (temporadas 2014–2024).
# Qualquer operação de escrita/delete sobre essas partidas é bloqueada.
ULTIMO_ID_HISTORICO = 8785


class HistoricalDataError(ValueError):
    """Lançada ao tentar modificar uma partida histórica (CSV 2014–2024)."""
    pass


def _verificar_protecao_historica(partida_id: int, operacao: str = "modificar") -> None:
    """
    Levanta HistoricalDataError se partida_id pertence ao dataset histórico.

    Args:
        partida_id: ID da partida alvo.
        operacao: Descrição da operação para mensagem de erro ("deletar", "editar"…).
    """
    if partida_id <= ULTIMO_ID_HISTORICO:
        raise HistoricalDataError(
            f"Não é permitido {operacao} dados históricos. "
            f"A partida {partida_id} faz parte do dataset oficial (2014–2024, "
            f"IDs até {ULTIMO_ID_HISTORICO}). "
            "Apenas partidas criadas via API (ID >= 9000) podem ser alteradas."
        )


# ════════════════════════════════════════════════════════
# HELPERS INTERNOS
# ════════════════════════════════════════════════════════

def _buscar_gols_partida(session: CassandraSession, partida_id: int) -> List:
    rows = session.execute(
        "SELECT atleta, clube, tipo_gol "
        "FROM gols_por_partida WHERE partida_id = %s",
        (partida_id,),
    )
    return list(rows)


def _buscar_cartoes_partida(session: CassandraSession, partida_id: int) -> List:
    rows = session.execute(
        "SELECT atleta, tipo_cartao, clube "
        "FROM cartoes_por_partida WHERE partida_id = %s",
        (partida_id,),
    )
    return list(rows)


def _clube_principal(clubes_contagem: dict) -> str:
    if not clubes_contagem:
        return ""
    return max(clubes_contagem, key=clubes_contagem.get)


# ════════════════════════════════════════════════════════
# GOLS — READ
# ════════════════════════════════════════════════════════

def get_gols_partida(
    session: CassandraSession, partida_id: int
) -> List[dict]:
    """Retorna todos os gols de uma partida, ordenados por minuto."""
    rows = session.execute(
        "SELECT partida_id, minuto, atleta, clube, tipo_gol, rodada "
        "FROM gols_por_partida WHERE partida_id = %s",
        (partida_id,),
    )
    return [dict(r._asdict()) for r in rows]


def get_gol_individual(
    session: CassandraSession,
    partida_id: int,
    minuto: int,
    atleta: str,
) -> Optional[dict]:
    """
    Retorna um gol específico pela chave completa (partida_id, minuto, atleta).
    Retorna None se não existir.
    """
    row = session.execute(
        "SELECT partida_id, minuto, atleta, clube, tipo_gol, rodada "
        "FROM gols_por_partida "
        "WHERE partida_id = %s AND minuto = %s AND atleta = %s",
        (partida_id, minuto, atleta),
    ).one()
    return dict(row._asdict()) if row else None


def get_artilheiros(
    session: CassandraSession,
    limite: int = 10,
    partida_ids: Optional[List[int]] = None,
) -> List[dict]:
    """
    Retorna os artilheiros ordenados por total de gols.
    Gols contra são excluídos da contagem.
    partida_ids deve sempre ser fornecido pelo router (obtido do PostgreSQL).
    """
    if not partida_ids:
        return []

    contagem: dict = defaultdict(
        lambda: {"total_gols": 0, "clubes": defaultdict(int)}
    )

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(_buscar_gols_partida, session, pid): pid
            for pid in partida_ids
        }
        for future in as_completed(futures):
            try:
                for r in future.result():
                    if r.tipo_gol != "Gol Contra":
                        contagem[r.atleta]["total_gols"] += 1
                        contagem[r.atleta]["clubes"][r.clube] += 1
            except Exception:
                pass

    resultado = [
        {
            "atleta":     atleta,
            "clube":      _clube_principal(dados["clubes"]),
            "total_gols": dados["total_gols"],
        }
        for atleta, dados in contagem.items()
    ]
    resultado.sort(key=lambda x: -x["total_gols"])
    return resultado[:limite]


def get_gols_clube_partidas(
    session: CassandraSession,
    clube: str,
    partida_ids: List[int],
) -> List[dict]:
    resultado = []
    for pid in partida_ids:
        rows = session.execute(
            "SELECT partida_id, minuto, atleta, clube, tipo_gol, rodada "
            "FROM gols_por_partida WHERE partida_id = %s",
            (pid,),
        )
        for r in rows:
            if r.clube == clube:
                resultado.append(dict(r._asdict()))
    return resultado


# ════════════════════════════════════════════════════════
# CARTÕES — READ
# ════════════════════════════════════════════════════════

def get_cartoes_partida(
    session: CassandraSession, partida_id: int
) -> List[dict]:
    """Retorna todos os cartões de uma partida, ordenados por minuto."""
    rows = session.execute(
        "SELECT partida_id, minuto, atleta, tipo_cartao, clube, posicao, rodada "
        "FROM cartoes_por_partida WHERE partida_id = %s",
        (partida_id,),
    )
    return [dict(r._asdict()) for r in rows]


def get_cartao_individual(
    session: CassandraSession,
    partida_id: int,
    minuto: int,
    atleta: str,
    tipo_cartao: str,
) -> Optional[dict]:
    """
    Retorna um cartão específico pela chave completa
    (partida_id, minuto, atleta, tipo_cartao).
    Retorna None se não existir.
    """
    row = session.execute(
        "SELECT partida_id, minuto, atleta, tipo_cartao, clube, posicao, rodada "
        "FROM cartoes_por_partida "
        "WHERE partida_id = %s AND minuto = %s AND atleta = %s AND tipo_cartao = %s",
        (partida_id, minuto, atleta, tipo_cartao),
    ).one()
    return dict(row._asdict()) if row else None


def get_ranking_cartoes(
    session: CassandraSession,
    limite: int = 10,
    partida_ids: Optional[List[int]] = None,
    tipo: Optional[str] = None,
) -> List[dict]:
    if not partida_ids:
        return []

    contagem: dict = defaultdict(
        lambda: {"amarelos": 0, "vermelhos": 0, "clubes": defaultdict(int)}
    )

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(_buscar_cartoes_partida, session, pid): pid
            for pid in partida_ids
        }
        for future in as_completed(futures):
            try:
                for r in future.result():
                    contagem[r.atleta]["clubes"][r.clube] += 1
                    if r.tipo_cartao == "Amarelo":
                        contagem[r.atleta]["amarelos"] += 1
                    elif r.tipo_cartao == "Vermelho":
                        contagem[r.atleta]["vermelhos"] += 1
            except Exception:
                pass

    resultado = [
        {
            "atleta":        atleta,
            "clube":         _clube_principal(dados["clubes"]),
            "amarelos":      dados["amarelos"],
            "vermelhos":     dados["vermelhos"],
            "total_cartoes": dados["amarelos"] + dados["vermelhos"],
        }
        for atleta, dados in contagem.items()
    ]

    if tipo == "Amarelo":
        resultado.sort(key=lambda x: -x["amarelos"])
    elif tipo == "Vermelho":
        resultado.sort(key=lambda x: -x["vermelhos"])
    else:
        resultado.sort(key=lambda x: -x["total_cartoes"])

    return resultado[:limite]


# ════════════════════════════════════════════════════════
# GOLS — WRITE
# ════════════════════════════════════════════════════════

def create_gol(
    session: CassandraSession,
    partida_id: int,
    dados: GolCreate,
) -> dict:
    """
    Insere um gol.
    Bloqueado para partidas históricas (ID <= ULTIMO_ID_HISTORICO).
    """
    _verificar_protecao_historica(partida_id, "adicionar gols em")

    stmt = session.prepare(
        "INSERT INTO gols_por_partida "
        "(partida_id, minuto, atleta, clube, tipo_gol, rodada) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )
    session.execute(stmt, (
        partida_id,
        dados.minuto,
        dados.atleta,
        dados.clube,
        dados.tipo_gol,
        dados.rodada,
    ))
    return {
        "partida_id": partida_id,
        "minuto":     dados.minuto,
        "atleta":     dados.atleta,
        "clube":      dados.clube,
        "tipo_gol":   dados.tipo_gol,
        "rodada":     dados.rodada,
    }


def update_gol(
    session: CassandraSession,
    partida_id: int,
    minuto_original: int,
    atleta_original: str,
    dados: GolCreate,
) -> Optional[dict]:
    """
    Atualiza um gol via delete + insert (padrão Cassandra).
    Retorna None se o gol original não existir.
    Bloqueado para partidas históricas.

    Se a chave mudar (minuto ou atleta diferentes), o registro antigo
    é removido e um novo é criado com a nova chave.
    """
    _verificar_protecao_historica(partida_id, "editar gols de")

    existia = delete_gol(session, partida_id, minuto_original, atleta_original)
    if not existia:
        return None

    return create_gol(session, partida_id, dados)


def delete_gol(
    session: CassandraSession,
    partida_id: int,
    minuto: int,
    atleta: str,
) -> bool:
    """
    Remove um gol específico pela chave composta (partida_id, minuto, atleta).
    Retorna True se existia, False se não encontrou.
    Bloqueado para partidas históricas.
    """
    _verificar_protecao_historica(partida_id, "deletar gols de")

    existia = session.execute(
        "SELECT atleta FROM gols_por_partida "
        "WHERE partida_id = %s AND minuto = %s AND atleta = %s",
        (partida_id, minuto, atleta),
    ).one()

    if not existia:
        return False

    session.execute(
        "DELETE FROM gols_por_partida "
        "WHERE partida_id = %s AND minuto = %s AND atleta = %s",
        (partida_id, minuto, atleta),
    )
    return True


def delete_gols_partida(
    session: CassandraSession, partida_id: int
) -> int:
    """
    Remove TODOS os gols de uma partida.
    Bloqueado para partidas históricas.
    Retorna a quantidade removida.
    """
    _verificar_protecao_historica(partida_id, "deletar gols de")

    existentes = get_gols_partida(session, partida_id)
    count = len(existentes)
    if count > 0:
        session.execute(
            "DELETE FROM gols_por_partida WHERE partida_id = %s",
            (partida_id,),
        )
    return count


# ════════════════════════════════════════════════════════
# CARTÕES — WRITE
# ════════════════════════════════════════════════════════

def create_cartao(
    session: CassandraSession,
    partida_id: int,
    dados: CartaoCreate,
) -> dict:
    """
    Insere um cartão.
    Bloqueado para partidas históricas.
    """
    _verificar_protecao_historica(partida_id, "adicionar cartões em")

    stmt = session.prepare(
        "INSERT INTO cartoes_por_partida "
        "(partida_id, minuto, atleta, tipo_cartao, clube, posicao, rodada) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    session.execute(stmt, (
        partida_id,
        dados.minuto,
        dados.atleta,
        dados.tipo_cartao,
        dados.clube,
        dados.posicao,
        dados.rodada,
    ))
    return {
        "partida_id":  partida_id,
        "minuto":      dados.minuto,
        "atleta":      dados.atleta,
        "tipo_cartao": dados.tipo_cartao,
        "clube":       dados.clube,
        "posicao":     dados.posicao,
        "rodada":      dados.rodada,
    }


def update_cartao(
    session: CassandraSession,
    partida_id: int,
    minuto_original: int,
    atleta_original: str,
    tipo_cartao_original: str,
    dados: CartaoCreate,
) -> Optional[dict]:
    """
    Atualiza um cartão via delete + insert.
    Retorna None se o cartão original não existir.
    Bloqueado para partidas históricas.
    """
    _verificar_protecao_historica(partida_id, "editar cartões de")

    existia = delete_cartao_individual(
        session, partida_id, minuto_original, atleta_original, tipo_cartao_original
    )
    if not existia:
        return None

    return create_cartao(session, partida_id, dados)


def delete_cartao_individual(
    session: CassandraSession,
    partida_id: int,
    minuto: int,
    atleta: str,
    tipo_cartao: str,
) -> bool:
    """
    Remove um cartão específico pela chave completa
    (partida_id, minuto, atleta, tipo_cartao).
    Retorna True se existia, False caso contrário.
    Bloqueado para partidas históricas.
    """
    _verificar_protecao_historica(partida_id, "deletar cartões de")

    existia = session.execute(
        "SELECT atleta FROM cartoes_por_partida "
        "WHERE partida_id = %s AND minuto = %s "
        "AND atleta = %s AND tipo_cartao = %s",
        (partida_id, minuto, atleta, tipo_cartao),
    ).one()

    if not existia:
        return False

    session.execute(
        "DELETE FROM cartoes_por_partida "
        "WHERE partida_id = %s AND minuto = %s "
        "AND atleta = %s AND tipo_cartao = %s",
        (partida_id, minuto, atleta, tipo_cartao),
    )
    return True


def delete_cartoes_partida(
    session: CassandraSession, partida_id: int
) -> int:
    """
    Remove TODOS os cartões de uma partida.
    Bloqueado para partidas históricas.
    Retorna a quantidade removida.
    """
    _verificar_protecao_historica(partida_id, "deletar cartões de")

    existentes = get_cartoes_partida(session, partida_id)
    count = len(existentes)
    if count > 0:
        session.execute(
            "DELETE FROM cartoes_por_partida WHERE partida_id = %s",
            (partida_id,),
        )
    return count