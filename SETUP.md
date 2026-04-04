# Guia de Setup - Consultor do Futebol Brasileiro

Este guia vai te ajudar a configurar todo o ambiente de desenvolvimento do projeto do zero.

---

## Pré-requisitos

Antes de começar, você vai precisar instalar:
- **Python 3.11** (não use 3.12+)
- **Docker Desktop** (para PostgreSQL e MongoDB)
- **Git** (para clonar o repositório)

---

## 1. Instalar Python 3.11

### Opção 1: Via Winget (Recomendado - Windows 10/11)

```powershell
winget install Python.Python.3.11
py -3.11 --version
```

### Opção 2: Download Manual

1. Acesse: https://www.python.org/downloads/release/python-31111/
2. Baixe o instalador **Windows installer (64-bit)**
3. Durante a instalação:
   - Marque **"Add Python 3.11 to PATH"**
   - Escolha **"Install for all users"** (opcional)

---

## 2. Instalar Docker Desktop

```powershell
winget install Docker.DockerDesktop
```

Ou baixe em: https://www.docker.com/products/docker-desktop/

> **Importante**: Após instalar, reinicie o computador e aguarde o ícone da baleia ficar verde.

```powershell
docker --version
docker-compose --version
```

---

## 3. Clonar o Repositório

```powershell
cd C:\Users\SEU_USUARIO\Documents
git clone https://github.com/LucasGalvano/football-consultant-br/tree/main
cd football_consultant_br
```

---

## 4. Criar Ambiente Virtual

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
```

**Se der erro de permissão:**

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\venv\Scripts\Activate.ps1
```

Você verá `(venv)` no início da linha quando ativado corretamente.

---

## 5. Instalar Dependências

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 6. Configurar Variáveis de Ambiente

```powershell
Copy-Item .env.example .env
```

O `.env` já vem configurado corretamente para o Docker. **Não altere as credenciais do PostgreSQL e MongoDB.**

``` env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=futebol_brasileiro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=           # ← pedir ao responsável pelo projeto

# MongoDB
MONGO_USER=admin
MONGO_PASSWORD=              # ← pedir ao responsável pelo projeto
MONGO_DB=futebol_brasileiro
MONGO_URI=mongodb://${MONGO_USER}:${MONGO_PASSWORD}@localhost:27017/${MONGO_DB}?authSource=admin
```

---

## 7. Configurar AstraDB (Cassandra na Nuvem)

Peça ao responsável pelo projeto os dois arquivos de credenciais:
1. `secure-connect-futebol-db.zip`
2. `futebol_db-token.json`

Coloque ambos na pasta `app/config/`:

```
app/config/
├── secure-connect-futebol-db.zip
└── futebol_db-token.json
```

> ⚠️ Esses arquivos **não estão no repositório** por segurança. Sem eles a conexão com o Cassandra não vai funcionar.

---

## 8. Subir os Containers Docker

```powershell
docker-compose up -d
docker-compose ps
```

**Saída esperada:**

```
NAME               IMAGE                STATUS
futebol_mongo      mongo:7.0            Up (healthy)
futebol_postgres   postgres:15-alpine   Up (healthy)
```

**Comandos úteis:**

```powershell
docker-compose logs -f   # Ver logs em tempo real
docker-compose stop      # Parar os containers
docker-compose start     # Iniciar novamente
docker-compose down      # Parar e remover (dados persistem)
```

---

## 9. Testar Conexões com os Bancos

```powershell
python -m app.config.database
```

**Saída esperada:**

```
PostgreSQL     OK
MongoDB        OK
AstraDB        OK

Todos os bancos estão conectados corretamente!
```

> ⚠️ Se o AstraDB falhar, verifique se os arquivos do passo 7 estão na pasta correta.

---

## 10. Popular os Bancos de Dados

```powershell
python scripts/1_clean_datasets.py
python scripts/3_seed_postgres.py
python scripts/4_seed_mongo.py
python scripts/5_seed_cassandra.py
```

> O seed do Cassandra pode demorar alguns minutos. Aguarde até o final.

---

## 11. Verificar se Tudo foi Inserido

```powershell
python scripts/verificar_bancos.py
```

**Saída esperada:**

```
✅ Clubes:      34   (esperado: 34)
✅ Estádios:    74   (esperado: 74)
✅ Partidas:  4179   (esperado: 4179)
✅ Documentos: 3799  (esperado: 3799)
✅ Gols:       9859  (esperado: 9859)
✅ Cartões:   20953  (esperado: 20953)

🎉 Todos os bancos verificados com sucesso!
```

---

## Troubleshooting

### "Port 5432 already in use"
A porta já está configurada como `5433` no `docker-compose.yml` para evitar conflito. Verifique se o `.env` tem `POSTGRES_PORT=5433`.

### "Unable to load a default connection class" (AstraDB)
Incompatibilidade com Python 3.12+. Use Python 3.11 conforme este guia.

### "Keyspace does not exist" (AstraDB)
O keyspace no `.env` precisa ser exatamente `brasileirao`.

### Containers não sobem

```powershell
docker-compose logs
docker-compose up -d --build --force-recreate
```

### Seed falha com erro de duplicata
O banco já tem dados de uma execução anterior. Rode com reset:

```powershell
python scripts/3_seed_postgres.py --reset
```

---

## Checklist Final

- [ ] Python 3.11 instalado (`py -3.11 --version`)
- [ ] Docker Desktop instalado e rodando
- [ ] Repositório clonado
- [ ] Ambiente virtual criado e ativado (`venv`)
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Arquivo `.env` criado
- [ ] Arquivos do AstraDB em `app/config/`
- [ ] Containers Docker rodando (`docker-compose ps`)
- [ ] Teste de conexões passou (`python -m app.config.database`)
- [ ] Seeds rodados com sucesso
- [ ] Verificação passou (`python scripts/verificar_bancos.py`)