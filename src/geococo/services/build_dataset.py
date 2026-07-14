"""Dataset build orchestrator.

This module contains a thin orchestration layer that tries to reuse existing
project entry-points when available (CLI/pipeline modules) and otherwise
returns a meaningful bootstrap result.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any

from geococo.models import JobResult, JobSpec


def build_dataset(
    config_path: str | Path | None = None,
    *,
    job_spec: JobSpec | None = None,
    **kwargs: Any,
) -> JobResult:
    """Orchestrate dataset build using existing project functionality.

    Reuse strategy (best effort, no hard dependency):
    1. If ``geococo.cli`` has callable ``run_pipeline`` -> call it.
    2. Else if ``geococo.pipeline`` has callable ``run_pipeline`` -> call it.
    3. Else return a bootstrap payload describing current status.

    Parameters
    ----------
    config_path:
        Optional path to configuration file.
    **kwargs:
        Optional parameters for downstream runners.
    """

    resolved_spec = _resolve_job_spec(
        config_path=config_path,
        job_spec=job_spec,
        kwargs=kwargs,
    )

    normalized_config = (
        Path(resolved_spec.config_path) if resolved_spec.config_path is not None else None
    )

    from_service = bool(resolved_spec.params.get("_from_service", False))
    params = dict(resolved_spec.params)
    params.pop("_from_service", None)
    resolved_spec = JobSpec(config_path=resolved_spec.config_path, params=params)

    if not from_service:
        cli_spec = JobSpec(
            config_path=resolved_spec.config_path,
            params={**resolved_spec.params, "_from_service": True},
        )
        delegated = _delegate_to_existing_runner(
            module_name="geococo.cli",
            func_name="run_pipeline",
            job_spec=cli_spec,
            config_path=normalized_config,
            _from_service=True,
            **resolved_spec.params,
        )
        if delegated is not None:
            return delegated

    delegated = _delegate_to_existing_runner(
        module_name="geococo.pipeline",
        func_name="run_pipeline",
        job_spec=resolved_spec,
        config_path=normalized_config,
        **resolved_spec.params,
    )
    if delegated is not None:
        return delegated

    return JobResult(
        status="bootstrap",
        message=(
            "GeoCOCO orchestration layer initialized. "
            "No legacy run_pipeline entry-point found yet."
        ),
        outputs={
            "config_path": str(normalized_config) if normalized_config else None,
            "params": dict(resolved_spec.params),
        },
        metadata={"orchestrator": "geococo.services.build_dataset"},
    )


def _resolve_job_spec(
    config_path: str | Path | None,
    job_spec: JobSpec | None,
    kwargs: dict[str, Any],
) -> JobSpec:
    if job_spec is not None:
        return JobSpec(
            config_path=job_spec.config_path,
            params=dict(job_spec.params),
        )

    return JobSpec(
        config_path=str(config_path) if config_path is not None else None,
        params=dict(kwargs),
    )


def _delegate_to_existing_runner(
    module_name: str,
    func_name: str,
    job_spec: JobSpec,
    config_path: Path | None,
    **kwargs: Any,
) -> JobResult | None:
    try:
        module = import_module(module_name)
    except Exception:
        return None

    runner = getattr(module, func_name, None)
    if not callable(runner):
        return None

    result = runner(job_spec=job_spec, config_path=config_path, **kwargs)
    if isinstance(result, JobResult):
        return result
    if isinstance(result, dict):
        return JobResult(
            status=str(result.get("status", "ok")),
            message=str(result.get("message", "Completed")),
            outputs={"payload": result},
            metadata={"runner": f"{module_name}.{func_name}", "coerced": True},
        )

    return JobResult(
        status="ok",
        message="Completed via delegated runner",
        outputs={"result": result},
        metadata={"runner": f"{module_name}.{func_name}"},
    )
