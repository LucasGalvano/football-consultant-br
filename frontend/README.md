# ⚽ Consultor do Futebol Brasileiro — Frontend

Uma aplicação web moderna e responsiva para análise e consulta de dados do Campeonato Brasileiro.

## 🚀 Stack Tecnológico

- **React 18** — Library UI
- **Vite** — Build tool rápido
- **Tailwind CSS** — Estilização responsiva
- **React Router** — Navegação entre páginas
- **Axios** — Cliente HTTP
- **Recharts** — Gráficos e visualizações

## 📦 Instalação & Setup

### Requisitos
- Node.js 16+ (com npm)
- Backend rodando em `http://localhost:8000`

### Passos

1. **Instalar dependências**
   ```bash
   cd frontend
   npm install
   ```

2. **Configurar variáveis de ambiente**
   ```bash
   # Copiar exemplo
   cp .env.example .env.local
   
   # Editar se necessário (padrão já é http://localhost:8000)
   ```

3. **Rodar em desenvolvimento**
   ```bash
   npm run dev
   ```
   Abre automaticamente em `http://localhost:5173`

4. **Build para produção**
   ```bash
   npm run build
   # Saída em: frontend/dist/
   ```

## 📁 Estrutura do Projeto

```
src/
├── pages/              # Páginas principais
│   ├── Home.jsx              # Página inicial
│   ├── Clubes.jsx            # Listagem de clubes
│   ├── ClubeDetail.jsx       # Detalhe de um clube
│   ├── Partidas.jsx          # Listagem com filtros
│   ├── PartidaDetail.jsx     # Detalhe completo da partida
│   ├── Estadios.jsx          # Listagem de estádios
│   ├── Classificacao.jsx     # Tabela de classificação
│   ├── Artilheiros.jsx       # Rankings (artilheiros + cartões)
│   └── Confronto.jsx         # Confronto direto entre clubes
│
├── components/         # Componentes reutilizáveis
│   ├── Layout.jsx            # Wrapper da aplicação
│   ├── Header.jsx            # Menu navegação
│   ├── Footer.jsx            # Rodapé
│   └── Common.jsx            # Componentes utilitários
│
├── services/           # Chamadas à API
│   └── api.js                # Cliente Axios centralizado
│
├── hooks/              # Custom React hooks
│   └── useApi.js             # Hook para requisições
│
├── assets/             # Imagens, ícones (se houver)
│
├── App.jsx             # Configuração de rotas
├── main.jsx            # Entrada da aplicação
└── index.css           # Estilos globais
```

## 🎨 Tema e Cores

O design segue as cores da bandeira brasileira:

- **Verde**: `#1e3a1f` (brasil-green) — Primária
- **Amarelo**: `#ffd700` (brasil-yellow) — Destaque
- **Branco**: `#ffffff` (brasil-white) — Fundo
- **Verde escuro**: `#0d1b0e` (brasil-dark) — Hover/Dark

## 📋 Funcionalidades Implementadas

### ✅ Páginas & Features

| Página | Features |
|--------|----------|
| **Home** | Cards de estatísticas, anos disponíveis, atalhos rápidos |
| **Clubes** | Listagem com busca por nome/sigla, cards informativos |
| **Detalhe de Clube** | Estatísticas tática (posse, passes, chutes, faltas) |
| **Partidas** | Filtros (ano, rodada, clube, estádio), paginação |
| **Detalhe de Partida** | Placar, gols, cartões, estatísticas, técnicos, formações |
| **Estádios** | Listagem com busca, dados de capacidade e fundação |
| **Classificação** | Tabela com seletor de ano, cores por posição (Libertadores/Rebaixamento) |
| **Artilheiros** | Top goleadores + ranking de cartões (amarelo/vermelho), filtros |
| **Confronto Direto** | Seletor de 2 clubes, histórico, estatísticas comparativas |

### 🔄 Recursos Técnicos

- ✅ Hook customizado `useApi` para requisições
- ✅ Tratamento de loading e erro em todas as chamadas
- ✅ Responsivo (mobile, tablet, desktop)
- ✅ Menu mobile com toggle
- ✅ Componentes reutilizáveis (Common.jsx)
- ✅ Navegação com React Router
- ✅ Tailwind CSS com classes utilitárias

## 🔌 Integração com API

A aplicação se conecta aos endpoints FastAPI do backend:

```javascript
// services/api.js centraliza todas as chamadas
GET  /clubes              → List all clubs
GET  /clubes/{id}         → Club details
GET  /estadios            → List stadiums
GET  /partidas            → Matches with filters
GET  /partidas/{id}       → Match details (all 3 databases)
GET  /analises/anos       → Available years
GET  /analises/classificacao/{ano} → Championship table
GET  /analises/artilheiros        → Top scorers
GET  /analises/ranking-cartoes    → Card rankings
GET  /analises/confronto          → Head-to-head stats
```

Variável de ambiente: `VITE_API_URL` (padrão: http://localhost:8000)

## 🛠️ Desenvolvimento

### Adicionar nova página

1. Criar arquivo em `src/pages/NovaPage.jsx`
2. Importar em `src/App.jsx`
3. Adicionar rota no componente `Routes`
4. Adicionar link no `Header.jsx` (se necessário)

### Adicionar novo endpoint

1. Implementar função em `src/services/api.js`
2. Usar hook `useApi` para consumir em componentes

### Customizar estilos

- Classes globais: `src/index.css`
- Tailwind config: `tailwind.config.js`
- Componentes: Use classes Tailwind inline

## 📊 Exemplo de Uso do Hook useApi

```jsx
import { useApi } from '../hooks/useApi'
import { getClubes } from '../services/api'

export default function MinhaPage() {
  const { data, loading, error } = useApi(getClubes)

  if (loading) return <p>Carregando...</p>
  if (error) return <p>Erro: {error}</p>
  
  return <div>{/* render data */}</div>
}
```

## 🚀 Deploy

### Vercel (recomendado)

```bash
npm install -g vercel
vercel
# Follow prompts
```

### Docker

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
EXPOSE 5173
CMD ["npm", "run", "preview"]
```

### Variáveis de Ambiente em Produção

Na plataforma de deploy, adicione:
```
VITE_API_URL=https://seu-backend.com
```

## 📝 Notas

- O frontend espera que a API esteja rodando e acessível em `VITE_API_URL`
- Todos os endpoints retornam JSON
- Loading states e error alerts são tratados automaticamente
- A interface é completamente responsiva
- Menu mobile funciona em telas < 768px

## 🐛 Troubleshooting

### "Failed to fetch from API"
- Verifique se o backend está rodando em `http://localhost:8000`
- Confira a variável `VITE_API_URL` em `.env.local`
- Verifique CORS no backend (FastAPI já tem configurado)

### "npm install fails"
- Delete `node_modules` e `package-lock.json`
- Run `npm install` novamente
- Verifique versão do Node (16+)

## 📄 Licença

MIT — Livre para uso educacional e comercial

---

Desenvolvido com ⚽ e ❤️
