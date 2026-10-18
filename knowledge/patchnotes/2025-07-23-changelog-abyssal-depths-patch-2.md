<!-- gid: 1806064758572808 -->
# Changelog: Abyssal Depths Patch 2

_date: 2025-07-23 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1806064758572808_

> _This patch adds further improvements and polish to the Abyssal Depths update, including a Marketplace to the Antiquarian's Den, adjustments to the Depths, and several bugfixes._

### Changes

**Antiquarian’s Den Changes**
- Antiquarian’s Dens now contain a Marketplace vendor for the corresponding city’s Marketplace
- The Antiquarian now shows its pet’s name, as chosen by the community

**The Depths Changes**
- Opening a small chest after completing a room now grants a Demonic Ferocity stack to all party members in range
- In the final level of the Depths, an additional key will appear after ten minutes, and every 3 minutes after that, if the Treasure Vault has not yet been opened
- Minimap icons for Coffers and Chests have been made larger
- Treasure Coffers now only appear on the minimap when in proximity
- There are now PvE and PvP Fame categories for the Depths category in the Player, Guild, and Alliance Rankings
- Timer in the entrance UI now displays seconds when less than 1 minute remains
 **Albion Journal Changes**
- The following missions have had their rewards adjusted:
  - Get a Weapon Generalist Node to level 30
  - Get a Weapon Specialist Node to level 30
  - Unlock Tier 5 Reaver
  - Unlock Tier 7 Reaver
  - Reach Level 30 in any Weapon Generalist Node
  - Reach Level 30 in any Weapon Specialist Node
  - Apply a Chest, Shoe and Helmet skin
  - Unlock x Wardrobe or Mount Skins

**UI Changes**
- Updated icons for Generalist and Specialist nodes in the Quick Learn node management UI
- To minimize notification spam, players will now receive fewer notifications when multiple Destiny Board nodes are leveled up simultaneously
- 10v10 Hellgate stats have been archived in the player stats UI
- Kill Details UI now displays a full timestamp for each kill
- Appearance UI filters now persist after switching tabs or closing the UI

**Other Changes**
- Mobs and mob groups in the open world and the Depths now have shorter leash ranges when not attacked
  - This change has been made to make open-world travel more comfortable and to help players in the Depths stay focused during ongoing PvP encounters

- Book Chests and Hidden Treasures have been removed from Corrupted Dungeons
  - Treasure spawns that were previously either Book Chests or Treasure Chests will now always spawn Treasure Chests

- Fame shrines have been removed from Hellgates
- All Captured Smugglers’ guards are now Tier 6
- Duels are no longer possible within Hellgates
- Gathering tools can no longer be swapped while in combat
-  Implemented basic HUD Tracker support

### Combat Balance Changes

**Axes**

> _Blood Bandit has been consistently punching above its weight, so its projectile speed has been reduced to give enemies at maximum range a more realistic chance to dodge it. However, its hitbox accuracy at extremely close and very long ranges has been improved._

- Blood Bandit (Battleaxe)
  - Reduced projectile speed (~9%) and increased hit detection reliability

**Cursed Staffs**

> _Great Cursed Staff has been mostly pushed out by the Rotcaller Staff in small group content. To help it succeed in its role of maintaining DoT pressure, Area of Decay’s cooldown has been reduced._

- Area of Decay (Great Cursed Staff)
  - Cooldown: 25s → 20s

**Fire Staffs**

> _Flamewalker Staff has been highly effective in solo content. Its survivability has been reduced with a longer base cooldown, while its cooldown refund for hitting enemy players has been increased to reward aggressive play._

- Spontaneous Combustion (Flamewalker Staff)
  - Cooldown: 30s → 40s
  - Cooldown refund: 25% → 40%

**Frost Staffs**

> _Frostbite and Ice Shard have been often superseded by Frozen Surge in most content. Rather than nerfing Frozen Surge directly, the alternatives have been adjusted to make them more attractive._

- Frostbite (all Frost Staffs)
  - Removed: 4% bonus damage
  - Added new effect: Frostbite
    - Stack duration: 2.5s
    - 3-stack effect: Stuns for 0.8s

- Ice Shard (all Frost Staffs)
  - Cast range: 13m → 14m

**Holy Staffs**

> _Lifetouch Staff has been too strong in Corrupted Dungeons, but underwhelming in group play, so it’s getting a higher cooldown, farther range, less burst healing, and a new buff for allies._

- Holy Touch (Lifetouch Staff)
  - Healing per tick: 76.8 → 55
  - Tick count: 5 → 7
  - Max channel duration: 2s → 3s
  - Range: 9m → 11m
  - Cooldown: 15s → 20s
  - Added: Increases all damage the targeted ally deals by 15%

> _Following recent buffs, Smite has become too strong in both PvE and PvP. Its damage has been reduced, while the improved cooldown is being retained._

- Smite (all Holy Staffs)
  - Instant damage: 151 → 136
  - Mark damage: 43 → 38

**Maces**

> _Dreadstorm Monarch has been given some quality-of-life improvements to help it compete, including a shorter cooldown between casts and increased slow strength._

- Eye of the Storm (Dreadstorm Monarch)
  - Cooldown between uses: 2s → 1.5s
  - Slow strength: 20% → 25%

