<!-- gid: 1819386365086089 -->
# Changelog: Realm Divided Patch 2

_date: 2025-12-17 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1819386365086089_

> _This patch brings further adjustments and polish to Faction Warfare features, along with some important bugfixes._

### Faction Warfare Changes

**Caerleon Attack Changes**

When any Faction declares an attack on a lethal Province, Caerleon now also declares an attack on that Province.
- Caerleon no longer has a limit on its number of lethal Province attacks
- Caerleon no longer declares a new attack after winning a Fortress Siege, or after winning a Supply contest as a defender
- If Caerleon does not have at least two active conflicts at any one time, they will declare up to two new attacks to reach this minimum

**Rallying Cry Buff**

When a Faction owns fewer Provinces than the other Factions contesting a Province, its players can now receive an increase to the damage they deal against other Faction players, and a reduction to the damage they receive from them. The size of this buff is determined by the difference between the number Provinces owned by their Faction and the number owned by the largest Faction in that conflict:
- Difference of 1: No buff
- Difference of 2: +5% damage and defense vs. Faction players
- Difference of 3: +10% damage and defense vs. Faction players
- Difference of 4: +15% damage and defense vs. Faction players
- Difference of 5: +20% damage and defense vs. Faction players

**Note:** This buff applies only in non-lethal Provinces.

**Other Changes**
- After changing Factions, a 24-hour cooldown now applies before a player can change Factions again
  - This cooldown does not apply after enlisting with a Faction for the first time

- Faction Warfare Item Power requirements now consider only Base Item Power, without bonuses
  - Players must have a Base Item Power of 700 or above to use Faction Transports and participate in Faction Warfare activities, regardless of their Average Item Power

- Adjustments and polish to several UI elements
  - Added a notification when a Province becomes cut off
  - Added a notification when a Fortress Siege enters the Last Stand stage
  - Fortress Siege and Pre-Siege states are now prioritized on the World Map over the Bandit Assault icon when both are present
  - Added a pulsating highlight on the World Map Province View to indicate zones with active relevant conflicts

### Other Changes

- The Trophy Shark furniture item can no longer be placed outdoors

### Combat Balance Changes

**Axes**

> _Internal Bleeding has received a significant damage increase, making enemies think twice before running away._

- Internal Bleeding (all Axes)
  - Damage dealt to moving targets (per tick): 11→ 20

**Bows**

> _Bows have been out-muscling opponents across all content after the recent Multishot changes, so their PvE and PvP damage has been split to give other weapons a fighting chance in PvP if they get close enough._

- Multishot (all Bows)
  - Damage to players: 116 → 100 (damage to mobs unchanged)

> _Slow Poison has been adjusted to no longer apply diminishing returns (DR) to its own subsequent slow effects, though it remains affected by any existing slow DR._

- Slow Poison (all Bows)
  - No longer applies slow diminishing returns (still affected by existing slow diminishing returns)

> _Undead Arrows has received an increased attack speed bonus to make it a more appealing option outside of ganking._

- Undead Arrows (Whispering Bow)
  - Attack speed buff: 20% → 30%

> _Bow of Badon has been too deadly as a solo clapper, so its explosive bolt interaction has been removed._

- Raging Storm (Bow of Badon)
  - No longer applies explosive arrows on hit

**Cursed Staffs**

> _Cursed Sickle has had its stand time reduced to help it compete more effectively with Cursed Tar._

- Cursed Sickle (all Cursed Staffs)
  - Stand time: 0.4s → 0.3s

**Daggers**

> _Twin Slayers have received a movement speed boost on cast, to not only feel more impactful, but also to more reliably reach good positions to recall their daggers._

- Ring of Death (Twin Slayers)
  - Added: Initial cast now grants 40% movement speed for 2s (removed on recast)

**Fire Staffs**

> _Fire Wave has had some of its knockback distance restored, helping it reclaim its role as a quick self-peel tool._

- Fire Wave (all Fire Staffs)
  - Knockback distance: 2.05m → 4m

**Maces**

> _The time window to cast Gravitas after using Close In has been increased, giving players more time to land the fight-winning root._

- Gravitas (Morning Star)
  - Multispell time window: 3s → 5s

> _Both the hit delay and stand times on Threatening Smash have been reduced to make the bruiser mace style smoother to play._

- Threatening Smash (all Maces)
  - Hit delay: 0.4s → 0.2s
  - Stand time: 0.5s → 0.3s

**Nature Staffs**

