"""
Funções de Limpeza de Dados
Funções auxiliares para normalização e limpeza dos datasets do Brasileirão.

Uso:    
    estadio_limpo = limpar_estadio(" Maracanã"), retorna "Maracanã"
"""

import unicodedata
import re
from datetime import datetime
from typing import Optional


def limpar_estadio(nome: str) -> str:
    """
    Remove caracteres especiais e espaços indesejados de nomes de estádios.
    
    Problemas comuns:
    - Espaço unicode no início (\\xa0)
    - Múltiplos espaços
    - Caracteres de controle
    
    Args:
        nome: Nome do estádio potencialmente sujo
        
    Returns:
        Nome do estádio limpo
        
    Examples:
        >>> limpar_estadio(" Maracanã")
        'Maracanã'
        
        >>> limpar_estadio("\\xa0Arena da Baixada")
        'Arena da Baixada'
        
        >>> limpar_estadio("  Mineirão  ")
        'Mineirão'
    """
    if not nome or not isinstance(nome, str):
        return nome
    
    # Remove non-breaking space (\\xa0) e outros espaços unicode
    nome_limpo = nome.replace('\xa0', ' ')
    
    # Remove espaços no início e fim
    nome_limpo = nome_limpo.strip()
    
    # Normaliza múltiplos espaços para um único
    nome_limpo = re.sub(r'\s+', ' ', nome_limpo)
    
    # Normaliza unicode para forma canônica (NFC)
    nome_limpo = unicodedata.normalize('NFC', nome_limpo)
    
    return nome_limpo


def limpar_unicode(texto: str) -> str:
    """
    Normaliza texto para formato unicode padrão (NFC).
    
    Resolve problemas como:
    - \\u00e1 → á
    - \\u00e3o → ão
    - Caracteres decompostos (á = a + ´)
    
    Args:
        texto: Texto com possíveis problemas de encoding
        
    Returns:
        Texto normalizado
        
    Examples:
        >>> limpar_unicode("Goi\\u00e1s")
        'Goiás'
        
        >>> limpar_unicode("S\\u00e3o Paulo")
        'São Paulo'
    """
    if not texto or not isinstance(texto, str):
        return texto
    
    # Normaliza para forma canônica (NFC)
    # NFC = caracteres pré-compostos (á como um único caractere)
    texto_limpo = unicodedata.normalize('NFC', texto)
    
    # Remove espaços extras
    texto_limpo = texto_limpo.strip()
    
    return texto_limpo


def parse_data_brasileira(data_str: str) -> Optional[datetime]:
    """
    Converte string de data no formato brasileiro para datetime.
    
    Formatos aceitos:
    - DD/MM/YYYY
    - DD-MM-YYYY
    - YYYY-MM-DD (ISO)
    
    Args:
        data_str: String com a data
        
    Returns:
        Objeto datetime ou None se inválido
        
    Examples:
        >>> parse_data_brasileira("15/08/2020")
        datetime.datetime(2020, 8, 15, 0, 0)
        
        >>> parse_data_brasileira("2020-08-15")
        datetime.datetime(2020, 8, 15, 0, 0)
    """
    if not data_str or not isinstance(data_str, str):
        return None
    
    # Remove espaços
    data_str = data_str.strip()
    
    # Tenta vários formatos
    formatos = [
        '%d/%m/%Y',  # 15/08/2020
        '%d-%m-%Y',  # 15-08-2020
        '%Y-%m-%d',  # 2020-08-15 (ISO)
        '%d/%m/%y',  # 15/08/20
    ]
    
    for formato in formatos:
        try:
            return datetime.strptime(data_str, formato)
        except ValueError:
            continue
    
    # Se nenhum formato funcionou, retorna None
    return None



def parse_hora(hora_str: str) -> Optional[str]:
    """
    Normaliza string de hora para formato HH:MM.
    
    Args:
        hora_str: String com hora (ex: "16:00", "16h", "16:00:00")
        
    Returns:
        Hora no formato HH:MM ou None se inválido
        
    Examples:
        >>> parse_hora("16:00")
        '16:00'
        
        >>> parse_hora("16h30")
        '16:30'
        
        >>> parse_hora("16:00:00")
        '16:00'
    """
    if not hora_str or not isinstance(hora_str, str):
        return None
    
    hora_str = hora_str.strip()
    
    # Remove segundos se existir (16:00:00 → 16:00)
    if hora_str.count(':') == 2:
        hora_str = ':'.join(hora_str.split(':')[:2])
    
    # Substitui 'h' por ':' (16h30 → 16:30)
    hora_str = hora_str.replace('h', ':')
    
    # Valida formato HH:MM
    if re.match(r'^\d{1,2}:\d{2}$', hora_str):
        return hora_str
    
    return None



def limpar_nome_atleta(nome: str) -> str:
    """
    Limpa e normaliza nome de atleta.
    
    Remove:
    - Espaços extras
    - Caracteres especiais indesejados
    
    Args:
        nome: Nome do atleta
        
    Returns:
        Nome limpo
        
    Examples:
        >>> limpar_nome_atleta("  Neymar Jr.  ")
        'Neymar Jr.'
        
        >>> limpar_nome_atleta("Gabriel  Barbosa")
        'Gabriel Barbosa'
    """
    if not nome or not isinstance(nome, str):
        return nome
    
    # Limpa unicode
    nome_limpo = limpar_unicode(nome)
    
    # Remove múltiplos espaços
    nome_limpo = re.sub(r'\s+', ' ', nome_limpo)
    
    # Remove espaços no início e fim
    nome_limpo = nome_limpo.strip()
    
    return nome_limpo


