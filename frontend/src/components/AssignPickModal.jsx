import { useState } from 'react'

export default function AssignPickModal({ player, managers, onConfirm, onClose }) {
  const [managerId, setManagerId] = useState(managers[0]?.id ?? '')
  const [price, setPrice] = useState(player.quotation || 1)
  const [submitting, setSubmitting] = useState(false)

  async function handleConfirm() {
    setSubmitting(true)
    await onConfirm({ player_id: player.id, manager_id: Number(managerId), price_paid: Number(price) })
    setSubmitting(false)
  }

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-sm rounded-lg bg-white p-5 shadow-xl">
        <h3 className="mb-1 text-lg font-semibold text-slate-800">{player.name}</h3>
        <p className="mb-4 text-xs text-slate-500">
          {player.role} · {player.team} · Quotazione {player.quotation}
          {player.avg_auction_price != null && ` · Media reale ${player.avg_auction_price.toFixed(1)}`}
        </p>

        <label className="mb-1 block text-sm font-medium text-slate-700">Assegnato a</label>
        <select
          value={managerId}
          onChange={(e) => setManagerId(e.target.value)}
          className="mb-3 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        >
          {managers.map((m) => (
            <option key={m.id} value={m.id}>
              {m.is_me ? `${m.name} (io)` : m.name}
            </option>
          ))}
        </select>

        <label className="mb-1 block text-sm font-medium text-slate-700">Prezzo pagato</label>
        <input
          type="number"
          min={1}
          autoFocus
          value={price}
          onChange={(e) => setPrice(e.target.value)}
          className="mb-4 w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />

        <div className="flex gap-2">
          <button
            onClick={onClose}
            className="flex-1 rounded-md border border-slate-300 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Annulla
          </button>
          <button
            onClick={handleConfirm}
            disabled={submitting || !managerId}
            className="flex-1 rounded-md bg-blue-600 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {submitting ? '...' : 'Conferma'}
          </button>
        </div>
      </div>
    </div>
  )
}
