import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Home from './pages/Home'
import Clubes from './pages/Clubes'
import ClubeDetail from './pages/ClubeDetail'
import Partidas from './pages/Partidas'
import PartidaDetail from './pages/PartidaDetail'
import Estadios from './pages/Estadios'
import Classificacao from './pages/Classificacao'
import Artilheiros from './pages/Artilheiros'
import Confronto from './pages/Confronto'

export default function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/clubes" element={<Clubes />} />
          <Route path="/clubes/:id" element={<ClubeDetail />} />
          <Route path="/partidas" element={<Partidas />} />
          <Route path="/partidas/:id" element={<PartidaDetail />} />
          <Route path="/estadios" element={<Estadios />} />
          <Route path="/classificacao/:ano" element={<Classificacao />} />
          <Route path="/artilheiros" element={<Artilheiros />} />
          <Route path="/confronto" element={<Confronto />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}
