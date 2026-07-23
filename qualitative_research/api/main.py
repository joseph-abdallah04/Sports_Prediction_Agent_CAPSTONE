"""FastAPI app for the qualitative research tool.

Start (from qualitative_research/):
    uv run uvicorn api.main:app --host 127.0.0.1 --port 8001
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    yield


app = FastAPI(
    title="NRL Qualitative Research Tool",
    description=(
        "Zero-cost multi-channel research for upcoming NRL fixtures. "
        "Returns structured facts (nrl.com, news search, Reddit) for the Orchestrator. "
        "No LLM analysis."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(router)
