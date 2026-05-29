import { useState, useEffect } from 'react'
import { api } from '../api.js'

export default function Settings() {
  const [config, setConfig]     = useState({ telegram_bot_token:'', telegram_chat_id:'', child_name:'', parent_password:'' })
  const [tokenSaved, setTokenSaved] = useState(false)
  const [loaded, setLoaded]     = useState(false)
  const [saving, setSaving]     = useState(false)
  const [msg, setMsg]           = useState(null)
  const [testMsg, setTestMsg]   = useState(null)
  const [testing, setTesting]   = useState(false)
  const [showPwd, setShowPwd]   = useState(false)
  const [showToken, setShowToken] = useState(false)

  useEffect(() => {
    api.getSettings()
      .then(d => {
        const saved = d.telegram_bot_token === '***SAVED***'
        setTokenSaved(saved)
        setConfig({ ...d, telegram_bot_token: saved ? '' : (d.telegram_bot_token || '') })
        setLoaded(true)
      })
      .catch(() => setLoaded(true))
  }, [])

  const save = async () => {
    setSaving(true); setMsg(null)
    try {
      // If token field empty and was previously saved — keep old token
      const payload = { ...config }
      if (!payload.telegram_bot_token && tokenSaved) {
        payload.telegram_bot_token = '***SAVED***'
      }
      await api.saveSettings(payload)
      setMsg({ type:'ok', text:'Настройки сохранены! Перезапусти бот: docker-compose restart bot' })
      // Reload to sync state
      const fresh = await api.getSettings()
      const saved = fresh.telegram_bot_token === '***SAVED***'
      setTokenSaved(saved)
      setConfig({ ...fresh, telegram_bot_token: saved ? '' : (fresh.telegram_bot_token || '') })
    } catch(e) {
      setMsg({ type:'err', text: e.message || 'Ошибка сохранения' })
    } finally { setSaving(false) }
  }

  const testBot = async () => {
    setTesting(true); setTestMsg(null)
    try {
      const res = await api.testTelegram()
      setTestMsg({ type:'ok', text: res.message || 'Сообщение отправлено! Проверь Telegram.' })
    } catch(e) {
      setTestMsg({ type:'err', text: e.message || 'Ошибка отправки' })
    } finally { setTesting(false) }
  }

  const f = (k,v) => {
    setConfig(p => ({...p, [k]: v}))
    if (k === 'telegram_bot_token') setTokenSaved(false)
    setMsg(null)
  }

  const inputStyle = {
    width:'100%', padding:'9px 12px', border:'1px solid var(--border)',
    borderRadius:8, fontSize:14, outline:'none',
    background: 'var(--surface)', color: 'var(--text)'
  }

  return (
    <div style={{ maxWidth: 580 }}>
      <h1 style={{ fontSize:20, fontWeight:700, marginBottom:4 }}>⚙️ Настройки</h1>
      <p style={{ color:'var(--muted)', fontSize:14, marginBottom:24 }}>
        Изменения сохраняются в <code style={{ background:'var(--bg)', padding:'1px 6px', borderRadius:4 }}>/app/data/.env.runtime</code>
      </p>

      {!loaded && <p style={{ color:'var(--muted)' }}>Загрузка...</p>}

      {loaded && (
        <div style={{ display:'flex', flexDirection:'column', gap:16 }}>

          {/* General */}
          <section style={{ background:'#fff', border:'1px solid var(--border)', borderRadius:12, padding:'1.25rem' }}>
            <h2 style={{ fontSize:15, fontWeight:600, marginBottom:14, display:'flex', alignItems:'center', gap:8 }}>
              Общие
            </h2>
            <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
              <div>
                <label style={{ fontSize:12, color:'var(--muted)', display:'block', marginBottom:4 }}>Имя сына</label>
                <input value={config.child_name || ''} onChange={e => f('child_name', e.target.value)}
                  placeholder="например: Артём" style={inputStyle} />
                <p style={{ fontSize:11, color:'var(--muted)', marginTop:3 }}>Отображается в приветствии и Telegram-уведомлениях</p>
              </div>
              <div>
                <label style={{ fontSize:12, color:'var(--muted)', display:'block', marginBottom:4 }}>Пароль для входа (папа)</label>
                <div style={{ position:'relative' }}>
                  <input
                    type={showPwd ? 'text' : 'password'}
                    value={config.parent_password || ''}
                    onChange={e => f('parent_password', e.target.value)}
                    placeholder="Новый пароль (оставь пустым чтобы не менять)"
                    style={{ ...inputStyle, paddingRight:42 }}
                  />
                  <button onClick={() => setShowPwd(p=>!p)}
                    style={{ position:'absolute', right:10, top:'50%', transform:'translateY(-50%)',
                      background:'none', border:'none', cursor:'pointer', fontSize:16, color:'var(--muted)', padding:0 }}>
                    {showPwd ? '🙈' : '👁'}
                  </button>
                </div>
              </div>
            </div>
          </section>

          {/* Telegram */}
          <section style={{ background:'#fff', border:'1px solid var(--border)', borderRadius:12, padding:'1.25rem' }}>
            <h2 style={{ fontSize:15, fontWeight:600, marginBottom:10 }}>
              Telegram бот
            </h2>

            <div style={{ background:'var(--bg)', borderRadius:8, padding:'10px 14px',
              fontSize:13, color:'var(--muted)', marginBottom:14, lineHeight:1.8 }}>
              <strong style={{ color:'var(--text)', display:'block', marginBottom:4 }}>Как подключить бота:</strong>
              1. Напишите <a href="https://t.me/BotFather" target="_blank" rel="noreferrer">@BotFather</a> → /newbot → получите токен<br/>
              2. Сын пишет боту <code>/start</code> — бот запомнит его<br/>
              3. Chat ID узнайте через <a href="https://t.me/userinfobot" target="_blank" rel="noreferrer">@userinfobot</a>
            </div>

            <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
              <div>
                <label style={{ fontSize:12, color:'var(--muted)', display:'block', marginBottom:4 }}>
                  Bot Token
                  {tokenSaved && (
                    <span style={{ marginLeft:8, fontSize:11, padding:'1px 7px', borderRadius:4,
                      background:'#d1fae5', color:'#065f46' }}>сохранён ✓</span>
                  )}
                </label>
                <div style={{ position:'relative' }}>
                  <input
                    type={showToken ? 'text' : 'password'}
                    value={config.telegram_bot_token || ''}
                    onChange={e => f('telegram_bot_token', e.target.value)}
                    placeholder={tokenSaved ? 'Токен сохранён (введи новый чтобы изменить)' : '1234567890:ABCdefGHI...'}
                    style={{ ...inputStyle, paddingRight:42,
                      borderColor: tokenSaved ? '#6ee7b7' : 'var(--border)' }}
                  />
                  <button onClick={() => setShowToken(p=>!p)}
                    style={{ position:'absolute', right:10, top:'50%', transform:'translateY(-50%)',
                      background:'none', border:'none', cursor:'pointer', fontSize:16, color:'var(--muted)', padding:0 }}>
                    {showToken ? '🙈' : '👁'}
                  </button>
                </div>
                <p style={{ fontSize:11, color:'var(--muted)', marginTop:3 }}>
                  Формат: <code>1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ</code>
                </p>
              </div>

              <div>
                <label style={{ fontSize:12, color:'var(--muted)', display:'block', marginBottom:4 }}>Chat ID сына</label>
                <input
                  type="text"
                  value={config.telegram_chat_id || ''}
                  onChange={e => f('telegram_chat_id', e.target.value)}
                  placeholder="например: 987654321"
                  style={inputStyle}
                />
                <p style={{ fontSize:11, color:'var(--muted)', marginTop:3 }}>
                  Узнать через <a href="https://t.me/userinfobot" target="_blank" rel="noreferrer">@userinfobot</a> — числовой ID
                </p>
              </div>
            </div>

            {/* Test result */}
            {testMsg && (
              <div style={{ marginTop:12, padding:'10px 14px', borderRadius:8, fontSize:13,
                background: testMsg.type==='ok' ? '#ecfdf5' : '#fef2f2',
                color: testMsg.type==='ok' ? '#065f46' : '#991b1b',
                border: `1px solid ${testMsg.type==='ok' ? '#a7f3d0' : '#fca5a5'}` }}>
                {testMsg.type==='ok' ? '✅ ' : '❌ '}{testMsg.text}
              </div>
            )}

            <button
              onClick={testBot}
              disabled={testing || (!config.telegram_bot_token && !tokenSaved) || !config.telegram_chat_id}
              style={{ marginTop:14, padding:'9px 20px', border:'1px solid var(--border)',
                borderRadius:8, background:'#fff', fontSize:13, cursor:'pointer',
                opacity: (testing || (!config.telegram_bot_token && !tokenSaved) || !config.telegram_chat_id) ? 0.5 : 1 }}>
              {testing ? '⏳ Отправка...' : '📨 Отправить тестовое сообщение'}
            </button>
            <p style={{ fontSize:11, color:'var(--muted)', marginTop:6 }}>
              Сначала сохрани настройки, потом нажми тест
            </p>
          </section>

          {/* Save result */}
          {msg && (
            <div style={{ padding:'10px 14px', borderRadius:8, fontSize:13,
              background: msg.type==='ok' ? '#ecfdf5' : '#fef2f2',
              color: msg.type==='ok' ? '#065f46' : '#991b1b',
              border: `1px solid ${msg.type==='ok' ? '#a7f3d0' : '#fca5a5'}` }}>
              {msg.type==='ok' ? '✅ ' : '❌ '}{msg.text}
            </div>
          )}

          <button
            onClick={save}
            disabled={saving}
            style={{ padding:'11px', background:'var(--primary)', color:'#fff',
              border:'none', borderRadius:8, fontWeight:600, fontSize:15, cursor:'pointer',
              opacity: saving ? 0.7 : 1 }}>
            {saving ? '⏳ Сохранение...' : '💾 Сохранить настройки'}
          </button>

        </div>
      )}
    </div>
  )
}
