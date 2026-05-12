"""
Schemas Pydantic para operações de escrita (POST / PUT).

Separados de responses.py para manter responsabilidade única:
- inputs.py  → valida o que ENTRA na API
- responses.py → formata o que SAI da API

Cobre todas as entidades dos 3 bancos:
  PostgreSQL  → ClubeCreate/Update, EstadioCreate/Update, PartidaCreate/Update
  MongoDB     → EstatisticasPartidaCreate
  Cassandra   → GolCreate, CartaoCreate
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional
from datetime import date, time


# ════════════════════════════════════════════════════════
# CLUBES  (PostgreSQL)
# ════════════════════════════════════════════════════════

class ClubeCreate(BaseModel):
    """
    Cria um novo clube.

    Exemplo — Remo promovido à Série A 2026:
    {
        "nome_oficial": "Clube do Remo",
        "sigla": "CRE",
        "estado": "PA",
        "ano_fundacao": 1905
    }
    """
    nome_oficial: str = Field(
        ..., min_length=2, max_length=100,
        examples=["Clube do Remo"],
    )
    sigla: Optional[str] = Field(
        None, max_length=10,
        examples=["CRE"],
    )
    estado: Optional[str] = Field(
        None, min_length=2, max_length=2,
        examples=["PA"],
        description="Sigla do estado (2 letras maiúsculas)",
    )
    ano_fundacao: Optional[int] = Field(
        None, ge=1800, le=2100,
        examples=[1905],
    )

    @field_validator("estado")
    @classmethod
    def estado_maiusculo(cls, v):
        return v.upper() if v else v


class ClubeUpdate(BaseModel):
    """
    Atualiza campos de um clube.
    Todos os campos são opcionais — apenas os enviados são alterados.
    """
    nome_oficial: Optional[str] = Field(None, min_length=2, max_length=100)
    sigla: Optional[str] = Field(None, max_length=10)
    estado: Optional[str] = Field(None, min_length=2, max_length=2)
    ano_fundacao: Optional[int] = Field(None, ge=1800, le=2100)

    @field_validator("estado")
    @classmethod
    def estado_maiusculo(cls, v):
        return v.upper() if v else v


# ════════════════════════════════════════════════════════
# ESTÁDIOS  (PostgreSQL)
# ════════════════════════════════════════════════════════

class EstadioCreate(BaseModel):
    """
    Cria um novo estádio.

    Exemplo:
    {
        "nome": "Estádio Evandro Almeida",
        "cidade": "Belém",
        "estado": "PA",
        "capacidade": 16200
    }
    """
    nome: str = Field(
        ..., min_length=2, max_length=200,
        examples=["Estádio Evandro Almeida"],
    )
    cidade: Optional[str] = Field(None, max_length=100, examples=["Belém"])
    estado: Optional[str] = Field(None, min_length=2, max_length=2, examples=["PA"])
    capacidade: Optional[int] = Field(None, ge=0, examples=[16200])

    @field_validator("estado")
    @classmethod
    def estado_maiusculo(cls, v):
        return v.upper() if v else v


class EstadioUpdate(BaseModel):
    nome: Optional[str] = Field(None, min_length=2, max_length=200)
    cidade: Optional[str] = Field(None, max_length=100)
    estado: Optional[str] = Field(None, min_length=2, max_length=2)
    capacidade: Optional[int] = Field(None, ge=0)

    @field_validator("estado")
    @classmethod
    def estado_maiusculo(cls, v):
        return v.upper() if v else v


# ════════════════════════════════════════════════════════
# PARTIDAS  (PostgreSQL)
# ════════════════════════════════════════════════════════

class PartidaCreate(BaseModel):
    """
    Cria uma nova partida.

    O campo vencedor_id é calculado automaticamente pelo backend
    a partir do placar — não precisa ser informado.

    Exemplo — Remo 2x1 Flamengo, rodada 1 de 2026:
    {
        "rodada": 1,
        "data": "2026-04-12",
        "hora": "16:00",
        "mandante_id": <id do Remo>,
        "visitante_id": <id do Flamengo>,
        "estadio_id": <id do estádio>,
        "placar_mandante": 2,
        "placar_visitante": 1,
        "formacao_mandante": "4-4-2",
        "formacao_visitante": "4-3-3",
        "tecnico_mandante": "Paulo Bonamigo",
        "tecnico_visitante": "Filipe Luís"
    }
    """
    rodada: int = Field(..., ge=1, le=38)
    data: date
    hora: Optional[time] = None

    mandante_id: int = Field(..., gt=0)
    visitante_id: int = Field(..., gt=0)
    estadio_id: int = Field(..., gt=0)

    placar_mandante: int = Field(..., ge=0)
    placar_visitante: int = Field(..., ge=0)

    formacao_mandante: Optional[str] = Field(
        None, max_length=10, examples=["4-4-2"],
    )
    formacao_visitante: Optional[str] = Field(
        None, max_length=10, examples=["4-3-3"],
    )
    tecnico_mandante: Optional[str] = Field(None, max_length=100)
    tecnico_visitante: Optional[str] = Field(None, max_length=100)

    @model_validator(mode="after")
    def times_diferentes(self):
        if self.mandante_id == self.visitante_id:
            raise ValueError("mandante_id e visitante_id não podem ser iguais")
        return self


class PartidaUpdate(BaseModel):
    """
    Atualiza campos de uma partida existente.
    Todos os campos são opcionais.
    Se placar for alterado, vencedor_id é recalculado automaticamente.
    """
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


# ════════════════════════════════════════════════════════
# ESTATÍSTICAS  (MongoDB)
# ════════════════════════════════════════════════════════

class EstatisticasTimeInput(BaseModel):
    """
    Estatísticas de um time em uma partida.
    Todos os campos são opcionais — preencha apenas o que você
    encontrou no Google/Sofascore/FBref.

    Exemplo:
    {
        "chutes": 14,
        "posse_de_bola": 58.5,
        "passes": 423,
        "finalizacoes": 6,
        "escanteios": 5,
        "faltas": 11
    }
    """
    chutes: Optional[int] = Field(None, ge=0)
    chutes_no_alvo: Optional[int] = Field(None, ge=0)
    posse_de_bola: Optional[float] = Field(
        None, ge=0, le=100,
        description="Percentual de posse (ex: 58.5)",
    )
    passes: Optional[int] = Field(None, ge=0)
    passes_completos: Optional[int] = Field(None, ge=0)
    precisao_passes: Optional[float] = Field(None, ge=0, le=100)
    finalizacoes: Optional[int] = Field(None, ge=0)
    finalizacoes_no_alvo: Optional[int] = Field(None, ge=0)
    escanteios: Optional[int] = Field(None, ge=0)
    faltas: Optional[int] = Field(None, ge=0)
    impedimentos: Optional[int] = Field(None, ge=0)
    desarmes: Optional[int] = Field(None, ge=0)

    class Config:
        # Permite campos extras (ex: assistencias, cruzamentos)
        # que não estão listados acima mas podem vir da fonte
        extra = "allow"


class EstatisticasPartidaCreate(BaseModel):
    """
    Cria/substitui o documento de estatísticas de uma partida no MongoDB.
    O partida_id vem pela URL — não precisa ser informado no body.

    Exemplo completo:
    {
        "rodada": 1,
        "mandante_nome": "Clube do Remo",
        "visitante_nome": "Flamengo",
        "mandante_stats": {
            "chutes": 14,
            "posse_de_bola": 58.5,
            "passes": 423,
            "finalizacoes": 6
        },
        "visitante_stats": {
            "chutes": 8,
            "posse_de_bola": 41.5,
            "passes": 301,
            "finalizacoes": 3
        }
    }
    """
    rodada: int = Field(..., ge=1, le=38)
    mandante_nome: str = Field(..., min_length=2, max_length=100)
    visitante_nome: str = Field(..., min_length=2, max_length=100)
    mandante_stats: EstatisticasTimeInput = Field(
        default_factory=EstatisticasTimeInput,
    )
    visitante_stats: EstatisticasTimeInput = Field(
        default_factory=EstatisticasTimeInput,
    )


# ════════════════════════════════════════════════════════
# GOLS  (Cassandra)
# ════════════════════════════════════════════════════════

class GolCreate(BaseModel):
    """
    Adiciona um gol a uma partida no Cassandra.

    tipo_gol aceita: "Normal", "Pênalti", "Gol Contra", "Falta"
    O minuto pode ser acrescimo — ex: 45+2 → informe 47.

    Exemplo:
    {
        "minuto": 23,
        "atleta": "Ytalo",
        "clube": "Clube do Remo",
        "tipo_gol": "Normal",
        "rodada": 1
    }
    """
    minuto: int = Field(
        ..., ge=0, le=150,
        description="Minuto do gol. Acréscimos já somados (45+2 → 47).",
    )
    atleta: str = Field(..., min_length=2, max_length=200)
    clube: str = Field(..., min_length=2, max_length=100)
    tipo_gol: Optional[str] = Field(
        None,
        examples=["Normal", "Pênalti", "Gol Contra", "Falta"],
    )
    rodada: int = Field(..., ge=1, le=38)


# ════════════════════════════════════════════════════════
# CARTÕES  (Cassandra)
# ════════════════════════════════════════════════════════

class CartaoCreate(BaseModel):
    """
    Adiciona um cartão a uma partida no Cassandra.

    tipo_cartao aceita exatamente: "Amarelo" ou "Vermelho"

    Exemplo:
    {
        "minuto": 67,
        "atleta": "Ronald",
        "tipo_cartao": "Amarelo",
        "clube": "Clube do Remo",
        "posicao": "Atacante",
        "rodada": 1
    }
    """
    minuto: int = Field(..., ge=0, le=150)
    atleta: str = Field(..., min_length=2, max_length=200)
    tipo_cartao: str = Field(
        ...,
        pattern="^(Amarelo|Vermelho)$",
        description="Deve ser exatamente 'Amarelo' ou 'Vermelho'",
    )
    clube: str = Field(..., min_length=2, max_length=100)
    posicao: Optional[str] = Field(
        None, max_length=50,
        examples=["Atacante", "Meio-campo", "Zagueiro", "Lateral", "Goleiro"],
    )
    rodada: int = Field(..., ge=1, le=38)