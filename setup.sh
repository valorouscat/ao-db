#!/bin/sh
# Fetch (or update) the game data dumps, build the knowledge base and fetch official patch notes.
set -e
cd "$(dirname "$0")"
if [ -d ao-bin-dumps/.git ]; then
  git -C ao-bin-dumps pull --ff-only
else
  git clone --depth 1 https://github.com/ao-data/ao-bin-dumps ao-bin-dumps
fi
python3 -m aodb.build --repo ao-bin-dumps
python3 -m aodb.patchnotes --update || echo "patch notes update failed (offline?); stored notes are still used" >&2
