import { useState, useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate, NavLink } from 'react-router-dom'
import { api, setToken, getToken, clearToken } from './api.js'
import Login from './pages/Login.jsx'
import Dashboard from './pages/Dashboard.jsx'
import Exercises from './pages/Exercises.jsx'
import Schedule from './pages/Schedule.jsx'
import Progress from './pages/Progress.jsx'
import SwimResults from './pages/SwimResults.jsx'
import Rewards from './pages/Rewards.jsx'

const NAV = [
  { to: '/',           icon: '🏠', label: 'Главная'    },
  { to: '/exercises',  icon: '🏋️', label: 'Упражнения' },
  { to: '/schedule',   icon: '📅', label: 'Расписание'  },
  { to: '/progress',   icon: '📊', label: 'Прогресс'   },
  { to: '/swim',       icon: '🏊', label: 'Заплывы'    },
  { to: '/rewards',    icon: '💰', label: 'Награды'    },
]

export default function App() {
  const [auth, setAuth] = useState(!!getToken())
  const [childName, setChildName] = useState('Сын')

  useEffect(() => {
    if (auth) api.me().then(d => setChildName(d.child_name)).catch(() => { clearToken(); setAuth(false) })
  }, [auth])

  if (!auth) return <Login onLogin={(t, name) => { setToken(t); setChildName(name); setAuth(true) }} />

  return (
    <BrowserRouter>
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
        <header style={{ background: '#fff', borderBottom: '1px solid var(--border)',
          padding: '0 1.5rem', display: 'flex', alignItems: 'center',
          justifyContent: 'space-between', height: 56 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span style={{ fontSize: 22 }}>🏊</span>
            <span style={{ fontWeight: 600, fontSize: 16 }}>Swim Trainer</span>
            <span style={{ fontSize: 13, color: 'var(--muted)', marginLeft: 4 }}>1% лучше каждый день</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span style={{ fontSize: 13, color: 'var(--muted)' }}>{childName}</span>
            <button onClick={() => { clearToken(); setAuth(false) }}
              style={{ fontSize: 12, padding: '4px 12px', border: '1px solid var(--border)',
                borderRadius: 6, background: 'transparent', color: 'var(--muted)' }}>
              Выйти
            </button>
          </div>
        </header>

        <div style={{ display: 'flex', flex: 1 }}>
          <nav style={{ width: 200, background: '#fff', borderRight: '1px solid var(--border)',
            padding: '1rem 0', flexShrink: 0 }}>
            {NAV.map(n => (
              <NavLink key={n.to} to={n.to} end={n.to === '/'}
                style={({ isActive }) => ({
                  display: 'flex', alignItems: 'center', gap: 10,
                  padding: '10px 20px', fontSize: 14, color: isActive ? 'var(--primary)' : 'var(--text)',
                  background: isActive ? 'var(--primary-light)' : 'transparent',
                  borderRight: isActive ? '3px solid var(--primary)' : '3px solid transparent',
                  textDecoration: 'none', transition: 'all .15s'
                })}>
                <span>{n.icon}</span>{n.label}
              </NavLink>
            ))}
          </nav>

          <main style={{ flex: 1, padding: '1.5rem', overflowY: 'auto', maxWidth: 1100 }}>
            <Routes>
              <Route path="/"          element={<Dashboard childName={childName} />} />
              <Route path="/exercises" element={<Exercises />} />
              <Route path="/schedule"  element={<Schedule />} />
              <Route path="/progress"  element={<Progress />} />
              <Route path="/swim"      element={<SwimResults />} />
              <Route path="/rewards"   element={<Rewards />} />
              <Route path="*"          element={<Navigate to="/" />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  )
}
