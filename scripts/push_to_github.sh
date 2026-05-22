#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: scripts/push_to_github.sh git@github.com:OWNER/REPO.git"
  echo "   or: scripts/push_to_github.sh https://github.com/OWNER/REPO.git"
  exit 2
fi

remote_url="$1"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git init -b main 2>/dev/null || {
    git init
    git branch -M main
  }
fi

git add .

if git diff --cached --quiet; then
  echo "No staged changes to commit."
else
  git commit -m "Initial Ableton MCP bridge"
fi

if git remote get-url origin >/dev/null 2>&1; then
  git remote set-url origin "$remote_url"
else
  git remote add origin "$remote_url"
fi

git push -u origin main

