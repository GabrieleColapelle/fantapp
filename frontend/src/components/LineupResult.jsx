const FLAG_LABELS = {
  rischio_panchina: { text: 'rischio panchina', className: 'bg-amber-100 text-amber-700' },
  in_dubbio: { text: 'in dubbio', className: 'bg-amber-100 text-amber-700' },
  rischio_squalifica: { text: 'rischio squalifica', className: 'bg-yellow-100 text-yellow-700' },
}

const EXCLUDED_LABELS = {
  infortunato: 'Infortunato',
  squalificato: 'Squalificato',
}

function PlayerRow({ player }) {
  return (
    <div className="flex items-center justify-between gap-2 py-1.5 text-sm">
      <div className="flex flex-wrap items-center gap-1.5">
        <span className="font-medium text-slate-700">{player.name}</span>
        <span className="text-xs text-slate-400">
          {player.role}
          {player.opponent && ` · vs ${player.opponent} (${player.home ? 'casa' : 'trasferta'})`}
        </span>
        {player.flags.map((f) => (
          <span key={f} className={`rounded-full px-2 py-0.5 text-[10px] font-medium ${FLAG_LABELS[f]?.className ?? 'bg-slate-100 text-slate-600'}`}>
            {FLAG_LABELS[f]?.text ?? f}
          </span>
        ))}
      </div>
      {player.score != null && <span className="font-semibold text-slate-700">{player.score.toFixed(2)}</span>}
    </div>
  )
}

export default function LineupResult({ recommendation, onSave, saving, saved }) {
  const { starters, bench, alternatives, excluded } = recommendation

  return (
    <div className="space-y-3">
      <div className="rounded-lg bg-white p-4 shadow-sm">
        <h3 className="mb-2 text-sm font-semibold text-slate-700">Titolari consigliati</h3>
        <div className="divide-y divide-slate-100">
          {starters.map((p) => (
            <PlayerRow key={p.player_id} player={p} />
          ))}
        </div>
      </div>

      {alternatives.length > 0 && (
        <div className="rounded-lg bg-amber-50 p-4 shadow-sm">
          <h3 className="mb-2 text-sm font-semibold text-amber-800">Ballottaggi</h3>
          <ul className="space-y-1 text-sm text-amber-800">
            {alternatives.map((a, i) => (
              <li key={i}>
                {a.role}: <strong>{a.starter}</strong> vs {a.alternative} — punteggi molto vicini
              </li>
            ))}
          </ul>
        </div>
      )}

      {bench.length > 0 && (
        <div className="rounded-lg bg-white p-4 shadow-sm">
          <h3 className="mb-2 text-sm font-semibold text-slate-700">Panchina (ordinata)</h3>
          <div className="divide-y divide-slate-100">
            {bench.map((p) => (
              <PlayerRow key={p.player_id} player={p} />
            ))}
          </div>
        </div>
      )}

      {excluded.length > 0 && (
        <div className="rounded-lg bg-red-50 p-4 shadow-sm">
          <h3 className="mb-2 text-sm font-semibold text-red-700">Non disponibili</h3>
          <ul className="space-y-1 text-sm text-red-700">
            {excluded.map((p) => (
              <li key={p.player_id}>
                {p.name} ({p.role}) — {EXCLUDED_LABELS[p.excluded_reason] ?? p.excluded_reason}
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={onSave}
        disabled={saving}
        className="w-full rounded-md bg-blue-600 py-2.5 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {saving ? 'Salvataggio...' : saved ? 'Formazione salvata ✓' : 'Salva formazione'}
      </button>
    </div>
  )
}
