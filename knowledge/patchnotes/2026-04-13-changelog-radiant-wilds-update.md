<!-- gid: 1829528821315042 -->
# Changelog: Radiant Wilds Update

_date: 2026-04-13 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1829528821315042_

> _This update transforms Albion Online with a sweeping visual overhaul across the open world. Landscapes, lighting, vegetation, and water have all been refreshed to bring new life to every biome. Major performance improvements make exploration and combat smoother than ever, while the Armory build system, fast-paced 1v1 Arena battles, and improved controller support give you new ways to engage with the world._

### Visual Overhaul

Radiant Wilds introduces a major visual rework of Albion’s open world. This refreshes the game’s visuals while preserving its distinctive artistic style, strengthening each biome’s unique identity and making the world feel more immersive and vibrant.

**Biome Identity and Terrain**

Each biome has been visually transformed to better reflect its environment and create clearer contrasts between regions.
- Updated terrain colors, vegetation, and environmental assets across all biomes
- Refined ground textures to feel more physical and varied depending on the biome
- Improved contrast and color intensity to make biomes more distinctive
- Adjusted terrain colors and textures to better match the style of Albion’s characters and creatures

**Water and Lighting**

Water shaders and environmental lighting have been updated to improve the atmosphere and bring more life to the landscape.
- Water now reflects the character of its surrounding environment, from murky swamp waters to slow-moving icy streams
- Rivers, lakes, and coastlines now reflect the sky, clouds, and sunlight more naturally
- Wet surfaces, snow, and sand reflect light more realistically
- Sunlight intensity and color grading have been refined
- Cloud shadows move across the landscape
- Shorelines and shallow water blend more naturally with the surrounding terrain

**Environmental Detail**

Many small environmental elements have been added or refined to make the world feel richer and more alive.
- Vegetation and biome-specific environmental assets updated
- Ground textures improved to feel more physical, for instance mossy undergrowth, muddy marshes, and sandy dunes
- New atmospheric effects added such as drifting pollen, sand gusts, and snow particles
- Small environmental details added like insects and airborne foliage

**Arrival Experience**

The tutorial beach has also been updated to create a stronger first impression for new players.
- The arrival beach scene features improved lighting, textures, and environmental detail
- New environmental assets such as wreckage pieces, shells, and coastal vegetation enhance the atmosphere of the starting area

### Performance Improvements

This update introduces several client and network optimizations aimed at reducing stutters and improving performance during demanding situations such as large-scale battles. This is the first step in an ongoing effort to further optimize the game’s performance, including continued work with hosting partners to improve connection stability across all regions.
- Expanded the use of asynchronous loading for assets, prefabs, and visual effects to reduce blocking during gameplay
- Updated systems responsible for loading environmental objects and dynamic world elements
- Adjusted how certain spell effects are processed to be less burdensome
- Applied performance optimizations to numerous other visual effects and rendering assets
Additional network monitoring improvements have also been introduced:
- Added a packet loss indicator to help players monitor connection issues
- Added additional telemetry and logging tools for monitoring network performance

### The Armory

The Armory is a new system designed to help players discover effective equipment builds based on real gameplay performance. Players can explore equipment combinations that have proven successful in specific types of content. The Armory continuously evaluates gameplay data; as balance changes or player strategies evolve, build recommendations update automatically to reflect current trends.

The Armory can be accessed from the Player Menu, or through an individual item’s details UI.
- When opened from the Player Menu, a landing page is displayed where players select the type of content they want to play
  - Activities can be filtered by activity type and group size

- After selecting an activity, the Armory displays equipment builds that perform well in that type of content
  - Builds can be filtered further by selecting performance metrics such as win rate, damage, or popularity, and by choosing between recent or more established builds
  - The equipment list can also be filtered by type, letting players browse builds centered on specific equipment pieces

- Each result shows a full equipment setup, including abilities and consumables, providing a quick overview of how successful builds are configured in practice
- Each build includes performance indicators to help players compare different setups, including variations in consumables and abilities
  - These metrics are displayed as a radar chart, allowing builds to be compared at a glance

- Selected builds can be saved as Loadouts directly, letting players quickly prepare a full equipment setup and jump into the activity they want to play
- The Armory can also be accessed by opening an item’s details UI, and scrolling down to the ‘Recommended Builds’ section
  - Clicking ‘View Build’ next to one of these recommendations will open that build within the Armory

### Arena Improvements

**1v1 Arena**

