<!-- gid: 1794014851385334 -->
# Changelog: Rogue Frontier Patch 3

_date: 2025-03-12 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1794014851385334_

> _This patch brings important refinements and bug fixes but primarily focuses on combat balance changes._

### Changes

**Destiny Board Changes**
- The Reaver line bonus has been reworked to prevent unintended interactions with spells and other effects
  - Bonus defense/damage vs mobs should now work as intended for higher-tier enemies
  - Armor and magic resistance reduction effects are now more effective against higher-tier enemies
  - Aside from these interactions, there should be no noticeable difference when fighting mobs

**Corrupted and Solo Randomized Dungeon Changes**

> _With the introduction of the Gold Market Stabilization system, Common Chests that typically dropped a single Bag of Silver could sometimes be empty. To prevent this without altering the stabilization system, we have moved Silver from Common Chests to higher-value chests, and replaced them with Tomes of Insight to ensure a guaranteed reward._

- Common Chests now drop Beginner’s Tomes of Insight instead of Bags of Silver
- Uncommon, Rare, and Legendary Chests now contain more Bags of Silver          

**UI Changes**
- To standardize Cast Time and Cooldown Rate modification values, they now always display a positive value to indicate longer durations and a negative value to indicate reductions
  - The item stat 'Cast Time Reduction' has been renamed to 'Cast Time' to align with this system

- Reduced chat frequency for /HCE, /LFG, /TR, and /REC by increasing message cooldown from 30 seconds to 2 minutes

### Combat Balance Changes

**Arcane Staffs**

> _Evensong has offered powerful offensive utility but is almost always used with plate armor. Its base damage has been increased to help players who want to lean more into being a DPS threat._

- Dark Sphere (Evensong)
  - Damage: 100 → 112

**Axes**

> _Axe players in ZvZs have been overperforming, frequently hitting more than 10 enemies. To address this, the damage and complexity of Raging Blades have been reduced._

- Raging Blades (all Axes)
  - Removed: Targets within 2 meters take no damage
  - Damage per tick: 26 → 22

**Hammers**

> _Giant Steps has been far from its previously overwhelming state. A portion of its slowing aura has been restored to reinforce Forge Hammers as a tanky disruptor._

- Giant Steps (Forge Hammers)
  - Slow: 20% → 35%

**Holy Staffs**

> _Great Holy Staff has been underperforming, so part of its resistance increase has been restored._

- Holy Explosion (Great Holy Staff)
  - Resistance increase: 0.12 → 0.16

> _To give Lifetouch Staff a unique role, Holy Touch’s target is now immune to Crowd Control for the channel's duration (unless self-targeting). In addition, its range has been increased to improve its reliability in modern Albion._

- Holy Touch (Lifetouch Staff)
  - Added: Target is immune to all crowd-control (unless self-targeting)
  - Range: 6m → 9m

**Spears**

> _Fling has struggled to find success. To improve its effectiveness, its stand time and cooldown have been reduced, making it easier to confirm an Impaler hit._

- Fling (Glaive)
  - Standtime: 0.85s → 0.6s
  - Cooldown: 20s → 18s

**Swords**

> _Swords already have strong chase potential due to their passive movement speed bonuses. To balance this, Heroic Strike’s above-average range has been reduced._

- Heroic Strike (all Swords)
  - Range: 4m → 3.5m

**War Gloves**

> _Fleet Footwork has provided War Gloves users with a solid mobility option while also serving as an exceptional DPS tool. Its damage output has been reduced to bring it more in line with alternatives._

- Fleet Footwork (all War Gloves)
  - Auto-attack damage buff: 150% → 125%

**Armors**

> _Ambush has remained a top-tier damage boost while also offering great defensive capabilities. Its maximum damage bonus has been reduced to allow other aggressive chest armors to be more competitive._

- Ambush (Assassin Jacket)
  - Damage buff per stack: 4% → 5%
  - Max buff stacks: 10 → 6 (max damage bonus 40% → 30%)
  - Stack rate: 0.5s → 1s (time to max stacks: unchanged)

**Shoes**

> _A few underused shoe abilities with restrictive conditions and mobility trade-offs have been improved. _

> _Giant’s cooldown and uptime have been adjusted to make Guardian Boots a more available defensive option._

- Giant (Guardian Boots)
  - Cooldown: 60s → 40s
  - Duration: 8s → 6s

> _Mark of Sacrifice, Shield Charge, and Swift Cut have been standardized to a 15m range with below-average cooldowns, as their target requirements have been too limiting._

- Mark of Sacrifice (Hellion Shoes)
  - Range: 12m → 15m

- Shield Charge (Knight Boots)
  - Cooldown: 20s → 18s

- Swift Cut (Assassin Shoes)
  - Range: 11m → 15m

### Fixes

**Spell Fixes**
- Holy Beam (Holy Staffs) no longer adds a spell effect icon to the target’s buff bar
- Hamstring (Swords): Fixed issue where the tooltip displayed an incorrect cooldown
- Ambush (Assassin Jacket): The damage buff can now be purged and no longer persists if the caster does not deal damage within the first 7 seconds

**UI Fixes**
- Fixed issue where icons on the Region Map could duplicate over time
- Fixed issue where some tooltips would remain visible and follow the cursor
- Fixed issue where Medium Treasure Chests were not visible on the map for players in a neighboring region

**Other Fixes**
- Fixed issue where Elite Cursed Harvester did not count towards the Albion Journal mission ‘Defeat any Reaper or Harvester’
- Various additional graphical, animation, terrain, audio, UI, and localization fixes
