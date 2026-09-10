const FASCIA_ICONS = {
  Top: '⭐',
  Semitop: '🔹',
  Buoni: '✓',
  Scommesse: '🎲',
}

const ROLE_NAMES = {
  P: 'Portieri',
  D: 'Difensori',
  C: 'Centrocampisti',
  A: 'Attaccanti',
}

function starterDotClass(probability) {
  if (probability == null) return 'bg-slate-300'
  if (probability >= 70) return 'bg-green-500'
  if (probability >= 40) return 'bg-amber-500'
  return 'bg-red-500'
}

function PlayerRow({ s }) {
  const hasBadges = s.is_midfielder_bug || s.penalty_rank != null
  return (
    <li className="py-1 text-sm">
      <div className="flex items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-1.5 text-slate-700">
          <span
            title={s.starter_probability != null ? `${s.starter_probability.toFixed(0)}% titolare` : 'Titolarità sconosciuta'}
            className={`inline-block h-2 w-2 shrink-0 rounded-full ${starterDotClass(s.starter_probability)}`}
          />
          {s.team_badge_url && (
            <img src={s.team_badge_url} alt="" title={s.team} className="h-4 w-4 shrink-0 object-contain" />
          )}
          <span className="truncate">
            {s.name} <span className="text-xs text-slate-400">({s.team})</span>
          </span>
        </span>
        <span className="shrink-0 text-right">
          <span className="font-medium text-slate-600">{s.quotation}</span>
          {s.avg_auction_price != null && (
            <span className="ml-1 text-xs text-slate-400">· {s.avg_auction_price.toFixed(1)}</span>
          )}
          {s.last_season_avg_fantavoto != null && (
            <span className="ml-1 text-xs text-slate-400" title="Fantamedia stagione scorsa">
              (FM {s.last_season_avg_fantavoto.toFixed(1)})
            </span>
          )}
        </span>
      </div>
      {hasBadges && (
        <div className="ml-3.5 flex gap-1">
          {s.is_midfielder_bug && (
            <span
              title="Ruolo Mantra più avanzato: centrocampista con potenziale da attaccante"
              className="rounded bg-fuchsia-100 px-1 py-0.5 text-[10px] font-bold text-fuchsia-700"
            >
              BUG
            </span>
          )}
          {s.penalty_rank != null && (
            <span
              title={`Rigorista ${s.penalty_rank === 1 ? 'titolare' : `di riserva (${s.penalty_rank}°)`}`}
              className={`rounded px-1 py-0.5 text-[10px] font-bold ${
                s.penalty_rank === 1 ? 'bg-orange-100 text-orange-700' : 'bg-orange-50 text-orange-500'
              }`}
            >
              ⚽{s.penalty_rank}
            </span>
          )}
        </div>
      )}
    </li>
  )
}

export default function SuggestionsPanel({ suggestions }) {
  return (
    <div className="rounded-lg bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Suggerimenti</h3>
        <span className="text-[11px] text-slate-400">ordinati per appetibilità, scorri per vederne di più</span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {suggestions.map((roleGroup) => (
          <div key={roleGroup.role} className="rounded-md border border-slate-100 p-3">
            <p className="mb-2 text-sm font-bold text-slate-500">{ROLE_NAMES[roleGroup.role] ?? roleGroup.role}</p>
            <div className="max-h-[420px] space-y-3 overflow-y-auto pr-1">
              {roleGroup.fasce.map((f) => (
                <div key={f.fascia}>
                  <p className="sticky top-0 mb-0.5 bg-white text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                    {FASCIA_ICONS[f.fascia] ?? ''} {f.fascia}
                  </p>
                  {f.players.length === 0 ? (
                    <p className="text-xs text-slate-400">Nessuno disponibile</p>
                  ) : (
                    <ul className="divide-y divide-slate-50">
                      {f.players.map((s) => (
                        <PlayerRow key={s.player_id} s={s} />
                      ))}
                    </ul>
                  )}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
