"""
Dicionário de Normalização de Clubes do Brasileirão

Mapeia todas as variações de nomes encontradas nos datasets para um nome oficial único.

Uso:    
    nome_limpo = normalizar_clube("Athletico-PR")  # retorna "Athletico Paranaense"
"""

# DICIONÁRIO PRINCIPAL: Nome Oficial de Cada Clube
CLUBES_OFICIAIS = {
    "america_mineiro": {
        "nome_oficial": "América Mineiro",
        "sigla": "AME",
        "estado": "MG",
        "variantes": ["America-MG", "América-MG", "América Mineiro"]
    },
    "america_natal": {
        "nome_oficial": "América de Natal",
        "sigla": "AME-RN",
        "estado": "RN",
        "variantes": ["America-RN", "América-RN", "América RN"]
    },
    "athletico_paranaense": {
        "nome_oficial": "Athletico Paranaense",
        "sigla": "CAP",
        "estado": "PR",
        "variantes": [
            "Athletico-PR", 
            "Atletico-PR", 
            "Atlético-PR", 
            "ATLÉTICO-PR",
            "Athletico Paranaense"
        ]
    },
    "atletico_goianiense": {
        "nome_oficial": "Atlético Goianiense",
        "sigla": "ACG",
        "estado": "GO",
        "variantes": ["Atletico-GO", "Atlético-GO", "Atlético Goianiense"]
    },
    "atletico_mineiro": {
        "nome_oficial": "Atlético Mineiro",
        "sigla": "CAM",
        "estado": "MG",
        "variantes": ["Atletico-MG", "Atlético-MG", "Atlético Mineiro"]
    },
    "avai": {
        "nome_oficial": "Avaí",
        "sigla": "AVA",
        "estado": "SC",
        "variantes": ["Avai", "Avaí"]
    },
    "bahia": {
        "nome_oficial": "Bahia",
        "sigla": "BAH",
        "estado": "BA",
        "variantes": ["Bahia"]
    },
    "barueri": {
        "nome_oficial": "Grêmio Barueri",
        "sigla": "GBA",
        "estado": "SP",
        "variantes": ["Barueri", "Grêmio Barueri"]
    },
    "botafogo": {
        "nome_oficial": "Botafogo",
        "sigla": "BOT",
        "estado": "RJ",
        "variantes": ["Botafogo-RJ", "Botafogo"]
    },
    "bragantino": {
        "nome_oficial": "Red Bull Bragantino",
        "sigla": "RBB",
        "estado": "SP",
        "variantes": ["Bragantino", "Red Bull Bragantino", "RB Bragantino"]
    },
    "brasiliense": {
        "nome_oficial": "Brasiliense",
        "sigla": "BRA",
        "estado": "DF",
        "variantes": ["Brasiliense"]
    },
    "ceara": {
        "nome_oficial": "Ceará",
        "sigla": "CEA",
        "estado": "CE",
        "variantes": ["Ceara", "Ceará"]
    },
    "chapecoense": {
        "nome_oficial": "Chapecoense",
        "sigla": "CHA",
        "estado": "SC",
        "variantes": ["Chapecoense"]
    },
    "corinthians": {
        "nome_oficial": "Corinthians",
        "sigla": "COR",
        "estado": "SP",
        "variantes": ["Corinthians"]
    },
    "coritiba": {
        "nome_oficial": "Coritiba",
        "sigla": "CFC",
        "estado": "PR",
        "variantes": ["Coritiba"]
    },
    "criciuma": {
        "nome_oficial": "Criciúma",
        "sigla": "CRI",
        "estado": "SC",
        "variantes": ["Criciuma", "Criciúma"]
    },
    "cruzeiro": {
        "nome_oficial": "Cruzeiro",
        "sigla": "CRU",
        "estado": "MG",
        "variantes": ["Cruzeiro"]
    },
    "csa": {
        "nome_oficial": "CSA",
        "sigla": "CSA",
        "estado": "AL",
        "variantes": ["CSA"]
    },
    "cuiaba": {
        "nome_oficial": "Cuiabá",
        "sigla": "CUI",
        "estado": "MT",
        "variantes": ["Cuiaba", "Cuiabá"]
    },
    "figueirense": {
        "nome_oficial": "Figueirense",
        "sigla": "FIG",
        "estado": "SC",
        "variantes": ["Figueirense"]
    },
    "flamengo": {
        "nome_oficial": "Flamengo",
        "sigla": "FLA",
        "estado": "RJ",
        "variantes": ["Flamengo"]
    },
    "fluminense": {
        "nome_oficial": "Fluminense",
        "sigla": "FLU",
        "estado": "RJ",
        "variantes": ["Fluminense"]
    },
    "fortaleza": {
        "nome_oficial": "Fortaleza",
        "sigla": "FOR",
        "estado": "CE",
        "variantes": ["Fortaleza"]
    },
    "goias": {
        "nome_oficial": "Goiás",
        "sigla": "GOI",
        "estado": "GO",
        "variantes": ["Goias", "Goiás"]
    },
    "gremio": {
        "nome_oficial": "Grêmio",
        "sigla": "GRE",
        "estado": "RS",
        "variantes": ["Gremio", "Grêmio"]
    },
    "gremio_prudente": {
        "nome_oficial": "Grêmio Prudente",
        "sigla": "GPR",
        "estado": "SP",
        "variantes": ["Gremio Prudente", "Grêmio Prudente"]
    },
    "guarani": {
        "nome_oficial": "Guarani",
        "sigla": "GUA",
        "estado": "SP",
        "variantes": ["Guarani"]
    },
    "internacional": {
        "nome_oficial": "Internacional",
        "sigla": "INT",
        "estado": "RS",
        "variantes": ["Internacional", "Internacional "]
    },
    "ipatinga": {
        "nome_oficial": "Ipatinga",
        "sigla": "IPA",
        "estado": "MG",
        "variantes": ["Ipatinga"]
    },
    "joinville": {
        "nome_oficial": "Joinville",
        "sigla": "JOI",
        "estado": "SC",
        "variantes": ["Joinville"]
    },
    "juventude": {
        "nome_oficial": "Juventude",
        "sigla": "JUV",
        "estado": "RS",
        "variantes": ["Juventude"]
    },
    "nautico": {
        "nome_oficial": "Náutico",
        "sigla": "NAU",
        "estado": "PE",
        "variantes": ["Nautico", "Náutico"]
    },
    "palmeiras": {
        "nome_oficial": "Palmeiras",
        "sigla": "PAL",
        "estado": "SP",
        "variantes": ["Palmeiras"]
    },
    "parana": {
        "nome_oficial": "Paraná",
        "sigla": "PAR",
        "estado": "PR",
        "variantes": ["Parana", "Paraná"]
    },
    "paysandu": {
        "nome_oficial": "Paysandu",
        "sigla": "PAY",
        "estado": "PA",
        "variantes": ["Paysandu"]
    },
    "ponte_preta": {
        "nome_oficial": "Ponte Preta",
        "sigla": "PON",
        "estado": "SP",
        "variantes": ["Ponte Preta"]
    },
    "portuguesa": {
        "nome_oficial": "Portuguesa",
        "sigla": "POR",
        "estado": "SP",
        "variantes": ["Portuguesa"]
    },
    "santa_cruz": {
        "nome_oficial": "Santa Cruz",
        "sigla": "STA",
        "estado": "PE",
        "variantes": ["Santa Cruz"]
    },
    "santo_andre": {
        "nome_oficial": "Santo André",
        "sigla": "SAN",
        "estado": "SP",
        "variantes": ["Santo Andre", "Santo André"]
    },
    "santos": {
        "nome_oficial": "Santos",
        "sigla": "SAN",
        "estado": "SP",
        "variantes": ["Santos"]
    },
    "sao_caetano": {
        "nome_oficial": "São Caetano",
        "sigla": "SCA",
        "estado": "SP",
        "variantes": ["Sao Caetano", "São Caetano"]
    },
    "sao_paulo": {
        "nome_oficial": "São Paulo",
        "sigla": "SAO",
        "estado": "SP",
        "variantes": ["Sao Paulo", "São Paulo", "SÃO PAULO"]
    },
    "sport": {
        "nome_oficial": "Sport",
        "sigla": "SPO",
        "estado": "PE",
        "variantes": ["Sport"]
    },
    "vasco": {
        "nome_oficial": "Vasco da Gama",
        "sigla": "VAS",
        "estado": "RJ",
        "variantes": ["Vasco", "Vasco da Gama"]
    },
    "vitoria": {
        "nome_oficial": "Vitória",
        "sigla": "VIT",
        "estado": "BA",
        "variantes": ["Vitoria", "Vitória"]
    }
}


