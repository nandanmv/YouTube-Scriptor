#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

REMOTE_HOST="${REMOTE_HOST:-188.245.84.61}"
REMOTE_PORT="${REMOTE_PORT:-569}"
REMOTE_USER="${REMOTE_USER:-nandanm}"
REMOTE_KEY="${REMOTE_KEY:-$HOME/.ssh/id_ed25519_nandanm_hetzner}"
REMOTE_REPO_PATH="${REMOTE_REPO_PATH:-/home/nandanm/apps/YouTube-Scriptor}"
APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-3010}"
APP_LOG="${APP_LOG:-nohup.out}"
BRANCH="${BRANCH:-master}"
AUTO_COMMIT="${AUTO_COMMIT:-0}"
COMMIT_MESSAGE="${COMMIT_MESSAGE:-Deploy commit}"
SERVER_STASH="${SERVER_STASH:-0}"

cd "$ROOT_DIR"

if ! git diff --quiet || ! git diff --cached --quiet || [ -n "$(git ls-files --others --exclude-standard)" ]; then
  if [ "$AUTO_COMMIT" = "1" ]; then
    echo "Auto-committing local changes..."
    git add -A
    git commit -m "$COMMIT_MESSAGE"
  else
    echo "Uncommitted changes found. Commit or stash before deploy."
    echo "To auto-commit and deploy:"
    echo 'AUTO_COMMIT=1 COMMIT_MESSAGE="your message" ./scripts/deploy_server.sh'
    exit 1
  fi
fi

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
  echo "Deploying current branch '$CURRENT_BRANCH' to origin/$BRANCH."
fi

echo "Pushing to origin/$BRANCH..."
git push origin "HEAD:$BRANCH"

REMOTE_CMD=$(cat <<EOF
set -euo pipefail
cd "$REMOTE_REPO_PATH"
if [ -n "\$(git status --short)" ]; then
  echo "Server repo has local changes:"
  git status --short
  if [ "$SERVER_STASH" = "1" ]; then
    git stash push -u -m "auto-stash before deploy"
  else
    echo "Set SERVER_STASH=1 to auto-stash server changes before pull."
    exit 1
  fi
fi
git pull --ff-only origin "$BRANCH"
echo "Server commit: \$(git rev-parse --short HEAD)"
if command -v fuser >/dev/null 2>&1; then
  fuser -k "$APP_PORT"/tcp || true
fi
pkill -f "python3.10 main.py serve" || true
pkill -f "uvicorn.*$APP_PORT" || true
sleep 2
nohup python3.10 main.py serve --host "$APP_HOST" --port "$APP_PORT" > "$APP_LOG" 2>&1 &
for _ in {1..20}; do
  if curl -fsS "http://$APP_HOST:$APP_PORT/health" >/dev/null; then
    break
  fi
  sleep 1
done
curl -fsS "http://$APP_HOST:$APP_PORT/health"
echo
ss -ltnp | grep ":$APP_PORT" || true
tail -n 20 "$APP_LOG" || true
EOF
)

echo "Deploying on server..."
ssh -p "$REMOTE_PORT" -i "$REMOTE_KEY" "$REMOTE_USER@$REMOTE_HOST" "$REMOTE_CMD"