> _A new mechanic has been added to Nature HoTs that won’t immediately close the gap for group PvE healing, but should incentivize bringing at least one Nature Staff along on group adventures. This buff does not apply to the caster._

- Rejuvenation Charge (all Nature Staffs)
  - Added: 5% defense vs mobs (per stack, others only)

**Quarterstaffs**

> _Because mounted players can’t interact with a root area by dashing or cleansing, Soul Shaker has been updated to affect mounts separately, with a shorter duration that respects both diminishing returns and crowd control resistance._

- Soul Shaker (Grailseeker)
  - Root vs mounted players now has a base duration of 2s (and are affected by diminishing returns and crowd-control resistance)

> _Quarterstaff has leapt to the top of the Corrupted Dungeon meta, so Vault Leap’s damage has been reduced to keep it in line with alternatives._

- Vault Leap (Quarterstaff)
  - Damage: 190 → 180

**Spears**

> _As with Bows, Slow Poison has been adjusted so it no longer applies diminishing returns (DR) to its own subsequent slow effects, though it remains affected by any existing slow DR._

- Slow Poison (all Spears)
  - No longer applies slow diminishing returns (still affected by existing slow diminishing returns)

**Armors**

> _Soldier Armor has received a mini-rework to function better in solo PvE and offer more interesting options in PvP. It has been turned into a toggle spell with an up-front heal and a persistent downside of increased damage taken. Transformations now remove the effect, while purges remove all Fury damage and CC strength stacks. Stacks can be rebuilt afterward, as long as players are willing to accept the risk of increased damage taken. Its cooldown is effectively longer, as active toggles prevent spells from cooling down._

- Fury (Soldier Armor)
  - Now a toggle spell (taking damage while active still adds bonus damage and crowd-control strength stacks)
  - Activation restores 30% of missing health
  - While active, defenses are decreased by 10%

**Potions**

> _Acid Potion has had its cooldown increased to preserve its power while limiting the frequency of solo one-shot bombing._

- Acid Potion
  - Cooldown: 60s → 100s

> _Calming Potion has been updated so it no longer affects guard-type mobs, ensuring Territory guards won’t ignore their guild members when they are getting ganked nearby._

- Calming Potion
  - No longer affects mobs that guard players (Faction Warfare Outpost mobs, Fortress and Territory mobs, Castle Guard mobs, City Guards)

> _Sticky Potion has received a small duration increase to better control choke points and other key battlefield locations._

- Sticky Potion
  - Duration: 6s → 7s

### Fixes

**Spell Fixes**
- Eye of the Storm (Dreadstorm Monarch): Fixed issue where incorrect VFX sizes were used for each stage

**Faction Warfare Fixes**
- Fixed issue where World Map Outpost information windows would indicate that an Outpost could be captured in inactive conflict zones
  - The specific reasons why an Outpost can or cannot be captured are now displayed

- Fixed issue where players could respawn in an Outpost shortly after it was captured by a rival Faction
- Fixed issue where Faction Transport icons would not change colors when Province control switched to another Faction
- Fixed issue where the Fortress UI would display incorrect status information during Bandit Assault
- Fixed issue where hints would stay open after closing the Faction Transport UI
- Fixed issue where Faction Standing payouts from Weekly Reports could be applied to a Faction the player had already left

**UI Fixes**
- Fixed issue where the Alliance UI appeared behind the Guild UI when opened by clicking the Alliance crest
- Fixed issue where Item Details UI would appear behind and overlap with the Kill Details UI
- Fixed issue where Alliance invitation mails would not display the Alliance name
- Fixed issue where ‘Move All’ would not work between Bank tabs
- Fixed issue where Smuggler Crate icons displayed as Faction Chests on the minimap
- Fixed issue where exit icons on Brecilien, Static Dungeons, and The Underway region maps could not be clicked for navigation
- Fixed issue where the crafting progress bar would be obstructed by opened UIs
- Fixed issue where the Party Finder UI could get stuck open until client restart

**Other Fixes**
- Fixed issue where two Regions were mistakenly renamed
  - These have been reverted to their correct names:
    - Ben Haldon → Haldon Tor
    - Frostfall Floes → Pen Uchaf

- Fixed issue where Morgana Infestor’s Demonic Blades aura could deal too much damage to unmounted players
- Fixed issue where activating Overcharge while casting could cause animation and visual glitches
  - It is no longer possible to activate Overcharge while casting

- Fixed issue where chests would not respawn in Tier 3 Static Dungeons
- Fixed issue where mobs with regeneration abilities could sometimes refuse to die
- Various additional graphical, animation, terrain, audio, UI, and localization fixes
