<!-- gid: 1846018067940491 -->
# Changelog: Dragonfire Patch 3

_date: 2026-10-12 · source: https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1846018067940491_

> _This patch introduces more frequent small portals to the Ancient Lands in Yellow Zones, adjustments to the Maeve fight, changes to open world Dragons, and new mobile targeting options._

### Ancient Lands Changes

Since the launch of Dragonfire, we’ve been closely monitoring both your feedback and the data around the new features, especially the Ancient Lands. One thing we’ve heard very clearly is that many of you would like the Ancient Lands to be available more frequently, so you can jump into the content more regularly.

We’ve taken that feedback into consideration, and with this patch we are significantly increasing the availability of non-lethal Small Portals to the Ancient Lands. Small Portals in Yellow Zones should now be frequent enough that players can chain this content, with portals almost constantly visible on the World Map. We will monitor the effects of this change to see if enough players remain engaged with the activity to sustain this high portal frequency.

With this increased availability, it is necessary to reduce the Fame and loot available in Ancient Lands accessed through Small Portals in Yellow Zones by 30% to avoid injecting too much Silver and too many items into the economy, and to allow other activities to remain competitive.

Note that this change only affects small Ancient Lands portals in Yellow Zones. Small Portals in Red and Black Zones remain unchanged and will remain opportunity targets offering access to the same high Fame and loot. This allows us to give players the choice between accessible and frequent portals in Yellow Zones, and high-risk/high-reward portals in Red and Black Zones.

The Fame and loot available through Medium and Large Portals will also remain at their current levels. Large Portals will appear more frequently but will remain occasional opportunity targets. Since more players are needed for these instances, keeping their availability more limited helps prevent them from becoming too empty while allowing us to keep Fame and loot high.

**Ancient Lands portal changes**
- Small Portals in Yellow Zones
  - Average spawn time: 45 minutes → 15.5 minutes
  - Chance of appearing in a region: 25% → 33%
  - Lock time: 15 minutes → 5 minutes
  - Time available to enter after unlocking: 8 minutes → 10 minutes
  - Fame and loot reduced by 30%

- Small Portals in Red and Black Zones
  - Chance of appearing in a region: 25% → 33%
  - Time available to enter after unlocking: 8 minutes → 10 minutes

- Canceling a completed portal channel now silences the player for a short time
  - This is intended to counter strategies in which groups cancel their finished portal channel and attack other groups

- Increased the chance of Large Portals appearing by 50%
  - They are now also more likely to appear during prime times

**Other Ancient Lands changes**
- Roughly 10% of the value from each of the four regular Drake chests has been moved to the central Fire Drake chest
- Additionally, the value of the central Fire Drake chest has been further increased by providing a significantly higher drop chance of the new artifact items
- The Small and Medium islands now require their Drake to be killed to complete the quest
- Reduced Ancient Lands mob health and damage
  - Small Portals: -10%
  - Medium Portals: -10%
  - Large Portals: -20%

- Reduced Stonebreaker Berserkers’ Pulse Shock damage
  - Damage: 400 → 300
  - Damage is now correctly applied to all players within the Pulse Shock range behind the player hit by the attack

- Reduced Renowned Huntress’ Cross Fissure damage
  - Damage: 1350 → 1000

### Dragon Sanctuary Changes

Our changes to Maeve in Patch 2 succeeded in making the fight more consistent, which is good. However, the fight is still too punishing once Meave drops below 40% health, especially at higher tiers (8.1+). With these changes, we want to address this specifically by reducing some of the chaos caused by the boulders and providing more breathing room toward the end of the fight.

**Maeve combat changes**
- Number of additional boulders summoned below 40% health:
  - 3 → 2 (Max. boulders 6 → 5)

- Reduced Primal Dragon Flame’s damage
  - Normal damage: 1250 → 1150 (true damage unchanged)

- Increased time between Storm Spire appearances
  -  45s → 55s

