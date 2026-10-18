<!-- gid: 5963414363386347462 -->
# Changelog: Paths to Glory Patch 1

_date: 2024-08-07 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/5963414363386347462_

### Paths to Glory Patch 1 - Version 26.010.1 - August 7, 2024

> _This is a small patch that primarily addresses issues introduced by the Paths to Glory update that were not critical enough to be included in previous hotfixes._

### Changes

**Albion Journal**

The following mission rewards have been changed:

- ‘Visit all six Royal Cities’
  - Monk's Hood →  Monk's Sandals

- ‘Catch 15 different fish’
  - Blue Bard's Hat → Blue Bard's Shoes

- ‘Finish 40 hunts’
  - 5 Tomes of Learning → 1 Tome of Learning

- ‘Own a million Silver’
  - Innkeeper's Hat → Master's Tome of Insight

- ‘Own a billion Silver’
  - 500 Community Tokens → Expert's Tome of Learning

- ‘Loot 5 different Baby Animals’
  - 5x Elder's Bag of Silver → Elder's Tome of Insight

Additionally, Scrolls of Repair earned as Journal rewards are now non-tradable. Those earned prior to this patch remain tradable.

**Territory Raiding**

The percentage of stored energy that is destroyed when unlocking Raw Energy Cores has been increased from 1% to 5%.

**Other**

Randomized Dungeons shown on the Minimap in the Roads of Avalon now continue to display enchantment VFX after a player has entered.

- This does not apply to randomly spawned dungeons in Hideout regions

### UI Improvements

- Added pop-up notifications for the completion of individual Journal missions
- Entries in the drop-down list in the Island Merchant UI now display visual cues to reflect the player's ownership and Guild permission status

### Combat Balance Changes

**Axes**

- Relentless Assault (Crystal Reaper)
  - Damage: 82.5 → 90

**Bows**

- Deadly Shot (all Bows)
  - Range: 18m → 20m

**Cursed Staffs**

- Enfeeble Blades (Lifecurse Staff)
  - Removed: Damage debuff
  - Damage per tick: 55 → 70

**Daggers**

- Dash (all Daggers)
  - Energy Cost: 5% → 8%

**Fire Staffs**

- Combustion (Infernal Staff)
  - Damage per tick: 13 → 16

- Flame Pillar (Great Fire Staff)
  - Damage: 190 → 200

**Frost Staffs**

- Arctic Volley (Arctic Staff)
  - Range: 18m → 22m

**Nature Staffs**

- Well of Life (Wild Staff)
  - Cast time: 1s → 0.7s
  - Duration: 5s → 4s
  - Total ticks: 5 → 4
  - Healing per tick: 55.2 → 69

**Quarterstaffs**

- Phantom Twin (Phantom Twinblade)
  - Damage per tick: 33 → 36

**Shoes**

- Spectral Run (Specter Shoes)
  - Previously: auto-attacks disabled for 3 seconds after moving more than 15m (after invisibility ends)
  - Now: damage reduced by 50% for 3 seconds after moving more than 15m (after invisibility ends)

### Fixes

> _A number of progression and reward issues in the Albion Journal have been addressed. These changes will take effect with this patch and will not retroactively change existing progression unless otherwise noted._

**Albion Journal fixes:**

- Fixed issue where the ‘Loot Baby Animals’ missions could be completed by looting the item from a player’s corpse
- Fixed issue where the same vanity item reward could be obtained from two missions (see updated mission rewards above)
- Fixed issue where the mission ’Own 3 plots in the same city simultaneously’ rewarded a Snow Leopard Cape item instead of the untradeable Snow Leopard Cape unlock item
  -  Unintended Snow Leopard Cape items that have already been claimed have been converted into the untradeable Snow Leopard Cape unlock item

- Fixed issue where resource mobs in the Mists would not count towards skinning missions
- Fixed issue where hide animals in the Mists and hide treasures were not counted as unique animal types
  - As a result of this fix, the amount of hide mobs required to complete the mission ‘Skin every type of Hide Animal’ has increased significantly. To offset this increase, two additional steps in the mission chain have been added:
    - ‘Skin 52 types of Hide Animal’
    - ‘Skin 65 types of Hide Animal’
    - Unfortunately, these missions have to be started from scratch as, for technical reasons, they are considered new missions

- Fixed issue where the mission 'Use the Journey Back ability in a Black Zone' could be completed by returning from any zone
- Fixed issue where missions to kill a certain number of mobs did not count mobs defeated by a party member
- Fixed issue where ‘Gain Brecilien standing’ missions were not completed if maximum standing was reached prior to the Journal’s release
- Fixed issue where Phalanx Beetle mounts did not count towards the 'Ride a Battle Mount' mission
- Fixed issue where some crafting missions could be completed by other means
- Fixed issue where percentages in category progress bars were rounded up, causing the UI to incorrectly indicate that a threshold had been met
  - Percentages now include one decimal number

- Fixed some inaccurate mission descriptions

**UI fixes:**

- Fixed issue where speech bubbles could obscure important UI elements. The display priority now functions correctly, in this order:
  - Player's own nametag
  - Selected nametags
  - Nametags with an icon
  - Spellcasting bars
  - Speech bubbles
  - Other nametags

- Fixed issue where mount healthbars and spellcasting bars could display incorrectly when other spells were cast nearby
- Fixed issue where the Journey Back ability could not be used after closing the notification pop-up with the ESC key
- Fixed issue where opening the Destiny Board or World Map with the Journal Tracker UI open would cause the tracker to display as empty
-  Fixed issue where mail notifications would appear during the tutorial despite the mail menu being inaccessible

**Other fixes:**

- Fixed various mob spawning issues in Randomized Dungeons:
  - Fixed issue where boss encounters could spawn twice
  - Fixed issue where elite mobs could spawn in solo dungeons
  - Fixed issue where veteran mobs could spawn in groups in solo dungeons
  - Fixed issue where multiple groups of mobs could spawn at once

- Fixed issue where cooldown reduction buffs could sometimes cause longer than intended cooldowns for the Crystal Reaper, Panther Shape, and Imp Shape
- Fixed issue where Territory Activity Chest shield visual states would not change when standing next to them
- Fixed issue where Victory Emotes would activate if a player used the ‘/die’ command when ‘also trigger on knockdown’ was enabled
- Various additional graphical, animation, terrain, audio, UI, and localization fixes
