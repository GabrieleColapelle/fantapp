function badgeClass(gap) {
  if (gap.remaining === 0) return 'bg-slate-100 text-slate-400'
  if (gap.remaining >= gap.slots / 2) return 'bg-red-100 text-red-700'
  return 'bg-amber-100 text-amber-700'
}

export default function AllManagersRoleGaps({ managerGaps }) {
  return (
    <div className="rounded-lg bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-sm font-semibold text-slate-700">Cosa manca a tutti</h3>
      <div className="space-y-2">
        {managerGaps.map((mg) => (
          <div key={mg.manager_id} className="flex items-center justify-between gap-2">
            <span className={`text-xs ${mg.is_me ? 'font-semibold text-blue-700' : 'text-slate-600'}`}>
              {mg.is_me ? `${mg.name} (io)` : mg.name}
            </span>
            <div className="flex gap-1">
              {mg.gaps.map((g) => (
                <span
                  key={g.role}
                  title={`${g.role}: ${g.filled}/${g.slots}`}
                  className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${badgeClass(g)}`}
                >
                  {g.role}
                  {g.remaining}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