# CRIAR DICIONÁRIO REVERSO (Variante → Nome Oficial)
CLUBES_MAP = {}

for clube_key, info in CLUBES_OFICIAIS.items():
    nome_oficial = info["nome_oficial"]
    
    # Mapear todas as variantes para o nome oficial
    for variante in info["variantes"]:
        CLUBES_MAP[variante] = nome_oficial
    
    # Adicionar o próprio nome oficial (caso apareça já correto)
    CLUBES_MAP[nome_oficial] = nome_oficial


# FUNÇÃO PRINCIPAL DE NORMALIZAÇÃO
def normalizar_clube(nome: str) -> str:
    """
    Normaliza o nome de um clube para o nome oficial.
    
    Args:
        nome: Nome do clube (pode ter variações, acentos errados, etc)
        
    Returns:
        Nome oficial do clube ou o nome original se não encontrado
        
    Examples:
        >>> normalizar_clube("Athletico-PR")
        'Athletico Paranaense'
        
        >>> normalizar_clube("Sao Paulo")
        'São Paulo'
        
        >>> normalizar_clube("Gremio")
        'Grêmio'
    """
    if not nome or not isinstance(nome, str):
        return nome
    
    # Remove espaços extras
    nome_limpo = nome.strip()
    
    # Busca no dicionário
    return CLUBES_MAP.get(nome_limpo, nome_limpo)


