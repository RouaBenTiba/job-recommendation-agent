#!/usr/bin/env bash
# Usage : REPO=utilisateur/job-recommender ./scripts/protect-branches.sh
# Prérequis : gh CLI authentifié avec les droits admin, branches main et develop déjà poussées.
# REVIEWS=0 si tu travailles seule (tu ne peux pas approuver ta propre PR).
set -euo pipefail
: "${REPO:?Définir REPO=utilisateur/depot}"
REVIEWS="${REVIEWS:-1}"

for branch in main develop; do
  echo "Protection de $branch..."
  gh api -X PUT "repos/$REPO/branches/$branch/protection" --input - <<JSON
{
  "required_status_checks": { "strict": true, "contexts": ["CI OK"] },
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": $REVIEWS },
  "restrictions": null
}
JSON
done
