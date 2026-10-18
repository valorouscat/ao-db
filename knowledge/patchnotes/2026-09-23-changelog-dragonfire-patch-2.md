<!-- gid: 1844751498217965 -->
# Changelog: Dragonfire Patch 2

_date: 2026-09-23 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1844751498217965_

> _This patch brings important adjustments to the Dragon Sanctuary and the Ancient Lands. Loot has also been increased across several Dragonfire features, while Season 33’s winners are celebrated with new statues in Conqueror’s Hall. _

### Loot Adjustments

We have improved the loot for specific Dragonfire features which have been underperforming in terms of loot output:
- Ancient Lands
  - Medium Ancient Lands have had their non-Drake loot from chests increased by roughly 50%
  - Large Ancient Lands have had their base loot from chests increased by roughly 140%

- Dragon Sanctuary
  - The chance of finding a Drake Egg in the final chest has been increased by roughly 400%
  - Base loot from chests has been increased by 100% on average

- Outlands Dragon Attacks
  - Base loot from chests has been approximately doubled
  - Fame is now rewarded as part of the Might payout, instead of non-tradable Tomes of Insight in the chest, to ensure all participants get Fame and not just the player who opens the chest

- New Dragon item drop chances (e.g. Dragon Armor items) have not been changed, so the value of the new items is maintained

### Ancient Lands Changes

- A new feature has been added to orange-zone Ancient Lands: Item Freeze
  - When entering the portal, all items in a player’s inventory are ‘frozen’
  - These items are not dropped on death
  - Any items picked up while inside the Ancient Lands are not frozen, however, and will be dropped on death

- Island chests (excluding the center island) are now unlocked by completing the island quest
  - This is to prevent players, particularly on the Drake Islands, from sniping the main reward and leaving the quest objective to players attempting to summon the Fire Drake

- Reduced Giants’ aggro range:
  - 11m → 8m

- Reduced Spirit Weaver’s Drowsy Essence sleep duration: 4s → 2s
- Added new Bleedout revival animation

### Dragon Sanctuary Changes

Since the Dragonfire launch we’ve been watching and analyzing your Dragon Sanctuary runs, and we love seeing your strategies emerge to beat these bosses!
In general we’re satisfied with the overall difficulty, but the Maeve fight in particular has a pretty high variance in how it unfolds. For this reason we have made some changes to Maeve that do not aim to nerf or buff her, but widen mid-fight recovery windows and change her pacing to increase more gradually.
Besides that, we’ve started to see some more… cheesy strategies emerge, which we’ve tried to discourage with a few fixes and adjustments.
Beyond those changes, there are some other things we may want to look at in future patches – in particular, higher-tier (8.1+) difficulty scaling. This does not necessarily mean that anything will change, but we want to keep an eye on these things. One small change we have made in this patch, though, is to reduce the potency of the Lingering Dragon Spirit.

**Maeve Changes**
- Adjusted fight pacing
  - Storm Spire appearance threshold: 80% Health → 60% Health
  - Rock Spike appearance threshold: 60% Health → 80% Health
  - Double Rock Spike appearance threshold: 40% Health

- Realm Rift
  - Max. stacks: 5 → 15
  - Each stack increases Realm Rift’s damage by an additional 400
  - Debuff duration: 3000s → 100s

- Boulder Stomp
  - Reduced shockwave speed by roughly 10%
  - Reduced initial damage by 20%: 1000 → 800
  - Now applies a debuff on hit, increasing damage taken from subsequent stomps by 5% for 75s, stacking up to 10 times

- Storm Spire
  - Health reduced by roughly 5%

- Primal Dragon Flame
  - True damage: 1250 → 900
  - Normal damage: 750 → 1250

- Rock Spike
  - Reduced area size slightly to make it a little more forgiving to run close to allies: 3m → 2.75m

- Boulder Charge
  - Damage: 1000 → 900

- Other adjustments
  - Reduced Maeve’s pursuit range: 50m → 40m

- Fixes
  - Maeve can no longer be CC’d before the fight starts
  - Adjusted her arena to stop her boulders from getting stuck in terrain
  - Some of her spells are no longer reflectable
  - Fixed a rare issue where Storm Spires could sometimes decide the fight was over and disappear prematurely

**Other Dragon Sanctuary Changes and Fixes**
- Reduced potency of Lingering Dragon Spirit
  - Mob damage and defense increase per stack: 33% → 20%

- Fixed an issue where Azaryon would sometimes stop using abilities
- Azaryon now enrages if players cause him to get stuck or repeat certain actions too often

### Season 33 Winner Statues Unveiled

Statues have been erected in Conqueror’s Hall to mark the winners of Season 33: _Upside_, _Contingent_, and _I The Flying Dutchman I_. Congratulations to the triumphant guilds!

