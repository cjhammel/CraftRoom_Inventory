import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import '../App.css'

function StampDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [stamp, setStamp] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showDelete, setShowDelete] = useState(false)

  useEffect(() => {
    fetchStamp()
  }, [id])

  const fetchStamp = async () => {
    try {
      const response = await fetch(`/api/stamps/${id}`)
      if (!response.ok) throw new Error('Stamp not found')
      const data = await response.json()
      setStamp(data)
    } catch (err) {
      alert(err.message)
      navigate('/')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    try {
      const response = await fetch(`/api/stamps/${id}`, { method: 'DELETE' })
      if (!response.ok) throw new Error('Failed to delete stamp')
      navigate('/')
    } catch (err) {
      alert(err.message)
    }
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  if (!stamp) {
    return <div className="empty-state"><p>Stamp not found</p></div>
  }

  const fields = [
    { label: 'Item Number', value: stamp.item_number },
    { label: 'Brand', value: stamp.brand_name },
    { label: 'Product Type', value: stamp.product_type },
    { label: 'Theme', value: stamp.theme },
    { label: 'Shape', value: stamp.shape_descriptor },
    { label: 'Sentiments', value: stamp.sentiments },
    { label: 'Location', value: stamp.location },
  ]

  return (
    <div className="detail-view">
      <div className="detail-header">
        <h1>{stamp.product_name}</h1>
        <div className="detail-actions">
          <Link to={`/edit/${stamp.id}`} className="btn btn-primary">
            Edit
          </Link>
          <button onClick={() => setShowDelete(true)} className="btn btn-danger">
            Delete
          </button>
        </div>
      </div>

      {stamp.image_url && (
        <div className="detail-image-container">
          <img
            src={stamp.image_url}
            alt={stamp.product_name}
            className="detail-image"
          />
        </div>
      )}

      <div className="detail-grid">
        {fields.map((field) => (
          field.value && (
            <div key={field.label} className="detail-field">
              <div className="detail-field-label">{field.label}</div>
              <div className="detail-field-value">{field.value}</div>
            </div>
          )
        ))}
      </div>

      {showDelete && (
        <DeleteModal
          onConfirm={handleDelete}
          onCancel={() => setShowDelete(false)}
        />
      )}
    </div>
  )
}

function DeleteModal({ onConfirm, onCancel }) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Delete Stamp</h2>
        <p>Are you sure you want to delete this stamp? This action cannot be undone.</p>
        <div className="modal-actions">
          <button onClick={onCancel} className="btn btn-secondary">
            Cancel
          </button>
          <button onClick={onConfirm} className="btn btn-danger">
            Delete
          </button>
        </div>
      </div>
    </div>
  )
}

export default StampDetail
