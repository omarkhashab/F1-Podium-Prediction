"""Build the Milestone 1 PDF report from the notebook's outputs.

Usage (from the repo root, after a full Run All of F1_Podium_Prediction.ipynb):
    python report/build_report.py
Tables are read from outputs/*.csv and figures from outputs/figures/, so the report always matches the notebook.
"""
from pathlib import Path
from datetime import date

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

ROOT = Path(__file__).resolve().parents[1]
OUT, FIG = ROOT / "outputs", ROOT / "outputs" / "figures"
PDF = ROOT / "report" / "F1_Podium_Prediction_Report.pdf"

TEAM = ["Omar Osama (58-7197)", "Mohamed Ayman (58-13475)",
        "Moataz Ashraf (58-7852)", "Omar Emad (58-14543)"]
REPO = "github.com/omarkhashab/F1-Podium-Prediction"

# ---- fonts: Arial has the glyphs we need (≈ ≥ ρ → −); fall back to Helvetica elsewhere ----------------------
FONT, BOLD, ITAL = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
for cand in [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/msttcorefonts")]:
    if (cand / "arial.ttf").exists():
        pdfmetrics.registerFont(TTFont("Arial", str(cand / "arial.ttf")))
        pdfmetrics.registerFont(TTFont("Arial-Bold", str(cand / "arialbd.ttf")))
        pdfmetrics.registerFont(TTFont("Arial-Italic", str(cand / "ariali.ttf")))
        pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold", italic="Arial-Italic")
        FONT, BOLD, ITAL = "Arial", "Arial-Bold", "Arial-Italic"
        break

NAVY = colors.HexColor("#1F3A5F")
GREY = colors.HexColor("#5A6270")
RULE = colors.HexColor("#C9CED6")
TINT = colors.HexColor("#EEF2F7")

ss = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("title", fontName=BOLD, fontSize=21, leading=26, textColor=NAVY, alignment=TA_CENTER),
    "sub": ParagraphStyle("sub", fontName=FONT, fontSize=11.5, leading=15, textColor=GREY, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=14, leading=18, textColor=NAVY, spaceBefore=12, spaceAfter=5),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=11.5, leading=15, textColor=NAVY, spaceBefore=8, spaceAfter=3),
    "body": ParagraphStyle("body", fontName=FONT, fontSize=9.6, leading=13.4, spaceAfter=5),
    "bullet": ParagraphStyle("bullet", fontName=FONT, fontSize=9.6, leading=13.2, leftIndent=12, bulletIndent=2,
                             spaceAfter=2.5),
    "cap": ParagraphStyle("cap", fontName=ITAL, fontSize=8.4, leading=11, textColor=GREY, spaceBefore=2, spaceAfter=9),
    "cell": ParagraphStyle("cell", fontName=FONT, fontSize=8.2, leading=10.2),
    "cellb": ParagraphStyle("cellb", fontName=BOLD, fontSize=8.2, leading=10.2, textColor=colors.white),
    "box": ParagraphStyle("box", fontName=FONT, fontSize=9.6, leading=13.4),
}


def P(text, style="body"):
    return Paragraph(text, S[style])


def bullets(items):
    return [Paragraph(t, S["bullet"], bulletText="•") for t in items]


def img(name, width_cm):
    path = FIG / f"{name}.png"
    w, h = ImageReader(str(path)).getSize()
    return Image(str(path), width=width_cm * cm, height=width_cm * cm * h / w)


def fig(name, width_cm, caption):
    path = FIG / f"{name}.png"
    w, h = ImageReader(str(path)).getSize()
    width = width_cm * cm
    width = min(width, 21.5 * cm * w / h)          # keep tall figures (plus caption) on one page
    img = Image(str(path), width=width, height=width * h / w)
    return KeepTogether([img, P(caption, "cap")])


