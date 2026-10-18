<!-- gid: 5875595438684143497 -->
# Changelog: Paths to Glory Patch 2

_date: 2024-08-21 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5875595438684143497_

### Paths to Glory Patch 2 - Version 26.020.1 - August 21, 2024

> _This patch is intended to fine-tune some of the changes introduced in the Paths to Glory update, refining the overall game dynamics and addressing community feedback._

### Mob Changes

**Health Regeneration Adjustments:**
- Avalonian Crystal Basilisk no longer regenerates health after the second phase has been triggered
- Reduced health regeneration amounts for all elite and high-tier veteran mobs:
  - Tier 7 Veteran: 72 → 61
  - Tier 8 Veteran: 109 → 76
  - Tier 4 Elite: 111 → 83
  - Tier 5 Elite: 137 → 103
  - Tier 6 Elite: 167 → 125
  - Tier 7 Elite: 241 → 154
  - Tier 8 Elite: 363 → 190

- Mobs no longer regenerate health while invincible

**Other Adjustments:**
- Demonic Harbinger:
  - Forceful Swing damage per tick: 350 → 250
  - Reckless Swing damage per tick: 400 → 300
  - Raging Onslaught cast time: 1.35s → 1.5s
  - Unrelenting Slaughter cast time: 0.65s → 0.75s

- Elite Earthkeeper Axe-Thrower:
  - Stun duration no longers scales with mob’s ability power or player’s crowd control resistance

- Respawn chances for T6+ resources and resource mobs affected by Dynamic Spawn Rates have been increased by up to 10%

### Other Changes and Improvements

**Armor Abilities:**

Armor items now have all their abilities unlocked from Tier 4 upwards, as has been the case with weapons since the Paths to Glory update.

**Albion Journal:**

The following Journal missions have had their rewards updated:
- Defeat 30 Roaming Mob Mini Bosses
  - Elder's Bag of Silver → Master's Tome of Insight

- Gain 3 million Fame from Roaming Mobs
  - Elder's Bag of Silver → Grandmaster's Tome of Insight

- Gain 10 million Fame from Roaming Mobs
  - 5 Elder's Bags of Silver → Elder's Tome of Insight

- Gain 30 million Fame from Roaming Mobs
  - 10 Elder's Bags of Silver → 50 Community Tokens

- Gain 100 million Fame from Roaming Mobs
  - 25 Elder's Bags of Silver → 15 Elder's Bags of Silver

- Kill 1000 Champions in Static Dungeons
  - 5 Elder's Bags of Silver → Elder's Tome of Insight

- Gain 3,000,000 fame in the Roads
  - Elder's Bag of Silver → Grandmaster's Tome of Insight

- Gain 10,000,000 fame in the Roads
  - 5 Elder's Bags of Silver → Elder's Tome of Insight

- Gain 30,000,000 fame in the Roads
  - 10 Elder's Bags of Silver → 50 Community Tokens

- Gain 100,000,000 fame in the Roads
  - 25 Elder's Bags of Silver → 15 Elder's Bags of Silver

- Kill 1000 Champions in Static Dungeons
  - 5 Elder's Tomes of Insight → 1 Elder's Tome of Insight

The following Journal mission has had its objective changed:
- 'Defeat 25 T3 Roaming Mobs' → 'Defeat 12 T3 Roaming Mobs'

**UI Changes:**
- Travel Planner and Island Merchant UIs:
  - Now grouped in a two-level dropdown menu for easier navigation of multiple personal and guild islands
  - Icons now indicate the destination’s biome/attached city and type (city, portal, personal/guild island)
  - Clearly distinguishes between Own Islands, Favorites, and Other Islands for quicker access

- Guild UI:
  - Added functionality to copy guild member list as TSV

- Claiming a reward from the Albion Journal now automatically opens the Inventory
- Dropdowns with submenus now have arrow symbols

**Other:**
- System-generated soup, salad, and mules have been removed from Marketplaces on Albion Europe
- Added Guild Logos for Albion Europe Beta Season winners

### Combat Balance Changes

**Arcane Staffs**
- Enigma Blade (all Arcane Staffs)
  - Damage: 180 → 190:

- Frazzle (all Arcane Staffs)
  - Cast Time: 0.6s → 0.5s
  - Range: 13m → 15m

**Daggers**
- Merciless Finish (Bridled Fury)
  - 0 Stack Damage: 68.3 → 75
  - 1 Stack Damage: 108.8 → 120
  - 2 Stack Damage: 163.3 → 180
  - 3 Stack Damage: 216.6 → 238

**Frost Staffs**
- Frost Bomb (all Frost Staffs)
  - Initial Area Slow: 20% → 30%

**Hammers**
- Powerful Swing (all Hammers)
  - Damage: 94 → 113
  - Bonus damage to crowd-controlled enemies: 48 → 56

- Seismic Tremor (all Hammers):
  - 1st and 2nd Hit Damage: 70 → 80
  - 3rd Hit Damage: 140 → 160

**Holy Staffs**
- Generous Heal (all Holy Staffs)
  - Cast Time: 0.6s → 0.5s
  - Range: 14m → 15m

**Shapeshifter Staffs**
- Fireflash Orb (Hellspawn Staff)
  - Initial Damage: 150 → 120
    - Every 0.6s the projectile travels, damage increases by 30, up to a maximum of 240

  - Recast Damage: 220 → 150

- Seedling's Bloom (Rootbound Staff)
  - Empowered Bloom Healing Received: 20% → 10%

- Barbed Roots (Rootbound Staff)
  - Shield: 150 → 175

**Shoes**
- Blind Spot (Shoes of Tenacity)
  - Caster is no longer invisible to mobs, but only to other players
  - Buff duration: 1s → 1.5s
  - Movespeed: 20% → 60%

### Fixes

**Albion Journal fixes:**
- Fixed issue where ‘Defeat Roaming Mobs’ missions would incorrectly count certain other mobs
- Fixed issue where ‘Find Hidden Treasures’ missions would not count those found by party members
- Fixed issue where the ‘Rescue 50 Wisps in Greater Mists’ mission would not count those rescued by party members
- Fixed issue where the mission ‘Defeat another player after invading their Corrupted Dungeon’ could not be completed in Hunter difficulty
- Fixed issue where the mission ‘Win a 5v5 Crystal League Match’ could be completed by winning a 20v20 Crystal League Match
- Fixed issue where the mission ‘Win a 20v20 Crystal League Match’ required a Level 1 match, rather than any level
- Fixed issue where the mission 'Use a crafting bonus in a Hideout' could be completed by acquiring items from the Energy Manipulator in a Hideout
- Fixed issue where untracking a mission in the summary would cause the UI to scroll to the top

**UI fixes:**
- Fixed issue where using Community Tokens to craft an item at the Vanity Merchant would default to the maximum number of items
- Fixed issue where Territory Control Cost tooltip on region map would incorrectly display zero
- Fixed issue where Albion Journal achievement popups could be hidden by other UI elements
- Fixed issue where a two-handed Vanity Item could not be equipped if the off-hand slot was already occupied
-  Fixed issue where region map would sometimes appear pink

**Other fixes:**
- Fixed issue where a stray Blue Zone Randomized Dungeon would appear in the Roads of Avalon
- Fixed issue where Siege Banners could not be raised against a territory that had already been raided
- Various additional graphical, animation, terrain, audio, UI, and localization fixes
