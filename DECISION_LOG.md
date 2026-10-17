# F1 Podium Prediction: decision log

CSEN 903 Milestone 1

For every decision in the project, this log gives **what we chose, why, and the numbers behind it**, plus where it lives in [`F1_Podium_Prediction.ipynb`](F1_Podium_Prediction.ipynb).

All numbers come from the committed, fully executed notebook. It runs top to bottom in a single Run All with 0 errors (~8 minutes on a laptop CPU), and a fresh re-run reproduces every table in `outputs/` exactly.

---

## 1. Key decisions

| # | Decision | Evidence |
|---|---|---|
| 1 | **Keep the modern scope (2006–2024).** | Same validation/test rows, only training differs. Validation PR-AUC modern vs all: LR **0.745 vs 0.727**, RF **0.729 vs 0.719**, FFNN 0.721 vs 0.729. Test: LR 0.698 vs 0.682, RF 0.682 vs 0.677, FFNN 0.683 vs 0.691. Missing feature cells: 2.7 % vs 21.1 %. All gaps are inside the bootstrap noise, so 4× the rows buys nothing measurable. |
| 2 | **Outliers: hard limits only**, for pit stops ([1.5 s, 120 s]) as well as qualifying (> 2 × session median). | The robust z-score (> 3.5) would have flagged 1,491 pit stops (13 %) and 703 qualifying times, mostly genuine slow ones. Hard limits flag 481 pit stops (red-flag suspensions, e.g. ~51-minute "stops") and 1 qualifying time (16:42.640, race 255). |
| 3 | **Drop the sprint features** (via the general selection rule, §9). | Sprints start in 2021 and training ends in 2019: `sprint_finish_pct` is 100 % empty and `is_sprint_weekend` constantly 0 in training. |
| 4 | **Stricter `race_shortened` rule:** laps < 75 % of typical **and** race time < 75 % of the season median, **or** half points. | The laps-only rule flagged 15 races, 8 of them false positives. The new rule flags 7, with 1 known false positive (Swiss GP 1950) and 1 known miss (Japan 2022). Reporting only, never a feature. |
| 5 | **Scale-free points in form features:** `drv_pts_frac_lastN` / `con_pts_frac_lastN` = average share of the race's best points haul over the last 5 races. | Raw points change meaning across the 2010 scoring change, half-points races and fastest-lap bonuses. Univariate AUC on train: 0.90 for both. |
| 6 | **Split = course guide boundaries:** train ≤ 2019, validation 2020–21, test 2022–24. | The course's F1 guide names these boundaries. Test is the whole ground-effect era, so it measures carry-over across a rule change; validation never sees the new era. Sensitivity (notebook §14.3): with train ≤ 2020 / validation 2021–22 / test 2023–24 the model beats the grid rule by the same +0.05. |
| 7 | **Gradient boosting** (HistGradientBoosting), tuned over 12 configs. | Usually the strongest tabular model. Best: learning rate 0.03, depth 3, leaf 100 → validation 0.739, test 0.693: not better than LR. |
| 8 | **FFNN architecture tuning** (6 configs, 1–2 hidden layers). | Best: one layer of 64 units, dropout 0.4 → validation 0.735 (starting 32-16: 0.721). More regularisation helped. |
| 9 | **Model choice rule:** simplest model within 0.005 of the best validation PR-AUC. | `lr_tuned` 0.7455 vs `lr_baseline` 0.7454 → `lr_baseline` (C = 1). Differences that small are far below the bootstrap noise. |
| 10 | **Race-bootstrap 95 % intervals** (1,000 resamples of whole races), incl. paired Δ vs the final model. | Final model: val 0.745 [0.636, 0.850], test 0.698 [0.637, 0.763]. Only the grid rule and default RF are significantly worse; RF, GB and both FFNNs are indistinguishable. |
| 11 | **Ablation on the final model** (+ RF over 5 seeds), threshold re-chosen per run, plus a combined "grid + qualifying" row. | Qualifying −0.097 [−0.136, −0.043] and grid + qualifying −0.114 [−0.153, −0.058] are the only groups whose CI excludes 0. |
| 12 | **Form window = 5 races** (tested 3 / 5 / 10). | N = 3: Δ −0.013 [−0.022, −0.002] (worse); N = 10: Δ −0.006 [−0.029, +0.014] (same). |
| 13 | **Lineage families (D12) kept** over plain constructorId. | Δ −0.001 [−0.008, +0.005]: lineage does not change accuracy. Kept as a judgement call (no history reset at renames; Q3 compares factories). |
| 14 | **Platt calibration** fitted on validation; the inference function reports the calibrated probability. | The class-weighted LR is over-confident (mean prediction 0.28 vs 15 % rate, Brier 0.095). Platt: cross-fitted Brier 0.067; on test 0.112 → 0.069. Isotonic gives the same Brier but only 64 distinct values (ties) on 780 rows. |
| 15 | **Inference from raw inputs** (`features_at_cutoff`) with a qualifying fallback. | Without the fallback, the missing-value indicators read "not known yet" as "set no qualifying time" (the only meaning missing qualifying had in training) and push the probability to ≈ 0. Fallback: quali_pos ← grid, Q2/Q3 from that position, gap ← training median for that position. Rebuilt features match the table for 300 random val/test rows (a second leakage test). |
| 16 | **LIME on raw features** (through the full pipeline); SHAP plots show real values. | On the standardised matrix LIME's rules would be z-scores and missing-indicator columns; on raw features they read in real units (e.g. "11 < quali_pos ≤ 17") and agree with SHAP on the main drivers. |
| 17 | **Q3 labels** "latest name (family)" + a per-constructorId table. | The question asks for constructors; the leaders are the same either way. |

