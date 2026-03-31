# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project layout
- `backend/`: FastAPI service that generates and stores prompts.
- `frontend/`: React (Create React App + CRACO + Tailwind) UI for submitting commands and displaying generated prompts.
- Root `README.md` is high-level and partially outdated for backend setup; prefer commands below, based on actual files in `backend/` and `frontend/`.

## Development commands
### Backend (`backend/`)
- Install dependencies:
  - `python -m pip install -r backend/requirements.txt`
- Run API locally (from repo root):
  - `python backend/server.py`
  - or `uvicorn backend.server:app --reload --host 0.0.0.0 --port 8001`
- Run the existing backend test/integration script:
  - `python backend/test_llm.py`

### Frontend (`frontend/`)
- Install dependencies:
  - `yarn --cwd frontend install`
- Run dev server:
  - `yarn --cwd frontend start`
- Build production bundle:
  - `yarn --cwd frontend build`
- Run tests:
  - `yarn --cwd frontend test`
- Run a single frontend test file (when test files exist):
  - `yarn --cwd frontend test --watchAll=false src/App.test.js`

### Linting status
- No dedicated lint script is defined in `frontend/package.json` and no separate backend linter config is present.
- Frontend lint checks are primarily surfaced through CRA/CRACO tooling during normal React scripts.

## Runtime configuration
- Backend environment variables:
  - `MONGO_URL` (defaults to `mongodb://localhost:27017`)
  - `EMERGENT_LLM_KEY` (used by health metadata and LLM test script)
- Frontend environment variables:
  - `REACT_APP_BACKEND_URL` (prefix for API calls; empty string by default in `App.js`)

## High-level architecture
### Request flow
1. User enters a command in `frontend/src/App.js`.
2. `handleGenerate` sends `POST /api/generate-prompt` to the backend using `fetch`.
3. `backend/server.py` validates input with `PromptRequest`, generates two prompt variants via `generate_enhanced_prompt`, persists the record to MongoDB (`prompt_engineer_db.prompts`), and returns `PromptResponse`.
4. Frontend stores the response in local component state and renders both prompt variants in tabbed cards with copy-to-clipboard actions.

### Backend design (`backend/server.py`)
- Single FastAPI app with permissive CORS.
- Async MongoDB access via Motor; collection is initialized at module load.
- Core endpoints:
  - `POST /api/generate-prompt`: main generation + persistence path.
  - `GET /api/prompts/{prompt_id}`: fetch a previously stored prompt by UUID.
  - `GET /api/health`: simple runtime health metadata.
- Prompt generation is currently template-based fallback logic (no direct LLM call inside API route).

### Frontend design (`frontend/src/`)
- `App.js` is the primary orchestration component (input, API call lifecycle, loading/error/success state, result rendering).
- UI primitives come from `src/components/ui/*` (Radix/shadcn-style components).
- Utility styling helper `cn()` lives in `src/lib/utils.js`.
- CRACO config (`frontend/craco.config.js`) defines `@` alias to `src` and custom watch/hot-reload behavior.
- Styling stack is Tailwind + PostCSS (`tailwind.config.js`, `postcss.config.js`).

## Notes for future changes
- If backend API contracts change, update `PromptRequest`/`PromptResponse` in `backend/server.py` and the frontend result handling in `frontend/src/App.js` together.
- Keep `REACT_APP_BACKEND_URL` handling consistent with deployment mode; the frontend currently assumes same-origin when unset.
