import { useState, useEffect } from 'react'
import { getArtilheiros, getAnosDisponiveis, getRankingCartoes } from '../services/api'
import { Loading, ErrorAlert, EmptyState } from '../components/Common'
import { useApi } from '../hooks/useApi'

export default function Artilheiros() {
  const [ano, setAno] = useState(null)
  const [limite, setLimite] = useState(10)
  const [tipoCartao, setTipoCartao] = useState(null)

  const [artilheiros, setArtilheiros] = useState(null)
  const [loadingArtilheiros, setLoadingArtilheiros] = useState(true)
  const [errorArtilheiros, setErrorArtilheiros] = useState(null)

  const [cartoes, setCartoes] = useState(null)
  const [loadingCartoes, setLoadingCartoes] = useState(true)
  const [errorCartoes, setErrorCartoes] = useState(null)

  const { data: anosData } = useApi(getAnosDisponiveis)
  const anos = anosData?.anos || []

  // Busca artilheiros sempre que ano ou limite mudar
  useEffect(() => {
    let mounted = true
    setLoadingArtilheiros(true)
    setErrorArtilheiros(null)

    getArtilheiros({ ano, limite })
      .then(res => { if (mounted) setArtilheiros(res.data) })
      .catch(err => { if (mounted) setErrorArtilheiros(err.response?.data?.detail || err.message) })
      .finally(() => { if (mounted) setLoadingArtilheiros(false) })

    return () => { mounted = false }
  }, [ano, limite])

  // Busca cartões sempre que ano, limite ou tipoCartao mudar
  useEffect(() => {
    let mounted = true
    setLoadingCartoes(true)
    setErrorCartoes(null)

    getRankingCartoes({ ano, limite, tipo: tipoCartao })
      .then(res => { if (mounted) setCartoes(res.data) })
      .catch(err => { if (mounted) setErrorCartoes(err.response?.data?.detail || err.message) })
      .finally(() => { if (mounted) setLoadingCartoes(false) })

    return () => { mounted = false }
  }, [ano, limite, tipoCartao])

  return (
    <div className="space-y-8">
      <div className="brasil-gradient text-white rounded-xl p-8">
        <h1 className="text-4xl font-bold mb-2">🔥 Ranking de Artilheiros & Cartões</h1>
        <p className="text-gray-100">Veja os maiores goleadores e jogadores mais polêmicos do campeonato</p>
      </div>

      {/* Filtros */}
      <div className="card">
        <h3 className="font-bold text-lg mb-4">🔍 Filtros</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-2">Ano (opcional)</label>
            <select
              value={ano || ''}
              onChange={(e) => setAno(e.target.value ? parseInt(e.target.value) : null)}
              className="input-field"
            >
              <option value="">Todos os anos</option>
              {anos.map(a => (
                <option key={a} value={a}>{a}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Limite</label>
            <select
              value={limite}
              onChange={(e) => setLimite(parseInt(e.target.value))}
              className="input-field"
            >
              <option value={5}>Top 5</option>
              <option value={10}>Top 10</option>
              <option value={20}>Top 20</option>
              <option value={50}>Top 50</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Tipo de Cartão</label>
            <select
              value={tipoCartao || ''}
              onChange={(e) => setTipoCartao(e.target.value || null)}
              className="input-field"
            >
              <option value="">Ambos</option>
              <option value="Amarelo">Amarelo</option>
              <option value="Vermelho">Vermelho</option>
            </select>
          </div>
        </div>
      </div>

      {/* Artilheiros */}
      {loadingArtilheiros ? (
        <Loading />
      ) : errorArtilheiros ? (
        <ErrorAlert message={errorArtilheiros} />
      ) : artilheiros && artilheiros.length > 0 ? (
        <div className="card">
          <h3 className="font-bold text-2xl mb-6 flex items-center gap-2">
            ⚽ Artilheiros {ano ? ano : '(All Time)'}
            <span className="text-sm bg-brasil-yellow text-brasil-green px-2 py-1 rounded">
              {artilheiros.length} jogadores
            </span>
          </h3>
          <div className="space-y-3">
            {artilheiros.map((jogador, idx) => (
              <div key={idx} className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-white rounded-lg border-l-4 border-brasil-yellow">
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-bold text-brasil-green">{idx + 1}</span>
                  <div>
                    <p className="font-bold text-lg text-brasil-dark">{jogador.atleta}</p>
                    {jogador.clube && (
                      <p className="text-sm text-gray-600">{jogador.clube}</p>
                    )}
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-brasil-yellow">{jogador.total_gols ?? 0}</p>
                  <p className="text-xs text-gray-600">gols</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState message="Nenhum artilheiro encontrado" />
      )}

      {/* Ranking de Cartões */}
      {loadingCartoes ? (
        <Loading />
      ) : errorCartoes ? (
        <ErrorAlert message={errorCartoes} />
      ) : cartoes && cartoes.length > 0 ? (
        <div className="card">
          <h3 className="font-bold text-2xl mb-6 flex items-center gap-2">
            🟥 Ranking de Cartões {ano ? ano : '(All Time)'}
            <span className="text-sm bg-yellow-400 text-brasil-dark px-2 py-1 rounded">
              {cartoes.length} jogadores
            </span>
          </h3>
          <div className="space-y-3">
            {cartoes.map((jogador, idx) => (
              <div key={idx} className="flex items-center justify-between p-4 bg-gradient-to-r from-yellow-50 to-white rounded-lg border-l-4 border-red-500">
                <div className="flex items-center gap-4">
                  <span className="text-2xl font-bold text-gray-700">{idx + 1}</span>
                  <div>
                    <p className="font-bold text-lg text-brasil-dark">{jogador.atleta}</p>
                    {jogador.clube && (
                      <p className="text-sm text-gray-600">{jogador.clube}</p>
                    )}
                  </div>
                </div>
                <div className="flex gap-2">
                  {jogador.amarelos > 0 && (
                    <div className="bg-yellow-400 text-black px-3 py-1 rounded font-bold">
                      {jogador.amarelos} 🟨
                    </div>
                  )}
                  {jogador.vermelhos > 0 && (
                    <div className="bg-red-600 text-white px-3 py-1 rounded font-bold">
                      {jogador.vermelhos} 🟥
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <EmptyState message="Nenhum cartão encontrado com esses filtros" />
      )}
    </div>
  )
}