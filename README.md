# CampusIQ

CampusIQ is a full-stack campus dashboard and assistant for students. It brings together library availability, cafeteria menus, campus events, academic details, attendance, exams, and notices into one React interface, backed by a FastAPI service and MCP-style campus data tools.

The project is built to work in two modes:

- A simple in-process backend mode for local development and single-service deployment.
- A microservice mode where each campus domain runs as an independent MCP-style FastAPI service.

## Features

- Student dashboard with borrowed books, weekly events, attendance, and urgent notices.
- Library book search, availability stats, and reservation flow.
- Cafeteria menus for breakfast, lunch, snacks, and dinner.
- Event listings with tags and upcoming event summaries.
- Academic profile, CGPA, course attendance, low-attendance checks, and exam schedule data.
- Campus notice board with urgent notice filtering.
- Campus AI assistant that can call campus tools and optionally use an LLM to plan and summarize answers.
- LLM fallback visibility so the UI can show whether responses came from an LLM or deterministic campus data.

## Tech Stack

- Frontend: React 18, Vite, plain CSS.
- Backend: FastAPI, Pydantic, HTTPX.
- LLM providers: Google Gemini via `google-genai`, OpenAI via the OpenAI Python SDK.
- Deployment: Vercel frontend, Render backend.
- Optional local orchestration: Docker Compose with separate MCP microservices.

## Repository Structure

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI orchestrator API
│   │   ├── data.py                  # Demo campus data
│   │   ├── models.py                # Pydantic response/request models
│   │   ├── mcp_servers/             # In-process MCP-style domain servers
│   │   └── services/
│   │       ├── assistant.py          # Tool routing and assistant response flow
│   │       └── llm.py                # Google/OpenAI integration and status
│   ├── microservices/               # Standalone MCP service apps
│   ├── Dockerfile
│   ├── integration_test.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx                  # Dashboard and assistant UI
│   │   └── styles.css
│   ├── package.json
│   └── vite.config.js
└── docker-compose.yml
```

## Local Setup

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Useful URLs:

```text
http://localhost:8000/health
http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:8000` for the backend. You can override it with:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Environment Variables

### Backend

Set these in `backend/.env` for local development or in Render for production:

```env
FRONTEND_ORIGIN=http://localhost:5173
LLM_PROVIDER=google
GOOGLE_API_KEY=your_google_api_key
GOOGLE_MODEL=gemini-3.1-flash-lite
```

Supported backend variables:

- `FRONTEND_ORIGIN`: Comma-separated allowed frontend origins. Example: `https://your-app.vercel.app,http://localhost:5173`.
- `LLM_PROVIDER`: Optional provider selection: `google` or `openai`. If omitted, the backend autodetects configured keys and prefers Google.
- `GOOGLE_API_KEY`: Gemini API key.
- `GOOGLE_MODEL`: Gemini model name. Default: `gemini-3.1-flash-lite`.
- `OPENAI_API_KEY`: OpenAI API key.
- `OPENAI_MODEL`: OpenAI model name. Default: `gpt-4o-mini`.
- `USE_MICROSERVICES`: Set to `true` to route domain calls through the standalone MCP services.
- `MCP_LIBRARY_URL`, `MCP_CAFETERIA_URL`, `MCP_EVENTS_URL`, `MCP_ACADEMICS_URL`, `MCP_NOTICES_URL`: Optional MCP service URLs.

### Frontend

Set this in Vercel:

```env
VITE_API_BASE_URL=https://your-render-backend.onrender.com
```

## API Overview

Main backend endpoints:

- `GET /health`
- `GET /api/dashboard`
- `GET /api/library/books`
- `GET /api/library/stats`
- `POST /api/library/books/{book_id}/reserve`
- `GET /api/cafeteria/menu`
- `GET /api/cafeteria/menu/{meal}`
- `GET /api/events`
- `GET /api/academics`
- `GET /api/academics/low-attendance`
- `GET /api/notices`
- `POST /api/assistant/query`
- `GET /api/mcp/tools`
- `POST /api/mcp/call`

The assistant response includes `llm_status`, so the frontend can distinguish between LLM answers, deterministic fallback answers, and canned small-talk/help responses.

## Assistant Flow

1. The user sends a message from the React sidebar.
2. The backend first handles simple greetings and help prompts directly.
3. For campus questions, the assistant tries to use the configured LLM to plan MCP tool calls.
4. If no LLM is configured, or the LLM call fails, it falls back to deterministic keyword routing.
5. Campus tools return structured data.
6. The LLM summarizes the results when available; otherwise the backend returns a factual fallback answer.

This keeps the assistant useful even without an LLM API key.

## Microservice Mode

Run the full local stack with independent MCP services:

```bash
docker compose build
docker compose up
```

Default ports:

- Backend orchestrator: `8000`
- Frontend Vite dev server: `5173`
- Library MCP: `8001`
- Cafeteria MCP: `8002`
- Events MCP: `8003`
- Academics MCP: `8004`
- Notices MCP: `8005`

The Docker Compose backend sets `USE_MICROSERVICES=true`, so the orchestrator forwards domain calls to the MCP services.

## Deployment

### Render Backend

Use the `backend/` directory as the service root.

Typical build command:

```bash
pip install -r requirements.txt
```

Typical start command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Important Render env vars:

```env
FRONTEND_ORIGIN=https://your-vercel-app.vercel.app
LLM_PROVIDER=google
GOOGLE_API_KEY=your_valid_google_api_key
GOOGLE_MODEL=gemini-3.1-flash-lite
```

### Vercel Frontend

Use the `frontend/` directory as the project root.

Build command:

```bash
npm run build
```

Output directory:

```text
dist
```

Important Vercel env var:

```env
VITE_API_BASE_URL=https://your-render-backend.onrender.com
```

## Troubleshooting

- If the UI says the backend is offline, check `VITE_API_BASE_URL` in Vercel and `FRONTEND_ORIGIN` in Render.
- If the assistant gives static-looking campus summaries, check the `llm_status` field in `/api/assistant/query` or the assistant header in the UI.
- If `llm_status.mode` is `fallback`, verify that the provider API key is valid and that the configured model exists.
- If Render redeploys but behavior does not change, confirm the latest commit is pushed to GitHub and Render deployed that commit.
- If Vercel still shows old UI text, trigger a fresh Vercel deployment and hard refresh the browser.

## Smoke Tests

With the backend running:

```bash
cd backend
source .venv/bin/activate
python integration_test.py
```

For frontend build validation:

```bash
cd frontend
npm run build
```

## Project Status

CampusIQ currently uses demo in-memory campus data. It is structured so each data domain can later be connected to real institute services, databases, or authenticated MCP tools without changing the frontend workflow.
