# PvP duel model vs killboard: no predictive power beyond IP (validation 2026-10-19)

_updated: 2026-10-19 · tags: pvp, model, validation, killboard, calibration · data: 1a469e5 · patch: Changelog: Dragonfire Patch 3 (2026-10-12)_

Backtest of aodb/pvp.py duel model on 568 solo kills (europe killboard, 20 pages, 2026-10-19; killer and victim gear,
spells and AverageItemPower as recorded; open world, no IP cap).

| predictor | picks the killer | log-loss |
|---|---|---|
| higher average IP wins | 77% | 0.495 (logistic, 0.85 per 100 IP ≈ 70% win at +100 IP) |
| duel model, before the 2026-10-19 spell-effect revision | 64% | 0.63 (refit) / 0.815 raw |
| duel model, after the revision | 62% | 0.66 (refit) / 1.07 raw |

- Logistic regression with both: model weight ≈ 0 (0.008 new, 0.044 old), IP weight unchanged → the model adds nothing over IP.
- Equal-IP fights (|ΔIP| < 50, n=201): model right 50% (new) / 54% (old) — a coin flip, also for its confident (p<0.2 or >0.8) calls.
- Strongly overconfident: predicted 0–10% → observed 25–29% wins; 90–100% → 71–75%. Raw outputs need temperature ≈ 0.16–0.3.
- Implication: kit-level matchup numbers from pvp_check / pvp_builds / pvp_tune / farm_plan are not validated; treat them as
  descriptive kit comparisons, not win rates. IP difference is the only signal confirmed by data.

Biases of the test: killboard holds only fights that ended in a death (ambushes, victims fighting mobs or gathering, third
parties), so it favours burst/ganks and IP; 'solo' = one participant on the killer side.

## Sources
- albion killboard europe gameinfo/events, 20×51 events fetched 2026-10-19 (scratch validate.py / fit.py)
- ao-db aodb/pvp.py duel() at commits before/after 'PvP model: armor/passive/cape/consumable effects'
