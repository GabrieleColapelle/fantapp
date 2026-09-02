const STATUS_OPTIONS = [
  { value: '', label: 'Nessuno' },
  { value: 'dubbio', label: 'In dubbio' },
  { value: 'diffidato', label: 'Diffidato' },
  { value: 'infortunato', label: 'Infortunato' },
  { value: 'squalificato', label: 'Squalificato' },
]

export default function PlayerStatusList({ players, onStatusChange }) {
  return (
    <div className="rounded-lg bg-white p-4 shadow-sm sm:p-6">
      <h2 className="mb-1 text-lg font-semibold text-slate-800">Stato giocatori (mia rosa)</h2>
      <p className="mb-3 text-sm text-slate-500">
        Segnala infortuni, squalifiche, diffide o dubbi: i giocatori infortunati/squalificati
        vengono esclusi dalla formazione consigliata.
      </p>
      {players.length === 0 ? (
        <p className="text-sm text-slate-400">Nessun giocatore in rosa. Vai prima all'asta.</p>
      ) : (
        <div className="divide-y divide-slate-100">
          {players.map((p) => (
            <div key={p.id} className="flex items-center justify-between gap-2 py-2">
              <div className="text-sm">
                <span className="font-medium text-slate-700">{p.name}</span>{' '}
                <span className="text-xs text-slate-400">
                  {p.role} · {p.team}
                </span>
              </div>
              <select
                value={p.status}
                onChange={(e) => onStatusChange(p.id, e.target.value)}
                className="rounded-md border border-slate-300 px-2 py-1 text-xs"
              >
                {STATUS_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
