import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Login from './components/Login'
import Register from './components/Register'
import Dashboard from './components/Dashboard'
import NewAudit from './components/NewAudit'
import AuditDetail from './components/AuditDetail'
import { useEffect, useState } from 'react'

function PrivateRoute({ children }) {
  const { user, loadUser } = useAuth()
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    loadUser().finally(() => setChecked(true))
  }, [loadUser])

  if (!checked) return <div style={{ color: '#00ff00', padding: 40 }}>Cargando...</div>
  return user ? children : <Navigate to="/login" replace />
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
          <Route path="/audits/new" element={<PrivateRoute><NewAudit /></PrivateRoute>} />
          <Route path="/audits/:id" element={<PrivateRoute><AuditDetail /></PrivateRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
