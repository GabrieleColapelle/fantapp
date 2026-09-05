function GoalkeeperRow({ gk }) {
  return (
    <div className={`rounded-md p-2.5 ${gk.recommended ? 'bg-green-50' : ''}`}>
      <div className="flex items-center justify-between gap-2 text-sm">
        <span className="flex items-center gap-1.5">
          <span className="font-medium text-slate-700">{gk.name}</span>
          <span className="text-xs text-slate-400">
            {gk.team}
            {gk.opponent && ` · vs ${gk.opponent} (${gk.home ? 'casa' : 'trasferta'})`}
          </span>
          {gk.recommended && (
            <span className="rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-semibold text-green-700">
              CONSIGLIATO
            </span>
          )}
          {gk.excluded_reason && (
            <span className="rounded-full bg-red-100 px-2 py-0.5 text-[10px] font-medium text-red-700">
              {gk.excluded_reason}
            </span>
          )}
        </span>
        {gk.score != null && <span className="font-semibold text-slate-700">{gk.score.toFixed(2)}</span>}
      </div>

      {gk.opponent_description ? (
        <p className="mt-1 text-xs text-slate-600">{gk.opponent_description}</p>
      ) : (
        <p className="mt-1 text-xs text-slate-400">
          Forza avversario non disponibile — aggiorna la classifica qui sopra per un confronto più preciso.
        </p>
      )}

      {gk.breakdown && gk.breakdown.length > 0 && (
        <details className="mt-1">
          <summary className="cursor-pointer text-[11px] font-medium text-slate-400">Dettagli punteggio</summary>
          <ul className="mt-1 list-disc space-y-0.5 pl-4 text-[11px] text-slate-500">
            {gk.breakdown.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  )
}

export default function GoalkeeperAdvice({ goalkeepers }) {
  if (!goalkeepers || goalkeepers.length < 2) return null

  return (
    <div className="rounded-lg bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Quale portiere schierare</h3>
        <span className="text-[11px] text-slate-400">confronto tra i tuoi portieri per questa giornata</span>
      </div>
      <div className="divide-y divide-slate-100">
        {goalkeepers.map((gk) => (
          <GoalkeeperRow key={gk.player_id} gk={gk} />
        ))}
      </div>
    </div>
  )
}
