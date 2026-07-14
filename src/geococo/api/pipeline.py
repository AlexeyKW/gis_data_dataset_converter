"""Public pipeline facade.

This module provides a stable public entry-point that delegates orchestration
to the service layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from geococo.models import JobResult, JobSpec
from geococo.services.build_dataset import build_dataset


def run_pipeline(
    config_path: str | Path | None = None,
    *,
    job_spec: JobSpec | None = None,
    **kwargs: Any,
) -> JobResult:
    """Run GeoCOCO pipeline via service orchestrator.

    Parameters
    ----------
    config_path:
        Optional path to a configuration file.
    **kwargs:
        Additional keyword arguments forwarded to service layer.

    job_spec:
        Typed input contract. If provided, takes precedence over explicit
        ``config_path``/``**kwargs`` parameters.
    """

    if job_spec is None:
        job_spec = JobSpec(
            config_path=str(config_path) if config_path is not None else None,
            params=dict(kwargs),
        )

    return build_dataset(config_path=config_path, job_spec=job_spec, **kwargs)
