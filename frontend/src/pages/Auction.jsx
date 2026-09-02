import { useCallback, useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import AllManagersRoleGaps from '../components/AllManagersRoleGaps'
import AssignPickModal from '../components/AssignPickModal'
import ManagerBudgetPanel from '../components/ManagerBudgetPanel'
import PlayerTable from '../components/PlayerTable'
import RoleBudgetPanel from '../components/RoleBudgetPanel'
import SuggestionsPanel from '../components/SuggestionsPanel'

export default function Auction({ league }) {
  const me = useMemo(() => league.managers.find((m) => m.is_me) ?? league.managers[0], [league])
  const managersById = useMemo(() => Object.fromEntries(league.managers.map((m) => [m.id, m])), [league])

  const [filters, setFilters] = useState({ search: '', role: '', available_only: false })
  const [players, setPlayers] = useState([])
  const [rosterPlayers, setRosterPlayers] = useState([])
  const [budgets, setBudgets] = useState([])
  const [roleBudgets, setRoleBudgets] = useState([])
  const [allRoleGaps, setAllRoleGaps] = useState([])
  const [suggestions, setSuggestions] = useState([])
  const [assigningPlayer, setAssigningPlayer] = useState(null)
  const [dealBanner, setDealBanner] = useState(null)
  const [error, setError] = useState('')

  const loadPlayers = useCallback(async () => {
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v))
    setPlayers(await api.listPlayers(league.id, params))
  }, [league.id, filters])

  const loadRosterPlayers = useCallback(async () => {
    setRosterPlayers(await api.listPlayers(league.id))
  }, [league.id])

  const loadSidebar = useCallback(async () => {
    const [b, rb, g, s] = await Promise.all([
      api.getBudgets(league.id),
      api.getBudgetByRole(league.id, me.id),
      api.getAllRoleGaps(league.id),
      api.getAllSuggestions(league.id, me.id),
    ])
    setBudgets(b)
    setRoleBudgets(rb)
    setAllRoleGaps(g)
    setSuggestions(s)
  }, [league.id, me.id])

  useEffect(() => {
    loadPlayers()
  }, [loadPlayers])

  useEffect(() => {
    loadRosterPlayers()
  }, [loadRosterPlayers])

  useEffect(() => {
    loadSidebar()
  }, [loadSidebar])

  async function handleConfirmPick(payload) {
    setError('')
    try {
      const pick = await api.createPick(league.id, payload)
      setDealBanner({ player: assigningPlayer.name, ...pick.deal_quality })
      setAssigningPlayer(null)
      await Promise.all([loadPlayers(), loadSidebar(), loadRosterPlayers()])
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
      await Promise.all([loadPlayers(), loadSidebar(), loadRosterPlayers()])
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
        <ManagerBudgetPanel budgets={budgets} players={rosterPlayers} />
        <RoleBudgetPanel roleBudgets={roleBudgets} defenseModifier={league.defense_modifier} />
        <AllManagersRoleGaps managerGaps={allRoleGaps} />
        <SuggestionsPanel suggestions={suggestions} />
      </div>

      {assigningPlayer && (
        <AssignPickModal
          player={assigningPlayer}
          managers={league.managers}
          budgets={budgets}
          onConfirm={handleConfirmPick}
          onClose={() => setAssigningPlayer(null)}
        />
      )}
    </div>
  )
}
