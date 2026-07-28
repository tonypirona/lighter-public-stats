#!/usr/bin/env sh

# Data is loaded from GitHub at runtime, so a stats-only commit needs no deploy.
if ! git rev-parse HEAD^ >/dev/null 2>&1; then
  exit 1
fi

git diff --quiet HEAD^ HEAD -- . ':(exclude)data/stats.json'
