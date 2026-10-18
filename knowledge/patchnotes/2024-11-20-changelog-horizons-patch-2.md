<!-- gid: 1783872411943167 -->
# Changelog: Horizons Patch 2

_date: 2024-11-20 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1783872411943167_

> _This patch makes some adjustments to features introduced with the Horizons update, along with combat balancing and some other important changes and fixes._

### Season 24 Winner Statues Unveiled

The statues to honor the winners of Season 24 are now viewable in each server’s Conqueror’s Hall. Congratulations to the triumphant guilds!

### New Boss Lairs

The Boss Lairs introduced with the Horizons update have been revamped, with new layouts and visuals that better communicate their status as a faction boss hideout.
- There is now a new Boss Lair for each faction (Undead, Heretic, Morgana)
- The +200% loot bonus for Boss Lairs has been removed, but now there are 3 chests instead of 1
- Each Boss Lair now contains only the boss, and no other mobs
- Their entrances in the open world have been modified slightly

### Territory Raiding Changes

- Once a banner has been dropped and channeled, the time until it is destroyed has been reduced from 5 minutes to 3 minutes
- Raid Banners can no longer be used to raid a territory if an older Raid Banner is already active there, or if two banners are spawned simultaneously
  - In order to raid a territory with your own banner, older Raid Banners must first be destroyed
  - Raid Banners that need to be destroyed first are visually distinguished on the minimap
  - If two Raid Banners are raised within 30 seconds of each other, one must be destroyed before the other can be used to raid
  - Raid Banners that are raised later on in the battle cannot be used to prevent raiding

### Mob Combat Changes

- Spells and combat behavior have been updated for a number of mobs
- Out-of-combat status in PvE now begins when the mob is killed, rather than when its corpse disappears

### Other Changes

- As a followup to our Solo Dynamic Encampment loot increases in Patch 1, Group Dynamic Encampments now award less Fame and Objective progress to players if they are solo or in very small groups
  - Our intent with this, along with the changes in Patch 1, is to create rewarding gameplay loops both for solo players in Solo Encampments, and for group players in Group Encampments

- Mini roaming mob camps in the open world no longer spawn around World Bosses
- Equipping food or potions now puts all spells on a 10 second cooldown
- Enchantment Level 4 Treasure Resources are now more likely to unlock at Prime Time, rather than spawning at Prime Time and unlocking later
- Certain items are now less expensive to Journey Back or use a S.A.F.E. Portal with
  - This mostly affects Randomized Dungeon Maps and Player Island furniture

- The radius of the Crystal Beetle’s ‘Magical Discharge’ spell has been significantly increased
- Hostile player count in safe regions now only counts players explicitly flagged as hostile, not unflagged players in open PvP areas
- Guild Codexes (guilds’ internal descriptions) can now be edited by any member with the ‘Change Guild Logo’ permission

### Combat Balance Changes

**Axes**
- Relentless Assault (Crystal Reaper)
  - Leaving the area does not end the spell
  - Hitting enemies while outside of the area does not reduce weapon ability cooldowns

**Holy Staffs**
- Sanctify (Exalted Staff)
  - Cast Range: 8m → 10m

**Nature Staffs**
- Soul Link (Ironroot Staff)
  - Cooldown: 20s → 12s
  - Energy cost: 18% → 11%
  - Duration: 7s → 5s
  - Ally/ally effect:
    - Healing shared: 100% → 50%

  - Ally/enemy effect:
    - Enemy healing redirected to ally: 30% → 50%

  - Casting both parts on the same target now resets its cooldown

- Circle of Life (Nature Staff)
  - Max targets: 5 → 10

**Quarterstaffs**
- Soul Shaker (Grailseeker)
  - Area duration: 3.5s → 4s
  - Multicast time window: 3s → 5s

**Shapeshifter Staffs**
- Werewolf Transformation (Bloodmoon Staff)
  - Bloody Roar lifesteal: 6% -] 8% (while below 40% health)
    - Lifesteal is now only triggered by Werewolf form abilities

- Distortion (all Shapeshifter Staffs)
  - Damage per tick: 54 → 48
  - No longer reflectable

- Sinister Swipes (Prowling Staff)
  - Range: 4m → 5m

- Spirit Bear Transformation (Primal Staff)
  - Cooldown: 5s → 10s

- Tether Shift (all Shapeshifter Staffs)
  - Dash now applies a shield to yourself which absorbs 200 damage for 1.5s

**Helmets**
- Ice Block (Cleric Cowl)
  - Cooldown: 60s → 90s
  - Removed 50% healing debuff while frozen

**Shoes**
- Dodge (all Shoes)
  - Added immunity to transformation

**Capes**
- Devious Trap (Heretic Cape)
  - Trap hit delay: 0.8s → 0.4s

- Energy Reserve (Lymhurst Cape)
  - Energy restoration: 80% → 70%

**Battle Mounts**
- Healing Sapling (Ancient Ent)
  - Cooldown: 4s → 3s
  - Radius: 2.5m → 4m

- Ent's Blessing (Ancient Ent)
  - Can no longer be interrupted

### Fixes

**Albion Journal fixes**
- Fixed issue where the mission ‘Raise all different types of animals’ could not be completed because it required an obsolete animal
- Fixed issue where the mission ‘Knock down another player in a Yellow Zone’ could be completed by knocking down oneself with self-damaging spells

**Spell fixes**
- Fixed issue where Avalanche (Hoarfrost Staff) could knock-up targets with forced movement immunity

**Mount fixes**
- Fixed issue where Phalanx Beetle and Roving Bastion dismount cooldowns were higher than intended
  - Cooldowns are now 30 seconds

- Morgana Raven: Fixed issue where Reactive Scream’s fear would ignore forced movement immunity

**UI fixes**
- Fixed issue where player count display would sometimes fail to update immediately after changing regions
- Fixed issue where player nametags would sometimes fail to display in safe regions
- Fixed issue where gathering tooltips would not scale correctly with window size
- Fixed issue where chat window size would reset after saving HUD changes
- Fixed issue where the Bandit Assault countdown would remain on the World Map after changing servers
- Fixed issue where, after an Arena battle, the Player Stats UI would open under the Arena Stats UI when clicking a player’s avatar
- Fixed issue where some UI elements would not function correctly after entering a Randomized Dungeon
- Various fixes and improvements made to the Travel Planner UI

**Other fixes**
- Fixed issue where some mobs in the Hardcore Expedition ‘Fistful of Silver’ had higher resistances than intended
- Fixed issue where Mists Encampments could sometimes contain mobs that did not count towards completing the quest
- Fixed issue where some Resource Guardians would grant too little Fame
- Fixed issue where rerolling an item’s quality would sometimes incorrectly state that the player’s inventory is full
- Fixed issue where saved frame rate settings would not be applied immediately after starting the game
- Fixed issue where the Forgotten General mob would perform a slide after its auto-attacks
- Fixed issue where guild logos on the ground of Guild Islands would appear mirrored
-  Fixed issue where emotes could not be used with custom hotkeys
