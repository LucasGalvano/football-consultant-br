"""
Script de Limpeza dos Datasets do Brasileirão

Processa os CSVs brutos aplicando normalização e limpeza.
CORREÇÕES APLICADAS: ID -> partida_id, rodata -> rodada

Filtros Temporais:
- campeonato-brasileiro-full.csv: ID >= 4607 (2014+)
- campeonato-brasileiro-estatisticas-full.csv: ID >= 4987 (2015+)
- campeonato-brasileiro-gols.csv: ID >= 4607 (2014+)
- campeonato-brasileiro-cartoes.csv: ID >= 4607 (2014+)

Saída:
- data/processed/full-limpo.csv
- data/processed/estatisticas-limpo.csv
- data/processed/gols-limpo.csv
- data/processed/cartoes-limpo.csv

Uso:
    python scripts/1_clean_datasets.py
"""

import pandas as pd
import sys
import os
from pathlib import Path

# Adicionar app ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils import (
    normalizar_clube,
    limpar_estadio,
    limpar_unicode,
    limpar_nome_atleta,
    parse_data_brasileira,
    normalizar_minuto,
    tratar_vazio
)

# Diretórios
DIR_RAW = Path("data/raw")
DIR_PROCESSED = Path("data/processed")

# Criar diretório de saída se não existir
DIR_PROCESSED.mkdir(parents=True, exist_ok=True)

# Pontos de corte (IDs)
ID_CORTE_2014 = 4607  # Início de 2014
ID_CORTE_2015 = 4987  # Início de 2015


def processar_coluna_clube(df: pd.DataFrame, coluna: str) -> pd.Series:
    """Normaliza nomes de clubes em uma coluna"""
    print(f"  -> Normalizando coluna '{coluna}'...")
    return df[coluna].apply(normalizar_clube)


def processar_coluna_estadio(df: pd.DataFrame, coluna: str) -> pd.Series:
    """Limpa nomes de estádios"""
    print(f"  -> Limpando coluna '{coluna}'...")
    return df[coluna].apply(limpar_estadio)


def processar_coluna_data(df: pd.DataFrame, coluna: str) -> pd.Series:
    """Converte datas para formato padrão"""
    print(f"  -> Convertendo coluna '{coluna}' para datetime...")
    # Usar pd.to_datetime que é mais robusto
    return pd.to_datetime(df[coluna], format='%d/%m/%Y', errors='coerce')


