import { Routes, Route, Link } from 'react-router-dom'
import StampsList from './pages/StampsList'
import StampDetail from './pages/StampDetail'
import StampForm from './pages/StampForm'
import Settings from './pages/Settings'

function App() {
  return (
    <div className="app">
      <header className="app-header">
        <div className="container">
          <Link to="/" className="app-title">
            CraftRoom Product Inventory
          </Link>
          <nav className="header-actions">
            <Link to="/settings" className="btn btn-secondary">
              Configuration
            </Link>
            <Link to="/new" className="btn btn-primary">
              + Add Stamp
            </Link>
          </nav>
        </div>
      </header>
      <main className="container">
        <Routes>
          <Route path="/" element={<StampsList />} />
          <Route path="/new" element={<StampForm />} />
          <Route path="/edit/:id" element={<StampForm />} />
          <Route path="/stamps/:id" element={<StampDetail />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  )
}

export default App
