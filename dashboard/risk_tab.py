"""Risk & compliance tab: every risk in one place, plus a downloadable report.

The file has two halves, like capacity.py:
  * plain Python (load_register, summarise, build_risk_report, ...) that can be
    tested without Streamlit
  * show_risk_tab(), the only function that draws anything on the page

Everything a teammate adds to the governance/ folder is optional. If a file
isn't there yet, that section shows a friendly message instead of an error.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
GOVERNANCE = ROOT / "governance"
REGISTER_FILE = GOVERNANCE / "risk_register.csv"
FAIRNESS_CSV = GOVERNANCE / "area_fairness.csv"
FAIRNESS_PNG = GOVERNANCE / "area_fairness.png"
LANGUAGE_FILE = GOVERNANCE / "bias_results_after.csv"
DECISION_LOG = GOVERNANCE / "logs" / "decisions.csv"
TRANSPARENCY_NOTES = GOVERNANCE / "transparency_notes.md"

REGISTER_COLUMNS = ["risk_id", "risk", "area", "who_is_harmed", "likelihood", "impact",
                    "score", "evidence", "mitigation", "owner", "status"]
TEXT_COLUMNS = ["risk_id", "risk", "area", "who_is_harmed", "evidence",
                "mitigation", "owner", "status"]
HIGH_SCORE = 15  # a risk with likelihood x impact of 15 or more is "high"
DONE_STATUSES = ("mitigated", "closed")  # risks we have dealt with; anything else is still open
SCORE_EXPLAINED = ("Score = likelihood x impact, each rated 1 to 5. "
                   f"A score of {HIGH_SCORE} or more is high; the maximum is 25.")


# ---------------------------------------------------------------------
# Reading files (plain Python)
# ---------------------------------------------------------------------
def read_table(path: Path) -> pd.DataFrame | None:
    """Read a CSV. Returns None if the file is missing or can't be read."""
    if not path.exists():
        return None
    try:
        return pd.read_csv(path)
    except (pd.errors.EmptyDataError, pd.errors.ParserError, UnicodeDecodeError):
        return None


def empty_register() -> pd.DataFrame:
    return pd.DataFrame(columns=REGISTER_COLUMNS + ["score_in_file"])


def load_register(path: Path = REGISTER_FILE) -> pd.DataFrame:
    """The risk register, cleaned and sorted with the highest score first.

    The score is always worked out again as likelihood x impact, so a typing
    mistake in the file can't make a risk look bigger or smaller than it is.
    """
    df = read_table(path)
    if df is None or df.empty:
        return empty_register()
    for col in REGISTER_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    df = df[REGISTER_COLUMNS].copy()
    for col in TEXT_COLUMNS:
        df[col] = df[col].fillna("").astype(str).str.strip()
    df["status"] = df["status"].str.lower()
    df["score_in_file"] = pd.to_numeric(df["score"], errors="coerce")
    df["likelihood"] = pd.to_numeric(df["likelihood"], errors="coerce")
    df["impact"] = pd.to_numeric(df["impact"], errors="coerce")
    df["score"] = (df["likelihood"] * df["impact"]).fillna(0).astype(int)
    df = df[(df["risk_id"] != "") | (df["risk"] != "")]  # drop blank lines
    return df.sort_values(["score", "risk_id"], ascending=[False, True],
                          kind="stable").reset_index(drop=True)


def register_problems(register: pd.DataFrame) -> list[str]:
    """Plain-language warnings about rows a teammate should fix."""
    notes = []
    for _, row in register.iterrows():
        name = row["risk_id"] or row["risk"] or "A row"
        ratings = [row["likelihood"], row["impact"]]
        if any(pd.isna(r) or r < 1 or r > 5 for r in ratings):
            notes.append(f"{name}: likelihood and impact must both be numbers from 1 to 5.")
        elif pd.notna(row["score_in_file"]) and int(row["score_in_file"]) != row["score"]:
            notes.append(f"{name}: the score in the file ({int(row['score_in_file'])}) is not "
                         f"likelihood x impact ({row['score']}). We use {row['score']}.")
    return notes


