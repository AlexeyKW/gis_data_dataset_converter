"""Command-line entrypoint for running GeoCOCO pipeline."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from typing import Any

from geococo.api import run_pipeline
from geococo.models import JobResult, JobSpec


def run_pipeline_cli(config_path: str | None = None, **kwargs: Any) -> JobResult:
    """Adapter used by CLI/tests to run the public API facade."""

    spec = JobSpec(config_path=config_path, params=dict(kwargs))
    return run_pipeline(job_spec=spec)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run GeoCOCO pipeline")
    parser.add_argument("--config", dest="config_path", default=None)
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Pipeline param as key=value (can be repeated)",
    )
    args = parser.parse_args()

    params: dict[str, Any] = {}
    for item in args.param:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        params[key] = value

    result = run_pipeline_cli(config_path=args.config_path, **params)
    print(json.dumps(asdict(result), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
