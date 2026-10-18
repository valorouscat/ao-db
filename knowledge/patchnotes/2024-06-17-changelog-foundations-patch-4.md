<!-- gid: 6890025005363009691 -->
# Changelog: Foundations Patch #4

_date: 2024-06-17 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/6890025005363009691_

### Foundations Patch 4 - Version 25.040.1 - June 17, 2024

### Changes

- Resilience amount is no longer displayed as a buff on players during combat

### Combat Balance Changes

**Crossbows**
- Divine Engine (Energy Shaper)
  - Channel Time: 4s → 3.3s
  - Number of ticks: 13 → 11
  - Damage per tick vs players: 80 → 96
  - Damage per tick vs mobs: 26 → 57

**Cursed Staffs**
- Dark Matter (all Cursed Staffs)
  - Number of ticks: 10 → 8
  - Damage per tick vs players: 78 → 98
  - Damage per tick vs mobs: 39 → 49

**Daggers**
- Lunging Stabs (Bloodletter)
  - When hitting a player below 40% health, cooldown is now reduced by 50%
  - Cooldown: 30s → 35s

**Fire Staffs**
- Pyroblast (one-handed Fire Staffs)
  - 0s Channel Damage: 200 → 190
  - 0.6s Channel Damage: 280 → 266
  - 1.2s Channel Damage: 360 → 342

**Hammers**
- Grasp of the Undead (Tombhammer)
  - Added Hitpoint Reduction: 10%
  - Hitpoint Reduction Duration: 3s

**Quarterstaffs**
- Stun Run (all Quarterstaffs)
  - Movespeed buff now ends upon auto-attacking

- Rising Blow (all Quarterstaffs)
  - Cooldown reduction per player hit: 12% → 15% (stacks up to 3 times)

- Separator (all Quarterstaffs)
  - Now deals 80 damage to all untargeted enemies hit

- Soaring Swipe (Double Bladed Staff)
  - Cooldown: 20s → 25s
  - Hitting a player now reduces the ability’s cooldown by 20%
  - Area Radius: 6m → 5m

**Shapeshifter Staffs**
- Pulse Shock (all Shapeshifter Staffs)
  - Damage: 124 → 109

- Tectonic Shift (Earthrune Staff)
  - Hitpoint reduction: 15% → 10%

**Spears**
- Harpoon (all Spears)
  - Max range: 18m → 20m
  - Projectile speed: 23.33 m/s → 23.53 m/s

**Swords**
- Fearless Strike (Carving Sword)
  - Damage: 150.10 → 135

- Spinning Blades (Dual Swords)
  - Auto-Attack Damage Increase buff: 100% → 65%
  - Attack Speed buff: 50% → 30%
  - Damage buff duration: 3s → 4s

**Helmets**
- Immortal (Mistwalker Hood)
  - Cooldown: 30s → 25s

**Shoes**
- After Image (Mistwalker Shoes)
  - 1st Cast Cooldown: 15s → 12s

- Royal March (Royal Boots)
  - Movement Speed per Stack: 8% → 9%

### Fixes

- Spell fixes:
  - Fixed issue where Soaring Swipe (Double Bladed Staff) slow effect would also apply to enemies in an area around the intended targets
  - Fixed issue where Tectonic Slam (Earthrune Staffs) did not apply debuff icon to enemies to indicate health reduction
  - Fixed issue where Enfeeble Blades (Lifecurse Staffs) would inflict too much damage and an unintended slow effect

- UI fixes:
  - Fixed issue where “Required for” section was missing from Artifact item details
  - Fixed issue where items in Eralia Wayfarer’s menu would not display correctly by tier after deselecting "Show craftable from inventory only"
  - Fixed issue where the countdown banner was not displayed during a duel

- Fixed issue where guild logos would sometimes not display correctly when entering a crowded region
- Fixed issue where chests in Heretic dungeons could not be opened without first destroying Volatile Barrels
- Fixed issue where the Arena search for a group would reset if a party member accepted a match while gathering, fishing, or opening a Tome
  - Accepting an Arena match is no longer possible while engaged in those actions

-  Fixed issue where faction zerg markers on the minimap would display the wrong color
