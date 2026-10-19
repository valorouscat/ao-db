# What sets chest rarity in the Roads of Avalon and Mists wisp rarity

_updated: 2026-10-19 · tags: avalon, roads, chests, mists, wisps, rarity · data: 1a469e5 · patch: Changelog: Dragonfire Patch 3 (2026-10-12)_

**Roads of Avalon chests** (`lootchests.json`, spawn points `LootChestSpawnpointChestUpgrade` AVALON_*):
- Two independent layers. 1) Stage = which chest a spawn point holds: BASE / CHAMPION / BOSS, weights 6 / 3 / 1
  (`lootchestupgradelevelindex` 4/6/8). The spawn point re-rolls every 450–1350 s (`rerollchance` 0.54), so an unopened chest
  can upgrade; guards in `mobupgraderadius` (60 small, 100 medium) upgrade with it. Respawn 120–240 s after opening (`respawn=OnOpen`).
  `activityquotientactive=true` (offset 600356 s ≈ 7 days): server-side activity scaling, exact formula not in the client data.
- 2) Rarity is rolled per chest from the stage's `RareStates` and hidden until unlock (`hiderarityuntil=OnUnlock`):
  BASE standard 60% / uncommon 40%; CHAMPION standard 50 / uncommon 35 / rare 15%; BOSS uncommon 60 / rare 30 / legendary 10%.
  Same weights for SMALL and MEDIUM, SOLO/VETERAN/ELITE — so small boss chests *can* be legendary in the current data
  (the 2023 dev note saying small chests can't go rare/legendary is outdated).
- Tier of the loot = Roads region tier (T4/T6/T8 by entry zone since Paths to Glory 2024-07-22), not the rarity.

**Mists wisps** (`mists.json` mistsmode difficultylevel 0–4 = Mundane(white) / Standard(green) / Uncommon(blue) / Rare(purple) /
Legendary(gold), each with its own wisp mob `MOB_UNIQUE_MISTS_PORTAL_WISP[_STANDARD|_UNCOMMON|_RARE|_LEGENDARY]`):
- Open-world wisp: `randomdungeons.json` RandomLevelReroll `MISTS_OPEN_WORLD_MODE_*` (same for yellow solo, black solo, black duo):
  95.9 / 1.95 / 1.1 / 0.65 / 0.4 %. Re-rolled every 150–450 s while it sits there; activity quotient (reroll chance 0.1111, offset 597600 s).
  Zone decides the mode (Royal T5 → yellow solo; Outlands / Avalon → black solo or duo), not the rarity.
- Wisp found inside the Mists (single roll, `MISTS_INSTANCE_MODE_*`): yellow solo 91.1/3.7/2.6/1.7/0.9; black solo 89.8/4.3/3.0/2.0/1.0;
  black duo 95.7/1.8/1.3/0.8/0.4; inside Knightfall Abbey better: black solo 85.2/6.2/4.3/2.9/1.4, yellow solo 87.1/5.4/3.75/2.5/1.2,
  black duo 93.7/2.65/1.8/1.2/0.6. Chaining wisps inside the Mists (and from the Abbey) gives better odds than open-world wisps.
- Rarity sets the Mists map pool (common maps `maxdifficulty=2`) and rare-resource distribution `MISTS_E0..E4`.
- Radiant Wilds Patch 3 (2026-06-29) raised Mists chest values and lowered mob stats, but didn't change wisp rarity odds.

## Sources
- ao-bin-dumps lootchests.json AVALON_* LootChest and LootChestSpawnpointChestUpgrade
- ao-bin-dumps mists.json mistsmode MISTS_SOLO_YELLOW / MISTS_SOLO_BLACK, mistsdifficultyleveluimapping
- ao-bin-dumps randomdungeons.json RandomLevelReroll MISTS_OPEN_WORLD_MODE_*, MISTS_INSTANCE_MODE_*; RandomExitDistribution
- https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1836506165559763 (Radiant Wilds Patch 3, 2026-06-29)
- https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5035620387702316054 (Beyond the Veil Patch 3, 2023-01-09: guards upgrade with chests)