- Fixed issue where Boulder Charge could hit twice on rare occasions

### Open-World Dragon Attack Changes

To reduce the impact of strategies where outsiders try to grief a group fighting a Dragon, the reset behavior of open-world Dragons has been adjusted.
- Open-world Dragons no longer fully recover their health when reset. Instead, they recover to the last 20% health threshold reached
  - For example, if a Dragon is reset at 72% health, it will resume the fight at 80% health when engaged again

- Might rewards from open-world Dragons have been increased by 150%

### Mobile Combat and Targeting

- Targeting modes have been added on mobile, allowing you to control which types of targets can be selected when switching targets or dragging the attack button
  - Targeting modes can be enabled or disabled in Settings → Controls → Auto-Targeting
    - They are disabled by default

  - Once enabled, the modes can be toggled in the HUD
    - Available modes are All, Enemies, Party, Allies, and Automatic
    - ‘All’ does not filter possible targets
    - ‘Enemies’ selects hostile players and mobs
    - ‘Party’ selects only your party members
    - ‘Allies’ selects friendly players, whether in your party or not
    - ‘Automatic’ chooses one of the above modes based on your current abilities and whether you’re in a party

- A new ‘Double Tap to Self-Cast’ option has been added
  - This can be found in Settings → Controls → General on mobile
  - It is enabled by default
  - It can be disabled to prevent accidental self-casts when repeatedly tapping and to remove the delay used to detect a double tap

### Other Changes

- Improved T4 Boar dash behavior and indication

### Combat Balance Changes

**Crossbows**

> _Explosive Bolt has been dealing too much effective damage in small-scale PvP and PvE, so its damage has been reduced._

- Explosive Bolt (all Crossbows)
  - Damage: 130 → 119

**Cursed Staffs**

> _Plaguebringer has been too dominant in 5v5 content, so its cooldown has been increased, giving enemy healers a larger window to act before the next team-wide heal negation._

-  Plaguebringer (Rotcaller Staff)
  - Cooldown: 30s → 35s

**Daggers**

> _Bloodthirsty Blade has been made slightly less thirsty for the caster’s own blood, reducing its self-damage and helping the caster stay healthier throughout many fights, even when they can’t maintain 100% DPS uptime._

- Bloodthirsty Blade (Dagger)
  - Self-damage: 4% → 2.5% (max.: 24% → 15%)

> _Ring of Death’s initial ring of floating daggers has had its area significantly increased and its damage raised, improving the value of the initial cast._

- Ring of Death (Twin Slayers)
  - Floating ring damage: 27 → 36 (total damage: 324 → 432)
  - Increased floating ring size by 1.5m (roughly doubling its area)

**Fire Staffs**

> _Flame Pillar’s stand time has been reduced, making it smoother to play._

- Flame Pillar (Great Fire Staff)
  - Stand time: 0.4s → 0.25s

> _Spontaneous Combustion’s cooldown has been increased, giving opponents more opportunities to fight back, chase, or escape._

- Spontaneous Combustion (Flamewalker Staff)
  - Cooldown: 40s → 45s

**Holy Staffs**

> _Smite’s damage against players has been reduced, giving opponents more room to fight through Holy Staff’s sustain._

- Smite (all Holy Staffs)
  - Damage vs. players: 136 → 115 (damage vs. mobs unchanged)

**Quarterstaffs**

> _Cartwheel’s excellent mobility has been given a greater tradeoff, with its energy cost increased. Players who want to spam it will therefore be more pressured to include a dedicated energy solution in their build._

- Cartwheel (all Quarterstaffs)
  - Energy cost: 5 → 7

> _Phantom Twinblade has seen increased play following its recent buffs. To sharpen its identity as a damage-focused Quarterstaff option, its slow has been removed._

- Phantom Twin (Phantom Twinblade)
  - No longer slows

**Shapeshifter Staffs**

