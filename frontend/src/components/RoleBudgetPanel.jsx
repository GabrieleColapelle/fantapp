function barClass(pctUsed) {
  if (pctUsed > 100) return 'bg-red-500'
  if (pctUsed > 85) return 'bg-amber-500'
  return 'bg-blue-500'
}

export default function RoleBudgetPanel({ roleBudgets, defenseModifier }) {
  return (
    <div className="rounded-lg bg-white p-4 shadow-sm">
      <h3 className="mb-1 text-sm font-semibold text-slate-700">Budget per reparto</h3>
      <p className="mb-2 text-[11px] text-slate-400">
        Obiettivo consigliato{defenseModifier ? ' (con modificatore difesa)' : ''}: {roleBudgets.map((r) => `${r.role} ${r.target_pct}%`).join(' · ')}
      </p>
      <div className="space-y-2">
        {roleBudgets.map((r) => {
          const pct = Math.min(100, Math.max(0, r.pct_used))
          return (
            <div key={r.role}>
              <div className="flex justify-between text-xs">
                <span className="font-medium text-slate-600">{r.role}</span>
                <span className={r.remaining_recommended < 0 ? 'text-red-600' : 'text-slate-500'}>
                  {r.spent.toFixed(0)}/{r.target_credits.toFixed(0)}
                  {r.remaining_recommended >= 0
                    ? ` · ${r.remaining_recommended.toFixed(0)} disp.`
                    : ` · +${Math.abs(r.remaining_recommended).toFixed(0)} sforato`}
                </span>
              </div>
              <div className="mt-0.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div className={`h-full rounded-full ${barClass(r.pct_used)}`} style={{ width: `${pct}%` }} />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
