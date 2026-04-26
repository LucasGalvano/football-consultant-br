import { useApi } from '../hooks/useApi'
import { getEstadios } from '../services/api'
import { Loading, ErrorAlert, EmptyState } from '../components/Common'
import { useState } from 'react'

export default function Estadios() {
  const { data: estadios, loading, error } = useApi(getEstadios)
  const [search, setSearch] = useState('')

  if (loading) return <Loading />
  if (error) return <ErrorAlert message={error} />

  const filteredEstadios = estadios?.filter(e =>
    e.nome.toLowerCase().includes(search.toLowerCase()) ||
    (e.cidade && e.cidade.toLowerCase().includes(search.toLowerCase()))
  ) || []

  return (
    <div className="space-y-6">
      <div className="brasil-gradient text-white rounded-xl p-8">
        <h1 className="text-4xl font-bold mb-2">🏟️ Estádios</h1>
        <p className="text-gray-100">Conheça todos os estádios que sediam partidas do Campeonato Brasileiro</p>
      </div>

      {/* Busca */}
      <div>
        <input
          type="text"
          placeholder="Buscar por nome ou cidade..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input-field w-full md:w-1/3"
        />
        <p className="text-sm text-gray-600 mt-2">{filteredEstadios.length} estádio(s) encontrado(s)</p>
      </div>

      {/* Grid de Estádios */}
      {filteredEstadios.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredEstadios.map(estadio => (
            <div key={estadio.id} className="card">
              <h3 className="text-lg font-bold text-brasil-dark mb-3">
                🏟️ {estadio.nome}
              </h3>
              <div className="space-y-2 text-sm">
                <p>
                  <span className="font-medium text-gray-600">Cidade:</span>{' '}
                  {estadio.cidade || <span className="text-gray-400 italic">Não informada</span>}
                </p>
                <p>
                  <span className="font-medium text-gray-600">Estado:</span>{' '}
                  {estadio.estado || <span className="text-gray-400 italic">Não informado</span>}
                </p>
                {estadio.capacidade && (
                  <p>
                    <span className="font-medium text-gray-600">Capacidade:</span>{' '}
                    {estadio.capacidade.toLocaleString('pt-BR')}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState message="Nenhum estádio encontrado com esse critério" />
      )}
    </div>
  )
}