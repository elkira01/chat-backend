# Web-Augmented AI Chat Agent — Project Blueprint

> A self-hosted, web-search-augmented chat application powered by Llama 3 1B running on a Contabo VPS.

---

## Project Overview

This project is a full-stack AI chat application where a user can converse with a locally hosted open-weight LLM (Llama 3 1B). When a question requires information beyond the model's training data, the backend automatically retrieves live web results and injects them into the prompt before querying the model — a pattern known as **Retrieval-Augmented Generation (RAG)**.

---

## Architecture

```
Browser (Chat UI)
       ↕
Backend Server (FastAPI — Python)
       ↕                    ↕
Llama 3 1B (Ollama     Web Search API
 on Contabo VPS)       (Tavily / Brave)
```

---

## Stack

| Layer | Technology |
|---|---|
| LLM Runtime | Ollama (serving Llama 3.2 1B) |
| Backend | Python + FastAPI |
| HTTP Client | httpx (async) |
| Web Search | Tavily API (recommended) |
| Process Manager | systemd |
| Reverse Proxy | Nginx + Let's Encrypt (HTTPS) |
| Rate Limiting | slowapi |
| Frontend | HTML/JS or React |

---

## Phase 1 — LLM Server (Contabo VPS)

- Install **Ollama** on the VPS
- Pull the `llama3.2:1b` model
- Run `ollama serve` — exposes an OpenAI-compatible API on `localhost:11434`
- Keep Ollama bound to **localhost only** — the backend calls it internally
- No need to open port 11434 in the firewall

---

## Phase 2 — Web Search API

- Recommended provider: **Tavily** (purpose-built for LLM/RAG use cases)
- Free tier: 1,000 calls/month
- Returns clean, pre-summarized snippets — minimal noise in prompts
- Alternative providers: Brave Search API (2,000 free/month), SerpAPI (100 free/month)
- Store API key in `.env` — never expose it in the frontend

---

## Phase 3 — Backend (FastAPI)

### Project Structure

```
/chat-backend
  ├── main.py        ← FastAPI app, endpoints, middleware
  ├── llm.py         ← Ollama communication (standard + streaming)
  ├── search.py      ← Web search API integration
  ├── prompt.py      ← Prompt building & history management
  ├── router.py      ← Search-or-not decision logic
  ├── config.py      ← Environment variable management
  ├── .env           ← Secrets (never commit)
  └── requirements.txt
```

### Key Dependencies

- `fastapi` — web framework
- `uvicorn` — ASGI server
- `httpx` — async HTTP client
- `python-dotenv` — loads `.env`
- `pydantic` — request/response validation
- `slowapi` — rate limiting

### Environment Variables (`.env`)

| Variable | Description |
|---|---|
| `SEARCH_API_KEY` | Tavily / Brave / SerpAPI key |
| `SEARCH_PROVIDER` | e.g. `tavily` |
| `OLLAMA_BASE_URL` | `http://localhost:11434` |
| `OLLAMA_MODEL` | `llama3.2:1b` |
| `MAX_SEARCH_RESULTS` | Recommended: `3` |
| `MAX_HISTORY_TURNS` | Recommended: `5` |
| `ALLOWED_ORIGINS` | Frontend domain (CORS) |

### Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Status check, confirms Ollama reachable |
| `POST` | `/chat` | Standard request/response chat |
| `POST` | `/chat/stream` | Streaming token-by-token response |

### Request Model
```
ChatRequest:
  - message: str        ← current user message
  - history: list       ← previous conversation turns
```

### Response Model
```
ChatResponse:
  - reply: str          ← assistant's answer
  - sources: list       ← URLs used (empty if no search)
  - used_search: bool   ← whether web search was triggered
```

---

## Phase 4 — Core Backend Logic

### Request Flow

```
1. Receive ChatRequest { message, history }
2. router.py → decide if web search is needed
3a. If YES → search.py fetches top 3 results
         → prompt.py builds augmented prompt
         → llm.py sends to Ollama → returns reply + sources
3b. If NO  → prompt.py builds plain prompt
         → llm.py sends to Ollama → returns reply
4. Return ChatResponse to frontend
```

### Routing Logic (router.py)

Two strategies — start with A, upgrade to B later:

