<!-- gid: 1800357164531726 -->
# Changelog: Rogue Frontier Patch 8

_date: 2025-05-26 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1800357164531726_

> _This small patch addresses some combat balance issues and improves underused spells, alongside some minor bug fixes._

### Combat Balance Changes

**Arcane Staffs**

> _To make Magic Shock a more reliable tool for dealing damage and interrupting enemy casts, its cast time has been significantly reduced._

- Magic Shock (all Arcane Staffs)
  - Cast time: 0.5s → 0.35s

**Crossbows**

> _Divine Engine was dealing too much damage too quickly following its recent buffs. Its damage per tick has therefore been reduced somewhat, while remaining higher than before its recent buffs._

- Divine Engine (Energy Shaper)
  - Damage per tick: 117 → 106

> _Flickershots’ dash range and speed have been increased so that its dashes are no longer slower than most sprint speeds._

- Flickershots (Arclight Blasters)
  - Dash range: 7m → 8m
  - Dash speed: 9.33m/s → 10.66m/s (duration unchanged)

**Fire Staffs**

> _Searing Flame has high damage potential with very long range. To help other ranged weapons fight back, its range has been reduced somewhat._

- Searing Flame (all Fire Staffs)
  - Range: 19.5m → 18m

**Nature Staffs**

> _Living Armor now has an instant guaranteed heal to improve its baseline value, even in suboptimal conditions._

- Living Armor (Great Nature Staff)
  - Added instant heal for 66

**Quarterstaffs**

> _Cartwheel’s cooldown has been reduced to help Quarterstaff tanks find more success, but to maintain a consistent total mobility, the movement speed buff on hit has been removed._

- Cartwheel (all Quarterstaffs)
  - Cooldown: 8s → 6s
  - Removed: 20% movespeed bonus when hit

**Shoes**

> _Vengeful Sprint has fallen by the wayside after its previous nerf. Some of its bonus speed has therefore been returned to support it as a boot option with sharper moments of power, but not to the point that it becomes ubiquitous._

- Vengeful Sprint (Demon Boots)
  - Move speed per stack: 22% → 25%

**Miscellaneous**
- These abilities no longer require line of sight:
  - Boulder Crash (Earthrune Staff)
  - Lightning Storm (Battle Eagle)

- These abilities now have more accurate spell indication areas:
  - Hail (Great Frost Staff)
  - Glacial Obelisk (all Frost Staffs)

- These abilities have had their skillshot indicators adjusted:
  - Searing Flame (all Fire Staffs)
  - Magma Sphere (Wildfire Staff)
  - Fire Wave (all Fire Staffs)
  - Rising Blow (all Quarterstaffs)
  - Cartwheel (all Quarterstaffs)

- These abilities now scale their slow duration with AoE escalation:
  - Caltrops (all Crossbows)
  - Frost Bomb (all Frost Staffs)
  - Frozen Surge (all Frost Staffs)
  - Glacial Obelisk (all Frost Staffs)
  - Hail (Great Frost Staff)

- Slowing Charge (all Hammers)
  - AoE slow escalation now increases slow duration instead of slow strength

- Frost Bomb (all Frost Staffs)
  - Initial slow area is no longer affected by diminishing returns, crowd control resistance, or ability power scaling

### Fixes

**Spell Fixes**
- Spontaneous Combustion (Flamewalker Staff): Fixed issue where the transformation could be treated as a valid target by other spells or effects

**UI Fixes**
- Fixed issue where clicking a character’s name in the player context menu opened via chat could cause unintended movement

**Other Fixes**
- Fixed issue where Raid Banners could continue to reduce Fortification damage protection even after being dropped
