# Open-world Dragon Attacks: how rewards are calculated

_updated: 2026-10-18 · tags: dragon, dragon attack, might, fame, outlands · data: 1a469e5 · patch: Changelog: Dragonfire Patch 3 (2026-10-12)_

Config: `treasuredistribution.json` › TreasureDragons (one entry per zone/tier), Might/Fame: `pvpchallenge.json`
objectives `PVPCHALLENGE_OPENWORLD_DRAGONATTACK_*`, chests: `lootchests.json` `TREASURE_DRAGON_OPEN_WORLD_*`.

| | Royal Continent (yellow/red) | Outlands (black) |
|---|---|---|
| tiers | T6 (yellow, red), T7 (red) | T6, T7, T8 |
| dragon HP | T6 312,707 · T7 365,985 · T8 438,441 (Fire Dragon / Greater / Elder) | same mobs |
| chest | `@personal=true`: one per eligible player | `@personal=false`: one shared chest |
| Might / Fame | none (objective has might 0) | T6 103,367 · T7 137,465 · T8 182,830 Might; Fame 3,931,200 / 5,522,400 / 7,675,200 |
| warning before spawn (`spawndelay`) | 5 min (red T7 20 min) | T6 30 min · T7 90 min · T8 4 h; RAID variants 5 min |

Rules from the data:
- The dragon flees at 20% HP (`escapeathealthpercentage=0.2`): you deal 80% of its HP. Since Dragonfire Patch 3 a reset
  dragon heals only to the last 20% threshold.
- Eligibility: `rewardminaggro=100` — a player needs at least 100 threat on the dragon to count (name-based reading).
- Might and Fame are pools divided by max(participants, `mindivisor`). Evidence: Patch 3 announced "+150% Might";
  the dump shows the pools unchanged (103,359 → 103,367) but `mindivisor` 100 → 40, i.e. ×2.5 per player; Fame pool was
  cut 9,828,000 → 3,931,200 with the same divisor change, keeping 98,280 Fame per player (T6) for groups up to 40.
  Per player with ≤40 participants: T6 2,584 Might + 98,280 Fame; T7 3,437 + 138,060; T8 4,571 + 191,880. Above 40 the
  pool is split N ways.
- Chests are always the 'rare' state (other states weight 0). Black chest rolls `LOOT_OW_DRAGON_ATTACK_SHARED` with
  chance 3.9 (T8 7.8), personal chest `LOOT_OW_DRAGON_ATTACK_PERSONAL` 1.4, plus Dragon artefacts/fragments/blood lists
  (1, T8 1.85). Patch 2's "base loot doubled" for Outlands is not visible in the client data: it only added
  `@listtype=OW_DRAGON_BASELOOT_*` (multiplier is server-side).

Unverified: exact meaning of `chance` > 1 on chest list references (read as roll multiplier), and of `rewardminaggro`.
`chest_value` mis-models these chests (treats lists as alternatives, ignores RareState weight 0).

## Sources
- ao-bin-dumps 7997c75 (2026-10-12) treasuredistribution.json TreasureDragons; pvpchallenge.json PVPCHALLENGE_OPENWORLD_DRAGONATTACK_*
- ao-bin-dumps history 585e848 (2026-08-31), 90b141e (2026-09-23), 7997c75 (2026-10-12): pvpchallenge.json mindivisor/pvekillfame, loot.json listtype
- https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1846018067940491 (Changelog: Dragonfire Patch 3, 2026-10-12)
- https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1844751498217965 (Changelog: Dragonfire Patch 2, 2026-09-23)
- https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1842212951309746 (Changelog: Dragonfire Update, 2026-08-31)
