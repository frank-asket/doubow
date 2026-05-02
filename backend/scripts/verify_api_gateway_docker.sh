#!/usr/bin/env bash
# Build the repo-root API gateway Dockerfile and confirm POST /v1/agents/job-search-pipeline/run is registered.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
IMAGE_TAG="${DOUBOW_API_IMAGE_TAG:-doubow-api-gateway:verify}"

echo "Building ${IMAGE_TAG} from ${REPO_ROOT}/Dockerfile ..."
docker build -t "${IMAGE_TAG}" -f "${REPO_ROOT}/Dockerfile" "${REPO_ROOT}"

echo "Verifying job-search-pipeline route is registered ..."
docker run --rm "${IMAGE_TAG}" python -c "
from main import app
ok = False
for r in app.routes:
    path = getattr(r, 'path', '') or ''
    if 'job-search-pipeline' in path:
        print('OK:', path, getattr(r, 'methods', None))
        ok = True
if not ok:
    raise SystemExit('route POST /v1/agents/job-search-pipeline/run not found on app')
"

echo "Docker image contains the job-search pipeline route. Deploy this image to Railway to fix 404s from an older build."