# FUNÇÃO PARA OBTER INFORMAÇÕES COMPLETAS
def obter_info_clube(nome: str) -> dict:
    """
    Retorna informações completas de um clube.
    
    Args:
        nome: Nome do clube (qualquer variante)
        
    Returns:
        Dicionário com nome_oficial, sigla, estado ou None se não encontrado
        
    Examples:
        >>> obter_info_clube("Flamengo")
        {'nome_oficial': 'Flamengo', 'sigla': 'FLA', 'estado': 'RJ'}
    """
    nome_oficial = normalizar_clube(nome)
    
    for info in CLUBES_OFICIAIS.values():
        if info["nome_oficial"] == nome_oficial:
            return {
                "nome_oficial": info["nome_oficial"],
                "sigla": info["sigla"],
                "estado": info["estado"]
            }
    
    return None


# VALIDAÇÃO (executar apenas se rodar diretamente)
if __name__ == "__main__":
    print("=" * 80)
    print("VALIDAÇÃO DO DICIONÁRIO DE CLUBES")
    print("=" * 80)
    
    print(f"\nTotal de clubes mapeados: {len(CLUBES_OFICIAIS)}")
    print(f"Total de variantes mapeadas: {len(CLUBES_MAP)}")
    
    print("\nEXEMPLOS DE NORMALIZAÇÃO:")
    print("-" * 80)
    
    testes = [
        "Athletico-PR",
        "Atletico-MG",
        "Sao Paulo",
        "Gremio",
        "Botafogo-RJ",
        "America-MG",
        "Goias",
        "Internacional "  # com espaço
    ]
    
    for teste in testes:
        normalizado = normalizar_clube(teste)
        info = obter_info_clube(teste)
        print(f"{teste:20s} → {normalizado:25s} ({info['sigla']} - {info['estado']})")
    
    print("\n" + "=" * 80)