---

## 2. Cleaning decisions (D1–D16 and fixed steps)

**Principle:** `RAW` is never modified (its hash is checked at the end), and cleaning works on copies. Cleaning runs on **all seasons**; `DATA_SCOPE` only chooses the modelling rows, so 2006 races still get 2005 history. Cleaning does not depend on the split, so these numbers did not change.

| Decision | What we did | Numbers / why |
|---|---|---|
| Fixed: sentinels | strip → `html.unescape` → `\N`, `""`, `NULL`, … → NaN | 1 trailing space (`'Argentinian '`), 1 HTML entity (`Lotus-Pratt &amp; Whitney`); 122,887 sentinel cells in `results` alone. |
| Fixed: typing | `Int64` / float / datetime / timedelta; durations → seconds (`m:ss`, `mm:ss`, `h:mm:ss`) | Missing values after typing **=** sentinels before typing → **0 parse failures** (asserted). |
| Fixed: drop `results.time` | also `sprint_results.time` | Mixes absolute time with `+gap` (22 formats); post-race anyway. |
| Fixed: missing-value types | `outputs/missingness_types.csv` | Every column labelled structural / outcome / pre-race-informative; only `q1–q3` are usable as features. |
| Fixed: allowed-feature list | explicit list; modelling table asserted ⊆ allowed features + IDs + target | Anything not approved is rejected. The inference function also rejects post-race fields. |
| **D1** seasons | main 2006–2024; comparison 1950–2024 | Coverage verified on our copy: qualifying from 1994 (complete from 2003), lap times 1996, pit stops 2011, sprints 2021. Scope comparison: §1, decision 1. |
| **D2** non-starters | drop rows with no grid slot | Dropped 1,535 rows: DNQ 1,025, DNPQ 331, Withdrew (grid 0) 164, 107 % rule 9, Excluded 6. Only 9 in 2006+. **Kept** 84 "Withdrew" with a grid slot (12 modern): at the cutoff we would have predicted for them. |
| **D3** shared drives | merge to one row; pre-race fields from earliest `resultId`; podium if any car | 125 rows → 61 driver-races. 15 races (1950–60) have ≠ 3 podium rows: all are one car shared by several drivers (explained in a table). |
| **D4** Indy 500 | excluded from races and all child tables | 11 races, 1,132 rows across tables. Separate set of drivers, 33-car grid; would distort Q2. |
| **D5** grid = 0 | 2006+: `field_size + 1` + `pitlane_start`; pre-2006: NaN + `grid_unknown` | 77 pit-lane starts, 45 unknown slots. Left as 0, a pit-lane start would look better than pole. |
| **D6** missing features | domain fill first, then train median + missing indicator | Domain fill 11,360 cells; 12,516 cells left for the median imputer. Indicators add +0.010 validation PR-AUC (E3). |
| **D7** round-1 standings | last season's final standings + `is_round_1` | 75 round-1 races; 1,348 of 1,610 round-1 rows get last-season standings (the rest are debutants / new teams). |
| **D8** outliers | hard limits only (§1, decision 2) | 482 cells → NaN; rows never deleted. |
| **D9** lap cleaning | drop lap 1, pit in/out laps, laps > 107 % of race median; pace = driver median / best median | 589,081 laps → 513,483 clean. `pace_ratio` for 10,655 driver-races (median 1.018). Used only shifted (past races). |
| **D10** target | `positionOrder <= 3` after D3 | No NaN; **all 375 modern races have exactly 3 podiums** (asserted). |
| **D11** status codebook | 139 labels → 7 groups | 57 mechanical, 33 lapped, 30 ambiguous, 11 incident, 4 non_start, 3 disqualified, 1 finished. Judgement calls: illness / injury → incident; Underweight → disqualified; Launch control and Heat shield fire → mechanical; Not classified, Out of fuel, Retired, Puncture, Wheel → ambiguous. |
| **D12** constructor lineage | 37 rules, 11 families, year ranges for reused IDs | IDs 51 (Alfa Romeo), 131 (Mercedes) and 4 (Renault) each cover two unrelated teams. Tested vs plain IDs: no accuracy difference (§1, decision 13). |
| **D13** standings | rank, `pts_share`, `gap_to_leader_share`; no raw points | Scale-free across scoring changes. |
| **D14** sprints | `is_sprint_weekend`, `sprint_finish_pct` (pre-race, allowed) | 18 sprint weekends. Dropped from the model (§1, decision 3). |
| **D15** ISO codes | nationality and country → ISO-3166 alpha-3 | 43 nationalities → 39 codes, 35 countries → 34 codes, **0 unmapped** (asserted). |
| **D16** abnormal races | `race_shortened` flag, reporting only | §1, decision 4. Never a feature. |

