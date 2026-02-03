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
# Buscar versões disponíveis
winget search Python.Python.3.11

# Instalar Python 3.11
winget install Python.Python.3.11

# Verificar instalação
py -3.11 --version
```

### Opção 2: Download Manual

1. Acesse: https://www.python.org/downloads/release/python-31111/
2. Baixe o instalador **Windows installer (64-bit)**
3. Durante a instalação:
   -Marque **"Add Python 3.11 to PATH"**
   -Escolha **"Install for all users"** (opcional)
4. Após instalação, verifique:
   ```powershell
   py -3.11 --version
   # Deve retornar: Python 3.11.11 (ou similar)
   ```

---

## 2️. Instalar Docker Desktop

### Via Winget (Recomendado)

```powershell
winget install Docker.DockerDesktop
```

### Download Manual

1. Acesse: https://www.docker.com/products/docker-desktop/
2. Baixe o instalador para Windows
3. Execute o instalador e siga as instruções
4. **Importante**: Após a instalação, reinicie o computador
5. Abra o Docker Desktop e aguarde ele inicializar completamente (ícone da baleia fica verde)

### Verificar Instalação

```powershell
docker --version
docker-compose --version
```

**Saída esperada:**
```
Docker version 24.x.x
Docker Compose version v2.x.x
```

**Tutorial em vídeo (se precisar)**: https://www.youtube.com/watch?v=5nX8U8Fz5S0

---

## 3️. Clonar o Repositório

```powershell
# Navegue até a pasta onde quer salvar o projeto
cd C:\Users\SEU_USUARIO\Documents

# Clone o repositório
git clone <URL_DO_REPOSITORIO>

# Entre na pasta do projeto
cd football_consultant_br
```

---

## 4️. Criar Ambiente Virtual (venv)

```powershell
# Criar venv com Python 3.11
py -3.11 -m venv venv

# Ativar o ambiente virtual
.\venv\Scripts\Activate.ps1
```

**Se der erro de permissão no PowerShell:**
```powershell
# Execute como Administrador:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Depois tente ativar novamente:
.\venv\Scripts\Activate.ps1
```

**Como saber se deu certo?**
- Você verá `(venv)` no início da linha do terminal
- Exemplo: `(venv) PS C:\...\football_consultant_br>`

---

## 5️. Instalar Dependências Python

```powershell
# Com o venv ativado, instale as dependências
pip install --upgrade pip
pip install -r requirements.txt
```

**Dependências principais que serão instaladas:**
- FastAPI (framework backend)
- SQLAlchemy (PostgreSQL)
- PyMongo (MongoDB)
- cassandra-driver (AstraDB/Cassandra)
- E outras...

---

## 6️. Configurar Variáveis de Ambiente

### Passo 1: Copiar o template

```powershell
# Criar o arquivo .env a partir do exemplo
Copy-Item .env.example .env
```

### Passo 2: Editar o arquivo `.env`

Abra o arquivo `.env` em um editor de texto e ajuste as configurações:

```env
# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=futebol_brasileiro
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres123

# MongoDB
MONGO_URI=mongodb://admin:admin123@localhost:27017/futebol_brasileiro?authSource=admin
MONGO_DB=futebol_brasileiro

# AstraDB (Cassandra)
ASTRA_DB_SECURE_BUNDLE_PATH=app/config/secure-connect-futebol-db.zip
ASTRA_DB_TOKEN_PATH=app/config/futebol_db-token.json
ASTRA_DB_KEYSPACE=brasileirao
```

**IMPORTANTE**: Não altere as credenciais do PostgreSQL e MongoDB (elas já batem com o docker-compose.yml)

---

## 7️. Configurar AstraDB (Cassandra na Nuvem)

### Opção A: Usar credenciais compartilhadas (seu colega vai fazer)

Peça ao seu colega de equipe:
1. O arquivo **Secure Connect Bundle** (`.zip`)
2. O arquivo **Token JSON** (`.json`)

Coloque esses arquivos na pasta `app/config/`:
```
app/config/
├── secure-connect-futebol-db.zip
└── futebol_db-token.json
```

### Opção B: Criar sua própria conta no AstraDB

Se você quiser criar sua própria instância:

1. **Criar conta gratuita**
   - Acesse: https://astra.datastax.com/
   - Clique em **"Try for Free"**
   - Crie uma conta (pode usar Google/GitHub)

2. **Criar um Database**
   - No painel, clique em **"Create Database"**
   - Preencha:
     - **Database name**: `futebol-db`
     - **Keyspace name**: `brasileirao`
     - **Provider**: `Google Cloud` (grátis)
     - **Region**: Escolha o mais próximo
   - Clique em **"Create Database"**
   - Aguarde 2-3 minutos até ficar "Active"

3. **Baixar o Secure Connect Bundle**
   - No painel do database, clique em **"Connect"**
   - Clique em **"Download Secure Connect Bundle"**
   - Salve o arquivo `.zip` em `app/config/`
   - Renomeie para: `secure-connect-futebol-db.zip`

4. **Gerar Token de Aplicação**
   - Vá em **"Settings"** → **"Tokens"**
   - Clique em **"Generate Token"**
   - Escolha role: **"Database Administrator"**
   - Clique em **"Generate Token"**
   - Baixe o arquivo JSON
   - Salve em `app/config/futebol_db-token.json`

**Tutorial em vídeo**: https://www.youtube.com/watch?v=S7d0sjOIG7E

---

## 8️. Subir os Containers Docker (PostgreSQL + MongoDB)

```powershell
# Certifique-se que o Docker Desktop está rodando (ícone da baleia)