The 1v1 Arena is a new ranked PvP mode focused on structured one-on-one combat. It launches as a limited-time mode, running for the duration of Season 32.
- Matches can be entered solo via the Arena Master
- Equipment is soft-capped at 900 Item Power, with excess IP reduced by 80%
  - Combat Potions above 900 IP use their 900 IP effects instead
  - Healing is decreased by 40%

- Matches are played in a best-of-three format
  - If a round lasts too long, overtime begins and poison gas gradually closes in to force engagement

- The mode has its own rank and Rank Points (RP) system
  - Ranks progress independently from the existing 5v5 Arena
  - Rewards increase with rank progression

**Crystal Arena**
- A new Crystal Arena map has been added to refresh gameplay and shift the competitive meta
  - Includes new chokepoints and additional flanking paths

- The Crystal Arena now allows groups of four players to queue together, helping improve matchmaking flexibility and queue times

**Other Changes**
- The Arena Rank UI now automatically scrolls to your current rank when opened
- Updated base tent invulnerability behavior in Crystal League, Crystal Arena, and custom matches:
  - Attacking no longer removes the invincibility effect
  - Healing begins 3 seconds after entering the area and stops when leaving it
  - Players standing in the base tent area are healed for 5% of their health and energy every second

### Enhanced Controller Support

Controller support has been significantly improved with new interface systems and combat options.
- Dedicated controller HUD for gamepad play
  - This is fully customizable through the HUD Editor

- Updated UI navigation across menus and windows to better support controller input
  - Added a full-screen controller menu that provides quick access to key systems
  - Added customizable radial menus for faster access to common actions

- Added multiple controller control schemes to support different playstyles
  - Includes configurable targeting modes, allowing players to filter targets
  - Expanded auto-targeting options, allowing players to customize targeting behavior, lock modes, and priority rules

### Battle Mount Changes

**Battle Mount Disarray**

Battle mounts are meant to be powerful tools that can turn the tide of large-scale battles. Over time, however, bringing large numbers of them became increasingly common and often felt mandatory in ZvZ fights. To address this, battle mounts now contribute to the existing Disarray system.
- Each battle mount adds a fixed Disarray value to its group when present in a region
  - Ancient Ent: 2
  - Battle Eagle: 4
  - Battle Rhino: 2
  - Behemoth: 4
  - Colossus Beetle: 5
  - Command Mammoth: 5
  - Flame Basilisk: 5
  - Goliath Horseeater: 3
  - Juggernaut: 4
  - Phalanx Beetle: 2
  - Roving Bastion: 5
  - Siege Ballista: 2
  - Tower Chariot: 5
  - Venom Basilisk: 5

- This contribution is calculated alongside the existing Disarray scaling and only starts when the total Battle Mount Disarray contribution exceeds 15 points
  - Only the excess value above 15 is added to the alliance’s Disarray

- Each battle mount now displays its Disarray contribution in the item details UI
- A status icon is displayed showing the current Disarray contribution
- The maximum number of Disarray levels has been extended to 99

### Party Leave Protection

A protection system has been added to make it safer to team up with unfamiliar players by preventing immediate attacks after leaving a party.
- When a player leaves or is removed from a party, they and their former party members cannot attack each other for 30 seconds
- The same temporary protection also applies when leaving or being removed from a guild or alliance
- This protection does not apply when an alliance dissolves or when a guild leaves an alliance

### Faction Warfare Changes

To improve access to red zones and encourage more movement between regions, several environment adjustments have been made across the Royal Continent.

**Yellow to Red Zone Connections**

Several underground passages between yellow and red zones have been removed and replaced with direct region connections. This simplifies access to red zones and removes some of the friction players previously encountered when entering lethal areas.

Connections added:
- Willowsigh Marsh ↔ Darkground Swamp (Swamp Burrow removed)
- Cairn Camain ↔ Creag Dhor (Ore Adit removed)
- Yew Wood ↔ Owlsong Glen (Forest Burrow removed)
- Lazygrass Plain ↔ Kindlegrass Steppe (Sabertooth Den removed)
- Eldon Hill ↔ Bowscale Fell (Rock Adit removed)
Players who logged out inside one of these passages before the update launch will be moved to the nearest valid region.

**Caerleon Access and Region Connections**

To reduce regional advantages between Factions and ensure more consistent travel distances to Caerleon from yellow zones, several region connections on the Royal Continent have been adjusted.
- Removed the connection between Wyre Forest and Murkweald
- Added a new connection between Murkweald and Longtimber Glen
- Moved the Caerleon Underway entrance in Longtimber Glen to the opposite side of the map from the new Murkweald entrance
- Replaced the direct connection between Roastcorpse Steppe and Broken Fell with a passage

**Faction Camp Distribution**