### Other Changes

- Added button to the Loadouts UI to share Loadouts outside of the game client
  - In addition, Loadouts can now be created using the ‘Start from clipboard’ option or by pasting text into an existing Loadout

- Leyfin fish can now be given as Laborer Journal rewards
- Polished appearance and clarity of Armory metrics section
- Polished appearance of Destiny Board specialization nodes
- Dragons in the open world are taking a minimalist approach to design, and periodically destroy any furniture in their vicinity
- Open-world Dragon Attacks now only show x-rays of the player character and party members to improve visibility
- When Tracking, a ping now appears on the minimap when in proximity to the target

### Combat Balance Changes

**Axes**

> _To make Internal Bleeding a more viable option in large-scale PvP, its damage-over-time effect can no longer be reflected.​_

- Internal Bleeding (all Axes)
  - Damage-over-time can no longer be reflected

> _AoE escalation has been added to Tear Apart’s CC resistance debuff to increase its value in group play._

- Tear Apart (Halberd)
  - Added AoE escalation to the crowd-control resistance reduction

**Holy Staffs**

> _Divine Protection now accounts for time spent waiting to cast the second part of the combo, effectively reducing its remaining cooldown.​_

- Divine Protection (Divine Staff)
  - Elapsed time before casting Divinity’s Grace is refunded

> _Holy Flash has been the go-to spell across most content due to its reliability, overall power, and high-healing output. To allow more room for alternatives to compete, its total healing has been reduced._

- Holy Flash (all Holy Staffs)
  - Healing: 117 → 106

**Nature Staffs**

> _Thorns should now feel smoother to use, as casting it no longer delays the next auto-attack._

- Thorn Growth (all Nature Staffs)
  - No longer triggers auto-attack cooldown after casting

**Quarterstaffs**

> _Rising Blow has received an additional CC resistance debuff, giving it a stronger identity as a supportive tank tool for starting or extending crowd-control chains.​_

- Rising Blow (all Quarterstaffs)
  - Now reduces enemies’ crowd-control resistance by 15% for 4s

**Shapeshifter Staffs**

> _A previous Fear duration change has been partially reverted to give the Spirit Bear’s Roar more oomph._

- Wild Onslaught (Primal Staff)
  - Fear duration: 1s → 1.2s

**Spears**

> _Some of Trinity Spear’s power has been moved from the area buff into impact damage, reducing its reliance on stat-checking with auto-attacks and better rewarding players for successfully landing the jump. _

- Spectral Trident (Trinity Spear)
  - Impact damage: 191.65 → 220
  - Attack speed buff: 85% → 75%

**Swords**

> _Limitbreaker now accounts for time spent waiting to cast the second part of the combo, effectively reducing the remaining cooldown.​_

- Limitbreaker (Infinity Blade)
  - Elapsed time before casting Limitbreaker is refunded

> _Spinning Blades’ crowd-control immunity now also protects against Polymorph._

- Spinning Blades (Dual Swords)
  - Now also grants immunity to transformation effects while jumping

**Helmets**

> _Displacement Immunity’s uptime has been increased, giving groups more time to move unimpeded._

- Displacement Immunity (Knight Helmet)
  - Buff duration: 6s → 7s (Uptime: 24% → 28%)

**Armors**

> _Wings of Fire has had a maximum energy cost added, limiting how much energy the ability can consume._

- Wings of Fire (Dragonslayer Jacket)
  - Added max. energy cost: 0% → 10%

### Fixes

**Spell Fixes**
- Reawaken (all Holy Staffs): Fixed issue where the spell could be used on enemy players
- Premonition (Boots of Valor): Fixed issue where the movement speed bonus was not properly removed upon mounting

**UI Fixes**
-  Fixed issue where ‘Close Application’ confirmation popup was missing buttons
-  Fixed issue where it was not possible to select a character’s name in the kill message in chat
-  Fixed issue where damage numbers would not display on some Android devices with resolution set to high

**Other Fixes**
- Fixed issue where several Dragon attacks could be interrupted by spells or delayed by damage
- Fixed issue where player kills in the Ancient Lands are registered as both Kills and Knockdowns in the stats UI
- Fixed issue where Player Navigation would stop working after visiting the Roads of Avalon
- Fixed issue where Ancient Lands portals could not be found in deep Roads of Avalon regions
- Fixed issue where Mammoth Hunters and Spirit Weavers in the Ancient Lands would regenerate health during combat
- Fixed issue where Spirit Weavers’ flame summons could appear in unreachable areas
-  Fixed issue where ‘Quickly Navigate Here’ Player Navigation option was not available
-  Fixed issue where notifications would appear offscreen when Controller UI was open
- Various additional controller, graphical, animation, terrain, audio, UI, and localization fixes
