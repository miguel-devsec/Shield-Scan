import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

const s = {
  page: { minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 },
  card: {
    background: 'linear-gradient(145deg,#1e1e1e,#2d2d2d)',
    border: '1px solid #333',
    borderRadius: 15,
    padding: 40,
    width: '100%',
    maxWidth: 420,
    boxShadow: '0 25px 50px rgba(0,0,0,.5)',
  },
  title: { color: '#00ff00', textAlign: 'center', fontSize: '2rem', marginBottom: 8, textShadow: '0 0 10px rgba(0,255,0,.3)' },
  sub: { color: '#b0b0b0', textAlign: 'center', marginBottom: 28 },
  label: { display: 'block', color: '#00ff00', fontSize: '.85rem', textTransform: 'uppercase', letterSpacing: .5, marginBottom: 6, fontWeight: 600 },
  input: { width: '100%', padding: '13px 15px', background: '#1a1a1a', border: '2px solid #333', borderRadius: 8, color: '#fff', fontSize: 15, outline: 'none', marginBottom: 18 },
  btn: { width: '100%', padding: '14px', background: 'linear-gradient(135deg,#00ff00,#009900)', color: '#000', border: 'none', borderRadius: 8, fontSize: 15, fontWeight: 700, cursor: 'pointer', textTransform: 'uppercase', letterSpacing: 1 },
  err: { color: '#ff4444', marginBottom: 14, textAlign: 'center', fontSize: '.9rem' },
  link: { display: 'block', textAlign: 'center', marginTop: 18, color: '#00ff00', fontSize: '.9rem' },
}

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch (err) {
      setError(err.response?.data?.detail || 'Credenciales inválidas')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={s.page}>
      <div style={s.card}>
        <h1 style={s.title}>🛡️ ShieldScan</h1>
        <p style={s.sub}>Auditor de Seguridad Web</p>
        {error && <p style={s.err}>{error}</p>}
        <form onSubmit={handleSubmit}>
          <label style={s.label}>Email</label>
          <input style={s.input} type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="usuario@ejemplo.com" />
          <label style={s.label}>Contraseña</label>
          <input style={s.input} type="password" value={password} onChange={e => setPassword(e.target.value)} required placeholder="••••••••" />
          <button style={s.btn} type="submit" disabled={loading}>
            {loading ? 'Iniciando sesión...' : '🔐 Iniciar Sesión'}
          </button>
        </form>
        <Link to="/register" style={s.link}>¿No tienes cuenta? Regístrate</Link>
      </div>
    </div>
  )
}
