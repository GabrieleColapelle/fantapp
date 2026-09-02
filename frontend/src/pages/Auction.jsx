import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import AssignPickModal from '../components/AssignPickModal'
import ManagerBudgetPanel from '../components/ManagerBudgetPanel'
import PlayerTable from '../components/PlayerTable'
import RoleGapPanel from '../components/RoleGapPanel'
import SuggestionsPanel from '../components/SuggestionsPanel'

export default function Auction({ league }) {
  const me = useMemo(() => league.managers.find((m) => m.is_me) ?? league.managers[0], [league])
  const managersById = useMemo(() => Object.fromEntries(league.managers.map((m) => [m.id, m])), [league])

  const [filters, setFilters] = useState({ search: '', role: '', available_only: false })
  const [players, setPlayers] = useState([])
  const [budgets, setBudgets] = useState([])
  const [roleGaps, setRoleGaps] = useState([])
  const [suggestionRole, setSuggestionRole] = useState('P')
  const [suggestions, setSuggestions] = useState([])
  const [assigningPlayer, setAssigningPlayer] = useState(null)
  const [dealBanner, setDealBanner] = useState(null)
  const [error, setError] = useState('')

  const loadPlayers = useCallback(async () => {
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
    setPlayers(await api.listPlayers(league.id, params))
  }, [league.id, filters])

  const loadSidebar = useCallback(async () => {
    const [b, g, s] = await Promise.all([
      api.getBudgets(league.id),
      api.getRoleGaps(league.id, me.id),
      api.getSuggestions(league.id, me.id, suggestionRole),
    ])
    setBudgets(b)
    setRoleGaps(g)
    setSuggestions(s)
  }, [league.id, me.id, suggestionRole])

  useEffect(() => {
    loadPlayers()
  }, [loadPlayers])

  useEffect(() => {
    loadSidebar()
  }, [loadSidebar])

  async function handleConfirmPick(payload) {
    setError('')
    try {
      const pick = await api.createPick(league.id, payload)
      setDealBanner({ player: assigningPlayer.name, ...pick.deal_quality })
      setAssigningPlayer(null)
      await Promise.all([loadPlayers(), loadSidebar()])
      setTimeout(() => setDealBanner(null), 5000)
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleRemovePick(player) {
    if (!window.confirm(`Rimuovere l'assegnazione di ${player.name}?`)) return
    setError('')
    try {
      await api.deletePick(league.id, player.pick_id)
      await Promise.all([loadPlayers(), loadSidebar()])
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_280px]">
      <div className="order-2 space-y-3 lg:order-1">
        {dealBanner && (
          <div
            className={`rounded-md p-3 text-sm font-medium ${
              dealBanner.label === 'Buon affare'
                ? 'bg-green-50 text-green-700'
                : dealBanner.label === 'Prezzo gonfiato'
                  ? 'bg-red-50 text-red-700'
                  : 'bg-slate-100 text-slate-600'
            }`}
          >
            {dealBanner.player}: {dealBanner.label} — {dealBanner.detail}
          </div>
        )}
        {error && <p className="text-sm text-red-600">{error}</p>}
        <PlayerTable
          players={players}
          filters={filters}
          onFiltersChange={setFilters}
          managersById={managersById}
          onAssign={setAssigningPlayer}
          onRemove={handleRemovePick}
        />
      </div>

      <div className="order-1 space-y-3 lg:order-2">
        <ManagerBudgetPanel budgets={budgets} />
        <RoleGapPanel gaps={roleGaps} />
        <SuggestionsPanel role={suggestionRole} onRoleChange={setSuggestionRole} suggestions={suggestions} />
      </div>

      {assigningPlayer && (
        <AssignPickModal
          player={assigningPlayer}
          managers={league.managers}
          onConfirm={handleConfirmPick}
          onClose={() => setAssigningPlayer(null)}
        />
      )}
    </div>
  )
}