---

## 3. Data-engineering questions (unchanged by the split)

| Q | Answer | Key numbers |
|---|---|---|
| **Q1** front row → podium | **The ranking changes after 2014.** 2014–24: Suzuka 89 %, Yas Marina 86 %, Monaco 85 %. 2003–13: Magny-Cours 92 %, Monaco / Monza ≈ 77 %. | 15 circuits in both eras: Spearman ρ = 0.21 (p = 0.46) on grid, 0.50 (p = 0.06) on qualifying. Grid and qualifying front rows differ for 74 entries (8.6 %). |
| **Q2** home advantage | **No home advantage once grid position is controlled for.** | Crude OR 0.84 → grid-adjusted Mantel–Haenszel OR **0.95 (95 % CI 0.80–1.13)**. Sensitivity: 1950–2005 0.95, 2006–24 0.87 (0.57–1.35). |
| **Q3** mechanical DNFs | 2014–21: Caterham 23.5 %, Toro Rosso / AlphaTauri 14.7 %, McLaren 13.5 %, Lotus / Renault 13.5 %; lowest Mercedes 3.8 %. 2022–24: Alpine 11.0 %, Alfa Romeo / Sauber 8.1 %; lowest Aston Martin 3.0 %. | Per constructorId the leaders are the same (Caterham, Lotus F1 17.3 %, Toro Rosso 16.1 %; Alfa Romeo 11.4 %, Alpine 11.0 %). Robust to ambiguous statuses: Spearman (a) vs (b) = 0.95 / 0.85. |

---

## 4. Features, split, preprocessing

- **Split:** train 2006–2019 (5,768 rows, 268 races), validation 2020–21 (780, 39 races), test 2022–24 (1,357, 68 races). Podium rate 13.9 / 15.0 / 15.0 %.
- **Feature selection (training seasons only):** 26 of 36 kept; dropped `grid`, `grid_pct` (ρ 0.97 / 0.96 with `quali_pos`), `gap_to_pole_sec`, `drv_pts_share`, `drv_gap_to_leader_share`, `con_pts_share`, `con_best_finish_lastN`, `grid_unknown`, `is_sprint_weekend`, `sprint_finish_pct`. Strongest univariate AUCs: `quali_pos` 0.92, `gap_to_pole_pct` 0.90, `drv_pts_frac_lastN` 0.90, `con_gap_to_leader_share` 0.90.
- **Leakage:** 300 random rows recomputed from earlier races only ✅; and the inference function rebuilds all features from raw inputs for 300 random val/test rows ✅.
- **Form window = 5 races:** best on validation (§1, decision 12).
- **Preprocessing experiments** (validation PR-AUC, LR): E1 impute → scale 0.7454 vs scale → impute 0.7422; E2 train-only 0.7454 vs leaky 0.7455 (no gain); E3 indicators 0.7454 vs none 0.7352.

