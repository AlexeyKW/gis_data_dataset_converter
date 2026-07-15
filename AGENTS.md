# AGENTS.md

## What this repo is
- GeoCOCO: a Python geospatial pipeline that converts GeoTIFF + SHP/GPKG inputs into COCO instance-segmentation outputs plus geospatial index files (`README.MD`).

## Real entrypoints (use these, not guesses)
- Web API app: `apps/web/geococo_web/main.py` (served as `geococo_web.main:app`).
- Public pipeline API: `src/geococo/api/pipeline.py` (`run_pipeline`).
- CLI entrypoint: `src/geococo/cli.py`.
- Data contracts: `src/geococo/models.py` (`JobSpec`, `JobResult`).

## Known-good run commands
- Web dev server:
  - `uvicorn geococo_web.main:app --app-dir apps/web --reload`
- CLI run:
  - `python -m geococo.cli --config path/to/config.yaml --param key=value`

## Setup and env gotchas
- Python 3.10+ is expected.
- If package import fails, set `PYTHONPATH=src` (docs rely on this layout).
- GIS native deps (GDAL/GEOS/PROJ) may be required depending on which modules you execute.

## Pipeline outputs and invariants to preserve
- Do not treat COCO export alone as success; this project is designed to emit both ML artifacts and geospatial index artifacts.
- Keep manifest/provenance outputs intact when changing pipeline code (`ARCHITECTURE.md` describes `dataset_manifest.json`, tile/annotation index outputs).

## CI/CD realities (important)
- CI is GitLab-based (`.gitlab-ci.yml`), not GitHub Actions.
- Stages: CI (build + health check), staging deploy (default branch), production deploy (manual trigger).
- Port conventions used by CI/CD docs: test `18000`, staging `8001`, production `8000`.
- Health endpoint is expected at `GET /health`.

## Verification guidance for agents
- There is no clearly defined repo-wide lint/typecheck/test command in current root config; do focused verification for changed entrypoints instead of inventing global commands.
- For API changes: verify `GET /health` and `POST /run` behavior.
- For CLI changes: run a focused `python -m geococo.cli ...` invocation and confirm `JobResult` shape remains stable.

## GIS rules
- Всегда считать ARCHITECTURE.md источником истины по схемам и контрактам (ARCHITECTURE.md).
- Любая обработка геоданных без явного указания CRS — ошибка, не предупреждение.
- Изменил публичный контракт — обнови документацию и примеры одновременно.