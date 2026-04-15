import { useApi } from '../hooks/useApi'
import { getClubes, getAnosDisponiveis } from '../services/api'
import { Loading, ErrorAlert, EmptyState } from '../components/Common'
import { Link } from 'react-router-dom'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'

export default function Home() {
  const { data: clubes, loading: loadingClubes } = useApi(getClubes)
  const { data: anosData, loading: loadingAnos } = useApi(getAnosDisponiveis)

  if (loadingClubes || loadingAnos) return <Loading />

  const anos = anosData?.anos || []

  const statsData = [
    { name: 'Total Clubes', value: clubes?.length || 0 },
    { name: 'Anos Analisados', value: anos.length },
    { name: 'Rodadas/Ano', value: 38 },
  ]

  const chartData = anos.map(ano => ({
    ano: ano.toString(),
    value: 1,
  }))

  const COLORS = ['#1e3a1f', '#ffd700', '#0d1b0e']

  return (
    <div className="space-y-8">
      {/* Hero */}
      <section className="brasil-gradient text-white rounded-xl p-8 md:p-12 shadow-lg">
        <h1 className="text-4xl md:text-5xl font-bold mb-4">
          ⚽ Consultor do Futebol Brasileiro
        </h1>
        <p className="text-lg mb-6 text-gray-100">
          Análise completa e em tempo real do Campeonato Brasileiro. Explore dados de clubes, partidas, estatísticas e confrontos diretos.
        </p>
        <div className="flex flex-wrap gap-4">
          <Link to="/clubes" className="btn-primary">
            🏆 Explorar Clubes
          </Link>
          <Link to="/partidas" className="btn-secondary">
            📅 Ver Partidas
          </Link>
          <Link to="/artilheiros" className="btn-secondary">
            🔥 Top Artilheiros
          </Link>
        </div>
      </section>

      {/* Estatísticas Gerais */}
      <section>
        <h2 className="text-3xl font-bold mb-6 text-brasil-dark">📊 Estatísticas Gerais</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {statsData.map((stat, idx) => (
            <div key={idx} className="card text-center">
              <p className="text-gray-600 text-sm font-medium">{stat.name}</p>
              <p className="text-4xl font-bold text-brasil-green">{stat.value}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Anos Disponíveis */}
      <section>
        <h2 className="text-3xl font-bold mb-6 text-brasil-dark">📅 Anos Disponíveis</h2>
        <div className="card">
          {anos && anos.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {anos.map(ano => (
                <Link
                  key={ano}
                  to={`/classificacao/${ano}`}
                  className="p-4 bg-gradient-to-br from-brasil-green to-brasil-dark text-white rounded-lg hover:shadow-lg transform hover:scale-105 transition text-center font-bold"
                >
                  {ano}
                </Link>
              ))}
            </div>
          ) : (
            <EmptyState message="Nenhum ano disponível" />
          )}
        </div>
      </section>

      {/* Atalhos Rápidos */}
      <section>
        <h2 className="text-3xl font-bold mb-6 text-brasil-dark">🚀 Atalhos Rápidos</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Link to="/estadios" className="card hover:shadow-lg hover:border-brasil-green border-2 border-transparent">
            <h3 className="font-bold text-xl mb-2">🏟️ Estádios</h3>
            <p className="text-gray-600">Conheça todos os estádios que sediam partidas do Brasileirão.</p>
          </Link>
          <Link to="/confronto" className="card hover:shadow-lg hover:border-brasil-yellow border-2 border-transparent">
            <h3 className="font-bold text-xl mb-2">⚔️ Confronto Direto</h3>
            <p className="text-gray-600">Compare históricos e estatísticas entre dois clubes.</p>
          </Link>
        </div>
      </section>
    </div>
  )
}
