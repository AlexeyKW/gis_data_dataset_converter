# CI/CD Setup (GitLab CI on self-hosted runner)

This repository uses GitLab CI/CD with Docker jobs executed on a self-hosted GitLab Runner.

## Files

- `.gitlab-ci.yml`
- `Dockerfile`
- `.dockerignore`
- `requirements.txt`

## 1) Register and configure self-hosted GitLab Runner

Register a runner for your GitLab project/group and ensure it has these tags:

- `self-hosted`
- `linux`

The pipeline jobs are tagged with those values by default, so the runner tags must match.

Runner host requirements:

- Docker Engine installed and running
- `curl` available in PATH
- Runner user can run Docker commands (docker socket/group access)
- Network access to GitLab and container/image dependencies

Recommended runner settings:

- Limit runner to trusted projects only
- Protect default branch in GitLab
- Use protected runners for production paths

## 2) Required variables / secrets

Set CI/CD variables in **GitLab → Settings → CI/CD → Variables**.

At minimum, use protected/masked variables for any environment-specific secrets your app needs (for example DB URLs, API keys, app secrets).

Suggested placement:

- **Staging secrets**: environment scope `staging` (or unscoped if shared)
- **Production secrets**: environment scope `production`, marked **Protected**

If production is protected, run production deploys only from protected branches/tags.

## 3) Pipeline trigger behavior

Defined in `.gitlab-ci.yml` with stages:

1. `ci`
2. `deploy_staging`
3. `deploy_production`

### CI job (`ci_docker_healthcheck`)

- Runs for merge requests and branch pipelines
- Builds Docker image
- Starts test container on host port `18000`
- Polls `GET /health` until success or timeout
- Always cleans up test container in `after_script`

### Staging deploy (`deploy_staging`)

- Runs only on the default branch
- Builds image tagged with current commit SHA
- Replaces container `geococo-staging` on port `8001`
- Runs health check on `/health`

### Production deploy (`deploy_production`)

- Runs only on the default branch
- Depends on successful staging deploy
- Manual trigger required (`when: manual`)
- Builds image tagged with commit SHA
- Replaces container `geococo-prod` on port `8000`
- Runs health check on `/health`

All shell scripts use `set -euo pipefail` and safe container removal (`docker rm -f <name> || true`).

## 4) How to run production deploy manually

1. Open **GitLab → CI/CD → Pipelines**.
2. Open a pipeline from the default branch where staging passed.
3. Click **Play** on `deploy_production`.
4. Monitor job logs and verify health-check success.

## 5) Quick troubleshooting

- **Job stuck / no runner**: verify runner is online and has tags `self-hosted`, `linux`.
- **Docker permission errors**: ensure runner user has Docker access.
- **Port already in use**: confirm no conflicting services on `18000`, `8001`, `8000`.
- **Health check fails**: inspect container logs from job output; verify app listens on container port `8000` and `/health` path is correct.
- **Manual production missing**: ensure pipeline is on default branch and `deploy_staging` succeeded.
