"""
Schemas de Input — operações de escrita (POST / PUT)
======================================================
Separados dos schemas de resposta (responses.py) para seguir o
princípio de responsabilidade única e facilitar validação independente
de entrada vs. saída.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import date, time


# ─── CLUBES ───────────────────────────────────────────────────────────────────

class ClubeCreate(BaseModel):
    nome_oficial: str = Field(..., min_length=2, max_length=100, examples=["Flamengo"])
    sigla: Optional[str] = Field(None, max_length=10, examples=["FLA"])
    estado: Optional[str] = Field(None, min_length=2, max_length=2, examples=["RJ"])
    ano_fundacao: Optional[int] = Field(None, ge=1800, le=2100, examples=[1895])

    @field_validator("estado")
    @classmethod
    def estado_upper(cls, v):
        return v.upper() if v else v


class ClubeUpdate(BaseModel):
    """Todos os campos opcionais — suporta PATCH semântico via PUT."""
    nome_oficial: Optional[str] = Field(None, min_length=2, max_length=100)
    sigla: Optional[str] = Field(None, max_length=10)
    estado: Optional[str] = Field(None, min_length=2, max_length=2)
    ano_fundacao: Optional[int] = Field(None, ge=1800, le=2100)

    @field_validator("estado")
    @classmethod
    def estado_upper(cls, v):
        return v.upper() if v else v


# ─── ESTÁDIOS ─────────────────────────────────────────────────────────────────

class EstadioCreate(BaseModel):
    nome: str = Field(..., min_length=2, max_length=200, examples=["Maracanã"])
    cidade: Optional[str] = Field(None, max_length=100, examples=["Rio de Janeiro"])
    estado: Optional[str] = Field(None, min_length=2, max_length=2, examples=["RJ"])
    capacidade: Optional[int] = Field(None, ge=0, examples=[78838])

    @field_validator("estado")
    @classmethod
    def estado_upper(cls, v):
        return v.upper() if v else v


class EstadioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=200)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, min_length=2, max_length=2)
    capacidade: Optional[int] = Field(None, ge=0)

    @field_validator("estado")
    @classmethod
    def estado_upper(cls, v):
        return v.upper() if v else v


# ─── PARTIDAS ─────────────────────────────────────────────────────────────────

class PartidaCreate(BaseModel):
    rodada: int = Field(..., ge=1, le=38)
    data: date
    hora: Optional[time] = None

    mandante_id: int = Field(..., gt=0)
    visitante_id: int = Field(..., gt=0)
    estadio_id: int = Field(..., gt=0)

    placar_mandante: int = Field(..., ge=0)
    placar_visitante: int = Field(..., ge=0)

    formacao_mandante: Optional[str] = Field(None, max_length=10, examples=["4-3-3"])
    formacao_visitante: Optional[str] = Field(None, max_length=10, examples=["4-4-2"])
    tecnico_mandante: Optional[str] = Field(None, max_length=100)
    tecnico_visitante: Optional[str] = Field(None, max_length=100)

    @field_validator("visitante_id")
    @classmethod
    def times_diferentes(cls, v, info):
        if "mandante_id" in info.data and v == info.data["mandante_id"]:
            raise ValueError("mandante_id e visitante_id não podem ser iguais")
        return v


class PartidaUpdate(BaseModel):
    rodada: Optional[int] = Field(None, ge=1, le=38)
    data: Optional[date] = None
    hora: Optional[time] = None

    mandante_id: Optional[int] = Field(None, gt=0)
    visitante_id: Optional[int] = Field(None, gt=0)
    estadio_id: Optional[int] = Field(None, gt=0)

    placar_mandante: Optional[int] = Field(None, ge=0)
    placar_visitante: Optional[int] = Field(None, ge=0)

    formacao_mandante: Optional[str] = Field(None, max_length=10)
    formacao_visitante: Optional[str] = Field(None, max_length=10)
    tecnico_mandante: Optional[str] = Field(None, max_length=100)
    tecnico_visitante: Optional[str] = Field(None, max_length=100)


# ─── MONGODB — Estatísticas ────────────────────────────────────────────────────

class EstatisticasTimeInput(BaseModel):
    """Estatísticas de um time em uma partida — todos opcionais."""
    chutes: Optional[int] = Field(None, ge=0)
    passes: Optional[int] = Field(None, ge=0)
    passes_completos: Optional[int] = Field(None, ge=0)
    precisao_passes: Optional[float] = Field(None, ge=0, le=100)
    posse_de_bola: Optional[float] = Field(None, ge=0, le=100)
    finalizacoes: Optional[int] = Field(None, ge=0)
    finalizacoes_no_alvo: Optional[int] = Field(None, ge=0)
    escanteios: Optional[int] = Field(None, ge=0)
    faltas: Optional[int] = Field(None, ge=0)
    desarmes: Optional[int] = Field(None, ge=0)
    impedimentos: Optional[int] = Field(None, ge=0)

    class Config:
        extra = "allow"


class EstatisticasPartidaCreate(BaseModel):
    """
    Cria/substitui o documento de estatísticas de uma partida no MongoDB.
    O partida_id deve referenciar uma partida existente no PostgreSQL.
    """
    mandante_nome: str = Field(..., min_length=2)
    visitante_nome: str = Field(..., min_length=2)
    rodada: int = Field(..., ge=1, le=38)
    mandante_stats: EstatisticasTimeInput = Field(default_factory=EstatisticasTimeInput)
    visitante_stats: EstatisticasTimeInput = Field(default_factory=EstatisticasTimeInput)


# ─── CASSANDRA — Gols e Cartões ────────────────────────────────────────────────

class GolCreate(BaseModel):
    minuto: int = Field(..., ge=0, le=150)
    atleta: str = Field(..., min_length=2, max_length=200)
    clube: str = Field(..., min_length=2, max_length=100)
    tipo_gol: Optional[str] = Field(None, examples=["Normal", "Pênalti", "Gol Contra"])
    rodada: int = Field(..., ge=1, le=38)


class CartaoCreate(BaseModel):
    minuto: int = Field(..., ge=0, le=150)
    atleta: str = Field(..., min_length=2, max_length=200)
    tipo_cartao: str = Field(..., pattern="^(Amarelo|Vermelho)$")
    clube: str = Field(..., min_length=2, max_length=100)
    posicao: Optional[str] = Field(None, max_length=50)
    rodada: int = Field(..., ge=1, le=38)