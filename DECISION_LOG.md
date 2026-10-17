# F1 Podium Prediction: decision log

CSEN 903 Milestone 1

For every decision in the project, this log gives **what we chose, why, and the evidence behind it**, plus where it lives in [`F1_Podium_Prediction.ipynb`](F1_Podium_Prediction.ipynb) (§ = notebook section). Each decision is either **hypothesis-driven** (motivated by EDA) or **empirical** (several options tried, each in its own notebook cell, results compared).

All numbers come from the committed, fully executed notebook. It runs top to bottom in a single Run All with 0 errors (~8 minutes on a laptop CPU), and a fresh re-run reproduces every table in `outputs/` exactly.

---

## 0. How each decision is motivated

**Hypothesis-driven** = an EDA finding led to the choice (the EDA is shown in the notebook). **Empirical** = several options were run, each with a baseline row and its own results table or plot, and compared.

| Decision | Basis | Evidence shown in the notebook |
|---|---|---|
| Modelling scope 2006–2024 (D1) | Hypothesis, then empirical | Qualifying-coverage plot (§4) → modern vs all-seasons trial on identical validation/test rows (§14.2) |
| Merge shared drives (D3) | Hypothesis | Duplicates-per-season plot and table (§3.3); 15 odd-podium races explained (§5.6) |
| Drop non-starters (D2), grid = 0 handling (D5) | Hypothesis | Grid = 0 share per season (§4 season overview); counts per status (§5.5, §5.7) |
| Exclude Indianapolis 500 (D4) | Hypothesis | Separate field and 33-car grid (F1 guide); 11 races listed (§5.4) |
| ISO country codes (D15) | Hypothesis | Category spellings found in EDA (§4) |
| Outlier rule: hard limits only (D8) | Empirical | Hard limits vs robust z-score: flagged counts per rule and before/after histograms (§5.8) |
| `race_shortened` rule (D16) | Empirical | Laps-only rule vs laps + time rule: false positives listed (§5.16) |
| Feature set (26 of 36) | Hypothesis | Univariate AUC, decile plots, correlation and missingness heatmaps on training seasons (§9) |
| Form window = 5 | Hypothesis, then empirical | N = 3 / 5 / 10 trial (§15.2) |
| Constructor lineage (D12) | Hypothesis, then empirical | Lineage vs plain constructorId trial (§15.3) |
| Missing indicators, preprocessing order | Empirical | E1–E3, each variant vs the baseline pipeline (§11) |
| Split boundaries | Course guide, then empirical | Course split vs previous split (§14.3) |
| Model family and hyperparameters | Empirical | 8 attempts, each in its own cell, with tuning grids and plots (§13); train/val comparison (§13.7) |
| Threshold strategy | Empirical | Max-F1 vs "top 3 per race" for every model (§13.7) |
| Class weights + calibration | Empirical | Weighted vs unweighted vs Platt vs isotonic (§13.8) |
| Primary metric PR-AUC | Hypothesis | Podium base rate ~14 % (§6); ROC-AUC ≈ 0.93 for every model (§13.7) |
| Final model choice | Empirical | Validation ranking + race-bootstrap intervals (§14, §14.1) |
| Feature-group contributions | Empirical | Ablation with confidence intervals (§15.1) |

---

## 1. Data scope and split