# ---------------------------------------------------------------------
# Summary (plain Python)
# ---------------------------------------------------------------------
def summarise(register: pd.DataFrame) -> dict:
    return {
        "total": len(register),
        "high": int((register["score"] >= HIGH_SCORE).sum()),
        "still_open": int((~register["status"].isin(DONE_STATUSES)).sum()),
        "top3": register.head(3),
    }


def summary_sentence(summary: dict) -> str:
    if summary["total"] == 0:
        return "No risks have been logged yet. Add rows to governance/risk_register.csv."
    return (f"We are tracking {summary['total']} risk{'s' if summary['total'] != 1 else ''}. "
            f"{summary['high']} {'is' if summary['high'] == 1 else 'are'} high "
            f"(score {HIGH_SCORE} or more) and {summary['still_open']} "
            f"{'is' if summary['still_open'] == 1 else 'are'} still open "
            "(not yet mitigated or closed).")


def top_risk_lines(register: pd.DataFrame, n: int = 3) -> list[str]:
    return [f"{r.risk_id} (score {r.score}): {r.risk}. Harms: {r.who_is_harmed}."
            for r in register.head(n).itertuples()]


# ---------------------------------------------------------------------
# Findings from teammates' files (plain Python)
# ---------------------------------------------------------------------
def _pick_column(df: pd.DataFrame, hints: tuple, numeric: bool) -> str | None:
    """First column whose name contains one of the hints and has the right type."""
    for col in df.columns:
        if any(h in str(col).lower() for h in hints) \
                and pd.api.types.is_numeric_dtype(df[col]) == numeric:
            return col
    return None


def _first_text_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            return col
    return None


def fairness_findings(df: pd.DataFrame | None) -> list[str]:
    """What the area fairness table says (waiting times by ward)."""
    if df is None or df.empty:
        return ["Area fairness results have not been added yet (governance/area_fairness.csv)."]
    label = _pick_column(df, ("ward", "area", "suburb"), numeric=False) or _first_text_column(df)
    value = _pick_column(df, ("wait", "hour", "resolve", "median", "mean", "average"), numeric=True)
    if label is None or value is None:
        return [f"Waiting times for {len(df)} area{'s' if len(df) != 1 else ''} are in governance/area_fairness.csv "
                "(see the chart in the dashboard)."]
    ordered = df.dropna(subset=[value]).sort_values(value)
    if ordered.empty:
        return ["The area fairness table has no waiting times yet."]
    low, high = ordered.iloc[0], ordered.iloc[-1]
    text = (f"Waiting time ({value}) is longest in {high[label]} ({high[value]:.1f}) "
            f"and shortest in {low[label]} ({low[value]:.1f})")
    if low[value] > 0:
        text += f", so the longest wait is {high[value] / low[value]:.1f} times the shortest"
    return [text + "."]


def language_findings(df: pd.DataFrame | None) -> list[str]:
    """What the per-language classifier results say."""
    if df is None or df.empty:
        return ["Language results have not been added yet (governance/bias_results_after.csv)."]
    label = _pick_column(df, ("language", "lang"), numeric=False) or _first_text_column(df)
    value = _pick_column(df, ("accuracy", "correct"), numeric=True)
    if label is None or value is None:
        return [f"Classifier results for {len(df)} languages are in "
                "governance/bias_results_after.csv."]
    ordered = df.dropna(subset=[value]).sort_values(value)
    if ordered.empty:
        return ["The language table has no accuracy figures yet."]
    scale = 100 if ordered[value].max() <= 1 else 1  # fractions become percentages
    low, high = ordered.iloc[0], ordered.iloc[-1]
    lo, hi = low[value] * scale, high[value] * scale
    return [f"The classifier is most accurate in {high[label]} ({hi:.0f}%) and least accurate "
            f"in {low[label]} ({lo:.0f}%), a gap of {hi - lo:.0f} percentage points."]


