import { useState } from 'react'
import { api } from '../api.js'

export default function Login({ onLogin }) {
  const [pwd, setPwd] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    setLoading(true); setErr('')
    try {
      const d = await api.login(pwd)
      onLogin(d.token, d.child_name)
    } catch (e) { setErr('Неверный пароль') } finally { setLoading(false) }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center',
      justifyContent: 'center', background: 'var(--bg)' }}>
      <div style={{ background: '#fff', borderRadius: 16, padding: '2.5rem 2rem',
        border: '1px solid var(--border)', width: 360, textAlign: 'center' }}>
        <div style={{ fontSize: 48, marginBottom: 12 }}>🏊</div>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>Swim Trainer</h1>
        <p style={{ color: 'var(--muted)', fontSize: 14, marginBottom: 28 }}>
          1% лучше каждый день
        </p>
        <input type="password" value={pwd} onChange={e => setPwd(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && submit()}
          placeholder="Пароль" autoFocus
          style={{ width: '100%', padding: '10px 14px', border: '1px solid var(--border)',
            borderRadius: 8, fontSize: 15, marginBottom: 12, outline: 'none' }} />
        {err && <p style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 10 }}>{err}</p>}
        <button onClick={submit} disabled={loading || !pwd}
          style={{ width: '100%', padding: '11px', background: 'var(--primary)',
            color: '#fff', border: 'none', borderRadius: 8, fontSize: 15,
            fontWeight: 600, opacity: loading ? 0.7 : 1 }}>
          {loading ? 'Вход...' : 'Войти'}
        </button>
      </div>
    </div>
  )
}
