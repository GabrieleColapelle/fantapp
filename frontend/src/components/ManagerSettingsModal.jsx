import { useState } from 'react'
import { api } from '../api/client'

export default function ManagerSettingsModal({ league, onClose, onChanged }) {
  const [newName, setNewName] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [editingName, setEditingName] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function refresh() {
    await onChanged()
  }

  async function handleAdd(e) {
    e.preventDefault()
    if (!newName.trim()) return
    setError('')
    setBusy(true)
    try {
      await api.addManager(league.id, { name: newName.trim(), is_me: false })
      setNewName('')
      await refresh()
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function handleRename(manager) {
    if (!editingName.trim()) return
    setError('')
    try {
      await api.updateManager(league.id, manager.id, { name: editingName.trim(), is_me: manager.is_me })
      setEditingId(null)
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleSetMe(manager) {
    setError('')
    try {
      await api.updateManager(league.id, manager.id, { name: manager.name, is_me: true })
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleDelete(manager) {
    if (!window.confirm(`Eliminare "${manager.name}" dalla lega?`)) return
    setError('')
    try {
      await api.deleteManager(league.id, manager.id)
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="fixed inset-0 z-20 flex items-center justify-center bg-black/40 p-4">
      <div className="w-full max-w-md rounded-lg bg-white p-5 shadow-xl">
        <h3 className="mb-3 text-lg font-semibold text-slate-800">Manager della lega</h3>

        <div className="mb-4 max-h-64 space-y-1 overflow-y-auto">
          {league.managers.map((m) => (
            <div key={m.id} className="flex items-center gap-2 rounded-md border border-slate-200 px-2 py-1.5">
              {editingId === m.id ? (
                <input
                  autoFocus
                  value={editingName}
                  onChange={(e) => setEditingName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleRename(m)}
                  className="flex-1 rounded border border-slate-300 px-2 py-1 text-sm"
                />
              ) : (
                <span className="flex-1 text-sm text-slate-700">
                  {m.name} {m.is_me && <span className="text-xs text-blue-600">(io)</span>}
                </span>
              )}

              {editingId === m.id ? (
                <button
                  onClick={() => handleRename(m)}
                  className="rounded px-2 py-1 text-xs font-medium text-blue-600 hover:bg-blue-50"
                >
                  Salva
                </button>
              ) : (
                <button
                  onClick={() => {
                    setEditingId(m.id)
                    setEditingName(m.name)
                  }}
                  className="rounded px-2 py-1 text-xs text-slate-500 hover:bg-slate-50"
                >
                  Rinomina
                </button>
              )}
              {!m.is_me && (
                <button
                  onClick={() => handleSetMe(m)}
                  className="rounded px-2 py-1 text-xs text-slate-500 hover:bg-slate-50"
                >
                  Sono io
                </button>
              )}
              <button
                onClick={() => handleDelete(m)}
                className="rounded px-2 py-1 text-xs text-slate-400 hover:bg-red-50 hover:text-red-600"
              >
                ✕
              </button>
            </div>
          ))}
        </div>

        <form onSubmit={handleAdd} className="mb-3 flex gap-2">
          <input
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            placeholder="Nome nuovo manager"
            className="flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            type="submit"
            disabled={busy}
            className="rounded-md bg-blue-600 px-3 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            Aggiungi
          </button>
        </form>

        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

        <button
          onClick={onClose}
          className="w-full rounded-md border border-slate-300 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
        >
          Chiudi
        </button>
      </div>
    </div>
  )
}
