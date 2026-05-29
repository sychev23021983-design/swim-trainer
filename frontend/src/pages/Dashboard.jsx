import { useState, useEffect } from 'react'
import { api } from '../api.js'
import dayjs from 'dayjs'

const CAT_COLORS = {
  butterfly: '#8b5cf6', freestyle: '#3b82f6', backstroke: '#14b8a6',
  breaststroke: '#f59e0b', universal: '#10b981'
}
const CAT_LABELS = {
  butterfly: 'Баттерфляй', freestyle: 'Кроль', backstroke: 'На спине',
  breaststroke: 'Брасс', universal: 'Универсальные'
}

export default function Dashboard({ childName }) {
  const [tasks, setTasks]     = useState([])
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [completing, setCompleting] = useState({})
  const [repsInput, setRepsInput] = useState({})

  const load = async () => {
    setLoading(true)
    try {
      const [t, s] = await Promise.all([api.today(), api.rewardsSummary()])
      setTasks(t); setSummary(s)
    } finally { setLoading(false) }
  }

  useEffect(() => { load() }, [])

  const complete = async (exId, inputType, value) => {
    setCompleting(p => ({...p, [exId]: true}))
    try {
      await api.complete({ exercise_id: exId, input_type: inputType,
        value_done: value || null, value_target: null })
      await load()
    } finally { setCompleting(p => ({...p, [exId]: false})) }
  }

  const pending = tasks.filter(t => !t.completed_today)
  const done    = tasks.filter(t => t.completed_today)

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
          Привет, {childName}!
        </h1>
        <p style={{ color: 'var(--muted)', fontSize: 14 }}>
          {dayjs().format('dddd, D MMMM YYYY')} · Сегодня {tasks.length} тренировок
        </p>
      </div>

      {summary && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(140px,1fr))',
          gap: 12, marginBottom: 28 }}>
          {[
            { label: 'Баланс', value: `$${summary.balance.toFixed(2)}`, color: '#10b981' },
            { label: 'Заработано', value: `$${summary.total_earned.toFixed(2)}`, color: '#3b82f6' },
            { label: 'Серия', value: `${summary.streak_days} дней`, color: '#f59e0b' },
            { label: 'Выплачено', value: `$${summary.total_paid.toFixed(2)}`, color: '#8b5cf6' },
          ].map(c => (
            <div key={c.label} style={{ background: '#fff', border: '1px solid var(--border)',
              borderRadius: 12, padding: '1rem', textAlign: 'center' }}>
              <div style={{ fontSize: 22, fontWeight: 700, color: c.color }}>{c.value}</div>
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>{c.label}</div>
            </div>
          ))}
        </div>
      )}

      {loading ? <p style={{ color: 'var(--muted)' }}>Загрузка...</p> : (
        <>
          {pending.length > 0 && (
            <section style={{ marginBottom: 28 }}>
              <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>
                Сегодня ({pending.length})
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {pending.map(t => (
                  <TaskCard key={t.id} task={t}
                    completing={completing[t.exercise_id]}
                    repsValue={repsInput[t.exercise_id] || ''}
                    onRepsChange={v => setRepsInput(p => ({...p, [t.exercise_id]: v}))}
                    onComplete={complete} />
                ))}
              </div>
            </section>
          )}

          {done.length > 0 && (
            <section>
              <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12, color: 'var(--success)' }}>
                Выполнено ({done.length})
              </h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                {done.map(t => (
                  <div key={t.id} style={{ background: 'var(--success-light)',
                    border: '1px solid #a7f3d0', borderRadius: 10, padding: '12px 16px',
                    display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ color: 'var(--success)', fontSize: 18 }}>✓</span>
                    <span style={{ fontWeight: 500 }}>{t.title}</span>
                    <span style={{ marginLeft: 'auto', fontSize: 13,
                      color: 'var(--success)', fontWeight: 600 }}>+${t.reward_usd.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </section>
          )}

          {tasks.length === 0 && (
            <div style={{ textAlign: 'center', padding: '3rem',
              color: 'var(--muted)', background: '#fff', borderRadius: 12,
              border: '1px solid var(--border)' }}>
              <div style={{ fontSize: 40, marginBottom: 12 }}>🎉</div>
              <p>На сегодня тренировок нет. Отдыхай!</p>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function TaskCard({ task, completing, repsValue, onRepsChange, onComplete }) {
  const color = CAT_COLORS[task.category] || '#3b82f6'
  const label = CAT_LABELS[task.category] || task.category
  const repsStr = task.reps ? `${task.sets} × ${task.reps} повт.` : `${task.sets} подхода`
  const durStr  = task.duration_sec ? ` · ${task.duration_sec} сек` : ''

  return (
    <div style={{ background: '#fff', border: '1px solid var(--border)', borderRadius: 12,
      padding: '1.25rem', borderLeft: `4px solid ${color}` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 12 }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
            <span style={{ fontSize: 11, padding: '2px 8px', borderRadius: 5,
              background: color + '18', color: color, fontWeight: 600 }}>{label}</span>
            <span style={{ fontSize: 11, color: 'var(--muted)' }}>
              {'★'.repeat(task.difficulty) + '☆'.repeat(3-task.difficulty)}
            </span>
          </div>
          <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{task.title}</h3>
          <p style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 6 }}>
            {repsStr}{durStr} · отдых {task.rest_sec} сек
          </p>
          {task.swim_benefit && (
            <p style={{ fontSize: 12, color: color, background: color+'10',
              borderRadius: 6, padding: '4px 8px', marginBottom: 8 }}>
              🏊 {task.swim_benefit}
            </p>
          )}
          {task.instructions && (
            <p style={{ fontSize: 12, color: 'var(--muted)' }}>{task.instructions}</p>
          )}
        </div>
        <div style={{ textAlign: 'right', flexShrink: 0 }}>
          <div style={{ fontSize: 20, fontWeight: 700, color: '#f59e0b' }}>
            +${task.reward_usd.toFixed(2)}
          </div>
        </div>
      </div>

      <div style={{ marginTop: 14, display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
        {task.input_type === 'done' ? (
          <button onClick={() => onComplete(task.exercise_id, 'done', null)}
            disabled={completing}
            style={{ padding: '8px 20px', background: 'var(--success)', color: '#fff',
              border: 'none', borderRadius: 8, fontWeight: 600, fontSize: 14 }}>
            {completing ? '...' : '✓ Выполнено'}
          </button>
        ) : (
          <>
            <input type="number" value={repsValue} min={0} max={999}
              onChange={e => onRepsChange(e.target.value)}
              placeholder={`из ${task.reps || '?'}`}
              style={{ width: 90, padding: '7px 10px', border: '1px solid var(--border)',
                borderRadius: 8, fontSize: 14 }} />
            <button onClick={() => onComplete(task.exercise_id, 'reps', parseInt(repsValue)||0)}
              disabled={completing || !repsValue}
              style={{ padding: '8px 16px', background: 'var(--success)', color: '#fff',
                border: 'none', borderRadius: 8, fontWeight: 600, fontSize: 14 }}>
              {completing ? '...' : 'Сохранить'}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
