# F1 Podium Prediction: progress and decision log

CSEN 903 Milestone 1 · **deadline 18 Oct 2026, 23:59** · last updated 13 Oct 2026

This file is for the evaluation. At the evaluation, any team member can be asked about any step. For every decision, this log gives **what we chose, why, and the numbers behind it**, plus where it lives in [`F1_Podium_Prediction.ipynb`](F1_Podium_Prediction.ipynb).

All numbers come from the committed, fully executed notebook. It runs top to bottom in a single Run All with 0 errors, and two consecutive runs produce identical outputs.

---

## 1. Progress

### Milestone checklist (from the brief)
| Item | Status | Where |
|---|---|---|
| EDA before and after cleaning, with plots | ✅ | §4, §6 |
| Sentinel handling (`\N`), semantic typing | ✅ | §5.1–5.3 |
| Grain = one row per (raceId, driverId), duplicates documented | ✅ | §5.6 (D3) |
| PK / FK checks (asserted after every row-changing step) | ✅ | §3.2, §5, §6 |
| Data questions Q1–Q3: answers, plots, markdown | ✅ | §7 |
| Feature selection with evidence; leakage-safe form features | ✅ | §8, §8.1, §9 |
| Preprocessing effect + preprocessing-order experiments (3) | ✅ | §11, §12 |
| Train / validation / test split, justified | ✅ | §10 |
| Baseline + ≥ 2 statistical models + shallow FFNN | ✅ | §13 |
| All metrics on train / val / test; primary/secondary metric justified | ✅ | §12–§14 |
| Feature-group ablation | ✅ | §15 |
| XAI: permutation importance, SHAP (global), SHAP + LIME (local) | ✅ | §16 |
| Inference function: complete and partially missing record | ✅ | §17 |
| Non-causal statement in the XAI write-up and the report | ✅ | §16 |

### Still to do
- [x] **Team names** in the notebook's first cell: Omar Osama · Mohamed Ayman · Moataz Ashraf · Omar Emad. (Add student IDs if the course requires them.)
- [ ] **Team sign-off on the two codebooks**: `codebooks/status_map.csv` (D11) and `codebooks/constructor_lineage.csv` (D12). Judgement calls are listed in §3 below.
- [x] **PDF report:** `report/F1_Podium_Prediction_Report.pdf` (12 pages). Regenerate with `python report/build_report.py` after any notebook re-run; tables are read from `outputs/*.csv`. **Team: read it once before submitting.**
- [ ] **Kaggle notebook** (accessible link). The notebook finds the Kaggle input folder automatically; enable Internet so `shap` and `lime` can install.
- [x] **GitHub**: pushed to the public repo `github.com/omarkhashab/F1-Podium-Prediction` (13 Oct). Add teammates as collaborators; the original `Aymanoski/ACL` can be synced later.
- [ ] **Submit** via the form: Kaggle link, GitHub link, PDF.
- [ ] Every member reads this file before the evaluation slot.

### Change log
| Date | Change |
|---|---|
| 12 Oct | First commit: notebook scaffold with placeholders; executed only up to §9 (crashed on a missing `jinja2`). |
| 13 Oct | Implemented `F1_Cleaning_Plan.md` (fixed steps + D1–D16), new modelling table, scope comparison; full notebook runs. |
| 13 Oct | Applied the five follow-up decisions (§2 below); filled every placeholder and write-up; created this log. |
| 13 Oct | Team names added; PDF report generated (`report/`). |

---

