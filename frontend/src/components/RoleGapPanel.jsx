export default function RoleGapPanel({ gaps }) {
  return (
    <div className="rounded-lg bg-white p-4 shadow-sm">
      <h3 className="mb-2 text-sm font-semibold text-slate-700">Cosa mi manca (io)</h3>
      <div className="grid grid-cols-4 gap-2">
        {gaps.map((g) => (
          <div
            key={g.role}
            className={`rounded-md p-2 text-center ${g.remaining > 0 ? 'bg-amber-50' : 'bg-green-50'}`}
          >
            <p className="text-xs font-semibold text-slate-700">{g.role}</p>
            <p className="text-sm text-slate-600">
              {g.filled}/{g.slots}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
