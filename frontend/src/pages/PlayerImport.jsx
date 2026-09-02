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
  const [avgPriceResult, setAvgPriceResult] = useState(null)
  const [avgPriceLoading, setAvgPriceLoading] = useState(false)
  const [avgPriceError, setAvgPriceError] = useState('')
  const [lineupsResult, setLineupsResult] = useState(null)
  const [lineupsLoading, setLineupsLoading] = useState(false)
  const [lineupsError, setLineupsError] = useState('')
  const [setPieceResult, setSetPieceResult] = useState(null)
  const [setPieceLoading, setSetPieceLoading] = useState(false)
  const [setPieceError, setSetPieceError] = useState('')

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

  async function handleRefreshAvgPrices() {
    setAvgPriceLoading(true)
    setAvgPriceError('')
    try {
      const result = await api.refreshAvgPrices(league.id)
      setAvgPriceResult(result)
    } catch (err) {
      setAvgPriceError(err.message)
    } finally {
      setAvgPriceLoading(false)
    }
  }

  async function handleRefreshLineups() {
    setLineupsLoading(true)
    setLineupsError('')
    try {
      const result = await api.refreshLineups(league.id)
      setLineupsResult(result)
    } catch (err) {
      setLineupsError(err.message)
    } finally {
      setLineupsLoading(false)
    }
  }

  async function handleRefreshSetPieceTakers() {
    setSetPieceLoading(true)
    setSetPieceError('')
    try {
      const result = await api.refreshSetPieceTakers(league.id)
      setSetPieceResult(result)
    } catch (err) {
      setSetPieceError(err.message)
    } finally {
      setSetPieceLoading(false)
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
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Prezzi medi aste reali</h2>
        <p className="mb-3 text-sm text-slate-500">
          Aggiunge, ai giocatori già in lista, il prezzo medio realmente pagato nelle aste
          2026/27 su Fantacalcio-Online (scelto in base al numero di manager e al budget di
          questa lega). Richiede di aver già importato i giocatori sopra.
        </p>
        <button
          onClick={handleRefreshAvgPrices}
          disabled={avgPriceLoading}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {avgPriceLoading ? 'Scaricamento...' : 'Aggiorna prezzi medi aste reali'}
        </button>
        {avgPriceResult && (
          <p className="mt-3 text-sm text-slate-600">
            <strong>{avgPriceResult.updated}</strong> giocatori aggiornati con il prezzo medio reale
            ({avgPriceResult.unmatched} non abbinati).
          </p>
        )}
        {avgPriceError && <p className="mt-3 text-sm text-red-600">{avgPriceError}</p>}
      </div>

      <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Probabili titolari</h2>
        <p className="mb-3 text-sm text-slate-500">
          Aggiunge la probabilità di essere titolare nella prossima giornata (media pesata di
          Fantacalcio.it, Gazzetta, SOS Fanta e Sky da Fantacalcio-Online) e segna
          automaticamente come infortunati i giocatori indisponibili. Sovrascrive uno stato
          impostato a mano in precedenza.
        </p>
        <button
          onClick={handleRefreshLineups}
          disabled={lineupsLoading}
          className="rounded-md bg-purple-600 px-4 py-2 text-sm font-semibold text-white hover:bg-purple-700 disabled:opacity-50"
        >
          {lineupsLoading ? 'Scaricamento...' : 'Aggiorna probabili titolari'}
        </button>
        {lineupsResult && (
          <p className="mt-3 text-sm text-slate-600">
            <strong>{lineupsResult.starters_updated}</strong> giocatori con probabilità titolare,{' '}
            <strong>{lineupsResult.status_updated}</strong> segnati infortunati
            ({lineupsResult.unmatched} non abbinati).
          </p>
        )}
        {lineupsError && <p className="mt-3 text-sm text-red-600">{lineupsError}</p>}
      </div>

      <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
        <h2 className="mb-1 text-lg font-semibold text-slate-800">Rigoristi e battitori di punizioni</h2>
        <p className="mb-3 text-sm text-slate-500">
          Segna, per ogni giocatore già in lista, la posizione nella gerarchia rigori/punizioni
          della sua squadra (1° = titolare del tiro) da Fantacalcio.it. Rieseguibile: azzera e
          ricalcola le gerarchie a ogni click, per riflettere eventuali cambi.
        </p>
        <button
          onClick={handleRefreshSetPieceTakers}
          disabled={setPieceLoading}
          className="rounded-md bg-orange-600 px-4 py-2 text-sm font-semibold text-white hover:bg-orange-700 disabled:opacity-50"
        >
          {setPieceLoading ? 'Scaricamento...' : 'Aggiorna rigoristi'}
        </button>
        {setPieceResult && (
          <p className="mt-3 text-sm text-slate-600">
            <strong>{setPieceResult.penalty_takers_updated}</strong> rigoristi,{' '}
            <strong>{setPieceResult.free_kick_takers_updated}</strong> battitori di punizioni
            ({setPieceResult.unmatched} non abbinati).
          </p>
        )}
        {setPieceError && <p className="mt-3 text-sm text-red-600">{setPieceError}</p>}
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