**Quarterstaffs**

> _Black Monk Stave has seen increasing use in ZvZs, while being one of the most demanding weapons in terms of visual and combat clarity. Its tick interval and maximum area duration have been reduced, while its damage reduction strength per stack has been increased to compensate._

- Fatal Blade (Black Monk Stave)
  - Area duration: 5s → 3s
  - Damage per tick: 25 → 80
  - Damage reduction per stack (vs players): 30% → 40%
  - Maximum stack count: 4 → 3
  - Damage and debuff interval: 0.75s → 1.25s

> _Hurricane’s damage to players has been increased to match its damage to mobs, and it has been given bonus resistances to help Iron-clad players escape safely after sowing chaos among their enemies._

- Hurricane (Iron-clad Staff)
  - Damage per tick: 32 → 55
  - Added: 0.15 armor and magic resistance for 5s

**Shapeshifter Staffs**

> _Crystalburst has been given a significant damage boost to ensure the Crystal Cobra transformation remains deadly._

- Crystalburst (Stillgaze Staff)
  - Tick count: 3 → 4
  - Tick interval: 1s → 0.8s
  - Damage per tick: 18 → 27 (Total damage: 54 → 108)

> _Hellspawn Imp’s passive has been offering too much safety in 2v2 and 3v3. To get a second life, it now requires transforming with sufficient stacks and giving up Hellfire Barrage._

- Return from Hell (Hellspawn Staff)
  - Respawn always → Respawn requires at least 3 shift charges
  - Heal based on shift charges → 18% of max health

**Spears**

> _Corrupting Steel has had its recent area damage-over-time nerf reverted to preserve its viability as a DPS contributor._

- Corrupting Steel (Spirithunter)
  - Returned damage over time
  - Damage per tick: 32
  - Tick interval: 0.5s (8 ticks total)

**War Gloves**

> _Forcepulse Bracers now use the ‘speed’ auto-attack pattern, and have received cooldown reductions, including a new refund based on the time elapsed between the initial cast and recast._

- Unstoppable Rush (Forcepulse Bracers)
  - Auto-attack pattern changed to ‘speed’ variant (from three-hit combo to two-hit combo)
  - Single cast cooldown: 20s → 15s
  - Recast cooldown: Refunds time elapsed before recasting

**Helmets**

> _Following the recent quality-of-life change that prevents Hellion Hood from silencing allies, players have been stacking Hellion Hoods to keep mobs permanently silenced, trivializing some PvE encounters._

- Smoke Bomb (Hellion Hood)
  - Mobs can no longer be consecutively silenced

**Armors**

> _Specter Jacket’s aura radius has been increased to better match its visuals. _

- Self Ignition (Specter Jacket)
  - Aura radius: 6m → 7m

### Fixes

**Albion Journal Fixes**
- Fixed issue where the mission ‘Apply a Chest, Shoe and Helmet Skin’ stated that all needed to be applied simultaneously
- Fixed issue where ‘Participate in x Raids’ missions would not track progress correctly
- Fixed issue where the mission ‘Hunt a Rare Creature’ would not count higher-tier Tracking targets
- Fixed issue where the mission ‘Catch 5 fish’ could progress from unrelated items
- Fixed issue where the missions ‘Defeat any Crystal Cobra’ and ‘Defeat any Crystal Beetle’ displayed the wrong icons
- Progress bars for combat specialization leveling missions now display the number of achieved nodes

**Mob Fixes**
- In the Living Legacy event, the mob Eastern Titan of the Nineteenth Age’s Separator spell now knocks players into the air
- Fixed issue where Royal Guard Towers outside Royal Cities would not attack players from enemy factions
- Fixed issue where Sir Bedivere would not perform auto-attacks when affected by Smokebomb
- Fixed issue where Shadow Panther would not spawn additional panthers within its Silencing Mist

**UI Fixes**
- Fixed issue where available Learning Points in the Destiny Board were rounded in a misleading way
- Fixed issue where Caerleon’s Antiquarian’s Den entrance displayed the wrong minimap icon
- Fixed issue where default item sorting would not follow Marketplace categorization
- Fixed issue where ‘Home’ button would erroneously display as a respawn option
- Fixed issue where clicking a chat link would move the character if ‘Lock Window’ was enabled
- Fixed issue where Death Recap would display a spell’s full CC duration, even if death occurred before this duration was elapsed
- Fixed various HUD Tracker display issues
- Fixed issue where the toggle to hide/show Vanity Sources was missing its icon
- Quick Thinker (Leather Jackets, Hoods, and Shoes): Fixed issue where an incorrect Cooldown Rate was displayed in the item details
-  Fixed issue where hovering over a node on the Destiny Board would sometimes cause it to open and close repeatedly

**Other Fixes**
- Fixed issue where the carry weight bonus from shoe passives would be reduced by Item Power caps
- Fixed issue where players could enter the next Hellgate without defeating the enemy team, and would not receive a reward chest after doing so
- Fixed issue where the rarity VFX of Treasure Vaults in the Depths would not display once opened
-  Fixed issue where Group Dungeon entrances in the Mists could sometimes not be used
- Various fixes and improvements to tutorial missions
- Various additional graphical, animation, terrain, audio, UI, and localization fixes
