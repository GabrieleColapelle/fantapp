import { useMemo, useState } from 'react'

export default function AssignPickModal({ player, managers, budgets, onConfirm, onClose }) {
  const [managerId, setManagerId] = useState(managers[0]?.id ?? '')
  const [price, setPrice] = useState(player.quotation || 1)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  const remaining = useMemo(
    () => budgets.find((b) => b.manager_id === Number(managerId))?.remaining,
    [budgets, managerId]
  )
  const overBudget = remaining != null && Number(price) > remaining

  async function handleConfirm() {
    if (overBudget) return
    setError('')
    setSubmitting(true)
    try {
      await onConfirm({ player_id: player.id, manager_id: Number(managerId), price_paid: Number(price) })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm rounded-lg bg-white p-5 shadow-xl">
        <h3 className="mb-1 text-lg font-semibold text-slate-800">
          {player.name}
          {player.is_midfielder_bug && (
            <span
              title="Ruolo Mantra più avanzato: centrocampista con potenziale da attaccante"
              className="ml-2 rounded bg-fuchsia-100 px-1.5 py-0.5 text-[10px] font-bold text-fuchsia-700 align-middle"
            >
              BUG
            </span>
          )}
        </h3>
        <p className="mb-4 text-xs text-slate-500">
          {player.role} · {player.team} · Quotazione {player.quotation}
          {player.avg_auction_price != null && ` · Media reale ${player.avg_auction_price.toFixed(1)}`}
        </p>

        <label className="mb-1 block text-sm font-medium text-slate-700">Assegnato a</label>
        <select
          value={managerId}
          onChange={(e) => setManagerId(e.target.value)}
          className="mb-1 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          {managers.map((m) => (
            <option key={m.id} value={m.id}>
              {m.is_me ? `${m.name} (io)` : m.name}
            </option>
          ))}
        </select>
        {remaining != null && (
          <p className="mb-3 text-xs text-slate-400">Budget residuo: {remaining}</p>
        )}

        <label className="mb-1 block text-sm font-medium text-slate-700">Prezzo pagato</label>
        <input
          type="number"
          min={1}
          autoFocus
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          className={`mb-1 w-full rounded-md border px-3 py-2 text-sm ${
            overBudget ? 'border-red-400' : 'border-slate-300'
          }`}
        />
        {overBudget && (
          <p className="mb-3 text-xs text-red-600">Supera il budget residuo ({remaining})</p>
        )}
        {error && <p className="mb-3 text-xs text-red-600">{error}</p>}

        <div className="mt-3 flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 rounded-md border border-slate-300 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Annulla
          </button>
          <button
            onClick={handleConfirm}
            disabled={submitting || !managerId || overBudget}
            className="flex-1 rounded-md bg-blue-600 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? '...' : 'Conferma'}
          </button>
        </div>
      </div>
    </div>
  )
}
