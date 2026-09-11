import { useEffect, useState } from 'react'
import { api } from '../api/client'

function parseStartingEleven(raw) {
  if (!raw) return { note: '', lines: [] }
  const noteMatch = raw.match(/^\(([^)]*)\)\s*:?\s*/)
  const note = noteMatch ? noteMatch[1] : ''
  const rest = (noteMatch ? raw.slice(noteMatch[0].length) : raw).replace(/\.$/, '')
  const lines = rest
    .split(';')
    .map((line) => line.split(',').map((name) => name.trim()).filter(Boolean))
    .filter((line) => line.length > 0)
  return { note, lines }
}

function splitList(raw) {
  if (!raw) return []
  return raw
    .split(',')
    .map((v) => v.trim())
    .filter(Boolean)
}

function TeamCard({ team }) {
  const [expanded, setExpanded] = useState(false)
  const { note, lines } = parseStartingEleven(team.starting_eleven)
  const ballottaggi = team.ballottaggi
    ? team.ballottaggi.split(';').map((b) => b.trim()).filter(Boolean)
    : []
  const penaltyTakers = splitList(team.penalty_takers)
  const freeKickTakers = splitList(team.free_kick_takers)

  return (
    <div className="overflow-hidden rounded-lg bg-white shadow-sm">
      <div className="flex items-center justify-between gap-2 border-b border-slate-100 p-3">
        <div className="flex items-center gap-2">
          {team.team_badge_url && <img src={team.team_badge_url} alt="" className="h-7 w-7 object-contain" />}
          <div>
            <p className="font-semibold text-slate-800">{team.team}</p>
            <p className="text-xs text-slate-500">{team.coach}</p>
          </div>
        </div>
        {team.formation_module && (
          <span className="shrink-0 rounded-full bg-blue-100 px-2.5 py-1 text-xs font-bold text-blue-700">
            {team.formation_module}
          </span>
        )}
      </div>

      <div className="p-3">
        {lines.length > 0 && (
          <div className="mb-3">
            {note && <p className="mb-1.5 text-[11px] uppercase tracking-wide text-slate-400">{note}</p>}
            <div className="space-y-1.5">
              {lines.map((line, i) => (
                <div key={i} className="flex flex-wrap gap-1">
                  {line.map((name) => (
                    <span key={name} className="rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                      {name}
                    </span>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {(penaltyTakers.length > 0 || freeKickTakers.length > 0) && (
          <div className="mb-3 flex flex-wrap gap-3 text-xs">
            {penaltyTakers.length > 0 && (
              <p>
                <span className="font-semibold text-orange-600">⚽ Rigoristi:</span>{' '}
                <span className="text-slate-600">{penaltyTakers.join(' → ')}</span>
              </p>
            )}
            {freeKickTakers.length > 0 && (
              <p>
                <span className="font-semibold text-sky-600">🎯 Punizioni:</span>{' '}
                <span className="text-slate-600">{freeKickTakers.join(' → ')}</span>
              </p>
            )}
          </div>
        )}

        {ballottaggi.length > 0 && (
          <div className="mb-3">
            <p className="mb-1 text-xs font-semibold text-amber-600">Ballottaggi</p>
            <ul className="space-y-0.5 text-xs text-slate-600">
              {ballottaggi.map((b, i) => (
                <li key={i}>{b}</li>
              ))}
            </ul>
          </div>
        )}

        {team.image_url && (
          <button onClick={() => setExpanded((v) => !v)} className="text-xs font-medium text-blue-600 hover:underline">
            {expanded ? 'Nascondi infografica' : 'Mostra infografica'}
          </button>
        )}
        {expanded && team.image_url && (
          <img src={team.image_url} alt={`Formazione ${team.team}`} className="mt-2 w-full rounded-md border border-slate-100" />
        )}
      </div>
    </div>
  )
}

export default function TeamFormations({ league }) {
  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState('')

  async function load() {
    setLoading(true)
    setError('')
    try {
      setTeams(await api.getTeamFormations(league.id))
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [league.id])

  async function handleRefresh() {
    setRefreshing(true)
    setError('')
    try {
      await api.refreshTeamFormations(league.id)
      await load()
    } catch (err) {
      setError(err.message)
    } finally {
      setRefreshing(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-semibold text-slate-800">Probabili formazioni Serie A 2026/27</h2>
            <p className="text-sm text-slate-500">
              Allenatore, modulo, probabile undici, ballottaggi, rigoristi e punizioni per tutte le 20 squadre —
              da Fantacalcio.it.
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="shrink-0 rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {refreshing ? 'Aggiorno...' : 'Aggiorna'}
          </button>
        </div>
        {error && <p className="mt-3 text-sm text-red-600">{error}</p>}
      </div>

      {loading ? (
        <p className="text-sm text-slate-500">Caricamento...</p>
      ) : teams.length === 0 ? (
        <div className="rounded-lg bg-white p-6 text-center text-sm text-slate-500 shadow-sm">
          Nessun dato ancora — premi "Aggiorna" per scaricarlo.
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {teams.map((team) => (
            <TeamCard key={team.team} team={team} />
          ))}
        </div>
      )}
    </div>
  )
}
