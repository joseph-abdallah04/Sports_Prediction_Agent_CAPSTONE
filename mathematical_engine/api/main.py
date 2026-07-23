"""FastAPI application for the NRL mathematical engine.

Start (from mathematical_engine/):
    uv run uvicorn api.main:app --host 127.0.0.1 --port 8000

Interactive docs: http://127.0.0.1:8000/docs

Design notes (see Architecture.md in this directory):
- Serves predictions only. Never scrapes, rebuilds features, or retrains -
  that is the weekly ETL's job. The only link between the two is models/.
- Artifacts hot-reload when models/metrics.json changes on disk, so the
  server keeps running across weekly ETL runs without a restart.
- Binds to localhost by default; no auth (capstone MVP - see Architecture.md).
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from model.serving import ModelNotTrainedError, get_bundle

from .routes import router

logger = logging.getLogger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Warm the model at startup so the first /predict is not slow.

    A missing model is not fatal: the server starts in degraded mode and
    /health reports it, so the operator can run the weekly ETL and the next
    request will load the fresh artifacts automatically.
    """
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    try:
        bundle = get_bundle()
        logger.info(
            "Model warmed: trained_at=%s, %s rows",
            bundle.metrics.get("trained_at"), bundle.metrics.get("n_training_rows"),
        )
    except ModelNotTrainedError as e:
        logger.warning("Starting without a model: %s", e)
    yield


app = FastAPI(
    title="NRL Mathematical Engine",
    description=(
        "Deterministic prediction core for the Sports Prediction Agent. "
        "The LLM Orchestrator calls POST /predict to get a calibrated win "
        "probability plus SHAP-based reasoning for an upcoming NRL fixture."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# Local agent development: allow browser-based or cross-process localhost callers.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)
