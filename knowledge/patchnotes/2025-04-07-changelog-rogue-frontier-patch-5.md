<!-- gid: 1795917897449046 -->
# Changelog: Rogue Frontier Patch 5

_date: 2025-04-07 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1795917897449046_

> _This patch focuses on Guild Season content, introducing the next batch of Crystal Weapons and several balance changes to shake up the ZvZ meta ahead of the new season._

### New Crystal Weapons

This patch introduces three brand-new Crystal Weapons, craftable from Artifacts awarded in Conqueror’s Chests at the end of Season 26. Each Crystal Weapon has its own unique, powerful spell:
- **Flamewalker Staff** (Fire Staff): **Spontaneous Combustion **transforms you into a raging fireball, flying towards your enemies and dealing damage to those in your path
- **Forgebark Staff **(Nature Staff): **Dual Nature** allows you to switch between fortifying your allies and ensnaring your enemies
- **Arclight Blasters** (Crossbow): **Flickershots **unleashes a barrage of energy bolts as you spin through the air, dealing damage and increasing your resistances

### Season 27 Changes

The following categories in the Conqueror's Challenge have had their Might requirements per level reduced, while their Season Point output for each level has also been reduced to maintain overall Season Point payouts:

**Treasures**
- Might needed per Level: 13,000 → 10,400
  - Season Points per Level: 20 → 16

**Crystal Creatures**
- Might needed per Level: 6,000 → 4,000
  - Season Points per Level: 30 → 20

**Smugglers**
- Might needed per Level: 34,000 → 27,200
  - Season Points per Level: 20 → 16

Gathering has also had its Might requirement per level reduced, to make it easier for smaller guilds to earn Season Points from this activity:

**Gathering**
- Might needed per Level: 3,500 → 2,700

### Other Changes

- Smuggler Crates are now visible on the minimap to everyone in the same region
- Players can now send only one message every two seconds in the following chat channels:
  - Say
  - Whisper
  - Help
  - Faction
  - Faction Local
  - All language channels

- The following automated chat message has been changed:
  - “Player x has committed suicide.” → “Player x has died.”

- Text entered in the Marketplace UI search box now carries over when switching between the Buy and Buy Order tabs
- The Kills and Deaths tabs in the Player Stats UI now remember the previous dropdown selection on opening

### Combat Balance Changes

**Axes**

> _Despite multiple nerfs, Infernal Scythe has continued to dominate as the ZvZ damage dealer of choice, crowding out alternatives. The damage of the second swing has been increased but converted into a DoT to disincentivize zergs from running five per party._

- Bloody Reap (Infernal Scythe)
  - 2nd swing now deals damage in 3 ticks over 2 seconds (doesn’t stack)
  - Damage per tick below 40%: 85 (total damage 220 → 255)
  - Damage per tick above 40%: 47 (total damage 120 → 141)

> _Raging Blades has been a powerful component of axes’ domination in ZvZs, so its area has been reduced to limit its effectiveness in the largest fights._

- Raging Blades (all Axes)
  - Radius: 6m → 5m

**Crossbows**

> _Energy Shaper has remained a niche pick in ZvZs. Its total channel duration has been reduced, while the damage per tick has been increased to make accurate beams deadlier in a shorter time._

- Divine Engine (Energy Shaper)
  - Channel duration: 3.3s → 2.6s (Total ticks 11 → 9)
  - Damage per tick (vs players): 96 → 117
  - Damage per tick (vs mobs): 57 → 70
  - Initial tick: 0.2s → 0.1s

**Daggers**

> _Because Demonfang has been a menace in ZvZ, it has received multiple nerfs to damage and resilience penetration over previous patches. Some of that damage has now been restored._

- Blood Ritual (Demonfang)
  - Damage per cast: 106 → 112

> _Due to the significant setup required for Ring of Death, its penalty for misexecution has been softened, giving Twin Slayer players more opportunities to land the one-shot._

- Ring of Death (Twin Slayers)
  - 1st cast cooldown: 25s → 15s
  - Energy cost: 12 → 10

**Fire Staffs**

> _Raging Flare’s damage has been condensed and increased to provide Fire users with a quicker, more impactful long-range damage option._

