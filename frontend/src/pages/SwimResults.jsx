import { useState, useEffect } from 'react'
import { api } from '../api.js'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
         Legend, ResponsiveContainer } from 'recharts'
import dayjs from 'dayjs'

const STYLES = [
  { value:'freestyle',  label:'Кроль',       color:'#3b82f6', emoji:'🏊' },
  { value:'backstroke', label:'На спине',     color:'#14b8a6', emoji:'🔄' },
  { value:'breaststroke',label:'Брасс',       color:'#f59e0b', emoji:'🐸' },
  { value:'butterfly',  label:'Баттерфляй',   color:'#8b5cf6', emoji:'🦋' },
]

export default function SwimResults() {
  const [results, setResults]     = useState({})
  const [loading, setLoading]     = useState(true)
  const [showAdd, setShowAdd]     = useState(false)
  const [form, setForm]           = useState({ style:'freestyle', distance_m:100, time_sec:'', note:'' })
  const [activeStyle, setActive]  = useState('freestyle')

  const load = async () => {
    setLoading(true)
    try { setResults(await api.swimProgress()) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const formatTime = sec => {
    const m = Math.floor(sec/60), s = (sec%60).toFixed(1)
    return m > 0 ? `${m}:${s.padStart(4,'0')}` : `${s}с`
  }

  const add = async () => {
    if (!form.time_sec) return
    await api.addSwimResult({ ...form, distance_m: parseInt(form.distance_m),
      time_sec: parseFloat(form.time_sec) })
    setShowAdd(false); setForm({ style:'freestyle', distance_m:100, time_sec:'', note:'' })
    await load()
  }

  const del = async id => {
    if (!confirm('Удалить результат?')) return
    await api.deleteSwimResult(id); await load()
  }

  const styleData = results[activeStyle] || []
  const chartData = styleData.map(r => ({
    date: dayjs(r.recorded_at).format('DD.MM'),
    'Пейс (сек/100м)': r.pace_per_100m,
    'Время (сек)': parseFloat(r.time_sec.toFixed(1))
  }))
  const activeInfo = STYLES.find(s => s.value === activeStyle)

  return (
    <div>
      <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:20 }}>
        <h1 style={{ fontSize:20,fontWeight:700 }}>Результаты заплывов</h1>
        <button onClick={() => setShowAdd(!showAdd)}
          style={{ padding:'8px 18px',background:'var(--primary)',color:'#fff',border:'none',borderRadius:8,fontWeight:600 }}>
          + Добавить результат
        </button>
      </div>

      {showAdd && (
        <div style={{ background:'#fff',border:'1px solid var(--border)',borderRadius:12,
          padding:'1.25rem',marginBottom:20 }}>
          <h3 style={{ fontSize:15,fontWeight:600,marginBottom:14 }}>Новый результат</h3>
          <div style={{ display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))',gap:10,marginBottom:12 }}>
            <div>
              <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Стиль</label>
              <select value={form.style} onChange={e=>setForm(p=>({...p,style:e.target.value}))}
                style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }}>
                {STYLES.map(s=><option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Дистанция (м)</label>
              <select value={form.distance_m} onChange={e=>setForm(p=>({...p,distance_m:e.target.value}))}
                style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }}>
                {[25,50,100,200,400].map(d=><option key={d} value={d}>{d}м</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Время (секунды)</label>
              <input type="number" step="0.1" value={form.time_sec}
                onChange={e=>setForm(p=>({...p,time_sec:e.target.value}))}
                placeholder="напр. 95.5"
                style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }} />
            </div>
            <div>
              <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Заметка</label>
              <input value={form.note} onChange={e=>setForm(p=>({...p,note:e.target.value}))}
                placeholder="необязательно"
                style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }} />
            </div>
          </div>
          <div style={{ display:'flex',gap:8 }}>
            <button onClick={add} disabled={!form.time_sec}
              style={{ padding:'8px 20px',background:'var(--primary)',color:'#fff',border:'none',borderRadius:8,fontWeight:600 }}>
              Сохранить
            </button>
            <button onClick={() => setShowAdd(false)}
              style={{ padding:'8px 16px',border:'1px solid var(--border)',borderRadius:8,background:'#fff' }}>
              Отмена
            </button>
          </div>
        </div>
      )}

      <div style={{ display:'flex',gap:8,marginBottom:20,flexWrap:'wrap' }}>
        {STYLES.map(s => (
          <button key={s.value} onClick={() => setActive(s.value)}
            style={{ padding:'8px 16px',borderRadius:10,border:'1px solid',fontSize:13,
              borderColor: activeStyle===s.value ? s.color : 'var(--border)',
              background: activeStyle===s.value ? s.color+'18' : '#fff',
              color: activeStyle===s.value ? s.color : 'var(--text)',fontWeight:500 }}>
            {s.emoji} {s.label} {results[s.value]?.length ? `(${results[s.value].length})` : ''}
          </button>
        ))}
      </div>

      {loading ? <p style={{color:'var(--muted)'}}>Загрузка...</p> : (
        <>
          {styleData.length === 0 ? (
            <div style={{ textAlign:'center',padding:'2.5rem',color:'var(--muted)',
              background:'#fff',borderRadius:12,border:'1px solid var(--border)' }}>
              Нет результатов для «{activeInfo?.label}». Добавьте первый заплыв!
            </div>
          ) : (
            <>
              {chartData.length >= 2 && (
                <div style={{ background:'#fff',border:'1px solid var(--border)',borderRadius:12,
                  padding:'1.25rem',marginBottom:20 }}>
                  <h2 style={{ fontSize:15,fontWeight:600,marginBottom:14,color:activeInfo?.color }}>
                    {activeInfo?.emoji} Прогресс — {activeInfo?.label}
                  </h2>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="date" tick={{ fontSize:11 }} />
                      <YAxis tick={{ fontSize:11 }} />
                      <Tooltip />
                      <Legend />
                      <Line type="monotone" dataKey="Пейс (сек/100м)"
                        stroke={activeInfo?.color} strokeWidth={2} dot={{ r:4 }} />
                    </LineChart>
                  </ResponsiveContainer>
                  <p style={{ fontSize:12,color:'var(--muted)',marginTop:8 }}>
                    Пейс — время на 100м. Чем ниже — тем быстрее.
                  </p>
                </div>
              )}

              <div style={{ background:'#fff',border:'1px solid var(--border)',borderRadius:12,padding:'1.25rem' }}>
                <h2 style={{ fontSize:15,fontWeight:600,marginBottom:12 }}>Все результаты</h2>
                <div style={{ display:'flex',flexDirection:'column',gap:8 }}>
                  {[...styleData].reverse().map((r,i) => (
                    <div key={r.id} style={{ display:'flex',justifyContent:'space-between',
                      alignItems:'center',padding:'10px 12px',borderRadius:8,
                      background: i===0 ? activeInfo?.color+'10' : 'var(--bg)',
                      border: `1px solid ${i===0 ? activeInfo?.color+'40' : 'var(--border)'}` }}>
                      <div>
                        <span style={{ fontWeight:600,fontSize:14 }}>{formatTime(r.time_sec)}</span>
                        <span style={{ color:'var(--muted)',fontSize:12,marginLeft:8 }}>{r.distance_m}м</span>
                        <span style={{ color:'var(--muted)',fontSize:12,marginLeft:8 }}>
                          пейс: {r.pace_per_100m}с/100м
                        </span>
                        {r.note && <span style={{ color:'var(--muted)',fontSize:12,marginLeft:8 }}>— {r.note}</span>}
                        {i===0 && <span style={{ fontSize:11,marginLeft:8,color:activeInfo?.color,fontWeight:600 }}>Лучший!</span>}
                      </div>
                      <div style={{ display:'flex',gap:8,alignItems:'center' }}>
                        <span style={{ fontSize:12,color:'var(--muted)' }}>{dayjs(r.recorded_at).format('DD.MM.YY')}</span>
                        <button onClick={() => del(r.id)}
                          style={{ fontSize:11,padding:'3px 8px',border:'1px solid #fee2e2',
                            borderRadius:5,background:'#fff',color:'var(--danger)' }}>×</button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