## 2. Five follow-up decisions (13 Oct)
| # | Decision | Evidence |
|---|---|---|
| 1 | **Keep the modern scope (2006–2024).** | Same validation/test rows, only training differs. Validation PR-AUC modern vs all: LR **0.722 vs 0.705**, RF **0.697 vs 0.670**, FFNN 0.704 vs 0.719. Test: LR 0.713 vs 0.694, RF 0.709 vs 0.670, FFNN 0.713 vs 0.701. Missing feature cells: 2.6 % vs 20.8 %. |
| 2 | **Outliers: hard limits only**, for pit stops ([1.5 s, 120 s]) as well as qualifying (> 2 × session median). | The robust z-score (> 3.5) would have flagged 1,491 pit stops (13 %) and 703 qualifying times, mostly genuine slow ones. Hard limits flag 481 pit stops (red-flag suspensions, e.g. ~51-minute "stops") and 1 qualifying time (16:42.640, race 255). |
| 3 | **Drop the sprint features** (via the general selection rule, §9). | Sprints start in 2021 and training ends in 2020: `sprint_finish_pct` is 100 % empty and `is_sprint_weekend` constantly 0 in training. The model cannot learn from them. |
| 4 | **Stricter `race_shortened` rule:** laps < 75 % of typical **and** race time < 75 % of the season median, **or** half points. | The laps-only rule flagged 15 races, 8 of them false positives (distance or layout changes: Swiss GP 1950–51, Monza 1955–61, Spa 1958, Paul Ricard 1985). The new rule flags 7, with 1 known false positive (Swiss GP 1950) and 1 known miss (Japan 2022: red-flag time counts). Reporting only, never a feature. |
| 5 | **Scale-free points in form features:** `drv_pts_frac_lastN` / `con_pts_frac_lastN` = average share of the race's best points haul over the last 5 races. | Same reason as D13: raw points change meaning across the 2010 scoring change (a win went from 10 to 25 points), half-points races and fastest-lap bonuses. Univariate AUC on train: 0.90 for both. |

---

## 3. Cleaning decisions (D1–D16 and fixed steps)

**Principle:** `RAW` is never modified (its hash is checked at the end), and cleaning works on copies. Cleaning runs on **all seasons**; `DATA_SCOPE` only chooses the modelling rows, so 2006 races still get 2005 history.

