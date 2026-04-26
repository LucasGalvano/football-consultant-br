from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import date, time


# ─── CLUBES ───────────────────────────────────────────────────────────────────

class ClubeOut(BaseModel):
    id: int
    nome_oficial: str
    sigla: Optional[str]
    estado: Optional[str]

    class Config:
        from_attributes = True


# ─── ESTÁDIOS ─────────────────────────────────────────────────────────────────

class EstadioOut(BaseModel):
    id: int
    nome: str
    cidade: Optional[str]
    estado: Optional[str]
    capacidade: Optional[int]

    class Config:
        from_attributes = True


# ─── PARTIDAS ─────────────────────────────────────────────────────────────────

class PartidaResumo(BaseModel):
    id: int
    rodada: int
    data: date
    hora: Optional[time]
    mandante: str
    visitante: str
    placar_mandante: int
    placar_visitante: int
    estadio: str
    vencedor: Optional[str]

    class Config:
        from_attributes = True


class PartidaDetalhe(PartidaResumo):
    formacao_mandante: Optional[str]
    formacao_visitante: Optional[str]
    tecnico_mandante: Optional[str]
    tecnico_visitante: Optional[str]
    gols: Optional[List[dict]] = None
    cartoes: Optional[List[dict]] = None
    estatisticas: Optional[dict] = None


# ─── ESTATÍSTICAS ─────────────────────────────────────────────────────────────

class EstatisticasTime(BaseModel):
    nome: str
    estatisticas: dict


class EstatisticasPartida(BaseModel):
    partida_id: int
    rodada: int
    mandante: EstatisticasTime
    visitante: EstatisticasTime


# ─── GOLS ─────────────────────────────────────────────────────────────────────

class GolOut(BaseModel):
    partida_id: int
    minuto: int
    atleta: str
    clube: str
    tipo_gol: Optional[str]
    rodada: int


# ─── CARTÕES ──────────────────────────────────────────────────────────────────

class CartaoOut(BaseModel):
    partida_id: int
    minuto: int
    atleta: str
    tipo_cartao: str
    clube: str
    posicao: Optional[str]
    rodada: int


# ─── RANKINGS / AGREGADOS ─────────────────────────────────────────────────────

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


# ─── PAGINAÇÃO ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    pagina: int
    por_pagina: int
    dados: List[Any]