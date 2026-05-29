import { useState, useEffect } from 'react'
import { api } from '../api.js'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
         BarChart, Bar, ResponsiveContainer } from 'recharts'
import dayjs from 'dayjs'

const CAT_COLORS = { butterfly:'#8b5cf6',freestyle:'#3b82f6',backstroke:'#14b8a6',breaststroke:'#f59e0b',universal:'#10b981' }

export default function Progress() {
  const [data, setData] = useState(null)
  const [completions, setCompletions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([api.progress(), api.completions(30)])
      .then(([p, c]) => { setData(p); setCompletions(c) })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <p style={{color:'var(--muted)'}}>Загрузка...</p>

  const weeklyChart = data?.weekly?.map(d => ({
    day: dayjs(d.day).format('DD.MM'),
    Выполнено: d.count,
    Заработано: parseFloat(d.earned.toFixed(2))
  })) || []

  const catChart = data?.by_category?.map(d => ({
    name: d.category, Раз: d.count, color: CAT_COLORS[d.category]||'#888'
  })) || []

  const total = completions.length
  const totalReward = completions.reduce((s,c) => s + (c.reward_earned||0), 0)

  return (
    <div>
      <h1 style={{ fontSize:20,fontWeight:700,marginBottom:20 }}>Прогресс (30 дней)</h1>

      <div style={{ display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(130px,1fr))',gap:12,marginBottom:28 }}>
        {[
          { label:'Выполнено', value: total, color:'var(--primary)' },
          { label:'Заработано', value:`$${totalReward.toFixed(2)}`, color:'#f59e0b' },
          { label:'Дней активно', value: new Set(completions.map(c=>c.completed_at?.slice(0,10))).size, color:'var(--success)' },
          { label:'Упр. сегодня', value: completions.filter(c=>c.completed_at?.startsWith(dayjs().format('YYYY-MM-DD'))).length, color:'#8b5cf6' },
        ].map(c => (
          <div key={c.label} style={{ background:'#fff',border:'1px solid var(--border)',
            borderRadius:12,padding:'1rem',textAlign:'center' }}>
            <div style={{ fontSize:24,fontWeight:700,color:c.color }}>{c.value}</div>
            <div style={{ fontSize:12,color:'var(--muted)',marginTop:2 }}>{c.label}</div>
          </div>
        ))}
      </div>

      {weeklyChart.length > 0 && (
        <div style={{ background:'#fff',border:'1px solid var(--border)',borderRadius:12,padding:'1.25rem',marginBottom:20 }}>
          <h2 style={{ fontSize:15,fontWeight:600,marginBottom:14 }}>Активность по дням</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={weeklyChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="day" tick={{ fontSize:11 }} />
              <YAxis tick={{ fontSize:11 }} />
              <Tooltip />
              <Bar dataKey="Выполнено" fill="#3b82f6" radius={[4,4,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {catChart.length > 0 && (
        <div style={{ background:'#fff',border:'1px solid var(--border)',borderRadius:12,padding:'1.25rem',marginBottom:20 }}>
          <h2 style={{ fontSize:15,fontWeight:600,marginBottom:14 }}>По категориям</h2>
          <div style={{ display:'flex',gap:8,flexWrap:'wrap' }}>
            {catChart.map(c => (
              <div key={c.name} style={{ background:'var(--bg)',borderRadius:10,
                padding:'10px 16px',textAlign:'center',minWidth:100 }}>
                <div style={{ fontSize:20,fontWeight:700,color:c.color }}>{c.Раз}</div>
                <div style={{ fontSize:11,color:'var(--muted)' }}>{c.name}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div style={{ background:'#fff',border:'1px solid var(--border)',borderRadius:12,padding:'1.25rem' }}>
        <h2 style={{ fontSize:15,fontWeight:600,marginBottom:14 }}>История (последние 20)</h2>
        {completions.slice(0,20).map(c => (
          <div key={c.id} style={{ display:'flex',justifyContent:'space-between',
            padding:'8px 0',borderBottom:'1px solid var(--border)',fontSize:13 }}>
            <div>
              <span style={{ fontWeight:500 }}>{c.title}</span>
              <span style={{ color:'var(--muted)',marginLeft:8 }}>{c.category}</span>
              {c.value_done && <span style={{ color:'var(--muted)',marginLeft:8 }}>{c.value_done} повт.</span>}
            </div>
            <div style={{ display:'flex',gap:10,alignItems:'center',color:'var(--muted)' }}>
              <span style={{ color:'var(--success)',fontWeight:600 }}>+${c.reward_earned?.toFixed(2)}</span>
              <span>{dayjs(c.completed_at).format('DD.MM HH:mm')}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