> _Crystalburst’s damage and healing reduction have been increased, giving the Crystal Cobra transformation more offensive pressure._

- Crystalburst (Stillgaze Staff)
  - Healing reduction: 20% → 35%
  - Instant damage: 66 → 75

> _Tether Shift has lost some self-shield power and gained a higher energy cost, limiting its strength as both an engage and escape tool._

- Tether Shift (all Shapeshifter Staffs)
  - Energy Usage: 11 → 16
  - Shield when jumping to enemy: 100 → 88

**Swords**

> _Heroic Strike’s speed boost duration has been increased, giving players a little more leeway to use their next first-slot ability without losing the bonus movement speed and slightly increasing Swords’ stickiness._

- Heroic Strike (all Swords)
  - Speed boost: 3.5s → 4s

**War Gloves**

> _Hellfire Hands have received a bit of extra damage-over-time damage to help them find a place in the meta again._

- Infernal Boulder (Hellfire Hands)
  - DoT damage per tick: 18 → 24 (max.: 162 → 216)

**Helmets**

> _Avalonian Beam’s maximum range has been reduced, limiting its power as a long-range, non-interactive poke tool._

- Avalonian Beam (Cowl of Purity)
  - Max range: 21m → 18m

> _Firebreath has gained an unconditional pierce effect, helping Mage Cowl stand out as more than a simple damage option and opening it up for consideration in group content. Get out there and melt through your opponents’ defenses._

- Firebreath (Mage Cowl)
  - Now reduces damage resistances by 0.08 for 3s

> _Flare’s cooldown has been reduced to better function as a high-uptime, anti-stealth flank control tool, while its cooldown reduction effect has been increased to improve its viability in small-scale group content._

- Flare (Dragonslayer Hood)
  - Cooldown rate decrease: 50% → 66%
  - Cooldown: 25s → 20s

**Armors**

> _Mage Robe’s cooldown has been reduced to better keep pace with enemy buffs._

- Purging Shield (Mage Robe)
  - Cooldown: 35s → 30s

> _Requite’s damage has been reduced to keep Armor of Valor focused on defense and utility._

- Requite (Armor of Valor)
  - Damage: 27 → 21

**Mounts**

> _Fire Breath has been moved to a different ability slot, and its cooldown has been reduced to better support open-world solo PvE._

- Fire Breath (Firewing Drake)
  - Cooldown: 90s → 60s
  - Slot: 3rd weapon → helmet

**Misc**

> _To reduce the power of full-stall lava comps in Hellgates, lava has been changed to significantly reduce defense against players. This should give comps that bring damage a better chance to defeat stall comps before everyone dies to the lava._

- Lava now also decreases defense vs. players by 50%

### Fixes

**Mob Fixes**
- Fixed issue where the Renowned Huntress’ Cross Fissure damage area would persist longer than the VFX indicated
- Fixed issue where Mammoth Hunter’s Forest of Spears would not correspond to its indication area

**Spell Fixes**
-  Falcon Smash (Battle Bracers): Fixed issue where the second part of the spell would sometimes fail to cast correctly

**UI Fixes**
- Fixed issue where popup notifications were larger than intended
- Fixed issue where it was not possible to close the Bank Overview by pressing Esc when the search bar contained text
-  Fixed issue where HUD Tracker header could not be interacted with
-  Fixed issue where it was not possible to interact with player names in the chat window
-  Fixed issue where whispering a player in the chat window could cause the virtual keyboard to disappear
-  Fixed issue where the Visible Channels list in the General Chat Settings could not be navigated with the right stick

**Other Fixes**
-  Fixed issue where certain spells would cast in a different direction to that shown by their indicators
-  Fixed issue where it was not possible to auto-attack an enemy while an ally was targeted
-  Fixed issue where rapidly casting spells could cause an ‘Invalid Target’ message to appear
- Various additional controller, graphical, animation, terrain, audio, UI, and localization fixes
