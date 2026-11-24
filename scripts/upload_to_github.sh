#!/usr/bin/env bash
# Publishes this repo to GitHub under the Adamson-lab organisation. Run from the repo root after extracting the zip.
# Prereqs: git, and either the GitHub CLI (gh auth login) or an empty repo already created in the browser.
set -euo pipefail
cd "$(dirname "$0")/.."
ORG="${1:-Adamson-lab}"; REPO="${2:-tag-governance-enforcer-multicloud}"
EMAIL="${GIT_AUTHOR_EMAIL:-favouradamson803@gmail.com}"; NAME="${GIT_AUTHOR_NAME:-Favour Adamson}"
DESC="Org-wide tag and label enforcement across AWS, Azure and GCP: one standard, preventive + detective + corrective controls."
TOPICS="multicloud enterprise-architecture finops governance terraform aws azure gcp opa policy-as-code togaf c4-model archimate tagging"
[ -d .git ] || git init -b main
git config user.email "$EMAIL"; git config user.name "$NAME"
git add -A && git commit -m "feat: initial release of tag governance enforcer (v1.0.0)" || echo "nothing to commit"
if command -v gh >/dev/null 2>&1; then
  gh repo create "$ORG/$REPO" --public --description "$DESC" --source . --remote origin --push || git push -u origin main
  for t in $TOPICS; do gh repo edit "$ORG/$REPO" --add-topic "$t" >/dev/null || true; done
else
  git remote get-url origin >/dev/null 2>&1 || git remote add origin "https://github.com/$ORG/$REPO.git"
  git push -u origin main
fi
echo "Done: https://github.com/$ORG/$REPO  (next: set social preview to diagrams/svg/08-multicloud-topology.svg exported as PNG, enable branch protection, Dependabot, secret scanning)"