# Subir os containers em modo background
docker-compose up -d

# Verificar se os containers estão rodando
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
# Ver logs em tempo real
docker-compose logs -f

# Parar os containers
docker-compose stop

# Iniciar novamente
docker-compose start

# Parar e remover (dados persistem)
docker-compose down
```

---

## 9️. Testar Conexões com os Bancos

```powershell
# Com o venv ativado, rode:
python -m app.config.database
```

**Saída esperada (SUCESSO!):**
```
============================================================
TESTANDO CONEXÕES COM OS BANCOS DE DADOS
============================================================
PostgreSQL conectado!
   Database: futebol_brasileiro
   Usuário: postgres
   Host: localhost:5433
MongoDB conectado!
   Versão: 7.0.29
   Databases disponíveis: ['admin', 'config', 'local']
AstraDB conectado!
   Versão do Cassandra: 4.0.11.0
   Keyspace: brasileirao
   Nenhuma tabela criada ainda no keyspace.

============================================================
📊 RESUMO DOS TESTES
============================================================
PostgreSQL     OK
MongoDB        OK
AstraDB        OK

Todos os bancos estão conectados corretamente!
```

---

## Troubleshooting (Resolução de Problemas)

### Problema: "Port 5432 already in use"

**Solução**: Você já tem PostgreSQL instalado localmente. Use porta diferente.

1. Edite `docker-compose.yml`:
   ```yaml
   postgres:
     ports:
       - "5433:5432"  # Mudar de 5432 para 5433
   ```

2. Edite `.env`:
   ```env
   POSTGRES_PORT=5433
   ```

3. Reinicie os containers:
   ```powershell
   docker-compose down
   docker-compose up -d
   ```

---

### Problema: "Unable to load a default connection class" (AstraDB)

**Causa**: Python 3.12+ tem incompatibilidade com cassandra-driver.

**Solução**: Use Python 3.11 conforme este guia.

---

### Problema: "Keyspace 'futebol_brasileiro' does not exist" (AstraDB)

**Solução**: Certifique-se que o keyspace no `.env` bate com o criado no AstraDB:

```env
ASTRA_DB_KEYSPACE=brasileirao  # ou o nome que você criou
```

---

### Problema: Containers não sobem

```powershell
# Ver os logs de erro
docker-compose logs

# Forçar rebuild
docker-compose up -d --build --force-recreate
```

---

## Estrutura Final do Projeto

Após configurado, você terá:

```
football_consultant_br/
├── venv/                          # Ambiente virtual (não vai pro Git)
├── app/
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── database.py
│   │   ├── secure-connect-futebol-db.zip  # Credenciais AstraDB
│   │   └── futebol_db-token.json          # Credenciais AstraDB
│   ├── models/
│   ├── repositories/
│   ├── routers/
│   └── services/
├── data/
│   └── brasileirao_dataset/
├── scripts/
├── .env                           # Suas configs (não vai pro Git)
├── .env.example                   # Template (vai pro Git)
├── .gitignore
├── docker-compose.yml
├── requirements.txt
├── SETUP.md                       # Este guia
└── README.md
```

---

##  Checklist Final

Marque conforme você for completando:

- [ ] Python 3.11 instalado e funcionando (`py -3.11 --version`)
- [ ] Docker Desktop instalado e rodando
- [ ] Repositório clonado
- [ ] Ambiente virtual criado e ativado (`venv`)
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Arquivo `.env` criado e configurado
- [ ] Arquivos do AstraDB na pasta `app/config/`
- [ ] Containers Docker rodando (`docker-compose ps`)
- [ ] Teste de conexões passou (3/3 bancos)

---

##  Precisa de Ajuda?

Se você seguiu todos os passos e algo não funcionou:

1. **Veja os logs**:
   ```powershell
   docker-compose logs
   python -m app.config.database
   ```

2. **Recursos úteis**:
   - AstraDB Docs: https://docs.datastax.com/en/astra/home/
   - Docker Docs: https://docs.docker.com/
