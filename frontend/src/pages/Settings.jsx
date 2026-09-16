import { useState } from 'react'
import { Link } from 'react-router-dom'
import '../App.css'

export const AI_API_URL_KEY = 'craftroom.aiApiUrl'
export const AI_PROMPT_KEY = 'craftroom.aiPrompt'

const DEFAULT_AI_PROMPT = 'Analyze this stamp image and return a JSON object with these exact keys: product_name, brand_name, product_type, theme, shape_descriptor, sentiments. Use null for unknown fields. Return ONLY valid JSON, no markdown, no explanation.'

function Settings() {
  const [aiApiUrl, setAiApiUrl] = useState(() => localStorage.getItem(AI_API_URL_KEY) || '')
  const [aiPrompt, setAiPrompt] = useState(() => localStorage.getItem(AI_PROMPT_KEY) || '')
  const [saved, setSaved] = useState(false)

  const handleSubmit = (e) => {
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

      <form onSubmit={handleSubmit}>
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
    </div>
  )
}

export default Settings
