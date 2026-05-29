import { useState, useEffect } from 'react'
import { api } from '../api.js'

export default function Settings() {
  const [config, setConfig]   = useState({ telegram_bot_token:'', telegram_chat_id:'', child_name:'', parent_password:'' })
  const [loaded, setLoaded]   = useState(false)
  const [saving, setSaving]   = useState(false)
  const [msg, setMsg]         = useState(null)
  const [testMsg, setTestMsg] = useState(null)
  const [testing, setTesting] = useState(false)
  const [showPwd, setShowPwd] = useState(false)
  const [showToken, setShowToken] = useState(false)

  useEffect(() => {
    api.getSettings().then(d => { setConfig(d); setLoaded(true) }).catch(() => setLoaded(true))
  }, [])

  const save = async () => {
    setSaving(true); setMsg(null)
    try {
      await api.saveSettings(config)
      setMsg({ type:'ok', text:'Настройки сохранены. Перезапусти бот-контейнер для применения.' })
    } catch(e) {
      setMsg({ type:'err', text: e.message || 'Ошибка сохранения' })
    } finally { setSaving(false) }
  }

  const testBot = async () => {
    setTesting(true); setTestMsg(null)
    try {
      await api.testTelegram()
      setTestMsg({ type:'ok', text:'Сообщение отправлено! Проверь Telegram.' })
    } catch(e) {
      setTestMsg({ type:'err', text: e.message || 'Не удалось отправить. Проверь токен и chat_id.' })
    } finally { setTesting(false) }
  }

  const f = (k,v) => setConfig(p => ({...p, [k]: v}))

  const Field = ({ label, k, type='text', show, onToggle, hint }) => (
    <div>
      <label style={{ fontSize:12, color:'var(--muted)', display:'block', marginBottom:4 }}>{label}</label>
      <div style={{ position:'relative' }}>
        <input
          type={onToggle ? (show ? 'text' : 'password') : type}
          value={config[k] || ''}
          onChange={e => f(k, e.target.value)}
          style={{ width:'100%', padding:'9px 12px', paddingRight: onToggle ? 44 : 12,
            border:'1px solid var(--border)', borderRadius:8, fontSize:14 }}
        />
        {onToggle && (
          <button onClick={onToggle} style={{ position:'absolute', right:10, top:'50%',
            transform:'translateY(-50%)', background:'none', border:'none',
            color:'var(--muted)', fontSize:16, cursor:'pointer', padding:0 }}>
            {show ? '🙈' : '👁'}
          </button>
        )}
      </div>
      {hint && <p style={{ fontSize:11, color:'var(--muted)', marginTop:4 }}>{hint}</p>}
    </div>
  )

  return (
    <div style={{ maxWidth: 600 }}>
      <h1 style={{ fontSize:20, fontWeight:700, marginBottom:6 }}>Настройки</h1>
      <p style={{ color:'var(--muted)', fontSize:14, marginBottom:24 }}>
        Все изменения сохраняются в файл <code>.env</code> на сервере.
      </p>

      {!loaded && <p style={{ color:'var(--muted)' }}>Загрузка...</p>}

      {loaded && (
        <div style={{ display:'flex', flexDirection:'column', gap:20 }}>

          {/* Child */}
          <section style={{ background:'#fff', border:'1px solid var(--border)',
            borderRadius:12, padding:'1.25rem' }}>
            <h2 style={{ fontSize:15, fontWeight:600, marginBottom:14 }}>Общие</h2>
            <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
              <Field label="Имя сына" k="child_name" hint="Отображается в приветствии и Telegram" />
              <Field label="Пароль папы" k="parent_password" type="password"
                show={showPwd} onToggle={() => setShowPwd(p=>!p)}
                hint="Пароль для входа в дашборд" />
            </div>
          </section>

          {/* Telegram */}
          <section style={{ background:'#fff', border:'1px solid var(--border)',
            borderRadius:12, padding:'1.25rem' }}>
            <h2 style={{ fontSize:15, fontWeight:600, marginBottom:4 }}>Telegram бот</h2>
            <p style={{ fontSize:13, color:'var(--muted)', marginBottom:14, lineHeight:1.6 }}>
              1. Создай бота через <a href="https://t.me/BotFather" target="_blank">@BotFather</a> → получи токен<br/>
              2. Сын пишет боту <code>/start</code><br/>
              3. Узнай его chat_id через <a href="https://t.me/userinfobot" target="_blank">@userinfobot</a>
            </p>
            <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
              <Field label="Bot Token" k="telegram_bot_token"
                show={showToken} onToggle={() => setShowToken(p=>!p)}
                hint="Формат: 123456789:ABCdef..." />
              <Field label="Chat ID сына" k="telegram_chat_id"
                hint="Числовой ID, например: 987654321" />
            </div>

            {testMsg && (
              <div style={{ marginTop:12, padding:'8px 12px', borderRadius:8, fontSize:13,
                background: testMsg.type==='ok' ? 'var(--success-light)' : '#fee2e2',
                color: testMsg.type==='ok' ? 'var(--success)' : 'var(--danger)',
                border: `1px solid ${testMsg.type==='ok' ? '#a7f3d0' : '#fca5a5'}` }}>
                {testMsg.text}
              </div>
            )}

            <button onClick={testBot} disabled={testing || !config.telegram_bot_token || !config.telegram_chat_id}
              style={{ marginTop:12, padding:'8px 18px', border:'1px solid var(--border)',
                borderRadius:8, background:'#fff', fontSize:13, cursor:'pointer' }}>
              {testing ? 'Отправка...' : '📨 Отправить тестовое сообщение'}
            </button>
          </section>

          {/* Save */}
          {msg && (
            <div style={{ padding:'10px 14px', borderRadius:8, fontSize:13,
              background: msg.type==='ok' ? 'var(--success-light)' : '#fee2e2',
              color: msg.type==='ok' ? 'var(--success)' : 'var(--danger)',
              border: `1px solid ${msg.type==='ok' ? '#a7f3d0' : '#fca5a5'}` }}>
              {msg.text}
            </div>
          )}

          <button onClick={save} disabled={saving}
            style={{ padding:'11px', background:'var(--primary)', color:'#fff',
              border:'none', borderRadius:8, fontWeight:600, fontSize:15, cursor:'pointer' }}>
            {saving ? 'Сохранение...' : 'Сохранить настройки'}
          </button>
        </div>
      )}
    </div>
  )
}
