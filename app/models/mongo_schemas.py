"""
Schemas Pydantic para MongoDB
==============================
Define a estrutura dos documentos JSON armazenados no MongoDB.

Collections:
- partidas_estatisticas: Estatísticas de cada partida (mandante + visitante)
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# SCHEMA: ESTATÍSTICAS DE UM TIME EM UMA PARTIDA

class EstatisticasTime(BaseModel):
    """
    Estatísticas de um time em uma partida específica.
    
    Campos podem ser opcionais pois nem todas as partidas têm dados completos.
    """
    chutes: Optional[int] = None
    chutes_bola_parada: Optional[int] = None
    chutes_bola_parada_a_gol: Optional[int] = None
    passes: Optional[int] = None
    passes_completos: Optional[int] = None
    precisao_passes: Optional[float] = None  # Percentual (ex: 87.5)
    assistencias: Optional[int] = None
    finalizacoes: Optional[int] = None
    finalizacoes_no_alvo: Optional[int] = None
    finalizacoes_defendidas: Optional[int] = None
    finalizacoes_na_trave: Optional[int] = None
    desarmes: Optional[int] = None
    impedimentos: Optional[int] = None
    escanteios: Optional[int] = None
    cruzamentos: Optional[int] = None
    tiro_livre: Optional[int] = None
    lateral: Optional[int] = None
    faltas: Optional[int] = None
    posse_de_bola: Optional[float] = None  # Percentual (ex: 58.5)
    
    class Config:
        # Permite campos extras não definidos no schema
        extra = "allow"


# SCHEMA: DADOS DE UM TIME NA PARTIDA (nome + estatísticas)

class TimePartida(BaseModel):
    """
    Representa um time (mandante ou visitante) em uma partida.
    
    Inclui nome do clube e suas estatísticas.
    """
    nome: str = Field(..., description="Nome oficial do clube")
    placar: Optional[int] = Field(None, description="Gols marcados")
    estatisticas: EstatisticasTime = Field(
        default_factory=EstatisticasTime,
        description="Estatísticas do time na partida"
    )


# SCHEMA: DOCUMENTO COMPLETO DA PARTIDA

class PartidaEstatisticas(BaseModel):
    """
    Documento completo de uma partida com estatísticas.
    
    Estrutura:
    {
      "partida_id": 5000,
      "rodada": 10,
      "data": "2020-08-15",
      "ano": 2020,
      "mandante": { ... },
      "visitante": { ... }
    }
    """
    partida_id: int = Field(..., description="ID da partida (referência ao PostgreSQL)")
    rodada: int = Field(..., description="Número da rodada")
    data: datetime = Field(..., description="Data da partida")
    ano: int = Field(..., description="Ano da temporada")
    
    mandante: TimePartida = Field(..., description="Time mandante com estatísticas")
    visitante: TimePartida = Field(..., description="Time visitante com estatísticas")
    
    class Config:
        # Configuração para serialização JSON
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        # Exemplo de documento
        schema_extra = {
            "example": {
                "partida_id": 5000,
                "rodada": 10,
                "data": "2020-08-15T00:00:00",
                "ano": 2020,
                "mandante": {
                    "nome": "Flamengo",
                    "placar": 3,
                    "estatisticas": {
                        "chutes": 18,
                        "passes": 512,
                        "posse_de_bola": 65.5,
                        "finalizacoes": 8,
                        "escanteios": 7
                    }
                },
                "visitante": {
                    "nome": "Palmeiras",
                    "placar": 1,
                    "estatisticas": {
                        "chutes": 10,
                        "passes": 287,
                        "posse_de_bola": 34.5,
                        "finalizacoes": 3,
                        "escanteios": 2
                    }
                }
            }
        }


# FUNÇÕES AUXILIARES

def criar_documento_partida(
    partida_id: int,
    rodada: int,
    data: datetime,
    mandante_nome: str,
    visitante_nome: str,
    mandante_stats: dict,
    visitante_stats: dict
) -> dict:
    """
    Cria um documento de partida validado.
    
    Args:
        partida_id: ID da partida
        rodada: Número da rodada
        data: Data da partida
        mandante_nome: Nome do time mandante
        visitante_nome: Nome do time visitante
        mandante_stats: Dicionário com estatísticas do mandante
        visitante_stats: Dicionário com estatísticas do visitante
    
    Returns:
        Dicionário validado pronto para inserir no MongoDB
    """
    # Criar e validar usando Pydantic
    partida = PartidaEstatisticas(
        partida_id=partida_id,
        rodada=rodada,
        data=data,
        ano=data.year,
        mandante=TimePartida(
            nome=mandante_nome,
            estatisticas=EstatisticasTime(**mandante_stats)
        ),
        visitante=TimePartida(
            nome=visitante_nome,
            estatisticas=EstatisticasTime(**visitante_stats)
        )
    )
    
    # Retornar como dicionário (dict)
    return partida.dict(exclude_none=True)


# TESTE (executar apenas se rodar diretamente)

if __name__ == "__main__":
    import json
    
    print("=" * 80)
    print("TESTE DOS SCHEMAS MONGODB")
    print("=" * 80)
    
    # Criar documento de exemplo
    doc_exemplo = criar_documento_partida(
        partida_id=5000,
        rodada=10,
        data=datetime(2020, 8, 15),
        mandante_nome="Flamengo",
        visitante_nome="Palmeiras",
        mandante_stats={
            "chutes": 18,
            "passes": 512,
            "posse_de_bola": 65.5,
            "finalizacoes": 8,
            "escanteios": 7
        },
        visitante_stats={
            "chutes": 10,
            "passes": 287,
            "posse_de_bola": 34.5,
            "finalizacoes": 3,
            "escanteios": 2
        }
    )
    
    print("\nDocumento de exemplo criado:")
    print(json.dumps(doc_exemplo, indent=2, default=str))
    
    # Validar schema
    try:
        partida_validada = PartidaEstatisticas(**doc_exemplo)
        print("\nSchema validado com sucesso!")
        print(f"   Partida ID: {partida_validada.partida_id}")
        print(f"   Mandante: {partida_validada.mandante.nome}")
        print(f"   Visitante: {partida_validada.visitante.nome}")
        print(f"   Posse mandante: {partida_validada.mandante.estatisticas.posse_de_bola}%")
    except Exception as e:
        print(f"\nErro na validação: {e}")
    
    print("\n" + "=" * 80)
    print("Schemas prontos para uso!")
    print("=" * 80)
