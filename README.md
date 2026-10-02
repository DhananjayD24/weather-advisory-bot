# Weather Advisory Bot

Weather Advisory Bot is a full-stack weather-safety assistant. It turns a
natural-language activity question into a structured request, retrieves
location and forecast data from Open-Meteo, evaluates deterministic safety
policies, and returns traceable guidance through a React chat interface.

This directory is a standalone Git repository with two applications:

- `backend/`: FastAPI API and LangGraph workflow
- `frontend/`: React 19/Vite web client

## Prerequisites

- Python 3.11 or newer
- Node.js 18 or newer and npm
- A Google Gemini API key for query parsing
- Internet access for Gemini, Open-Meteo geocoding, and Open-Meteo forecast
  requests

## Backend setup and run

From the repository root, create and activate a virtual environment:

```powershell
python -m venv backend\.venv
.\backend\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Create `backend\.env` (this file is ignored by Git) and add:

```dotenv
GOOGLE_API_KEY=your-gemini-api-key
```

Start the API from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://127.0.0.1:8000`. Useful endpoints:

- `GET /health` returns `{"status": "ok"}`.
- `POST /chat` accepts `{"message": "...", "session_id": "..."}` and returns
  the advisory response.
- `GET /docs` opens the generated FastAPI/OpenAPI documentation.

Example API request:

```powershell
Invoke-RestMethod `
  -Uri http://127.0.0.1:8000/chat `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message":"Is it safe to cycle in Bhopal today?","session_id":"demo"}'
```

## Frontend setup and run

In a second terminal:

```powershell
Set-Location frontend
npm install
Copy-Item .env.example .env
npm run dev
```

The Vite development server prints its local URL, normally
`http://localhost:5173`. The provided `frontend\.env.example` points the
client at `http://127.0.0.1:8000`; change `VITE_BACKEND_URL` if the API is
running elsewhere.

Production build and local preview:

```powershell
npm run build
npm run preview
```

## LangGraph implementation

The workflow is defined in `backend/app/graph/graph.py` and uses
`WeatherState` from `backend/app/graph/state.py`. A `MemorySaver` checkpointer
uses the API's `session_id` as the LangGraph `thread_id`, allowing context to
persist during a chat session.

The graph follows this path:

```text
START
  -> parse_query
  -> check_context
       -> resolve_location (when coordinates are not already known)
       -> fetch_weather
  -> match_sops
       -> resolve_policy (when one or more SOPs match)
       -> no_guidance (when no SOP matches)
  -> generate_response
  -> END
```

Each failure branch (`parse_error`, `location_error`, and `weather_error`) ends
in `generate_response` with an explicit, non-guessing error message. Query
parsing is the LLM-assisted step; SOP matching, priority/severity resolution,
weather-period selection, and response construction are deterministic Python
logic.

## SOPs

SOPs are stored in `backend/app/policies/sops.json` and loaded by
`backend/app/services/sop_service.py`. Each policy declares its activity
scope, conditions, priority, severity, action, and user-facing guidance.
Supported policy checks include numeric thresholds, weather codes, favorable
weather, and fuzzy weather assessment.

**Format choice:** JSON was chosen because these rules are structured,
version-controllable configuration that can be reviewed and edited without
changing the policy engine code.

When multiple policies match, the resolver chooses the highest severity; a
priority value breaks ties. If required weather data is missing, the engine
returns an explicit incomplete-data error rather than inventing a result.

## Evaluation suite

The automated backend evaluation suite is the pytest files under
`backend/app/**/test_*.py`. It covers:

- SOP loading and activity/condition matching
- severe-weather and favorable-weather cases
- severity and priority resolution
- no-match behavior
- response traceability and honest error responses
- conversation-context retention and invalidation when activity, location, or
  time changes
- graph import/compilation

Run it from the repository root:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest backend\app -q
```

### Latest local results

| Check | Command | Result |
| --- | --- | --- |
| Backend unit/evaluation suite | `python -m pytest backend\app -q` | **16 passed** |
| Frontend lint | `Set-Location frontend; npm run lint` | **Passed** |
| Frontend production build | `Set-Location frontend; npm run build` | **Passed** |

### Honest limitations and failures

- The 16 passing tests are deterministic unit/evaluation tests; they do not
  prove that external services are available.
- `backend/app/services/test_llm.py` and
  `backend/app/services/test_weather_service.py` are manual smoke scripts, not
  pytest tests. They require a valid Gemini key and network access and were not
  included in the 16-test result.
- There are currently no automated browser/end-to-end frontend tests.
- Live behavior can fail because Gemini, Open-Meteo geocoding, or Open-Meteo
  forecast services can time out, reject requests, or return incomplete data.
  The API surfaces those failures as explicit responses rather than silently
  returning advice.

## Repository safety

Do not commit `backend\.env` or `frontend\.env`; both are ignored. Use the
checked-in `frontend\.env.example` as the frontend template and provide API
keys only through local environment files.
