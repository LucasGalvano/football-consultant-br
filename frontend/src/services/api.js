import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
  timeout: 120000, // 2 minutos — queries no Cassandra podem demorar
})

// Health check
export const checkHealth = () => api.get('/health')

// Clubes
export const getClubes = () => api.get('/clubes/')
export const getClubeById = (id) => api.get(`/clubes/${id}`)

// Estádios
export const getEstadios = () => api.get('/estadios/')
export const getEstadioById = (id) => api.get(`/estadios/${id}`)

// Partidas
export const getPartidas = (params) => api.get('/partidas/', { params })
export const getPartidaById = (id) => api.get(`/partidas/${id}`)
export const getPartidaGols = (id) => api.get(`/partidas/${id}/gols`)
export const getPartidaCartoes = (id) => api.get(`/partidas/${id}/cartoes`)
export const getPartidaEstatisticas = (id) => api.get(`/partidas/${id}/estatisticas`)

// Análises
export const getAnosDisponiveis = () => api.get('/analises/anos')
export const getClassificacao = (ano) => api.get(`/analises/classificacao/${ano}`)
export const getArtilheiros = (params) => api.get('/analises/artilheiros', { params })
export const getRankingCartoes = (params) => api.get('/analises/ranking-cartoes', { params })
export const getEstatisticasClube = (clubeId) => api.get(`/analises/clube/${clubeId}/estatisticas`)
export const getConfrontoDireto = (clube1Id, clube2Id) =>
  api.get('/analises/confronto', {
    params: { clube1_id: clube1Id, clube2_id: clube2Id }
  })

export default api