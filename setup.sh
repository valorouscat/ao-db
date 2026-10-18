#!/bin/sh
# Fetch (or update) the game data dumps and build the knowledge base.
set -e
cd "$(dirname "$0")"
if [ -d ao-bin-dumps/.git ]; then
  git -C ao-bin-dumps pull --ff-only
else
  git clone --depth 1 https://github.com/ao-data/ao-bin-dumps ao-bin-dumps
fi
python3 build.py --repo ao-bin-dumps
