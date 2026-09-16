import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import '../App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function StampsList() {
  const [stamps, setStamps] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [brand, setBrand] = useState('')
  const [theme, setTheme] = useState('')
  const [location, setLocation] = useState('')
  const [sentiments, setSentiments] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchStamps()
  }, [])

  const fetchStamps = async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (search) params.set('q', search)
      if (brand) params.set('brand_name', brand)
      if (theme) params.set('theme', theme)
      if (location) params.set('location', location)
      if (sentiments) params.set('sentiments', sentiments)

      const url = `/api/stamps${params.toString() ? '?' + params.toString() : ''}`
      const response = await fetch(url)
      if (!response.ok) throw new Error('Failed to fetch stamps')
      const data = await response.json()
      setStamps(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (e) => {
    e.preventDefault()
    fetchStamps()
  }

  if (loading) {
    return <div className="loading">Loading stamps...</div>
  }

  if (error) {
    return <div className="empty-state"><p>Error: {error}</p></div>
  }

  return (
    <div>
      <h1>My Stamp Collection</h1>

      <form className="search-bar" onSubmit={handleSearch}>
        <input
          type="text"
          placeholder="Search by name or brand..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <input
          type="text"
          placeholder="Filter by brand..."
          value={brand}
          onChange={(e) => setBrand(e.target.value)}
        />
        <input
          type="text"
          placeholder="Filter by theme..."
          value={theme}
          onChange={(e) => setTheme(e.target.value)}
        />
        <input
          type="text"
          placeholder="Filter by location..."
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <input
          type="text"
          placeholder="Filter by sentiments..."
          value={sentiments}
          onChange={(e) => setSentiments(e.target.value)}
        />
        <button type="submit" className="btn btn-primary">
          Search
        </button>
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => {
            setSearch('')
            setBrand('')
            setTheme('')
            setLocation('')
            setSentiments('')
          }}
        >
          Clear
        </button>
      </form>

      {stamps.length === 0 ? (
        <div className="empty-state">
          <h2>No stamps found</h2>
          <p>
            {search || brand || theme || location || sentiments
              ? 'Try adjusting your filters'
              : 'Add your first stamp to get started!'}
          </p>
        </div>
      ) : (
        <div className="stamps-grid">
          {stamps.map((stamp) => (
            <Link to={`/stamps/${stamp.id}`} key={stamp.id} className="stamp-card">
              {stamp.image_url && (
                <img
                  src={`${API_URL}${stamp.image_url}`}
                  alt={stamp.product_name}
                  className="stamp-card-image"
                />
              )}
              <div className="stamp-card-body">
                <div className="stamp-card-name">{stamp.product_name}</div>
                {stamp.brand_name && (
                  <div className="stamp-card-brand">{stamp.brand_name}</div>
                )}
                <div className="stamp-card-meta">
                  {stamp.price && (
                    <span className="stamp-card-price">
                      ${Number(stamp.price).toFixed(2)}
                    </span>
                  )}
                  {stamp.retired && (
                    <span className="stamp-retired-badge">Retired</span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export default StampsList