def validar_numero(valor, tipo=int, padrao=None):
    """
    Valida e converte valor para número.
    
    Args:
        valor: Valor a ser convertido
        tipo: Tipo numérico desejado (int ou float)
        padrao: Valor padrão se conversão falhar
        
    Returns:
        Valor convertido ou padrão
        
    Examples:
        >>> validar_numero("10", int)
        10
        
        >>> validar_numero("abc", int, 0)
        0
        
        >>> validar_numero("3.14", float)
        3.14
    """
    try:
        return tipo(valor)
    except (ValueError, TypeError):
        return padrao


def tratar_vazio(valor: str, substituir_por=None):
    """
    Trata valores vazios, convertendo para None ou valor padrão.
    
    Considera vazio:
    - String vazia ""
    - String com apenas espaços "   "
    - String "-"
    - None
    
    Args:
        valor: Valor a verificar
        substituir_por: Valor para substituir vazios (None por padrão)
        
    Returns:
        Valor original ou substituição
        
    Examples:
        >>> tratar_vazio("")
        None
        
        >>> tratar_vazio("   ")
        None
        
        >>> tratar_vazio("-")
        None
        
        >>> tratar_vazio("Valor válido")
        'Valor válido'
    """
    if valor is None:
        return substituir_por
    
    if isinstance(valor, str):
        valor = valor.strip()
        
        # Considera vazio
        if valor == "" or valor == "-":
            return substituir_por
    
    return valor


def normalizar_minuto(minuto_str: str) -> Optional[int]:
    """
    Normaliza string de minuto para inteiro.
    
    Lida com formatos como:
    - "45" → 45
    - "45+2" → 47
    - "90+3" → 93
    
    Args:
        minuto_str: String com o minuto
        
    Returns:
        Minuto como inteiro ou None se inválido
        
    Examples:
        >>> normalizar_minuto("45")
        45
        
        >>> normalizar_minuto("45+2")
        47
        
        >>> normalizar_minuto("90+3")
        93
    """
    if not minuto_str or not isinstance(minuto_str, str):
        return None
    
    minuto_str = minuto_str.strip()
    
    # Se tem adição (ex: 45+2)
    if '+' in minuto_str:
        partes = minuto_str.split('+')
        if len(partes) == 2:
            try:
                base = int(partes[0])
                adicional = int(partes[1])
                return base + adicional
            except ValueError:
                return None
    
    # Senão, tenta converter direto
    try:
        return int(minuto_str)
    except ValueError:
        return None


def validar_linha_csv(linha: dict, campos_obrigatorios: list) -> tuple[bool, list]:
    """
    Valida se uma linha do CSV tem todos os campos obrigatórios preenchidos.
    
    Args:
        linha: Dicionário com dados da linha
        campos_obrigatorios: Lista de campos que não podem estar vazios
        
    Returns:
        Tupla (valido, erros) onde:
        - valido: True se passou, False se não
        - erros: Lista de mensagens de erro
        
    Examples:
        >>> linha = {'ID': '1', 'mandante': 'Flamengo', 'visitante': ''}
        >>> validar_linha_csv(linha, ['ID', 'mandante', 'visitante'])
        (False, ['Campo obrigatório vazio: visitante'])
    """
    erros = []
    
    for campo in campos_obrigatorios:
        valor = linha.get(campo)
        
        if valor is None or (isinstance(valor, str) and valor.strip() == ""):
            erros.append(f"Campo obrigatório vazio: {campo}")
    
    return (len(erros) == 0, erros)


if __name__ == "__main__":
    print("=" * 80)
    print("TESTES DAS FUNÇÕES DE LIMPEZA")
    print("=" * 80)
    
    print("\n1. LIMPEZA DE ESTÁDIOS:")
    print("-" * 80)
    testes_estadio = [
        " Maracanã",
        "\xa0Arena da Baixada",
        "  Mineirão  ",
        "Brinco  de   Ouro"
    ]
    for teste in testes_estadio:
        limpo = limpar_estadio(teste)
        print(f"'{teste}' → '{limpo}'")
    
    print("\n2. NORMALIZAÇÃO DE MINUTOS:")
    print("-" * 80)
    testes_minuto = ["45", "45+2", "90+3", "120"]
    for teste in testes_minuto:
        normalizado = normalizar_minuto(teste)
        print(f"'{teste}' → {normalizado}")
    
    print("\n3. CONVERSÃO DE DATAS:")
    print("-" * 80)
    testes_data = ["15/08/2020", "2020-08-15", "15-08-2020"]
    for teste in testes_data:
        convertida = parse_data_brasileira(teste)
        print(f"'{teste}' → {convertida}")
    
    print("\n4. TRATAMENTO DE VAZIOS:")
    print("-" * 80)
    testes_vazio = ["", "   ", "-", None, "Valor válido"]
    for teste in testes_vazio:
        tratado = tratar_vazio(teste)
        print(f"{repr(teste)} → {repr(tratado)}")
    
    print("\n" + "=" * 80)
    print("Todos os testes concluídos!")
    print("=" * 80)