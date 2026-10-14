"""
Developer Pay Insights — client dashboard for MIE1624 Assignment 1 (Q4).

Every number shown here is read from data/summary.json and data/bootstrap.npz,
which build_data.py produces by re-running the notebook's exact code and seeds.
The app never loads individual survey responses.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Developer Pay Insights",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------- palette
NAVY = "#1E2A5A"
INDIGO = "#4F46E5"
INDIGO_LIGHT = "#E0E7FF"
TEAL = "#0D9488"
AMBER = "#D97706"
MUTED = "#64748B"
GRID = "#E6E8F0"
GROUP_COLORS = {"Remote": INDIGO, "Hybrid": TEAL,
                "Bachelor's": INDIGO, "Master's": TEAL, "Professional": AMBER}
BACH, MAST = "Bachelor's", "Master's"
EDU_ORDER = ["Bachelor's degree", "Master's degree", "Professional degree"]
EDU_SHORT = {"Bachelor's degree": "Bachelor's", "Master's degree": "Master's",
             "Professional degree": "Professional"}

st.markdown(
    f"""
<style>
  .block-container {{ padding-top: 2rem; max-width: 1250px; }}
  section[data-testid="stSidebar"] {{ background: {NAVY}; }}
  section[data-testid="stSidebar"] * {{ color: #E8EAF6 !important; }}
  section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.15); }}
  h1, h2, h3, h4 {{ color: {NAVY}; letter-spacing: -0.01em; }}
  .hero {{
      background: linear-gradient(120deg, {NAVY} 0%, #2E3A8C 55%, {INDIGO} 100%);
      color: #fff; border-radius: 18px; padding: 2rem 2.2rem; margin-bottom: 1.4rem;
  }}
  .hero h1 {{ color: #fff; margin: 0 0 .4rem 0; font-size: 2.1rem; }}
  .hero p {{ color: #DDE1FF; margin: 0; font-size: 1.05rem; max-width: 820px; }}
  .kpi {{
      background: #fff; border: 1px solid {GRID}; border-top: 4px solid {INDIGO};
      border-radius: 14px; padding: 1.05rem 1.15rem; height: 100%;
      box-shadow: 0 1px 2px rgba(30,42,90,.05);
  }}
  .kpi .label {{ color: {MUTED}; font-size: .78rem; text-transform: uppercase;
                 letter-spacing: .06em; font-weight: 600; }}
  .kpi .value {{ color: {NAVY}; font-size: 1.85rem; font-weight: 700; margin: .25rem 0; }}
  .kpi .sub {{ color: {MUTED}; font-size: .86rem; line-height: 1.35; }}
  .callout {{
      background: #F4F5FB; border-left: 4px solid {INDIGO}; border-radius: 10px;
      padding: .9rem 1.1rem; margin: .6rem 0 1rem 0; color: {NAVY};
  }}
  .callout.plain {{ border-left-color: {TEAL}; }}
  .callout.warn {{ border-left-color: {AMBER}; background: #FFF8EB; }}
  .callout b {{ color: {NAVY}; }}
  .tag {{ display:inline-block; background:{INDIGO_LIGHT}; color:{INDIGO}; font-weight:600;
          font-size:.75rem; padding:.15rem .55rem; border-radius:999px; margin-right:.35rem; }}
  div[data-testid="stTabs"] button p {{ font-weight: 600; }}
  .formula {{ font-family: ui-monospace, Menlo, monospace; font-size: .9rem;
              background:#F8F9FD; border:1px solid {GRID}; border-radius:8px; padding:.6rem .8rem; }}
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------- data
@st.cache_data
def load():
    root = Path(__file__).parent / "data"
    summary = json.loads((root / "summary.json").read_text())
    with np.load(root / "bootstrap.npz") as z:
        arrays = {k: z[k] for k in z.files}
    return summary, arrays


D, A = load()
Q1, Q2, Q3 = D["q1"], D["q2"], D["q3"]


# --------------------------------------------------------------------------- helpers
def tint(hex_color, alpha=0.2):
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return f"rgba({r},{g},{b},{alpha})"


def usd(x, dec=0):
    sign = "−" if x < 0 else ""
    return f"{sign}${abs(x):,.{dec}f}"


SUPERSCRIPT = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def pval(p, digits=2):
    """3.16e-41 -> '3.16 × 10⁻⁴¹'; ordinary values printed plainly."""
    if p >= 0.001:
        return f"{p:.4f}"
    mant, exp = f"{p:.{digits}e}".split("e")
    return f"{mant} × 10{str(int(exp)).translate(SUPERSCRIPT)}"


def kpi(label, value, sub):
    st.markdown(f'<div class="kpi"><div class="label">{label}</div>'
                f'<div class="value">{value}</div><div class="sub">{sub}</div></div>',
                unsafe_allow_html=True)


def callout(html, kind=""):
    st.markdown(f'<div class="callout {kind}">{html}</div>', unsafe_allow_html=True)


def style(fig, height=420, title=None, xtitle=None, ytitle=None, legend=True):
    fig.update_layout(
        height=height, template="plotly_white",
        title=dict(text=title, font=dict(size=16, color=NAVY), x=0, xanchor="left") if title else None,
        font=dict(family="Inter, system-ui, sans-serif", color=NAVY, size=13),
        margin=dict(l=10, r=20, t=60 if title else 20, b=10),
        plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
        hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=GRID, font=dict(color=NAVY)),
        showlegend=legend,
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)"),
        bargap=0.06,
    )
    fig.update_xaxes(title=xtitle, gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    fig.update_yaxes(title=ytitle, gridcolor=GRID, zerolinecolor=GRID, linecolor=GRID)
    return fig


def vline(fig, x, label, color=NAVY, dash="dash", pos="top right", row=None, col=None):
    kw = dict(row=row, col=col) if row else {}
    fig.add_vline(x=x, line=dict(color=color, dash=dash, width=2),
                  annotation=dict(text=label, font=dict(color=color, size=12)),
                  annotation_position=pos, **kw)


def hist(values, color, name, nbins=50, xfmt="$,.0f"):
    return go.Histogram(
        x=values, nbinsx=nbins, name=name, marker=dict(color=color, line=dict(color="#fff", width=1)),
        opacity=0.9, hovertemplate=f"%{{x:{xfmt}}}<br>%{{y}} replications<extra>{name}</extra>",
    )


def table(df, fmt):
    st.dataframe(df.style.format(fmt), hide_index=True, width="stretch")


# --------------------------------------------------------------------------- sidebar
PAGES = [
    "Executive summary",
    "1 · Roles, satisfaction & pay",
    "2 · Remote vs. hybrid pay",
    "3 · Education & pay",
    "Methods, data & limitations",
]
with st.sidebar:
    st.markdown("### 📊 Developer Pay Insights")
    st.caption("Remote-work, compensation and hiring evidence from the "
               "2025 Stack Overflow Developer Survey")
    st.markdown("---")
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
    st.markdown("---")
    st.caption(f"**Survey sample:** {D['meta']['rows']:,} respondents with reported salary")
    st.caption(f"**Bootstrap:** {D['meta']['bootstrap_reps']:,} replications, fixed seeds")
    st.caption("All figures are aggregates; no individual responses are published.")


W, ST, BT, CI, MD = Q2["welch"], Q2["student"], Q2["bootstrap"], Q2["ci"], Q2["mood"]
PAIRS = Q3["pairs"]


# =========================================================================== EXEC
def page_summary():
    st.markdown(
        """<div class="hero"><h1>Developer Pay Insights</h1>
        <p>What the 2025 Stack Overflow Developer Survey tells us about pay for remote versus
        hybrid developers, and the pay premium attached to advanced degrees in North America.
        Prepared to support your review of remote-work, compensation and hiring policy.</p></div>""",
        unsafe_allow_html=True,
    )

    c = st.columns(4)
    with c[0]:
        kpi("Remote pay premium (mean)", usd(W["mean_diff"]),
            f"Remote vs. hybrid, per year. 95% CI {usd(CI['welch'][0])} – {usd(CI['welch'][1])}")
    with c[1]:
        kpi("Remote pay premium (median)", usd(MD["obs_median_diff"]),
            f"Median {usd(MD['median_r'])} remote vs. {usd(MD['median_h'])} hybrid")
    with c[2]:
        kpi("Master's vs. Bachelor's", "+" + usd(PAIRS["Master's − Bachelor's"]["mean"]),
            "US & Canada, bootstrap mean difference; 95% CI excludes zero")
    with c[3]:
        kpi("Professional vs. Master's", "+" + usd(PAIRS["Professional − Master's"]["mean"]),
            "Not statistically conclusive: the 95% CI includes zero")

    st.markdown("#### Key takeaways")
    l, r = st.columns([1.15, 1])
    with l:
        st.markdown(
            f"""
1. **Remote developers earn more than hybrid developers.** After removing the top 1% of
   salaries in each group, remote workers averaged **{usd(W['mean_r'])}** versus
   **{usd(W['mean_h'])}** for hybrid workers, a gap of **{usd(W['mean_diff'])}** a year.
   Every method we used (two t-tests, a bootstrap test, a bootstrap confidence interval
   and a median test) agrees the gap is real and not a sampling fluke.
2. **The gap holds for typical workers, not only top earners.** The median remote salary is
   **{usd(MD['obs_median_diff'])}** higher, and {MD['pct_above_r']:.1%} of remote workers earn
   above the overall median, against {MD['pct_above_h']:.1%} of hybrid workers.
3. **Advanced degrees carry a pay premium in North America.** Master's holders earn about
   **{usd(PAIRS["Master's − Bachelor's"]['mean'])}** and Professional-degree holders about
   **{usd(PAIRS["Professional − Bachelor's"]['mean'])}** more on average than Bachelor's
   holders. The ANOVA (F = {Q3['anova']['F']:.2f}, p = {pval(Q3['anova']['p'])}) confirms
   that education groups differ.
4. **A Professional degree does not clearly beat a Master's.** The estimated
   {usd(PAIRS["Professional − Master's"]['mean'])} difference has a 95% interval from
   {usd(PAIRS["Professional − Master's"]['ci'][0])} to {usd(PAIRS["Professional − Master's"]['ci'][1])},
   so the data cannot rule out no difference.
5. **Averages are distorted by a handful of extreme salaries.** Reported salaries reach
   {usd(Q2['box']['Remote']['max'] / 1e6, 2)}M, which inflates role averages (Financial
   analysts: mean {usd(Q1['job_salary'][0]['mean_salary'])} vs. median
   {usd(Q1['job_salary'][0]['median_salary'])}). Benchmark with medians.
""".replace("$", r"\$")  # stop Streamlit reading "$...$" as LaTeX
        )
    with r:
        st.markdown("#### What this means for your policies")
        callout(
            "<b>Remote-work policy.</b> Remote roles are associated with higher pay in the "
            "market. Moving roles from remote to hybrid without adjusting pay may make offers "
            "less competitive. The survey shows an <i>association</i>, though, and not the effect "
            "of switching any one employee's work mode.")
        callout(
            "<b>Compensation benchmarking.</b> Use medians and trimmed figures, not raw averages. "
            "One extreme response can move a role's average by hundreds of thousands of dollars.",
            "plain")
        callout(
            "<b>Hiring.</b> Budget a premium for Master's-level candidates in North America. "
            "The evidence does not support paying Professional-degree holders more than "
            "Master's holders by default.", "plain")
        callout(
            "<b>Read with care.</b> The survey is self-reported and mixes countries, seniority "
            "levels and roles, so these comparisons do not adjust for those factors.", "warn")

    st.markdown("#### The two headline comparisons at a glance")
    g1, g2 = st.columns(2)
    with g1:
        fig = go.Figure()
        for name, key in (("Hybrid", "mean_h"), ("Remote", "mean_r")):
            fig.add_bar(y=[name], x=[W[key]], orientation="h", marker_color=GROUP_COLORS[name],
                        text=[usd(W[key])], textposition="inside", insidetextanchor="end",
                        textfont=dict(color="#fff"), name=name,
                        hovertemplate=f"{name}: %{{x:$,.0f}}<extra></extra>")
        style(fig, 230, "Mean salary after trimming top 1% (USD)", legend=False)
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig, width="stretch")
    with g2:
        fig = go.Figure()
        for name in ["Bachelor's", "Master's", "Professional"]:
            b = Q3["bootstrap"][name]
            fig.add_bar(y=[name], x=[b["observed"]], orientation="h", name=name,
                        marker_color=GROUP_COLORS[name],
                        error_x=dict(type="data", symmetric=False, color=NAVY, thickness=1.5,
                                     array=[b["ci"][1] - b["observed"]],
                                     arrayminus=[b["observed"] - b["ci"][0]]),
                        hovertemplate=(f"{name}: %{{x:$,.0f}}<br>95% CI {usd(b['ci'][0])} – "
                                       f"{usd(b['ci'][1])}<extra></extra>"))
        style(fig, 230, "Mean salary by degree, US & Canada (with 95% bootstrap CI)", legend=False)
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        fig.update_yaxes(categoryorder="array", categoryarray=["Professional", "Master's", "Bachelor's"])
        st.plotly_chart(fig, width="stretch")


# =========================================================================== Q1
def page_q1():
    st.title("1 · Roles, satisfaction & pay")
    st.markdown("A first look at the full survey sample: how satisfied each job title is, "
                "what each title earns, and how pay changes with age.")
    with st.expander("How the data were prepared for this section"):
        st.markdown(
            f"""
- **Age:** five implausible ages (1, 3, 9, 126 and 151) were treated as missing; ages 18–100
  were kept. ({Q1['cleaning']['age_missing_after']} ages missing after cleaning.)
- **Job satisfaction:** one response of 60, outside the 0–10 scale, was treated as missing.
  ({Q1['cleaning']['jobsat_missing_after']:,} satisfaction scores missing after cleaning.)
- **Minimum sample size:** job titles with fewer than 30 valid responses are left out of the
  satisfaction and salary charts so that very small groups do not mislead.
- **Salaries:** extreme salaries are kept here on purpose to show how they affect averages.
  Medians are shown next to means for comparison.
"""
        )

    t1, t2, t3 = st.tabs(["Figure 1 · Job satisfaction", "Figure 2 · Salary by role",
                          "Figure 3 · Salary vs. age"])

    with t1:
        js = pd.DataFrame(Q1["job_satisfaction"])
        jf = js[js["respondent_count"] >= 30].sort_values("mean_satisfaction")
        fig = go.Figure(go.Bar(
            x=jf["mean_satisfaction"], y=jf["DevType"], orientation="h",
            marker=dict(color=[AMBER if v == jf["mean_satisfaction"].min() else
                               (NAVY if v == jf["mean_satisfaction"].max() else INDIGO)
                               for v in jf["mean_satisfaction"]]),
            customdata=jf["respondent_count"],
            hovertemplate="<b>%{y}</b><br>Average satisfaction: %{x:.2f}/10"
                          "<br>Responses: %{customdata:,}<extra></extra>"))
        style(fig, 760, "Average job satisfaction by job title (n ≥ 30)",
              "Average job satisfaction (0–10)", None, legend=False)
        fig.update_xaxes(range=[0, 10])
        st.plotly_chart(fig, width="stretch")
        callout(
            "<b>Diagnostic interpretation.</b> Among job titles with at least 30 valid responses, "
            "senior executives reported the highest average job satisfaction (8.11), while QA/test "
            "developers reported the lowest (6.54); categories with fewer than 30 responses were "
            "excluded to reduce the influence of very small samples.")
        callout(
            "<b>What it means for you.</b> Satisfaction is fairly flat across most technical roles "
            "(roughly 7 out of 10). Leadership roles sit at the top and QA/testing at the bottom, "
            "which makes QA a good candidate for retention attention. The excluded small groups "
            "(for example a single 'Retired' respondent scoring 10) show why tiny samples were "
            "removed.", "plain")
        with st.expander("Show the table for all job titles"):
            table(js.rename(columns={"DevType": "Job title", "mean_satisfaction": "Mean satisfaction",
                                     "respondent_count": "Responses"}),
                  {"Mean satisfaction": "{:.3f}", "Responses": "{:,}"})

    with t2:
        jsal = pd.DataFrame(Q1["job_salary"])
        sf = jsal[jsal["respondent_count"] >= 30].sort_values("mean_salary")
        fig = go.Figure()
        fig.add_bar(x=sf["mean_salary"], y=sf["DevType"], orientation="h", name="Mean salary",
                    marker_color=INDIGO,
                    customdata=np.stack([sf["median_salary"], sf["respondent_count"],
                                         sf["mean_median_ratio"]], axis=1),
                    hovertemplate="<b>%{y}</b><br>Mean: %{x:$,.0f}<br>Median: %{customdata[0]:$,.0f}"
                                  "<br>Mean ÷ median: %{customdata[2]:.2f}"
                                  "<br>Respondents: %{customdata[1]:,}<extra></extra>")
        fig.add_scatter(x=sf["median_salary"], y=sf["DevType"], mode="markers", name="Median salary",
                        marker=dict(symbol="diamond", size=10, color=AMBER,
                                    line=dict(color="#fff", width=1.5)),
                        hovertemplate="<b>%{y}</b><br>Median: %{x:$,.0f}<extra></extra>")
        style(fig, 820, "Mean salary by job title (n ≥ 30)", "Annual salary (USD)")
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig, width="stretch")
        callout(
            "<b>Diagnostic interpretation.</b> Financial analysts and engineers have the highest "
            "mean salary ($501,248), but their substantially lower median ($87,249) suggests that "
            "extreme high-income observations inflate the average and may distort comparisons "
            "across job titles.")
        callout(
            "<b>What it means for you.</b> Where the orange diamond sits far left of the bar's end, "
            "a few very high salaries are pulling the average up. Financial analysts (mean 5.7× "
            "the median), system administrators and senior executives are the clearest cases. "
            "For pay benchmarking, the median is the more reliable figure.", "plain")
        with st.expander("Show the table for all job titles"):
            table(jsal.rename(columns={"DevType": "Job title", "mean_salary": "Mean",
                                       "median_salary": "Median", "respondent_count": "Respondents",
                                       "max_salary": "Max", "mean_median_ratio": "Mean ÷ median"}),
                  {"Mean": "${:,.0f}", "Median": "${:,.0f}", "Respondents": "{:,}",
                   "Max": "${:,.0f}", "Mean ÷ median": "{:.2f}"})

    with t3:
        a = Q1["age_salary"]
        counts = np.array(a["counts"], dtype=float).T          # rows = salary bins
        age_mid = (np.array(a["age_edges"][:-1]) + np.array(a["age_edges"][1:])) / 2
        log_mid = (np.array(a["log_edges"][:-1]) + np.array(a["log_edges"][1:])) / 2
        z = np.log10(np.where(counts > 0, counts, np.nan))
        hover = np.vectorize(lambda c: f"{int(c):,}")(counts)
        sal_lo = np.vectorize(lambda v: usd(10 ** v))(np.array(a["log_edges"][:-1]))
        sal_hi = np.vectorize(lambda v: usd(10 ** v))(np.array(a["log_edges"][1:]))
        cd = np.dstack([hover, np.repeat(sal_lo[:, None], len(age_mid), 1),
                        np.repeat(sal_hi[:, None], len(age_mid), 1)])
        fig = go.Figure(go.Heatmap(
            x=age_mid, y=log_mid, z=z, customdata=cd,
            colorscale=[[0, "#EEF0FF"], [0.45, "#8B8FF0"], [0.8, INDIGO], [1, NAVY]],
            colorbar=dict(title="Respondents", tickvals=[0, 1, 2, 3],
                          ticktext=["1", "10", "100", "1,000"], thickness=12),
            hovertemplate="Age %{x:.0f} (±1)<br>Salary %{customdata[1]}–%{customdata[2]}"
                          "<br>Respondents: %{customdata[0]}<extra></extra>"))
        bands = pd.DataFrame(a["bands"])
        band_x = [21, 29.5, 39.5, 49.5, 59.5, 82]
        fig.add_scatter(x=band_x, y=np.log10(bands["median"]), mode="lines+markers",
                        name="Median salary by age band",
                        line=dict(color=AMBER, width=2.5), marker=dict(size=9, color=AMBER,
                                                                         line=dict(color="#fff", width=1.5)),
                        customdata=np.stack([bands["band"], bands["median"], bands["n"]], axis=1),
                        hovertemplate="Ages %{customdata[0]}<br>Median %{customdata[1]:$,.0f}"
                                      "<br>n = %{customdata[2]:,}<extra></extra>")
        ticks = [2, 3, 4, 5, 6, 7]
        style(fig, 520, f"Annual salary vs. age (n = {a['n']:,}; log salary scale)",
              "Age (years)", "Annual salary (USD, log scale)")
        fig.update_yaxes(tickvals=ticks, ticktext=["$100", "$1K", "$10K", "$100K", "$1M", "$10M"])
        st.plotly_chart(fig, width="stretch")
        st.caption("To protect respondents' privacy, individual points are shown as counts in "
                   "2-year × 0.1-log-salary cells instead of as a scatter plot. Darker cells hold "
                   "more respondents.")
        callout(
            "<b>Diagnostic interpretation.</b> Annual salaries generally appear to increase from "
            "early adulthood into middle age, but substantial variation within age groups and "
            "several extreme high-income outliers suggest that age alone does not explain salary "
            "differences.")
        callout(
            "<b>What it means for you.</b> Pay rises with age up to about the mid-40s and then "
            "levels off. Within any age group, salaries still span more than 100-fold (from under "
            "$1K to over $1M), because country, role and seniority matter far more than age. "
            "The isolated cells above $10M are almost certainly data-entry anomalies.", "plain")
        table(bands.rename(columns={"band": "Age band", "n": "Respondents", "p25": "25th pct",
                                    "median": "Median", "p75": "75th pct", "mean": "Mean"}),
              {"Respondents": "{:,}", "25th pct": "${:,.0f}", "Median": "${:,.0f}",
               "75th pct": "${:,.0f}", "Mean": "${:,.0f}"})


# =========================================================================== Q2
def page_q2():
    st.title("2 · Remote vs. hybrid pay")
    st.markdown(
        f"Do fully remote developers earn more than hybrid developers? The comparison covers "
        f"**{Q2['counts']['Remote']:,} remote** and **{Q2['counts']['Hybrid']:,} hybrid** "
        "respondents worldwide.")
    tabs = st.tabs(["a · Descriptives & outliers", "b · t-tests", "c · Bootstrap",
                    "d · Bootstrap test", "e · Confidence intervals", "f · Medians",
                    "Sensitivity check"])

    # ---------------------------------------------------------------- a
    with tabs[0]:
        st.subheader("Descriptive statistics (all responses)")
        desc = pd.DataFrame(Q2["descriptive"]).rename(columns={
            "RemoteWork": "Work mode", "count": "Count", "mean": "Mean", "median": "Median",
            "std": "Std. dev.", "min": "Min", "max": "Max"})
        money_cols = ["Mean", "Median", "Std. dev.", "Min", "Max", "Q1", "Q3", "P95", "P99"]
        table(desc, {"Count": "{:,}", **{c: "${:,.2f}" for c in money_cols}})

        c1, c2 = st.columns(2)
        for col, key, title in ((c1, "box", "All responses"),
                                (c2, "box_trimmed", "After removing top 1% per group")):
            with col:
                fig = go.Figure()
                for name in ["Remote", "Hybrid"]:
                    b = Q2[key][name]
                    fig.add_trace(go.Box(
                        x=[name], q1=[b["q1"]], median=[b["median"]], q3=[b["q3"]],
                        lowerfence=[b["lowerfence"]], upperfence=[b["upperfence"]], name=name,
                        marker_color=GROUP_COLORS[name], fillcolor=tint(GROUP_COLORS[name]),
                        line=dict(width=2), boxpoints=False))
                    fig.add_scatter(x=[name], y=[b["max"]], mode="markers", showlegend=False,
                                    marker=dict(symbol="triangle-up", size=11,
                                                color=GROUP_COLORS[name]),
                                    hovertemplate=f"{name} maximum: %{{y:$,.0f}}<br>"
                                                  f"{b['n_outliers_high']} high outliers beyond "
                                                  f"the whisker<extra></extra>")
                style(fig, 400, f"Salary distribution, log scale: {title}", None,
                      "Annual salary (USD, log scale)", legend=False)
                fig.update_yaxes(type="log", tickprefix="$")
                st.plotly_chart(fig, width="stretch")
        st.caption("Boxes show the 25th–75th percentiles with the median line; whiskers extend "
                   "to 1.5× the box height. Triangles mark each group's maximum salary.")

        st.subheader("Outlier treatment")
        thr = Q2["p99_thresholds"]
        trimmed = pd.DataFrame(Q2["trimmed"]).rename(columns={
            "RemoteWork": "Work mode", "count": "Count", "mean": "Mean", "median": "Median",
            "std": "Std. dev."})
        trimmed.insert(1, "Removed", trimmed["Work mode"].map(Q2["removed"]))
        trimmed.insert(2, "99th pct. cut-off", trimmed["Work mode"].map(thr))
        table(trimmed, {"Count": "{:,}", "Removed": "{:,}", "99th pct. cut-off": "${:,.2f}",
                        "Mean": "${:,.2f}", "Median": "${:,.2f}", "Std. dev.": "${:,.2f}"})
        callout(
            "<b>Rationale.</b> Both hybrid and remote salary distributions are strongly "
            f"right-skewed, with extreme maximum salaries of approximately "
            f"{usd(Q2['box']['Hybrid']['max'] / 1e6, 2)} million and "
            f"{usd(Q2['box']['Remote']['max'] / 1e6, 2)} million, respectively. To reduce the "
            "influence of extreme observations, salaries above the 99th percentile within each "
            f"group were excluded from the primary analysis, removing {Q2['removed']['Hybrid']} "
            f"hybrid and {Q2['removed']['Remote']} remote observations. After trimming, mean "
            f"salaries were {usd(W['mean_h'])} for hybrid workers and {usd(W['mean_r'])} for "
            f"remote workers, compared with {usd(Q2['descriptive'][0]['mean'])} and "
            f"{usd(Q2['descriptive'][1]['mean'])} before trimming. Although this substantially "
            "reduced the standard deviations, remote workers continued to have a higher mean "
            "salary. Because trimming changes the target population and high salaries are not "
            "necessarily erroneous, the untrimmed results should also be considered as a "
            "sensitivity check.")
        callout(
            "<b>In plain terms.</b> About 1 in 100 responses in each group reported salaries so "
            "large (e.g. $33.5 million) that they would dominate any average. Setting them aside "
            "makes the comparison about typical developers. The 'Sensitivity check' tab shows "
            "that the conclusion is the same with them included.", "plain")

    # ---------------------------------------------------------------- b
    with tabs[1]:
        st.subheader("Hypotheses")
        st.markdown("**H₀:** μ<sub>Remote</sub> = μ<sub>Hybrid</sub> &nbsp;&nbsp; "
                    "**H₁:** μ<sub>Remote</sub> ≠ μ<sub>Hybrid</sub> &nbsp;&nbsp; "
                    "two-sided, α = 0.05", unsafe_allow_html=True)

        AS = Q2["assumptions"]
        st.subheader("Step 1 · Group means and variances")
        table(pd.DataFrame({
            "Group": ["Remote", "Hybrid"], "Sample size": [W["n_r"], W["n_h"]],
            "Mean": [W["mean_r"], W["mean_h"]], "Variance": [AS["var_r"], AS["var_h"]],
            "Std. dev.": [AS["sd_r"], AS["sd_h"]]}),
            {"Sample size": "{:,}", "Mean": "${:,.2f}", "Variance": "{:.6e}", "Std. dev.": "${:,.2f}"})

        st.subheader("Step 2 · Manual calculations")
        m1, m2 = st.columns(2)
        with m1:
            st.markdown("##### Welch's t-test (unequal variances), the primary test")
            st.markdown(
                f"""<div class="formula">
SE = √(s²ᵣ/nᵣ + s²ₕ/nₕ) = <b>{W['se_diff']:,.4f}</b><br>
t = (x̄ᵣ − x̄ₕ) / SE = {W['mean_diff']:,.2f} / {W['se_diff']:,.4f} = <b>{W['t']:.4f}</b><br>
df (Welch–Satterthwaite) = <b>{W['df']:,.2f}</b><br>
p = 2·P(T > |t|) = <b>{W['p']:.6e}</b></div>""", unsafe_allow_html=True)
        with m2:
            st.markdown("##### Student's t-test (pooled variance)")
            st.markdown(
                f"""<div class="formula">
s²ₚ = [(nᵣ−1)s²ᵣ + (nₕ−1)s²ₕ] / (nᵣ+nₕ−2) = {ST['pooled_var']:.6e}<br>
sₚ (pooled SD) = <b>{ST['pooled_std']:,.2f}</b><br>
SE = sₚ·√(1/nᵣ + 1/nₕ) = {ST['se_pooled']:,.4f}<br>
t = <b>{ST['t']:.4f}</b>, df = {ST['df']:,}, p = <b>{ST['p']:.6e}</b></div>""",
                unsafe_allow_html=True)

        st.subheader("Step 3 · Manual vs. built-in (SciPy) results")
        cmp = pd.DataFrame({
            "Test": ["Welch (manual)", "Welch (scipy.stats.ttest_ind, equal_var=False)",
                     "Student (manual)", "Student (scipy.stats.ttest_ind, equal_var=True)"],
            "t-statistic": [W["t"], W["scipy_t"], ST["t"], ST["scipy_t"]],
            "p-value": [W["p"], W["scipy_p"], ST["p"], ST["scipy_p"]],
        })
        table(cmp, {"t-statistic": "{:.4f}", "p-value": "{:.6e}"})
        callout(
            "<b>Discrepancies.</b> None between the manual and built-in calculations: each pair "
            "agrees to the displayed precision. The slight difference between the two "
            "t-statistics arises from their variance assumptions. Student's t-test uses a pooled "
            "variance estimate under the equal-variance assumption, whereas Welch's t-test uses "
            "separate sample variances and adjusted degrees of freedom. Despite these "
            "differences, both tests lead to the same conclusion of a statistically significant "
            "difference in mean salaries.")

        st.subheader("Assumption checks")
        a1, a2, a3 = st.columns(3)
        with a1:
            kpi("Variance ratio", f"{AS['variance_ratio']:.4f}", "Larger ÷ smaller sample variance")
        with a2:
            kpi("Levene statistic", f"{AS['levene_stat']:.4f}",
                f"p = {pval(AS['levene_p'])}: variances differ")
        with a3:
            kpi("Independence & normality", "Reasonable",
                "Independent respondents; large n makes the sample mean approximately normal")
        callout(
            "<b>Assumption check.</b> The analysis assumes independent survey responses within "
            "and across the two groups. Although salary distributions were right-skewed, the "
            "large sample sizes support an approximately normal sampling distribution of the "
            "difference in means. Levene's test indicated unequal group variances (statistic = "
            f"{AS['levene_stat']:.4f}, p = {pval(AS['levene_p'])}; variance ratio = "
            f"{AS['variance_ratio']:.4f}). Therefore, Welch's t-test was preferred because it does "
            "not assume equal population variances. Student's pooled-variance t-test was also "
            "calculated to satisfy the assignment requirements.")

        st.subheader("What the p-value means")
        callout(
            f"<b>Meaning of the p-value.</b> The Welch's t-test p-value represents the probability "
            f"of obtaining a t-statistic whose absolute value is at least as large as the observed "
            f"value (|t| = {W['t']:.2f}), assuming the null hypothesis of equal population mean "
            "salaries is true. Because this probability is far below the 0.05 significance level, "
            "we reject the null hypothesis. This provides strong statistical evidence that remote "
            "and hybrid workers have different population mean salaries. However, the p-value is "
            "not the probability that the null hypothesis is true, nor does it measure the "
            "magnitude or practical importance of the difference. The observed mean difference "
            f"({usd(W['mean_diff'])}) and its confidence interval provide more information about "
            "the size and precision of the estimated difference.")
        callout(
            f"<b>In plain terms.</b> If remote and hybrid developers truly earned the same on "
            f"average, a gap as large as {usd(W['mean_diff'])} would appear by chance about "
            f"{pval(W['p'])} of the time, which is effectively never. The gap is real. Whether "
            "it matters for your budget is a separate question, answered by its size and the "
            "confidence interval (tab e).", "plain")

    # ---------------------------------------------------------------- c
    with tabs[2]:
        st.markdown(
            f"We resampled each group **{BT['B']:,} times** with replacement, each time drawing "
            f"as many workers as the group contains ({W['n_r']:,} remote, {W['n_h']:,} hybrid), "
            "and recorded the mean salary. The spread of those means shows how much the estimate "
            "could move with a different sample.")
        bins = st.slider("Histogram bins", 20, 100, 50, 5, key="q2bins")

        # Figure 1
        fig = go.Figure()
        fig.add_trace(hist(A["q2_boot_hybrid"], TEAL, "Hybrid", bins))
        fig.add_trace(hist(A["q2_boot_remote"], INDIGO, "Remote", bins))
        vline(fig, W["mean_h"], f"Hybrid observed {usd(W['mean_h'])}", TEAL, pos="top left")
        vline(fig, W["mean_r"], f"Remote observed {usd(W['mean_r'])}", INDIGO)
        style(fig, 420, "Figure 1 · Bootstrap distributions of mean salary",
              "Bootstrap mean annual salary (USD)", "Replications")
        fig.update_layout(barmode="overlay")
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig, width="stretch")
        callout(
            "<b>Figure 1.</b> A total of 10,000 bootstrap replications were performed "
            "independently for remote and hybrid workers, with each resample matching its "
            "original group size. The bootstrap mean salaries were approximately "
            f"{usd(BT['remote_mean'], 2)} for remote workers and {usd(BT['hybrid_mean'], 2)} for "
            "hybrid workers. Both distributions were approximately bell-shaped and centered near "
            "their respective observed sample means. <i>The two distributions do not overlap at "
            "all.</i>")

        # Figure 2
        fig = go.Figure(hist(A["q2_boot_diffs"], INDIGO, "Remote − Hybrid", bins))
        vline(fig, W["mean_diff"], f"Observed {usd(W['mean_diff'])}", NAVY)
        vline(fig, 0, "No difference", MUTED, "dot", "top left")
        style(fig, 400, "Figure 2 · Bootstrap distribution of the mean difference (Remote − Hybrid)",
              "Mean difference (USD)", "Replications", legend=False)
        fig.update_xaxes(tickprefix="$", tickformat=",.0f")
        st.plotly_chart(fig, width="stretch")
        callout(
            f"<b>Figure 2.</b> The observed mean salary difference (Remote − Hybrid) was "
            f"{usd(W['mean_diff'], 2)}, while the bootstrap mean difference was "
            f"{usd(BT['diff_mean'], 2)}, with a bootstrap standard error of {usd(BT['se'], 2)}. "
            "The bootstrap distribution was approximately symmetric and centered near the observed "
            "difference. The distribution was far from zero, suggesting that the estimated salary "
            "difference is large relative to its sampling variability.")

        # Figure 3
        std_diffs = (A["q2_boot_diffs"] - A["q2_boot_diffs"].mean()) / A["q2_boot_diffs"].std(ddof=1)
        fig = go.Figure(hist(std_diffs, "#7C73E6", "Standardized", bins, ".2f"))
        xs = np.linspace(-4.5, 4.5, 300)
        width = (std_diffs.max() - std_diffs.min()) / bins
        fig.add_scatter(x=xs, y=len(std_diffs) * width * np.exp(-xs ** 2 / 2) / np.sqrt(2 * np.pi),
                        mode="lines", line=dict(color=NAVY, width=2), name="Standard normal",
                        hoverinfo="skip")
        vline(fig, 0, "Bootstrap center", NAVY)
        style(fig, 400, "Figure 3 · Standardized bootstrap distribution of the mean difference",
              "Standardized mean difference (z)", "Replications")
        st.plotly_chart(fig, width="stretch")
        callout(
            "<b>Figure 3.</b> The bootstrap mean differences were standardized by subtracting the "
            "bootstrap mean difference and dividing by the bootstrap standard error. The resulting "
            f"distribution was approximately bell-shaped, with a mean of {BT['std_mean']:.4f} and a "
            f"standard deviation of {BT['std_sd']:.4f}. This transformation facilitates the "
            "examination of sampling variability on a standardized scale. The zero-centered "
            "distribution results from standardization and does not imply that the original group "
            "means are equal. <i>The close fit to the standard-normal curve supports using "
            "t-based methods here.</i>")
        callout(
            "<b>Overall.</b> The bootstrap results consistently indicate that remote workers have "
            "a higher estimated mean annual salary than hybrid workers in the trimmed dataset. "
            "Formal statistical significance is evaluated separately in Q2(d).", "plain")

    # ---------------------------------------------------------------- d
    with tabs[3]:
        BTT = Q2["boot_ttest"]
        k1, k2, k3 = st.columns(3)
        with k1:
            kpi("Observed Welch t", f"{BTT['observed_t']:.4f}", "From the original (trimmed) data")
        with k2:
            kpi("Bootstrap p-value", f"{BTT['p']:.6f}",
                f"(0 + 1) / ({D['meta']['bootstrap_reps']:,} + 1); the smallest possible value")
        with k3:
            kpi("Decision at α = 0.05", "Reject H₀", "Same conclusion as Q2(b)")
        fig = go.Figure(hist(A["q2_boot_t"], INDIGO, "Bootstrap t under H₀", 50, ".2f"))
        vline(fig, BTT["observed_t"], f"Observed t = {BTT['observed_t']:.2f}", AMBER)
        vline(fig, 0, "Null hypothesis", MUTED, "dot", "top left")
        style(fig, 400, "Bootstrap distribution of Welch's t-statistic under H₀",
              "Bootstrap t-statistic", "Replications", legend=False)
        st.plotly_chart(fig, width="stretch")
        st.markdown(
            "**Method.** Each group was shifted so its mean is zero, which makes the null "
            "hypothesis true by construction while keeping each group's spread and shape. "
            "Resampling 10,000 times (seed 123) shows how large t gets by chance alone.")
        callout(
            "A bootstrap-based Welch's t-test was performed using 10,000 resamples under the null "
            "hypothesis of equal population means. For each bootstrap replication, a studentized "
            "t-statistic was calculated and compared with the observed t-statistic. The observed "
            f"t-statistic was {BTT['observed_t']:.4f}, and the bootstrap Monte Carlo p-value was "
            "approximately 0.0001. Since the p-value was below the significance level of 0.05, the "
            "null hypothesis was rejected. This conclusion is consistent with Q2(b), where Welch's "
            f"two-sample t-test yielded t = {W['t']:.4f} and p &lt; 0.001. Both methods provide "
            "strong evidence of a statistically significant difference in mean annual salaries "
            "between remote and hybrid workers.")
        callout(
            f"<b>In plain terms.</b> In 10,000 simulated worlds where remote and hybrid pay are "
            f"equal, the largest t we ever saw was {BTT['max_abs_boot_t']:.2f}; the real data gave "
            f"{BTT['observed_t']:.2f}. The bootstrap p-value of 0.0001 is a floor set by the number "
            f"of replications, while the formula-based p-value ({pval(W['p'])}) can go much lower. "
            "Both say the same thing.", "plain")

    # ---------------------------------------------------------------- e
    with tabs[4]:
        k1, k2 = st.columns(2)
        with k1:
            kpi("95% CI · Welch t-based (formula)",
                f"{usd(CI['welch'][0], 2)} – {usd(CI['welch'][1], 2)}",
                f"Observed difference ± t* × SE, with t* = {CI['t_crit']:.4f}")
        with k2:
            kpi("95% CI · Bootstrap percentile",
                f"{usd(CI['bootstrap'][0], 2)} – {usd(CI['bootstrap'][1], 2)}",
                "2.5th and 97.5th percentiles of the 10,000 bootstrap differences")
        fig = go.Figure()
        for i, (name, lohi, color) in enumerate((("Bootstrap percentile", CI["bootstrap"], TEAL),
                                                 ("Welch t-based", CI["welch"], INDIGO))):
            fig.add_scatter(
                x=[W["mean_diff"]], y=[name], mode="markers", name=name,
                marker=dict(size=13, color=color, line=dict(color="#fff", width=2)),
                error_x=dict(type="data", symmetric=False, array=[lohi[1] - W["mean_diff"]],
                             arrayminus=[W["mean_diff"] - lohi[0]], color=color, thickness=3, width=10),
                hovertemplate=f"{name}<br>{usd(lohi[0], 2)} – {usd(lohi[1], 2)}<extra></extra>")
        vline(fig, 0, "No difference", MUTED, "dot", "top right")
        style(fig, 300, "95% confidence intervals for the mean salary difference (Remote − Hybrid)",
              "Mean salary difference (USD)", None, legend=False)
        fig.update_xaxes(tickprefix="$", tickformat=",.0f", range=[-1000, 20000])
        st.plotly_chart(fig, width="stretch")
        callout(
            "<b>Interpretation.</b> The 95% Welch's t-based confidence interval for the mean salary "
            f"difference (Remote − Hybrid) was [{usd(CI['welch'][0], 2)}, {usd(CI['welch'][1], 2)}], "
            "while the bootstrap percentile confidence interval was "
            f"[{usd(CI['bootstrap'][0], 2)}, {usd(CI['bootstrap'][1], 2)}]. Both intervals exclude "
            "zero and are very similar, supporting a positive mean salary difference in favor of "
            "remote workers in the trimmed dataset. The small differences between them (under $30 "
            "at each end) come from bootstrap Monte Carlo variation and the fact that the bootstrap "
            "makes no normality assumption; with samples this large the two approaches converge.")

        st.markdown("##### What could this gap mean for your payroll?")
        hc = st.slider("Number of roles converted between remote and hybrid", 1, 500, 50, 1)
        lo, hi = CI["welch"][0] * hc, CI["welch"][1] * hc
        callout(
            f"For <b>{hc}</b> roles, the market pay gap amounts to roughly <b>{usd(W['mean_diff'] * hc)}</b> "
            f"per year (plausible range {usd(lo)} – {usd(hi)}, from the 95% CI). This is a "
            "market-level association: it estimates what comparable remote roles pay, not the "
            "savings or cost from changing any individual's work mode.", "plain")

    # ---------------------------------------------------------------- f
    with tabs[5]:
        k1, k2, k3, k4 = st.columns(4)
        with k1:
            kpi("Median salary", f"{usd(MD['median_r'])} / {usd(MD['median_h'])}", "Remote / Hybrid")
        with k2:
            kpi("Mood's median test", f"χ² = {MD['stat']:.4f}", f"p = {pval(MD['p'])}")
        with k3:
            kpi("Bootstrap median test", f"p = {MD['boot_p']:.6f}",
                f"Two-sided, {D['meta']['bootstrap_reps']:,} replications (seed {MD['seed']})")
        with k4:
            kpi("Grand median", usd(MD["grand_median"]), "Both groups combined")

        tb = MD["table"]
        c1, c2 = st.columns([1, 1.25])
        with c1:
            st.markdown("##### Mood's contingency table")
            table(pd.DataFrame({
                "": ["Above grand median", "At or below grand median", "Share above"],
                "Remote": [f"{tb[0][0]:,}", f"{tb[1][0]:,}", f"{MD['pct_above_r']:.1%}"],
                "Hybrid": [f"{tb[0][1]:,}", f"{tb[1][1]:,}", f"{MD['pct_above_h']:.1%}"],
            }), {})
            fig = go.Figure()
            for name, share in (("Remote", MD["pct_above_r"]), ("Hybrid", MD["pct_above_h"])):
                fig.add_bar(x=[share], y=[name], orientation="h", marker_color=GROUP_COLORS[name],
                            text=[f"{share:.1%}"], textposition="inside", textfont=dict(color="#fff"),
                            hovertemplate=f"{name}: %{{x:.1%}} above the grand median<extra></extra>")
            fig.add_vline(x=0.5, line=dict(color=MUTED, dash="dot"))
            style(fig, 200, "Share earning above the grand median", legend=False)
            fig.update_xaxes(tickformat=".0%", range=[0, 1])
            st.plotly_chart(fig, width="stretch")
        with c2:
            fig = go.Figure(hist(A["q2_boot_median_null"], TEAL, "Median difference under H₀", 50))
            vline(fig, MD["obs_median_diff"], f"Observed {usd(MD['obs_median_diff'])}", AMBER)
            vline(fig, 0, "Null hypothesis", MUTED, "dot", "top left")
            style(fig, 420, "Bootstrap distribution of median differences under H₀",
                  "Median difference: Remote − Hybrid (USD)", "Replications", legend=False)
            fig.update_xaxes(tickprefix="$", tickformat=",.0f")
            st.plotly_chart(fig, width="stretch")
        callout(
            "<b>Interpretation.</b> Mood's median test revealed a statistically significant "
            f"difference between remote and hybrid salary distributions (χ² = {MD['stat']:.4f}, "
            f"p = {pval(MD['p'])}). The median annual salary was {usd(MD['median_r'])} for remote "
            f"workers and {usd(MD['median_h'])} for hybrid workers, resulting in an observed "
            f"difference of {usd(MD['obs_median_diff'])}. Approximately {MD['pct_above_r']:.1%} of "
            f"remote workers earned above the grand median of {usd(MD['grand_median'])}, compared "
            f"with {MD['pct_above_h']:.1%} of hybrid workers. A two-sided bootstrap test was also "
            "conducted using 10,000 replications. Under the null hypothesis of equal population "
            "medians, the two groups were centered to have the same median before resampling. The "
            "resulting bootstrap p-value was approximately 0.0001, indicating a statistically "
            "significant median difference at the 5% significance level.")
        callout(
            "<b>Are the two p-values close?</b> Although Mood's p-value and the bootstrap p-value "
            "were not numerically close, both tests rejected the null hypothesis at the 5% "
            "significance level. Mood's test compares the proportions of observations above and "
            "below the pooled median, whereas the bootstrap test directly evaluates the difference "
            "between sample medians using resampling under the null hypothesis. Therefore, the two "
            "methods need not produce similar p-values. The finite number of bootstrap replications "
            "also limits the precision of very small p-values. Overall, both approaches support the "
            "conclusion that remote workers had higher median annual salaries than hybrid workers "
            "in the trimmed dataset.")
        callout(
            "<b>In plain terms.</b> The median is the salary of the worker in the middle, so it is "
            "not moved by a few huge salaries. The typical remote developer still earns about "
            f"{usd(MD['obs_median_diff'])} more than the typical hybrid developer. The bootstrap "
            "histogram is lumpy because medians jump between a small number of commonly reported "
            "round salaries.", "plain")

    # ---------------------------------------------------------------- sensitivity
    with tabs[6]:
        SE = Q2["sensitivity"]
        sens = pd.DataFrame({
            "Dataset": ["Original (all responses)", "Trimmed (top 1% removed per group)"],
            "Mean difference": [SE["original_diff"], W["mean_diff"]],
            "Welch t": [SE["original_t"], W["t"]],
            "p-value": [SE["original_p"], W["p"]],
            "Significant at 0.05": ["Yes", "Yes"],
        })
        table(sens, {"Mean difference": "${:,.2f}", "Welch t": "{:.4f}", "p-value": "{:.6e}"})
        callout(
            "<b>Sensitivity analysis.</b> To assess the robustness of the findings, Welch's "
            "two-sample t-test was repeated using the original, untrimmed salary data. The "
            f"original data showed a statistically significant mean salary difference of "
            f"{usd(SE['original_diff'], 2)} (t = {SE['original_t']:.4f}, p = {SE['original_p']:.5f}). "
            "After removing salaries above the group-specific 99th percentile, the difference was "
            f"{usd(W['mean_diff'], 2)} (t = {W['t']:.4f}, p &lt; 0.001). Both analyses reject the "
            "null hypothesis at the 5% significance level, indicating that the direction and "
            "statistical significance of the difference are robust to this outlier treatment. "
            "However, the substantial change in the t-statistic and p-value demonstrates that the "
            "strength of statistical evidence is sensitive to extreme salary observations.")


# =========================================================================== Q3
def page_q3():
    st.title("3 · Education & pay")
    st.markdown(
        f"Does a higher degree pay more? This section compares **{Q3['n_total']:,}** respondents "
        f"in the **United States ({Q3['by_country']['United States of America']:,})** and "
        f"**Canada ({Q3['by_country']['Canada']:,})** holding a Bachelor's, Master's or "
        "Professional degree.")
    tabs = st.tabs(["a · Descriptives & outliers", "b · ANOVA", "c · Bootstrap",
                    "d · Bootstrap ANOVA"])
    G = Q3["groups"]

    # ---------------------------------------------------------------- a
    with tabs[0]:
        st.subheader("Descriptive statistics (all responses)")
        desc = pd.DataFrame(Q3["describe"]).rename(columns={
            "EdLevel": "Education", "count": "Count", "mean": "Mean", "std": "Std. dev.",
            "min": "Min", "25%": "25%", "50%": "Median", "75%": "75%", "max": "Max"})
        table(desc, {"Count": "{:,.0f}", **{c: "${:,.2f}" for c in
                                            ["Mean", "Std. dev.", "Min", "25%", "Median", "75%", "Max"]}})
        st.markdown("##### Salary percentiles")
        perc = pd.DataFrame(Q3["percentiles"]).rename(columns={"EdLevel": "Education"})
        table(perc, {c: "${:,.2f}" for c in ["Min", "Q1", "Median", "Q3", "P95", "P99", "Max"]})

        fig = go.Figure()
        for lvl in EDU_ORDER:
            b, name = Q3["box"][lvl], EDU_SHORT[lvl]
            fig.add_trace(go.Box(
                x=[name], q1=[b["q1"]], median=[b["median"]], q3=[b["q3"]],
                lowerfence=[b["lowerfence"]], upperfence=[b["upperfence"]], name=name,
                marker_color=GROUP_COLORS[name], fillcolor=tint(GROUP_COLORS[name]),
                line=dict(width=2), boxpoints=False))
            fig.add_scatter(x=[name], y=[b["max"]], mode="markers", showlegend=False,
                            marker=dict(symbol="triangle-up", size=11, color=GROUP_COLORS[name]),
                            hovertemplate=f"{name} maximum: %{{y:$,.0f}}<br>{b['n_outliers_high']} "
                                          "high outliers beyond the whisker<extra></extra>")
        style(fig, 420, "Salary distribution by education (US & Canada, log scale)", None,
              "Annual salary (USD, log scale)", legend=False)
        fig.update_yaxes(type="log", tickprefix="$")
        st.plotly_chart(fig, width="stretch")

        st.subheader("Outlier treatment: top 1% removed within each degree group")
        orig = pd.DataFrame(Q3["original"]).set_index("EdLevel")
        trim = pd.DataFrame(Q3["trimmed"]).set_index("EdLevel")
        comb = pd.DataFrame({
            "Education": EDU_ORDER,
            "Removed": [Q3["removed"][l] for l in EDU_ORDER],
            "Mean (original)": orig.loc[EDU_ORDER, "mean"].values,
            "Mean (trimmed)": trim.loc[EDU_ORDER, "mean"].values,
            "Median (trimmed)": trim.loc[EDU_ORDER, "median"].values,
            "Std. dev. (original)": orig.loc[EDU_ORDER, "std"].values,
            "Std. dev. (trimmed)": trim.loc[EDU_ORDER, "std"].values,
            "n (trimmed)": trim.loc[EDU_ORDER, "count"].values,
        })
        table(comb, {"Removed": "{:,}", "n (trimmed)": "{:,}",
                     **{c: "${:,.2f}" for c in comb.columns if "(" in c and "n (" not in c}})
        callout(
            "<b>Rationale.</b> The salary distributions for all three education groups were "
            "right-skewed, with several extreme high-income observations. These values could "
            "disproportionately influence group means and the subsequent ANOVA results. To reduce "
            "the influence of extreme salaries and maintain consistency with Q2, observations above "
            "the 99th percentile within each education group were excluded. Group-specific "
            "thresholds were used to account for differences in salary distributions across "
            "education levels. The original data were retained separately to allow a sensitivity "
            "analysis of the effect of outlier removal.")

    # ---------------------------------------------------------------- b
    with tabs[1]:
        AN, LV, SN = Q3["anova"], Q3["levene"], Q3["sensitivity"]
        st.markdown("**H₀:** μ<sub>Bachelor's</sub> = μ<sub>Master's</sub> = μ<sub>Professional</sub>"
                    " &nbsp;&nbsp; **H₁:** at least one mean differs &nbsp;&nbsp; α = 0.05",
                    unsafe_allow_html=True)
        k1, k2, k3 = st.columns(3)
        with k1:
            kpi("ANOVA F-statistic", f"{AN['F']:.4f}", "scipy.stats.f_oneway, trimmed data")
        with k2:
            kpi("p-value", pval(AN["p"]), f"{AN['p']:.6e}")
        with k3:
            kpi("Decision", "Reject H₀", "At least one group mean differs")
        grp = pd.DataFrame([{"Group": k, "n": v["n"], "Mean": v["mean"], "Std. dev.": v["std"],
                             "Variance": v["var"]} for k, v in G.items()])
        table(grp, {"n": "{:,}", "Mean": "${:,.2f}", "Std. dev.": "${:,.2f}", "Variance": "{:,.2f}"})
        callout(
            "<b>ANOVA results and interpretation.</b> A one-way ANOVA was conducted to compare the "
            "mean annual salaries of respondents with Bachelor's, Master's, and Professional "
            "degrees in the United States and Canada, after removing the top 1% of salary "
            f"observations within each education group. The ANOVA yielded an F-statistic of "
            f"{AN['F']:.4f} and a p-value of {pval(AN['p'])}. This p-value represents the "
            "probability of obtaining an F-statistic at least as large as the observed value, "
            "assuming that all three education groups have equal population mean salaries. Since "
            "the p-value is far below 0.05, we reject the null hypothesis. This provides strong "
            "statistical evidence that at least one education group has a different population mean "
            "salary. However, ANOVA alone does not identify which specific groups differ or quantify "
            "the differences.")
        callout(
            "<b>Assumption check.</b> The analysis assumes independent survey responses within and "
            "across education groups. Although salary distributions were right-skewed, the large "
            "sample sizes support approximate normality of the sampling distributions of group "
            "means. Levene's test indicated significant differences in group variances (statistic = "
            f"{LV['stat']:.4f}, p = {pval(LV['p'])}), suggesting that the equal-variance assumption "
            "of conventional one-way ANOVA is violated. Therefore, the results should be "
            "interpreted with caution, particularly given unequal group sizes.", "warn")
        st.markdown("##### Sensitivity: original vs. trimmed data")
        table(pd.DataFrame({
            "Dataset": ["Original", "Trimmed (top 1% removed)"],
            "F-statistic": [SN["F_original"], AN["F"]],
            "p-value": [SN["p_original"], AN["p"]],
            "Significant at 0.05": ["Yes", "Yes"]}),
            {"F-statistic": "{:.4f}", "p-value": "{:.6e}"})
        callout(
            "<b>Sensitivity analysis.</b> The ANOVA results remained statistically significant "
            f"before and after outlier removal (original: F = {SN['F_original']:.4f}, "
            f"p = {pval(SN['p_original'])}; trimmed: F = {AN['F']:.4f}, p = {pval(AN['p'])}). "
            "Although the F-statistic increased after removing the highest 1% of salaries within "
            "each education group, both analyses rejected the null hypothesis at the 5% "
            "significance level. This suggests that the overall statistical significance was robust "
            "to the chosen outlier treatment, although unequal variances remain a limitation.")
        callout(
            "<b>In plain terms.</b> ANOVA asks one question: are all three degree groups paid the "
            "same on average? The answer is clearly no. It does not say which groups differ; the "
            "bootstrap comparisons in the next tab answer that.", "plain")

    # ---------------------------------------------------------------- c
    with tabs[2]:
        BS = Q3["bootstrap"]
        bins = st.slider("Histogram bins", 20, 100, 40, 5, key="q3bins")
        boot = {"Bachelor's": A["q3_boot_bachelor"], "Master's": A["q3_boot_master"],
                "Professional": A["q3_boot_professional"]}

        # Figure 1
        fig = make_subplots(rows=1, cols=3, subplot_titles=[f"{n} degree" for n in boot],
                            horizontal_spacing=0.06)
        for i, (name, arr) in enumerate(boot.items(), start=1):
            fig.add_trace(hist(arr, GROUP_COLORS[name], name, bins), row=1, col=i)
            fig.add_vline(x=BS[name]["observed"], line=dict(color=NAVY, dash="dash", width=2),
                          row=1, col=i)
            for x in BS[name]["ci"]:
                fig.add_vline(x=x, line=dict(color=MUTED, dash="dot", width=1.5), row=1, col=i)
        style(fig, 400, "Figure 1 · Bootstrap distributions of mean salary by education",
              None, "Replications", legend=False)
        fig.update_xaxes(tickprefix="$", tickformat=",.0f", nticks=5,
                         title="Bootstrap mean salary (USD)")
        st.plotly_chart(fig, width="stretch")
        st.caption("Dashed navy line = observed mean. Dotted lines = 95% bootstrap CI.")
        table(pd.DataFrame([{"Group": k, "Observed mean": v["observed"], "Bootstrap mean": v["mean"],
                             "Bootstrap SE": v["se"], "95% CI lower": v["ci"][0],
                             "95% CI upper": v["ci"][1]} for k, v in BS.items()]),
              {c: "${:,.2f}" for c in ["Observed mean", "Bootstrap mean", "Bootstrap SE",
                                       "95% CI lower", "95% CI upper"]})
        callout(
            "<b>Figure 1.</b> A total of 10,000 bootstrap replications were performed independently "
            "for each education group. The bootstrap mean estimates were approximately "
            f"{usd(BS[BACH]['mean'])} (Bachelor's), "
            f"{usd(BS[MAST]['mean'])} (Master's) and "
            f"{usd(BS['Professional']['mean'])} (Professional). The Professional degree group had "
            "the highest estimated mean salary and the largest bootstrap standard error "
            f"({usd(BS['Professional']['se'])}), indicating greater uncertainty in its estimated "
            "mean salary. <i>That wider spread reflects its smaller sample (298 people).</i>")

        # Figure 2 — pairwise differences
        pair_arrays = {
            "Master's − Bachelor's": boot["Master's"] - boot["Bachelor's"],
            "Professional − Bachelor's": boot["Professional"] - boot["Bachelor's"],
            "Professional − Master's": boot["Professional"] - boot["Master's"],
        }
        pair_colors = [INDIGO, TEAL, AMBER]
        fig = make_subplots(rows=1, cols=3, subplot_titles=list(pair_arrays), horizontal_spacing=0.06)
        for i, ((name, arr), color) in enumerate(zip(pair_arrays.items(), pair_colors), start=1):
            fig.add_trace(hist(arr, color, name, bins), row=1, col=i)
            lo, hi = PAIRS[name]["ci"]
            for x, dash, c in ((0, "dash", "#B91C1C"), (lo, "dot", NAVY), (hi, "dot", NAVY)):
                fig.add_vline(x=x, line=dict(color=c, dash=dash, width=2 if x == 0 else 1.5),
                              row=1, col=i)
        style(fig, 400, "Figure 2 · Pairwise bootstrap distributions of mean salary differences",
              None, "Replications", legend=False)
        fig.update_xaxes(tickprefix="$", tickformat=",.0f", title="Difference in mean salary (USD)")
        st.plotly_chart(fig, width="stretch")
        st.caption("Red dashed line = no difference. Dotted navy lines = 95% bootstrap CI.")
        pair_tbl = pd.DataFrame([{"Comparison": k, "Mean difference": v["mean"],
                                  "95% CI lower": v["ci"][0], "95% CI upper": v["ci"][1],
                                  "CI excludes 0?": "Yes" if v["ci"][0] > 0 or v["ci"][1] < 0 else "No"}
                                 for k, v in PAIRS.items()])
        table(pair_tbl, {"Mean difference": "${:,.2f}", "95% CI lower": "${:,.2f}",
                         "95% CI upper": "${:,.2f}"})
        mb, pb, pm = (PAIRS[k] for k in pair_arrays)
        callout(
            "<b>Figure 2.</b> The estimated mean differences and their 95% bootstrap confidence "
            f"intervals were: Master's − Bachelor's {usd(mb['mean'])} (95% CI {usd(mb['ci'][0])} to "
            f"{usd(mb['ci'][1])}); Professional − Bachelor's {usd(pb['mean'])} (95% CI "
            f"{usd(pb['ci'][0])} to {usd(pb['ci'][1])}); Professional − Master's {usd(pm['mean'])} "
            f"(95% CI {usd(pm['ci'][0])} to {usd(pm['ci'][1])}). The confidence intervals for "
            "Master's versus Bachelor's and Professional versus Bachelor's excluded zero, suggesting "
            "positive differences in mean annual salaries. However, the confidence interval for "
            "Professional versus Master's included zero, indicating insufficient evidence of a "
            "difference between these two groups at the individual 95% confidence level. These "
            "confidence intervals were not adjusted for multiple comparisons.")

        # Figure 3 — standardized
        fig = make_subplots(rows=1, cols=3, subplot_titles=list(pair_arrays), horizontal_spacing=0.06)
        xs = np.linspace(-4.5, 4.5, 300)
        for i, ((name, arr), color) in enumerate(zip(pair_arrays.items(), pair_colors), start=1):
            z = (arr - arr.mean()) / arr.std(ddof=1)
            fig.add_trace(hist(z, color, name, bins, ".2f"), row=1, col=i)
            width = (z.max() - z.min()) / bins
            fig.add_scatter(x=xs, y=len(z) * width * np.exp(-xs ** 2 / 2) / np.sqrt(2 * np.pi),
                            mode="lines", line=dict(color=NAVY, width=2), hoverinfo="skip",
                            row=1, col=i)
            fig.add_vline(x=0, line=dict(color=NAVY, dash="dash", width=1.5), row=1, col=i)
        style(fig, 380, "Figure 3 · Standardized bootstrap distributions of mean differences",
              None, "Replications", legend=False)
        fig.update_xaxes(title="Standardized mean difference (z)")
        st.plotly_chart(fig, width="stretch")
        st.caption("Navy curve = standard normal reference.")
        callout(
            "<b>Figure 3.</b> The pairwise bootstrap distributions were standardized by subtracting "
            "the mean of each bootstrap distribution and dividing by its corresponding bootstrap "
            "standard error. The resulting distributions were approximately centered at zero with "
            "similar spreads, allowing the uncertainty across the three pairwise comparisons to be "
            "examined on a common standardized scale. The centering at zero results from the "
            "standardization procedure and does not imply that the original mean salary differences "
            "are zero.")
        callout(
            "<b>Overall.</b> The bootstrap analysis suggests that Master's and Professional degree "
            "holders have higher mean annual salaries than Bachelor's degree holders in the analyzed "
            "sample. Although Professional degree holders have a higher estimated mean salary than "
            "Master's degree holders, the corresponding 95% bootstrap confidence interval includes "
            "zero, so this difference is not statistically conclusive. These results indicate "
            "associations between education level and annual salary rather than causal effects.",
            "plain")

    # ---------------------------------------------------------------- d
    with tabs[3]:
        BA = Q3["boot_anova"]
        k1, k2, k3 = st.columns(3)
        with k1:
            kpi("Observed F", f"{BA['observed_F']:.4f}", "From Q3(b)")
        with k2:
            kpi("Bootstrap p-value", f"{BA['p']:.6f}", "Right-tailed, 10,000 replications (seed 123)")
        with k3:
            kpi("Decision at α = 0.05", "Reject H₀", "Consistent with the standard ANOVA")
        fig = go.Figure(hist(A["q3_boot_f"], INDIGO, "Bootstrap F under H₀", 50, ".2f"))
        vline(fig, BA["observed_F"], f"Observed F = {BA['observed_F']:.2f}", AMBER, pos="top left")
        style(fig, 400, "Bootstrap distribution of the ANOVA F-statistic under H₀",
              "Bootstrap F-statistic", "Replications", legend=False)
        st.plotly_chart(fig, width="stretch")
        callout(
            "A bootstrap-based ANOVA was conducted using 10,000 resamples to test whether the three "
            "education groups had equal population mean annual salaries. Under the null hypothesis, "
            "the three groups were centered to a common mean while retaining their within-group "
            "variation. An ANOVA F-statistic was calculated for each bootstrap replication to "
            f"construct the null distribution. The observed F-statistic was {BA['observed_F']:.4f}, "
            "and the estimated bootstrap p-value was approximately 0.0001. Since this is below the "
            "significance level of 0.05, the null hypothesis was rejected. This result is consistent "
            f"with the conventional one-way ANOVA in Q3(b), which yielded F = {Q3['anova']['F']:.4f} "
            f"and p = {pval(Q3['anova']['p'])}. Both methods provide strong evidence that at least "
            "one education group has a different mean annual salary. However, the bootstrap p-value "
            "is limited by the 10,000 replications, and the analysis does not establish a causal "
            "relationship between education level and salary.")
        callout(
            f"<b>In plain terms.</b> If degree level made no difference to average pay, F would "
            f"almost always land below about 5; across 10,000 simulations the largest was "
            f"{BA['max_boot_F']:.2f}. The real data produced {BA['observed_F']:.2f}, far outside "
            "what chance alone generates. Because this test resamples the actual salary data, it "
            "also eases the concern that unequal group variances distort the standard ANOVA.",
            "plain")


# =========================================================================== Methods
def page_methods():
    st.title("Methods, data & limitations")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            f"""
#### Data
- **Source:** 2025 Stack Overflow Developer Survey, course-cleaned file
  (`clean_stackoverflow_data.csv`): {D['meta']['rows']:,} respondents × {D['meta']['columns']}
  columns, all with a reported annual salary in USD (`ConvertedCompYearly`).
- **Q1** uses the full sample. **Q2** compares respondents reporting *Remote* vs. *Hybrid*
  work (worldwide). **Q3** compares Bachelor's, Master's and Professional degree holders in
  the United States and Canada.
- **Outliers:** salaries above each group's 99th percentile were removed for Q2 and Q3.
  Untrimmed results are reported as sensitivity checks.

#### Statistical methods
- Welch's and Student's two-sample t-tests (manual and SciPy), Levene's test.
- Non-parametric bootstrap, 10,000 replications, resampling each group at its own size.
  Fixed seeds (42, 123, 2026) make every figure reproducible.
- Bootstrap hypothesis tests built by centering groups so the null hypothesis holds.
- Welch t-based and bootstrap percentile 95% confidence intervals.
- Mood's median test, one-way ANOVA, and a bootstrap ANOVA.
"""
        )
    with c2:
        st.markdown(
            """
#### How to read the statistics
- **p-value:** how surprising the data would be if there were truly *no* difference.
  Below 0.05 we call a difference statistically significant. It does **not** measure
  how large or how important the difference is.
- **95% confidence interval:** a range of plausible values for the true difference.
  If it excludes zero, the difference is significant at the 5% level.
- **Bootstrap:** re-drawing the sample thousands of times to see how much a result
  could vary, without assuming salaries follow a bell curve.

#### Limitations
- **Association, not causation.** Remote workers may differ from hybrid workers in
  country, seniority, role and company type; degree holders may differ in experience.
  None of these factors are controlled for.
- **Self-reported, self-selected data.** Survey respondents may not represent all
  developers, and salaries are converted to USD at a single exchange rate.
- **Q2 mixes countries.** Part of the remote premium may reflect where remote workers live.
- **Unequal variances in Q3** violate a classical ANOVA assumption; the bootstrap ANOVA
  reaches the same conclusion.
- **Pairwise education CIs are not adjusted** for multiple comparisons.
"""
        )
    callout(
        "<b>Privacy.</b> This dashboard is public, so it contains only aggregated results: group "
        "statistics, test results, box-plot summaries, binned counts for the salary-vs-age view, and "
        "bootstrap replicate statistics (resampled means, medians, t and F values). No individual "
        "survey response is included.", "plain")
    callout(
        "<b>Reproducibility.</b> Every value is generated by <code>build_data.py</code>, which re-runs "
        "the analysis notebook's code with the same filters and random seeds, and matches the "
        "notebook's printed outputs.", "plain")


{
    PAGES[0]: page_summary, PAGES[1]: page_q1, PAGES[2]: page_q2,
    PAGES[3]: page_q3, PAGES[4]: page_methods,
}[page]()

st.markdown("---")
st.caption("Developer Pay Insights · MIE1624 Assignment 1 · Data: 2025 Stack Overflow Developer "
           "Survey (aggregated)")
