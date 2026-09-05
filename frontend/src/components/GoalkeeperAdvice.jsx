function GoalkeeperRow({ gk }) {
  const hasExplanation = gk.breakdown && gk.breakdown.length > 0

  return (
    <div className={`group relative rounded-md p-2 ${gk.recommended ? 'bg-green-50' : ''}`}>
      <div className="flex items-center justify-between gap-2 text-sm">
        <span className="flex items-center gap-1.5">
          <span
            className={`font-medium text-slate-700 ${hasExplanation ? 'cursor-help decoration-dotted decoration-slate-300 underline underline-offset-2' : ''}`}
          >
            {gk.name}
          </span>
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

      {hasExplanation && (
        <div className="pointer-events-none absolute left-0 top-full z-10 mt-1 w-72 rounded-md bg-slate-800 p-3 text-xs text-slate-100 opacity-0 shadow-lg transition-opacity duration-150 group-hover:opacity-100">
          <p className="mb-1.5 font-semibold text-white">Perché {gk.name}?</p>
          <ul className="list-disc space-y-1 pl-4">
            {gk.breakdown.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </div>
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
      <div className="space-y-1">
        {goalkeepers.map((gk) => (
          <GoalkeeperRow key={gk.player_id} gk={gk} />
        ))}
      </div>
    </div>
  )
}
