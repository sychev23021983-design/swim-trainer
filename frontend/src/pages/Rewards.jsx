import { useState, useEffect } from 'react'
import { api } from '../api.js'
import dayjs from 'dayjs'

export default function Rewards() {
  const [summary, setSummary] = useState(null)
  const [rewards, setRewards] = useState([])
  const [loading, setLoading] = useState(true)

  const load = async () => {
    setLoading(true)
    try {
      const [s, r] = await Promise.all([api.rewardsSummary(), api.rewards()])
      setSummary(s); setRewards(r)
    } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [])

  const pay = async id => {
    await api.markPaid(id); await load()
  }
  const payAll = async () => {
    if (!confirm('Отметить все неоплаченные как выплаченные?')) return
    const unpaid = rewards.filter(r => !r.paid)
    for (const r of unpaid) await api.markPaid(r.id)
    await load()
  }

  const unpaid = rewards.filter(r => !r.paid)
  const unpaidSum = unpaid.reduce((s,r) => s + r.amount_usd, 0)

  return (
    <div>
      <h1 style={{ fontSize:20,fontWeight:700,marginBottom:20 }}>Награды</h1>

      {summary && (
        <div style={{ display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(140px,1fr))',
          gap:12,marginBottom:28 }}>
          {[
            { label:'Баланс к выплате', value:`$${summary.balance.toFixed(2)}`, color:'#10b981', big:true },
            { label:'Заработано всего', value:`$${summary.total_earned.toFixed(2)}`, color:'#3b82f6' },
            { label:'Выплачено',        value:`$${summary.total_paid.toFixed(2)}`,  color:'#8b5cf6' },
            { label:'Серия дней',       value:`${summary.streak_days}`,             color:'#f59e0b' },
          ].map(c => (
            <div key={c.label} style={{ background:'#fff',border:`1px solid ${c.big?'#a7f3d0':'var(--border)'}`,
              borderRadius:12,padding:'1rem',textAlign:'center',
              background: c.big ? 'var(--success-light)' : '#fff' }}>
              <div style={{ fontSize: c.big?26:20, fontWeight:700,color:c.color }}>{c.value}</div>
              <div style={{ fontSize:12,color:'var(--muted)',marginTop:2 }}>{c.label}</div>
            </div>
          ))}
        </div>
      )}

      {unpaid.length > 0 && (
        <div style={{ background:'var(--warning-light)',border:'1px solid #fde68a',
          borderRadius:12,padding:'1rem 1.25rem',marginBottom:20,
          display:'flex',justifyContent:'space-between',alignItems:'center',flexWrap:'wrap',gap:10 }}>
          <div>
            <div style={{ fontWeight:600,fontSize:15 }}>К выплате: ${unpaidSum.toFixed(2)}</div>
            <div style={{ fontSize:13,color:'var(--muted)' }}>{unpaid.length} невыплаченных</div>
          </div>
          <button onClick={payAll}
            style={{ padding:'8px 20px',background:'#f59e0b',color:'#fff',border:'none',
              borderRadius:8,fontWeight:600,fontSize:14 }}>
            Выплатить всё
          </button>
        </div>
      )}

      <div style={{ background:'#fff',border:'1px solid var(--border)',borderRadius:12,padding:'1.25rem' }}>
        <h2 style={{ fontSize:15,fontWeight:600,marginBottom:14 }}>История наград</h2>
        {loading ? <p style={{color:'var(--muted)'}}>Загрузка...</p> : (
          <div style={{ display:'flex',flexDirection:'column',gap:8 }}>
            {rewards.length === 0 && (
              <p style={{ color:'var(--muted)',textAlign:'center',padding:'2rem' }}>
                Пока нет выполненных заданий
              </p>
            )}
            {rewards.map(r => (
              <div key={r.id} style={{ display:'flex',justifyContent:'space-between',
                alignItems:'center',padding:'10px 12px',borderRadius:8,
                background: r.paid ? 'var(--bg)' : 'var(--warning-light)',
                border: `1px solid ${r.paid ? 'var(--border)' : '#fde68a'}` }}>
                <div>
                  <span style={{ fontWeight:600,fontSize:14,
                    color: r.paid ? 'var(--muted)' : 'var(--text)' }}>
                    +${r.amount_usd.toFixed(2)}
                  </span>
                  <span style={{ color:'var(--muted)',fontSize:12,marginLeft:10 }}>{r.reason}</span>
                </div>
                <div style={{ display:'flex',gap:8,alignItems:'center' }}>
                  <span style={{ fontSize:11,color:'var(--muted)' }}>
                    {dayjs(r.earned_at).format('DD.MM HH:mm')}
                  </span>
                  {r.paid ? (
                    <span style={{ fontSize:11,padding:'2px 8px',borderRadius:5,
                      background:'#d1fae5',color:'var(--success)' }}>выплачено</span>
                  ) : (
                    <button onClick={() => pay(r.id)}
                      style={{ fontSize:11,padding:'4px 10px',border:'1px solid #f59e0b',
                        borderRadius:5,background:'#fffbeb',color:'#92400e',cursor:'pointer' }}>
                      Выплатить
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
