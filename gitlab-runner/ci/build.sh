#!/bin/bash

set -euo pipefail
set +x

IMAGE_REPO=$1
IMAGE_TAG=$2

if [[ -z "${IMAGE_REPO}" ]]; then
  echo "IMAGE_REPO is required" >&2
  exit 1
fi

if [[ -z "${IMAGE_TAG}" ]]; then
  echo "IMAGE_TAG is required" >&2
  exit 1
fi

echo "===== Build Image ${IMAGE_REPO}:${IMAGE_TAG} ====="

buildctl build \
--frontend dockerfile.v0 \
--local context=. \
--local dockerfile=. \
--export-cache type=registry,ref=${IMAGE_REPO}:cache \
--import-cache type=registry,ref=${IMAGE_REPO}:cache \
--output type=image,\"name=${IMAGE_REPO}:${IMAGE_TAG},${IMAGE_REPO}:latest\",push=true