| # | Decision | Why | Evidence |
|---|---|---|---|
| 1 | **Modelling scope = 2006–2024** (the knockout-qualifying era); all seasons kept as a comparison trial. | Qualifying data is patchy before 2003 and absent before 1994, so older rows would be mostly imputed; podium patterns of 30-car, high-retirement fields differ from today. (Hypothesis from EDA, then tested empirically.) | EDA §4: qualifying covers 6–59 % of entries in 1996–2002, ≥ 99 % from 2003. Scope trial §14.2 (same validation/test rows, only training differs): validation PR-AUC modern vs all — LR **0.745 vs 0.727**, RF **0.729 vs 0.719**, FFNN 0.721 vs 0.729; test LR 0.698 vs 0.682, RF 0.682 vs 0.677, FFNN 0.683 vs 0.691. Missing feature cells 2.7 % vs 21.1 %. All gaps are within the bootstrap noise, so 4× the rows buys nothing measurable. |
| 2 | **Split by season**, not randomly; whole races stay in one split. | Rows are not independent: a driver's form carries over from race to race and the sport drifts from season to season. A random split would put later races in training and earlier ones in test (predicting the past from the future) and split the 20 drivers of one race across sets. A season split mirrors real use. | §10: train, validation and test share no race (asserted). |
| 3 | **Boundaries from the course's F1 guide:** train ≤ 2019, validation 2020–21, test 2022–24. | The guide names these boundaries. Test is then the whole ground-effect era (new car rules from 2022), so it measures how a model trained on the hybrid era carries over to a regulation change; validation (end of the hybrid era) never sees the new era. | §10: 5,768 / 780 / 1,357 rows (268 / 39 / 68 races), podium rate 13.9 / 15.0 / 15.0 %. Sensitivity §14.3: with train ≤ 2020 / validation 2021–22 / test 2023–24 the model beats the grid rule by the same +0.05 PR-AUC (test 0.713 vs 0.664). |

---

## 2. Cleaning decisions (D1–D16 and fixed steps)

**Principle:** `RAW` is never modified (its hash is checked at the end) and cleaning works on copies. Cleaning runs on **all seasons**; `DATA_SCOPE` only chooses the modelling rows, so 2006 races still get 2005 history. Key, grain and foreign-key checks are **assertions** that run after every step that changes rows. Every rule writes a row to `outputs/cleaning_log.csv`.

