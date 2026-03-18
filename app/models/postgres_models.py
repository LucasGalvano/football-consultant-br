"""
Modelos SQLAlchemy para PostgreSQL
===================================
Define as tabelas relacionais do projeto.

Tabelas:
- clubes: Times do brasileirão
- estadios: Estádios/arenas
- partidas: Partidas do campeonato
"""

from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, CHAR
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()


# MODELO: CLUBES

class Clube(Base):
    """
    Representa um clube de futebol.
    
    Tabela mestre que armazena todos os clubes únicos.
    """
    __tablename__ = 'clubes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome_oficial = Column(String(100), unique=True, nullable=False, index=True)
    sigla = Column(String(10), nullable=True)
    estado = Column(CHAR(2), nullable=True)
    
    # Relacionamentos (back_populates)
    partidas_mandante = relationship(
        "Partida", 
        foreign_keys="Partida.mandante_id",
        back_populates="mandante"
    )
    partidas_visitante = relationship(
        "Partida", 
        foreign_keys="Partida.visitante_id",
        back_populates="visitante"
    )
    partidas_vencedor = relationship(
        "Partida", 
        foreign_keys="Partida.vencedor_id",
        back_populates="vencedor"
    )
    
    def __repr__(self):
        return f"<Clube(id={self.id}, nome='{self.nome_oficial}', sigla='{self.sigla}')>"


# MODELO: ESTADIOS

class Estadio(Base):
    """
    Representa um estádio/arena.
    
    Armazena informações dos locais onde as partidas acontecem.
    """
    __tablename__ = 'estadios'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(200), unique=True, nullable=False, index=True)
    cidade = Column(String(100), nullable=True)
    estado = Column(CHAR(2), nullable=True)
    capacidade = Column(Integer, nullable=True)
    
    # Relacionamento
    partidas = relationship("Partida", back_populates="estadio")
    
    def __repr__(self):
        return f"<Estadio(id={self.id}, nome='{self.nome}')>"


# MODELO: PARTIDAS

class Partida(Base):
    """
    Representa uma partida do campeonato brasileiro.
    
    Contém informações sobre data, times, placar e resultado.
    """
    __tablename__ = 'partidas'
    
    # ID é o mesmo do CSV (não auto-increment)
    id = Column(Integer, primary_key=True, autoincrement=False)
    
    # Informações temporais
    rodada = Column(Integer, nullable=False)
    data = Column(Date, nullable=False, index=True)
    hora = Column(Time, nullable=True)
    
    # Foreign Keys - Times
    mandante_id = Column(Integer, ForeignKey('clubes.id'), nullable=False, index=True)
    visitante_id = Column(Integer, ForeignKey('clubes.id'), nullable=False, index=True)
    vencedor_id = Column(Integer, ForeignKey('clubes.id'), nullable=True)  # NULL = empate
    
    # Foreign Key - Estádio
    estadio_id = Column(Integer, ForeignKey('estadios.id'), nullable=False)
    
    # Placar
    placar_mandante = Column(Integer, nullable=False)
    placar_visitante = Column(Integer, nullable=False)
    
    # Informações táticas (podem ser NULL)
    formacao_mandante = Column(String(10), nullable=True)
    formacao_visitante = Column(String(10), nullable=True)
    tecnico_mandante = Column(String(100), nullable=True)
    tecnico_visitante = Column(String(100), nullable=True)
    
    # Relacionamentos
    mandante = relationship("Clube", foreign_keys=[mandante_id], back_populates="partidas_mandante")
    visitante = relationship("Clube", foreign_keys=[visitante_id], back_populates="partidas_visitante")
    vencedor = relationship("Clube", foreign_keys=[vencedor_id], back_populates="partidas_vencedor")
    estadio = relationship("Estadio", back_populates="partidas")
    
    def __repr__(self):
        return (
            f"<Partida(id={self.id}, "
            f"mandante_id={self.mandante_id}, "
            f"visitante_id={self.visitante_id}, "
            f"placar={self.placar_mandante}x{self.placar_visitante})>"
        )
    
    @property
    def resultado(self):
        """Retorna 'V' (vitória mandante), 'E' (empate) ou 'D' (derrota mandante)"""
        if self.placar_mandante > self.placar_visitante:
            return 'V'
        elif self.placar_mandante < self.placar_visitante:
            return 'D'
        else:
            return 'E'


# FUNÇÃO AUXILIAR: CRIAR TODAS AS TABELAS

def criar_tabelas(engine):
    """
    Cria todas as tabelas no banco de dados.
    
    Args:
        engine: SQLAlchemy engine conectado ao PostgreSQL
    """
    print("Criando tabelas no PostgreSQL...")
    Base.metadata.create_all(engine)
    print("Tabelas criadas com sucesso!")


def dropar_tabelas(engine):
    """
    Remove todas as tabelas do banco de dados.
    
    CUIDADO: Isso apaga todos os dados!
    
    Args:
        engine: SQLAlchemy engine conectado ao PostgreSQL
    """
    print("ATENÇÃO: Removendo todas as tabelas...")
    Base.metadata.drop_all(engine)
    print("Tabelas removidas!")


# TESTE (executar apenas se rodar diretamente)

if __name__ == "__main__":
    from sqlalchemy import create_engine
    from app.config.settings import settings
    
    # Criar engine
    DATABASE_URL = (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
    
    engine = create_engine(DATABASE_URL, echo=True)
    
    print("=" * 80)
    print("TESTE DOS MODELOS POSTGRESQL")
    print("=" * 80)
    
    # Criar tabelas
    criar_tabelas(engine)
    
    # Verificar tabelas criadas
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tabelas = inspector.get_table_names()
    
    print(f"\nTabelas criadas: {tabelas}")
    
    print("\n" + "=" * 80)
    print("Modelos prontos para uso!")
    print("=" * 80)
