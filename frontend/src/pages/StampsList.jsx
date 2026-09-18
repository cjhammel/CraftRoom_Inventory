import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import '../App.css'

function StampsList() {
  const [stamps, setStamps] = useState([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [brand, setBrand] = useState('')
  const [productType, setProductType] = useState('')
  const [theme, setTheme] = useState('')
  const [location, setLocation] = useState('')
  const [sentiments, setSentiments] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchStamps()
  }, [])

  const fetchStamps = async (filters = { search, brand, productType, theme, location, sentiments }) => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams()
      if (filters.search) params.set('q', filters.search)
      if (filters.brand) params.set('brand_name', filters.brand)
      if (filters.productType) params.set('product_type', filters.productType)
      if (filters.theme) params.set('theme', filters.theme)
      if (filters.location) params.set('location', filters.location)
      if (filters.sentiments) params.set('sentiments', filters.sentiments)

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

  const handleClear = () => {
    const emptyFilters = {
      search: '',
      brand: '',
      productType: '',
      theme: '',
      location: '',
      sentiments: '',
    }

    setSearch(emptyFilters.search)
    setBrand(emptyFilters.brand)
    setProductType(emptyFilters.productType)
    setTheme(emptyFilters.theme)
    setLocation(emptyFilters.location)
    setSentiments(emptyFilters.sentiments)
    fetchStamps(emptyFilters)
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
          placeholder="Search by item, name, or brand..."
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
          placeholder="Filter by product type..."
          value={productType}
          onChange={(e) => setProductType(e.target.value)}
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
          onClick={handleClear}
        >
          Clear
        </button>
      </form>

      {stamps.length === 0 ? (
        <div className="empty-state">
          <h2>No stamps found</h2>
          <p>
            {search || brand || productType || theme || location || sentiments
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
                  src={stamp.image_url}
                  alt={stamp.product_name}
                  className="stamp-card-image"
                />
              )}
              <div className="stamp-card-body">
                <div className="stamp-card-name">{stamp.product_name}</div>
                {stamp.item_number && (
                  <div className="stamp-card-brand">Item #{stamp.item_number}</div>
                )}
                {stamp.brand_name && (
                  <div className="stamp-card-brand">{stamp.brand_name}</div>
                )}
                <dl className="stamp-card-details">
                  {stamp.product_type && (
                    <div><dt>Type</dt><dd>{stamp.product_type}</dd></div>
                  )}
                  {stamp.theme && (
                    <div><dt>Theme</dt><dd>{stamp.theme}</dd></div>
                  )}
                  {stamp.shape_descriptor && (
                    <div><dt>Shape</dt><dd>{stamp.shape_descriptor}</dd></div>
                  )}
                  {stamp.sentiments && (
                    <div><dt>Sentiments</dt><dd>{stamp.sentiments}</dd></div>
                  )}
                  {stamp.location && (
                    <div><dt>Location</dt><dd>{stamp.location}</dd></div>
                  )}
                </dl>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}

export default StampsList