The number of Faction Camps has been adjusted to encourage players to move across multiple regions instead of concentrating in the same few areas.
- The number of Medium Faction Camps available has been reduced in several regions

### UI Changes

**Destiny Board Improvements**

The Destiny Board has been updated to improve clarity and progression visibility, especially for newer players.
- Nodes that cannot yet be progressed are now hidden by default
  - Areas beyond current progression become visually subdued, with obscured distant nodes and connections toward the edges of the board
  - This can be toggled with the ‘Show all Nodes’ option on the Destiny Board

- Connections to locked nodes now display partial progress toward unlocking their first level
- When referencing hidden nodes in the Item Details UI, the Destiny Board now opens the nearest visible parent node instead
- The Reaver line have been removed from the Destiny Board
  - Avatars previously unlocked through Reaver nodes have been moved to Albion Journal missions tied to similar PvE Fame milestones
  - Reaver Line related Albion Journal missions have been archived
  - Solo, Group, and Hardcore Expeditions no longer require matching Reaver bonuses

**Take All**

A Take All option has been added to loot windows:
- All items from PvE drops and chests can now be looted with a single click
  - This does not include treasure chests that spawn in the open world, the Depths, the Mists, Faction Warfare or during temporary events

- This only applies to situations where all loot is guaranteed to the player
- Items are taken in order until carry weight limit is reached
- Not available for items dropped by other players

**Other Changes**
- Introduced a new window focus system:
  - Multiple UI windows can now remain open at the same time instead of closing each other
  - Interacting with a window automatically brings it to the front, preventing overlapping or hidden interface elements

- The Laborer UI has been updated with a new design to match the rest of the game's interface
  - Added warnings before sending laborers and after their return that uncollected items are removed after 7 days

- The Loot UI now displays 4 columns instead of 3, allowing more items to be visible at once
- Adjusted the default replacement settings of the Lost Equipment Loadout to:
  - Tier: Same
  - Enchantment: Same
  - Quality: Same or Higher

- Potion and Food slots in the Action Bar now display the number of items equipped
- Added buttons to the Region Map to place pings and return to the map of the current region
- Item Details UI now shows estimated market value per item and for the entire stack

### Combat Balance Changes

**Axes**

> _Battle Rush’s cooldown has been reduced to help Axes keep up with enemy mobility in 1v1 situations, while also increasing uptime on its supportive buffs in group PvP._

- Battle Rush (all Axes)
  - Cooldown: 20s → 18s

> _Crystal Reaper has continued to overperform in PvE, so it has been adjusted to allow alternative options to compete._

- Relentless Assault (Crystal Reaper)
  - Damage vs mobs: 95 → 86

**Bows**

> _Sky’s Fury has had its energy cost adjusted so that players can no longer get stuck mid-air due to running out of energy. Its damage per bolt has also been reduced, as it was dealing too much damage while limiting most enemy counterplay._

- Sky's Fury (Skystrider Bow)
  - Damage per bolt: 140 → 128
  - Initial cast energy cost: 12 → 18
  - Bolt energy cost: 3 → 0

**Crossbows**

> _Arclight Blasters have been overperforming in both solo and small-scale PvP, so they’ve had some damage removed to promote equipment diversity._

- Flickershots (Arclight Blasters)
  - Damage per cast: 101 → 94

> _Vicious Barrage has had part of its damage shifted into percentage health to reduce the effectiveness of multiple Siegebows hitting the same targets._

- Vicious Barrage (Siegebow)
  - Damage: 130 → 105
  - Current health damage: 2.5% → 3%

**Cursed Staffs**

> _Fear duration at all Vile Curse stack counts has been increased to allow Anguished Soul to operate better as a defensive tank or provide crowd control during small-scale burst windows._

- Anguished Soul (Demonic Staff)
  - Fear duration at 0 stacks: 1s → 1.25s
  - Fear duration at 1 stack: 1.25s → 1.5s
  - Fear duration at 2 stack: 1.5s → 1.75s
  - Fear duration at 3 stack: 1.75s → 2s
  - Fear duration at 4 stack: 2s → 2.25s

**Fire Staffs**

> _Combustion now also fears all enemies within 4m of the initial target. The targeted enemy remains the only one with a trail, while feared mobs now run away at a lower speed._

- Combustion (Infernal Staff)
  - Added: Initial fear hits enemies in a 4m AoE around the target
  - Feared mobs no longer run as far

> _Flaming Phoenix’s instant damage has been reduced to lower its burst potential in large-scale fights._

- Flaming Phoenix (Dawnsong)
  - Instant damage: 225 → 200

