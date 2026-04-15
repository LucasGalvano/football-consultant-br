import { useApi } from '../hooks/useApi'
import { getPartidas } from '../services/api'
import { Loading, ErrorAlert, EmptyState } from '../components/Common'
import { Link } from 'react-router-dom'
import { useState } from 'react'

export default function Partidas() {
  const [filters, setFilters] = useState({
    ano: null,
    rodada: null,
    clube_id: null,
    pagina: 1,
    por_pagina: 20,
  })

  const { data: response, loading, error } = useApi(
    () => getPartidas(filters),
    [filters.ano, filters.rodada, filters.clube_id, filters.pagina]
  )

  const partidas = response?.dados || []
  const total = response?.total || 0
  const pagina = response?.pagina || 1
  const totalPaginas = Math.ceil(total / filters.por_pagina)

  const handleFilter = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value, pagina: 1 }))
  }

  return (
    <div className="space-y-6">
      <div className="brasil-gradient text-white rounded-xl p-8">
        <h1 className="text-4xl font-bold mb-2">📅 Partidas do Brasileirão</h1>
        <p className="text-gray-100">Explore todas as partidas com detalhes completos de gols, cartões e estatísticas</p>
      </div>

      {/* Filtros */}
      <div className="card">
        <h3 className="font-bold text-lg mb-4">🔍 Filtros</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Ano</label>
            <input
              type="number"
              value={filters.ano || ''}
              onChange={(e) => handleFilter('ano', e.target.value ? parseInt(e.target.value) : null)}
              placeholder="2023"
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Rodada</label>
            <input
              type="number"
              value={filters.rodada || ''}
              onChange={(e) => handleFilter('rodada', e.target.value ? parseInt(e.target.value) : null)}
              placeholder="1-38"
              min="1"
              max="38"
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">ID do Clube</label>
            <input
              type="number"
              value={filters.clube_id || ''}
              onChange={(e) => handleFilter('clube_id', e.target.value ? parseInt(e.target.value) : null)}
              placeholder="1"
              className="input-field"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Resultados/Página</label>
            <select
              value={filters.por_pagina}
              onChange={(e) => setFilters(prev => ({ ...prev, por_pagina: parseInt(e.target.value), pagina: 1 }))}
              className="input-field"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        </div>
      </div>

      {/* Resultados */}
      {loading ? (
        <Loading />
      ) : error ? (
        <ErrorAlert message={error} />
      ) : partidas.length > 0 ? (
        <>
          <div className="space-y-4">
            {partidas.map(partida => (
              <Link
                key={partida.id}
                to={`/partidas/${partida.id}`}
                className="card group hover:border-brasil-green border-2 border-transparent"
              >
                <div className="flex flex-col md:flex-row items-start md:items-center justify-between">
                  <div className="flex-1">
                    <div className="text-sm text-gray-500 mb-1">
                      Rodada {partida.rodada} • {new Date(partida.data).toLocaleDateString('pt-BR')}
                      {partida.hora && ` às ${partida.hora}`}
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="font-bold text-brasil-dark">{partida.mandante}</span>
                      <span className="bg-brasil-yellow text-brasil-green px-3 py-1 rounded-lg font-bold text-lg">
                        {partida.placar_mandante}×{partida.placar_visitante}
                      </span>
                      <span className="font-bold text-brasil-dark">{partida.visitante}</span>
                    </div>
                    <p className="text-sm text-gray-500 mt-2">📍 {partida.estadio}</p>
                  </div>
                  {partida.vencedor && (
                    <div className="mt-2 md:mt-0 text-right">
                      <p className="text-xs text-gray-600">Vencedor</p>
                      <p className="font-bold text-brasil-green">{partida.vencedor}</p>
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>

          {/* Paginação */}
          {totalPaginas > 1 && (
            <div className="flex justify-center gap-2">
              <button
                onClick={() => setFilters(prev => ({ ...prev, pagina: prev.pagina - 1 }))}
                disabled={pagina === 1}
                className="px-3 py-2 bg-gray-300 rounded disabled:opacity-50"
              >
                ← Anterior
              </button>
              <div className="px-3 py-2">
                Página {pagina} de {totalPaginas}
              </div>
              <button
                onClick={() => setFilters(prev => ({ ...prev, pagina: prev.pagina + 1 }))}
                disabled={pagina === totalPaginas}
                className="px-3 py-2 bg-brasil-green text-white rounded disabled:opacity-50"
              >
                Próxima →
              </button>
            </div>
          )}
        </>
      ) : (
        <EmptyState message="Nenhuma partida encontrada com os filtros selecionados" />
      )}
    </div>
  )
}
