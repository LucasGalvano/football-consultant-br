"""
Script de Validação dos Dados Limpos
Valida a integridade e consistência dos dados após a limpeza.
CORREÇÕES: Usa 'partida_id' e 'rodada' ao invés de 'ID' e 'rodata'

Verificações:
- Integridade referencial (IDs existem entre CSVs)
- Valores ausentes em campos críticos
- Duplicatas
- Consistência de datas
- Valores numéricos válidos
- Nomes normalizados corretamente

Uso:
    python scripts/2_validate_data.py
"""

import pandas as pd
import sys
from pathlib import Path
from collections import Counter

# Adicionar app ao path para imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils import CLUBES_MAP

DIR_PROCESSED = Path("data/processed")

# Arquivos processados
ARQUIVO_FULL = DIR_PROCESSED / "full-limpo.csv"
ARQUIVO_STATS = DIR_PROCESSED / "estatisticas-limpo.csv"
ARQUIVO_GOLS = DIR_PROCESSED / "gols-limpo.csv"
ARQUIVO_CARTOES = DIR_PROCESSED / "cartoes-limpo.csv"


class ValidadorDados:
    """Classe para validação de dados limpos"""
    
    def __init__(self):
        self.erros = []
        self.avisos = []
        self.sucessos = []
    
    def adicionar_erro(self, mensagem: str):
        """Registra um erro crítico"""
        self.erros.append(f"ERRO: {mensagem}")
    
    def adicionar_aviso(self, mensagem: str):
        """Registra um aviso (não crítico)"""
        self.avisos.append(f"AVISO: {mensagem}")
    
    def adicionar_sucesso(self, mensagem: str):
        """Registra uma validação bem-sucedida"""
        self.sucessos.append(f"✓ {mensagem}")
    
    def imprimir_relatorio(self):
        """Imprime relatório de validação"""
        print("\n" + "=" * 80)
        print("RELATÓRIO DE VALIDAÇÃO")
        print("=" * 80)
        
        if self.sucessos:
            print("\nVALIDAÇÕES BEM-SUCEDIDAS:")
            print("-" * 80)
            for sucesso in self.sucessos:
                print(sucesso)
        
        if self.avisos:
            print("\nAVISOS:")
            print("-" * 80)
            for aviso in self.avisos:
                print(aviso)
        
        if self.erros:
            print("\nERROS CRÍTICOS:")
            print("-" * 80)
            for erro in self.erros:
                print(erro)
        
        print("\n" + "=" * 80)
        print(f"RESUMO: {len(self.sucessos)} sucessos | {len(self.avisos)} avisos | {len(self.erros)} erros")
        print("=" * 80)
        
        return len(self.erros) == 0


def validar_arquivo_existe(arquivo: Path, validador: ValidadorDados) -> bool:
    """Verifica se arquivo existe"""
    if arquivo.exists():
        validador.adicionar_sucesso(f"Arquivo encontrado: {arquivo.name}")
        return True
    else:
        validador.adicionar_erro(f"Arquivo não encontrado: {arquivo}")
        return False


