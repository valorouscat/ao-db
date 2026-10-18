<!-- gid: 1833334318578987 -->
# Changelog: Radiant Wilds Patch 2

_date: 2026-05-26 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1833334318578987_

> _This patch introduces further improvements and polish for features introduced with Radiant Wilds, including controller support, the Armory, and the visual overhaul, alongside combat balance changes and various fixes._
_Please note: With this patch, the minimum supported iOS version has been raised from iOS 14.3 to iOS 15. Devices that cannot update to iOS 15 or higher will no longer be supported._

### Controller Improvements

- Polished navigation, button hints, tooltips, and highlights across multiple UI elements
- Quick messages can now be used through chat
- Improved Farming navigation flow and controls
- Polished Fishing interaction prompts and visual feedback
- Added a ‘Changelog’ entry in the Game Menu that links directly to the latest patchnotes
- Adjusted target selection visuals to better match target sizes
- Improved line indicator that moves between targets when switching manually
- Updated Gold Market UI to support graph points and tab navigation
- Changed Silver deposit amount selection to digit-based input
- Minimap and Mount buttons can now be clicked with a mouse
- Delete Order action in the Marketplace UI now requires a short hold
- Reintroduced target cycling on right shoulder button for the Legacy control scheme
- Further improvements to manual target selection and auto-targeting responsiveness
-  Implemented HUD Tracker navigation
- [DESKTOP/MOBILE] The chat input field is now automatically reselected when switching tabs

### Armory Improvements

- Can now be accessed directly from the Loadouts UI
- Improved recommendation accuracy through expanded build tracking and evaluation metrics
  - Now tracks equipment swaps during an activity
  - Reduced bleed between different open world activities, making recommendations more precise
  - Improved data accuracy across several activities
  - These improvements will take effect gradually as new data is tracked

- Adjusted filter sorting to match existing Marketplace categories

### Changes

- Polished several visual overhaul elements across multiple biomes, including adjustments to lighting, terrain textures, and water materials
- The number and frequency of Weapon Cache spawns during Bandit Assaults has been reduced
- Added new _/forfeit_, _/ff _and _/surrender_ chat commands to surrender in Custom Matches
- Added stronger selection highlights around health bars when using mouse and keyboard
  - This option can be disabled under the Nametags section in Interface settings

-  Reintroduced ‘Auto-walk in range’ behavior for ground-targeted and skillshot spells
  - This option can be disabled under the Auto-Targeting section in Controls settings

- [DESKTOP/MOBILE] Added ‘Show targeting line and range’ option under Controls settings for Mouse and Touch input

### Combat Balance Changes

**Arcane Staffs**

> _Magic Shock has had its stand time removed to make it smoother to play._

- Magic Shock (all Arcane Staffs)
  - Stand time: 0.2s → 0s

> _Time Freeze’s stun duration against mobs has been reduced to match its PvP stun duration and limit its ability to trivialize PvE encounters._

- Time Freeze (Great Arcane Staff)
  - Stun duration vs mobs: 3.5s → 2.5s

**Axes**

> _Spin to win. Me spin, me kill. Kill good._

- Whirlwind (Greataxe)
  - Damage per tick for hitting the same target: 5 → 6.5 (Max damage: 411 → 433.5)

> _Razor Cut has been adjusted to hit targets more consistently at the cast position, and now has improved targeting on mobile and controller._

- Razor Cut (Bear Paws)
  - Changed spell indicator to a circle showing the landing position
  - Slightly expanded hit area under the caster

**Fire Staffs**

> _Fire Wave has had its cooldown reduced to help it act as a more reliable interrupt._

- Fire Wave (all Fire Staffs)
  - Cooldown: 15s → 12s

**Frost Staffs**

> _Frostbite has had its stand time removed to help it feel more fluid to play._

- Frostbite (all Frost Staffs)
  - Stand time: 0.15s → 0s

**Holy Staffs**

> _Spamming Reawaken on downed allies has become the go-to method for brute-forcing many difficult PvE fights. It’s time to get good and step out of the fire: only one resurrection per fight._

- Reawaken (all Holy Staffs)
  - Allies who accept the resurrection now receive Awakening Sickness for 180s (cannot be Reawakened again during that time)

**Maces**

> _Incubus Mace has remained the premier PvE tank weapon thanks to its multiple powerful debuffs. At the same time, it has also been too effective in PvP situations like duo ganking and ZvZs, so its Max Health reduction has been reduced slightly to make it less of an “all-in-one” debuff._

- Shrinking Curse (Incubus Mace)
  - Max health reduction: 25% → 20%

**Quarterstaffs**

> _Soulscythe hasn’t been keeping up in modern Albion large-scale PvP, so its projectile speed has been increased to make its group knockup more reliable._

- Tornado (Soulscythe)
  - Now moves ~10% faster

**Shapeshifter Staffs**

> _Lightcaller has been dominating in Corrupted Dungeons and the Mists. Its extreme auto-attack range, combined with its Q detonation, has offered too little room for meaningful counterplay. Therefore its auto-attack range has been reduced._

- Dawnbird Transformation (Lightcaller)
  - Attack range: 15m → 13m

> _The previous nerf to Tear Open’s Blood Pool charge requirement resulted in a more awkward play pattern, so this has been reverted in favor of a straightforward healing reduction to keep its total self-healing in check._

- Tear Open (Bloodmoon Staff)
  - Blood Pool charge requirement: 2 → 1
  - Blood Pool heal: 61 → 30

> _This change was introduced with Radiant Wilds Patch 1, but was accidentally omitted from the patchnotes. Neurotoxin has had its damage application adjusted to behave more consistently and better support a bruiser playstyle._

