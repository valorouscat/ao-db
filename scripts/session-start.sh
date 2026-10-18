#!/bin/sh
# SessionStart hook: make sure the knowledge base exists (fresh cloud containers start without ao.db).
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/..}" || exit 0
[ -f ao.db ] && exit 0
echo "ao-db: building Albion knowledge base (first run, ~1-2 min)..." >&2
./setup.sh >&2 || echo "ao-db: setup failed; run ./setup.sh manually" >&2
exit 0
