import { Link, useLocation } from 'react-router-dom'
import { useState } from 'react'

export default function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const location = useLocation()

  const isActive = (path) => location.pathname === path

  const navItems = [
    { label: 'Início', path: '/' },
    { label: 'Clubes', path: '/clubes' },
    { label: 'Partidas', path: '/partidas' },
    { label: 'Estádios', path: '/estadios' },
    { label: 'Classificação', path: '/classificacao/2023' },
    { label: 'Artilheiros', path: '/artilheiros' },
    { label: 'Confronto', path: '/confronto' },
  ]

  return (
    <header className="brasil-gradient text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-2xl font-bold hover:text-brasil-yellow">
            ⚽ Consultor do Futebol
          </Link>

          {/* Menu desktop */}
          <nav className="hidden md:flex gap-1">
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-4 py-2 rounded-lg transition-colors ${
                  isActive(item.path)
                    ? 'bg-brasil-yellow text-brasil-green font-bold'
                    : 'hover:bg-brasil-yellow/20'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>

          {/* Menu mobile */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden text-brasil-yellow text-2xl"
          >
            ☰
          </button>
        </div>

        {/* Mobile menu dropdown */}
        {isMenuOpen && (
          <nav className="md:hidden mt-4 space-y-2">
            {navItems.map(item => (
              <Link
                key={item.path}
                to={item.path}
                onClick={() => setIsMenuOpen(false)}
                className={`block px-4 py-2 rounded-lg transition-colors ${
                  isActive(item.path)
                    ? 'bg-brasil-yellow text-brasil-green font-bold'
                    : 'hover:bg-brasil-yellow/20'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        )}
      </div>
    </header>
  )
}
