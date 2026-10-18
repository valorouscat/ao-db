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
# code expects a newer ao.db layout (new tables / indexes) -> rebuild from the local dumps
if [ -d ao-bin-dumps ] && ! python3 -c "import sqlite3,sys; from aodb.build import SCHEMA_VERSION as v; r=sqlite3.connect('ao.db').execute(\"SELECT v FROM meta WHERE k='schema'\").fetchone(); sys.exit(0 if r and r[0]==v else 1)" 2>/dev/null; then
  echo "ao-db: index layout changed, rebuilding ao.db (~20 s)..." >&2
  python3 -m aodb.build >&2 || echo "ao-db: rebuild failed; run python3 -m aodb.build" >&2
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