| Decision | What we did | Numbers / why |
|---|---|---|
| Fixed: sentinels | strip → `html.unescape` → `\N`, `""`, `NULL`, … → NaN | 1 trailing space (`'Argentinian '`), 1 HTML entity (`Lotus-Pratt &amp; Whitney`); 122,887 sentinel cells in `results` alone. |
| Fixed: typing | `Int64` / float / datetime / timedelta; durations → seconds (`m:ss`, `mm:ss`, `h:mm:ss`) | Missing values after typing **=** sentinels before typing → **0 parse failures** (asserted). |
| Fixed: drop `results.time` | also `sprint_results.time` | Mixes absolute time with `+gap` (22 formats); post-race anyway. |
| Fixed: missing-value types | `outputs/missingness_types.csv` | Every column labelled structural / outcome / pre-race-informative; only `q1–q3` are usable as features. |
| Fixed: allowed-feature list | explicit list; modelling table asserted ⊆ allowed features + IDs + target | Safer than a blocked-field list: anything not approved is rejected. The inference function still rejects post-race fields. |
| **D1** seasons | main 2006–2024; comparison 1950–2024 | Coverage verified on our copy: qualifying from 1994 (complete from 2003), lap times 1996, pit stops 2011, sprints 2021. Scope comparison: see §2, decision 1. |
| **D2** non-starters | drop rows with no grid slot | Dropped 1,535 rows: DNQ 1,025, DNPQ 331, Withdrew (grid 0) 164, 107 % rule 9, Excluded 6. Only 9 in 2006+. **Kept** 84 "Withdrew" with a grid slot (12 modern): at the cutoff we would have predicted for them. |
| **D3** shared drives | merge to one row; pre-race fields from earliest `resultId`; podium if any car | 125 rows → 61 driver-races. The old "keep earliest row" placeholder dropped 18 podium rows and kept 6. 15 races (1950–60) have ≠ 3 podium rows: all are one car shared by several drivers (explained in a table). |
| **D4** Indy 500 | excluded from races and all child tables | 11 races, 1,132 rows across tables. It had a separate set of drivers and a 33-car grid, and would distort Q2. |
| **D5** grid = 0 | 2006+: `field_size + 1` + `pitlane_start`; pre-2006: NaN + `grid_unknown` | 77 pit-lane starts, 45 unknown slots. Left as 0, a pit-lane start would look better than pole. 43 races have grid numbers > rows (F2 cars), handled by `field_size = max(rows, max grid)`. |
| **D6** missing features | domain fill first, then train median + missing indicator | Domain fill 11,360 cells (rookies = 0 starts, first visit to a circuit = NaN + flag, no pit data = flag). 12,516 cells left for the median imputer. Indicators add +0.006 validation PR-AUC (experiment E3). |
| **D7** round-1 standings | last season's final standings + `is_round_1` | 75 round-1 races; 1,348 of 1,610 round-1 rows get last-season standings (the rest are rookies / new teams). Asserted: the source race is dated earlier, and from the previous season. |
| **D8** outliers | hard limits only (see §2, decision 2) | 482 cells → NaN; rows never deleted. |
| **D9** lap cleaning | drop lap 1, pit in/out laps, laps > 107 % of race median; pace = driver median / best median | 589,081 laps → 513,483 clean (−11,041 lap 1, −21,877 pit laps, −42,680 slow laps). `pace_ratio` for 10,655 driver-races (median 1.018). Used only shifted (past races). |
| **D10** target | `positionOrder <= 3` after D3 | No NaN; **all 375 modern races have exactly 3 podiums** (asserted). |
| **D11** status codebook | 139 labels → 7 groups | 57 mechanical, 33 lapped, 30 ambiguous, 11 incident, 4 non_start, 3 disqualified, 1 finished. Judgement calls: illness / injury → incident (driver-related); Underweight → disqualified; Launch control and Heat shield fire → mechanical; Not classified, Out of fuel, Retired, Puncture, Wheel → ambiguous. |
| **D12** constructor lineage | 37 rules, 11 families, year ranges for reused IDs | IDs 51 (Alfa Romeo), 131 (Mercedes) and 4 (Renault) each cover two unrelated teams. Judgement calls: Racing Point after the 2018 administration and Manor 2015 kept in their families; Brawn → Brackley; Toleman → Enstone; Lotus Racing → Caterham; Prost → Ligier; Tyrrell → BAR **not** linked. MF1 / Spyker MF1 (renamed mid-2006) points are summed in the standings. |
| **D13** standings | rank, `pts_share`, `gap_to_leader_share`; no raw points | Scale-free across the 2010 scoring change, 2014 double points and half-points races. |
| **D14** sprints | `is_sprint_weekend`, `sprint_finish_pct` (pre-race, allowed) | 18 sprint weekends (2021: 3, 2022: 3, 2023: 6, 2024: 6). Dropped from the model (§2, decision 3). |
| **D15** ISO codes | nationality and country → ISO-3166 alpha-3 | 43 nationalities → 39 codes, 35 countries → 34 codes, **0 unmapped** (asserted). East German → DEU; dual nationality → first listed. |
| **D16** abnormal races | `race_shortened` flag, reporting only | See §2, decision 4. Never a feature (unknown before the start). |

---

## 4. Data-engineering questions

| Q | Answer | Key numbers |
|---|---|---|
| **Q1** front row → podium | **The ranking changes after 2014.** 2014–24: Suzuka 89 %, Yas Marina 86 %, Monaco 85 %. 2003–13: Magny-Cours 92 %, Monaco / Monza ≈ 77 %. | 15 circuits in both eras: Spearman ρ = 0.21 (p = 0.46) on grid, 0.50 (p = 0.06) on qualifying. Grid and qualifying front rows differ for 74 entries (8.6 %). Eras: 2003–13 (complete qualifying) vs 2014–24; ≥ 8 front-row starts. |
| **Q2** home advantage | **No home advantage once grid position is controlled for.** | Crude OR 0.84 → grid-adjusted Mantel–Haenszel OR **0.95 (95 % CI 0.80–1.13)**. Sensitivity: 1950–2005 0.95 (0.79–1.15), 2006–24 0.87 (0.57–1.35). 24,710 starters, 1,941 at home. |
| **Q3** mechanical DNFs | 2014–21: Caterham 23.5 %, Faenza 14.7 %, McLaren 13.5 %, Enstone 13.5 %; lowest Brackley 3.8 %. 2022–24: Enstone 11.0 %, Hinwil 8.1 %; lowest Silverstone 3.0 %. | Robust to ambiguous statuses: Spearman (a) vs (b) = 0.95 / 0.85. Denominator = starts (excludes `non_start`). ≥ 20 starts per family and era; Wilson 95 % CIs. |