def validar_full_csv(validador: ValidadorDados):
    """Valida o arquivo full-limpo.csv"""
    
    print("\n" + "=" * 80)
    print("VALIDANDO: full-limpo.csv")
    print("=" * 80)
    
    if not validar_arquivo_existe(ARQUIVO_FULL, validador):
        return None
    
    df = pd.read_csv(ARQUIVO_FULL)
    print(f"\nTotal de partidas: {len(df)}")
    
    # VERIFICAR SE AS COLUNAS FORAM CORRIGIDAS
    print("\nVerificando nomes de colunas...")
    if 'partida_id' in df.columns:
        validador.adicionar_sucesso("Coluna 'partida_id' presente (ID foi corrigido)")
    else:
        validador.adicionar_erro("Coluna 'partida_id' não encontrada - execute o script de correção!")
    
    if 'rodada' in df.columns:
        validador.adicionar_sucesso("Coluna 'rodada' presente (rodata foi corrigido)")
    else:
        validador.adicionar_erro("Coluna 'rodada' não encontrada - execute o script de correção!")
    
    # 1. Campos obrigatórios não podem ser nulos
    print("\nVerificando campos obrigatórios...")
    campos_obrigatorios = ['partida_id', 'mandante', 'visitante', 'arena', 'data', 
                           'mandante_Placar', 'visitante_Placar']
    
    for campo in campos_obrigatorios:
        if campo not in df.columns:
            validador.adicionar_erro(f"{campo}: coluna não encontrada")
            continue
            
        nulos = df[campo].isna().sum()
        if nulos > 0:
            validador.adicionar_erro(f"{campo}: {nulos} valores nulos encontrados")
        else:
            validador.adicionar_sucesso(f"{campo}: sem valores nulos")
    
    # 2. Verificar duplicatas de partida_id
    print("\nVerificando duplicatas...")
    if 'partida_id' in df.columns:
        duplicados = df['partida_id'].duplicated().sum()
        if duplicados > 0:
            validador.adicionar_erro(f"partida_id duplicados encontrados: {duplicados}")
        else:
            validador.adicionar_sucesso(f"Sem partida_id duplicados")
    
    # 3. Validar datas
    print("\nVerificando datas...")
    try:
        df['data'] = pd.to_datetime(df['data'])
        data_min = df['data'].min()
        data_max = df['data'].max()
        validador.adicionar_sucesso(f"Datas válidas: {data_min.date()} a {data_max.date()}")
        
        # Verificar se está no período esperado (2014+)
        if data_min.year < 2014:
            validador.adicionar_aviso(f"Partidas antes de 2014 encontradas: {(df['data'].dt.year < 2014).sum()}")
    except Exception as e:
        validador.adicionar_erro(f"Erro ao processar datas: {e}")
    
    # 4. Validar clubes normalizados
    print("\nVerificando normalização de clubes...")
    clubes_mandante = set(df['mandante'].unique())
    clubes_visitante = set(df['visitante'].unique())
    todos_clubes = clubes_mandante | clubes_visitante
    
    # Verificar se há clubes não mapeados
    clubes_oficiais = set(CLUBES_MAP.values())
    clubes_nao_mapeados = todos_clubes - clubes_oficiais
    
    if clubes_nao_mapeados:
        validador.adicionar_aviso(f"Clubes não no dicionário oficial: {clubes_nao_mapeados}")
    else:
        validador.adicionar_sucesso(f"Todos os {len(todos_clubes)} clubes estão normalizados")
    
    # 5. Validar estádios limpos (sem \xa0)
    print("\nVerificando estádios...")
    estadios_com_problema = df['arena'].str.contains('\xa0', na=False).sum()
    if estadios_com_problema > 0:
        validador.adicionar_erro(f"Estádios com \\xa0: {estadios_com_problema}")
    else:
        validador.adicionar_sucesso(f"Estádios limpos (sem \\xa0)")
    
    # 6. Validar placares
    print("\nVerificando placares...")
    placares_invalidos = (df['mandante_Placar'] < 0).sum() + (df['visitante_Placar'] < 0).sum()
    if placares_invalidos > 0:
        validador.adicionar_erro(f"Placares negativos encontrados: {placares_invalidos}")
    else:
        validador.adicionar_sucesso(f"Placares válidos")
    
    return df


def validar_estatisticas_csv(validador: ValidadorDados, df_full: pd.DataFrame):
    """Valida o arquivo estatisticas-limpo.csv"""
    
    print("\n" + "=" * 80)
    print("VALIDANDO: estatisticas-limpo.csv")
    print("=" * 80)
    
    if not validar_arquivo_existe(ARQUIVO_STATS, validador):
        return None
    
    df = pd.read_csv(ARQUIVO_STATS)
    print(f"\nTotal de registros: {len(df)}")
    
    # VERIFICAR SE AS COLUNAS FORAM CORRIGIDAS
    print("\nVerificando nomes de colunas...")
    if 'rodada' in df.columns:
        validador.adicionar_sucesso("Coluna 'rodada' presente (rodata foi corrigido)")
    else:
        validador.adicionar_erro("Coluna 'rodada' não encontrada - execute o script de correção!")
    
    # 1. Integridade referencial com full.csv
    print("\nVerificando integridade referencial...")
    if df_full is not None and 'partida_id' in df_full.columns:
        ids_full = set(df_full['partida_id'])
        ids_stats = set(df['partida_id'].unique())
        
        # IDs que existem em stats mas não em full
        ids_orfaos = ids_stats - ids_full
        if ids_orfaos:
            validador.adicionar_erro(f"partida_id órfãos (não existem em full.csv): {len(ids_orfaos)}")
        else:
            validador.adicionar_sucesso(f"Todos os partida_id existem em full.csv")
    
    # 2. Cada partida deve ter 2 registros (mandante e visitante)
    print("\nVerificando registros por partida...")
    contagem_por_partida = df['partida_id'].value_counts()
    partidas_incompletas = (contagem_por_partida != 2).sum()
    
    if partidas_incompletas > 0:
        validador.adicionar_aviso(f"Partidas sem 2 registros: {partidas_incompletas}")
    else:
        validador.adicionar_sucesso(f"Todas as partidas têm 2 registros (mandante + visitante)")
    
    # 3. Validar clubes
    print("\nVerificando normalização de clubes...")
    clubes = set(df['clube'].unique())
    clubes_oficiais = set(CLUBES_MAP.values())
    clubes_nao_mapeados = clubes - clubes_oficiais
    
    if clubes_nao_mapeados:
        validador.adicionar_aviso(f"Clubes não no dicionário: {clubes_nao_mapeados}")
    else:
        validador.adicionar_sucesso(f"Todos os {len(clubes)} clubes estão normalizados")
    
    # 4. Validar dados numéricos
    print("\nVerificando campos numéricos...")
    colunas_numericas = ['chutes', 'passes', 'finalizacoes', 'posse_de_bola']
    
    for col in colunas_numericas:
        if col in df.columns:
            negativos = (df[col] < 0).sum()
            if negativos > 0:
                validador.adicionar_erro(f"{col}: valores negativos encontrados: {negativos}")
            
            # Verificar completude
            completude = (df[col].notna().sum() / len(df)) * 100
            if completude < 50:
                validador.adicionar_aviso(f"{col}: apenas {completude:.1f}% preenchido")
            else:
                validador.adicionar_sucesso(f"{col}: {completude:.1f}% preenchido")
    
    return df


