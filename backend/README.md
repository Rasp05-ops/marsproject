# CampusIQ Backend

FastAPI backend for the unified campus dashboard. It exposes REST APIs for each campus data source and a lightweight MCP-style tool interface used by the assistant route.

## Run locally

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs:

```text
http://localhost:8000/docs
```

Health check:

```text
http://localhost:8000/health
```

## LLM / Assistant notes

The assistant can optionally use an external LLM (OpenAI) to plan which MCP tools to call and to synthesize
natural-language answers. If you don't provide an API key the backend will continue to work using a simple
rule-based router.

Environment variables:

- `OPENAI_API_KEY` — (optional) your OpenAI API key. When set, the backend will attempt to use the OpenAI
	Python SDK to plan and generate assistant responses.
- `OPENAI_MODEL` — (optional) model name (defaults to `gpt-4o-mini`).

- `OPENAI_MODEL` — (optional) model name (defaults to `gpt-4o-mini`).
- `LLM_PROVIDER` — (optional) choose the LLM provider: `google` or `openai`. If empty the backend will autodetect available providers (prefers Google if available).
- `GOOGLE_API_KEY` — (optional) your Google API key to use Gemini/Google Generative AI.
- `GOOGLE_MODEL` — (optional) Google model name (defaults to `gemini-1.5-mini`).

When adding an API key, install the updated requirements and restart the backend:

```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

If no LLM is configured the assistant falls back to the existing keyword-based tool router and will still
return results from the local MCP functions.

## Microservices (production-style)

This repository supports running MCP servers as separate microservices using Docker Compose.
Each MCP service runs a small FastAPI app that exposes the same endpoints as the in-process
servers. The orchestrator backend can be configured to call those services instead of
the local Python `SERVERS` map.

To run everything with docker-compose:

```bash
docker compose build
docker compose up
```

Services and default ports exposed by compose:
- backend (orchestrator): 8000
- frontend (Vite dev): 5173
- mcp_library: 8001
- mcp_cafeteria: 8002
- mcp_events: 8003
- mcp_academics: 8004
- mcp_notices: 8005

When `USE_MICROSERVICES=true` (set in environment or through compose), the backend
will forward MCP calls to these microservices. This mode is closer to the project
requirement for "independent MCP Servers".