def cant_fix_lines(register: pd.DataFrame) -> list[str]:
    """Honest list of what is still open, for the report."""
    lines = []
    open_high = register[(register["score"] >= HIGH_SCORE)
                         & ~register["status"].isin(DONE_STATUSES)]
    for r in open_high.itertuples():
        lines.append(f"**{r.risk_id}: {r.risk}** (score {r.score}, owner {r.owner}, status "
                     f"{r.status or 'not set'}). Planned fix: {r.mitigation or 'not written yet'}")
    lines.append("All our data is synthetic, so our results show the method works, "
                 "not what is really happening in Alexandra.")
    lines.append("We cannot tell whether a quiet area has fewer problems or fewer residents "
                 "reporting them.")
    lines.append("We have not tested the system on real reports or with real residents.")
    return lines


# ---------------------------------------------------------------------
# The report (plain Python, no Streamlit)
# ---------------------------------------------------------------------
def _cell(value) -> str:
    """Make text safe inside a Markdown table cell."""
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _markdown_table(df: pd.DataFrame) -> str:
    header = "| " + " | ".join(df.columns) + " |"
    divider = "|" + "|".join(["---"] * len(df.columns)) + "|"
    rows = ["| " + " | ".join(_cell(v) for v in row) + " |" for row in df.itertuples(index=False)]
    return "\n".join([header, divider, *rows])


def build_risk_report(register: pd.DataFrame,
                      fairness: pd.DataFrame | None = None,
                      language: pd.DataFrame | None = None,
                      today: date | None = None,
                      top_n: int = 5) -> str:
    """A one-page Markdown report. Works with an empty register."""
    today = today or date.today()
    summary = summarise(register)
    parts = [
        "# Risk evaluation report",
        f"**Date:** {today.day} {today:%B %Y}  \n"
        "**Project:** Report Radar, Alexandra, Johannesburg (all data is synthetic)",
        "## Summary",
        summary_sentence(summary),
    ]
    lines = top_risk_lines(register)
    if lines:
        parts.append("The three biggest risks:\n\n" + "\n".join(f"- {line}" for line in lines))

    parts.append("## Top risks (highest score first)")
    if register.empty:
        parts.append("No risks have been logged yet.")
    else:
        top = register.head(top_n)
        table = pd.DataFrame({
            "Risk": top["risk"], "Score": top["score"], "Who is harmed": top["who_is_harmed"],
            "Evidence": top["evidence"], "Mitigation": top["mitigation"],
            "Owner": top["owner"], "Status": top["status"],
        })
        parts.append(_markdown_table(table))
        parts.append(f"_{SCORE_EXPLAINED}_")

    parts.append("## Fairness findings: waiting times by area")
    parts.append("\n".join(f"- {line}" for line in fairness_findings(fairness)))
    parts.append("## Language findings: classifier accuracy")
    parts.append("\n".join(f"- {line}" for line in language_findings(language)))
    parts.append("## What we can't fix yet")
    parts.append("\n".join(f"- {line}" for line in cant_fix_lines(register)))
    return "\n\n".join(parts) + "\n"


