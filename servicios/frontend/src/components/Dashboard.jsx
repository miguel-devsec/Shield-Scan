import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import api from '../api/client'

const statusColor = { PASS: '#00ff88', WARNING: '#ff8c00', CRITICAL: '#ff4444', ERROR: '#888', pending: '#aaa', running: '#00bfff', completed: '#00ff88', failed: '#ff4444' }

const s = {
  page: { minHeight: '100vh', padding: '30px 20px' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 30, maxWidth: 900, margin: '0 auto 30px' },
  title: { color: '#00ff00', fontSize: '1.8rem' },
  btnGroup: { display: 'flex', gap: 12 },
  btn: { padding: '10px 20px', background: 'linear-gradient(135deg,#00ff00,#009900)', color: '#000', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: 14 },
  btnLogout: { padding: '10px 20px', background: '#333', color: '#ccc', border: '1px solid #555', borderRadius: 8, cursor: 'pointer', fontWeight: 700, fontSize: 14 },
  table: { width: '100%', maxWidth: 900, margin: '0 auto', background: 'linear-gradient(145deg,#1e1e1e,#2d2d2d)', border: '1px solid #333', borderRadius: 12, overflow: 'hidden' },
  th: { padding: '14px 16px', background: '#1a1a1a', color: '#00ff00', textAlign: 'left', fontSize: '.85rem', textTransform: 'uppercase', letterSpacing: .5 },
  td: { padding: '13px 16px', borderTop: '1px solid #2a2a2a', color: '#ddd', fontSize: '.9rem' },
  empty: { textAlign: 'center', padding: 50, color: '#666' },
  badge: (st) => ({ display: 'inline-block', padding: '3px 10px', borderRadius: 12, background: statusColor[st] + '22', color: statusColor[st], border: `1px solid ${statusColor[st]}`, fontSize: '.8rem', fontWeight: 700 }),
  link: { color: '#00ff00', textDecoration: 'none', fontWeight: 600 },
}

export default function Dashboard() {
  const [audits, setAudits] = useState([])
  const [loading, setLoading] = useState(true)
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    api.get('/audits/').then(r => setAudits(r.data)).catch(() => {}).finally(() => setLoading(false))
    const interval = setInterval(() => {
      api.get('/audits/').then(r => setAudits(r.data)).catch(() => {})
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  function handleLogout() { logout(); navigate('/login') }

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div>
          <h1 style={s.title}>🛡️ ShieldScan</h1>
          <p style={{ color: '#888', marginTop: 4, fontSize: '.9rem' }}>{user?.email} · {user?.role}</p>
        </div>
        <div style={s.btnGroup}>
          <button style={s.btn} onClick={() => navigate('/audits/new')}>+ Nueva Auditoría</button>
          <button style={s.btnLogout} onClick={handleLogout}>Cerrar Sesión</button>
        </div>
      </div>

      <div style={s.table}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={s.th}>#</th>
              <th style={s.th}>URL</th>
              <th style={s.th}>Cliente</th>
              <th style={s.th}>Estado</th>
              <th style={s.th}>Resultado</th>
              <th style={s.th}>Fecha</th>
              <th style={s.th}></th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr><td colSpan={7} style={{ ...s.empty }}><p style={s.empty}>Cargando auditorías...</p></td></tr>
            )}
            {!loading && audits.length === 0 && (
              <tr><td colSpan={7}><p style={s.empty}>No hay auditorías aún. ¡Inicia la primera!</p></td></tr>
            )}
            {audits.map(a => {
              let overallStatus = '—'
              try {
                const r = JSON.parse(a.result || '{}')
                overallStatus = r.overall_status || '—'
              } catch { /* noop */ }
              return (
                <tr key={a.id}>
                  <td style={s.td}>{a.id}</td>
                  <td style={{ ...s.td, maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{a.url}</td>
                  <td style={s.td}>{a.company_name || '—'}</td>
                  <td style={s.td}><span style={s.badge(a.status)}>{a.status.toUpperCase()}</span></td>
                  <td style={s.td}>
                    {a.status === 'completed' ? <span style={s.badge(overallStatus)}>{overallStatus}</span> : '—'}
                  </td>
                  <td style={s.td}>{new Date(a.created_at).toLocaleString('es-CO')}</td>
                  <td style={s.td}>
                    {a.status === 'completed' && (
                      <Link to={`/audits/${a.id}`} style={s.link}>Ver →</Link>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
