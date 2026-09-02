const ROLES = ['P', 'D', 'C', 'A']

export default function PlayerTable({ players, filters, onFiltersChange, managersById, onAssign, onRemove }) {
  return (
    <div className="rounded-lg bg-white shadow-sm">
      <div className="flex flex-wrap gap-2 border-b border-slate-100 p-3">
        <input
          value={filters.search}
          onChange={(e) => onFiltersChange({ ...filters, search: e.target.value })}
          placeholder="Cerca giocatore..."
          className="flex-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm"
        />
        <select
          value={filters.role}
          onChange={(e) => onFiltersChange({ ...filters, role: e.target.value })}
          className="rounded-md border border-slate-300 px-2 py-1.5 text-sm"
        >
          <option value="">Tutti i ruoli</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
        <label className="flex items-center gap-1.5 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={filters.available_only}
            onChange={(e) => onFiltersChange({ ...filters, available_only: e.target.checked })}
          />
          Solo disponibili
        </label>
      </div>

      <div className="max-h-[60vh] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-slate-50 text-left text-xs uppercase text-slate-500">
            <tr>
              <th className="px-3 py-2">Nome</th>
              <th className="px-3 py-2">R</th>
              <th className="px-3 py-2">Squadra</th>
              <th className="px-3 py-2">Quot.</th>
              <th className="px-3 py-2">Media aste</th>
              <th className="px-3 py-2">Stato</th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {players.map((p) => (
              <tr key={p.id} className={p.is_taken ? 'bg-slate-50 text-slate-400' : ''}>
                <td className="px-3 py-2 font-medium">{p.name}</td>
                <td className="px-3 py-2">{p.role}</td>
                <td className="px-3 py-2">{p.team}</td>
                <td className="px-3 py-2">{p.quotation}</td>
                <td className="px-3 py-2 text-slate-500">
                  {p.avg_auction_price != null ? p.avg_auction_price.toFixed(1) : '—'}
                </td>
                <td className="px-3 py-2 text-xs">
                  {p.is_taken ? (
                    <span>
                      {managersById[p.manager_id]?.name ?? '—'} · {p.price_paid}
                    </span>
                  ) : (
                    <span className="text-green-600">libero</span>
                  )}
                </td>
                <td className="px-3 py-2 text-right">
                  {p.is_taken ? (
                    <button
                      onClick={() => onRemove(p)}
                      className="rounded-md border border-slate-300 px-2.5 py-1 text-xs font-medium text-slate-500 hover:border-red-300 hover:text-red-600"
                    >
                      Rimuovi
                    </button>
                  ) : (
                    <button
                      onClick={() => onAssign(p)}
                      className="rounded-md bg-blue-600 px-2.5 py-1 text-xs font-medium text-white hover:bg-blue-700"
                    >
                      Assegna
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {players.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-6 text-center text-slate-400">
                  Nessun giocatore trovato
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
