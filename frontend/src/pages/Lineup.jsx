import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import GoalkeeperAdvice from '../components/GoalkeeperAdvice'
import LineupResult from '../components/LineupResult'
import PlayerStatusList from '../components/PlayerStatusList'

const FORMATIONS = ['3-4-3', '3-5-2', '4-3-3', '4-4-2', '4-5-1', '5-3-2', '5-4-1']

export default function Lineup({ league }) {
  const me = useMemo(() => league.managers.find((m) => m.is_me) ?? league.managers[0], [league])

  const [myPlayers, setMyPlayers] = useState([])
  const [matchday, setMatchday] = useState(1)
  const [formation, setFormation] = useState('4-3-3')
  const [recommendation, setRecommendation] = useState(null)
  const [goalkeepers, setGoalkeepers] = useState([])
  const [importResult, setImportResult] = useState(null)
  const [votesRefreshing, setVotesRefreshing] = useState(false)
  const [votesResult, setVotesResult] = useState(null)
  const [fixturesRefreshing, setFixturesRefreshing] = useState(false)
  const [fixturesResult, setFixturesResult] = useState(null)
  const [strengthRefreshing, setStrengthRefreshing] = useState(false)
  const [strengthResult, setStrengthResult] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function refreshMyPlayers() {
    const players = await api.listPlayers(league.id)
    setMyPlayers(players.filter((p) => p.is_taken && p.manager_id === me.id))
  }

  useEffect(() => {
    refreshMyPlayers()
  }, [league.id])

  async function handleStatusChange(playerId, status) {
    await api.updatePlayerStatus(league.id, playerId, status)
    await refreshMyPlayers()
  }

  async function handleImport(kind, file) {
    setError('')
    try {
      const result =
        kind === 'stats' ? await api.importMatchStatsCsv(league.id, file) : await api.importFixturesCsv(league.id, file)
      setImportResult({ kind, ...result })
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRefreshVotes() {
    setError('')
    setVotesResult(null)
    setVotesRefreshing(true)
    try {
      const result = await api.refreshMatchVotes(league.id, Number(matchday))
      setVotesResult(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setVotesRefreshing(false)
    }
  }

  async function handleRefreshFixtures() {
    setError('')
    setFixturesResult(null)
    setFixturesRefreshing(true)
    try {
      const result = await api.refreshFixtures(league.id, Number(matchday))
      setFixturesResult(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setFixturesRefreshing(false)
    }
  }

  async function handleRefreshTeamStrength() {
    setError('')
    setStrengthResult(null)
    setStrengthRefreshing(true)
    try {
      const result = await api.refreshTeamStrength(league.id)
      setStrengthResult(result)
    } catch (err) {
      setError(err.message)
    } finally {
      setStrengthRefreshing(false)
    }
  }

  async function handleCompute() {
    setError('')
    setSaved(false)
    setLoading(true)
    try {
      const [rec, gk] = await Promise.all([
        api.getRecommendation(league.id, me.id, matchday, formation),
        api.getGoalkeeperAdvice(league.id, me.id, matchday),
      ])
      setRecommendation(rec)
      setGoalkeepers(gk)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleSave() {
    setSaving(true)
    try {
      await api.saveLineup(league.id, {
        manager_id: me.id,
        matchday: Number(matchday),
        formation,
        starters: recommendation.starters.map((p) => p.player_id),
        bench: recommendation.bench.map((p) => p.player_id),
      })
      setSaved(true)
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Voti giornata</h2>
        <p className="mb-3 text-sm text-slate-500">
          Scarica in automatico i voti ufficiali Fantacalcio.it della giornata (con avversario e
          casa/trasferta) per calcolare i punteggi di consigliabilità — nessun file da caricare.
        </p>
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Giornata</label>
            <input
              type="number"
              min={1}
              value={matchday}
              onChange={(e) => setMatchday(e.target.value)}
              className="w-24 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            />
          </div>
          <button
            onClick={handleRefreshVotes}
            disabled={votesRefreshing}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {votesRefreshing ? 'Aggiorno...' : 'Aggiorna voti da Fantacalcio.it'}
          </button>
        </div>
        {votesResult && (
          <p className="mt-3 text-sm text-slate-600">
            Aggiornati <strong>{votesResult.updated}</strong> giocatori, {votesResult.unmatched} non
            trovati in rosa (normale: contiene tutta la Serie A, non solo i tuoi).
          </p>
        )}

        <details className="mt-4">
          <summary className="cursor-pointer text-xs font-medium text-slate-500">
            Non riesci a scaricarli? Importa da CSV manualmente
          </summary>
          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Voti giornata (CSV)</label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => e.target.files[0] && handleImport('stats', e.target.files[0])}
                className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-blue-600 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-white hover:file:bg-blue-700"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-slate-600">Calendario/avversari (CSV)</label>
              <input
                type="file"
                accept=".csv"
                onChange={(e) => e.target.files[0] && handleImport('fixtures', e.target.files[0])}
                className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-blue-600 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-white hover:file:bg-blue-700"
              />
            </div>
          </div>
          {importResult && (
            <p className="mt-3 text-sm text-slate-600">
              Importate <strong>{importResult.imported}</strong> righe, {importResult.skipped} saltate.
            </p>
          )}
        </details>
      </div>

      <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Calendario e forza avversari</h2>
        <p className="mb-3 text-sm text-slate-500">
          Scarica il calendario reale (avversario/casa-trasferta) e la classifica Serie A (gol
          fatti/subiti a partita), usati per pesare le prossime partite: un difensore contro un
          attacco debole, o un attaccante contro una difesa permeabile, valgono di più.
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <button
            onClick={handleRefreshFixtures}
            disabled={fixturesRefreshing}
            className="rounded-md bg-teal-600 px-4 py-2 text-sm font-medium text-white hover:bg-teal-700 disabled:opacity-50"
          >
            {fixturesRefreshing ? 'Aggiorno...' : `Aggiorna calendario giornata ${matchday}`}
          </button>
          <button
            onClick={handleRefreshTeamStrength}
            disabled={strengthRefreshing}
            className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
          >
            {strengthRefreshing ? 'Aggiorno...' : 'Aggiorna forza squadre (classifica)'}
          </button>
        </div>
        {fixturesResult && (
          <p className="mt-3 text-sm text-slate-600">
            Calendario aggiornato: <strong>{fixturesResult.imported}</strong> squadre per la giornata {matchday}.
          </p>
        )}
        {strengthResult && (
          <p className="mt-1 text-sm text-slate-600">
            Classifica aggiornata: <strong>{strengthResult.updated}</strong> squadre.
          </p>
        )}
      </div>

      <PlayerStatusList players={myPlayers} onStatusChange={handleStatusChange} />

      <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">Formazione consigliata</h2>
        <div className="mb-4 flex flex-wrap items-end gap-3">
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Giornata</label>
            <input
              type="number"
              min={1}
              value={matchday}
              onChange={(e) => setMatchday(e.target.value)}
              className="w-24 rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs font-medium text-slate-600">Modulo</label>
            <select
              value={formation}
              onChange={(e) => setFormation(e.target.value)}
              className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
            >
              {FORMATIONS.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleCompute}
            disabled={loading}
            className="rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-900 disabled:opacity-50"
          >
            {loading ? 'Calcolo...' : 'Calcola formazione'}
          </button>
        </div>

        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

        {recommendation && (
          <LineupResult recommendation={recommendation} onSave={handleSave} saving={saving} saved={saved} />
        )}
      </div>

      <GoalkeeperAdvice goalkeepers={goalkeepers} />
    </div>
  )
}
