# F1 Podium Prediction: progress and decision log

CSEN 903 Milestone 1 · **deadline 18 Oct 2026, 23:59** · last updated 13 Oct 2026

This file is for the evaluation. At the evaluation, any team member can be asked about any step. For every decision, this log gives **what we chose, why, and the numbers behind it**, plus where it lives in [`F1_Podium_Prediction.ipynb`](F1_Podium_Prediction.ipynb).

All numbers come from the committed, fully executed notebook. It runs top to bottom in a single Run All with 0 errors (~8 minutes on a laptop CPU), and a fresh re-run reproduces every table in `outputs/` exactly.

---

## 1. Progress

### Milestone checklist (from the brief)
| Item | Status | Where |
|---|---|---|
| EDA before and after cleaning, with plots | ✅ | §4, §6 |
| Sentinel handling (`\N`), semantic typing | ✅ | §5.1–5.3 |
| Grain = one row per (raceId, driverId), duplicates documented | ✅ | §5.6 (D3) |
| PK / FK checks (asserted after every row-changing step) | ✅ | §3.2, §5, §6 |
| Data questions Q1–Q3: answers, plots, markdown, in the report | ✅ | §7, report §3 |
| Feature selection with evidence; leakage-safe form features | ✅ | §8, §8.1, §9 |
| Preprocessing effect + preprocessing-order experiments (3) | ✅ | §11 |
| Train / validation / test split, justified (course guide boundaries) | ✅ | §10, §14.3 |
| Baseline + ≥ 2 statistical models + shallow FFNN (+ tuning of each) | ✅ | §13 |
| All 5 metrics on train / val / test; primary/secondary metric justified | ✅ | §12–§14, report Tables 8–9 |
| Feature-group ablation (with confidence intervals) | ✅ | §15.1 |
| XAI: permutation importance, SHAP (global), SHAP + LIME (local), in real units | ✅ | §16 |
| Inference function from raw inputs: complete and partially missing records | ✅ | §17 |
| Non-causal statement in the XAI write-up and the report | ✅ | §16, report §8 |
| README, requirements.txt | ✅ | repo root |

