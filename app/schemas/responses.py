"""
Schemas Pydantic para respostas da API (saída).
"""

from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date, time


# ────────────────────────────────────────────────────────────
# CLUBES
# ────────────────────────────────────────────────────────────

class ClubeOut(BaseModel):
    id: int
    nome_oficial: str
    sigla: Optional[str] = None
    estado: Optional[str] = None
    ano_fundacao: Optional[int] = None

    class Config:
        from_attributes = True


# ────────────────────────────────────────────────────────────
# ESTÁDIOS
# ────────────────────────────────────────────────────────────

class EstadioOut(BaseModel):
    id: int
    nome: str
    cidade: Optional[str] = None
    estado: Optional[str] = None
    capacidade: Optional[int] = None

    class Config:
        from_attributes = True


# ────────────────────────────────────────────────────────────
# PARTIDAS
# ────────────────────────────────────────────────────────────

class PartidaResumo(BaseModel):
    id: int
    rodada: int
    data: date
    hora: Optional[time] = None
    mandante: str
    visitante: str
    placar_mandante: int
    placar_visitante: int
    estadio: str
    vencedor: Optional[str] = None

    class Config:
        from_attributes = True


class PartidaDetalhe(PartidaResumo):
    formacao_mandante: Optional[str] = None
    formacao_visitante: Optional[str] = None
    tecnico_mandante: Optional[str] = None
    tecnico_visitante: Optional[str] = None
    gols: Optional[List[dict]] = None
    cartoes: Optional[List[dict]] = None
    estatisticas: Optional[dict] = None


# ────────────────────────────────────────────────────────────
# RANKINGS / AGREGADOS
# ────────────────────────────────────────────────────────────

class ArtilheiroOut(BaseModel):
    atleta: str
    clube: str
    total_gols: int


class ClassificacaoOut(BaseModel):
    posicao: int
    clube: str
    jogos: int
    vitorias: int
    empates: int
    derrotas: int
    gols_pro: int
    gols_contra: int
    saldo_gols: int
    pontos: int


class RankingCartoesOut(BaseModel):
    atleta: str
    clube: str
    total_cartoes: int
    amarelos: int
    vermelhos: int


# ────────────────────────────────────────────────────────────
# PAGINAÇÃO
# ────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    dados: List[Any]


# ────────────────────────────────────────────────────────────
# RESPOSTAS DE ESCRITA
# ────────────────────────────────────────────────────────────

class DeletePartidaOut(BaseModel):
    """Retorno do DELETE /partidas/{id} — resume o que foi removido nos 3 bancos."""
    partida_id: int
    removido: bool
    detalhes: dict