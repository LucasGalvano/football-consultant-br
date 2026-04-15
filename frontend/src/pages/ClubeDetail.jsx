import { useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getClubeById, getEstatisticasClube } from '../services/api'
import { Loading, ErrorAlert, EmptyState } from '../components/Common'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export default function ClubeDetail() {
  const { id } = useParams()
  const { data: clube, loading: loadingClube, error: errorClube } = useApi(() => getClubeById(id))
  const { data: stats, loading: loadingStats } = useApi(() => getEstatisticasClube(id))

  if (loadingClube || loadingStats) return <Loading />
  if (errorClube) return <ErrorAlert message={errorClube} />
  if (!clube) return <EmptyState message="Clube não encontrado" />

  return (
    <div className="space-y-8">
      {/* Header do Clube */}
      <div className="brasil-gradient text-white rounded-xl p-8">
        <h1 className="text-4xl font-bold mb-2">{clube.nome_oficial}</h1>
        <div className="flex gap-4 items-center">
          <span className="bg-brasil-yellow text-brasil-green px-4 py-2 rounded-lg font-bold text-xl">
            {clube.sigla}
          </span>
          <p className="text-gray-100">Estado: {clube.estado}</p>
          {clube.ano_fundacao && <p className="text-gray-100">Fundado: {clube.ano_fundacao}</p>}
        </div>
      </div>

      {/* Estatísticas */}
      {stats && (
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-brasil-dark">📊 Estatísticas do Clube</h2>

          {/* Cards de Stats Principais */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {stats.media_posse_bola && (
              <div className="card text-center">
                <p className="text-gray-600 text-sm">Posse de Bola Média</p>
                <p className="text-3xl font-bold text-brasil-green">
                  {(stats.media_posse_bola * 100).toFixed(1)}%
                </p>
              </div>
            )}
            {stats.media_passes && (
              <div className="card text-center">
                <p className="text-gray-600 text-sm">Passes Médios</p>
                <p className="text-3xl font-bold text-brasil-green">
                  {stats.media_passes.toFixed(0)}
                </p>
              </div>
            )}
            {stats.media_chutes && (
              <div className="card text-center">
                <p className="text-gray-600 text-sm">Chutes Médios</p>
                <p className="text-3xl font-bold text-brasil-green">
                  {stats.media_chutes.toFixed(1)}
                </p>
              </div>
            )}
            {stats.media_faltas && (
              <div className="card text-center">
                <p className="text-gray-600 text-sm">Faltas Médias</p>
                <p className="text-3xl font-bold text-brasil-green">
                  {stats.media_faltas.toFixed(1)}
                </p>
              </div>
            )}
          </div>

          {/* Dados Brutos */}
          <div className="card">
            <h3 className="font-bold text-lg mb-4">Dados Completos</h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <tbody>
                  {Object.entries(stats).map(([key, value]) => (
                    <tr key={key} className="border-b border-gray-200">
                      <td className="py-2 font-medium text-gray-600">{key.replace(/_/g, ' ')}</td>
                      <td className="py-2 text-right font-bold">
                        {typeof value === 'number' ? value.toFixed(2) : value}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
