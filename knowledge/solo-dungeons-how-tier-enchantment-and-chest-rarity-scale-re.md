# Solo dungeons: how tier, enchantment and chest rarity scale rewards

_updated: 2026-10-18 · tags: solo dungeon, randomized dungeon, loot, enchantment · data: 1a469e5 · patch: Changelog: Dragonfire Patch 3 (2026-10-12)_

How tier, dungeon enchantment and chest rarity scale rewards in **Solo Randomized Dungeons**.

**Dungeon enchantment (.0–.4)** — `randomdungeons.json › DifficultyLevels › default`. Mob buff = `MOB_RANDOM_DUNGEON_BUFF_0N`.

| level | loot & silver ×| fame × | mob HP and damage vs players |
|---|---|---|---|
| .0 | 1.00 | 1.00 | +0% |
| .1 | 1.43 | 1.28 | +16% |
| .2 | 1.88 | 1.66 | +36% |
| .3 | 2.43 | 2.13 | +58% |
| .4 | 3.18 | 2.74 | +84% |

Loot grows faster than mob strength up to .2 (×1.88 loot for +36%); .4 gives ×3.18 for +84%.
The boss room has its own group `bossroom_solo`: loot ×3, mob fame ×2.64.

**Chest rarity** (KEEPER faction; other factions are similar). Values are the game's item value (offline proxy, not market price), from `chest_value KEEPER_SOLO_CHEST --tier N`:

| tier | standard | uncommon | rare | legendary |
|---|---|---|---|---|
| T4 | 37 | 48 | 78 | 152 |
| T6 | 41 | 64 | 126 | 279 |
| T8 | 48 | 92 | 208 | 499 |

- Legendary ≈ 4× standard at T4, ≈ 7× at T6, ≈ 10× at T8. Rarity matters more the higher the tier.
- Standard chests barely grow with tier: since Rogue Frontier Patch 3 (2025-03-12) they give Beginner's Tomes instead of silver.
  Uncommon/rare/legendary got more silver bags, which this proxy doesn't value (silver is scaled by the Gold Market Stabilization system).
- Boss chests (`*_BOSS_*`) come only as uncommon+ and have about 75% of the value of a regular chest of the same rarity.

**Tier** (`mobs` table, regular `T*_MOB_RD_*` mobs; bosses in brackets): average fame T4 103 (701) → T6 203 (1,415) → T8 374 (2,612);
HP T4 684 → T8 1,247. Fame ≈ ×3.6 from T4 to T8, while mob HP is only ×1.8.
Horizons Update (2024-10-28) raised mob power from T5 (+9%) to T8 (+42%) with proportional rewards (Elite enemies excluded).

Model caveat: loot.xml `chance` is read as a percentage, so absolute values aren't calibrated; ratios between tiers, rarities and
enchant levels are reliable. Live market valuation was blocked by the price API rate limit at the time of writing.

## Sources
- ao-bin-dumps randomdungeons.json DifficultyLevels (default, bossroom_solo); spells MOB_RANDOM_DUNGEON_BUFF_01..04
- ao-db chest_value KEEPER_SOLO_CHEST / HERETIC / UNDEAD / MORGANA --tier 4..8 (lootchests.json + loot.xml)
- ao-db sql over mobs T*_MOB_RD_* (fame/HP by tier)
- https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1794014851385334 (Rogue Frontier Patch 3, 2025-03-12: common chests → tomes, more silver in higher rarities)
- https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6212245217911946792 (Horizons Update, 2024-10-28: mob power T5 +9% … T8 +42%, rewards scaled)
