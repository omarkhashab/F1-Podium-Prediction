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

TEAM = ["Omar Osama", "Mohamed Ayman", "Moataz Ashraf", "Omar Emad"]
REPO = "github.com/Aymanoski/ACL"

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

# ---- data from the notebook outputs -----------------------------------------------------------------------------
MC = pd.read_csv(OUT / "model_comparison.csv", header=[0, 1], index_col=0)
SC = pd.read_csv(OUT / "scope_comparison.csv", index_col=0)
AB = pd.read_csv(OUT / "ablation.csv", index_col=0)
PE = pd.read_csv(OUT / "preprocessing_experiments.csv")
Q2S = pd.read_csv(OUT / "q2_sensitivity.csv", index_col=0)
TH = pd.read_csv(OUT / "threshold_strategy.csv", index_col=0)
FS = pd.read_csv(OUT / "feature_selection.csv")
EV = pd.read_csv(OUT / "feature_evidence.csv").set_index("feature")
PI = pd.read_csv(OUT / "permutation_importance.csv", index_col=0).sort_values("mean", ascending=False)
Q3 = pd.read_csv(OUT / "q3_mechanical_rates.csv")

m = lambda model, metric, split: MC.loc[model, (metric, split)]
FINAL = "lr_tuned"

story = []

# =================================================================================================================
# Title + summary
# =================================================================================================================
story += [Spacer(1, 1.2 * cm), P("Formula 1 Podium Prediction", "title"), Spacer(1, 4),
          P("Milestone 1 — Data engineering, leakage-safe modelling and explainability", "sub"), Spacer(1, 10),
          P("CSEN 903 Advanced Computer Lab · German University in Cairo · Winter 2026", "sub"),
          P(" · ".join(TEAM), "sub"),
          P(f"{date(2026, 10, 18).strftime('%d %B %Y')} · code: {REPO}", "sub"), Spacer(1, 16)]

