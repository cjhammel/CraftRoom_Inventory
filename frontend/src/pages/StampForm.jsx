import { useState, useEffect, useRef } from 'react'
import { Link, useParams, useNavigate } from 'react-router-dom'
import { AI_API_URL_KEY, AI_PROMPT_KEY } from './Settings'
import '../App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function StampForm() {
  const { id } = useParams()
  const navigate = useNavigate()
  const isEdit = !!id
  const fileInputRef = useRef(null)

  const [form, setForm] = useState({
    product_name: '',
    item_number: '',
    brand_name: '',
    product_type: '',
    theme: '',
    shape_descriptor: '',
    sentiments: '',
    location_id: '',
  })

  const [locations, setLocations] = useState([])
  const [locationsLoading, setLocationsLoading] = useState(true)
  const [locationError, setLocationError] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const [rotatedFile, setRotatedFile] = useState(null)
  const [imagePreview, setImagePreview] = useState(null)
  const [rotation, setRotation] = useState(0)
  const [isDragging, setIsDragging] = useState(false)
  const [errors, setErrors] = useState({})
  const [loading, setLoading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [aiError, setAiError] = useState(null)

  useEffect(() => {
    fetchLocations()
    if (isEdit) {
      fetchStamp()
    }
  }, [id])

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

  const formatLocation = (location) => {
    const label = [location.cabinet, location.shelf, location.bin].filter(Boolean).join(' / ')
    return label || `Location #${location.id}`
  }

  const fetchStamp = async () => {
    setLoading(true)
    try {
      const response = await fetch(`/api/stamps/${id}`)
      if (!response.ok) throw new Error('Stamp not found')
      const stamp = await response.json()
      setForm({
        product_name: stamp.product_name || '',
        item_number: stamp.item_number || '',
        brand_name: stamp.brand_name || '',
        product_type: stamp.product_type || '',
        theme: stamp.theme || '',
        shape_descriptor: stamp.shape_descriptor || '',
        sentiments: stamp.sentiments || '',
        location_id: stamp.location_id ? String(stamp.location_id) : '',
      })
      setImagePreview(stamp.image_url ? `${API_URL}${stamp.image_url}` : null)
    } catch (err) {
      alert(err.message)
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setForm((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
    // Clear error when user types
    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }))
    }
  }

  const rotateImage = async (degrees) => {
    const img = new Image()
    img.src = imagePreview
    await new Promise((resolve) => {
      img.onload = resolve
    })

    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')

    const rad = (degrees * Math.PI) / 180
    const shouldSwapDimensions = Math.abs(degrees) === 90 || Math.abs(degrees) === 270

    if (shouldSwapDimensions) {
      canvas.width = img.height
      canvas.height = img.width
    } else {
      canvas.width = img.width
      canvas.height = img.height
    }

    ctx.translate(canvas.width / 2, canvas.height / 2)
    ctx.rotate(rad)
    ctx.drawImage(img, -img.width / 2, -img.height / 2)

    canvas.toBlob((blob) => {
      if (blob) {
        const newFile = new File([blob], imageFile.name, { type: imageFile.type })
        const newUrl = URL.createObjectURL(newFile)
        setRotatedFile(newFile)
        setImagePreview(newUrl)
      }
    }, imageFile.type, 0.9)
  }

  const handleRotateLeft = () => {
    const newRotation = (rotation - 90 + 360) % 360
    rotateImage(-90).then(() => setRotation(newRotation))
  }

  const handleRotateRight = () => {
    const newRotation = (rotation + 90) % 360
    rotateImage(90).then(() => setRotation(newRotation))
  }

  const handleResetImage = () => {
    setRotation(0)
    setRotatedFile(null)
    setImagePreview(null)
    setImageFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const processFile = (file) => {
    if (file && file.type.startsWith('image/')) {
      setRotation(0)
      setRotatedFile(null)
      setImageFile(file)
      setImagePreview(URL.createObjectURL(file))
    }
  }

  const handleImageChange = (e) => {
    const file = e.target.files[0]
    processFile(file)
  }

  const handleDragEnter = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const files = e.dataTransfer.files
    if (files && files.length > 0) {
      processFile(files[0])
    }
  }

  const handleAnalyzeImage = async () => {
    if (!imageFile) {
      setAiError('Please select an image first')
      return
    }

    setAnalyzing(true)
    setAiError(null)

    const formData = new FormData()
    formData.append('image', imageFile)
    const aiApiUrl = localStorage.getItem(AI_API_URL_KEY)
    const aiPrompt = localStorage.getItem(AI_PROMPT_KEY)
    if (aiApiUrl) formData.append('ai_api_url', aiApiUrl)
    if (aiPrompt) formData.append('ai_prompt', aiPrompt)

    try {
      const response = await fetch('/api/ai/analyze-image', {
        method: 'POST',
        body: formData,
      })

      if (response.status === 501) {
        const data = await response.json()
        setAiError(data.detail?.message || 'AI service not configured')
        return
      }

      if (!response.ok) throw new Error('AI analysis failed')

      const data = await response.json()
      const suggestions = data.suggestions || {}

      setForm((prev) => ({
        ...prev,
        product_name: suggestions.product_name || prev.product_name,
        brand_name: suggestions.brand_name || prev.brand_name,
        product_type: suggestions.product_type || prev.product_type,
        theme: suggestions.theme || prev.theme,
        shape_descriptor: suggestions.shape_descriptor || prev.shape_descriptor,
        sentiments: suggestions.sentiments || prev.sentiments,
      }))

      setAiError(null)
    } catch (err) {
      setAiError(err.message)
    } finally {
      setAnalyzing(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Client-side validation
    const newErrors = {}
    if (!form.product_name.trim()) {
      newErrors.product_name = 'Product name is required'
    }
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors)
      return
    }

    setLoading(true)

    const formData = new FormData()
    formData.append('product_name', form.product_name)
    if (isEdit || form.item_number) formData.append('item_number', form.item_number)
    if (form.brand_name) formData.append('brand_name', form.brand_name)
    if (form.product_type) formData.append('product_type', form.product_type)
    if (form.theme) formData.append('theme', form.theme)
    if (form.shape_descriptor) formData.append('shape_descriptor', form.shape_descriptor)
    if (form.sentiments) formData.append('sentiments', form.sentiments)
    if (isEdit || form.location_id) formData.append('location_id', form.location_id)
    if (rotatedFile) formData.append('image', rotatedFile)
    else if (imageFile) formData.append('image', imageFile)

    try {
      const url = isEdit ? `/api/stamps/${id}` : '/api/stamps'
      const method = isEdit ? 'PUT' : 'POST'

      const response = await fetch(url, {
        method,
        body: formData,
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to save stamp')
      }

      navigate(`/stamps/${isEdit ? id : (await response.json()).id}`)
    } catch (err) {
      alert(err.message)
    } finally {
      setLoading(false)
    }
  }

  if (loading && isEdit) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="detail-view">
      <h1>{isEdit ? 'Edit Stamp' : 'Add New Stamp'}</h1>

      <form onSubmit={handleSubmit}>
        {/* Image upload section */}
        <div className="form-group">
          <label>Image</label>
          <div
            className={`image-upload-area ${isDragging ? 'drag-over' : ''}`}
            onClick={() => fileInputRef.current?.click()}
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            {imagePreview ? (
              <img src={imagePreview} alt="Preview" className="image-preview" />
            ) : (
              <p>{isDragging ? 'Drop image here' : 'Click or drag an image here'}</p>
            )}
            <input
              ref={fileInputRef}
              id="image-input"
              type="file"
              accept="image/jpeg,image/jpg,image/png,image/webp"
              onChange={handleImageChange}
              style={{ display: 'none' }}
            />
          </div>
          {imageFile && (
            <div className="image-actions">
              <button
                type="button"
                className="btn btn-secondary analyze-btn"
                onClick={handleAnalyzeImage}
                disabled={analyzing}
              >
                {analyzing ? 'Analyzing...' : '✨ Analyze Image'}
              </button>
              <button
                type="button"
                className="btn btn-secondary rotate-btn"
                onClick={handleRotateLeft}
              >
                ↺ Rotate Left
              </button>
              <button
                type="button"
                className="btn btn-secondary rotate-btn"
                onClick={handleRotateRight}
              >
                ↻ Rotate Right
              </button>
              <button
                type="button"
                className="btn btn-danger reset-btn"
                onClick={handleResetImage}
              >
                Remove Image
              </button>
            </div>
          )}
          {aiError && <div className="error">{aiError}</div>}
        </div>

        <div className="form-group">
          <label>Product Name *</label>
          <input
            type="text"
            name="product_name"
            value={form.product_name}
            onChange={handleChange}
            placeholder="e.g. Blue Mauritius"
          />
          {errors.product_name && <div className="error">{errors.product_name}</div>}
        </div>

        <div className="form-group">
          <label>Item Number</label>
          <input
            type="text"
            name="item_number"
            value={form.item_number}
            onChange={handleChange}
            placeholder="e.g. ITEM-001"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Brand Name</label>
            <input
              type="text"
              name="brand_name"
              value={form.brand_name}
              onChange={handleChange}
              placeholder="e.g. StampCo"
            />
          </div>
          <div className="form-group">
            <label>Product Type</label>
            <input
              type="text"
              name="product_type"
              value={form.product_type}
              onChange={handleChange}
              placeholder="e.g. Rubber"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Theme</label>
            <input
              type="text"
              name="theme"
              value={form.theme}
              onChange={handleChange}
              placeholder="e.g. Floral"
            />
          </div>
          <div className="form-group">
            <label>Shape Descriptor</label>
            <input
              type="text"
              name="shape_descriptor"
              value={form.shape_descriptor}
              onChange={handleChange}
              placeholder="e.g. Square"
            />
          </div>
        </div>

        <div className="form-group">
          <label>Sentiments</label>
          <input
            type="text"
            name="sentiments"
            value={form.sentiments}
            onChange={handleChange}
            placeholder="e.g. Hello, Goodbye"
          />
        </div>

        <div className="form-group">
          <label>Storage Location</label>
          <select
            name="location_id"
            value={form.location_id}
            onChange={handleChange}
            disabled={locationsLoading || !!locationError}
          >
            <option value="">
              {locationsLoading ? 'Loading locations...' : 'No location'}
            </option>
            {locations.map((location) => (
              <option key={location.id} value={location.id}>
                {formatLocation(location)}
              </option>
            ))}
          </select>
          {locationError && <div className="error">{locationError}</div>}
          {!locationsLoading && !locationError && locations.length === 0 && (
            <p className="field-help">
              Add locations in <Link to="/settings">Configuration</Link> to select one here.
            </p>
          )}
        </div>

        <div className="form-actions">
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? 'Saving...' : isEdit ? 'Update' : 'Create'}
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() => navigate(-1)}
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  )
}

export default StampForm
