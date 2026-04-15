export default function Footer() {
  return (
    <footer className="brasil-gradient text-white mt-12 py-8">
      <div className="max-w-7xl mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="font-bold text-lg mb-2">📊 Sobre</h3>
            <p className="text-sm text-gray-300">
              Análise completa do Campeonato Brasileiro (2014-2023) com dados de PostgreSQL, MongoDB e Cassandra.
            </p>
          </div>
          <div>
            <h3 className="font-bold text-lg mb-2">🔗 APIs</h3>
            <ul className="text-sm text-gray-300 space-y-1">
              <li><a href="/docs" className="hover:text-brasil-yellow">Swagger UI</a></li>
              <li><a href="/redoc" className="hover:text-brasil-yellow">ReDoc</a></li>
            </ul>
          </div>
          <div>
            <h3 className="font-bold text-lg mb-2">⚽ Dados</h3>
            <p className="text-sm text-gray-300">
              Resultado de jogos do Brasileirão com estatísticas táticas e eventos de gols/cartões.
            </p>
          </div>
        </div>
        <div className="border-t border-white/20 mt-6 pt-6 text-center text-sm text-gray-300">
          <p>© 2024 Consultor do Futebol Brasileiro • Desenvolvido com ⚽ e ❤️</p>
        </div>
      </div>
    </footer>
  )
}
