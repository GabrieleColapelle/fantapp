import { useEffect, useState } from 'react'
import { api } from '../api/client'

const ROLES = ['P', 'D', 'C', 'A']

export default function PlayerImport({ league, onDone }) {
  const [playerCount, setPlayerCount] = useState(null)
  const [importResult, setImportResult] = useState(null)
  const [importing, setImporting] = useState(false)
  const [error, setError] = useState('')
  const [listoneResult, setListoneResult] = useState(null)
  const [listoneLoading, setListoneLoading] = useState(false)
  const [listoneError, setListoneError] = useState('')

  const [manual, setManual] = useState({ name: '', role: 'P', team: '', quotation: '', tier: '' })

  async function refreshCount() {
    const players = await api.listPlayers(league.id)
    setPlayerCount(players.length)
  }

  useEffect(() => {
    refreshCount()
  }, [league.id])

  async function handleFileChange(e) {
    const file = e.target.files[0]
    if (!file) return
    setImporting(true)
    setError('')
    try {
      const result = await api.importPlayersCsv(league.id, file)
      setImportResult(result)
      await refreshCount()
    } catch (err) {
      setError(err.message)
    } finally {
      setImporting(false)
      e.target.value = ''
    }
  }

  async function handleRefreshListone() {
    setListoneLoading(true)
    setListoneError('')
    try {
      const result = await api.refreshListone(league.id)
      setListoneResult(result)
      await refreshCount()
    } catch (err) {
      setListoneError(err.message)
    } finally {
      setListoneLoading(false)
    }
  }

  async function handleManualAdd(e) {
    e.preventDefault()
    if (!manual.name.trim()) return
    setError('')
    try {
      await api.addPlayer(league.id, {
        ...manual,
        name: manual.name.trim(),
        quotation: Number(manual.quotation) || 0,
      })
      setManual({ name: '', role: 'P', team: '', quotation: '', tier: '' })
      await refreshCount()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="space-y-4">
      <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Aggiorna da Fantacalcio.it</h2>
        <p className="mb-3 text-sm text-slate-500">
          Scarica il listone ufficiale aggiornato (quotazioni Classic) direttamente dal sito.
          Rieseguibile in ogni momento: aggiorna i giocatori già presenti invece di duplicarli.
        </p>
        <button
          onClick={handleRefreshListone}
          disabled={listoneLoading}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {listoneLoading ? 'Scaricamento...' : 'Aggiorna da Fantacalcio.it'}
        </button>
        {listoneResult && (
          <p className="mt-3 text-sm text-slate-600">
            <strong>{listoneResult.imported}</strong> nuovi giocatori, <strong>{listoneResult.updated}</strong> aggiornati.
          </p>
        )}
        {listoneError && (
          <p className="mt-3 text-sm text-red-600">
            {listoneError} Puoi usare l'import CSV qui sotto come alternativa.
          </p>
        )}
      </div>

      <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Importa da CSV</h2>
        <p className="mb-3 text-sm text-slate-500">
          Carica il listino quotazioni (es. export Fantacalcio.it o Gazzetta). Colonne riconosciute
          automaticamente: Nome, Ruolo, Squadra, Quotazione.
        </p>
        <input
          type="file"
          accept=".csv"
          onChange={handleFileChange}
          disabled={importing}
          className="block w-full text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:text-sm file:font-medium file:text-white hover:file:bg-blue-700"
        />
        {importResult && (
          <p className="mt-3 text-sm text-slate-600">
            Importati <strong>{importResult.imported}</strong> giocatori, {importResult.skipped} righe saltate.
            {importResult.errors.length > 0 && (
              <ul className="mt-1 list-disc pl-5 text-xs text-amber-600">
                {importResult.errors.slice(0, 5).map((e, i) => (
                  <li key={i}>{e}</li>
                ))}
              </ul>
            )}
          </p>
        )}
      </div>

      <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">Aggiungi giocatore manualmente</h2>
        <form onSubmit={handleManualAdd} className="grid grid-cols-2 gap-2 sm:grid-cols-5">
          <input
            value={manual.name}
            onChange={(e) => setManual((p) => ({ ...p, name: e.target.value }))}
            placeholder="Nome"
            className="col-span-2 rounded-md border border-slate-300 px-2 py-2 text-sm sm:col-span-1"
          />
          <select
            value={manual.role}
            onChange={(e) => setManual((p) => ({ ...p, role: e.target.value }))}
            className="rounded-md border border-slate-300 px-2 py-2 text-sm"
          >
            {ROLES.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
          <input
            value={manual.team}
            onChange={(e) => setManual((p) => ({ ...p, team: e.target.value }))}
            placeholder="Squadra"
            className="rounded-md border border-slate-300 px-2 py-2 text-sm"
          />
          <input
            type="number"
            value={manual.quotation}
            onChange={(e) => setManual((p) => ({ ...p, quotation: e.target.value }))}
            placeholder="Quotazione"
            className="rounded-md border border-slate-300 px-2 py-2 text-sm"
          />
          <button type="submit" className="rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-900">
            Aggiungi
          </button>
        </form>
      </div>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="flex items-center justify-between rounded-lg bg-white p-4 shadow-sm">
        <p className="text-sm text-slate-600">
          Giocatori in lista: <strong>{playerCount ?? '...'}</strong>
        </p>
        <button
          onClick={onDone}
          disabled={!playerCount}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
        >
          Vai all'asta →
        </button>
      </div>
    </div>
  )
}
