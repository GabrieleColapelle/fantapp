import { useMemo } from 'react'

const ROLES = ['P', 'D', 'C', 'A']

function presenceDot(matches, avg) {
  if (matches == null || avg == null) return null
  const ratio = matches / avg
  if (ratio >= 1.15) return { className: 'bg-green-600', label: 'molto sopra la media' }
  if (ratio >= 1.0) return { className: 'bg-green-300', label: 'poco sopra la media' }
  if (ratio >= 0.85) return { className: 'bg-amber-400', label: 'nella media' }
  return { className: 'bg-red-500', label: 'sotto la media' }
}

function recoveryDaysLabel(expectedReturnDate) {
  if (!expectedReturnDate) return null
  const days = Math.ceil((new Date(expectedReturnDate) - new Date().setHours(0, 0, 0, 0)) / 86400000)
  if (days <= 0) return 'rientro imminente'
  return `${days}g`
}

function starterClass(probability) {
  if (probability == null) return 'text-slate-400'
  if (probability >= 70) return 'text-green-600 font-medium'
  if (probability >= 40) return 'text-amber-600'
  return 'text-red-500'
}

export default function PlayerTable({ players, filters, onFiltersChange, managersById, onAssign, onRemove }) {
  const avgMatches = useMemo(() => {
    const withMatches = players.filter((p) => p.last_season_matches != null)
    if (withMatches.length === 0) return null
    return withMatches.reduce((sum, p) => sum + p.last_season_matches, 0) / withMatches.length
  }, [players])

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
              <th className="px-3 py-2" title="Fantamedia stagione scorsa">FM scorsa</th>
              <th className="px-3 py-2">Titolare</th>
              <th className="px-3 py-2" title="Presenze stagione scorsa (per i giocatori liberi); manager e prezzo (per quelli già presi)">
                Presenze 25/26
              </th>
              <th className="px-3 py-2" />
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {players.map((p) => (
              <tr key={p.id} className={p.is_taken ? 'bg-slate-50 text-slate-400' : ''}>
                <td className="px-3 py-2 font-medium">
                  {p.name}
                  {p.injury_description && (
                    <span
                      title={
                        p.injury_expected_return_date
                          ? `${p.injury_description} — rientro stimato ${p.injury_expected_return_date}`
                          : p.injury_description
                      }
                      className="ml-1 rounded bg-red-100 px-1 py-0.5 text-[9px] font-bold text-red-700"
                    >
                      🩹{recoveryDaysLabel(p.injury_expected_return_date) ? ` ${recoveryDaysLabel(p.injury_expected_return_date)}` : ''}
                    </span>
                  )}
                  {p.is_midfielder_bug && (
                    <span
                      title="Ruolo Mantra più avanzato: centrocampista con potenziale da attaccante"
                      className="ml-1 rounded bg-fuchsia-100 px-1 py-0.5 text-[9px] font-bold text-fuchsia-700"
                    >
                      BUG
                    </span>
                  )}
                  {p.penalty_rank != null && (
                    <span
                      title={`Rigorista ${p.penalty_rank === 1 ? 'titolare' : `di riserva (${p.penalty_rank}°)`}`}
                      className={`ml-1 rounded px-1 py-0.5 text-[9px] font-bold ${
                        p.penalty_rank === 1 ? 'bg-orange-100 text-orange-700' : 'bg-orange-50 text-orange-500'
                      }`}
                    >
                      ⚽{p.penalty_rank}
                    </span>
                  )}
                  {p.free_kick_rank != null && (
                    <span
                      title={`Battitore punizioni ${p.free_kick_rank === 1 ? 'titolare' : `di riserva (${p.free_kick_rank}°)`}`}
                      className="ml-1 rounded bg-sky-50 px-1 py-0.5 text-[9px] font-bold text-sky-600"
                    >
                      P{p.free_kick_rank}
                    </span>
                  )}
                </td>
                <td className="px-3 py-2">{p.role}</td>
                <td className="px-3 py-2">
                  <span className="flex items-center gap-1.5">
                    {p.team_badge_url && <img src={p.team_badge_url} alt="" className="h-4 w-4 object-contain" />}
                    {p.team}
                  </span>
                </td>
                <td className="px-3 py-2">{p.quotation}</td>
                <td className="px-3 py-2 text-slate-500">
                  {p.avg_auction_price != null ? p.avg_auction_price.toFixed(1) : '—'}
                </td>
                <td className="px-3 py-2 text-slate-500">
                  {p.last_season_avg_fantavoto != null ? (
                    <span title={`${p.last_season_matches} presenze, media voto ${p.last_season_avg_vote?.toFixed(2)}`}>
                      {p.last_season_avg_fantavoto.toFixed(2)}
                    </span>
                  ) : (
                    '—'
                  )}
                </td>
                <td className={`px-3 py-2 ${starterClass(p.starter_probability)}`}>
                  {p.starter_probability != null ? `${p.starter_probability.toFixed(0)}%` : '—'}
                </td>
                <td className="px-3 py-2 text-xs">
                  {p.is_taken ? (
                    <span>
                      {managersById[p.manager_id]?.name ?? '—'} · {p.price_paid}
                    </span>
                  ) : (
                    <span className="flex items-center gap-1.5 text-slate-500">
                      {(() => {
                        const dot = presenceDot(p.last_season_matches, avgMatches)
                        return (
                          dot && (
                            <span
                              title={`${p.last_season_matches} presenze — ${dot.label} (media ${avgMatches.toFixed(1)})`}
                              className={`inline-block h-2 w-2 shrink-0 rounded-full ${dot.className}`}
                            />
                          )
                        )
                      })()}
                      {p.last_season_matches ?? '—'}
                    </span>
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
                <td colSpan={8} className="px-3 py-6 text-center text-slate-400">
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
