# Roads of Avalon: which chests are worth opening

_updated: 2026-10-18 · tags: avalon, roads, chests, loot · data: 1a469e5 · patch: Changelog: Dragonfire Patch 3 (2026-10-12)_

Ranking of Roads of Avalon chests (`chesttype=avaroadloot`) by expected loot value at T8, from `chest_value avaroadloot --tier 8 --live`
(europe, Caerleon prices, 2026-10-18). Value index, best = 100:

| chest | index |
|---|---|
| AVALON_MEDIUM_ELITE_BOSS | 100 |
| AVALON_MEDIUM_VETERAN_BOSS | 62 |
| AVALON_MEDIUM_ELITE_CHAMPION | 52 |
| AVALON_SMALL_ELITE_BOSS | 42 |
| AVALON_SMALL_SOLO_BOSS | 27 |
| AVALON_MEDIUM_VETERAN_CHAMPION | 21 |
| AVALON_MEDIUM_ELITE_BASE | 15 |
| AVALON_SMALL_ELITE_CHAMPION | 13 |
| AVALON_SMALL_SOLO_CHAMPION | 8 |
| AVALON_MEDIUM_VETERAN_BASE | 6 |
| AVALON_SMALL_ELITE_BASE | 4 |
| AVALON_SMALL_SOLO_BASE | 2 |

Takeaways:
- `*_BASE` chests are worth 2–15% of a boss chest of the same size: skip them unless they are on your way.
  `*_CHAMPION` chests sit in between; `*_BOSS` chests carry most of the value.
- Rarity matters only for chests that can roll it. Veteran boss: uncommon ≈ 96k → legendary ≈ 204k model value.
  Small chests can't become rare/legendary (patch notes).
- Value comes mostly from rare high-value drops (T8 bags, Avalonian capes, capes), so single chests vary a lot.
- Every chest type has `triggermobspawn=true`: opening it spawns guards, so time and risk scale with chest size.

Assumptions: loot.xml `chance` read as a percentage (999 = guaranteed), so trust the ranking more than the absolute silver.
The name → in-game colour mapping (SOLO = green, VETERAN = blue, ELITE = gold) is inferred, not confirmed by game text.
Fame, clear time and PvP risk are not modelled. Group-size intent per colour comes from older dev notes.


Patch history relevant to Roads chests (from `patchnotes "roads of avalon"`, newest first):
- 2024-07-22 Paths to Glory Update: Roads tier depends on where you enter (T4 from blue/yellow, T6 from red/black,
  T8 only Deep Roads / 20-player portals); Fame cut ~20–25%, Roads made "more attractive for loot".
- 2023-01-09 Beyond the Veil Patch 3: camps rebalanced per group size and marked by a chest icon; guards upgrade
  and respawn together with the chest.
- No Roads-chest changes found in changelogs after 2024-07-22 up to Dragonfire Patch 3 (2026-10-12).
  Avalonian *Dungeon* chests (a different content type) were changed in 2026-01 and 2026-06.

## Sources
- ao-db chest_value avaroadloot --tier 8 --live (lootchests.json + loot.xml, ao-bin-dumps 1a469e5)
- https://massivelyop.com/?p=291840 (Roads of Avalon preview: chest colours by group size)
- https://devtrackers.gg/albion/p/295c50ab-beyond-the-veil-patch-3-dev-update (group chest value increased; small chests cannot become rare/legendary)
- https://lr.us.psf.lt/r/albiononline/comments/1g0i9ny/solo_roads_question (community: gold not soloable, blue slow solo)
- https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5969041959978883917 (Changelog: Paths to Glory Update, 2024-07-22)
