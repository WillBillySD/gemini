from __future__ import annotations

from fastapi import FastAPI, HTTPException

from .main import run

app = FastAPI(title="Gemini Newsletter API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/run")
def trigger_run() -> dict:
    try:
        result = run()
    except Exception as exc:  # pragma: no cover - surface errors to caller
        raise HTTPException(status_code=500, detail=str(exc))
    return result


@app.get("/run")
def trigger_run_get() -> dict:
    """Allow GET for quick curl testing."""
    return trigger_run()
