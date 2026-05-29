import { useState, useEffect } from 'react'
import { api } from '../api.js'

const CATS = [
  { value: '',             label: 'Все' },
  { value: 'butterfly',   label: 'Баттерфляй' },
  { value: 'freestyle',   label: 'Кроль' },
  { value: 'backstroke',  label: 'На спине' },
  { value: 'breaststroke',label: 'Брасс' },
  { value: 'universal',   label: 'Универсальные' },
]
const CAT_COLORS = { butterfly:'#8b5cf6',freestyle:'#3b82f6',backstroke:'#14b8a6',breaststroke:'#f59e0b',universal:'#10b981' }
const EMPTY = { title:'',category:'butterfly',sub_category:'kick',difficulty:1,sets:3,reps:10,
  duration_sec:'',rest_sec:45,reward_usd:0.25,input_type:'reps',
  muscles_primary:[],muscles_secondary:[],muscles_stabilizer:[],
  swim_benefit:'',instructions:'',tips:'',active:true }

export default function Exercises() {
  const [exercises, setExercises] = useState([])
  const [cat, setCat] = useState('')
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState(null)
  const [form, setForm] = useState(EMPTY)
  const [saving, setSaving] = useState(false)

  const load = async () => {
    setLoading(true)
    try { setExercises(await api.exercises(cat||null)) } finally { setLoading(false) }
  }
  useEffect(() => { load() }, [cat])

  const openNew = () => { setForm({...EMPTY}); setModal('new') }
  const openEdit = ex => {
    setForm({ ...ex, muscles_primary: ex.muscles_primary||[],
      muscles_secondary: ex.muscles_secondary||[], muscles_stabilizer: ex.muscles_stabilizer||[] })
    setModal('edit')
  }

  const save = async () => {
    setSaving(true)
    try {
      const payload = { ...form,
        reps: form.reps ? parseInt(form.reps) : null,
        duration_sec: form.duration_sec ? parseInt(form.duration_sec) : null,
        sets: parseInt(form.sets), rest_sec: parseInt(form.rest_sec),
        difficulty: parseInt(form.difficulty), reward_usd: parseFloat(form.reward_usd),
        muscles_primary: typeof form.muscles_primary === 'string'
          ? form.muscles_primary.split(',').map(s=>s.trim()).filter(Boolean)
          : form.muscles_primary,
        muscles_secondary: typeof form.muscles_secondary === 'string'
          ? form.muscles_secondary.split(',').map(s=>s.trim()).filter(Boolean)
          : form.muscles_secondary,
        muscles_stabilizer: typeof form.muscles_stabilizer === 'string'
          ? form.muscles_stabilizer.split(',').map(s=>s.trim()).filter(Boolean)
          : form.muscles_stabilizer,
      }
      if (modal === 'new') await api.createExercise(payload)
      else await api.updateExercise(form.id, payload)
      setModal(null); await load()
    } finally { setSaving(false) }
  }

  const del = async (id) => {
    if (!confirm('Удалить упражнение?')) return
    await api.deleteExercise(id); await load()
  }

  const f = (k,v) => setForm(p => ({...p, [k]: v}))
  const inp = (k, type='text') => (
    <input type={type} value={form[k]??''} onChange={e=>f(k,e.target.value)}
      style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }} />
  )

  return (
    <div>
      <div style={{ display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:20,flexWrap:'wrap',gap:10 }}>
        <h1 style={{ fontSize:20,fontWeight:700 }}>Упражнения</h1>
        <button onClick={openNew}
          style={{ padding:'8px 18px',background:'var(--primary)',color:'#fff',border:'none',borderRadius:8,fontWeight:600 }}>
          + Добавить
        </button>
      </div>

      <div style={{ display:'flex',gap:8,marginBottom:20,flexWrap:'wrap' }}>
        {CATS.map(c => (
          <button key={c.value} onClick={() => setCat(c.value)}
            style={{ padding:'6px 14px',borderRadius:20,border:'1px solid var(--border)',fontSize:13,
              background: cat===c.value ? 'var(--primary)' : '#fff',
              color: cat===c.value ? '#fff' : 'var(--text)' }}>
            {c.label}
          </button>
        ))}
      </div>

      {loading ? <p style={{color:'var(--muted)'}}>Загрузка...</p> : (
        <div style={{ display:'flex',flexDirection:'column',gap:10 }}>
          {exercises.length === 0 && (
            <div style={{ textAlign:'center',padding:'3rem',color:'var(--muted)',
              background:'#fff',borderRadius:12,border:'1px solid var(--border)' }}>
              Упражнений нет. Нажмите «+ Добавить»
            </div>
          )}
          {exercises.map(ex => {
            const color = CAT_COLORS[ex.category] || '#888'
            return (
              <div key={ex.id} style={{ background:'#fff',border:'1px solid var(--border)',
                borderRadius:12,padding:'1rem 1.25rem',borderLeft:`4px solid ${color}`,
                opacity: ex.active ? 1 : 0.55 }}>
                <div style={{ display:'flex',justifyContent:'space-between',alignItems:'flex-start',gap:8 }}>
                  <div>
                    <div style={{ display:'flex',gap:6,marginBottom:5,flexWrap:'wrap' }}>
                      <span style={{ fontSize:11,padding:'2px 8px',borderRadius:5,
                        background:color+'18',color:color,fontWeight:600 }}>
                        {CATS.find(c=>c.value===ex.category)?.label||ex.category}
                      </span>
                      <span style={{ fontSize:11,padding:'2px 8px',borderRadius:5,
                        background:'var(--bg)',color:'var(--muted)',border:'1px solid var(--border)' }}>
                        {ex.sub_category}
                      </span>
                      {!ex.active && <span style={{ fontSize:11,padding:'2px 8px',borderRadius:5,
                        background:'#fee2e2',color:'var(--danger)' }}>неактивно</span>}
                    </div>
                    <h3 style={{ fontSize:15,fontWeight:600,marginBottom:3 }}>{ex.title}</h3>
                    <p style={{ fontSize:13,color:'var(--muted)' }}>
                      {ex.sets} подх. {ex.reps ? `× ${ex.reps} повт.` : ''}{ex.duration_sec ? ` × ${ex.duration_sec}сек` : ''} ·
                      отдых {ex.rest_sec}сек · сложность {'★'.repeat(ex.difficulty)+'☆'.repeat(3-ex.difficulty)}
                    </p>
                    {ex.swim_benefit && <p style={{ fontSize:12,color:color,marginTop:3 }}>🏊 {ex.swim_benefit}</p>}
                    {ex.muscles_primary?.length > 0 && (
                      <p style={{ fontSize:12,color:'var(--muted)',marginTop:2 }}>
                        Мышцы: {ex.muscles_primary.join(', ')}
                      </p>
                    )}
                  </div>
                  <div style={{ textAlign:'right',flexShrink:0 }}>
                    <div style={{ fontSize:16,fontWeight:700,color:'#f59e0b',marginBottom:8 }}>
                      ${ex.reward_usd.toFixed(2)}
                    </div>
                    <div style={{ display:'flex',gap:6 }}>
                      <button onClick={() => openEdit(ex)}
                        style={{ padding:'5px 12px',border:'1px solid var(--border)',borderRadius:6,fontSize:12,background:'#fff' }}>
                        Изменить
                      </button>
                      <button onClick={() => del(ex.id)}
                        style={{ padding:'5px 12px',border:'1px solid #fee2e2',borderRadius:6,fontSize:12,
                          background:'#fff',color:'var(--danger)' }}>
                        Удалить
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {modal && (
        <div style={{ position:'fixed',inset:0,background:'rgba(0,0,0,0.4)',
          display:'flex',alignItems:'center',justifyContent:'center',zIndex:100,padding:'1rem' }}>
          <div style={{ background:'#fff',borderRadius:16,padding:'1.5rem',width:'100%',maxWidth:560,
            maxHeight:'90vh',overflowY:'auto' }}>
            <h2 style={{ fontSize:17,fontWeight:700,marginBottom:20 }}>
              {modal==='new' ? 'Новое упражнение' : 'Редактировать'}
            </h2>
            <div style={{ display:'flex',flexDirection:'column',gap:12 }}>
              <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Название *</label>{inp('title')}</div>
              <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr',gap:10 }}>
                <div>
                  <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Категория</label>
                  <select value={form.category} onChange={e=>f('category',e.target.value)}
                    style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }}>
                    {CATS.filter(c=>c.value).map(c=><option key={c.value} value={c.value}>{c.label}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Подкатегория</label>
                  <select value={form.sub_category} onChange={e=>f('sub_category',e.target.value)}
                    style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }}>
                    {['kick','pull','arms','core','strength','general'].map(s=><option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <div style={{ display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:10 }}>
                <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Подходы</label>{inp('sets','number')}</div>
                <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Повторения</label>{inp('reps','number')}</div>
                <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Сек (если время)</label>{inp('duration_sec','number')}</div>
                <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Отдых (сек)</label>{inp('rest_sec','number')}</div>
              </div>
              <div style={{ display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:10 }}>
                <div>
                  <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Сложность</label>
                  <select value={form.difficulty} onChange={e=>f('difficulty',e.target.value)}
                    style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }}>
                    <option value={1}>★ Легко</option><option value={2}>★★ Средне</option><option value={3}>★★★ Сложно</option>
                  </select>
                </div>
                <div>
                  <label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Тип ввода</label>
                  <select value={form.input_type} onChange={e=>f('input_type',e.target.value)}
                    style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }}>
                    <option value="done">Выполнено</option><option value="reps">Кол-во</option><option value="time_sec">Время</option>
                  </select>
                </div>
                <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Награда ($)</label>{inp('reward_usd','number')}</div>
              </div>
              <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Польза для плавания</label>{inp('swim_benefit')}</div>
              <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Инструкция</label>
                <textarea value={form.instructions} onChange={e=>f('instructions',e.target.value)} rows={2}
                  style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13,resize:'vertical' }} />
              </div>
              <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Советы</label>
                <textarea value={form.tips} onChange={e=>f('tips',e.target.value)} rows={2}
                  style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13,resize:'vertical' }} />
              </div>
              <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Основные мышцы (через запятую)</label>
                <input value={Array.isArray(form.muscles_primary)?form.muscles_primary.join(', '):form.muscles_primary}
                  onChange={e=>f('muscles_primary',e.target.value)}
                  style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }} />
              </div>
              <div><label style={{ fontSize:12,color:'var(--muted)',display:'block',marginBottom:4 }}>Вспомогательные мышцы</label>
                <input value={Array.isArray(form.muscles_secondary)?form.muscles_secondary.join(', '):form.muscles_secondary}
                  onChange={e=>f('muscles_secondary',e.target.value)}
                  style={{ width:'100%',padding:'8px 10px',border:'1px solid var(--border)',borderRadius:7,fontSize:13 }} />
              </div>
              <div style={{ display:'flex',alignItems:'center',gap:8 }}>
                <input type="checkbox" id="active_cb" checked={form.active} onChange={e=>f('active',e.target.checked)} />
                <label htmlFor="active_cb" style={{ fontSize:13 }}>Активное упражнение</label>
              </div>
            </div>
            <div style={{ display:'flex',gap:10,marginTop:20 }}>
              <button onClick={save} disabled={saving||!form.title}
                style={{ flex:1,padding:'10px',background:'var(--primary)',color:'#fff',border:'none',borderRadius:8,fontWeight:600 }}>
                {saving ? 'Сохранение...' : 'Сохранить'}
              </button>
              <button onClick={() => setModal(null)}
                style={{ padding:'10px 20px',border:'1px solid var(--border)',borderRadius:8,background:'#fff' }}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