def validar_gols_csv(validador: ValidadorDados, df_full: pd.DataFrame):
    """Valida o arquivo gols-limpo.csv"""
    
    print("\n" + "=" * 80)
    print("VALIDANDO: gols-limpo.csv")
    print("=" * 80)
    
    if not validar_arquivo_existe(ARQUIVO_GOLS, validador):
        return None
    
    df = pd.read_csv(ARQUIVO_GOLS)
    print(f"\nTotal de gols: {len(df)}")
    
    # VERIFICAR SE AS COLUNAS FORAM CORRIGIDAS
    print("\nVerificando nomes de colunas...")
    if 'rodada' in df.columns:
        validador.adicionar_sucesso("Coluna 'rodada' presente (rodata foi corrigido)")
    else:
        validador.adicionar_erro("Coluna 'rodada' não encontrada - execute o script de correção!")
    
    # 1. Integridade referencial
    print("\nVerificando integridade referencial...")
    if df_full is not None and 'partida_id' in df_full.columns:
        ids_full = set(df_full['partida_id'])
        ids_gols = set(df['partida_id'].unique())
        
        ids_orfaos = ids_gols - ids_full
        if ids_orfaos:
            validador.adicionar_erro(f"partida_id órfãos: {len(ids_orfaos)}")
        else:
            validador.adicionar_sucesso(f"Todos os partida_id existem em full.csv")
    
    # 2. Validar clubes
    print("\nVerificando normalização de clubes...")
    clubes = set(df['clube'].unique())
    clubes_oficiais = set(CLUBES_MAP.values())
    clubes_nao_mapeados = clubes - clubes_oficiais
    
    if clubes_nao_mapeados:
        validador.adicionar_aviso(f"Clubes não no dicionário: {clubes_nao_mapeados}")
    else:
        validador.adicionar_sucesso(f"Todos os clubes estão normalizados")
    
    # 3. Validar minutos
    print("\nVerificando minutos...")
    if 'minuto_numerico' in df.columns:
        minutos_invalidos = ((df['minuto_numerico'] < 0) | (df['minuto_numerico'] > 150)).sum()
        if minutos_invalidos > 0:
            validador.adicionar_aviso(f"Minutos fora do range esperado (0-150): {minutos_invalidos}")
        else:
            validador.adicionar_sucesso(f"Minutos dentro do range válido")
    
    # 4. Validar atletas
    print("\nVerificando atletas...")
    atletas_nulos = df['atleta'].isna().sum()
    if atletas_nulos > 0:
        validador.adicionar_aviso(f"Gols sem atleta informado: {atletas_nulos}")
    else:
        validador.adicionar_sucesso(f"Todos os gols têm atleta informado")
    
    return df


