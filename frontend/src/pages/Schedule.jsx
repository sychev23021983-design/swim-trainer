import { useState, useEffect } from 'react'
import { api } from '../api.js'

const DAYS = [
  { code:'mon',label:'Пн' }, { code:'tue',label:'Вт' }, { code:'wed',label:'Ср' },
  { code:'thu',label:'Чт' }, { code:'fri',label:'Пт' }, { code:'sat',label:'Сб' },
  { code:'sun',label:'Вс' }
]

export default function Schedule() {
  const [schedules, setSchedules]   = useState([])
  const [exercises, setExercises]   = useState([])
  const [loading, setLoading]       = useState(true)
  const [showAdd, setShowAdd]       = useState(false)
  const [form, setForm]             = useState({ exercise_id:'', days:['mon','wed','fri'], notify_time:'17:00' })

  const load = async () => {
    setLoading(true)
    try {
      const [s, e] = await Promise.all([api.schedules(), api.exercises(null, 1)])
      setSchedules(s); setExercises(e)
    } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const toggleDay = d => setForm(p => ({
    ...p, days: p.days.includes(d) ? p.days.filter(x=>x!==d) : [...p.days, d]
  }))

  const add = async () => {
    if (!form.exercise_id) return
    await api.createSchedule({ ...form, exercise_id: parseInt(form.exercise_id) })
    setShowAdd(false); setForm({ exercise_id:'', days:['mon','wed','fri'], notify_time:'17:00' })
    await load()
  }
  const del = async id => { if (!confirm('Удалить?')) return; await api.deleteSchedule(id); await load() }

  return (
    <div>
      <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:20 }}>
        <h1 style={{ fontSize:20,fontWeight:700 }}>Расписание</h1>
        <button onClick={() => setShowAdd(!showAdd)}
          style={{ padding:'8px 18px',background:'var(--primary)',color:'#fff',border:'none',borderRadius:8,fontWeight:600 }}>
          + Добавить
        </button>
      </div>

      {showAdd && (
        <div style={{ background:'#fff',border:'1px solid var(--border)',borderRadius:12,
          padding:'1.25rem',marginBottom:20 }}>
          <h3 style={{ fontSize:15,fontWeight:600,marginBottom:14 }}>Новое расписание</h3>
          <div style={{ display:'flex',flexDirection:'column',gap:12 }}>
            <div>
              <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Упражнение</label>
              <select value={form.exercise_id} onChange={e => setForm(p=>({...p,exercise_id:e.target.value}))}
                style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }}>
                <option value="">Выберите упражнение</option>
                {exercises.map(e => <option key={e.id} value={e.id}>{e.title}</option>)}
              </select>
            </div>
            <div>
              <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:6 }}>Дни недели</label>
              <div style={{ display:'flex',gap:6,flexWrap:'wrap' }}>
                {DAYS.map(d => (
                  <button key={d.code} onClick={() => toggleDay(d.code)}
                    style={{ padding:'6px 12px',borderRadius:8,border:'1px solid',fontSize:13,
                      borderColor: form.days.includes(d.code) ? 'var(--primary)' : 'var(--border)',
                      background: form.days.includes(d.code) ? 'var(--primary-light)' : '#fff',
                      color: form.days.includes(d.code) ? 'var(--primary)' : 'var(--text)' }}>
                    {d.label}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Время уведомления</label>
              <input type="time" value={form.notify_time} onChange={e=>setForm(p=>({...p,notify_time:e.target.value}))}
                style={{ padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }} />
            </div>
            <div style={{ display:'flex',gap:8 }}>
              <button onClick={add} disabled={!form.exercise_id}
                style={{ padding:'8px 20px',background:'var(--primary)',color:'#fff',border:'none',borderRadius:8,fontWeight:600 }}>
                Сохранить
              </button>
              <button onClick={() => setShowAdd(false)}
                style={{ padding:'8px 16px',border:'1px solid var(--border)',borderRadius:8,background:'#fff' }}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? <p style={{color:'var(--muted)'}}>Загрузка...</p> : (
        <div style={{ display:'flex',flexDirection:'column',gap:10 }}>
          {schedules.length === 0 && (
            <div style={{ textAlign:'center',padding:'3rem',color:'var(--muted)',
              background:'#fff',borderRadius:12,border:'1px solid var(--border)' }}>
              Расписание пустое. Добавьте упражнение!
            </div>
          )}
          {schedules.map(s => (
            <div key={s.id} style={{ background:'#fff',border:'1px solid var(--border)',
              borderRadius:12,padding:'1rem 1.25rem',display:'flex',
              justifyContent:'space-between',alignItems:'center',gap:12,flexWrap:'wrap' }}>
              <div>
                <div style={{ fontWeight:600,fontSize:15,marginBottom:4 }}>{s.title}</div>
                <div style={{ display:'flex',gap:4,flexWrap:'wrap',marginBottom:4 }}>
                  {DAYS.map(d => (
                    <span key={d.code} style={{ fontSize:11,padding:'2px 7px',borderRadius:5,
                      background: s.days.includes(d.code) ? 'var(--primary-light)' : 'var(--bg)',
                      color: s.days.includes(d.code) ? 'var(--primary)' : 'var(--muted)',
                      border: `1px solid ${s.days.includes(d.code) ? 'var(--primary)' : 'var(--border)'}` }}>
                      {d.label}
                    </span>
                  ))}
                </div>
                <div style={{ fontSize:12,color:'var(--muted)' }}>
                  Уведомление: {s.notify_time} · Награда: ${s.reward_usd?.toFixed(2)}
                </div>
              </div>
              <button onClick={() => del(s.id)}
                style={{ padding:'6px 14px',border:'1px solid #fee2e2',borderRadius:7,
                  fontSize:13,background:'#fff',color:'var(--danger)',flexShrink:0 }}>
                Удалить
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
