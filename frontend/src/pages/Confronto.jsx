import { useApi } from '../hooks/useApi'
import { getClubes, getConfrontoDireto } from '../services/api'
import { Loading, ErrorAlert, EmptyState } from '../components/Common'
import { useState } from 'react'

export default function Confronto() {
  const [clube1Id, setClube1Id] = useState(null)
  const [clube2Id, setClube2Id] = useState(null)
  const [comparacao, setComparacao] = useState(null)

  const { data: clubes, loading: loadingClubes } = useApi(getClubes)

  const handleComparar = async () => {
    if (!clube1Id || !clube2Id || clube1Id === clube2Id) {
      alert('Selecione dois clubes diferentes')
      return
    }

    try {
      const response = await getConfrontoDireto(clube1Id, clube2Id)
      setComparacao(response.data)
    } catch (err) {
      alert('Erro ao carregar confronto: ' + (err.response?.data?.detail || err.message))
    }
  }

  const club1 = clubes?.find(c => c.id === clube1Id)
  const club2 = clubes?.find(c => c.id === clube2Id)

  if (loadingClubes) return <Loading />

  return (
    <div className="space-y-8">
      <div className="brasil-gradient text-white rounded-xl p-8">
        <h1 className="text-4xl font-bold mb-2">⚔️ Confronto Direto</h1>
        <p className="text-gray-100">Compare o histórico e estatísticas entre dois clubes</p>
      </div>

      {/* Seletor de Clubes */}
      <div className="card">
        <h3 className="font-bold text-lg mb-6">Selecione dois clubes para comparar</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium mb-2">Primeiro Clube</label>
            <select
              value={clube1Id || ''}
              onChange={(e) => setClube1Id(e.target.value ? parseInt(e.target.value) : null)}
              className="input-field"
            >
              <option value="">Selecionar...</option>
              {clubes?.map(c => (
                <option key={c.id} value={c.id}>
                  {c.nome_oficial} ({c.sigla})
                </option>
              ))}
            </select>
          </div>

          <div className="text-center">
            <span className="text-2xl font-bold text-brasil-yellow">VS</span>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2">Segundo Clube</label>
            <select
              value={clube2Id || ''}
              onChange={(e) => setClube2Id(e.target.value ? parseInt(e.target.value) : null)}
              className="input-field"
            >
              <option value="">Selecionar...</option>
              {clubes?.map(c => (
                <option key={c.id} value={c.id}>
                  {c.nome_oficial} ({c.sigla})
                </option>
              ))}
            </select>
          </div>
        </div>

        <button
          onClick={handleComparar}
          disabled={!clube1Id || !clube2Id || clube1Id === clube2Id}
          className="btn-primary mt-6 w-full md:w-auto"
        >
          🔍 Comparar
        </button>
      </div>

      {/* Resultado da Comparação */}
      {comparacao && (
        <div className="space-y-6">
          {/* Stats Gerais */}
          <div className="card">
            <h3 className="font-bold text-2xl mb-6 text-center">
              {club1?.nome_oficial} vs {club2?.nome_oficial}
            </h3>

            <div className="grid grid-cols-3 gap-4 text-center mb-6">
              <div>
                <p className="font-bold text-xl text-brasil-green">
                  {comparacao[`vitorias_${club1?.sigla}`] || 0}
                </p>
                <p className="text-sm text-gray-600">Vitórias {club1?.sigla}</p>
              </div>
              <div>
                <p className="font-bold text-xl text-gray-600">
                  {comparacao.empates}
                </p>
                <p className="text-sm text-gray-600">Empates</p>
              </div>
              <div>
                <p className="font-bold text-xl text-red-600">
                  {comparacao[`vitorias_${club2?.sigla}`] || 0}
                </p>
                <p className="text-sm text-gray-600">Vitórias {club2?.sigla}</p>
              </div>
            </div>

            <p className="text-center text-sm text-gray-600 border-t pt-4">
              Total de jogos: <span className="font-bold">{comparacao.total_jogos}</span>
            </p>
          </div>

          {/* Histórico Recente */}
          {comparacao.historico_recente && comparacao.historico_recente.length > 0 && (
            <div className="card">
              <h3 className="font-bold text-lg mb-4">📅 Últimos Confrontos</h3>
              <div className="space-y-3">
                {comparacao.historico_recente.map((partida, idx) => (
                  <div key={idx} className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-xs text-gray-500 mb-2">
                      {new Date(partida.data).toLocaleDateString('pt-BR')}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="font-bold">{partida.mandante}</span>
                      <span className="bg-brasil-yellow text-brasil-green px-3 py-1 rounded font-bold">
                        {partida.placar}
                      </span>
                      <span className="font-bold">{partida.visitante}</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">📍 {partida.estadio}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Estatísticas Detalhadas */}
          {comparacao.estatisticas_detalhadas && comparacao.estatisticas_detalhadas.length > 0 && (
            <div className="card">
              <h3 className="font-bold text-lg mb-4">📊 Estatísticas Detalhadas</h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <tbody>
                    {comparacao.estatisticas_detalhadas.map((stat, idx) => (
                      <tr key={idx} className="border-b border-gray-200">
                        <td className="py-2 font-medium text-gray-600">
                          {typeof stat === 'object' ? Object.keys(stat)[0] : stat}
                        </td>
                        <td className="py-2 text-right">
                          {typeof stat === 'object' ? Object.values(stat)[0] : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
