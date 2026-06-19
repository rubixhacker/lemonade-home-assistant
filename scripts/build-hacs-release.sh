#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DIST_DIR="${ROOT_DIR}/dist"
BUILD_DIR="${DIST_DIR}/hacs"
ASSET="${DIST_DIR}/lemonade.zip"

rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}/custom_components"
cp -R "${ROOT_DIR}/lemonade" "${BUILD_DIR}/custom_components/lemonade"
find "${BUILD_DIR}" \( -type d -name "__pycache__" -o -type f -name "*.pyc" \) -prune -exec rm -rf {} +

rm -f "${ASSET}"
(
  cd "${BUILD_DIR}"
  zip -qr "${ASSET}" custom_components
)

echo "Built ${ASSET}"
