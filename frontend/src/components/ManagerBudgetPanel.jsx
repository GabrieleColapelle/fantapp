export default function ManagerBudgetPanel({ budgets }) {
  return (
    <div className="rounded-lg bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-sm font-semibold text-slate-700">Budget manager</h3>
      <div className="space-y-2">
        {budgets.map((b) => {
          const pct = b.budget_total > 0 ? Math.min(100, (b.spent / b.budget_total) * 100) : 0
          return (
            <div key={b.manager_id}>
              <div className="flex justify-between text-xs">
                <span className={b.is_me ? 'font-semibold text-blue-700' : 'text-slate-600'}>
                  {b.is_me ? `${b.name} (io)` : b.name}
                </span>
                <span className="text-slate-500">
                  {b.remaining}/{b.budget_total}
                </span>
              </div>
              <div className="mt-0.5 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full rounded-full ${pct > 90 ? 'bg-red-500' : 'bg-blue-500'}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