---

## 5. Features, split, preprocessing

- **Split:** train 2006–2020 (6,108 rows), validation 2021–22 (879), test 2023–24 (918), by season so whole races stay together. The validation and test seasons are the same for both scopes. Podium rate: 14.0 / 15.0 / 15.0 %.
- **Feature selection (training seasons only):**
  - Rule: drop features that are empty or constant in training, then drop |ρ| ≥ 0.95 duplicates of a feature with higher univariate AUC.
  - **26 of 36 kept.** Dropped: `grid`, `grid_pct` (ρ 0.97 / 0.96 with `quali_pos`; grid = `quali_pos + grid_minus_quali`), `gap_to_pole_sec`, `drv_pts_share`, `drv_gap_to_leader_share`, `con_pts_share`, `con_best_finish_lastN`, `grid_unknown`, `is_sprint_weekend`, `sprint_finish_pct`.
  - Strongest univariate AUCs: `quali_pos` 0.92, `gap_to_pole_pct` 0.90, `drv_pts_frac_lastN` 0.90, `con_gap_to_leader_share` 0.90.
- **Leakage:** 300 random rows recomputed from earlier races only. Form, points share, pace and pit features all match; standings come from the previous round (round 1: previous season) ✅.
- **Form window = 5 races:** about a quarter season. The ablation shows form groups add ≤ 0.012 PR-AUC, so the exact window is not critical.
- **Preprocessing experiments** (validation PR-AUC, LR):

  | Experiment | Variant A | Variant B |
  |---|---|---|
  | E1 order | impute → scale 0.7223 | scale → impute 0.7217 |
  | E2 fit scope | fit on train only 0.7223 | fit on all data, leaky: 0.7215 |
  | E3 missing indicators | with 0.7223 | without 0.7163 |

---

## 6. Models and metrics

| Model | Train PR-AUC | Val PR-AUC | Test PR-AUC | Test ROC-AUC | Test F1 |
|---|---|---|---|---|---|
| Grid rule (reference, 1/grid) | 0.644 | 0.629 | 0.664 | 0.911 | 0.667 |
| LR baseline (C = 1, balanced) | 0.711 | 0.722 | 0.713 | 0.928 | 0.679 |
| **LR tuned (C = 10), final** | 0.710 | **0.723** | **0.713** | 0.928 | 0.679 |
| RF default | 1.000 | 0.646 | 0.668 | 0.922 | 0.619 |
| RF tuned (depth 4, leaf 20) | 0.705 | 0.697 | 0.709 | 0.926 | 0.630 |
| FFNN (32-16, dropout 0.2, L2 1e-4) | 0.733 | 0.704 | 0.713 | 0.925 | 0.655 |

- **Primary metric, PR-AUC:** podiums are about 14–15 % of rows, and the task is ranking podium finishers on top. ROC-AUC is ≈ 0.93 for every model because the many easy backmarkers inflate it.
- **Secondary metric, F1:** the quality of the yes/no call at the threshold chosen on validation (0.724 for the final model).
- **Threshold strategy = max-F1 on validation.** It beats "top 3 per race" for every model (LR: F1 0.718 vs 0.682).
- **Final model = tuned LR:** best validation PR-AUC, and the simplest model. Test was never used to choose.
  - Test: PR-AUC 0.713, ROC-AUC 0.928, F1 0.679, precision 0.583, recall 0.812. Confusion matrix: 112 TP, 80 FP, 26 FN, 700 TN.
  - +0.049 PR-AUC over the grid rule.
  - Per season: 2023 0.766, 2024 0.673 (2024 had four winning teams).