**Strategy A — Rule-based (fast):**
Scan for keywords signaling live data need:
- Time: *today, now, current, latest, recent, 2025*
- News: *news, update, what happened*
- Lookup: *who is, price of, how many, search for*

**Strategy B — LLM-based (smarter):**
Send message to Llama 3 with strict system prompt:
*"Reply SEARCH if this needs real-time web info, otherwise reply ANSWER."*
Branch on the response.

### Prompt Design (prompt.py)

**Plain prompt structure:**
```
[System message — assistant persona]
[Last N conversation turns]
[Current user message]
```

**Augmented prompt structure:**
```
[System message]
--- Web Search Results ---
[1] Title | Source URL
    Snippet (max ~150 words)
[2] ...
[3] ...
--- End of Results ---
Instruction: Use above results where relevant. Cite sources.
If unhelpful, use own knowledge and say so.
[Last N conversation turns]
[Current user message]
```

### History Management
- Keep a rolling window of the last `MAX_HISTORY_TURNS` exchanges
- Each turn: `{ role: "user"|"assistant", content: "..." }`
- Trim oldest messages from the front when limit is exceeded
- Critical for small models — they have limited context windows

### Search Module (search.py)
- Async call to search provider API
- Extract `title`, `url`, `snippet` from each result
- Return top N results as a clean list
- On failure: return empty list (graceful degradation to LLM-only)

### LLM Module (llm.py)
- POST to `http://localhost:11434/v1/chat/completions`
- Standard mode: return `choices[0].message.content`
- Streaming mode: yield `choices[0].delta.content` tokens as they arrive
- Set 60s timeout on HTTP client
- Handle: Ollama unreachable, wrong model name (404), timeouts

---

## Phase 5 — Security & Production Setup

### Security Rules
- API keys only in `.env` on the server — never in frontend code
- Ollama bound to `localhost` — not exposed to internet
- Backend bound to `localhost` — Nginx proxies public traffic to it
- CORS restricted to your frontend's domain in production
- Rate limit: 20 requests/minute per IP on `/chat`

### Nginx Configuration
- Listens on ports 80 and 443 (public)
- Forwards `/api/` requests → `localhost:8000` (FastAPI)
- Serves frontend static files directly
- HTTPS via Let's Encrypt / Certbot (free)

### Process Management (systemd)
- Run backend as a systemd service
- Auto-start on VPS reboot
- Auto-restart on crashes
- Logs available via `journalctl`

---

## Phase 6 — Frontend Requirements

The chat UI needs these capabilities beyond a basic chat:

- **"Searching the web..." indicator** — shown while backend processes
- **Source citations panel** — collapsible list of URLs used
- **Answer type label** — distinguish "from web" vs "from knowledge"
- **Streaming support** — render tokens as they arrive for better UX
- **Error handling** — graceful messages if backend is unreachable
- All API calls go through the backend — no direct LLM or search calls from browser

---

## Logging & Observability

Log the following for every request:
- Incoming message length
- Whether search was triggered
- Search API response time + result count
- LLM response time
- All errors with full stack traces

Use Python's `logging` module with daily log rotation.

---

## Testing Checklist

- [ ] `GET /health` returns 200 and model name
- [ ] `POST /chat` with general question returns reply (no search)
- [ ] `POST /chat` with current-events question triggers search + returns sources
- [ ] Search failure falls back gracefully to LLM-only
- [ ] Rate limiter blocks requests over threshold
- [ ] Streaming endpoint delivers tokens progressively
- [ ] Final streaming chunk delivers sources
- [ ] App restarts cleanly via systemd after crash
- [ ] HTTPS working via Nginx + Certbot
- [ ] CORS blocks requests from unauthorized origins

---

## Implementation Order

1. Get Ollama running and test with `curl`
2. Build and test backend `/health` + `/chat` (LLM only, no search)
3. Integrate search API and test in isolation
4. Write and test prompt templates
5. Wire routing logic into `/chat` endpoint
6. Add `/chat/stream` streaming endpoint
7. Add rate limiting, CORS, logging
8. Set up Nginx + HTTPS
9. Register backend as systemd service
10. Build and connect the frontend
11. End-to-end testing of all flows

---

*Document generated from project planning conversation — May 2026*
