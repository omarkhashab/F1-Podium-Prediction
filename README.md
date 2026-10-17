# Formula 1 Podium Prediction — CSEN 903 Milestone 1

Predict, for every driver in every race, whether they finish on the podium (`positionOrder <= 3`) using only what is known **after qualifying and before the race starts**. The project covers the full pipeline: audit and cleaning of the 14-table Ergast/Kaggle F1 dataset (1950–2024), three data-engineering questions, a leakage-safe one-row-per-driver-race modelling table, model comparison, experiments, explainability and an inference function.

**Team:** Omar Osama · Mohamed Ayman · Moataz Ashraf · Omar Emad

| Deliverable | Where |
|---|---|
| Run-all notebook | [`F1_Podium_Prediction.ipynb`](F1_Podium_Prediction.ipynb) |
| PDF report | [`report/F1_Podium_Prediction_Report.pdf`](report/F1_Podium_Prediction_Report.pdf) |
| Project flow + every Milestone 1 deliverable with its results | [`PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) |
| Every decision, with the numbers behind it | [`DECISION_LOG.md`](DECISION_LOG.md) |
| Kaggle notebook | *add the link after uploading* |

## Headline results
- **Split** (course guide boundaries): train 2006–2019, validation 2020–21, test 2022–24 — the test set is the whole ground-effect regulation era.
- **Final model:** logistic regression (the simplest model within 0.005 of the best validation PR-AUC). On the unseen test seasons: **PR-AUC 0.698**, ROC-AUC 0.934, F1 0.690, versus 0.647 PR-AUC for ranking by starting grid. Random forest, gradient boosting and shallow neural networks are statistically indistinguishable from it (race-bootstrap intervals).
- **Data questions:** front-row conversion rankings change after 2014; no home-race advantage once grid position is controlled for (Mantel–Haenszel OR 0.95, 95 % CI 0.80–1.13); mechanical-retirement rates roughly halve from 2014–21 to 2022–24.

## Repository layout
```
F1_Podium_Prediction.ipynb   the notebook (audit → cleaning → Q1–Q3 → features → models → experiments → XAI → inference)
data/                        the 14 raw CSVs (never modified; the notebook works on copies)
codebooks/                   status groups, constructor lineage, nationality/country ISO codes (written by the notebook)
outputs/                     every table the notebook writes (model_comparison.csv, ablation.csv, ...)
outputs/figures/             every figure the notebook writes
report/                      build_report.py and the generated PDF
```

## How to run
**Locally**
```bash
pip install -r requirements.txt
jupyter nbconvert --to notebook --execute --inplace F1_Podium_Prediction.ipynb   # or Run All in Jupyter (~8 min on a laptop CPU)
python report/build_report.py                                                     # regenerates the PDF from outputs/
```
The notebook finds the CSVs in `./data` (or set `F1_DATA_DIR`). A fresh run reproduces every table in `outputs/` exactly.

**On Kaggle:** attach the dataset *Formula 1 World Championship (1950–2024)* (rohanrao) — or upload this repo's `data/` folder as a dataset so the numbers match exactly — turn **Internet ON** (Settings → Internet) so `shap` and `lime` can be installed if missing, then Run All. The input folder is detected automatically.