---

## 5. Models and metrics

| Model | Train PR-AUC | Val PR-AUC | Test PR-AUC | Test ROC-AUC | Test F1 |
|---|---|---|---|---|---|
| Grid rule (reference, 1/grid) | 0.645 | 0.639 | 0.647 | 0.914 | 0.649 |
| **LR baseline (C = 1, balanced), final** | 0.711 | **0.745** | **0.698** | 0.934 | 0.690 |
| LR tuned (C = 10) | 0.710 | 0.746 | 0.699 | 0.934 | 0.690 |
| RF default | 1.000 | 0.689 | 0.642 | 0.926 | 0.653 |
| RF tuned (depth 12, leaf 20) | 0.776 | 0.729 | 0.682 | 0.932 | 0.642 |
| Gradient boosting tuned (lr 0.03, depth 3, leaf 100) | 0.755 | 0.739 | 0.693 | 0.930 | 0.654 |
| FFNN starting (32-16, dropout 0.2) | 0.749 | 0.721 | 0.683 | 0.930 | 0.648 |
| FFNN tuned (64, dropout 0.4) | 0.714 | 0.735 | 0.680 | 0.928 | 0.652 |

All five metrics on validation and test are in the report (Tables 8–9) and `outputs/model_comparison.csv`.

- **Primary metric, PR-AUC:** podiums are ~15 % of rows, and the task is ranking podium finishers on top. ROC-AUC is ≈ 0.93 for every model (0.91 for the grid rule), so it barely separates them.
- **Secondary metric, F1** at the threshold chosen on validation (0.732 for the final model). Max-F1 thresholds are at least as good as "top 3 per race" for every model (LR: 0.714 vs 0.709).
- **Final model = LR baseline:** test PR-AUC 0.698, ROC-AUC 0.934, F1 0.690, precision 0.599, recall 0.814 (166 TP, 111 FP, 38 FN, 1,042 TN). +0.051 over the grid rule (paired 95 % CI [+0.003, +0.095]).
- **Per season (test):** 2022 0.660 (first ground-effect season), 2023 0.770, 2024 0.664.
- **Calibration:** Platt scaling on validation; test Brier 0.112 → 0.069.

## 6. Ablation (Δ validation PR-AUC when the group is removed)
| | grid + qualifying | qualifying | grid | standings | pace / pit | driver form | constructor form | experience |
|---|---|---|---|---|---|---|---|---|
| **LR (final), 95 % CI** | **−0.114** [−0.153, −0.058] | **−0.097** [−0.136, −0.043] | −0.024 [−0.065, +0.007] | −0.012 | −0.009 | −0.008 | −0.002 | −0.000 |
| RF tuned, 5 seeds | −0.093 | −0.068 | −0.012 | +0.011 | −0.003 | −0.010 | +0.007 | +0.014 |

The starting position is the core signal; the history groups add little unique signal on top of it.

## 7. Explainability (final model)
- **Permutation importance:** `quali_pos` 0.48, `reached_q2` 0.07, `drv_career_podiums` 0.05, `gap_to_pole_pct` 0.03, `drv_pace_ratio_lastN` 0.02, `grid_minus_quali` 0.02. SHAP agrees.
- **Counter-intuitive signs:** `reached_q2` and `drv_age` push down because they are collinear with `quali_pos` and career podiums → the go-to example of **importance ≠ causation**.
- **Local cases:** Hamilton, 2021 Spanish GP, pole: p = 0.98, won. Vettel, 2020 Turkish GP, qualified 12th in the wet (gap 6.9 %): p = 0.04, finished 3rd in a wet race — an outcome the pre-race data cannot show.
- **LIME vs SHAP:** LIME (raw features) agrees with SHAP on the main drivers; its local fit is weak for the near-zero case (R² 0.29), so it is read qualitatively.

## Reproduce
`pip install -r requirements.txt`, put the 14 CSVs in `./data` (or attach the Kaggle dataset), Run All, then `python report/build_report.py`. Outputs: `outputs/*.csv` (tables), `outputs/figures/` (37 figures), `codebooks/` (4 codebooks).
