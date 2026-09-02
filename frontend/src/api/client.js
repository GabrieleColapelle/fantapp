async function request(path, options = {}) {
  const res = await fetch(`/api${path}`, {
    headers: options.body instanceof FormData ? undefined : { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || `Errore ${res.status}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  createLeague: (payload) => request('/leagues', { method: 'POST', body: JSON.stringify(payload) }),
  getLeague: (leagueId) => request(`/leagues/${leagueId}`),

  listPlayers: (leagueId, params = {}) => {
    const qs = new URLSearchParams(params).toString()
    return request(`/leagues/${leagueId}/players${qs ? `?${qs}` : ''}`)
  },
  addPlayer: (leagueId, payload) =>
    request(`/leagues/${leagueId}/players`, { method: 'POST', body: JSON.stringify(payload) }),
  importPlayersCsv: (leagueId, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/leagues/${leagueId}/players/import-csv`, { method: 'POST', body: form })
  },
  refreshListone: (leagueId) => request(`/leagues/${leagueId}/players/refresh-listone`, { method: 'POST' }),

  createPick: (leagueId, payload) =>
    request(`/leagues/${leagueId}/auction/picks`, { method: 'POST', body: JSON.stringify(payload) }),
  deletePick: (leagueId, pickId) =>
    request(`/leagues/${leagueId}/auction/picks/${pickId}`, { method: 'DELETE' }),
  getBudgets: (leagueId) => request(`/leagues/${leagueId}/auction/budgets`),
  getRoleGaps: (leagueId, managerId) =>
    request(`/leagues/${leagueId}/auction/role-gaps?manager_id=${managerId}`),
  getSuggestions: (leagueId, managerId, role) =>
    request(`/leagues/${leagueId}/auction/suggestions?manager_id=${managerId}&role=${role}`),

  updatePlayerStatus: (leagueId, playerId, status) =>
    request(`/leagues/${leagueId}/players/${playerId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    }),

  importMatchStatsCsv: (leagueId, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/leagues/${leagueId}/lineup/match-stats/import-csv`, { method: 'POST', body: form })
  },
  importFixturesCsv: (leagueId, file) => {
    const form = new FormData()
    form.append('file', file)
    return request(`/leagues/${leagueId}/lineup/fixtures/import-csv`, { method: 'POST', body: form })
  },
  getRecommendation: (leagueId, managerId, matchday, formation) =>
    request(
      `/leagues/${leagueId}/lineup/recommend?manager_id=${managerId}&matchday=${matchday}&formation=${formation}`
    ),
  saveLineup: (leagueId, payload) =>
    request(`/leagues/${leagueId}/lineup/save`, { method: 'POST', body: JSON.stringify(payload) }),
  getSavedLineup: (leagueId, managerId, matchday) =>
    request(`/leagues/${leagueId}/lineup/saved?manager_id=${managerId}&matchday=${matchday}`),
}