- **Why not RF / FFNN?** The default RF memorises the training data (train 1.000 vs val 0.646). Tuned, it doesn't overfit but scores lower. The FFNN overfits slightly (0.733 vs 0.704). The signal is mostly monotonic, so a linear model is enough.
- **Calibration:** probabilities are over-confident (predicted ≈ 0.6 ↔ observed ≈ 0.15) because of class weighting (podiums up-weighted about 6×). Use them as scores, or calibrate on validation.

## 7. Ablation (tuned RF; Δ validation PR-AUC when the group is removed)
| qualifying | grid | driver form | standings | experience | constructor form | pace / pit |
|---|---|---|---|---|---|---|
| **−0.075** (test −0.112) | −0.019 | −0.012 | −0.009 | −0.003 | +0.008 | +0.009 |

Qualifying is the core signal. Grid, standings and form have high univariate AUC (≈ 0.89–0.92), but most of their signal overlaps with qualifying.

## 8. Explainability (final model)
- **Permutation importance** (drop in validation PR-AUC when shuffled): `quali_pos` 0.49, `reached_q2` 0.08, `drv_career_podiums` 0.05, `gap_to_pole_pct` / `grid_minus_quali` / `drv_age` ≈ 0.02. SHAP agrees on the top features.
- **Directions:**
  - Better qualifying position, faster recent pace and more career podiums push towards a podium.
  - A pit-lane start and a grid penalty push strongly down.
  - `reached_q2/q3` and `drv_age` have counter-intuitive negative signs because they are collinear with `quali_pos` and career podiums. This is the go-to example of **importance ≠ causation**.
- **Local cases:**
  - Hamilton, 2021 Spanish GP, on pole: p = 0.98, won.
  - Ocon, 2021 Hungarian GP, started P8: p = 0.11, won after the first-corner pile-up. A sensible pre-race view; the outcome came from an incident nobody could know at the cutoff.
- **LIME vs SHAP:** LIME's top terms for the Ocon row are near-constant binary indicator columns, an artefact of how LIME perturbs and discretises them. SHAP is exact for a linear model, so we rely on it.

## 9. Likely evaluation questions
| Question | Short answer |
|---|---|
| Why 2006+ and not all data? | Complete, consistent qualifying data. All-seasons training has 20.8 % missing feature cells vs 2.6 %, and is worse on validation for LR and RF (§2, decision 1). |
| How do you know there is no leakage? | Allowed-feature list asserted; standings from the previous round (asserted by date); every history feature uses `shift(1)`; 300-row independent recomputation; preprocessing fitted on train only; test touched once in §14. |
| Why keep "Withdrew" rows with a grid slot? | At the cutoff we would have predicted for them; dropping them would select rows on the outcome. |
| Why PR-AUC over ROC-AUC? | 14 % positives; ROC-AUC is ≈ 0.93 for everything, including the grid rule (0.91). PR-AUC separates the models. |
| Why did you drop `grid`? | ρ = 0.97 with `quali_pos`, and grid is still available as `quali_pos + grid_minus_quali`. The ablation shows the grid group adds only 0.019. |
| Is the model better than "pick the front three on the grid"? | Yes: test PR-AUC 0.713 vs 0.664. |
| Does a home race help? | No: grid-adjusted OR 0.95, CI 0.80–1.13, in every period. |
| Why is LIME different from SHAP? | LIME perturbs and discretises near-constant binary columns, so its local fit is unstable; SHAP is exact for a linear model. |

---

## Reproduce
Requirements: Python 3.12+, pandas 3.x, scikit-learn, seaborn, scipy, tensorflow, shap, lime, jinja2. Put the 14 CSVs in `./data` (or attach the Kaggle dataset), then Run All. It takes a few minutes on a laptop CPU.

Outputs:
- `outputs/`: the tables, including `cleaning_log.csv`, `decision_summary.csv`, `model_comparison.csv`, `scope_comparison.csv`, `ablation.csv`, `feature_selection.csv`, `q2_sensitivity.csv`, `threshold_strategy.csv`;
- `outputs/figures/`: about 33 figures;
- `codebooks/`: the 4 codebooks.
