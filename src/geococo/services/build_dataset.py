"""Dataset build orchestrator.

This module contains a thin orchestration layer that tries to reuse existing
project entry-points when available (CLI/pipeline modules) and otherwise
returns a meaningful bootstrap result.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any


def build_dataset(config_path: str | Path | None = None, **kwargs: Any) -> dict[str, Any]:
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

    normalized_config = Path(config_path) if config_path is not None else None

    delegated = _delegate_to_existing_runner(
        module_name="geococo.cli",
        func_name="run_pipeline",
        config_path=normalized_config,
        **kwargs,
    )
    if delegated is not None:
        return delegated

    delegated = _delegate_to_existing_runner(
        module_name="geococo.pipeline",
        func_name="run_pipeline",
        config_path=normalized_config,
        **kwargs,
    )
    if delegated is not None:
        return delegated

    return {
        "status": "bootstrap",
        "message": (
            "GeoCOCO orchestration layer initialized. "
            "No legacy run_pipeline entry-point found yet."
        ),
        "config_path": str(normalized_config) if normalized_config else None,
        "params": kwargs,
    }


def _delegate_to_existing_runner(
    module_name: str,
    func_name: str,
    config_path: Path | None,
    **kwargs: Any,
) -> dict[str, Any] | None:
    try:
        module = import_module(module_name)
    except Exception:
        return None

    runner = getattr(module, func_name, None)
    if not callable(runner):
        return None

    result = runner(config_path=config_path, **kwargs)
    if isinstance(result, dict):
        return result

    return {
        "status": "ok",
        "runner": f"{module_name}.{func_name}",
        "result": result,
    }