| Decision | What we did | Why | Numbers |
|---|---|---|---|
| Fixed: sentinels | strip → `html.unescape` → `\N`, `""`, `NULL`, … → NaN | Sentinels are text, so they hide as valid values; untrimmed spaces and HTML entities silently break joins. | 1 trailing space (`'Argentinian '`), 1 HTML entity (`Lotus-Pratt &amp; Whitney`); 122,887 sentinel cells in `results` alone; 0 `\N` left (asserted). |
| Fixed: typing | `Int64` / float / datetime / timedelta; durations → seconds (`m:ss`, `mm:ss`, `h:mm:ss`) | Numbers and dates stored as text can't be compared, averaged or ordered in time; durations come in three formats, so one parser handles all. | Missing values after typing **=** sentinels before typing → **0 parse failures** (asserted). |
| Fixed: drop `results.time` | also `sprint_results.time` | It mixes the winner's absolute time with gaps (`+5.478`) — not one quantity — and it is post-race anyway. | 22 different formats found in EDA. |
| Fixed: missing-value types | every column with missing values labelled structural / outcome / pre-race-informative (`outputs/missingness_types.csv`) | Only missingness known *before* the race may be used; outcome missingness (e.g. no finishing time) would leak the result. | Only `q1–q3` are pre-race-informative (knocked out of qualifying). |
| Fixed: allowed-feature list | explicit allowed list; modelling table asserted ⊆ allowed features + IDs + target | Safer than a block list: anything not explicitly approved is rejected. | The inference function also rejects post-race fields. |
| **D1** seasons | main 2006–2024; comparison 1950–2024 | See §1, decision 1. | Coverage verified on our copy (run stops if it differs): qualifying from 1994 (complete from 2003), lap times 1996, pit stops 2011, sprints 2021. |
| **D2** non-starters | drop rows with **no grid slot** (DNQ, DNPQ, 107 % rule, not qualified; withdrew/excluded with grid 0) | The prediction is made once the grid is set; an entry without a grid slot is not a prediction row. **Kept** "Withdrew" rows that had a grid slot: at the cutoff we would have predicted for them, so dropping them would choose rows by what happened later. | Dropped 1,535 rows (DNQ 1,025, DNPQ 331, Withdrew grid 0 164, 107 % rule 9, Excluded 6), only 9 in 2006+. Kept 84 "Withdrew" with a grid slot (12 modern). |
| **D3** shared drives | merge duplicates into one row per (raceId, driverId): pre-race fields (grid, constructor, number) from the **earliest `resultId`** (the car the driver started in); points summed; best `positionOrder`, so podium if **any** of his cars made it | The brief requires one row per driver-race. Rejected alternatives: "keep the earliest row" throws away real podiums (on this data it drops 18 podium rows and keeps only 6); "keep the best row" would take the *pre-race* fields from a row picked by the result. | 125 rows → 61 driver-races; grain unique (asserted). 15 races (1950–60) then have ≠ 3 podium rows, each explained in a table (one car shared by several drivers). Nothing to merge from 2006. |
| **D4** Indianapolis 500 | excluded from races and every child table | Counted for the championship on paper only: an American oval race with an almost separate set of drivers and a 33-car grid; it would distort home-race analysis (Q2), race counts and form history. | 11 races, 1,132 rows across tables; foreign keys still pass. |
| **D5** grid = 0 | 2006+: `grid = field_size + 1` + `pitlane_start`; pre-2006: `grid = NaN` + `grid_unknown` | Left as 0, a pit-lane starter would look *better than pole*. From 2006, 0 means a pit-lane start, which really is behind the last slot; before 2006 it often just means "not recorded", and inventing a slot would be a guess. `field_size = max(rows, highest grid)` handles races with Formula 2 cars mixed in. | 77 pit-lane starts, 45 unknown slots; 43 races have grid numbers above the row count. |
| **D6** missing features | step 1 domain fill where the true value is known; step 2 training-median imputation + missing-indicator columns | A debutant truly has 0 previous starts, so filling 0 is exact, not a guess. A first visit to a circuit stays NaN + flag because "never been here" ≠ "0 % podiums". Medians are fitted on training only (no leakage); indicators let the model use the fact that something is missing. | Domain fill 11,360 cells; 12,516 cells left for the imputer. Indicators +0.010 validation PR-AUC (experiment E3). |
| **D7** round-1 standings | last season's final standings + `is_round_1` flag; renamed teams matched by lineage | Otherwise round 1 has no "standings before the race" at all; last season's final table is the latest information available at that cutoff. | 75 round-1 races; 1,348 of 1,610 round-1 rows get last-season standings (the rest are debutants / new teams). Source race dated earlier and from the previous season (asserted). |
| **D8** timing outliers | hard limits only: pit stop outside [1.5 s, 120 s], qualifying time > 2 × session median → NaN + `<col>_outlier` flag; rows never deleted | Under 1.5 s is physically impossible; over 120 s is a red-flag suspension or repair, not a stop. The robust z-score (Iglewicz & Hoaglin) was computed but not applied: times within a race are tightly packed, so it also flags genuine slow stops and would make slow teams look faster. | Hard limits: 481 pit stops (e.g. ~51-minute "stops") + 1 qualifying time (16:42.640, race 255). The z-score (> 3.5) would have flagged 1,491 pit stops (13 %) and 703 qualifying times. |
| **D9** lap cleaning | per race, drop lap 1, pit in/out laps and laps > 107 % of the race median; `pace_ratio` = driver median ÷ best median; < 5 clean laps → NaN | Finishing position mixes pace with luck; clean lap pace measures how fast car and driver really were. Lap 1 is standing-start traffic, in/out laps include pit time, > 107 % laps are safety-car / VSC / red-flag laps. Used **only** from earlier races. | 589,081 laps → 513,483 clean (−11,041 lap 1, −21,877 pit laps, −42,680 slow laps). `pace_ratio` for 10,655 driver-races (median 1.018). |
| **D10** target | `podium = positionOrder <= 3`, after D3 | `positionOrder` is the only position column filled for every row (classified or not), and it already reflects post-race disqualifications. | No NaN; **all 375 modern races have exactly 3 podiums** (asserted). |
| **D11** status codebook | 139 labels → finished / lapped / mechanical / incident / non_start / disqualified / ambiguous (`codebooks/status_map.csv`) | Q3 needs mechanical vs other causes, and the brief's definition excludes crashes, the driver and regulation decisions. Illness/injury → incident (driver-related, not a car failure). Labels that can be either a car failure or contact ("Retired", "Puncture", "Wheel", …) → ambiguous, and Q3 is computed both ways instead of guessing. | 57 mechanical, 33 lapped, 30 ambiguous, 11 incident, 4 non_start, 3 disqualified, 1 finished; every label mapped exactly once (asserted). |
| **D12** constructor lineage | renamed teams grouped into families (e.g. Minardi → Toro Rosso → AlphaTauri → RB), with year ranges for IDs reused by unrelated teams (`codebooks/constructor_lineage.csv`) | Each name is a new `constructorId`, so team history would reset at every rename (Racing Point 2019 would look like a brand-new team although it is Force India's factory and staff). | 37 rules, 11 families; IDs 51, 131 and 4 each cover two unrelated teams. Tested vs plain IDs: no accuracy difference (§5, decision 3) — kept as a documented judgement call. |
| **D13** standings | championship rank, `pts_share = points / leader`, `gap_to_leader_share`; never raw points | Raw points are not comparable across eras: a win was worth 10 points before 2010 and 25 after, 2014 had double points, some races gave half points, seasons have 17–24 races. Rank and share of the leader are scale-free. | Applied to drivers and constructors, from the standings after the previous round. |
| **D14** sprints | `is_sprint_weekend`, `sprint_finish_pct` (pre-race, allowed) | The sprint runs before the Sunday race, so its result is known at the cutoff. | 18 sprint weekends. Dropped from the model by the selection rule (§3, decision 3): empty in training. |
| **D15** ISO codes | nationality and circuit country → ISO-3166 alpha-3 | Nationality is a demonym ("British") and country a name ("UK", "USA"/"United States"); one standard code makes the Q2 home-race join exact. Judgement calls: East German → DEU, Rhodesian → ZWE, dual nationality → first listed. | 43 nationalities → 39 codes, 35 countries → 34 codes, **0 unmapped** (asserted). |
| **D16** abnormal races | `race_shortened` = (laps < 75 % of typical **and** race time < 75 % of the season median) **or** half points; every race kept | Needed for error analysis; never a feature, because nobody knows before the start that a race will be cut short. The time condition was added because a laps-only rule flagged races whose distance or layout had changed. | Laps-only rule: 15 races, 8 false positives. Final rule: 7 races, 1 known false positive (Swiss GP 1950), 1 known miss (Japan 2022). |

---

## 3. Features and preprocessing

**Features valid at the cutoff (26 selected of 36 candidates):**

| Group | Features | Why valid at the cutoff |
|---|---|---|
| Grid | `pitlane_start`, `grid_minus_quali`, `field_size` | Known once the grid is set (qualifying + penalties). |
| Qualifying | `quali_pos`, `gap_to_pole_pct`, `reached_q2`, `reached_q3` | Qualifying ends before the race. |
| Standings | `drv_champ_rank`, `con_champ_rank`, `con_gap_to_leader_share`, `is_round_1` | Standings after the **previous** round (round 1: last season's final standings); source dated earlier (asserted). |
| Driver form | `drv_avg_finish_lastN`, `drv_podium_rate_lastN`, `drv_finish_rate_lastN`, `drv_pts_frac_lastN` | Rolling over the driver's previous 5 races with `shift(1)`: the current race is never included. |
| Constructor form | `con_podiums_lastN`, `con_pts_frac_lastN` | Previous 5 races of the team, aggregated per race first so a team-mate's current result can't leak. |
| Pace / pit | `drv_pace_ratio_lastN`, `con_pit_ratio_lastN`, `pit_data_available` | From earlier races only; pit data exists from 2011 (flag). |
| Experience | `drv_career_starts`, `drv_career_podiums`, `drv_circuit_visits`, `drv_circuit_podium_rate`, `drv_circuit_first_visit`, `drv_age` | Counts and rates over earlier races; age at race date. |

**Leakage checks:** (1) §8.1 recomputes form, points-share, pace and pit features for 300 random rows from races with an earlier date only — exact match; (2) §17 rebuilds every feature from raw pre-race inputs for 300 random validation/test rows — exact match.

| # | Decision | Why | Evidence |
|---|---|---|---|
| 1 | **Points as a share of the race's best haul** in form features (`drv_pts_frac_lastN`, `con_pts_frac_lastN`). | Same reason as D13: raw points change meaning across scoring systems, half-points races and fastest-lap bonuses. | Univariate AUC on train: 0.90 for both. |
| 2 | **Gap to pole as a percentage**, not seconds. | A 1-second gap means more at a 70-second lap than at a 100-second lap; percentages are comparable across circuits. | `gap_to_pole_sec` dropped as redundant (ρ = 0.99 with the percentage). |
| 3 | **Feature selection on the training seasons only:** (1) drop features that are empty or constant in training; (2) greedy redundancy filter — visit features by univariate AUC, drop one whose \|Spearman ρ\| with an already-kept feature is ≥ 0.95. | Validation and test must not influence the choice. A feature with no variation in training can't be learned; ρ ≥ 0.95 means near-duplicate information that only splits weight in a linear model. Weak features (`grid_minus_quali` AUC 0.56, `drv_age` 0.58, `pitlane_start`, `field_size`, `is_round_1`, `pit_data_available`) are kept: they tell the model when other features are less reliable, and the models can give them little weight. | 26 of 36 kept. Dropped: `grid`, `grid_pct` (ρ 0.97 / 0.96 with `quali_pos`; grid = `quali_pos + grid_minus_quali`), `gap_to_pole_sec`, `drv_pts_share`, `drv_gap_to_leader_share`, `con_pts_share`, `con_best_finish_lastN`, `grid_unknown`, `is_sprint_weekend`, `sprint_finish_pct`. Strongest: `quali_pos` 0.92, `gap_to_pole_pct` 0.90, `drv_pts_frac_lastN` 0.90, `con_gap_to_leader_share` 0.90. |
| 4 | **No one-hot driver / team / circuit IDs.** | Team and driver strength is already carried by standings and form; and IDs don't generalise: renamed teams get new IDs, so they would be unseen categories at prediction time. | Four constructor IDs in validation/test never appear in training (AlphaTauri 2020, Alpine 2021, Aston Martin 2021, RB 2024), and 14 validation/test drivers are not in training. |
| 5 | **Form window = 5 races** (≈ a quarter season). | Long enough to smooth a single DNF, short enough to follow car upgrades. (Hypothesis, then tested.) | §15.2: N = 3 Δ −0.013 [−0.022, −0.002] (worse); N = 10 Δ −0.006 [−0.029, +0.014] (same). |
| 6 | **Preprocessing:** median imputation + missing indicators, then standardisation; fitted on training only; trees skip scaling. | Scaling matters for the penalised LR and the NN (gradient steps, comparable coefficients); trees split on thresholds and don't need it. Fitting on training only avoids leaking validation/test statistics. | §11, E1: impute → scale 0.7454 vs scale → impute 0.7422. E2: train-only 0.7454 vs fitted on all data 0.7455 (no gain, and it would be leakage). E3: indicators 0.7454 vs none 0.7352. |

---

## 4. Models, metrics and evaluation

| # | Decision | Why | Evidence |
|---|---|---|---|
| 1 | **Reference: rank by grid** (score = 1/grid). | The obvious no-model answer; any learned model must beat it to be worth anything. | Test PR-AUC 0.647. |
| 2 | **Baseline: logistic regression.** | The simplest learned model that uses every feature: fast, stable, interpretable coefficients. Every more complex model is compared against it. | Validation 0.745, test 0.698. |
| 3 | **Class weights `balanced`** in every model. | Podiums are ~14 % of training rows; weighting each podium row ≈ 6× keeps the models from ignoring the rare class. | Unweighted LR ranks almost as well (validation 0.741 vs 0.745), but weighting inflates probabilities (decision 10 handles that). |
| 4 | **Tuning grids** (validation PR-AUC): LR C ∈ {0.001 … 10} log-spaced; RF depth {4, 8, 12, none} × leaf {1, 5, 20}; GB learning rate {0.03, 0.1} × depth {2, 3, 5} × leaf {20, 100}; FFNN 6 architectures (1–2 layers, width 16–64, dropout 0–0.4). | Each grid spans the main overfitting control of its model: regularisation strength (LR), tree size (RF, GB), capacity and dropout (NN). | LR: C ≤ 0.1 hurts (0.737 → 0.677), C = 1 and 10 tie (0.745 / 0.746). RF: depth 12 / leaf 20 0.729 (depth 4 / leaf 20 0.729, tied). GB: lr 0.03, depth 3, leaf 100 → 0.739. FFNN: one layer of 64, dropout 0.4 → 0.735 (starting 32-16 / 0.2: 0.721; 32-16 without dropout stopped early at 0.689). |
| 5 | **FFNN training:** Adam, class-weighted cross-entropy, dropout + L2, early stopping on **validation PR-AUC** (patience 15, best weights restored). | ~5,800 rows and 26 features support only a small network (brief: 1–2 hidden layers); early stopping on the primary metric stops before overfitting. | Training curves §13.5. |
| 6 | **Gradient boosting** added as a third model family. | Usually the strongest model on tabular data, and the forest's preference for shallow trees is exactly what boosting combines. | Validation 0.739, test 0.693: not better than LR. |
| 7 | **Primary metric: PR-AUC.** | Podiums are ~15 % of rows and the task is ranking podium finishers above the rest. ROC-AUC is inflated by the many easy back-markers. | ROC-AUC ≈ 0.93 for every model and 0.91 even for the grid rule, so it barely separates them. |
| 8 | **Secondary metric: F1** at a threshold chosen on validation (max F1). | Measures the actual yes/no call. Max-F1 was compared with the domain rule "exactly 3 podiums per race". | Max-F1 ≥ top-3 for every model (LR 0.714 vs 0.709). Final threshold 0.732. |
| 9 | **Model choice on validation only:** the simplest model within 0.005 of the best validation PR-AUC. | Differences that small are far below the noise of 39 validation races, so extra complexity is not earned. | `lr_tuned` 0.7455 vs `lr_baseline` 0.7454 → **`lr_baseline` (C = 1)**. |
| 10 | **Platt calibration** of the final model's score, fitted on validation; the inference function reports the calibrated probability. | The weighted model's raw scores are over-confident. Platt (2 parameters) is smooth and keeps the ranking; isotonic is too flexible for 780 rows. | Mean raw prediction 0.28 vs 15 % rate (Brier 0.095). Cross-fitted Brier: Platt 0.067, isotonic 0.067 but only 64 distinct values (ties). Test Brier 0.112 → 0.069. |
| 11 | **Test scored once**, with the models fitted on the training seasons; no refit on train + validation. | Every choice (hyperparameters, threshold, model, calibration) was made on validation; scoring test once keeps it an honest estimate of the selected model. | §14. |
| 12 | **Race-bootstrap 95 % intervals** (1,000 resamples of whole races), incl. paired Δ vs the final model. | 39 validation / 68 test races: single-split differences need an uncertainty estimate before they are called real. Races are resampled whole because rows of one race are linked. | Final model: val 0.745 [0.636, 0.850], test 0.698 [0.637, 0.763]. Grid rule test Δ −0.051 [−0.095, −0.003] (significantly worse); RF, GB and both FFNNs indistinguishable from LR. |

**Results (PR-AUC unless stated):**

| Model | Train | Val | Test | Test ROC-AUC | Test F1 |
|---|---|---|---|---|---|
| Grid rule (reference, 1/grid) | 0.645 | 0.639 | 0.647 | 0.914 | 0.649 |
| **LR baseline (C = 1, balanced), final** | 0.711 | **0.745** | **0.698** | 0.934 | 0.690 |
| LR tuned (C = 10) | 0.710 | 0.746 | 0.699 | 0.934 | 0.690 |
| RF default | 1.000 | 0.689 | 0.642 | 0.926 | 0.653 |
| RF tuned (depth 12, leaf 20) | 0.776 | 0.729 | 0.682 | 0.932 | 0.642 |
| Gradient boosting tuned (lr 0.03, depth 3, leaf 100) | 0.755 | 0.739 | 0.693 | 0.930 | 0.654 |
| FFNN starting (32-16, dropout 0.2) | 0.749 | 0.721 | 0.683 | 0.930 | 0.648 |
| FFNN tuned (64, dropout 0.4) | 0.714 | 0.735 | 0.680 | 0.928 | 0.652 |

All five metrics on validation and test are in the report (Tables 8–9) and `outputs/model_comparison.csv`. Final model on test: precision 0.599, recall 0.814 (166 TP, 111 FP, 38 FN, 1,042 TN); by season 2022 0.660 (first ground-effect season), 2023 0.770, 2024 0.664.

---

## 5. Experiments

| # | Decision | Why | Evidence |
|---|---|---|---|
| 1 | **Ablation on the final model** (+ tuned RF over 5 seeds as a second model family); hyperparameters fixed, threshold re-chosen on validation each run; 95 % paired race-bootstrap CI (LR) / seed std (RF). | Ablation measures each group's *unique* contribution after training, complementing the univariate evidence of §9; intervals separate real effects from noise. | Table below. |
| 2 | **Extra row: grid + qualifying removed together.** | Grid was dropped as a near-duplicate of `quali_pos`, so removing either group alone understates the starting position. | −0.114 together vs −0.024 (grid) and −0.097 (qualifying) alone. |
| 3 | **Lineage families (D12) tested against plain constructorId.** | The course guide suggests following `constructorId` and accepting resets at renames; we wanted evidence before keeping our choice. | Δ −0.001 [−0.008, +0.005], test identical: no accuracy difference. Plain IDs leave 1.1 % of training and 0.8 % of validation rows without constructor standings (renamed teams' first race) vs 0.5 % / 0 %. Kept as a judgement call (no history reset at renames; Q3 compares factories). |

| Δ validation PR-AUC when removed | grid + qualifying | qualifying | grid | standings | pace / pit | driver form | constructor form | experience |
|---|---|---|---|---|---|---|---|---|
| **LR (final), 95 % CI** | **−0.114** [−0.153, −0.058] | **−0.097** [−0.136, −0.043] | −0.024 [−0.065, +0.007] | −0.012 | −0.009 | −0.008 | −0.002 | −0.000 |
| RF tuned, 5 seeds | −0.093 | −0.068 | −0.012 | +0.011 | −0.003 | −0.010 | +0.007 | +0.014 |

Only qualifying and the combined starting position have intervals that exclude 0: the starting position is the core signal, and the history groups add little unique signal on top of it.

---

## 6. Data-engineering questions

All three use multi-hop joins (results ⨝ races ⨝ circuits ⨝ drivers ⨝ constructors ⨝ status ⨝ qualifying) on the cleaned driver-race grain, Indianapolis 500 excluded (D4).

| Q | Design decisions (why) | Answer and key numbers |
|---|---|---|
| **Q1** front row → podium, before vs after 2014 | Eras **2003–13 vs 2014–24**: qualifying is complete from 2003, so the grid and qualifying definitions are comparable in both eras. Front row measured **twice** — grid (after penalties) and qualifying position (before) — as the question asks. **≥ 8 front-row starts** per circuit and era (below that one podium moves a rate by more than 12 points). Ranks compared (Spearman) only for circuits present in both eras. | **The ranking changes after 2014.** 2014–24: Suzuka 89 %, Yas Marina 86 %, Monaco 85 %; 2003–13: Magny-Cours 92 %, Monaco / Monza ≈ 77 %. 15 circuits in both eras: Spearman ρ = 0.21 (p = 0.46) on grid, 0.50 (p = 0.06) on qualifying. Grid and qualifying front rows differ for 74 entries (8.6 %). |
| **Q2** home advantage, controlling for start | Home = nationality and circuit country map to the same ISO code (D15). Control for starting position by comparing **within six grid strata** (pole, P2–3, P4–6, P7–10, P11–15, P16+ — the podium rate falls 2–4× from one bin to the next), pooled with a **Mantel–Haenszel odds ratio** with 95 % CI. All seasons for the largest home sample, plus a sensitivity check by period. Unknown pre-2006 grid slots excluded. | **No home advantage once grid position is controlled for.** Crude OR 0.84 (home entries are often one-off locals starting near the back) → grid-adjusted OR **0.95 (95 % CI 0.80–1.13)**. 1950–2005 0.95, 2006–24 0.87 (0.57–1.35). 24,710 starters, 1,941 at home. |
| **Q3** mechanical retirements, 2014–21 vs 2022–24 | Mechanical = D11 codebook; **ambiguous labels counted both ways** (a: not mechanical, b: mechanical). Denominator = **race starts** (excludes the `non_start` group). Teams grouped by lineage (D12) and also shown per `constructorId`. **≥ 20 starts** per team and era (smaller samples give intervals wider than the rates); Wilson 95 % intervals. | 2014–21: Caterham 23.5 %, Toro Rosso / AlphaTauri 14.7 %, McLaren 13.5 %, Lotus / Renault 13.5 %; lowest Mercedes 3.8 %. 2022–24: Alpine 11.0 %, Alfa Romeo / Sauber 8.1 %; lowest Aston Martin 3.0 %. Per constructorId the leaders are the same (Lotus F1 17.3 %, Toro Rosso 16.1 %; Alfa Romeo 11.4 %). Robust to the ambiguous labels: Spearman (a) vs (b) = 0.95 / 0.85. |

---

## 7. Explainability and inference

| # | Decision | Why | Evidence |
|---|---|---|---|
| 1 | **Explain the final model** (not a different, easier-to-explain one); permutation importance on **validation**. | The explanation must describe the model we actually use; validation rows were not used to fit it. | Permutation importance: `quali_pos` 0.48, `reached_q2` 0.07, `drv_career_podiums` 0.05, `gap_to_pole_pct` 0.03, `drv_pace_ratio_lastN` 0.02, `grid_minus_quali` 0.02. SHAP agrees. |
| 2 | **Not causal**, stated explicitly. | Importance means the model *relies* on a feature, not that it *causes* podiums; correlated features share and swap importance. | `reached_q2` and `drv_age` have negative signs because they are collinear with `quali_pos` and career podiums. |
| 3 | **Local explanations for two chosen rows:** the most confident correct podium and the podium the model considered least likely (validation). | One success and one failure show both what drives a confident prediction and where pre-race information runs out. | Hamilton, 2021 Spanish GP, pole: p = 0.98, won. Vettel, 2020 Turkish GP, qualified 12th in the wet (gap 6.9 %): p = 0.04, finished 3rd in a wet race. |
| 4 | **LIME on raw features** (through the full pipeline); SHAP plots show real values. | Explanations must be readable in real units. On the standardised matrix, LIME's rules would be z-scores and missing-indicator columns. | LIME agrees with SHAP on the main drivers; its local fit is good for the confident case (R² 0.66) and weak for the near-zero case (R² 0.29), so it is read qualitatively. |
| 5 | **Inference from raw pre-race inputs** (`features_at_cutoff`), post-race fields rejected. | A usable function must accept what is actually known before a race, not hand-built features; rejecting post-race fields makes leakage impossible through it. | Rebuilt features match the table for 300 random validation/test rows. Passing `points` raises an error. |
| 6 | **Missing qualifying → domain fallback** (`quali_pos` ← grid slot, Q2/Q3 from that position, gap ← training median for that position); missing history (debutant) left to the imputer. | In training, missing qualifying only ever meant "set no time", so the missing indicators would read "not known yet" the same way and push the probability to ≈ 0. A debutant's missing history matches training, so imputation is correct there. | Hülkenberg, Abu Dhabi 2024: complete 0.080, no qualifying 0.037 (fallback assumes he qualified where he started), debutant in the same car from P5 0.090 (calibrated probabilities). |

---

## Reproduce
`pip install -r requirements.txt`, put the 14 CSVs in `./data` (or attach the Kaggle dataset), Run All, then `python report/build_report.py`. Outputs: `outputs/*.csv` (tables), `outputs/figures/` (37 figures), `codebooks/` (4 codebooks).
