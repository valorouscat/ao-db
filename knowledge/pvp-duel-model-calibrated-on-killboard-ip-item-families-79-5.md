# PvP duel model calibrated on killboard: IP + item families (79.5% held-out)

_updated: 2026-10-19 · tags: pvp, model, validation, calibration · data: 1a469e5 · patch: Changelog: Dragonfire Patch 3 (2026-10-12)_

pvp_backtest (2026-10-19, 1252 solo kills europe+west+east, 30% held out) after calibrating duel() on killboard outcomes:

| predictor | picks the killer | log-loss | confident (≥75/≤25%) right |
|---|---|---|---|
| IP gap only | 75.3% | 0.484 | 93% |
| raw TTK simulation | 62.9% | 1.009 | 69% |
| IP + simulated kit | 76.8% | 0.485 | 93% |
| **IP + kit + item families** | **79.5%** | **0.462** | 92% |

Calibration is honest (predicted 80–100% → 95% observed). Weights: +0.84 log-odds per 100 effective IP (≈70% at +100 IP);
simulated kit signals ≈ 0 (the TTK simulation has heavy outliers and carries no signal beyond IP); item families add the
rest. Over-performers: Smuggler Cape +0.31, Hunter Hood +0.22, Spear +0.17, Boots of Valor +0.17, Taproot +0.16, Royal Boots
+0.15, Heavy Crossbow +0.14; under: Mage Sandals −0.13, Martlock/Caerleon/Lymhurst capes −0.11…−0.13, Battleaxe −0.13,
Mercenary Shoes −0.11. Killboard events carry no spells (ActiveSpells empty): spell choice can't be validated; spells are
auto-picked. Consequence: spell/armor swaps from pvp_tune change predictions only through item families — tiny, noisy
differences (Dual Swords T6 CD set: +0.22 vs +0.24) are not real improvements. Open-world data (no cap); in capped content
the IP weight acts on effective IP.

## Sources
- ao-db pvp_backtest --fit (killboard gameinfo/events europe/west/east, 20×51 each, 2026-10-19)
- knowledge/pvp_calibration.json