- Raging Flare (all Fire Staffs)
  - Cast time: 0.6s → 0.4s
  - Impact damage: 186 → 205
  - DoT ticks: 6 → 3 (1s interval unchanged)
  - DoT damage per tick: 7.2 → 21.4
  - Total DoT damage: 43.2 → 64.2

**Frost Staffs**

> _Frost’s spell stack requirement has been reduced, as it felt too high on builds using less spammable abilities like Frozen Surge and Frost Nova. This will help Frost players keep enemies locked down more consistently._

- Frost (all Frost Staffs)
  - Stack requirement: 5 → 4

> _Icicle Staff has remained a niche defensive tank option in ZvZs, but its dramatic hit delay has made it feel outdated in modern Albion, so this has been reduced to improve responsiveness._

- Frozen Hell (Icicle Staff)
  - Hit delay: 0.7s → 0.3s

> _Permafrost has been a strong ZvZ option, but its crowd control when stacked as an 8-man bomb squad has left too little room for reaction. With such a consistently valuable long-range stun, its damage has been reduced to compensate._

- Ice Crystal (Permafrost Prism)
  - Damage: 184.69 → 173
  - Stun duration now ignores diminishing returns (but does not apply it)
  - Stun duration no longer refreshes by consecutive Ice Crystal stuns

**Hammers**

> _Grovekeeper has fallen out of favor as both an engage and peel tank option. The bonus resistances for hitting targets have not felt impactful to Grovekeeper players, so they have been removed in favor of an instant knock-up, making engages more deadly, even against enemy cleanses._

- Ground Pound (Grovekeeper)
  - Removed: Increased resistances per targets hit
  - Added: Knocks up all targets for a duration based on the amount of enemies hit
    - 1, 2, or 3 enemies hit: 0.4s knock up
    - 4, 5 or 6 enemies hit: 0.8s knock up
    - 7 or more enemies hit: 1.2s knock up

**Holy Staffs**

> _To help Exalted Staff feel more responsive and succeed in its intended role of clearing hostile ground areas, its long cast time has been reduced._

- Sanctify (Exalted Staff)
  - Cast time: 1s → 0.6s

**Maces**

> _Dreadstorm Monarch has struggled to find a strong foothold in the meta. As a result, the value of Eye of the Storm’s uncleansable resistance reduction has been increased, to help it compete with alternative pierce options._

- Eye of the Storm (Dreadstorm Monarch)
  - Resistance reduction: 0.15 → 0.18

> _Vendetta’s pull hit delay has felt overly generous to opponents, so it has been shortened to help Camlann compete with other clump tank options._

- Vendetta (Camlann Mace)
  - Hit delay: 1.5s → 1.2s

**Nature Staffs**

> _Protection of Nature has been a strong defensive tool with a very high uptime. Its high damage reduction, paired with the bonus healing received, has resulted in targets having too much survivability too often in smaller-scale group fights, so its resistance has been reduced somewhat._

- Protection of Nature (all Nature Staffs)
  - Resistance: 0.24 → 0.2

**Quarterstaffs**

> _To help Fatal Blades counter fast ZvZ engages, its damage reduction now stacks higher and faster, but with reduced duration._

- Fatal Blade (Black Monk Stave)
  - Damage reduction (vs. players): 22% → 30%
  - Duration: 6s → 5s
  - Initial tick: 0.25s → 0.1s
  - Projectile speed: 30 m/s → 35 m/s

> _Soul Shaker has fallen out of favor as a viable defensive tank option in ZvZs. To help players better protect their team’s flanks, its root duration has been increased to match its area duration._

- Soul Shaker (Grailseeker)
  - Area duration: 4s → 3.5s
  - Root duration: 3s → 3.5s

> _Soulscythe has remained a niche shotcaller option in ZvZs, so its standtime has been reduced to make it feel more responsive and return control to its users more quickly._

- Tornado (Soulscythe)
  - Standtime: 0.7s → 0.4s

**Spears**

> _While Cripple has been a good tool to counter swords, adjustments have been made to help it feel powerful in more situations, more often._

