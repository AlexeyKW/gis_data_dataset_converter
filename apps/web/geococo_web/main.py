"""FastAPI MVP application for running GeoCOCO pipeline."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel, Field

from geococo.api import run_pipeline
from geococo.models import JobResult, JobSpec

app = FastAPI(
    title="GeoCOCO Web",
    version="0.1.0",
    docs_url="/docs",
    openapi_url="/openapi.json",
    redoc_url="/redoc",
)


class RunRequest(BaseModel):
    config_path: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run")
def run(request: RunRequest) -> dict[str, Any]:
    spec = JobSpec(config_path=request.config_path, params=dict(request.params))
    result: JobResult = run_pipeline(job_spec=spec)
    return asdict(result)
