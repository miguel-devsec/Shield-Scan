import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import api from '../api/client'

const s = {
  page: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 },
  card: { background: 'linear-gradient(145deg,#1e1e1e,#2d2d2d)', border: '1px solid #333', borderRadius: 15, padding: 40, width: '100%', maxWidth: 520, boxShadow: '0 25px 50px rgba(0,0,0,.5)' },
  title: { color: '#00ff00', fontSize: '1.5rem', marginBottom: 6 },
  sub: { color: '#888', marginBottom: 28, fontSize: '.9rem' },
  label: { display: 'block', color: '#00ff00', fontSize: '.85rem', textTransform: 'uppercase', letterSpacing: .5, marginBottom: 6, fontWeight: 600 },
  input: { width: '100%', padding: '13px 15px', background: '#1a1a1a', border: '2px solid #333', borderRadius: 8, color: '#fff', fontSize: 15, marginBottom: 18 },
  btn: { width: '100%', padding: '14px', background: 'linear-gradient(135deg,#00ff00,#009900)', color: '#000', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: 'pointer', textTransform: 'uppercase', letterSpacing: 1 },
  err: { color: '#ff4444', marginBottom: 14, textAlign: 'center', fontSize: '.9rem' },
  back: { display: 'block', textAlign: 'center', marginTop: 18, color: '#888', fontSize: '.9rem', textDecoration: 'none' },
}

export default function NewAudit() {
  const [url, setUrl] = useState('')
  const [company, setCompany] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const { data } = await api.post('/audits/', { url, company_name: company || undefined })
      navigate(`/audits/${data.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al iniciar la auditoría')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <h2 style={s.title}>🔍 Nueva Auditoría de Seguridad</h2>
        <p style={s.sub}>El análisis se ejecuta en segundo plano. Puedes seguir el progreso en el dashboard.</p>
        {error && <p style={s.err}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <label style={s.label}>URL del sitio a auditar *</label>
          <input style={s.input} type="url" value={url} onChange={e => setUrl(e.target.value)} required placeholder="https://ejemplo.com" />
          <label style={s.label}>Nombre del cliente (opcional)</label>
          <input style={s.input} type="text" value={company} onChange={e => setCompany(e.target.value)} placeholder="Mi Empresa S.A.S." />
          <button style={s.btn} type="submit" disabled={loading}>
            {loading ? '⏳ Enviando...' : '🚀 Iniciar Auditoría'}
          </button>
        </form>
        <Link to="/" style={s.back}>← Volver al dashboard</Link>
      </div>
    </div>
  )
}
