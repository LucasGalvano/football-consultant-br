import { useParams } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getClassificacao, getAnosDisponiveis } from '../services/api'
import { Loading, ErrorAlert, EmptyState } from '../components/Common'
import { useState } from 'react'
import { Link } from 'react-router-dom'

export default function Classificacao() {
  const { ano } = useParams()
  const [selectedAno, setSelectedAno] = useState(parseInt(ano) || 2023)

  const { data: anosData } = useApi(getAnosDisponiveis)
  const { data: classificacao, loading, error } = useApi(
    () => getClassificacao(selectedAno),
    [selectedAno]
  )

  const anos = anosData?.anos || []

  if (loading) return <Loading />
  if (error) return <ErrorAlert message={error} />

  return (
    <div className="space-y-6">
      <div className="brasil-gradient text-white rounded-xl p-8">
        <h1 className="text-4xl font-bold mb-4">🏆 Tabela de Classificação</h1>

        {/* Seletor de Ano */}
        <div className="flex flex-wrap gap-2">
          {anos.map(a => (
            <button
              key={a}
              onClick={() => setSelectedAno(a)}
              className={`px-4 py-2 rounded-lg font-bold transition ${
                selectedAno === a
                  ? 'bg-brasil-yellow text-brasil-green'
                  : 'bg-white/20 text-white hover:bg-white/30'
              }`}
            >
              {a}
            </button>
          ))}
        </div>
      </div>

      {/* Tabela */}
      {classificacao && classificacao.length > 0 ? (
        <div className="card overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-brasil-green">
                <th className="px-4 py-3 text-left font-bold text-brasil-dark">#</th>
                <th className="px-4 py-3 text-left font-bold text-brasil-dark">Clube</th>
                <th className="px-4 py-3 text-center font-bold text-brasil-dark">PG</th>
                <th className="px-4 py-3 text-center font-bold text-brasil-dark">V</th>
                <th className="px-4 py-3 text-center font-bold text-brasil-dark">E</th>
                <th className="px-4 py-3 text-center font-bold text-brasil-dark">D</th>
                <th className="px-4 py-3 text-center font-bold text-brasil-dark">GP</th>
                <th className="px-4 py-3 text-center font-bold text-brasil-dark">GC</th>
                <th className="px-4 py-3 text-center font-bold text-brasil-dark">SG</th>
              </tr>
            </thead>
            <tbody>
              {classificacao.map((time, idx) => (
                <tr
                  key={time.clube_id}
                  className={`border-b border-gray-200 ${
                    idx < 4 ? 'bg-green-50' : idx < 6 ? 'bg-blue-50' : idx < 18 ? 'bg-white' : 'bg-red-50'
                  }`}
                >
                  <td className="px-4 py-3 font-bold text-brasil-dark">{idx + 1}</td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/clubes/${time.clube_id}`}
                      className="font-bold text-brasil-green hover:underline"
                    >
                      {time.nome_clube}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-center font-bold text-2xl text-brasil-dark">
                    {time.pontos_ganhos}
                  </td>
                  <td className="px-4 py-3 text-center text-green-600 font-bold">{time.vitorias}</td>
                  <td className="px-4 py-3 text-center text-gray-600 font-bold">{time.empates}</td>
                  <td className="px-4 py-3 text-center text-red-600 font-bold">{time.derrotas}</td>
                  <td className="px-4 py-3 text-center font-bold">{time.gols_marcados}</td>
                  <td className="px-4 py-3 text-center font-bold">{time.gols_sofridos}</td>
                  <td className="px-4 py-3 text-center font-bold">
                    {time.gols_marcados - time.gols_sofridos > 0 ? '+' : ''}
                    {time.gols_marcados - time.gols_sofridos}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState message="Nenhuma classificação encontrada" />
      )}

      {/* Legenda */}
      <div className="card">
        <h3 className="font-bold mb-3">📋 Legenda</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-100 border border-green-500 rounded"></div>
            <span>Libertadores (1-4)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-100 border border-blue-500 rounded"></div>
            <span>Pré-Libertadores (5-6)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-white border border-gray-300 rounded"></div>
            <span>Outros (7-17)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-100 border border-red-500 rounded"></div>
            <span>Rebaixamento (18-20)</span>
          </div>
        </div>
      </div>
    </div>
  )
}
