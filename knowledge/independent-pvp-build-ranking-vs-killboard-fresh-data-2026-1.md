# Independent PvP build ranking vs killboard (fresh data, 2026-10-19)

_updated: 2026-10-19 · tags: pvp, model, validation, killboard, weapons · data: 1a469e5 · patch: Changelog: Dragonfire Patch 3 (2026-10-12)_

Out-of-sample check: 1429 killboard events from the hour after the calibration was fitted (no overlap), 627 solo fights.

Per fight (fresh data): IP only 70.0% right (log-loss 0.535); raw duel simulation 59.0% (1.066); calibrated model 74.5% (0.508),
confident calls (≥75%) right 88%. The calibration generalises: +4.5 points over IP.

Weapon ranking (round-robin at 1200 IP, standard Hunter Hood / Mercenary Jacket / Mercenary Shoes / Thetford kit) vs observed
IP-adjusted strength (mean outcome − IP-only prediction per fight):
- Raw simulation (never saw the killboard): Spearman −0.01 (fresh hour, 55 weapons) / −0.16 (training period, 68). No signal —
  e.g. it ranks Cursed Staff first (0.90) while the killboard has it below average (−0.09), Dual Swords near last (0.26) while
  the killboard has them above average (+0.07). Of the killboard's top-10 weapons it ranks 1, 5 and 9 high and the rest 24–58.
- Calibrated model: +0.17 fresh / +0.48 training (in-sample, inflated).
- The killboard ranking itself is unstable at this sample size: training period vs fresh hour Spearman +0.26 — that is
  roughly the ceiling a weapon ranking can reach against one hour of data.
Killboard top weapons (IP-adjusted, ≥20 fights, both periods): Daybreaker, Forcepulse Bracers, Great Frost Staff, Arcane Staff,
Heavy Crossbow, Lifecurse Staff, Heron Spear, Bow, Wildfire Staff, Trinity Spear (+0.08…+0.16 ≈ +10–20 IP worth).

Conclusion: build advice should come from the calibrated model / killboard statistics; the raw simulation's kit judgement
is not reliable for choosing weapons.

## Sources
- albion killboard gameinfo/events europe/west/east, fetched 2026-10-19 10:26–11:25 UTC (fresh) and earlier (training)
- ao-db pvp.win_probability with knowledge/pvp_calibration.json