def validar_cartoes_csv(validador: ValidadorDados, df_full: pd.DataFrame):
    """Valida o arquivo cartoes-limpo.csv"""
    
    print("\n" + "=" * 80)
    print("VALIDANDO: cartoes-limpo.csv")
    print("=" * 80)
    
    if not validar_arquivo_existe(ARQUIVO_CARTOES, validador):
        return None
    
    df = pd.read_csv(ARQUIVO_CARTOES)
    print(f"\nTotal de cartões: {len(df)}")
    
    # VERIFICAR SE AS COLUNAS FORAM CORRIGIDAS
    print("\nVerificando nomes de colunas...")
    if 'rodada' in df.columns:
        validador.adicionar_sucesso("Coluna 'rodada' presente (rodata foi corrigido)")
    else:
        validador.adicionar_erro("Coluna 'rodada' não encontrada - execute o script de correção!")
    
    # 1. Integridade referencial
    print("\nVerificando integridade referencial...")
    if df_full is not None and 'partida_id' in df_full.columns:
        ids_full = set(df_full['partida_id'])
        ids_cartoes = set(df['partida_id'].unique())
        
        ids_orfaos = ids_cartoes - ids_full
        if ids_orfaos:
            validador.adicionar_erro(f"partida_id órfãos: {len(ids_orfaos)}")
        else:
            validador.adicionar_sucesso(f"Todos os partida_id existem em full.csv")
    
    # 2. Validar clubes
    print("\nVerificando normalização de clubes...")
    clubes = set(df['clube'].unique())
    clubes_oficiais = set(CLUBES_MAP.values())
    clubes_nao_mapeados = clubes - clubes_oficiais
    
    if clubes_nao_mapeados:
        validador.adicionar_aviso(f"Clubes não no dicionário: {clubes_nao_mapeados}")
    else:
        validador.adicionar_sucesso(f"Todos os clubes estão normalizados")
    
    # 3. Validar tipos de cartão
    print("\nVerificando tipos de cartão...")
    tipos_validos = {'Amarelo', 'Vermelho'}
    tipos_encontrados = set(df['cartao'].unique())
    tipos_invalidos = tipos_encontrados - tipos_validos
    
    if tipos_invalidos:
        validador.adicionar_erro(f"Tipos de cartão inválidos: {tipos_invalidos}")
    else:
        validador.adicionar_sucesso(f"Tipos de cartão válidos: {tipos_encontrados}")
    
    # 4. Validar minutos
    print("\nVerificando minutos...")
    if 'minuto_numerico' in df.columns:
        minutos_invalidos = ((df['minuto_numerico'] < 0) | (df['minuto_numerico'] > 150)).sum()
        if minutos_invalidos > 0:
            validador.adicionar_aviso(f"Minutos fora do range esperado (0-150): {minutos_invalidos}")
        else:
            validador.adicionar_sucesso(f"Minutos dentro do range válido")
    
    return df


def validar_consistencia_cruzada(validador: ValidadorDados, df_full, df_gols, df_stats):
    """Valida consistência entre os diferentes CSVs"""
    
    print("\n" + "=" * 80)
    print("VALIDANDO: Consistência Cruzada")
    print("=" * 80)
    
    if df_full is None or df_gols is None:
        validador.adicionar_aviso("Não é possível validar consistência (arquivos faltando)")
        return
    
    # 1. Verificar se número de gols bate com placares
    print("\nVerificando placares vs gols...")
    
    for _, partida in df_full.head(10).iterrows():  # Amostra de 10 partidas
        partida_id = partida['partida_id']
        placar_mandante = partida['mandante_Placar']
        placar_visitante = partida['visitante_Placar']
        
        gols_partida = df_gols[df_gols['partida_id'] == partida_id]
        gols_mandante = len(gols_partida[gols_partida['clube'] == partida['mandante']])
        gols_visitante = len(gols_partida[gols_partida['clube'] == partida['visitante']])
        
        if gols_mandante != placar_mandante or gols_visitante != placar_visitante:
            validador.adicionar_aviso(
                f"Partida {partida_id}: Placar ({placar_mandante}x{placar_visitante}) "
                f"≠ Gols registrados ({gols_mandante}x{gols_visitante})"
            )
    
    validador.adicionar_sucesso("Validação cruzada de amostra concluída")


def main():
    """Executa todas as validações"""
    
    print("\n" + "=" * 80)
    print("VALIDAÇÃO DOS DADOS LIMPOS (VERSÃO CORRIGIDA)")
    print("=" * 80)
    
    validador = ValidadorDados()
    
    # Validar cada arquivo
    df_full = validar_full_csv(validador)
    df_stats = validar_estatisticas_csv(validador, df_full)
    df_gols = validar_gols_csv(validador, df_full)
    df_cartoes = validar_cartoes_csv(validador, df_full)
    
    # Validação cruzada
    validar_consistencia_cruzada(validador, df_full, df_gols, df_stats)
    
    # Relatório final
    sucesso = validador.imprimir_relatorio()
    
    if sucesso:
        print("\nVALIDAÇÃO CONCLUÍDA: Dados prontos para uso!")
    else:
        print("\nVALIDAÇÃO FALHOU: Corrija os erros antes de continuar.")
    
    return sucesso


if __name__ == "__main__":
    sucesso = main()
    sys.exit(0 if sucesso else 1)