def latest_decisions(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    """The n newest rows of the decision log, newest first."""
    if "timestamp" in df.columns:
        stamps = pd.to_datetime(df["timestamp"], errors="coerce")
        if stamps.notna().any():
            return df.assign(_when=stamps).sort_values("_when", ascending=False) \
                     .drop(columns="_when").head(n)
    return df.tail(n).iloc[::-1]


# ---------------------------------------------------------------------
# The page (the only part that uses Streamlit)
# ---------------------------------------------------------------------
def _not_added(what: str, who: str, where: Path) -> None:
    st.info(f"{what} hasn't been added yet ({who}). It will appear here once "
            f"`{where.relative_to(ROOT).as_posix()}` exists.")


def show_risk_tab() -> None:
    st.subheader("Risk & compliance")
    st.caption("Everything that could go wrong with Report Radar, who it could hurt, and what "
               "we are doing about it. Written for managers: no technical knowledge needed.")

    register = load_register()
    fairness = read_table(FAIRNESS_CSV)
    language = read_table(LANGUAGE_FILE)

    # ----- 1. Summary -----
    summary = summarise(register)
    if summary["total"] == 0:
        st.info(summary_sentence(summary))
    elif summary["high"]:
        st.warning(summary_sentence(summary))
    else:
        st.success(summary_sentence(summary))
    c1, c2, c3 = st.columns(3)
    c1.metric("Risks tracked", summary["total"])
    c2.metric(f"High risks (score {HIGH_SCORE}+)", summary["high"])
    c3.metric("Still open", summary["still_open"])
    if summary["total"]:
        st.markdown("**The three biggest risks**")
        st.markdown("\n".join(f"- {line}" for line in top_risk_lines(register)))

    report = build_risk_report(register, fairness, language)
    st.download_button("Download risk evaluation report", data=report,
                       file_name=f"risk_evaluation_report_{date.today().isoformat()}.md",
                       mime="text/markdown")

    # ----- 2. Risk register -----
    st.divider()
    st.markdown("### All risks")
    st.caption(SCORE_EXPLAINED)
    if register.empty:
        _not_added("The risk register is empty or", "Role 5", REGISTER_FILE)
    else:
        for note in register_problems(register):
            st.warning(note)
        f1, f2 = st.columns(2)
        owners = sorted(o for o in register["owner"].unique() if o)
        statuses = sorted(s for s in register["status"].unique() if s)
        picked_owners = f1.multiselect("Owner", owners, placeholder="All owners")
        picked_status = f2.multiselect("Status", statuses, placeholder="All statuses")
        view = register
        if picked_owners:
            view = view[view["owner"].isin(picked_owners)]
        if picked_status:
            view = view[view["status"].isin(picked_status)]
        if view.empty:
            st.info("No risks match those filters. Clear a filter to see more.")
        else:
            table = view.rename(columns={
                "risk_id": "ID", "risk": "Risk", "area": "Area", "who_is_harmed": "Who is harmed",
                "likelihood": "Likelihood (1-5)", "impact": "Impact (1-5)", "score": "Score",
                "evidence": "Evidence", "mitigation": "What we did", "owner": "Owner",
                "status": "Status"}).drop(columns="score_in_file")
            st.caption(f"{len(view)} of {len(register)} risks, highest score first.")
            st.dataframe(table, hide_index=True, width="stretch")

    # ----- 3. Fairness and language -----
    st.divider()
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("### Do some areas wait longer?")
        if FAIRNESS_PNG.exists():
            st.image(str(FAIRNESS_PNG))
            st.caption("Waiting times by area. Large gaps could mean some residents are "
                       "served more slowly than others.")
        else:
            _not_added("The area fairness chart", "Role 2", FAIRNESS_PNG)
        if fairness is not None and not fairness.empty:
            with st.expander("Show the numbers"):
                st.dataframe(fairness, hide_index=True, width="stretch")
    with right:
        st.markdown("### Does the system work equally well in every language?")
        if language is None:
            _not_added("The language results", "Role 1", LANGUAGE_FILE)
        elif language.empty:
            st.info("The language results file has no rows yet.")
        else:
            st.dataframe(language, hide_index=True, width="stretch")
            st.caption("Accuracy is how often the system sorted a report into the right "
                       "problem type. A lower figure means that language is served worse.")

    # ----- 4. Decision log -----
    st.divider()
    st.markdown("### Latest decisions the system made")
    log = read_table(DECISION_LOG)
    if log is None:
        _not_added("The decision log", "Role 4", DECISION_LOG)
    elif log.empty:
        st.info("The decision log exists but has no decisions in it yet.")
    else:
        st.caption(f"The newest 20 of {len(log):,} decisions, with the reason for each.")
        st.dataframe(latest_decisions(log), hide_index=True, width="stretch")

    # ----- 5. Transparency notes -----
    with st.expander("Transparency notes: how the system makes decisions"):
        if TRANSPARENCY_NOTES.exists():
            st.markdown(TRANSPARENCY_NOTES.read_text(encoding="utf-8"))
        else:
            _not_added("The transparency notes", "Role 4", TRANSPARENCY_NOTES)