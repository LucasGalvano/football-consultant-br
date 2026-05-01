"""
Script de Seed de Dados Extras
================================
Popula cidade, estado e capacidade dos estádios.
Popula ano de fundação dos clubes.

ATENÇÃO: Verifique os dados marcados com  antes de rodar.

Uso:
    python scripts/6_seed_extras.py
"""

import sys
from pathlib import Path
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, text

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config.database import get_postgres_engine
from app.models.postgres_models import Clube, Estadio

# ─── DADOS DOS ESTÁDIOS ───────────────────────────────────────────────────────

ESTADIOS_INFO = {
    "Adelmar da Costa Carvalho": {"cidade": "Recife", "estado": "PE", "capacidade": 35000},
    "Alfredo Jaconi":            {"cidade": "Caxias do Sul", "estado": "RS", "capacidade": 19831},
    "Allianz Parque":            {"cidade": "São Paulo", "estado": "SP", "capacidade": 43713},
    "Arena BRB Mané Garrincha":  {"cidade": "Brasília", "estado": "DF", "capacidade": 69349},
    "Arena Barueri":             {"cidade": "Barueri", "estado": "SP", "capacidade": 29500},  
    "Arena Castelão":            {"cidade": "Fortaleza", "estado": "CE", "capacidade": 63903},
    "Arena Condá":               {"cidade": "Chapecó", "estado": "SC", "capacidade": 22600},  
    "Arena Fonte Nova":          {"cidade": "Salvador", "estado": "BA", "capacidade": 47907},
    "Arena Joinville":           {"cidade": "Joinville", "estado": "SC", "capacidade": 22000},  
    "Arena MRV":                 {"cidade": "Belo Horizonte", "estado": "MG", "capacidade": 46000},
    "Arena Pantanal":            {"cidade": "Cuiabá", "estado": "MT", "capacidade": 44058},
    "Arena da Amazônia":         {"cidade": "Manaus", "estado": "AM", "capacidade": 44310},
    "Arena das Dunas":           {"cidade": "Natal", "estado": "RN", "capacidade": 42086},
    "Arena de Pernambuco":       {"cidade": "São Lourenço da Mata", "estado": "PE", "capacidade": 46154},
    "Arena do Grêmio":           {"cidade": "Porto Alegre", "estado": "RS", "capacidade": 55000},
    "Beira-Rio":                 {"cidade": "Porto Alegre", "estado": "RS", "capacidade": 50128},
    "Bezerrão":                  {"cidade": "Gama", "estado": "DF", "capacidade": 19000},  
    "Brinco de Ouro da Princesa":{"cidade": "Campinas", "estado": "SP", "capacidade": 29500},  
    "Couto Pereira":             {"cidade": "Curitiba", "estado": "PR", "capacidade": 40502},
    "Domingão":                  {"cidade": "Chapecó", "estado": "SC", "capacidade": 7000},  
    "Estádio Governador Magalhães Pinto": {"cidade": "Belo Horizonte", "estado": "MG", "capacidade": 61846},
    "Estádio Jornalista Felipe Drummond": {"cidade": "Ipatinga", "estado": "MG", "capacidade": 22000},  
    "Estádio Kléber Andrade":    {"cidade": "Cariacica", "estado": "ES", "capacidade": 19000},  
    "Estádio Luso-Brasileiro":   {"cidade": "Rio de Janeiro", "estado": "RJ", "capacidade": 8000},  
    "Estádio Moisés Lucarelli":  {"cidade": "Campinas", "estado": "SP", "capacidade": 23000},  
    "Estádio Municipal Lauro Gomes": {"cidade": "São Bernardo do Campo", "estado": "SP", "capacidade": 17000},  
    "Estádio Municipal de Pituaçu": {"cidade": "Salvador", "estado": "BA", "capacidade": 35000},  
    "Estádio Olímpico Nilton Santos": {"cidade": "Rio de Janeiro", "estado": "RJ", "capacidade": 46931},
    "Estádio do Café":           {"cidade": "Londrina", "estado": "PR", "capacidade": 25000},  
    "Estádio do Maracanã":       {"cidade": "Rio de Janeiro", "estado": "RJ", "capacidade": 78838},
    "Figueirense":               {"cidade": "Florianópolis", "estado": "SC", "capacidade": 19000},  
    "Giulite Coutinho":          {"cidade": "Mesquita", "estado": "RJ", "capacidade": 10000},  
    "Heriberto Hülse":           {"cidade": "Criciúma", "estado": "SC", "capacidade": 19000},  
    "Independência":             {"cidade": "Belo Horizonte", "estado": "MG", "capacidade": 23018},
    "João Lamego Netto":         {"cidade": "Volta Redonda", "estado": "RJ", "capacidade": 22000},  
    "José Pinheiro Borda":       {"cidade": "Porto Alegre", "estado": "RS", "capacidade": 58000},  # Beira-Rio antigo nome
    "Ligga Arena":               {"cidade": "Curitiba", "estado": "PR", "capacidade": 41456},
    "Lotação Máxima":            {"cidade": "São Paulo", "estado": "SP", "capacidade": None}, 
    "Lourival Batista":          {"cidade": "Aracaju", "estado": "SE", "capacidade": 15000},  
    "Luís Aparecido Corridor":   {"cidade": "Ribeirão Preto", "estado": "SP", "capacidade": 14000},  
    "Maracanã":                  {"cidade": "Rio de Janeiro", "estado": "RJ", "capacidade": 78838},
    "Mineirão":                  {"cidade": "Belo Horizonte", "estado": "MG", "capacidade": 61846},
    "Morumbi":                   {"cidade": "São Paulo", "estado": "SP", "capacidade": 66795},
    "Neo Química Arena":         {"cidade": "São Paulo", "estado": "SP", "capacidade": 49205},
    "Olímpico Monumental":       {"cidade": "Porto Alegre", "estado": "RS", "capacidade": 50000},
    "PV":                        {"cidade": "Maceió", "estado": "AL", "capacidade": 16000},  
    "Ressacada":                 {"cidade": "Florianópolis", "estado": "SC", "capacidade": 17200},  
    "Santa Cruz":                {"cidade": "Natal", "estado": "RN", "capacidade": 20000},  
    "Serra Dourada":             {"cidade": "Goiânia", "estado": "GO", "capacidade": 53000},  
    "Serrinha":                  {"cidade": "Goiânia", "estado": "GO", "capacidade": 11500},  
    "Vila Belmiro":              {"cidade": "Santos", "estado": "SP", "capacidade": 16798},
    "Vivaldo Lima":              {"cidade": "Manaus", "estado": "AM", "capacidade": 40000},  
    "Walter Ribeiro":            {"cidade": "Sorocaba", "estado": "SP", "capacidade": 14000},  
    "aracana":                   {"cidade": "Rio de Janeiro", "estado": "RJ", "capacidade": 78838},  # Maracanã com nome sujo no CSV
}


