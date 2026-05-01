import { useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getClubeById, getEstatisticasClube } from '../services/api'
import { Loading, ErrorAlert, EmptyState } from '../components/Common'

function StatCard({ label, value, unit = '' }) {
  if (value === null || value === undefined) return null
  return (
    <div className="card text-center">
      <p className="text-gray-600 text-sm">{label}</p>
      <p className="text-3xl font-bold text-brasil-green">
        {typeof value === 'number' ? value.toFixed(1) : value}{unit}
      </p>
    </div>
  )
}

function StatsTable({ titulo, dados }) {
  if (!dados || Object.keys(dados).length === 0) return null
  const labels = {
    media_posse: 'Posse de Bola Média',
    media_chutes: 'Chutes por Jogo',
    media_passes: 'Passes por Jogo',
    media_finalizacoes: 'Finalizações por Jogo',
    media_escanteios: 'Escanteios por Jogo',
    total_partidas: 'Total de Partidas',
  }
  return (
    <div className="card">
      <h4 className="font-bold text-brasil-green mb-3">{titulo}</h4>
      <table className="w-full text-sm">
        <tbody>
          {Object.entries(dados).map(([key, value]) => (
            <tr key={key} className="border-b border-gray-100">
              <td className="py-2 text-gray-600">{labels[key] || key.replace(/_/g, ' ')}</td>
              <td className="py-2 text-right font-bold">
                {typeof value === 'number' ? value.toFixed(2) : String(value ?? '—')}
                {key === 'media_posse' ? '%' : ''}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function ClubeDetail() {
  const { id } = useParams()
  const { data: clube, loading: loadingClube, error: errorClube } = useApi(() => getClubeById(id))
  const { data: stats, loading: loadingStats } = useApi(() => getEstatisticasClube(id))

  if (loadingClube || loadingStats) return <Loading />
  if (errorClube) return <ErrorAlert message={errorClube} />
  if (!clube) return <EmptyState message="Clube não encontrado" />

  const mandante = stats?.como_mandante || {}
  const visitante = stats?.como_visitante || {}

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="brasil-gradient text-white rounded-xl p-8">
        <h1 className="text-4xl font-bold mb-2">{clube.nome_oficial}</h1>
        <div className="flex gap-4 items-center">
          <span className="bg-brasil-yellow text-brasil-green px-4 py-2 rounded-lg font-bold text-xl">
            {clube.sigla}
          </span>
          <p className="text-gray-100">Estado: {clube.estado || 'N/A'}</p>
        </div>
      </div>

      {/* Cards resumo como mandante */}
      {mandante.total_partidas > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-brasil-dark mb-4">📊 Estatísticas como Mandante</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <StatCard label="Partidas" value={mandante.total_partidas} />
            <StatCard label="Posse Média" value={mandante.media_posse} unit="%" />
            <StatCard label="Passes/Jogo" value={mandante.media_passes} />
            <StatCard label="Chutes/Jogo" value={mandante.media_chutes} />
          </div>
        </div>
      )}

      {/* Cards resumo como visitante */}
      {visitante.total_partidas > 0 && (
        <div>
          <h2 className="text-2xl font-bold text-brasil-dark mb-4">✈️ Estatísticas como Visitante</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <StatCard label="Partidas" value={visitante.total_partidas} />
            <StatCard label="Posse Média" value={visitante.media_posse} unit="%" />
            <StatCard label="Passes/Jogo" value={visitante.media_passes} />
            <StatCard label="Chutes/Jogo" value={visitante.media_chutes} />
          </div>
        </div>
      )}

      {/* Tabelas detalhadas lado a lado */}
      {(mandante.total_partidas > 0 || visitante.total_partidas > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <StatsTable titulo="🏠 Detalhes como Mandante" dados={mandante} />
          <StatsTable titulo="✈️ Detalhes como Visitante" dados={visitante} />
        </div>
      )}

      {!stats && (
        <EmptyState message="Sem estatísticas disponíveis para este clube" />
      )}
    </div>
  )
}