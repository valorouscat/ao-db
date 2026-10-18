<!-- gid: 1818118366169616 -->
# Changelog: Realm Divided Patch 1

_date: 2025-12-03 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1818118366169616_

> _Adjustments to new features introduced with the Realm Divided update, along with important fixes to a few gameplay issues._

### Faction Warfare Changes

**Faction Travel Costs**
- Resolved an issue that caused carrying some items to be much more expensive than intended
  - This primarily affected high-value items, and when traveling to lethal Provinces or back to cities

- Travel distances are now determined by Provinces instead of Regions to fairly distribute the cost across Factions
- Traveling from a city to an adjacent non-lethal Province is now free, to eliminate the possibility of having to pay to transport directly outside
- Prices have been adjusted to accommodate these new rule changes

**Other Changes**
- Added three additional Siege Times on all servers (all times UTC):
  - Albion Asia: 02:00, 05:00, 19:00
  - Albion Americas: 05:00, 13:00, 17:00
  - Albion Europe: 01:00, 09:00, 23:00

- The Pre-Siege period has been reduced to 10 minutes
- The respawn time of Faction Camps has been slightly randomized to distribute the availability of active camps more unpredictably
- Increased the bonus to Supply generation when a Faction falls a certain amount behind
  - This bonus was increased from 50% to 75% and now activates when a Faction is more than 30% behind another (previously 75%)
  - This bonus only applies once the Faction has generated at least 3,000 Supply in a Province

### Fixes

**Faction Warfare Fixes**
- Fixed issue where players could use Faction Transports to travel directly to friendly Outposts in lethal Provinces
- Fixed issue where Fortress Sieges won by defenders during server maintenance would not trigger an attack on a neighboring Province
- Fixed issue where parties would continue to appear as Faction Transport destinations when full
- Fixed issue where Faction Transport to a party in a lethal zone could place players further away than intended
- Fixed issue where changing party leader to a different Faction could prevent Faction Transport destinations from updating correctly
- Fixed issue where Faction bonuses would display within cities
-  Fixed issue where players using virtual controller could not resume attacking Fortress walls if interrupted

**UI Fixes**
- Fixed issue where the Party Finder could crash when listing existing parties
- Fixed issue where Crystal Arena season end time displayed incorrectly
-  Fixed issue where the 'Send Ping At Your Current Position' action would not accept controller keybinding

**Other Fixes**
- Fixed issue where party loot distribution settings would not apply to most chests
- Fixed issue where the /report command would not work
-  Fixed issue where players could only target the closest ally with spells, preventing proper healing
-  Fixed issue where target cycling could select only enemies
- Various additional graphical, animation, terrain, audio, UI, and localization fixes
