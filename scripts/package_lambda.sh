#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
rm -rf dist && mkdir -p dist/build
cp -r src/tagenforcer dist/build/ && mkdir -p dist/build/policies && cp policies/tag-standard.json dist/build/policies/
(cd dist/build && python3 -c "import shutil; shutil.make_archive('../enforcer','zip','.')")
echo "built dist/enforcer.zip"