- Cripple (all Spears)
  - Damage type: magical → physical
  - Added: Auto-attack speed is reduced by 25% for 4s
  - Cooldown: 20s → 18s
  - Move speed buff duration: 5s → 4s
  - No longer gives bonus damage when purging a sprint

**Swords**

> _The previous buff to Blade Cyclone has been reverted, as it became the default option and outperformed all other options, particularly for Carving and Infinity Blade players._

- Blade Cyclone (all Swords)
  - 1 charge damage: 70 → 60

**War Gloves**

> _To help Ursine Maulers find more success, the damage reduction from a previous nerf, originally paired with a significant resilience penetration decrease, has been reverted._

- Hundred Striking Fists (Ursine Maulers)
  - Damage per tick: 32.4 → 36 (vs players)
  - Delayed damage: 27 → 30 (per stack)

> _Some of Infernal Boulder’s instant damage has been moved into its DoT component, to both reward skilled players for hitting all three boulders and to limit its effectiveness when stacked in ZvZs._

- Infernal Boulder (Hellfire Hands)
  - 1st boulder damage: 199.5 → 177
  - 2nd boulder damage: 133 → 126
  - 3rd boulder damage: 66.5 → 76
  - DoT tick damage: 14 → 18

**Armors**

> _To make Protection of the Fiends more risky, its negative resistance penalty has been increased, making it more important to combo with allies or cancel the channel early._

- Protection of the Fiends (Demon Armor)
  - Caster resistance reduction: 0.34 → 0.37

> _Taunt has been simplified to apply the same effects regardless of the selected target, while increasing its value as a short-cooldown damage option for Plate Armor users._

- Taunt (all Plate Armors)
  - No longer distinguishes between target types
  - Bonus Damage vs All: 10% → 20%
  - Defense vs Players: -10% → -20%

**Capes**

> _The Fort Sterling Cape has had its cooldown significantly reduced at higher tiers to justify its price increase and enable players to rely on it as a consistent cleanse option._

- Untouchable (Fort Sterling Cape)
  - Base cooldown: 139 → 168
  - Cooldown reduction per 100 IP: 3s → 8s (118s → 112s at 700 IP, 91s → 40s at 1600 IP)

**Potions**

> _Invisibility Potion’s damage reduction has not been significant enough or lasted long enough to give opponents a fair chance to react to fully undetectable engages. Damage reduction has now been changed to reduce all damage dealt by players, making it harder to bypass the penalty with stacked damage buffs. The effect also lingers for 2 seconds after exiting stealth, rather than starting from the moment of use, giving players a chance to fight back if revealed early._

- Invisibility Potion
  - Ability damage reduction → Damage vs All reduction (-50% value is unchanged)
  - Duration: Fixed time on cast → While Invisible, and remaining for 2s once revealed

**Other**
- Judgment (Lightcaller) visuals have been updated to be more readable in large-scale fights

### Fixes

**Spell Fixes**
- Spinning Blades (Dual Swords): Fixed issue where immunity to Crowd Control persisted after impact
- Holy Beam (Holy Staffs): Fixed issue where stacks persisted after casting was interrupted
- Razor Cut (Bear Paws): Fixed issue where the same enemy could be hit multiple times
- Time Freeze (Great Arcane Staffs): Fixed issue where frozen enemies could still receive healing from lifesteal effects

**UI Fixes**
- Fixed issue where the Arena queue timer would not reappear if a player canceled the match invitation
- Fixed issue where combat logs in the Death Recap would be overwritten by new actions performed on the player when switching tabs in the UI
- Fixed issue where the ‘Take All’ button on the Marketplace would reset filters without resetting the filter text
  - The text is now reset along with the filters

-  Fixed issue where main dynamic action button on the virtual controller could appear to remain in motion after use
-  Fixed issue where ‘Select Next Party Member’ keybinding option was missing from the Settings menu

**Other Fixes**
- Fixed Faction Warfare “connection bug”; it is now always possible to capture Outposts in a region if at least one adjacent frontline or backline region is owned by your Faction
- Fixed issue where it was possible for players to buy their own items at the Marketplace
- Fixed issue where Rock Giant’s Aspect would not pursue players or use melee attacks
