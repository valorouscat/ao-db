#!/bin/sh
# SessionStart hook: keep the knowledge base current.
#  - no ao.db           -> full setup (clone dumps, build, fetch patch notes)
#  - dumps changed      -> pull + rebuild
#  - always             -> fetch new official patch notes (incremental, a few seconds)
cd "${CLAUDE_PROJECT_DIR:-$(dirname "$0")/..}" || exit 0
if [ ! -f ao.db ]; then
  echo "ao-db: building Albion knowledge base (first run, ~1-2 min)..." >&2
  ./setup.sh >&2 || echo "ao-db: setup failed; run ./setup.sh manually" >&2
  exit 0
fi
if [ -d ao-bin-dumps/.git ]; then
  local_rev=$(git -C ao-bin-dumps rev-parse HEAD 2>/dev/null)
  remote_rev=$(timeout 20 git -C ao-bin-dumps ls-remote origin HEAD 2>/dev/null | cut -f1)
  if [ -n "$remote_rev" ] && [ "$local_rev" != "$remote_rev" ]; then
    echo "ao-db: new game data dump upstream, updating..." >&2
    ./setup.sh >&2 || echo "ao-db: update failed" >&2
    exit 0
  fi
fi
timeout 60 python3 -m aodb.patchnotes --update >&2 || echo "ao-db: patch notes update skipped" >&2
exit 0
