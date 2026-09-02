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

export default function SuggestionsPanel({ suggestions }) {
  return (
    <div className="rounded-lg bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-sm font-semibold text-slate-700">Suggerimenti</h3>

      <div className="space-y-4">
        {suggestions.map((roleGroup) => {
          const players = roleGroup.fasce.flatMap((f) => f.players.map((p) => ({ ...p, fascia: f.fascia })))
          return (
            <div key={roleGroup.role}>
              <p className="mb-1 text-xs font-bold text-slate-500">{roleGroup.role}</p>
              {players.length === 0 ? (
                <p className="text-xs text-slate-400">Nessuno disponibile</p>
              ) : (
                <ul className="space-y-1">
                  {players.map((s) => (
                    <li key={s.player_id} className="flex justify-between text-xs">
                      <span className="flex items-center gap-1 text-slate-700">
                        <span
                          title={s.starter_probability != null ? `${s.starter_probability.toFixed(0)}% titolare` : 'Titolarità sconosciuta'}
                          className={`inline-block h-1.5 w-1.5 shrink-0 rounded-full ${starterDotClass(s.starter_probability)}`}
                        />
                        <span title={s.fascia}>{FASCIA_ICONS[s.fascia] ?? ''}</span>
                        {s.name} <span className="text-slate-400">({s.team})</span>
                        {s.is_midfielder_bug && (
                          <span
                            title="Ruolo Mantra più avanzato: centrocampista con potenziale da attaccante"
                            className="rounded bg-fuchsia-100 px-1 py-0.5 text-[9px] font-bold text-fuchsia-700"
                          >
                            BUG
                          </span>
                        )}
                        {s.penalty_rank != null && (
                          <span
                            title={`Rigorista ${s.penalty_rank === 1 ? 'titolare' : `di riserva (${s.penalty_rank}°)`}`}
                            className={`rounded px-1 py-0.5 text-[9px] font-bold ${
                              s.penalty_rank === 1 ? 'bg-orange-100 text-orange-700' : 'bg-orange-50 text-orange-500'
                            }`}
                          >
                            ⚽{s.penalty_rank}
                          </span>
                        )}
                      </span>
                      <span className="text-right shrink-0">
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
          )
        })}
      </div>
    </div>
  )
}
