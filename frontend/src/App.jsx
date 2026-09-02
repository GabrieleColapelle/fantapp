import { useEffect, useState } from 'react'
import { api } from './api/client'
import ManagerSettingsModal from './components/ManagerSettingsModal'
import Auction from './pages/Auction'
import LeagueSetup from './pages/LeagueSetup'
import Lineup from './pages/Lineup'
import PlayerImport from './pages/PlayerImport'

const LEAGUE_ID_KEY = 'fantapp.leagueId'

export default function App() {
  const [league, setLeague] = useState(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState('import')
  const [showManagers, setShowManagers] = useState(false)

  useEffect(() => {
    const storedId = localStorage.getItem(LEAGUE_ID_KEY)
    if (!storedId) {
      setLoading(false)
      return
    }
    api
      .getLeague(storedId)
      .then(setLeague)
      .catch(() => localStorage.removeItem(LEAGUE_ID_KEY))
      .finally(() => setLoading(false))
  }, [])

  function handleLeagueCreated(newLeague) {
    localStorage.setItem(LEAGUE_ID_KEY, newLeague.id)
    setLeague(newLeague)
  }

  function handleChangeLeague() {
    localStorage.removeItem(LEAGUE_ID_KEY)
    setLeague(null)
    setTab('import')
  }

  async function refreshLeague() {
    setLeague(await api.getLeague(league.id))
  }

  async function handleToggleDefenseModifier() {
    setLeague(await api.updateDefenseModifier(league.id, !league.defense_modifier))
  }

  if (loading) {
    return <div className="p-6 text-slate-500">Caricamento...</div>
  }

  if (!league) {
    return (
      <div className="mx-auto max-w-2xl p-4 sm:p-6">
        <Header />
        <LeagueSetup onCreated={handleLeagueCreated} />
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-6xl p-3 sm:p-6">
      <Header />
      <div className="mb-4 flex flex-wrap items-center justify-between gap-2 rounded-lg bg-white p-3 shadow-sm">
        <div>
          <p className="font-semibold text-slate-800">{league.name}</p>
          <p className="text-xs text-slate-500">
            {league.ruleset === 'mantra' ? 'Mantra' : 'Classic'} · Budget {league.budget_total} crediti
            {league.defense_modifier && ' · Modificatore difesa'}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleToggleDefenseModifier}
            className={`text-sm underline ${league.defense_modifier ? 'text-orange-600' : 'text-slate-400'}`}
          >
            Modificatore difesa: {league.defense_modifier ? 'ON' : 'OFF'}
          </button>
          <button onClick={() => setShowManagers(true)} className="text-sm text-blue-600 underline">
            Manager ({league.managers.length})
          </button>
          <button onClick={handleChangeLeague} className="text-sm text-slate-500 underline">
            Cambia lega
          </button>
        </div>
      </div>

      {showManagers && (
        <ManagerSettingsModal
          league={league}
          onClose={() => setShowManagers(false)}
          onChanged={refreshLeague}
        />
      )}

      <div className="mb-4 flex gap-2">
        <TabButton active={tab === 'import'} onClick={() => setTab('import')}>
          Importa giocatori
        </TabButton>
        <TabButton active={tab === 'auction'} onClick={() => setTab('auction')}>
          Asta live
        </TabButton>
        <TabButton active={tab === 'lineup'} onClick={() => setTab('lineup')}>
          Formazioni
        </TabButton>
      </div>

      {tab === 'import' && <PlayerImport league={league} onDone={() => setTab('auction')} />}
      {tab === 'auction' && <Auction league={league} />}
      {tab === 'lineup' &&
        (league.ruleset === 'mantra' ? (
          <div className="rounded-lg bg-white p-6 text-sm text-slate-500 shadow-sm">
            L'assistente formazioni per il regolamento Mantra arriverà in una prossima
            iterazione. Per ora è disponibile solo per leghe Classic.
          </div>
        ) : (
          <Lineup league={league} />
        ))}
    </div>
  )
}

function Header() {
  return (
    <header className="mb-4">
      <h1 className="text-2xl font-bold text-slate-900">⚽ Fantapp</h1>
      <p className="text-sm text-slate-500">Assistente asta fantacalcio</p>
    </header>
  )
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`rounded-md px-4 py-2 text-sm font-medium transition ${
        active ? 'bg-blue-600 text-white' : 'bg-white text-slate-600 hover:bg-slate-100'
      }`}
    >
      {children}
    </button>
  )
}
