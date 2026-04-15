import { useApi } from '../hooks/useApi'
import { getClubes } from '../services/api'
import { Loading, ErrorAlert, EmptyState } from '../components/Common'
import { Link } from 'react-router-dom'
import { useState } from 'react'

export default function Clubes() {
  const { data: clubes, loading, error } = useApi(getClubes)
  const [search, setSearch] = useState('')

  if (loading) return <Loading />
  if (error) return <ErrorAlert message={error} />

  const filteredClubes = clubes?.filter(c =>
    c.nome_oficial.toLowerCase().includes(search.toLowerCase()) ||
    c.sigla.toLowerCase().includes(search.toLowerCase())
  ) || []

  return (
    <div className="space-y-6">
      <div className="brasil-gradient text-white rounded-xl p-8">
        <h1 className="text-4xl font-bold mb-2">🏆 Clubes Brasileiros</h1>
        <p className="text-gray-100">Explore todos os clubes que participaram do Campeonato Brasileiro (2014-2023)</p>
      </div>

      {/* Busca */}
      <div>
        <input
          type="text"
          placeholder="Buscar por nome ou sigla..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field w-full md:w-1/3"
        />
        <p className="text-sm text-gray-600 mt-2">{filteredClubes.length} clube(s) encontrado(s)</p>
      </div>

      {/* Grid de Clubes */}
      {filteredClubes.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredClubes.map(clube => (
            <Link
              key={clube.id}
              to={`/clubes/${clube.id}`}
              className="card group"
            >
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-bold text-brasil-dark group-hover:text-brasil-green">
                  {clube.nome_oficial}
                </h3>
                <span className="bg-brasil-yellow text-brasil-green px-3 py-1 rounded-full text-sm font-bold">
                  {clube.sigla}
                </span>
              </div>
              <div className="space-y-1 text-sm text-gray-600">
                <p><span className="font-medium">Estado:</span> {clube.estado}</p>
                <p><span className="font-medium">Fundado:</span> {clube.ano_fundacao || 'N/A'}</p>
                {clube.estadia_id && (
                  <p><span className="font-medium">ID:</span> {clube.id}</p>
                )}
              </div>
              <div className="mt-4 text-brasil-green font-bold hover:text-brasil-dark">
                Ver detalhes →
              </div>
            </Link>
          ))}
        </div>
      ) : (
        <EmptyState message="Nenhum clube encontrado com esse critério" />
      )}
    </div>
  )
}
