<!-- gid: 1784506359205047 -->
# Changelog: Horizons Patch 3

_date: 2024-12-04 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1784506359205047_

> _This patch further refines the Horizons update with tweaks and fixes. We are also reintroducing developer notes for Combat Balance changes to provide more context for these adjustments._

**Note for Android users: With this patch, we are rolling back the recent platform migration introduced with the Horizons Update. This will again require a larger-than-normal installation. If you experience space issues, please uninstall the Albion Online app before performing a clean install.**

### Changes and Improvements

**Albion Journal Missions**
- Collect 20 offspring in 10 minutes on a single island → Have offspring from 10 different animals

**HUD Editor**
- Default Spells and their Transformation Spells are now always displayed
  - If Vanity Spells are in use, they will switch to the default spells while the HUD Editor is open

**Dynamic Encampments**
- Lair Maps in Solo Encampments are now hidden until the Encampment's objective has been completed by a player. Once completed, the Lair Map becomes visible to all players
  - This change does not affect Lair Maps in Group Encampments

**Other Changes**
-  Adjusted Custom Button Slot hotkey assignments:
  - ‘Recording Mode,’ ‘Walk Up,’ ‘Walk Down,’ ‘Walk Right,’ and ‘Walk Left’ can no longer be assigned to custom buttons
  - ‘World Map’ and ‘Destiny Board’ can now be assigned

### Combat Balance Changes

**Arcane Staffs**

> _Frazzle has been outshined by Enigma Blade in DPS arcane builds, even in smaller group fights. We’ve increased its burst damage to make it more competitive, even if allies don’t take advantage of the powerful damage-amplifying component._

- Frazzle (all Arcane Staffs)
  - Now reduces enemy defenses before dealing damage
  - Damage: 103.11 → 125

**Daggers**

> _Bridled Fury players have struggled to find success in ZvZs, so we’ve reintroduced some resilience penetration to make Merciless Finish live up to its name._

- Bridled Fury
  - Resilience penetration: 30% → 35%

**Frost Staffs**

> _Ice Storm hasn’t been very popular, despite its high damage potential. We've reduced its travel distance to boost area denial and threat to keep chokes covered longer. We've also reduced its cast and stand times to make its use smoother._

- Ice Storm (Glacial Staff)
  - Cast time: 1s → 0.5s
  - Stand time: 0.5s → 0.3s
  - Travel distance: 18m → 12m (1.2m/s → 0.8 m/s)

**Holy Staffs**

> _We’ve smoothed out Sacred Pulse’s animation and stand time for a better experience in both PvE and PvP._

- Sacred Pulse (all Holy Staffs)
  - Stand time: 0.5s → 0.3s

**War Gloves**

> _Counter is outshined by other War Gloves’ W abilities in most contexts. Extending the powerful defense buff should provide more flexibility, allowing players to either disengage more safely or follow up confidently after a successful counter._

- Counter (all War Gloves)
  - 75% defense buff duration: Up to 1.2s → always 2s

> _Ravenstrikes haven’t been performing well in ZvZs, despite recent buffs. A big downside is that while the damage can be reflected, the caster can't cancel the channel once the ability has started. So we’ve made the ability non-reflectable to make it less likely to die to Demon Armor in ZvZ. Since this makes it significantly more valuable, we’ve reduced its damage slightly._

- Earth Crusher (Ravenstrike Cestus)
  - No longer reflectable
  - 0.5s Charge-up damage : 179 → 175
  - 1s Charge-up damage : 190 → 185
  - 1.5s Charge-up damage : 202 → 195
  - 2s Charge-up damage : 214 → 205

**Helmets**

> _Royal Helmet is currently only used by niche one-shot combo builds. To encourage tank and support use, we’ve significantly reduced its cooldown._

- Ballista Support Fire (Royal Helmet)
  - Cooldown: 40s → 30s

**Armors**

> _Dynamic Defense is strong and popular in ZvZs as both an offensive and defensive tool. Due to the prevalence of reflect, Dynamic Defense has been putting pressure on DPS players to strongly consider only magic damage weapons, as Jacket of Tenacity would do double duty as a strong defense against enemy reflect while also providing a damage boost that brings magic damage users close to the damage levels of cloth armor. We’ve reduced the maximum damage potential, but allowed players to choose the optimal defensive buff without losing access to the bonus damage._

- Dynamic Defense (Jacket of Tenacity)
  - 20% bonus damage based on opponents weapon → 10% bonus to all damage types

**Shoes**

> _Scholar Sandals have fallen short of their promise to be a complete energy solution, so we’ve significantly increased their mana regeneration._

- Focused Run (Scholar Sandals)
  - Energy per tick: 2.63 → 4 (max 26.3 → 40)

> _Demon Boots' movement speed was previously reduced to prevent them from being a guaranteed ‘get out of jail free card’. However, since they are now a fairly underused item, we believe they deserve a cooldown in line with other sprints in their class._

- Vengeful Sprint (Demon Boots)
  - Cooldown: 40s → 30s

**Potions**

> _Underutilized potions have been given significant buffs to make them more competitive with their alternatives._

- Acid Potion (all Tiers)
  - Increased armor and magic resistance reduction by 50%

- Cleansing Potion (Tiers 3.1 and above)
  - Added 30% movement speed buff for the duration of immunity only if CC or debuffs are removed

- Hellfire Potion (all Tiers)
  - Added 35% healing reduction for 3s to all targets hit
  - Increased true damage to players and mobs by 25%
  - Cooldown 60s → 90s

- Sticky Potion (all Tiers)
  - Increased damage reduction by 50%

- Tornado in a Bottle (all Tiers)
  - Radius: 3m → 4m
  - Cooldown: 90s → 60s

**Misc**
- Deflecting Spin (all Spears)
  - No longer stops moving on usage

- Mimic (all Arcane Staffs)
  - No longer queues auto-attacks after casting

### Fixes

**Spell Fixes**
- Fixed issue where spells that activate at a certain health threshold would not be triggered by damage from potions
- Fixed issue where mounting up immediately after casting an invisibility spell would not break the invisibility
- Mend Wounds (all Armors): Fixed issue where it would sometimes override movement commands

**Mob Fixes**
- Fixed issue where Morgana Occultists in the Mists would not spawn bats after using their instant ability

**UI Fixes**
- Fixed issue where search filters would reset after switching tabs in the Marketplace UI
- Fixed issue where clicking a loadout shared in chat would also move the character to the clicked position
- Fixed issue where the Building Management UI of some tiers of Guild Halls and Houses could not be opened while inside
- Fixed issue where the Element Switch button could appear on invalid elements when opening the HUD Editor
  - This button is no longer available on Desktop

-  Fixed issue where selected emotes in the Key Bindings settings would reset when selecting a Custom Button Slot
-  Fixed issue where the on-screen keyboard obstructed the Loadouts dropdown in the Marketplace UI

**Other Fixes**
- Fixed issue where static Randomized Dungeon entrances in the Roads of Avalon would not be visible
- Various additional graphical, animation, terrain, audio, UI, and localization fixes
