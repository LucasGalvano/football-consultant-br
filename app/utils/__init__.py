"""
Utilitários do Projeto Consultor Futebol Brasileiro

Funções auxiliares para normalização e limpeza de dados.
"""

from .clubes_normalizacao import (
    CLUBES_OFICIAIS,
    CLUBES_MAP,
    normalizar_clube,
    obter_info_clube
)

from .cleaning_functions import (
    limpar_estadio,
    limpar_unicode,
    limpar_nome_atleta,
    parse_data_brasileira,
    parse_hora,
    normalizar_minuto,
    validar_numero,
    tratar_vazio,
    validar_linha_csv
)

__all__ = [
    # Normalização de clubes
    'CLUBES_OFICIAIS',
    'CLUBES_MAP',
    'normalizar_clube',
    'obter_info_clube',
    
    # Funções de limpeza
    'limpar_estadio',
    'limpar_unicode',
    'limpar_nome_atleta',
    'parse_data_brasileira',
    'parse_hora',
    'normalizar_minuto',
    'validar_numero',
    'tratar_vazio',
    'validar_linha_csv',
]