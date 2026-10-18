<!-- gid: 1786409468838205 -->
# Changelog: Horizons Patch 4

_date: 2024-12-18 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1786409468838205_

> _This patch follows up on previous combat balance changes, enhances some less prominent weapons and abilities, and introduces additional changes and fixes._

### Changes

- Dropped banners no longer reduce Fortification protection
-  Stack and Sort buttons have been restored to the main Inventory menu

### Combat Balance Changes

**Bows**

> _Wailing Bow has been underperforming in ZvZs despite being the only ability with custom AoE escalation. We have increased the damage escalation per target hit to bring Wailing Bow back to its glory days._

- Demon Arrow (Wailing Bow)
  - Damage to 1st target: 189 → 189 (unchanged)
  - Damage to 2nd target: 236 → 256
  - Damage to 3rd target: 283 → 323
  - Damage to 4th or more targets: 331 → 391

**Cursed Staffs**

> _While Dark Matter has high damage potential, it has been too easy to counter. We have decreased its cooldown to improve reliability but have also increased the energy cost to keep the ability's spam potential in check._

- Dark Matter (all Cursed Staffs)
  - Cooldown: 20s → 15s
  - Energy cost: 10 → 16

**Holy Staffs**

> _Sanctify’s unique ability to remove hostile ground effects created by enemies has proven less impactful than anticipated. As a result, we have increased its value as a traditional healing weapon._

- Sanctify (Exalted Staff)
  - Healing: 122 → 138
  - Range: 10m → 12m

**Maces**

> _We have given Dreadstorm Monarch’s Eye of the Storm additional damage and resistance reduction to help it command the respect it deserves._

- Eye of the Storm (Dreadstorm Monarch)
  - 1st & 2nd cast damage: 39 → 50
  - Resistance reduction: 0.12 → 0.15

> _Vendetta’s cast time has been significantly reduced to help Camlann players hit their intended targets more accurately without requiring additional setup._

- Vendetta (Camlann Mace)
  - Cast time: 0.7s → 0.25s
  - Stand time: 0.7s → 0.2s

**Nature Staffs**

> _The previous changes to Soul Link have been a step in the right direction, giving Iron Root players a legitimate reason to use the Ally/Enemy effect. However, with the increase in power, the reduction to the Ally/Ally effect was too conservative. The intent is to maintain the Ally/Ally effect as the powerful and consistent option it has always been._

- Soul Link (Ironroot Staff)
  - Ally/Ally healing transfer percentage: 50% → 75%
  - 2nd cast stand time: 1s → 0s

**Quarterstaffs**

> _We have added more value to the 1st and 2nd casts of Phantom Twin to help the Phantom Twinblade perform more effectively as a DPS Quarterstaff._

- Phantom Twin (Phantom Twinblade)
  - Damage per tick: 36 → 41
  - Slow: 10% → 15%
  - Added missing energy costs: 5/5/7

> _Separator is emerging as an effective tool for singling out a target. To help it succeed in that role, we have increased its single-target damage._

- Separator (all Quarterstaffs)
  - Damage to target: 125 → 157

**War Gloves**

> _Ravenstrikes have become a more viable option now that players are no longer at risk of dying without the ability to stop their own damage. Due to this increased consistency, their damage and speed while channeling have been reduced to give enemies more room to react and recover._

- Earth Crusher (Ravenstrike Cestus)
  - Self-slow: 25% → 40%
  - 0 charge damage: 175 → 155
  - 1 charge damage: 185 → 165
  - 2 charge damage: 195 → 175
  - 3 charge damage: 205 →  185

**Armors**

> _Following recent buffs, we are happy with the adoption of Armor of Valor as a powerful defensive option with unique utility. However, tank items should not provide high CC, strong defenses, and significant damage in a single ability. The amount of damage it could return, particularly in 1v1 fights, was too high._

- Requite (Armor of Valor)
  - Damage: 46 → 31

**Shoes**

> _Mage Sandals have fallen out of favor in modern Albion, so we have added a new resistance buff upon landing. Additionally, changes have been made to make it harder for enemies to predict the exact landing location._

- Delayed Teleport (Mage Sandals)
  - Now increases resistances by 0.2 for 2s after landing
  - No longer shows the exact ending position VFX to enemies

**Mounts**

> _Tanks have been using Morgana Ravens as an additional CC option, overwhelming large groups of players by chaining long-duration fears. We have made changes to Raven Scream to address these issues._

- Raven Scream (Morgana Raven)
  - Now gives feared targets immunity to consecutive Raven fears for 15s
  - No longer inherits the rider’s bonus CC duration

> _Reactive Scream has been removed as it had the potential to put the mount's rider into combat uncontrollably, hindering their ability to flee._

- Reactive Scream (Morgana Raven)
  - Removed

**Potions**

> _The recent change to potion swapping has made using Fish Bait inconvenient, so we have changed the way it is consumed._

- Fish Bait (all Tiers)
  - Fish Bait is now consumable from inventory, rather than as a potion
  - If a character had Fish Bait equipped in the potion slot prior to this patch, this will need to be removed before it can be used from the inventory

### Fixes

**Spell Fixes**
- Vengeful Sprint (Demon Boots): Fixed issue where the active charge count VFX did not display correctly
- Hellfire Potion: Fixed issue where it reduced healing cast instead of healing received

**Salvaging Fixes**
- Fixed issue where certain items would have a lower salvage value than intended
- Fixed issue where non-salvageable items would display a salvage value

**Mob Fixes**
- Fixed issue where Keeper Bear and Giant mobs could knock players out of combat range, causing them to reset
- Fixed issue where the Morgana Fang boss would stand still while casting Splitting Claw

**Albion Journal Fixes**
- Restored progress towards the mission ‘Have the offspring of every type of animal’ that was lost with Horizons Patch 2
- Fixed issue where the mission ‘Deliver a Weakened Wisp in Lethal Mists’ could not be completed in Greater Mists
- Fixed issue where the mission ‘Directly sell 9999 preferred luxury goods to Caerleon’ would only count those sold in one of Caerleon’s Marketplaces
- Fixed issue where the mission ‘Raise a Tier 7 Mount’ could be completed by raising a pig
- Fixed issue where the mission ‘Get your very own island’ could be completed by having any type of island in your island list
- Fixed issue where ‘Kill or assist in killing players within one minute’ missions would not count assists
- Fixed issue where the mission ‘Have 2 offspring from a single horse’ could not be completed
- Changed mission ‘Reach Guild Challenge Level 100 with your Guild’ to ‘Reach Guild Challenge Level 99 with your Guild’

**Other Fixes**
- Various additional graphical, animation, terrain, audio, UI, and localization fixes
