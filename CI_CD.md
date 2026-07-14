# CI/CD Setup (Docker on self-hosted runner)

This repository includes two GitHub Actions workflows that run on a self-hosted Linux runner.

## Files

- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`
- `Dockerfile`
- `.dockerignore`
- `requirements.txt`

## Runner requirements

Use a GitHub Actions self-hosted runner with labels:

- `self-hosted`
- `linux`

The runner host must have:

- Docker engine installed and running
- `curl` available in PATH
- Network access to GitHub for checkout

## GitHub environments

Create environments in the repository settings:

- `staging`
- `production`

Optional but recommended:

- Add required reviewers for `production`
- Add branch protection for `main`

## Workflow behavior

### CI (`ci.yml`)

- Triggers on `push` and `pull_request`
- Builds Docker image locally on runner
- Runs a test container on port `18000`
- Calls `GET /health` until healthy or timeout
- Always removes test container at the end

### CD (`cd.yml`)

- Triggers on `push` to `main` and manual `workflow_dispatch`
- `deploy-staging` runs first:
  - Builds image tagged with commit SHA
  - Replaces `geococo-web-staging` container on port `8001`
  - Performs `/health` check
- `deploy-production` runs only after staging succeeds:
  - Builds image tagged with commit SHA
  - Replaces `geococo-web-production` container on port `8000`
  - Performs `/health` check

Both deploy jobs safely remove any existing container with the same name before starting a new one.
