# Fantapp

Webapp locale per gestire il fantacalcio: asta live e (in arrivo) assistente
formazioni, aggiornamento dati e dashboard di lega. Pensata per girare sul tuo
computer durante l'asta, raggiungibile anche da tablet/telefono sulla stessa
rete Wi-Fi.

## Stack

- **Backend**: Python + FastAPI + SQLAlchemy, database SQLite locale.
- **Frontend**: React + Vite + Tailwind CSS.
- Nessun account/login: è pensata per un uso privato tra amici sulla stessa rete.

## Avvio rapido

Richiede Python 3.11+ e Node.js 20+ già installati.

```bash
./start.sh
```

Il primo avvio crea automaticamente il virtualenv Python e installa le
dipendenze npm (può richiedere qualche minuto). Le volte successive parte
tutto in pochi secondi.

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000 (documentazione interattiva su `/docs`)

Per usare l'app da un altro dispositivo (es. tablet durante l'asta), collegati
alla stessa rete Wi-Fi e apri `http://<ip-del-computer>:5173`.

Per fermare tutto: `Ctrl+C` nel terminale dove gira `start.sh`.

## Test

```bash
cd backend
./venv/bin/pytest tests
```

## Roadmap moduli

- [x] **Modulo 1 — Assistente Asta**: import quotazioni da CSV, assegnazione
      giocatori multi-manager, budget in tempo reale, alert buon
      affare/prezzo gonfiato, gap per ruolo, suggerimenti.
- [x] **Modulo 2 — Assistente Formazioni** (solo Classic per ora): punteggio
      di consigliabilità per giocatore (forma recente, casa/trasferta,
      scontro diretto, rischio panchina/squalifica), formazione consigliata
      con ballottaggi, salvataggio della formazione scelta.
- [ ] **Modulo 3 — Aggiornamento dati**: import automatico di voti,
      infortuni, calendario e probabili formazioni.
- [ ] **Modulo 4 — Dashboard e gestione lega**: classifica, storico
      formazioni, watchlist, confronto giocatori.
