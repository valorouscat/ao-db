# Dual Swords in T6 corrupted dungeons vs mages and bows: tuned kit (pvp_tune)

_updated: 2026-10-19 · tags: pvp, corrupted, stalker, dual swords, counter, consumables · data: 1a469e5 · patch: Changelog: Dragonfire Patch 3 (2026-10-12)_

Model result (ao-db pvp_tune, PvP model with spell effects revised 2026-10-19) for Dual Swords 5.1 at ~1020 in-game IP in
Corrupted Stalker (cap 1000, ×0.2 above) against 8 reference ranged builds (fire/frost/cursed staff + tome, demonic staff,
light crossbow + mistcaller, bow, warbow, longbow) at 1400 IP (→ 1080 effective).

Best set found (score = mean win − death vs ranged): **−0.07 → +0.42**; vs melee references +0.01 → +0.35; live killboard
field (europe, solo fights) 34% → 57% field-weighted win rate.
- Weapon: Heroic Strike / Hamstring / Spinning Blades (Hamstring > Blade Cyclone, Parry Strike, Interrupt).
- Head: Hunter Hood — Retaliate (85% reflect for 3 s, timed on the opponent's burst) / Balanced Mind.
- Armor: Hunter Jacket — Haste / Balanced Mind (≈ Scholar or Cleric Robe with Frost Shield, Jacket of Tenacity Dynamic Defense).
- Shoes: any cloth sandals with Dodge / Aggression (Scholar Sandals cheapest; Mage Sandals Delayed Teleport close).
- Cape: Smuggler (resets the potion cooldown → two poison potions per fight); all other capes far behind.
- Potion: Major Poison Potion **8.3** (true damage vs players 5 ticks; ignores armor and IP cap); Food: Beef Stew 8.3 (+17.5% dmg).
- Consumables alone (poison 8.3 + beef stew 8.3) raise the score −0.07 → +0.30: by far the cheapest upgrade.

Model fixes made for this analysis (aodb/pvp.py): spellimmunity counted as damage immunity only for category 'damage'
(was half-invulnerability for knockback/purge immunity); conditions (If…/not) no longer followed as casts; mob-only and
arena-only effect variants skipped; Defense rating x → damage × 1/(1+x); % resistance buffs, damage buffs/self-debuffs,
weakening, attack speed, max-HP buffs, reflect, cast interrupts, CC resistance, cooldown rate; passives, food and cape procs
(internal cooldown); potion damage vs players; armor spells auto-picked when missing; stacking procs ½ of charges;
short-radius auras at 50% vs ranged; melee-vs-ranged uptime (kiting) 0.6 base ± gap closers / slows.

Caveats: model, not a guarantee — skill, positioning and cooldown timing are not modelled; kiting uptime and the 50% burst
timing for defensive cooldowns are assumptions; reference opponents are fixed archetypes.

## Sources
- ao-db pvp_tune --vs ranged --opp-ip 1400 --ips avg=1020 (aodb/pvp.py, ao-bin-dumps current dump)
- ao-db pvp_check corrupted_stalker (killboard europe, 510 solo kills, 2026-10-19)
- spells.json RETALIATE2, POTION_POISON_P5/P8, PASSIVE_CAPE_SMUGGLER(_EFFECT/_COOLDOWN), ENRAGE/ENRAGE_BUFF, POTION_RESISTANCE_P8, POTION_MOB_RESET_P8, DELAYED_TELEPORT
- https://steamstore-a.akamaihd.net/news/externalpost/steam_community_announcements/1846018067940491 (Dragonfire Patch 3, 2026-10-12: no changes to these items)
