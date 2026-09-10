import { useEffect, useState } from 'react'
import { api } from '../api/client'
import LeagueSetup from './LeagueSetup'

export default function LeagueSelect({ onSelected }) {
  const [leagues, setLeagues] = useState(null)
  const [creating, setCreating] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .listLeagues()
      .then(setLeagues)
      .catch((err) => setError(err.message))
  }, [])

  if (creating || (leagues && leagues.length === 0)) {
    return <LeagueSetup onCreated={onSelected} />
  }

  if (!leagues) {
    return <p className="text-sm text-slate-500">Caricamento leghe...</p>
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">Le tue leghe</h2>
        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
        <div className="space-y-2">
          {leagues.map((l) => (
            <button
              key={l.id}
              onClick={() => onSelected(l)}
              className="block w-full rounded-md border border-slate-200 px-4 py-3 text-left hover:border-blue-400 hover:bg-blue-50"
            >
              <p className="font-medium text-slate-800">{l.name}</p>
              <p className="text-xs text-slate-500">
                {l.ruleset === 'mantra' ? 'Mantra' : 'Classic'} · Budget {l.budget_total} crediti ·{' '}
                {l.managers.length} manager
                {l.defense_modifier && ' · Modificatore difesa'}
              </p>
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={() => setCreating(true)}
        className="w-full rounded-md bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700"
      >
        + Crea nuova lega
      </button>
    </div>
  )
}
