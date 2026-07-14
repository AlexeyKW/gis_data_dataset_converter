"""Public pipeline facade.

This module provides a stable public entry-point that delegates orchestration
to the service layer.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from geococo.services.build_dataset import build_dataset


def run_pipeline(config_path: str | Path | None = None, **kwargs: Any) -> dict[str, Any]:
    """Run GeoCOCO pipeline via service orchestrator.

    Parameters
    ----------
    config_path:
        Optional path to a configuration file.
    **kwargs:
        Additional keyword arguments forwarded to service layer.

    Returns
    -------
    dict[str, Any]
        Orchestrator result payload.
    """

    return build_dataset(config_path=config_path, **kwargs)