# ─── DADOS DOS CLUBES ─────────────────────────────────────────────────────────
# Coluna ano_fundacao não existe ainda — o script adiciona via ALTER TABLE

CLUBES_INFO = {
    "América Mineiro":       1912,
    "América de Natal":      1915,  
    "Athletico Paranaense":  1924,
    "Atlético Goianiense":   1937,
    "Atlético Mineiro":      1908,
    "Avaí":                  1923,
    "Bahia":                 1931,
    "Botafogo":              1894,
    "Red Bull Bragantino":   1928,
    "Ceará":                 1914,
    "Chapecoense":           1973,
    "Corinthians":           1910,
    "Coritiba":              1909,
    "Criciúma":              1947,
    "Cruzeiro":              1921,
    "CSA":                   1913,
    "Cuiabá":                2001,
    "Figueirense":           1921,
    "Flamengo":              1895,
    "Fluminense":            1902,
    "Fortaleza":             1918,
    "Goiás":                 1943,
    "Grêmio":                1903,
    "Grêmio Barueri":        1981,  
    "Grêmio Prudente":       1940,  
    "Guarani":               1911,
    "Internacional":         1909,
    "Ipatinga":              1956,  
    "Joinville":             1913,
    "Juventude":             1913,
    "Náutico":               1901,
    "Palmeiras":             1914,
    "Paraná":                1989, 
    "Paysandu":              1914,
    "Ponte Preta":           1900,
    "Portuguesa":            1920,
    "Santa Cruz":            1914,
    "Santo André":           1967,  
    "Santos":                1912,
    "São Caetano":           1949,  
    "São Paulo":             1930,
    "Sport":                 1905,
    "Vasco da Gama":         1898,
    "Vitória":               1899,
}


# ─── EXECUÇÃO ─────────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("SEED DE DADOS EXTRAS — Estádios e Clubes")
    print("=" * 80)

    engine = get_postgres_engine()
    Session = sessionmaker(bind=engine)
    session = Session()

    # Adiciona coluna ano_fundacao nos clubes se não existir
    print("\nVerificando coluna ano_fundacao em clubes...")
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE clubes ADD COLUMN IF NOT EXISTS ano_fundacao INTEGER"))
            conn.commit()
            print("  Coluna ano_fundacao OK")
        except Exception as e:
            print(f"  {e}")

    # Atualiza estádios
    print("\nAtualizando estádios...")
    estadios_atualizados = 0
    estadios_nao_encontrados = []

    todos_estadios = session.query(Estadio).all()
    for estadio in todos_estadios:
        info = ESTADIOS_INFO.get(estadio.nome)
        if info:
            estadio.cidade = info.get("cidade")
            estadio.estado = info.get("estado")
            if info.get("capacidade"):
                estadio.capacidade = info["capacidade"]
            estadios_atualizados += 1
        else:
            estadios_nao_encontrados.append(estadio.nome)

    session.commit()
    print(f"  Atualizados: {estadios_atualizados}")
    if estadios_nao_encontrados:
        print(f"  Não encontrados no dicionário ({len(estadios_nao_encontrados)}):")
        for nome in estadios_nao_encontrados:
            print(f"    - '{nome}'")

    # Atualiza clubes
    print("\nAtualizando clubes...")
    clubes_atualizados = 0
    clubes_nao_encontrados = []

    todos_clubes = session.query(Clube).all()
    for clube in todos_clubes:
        ano = CLUBES_INFO.get(clube.nome_oficial)
        if ano:
            clube.ano_fundacao = ano
            clubes_atualizados += 1
        else:
            clubes_nao_encontrados.append(clube.nome_oficial)

    session.commit()
    print(f"  Atualizados: {clubes_atualizados}")
    if clubes_nao_encontrados:
        print(f"  Não encontrados no dicionário ({len(clubes_nao_encontrados)}):")
        for nome in clubes_nao_encontrados:
            print(f"    - '{nome}'")

    session.close()
    print("\n" + "=" * 80)
    print("Concluído! Verifique os itens marcados com  no script.")
    print("=" * 80)


if __name__ == "__main__":
    main()