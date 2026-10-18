<!-- gid: 1795283637782156 -->
# Changelog: Rogue Frontier Patch 4

_date: 2025-03-26 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1795283637782156_

> _This patch improves the Conqueror's Challenge reward system with better tracking and reward claiming for past seasons. It also includes combat balance changes, bug fixes, and gameplay improvements._

### Changes

**Conqueror’s Challenge Changes**

A new Conqueror’s Challenge History Tab has been added, allowing players to track their past seasons and claim rewards more easily.
- Players can now view their stats and rewards from previous seasons by selecting them from a dropdown menu
Within this new tab, rewards can be claimed through an improved UI:
- Conqueror’s Chest rewards now appear as a list of claimable items instead of a single chest
  - Players can claim items individually or use ‘Claim All’ to collect as much as their inventory space allows

- Knight’s Vows and Avatars are sent directly to the inventory when claimed

**Other Changes**
- Personal and Guild tabs within a Guild Bank are now visually distinguished

### Combat Balance Changes

**Frost Staffs**

> _To increase the consistency of Arctic Volley, each icicle has been adjusted to slow all targets hit, making it easier to land multiple volleys._

- Arctic Volley (Arctic Staff)
  - Slow per hit: 10% for 1s (stacks up to 6 times)

**Holy Staffs**

> _As Holy Staff has been a dominant option in the 2v2 meta, the energy cost of Desperate Prayer has been increased to make energy denial a possible counter._

- Desperate Prayer (Holy Staff)
  - Energy cost: 12 → 15

**Nature Staffs**

> _Since Druidic Staff has fallen out of the meta following previous nerfs, the additional cooldown for recasting Spiritual Seed has now been removed to increase its healing output in group play._

- Spiritual Seed (Druidic Staff)
  - Recast cooldown: 25s → 20s

**Shapeshifter Staffs**

> _Bloodmoon continues to be a problem for larger groups to deal with. To give enemies a better chance at bursting a Werewolf down, their max health while transformed has been reduced._

- Werewolf Transformation (Bloodmoon Staff)
  - Transformation health: 1100 → 1000

**Swords**

> _Infinity Blade’s popularity has increased since Limit Breaker stopped consuming its damage buff. To reduce its brawling power somewhat, its long buff duration has been reduced._

- Limitbreaker (Infinity Blade)
  - Damage buff duration: 7s → 5s

**Helmets**

> _Smokebomb has been adjusted to no longer silence party members, as this behavior was difficult to control and led to frustrating gameplay experiences._

- Smokebomb (Hellion Hood)
  - No longer silences group members

**Shoes**

> _The stun duration for Crush Charge – a highly telegraphed ability – has been increased to make it more rewarding, especially since it takes the place of a traditional mobility option._

- Crush Charge (Duskweaver Boots)
  - Stun: 2.35s → 2.5s

**Capes**

> _Capes that primarily scale their cooldowns with Item Power have not provided enough value to warrant their increasing cost per tier. With significantly shorter cooldowns at higher tiers, these capes can now become a more reliable build component._

- Berserk (Keeper Cape)
  - Base cooldown: 112.5 → 150
  - Cooldown reduction: 2.5s → 7.5s (95s → 98s at 700 IP, 73s → 30s at 1600 IP)
  - Buff duration: 6s → 5s

- Devious Trap (Heretic Cape)
  - Base cooldown: 112.5 → 150
  - Cooldown reduction: 2.5s → 7s (95s → 101s at 700 IP, 73s → 38s at 1600 IP)

- Mark of the Raven (Morgana Cape)
  - Cooldown reduction: 3.1s → 6s (98s → 78s at 700 IP, 70s → 24s at 1600 IP)
  - Buff duration: 8s → 5s

**Miscellaneous**
- Hellgates
  - Rising Lava stacks now persist after being knocked down while inside the lava
  - Rising Lava stacks now break shields and cause immunity against shield effects

### Fixes

**Spell Fixes**
- Enfeeble Blades (Lifecurse Staff)
  - Fixed issue where enemies would continue having their buffs purged shortly after leaving the target area
  - Fixed issue where enemies could become invisible within the target area

- Fixed issue where Holy Beam (Holy Staffs), Hover (Sandals of Purity), and Levitate (Cultist Robes) could have their channeled effects purged

**UI Fixes**
- Fixed issue where removing an item from either the Main Hand or Off-Hand slot in the Loadouts menu would clear both slots
- Fixed issue where Tracking Toolkits could be placed in the weapon slot when creating a Loadout
- Fixed issue where the Overcharge confirmation pop-up could appear twice when using a hotkey
- Fixed issue where Crystal Weapon combat and crafting specializations on the Destiny Board displayed incorrect bonus values
- Fixed issue where the item icon in the furniture UI was selectable but not clickable with a controller
  - The icon is now clickable across all inputs to open the furniture item's details UI

**Other Fixes**
- Fixed issue where the following mobs would deal significantly higher damage than intended:
  - Earthkeeper Shaman
  - Avalonian High Priestess
  - Sir Bedivere
  - Castle Mortar
  - Champion of Fort Sterling
  - Bandit Ringleader

- Fixed issue where items that cannot drop as loot could be listed for sale on the Black Market
- Various additional graphical, animation, terrain, audio, UI, and localization fixes
