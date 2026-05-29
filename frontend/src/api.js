const BASE = '/api'
let _token = localStorage.getItem('swim_token') || ''

export const setToken = t => { _token = t; localStorage.setItem('swim_token', t) }
export const clearToken = () => { _token = ''; localStorage.removeItem('swim_token') }
export const getToken = () => _token

const headers = () => ({
  'Content-Type': 'application/json',
  ...(_token ? { Authorization: `Bearer ${_token}` } : {})
})

const req = async (method, path, body) => {
  const r = await fetch(BASE + path, { method, headers: headers(),
    body: body ? JSON.stringify(body) : undefined })
  if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.detail || r.statusText) }
  return r.json()
}

export const api = {
  login:          pwd => req('POST', '/auth/login', { password: pwd }),
  me:             ()  => req('GET', '/auth/me'),
  health:         ()  => req('GET', '/health'),

  exercises:      (cat, active) => req('GET', `/exercises${cat?`?category=${cat}`:''}${active!=null?`${cat?'&':'?'}active=${active}`:''}` ),
  exercise:       id  => req('GET', `/exercises/${id}`),
  createExercise: ex  => req('POST', '/exercises', ex),
  updateExercise: (id,ex) => req('PUT', `/exercises/${id}`, ex),
  deleteExercise: id  => req('DELETE', `/exercises/${id}`),

  schedules:      ()  => req('GET', '/schedules'),
  createSchedule: s   => req('POST', '/schedules', s),
  deleteSchedule: id  => req('DELETE', `/schedules/${id}`),

  today:          ()  => req('GET', '/today'),
  complete:       c   => req('POST', '/completions', c),
  completions:    d   => req('GET', `/completions?days=${d||30}`),

  swimResults:    style => req('GET', `/swim-results${style?`?style=${style}`:''}` ),
  addSwimResult:  r   => req('POST', '/swim-results', r),
  deleteSwimResult: id => req('DELETE', `/swim-results/${id}`),

  rewardsSummary: ()  => req('GET', '/rewards/summary'),
  rewards:        ()  => req('GET', '/rewards'),
  markPaid:       id  => req('POST', `/rewards/${id}/pay`),

  progress:       ()  => req('GET', '/stats/progress'),
  swimProgress:   ()  => req('GET', '/stats/swim-progress'),

  getSettings:    ()  => req('GET', '/settings'),
  saveSettings:   s   => req('POST', '/settings', s),
  testTelegram:   ()  => req('POST', '/settings/test-telegram'),

  sendExercise:   id => req('POST', `/exercises/${id}/send-telegram`),
  uploadExerciseImage: async (id, file, type='demo') => {
    const fd = new FormData()
    fd.append('file', file)
    const r = await fetch(`/api/exercises/${id}/upload-image?image_type=${type}`,
      { method: 'POST', headers: _token ? { Authorization: `Bearer ${_token}` } : {}, body: fd })
    if (!r.ok) throw new Error('Upload failed')
    return r.json()
  },

  upload: async (file) => {
    const fd = new FormData(); fd.append('file', file)
    const r = await fetch(BASE+'/upload', { method:'POST',
      headers: _token ? { Authorization:`Bearer ${_token}` } : {}, body: fd })
    if (!r.ok) throw new Error('Upload failed')
    return r.json()
  }
}
