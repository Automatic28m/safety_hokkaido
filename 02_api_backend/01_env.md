# Environment

- Python 3.11+ and FastAPI/Uvicorn
- Install dependencies with `pip install -r requirements.txt`
- Copy `.env.example` to `.env`; never commit the resulting file.

## API-layer environment variables

| Variable | Default | Purpose |
|---|---|---|
| `ALLOWED_ORIGINS` | `http://localhost:3000` | Comma-separated list of CORS origins allowed to call this API. `*` is always stripped. |
| `ENABLE_DEBUG_ENDPOINTS` | `false` | Set to `true` to expose `/reset_memory`. Keep off in shared environments since `global_memory` is shared across every user. |

## Running the API contract tests

```powershell
cd 02_api_backend
pip install -r requirements-dev.txt
python -m pytest -q
```

The tests build the FastAPI app from `api/app.py` with a fake pipeline, so they run without Groq, FAISS, or network access.

