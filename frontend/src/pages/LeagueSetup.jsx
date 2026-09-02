import { useState } from 'react'
import { api } from '../api/client'

const DEFAULT_ROSTER = { P: 3, D: 8, C: 8, A: 6 }

export default function LeagueSetup({ onCreated }) {
  const [name, setName] = useState('')
  const [ruleset, setRuleset] = useState('classic')
  const [budgetTotal, setBudgetTotal] = useState(500)
  const [roster, setRoster] = useState(DEFAULT_ROSTER)
  const [managers, setManagers] = useState([
    { name: '', is_me: true },
    { name: '', is_me: false },
  ])
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  function updateManager(index, field, value) {
    setManagers((prev) =>
      prev.map((m, i) => (i === index ? { ...m, [field]: value } : field === 'is_me' ? { ...m, is_me: false } : m))
    )
  }

  function addManager() {
    setManagers((prev) => [...prev, { name: '', is_me: false }])
  }

  function removeManager(index) {
    setManagers((prev) => prev.filter((_, i) => i !== index))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')

    const cleanManagers = managers.map((m) => ({ ...m, name: m.name.trim() })).filter((m) => m.name)
    if (!name.trim()) {
      setError('Inserisci il nome della lega')
      return
    }
    if (cleanManagers.length < 2) {
      setError('Servono almeno 2 manager')
      return
    }
    if (!cleanManagers.some((m) => m.is_me)) {
      setError('Segna quale squadra è la tua ("Io")')
      return
    }

    setSubmitting(true)
    try {
      const league = await api.createLeague({
        name: name.trim(),
        ruleset,
        budget_total: Number(budgetTotal),
        roster_config: roster,
        managers: cleanManagers,
      })
      onCreated(league)
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 rounded-lg bg-white p-4 shadow-sm sm:p-6">
      <h2 className="text-lg font-semibold text-slate-800">Crea la tua lega</h2>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">Nome lega</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          placeholder="Lega tra amici"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Regolamento</label>
          <select
            value={ruleset}
            onChange={(e) => setRuleset(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            <option value="classic">Classic</option>
            <option value="mantra">Mantra</option>
          </select>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-slate-700">Budget per squadra</label>
          <input
            type="number"
            min={1}
            value={budgetTotal}
            onChange={(e) => setBudgetTotal(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
      </div>

      <div>
        <label className="mb-1 block text-sm font-medium text-slate-700">Slot per ruolo</label>
        <div className="grid grid-cols-4 gap-2">
          {Object.entries(roster).map(([role, count]) => (
            <div key={role}>
              <span className="mb-1 block text-center text-xs text-slate-500">{role}</span>
              <input
                type="number"
                min={0}
                value={count}
                onChange={(e) => setRoster((prev) => ({ ...prev, [role]: Number(e.target.value) }))}
                className="w-full rounded-md border border-slate-300 px-2 py-2 text-center text-sm"
              />
            </div>
          ))}
        </div>
      </div>

      <div>
        <label className="mb-2 block text-sm font-medium text-slate-700">Manager della lega</label>
        <div className="space-y-2">
          {managers.map((m, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                value={m.name}
                onChange={(e) => updateManager(i, 'name', e.target.value)}
                placeholder={`Manager ${i + 1}`}
                className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
              />
              <label className="flex items-center gap-1 text-xs text-slate-600 whitespace-nowrap">
                <input type="radio" name="is_me" checked={m.is_me} onChange={() => updateManager(i, 'is_me', true)} />
                Io
              </label>
              {managers.length > 2 && (
                <button type="button" onClick={() => removeManager(i)} className="text-slate-400 hover:text-red-500">
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>
        <button type="button" onClick={addManager} className="mt-2 text-sm text-blue-600 hover:underline">
          + Aggiungi manager
        </button>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-md bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {submitting ? 'Creazione...' : 'Crea lega e continua'}
      </button>
    </form>
  )
}