def limpar_full_csv():
    """Processa campeonato-brasileiro-full.csv"""
    
    print("\n" + "=" * 80)
    print("PROCESSANDO: campeonato-brasileiro-full.csv")
    print("=" * 80)
    
    arquivo_entrada = DIR_RAW / "campeonato-brasileiro-full.csv"
    arquivo_saida = DIR_PROCESSED / "full-limpo.csv"
    
    # Verificar se arquivo existe
    if not arquivo_entrada.exists():
        print(f"ERRO: Arquivo não encontrado: {arquivo_entrada}")
        return False
    
    # Carregar CSV
    print(f"\nCarregando: {arquivo_entrada}")
    df = pd.read_csv(arquivo_entrada)
    print(f"Carregado: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Filtrar por ID (2014+)
    print(f"\nAplicando filtro: ID >= {ID_CORTE_2014}")
    df_filtrado = df[df['ID'] >= ID_CORTE_2014].copy()
    print(f"Filtrado: {len(df_filtrado)} linhas (removido: {len(df) - len(df_filtrado)})")
    
    # CORREÇÃO: Renomear ID -> partida_id e rodata -> rodada
    print(f"\nCorrigindo nomes de colunas...")
    df_filtrado.rename(columns={
        'ID': 'partida_id',
        'rodata': 'rodada'
    }, inplace=True)
    print(f"ID -> partida_id")
    print(f"rodata -> rodada")
    
    # Normalizar clubes
    print(f"\nNormalizando nomes de clubes...")
    df_filtrado['mandante'] = processar_coluna_clube(df_filtrado, 'mandante')
    df_filtrado['visitante'] = processar_coluna_clube(df_filtrado, 'visitante')
    df_filtrado['vencedor'] = df_filtrado['vencedor'].apply(
        lambda x: normalizar_clube(x) if x and x != '-' else x
    )
    
    # Limpar estádios
    print(f"\nLimpando nomes de estádios...")
    df_filtrado['arena'] = processar_coluna_estadio(df_filtrado, 'arena')
    
    # Converter datas
    print(f"\nConvertendo datas...")
    df_filtrado['data'] = processar_coluna_data(df_filtrado, 'data')
    
    # Limpar campos de texto (técnicos)
    print(f"\nLimpando nomes de técnicos...")
    df_filtrado['tecnico_mandante'] = df_filtrado['tecnico_mandante'].apply(
        lambda x: limpar_unicode(x) if pd.notna(x) else None
    )
    df_filtrado['tecnico_visitante'] = df_filtrado['tecnico_visitante'].apply(
        lambda x: limpar_unicode(x) if pd.notna(x) else None
    )
    
    # Salvar
    print(f"\nSalvando em: {arquivo_saida}")
    df_filtrado.to_csv(arquivo_saida, index=False)
    print(f"Salvo: {len(df_filtrado)} linhas")
    
    # Estatísticas
    print(f"\nESTATÍSTICAS:")
    print(f"  - Período: {df_filtrado['data'].min().date()} a {df_filtrado['data'].max().date()}")
    print(f"  - Clubes únicos: {len(set(df_filtrado['mandante']) | set(df_filtrado['visitante']))}")
    print(f"  - Estádios únicos: {df_filtrado['arena'].nunique()}")
    print(f"  - Partidas com técnico informado: {df_filtrado['tecnico_mandante'].notna().sum()} ({df_filtrado['tecnico_mandante'].notna().sum()/len(df_filtrado)*100:.1f}%)")
    
    return True


# 2. LIMPAR ESTATISTICAS.CSV

def limpar_estatisticas_csv():
    """Processa campeonato-brasileiro-estatisticas-full.csv"""
    
    print("\n" + "=" * 80)
    print("PROCESSANDO: campeonato-brasileiro-estatisticas-full.csv")
    print("=" * 80)
    
    arquivo_entrada = DIR_RAW / "campeonato-brasileiro-estatisticas-full.csv"
    arquivo_saida = DIR_PROCESSED / "estatisticas-limpo.csv"
    
    # Verificar se arquivo existe
    if not arquivo_entrada.exists():
        print(f"ERRO: Arquivo não encontrado: {arquivo_entrada}")
        return False
    
    # Carregar CSV
    print(f"\nCarregando: {arquivo_entrada}")
    df = pd.read_csv(arquivo_entrada)
    print(f"Carregado: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Filtrar por partida_id (2015+)
    print(f"\nAplicando filtro: partida_id >= {ID_CORTE_2015}")
    df_filtrado = df[df['partida_id'] >= ID_CORTE_2015].copy()
    print(f"Filtrado: {len(df_filtrado)} linhas (removido: {len(df) - len(df_filtrado)})")
    
    #Renomear rodata -> rodada
    print(f"\nCorrigindo nomes de colunas...")
    df_filtrado.rename(columns={'rodata': 'rodada'}, inplace=True)
    print(f"rodata -> rodada")
    
    # Normalizar clubes
    print(f"\nNormalizando nomes de clubes...")
    df_filtrado['clube'] = processar_coluna_clube(df_filtrado, 'clube')
    
    # Limpar valores numéricos (remover % se necessário)
    print(f"\nProcessando valores numéricos...")
    colunas_numericas = [
        'chutes', 'chutes_bola_parada', 'chutes_bola_parada_a_gol',
        'passes', 'passes_completos', 'assistencias', 'finalizacoes',
        'finalizacoes_no_alvo', 'finalizacoes_defendidas',
        'finalizacoes_na_trave', 'desarmes', 'impedimentos',
        'escanteios', 'cruzamentos', 'tiro_livre', 'lateral',
        'faltas', 'cartao_amarelo', 'cartao_vermelho'
    ]
    
    for col in colunas_numericas:
        if col in df_filtrado.columns:
            # Converter para numérico, forçando erros para NaN
            df_filtrado[col] = pd.to_numeric(df_filtrado[col], errors='coerce')
    
    # Processar posse_de_bola (pode estar como "58.5%" ou "58.5")
    if 'posse_de_bola' in df_filtrado.columns:
        print(f"  -> Processando 'posse_de_bola'...")
        df_filtrado['posse_de_bola'] = df_filtrado['posse_de_bola'].astype(str).str.replace('%', '').str.strip()
        df_filtrado['posse_de_bola'] = pd.to_numeric(df_filtrado['posse_de_bola'], errors='coerce')
    
    # Processar precisao_passes (mesma lógica)
    if 'precisao_passes' in df_filtrado.columns:
        print(f"  -> Processando 'precisao_passes'...")
        df_filtrado['precisao_passes'] = df_filtrado['precisao_passes'].astype(str).str.replace('%', '').str.strip()
        df_filtrado['precisao_passes'] = pd.to_numeric(df_filtrado['precisao_passes'], errors='coerce')
    
    # Salvar
    print(f"\nSalvando em: {arquivo_saida}")
    df_filtrado.to_csv(arquivo_saida, index=False)
    print(f"Salvo: {len(df_filtrado)} linhas")
    
    # Estatísticas
    print(f"\nESTATÍSTICAS:")
    print(f"  - Partidas únicas: {df_filtrado['partida_id'].nunique()}")
    print(f"  - Clubes únicos: {df_filtrado['clube'].nunique()}")
    print(f"  - Rodadas: {df_filtrado['rodada'].min()} a {df_filtrado['rodada'].max()}")
    
    # Completude dos dados
    if 'chutes' in df_filtrado.columns:
        completude = df_filtrado['chutes'].notna().sum() / len(df_filtrado) * 100
        print(f"  - Dados completos (chutes): {completude:.1f}%")
    
    return True


# 3. LIMPAR GOLS.CSV

def limpar_gols_csv():
    """Processa campeonato-brasileiro-gols.csv"""
    
    print("\n" + "=" * 80)
    print("PROCESSANDO: campeonato-brasileiro-gols.csv")
    print("=" * 80)
    
    arquivo_entrada = DIR_RAW / "campeonato-brasileiro-gols.csv"
    arquivo_saida = DIR_PROCESSED / "gols-limpo.csv"
    
    # Verificar se arquivo existe
    if not arquivo_entrada.exists():
        print(f"ERRO: Arquivo não encontrado: {arquivo_entrada}")
        return False
    
    # Carregar CSV
    print(f"\nCarregando: {arquivo_entrada}")
    df = pd.read_csv(arquivo_entrada)
    print(f"Carregado: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Filtrar por partida_id (2014+)
    print(f"\nAplicando filtro: partida_id >= {ID_CORTE_2014}")
    df_filtrado = df[df['partida_id'] >= ID_CORTE_2014].copy()
    print(f"Filtrado: {len(df_filtrado)} linhas (removido: {len(df) - len(df_filtrado)})")
    
    # CORREÇÃO: Renomear rodata -> rodada
    print(f"\nCorrigindo nomes de colunas...")
    df_filtrado.rename(columns={'rodata': 'rodada'}, inplace=True)
    print(f"rodata -> rodada")
    
    # Normalizar clubes
    print(f"\nNormalizando nomes de clubes...")
    df_filtrado['clube'] = processar_coluna_clube(df_filtrado, 'clube')
    
    # Limpar nomes de atletas
    print(f"\nLimpando nomes de atletas...")
    df_filtrado['atleta'] = df_filtrado['atleta'].apply(
        lambda x: limpar_nome_atleta(x) if pd.notna(x) else None
    )
    
    # Normalizar minutos
    print(f"\nNormalizando minutos...")
    df_filtrado['minuto_numerico'] = df_filtrado['minuto'].apply(normalizar_minuto)
    
    # Limpar tipo de gol
    print(f"\nProcessando tipos de gol...")
    df_filtrado['tipo_de_gol'] = df_filtrado['tipo_de_gol'].apply(
        lambda x: limpar_unicode(x) if pd.notna(x) and x.strip() else None
    )
    
    # Salvar
    print(f"\nSalvando em: {arquivo_saida}")
    df_filtrado.to_csv(arquivo_saida, index=False)
    print(f"Salvo: {len(df_filtrado)} linhas")
    
    # Estatísticas
    print(f"\nESTATÍSTICAS:")
    print(f"  - Total de gols: {len(df_filtrado)}")
    print(f"  - Partidas únicas: {df_filtrado['partida_id'].nunique()}")
    print(f"  - Clubes únicos: {df_filtrado['clube'].nunique()}")
    print(f"  - Gols de pênalti: {(df_filtrado['tipo_de_gol'] == 'Penalty').sum()}")
    print(f"  - Gols contra: {(df_filtrado['tipo_de_gol'] == 'Gol Contra').sum()}")
    
    return True


# 4. LIMPAR CARTOES.CSV

def limpar_cartoes_csv():
    """Processa campeonato-brasileiro-cartoes.csv"""
    
    print("\n" + "=" * 80)
    print("PROCESSANDO: campeonato-brasileiro-cartoes.csv")
    print("=" * 80)
    
    arquivo_entrada = DIR_RAW / "campeonato-brasileiro-cartoes.csv"
    arquivo_saida = DIR_PROCESSED / "cartoes-limpo.csv"
    
    # Verificar se arquivo existe
    if not arquivo_entrada.exists():
        print(f"ERRO: Arquivo não encontrado: {arquivo_entrada}")
        return False
    
    # Carregar CSV
    print(f"\nCarregando: {arquivo_entrada}")
    df = pd.read_csv(arquivo_entrada)
    print(f"Carregado: {len(df)} linhas, {len(df.columns)} colunas")
    
    # Filtrar por partida_id (2014+)
    print(f"\nAplicando filtro: partida_id >= {ID_CORTE_2014}")
    df_filtrado = df[df['partida_id'] >= ID_CORTE_2014].copy()
    print(f"Filtrado: {len(df_filtrado)} linhas (removido: {len(df) - len(df_filtrado)})")
    
    # Renomear rodata -> rodada
    print(f"\nCorrigindo nomes de colunas...")
    df_filtrado.rename(columns={'rodata': 'rodada'}, inplace=True)
    print(f"rodata -> rodada")
    
    # Normalizar clubes
    print(f"\nNormalizando nomes de clubes...")
    df_filtrado['clube'] = processar_coluna_clube(df_filtrado, 'clube')
    
    # Limpar nomes de atletas
    print(f"\nLimpando nomes de atletas...")
    df_filtrado['atleta'] = df_filtrado['atleta'].apply(
        lambda x: limpar_nome_atleta(x) if pd.notna(x) else None
    )
    
    # Normalizar minutos
    print(f"\nNormalizando minutos...")
    df_filtrado['minuto_numerico'] = df_filtrado['minuto'].apply(normalizar_minuto)
    
    # Limpar posição
    print(f"\nLimpando posições...")
    df_filtrado['posicao'] = df_filtrado['posicao'].apply(
        lambda x: limpar_unicode(x) if pd.notna(x) and x.strip() else None
    )
    
    # Salvar
    print(f"\nSalvando em: {arquivo_saida}")
    df_filtrado.to_csv(arquivo_saida, index=False)
    print(f"Salvo: {len(df_filtrado)} linhas")
    
    # Estatísticas
    print(f"\nESTATÍSTICAS:")
    print(f"  - Total de cartões: {len(df_filtrado)}")
    print(f"  - Partidas únicas: {df_filtrado['partida_id'].nunique()}")
    print(f"  - Clubes únicos: {df_filtrado['clube'].nunique()}")
    print(f"  - Cartões amarelos: {(df_filtrado['cartao'] == 'Amarelo').sum()}")
    print(f"  - Cartões vermelhos: {(df_filtrado['cartao'] == 'Vermelho').sum()}")
    
    return True


# FUNÇÃO PRINCIPAL

def main():
    """Executa limpeza de todos os CSVs"""
    
    print("\n" + "=" * 80)
    print("LIMPEZA DOS DATASETS DO BRASILEIRÃO")
    print("=" * 80)
    print(f"\nDiretório de entrada: {DIR_RAW}")
    print(f"Diretório de saída: {DIR_PROCESSED}")
    print(f"\nCorreções aplicadas automaticamente:")
    print(f"   - full-limpo.csv: ID -> partida_id, rodata -> rodada")
    print(f"   - Outros CSVs: rodata -> rodada")
    
    # Processar cada CSV
    resultados = {
        "Full CSV": limpar_full_csv(),
        "Estatísticas CSV": limpar_estatisticas_csv(),
        "Gols CSV": limpar_gols_csv(),
        "Cartões CSV": limpar_cartoes_csv()
    }
    
    # Resumo final
    print("\n\n" + "=" * 80)
    print("RESUMO DA LIMPEZA")
    print("=" * 80)
    
    for nome, sucesso in resultados.items():
        status = "SUCESSO" if sucesso else "FALHOU"
        print(f"{status} - {nome}")
    
    if all(resultados.values()):
        print("\nTODOS OS ARQUIVOS FORAM PROCESSADOS COM SUCESSO!")
        print(f"\nArquivos limpos disponíveis em: {DIR_PROCESSED}/")
    else:
        print("\nATENÇÃO: Alguns arquivos falharam no processamento.")
        print("Verifique os erros acima.")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()