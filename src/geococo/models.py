"""Typed contracts for GeoCOCO orchestration APIs."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class JobSpec:
    """Input contract for pipeline runs."""

    config_path: str | None = None
    params: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class JobResult:
    """Output contract for pipeline runs."""

    status: str
    message: str
    outputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
