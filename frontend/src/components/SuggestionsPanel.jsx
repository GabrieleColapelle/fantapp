const ROLES = ['P', 'D', 'C', 'A']

const FASCIA_ICONS = {
  Top: '⭐',
  Semitop: '🔹',
  Buoni: '✓',
  Scommesse: '🎲',
}

function starterDotClass(probability) {
  if (probability == null) return 'bg-slate-300'
  if (probability >= 70) return 'bg-green-500'
  if (probability >= 40) return 'bg-amber-500'
  return 'bg-red-500'
}

export default function SuggestionsPanel({ role, onRoleChange, suggestions }) {
  return (
    <div className="rounded-lg bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Suggerimenti</h3>
        <select
          value={role}
          onChange={(e) => onRoleChange(e.target.value)}
          className="rounded-md border border-slate-300 px-1.5 py-0.5 text-xs"
        >
          {ROLES.map((r) => (
            <option key={r} value={r}>
              {r}
            </option>
          ))}
        </select>
      </div>

      <div className="space-y-3">
        {suggestions.map((group) => (
          <div key={group.fascia}>
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
              {FASCIA_ICONS[group.fascia] ?? ''} {group.fascia}
            </p>
            {group.players.length === 0 ? (
              <p className="text-xs text-slate-400">Nessuno disponibile</p>
            ) : (
              <ul className="space-y-1">
                {group.players.map((s) => (
                  <li key={s.player_id} className="flex justify-between text-xs">
                    <span className="text-slate-700">
                      <span
                        title={s.starter_probability != null ? `${s.starter_probability.toFixed(0)}% titolare` : 'Titolarità sconosciuta'}
                        className={`mr-1 inline-block h-1.5 w-1.5 rounded-full ${starterDotClass(s.starter_probability)}`}
                      />
                      {s.name} <span className="text-slate-400">({s.team})</span>
                    </span>
                    <span className="text-right">
                      <span className="font-medium text-slate-600">{s.quotation}</span>
                      {s.avg_auction_price != null && (
                        <span className="ml-1 text-slate-400">· media {s.avg_auction_price.toFixed(1)}</span>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