story.append(box([P("<b>Summary</b>", "box"), Spacer(1, 3)] + bullets([
    "<b>Task:</b> for every driver in every race, predict a podium finish (<i>positionOrder</i> ≤ 3) using only "
    "information available after qualifying and before the start.",
    "<b>Data:</b> the 14-table Ergast / Kaggle dataset (1950–2024), cleaned into one leakage-safe row per "
    "(race, driver). Raw files are never modified; every cleaning rule is logged and asserted.",
    f"<b>Model:</b> a tuned logistic regression reaches <b>test PR-AUC {f3(m(FINAL, 'pr_auc', 'test'))}</b> "
    f"(ROC-AUC {f3(m(FINAL, 'roc_auc', 'test'))}, F1 {f3(m(FINAL, 'f1', 'test'))}) on the unseen 2023–24 seasons. "
    f"The 'rank by starting grid' reference scores {f3(m('ref_grid_rule', 'pr_auc', 'test'))}. "
    "A random forest and a shallow neural network do not beat it.",
    "<b>What drives predictions:</b> qualifying is the core signal (removing it costs 0.075 validation PR-AUC). "
    "Standings, recent form and pace add little that qualifying does not already carry.",
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
            "which runs top to bottom without manual steps and produces every table and figure in this report.")]

# =================================================================================================================
# 2. Audit and cleaning
# =================================================================================================================
story += [P("2. Data audit and cleaning", "h1"), P("2.1 Audit before cleaning", "h2")]
story += bullets([
    "<b>Sentinels.</b> Missing values are stored as the literal text <i>\\N</i>. They are concentrated in "
    "<i>structural</i> columns (session times recorded only from 2021, fastest-lap data from 2004) and "
    "<i>outcome</i> columns (<i>results.time</i> 71% missing for drivers not on the lead lap, <i>position</i> 41% "
    "for non-classified drivers). Only <i>q2/q3</i> are missing for a pre-race reason: the driver was knocked out.",
    "<b>Keys.</b> All primary keys are unique and non-null and every foreign key resolves. The one violation is "
    "the required grain: 176 result rows form 85 duplicated (race, driver) pairs. These are 1950s shared drives, "
    "where drivers swapped cars mid-race.",
    "<b>Coverage drift.</b> Qualifying rows exist from 1994 but cover only 6–59% of entries in 1996–2002. They are "
    "complete from 2003 (Figure 1). Lap times start in 1996, pit stops in 2011 and sprints in 2021.",
    "<b>Formats and categories.</b> Durations appear as <i>m:ss.sss</i>, <i>mm:ss.sss</i> and "
    "<i>h:mm:ss.sss</i>, and <i>results.time</i> mixes absolute times with gaps (22 formats). There are spelling "
    "issues ('Argentinian ' with a trailing space, 'USA' vs 'United States') and one HTML entity.",
])
story.append(fig("eda_raw_quali_coverage", 15.5,
                 "Figure 1 — Share of race entries with a qualifying row, per season (raw data). Coverage is "
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
    ["D6", "Missing features", "Domain fill where the true value is known (rookie = 0 starts; first visit to a "
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
     "RB), with year ranges for IDs reused by unrelated teams.", "37 rules, 11 families"],
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

story.append(P("2.3 Effect of cleaning", "h2"))
story += bullets([
    "<i>results</i> goes from 26,759 to 24,755 rows: −405 rows from the Indy 500, −1,535 non-starters, −64 from "
    "merged shared drives. All key, grain and foreign-key checks pass after every step.",
    "Missing shares in the original columns barely change (results 22.8% → 21.9%). Cleaning converts sentinels "
    "into real missing values; it does not invent or fill values. Filling is done per feature (D6), with the "
    "median fitted on the training split only.",
    "Outlier removal targets data errors: the 481 removed pit stops include ~51-minute red-flag suspensions, and "
    "the one qualifying time removed is 16:42.640 (Figure 2).",
    "<b>Class imbalance:</b> 14.2% of rows in the modelling scope are podiums (train 14.0%, validation and test "
    "15.0%). This drives the metric choice in Section 6.",
])
story.append(fig("cleaning_outliers_before_after", 16.5,
                 "Figure 2 — Timing distributions before and after outlier handling (log counts). Left: pit-stop "
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
    "because penalties and pit-lane starts move drivers off the front row.",
    "<b>Grain, missingness, cutoff.</b> One row per (race, driver), filtered to front-row starters. Only "
    "2003–2024 is used, where qualifying is complete. Grid and qualifying position are both known before the "
    "start. With 8–22 starts per circuit and era, one podium moves a rate by 5–12 points.",
])
story.append(fig("q1_front_row_grid", 16.5,
                 "Figure 3 — Front-row (grid) → podium rate per circuit, 2003–13 vs 2014–24, and the change in "
                 "rank between the eras."))

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
story.append(fig("q2_home_vs_away_by_grid", 11.5, "Figure 4 — Podium rate at home vs away within grid strata."))

story.append(P("Q3 — Which constructors have the highest mechanical-retirement rate in 2014–2021 vs 2022–2024?",
               "h2"))
story.append(P("A mechanical retirement is a race start that ended because a car component failed. The status "
               "codebook (D11) defines it; ambiguous labels such as 'Retired', 'Puncture' and 'Wheel' are counted "
               "both ways: (a) not mechanical, (b) mechanical. The denominator is race starts, excluding drivers "
               "who withdrew after taking a grid slot. Teams are grouped by lineage (D12), so Toro Rosso → "
               "AlphaTauri → RB counts as one team (shown as 'Faenza')."))
q3a = Q3[Q3.variant == "a_mech_only"]
q3rows = [["Era", "Highest rates (variant a)", "Lowest rate", "Spearman (a) vs (b)"]]
for era, rho in [("2014-2021", "0.95"), ("2022-2024", "0.85")]:
    d = q3a[q3a.era == era].sort_values("rate", ascending=False)
    top = ", ".join(f"{r.constructor_family} {100 * r.rate:.1f}%" for r in d.head(4).itertuples())
    low = d.iloc[-1]
    q3rows.append([era.replace("-", "–"), top, f"{low.constructor_family} {100 * low.rate:.1f}%", rho])
story.append(table(q3rows, [2.2, 9.0, 3.4, 2.4]))
story.append(P("Table 3 — Mechanical-retirement rate per start (teams with ≥ 20 starts per era). Families: Faenza = "
               "Toro Rosso / AlphaTauri / RB; Enstone = Lotus / Renault / Alpine; Hinwil = Sauber / Alfa Romeo; "
               "Brackley = Mercedes; Silverstone = Force India / Racing Point / Aston Martin.", "cap"))
story += bullets([
    "<b>Answer.</b> 2014–21 is led by Caterham, Toro Rosso / AlphaTauri, McLaren (the McLaren-Honda years) and "
    "Renault, with Mercedes the most reliable. In 2022–24 Alpine and Sauber / Alfa Romeo lead, and rates roughly "
    "halve across the field.",
    "<b>Robustness.</b> Counting ambiguous statuses as mechanical changes little: rank correlation 0.95 and 0.85, "
    "and the top team in each era is unchanged. Wilson 95% intervals (Figure 5) overlap for differences under "
    "about 4 points.",
])
story.append(fig("q3_mechanical_dnf_rate", 16.5,
                 "Figure 5 — Mechanical-retirement rate per constructor family with 95% intervals; orange = "
                 "mechanical only, grey = including ambiguous statuses."))

# =================================================================================================================
# 4. Modelling table and features
# =================================================================================================================
story += [P("4. Modelling table and features", "h1"),
          P("The modelling table has exactly one row per (race, driver): 7,905 rows for 2006–2024 (asserted unique). "
            "Features are written to an explicit allowed list; the table may only contain listed features, IDs "
            "and the target. Table 4 lists the 26 selected features and why each is valid at the cutoff.")]
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
story.append(P("Table 4 — Selected features by group.", "cap"))

story.append(P("Leakage control", "h2"))
story += bullets([
    "Form, points-share, pace and pit features use only races dated before the race being predicted. An "
    "independent recomputation for 300 random rows matches the vectorised features exactly.",
    "Standings come from a race dated earlier, asserted for every row; round-1 standings come from the previous "
    "season.",
    "Imputer and scaler are fitted on the training seasons only; the test set is scored once, after every choice "
    "was fixed on validation. The inference function rejects post-race fields such as <i>points</i>.",
    "Raw championship points are never used: points are expressed as shares (D13), so the 2010 scoring change "
    "(a win went from 10 to 25 points) does not shift feature values between training and test.",
])

story.append(P("Feature selection", "h2"))
story.append(P("Selection uses the <b>training seasons only</b>, so validation and test never influence it. It has "
               "two rules: (1) drop features that are empty or constant in training; (2) visit features by "
               "univariate AUC, highest first, and drop any whose |Spearman ρ| with an already-kept feature is "
               "≥ 0.95. Of 36 candidates, 26 are kept (Table 5). The strongest single features are "
               f"<i>quali_pos</i> (univariate AUC {EV.loc['quali_pos', 'univariate_auc']:.2f}), "
               f"<i>gap_to_pole_pct</i> ({EV.loc['gap_to_pole_pct', 'univariate_auc']:.2f}), "
               f"<i>drv_pts_frac_lastN</i> ({EV.loc['drv_pts_frac_lastN', 'univariate_auc']:.2f}) and "
               f"<i>con_gap_to_leader_share</i> ({EV.loc['con_gap_to_leader_share', 'univariate_auc']:.2f})."))
drows = [["Dropped feature", "Reason (training seasons 2006–2020)"]]
for r in FS[~FS.kept].itertuples():
    drows.append([f"<i>{r.feature}</i>", r.reason_dropped.replace("rho", "ρ")])
story.append(table(drows, [4.6, 12.4]))
story.append(P("Table 5 — Dropped candidates. <i>grid</i> is not lost: it equals <i>quali_pos + "
               "grid_minus_quali</i>, both kept. The sprint features cannot be learned because sprints start in "
               "2021 and training ends in 2020.", "cap"))

# =================================================================================================================
# 5. Split and preprocessing
# =================================================================================================================
story += [P("5. Split and preprocessing", "h1"),
          P("Rows are not independent: form carries over between races and the sport drifts from season to season. "
            "We therefore split <b>by season</b>, so whole races stay together and the model always predicts the "
            "future from the past: train 2006–2020 (6,108 rows, 285 races), validation 2021–22 (879 rows), test "
            "2023–24 (918 rows). Podium rates are 14.0%, 15.0% and 15.0%. Validation includes 2022, the first "
            "season of the ground-effect regulations, so model selection already sees the newest era."),
          P("Preprocessing is median imputation with missing-value indicators, followed by standardisation (the "
            "random forest skips scaling). Table 6 reports three controlled experiments; only the preprocessing "
            "changes, with the same logistic regression and features each time.")]
perows = [["Experiment", "Variant", "Val PR-AUC", "Val ROC-AUC"]]
for r in PE.itertuples():
    perows.append([r.experiment, r.variant.replace("_", " "), f"{r.pr_auc:.4f}", f"{r.roc_auc:.4f}"])
story.append(table(perows, [3.4, 6.0, 2.6, 2.6]))
story.append(P("Table 6 — Preprocessing experiments (validation).", "cap"))
story += bullets([
    "<b>E1, order:</b> imputing before or after scaling makes no practical difference. Only about 2.6% of cells "
    "are imputed, and scaling first just places the imputed value at the median of the scaled column.",
    "<b>E2, fit scope:</b> fitting the preprocessing on all data, including validation and test, brings no gain "
    "(0.7215 vs 0.7223) and would be leakage, so it is fitted on train only.",
    "<b>E3, missing indicators</b> help (+0.006 PR-AUC). Being missing is informative: no previous standings "
    "means a rookie or a new team, and no pit data means before 2011.",
])

# =================================================================================================================
# 6. Models
# =================================================================================================================
story += [P("6. Models and evaluation", "h1"), P("6.1 Models", "h2")]
story += bullets([
    "<b>Reference rule</b> (not learned): score = 1 / grid position. Every model must beat it.",
    "<b>Logistic regression (baseline).</b> A linear score of the standardised features passed through a sigmoid; "
    "class weights counter the 14% positive rate. It is simple and interpretable, but models only additive linear "
    "effects. Tuned over C (C = 10 chosen).",
    "<b>Random forest.</b> An average of many decision trees on bootstrap samples, which captures interactions "
    "without scaling. The default (unlimited depth) memorises the training data; tuning over depth × leaf size "
    "picked depth 4, leaf 20.",
    "<b>Shallow neural network.</b> Two hidden layers (32, 16) with ReLU, dropout 0.2, L2 1e-4, and early stopping "
    "on validation PR-AUC. About 2,000 weights for about 6,000 training rows.",
])
names = {"ref_grid_rule": "Grid rule (reference)", "lr_baseline": "Logistic regression (C = 1)",
         "lr_tuned": "Logistic regression, tuned (final)", "rf_default": "Random forest, default",
         "rf_tuned": "Random forest, tuned", "ffnn": "Shallow neural network"}
mrows = [["Model", "PR-AUC train", "PR-AUC val", "PR-AUC test", "ROC-AUC test", "F1 test", "Prec. test",
          "Recall test"]]
for k, label in names.items():
    cells = [m(k, "pr_auc", "train"), m(k, "pr_auc", "val"), m(k, "pr_auc", "test"), m(k, "roc_auc", "test"),
             m(k, "f1", "test"), m(k, "precision", "test"), m(k, "recall", "test")]
    row = [f3(x) for x in cells]
    if k == FINAL:
        row = [f"<b>{x}</b>" for x in row]
        label = f"<b>{label}</b>"
    mrows.append([label] + row)
story.append(table(mrows, [4.6, 1.75, 1.75, 1.75, 1.85, 1.6, 1.6, 1.6]))
story.append(P("Table 7 — Model comparison: same rows and the same 26 features for every model. F1, precision "
               "and recall use the threshold chosen on validation. Validation ROC-AUC, F1 and the other metrics "
               "are in <i>outputs/model_comparison.csv</i>.", "cap"))

story.append(P("6.2 Metric choice and threshold", "h2"))
story += bullets([
    "<b>Primary metric: PR-AUC.</b> Podiums are a minority (14–15%), and the task is ranking podium finishers above "
    "everyone else. ROC-AUC is inflated by the many easy back-of-grid entries: it is ≈ 0.93 for every model and "
    "0.91 even for the grid rule, so it barely separates the models.",
    "<b>Secondary metric: F1</b> at a probability threshold chosen on validation. This measures the quality of "
    "the actual yes/no prediction.",
    f"<b>Threshold strategy.</b> The F1-maximising validation threshold beat the domain rule 'exactly 3 podiums "
    f"per race' for every model (logistic regression: {TH.loc[FINAL, 'val_f1_max_f1_threshold']:.3f} vs "
    f"{TH.loc[FINAL, 'val_f1_top3_per_race']:.3f}). Thresholds and hyperparameters were chosen on training and "
    "validation data only.",
])

story.append(P("6.3 Results", "h2"))
story += bullets([
    f"<b>Final model: tuned logistic regression</b>. It has the best validation PR-AUC "
    f"({f3(m(FINAL, 'pr_auc', 'val'))}) and is also the simplest model. On the unseen test seasons it reaches "
    f"PR-AUC {f3(m(FINAL, 'pr_auc', 'test'))}, finding 112 of 138 podiums with 80 false alarms "
    f"(precision {f3(m(FINAL, 'precision', 'test'))}, recall {f3(m(FINAL, 'recall', 'test'))}).",
    "<b>Generalisation.</b> Validation and test scores are close (0.723 → 0.713) and train ≈ validation, so there "
    "is no overfitting. By season, 2023 scores 0.766 and 2024 0.673: 2023 was dominated by one team, while 2024 "
    "had four different race-winning teams.",
    "<b>Complexity does not pay off.</b> The default random forest overfits (train PR-AUC 1.000 vs validation "
    "0.646). The tuned forest and the neural network are no better than logistic regression. The signal is "
    "mostly monotonic (better qualifying, form and standings → higher chance), which a linear model captures well.",
    "<b>Calibration.</b> Probabilities are over-confident: a predicted 0.6 corresponds to an observed rate of about "
    "0.15, because class weighting up-weights podiums about 6×. The outputs are good scores for ranking and "
    "thresholding but should be calibrated (e.g. isotonic regression on validation) before being read as "
    "probabilities.",
])
story.append(fig("test_confusion_pr_calibration", 16.8,
                 "Figure 6 — Test set: confusion matrix of the final model, precision–recall curves of all "
                 "models (dashed = base rate), and calibration of the final model."))

# =================================================================================================================
# 7. Scope comparison
# =================================================================================================================
story += [P("7. Experiment: modern seasons vs all seasons", "h1"),
          P("To justify D1 empirically, the same features and model settings were trained on two windows, 2006–2020 "
            "and 1950–2020, and scored on <b>identical</b> validation and test rows.")]
srows = [["Training window", "Train rows", "Missing feature cells", "LR val", "RF val", "NN val", "LR test",
          "RF test", "NN test"]]
for scope, r in SC.iterrows():
    srows.append([f"{scope} ({r.train_seasons})", f"{int(r.train_rows):,}", f"{r.pct_feature_cells_missing:.1f}%",
                  f3(r.LR_val_pr_auc), f3(r.RF_val_pr_auc), f3(r.FFNN_val_pr_auc), f3(r.LR_test_pr_auc),
                  f3(r.RF_test_pr_auc), f3(r.FFNN_test_pr_auc)])
story.append(table(srows, [3.6, 1.7, 2.3, 1.55, 1.55, 1.55, 1.55, 1.55, 1.65]))
story.append(P("Table 8 — PR-AUC by training window (same validation and test rows).", "cap"))
story.append(P("Modern training is better for logistic regression (0.722 vs 0.705) and the random forest (0.697 vs "
               "0.670) on validation, and for all three models on test. The neural network is the only exception "
               "on validation (0.704 vs 0.719). The older data has 20.8% missing feature cells (no qualifying "
               "before 1994, unknown grid slots, no lap data before 1996), and its podium patterns (30+ car "
               "fields, high retirement rates) differ from today's. Four times as many rows does not compensate, "
               "so the modern scope is kept."))
story.append(fig("scope_comparison", 16.8, "Figure 7 — Scope comparison on validation and test."))

# =================================================================================================================
# 8. Ablation
# =================================================================================================================
story += [P("8. Feature-group ablation", "h1"),
          P("Each feature group is removed in turn and the tuned random forest is retrained with fixed "
            "hyperparameters. The forest needs no scaling and captures interactions, so a group's value is not "
            "hidden by linearity.")]
abrows = [["Removed group", "Val PR-AUC", "Δ val PR-AUC", "Δ val ROC-AUC", "Δ test PR-AUC"]]
for g, r in AB.iterrows():
    label = "none (full model)" if g.startswith("(none") else g.replace("_", " ")
    abrows.append([label, f3(r.val_pr_auc), f"{r['Δval_pr_auc']:+.3f}", f"{r['Δval_roc_auc']:+.3f}",
                   f"{r['Δtest_pr_auc']:+.3f}"])
story.append(table(abrows, [4.4, 2.6, 2.8, 2.8, 2.8]))
story.append(P("Table 9 — Ablation (negative Δ = the group helps).", "cap"))
story.append(P("Qualifying is the core signal: removing it costs 0.075 validation PR-AUC (0.112 on test). Grid, "
               "driver form and standings add a little (0.009–0.019). Removing constructor form or pace/pit "
               "slightly improves validation, because their information is already carried by standings and "
               "qualifying (a fast car shows up in qualifying). This complements the univariate evidence of "
               "Section 4: grid, standings and form all have univariate AUC ≈ 0.89–0.92, but most of that signal "
               "overlaps with qualifying. Univariate evidence measures signal; ablation measures <i>unique</i> "
               "signal."))

# =================================================================================================================
# 9. XAI
# =================================================================================================================
story += [P("9. Explainability", "h1")]
story.append(box([P("<b>These explanations are not causal.</b> A feature being important means the model "
                    "<i>relies</i> on it to predict, not that it <i>causes</i> podium finishes. Correlated "
                    "features (e.g. qualifying position and reaching Q3) share and swap importance, and the sign of "
                    "one feature can only be read given the others.", "box")]))
story.append(Spacer(1, 6))
story.append(P("9.1 Global explanations", "h2"))
top = PI.head(6)
story.append(P("Permutation importance (drop in validation PR-AUC when a feature is shuffled) is dominated by "
               + ", ".join(f"<i>{f}</i> ({v:.3f})" for f, v in top["mean"].items())
               + ". SHAP agrees on the ranking (Figure 8): <i>quali_pos</i> dominates, followed by reaching Q2/Q3, "
                 "recent pace, age and recent finishing positions."))
story += bullets([
    "<b>Directions.</b> A better (lower) qualifying position, faster recent pace, better recent finishes and more "
    "career podiums push towards a podium. A pit-lane start and a grid penalty push strongly down.",
    "<b>Counter-intuitive signs.</b> <i>reached_q2</i>, <i>reached_q3</i> and <i>drv_age</i> push down. They are "
    "strongly correlated with <i>quali_pos</i> and career podiums, and in a linear model correlated features offset "
    "each other's weights. This is a concrete example of why importance must not be read as a causal effect.",
])
xai = Table([[img("xai_permutation_importance", 7.6), img("xai_shap_beeswarm", 9.2)]],
            colWidths=[7.9 * cm, 9.4 * cm])
xai.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
story += [xai, P("Figure 8 — Left: permutation importance on validation. Right: SHAP beeswarm (colour = feature "
                 "value; right = towards podium).", "cap")]

story.append(P("9.2 Local explanations", "h2"))
story += bullets([
    "<b>Confident hit:</b> Lewis Hamilton, 2021 Spanish Grand Prix, starting from pole. Predicted probability "
    "0.98; he won. Qualifying position 1 and strong recent form drive the score.",
    "<b>Missed podium:</b> Esteban Ocon, 2021 Hungarian Grand Prix, starting P8. Predicted probability 0.11; he "
    "won after a first-corner pile-up eliminated several front-runners. SHAP (Figure 9) shows P8 raising the score "
    "above a typical entry, while weaker recent finishes and pace pull it down. This is a reasonable pre-race "
    "view; the outcome came from an incident nobody could know at the cutoff.",
    "<b>LIME vs SHAP.</b> For the Ocon row, LIME's largest terms are near-constant missing-value indicators "
    "(Figure 9, bottom), an artefact of how LIME perturbs and discretises such columns. SHAP is exact for a "
    "linear model, so we rely on SHAP for local explanations and report LIME's instability as a limitation.",
])
story += [KeepTogether([img("xai_shap_waterfall_missed_podium", 12.5), Spacer(1, 4),
                        img("xai_lime_missed_podium", 11.5),
                        P("Figure 9 — Local explanations for Ocon, Hungary 2021. Top: SHAP waterfall (log-odds; "
                          "standardised feature values). Bottom: LIME for the same row.", "cap")])]

# =================================================================================================================
# 10. Inference
# =================================================================================================================
story += [P("10. Inference function", "h1"),
          P("<i>predict_podium(record)</i> takes a dictionary of pre-race fields for one driver in one race and "
            "returns the podium probability, the yes/no prediction at the validation threshold, and the list of "
            "missing features. Missing features are imputed by the fitted pipeline. Post-race fields are rejected, "
            "so the function itself cannot be fed leakage.")]
story += bullets([
    "<b>Complete record</b> (a real test entry with all 26 features present: Oscar Piastri, Abu Dhabi 2024, "
    "qualified P2): probability 0.92, predicted podium. He finished 10th after first-lap contact, another "
    "reminder that race incidents are unpredictable at the cutoff.",
    "<b>Partially missing record</b> (the same entry without qualifying and standings): the call still runs and "
    "lists the 8 missing features, but the probability drops to ≈ 0. In training, missing qualifying data mostly "
    "belonged to drivers who did not set a time, so the missing-value indicators push the score down hard. "
    "Missing inputs are handled safely, but should be filled whenever possible.",
    "<b>Leakage guard:</b> passing <i>points</i> raises an error.",
])

# =================================================================================================================
# 11. Limitations + conclusion
# =================================================================================================================
story += [P("11. Limitations", "h1")]
story += bullets([
    "<b>Qualifying-coverage drift.</b> Qualifying data is complete only from 2003, so the model is restricted to "
    "2006+. Older seasons were tested (Section 7) and do not help.",
    "<b>Era sensitivity.</b> Regulation changes (2014, 2022) reshuffle team performance. The test covers only "
    "2023–24, and performance differs between them (PR-AUC 0.77 vs 0.67).",
    "<b>Calibration.</b> Probabilities are over-confident because of class weighting; use them as ranking scores.",
    "<b>Unused data.</b> Sprint features cannot be learned while training ends in 2020; pit-stop data starts only "
    "in 2011.",
    "<b>Small samples in the data questions.</b> 8–22 front-row starts per circuit and era (Q1); 82 home entries "
    "on pole (Q2).",
    "<b>Judgement calls.</b> Status grouping (D11), constructor lineage (D12) and 'nationality = home' are "
    "documented choices; Q3 is shown to be robust to the ambiguous statuses.",
    "<b>Unpredictable events.</b> First-lap incidents, safety cars and weather limit what any pre-race model can "
    "achieve (the Ocon example).",
    "<b>LIME</b> is unstable on near-constant binary columns; SHAP is used for local conclusions.",
])
story += [P("12. Conclusion", "h1"),
          P("A careful, fully asserted cleaning pipeline turns the relational Ergast tables into a leakage-safe "
            "modelling table with one row per driver and race. On unseen 2023–24 races, a tuned logistic regression "
            f"reaches PR-AUC {f3(m(FINAL, 'pr_auc', 'test'))} against {f3(m('ref_grid_rule', 'pr_auc', 'test'))} "
            "for ranking by grid position. More complex models do not improve on it, and qualifying carries most "
            "of the predictive signal. The data questions show that front-row conversion rankings changed in the "
            "hybrid era, that there is no measurable home advantage once grid position is accounted for, and that "
            "mechanical reliability improved markedly in 2022–24. Every decision, with the numbers behind it, is "
            "recorded in the notebook and in <i>DECISION_LOG.md</i>.")]

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
            "Tyrrell → BAR (new team, new factory)."),
          P("Appendix B — Reproducibility", "h1"),
          P(f"Code and outputs: {REPO}. Run <i>F1_Podium_Prediction.ipynb</i> top to bottom (a few minutes on a laptop "
            "CPU), then <i>python report/build_report.py</i> to regenerate this report. Main outputs: "
            "<i>outputs/cleaning_log.csv</i>, <i>decision_summary.csv</i>, <i>model_comparison.csv</i>, "
            "<i>scope_comparison.csv</i>, <i>ablation.csv</i>, <i>feature_selection.csv</i>, "
            "<i>q2_sensitivity.csv</i>, <i>q3_mechanical_rates.csv</i>, and the figures in <i>outputs/figures/</i>.")]


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
