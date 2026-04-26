import { useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getPartidaById } from '../services/api'
import { Loading, ErrorAlert, EmptyState } from '../components/Common'

export default function PartidaDetail() {
  const { id } = useParams()
  const { data: partida, loading, error } = useApi(() => getPartidaById(id))

  if (loading) return <Loading />
  if (error) return <ErrorAlert message={error} />
  if (!partida) return <EmptyState message="Partida não encontrada" />

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="brasil-gradient text-white rounded-xl p-8">
        <div className="text-sm text-gray-200 mb-4">
          Rodada {partida.rodada} •{' '}
          {new Date(partida.data).toLocaleDateString('pt-BR', {
            weekday: 'long',
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
          {partida.hora && ` às ${partida.hora}`}
        </div>

        <div className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-8">
          <div className="text-right">
            <h2 className="text-3xl font-bold">{partida.mandante}</h2>
            <p className="text-gray-200 text-sm">(Mandante)</p>
          </div>

          <div className="text-center">
            <div className="bg-brasil-yellow text-brasil-green px-6 py-3 rounded-lg">
              <p className="text-4xl font-bold">
                {partida.placar_mandante}×{partida.placar_visitante}
              </p>
            </div>
            {partida.vencedor && (
              <p className="text-sm text-brasil-yellow mt-2 font-bold">
                ✓ {partida.vencedor} venceu
              </p>
            )}
          </div>

          <div>
            <h2 className="text-3xl font-bold">{partida.visitante}</h2>
            <p className="text-gray-200 text-sm">(Visitante)</p>
          </div>
        </div>
      </div>

      {/* Informações da Partida */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card">
          <h3 className="font-bold mb-3">🏟️ Local</h3>
          <p className="text-lg">{partida.estadio}</p>
        </div>

        <div className="card">
          <h3 className="font-bold mb-3">⚽ Formações</h3>
          <p><span className="text-gray-600">{partida.mandante}:</span> {partida.formacao_mandante || 'N/A'}</p>
          <p><span className="text-gray-600">{partida.visitante}:</span> {partida.formacao_visitante || 'N/A'}</p>
        </div>

        <div className="card">
          <h3 className="font-bold mb-3">👨‍🏫 Técnicos</h3>
          <p><span className="text-gray-600">{partida.mandante}:</span> {partida.tecnico_mandante || 'N/A'}</p>
          <p><span className="text-gray-600">{partida.visitante}:</span> {partida.tecnico_visitante || 'N/A'}</p>
        </div>
      </div>

      {/* Gols — API retorna: atleta, clube, minuto, tipo_gol */}
      {partida.gols && partida.gols.length > 0 && (
        <div className="card">
          <h3 className="font-bold text-lg mb-4">⚽ Gols</h3>
          <div className="space-y-2">
            {partida.gols.map((gol, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                  <span className="font-medium">{gol.atleta}</span>
                  {gol.clube && (
                    <span className="text-sm text-gray-500 ml-2">({gol.clube})</span>
                  )}
                  {gol.tipo_gol && gol.tipo_gol !== 'Normal' && (
                    <span className="text-xs bg-gray-200 text-gray-700 px-2 py-0.5 rounded ml-2">
                      {gol.tipo_gol}
                    </span>
                  )}
                </div>
                <span className="text-sm text-gray-600 font-bold">{gol.minuto}'</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cartões — API retorna: atleta, clube, tipo_cartao, minuto */}
      {partida.cartoes && partida.cartoes.length > 0 && (
        <div className="card">
          <h3 className="font-bold text-lg mb-4">🟨 Cartões</h3>
          <div className="space-y-2">
            {partida.cartoes.map((cartao, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div>
                  <span className="font-medium">{cartao.atleta}</span>
                  {cartao.clube && (
                    <span className="text-sm text-gray-500 ml-2">({cartao.clube})</span>
                  )}
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">{cartao.minuto}'</span>
                  <span
                    className={`px-2 py-1 rounded text-white text-sm font-bold ${
                      cartao.tipo_cartao === 'Vermelho' ? 'bg-red-600' : 'bg-yellow-500'
                    }`}
                  >
                    {cartao.tipo_cartao}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Estatísticas (MongoDB) */}
      {partida.estatisticas && (
        <div className="card">
          <h3 className="font-bold text-lg mb-4">📊 Estatísticas Táticas</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {['mandante', 'visitante'].map(lado => {
              const dados = partida.estatisticas[lado]
              if (!dados) return null
              return (
                <div key={lado}>
                  <h4 className="font-bold text-brasil-green mb-3">
                    {dados.nome} ({lado === 'mandante' ? 'Mandante' : 'Visitante'})
                  </h4>
                  <table className="w-full text-sm">
                    <tbody>
                      {Object.entries(dados.estatisticas || {}).map(([key, value]) => (
                        <tr key={key} className="border-b border-gray-100">
                          <td className="py-1 text-gray-600 capitalize">{key.replace(/_/g, ' ')}</td>
                          <td className="py-1 text-right font-bold">{value}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}