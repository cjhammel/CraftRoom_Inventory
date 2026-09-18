import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import '../App.css'

export const AI_API_URL_KEY = 'craftroom.aiApiUrl'
export const AI_PROMPT_KEY = 'craftroom.aiPrompt'

const DEFAULT_AI_PROMPT = 'Analyze this stamp image and return a JSON object with these exact keys: product_name, brand_name, product_type, theme, shape_descriptor, sentiments. Use null for unknown fields. Return ONLY valid JSON, no markdown, no explanation.'

const emptyLocationForm = {
  cabinet: '',
  shelf: '',
  bin: '',
}

function formatLocation(location) {
  return [location.cabinet, location.shelf, location.bin].filter(Boolean).join(' / ')
}

function Settings() {
  const [activeTab, setActiveTab] = useState('locations')
  const [locations, setLocations] = useState([])
  const [locationForm, setLocationForm] = useState(emptyLocationForm)
  const [editingLocationId, setEditingLocationId] = useState(null)
  const [locationsLoading, setLocationsLoading] = useState(true)
  const [locationError, setLocationError] = useState(null)
  const [aiApiUrl, setAiApiUrl] = useState(() => localStorage.getItem(AI_API_URL_KEY) || '')
  const [aiPrompt, setAiPrompt] = useState(() => localStorage.getItem(AI_PROMPT_KEY) || '')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    fetchLocations()
  }, [])

  const fetchLocations = async () => {
    setLocationsLoading(true)
    setLocationError(null)

    try {
      const response = await fetch('/api/locations')
      if (!response.ok) throw new Error('Failed to load locations')
      setLocations(await response.json())
    } catch (err) {
      setLocationError(err.message)
    } finally {
      setLocationsLoading(false)
    }
  }

  const handleLocationChange = (e) => {
    const { name, value } = e.target
    setLocationForm((prev) => ({ ...prev, [name]: value }))
    setLocationError(null)
  }

  const resetLocationForm = () => {
    setLocationForm(emptyLocationForm)
    setEditingLocationId(null)
    setLocationError(null)
  }

  const handleLocationSubmit = async (e) => {
    e.preventDefault()

    const payload = {
      cabinet: locationForm.cabinet.trim() || null,
      shelf: locationForm.shelf.trim() || null,
      bin: locationForm.bin.trim() || null,
    }

    if (!payload.cabinet && !payload.shelf && !payload.bin) {
      setLocationError('Enter at least one location field.')
      return
    }

    try {
      const url = editingLocationId ? `/api/locations/${editingLocationId}` : '/api/locations'
      const response = await fetch(url, {
        method: editingLocationId ? 'PUT' : 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to save location')
      }

      await fetchLocations()
      resetLocationForm()
    } catch (err) {
      setLocationError(err.message)
    }
  }

  const handleEditLocation = (location) => {
    setEditingLocationId(location.id)
    setLocationForm({
      cabinet: location.cabinet || '',
      shelf: location.shelf || '',
      bin: location.bin || '',
    })
    setLocationError(null)
  }

  const handleAiSubmit = (e) => {
    e.preventDefault()

    const trimmedUrl = aiApiUrl.trim()
    const trimmedPrompt = aiPrompt.trim()

    if (trimmedUrl) localStorage.setItem(AI_API_URL_KEY, trimmedUrl)
    else localStorage.removeItem(AI_API_URL_KEY)

    if (trimmedPrompt) localStorage.setItem(AI_PROMPT_KEY, trimmedPrompt)
    else localStorage.removeItem(AI_PROMPT_KEY)

    setAiApiUrl(trimmedUrl)
    setAiPrompt(trimmedPrompt)
    setSaved(true)
  }

  const handleResetPrompt = () => {
    setAiPrompt(DEFAULT_AI_PROMPT)
    setSaved(false)
  }

  return (
    <div className="detail-view settings-view">
      <div className="detail-header">
        <div>
          <h1>Configuration</h1>
          <p className="settings-subtitle">Configure image analysis for this browser.</p>
        </div>
        <Link to="/" className="btn btn-secondary">Back</Link>
      </div>

      <div className="settings-tabs">
        <button
          type="button"
          className={`settings-tab ${activeTab === 'locations' ? 'active' : ''}`}
          onClick={() => setActiveTab('locations')}
        >
          Locations
        </button>
        <button
          type="button"
          className={`settings-tab ${activeTab === 'ai' ? 'active' : ''}`}
          onClick={() => setActiveTab('ai')}
        >
          AI Settings
        </button>
      </div>

      {activeTab === 'locations' && (
        <div className="settings-section">
          <h2>{editingLocationId ? 'Edit Location' : 'Create Location'}</h2>
          <form onSubmit={handleLocationSubmit}>
            <div className="form-row">
              <div className="form-group">
                <label>Cabinet</label>
                <input
                  type="text"
                  name="cabinet"
                  value={locationForm.cabinet}
                  onChange={handleLocationChange}
                  placeholder="e.g. Cabinet A"
                />
              </div>
              <div className="form-group">
                <label>Shelf</label>
                <input
                  type="text"
                  name="shelf"
                  value={locationForm.shelf}
                  onChange={handleLocationChange}
                  placeholder="e.g. Shelf 2"
                />
              </div>
              <div className="form-group">
                <label>Bin</label>
                <input
                  type="text"
                  name="bin"
                  value={locationForm.bin}
                  onChange={handleLocationChange}
                  placeholder="e.g. Bin 4"
                />
              </div>
            </div>
            {locationError && <div className="error settings-error">{locationError}</div>}
            <div className="settings-actions">
              <button type="submit" className="btn btn-primary">
                {editingLocationId ? 'Update Location' : 'Create Location'}
              </button>
              {editingLocationId && (
                <button type="button" className="btn btn-secondary" onClick={resetLocationForm}>
                  Cancel Edit
                </button>
              )}
            </div>
          </form>

          <div className="locations-list">
            <h3>Saved Locations</h3>
            {locationsLoading ? (
              <div className="loading">Loading locations...</div>
            ) : locations.length === 0 ? (
              <p>No locations yet. Create one above to make it available when adding stamps.</p>
            ) : (
              locations.map((location) => (
                <div className="location-row" key={location.id}>
                  <div>
                    <strong>{formatLocation(location)}</strong>
                    <span>Location #{location.id}</span>
                  </div>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => handleEditLocation(location)}
                  >
                    Edit
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === 'ai' && (
        <form onSubmit={handleAiSubmit}>
          <div className="settings-section">
            <h2>Local AI Instance</h2>
            <p>
              Use your local Ollama or OpenAI-compatible server. Leave blank to use the backend `.env` setting.
            </p>
            <div className="form-group">
              <label>AI Server URL</label>
              <input
                type="url"
                value={aiApiUrl}
                onChange={(e) => {
                  setAiApiUrl(e.target.value)
                  setSaved(false)
                }}
                placeholder="http://localhost:11434"
              />
            </div>
          </div>

          <div className="settings-section">
            <h2>Custom AI Prompt</h2>
            <p>Leave blank to use the backend default prompt.</p>
            <div className="form-group">
              <label>Prompt</label>
              <textarea
                value={aiPrompt}
                onChange={(e) => {
                  setAiPrompt(e.target.value)
                  setSaved(false)
                }}
                rows="8"
                placeholder={DEFAULT_AI_PROMPT}
              />
            </div>
            <button type="button" className="btn btn-secondary" onClick={handleResetPrompt}>
              Use Suggested Prompt
            </button>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary">Save Settings</button>
            <Link to="/" className="btn btn-secondary">Cancel</Link>
          </div>
          {saved && <div className="settings-saved">Settings saved.</div>}
        </form>
      )}
    </div>
  )
}

export default Settings