> _Flamewalker Staff has been overperforming in solo PvP and has had its impact damage reduced to promote equipment diversity._

- Spontaneous Combustion (Flamewalker Staff)
  - Impact Damage: 189 → 178

**Frost Staffs**

> _Arctic Volley’s cooldown has been reduced to make it more reliably powerful, while its damage per volley has been reduced._

- Arctic Volley (Arctic Staff)
  - Cooldown: 15s → 12s
  - Damage per tick: 90 → 76
  - Energy cost per tick: 3 → 2

**Hammers**

> _Polehammer has had its damage lowered significantly to reduce the strength of its poke-and-kite play pattern in solo PvP._

- Groundbreaker (Polehammer)
  - Damage: 77.7 → 46

**Holy Staffs**

> _Holy Orb’s stand time has been reduced, making it feel more fluid to use and offering its caster greater mobility._

- Holy Orb (all Holy Staffs)
  - Stand time: 0.4s → 0.25s

**Maces**

> _Guard Rune has been a dominant, universal defensive tool that answers a wide range of threats. It now covers more allies, but its resistance increase has been significantly reduced while preserving its strong anti-CC properties._

- Guard Rune (all Maces)
  - Players: 5 → 10
  - Resistance: 0.2 → 0.06

> _Deep Leap’s damage has been increased to promote solo and bruiser play._

- Deep Leap (all Maces)
  - Damage: 180 → 203

**Quarterstaffs**

> _Quarterstaff has continued to overperform in solo PvP, so its damage has been reduced further to promote equipment diversity._

- Vault Leap (Quarterstaff)
  - Damage: 180 → 161

> _Phantom Twin’s first and second casts have gained additional damage to reward keeping enemies within the areas._

- Phantom Twin (Phantom Twinblade)
  - First and second cast damage per tick: 41 → 46 (Total damage: 205 → 230)

**Shapeshifter Staffs**

> _Tear Open’s Blood Pool now requires two Shift Charges to put more pressure on Shift Charge upkeep and reduce sustain._

- Tear Open (Bloodmoon Staff)
  - Blood Pool now requires 2 Shift Charges

> _Lightcaller players in solo PvP have been too slippery, so their passive immunity to slow has been removed to offer opponents additional counterplay._

- Dawnbird Transformation (Lightcaller)
  - No longer grants immunity to slow effects

> _Wild Onslaught has had its damage increased significantly to help Primal Staff players compete._

- Wild Onslaught (Primal Staff)
  - Damage: 50 → 85

**Swords**

> _Clarent Blade’s three-stack damage effect has been increased to help it find a place once again._

- Crescent Slash (Clarent Blade)
  - 3 stack damage: 160 → 170

> _Carving Sword’s mobility has been reduced to promote equipment diversity in solo PvP content._

- Fearless Strike (Carving Sword)
  - Cooldown: 20s → 25s

**War Gloves**

> _Counter has been significantly buffed to make it a more attractive option against opponents with telegraphed damage abilities._

- Counter (all War Gloves)
  - Reflect percentage: 100% → 150%

> _Earth Crusher has had its damage increased to help it perform in large-scale combat._

- Earth Crusher (Ravenstrike Cestus)
  - 0 charge damage: 155 → 165
  - 1 charge damage: 165 → 175
  - 2 charge damage: 175 → 185
  - 3 charge damage: 185 → 195

> _Falcon Smash has had its multicast time window increased to give players more time in the air to aim._

- Falcon Smash (Battle Bracers)
  - Multicast time window: 2s → 3s

**Helmets**

> _Hush’s cooldown has been reduced to make it more reliable._

- Hush (Demon Helmet)
  - Cooldown: 30s → 25s

**Shoes**

> _Dodge has had its mobility increased to incentivize switching to it in certain matchups._

- Dodge (all Shoes)
  - Movement speed buff duration: 4s → 5s

### Fixes

**UI Fixes**
- Fixed issue where the Personal Loadouts list would scroll back to the top after opening a loadout from a filtered list

**Mob Fixes**
- Fixed issue where the Energy Singularity spawned by the Dawnbird tracking mob could take full damage shortly after spawning
- Fixed issue where Dryad's Tendrils VFX did not match its duration
- Fixed issue where the Bandit Ringleader's torch throw had no spell indicator before impact
- Fixed issue where Undead Mage's Blizzard VFX faded before the spell ended
- Fixed issue where Undead Ghost's Blizzard indicator persisted after the spell ended
- Fixed issue where mobs could sometimes move incorrectly across certain terrain

**Other Fixes**
- Various additional graphical, animation, terrain, audio, UI, and localization fixes