### Still to do
- [ ] **Team sign-off on the two codebooks**: `codebooks/status_map.csv` (D11) and `codebooks/constructor_lineage.csv` (D12). Judgement calls are listed in §3 below.
- [ ] **Kaggle notebook** (accessible link). Attach the dataset (or upload this repo's `data/` as a dataset so the numbers match exactly), turn **Internet ON** for `shap` / `lime`, Run All, and check the numbers against this file. Then add the link to `README.md`.
- [ ] **Commit and push** the 13 Oct changes to `github.com/omarkhashab/F1-Podium-Prediction`.
- [ ] **Submit** via the form: Kaggle link, GitHub link, `report/F1_Podium_Prediction_Report.pdf`.
- [ ] Every member reads this file and the report before the evaluation slot.

### Change log
| Date | Change |
|---|---|
| 12 Oct | First commit: notebook scaffold with placeholders; executed only up to §9 (crashed on a missing `jinja2`). |
| 13 Oct | Implemented `F1_Cleaning_Plan.md` (fixed steps + D1–D16), new modelling table, scope comparison; full notebook runs. |
| 13 Oct | Applied the five follow-up decisions (§2 below); filled every placeholder and write-up; created this log; team names; PDF report. |
| 13 Oct | **Review fixes** (§2b): course-guide split; gradient boosting and FFNN tuning; race-bootstrap intervals; ablation on the final model with intervals + "grid + qualifying" row; form-window and lineage experiments; split sensitivity; Platt calibration; raw-input inference function with a qualifying fallback; LIME / SHAP in real units; readable Q3 team names + per-constructorId table; report with all five metrics on validation and test and every figure; README, requirements.txt. |

---

## 2. Five follow-up decisions (13 Oct, first pass)
Numbers updated to the current split.

| # | Decision | Evidence |
|---|---|---|
| 1 | **Keep the modern scope (2006–2024).** | Same validation/test rows, only training differs. Validation PR-AUC modern vs all: LR **0.745 vs 0.727**, RF **0.729 vs 0.719**, FFNN 0.721 vs 0.729. Test: LR 0.698 vs 0.682, RF 0.682 vs 0.677, FFNN 0.683 vs 0.691. Missing feature cells: 2.7 % vs 21.1 %. All gaps are inside the bootstrap noise, so 4× the rows buys nothing measurable. |
| 2 | **Outliers: hard limits only**, for pit stops ([1.5 s, 120 s]) as well as qualifying (> 2 × session median). | The robust z-score (> 3.5) would have flagged 1,491 pit stops (13 %) and 703 qualifying times, mostly genuine slow ones. Hard limits flag 481 pit stops (red-flag suspensions, e.g. ~51-minute "stops") and 1 qualifying time (16:42.640, race 255). |
| 3 | **Drop the sprint features** (via the general selection rule, §9). | Sprints start in 2021 and training ends in 2019: `sprint_finish_pct` is 100 % empty and `is_sprint_weekend` constantly 0 in training. |
| 4 | **Stricter `race_shortened` rule:** laps < 75 % of typical **and** race time < 75 % of the season median, **or** half points. | The laps-only rule flagged 15 races, 8 of them false positives. The new rule flags 7, with 1 known false positive (Swiss GP 1950) and 1 known miss (Japan 2022). Reporting only, never a feature. |
| 5 | **Scale-free points in form features:** `drv_pts_frac_lastN` / `con_pts_frac_lastN` = average share of the race's best points haul over the last 5 races. | Raw points change meaning across the 2010 scoring change, half-points races and fastest-lap bonuses. Univariate AUC on train: 0.90 for both. |

## 2b. Review fixes (13 Oct, second pass)
| # | Change | Why / evidence |
|---|---|---|
| R1 | **Split = course guide boundaries:** train ≤ 2019, validation 2020–21, test 2022–24 (was ≤ 2020 / 2021–22 / 2023–24). | The course's F1 guide names these boundaries. Test is now the whole ground-effect era, so it measures carry-over across a rule change, and validation never sees the new era. Sensitivity (§14.3): with the old split the model still beats the grid rule by the same +0.05. |
| R2 | **Gradient boosting** (HistGradientBoosting) added and tuned (12 configs). | Usually the strongest tabular model. Best: learning rate 0.03, depth 3, leaf 100 → validation 0.739, test 0.693: not better than LR. |
| R3 | **FFNN architecture tuning** (6 configs, 1–2 hidden layers). | Best: one layer of 64 units, dropout 0.4 → validation 0.735 (starting 32-16: 0.721). More regularisation helped. |
| R4 | **Model choice rule:** simplest model within 0.005 of the best validation PR-AUC. | `lr_tuned` 0.7455 vs `lr_baseline` 0.7454 → `lr_baseline` (C = 1). Differences that small are far below the bootstrap noise. |
| R5 | **Race-bootstrap 95 % intervals** (1,000 resamples of whole races), incl. paired Δ vs the final model. | Final model: val 0.745 [0.636, 0.850], test 0.698 [0.637, 0.763]. Only the grid rule and default RF are significantly worse; RF, GB and both FFNNs are indistinguishable. |
| R6 | **Ablation re-done on the final model** (+ RF with 5 seeds), threshold re-chosen per run, **+ "grid + qualifying" row**. | Before: RF only, threshold fixed at 0.5, single seed. Now: qualifying −0.097 [−0.136, −0.043] and grid + qualifying −0.114 [−0.153, −0.058] are the only groups whose CI excludes 0. |
| R7 | **Form-window experiment** (N = 3 / 5 / 10). | N = 3: Δ −0.013 [−0.022, −0.002] (worse); N = 10: Δ −0.006 [−0.029, +0.014] (same). N = 5 kept, now with evidence. |
| R8 | **Lineage (D12) vs plain constructorId** experiment. | Δ −0.001 [−0.008, +0.005]: lineage does not change accuracy. Kept as a judgement call (no history reset at renames; Q3 compares factories). |
| R9 | **Calibration: Platt scaling** fitted on validation; the inference function reports the calibrated probability. | Weighted LR is over-confident (mean prediction 0.28 vs 15 % rate, Brier 0.095). Platt: cross-fitted Brier 0.067; on test 0.112 → 0.069. Isotonic gave the same Brier but only 64 distinct values (ties) on 780 rows. |
| R10 | **Inference from raw inputs** (`features_at_cutoff`) with a qualifying fallback. | The old version took engineered features and returned p = 0.0000 when qualifying was missing (the missing indicators read "unknown" as "set no time"). Now: quali_pos ← grid, Q2/Q3 from that position, gap ← training median for that position. Rebuilt features match the table for 300 random val/test rows (a second leakage test). |
| R11 | **LIME on raw features** (through the full pipeline); SHAP plots show real values. | The old LIME ran on standardised + missing-indicator columns, so its bars read "missingindicator_… ≤ −0.11". |
| R12 | **Q3 labels** "latest name (family)" + a per-constructorId table. | The question asks for constructors; factory-town labels ("Brackley") were unclear. Leaders are the same either way. |
| R13 | **Preprocessing experiments' F1** at the validation-chosen threshold (was 0.5). | Consistent with how every model is scored. |

---

## 3. Cleaning decisions (D1–D16 and fixed steps)

**Principle:** `RAW` is never modified (its hash is checked at the end), and cleaning works on copies. Cleaning runs on **all seasons**; `DATA_SCOPE` only chooses the modelling rows, so 2006 races still get 2005 history. Cleaning does not depend on the split, so these numbers did not change.

| Decision | What we did | Numbers / why |
|---|---|---|
| Fixed: sentinels | strip → `html.unescape` → `\N`, `""`, `NULL`, … → NaN | 1 trailing space (`'Argentinian '`), 1 HTML entity (`Lotus-Pratt &amp; Whitney`); 122,887 sentinel cells in `results` alone. |
| Fixed: typing | `Int64` / float / datetime / timedelta; durations → seconds (`m:ss`, `mm:ss`, `h:mm:ss`) | Missing values after typing **=** sentinels before typing → **0 parse failures** (asserted). |
| Fixed: drop `results.time` | also `sprint_results.time` | Mixes absolute time with `+gap` (22 formats); post-race anyway. |
| Fixed: missing-value types | `outputs/missingness_types.csv` | Every column labelled structural / outcome / pre-race-informative; only `q1–q3` are usable as features. |
| Fixed: allowed-feature list | explicit list; modelling table asserted ⊆ allowed features + IDs + target | Anything not approved is rejected. The inference function also rejects post-race fields. |
| **D1** seasons | main 2006–2024; comparison 1950–2024 | Coverage verified on our copy: qualifying from 1994 (complete from 2003), lap times 1996, pit stops 2011, sprints 2021. Scope comparison: §2, decision 1. |
| **D2** non-starters | drop rows with no grid slot | Dropped 1,535 rows: DNQ 1,025, DNPQ 331, Withdrew (grid 0) 164, 107 % rule 9, Excluded 6. Only 9 in 2006+. **Kept** 84 "Withdrew" with a grid slot (12 modern): at the cutoff we would have predicted for them. |
| **D3** shared drives | merge to one row; pre-race fields from earliest `resultId`; podium if any car | 125 rows → 61 driver-races. 15 races (1950–60) have ≠ 3 podium rows: all are one car shared by several drivers (explained in a table). |
| **D4** Indy 500 | excluded from races and all child tables | 11 races, 1,132 rows across tables. Separate set of drivers, 33-car grid; would distort Q2. |
| **D5** grid = 0 | 2006+: `field_size + 1` + `pitlane_start`; pre-2006: NaN + `grid_unknown` | 77 pit-lane starts, 45 unknown slots. Left as 0, a pit-lane start would look better than pole. |
| **D6** missing features | domain fill first, then train median + missing indicator | Domain fill 11,360 cells; 12,516 cells left for the median imputer. Indicators add +0.010 validation PR-AUC (E3). |
| **D7** round-1 standings | last season's final standings + `is_round_1` | 75 round-1 races; 1,348 of 1,610 round-1 rows get last-season standings (the rest are debutants / new teams). |
| **D8** outliers | hard limits only (§2, decision 2) | 482 cells → NaN; rows never deleted. |
| **D9** lap cleaning | drop lap 1, pit in/out laps, laps > 107 % of race median; pace = driver median / best median | 589,081 laps → 513,483 clean. `pace_ratio` for 10,655 driver-races (median 1.018). Used only shifted (past races). |
| **D10** target | `positionOrder <= 3` after D3 | No NaN; **all 375 modern races have exactly 3 podiums** (asserted). |
| **D11** status codebook | 139 labels → 7 groups | 57 mechanical, 33 lapped, 30 ambiguous, 11 incident, 4 non_start, 3 disqualified, 1 finished. Judgement calls: illness / injury → incident; Underweight → disqualified; Launch control and Heat shield fire → mechanical; Not classified, Out of fuel, Retired, Puncture, Wheel → ambiguous. |
| **D12** constructor lineage | 37 rules, 11 families, year ranges for reused IDs | IDs 51 (Alfa Romeo), 131 (Mercedes) and 4 (Renault) each cover two unrelated teams. Tested vs plain IDs: no accuracy difference (R8). |
| **D13** standings | rank, `pts_share`, `gap_to_leader_share`; no raw points | Scale-free across scoring changes. |
| **D14** sprints | `is_sprint_weekend`, `sprint_finish_pct` (pre-race, allowed) | 18 sprint weekends. Dropped from the model (§2, decision 3). |
| **D15** ISO codes | nationality and country → ISO-3166 alpha-3 | 43 nationalities → 39 codes, 35 countries → 34 codes, **0 unmapped** (asserted). |
| **D16** abnormal races | `race_shortened` flag, reporting only | §2, decision 4. Never a feature. |

---

## 4. Data-engineering questions (unchanged by the split)

| Q | Answer | Key numbers |
|---|---|---|
| **Q1** front row → podium | **The ranking changes after 2014.** 2014–24: Suzuka 89 %, Yas Marina 86 %, Monaco 85 %. 2003–13: Magny-Cours 92 %, Monaco / Monza ≈ 77 %. | 15 circuits in both eras: Spearman ρ = 0.21 (p = 0.46) on grid, 0.50 (p = 0.06) on qualifying. Grid and qualifying front rows differ for 74 entries (8.6 %). |
| **Q2** home advantage | **No home advantage once grid position is controlled for.** | Crude OR 0.84 → grid-adjusted Mantel–Haenszel OR **0.95 (95 % CI 0.80–1.13)**. Sensitivity: 1950–2005 0.95, 2006–24 0.87 (0.57–1.35). |
| **Q3** mechanical DNFs | 2014–21: Caterham 23.5 %, Toro Rosso / AlphaTauri 14.7 %, McLaren 13.5 %, Lotus / Renault 13.5 %; lowest Mercedes 3.8 %. 2022–24: Alpine 11.0 %, Alfa Romeo / Sauber 8.1 %; lowest Aston Martin 3.0 %. | Per constructorId the leaders are the same (Caterham, Lotus F1 17.3 %, Toro Rosso 16.1 %; Alfa Romeo 11.4 %, Alpine 11.0 %). Robust to ambiguous statuses: Spearman (a) vs (b) = 0.95 / 0.85. |

---

## 5. Features, split, preprocessing

- **Split:** train 2006–2019 (5,768 rows, 268 races), validation 2020–21 (780, 39 races), test 2022–24 (1,357, 68 races). Podium rate 13.9 / 15.0 / 15.0 %.
- **Feature selection (training seasons only):** 26 of 36 kept; dropped `grid`, `grid_pct` (ρ 0.97 / 0.96 with `quali_pos`), `gap_to_pole_sec`, `drv_pts_share`, `drv_gap_to_leader_share`, `con_pts_share`, `con_best_finish_lastN`, `grid_unknown`, `is_sprint_weekend`, `sprint_finish_pct`. Strongest univariate AUCs: `quali_pos` 0.92, `gap_to_pole_pct` 0.90, `drv_pts_frac_lastN` 0.90, `con_gap_to_leader_share` 0.90.
- **Leakage:** 300 random rows recomputed from earlier races only ✅; and the inference function rebuilds all features from raw inputs for 300 random val/test rows ✅.
- **Form window = 5 races:** best on validation (R7).
- **Preprocessing experiments** (validation PR-AUC, LR): E1 impute → scale 0.7454 vs scale → impute 0.7422; E2 train-only 0.7454 vs leaky 0.7455 (no gain); E3 indicators 0.7454 vs none 0.7352.

---

## 6. Models and metrics

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

## 7. Ablation (Δ validation PR-AUC when the group is removed)
| | grid + qualifying | qualifying | grid | standings | pace / pit | driver form | constructor form | experience |
|---|---|---|---|---|---|---|---|---|
| **LR (final), 95 % CI** | **−0.114** [−0.153, −0.058] | **−0.097** [−0.136, −0.043] | −0.024 [−0.065, +0.007] | −0.012 | −0.009 | −0.008 | −0.002 | −0.000 |
| RF tuned, 5 seeds | −0.093 | −0.068 | −0.012 | +0.011 | −0.003 | −0.010 | +0.007 | +0.014 |

The starting position is the core signal; the history groups add little unique signal on top of it.

## 8. Explainability (final model)
- **Permutation importance:** `quali_pos` 0.48, `reached_q2` 0.07, `drv_career_podiums` 0.05, `gap_to_pole_pct` 0.03, `drv_pace_ratio_lastN` 0.02, `grid_minus_quali` 0.02. SHAP agrees.
- **Counter-intuitive signs:** `reached_q2` and `drv_age` push down because they are collinear with `quali_pos` and career podiums → the go-to example of **importance ≠ causation**.
- **Local cases:** Hamilton, 2021 Spanish GP, pole: p = 0.98, won. Vettel, 2020 Turkish GP, qualified 12th in the wet (gap 6.9 %): p = 0.04, finished 3rd in a wet race — an outcome the pre-race data cannot show.
- **LIME vs SHAP:** LIME (raw features) agrees with SHAP on the main drivers; its local fit is weak for the near-zero case (R² 0.29), so it is read qualitatively.

## 9. Likely evaluation questions
| Question | Short answer |
|---|---|
| Why this split? | The course guide's boundaries. Test = the whole new regulation era; validation never sees it. With the previous split the margin over the grid rule is the same (+0.05). |
| Why 2006+ and not all data? | Complete, consistent qualifying data. All-seasons training has 21 % missing feature cells vs 2.7 %, and is worse for LR and RF; all gaps are within noise, so the old data buys nothing. |
| How do you know there is no leakage? | Allowed-feature list asserted; standings from the previous round (asserted by date); `shift(1)` for every history feature; two independent 300-row recomputations; preprocessing fitted on train only; test scored once. |
| Why logistic regression and not boosting / the NN? | Best validation PR-AUC (tied with tuned LR), and the bootstrap shows RF, GB and both NNs are statistically indistinguishable from it. Simplest model of the tied group. |
| Why PR-AUC over ROC-AUC? | 15 % positives; ROC-AUC is ≈ 0.93 for everything, including the grid rule. PR-AUC separates the models. |
| Why did you drop `grid`? | ρ = 0.97 with `quali_pos`; still available as `quali_pos + grid_minus_quali`. Removing grid + qualifying together costs 0.114 PR-AUC. |
| Is the model better than "front three on the grid"? | Yes: test PR-AUC 0.698 vs 0.647; paired 95 % CI of the difference excludes 0. |
| Why lineage families if they don't help accuracy? | They don't hurt (Δ −0.001, CI includes 0), avoid resetting a team's history at renames, and Q3 compares factories across eras. A documented judgement call. |
| What does the inference function do with missing qualifying? | Falls back to the grid slot and the typical gap for that position; otherwise the missing indicators would read "unknown" as "set no time" (the old version returned p ≈ 0). |
| Does a home race help? | No: grid-adjusted OR 0.95, CI 0.80–1.13, in every period. |

---

## Reproduce
`pip install -r requirements.txt`, put the 14 CSVs in `./data` (or attach the Kaggle dataset), Run All, then `python report/build_report.py`. Outputs: `outputs/*.csv` (tables), `outputs/figures/` (37 figures), `codebooks/` (4 codebooks).
