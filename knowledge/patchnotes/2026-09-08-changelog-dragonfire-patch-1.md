<!-- gid: 1842846814455196 -->
# Changelog: Dragonfire Patch 1

_date: 2026-09-08 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1842846814455196_

> _This patch brings important adjustments and fixes to features introduced with the Dragonfire update._

### Ancient Lands Changes

We’ve been closely following feedback around Ancient Lands portal availability and the amount of time players currently spend waiting at portal entrances. These changes are intended to make portals easier to find, reduce unnecessary waiting, and give groups more opportunities to explore the Ancient Lands while the feature is still new.
In the longer term, the Ancient Lands are intended to be opportunity-driven content that appears more spontaneously during regular gameplay, rather than something that is always readily available. Portal availability and timings may therefore be adjusted again in future updates as we move closer to that intended balance.
Several adjustments have been made to Ancient Lands portals to reduce waiting times and improve entry windows. In addition, changes have been made to mob health in large group variants to speed up progression through larger encounters, and to island quest completion requirements in all forms.
- Small Portals
  - Lock Time: 30 minutes → 15 minutes
  - Time available to enter after unlocking: 3 minutes → 8 minutes

- Medium Portals
  - Time available to enter after unlocking: 3 minutes → 5 minutes

- Large Portals
  - Portal lifetime: 45 minutes → 60 minutes
  - Time available to enter after unlocking: 3 minutes → 5 minutes
  - Regular enemy Health reduced by 50%
    - Drakes are unaffected

- Portals are now always visible on the World Map, regardless of distance
- Ancient Lands island quests now require defeating 50% of the mobs on an island instead of earning a set amount of Fame
  - Marmots do not count toward this requirement

### Dragon Sanctuary Changes

These are some initial adjustments based on the Dragon Sanctuary attempts we've seen so far. We’ll need some time to review combat data, player progression, and feedback, and we’ll likely make further adjustments in future patches.
With high-end PvE content like the Dragon Sanctuary, it takes time to distinguish between mechanics that are still unfamiliar to players and those that may genuinely be overtuned, particularly at Tier 8.1 and above. These encounters are intended to be highly challenging, but should feel fair once their mechanics are understood. Please continue to give your feedback, as we're closely following your attempts and progress!
- Maeve's Boulders no longer dash during her Primal Dragon Flame ability
  - This behavior occurred only rarely and should no longer occur

- Maeve's Rock Spike stacks now clear correctly when the effect ends
  - This was a visual issue only and did not affect gameplay

- Azaryon’s Inferno, which requires players to hide behind rocks, now deals significantly more damage toward the end of the attack
  - This does not increase the attack’s intended difficulty, but more strongly punishes ignoring the mechanic entirely

- Reduced the duration of Lingering Dragon Spirit by approximately 2 hours
  - This is designed to make it easier for players to follow a consistent weekly raid schedule

### Other Changes

- Combined specialization node UIs on the Destiny Board can now be closed by clicking anywhere on the Destiny Board
- Reduced the UI scale of Destiny Board specialization nodes when hovered to prevent overlap with other nodes
  - Item icons have been enlarged at the same time to improve readability

- Improved profanity filtering in chat and in player-generated names, including better detection of common variations of blocked terms

### Combat Balance Changes

**Maces**
- Blessed Aurora (Oathkeepers)
  - Heal on auto-attack: 66 → 50

### Fixes

**Ancient Lands Fixes**
- Fixed an issue where Blessings could be removed upon knockdown or death
- Fixed an issue where certain mobs dropped significantly more Silver than intended upon death
  - Chest loot is unaffected

- Fixed issue where defeating Mammoth Hunters did not count toward the corresponding Albion Journal mission
- Fixed issue where players defeated by a damage-over-time effect could become invulnerable instead of entering the Bleedout state

**UI Fixes**
- Fixed issue where sent whispers could appear as if they had been received from oneself
- Fixed issue where specialization bonus values were cut off in Destiny Board flyouts
- Fixed issue where the ‘Collapse Tracker’ button would be positioned incorrectly when the Combined HUD Tracker was placed on the left side of the screen
- Fixed issue where Dragon Armor would display the mastery level of the corresponding Avalonian Armor instead of its own
- Fixed issue where the Item Details UI would remain open after clicking the ‘Take’ button

**Other Fixes**
- Fixed issue where cleared enemies in the Dragon Sanctuary could respawn after three hours
- Fixed issue where Spirit Weavers’ summons would remain active after the Spirit Weaver was defeated
- Fixed issue where Dragon Attacks could remain active beyond their three-hour duration if no players were nearby when they were due to despawn
-  Fixed issue where Destiny Board search results could not be scrolled through fully with the right analog stick
-  Fixed issue where the price slider for Buy and Sell Orders was not set correctly
-  Fixed issue where ‘Cancel Order’ and ‘Apply Market Average’ had overlapping Y-button inputs when editing active Buy Orders
- Various additional controller, graphical, animation, terrain, audio, UI, and localization fixes
