import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import '../App.css'

export const AI_API_URL_KEY = 'craftroom_ai_api_url'
export const AI_PROMPT_KEY = 'craftroom_ai_prompt'

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
  
  // Config state from backend
  const [config, setConfig] = useState(null)
  const [configLoading, setConfigLoading] = useState(true)
  const [configSaved, setConfigSaved] = useState(false)
  
  // AI config form
  const [aiApiUrl, setAiApiUrl] = useState('')
  const [aiModel, setAiModel] = useState('qwen3.6:35B')
  const [aiPrompt, setAiPrompt] = useState('')

  useEffect(() => {
    fetchLocations()
    fetchConfig()
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

  const fetchConfig = async () => {
    setConfigLoading(true)
    try {
      const response = await fetch('/api/config')
      if (!response.ok) throw new Error('Failed to load configuration')
      const data = await response.json()
      setConfig(data)
      setAiApiUrl(data.ai?.api_url || '')
      setAiModel(data.ai?.model || 'qwen3.6:35B')
      setAiPrompt(data.ai?.prompt || '')
    } catch (err) {
      console.error('Error loading config:', err)
    } finally {
      setConfigLoading(false)
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

  const handleConfigSubmit = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('/api/config/ai', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          api_url: aiApiUrl.trim(),
          model: aiModel.trim(),
          prompt: aiPrompt.trim(),
        }),
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to save configuration')
      }

      setConfigSaved(true)
      setTimeout(() => setConfigSaved(false), 3000)
    } catch (err) {
      console.error('Error saving config:', err)
      alert('Failed to save configuration: ' + err.message)
    }
  }

  const handleResetPrompt = () => {
    setAiPrompt('Analyze this stamp image and return a JSON object with these exact keys: product_name, brand_name, product_type, theme, shape_descriptor, sentiments. Use null for unknown fields. Return ONLY valid JSON, no markdown, no explanation.')
  }

  if (configLoading) {
    return (
      <div className="detail-view settings-view">
        <div className="detail-header">
          <div>
            <h1>Configuration</h1>
          </div>
          <Link to="/" className="btn btn-secondary">Back</Link>
        </div>
        <div className="loading">Loading configuration...</div>
      </div>
    )
  }

  return (
    <div className="detail-view settings-view">
      <div className="detail-header">
        <div>
          <h1>Configuration</h1>
          <p className="settings-subtitle">Manage application settings and AI configuration.</p>
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
        <form onSubmit={handleConfigSubmit}>
          <div className="settings-section">
            <h2>AI Server Configuration</h2>
            <p>Configure the AI server for image analysis. Settings are saved to config/config.yaml.</p>
            <div className="form-group">
              <label>AI Server URL</label>
              <input
                type="url"
                value={aiApiUrl}
                onChange={(e) => {
                  setAiApiUrl(e.target.value)
                  setConfigSaved(false)
                }}
                placeholder="http://localhost:11434/v1"
              />
            </div>
            <div className="form-group">
              <label>Model</label>
              <input
                type="text"
                value={aiModel}
                onChange={(e) => {
                  setAiModel(e.target.value)
                  setConfigSaved(false)
                }}
                placeholder="qwen3.6:35B"
              />
            </div>
          </div>

          <div className="settings-section">
            <h2>AI Prompt</h2>
            <p>Configure the prompt used for image analysis. This is saved to config/config.yaml.</p>
            <div className="form-group">
              <label>Prompt</label>
              <textarea
                value={aiPrompt}
                onChange={(e) => {
                  setAiPrompt(e.target.value)
                  setConfigSaved(false)
                }}
                rows="8"
                placeholder="Analyze this stamp image and return a JSON object..."
              />
            </div>
            <button type="button" className="btn btn-secondary" onClick={handleResetPrompt}>
              Use Default Prompt
            </button>
          </div>

          <div className="form-actions">
            <button type="submit" className="btn btn-primary">Save Configuration</button>
            <Link to="/" className="btn btn-secondary">Cancel</Link>
          </div>
          {configSaved && <div className="settings-saved">Configuration saved to config/config.yaml</div>}
        </form>
      )}
    </div>
  )
}

export default Settings
