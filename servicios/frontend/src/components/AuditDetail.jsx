import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import api from '../api/client'

const statusColor = { PASS: '#00ff88', WARNING: '#ff8c00', CRITICAL: '#ff4444', ERROR: '#888888', INFO: '#00bfff' }
const statusEmoji = { PASS: '✅', WARNING: '⚠️', CRITICAL: '🚨', ERROR: '❌', INFO: 'ℹ️' }

const s = {
  page: { minHeight: '100vh', padding: '30px 20px' },
  wrap: { maxWidth: 860, margin: '0 auto' },
  back: { color: '#00ff00', textDecoration: 'none', fontSize: '.9rem', display: 'inline-block', marginBottom: 20 },
  title: { color: '#00ff00', fontSize: '1.6rem', marginBottom: 4 },
  meta: { color: '#888', fontSize: '.85rem', marginBottom: 30 },
  card: { background: 'linear-gradient(145deg,#1e1e1e,#2d2d2d)', border: '1px solid #333', borderRadius: 12, padding: '20px 24px', marginBottom: 20 },
  cardTitle: { color: '#00ff00', fontSize: '1rem', fontWeight: 700, marginBottom: 16, paddingBottom: 10, borderBottom: '1px solid #333' },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', padding: '10px 0', borderBottom: '1px solid #222' },
  checkName: { color: '#ddd', fontWeight: 600, flex: 1 },
  badge: (st) => ({ padding: '4px 12px', borderRadius: 12, background: (statusColor[st] || '#888') + '22', color: statusColor[st] || '#888', border: `1px solid ${statusColor[st] || '#888'}`, fontSize: '.8rem', fontWeight: 700, whiteSpace: 'nowrap' }),
  detail: { color: '#888', fontSize: '.82rem', marginTop: 4 },
  pending: { textAlign: 'center', padding: 60, color: '#888' },
  overall: (st) => ({ display: 'inline-block', padding: '8px 22px', borderRadius: 20, background: (statusColor[st] || '#888') + '33', color: statusColor[st] || '#888', border: `2px solid ${statusColor[st] || '#888'}`, fontWeight: 700, fontSize: '1rem', letterSpacing: 1, marginBottom: 24 }),
}

function CheckRow({ name, data }) {
  if (!data || typeof data !== 'object') return null
  const st = data.status || 'INFO'
  return (
    <div style={s.row}>
      <div style={{ flex: 1 }}>
        <div style={s.checkName}>{name}</div>
        {data.message && <div style={s.detail}>{data.message}</div>}
        {data.risk_explanation && <div style={{ ...s.detail, marginTop: 4, color: '#aaa' }}>{data.risk_explanation}</div>}
        {data.recommendation && <div style={{ ...s.detail, color: '#00bfff' }}>💡 {data.recommendation}</div>}
      </div>
      <span style={s.badge(st)}>{statusEmoji[st]} {st}</span>
    </div>
  )
}

export default function AuditDetail() {
  const { id } = useParams()
  const [audit, setAudit] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetch = () => api.get(`/audits/${id}`).then(r => setAudit(r.data)).catch(() => {})
    fetch().finally(() => setLoading(false))
    const iv = setInterval(() => {
      if (audit?.status === 'completed' || audit?.status === 'failed') return
      fetch()
    }, 3000)
    return () => clearInterval(iv)
  }, [id, audit?.status])

  if (loading) return <div style={s.pending}>Cargando...</div>
  if (!audit) return <div style={s.pending}>Auditoría no encontrada</div>

  let result = null
  try { result = JSON.parse(audit.result || 'null') } catch { /* noop */ }

  if (audit.status !== 'completed' || !result) {
    return (
      <div style={s.page}>
        <div style={s.wrap}>
          <Link to="/" style={s.back}>← Dashboard</Link>
          <h2 style={s.title}>Auditoría #{audit.id}</h2>
          <p style={{ color: '#888', marginBottom: 20 }}>{audit.url}</p>
          <div style={{ ...s.card, textAlign: 'center', padding: 50 }}>
            <p style={{ color: '#00bfff', fontSize: '1.1rem', marginBottom: 10 }}>
              {audit.status === 'pending' && '⏳ En cola — la auditoría comenzará pronto...'}
              {audit.status === 'running' && '🔍 Analizando vulnerabilidades...'}
              {audit.status === 'failed' && '❌ La auditoría falló. Intenta de nuevo.'}
            </p>
            <p style={{ color: '#555' }}>Esta página se actualiza automáticamente.</p>
          </div>
        </div>
      </div>
    )
  }

  const overall = result.overall_status || 'UNKNOWN'

  return (
    <div style={s.page}>
      <div style={s.wrap}>
        <Link to="/" style={s.back}>← Dashboard</Link>
        <h2 style={s.title}>🔒 Reporte de Auditoría #{audit.id}</h2>
        <div style={s.meta}>
          {audit.url} · {result.company_name} · {new Date(audit.created_at).toLocaleString('es-CO')}
        </div>

        <div style={s.overall(overall)}>{statusEmoji[overall]} Estado General: {overall}</div>

        {/* Security Headers */}
        {result.security_headers && (
          <div style={s.card}>
            <div style={s.cardTitle}>🛡️ Headers de Seguridad</div>
            {Object.entries(result.security_headers).map(([h, d]) => (
              <CheckRow key={h} name={h} data={d} />
            ))}
          </div>
        )}

        {/* WordPress-specific */}
        {result.site_type === 'WordPress' && (
          <div style={s.card}>
            <div style={s.cardTitle}>🔧 Verificaciones WordPress</div>
            {result.wp_admin_access && <CheckRow name="Acceso a wp-admin" data={result.wp_admin_access} />}
            {result.xmlrpc_access && <CheckRow name="xmlrpc.php" data={result.xmlrpc_access} />}
            {result.wp_config_exposure && <CheckRow name="wp-config.php" data={result.wp_config_exposure} />}
          </div>
        )}

        {/* General checks */}
        <div style={s.card}>
          <div style={s.cardTitle}>🌐 Verificaciones Generales</div>
          {result.directory_listing && <CheckRow name="Listado de Directorios" data={result.directory_listing} />}
          {result.ssl_configuration && <CheckRow name="Configuración SSL" data={result.ssl_configuration} />}
          {result.sensitive_files && <CheckRow name="Archivos Sensibles" data={result.sensitive_files} />}
        </div>

        {/* Detection */}
        {result.wordpress_detection && (
          <div style={s.card}>
            <div style={s.cardTitle}>🔍 Detección de Tecnología</div>
            <CheckRow name={`Tipo de Sitio: ${result.site_type}`} data={result.wordpress_detection} />
          </div>
        )}
      </div>
    </div>
  )
}
