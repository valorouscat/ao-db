# Roads of Avalon: which chests are worth opening

_updated: 2026-10-18 · tags: avalon, roads, chests, loot · data: 1a469e5_

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

By colour: green = SMALL_SOLO_*; blue = MEDIUM_VETERAN_*; gold = SMALL_ELITE_* and MEDIUM_ELITE_*.

Takeaways:
- Solo (green): only SMALL_SOLO_BOSS (27) is clearly worth stopping for; SMALL_SOLO_BASE (2) and _CHAMPION (8) are pocket change.
- Groups ≤5 (blue): MEDIUM_VETERAN_BOSS (62) is the second-best chest overall; VETERAN_BASE (6) isn't worth a detour.
- 5+ (gold): MEDIUM_ELITE_BOSS (100) is the best chest; ELITE_BASE chests (4–15) give less than a blue boss.
- `*_BASE` chests are worth 2–15% of a boss chest of the same size: skip them unless they are on your way.
  `*_CHAMPION` chests sit in between; `*_BOSS` chests carry most of the value.
- Rarity matters only for chests that can roll it. Veteran boss: uncommon ≈ 96k → legendary ≈ 204k model value.
  Small chests can't become rare/legendary (patch notes).
- Value comes mostly from rare high-value drops (T8 bags, Avalonian capes, capes), so single chests vary a lot.
- Every chest type has `triggermobspawn=true`: opening it spawns guards, so time and risk scale with chest size.

Assumptions: loot.xml `chance` read as a percentage (999 = guaranteed), so trust the ranking more than the absolute silver.
Chest colours: green = solo, blue = groups up to 5, gold = 5+ (confirmed by the project owner, an active player).
In the data they correspond to the group level in the chest name: SOLO = green, VETERAN = blue, ELITE = gold.
The game files don't name the colour; `prefab` LOOTCHEST_REGULAR_01–04 is the rarity look.
Fame, clear time and PvP risk are not modelled. Group-size intent per colour comes from older dev notes.

## Sources
- ao-db chest_value avaroadloot --tier 8 --live (lootchests.json + loot.xml, ao-bin-dumps 1a469e5)
- https://massivelyop.com/?p=291840 (Roads of Avalon preview: chest colours by group size)
- https://devtrackers.gg/albion/p/295c50ab-beyond-the-veil-patch-3-dev-update (group chest value increased; small chests cannot become rare/legendary)
- https://lr.us.psf.lt/r/albiononline/comments/1g0i9ny/solo_roads_question (community: gold not soloable, blue slow solo)
- Project owner (player knowledge): green = solo, blue = groups up to 5, gold = 5+