def table(rows, widths_cm, header=True, align_right_from=None, zebra=True):
    data = [[Paragraph(str(c), S["cellb" if (header and i == 0) else "cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * cm for w in widths_cm], repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, RULE), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    if zebra:
        for i in range(1 if header else 0, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), TINT))
    t.setStyle(TableStyle(style))
    return t


def box(paragraphs):
    t = Table([[paragraphs]], colWidths=[17 * cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), TINT), ("BOX", (0, 0), (-1, -1), 0.8, NAVY),
                           ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                           ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return t


f3 = lambda x: f"{x:.3f}"

pct = lambda x: f"{100 * x:.1f}%"

# ---- data from the notebook outputs -----------------------------------------------------------------------------
MC = pd.read_csv(OUT / "model_comparison.csv", header=[0, 1], index_col=0)
SC = pd.read_csv(OUT / "scope_comparison.csv", index_col=0)
AB = pd.read_csv(OUT / "ablation.csv", index_col=[0, 1])
PE = pd.read_csv(OUT / "preprocessing_experiments.csv")
Q2S = pd.read_csv(OUT / "q2_sensitivity.csv", index_col=0)
TH = pd.read_csv(OUT / "threshold_strategy.csv", index_col=0)
FS = pd.read_csv(OUT / "feature_selection.csv")
EV = pd.read_csv(OUT / "feature_evidence.csv").set_index("feature")
PI = pd.read_csv(OUT / "permutation_importance.csv", index_col=0).sort_values("mean", ascending=False)
Q3 = pd.read_csv(OUT / "q3_mechanical_rates.csv")
Q3ID = pd.read_csv(OUT / "q3_by_constructor_id.csv")
BOOT = pd.read_csv(OUT / "bootstrap_ci.csv").set_index(["split", "model"])
SPL = pd.read_csv(OUT / "split_sensitivity.csv", index_col=[0, 1])
FW = pd.read_csv(OUT / "form_window_experiment.csv", index_col=0)
LIN = pd.read_csv(OUT / "lineage_experiment.csv", index_col=0)
FSE = pd.read_csv(OUT / "feature_set_experiment.csv", index_col=0)
CAL = pd.read_csv(OUT / "calibration_experiment.csv", index_col=0)
INF = pd.read_csv(OUT / "inference_demo.csv", index_col=0)
TNN = pd.read_csv(OUT / "tuning_nn.csv")
TGB = pd.read_csv(OUT / "tuning_gb.csv")
TRF = pd.read_csv(OUT / "tuning_rf.csv")

m = lambda model, metric, split: MC.loc[model, (metric, split)]
SIMPLICITY = ["lr_baseline", "lr_tuned", "rf_default", "rf_tuned", "gb_tuned", "ffnn", "ffnn_tuned"]
best_val = max(m(k, "pr_auc", "val") for k in SIMPLICITY)
FINAL = next(k for k in SIMPLICITY if m(k, "pr_auc", "val") >= best_val - 0.005)
NAMES = {"ref_grid_rule": "Grid rule (reference)", "lr_baseline": "Logistic regression, C = 1",
         "lr_tuned": "Logistic regression, tuned", "rf_default": "Random forest, default",
         "rf_tuned": "Random forest, tuned", "gb_tuned": "Gradient boosting, tuned",
         "ffnn": "Shallow NN, starting architecture", "ffnn_tuned": "Shallow NN, tuned"}
ab = lambda model, removed, col: AB.loc[(model, removed), col]
FULLROW = "(none — full model)"
b = lambda split, model, col: BOOT.loc[(split, model), col]
rf_best, gb_best, nn_best = TRF.iloc[0], TGB.iloc[0], TNN.iloc[0]

story = []

# =================================================================================================================
# Title + summary
# =================================================================================================================
story += [Spacer(1, 1.2 * cm), P("Formula 1 Podium Prediction", "title"), Spacer(1, 4),
          P("Milestone 1 — Data engineering, leakage-safe modelling and explainability", "sub"), Spacer(1, 10),
          P("CSEN 903 Advanced Computer Lab · German University in Cairo · Winter 2026", "sub"),
          *[P(member, "sub") for member in TEAM],
          P(f"{date(2026, 10, 18).strftime('%d %B %Y')} · code: {REPO}", "sub"), Spacer(1, 16)]

story.append(box([P("<b>Summary</b>", "box"), Spacer(1, 3)] + bullets([
    "<b>Task:</b> for every driver in every race, predict a podium finish (<i>positionOrder</i> ≤ 3) using only "
    "information available after qualifying and before the start.",
    "<b>Data:</b> the 14-table Ergast / Kaggle dataset (1950–2024), cleaned into one leakage-safe row per "
    "(race, driver). Raw files are never modified; every cleaning rule is logged and asserted.",
    f"<b>Model:</b> logistic regression reaches <b>test PR-AUC {f3(m(FINAL, 'pr_auc', 'test'))}</b> "
    f"(ROC-AUC {f3(m(FINAL, 'roc_auc', 'test'))}, F1 {f3(m(FINAL, 'f1', 'test'))}) on the unseen 2022–24 seasons, "
    f"a new regulation era. Ranking by starting grid scores {f3(m('ref_grid_rule', 'pr_auc', 'test'))}. A random "
    "forest, gradient boosting and a shallow neural network are statistically indistinguishable from it "
    "(race-bootstrap intervals), so the simplest model is kept.",
    f"<b>What drives predictions:</b> the starting position. Removing grid and qualifying together costs "
    f"{-ab(FINAL, 'grid + qualifying (starting position)', 'Δval_pr_auc'):.3f} validation PR-AUC (95% CI excludes 0); "
    "standings, form and pace each add little on top of it.",
    "<b>Data questions:</b> front-row conversion rankings change after 2014 (Spearman ρ = 0.21); "
    "there is no home-race advantage once grid position is controlled for (odds ratio 0.95, 95% CI 0.80–1.13); "
    "mechanical-retirement rates roughly halve from 2014–21 to 2022–24.",
]), ))

# =================================================================================================================
# 1. Task and data
# =================================================================================================================
story += [P("1. Task and data", "h1"),
          P("The unit of analysis is one driver entering one race, and the target is a podium finish. The prediction "
            "is made at a fixed <b>cutoff</b>: after the starting grid is known and before the race starts. Results, "
            "points, status, laps, pit stops, lap times and post-race standings of the current race are only known "
            "after it, so using them as features would be <b>data leakage</b>. Every feature in this project is "
            "either known at the cutoff (qualifying, grid, sprint result) or computed only from earlier races."),
          P("The dataset is relational. Most questions need multi-hop joins, e.g. results joined with races, circuits, "
            "drivers, status and qualifying. All work is in one run-all notebook (<i>F1_Podium_Prediction.ipynb</i>), "
            "which runs top to bottom without manual steps and produces every table and figure in this report. "
            "A fresh re-run reproduces every output table exactly.")]

# =================================================================================================================
# 2. Audit and cleaning
# =================================================================================================================
story += [P("2. Data audit and cleaning", "h1"), P("2.1 Audit and EDA before cleaning", "h2")]
story += bullets([
    "<b>Sentinels.</b> Missing values are stored as the literal text <i>\\N</i> (Figure 1). They are concentrated in "
    "<i>structural</i> columns (session times recorded only from 2021, fastest-lap data from 2004) and "
    "<i>outcome</i> columns (<i>results.time</i> 71% missing for drivers not on the lead lap, <i>position</i> 41% "
    "for non-classified drivers). Only <i>q2/q3</i> are missing for a pre-race reason: the driver was knocked out.",
    "<b>Keys.</b> All primary keys are unique and non-null and every foreign key resolves. The one violation is "
    "the required grain: 176 result rows form 85 duplicated (race, driver) pairs. These are 1950s shared drives, "
    "where drivers swapped cars mid-race (Figure 2).",
    "<b>Coverage drift.</b> Qualifying rows exist from 1994 but cover only 6–59% of entries in 1996–2002. They are "
    "complete from 2003 (Figure 3). Lap times start in 1996, pit stops in 2011 and sprints in 2021.",
    "<b>Formats and categories.</b> Durations appear as <i>m:ss.sss</i>, <i>mm:ss.sss</i> and "
    "<i>h:mm:ss.sss</i>, and <i>results.time</i> mixes absolute times with gaps (22 formats). There are spelling "
    "issues ('Argentinian ' with a trailing space, 'USA' vs 'United States') and one HTML entity.",
])
story.append(fig("audit_sentinels_heatmap", 15.5, "Figure 1 — Share of '\\N' / empty sentinels per column (raw data)."))
story.append(fig("audit_duplicates_per_year", 15.5, "Figure 2 — Duplicate (raceId, driverId) rows per season: "
                 "almost all in the 1950s (shared drives)."))
story.append(fig("eda_raw_quali_coverage", 15.5,
                 "Figure 3 — Share of race entries with a qualifying row, per season (raw data). Coverage is "
                 "complete only from 2003, which motivates the 2006+ modelling scope."))

story.append(P("2.2 Cleaning pipeline and decisions", "h2"))
story.append(P("Cleaning works on copies of the raw tables; a hash check confirms the raw data is unchanged at the "
               "end. Each rule writes a row to <i>outputs/cleaning_log.csv</i>, and key, grain and foreign-key "
               "assertions run after every step that changes rows. Cleaning runs on <b>all seasons</b>, so the "
               "history features of a 2006 race can still use 2005. The modelling scope only selects rows "
               "afterwards. Table 1 lists the decisions."))
decisions = [
    ["#", "Decision", "Rule and justification", "Effect"],
    ["F", "Sentinels, typing", "strip, HTML-unescape, sentinels → NaN; IDs Int64, dates, durations → seconds. "
     "Missing values after typing must equal sentinels before (asserted).", "0 parse failures"],
    ["D1", "Seasons", "Model on 2006–2024 (knockout qualifying, complete data); 1950–2024 kept as a comparison "
     "trial (Section 7).", "7,905 model rows"],
    ["D2", "Non-starters", "Drop entries with no grid slot (DNQ, DNPQ, 107% rule; withdrew/excluded with grid 0). "
     "Keep 'Withdrew' with a grid slot: they were prediction rows at the cutoff.", "−1,535 rows (9 in 2006+)"],
    ["D3", "Shared drives", "Merge to one row per (race, driver): pre-race fields from the car the driver started "
     "in (earliest resultId); podium if any of his cars made the podium; points summed.", "125 → 61 rows"],
    ["D4", "Indianapolis 500", "Excluded (1950–60): separate set of drivers, 33-car grid, distorts the home-race "
     "analysis.", "11 races"],
    ["D5", "grid = 0", "2006+: pit-lane start → field size + 1, plus a flag. Pre-2006: slot unknown → NaN, plus a "
     "flag. Left as 0, a pit-lane start would look better than pole.", "77 / 45 rows"],
    ["D6", "Missing features", "Domain fill where the true value is known (debutant = 0 starts; first visit to a "
     "circuit = NaN + flag), then the training-set median plus missing-indicator columns.", "11,360 / 12,516 cells"],
    ["D7", "Round-1 standings", "Use last season's final standings (renamed teams matched by lineage) plus an "
     "is_round_1 flag.", "75 races"],
    ["D8", "Timing outliers", "Hard limits only: pit stop outside [1.5 s, 120 s]; qualifying time > 2× session "
     "median. A robust z-score would also remove genuine slow stops (13%).", "482 cells → NaN"],
    ["D9", "Lap cleaning", "Remove lap 1, pit in/out laps and laps > 107% of the race median; pace = driver "
     "median ÷ best median. Used only from earlier races.", "513,483 of 589,081 laps"],
    ["D10", "Target", "podium = positionOrder ≤ 3 after D3; every modern race has exactly 3 podiums "
     "(asserted).", "375 races checked"],
    ["D11", "Status codebook", "All 139 status labels mapped to finished / lapped / mechanical / incident / "
     "non-start / disqualified / ambiguous.", "57 mechanical, 30 ambiguous"],
    ["D12", "Constructor lineage", "Renamed teams grouped into families (e.g. Minardi → Toro Rosso → AlphaTauri → "
     "RB), with year ranges for IDs reused by unrelated teams. Tested against plain IDs (Section 7.5).",
     "37 rules, 11 families"],
    ["D13", "Standings", "No raw points: championship rank and share of the leader's points, which are comparable "
     "across scoring systems.", "—"],
    ["D14", "Sprints", "Sprint finish (known before the race) as a feature, 2021+.", "18 weekends"],
    ["D15", "Countries", "Nationalities and circuit countries → ISO-3166 codes; zero unmapped (asserted).",
     "43 + 35 values"],
    ["D16", "Abnormal races", "race_shortened flag (laps and race time < 75% of normal, or half points). For error "
     "analysis only, never a feature.", "7 races"],
]
story.append(table(decisions, [1.0, 2.6, 10.3, 3.1]))
story.append(P("Table 1 — Cleaning decisions. F = fixed steps. Full counts are in "
               "<i>outputs/decision_summary.csv</i>.", "cap"))

story.append(P("2.3 Effect of cleaning (EDA after cleaning)", "h2"))
story += bullets([
    "<i>results</i> goes from 26,759 to 24,755 rows: −405 rows from the Indy 500, −1,535 non-starters, −64 from "
    "merged shared drives (Figure 4). All key, grain and foreign-key checks pass after every step.",
    "Missing shares in the original columns barely change (results 22.8% → 21.9%). Cleaning converts sentinels "
    "into real missing values; it does not invent or fill values. Filling is done per feature (D6), with the "
    "median fitted on the training split only.",
    "Outlier removal targets data errors: the 481 removed pit stops include ~51-minute red-flag suspensions, and "
    "the one qualifying time removed is 16:42.640 (Figure 5).",
    "<b>Class imbalance:</b> 14.2% of rows in the modelling scope are podiums (train 13.9%, validation and test "
    "15.0%). This drives the metric choice in Section 6.",
])
story.append(fig("cleaning_before_after", 16.0, "Figure 4 — Rows per table (log scale) and missing cells before vs "
                 "after cleaning."))
story.append(fig("cleaning_outliers_before_after", 16.5,
                 "Figure 5 — Timing distributions before and after outlier handling (log counts). Left: pit-stop "
                 "duration. Middle and right: Q1 time relative to the session median."))

# =================================================================================================================
# 3. Data-engineering questions
# =================================================================================================================
story += [P("3. Data-engineering questions", "h1"),
          P("Q1 — Which circuits convert a front-row start into a podium most often, and does the ranking change "
            "after 2014?", "h2")]
story += bullets([
    "<b>Answer.</b> In 2014–2024 the best converters are Suzuka (89%, 16/18), Yas Marina (86%) and Monaco (85%). "
    "In 2003–2013 they are Magny-Cours (92%), Monaco and Monza (≈ 77%).",
    "<b>The ranking changes.</b> For the 15 circuits with at least 8 front-row starts in both eras, the Spearman "
    "rank correlation between eras is 0.21 (p = 0.46) using the grid and 0.50 (p = 0.06) using qualifying. Monza "
    "falls from joint first to eleventh; Yas Marina and Interlagos rise. Conversion increases almost everywhere "
    "after 2014: in the Mercedes and Red Bull years the front row was usually the fastest car.",
    "<b>Grid vs qualifying.</b> 74 entries (8.6% of qualifying front rows) differ between the two definitions, "
    "because penalties and pit-lane starts move drivers off the front row. Figures 6 and 7 show both rankings; the "
    "qualifying-based ranking is the more stable one across eras (0.50 vs 0.21).",
    "<b>Grain, missingness, cutoff.</b> One row per (race, driver), filtered to front-row starters. Only "
    "2003–2024 is used, where qualifying is complete. Grid and qualifying position are both known before the "
    "start. With 8–22 starts per circuit and era, one podium moves a rate by 5–12 points.",
])
story.append(fig("q1_front_row_grid", 16.5, "Figure 6 — Front-row conversion by circuit using the <b>grid</b> "
                 "(after penalties), 2003–13 vs 2014–24, and the change in rank between eras."))
story.append(fig("q1_front_row_qualifying", 16.5, "Figure 7 — The same using the <b>qualifying</b> position "
                 "(before penalties)."))

story.append(P("Q2 — Do drivers reach the podium more often at home, controlling for starting position?", "h2"))
story.append(P("A home race means the driver's nationality and the circuit's country map to the same ISO code "
               "(D15). Drivers are compared within six grid strata (pole, P2–3, P4–6, P7–10, P11–15, P16+), and "
               "the strata are pooled with a Mantel–Haenszel odds ratio."))
q2rows = [["Period", "Starters", "Home", "Crude OR", "Grid-adjusted OR", "95% CI"]]
for period, r in Q2S.iterrows():
    q2rows.append([period, f"{int(r.entries):,}", f"{int(r.home_entries):,}", f"{r.crude_OR:.2f}",
                   f"<b>{r.MH_OR:.2f}</b>", f"{r.CI_low:.2f}–{r.CI_high:.2f}"])
story.append(table(q2rows, [3.6, 2.2, 1.8, 2.2, 3.2, 2.6]))
story.append(P("Table 2 — Home vs away podium odds. An OR above 1 would mean a home advantage.", "cap"))
story += bullets([
    "<b>Answer: no home advantage.</b> Home entries look worse overall (crude OR 0.84), but only because many home "
    "entries are one-off local drivers starting near the back. Within grid strata the effect disappears "
    "(OR 0.95, 95% CI 0.80–1.13), and the conclusion holds in every period.",
    "<b>Grain and missingness.</b> One row per starter with a known grid slot (24,710 rows, 1,941 home); zero "
    "unmapped nationalities. <b>Limitation:</b> nationality is not always where a driver grew up, and there are "
    "only 82 home entries on pole.",
])
story.append(fig("q2_home_vs_away_by_grid", 11.5, "Figure 8 — Podium rate at home vs away within grid strata."))

story.append(P("Q3 — Which constructors have the highest mechanical-retirement rate in 2014–2021 vs 2022–2024?",
               "h2"))
story.append(P("A mechanical retirement is a race start that ended because a car component failed. The status "
               "codebook (D11) defines it; ambiguous labels such as 'Retired', 'Puncture' and 'Wheel' are counted "
               "both ways: (a) not mechanical, (b) mechanical. The denominator is race starts, excluding drivers "
               "who withdrew after taking a grid slot. Table 3 groups renamed teams (D12) and labels each by its "
               "latest name in the era plus its family; Table 4 gives the same rates per constructor ID."))
q3a = Q3[Q3.variant == "a_mech_only"]
q3rows = [["Era", "Highest rates (variant a)", "Lowest rate", "Spearman (a) vs (b)"]]
for era, rho in [("2014-2021", "0.95"), ("2022-2024", "0.85")]:
    d = q3a[q3a.era == era].sort_values("rate", ascending=False)
    top = ", ".join(f"{r.label} {pct(r.rate)}" for r in d.head(4).itertuples())
    low = d.iloc[-1]
    q3rows.append([era.replace("-", "–"), top, f"{low.label} {pct(low.rate)}", rho])
story.append(table(q3rows, [2.0, 9.6, 3.2, 2.2]))
story.append(P("Table 3 — Mechanical-retirement rate per start, teams grouped by lineage (≥ 20 starts per era).",
               "cap"))
idrows = [["Era", "Highest rates per constructor ID (variant a)"]]
for era, d in Q3ID.groupby("era"):
    idrows.append([era.replace("-", "–"), ", ".join(f"{r.constructor} {pct(r.rate)} ({r.mech_dnf}/{r.starts})"
                                                    for r in d.head(5).itertuples())])
story.append(table(idrows, [2.0, 15.0]))
story.append(P("Table 4 — The same per constructorId (renamed teams split). The leaders are the same teams.", "cap"))
story += bullets([
    "<b>Answer.</b> 2014–21 is led by Caterham, Toro Rosso / AlphaTauri, McLaren (the McLaren-Honda years) and "
    "Lotus / Renault, with Mercedes the most reliable (3.8%). In 2022–24 Alpine and Alfa Romeo / Sauber lead, "
    "Aston Martin is the most reliable, and rates roughly halve across the field.",
    "<b>Robustness.</b> Counting ambiguous statuses as mechanical changes little: rank correlation 0.95 and 0.85, "
    "and the top team in each era is unchanged. Wilson 95% intervals (Figure 9) overlap for differences under "
    "about 4 points.",
])
story.append(fig("q3_mechanical_dnf_rate", 16.5,
                 "Figure 9 — Mechanical-retirement rate per team with 95% intervals; orange = mechanical only, "
                 "grey = including ambiguous statuses."))

# =================================================================================================================
# 4. Modelling table and features
# =================================================================================================================
story += [P("4. Modelling table and features", "h1"),
          P("The modelling table has exactly one row per (race, driver): 7,905 rows for 2006–2024 (asserted unique). "
            "Features are written to an explicit allowed list; the table may only contain listed features, IDs "
            "and the target. Table 5 lists the 26 selected features and why each is valid at the cutoff.")]
VALID = {
    "grid": "Known once the grid is fixed (qualifying + penalties).",
    "qualifying": "Qualifying ends before the race.",
    "standings": "Standings after the <b>previous</b> round; round 1 uses last season's final standings.",
    "driver_form": "Rolling over the driver's previous 5 races (shift by one race).",
    "constructor_form": "Rolling over the team family's previous 5 races, aggregated per race first.",
    "pace_pit": "Clean-lap pace and pit-crew speed from <b>earlier</b> races only; pit data exists from 2011.",
    "experience": "Counts and rates over earlier races; age at race date.",
}
kept = FS[FS.kept]
frows = [["Group", "Selected features", "Valid at the cutoff because"]]
for g, d in kept.groupby("group", sort=False):
    frows.append([g.replace("_", " "), ", ".join(f"<i>{f}</i>" for f in d.feature), VALID[g]])
story.append(table(frows, [2.6, 8.2, 6.2]))
story.append(P("Table 5 — Selected features by group.", "cap"))

story.append(P("Leakage control", "h2"))
story += bullets([
    "Form, points-share, pace and pit features use only races dated before the race being predicted. An "
    "independent recomputation for 300 random rows matches the vectorised features exactly.",
    "A second, independent check: the inference function rebuilds all features from raw inputs using only races "
    "dated before the entry, and reproduces the modelling table for 300 random validation/test entries.",
    "Standings come from a race dated earlier, asserted for every row; round-1 standings come from the previous "
    "season. Raw championship points are never used (D13).",
    "Imputer and scaler are fitted on the training seasons only; the test set is scored once, after every choice "
    "was fixed on validation. The inference function rejects post-race fields such as <i>points</i>.",
])

story.append(P("Feature selection", "h2"))
story.append(P("Selection uses the <b>training seasons only</b> (2006–2019), so validation and test never influence "
               "it. Rule 1 drops features that are empty or constant in training; rule 2 visits features by "
               "univariate AUC, highest first, and drops any whose |Spearman ρ| with an already-kept feature is "
               "≥ 0.95. Of 36 candidates, 26 are kept. The strongest single features are "
               f"<i>quali_pos</i> (univariate AUC {EV.loc['quali_pos', 'univariate_auc']:.2f}), "
               f"<i>gap_to_pole_pct</i> ({EV.loc['gap_to_pole_pct', 'univariate_auc']:.2f}), "
               f"<i>drv_pts_frac_lastN</i> ({EV.loc['drv_pts_frac_lastN', 'univariate_auc']:.2f}) and "
               f"<i>con_gap_to_leader_share</i> ({EV.loc['con_gap_to_leader_share', 'univariate_auc']:.2f}). "
               "Figure 10 shows the podium rate across the values of every candidate. A controlled check (Section 7.6) confirms the rule costs no accuracy."))
drows = [["Dropped feature", "Reason (training seasons 2006–2019)"]]
for r in FS[~FS.kept].itertuples():
    drows.append([f"<i>{r.feature}</i>", r.reason_dropped.replace("rho", "ρ")])
story.append(table(drows, [4.6, 12.4]))
story.append(P("Table 6 — Dropped candidates. <i>grid</i> is not lost: it equals <i>quali_pos + "
               "grid_minus_quali</i>, both kept. The sprint features cannot be learned because sprints start in "
               "2021 and training ends in 2019.", "cap"))
story.append(fig("features_univariate_podium_rate", 16.8, "Figure 10 — Podium rate across feature values "
                 "(deciles, training seasons): the evidence behind each feature."))

# =================================================================================================================
# 5. Split and preprocessing
# =================================================================================================================
story += [P("5. Split and preprocessing", "h1"),
          P("Rows are not independent: form carries over between races and the sport drifts from season to season. "
            "We therefore split <b>by season</b>, with the boundaries from the course's F1 guide: train 2006–2019 "
            "(5,768 rows, 268 races), validation 2020–21 (780 rows, 39 races), test 2022–24 (1,357 rows, 68 races). "
            "Podium rates are 13.9%, 15.0% and 15.0%. The test set is the whole ground-effect era (new car rules "
            "from 2022), so it measures how a model trained on the hybrid era carries over to a regulation change; "
            "validation never sees the new era. The previous split (test 2023–24) is reported as a sensitivity "
            "check in Section 7.2."),
          P("Preprocessing is median imputation with missing-value indicators, followed by standardisation (tree "
            "models skip scaling); Figure 11 shows the effect on the distributions. Table 7 reports three "
            "controlled experiments; only the preprocessing changes, with the same logistic regression and "
            "features each time.")]
story.append(fig("preprocessing_effect", 16.8, "Figure 11 — Five features before (top) and after (bottom) "
                 "imputation and scaling."))
perows = [["Experiment", "Variant", "Val PR-AUC", "Val ROC-AUC", "Val F1"]]
for r in PE.itertuples():
    perows.append([r.experiment, r.variant.replace("_", " "), f"{r.pr_auc:.4f}", f"{r.roc_auc:.4f}", f"{r.f1:.4f}"])
story.append(table(perows, [3.2, 5.6, 2.6, 2.6, 2.4]))
story.append(P("Table 7 — Preprocessing experiments (validation; F1 at the validation-chosen threshold).", "cap"))
pe = PE.set_index("variant").pr_auc
story += bullets([
    f"<b>E1, order:</b> impute → scale {pe['impute_then_scale']:.4f} vs scale → impute "
    f"{pe['scale_then_impute']:.4f}. Only about 2.7% of cells are imputed; scaling first places the imputed value "
    "at the median of the scaled column, so the difference is small.",
    f"<b>E2, fit scope:</b> fitting the preprocessing on all data, including validation and test, brings no gain "
    f"({pe['fit on all data (leaky)']:.4f} vs {pe['fit on train only']:.4f}) and would be leakage, so it is fitted "
    "on train only.",
    f"<b>E3, missing indicators</b> help (+{pe['add_indicator=True'] - pe['add_indicator=False']:.3f} PR-AUC). "
    "Being missing is informative: no previous standings means a debutant or a new team, and no pit data means "
    "before 2011.",
])

# =================================================================================================================
# 6. Models
# =================================================================================================================
story += [P("6. Models and evaluation", "h1"), P("6.1 Models: how they work and their limitations", "h2")]
story += bullets([
    "<b>Reference rule</b> (not learned): score = 1 / grid position. Every model must beat it.",
    "<b>Logistic regression (baseline).</b> A weighted sum of the standardised features passed through a sigmoid, "
    "fitted by minimising the log-loss with an L2 penalty; class weights counter the 14% positive rate. Simple and "
    "interpretable, but only additive linear effects, and correlated features share their weights. Tuned over C.",
    "<b>Random forest.</b> Many decision trees on bootstrap samples with random feature subsets; their votes are "
    "averaged. Captures interactions without scaling, but deep trees memorise the training seasons. Tuned over "
    f"depth × leaf size (best: depth {int(rf_best.max_depth) if pd.notna(rf_best.max_depth) else 'None'}, "
    f"leaf {int(rf_best.min_samples_leaf)}).",
    "<b>Gradient boosting</b> (histogram-based). Shallow trees built one after another, each fitted to the errors of "
    "the previous ones with a small learning rate. Usually the strongest tabular model, but more hyperparameters "
    f"and easy to overfit. Tuned over learning rate × depth × leaf (best: {gb_best.learning_rate:g}, depth "
    f"{int(gb_best.max_depth)}, leaf {int(gb_best.min_samples_leaf)}).",
    "<b>Shallow neural network.</b> One or two ReLU hidden layers and a sigmoid output, trained with Adam on "
    "class-weighted cross-entropy, with dropout, L2 and early stopping on validation PR-AUC. Starting architecture "
    f"32-16 with dropout 0.2; six architectures tried; best: {nn_best.architecture} "
    f"({int(nn_best.weights):,} weights). Limitations: stochastic, needs scaling, hard to interpret.",
])
story.append(fig("tuning_nn", 11.0, "Figure 12 — Neural-network architectures: train vs validation PR-AUC."))

story.append(P("6.2 Results on training, validation and test", "h2"))
order = ["ref_grid_rule", "lr_baseline", "lr_tuned", "rf_default", "rf_tuned", "gb_tuned", "ffnn", "ffnn_tuned"]
for split, tno in [("val", 8), ("test", 9)]:
    rows = [["Model", "ROC-AUC", "PR-AUC", "F1", "Precision", "Recall", "PR-AUC train"]]
    for k in order:
        r = [f3(m(k, x, split)) for x in ["roc_auc", "pr_auc", "f1", "precision", "recall"]] + [f3(m(k, "pr_auc", "train"))]
        label = NAMES[k]
        if k == FINAL:
            r, label = [f"<b>{x}</b>" for x in r], f"<b>{label} (final)</b>"
        rows.append([label] + r)
    story.append(table(rows, [5.4, 1.9, 1.9, 1.9, 1.9, 1.9, 2.1]))
    story.append(P(f"Table {tno} — All five metrics on the <b>{'validation' if split == 'val' else 'unseen test'}"
                   f"</b> seasons ({'2020–21' if split == 'val' else '2022–24'}); same rows and the same 26 features for "
                   "every model. F1, precision and recall use the threshold chosen on validation.", "cap"))
story.append(fig("val_roc_pr_curves", 15.0, "Figure 13 — ROC and precision–recall curves on validation."))

story.append(P("6.3 Metric choice, threshold and model selection", "h2"))
story += bullets([
    "<b>Primary metric: PR-AUC.</b> Podiums are a minority (14–15%), and the task is ranking podium finishers above "
    "everyone else. ROC-AUC is inflated by the many easy back-of-grid entries: it is ≈ 0.93 for every model and "
    "0.91 even for the grid rule, so it barely separates the models.",
    "<b>Secondary metric: F1</b> at a probability threshold chosen on validation: the quality of the actual yes/no "
    f"prediction. The F1-maximising threshold was at least as good as 'exactly 3 podiums per race' for every model "
    f"(logistic regression: {TH.loc[FINAL, 'val_f1_max_f1_threshold']:.3f} vs "
    f"{TH.loc[FINAL, 'val_f1_top3_per_race']:.3f}).",
    f"<b>Model selection</b> (validation only): the simplest model within 0.005 of the best validation PR-AUC. "
    f"Logistic regression with C = 1 ({f3(m('lr_baseline', 'pr_auc', 'val'))}) ties the tuned C = 10 "
    f"({f3(m('lr_tuned', 'pr_auc', 'val'))}) and beats every more complex model, so it is the final model.",
])

story.append(P("6.4 Is the difference real? Race-bootstrap intervals", "h2"))
story.append(P("Validation and test hold only 39 and 68 races, so we resample whole races 1,000 times and compute "
               "95% intervals, including paired intervals for the difference to the final model."))
brows = [["Model", "Val PR-AUC [95% CI]", "Δ vs final (val)", "Test PR-AUC [95% CI]", "Δ vs final (test)"]]
for k in order:
    cells = []
    for s in ["val", "test"]:
        cells += [f"{b(s, k, 'pr_auc'):.3f} [{b(s, k, 'ci_low'):.3f}, {b(s, k, 'ci_high'):.3f}]",
                  "—" if k == FINAL else f"{b(s, k, 'diff_vs_final'):+.3f} [{b(s, k, 'diff_ci_low'):+.3f}, "
                                         f"{b(s, k, 'diff_ci_high'):+.3f}]"]
    brows.append([NAMES[k]] + cells)
story.append(table(brows, [4.6, 3.1, 3.1, 3.1, 3.1]))
story.append(P("Table 10 — PR-AUC with 95% race-bootstrap intervals. A Δ interval that excludes 0 means a real "
               "difference from the final model.", "cap"))
story += bullets([
    f"Only the grid rule ({b('test', 'ref_grid_rule', 'diff_vs_final'):+.3f} on test, interval "
    f"[{b('test', 'ref_grid_rule', 'diff_ci_low'):+.3f}, {b('test', 'ref_grid_rule', 'diff_ci_high'):+.3f}]) and the "
    "default random forest are clearly worse than the final model. Tuned forest, boosting and both networks are "
    "statistically indistinguishable from it, so choosing the simplest model of the tied group is justified.",
    f"<b>Test result.</b> The final model reaches PR-AUC {f3(m(FINAL, 'pr_auc', 'test'))} on 2022–24, "
    f"{m(FINAL, 'pr_auc', 'test') - m('ref_grid_rule', 'pr_auc', 'test'):+.3f} over the grid rule, finding 166 of "
    f"204 podiums with 111 false alarms (precision {f3(m(FINAL, 'precision', 'test'))}, recall "
    f"{f3(m(FINAL, 'recall', 'test'))}).",
    "<b>Across the rule change.</b> Validation → test falls from 0.745 to 0.698. By season: 2022 0.660 (first "
    "ground-effect season), 2023 0.770 (one dominant team), 2024 0.664 (four winning teams). ROC-AUC stays at "
    "0.93–0.95: the model still separates the field, but ordering the front-runners gets harder.",
])
story.append(fig("bootstrap_ci", 16.8, "Figure 14 — PR-AUC with 95% race-bootstrap intervals."))

story.append(P("6.5 Class weighting and calibration", "h2"))
crows = [["Variant (validation)", "PR-AUC", "Brier score", "Mean predicted", "Distinct values"]]
for n, r in CAL.iterrows():
    crows.append([n, f"{r.val_pr_auc:.3f}", f"{r.val_brier:.4f}", f"{r.mean_predicted:.3f}", f"{int(r.distinct_values)}"])
story.append(table(crows, [5.6, 2.4, 2.6, 3.0, 3.0]))
story.append(P("Table 11 — Class weighting and calibration (observed podium rate 0.150). Calibration is scored with "
               "5-fold cross-fitting by race on validation.", "cap"))
story.append(P("Class weighting barely changes the ranking but makes the raw scores over-confident (mean prediction "
               "0.28 for a 15% rate). We keep the weighted model for ranking and thresholding and calibrate its "
               "score with <b>Platt scaling</b> fitted on validation: it is smooth and rank-preserving, while "
               "isotonic regression collapses the scores to 64 values on 780 rows. On test the Brier score falls "
               "from 0.112 (raw) to 0.069 (calibrated); Figure 15, right, shows the calibration curves."))
story.append(fig("test_confusion_pr_calibration", 16.8,
                 "Figure 15 — Test set: confusion matrix of the final model, precision–recall curves of all models "
                 "(dashed = base rate), and calibration of the raw and Platt-calibrated scores."))

# =================================================================================================================
# 7. Experiments
# =================================================================================================================
story += [P("7. Experiments", "h1"), P("7.1 Modern seasons vs all seasons (decision D1)", "h2"),
          P("The same features and settings were trained on 2006–2019 and on 1950–2019 and scored on <b>identical</b> "
            "validation and test rows.")]
srows = [["Training window", "Train rows", "Missing cells", "LR val", "RF val", "NN val", "LR test", "RF test",
          "NN test"]]
for scope, r in SC.iterrows():
    srows.append([f"{scope} ({r.train_seasons})", f"{int(r.train_rows):,}", f"{r.pct_feature_cells_missing:.1f}%",
                  f3(r.LR_val_pr_auc), f3(r.RF_val_pr_auc), f3(r.FFNN_val_pr_auc), f3(r.LR_test_pr_auc),
                  f3(r.RF_test_pr_auc), f3(r.FFNN_test_pr_auc)])
story.append(table(srows, [3.6, 1.7, 2.1, 1.6, 1.6, 1.6, 1.6, 1.6, 1.6]))
story.append(P("Table 12 — PR-AUC by training window (same validation and test rows).", "cap"))
story.append(P("Modern training is better for logistic regression and the random forest on both validation and "
               "test; the neural network is slightly better with all seasons (+0.008). The older data has 21% "
               "missing feature cells (no qualifying before 1994, unknown grid slots, no lap data before 1996) and "
               "different podium patterns (30+ car fields, high retirement rates). All gaps are within the "
               "bootstrap noise, so four times as many rows buys no measurable accuracy; the modern scope is kept "
               "for consistent definitions and the better result of the final model family."))

story.append(P("7.2 Split sensitivity", "h2"))
sprows = [["Split", "Model", "Train rows", "Val PR-AUC", "Test PR-AUC", "Test ROC-AUC", "Test F1"]]
for (split, model), r in SPL.iterrows():
    sprows.append([split.split(":")[0].capitalize(), NAMES.get(model, model), f"{int(r.train_rows):,}",
                   f3(r.val_pr_auc), f3(r.test_pr_auc), f3(r.test_roc_auc), f3(r.test_f1)])
story.append(table(sprows, [3.4, 4.6, 1.6, 1.8, 1.9, 1.9, 1.8]))
story.append(P("Table 13 — The final model and the grid rule under the course split (train ≤ 2019, validation "
               "2020–21, test 2022–24) and the previous split (train ≤ 2020, validation 2021–22, test 2023–24).",
               "cap"))
story.append(P("The model beats the grid rule by +0.05 PR-AUC under both splits. The course split's test score is "
               "lower because its test set starts with 2022, the least predictable season; the previous split had "
               "put 2022 into validation."))

story.append(P("7.3 Feature-group ablation", "h2"))
story.append(P("Each group is removed in turn and the model re-trained with fixed hyperparameters; the threshold is "
               "re-chosen on validation. Done for the final model (95% paired race-bootstrap interval) and the tuned "
               "random forest (mean of 5 seeds ± seed std). One row removes grid and qualifying together, because "
               "grid was dropped as a near-duplicate of the qualifying position."))
abrows = [["Removed group", "LR val PR-AUC", "LR Δ val [95% CI]", "LR Δ test", "RF Δ val (± std)", "RF Δ test"]]
for g in AB.loc[FINAL].index:
    if g == FULLROW:
        abrows.append(["none (full model)", f3(ab(FINAL, g, "val_pr_auc")), "—", "—",
                       f"RF full = {f3(ab('rf_tuned', g, 'val_pr_auc'))}", "—"])
        continue
    abrows.append([g.replace("_", " "), f3(ab(FINAL, g, "val_pr_auc")),
                   f"{ab(FINAL, g, 'Δval_pr_auc'):+.3f} [{ab(FINAL, g, 'Δval_ci_low'):+.3f}, "
                   f"{ab(FINAL, g, 'Δval_ci_high'):+.3f}]", f"{ab(FINAL, g, 'Δtest_pr_auc'):+.3f}",
                   f"{ab('rf_tuned', g, 'Δval_pr_auc'):+.3f} ± {ab('rf_tuned', g, 'Δval_seed_std'):.3f}",
                   f"{ab('rf_tuned', g, 'Δtest_pr_auc'):+.3f}"])
story.append(table(abrows, [4.8, 2.1, 3.6, 1.7, 2.9, 1.9]))
story.append(P("Table 14 — Ablation (negative Δ = the group helps).", "cap"))
story.append(P("Only qualifying and the combined starting position have intervals that exclude 0: removing both costs "
               f"{-ab(FINAL, 'grid + qualifying (starting position)', 'Δval_pr_auc'):.3f} validation PR-AUC "
               f"({-ab(FINAL, 'grid + qualifying (starting position)', 'Δtest_pr_auc'):.3f} on test). Grid, standings, "
               "form, pace and experience each add little on their own, and for the forest removing standings or "
               "experience even helps slightly. Grid, standings and form all have univariate AUC ≈ 0.89–0.92 "
               "(Section 4), but most of that signal overlaps with the starting position: univariate evidence "
               "measures signal, ablation measures <i>unique</i> signal."))
story.append(fig("ablation", 16.8, "Figure 16 — Δ validation PR-AUC when a group is removed: final model (left, "
                 "95% race-bootstrap CI) and tuned random forest (right, ± seed std)."))

story.append(P("7.4 Form window", "h2"))
fwrows = [["Window (races)", "Val PR-AUC", "Δ vs 5 [95% CI]", "Test PR-AUC"]]
for w, r in FW.iterrows():
    fwrows.append([f"{w}{' (chosen)' if r.chosen else ''}", f3(r.val_pr_auc),
                   "—" if r.chosen else f"{r.Δval_vs_chosen:+.3f} [{r.Δ_ci_low:+.3f}, {r.Δ_ci_high:+.3f}]",
                   f3(r.test_pr_auc)])
story.append(table(fwrows, [3.6, 2.6, 4.4, 2.6]))
story.append(P("Table 15 — Every rolling feature rebuilt with N = 3, 5, 10; final model re-trained.", "cap"))
story.append(P("Three races is measurably worse on validation (one DNF moves the average too much); ten is not "
               "distinguishable from five. Five is kept, now with evidence."))

story.append(P("7.5 Constructor lineage vs plain constructorId (decision D12)", "h2"))
lrows = [["Constructor history", "Val PR-AUC", "Test PR-AUC", "Train rows w/o standings", "Val rows w/o standings"]]
for n, r in LIN.iterrows():
    lrows.append([n, f3(r.val_pr_auc), f3(r.test_pr_auc), f"{r.train_rows_without_con_standings_pct:.1f}%",
                  f"{r.val_rows_without_con_standings_pct:.1f}%"])
story.append(table(lrows, [5.2, 2.2, 2.2, 3.7, 3.7]))
story.append(P(f"Table 16 — Constructor features by lineage family vs by plain ID. Δ val = "
               f"{LIN.Δval_vs_lineage.iloc[1]:+.3f}, 95% CI {LIN.Δ_ci.iloc[1]}.", "cap"))
story.append(P("The course guide suggests following <i>constructorId</i> and accepting that a rename resets history. "
               "The experiment shows lineage does not change accuracy measurably. We keep the families because "
               "they do not reset a real team's history at a rename (e.g. round 1 of 2020 AlphaTauri and 2021 Aston "
               "Martin and Alpine would otherwise have no standings) and because Q3 compares the same factory "
               "across eras. It is a documented judgement call, not a performance claim."))

story.append(P("7.6 Feature-set check", "h2"))
fsrows = [["Feature set", "Features", "Val PR-AUC", "Δ vs selected [95% CI]", "Test PR-AUC"]]
for n, r in FSE.iterrows():
    fsrows.append([n, f"{int(r.n_features)}", f3(r.val_pr_auc), "—" if r.Δ_ci == "—" else f"{r.Δval_vs_selected:+.3f} {r.Δ_ci}",
                   f3(r.test_pr_auc)])
story.append(table(fsrows, [5.2, 1.8, 2.3, 4.6, 2.3]))
story.append(P("Table 17 — The final model trained on the 26 selected features vs all 33 usable candidates (the 7 near-duplicates added back).", "cap"))
story.append(P("Adding the near-duplicates back changes validation PR-AUC by +0.004 with an interval that includes 0, and test is identical. The selection rule therefore costs no accuracy; the 26 features are kept because near-duplicate columns split and offset weights in a linear model and make the explanations harder to read."))

# =================================================================================================================
# 8. XAI
# =================================================================================================================
story += [P("8. Explainability", "h1")]
story.append(box([P("<b>These explanations are not causal.</b> A feature being important means the model "
                    "<i>relies</i> on it to predict, not that it <i>causes</i> podium finishes. Correlated "
                    "features (e.g. qualifying position and reaching Q3) share and swap importance, and the sign of "
                    "one feature can only be read given the others.", "box")]))
story.append(Spacer(1, 6))
story.append(P("8.1 Global explanations", "h2"))
top = PI.head(6)
story.append(P("Permutation importance (drop in validation PR-AUC when a feature is shuffled) is dominated by "
               + ", ".join(f"<i>{f}</i> ({v:.3f})" for f, v in top["mean"].items())
               + ". SHAP agrees (Figure 17): <i>quali_pos</i> dominates, followed by reaching Q2/Q3, recent pace, "
                 "recent finishes, age and gap to pole."))
story += bullets([
    "<b>Directions.</b> A better (lower) qualifying position, a smaller gap to pole, faster recent pace, better "
    "recent finishes and more career podiums push towards a podium. A pit-lane start and a grid penalty push "
    "strongly down.",
    "<b>Counter-intuitive signs.</b> <i>reached_q2</i> and <i>drv_age</i> push down. They are strongly correlated "
    "with <i>quali_pos</i> and career podiums, and in a linear model correlated features offset each other's "
    "weights. This is a concrete example of why importance must not be read as a causal effect.",
])
xai = Table([[img("xai_permutation_importance", 7.6), img("xai_shap_beeswarm", 9.2)]],
            colWidths=[7.9 * cm, 9.4 * cm])
xai.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story += [xai, P("Figure 17 — Left: permutation importance on validation. Right: SHAP beeswarm in real units "
                 "(colour = feature value; right = towards podium).", "cap")]

story.append(P("8.2 Local explanations", "h2"))
story += bullets([
    "<b>Confident hit:</b> Lewis Hamilton, 2021 Spanish Grand Prix, on pole. Predicted probability 0.98; he won. "
    "SHAP and LIME both put qualifying position first, then no pit-lane start, fast recent pace and good recent "
    "finishes (Appendix B).",
    "<b>Missed podium:</b> Sebastian Vettel, 2020 Turkish Grand Prix, qualified 12th, started 11th. Predicted "
    "probability 0.04; he finished third in a wet, chaotic race. SHAP (Figure 18) shows the 6.9% gap to pole "
    "(qualifying was wet, which inflated the gaps) and <i>reached_q2</i> (the collinearity artefact) pulling down, "
    "and his 120 career podiums pushing up. A reasonable pre-race view: the outcome came from race conditions "
    "nobody could know at the cutoff.",
    "<b>LIME vs SHAP.</b> LIME runs on the raw features, so its rules read in real units "
    "(\"11 &lt; quali_pos ≤ 17\", \"gap_to_pole_pct &gt; 3.03\"), and it agrees with SHAP on the main drivers. Its "
    "local linear surrogate fits well for the confident hit (R² 0.66) but poorly for the missed podium (R² 0.29), "
    "where the probability is near 0 and the sigmoid is flat, so LIME is read qualitatively; SHAP is exact for a "
    "linear model.",
])
story += [KeepTogether([img("xai_shap_waterfall_missed_podium", 12.0), Spacer(1, 4),
                        img("xai_lime_missed_podium", 11.0),
                        P("Figure 18 — Local explanations for Vettel, Turkey 2020. Top: SHAP waterfall (log-odds, "
                          "real feature values). Bottom: LIME for the same row.", "cap")])]

# =================================================================================================================
# 9. Inference
# =================================================================================================================
story += [P("9. Inference function", "h1"),
          P("<i>predict_podium(entry)</i> takes raw pre-race inputs for one driver in one race (driver, constructor, "
            "circuit, date, grid; optionally qualifying position, gap to pole, Q2/Q3 flags, field size, sprint "
            "result) and builds every feature itself from races dated before the entry. It returns the model "
            "score, the Platt-calibrated probability, the yes/no prediction at the validation threshold, and which "
            "features were filled by a fallback or imputed. Missing qualifying data is filled from the grid slot "
            "(with the typical gap for that position), because the pipeline's missing-value indicators would "
            "otherwise read 'not known' as 'set no time' and push the probability to ≈ 0. Missing history (a "
            "debutant) stays missing, exactly as for debutants in training. Post-race fields are rejected.")]
irows = [["Record (Hülkenberg, Haas, Abu Dhabi 2024)", "Score", "Calibrated probability", "Prediction", "Filled / imputed"]]
for n, r in INF.iterrows():
    irows.append([n, f"{r.score:.3f}", f"{r.calibrated_probability:.3f}", "podium" if r.predicted_podium else "no podium",
                  f"{int(r.n_fallback)} / {int(r.n_imputed)}"])
story.append(table(irows, [5.6, 1.8, 3.4, 2.4, 3.0]))
story.append(P("Table 18 — Inference demo. Complete record: qualified 4th, started 7th after a grid penalty, "
               "finished off the podium. Without qualifying data the fallback assumes he qualified 7th, so the "
               "probability drops. Debutant: an unknown driver in the same car starting 5th.", "cap"))

# =================================================================================================================
# 10. Limitations + conclusion
# =================================================================================================================
story += [P("10. Limitations", "h1")]
story += bullets([
    "<b>Qualifying-coverage drift.</b> Qualifying data is complete only from 2003, so the model is restricted to "
    "2006+. Older seasons were tested (Section 7.1) and do not help.",
    "<b>Era sensitivity.</b> Regulation changes reshuffle team performance. The test set is a new era, and its first "
    "season is the hardest (PR-AUC 0.66 in 2022 vs 0.77 in 2023).",
    "<b>Small evaluation sets.</b> 39 validation and 68 test races; 95% intervals span about ±0.06–0.10 PR-AUC, so "
    "most model differences are not significant.",
    "<b>Calibration.</b> The class-weighted score is over-confident; reported probabilities are Platt-calibrated on "
    "validation.",
    "<b>Unused data.</b> Sprint features cannot be learned while training ends in 2019; pit-stop data starts only "
    "in 2011.",
    "<b>Small samples in the data questions.</b> 8–22 front-row starts per circuit and era (Q1); 82 home entries "
    "on pole (Q2).",
    "<b>Judgement calls.</b> Status grouping (D11), constructor lineage (D12, shown not to change accuracy) and "
    "'nationality = home' are documented choices; Q3 is robust to the ambiguous statuses.",
    "<b>Unpredictable events.</b> First-lap incidents, safety cars and weather limit what any pre-race model can "
    "achieve (the Vettel example).",
    "<b>Inference fallback.</b> Filling a missing qualifying position from the grid hides a grid penalty.",
])
story += [P("11. Conclusion", "h1"),
          P("A careful, fully asserted cleaning pipeline turns the relational Ergast tables into a leakage-safe "
            "modelling table with one row per driver and race. On the unseen 2022–24 seasons — a new regulation era — "
            f"logistic regression reaches PR-AUC {f3(m(FINAL, 'pr_auc', 'test'))} against "
            f"{f3(m('ref_grid_rule', 'pr_auc', 'test'))} for ranking by grid position, a gap that holds under both "
            "splits and whose bootstrap interval excludes zero. Forests, boosting and neural networks do not beat "
            "it, and the starting position carries most of the predictive signal. The data questions show that "
            "front-row conversion rankings changed in the hybrid era, that there is no measurable home advantage "
            "once grid position is accounted for, and that mechanical reliability improved markedly in 2022–24. "
            "Every decision, with the numbers behind it, is recorded in the notebook and in <i>DECISION_LOG.md</i>.")]

# =================================================================================================================
# Appendix
# =================================================================================================================
story += [PageBreak(), P("Appendix A — Judgement calls in the codebooks", "h1"),
          P("<b>Status codebook (D11, codebooks/status_map.csv).</b> Illness, injury and similar → incident "
            "(driver-related, not a car failure). Underweight → disqualified (a regulation decision). Launch control "
            "and heat-shield fire → mechanical. Ambiguous (counted both ways in Q3): Retired, Technical, Not "
            "classified, Puncture, Tyre, Wheel, Wheel nut, Front/Rear/Broken wing, Damage, Debris, Out of fuel, "
            "Handling, Chassis, Stalled and a few rare labels."),
          P("<b>Constructor lineage (D12, codebooks/constructor_lineage.csv).</b> Families: Faenza (Minardi → Toro "
            "Rosso → AlphaTauri → RB); Silverstone (Jordan → MF1 → Spyker → Force India → Racing Point → Aston "
            "Martin); Hinwil (Sauber ↔ BMW Sauber, and Alfa Romeo 2019–23); Enstone (Toleman → Benetton → Renault → "
            "Lotus F1 → Renault → Alpine); Brackley (BAR → Honda → Brawn → Mercedes 2010+); Milton Keynes (Stewart → "
            "Jaguar → Red Bull); Banbury (Virgin → Marussia → Manor); Caterham (Lotus Racing → Caterham); Arrows "
            "(with Footwork); Ligier → Prost; March ↔ Leyton House. The IDs for Alfa Romeo, Mercedes and Renault are "
            "shared with unrelated works teams of the 1950s–80s, so these rules carry year ranges. Not linked: "
            "Tyrrell → BAR (new team, new factory).")]

story += [PageBreak(), P("Appendix B — Remaining figures from the notebook", "h1"),
          P("Every figure the notebook produces is in this report; those not shown above follow, in notebook order.")]
EXTRA = [
    ("eda_raw_table_coverage", 16.0, "Table coverage by season (raw): share of races with rows in each table."),
    ("eda_raw_season_overview", 16.5, "Races per season, mean entrants per race, and share of entries with grid = 0."),
    ("audit_nan_heatmap_after", 15.0, "Share of NaN per column after cleaning (compare with Figure 1)."),
    ("eda_clean_durations", 16.5, "Typed duration columns after cleaning: lap times, pit stops, Q1 by season."),
    ("eda_clean_grain_and_base_rate", 15.0, "Result rows before/after cleaning, and podium base rate per season."),
    ("features_corr_and_missingness", 16.8, "Feature redundancy (Spearman ρ, training seasons) and missingness "
                                            "by season."),
    ("split_rows_per_season", 15.0, "Rows per season by split."),
    ("lr_coefficients", 9.5, "Logistic-regression coefficients (standardised features)."),
    ("tuning_lr", 8.0, "Logistic regression: validation PR-AUC vs regularisation strength C."),
    ("tuning_rf", 8.0, "Random forest: validation PR-AUC over depth × leaf size."),
    ("tuning_gb", 13.0, "Gradient boosting: validation PR-AUC over learning rate × depth × leaf size."),
    ("nn_training_curves", 14.0, "Neural network (starting architecture): loss and PR-AUC per epoch."),
    ("calibration_experiment", 9.5, "Calibration on validation: weighted, unweighted, Platt and isotonic."),
    ("scope_comparison", 16.8, "Scope comparison on validation and test (Table 12)."),
    ("xai_shap_bar", 11.0, "Global SHAP: mean |SHAP| per feature."),
    ("xai_shap_waterfall_confident_hit", 12.0, "Local SHAP for Hamilton, Spain 2021 (confident hit)."),
    ("xai_lime_confident_hit", 11.0, "LIME for Hamilton, Spain 2021 (confident hit)."),
]
for i, (name, w, cap) in enumerate(EXTRA, start=1):
    story.append(fig(name, w, f"Figure B{i} — {cap}"))

story += [P("Appendix C — Reproducibility", "h1"),
          P(f"Code and outputs: {REPO}. Install <i>requirements.txt</i>, run <i>F1_Podium_Prediction.ipynb</i> top to "
            "bottom (about 8 minutes on a laptop CPU), then <i>python report/build_report.py</i> to regenerate this "
            "report. Every table above is read from <i>outputs/*.csv</i> and every figure from "
            "<i>outputs/figures/</i>; a fresh re-run reproduces the output tables exactly.")]



def on_page(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(GREY)
    canvas.drawString(2 * cm, 1.2 * cm, "CSEN 903 · Milestone 1 · Formula 1 Podium Prediction")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"{doc.page}")
    canvas.restoreState()


PDF.parent.mkdir(exist_ok=True)
doc = SimpleDocTemplate(str(PDF), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.7 * cm,
                        bottomMargin=1.8 * cm, title="Formula 1 Podium Prediction — Milestone 1 Report",
                        author=", ".join(TEAM), subject="CSEN 903 Milestone 1")
doc.build(story, onFirstPage=on_page, onLaterPages=on_page)
print("wrote", PDF)