- Neurotoxin (Stillgaze Staff)
  - Max stacks: 4 → 1
  - Damage decrease per stack: 4% → 12%
  - Tick interval: 0.8s → 1s
  - Damage per tick: 6 → 25

**Swords**

> _Carving Sword has received many nerfs due to its strength in 1v1 and 2v2 content, and has since fallen out of favor in group-scale PvP. To help it regain relevance there, AoE escalation is now applied to its resistance reduction._

- Fearless Strike (Carving Sword)
  - Resistance reduction now scales with AoE escalation

> _Soulless Stream’s area of effect duration has been cleaned up and reduced slightly to better match its visuals, and to make it less likely for opponents to step into invisible lingering hitboxes._

- Soulless Stream (Galatine Pair)
  - Area lifetime: 0.8s → 0.7s

**Armors**

> _Speed Caster has had its cooldown reduced to help it line up better with classic combos like Brimstone, hopefully opening up more caster options in group PvP._

- Speed Caster (Scholar Robe)
  - Cooldown: 35s → 30s

> _Knight Armor became an all-in-one chest armor, providing defensive peel for groups, aggressive crowd control, and purging, while also granting a personal defensive bonus. That personal defensive component has been removed to create clearer counterplay against tanks dismounting behind enemy groups to push them back with Wind Wall. In addition, its channel duration will no longer be reduced by incoming damage._

- Wind Wall (Knight Armor)
  - Removed defense and CC resistance for hitting enemies
  - Disruption factor: 1 → 0

**Capes**

> _Berserk can no longer be purged: may your rage be swift, unmitigated, and destructive._

- Berserk (Keeper Cape)
  - Health percentage application: 70% → 80%
  - Damage buff: 50% → 40%
  - Cannot be purged

### Fixes

**Spell Fixes**
- Sinister Swipes (Prowling Staff): Fixed issue where its execute would apply without the required stacks
- Soulless Stream (Galatine Pair): Fixed issue where Heroic Charges could briefly persist after casting

**UI Fixes**
- Fixed issue where opening and closing the Destiny Board could cause performance drops or temporary freezing
- Fixed issue where clicking UI elements beneath the Region Map could cause unintended character movement
- Fixed issue where changing graphics settings after a reset could modify all other graphics options
- Fixed issue where the Food Supply UI would shift down the screen after supplying food to multiple stations
- Fixed issue where the Arena Ready popup would remain visible after logging out
- Fixed issue where Player Building tooltips would show incorrect furniture and resident capacity information
- Fixed issue where the HUD Tracker would not be visible when the Destiny Board was open
- Fixed issue where the spell selection view in the Item Details UI would not correctly reflect combat state after reconnecting
- Fixed issue where Custom Presets would not save correctly when switching between presets
- Fixed issue where reconnecting during the countdown between rounds in the 1v1 Arena would cause the points tracker to disappear
- Fixed issue where disabling the ‘Auto-hide chat’ setting while chat was hidden would open the input box and close the chat settings menu
- Fixed issue where basic attacks and reflected damage could be displayed as a combined entry in Death Recap UI
- Fixed issue where cancelling a trade invite with Esc could cause the Trade UI to behave incorrectly
- Fixed issue where keyboard input could stop working correctly after pressing Enter while the chat window was hidden
- [STEAM DECK] Fixed issue where the chat input window could not be closed after sending a message

**Controller Fixes**
- Fixed issue where the ’Always Self’ Beneficial Target Priority setting did not work as intended
- Fixed issue where tooltips could overlap editable slider values
- Fixed issue where Fortress Chests would not display proximity tooltips
- Fixed issue where the self-cast button hint would disappear after casting a spell
- Fixed issue where ‘Craft’ and ‘Max Quantity’ shared the same key binding in the Crafting UI
- Fixed issue where Item Details could not be opened from the Death Recap UI
- Fixed issue where self-casting could interrupt target lock
- Fixed issue where the ‘Inspect’ option in the Radial Menu would not respond when selected
- Fixed issue where the Estimated Market Value of equipment was not displayed in the Inventory UI
- Fixed issue where Battlevault Tab Management UIs would appear empty
- Fixed issue where it was not possible to join or cancel an Arena match after being invited
-  Fixed issue where Travel Mode could not be toggled via the Radial Menu
- [DESKTOP / MOBILE] Fixed issue where button hints in chat could display incorrectly or remain visible when unfocused
- [DESKTOP / MOBILE] Fixed issue where chat navigation could become stuck when the selected channel had no messages

**Xbox Fixes**
- Fixed issue where game audio would stop when the game lost focus
- Fixed issue where using ‘Reset All’ in the Settings menu could temporarily reduce performance
- Fixed issue where the Virtual Keyboard and other text input fields could stop opening after being closed
- Fixed issue where certain dialog popups could be accidentally confirmed during gameplay and UI interactions

**Other Fixes**
- Fixed issue where Raid Banners dropped at the entrance of a Smuggler’s Den could no longer be picked up
- Fixed issue where interacting with Treasure Coffers while mounted would not automatically dismount the character
- Fixed issue where some mounts and mount skins would not display Guild Emblems correctly
- Fixed issue where spell indicators could remain visible after reconnecting while aiming a spell
-  Fixed issue where ‘Cast On Press’ would always be enabled for the Virtual Controller scheme
-  Fixed issue where dragging the attack button could target allied players
-  Fixed issue where the ‘None’ option for Auto-Target Lock would behave like ‘Sticky’ instead
-  Fixed issue where targeted spells could become locked and impossible to retarget or cancel after another spell’s recast window ended
- Various additional performance, graphical, animation, terrain, audio, UI, and localization fixes
