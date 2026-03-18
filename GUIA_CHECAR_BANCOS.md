# 🔍 GUIA COMPLETO: Como Checar os Bancos de Dados


## 1️⃣ PostgreSQL (Docker)

### **Via Terminal (CLI)**

```powershell
# Entrar no container do PostgreSQL
docker exec -it futebol_postgres psql -U postgres -d futebol_brasileiro
```

**Comandos úteis dentro do psql:**

```sql
-- Listar todas as tabelas
\dt

-- Ver estrutura de uma tabela
\d clubes
\d partidas

-- Contar registros
SELECT COUNT(*) FROM clubes;
SELECT COUNT(*) FROM estadios;
SELECT COUNT(*) FROM partidas;

-- Ver primeiros registros
SELECT * FROM clubes LIMIT 10;
SELECT * FROM partidas LIMIT 5;

-- Query com JOIN (exemplo)
SELECT 
    p.data,
    m.nome_oficial as mandante,
    v.nome_oficial as visitante,
    p.placar_mandante,
    p.placar_visitante
FROM partidas p
JOIN clubes m ON p.mandante_id = m.id
JOIN clubes v ON p.visitante_id = v.id
LIMIT 10;

-- Sair do psql
\q
```

---

## 2️⃣ MongoDB (Docker)

### **Via Terminal (mongosh)**

```powershell
# Entrar no container do MongoDB
docker exec -it futebol_mongo mongosh -u admin -p admin123 --authenticationDatabase admin
```

**Comandos úteis dentro do mongosh:**

```javascript
// Listar databases
show dbs

// Usar o database do projeto
use futebol_brasileiro

// Listar collections
show collections

// Contar documentos
db.partidas_estatisticas.countDocuments()

// Ver um documento de exemplo
db.partidas_estatisticas.findOne()

// Ver primeiros 5 documentos (formatado)
db.partidas_estatisticas.find().limit(5).pretty()

// Query específica
db.partidas_estatisticas.find({
  "ano": 2020,
  "mandante.nome": "Flamengo"
}).limit(3)

// Agregação (média de posse de bola)
db.partidas_estatisticas.aggregate([
  { $match: { "mandante.nome": "Flamengo" }},
  { $group: {
      _id: null,
      media_posse: { $avg: "$mandante.estatisticas.posse_de_bola" }
  }}
])

// Sair
exit
```

---

## 3️⃣ Cassandra/AstraDB (Cloud)

### **CQL Console (Web - Mais Fácil!)**

#### **1. Acessar o Dashboard**

1. Vá para: https://astra.datastax.com
2. Faça login
3. Clique no seu database (**futebol-db** ou como você nomeou)

#### **2. Abrir CQL Console**

1. No menu lateral, clique em **"CQL Console"**
2. Ou vá em **"Connect"** → **"Launch CQL Console"**
3. Aguarde carregar (pode demorar ~10 segundos)

#### **3. Executar Queries**

```cql
-- Ver tabelas
DESCRIBE TABLES;

-- Contar gols
SELECT COUNT(*) FROM gols_por_partida;

-- Contar cartões
SELECT COUNT(*) FROM cartoes_por_partida;

-- Ver gols de uma partida específica
SELECT atleta, clube, minuto, tipo_gol
FROM gols_por_partida
WHERE partida_id = 5000;

-- Ver cartões de uma partida
SELECT atleta, clube, tipo_cartao, minuto
FROM cartoes_por_partida
WHERE partida_id = 5000;

-- Gols de pênalti (usa ALLOW FILTERING - lento!)
SELECT partida_id, atleta, clube, minuto
FROM gols_por_partida
WHERE tipo_gol = 'Penalty'
ALLOW FILTERING
LIMIT 10;
```

---

---

## 🎯 Checklist de Verificação

Depois de rodar os seeds, verifique:

- [ ] **PostgreSQL**: 34 clubes, 74 estádios, 4.179 partidas
- [ ] **MongoDB**: 3.799 documentos
- [ ] **Cassandra**: 9.861 gols + 20.953 cartões

---

**Pronto! Agora você sabe checar tudo! 🎉**
