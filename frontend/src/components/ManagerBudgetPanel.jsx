import { useState } from 'react'

const ROLE_ORDER = { P: 0, D: 1, C: 2, A: 3 }

export default function ManagerBudgetPanel({ budgets, players }) {
  const [expandedId, setExpandedId] = useState(null)
  const [isOpen, setIsOpen] = useState(true)

  return (
    <div className="rounded-lg bg-white p-4 shadow-sm">
      <button onClick={() => setIsOpen((v) => !v)} className="mb-2 flex w-full items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">Budget manager</h3>
        <span className="text-xs text-slate-400">{isOpen ? '▲' : '▼'}</span>
      </button>
      {isOpen && (
      <div className="space-y-2">
        {budgets.map((b) => {
          const pct = b.budget_total > 0 ? Math.min(100, (b.spent / b.budget_total) * 100) : 0
          const isExpanded = expandedId === b.manager_id
          const roster = players
            .filter((p) => p.manager_id === b.manager_id)
            .sort((a, z) => (ROLE_ORDER[a.role] ?? 9) - (ROLE_ORDER[z.role] ?? 9) || z.quotation - a.quotation)

          return (
            <div key={b.manager_id}>
              <button
                onClick={() => setExpandedId(isExpanded ? null : b.manager_id)}
                className="block w-full text-left"
              >
                <div className="flex justify-between text-xs">
                  <span className={b.is_me ? 'font-semibold text-blue-700' : 'text-slate-600'}>
                    {b.is_me ? `${b.name} (io)` : b.name} · {b.players_taken}
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
              </button>

              {isExpanded && (
                <ul className="mt-1.5 space-y-0.5 border-l-2 border-slate-100 pl-2">
                  {roster.length === 0 ? (
                    <li className="text-xs text-slate-400">Nessun giocatore ancora</li>
                  ) : (
                    roster.map((p) => (
                      <li key={p.id} className="flex justify-between text-xs">
                        <span className="text-slate-600">
                          {p.role} {p.name}
                        </span>
                        <span className="text-slate-400">{p.price_paid}</span>
                      </li>
                    ))
                  )}
                </ul>
              )}
            </div>
          )
        })}
      </div>
      )}
    </div>
  )
}
