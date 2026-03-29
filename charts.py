"""
charts.py
=========
Every chart in the app, production-quality.
Import this in app.py — replaces the inline figure code.

Usage:
    from charts import (
        fig_collapse, fig_origination_rate,
        fig_fha_phases, fig_purchase_refi,
        fig_lti_violin, fig_rvs_bar, fig_choropleth,
        fig_msa_scissor, fig_denial_heatmap,
        fig_origination_share_by_race,
        fig_credit_desert, fig_homeownership_overlay,
        fig_lender_bubble,
    )
"""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────────────────
# DESIGN TOKENS  — single source of truth for all charts
# ─────────────────────────────────────────────────────────
C = {
    "bg":          "rgba(0,0,0,0)",   # transparent — host provides bg
    "grid":        "rgba(26,26,26,0.10)",
    "border":      "rgba(26,26,26,0.20)",
    "text":        "#1A1A1A",
    "muted":       "#3F3F3F",
    "surface":     "#EFEDE7",

    # Semantic
    "crash":       "#E3120B",
    "recovery":    "#2C7A5A",
    "govt":        "#006BA2",
    "conventional":"#23364D",
    "warning":     "#A6761D",
    "purchase":    "#006BA2",
    "refi":        "#3D8B6D",
    "bank":        "#23364D",
    "nonbank":     "#A84A34",
    "veteran":     "#4F4B7A",
    "fha":         "#006BA2",
    "va":          "#3D8B6D",
    "fsa":         "#84BDAA",

    # Race palette
    "white":       "#23364D",
    "black":       "#D7261E",
    "hispanic":    "#A6761D",
    "asian":       "#006BA2",
}

FONT  = "'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
FONT_SERIF = "'Libre Baskerville', Georgia, 'Times New Roman', serif"
H     = 380   # default chart height
H_SM  = 240   # small chart height
H_LG  = 440   # large chart height
M     = dict(l=56, r=28, t=48, b=52)    # default margins
M_MAP = dict(l=0,  r=0,  t=16, b=0)

# Key event annotations shown on timeline charts
EVENTS = [
    (2007.6,  "Bear Stearns",    "top"),
    (2008.75, "Lehman / TARP",   "top"),
    (2010.5,  "Dodd-Frank",      "top"),
    (2012.75, "QE3",             "bottom"),
    (2014.0,  "ATR/QM rules",    "bottom"),
]


def _base_layout(height=H, margin=None, **kwargs):
    """Shared layout applied to every figure.
    Does NOT set xaxis/yaxis — callers do that to avoid kwarg conflicts.
    """
    base = dict(
        height=height,
        margin=margin or M,
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["bg"],
        uirevision="keep",
        transition=dict(duration=90, easing="linear"),
        font=dict(family=FONT, size=12, color=C["text"]),
        title=dict(font=dict(family=FONT_SERIF, size=14, color=C["text"]), x=0, xanchor="left"),
        hoverlabel=dict(
            font=dict(family=FONT, size=12, color=C["text"]),
            bgcolor="rgba(255,255,255,0.98)",
            bordercolor=C["border"],
        ),
        colorway=["#006BA2", "#E3120B", "#379A8B", "#A6761D", "#7A7A7A", "#3EBCD2"],
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.03,
            xanchor="left",   x=0,
            font=dict(size=10, color=C["muted"]),
            bgcolor="rgba(0,0,0,0)",
        ),
        uniformtext_minsize=9,
        uniformtext_mode="hide",
    )
    base.update(kwargs)
    return base


def _add_events(fig, df, y_col, position="top"):
    """Add vertical event lines + labels to a time-series chart."""
    y_max = df[y_col].max() if y_col in df.columns else 1
    for xval, label, pos in EVENTS:
        fig.add_vline(
            x=xval,
            line=dict(color=C["border"], width=1, dash="dot"),
        )
        y_pos = y_max * (1.08 if pos == "top" else 0.06)
        fig.add_annotation(
            x=xval, y=y_pos,
            text=label,
            showarrow=False,
            font=dict(size=9, color=C["muted"]),
            textangle=-35,
            xanchor="left",
        )
    return fig


# ─────────────────────────────────────────────────────────
# CHAPTER 1 — THE BET
# ─────────────────────────────────────────────────────────

# Canonical Chapter 1/2/3 chart implementations are defined later in this file.



# ─────────────────────────────────────────────────────────
# CHAPTER 4 — THE FAKE RECOVERY
# ─────────────────────────────────────────────────────────

def fig_purchase_refi(df: pd.DataFrame) -> go.Figure:
    """
    Stacked area: Purchase vs Refinance.
    The 'fake recovery' is visible — refi spike in 2012-13
    while purchase never recovers to 2007 baseline.
    """
    fig = go.Figure()

    # Refi fill (bottom)
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["refinance"],
        name="Refinance",
        mode="lines",
        line=dict(color=C["refi"], width=1.5),
        fill="tozeroy",
        fillcolor="rgba(93,202,165,0.30)",
        stackgroup="one",
        hovertemplate="Refi: %{y:,.0f}<extra></extra>",
    ))

    # Purchase fill (stacked on top)
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["purchase"],
        name="Purchase",
        mode="lines",
        line=dict(color=C["purchase"], width=2),
        fill="tonexty",
        fillcolor="rgba(24,95,165,0.30)",
        stackgroup="one",
        hovertemplate="Purchase: %{y:,.0f}<extra></extra>",
    ))

    # 2007 purchase baseline — the level never returned to
    _b = df[df["year"] == 2007]["purchase"]
    baseline_2007 = _b.values[0] if len(_b) > 0 else None
    if baseline_2007 is None:
        return fig
    fig.add_hline(
        y=baseline_2007,
        line=dict(color=C["crash"], width=1.2, dash="dash"),
        annotation_text="2007 purchase baseline<br>(never recovered)",
        annotation_position="right",
        annotation_font=dict(size=9, color=C["crash"]),
    )

    # QE3 label — the fake recovery trigger
    _q = df[df["year"] == 2012]["refinance"]
    qe3_y = _q.values[0] if len(_q) > 0 else None
    fig.add_vline(
        x=2012,
        line=dict(color=C["warning"], width=1.5, dash="dash"),
    )
    fig.add_annotation(
        x=2012.1,
        y=(qe3_y * 0.5) if qe3_y is not None else 0,
        text="Fed QE3:<br>the refi wave",
        showarrow=False,
        font=dict(size=9, color=C["warning"]),
        xanchor="left",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=C["warning"], borderwidth=0.5, borderpad=3,
    )

    # Shade fake recovery zone
    fig.add_vrect(
        x0=2011.5, x1=2013.5,
        fillcolor="rgba(239,159,39,0.06)",
        line_width=0,
        annotation_text="The 'recovery'<br>was 80% refi",
        annotation_position="top right",
        annotation_font=dict(size=9, color=C["warning"]),
    )

    fig.update_layout(**_base_layout(
        height=H,
        margin=dict(l=48, r=160, t=36, b=44),
        title=dict(
            text="Purchase vs refinance — the fake recovery revealed",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickcolor=C["border"], dtick=1),
        yaxis=dict(gridcolor=C["grid"], zeroline=False,
                   tickformat=".2s", title="Loan count"),
    ))

    return fig


def fig_lti_violin(df: pd.DataFrame) -> go.Figure:
    """
    Violin plot: loan-to-income ratio distribution by year.
    Shows the compression post-crisis and re-expansion post-2014.
    Uses alternating years to keep it readable.
    """
    show_years = [2007, 2009, 2011, 2013, 2015, 2017]
    sub = df[df["year"].isin(show_years)].copy()
    sub["year_str"] = sub["year"].astype(str)

    year_colors      = {
        "2007": C["crash"],
        "2009": "#D85A30",
        "2011": C["muted"],
        "2013": C["muted"],
        "2015": C["recovery"],
        "2017": C["purchase"],
    }
    year_fill_colors = {
        "2007": "rgba(226,75,74,0.15)",
        "2009": "rgba(216,90,48,0.15)",
        "2011": "rgba(136,135,128,0.15)",
        "2013": "rgba(136,135,128,0.15)",
        "2015": "rgba(29,158,117,0.15)",
        "2017": "rgba(24,95,165,0.15)",
    }

    fig = go.Figure()

    for y in show_years:
        data = sub[sub["year"] == y]["lti_ratio"]
        fig.add_trace(go.Violin(
            x=[str(y)] * len(data),
            y=data,
            name=str(y),
            box_visible=True,
            meanline_visible=True,
             fillcolor=year_fill_colors[str(y)],
            opacity=0.8,
            points=False,
            showlegend=False,
        ))

    # 3x safe zone line
    fig.add_hline(
        y=3.0,
        line=dict(color=C["crash"], width=1.2, dash="dot"),
        annotation_text="3× income rule (safe zone)",
        annotation_position="right",
        annotation_font=dict(size=9, color=C["crash"]),
    )

    # Annotations at compression peak and re-expansion
    fig.add_annotation(
        x="2011", y=2.1,
        text="Tightest<br>credit",
        showarrow=True, arrowhead=2, arrowcolor=C["muted"],
        ax=0, ay=30,
        font=dict(size=9, color=C["muted"]),
    )
    fig.add_annotation(
        x="2017", y=3.4,
        text="Ratios<br>climbing again",
        showarrow=True, arrowhead=2, arrowcolor=C["purchase"],
        ax=0, ay=-30,
        font=dict(size=9, color=C["purchase"]),
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 60,
        margin=dict(l=48, r=120, t=36, b=44),
        title=dict(
            text="Loan-to-income ratio — how much were borrowers stretching-",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickcolor=C["border"], title="Year"),
        yaxis=dict(gridcolor=C["grid"], zeroline=False,
                   title="Loan amount / annual income",
                   range=[0.5, 7]),
        violingap=0.15,
        violinmode="overlay",
    ))

    return fig


def fig_lti_by_income_band(df: pd.DataFrame) -> go.Figure:
    """
    Line chart: median LTI per income band per year.
    The NBER insight — higher income bands were MORE over-leveraged pre-crisis.
    """
    band_order = ["<50K", "50-80K", "80-100K", "100-150K", "150K+"]
    band_colors = {
        "<50K":     C["recovery"],
        "50-80K":   C["purchase"],
        "80-100K":  C["warning"],
        "100-150K": C["crash"],
        "150K+":    C["veteran"],
    }

    medians = (
        df.groupby(["year", "income_band"])["lti_ratio"]
        .median()
        .reset_index()
        .rename(columns={"lti_ratio": "median_lti"})
    )

    fig = go.Figure()

    for band in band_order:
        sub = medians[medians["income_band"] == band].sort_values("year")
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["median_lti"],
            name=band,
            mode="lines+markers",
            line=dict(color=band_colors[band], width=2),
            marker=dict(size=5),
            hovertemplate=f"{band}: %{{y:.2f}}x<extra></extra>",
        ))

    fig.add_hline(
        y=3.0,
        line=dict(color=C["crash"], width=1, dash="dot"),
        annotation_text="3× rule",
        annotation_position="right",
        annotation_font=dict(size=9, color=C["crash"]),
    )

    # Callout: higher earners more leveraged pre-2008
    fig.add_annotation(
        x=2007, y=4.2,
        text="$150K+ borrowers:<br>most over-leveraged<br>pre-crisis (NBER)",
        showarrow=True, arrowhead=2, arrowcolor=C["veteran"],
        ax=40, ay=-20,
        font=dict(size=9, color=C["veteran"]),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=C["veteran"], borderwidth=0.5, borderpad=3,
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 40,
        margin=dict(l=48, r=130, t=36, b=44),
        title=dict(
            text="Median loan/income ratio by income band — who was really over-leveraged-",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickcolor=C["border"], dtick=1),
        yaxis=dict(gridcolor=C["grid"], zeroline=False,
                   title="Median loan / income ratio"),
    ))

    return fig


# ─────────────────────────────────────────────────────────
# CHAPTER 5 — RECOVERY MAP
# ─────────────────────────────────────────────────────────

def fig_bank_nonbank_slope(df: pd.DataFrame) -> go.Figure:
    """
    Slope chart: Bank vs Nonbank origination share 2007 → 2017.
    Two lines crossing — the structural handoff visible as a single motion.
    Banks: 70% → 31%. Nonbanks: 30% → 69%.
    """
    bank    = df[df["lender_type"] == "Bank"].sort_values("year")
    nonbank = df[df["lender_type"] == "Nonbank"].sort_values("year")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=bank["year"], y=bank["share"],
        name="Banks",
        mode="lines+markers",
        line=dict(color=C["conventional"], width=2.5),
        marker=dict(size=6),
        hovertemplate="Banks %{x}: %{y:.1%}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=nonbank["year"], y=nonbank["share"],
        name="Nonbanks",
        mode="lines+markers",
        line=dict(color=C["nonbank"], width=2.5),
        marker=dict(size=6),
        hovertemplate="Nonbanks %{x}: %{y:.1%}<extra></extra>",
    ))

    # Mark the crossover
    cross_year = None
    for i in range(len(bank) - 1):
        b0 = float(bank["share"].iloc[i])
        b1 = float(bank["share"].iloc[i + 1])
        n0 = float(nonbank["share"].iloc[i])
        n1 = float(nonbank["share"].iloc[i + 1])
        if (b0 > n0) != (b1 > n1):
            cross_year = int(bank["year"].iloc[i])
            break

    if cross_year:
        fig.add_vline(
            x=cross_year + 0.5,
            line=dict(color=C["crash"], width=1.2, dash="dash"),
        )
        fig.add_annotation(
            x=cross_year + 0.6, y=0.52,
            text="Crossover<br>Banks lose majority",
            showarrow=False,
            font=dict(size=9, color=C["crash"]),
            xanchor="left",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
        )

    # 2007 and 2017 endpoint labels
    b2007 = float(bank[bank["year"] == 2007]["share"].iloc[0]) if len(bank[bank["year"] == 2007]) else 0
    b2017 = float(bank[bank["year"] == 2017]["share"].iloc[0]) if len(bank[bank["year"] == 2017]) else 0
    n2007 = float(nonbank[nonbank["year"] == 2007]["share"].iloc[0]) if len(nonbank[nonbank["year"] == 2007]) else 0
    n2017 = float(nonbank[nonbank["year"] == 2017]["share"].iloc[0]) if len(nonbank[nonbank["year"] == 2017]) else 0

    for x, y, txt, color in [
        (2007, b2007, f"{b2007:.0%}", C["conventional"]),
        (2017, b2017, f"{b2017:.0%}", C["conventional"]),
        (2007, n2007, f"{n2007:.0%}", C["nonbank"]),
        (2017, n2017, f"{n2017:.0%}", C["nonbank"]),
    ]:
        fig.add_annotation(
            x=x, y=y,
            text=txt,
            showarrow=False,
            font=dict(size=10, color=color, weight=600),
            xanchor="right" if x == 2007 else "left",
            xshift=-8 if x == 2007 else 8,
        )

    fig.update_layout(**_base_layout(
        height=H,
        margin=dict(l=48, r=48, t=48, b=44),
        title=dict(
            text="Who survived — banks handed the market to nonbanks",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False, dtick=2, tickcolor=C["border"]),
        yaxis=dict(
            gridcolor=C["grid"], zeroline=False,
            tickformat=".0%", title="Share of originations",
            range=[0.2, 0.85],
        ),
    ))
    return fig


def fig_recovery_vs_affordability(df: pd.DataFrame) -> go.Figure:
    """
    Scatter: recovery speed (rvs_years) vs median LTI in 2017.
    Fast recovery states became unaffordable — the recovery trap.
    One point per state, labelled.
    """
    fig = go.Figure()

    if df.empty:
        return fig

    colors = [C["recovery"] if r <= 2 else C["warning"] if r <= 4 else C["crash"]
              for r in df["rvs_years"]]

    fig.add_trace(go.Scatter(
        x=df["rvs_years"],
        y=df["median_lti_2017"],
        mode="markers+text",
        marker=dict(size=12, color=colors, opacity=0.85,
                    line=dict(color="white", width=1.5)),
        text=df["state"],
        textposition="top center",
        textfont=dict(size=9),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Recovery: %{x} years<br>"
            "2017 median LTI: %{y:.2f}x"
            "<extra></extra>"
        ),
    ))

    # 3x affordability line
    fig.add_hline(
        y=3.0,
        line=dict(color=C["crash"], width=1, dash="dot"),
        annotation_text="LTI = 3× (affordability threshold)",
        annotation_position="right",
        annotation_font=dict(size=9, color=C["crash"]),
    )

    # Quadrant label
    fig.add_annotation(
        x=1.2, y=3.4,
        text="Fast recovery<br>→ unaffordable",
        showarrow=False,
        font=dict(size=9, color=C["crash"]),
        bgcolor="rgba(255,240,240,0.85)",
        bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
    )
    fig.add_annotation(
        x=6.5, y=2.2,
        text="Slow recovery<br>→ affordable",
        showarrow=False,
        font=dict(size=9, color=C["recovery"]),
        bgcolor="rgba(240,255,245,0.85)",
        bordercolor=C["recovery"], borderwidth=0.5, borderpad=3,
    )

    fig.update_layout(**_base_layout(
        height=H,
        margin=dict(l=48, r=100, t=48, b=48),
        title=dict(
            text="The recovery trap — fast recovery, unaffordable outcome",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(
            showgrid=True, gridcolor=C["grid"], zeroline=False,
            title="Years to recover to 80% of 2007 volume",
            tickcolor=C["border"], dtick=1,
        ),
        yaxis=dict(
            gridcolor=C["grid"], zeroline=False,
            title="Median loan / income ratio (2017)",
        ),
        showlegend=False,
    ))
    return fig


def fig_rvs_bar(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar: Recovery Velocity Score per state.
    Color-coded: green (fast) → amber → red (slow/never).
    """
    df = df.sort_values(["rvs_years", "state"], ascending=[True, True])

    def color(r):
        if r <= 2:  return C["recovery"]
        if r <= 4:  return "#D9A441"
        return C["crash"]

    fig = go.Figure(go.Bar(
        x=df["rvs_years"],
        y=df["state"],
        orientation="h",
        marker_color=[color(r) for r in df["rvs_years"]],
        text=[f"{r}y" for r in df["rvs_years"]],
        textposition="outside",
        hovertemplate="%{y}: %{x} years to recover<extra></extra>",
    ))
    fig.update_traces(cliponaxis=False)

    fast_max = int(df["rvs_years"].min()) if len(df) else 0
    slow_max = int(df["rvs_years"].max()) if len(df) else 0
    fig.add_annotation(
        x=slow_max * 0.6 if slow_max else 4,
        y=1.04,
        xref="x",
        yref="paper",
        text=f"Recovery ranged from {fast_max} year to {slow_max} years across states.",
        showarrow=False,
        font=dict(size=9, color=C["muted"]),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=C["border"],
        borderwidth=0.5,
        borderpad=3,
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 80,
        margin=dict(l=56, r=104, t=44, b=50),
        title=dict(
            text="Recovery time by state (fast to slow)",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(
            showgrid=True, gridcolor=C["grid"], zeroline=False,
            tickcolor=C["border"], title="Years to recover",
        ),
        yaxis=dict(showgrid=False, zeroline=False, tickcolor=C["border"]),
        showlegend=False,
        bargap=0.25,
    ))

    return fig


def fig_recovery_map_discrete(df: pd.DataFrame) -> go.Figure:
    """Chapter 5 anchor map: discrete recovery speed categories."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.copy()
    d["category_code"] = d["rvs_years"].apply(lambda v: 0 if v <= 2 else (1 if v <= 4 else 2))
    d["category_label"] = d["rvs_years"].apply(lambda v: "Fast (≤2y)" if v <= 2 else ("Medium (3-4y)" if v <= 4 else "Slow (5+y)"))

    fig.add_trace(go.Choropleth(
        locations=d["state"],
        z=d["category_code"],
        locationmode="USA-states",
        colorscale=[
            [0.0, "#2E8B57"], [0.3333, "#2E8B57"],
            [0.3334, "#D9A441"], [0.6666, "#D9A441"],
            [0.6667, "#C23B31"], [1.0, "#C23B31"],
        ],
        zmin=0, zmax=2,
        marker_line_color="#FAFAF7",
        marker_line_width=0.7,
        colorbar=dict(
            title=dict(text="Recovery speed", font=dict(size=10)),
            tickmode="array",
            tickvals=[0, 1, 2],
            ticktext=["Fast (≤2y)", "Medium (3-4y)", "Slow (5+y)"],
            thickness=12,
            len=0.55,
        ),
        customdata=d[["rvs_years", "category_label"]],
        hovertemplate=(
            "<b>%{location}</b><br>"
            "Recovery time: %{customdata[0]} years<br>"
            "Category: %{customdata[1]}"
            "<extra></extra>"
        ),
    ))

    fig.update_geos(
        scope="usa",
        bgcolor=C["bg"],
        showlakes=False,
        showland=True, landcolor="#F1EFE8",
        showcoastlines=False,
    )
    fig.add_annotation(
        x=0.01, y=0.04, xref="paper", yref="paper",
        text="Recovery speed varied sharply across regions.",
        showarrow=False, xanchor="left",
        font=dict(size=10, color=C["muted"]),
        bgcolor="rgba(255,255,255,0.90)", bordercolor=C["border"], borderwidth=0.5, borderpad=4,
    )
    fig.update_layout(
        height=370,
        margin=M_MAP,
        paper_bgcolor=C["bg"],
        uirevision="keep",
        transition=dict(duration=280, easing="cubic-in-out"),
        font=dict(family=FONT, size=11),
        geo=dict(bgcolor=C["bg"]),
        title=dict(
            text="Recovery speed across states",
            font=dict(size=12), x=0.02, xanchor="left", y=0.97,
        ),
    )
    return fig


def fig_lti_affordability(df: pd.DataFrame) -> go.Figure:
    """Chapter 5 outcome chart: latest-year LTI distribution sorted by area."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.copy()
    latest_year = int(d["year"].max())
    sub = d[d["year"] == latest_year].copy()
    if sub.empty:
        sub = d.sort_values("year", ascending=False).head(20).copy()
    sub = sub.sort_values("median_lti", ascending=False)

    colors = [C["crash"] if v > 3 else C["recovery"] for v in sub["median_lti"]]
    fig.add_trace(go.Bar(
        x=sub["median_lti"],
        y=sub["msa"],
        orientation="h",
        marker_color=colors,
        hovertemplate="%{y}: %{x:.2f}x income<extra></extra>",
    ))
    fig.add_vline(x=3, line=dict(color=C["muted"], width=1.2, dash="dot"))
    fig.add_annotation(
        x=3, y=1.02, xref="x", yref="paper",
        text="LTI = 3 reference",
        showarrow=False, font=dict(size=9, color=C["muted"]),
    )
    fig.add_annotation(
        x=float(sub["median_lti"].max()) * 0.62 if len(sub) else 3.3,
        y=1.08, xref="x", yref="paper",
        text="Even recovered markets became less affordable.",
        showarrow=False, font=dict(size=9, color=C["crash"]),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 80,
        margin=dict(l=92, r=24, t=44, b=50),
        title=dict(text=f"Affordability pressure: median loan-to-income ({latest_year})", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=True, gridcolor=C["grid"], title="Median LTI", tickcolor=C["border"]),
        yaxis=dict(showgrid=False, tickcolor=C["border"], automargin=True),
        showlegend=False,
    ))
    return fig


def fig_choropleth(df: pd.DataFrame, selected_year: int = 2017) -> go.Figure:
    """
    US state choropleth: recovery ratio vs 2007 baseline.
    Called with a year for the time-slider.
    """
    year_df = df[df["year"] == selected_year]

    fig = go.Figure(go.Choropleth(
        locations=year_df["state"],
        z=year_df["recovery_ratio"],
        locationmode="USA-states",
        colorscale=[
            [0.0,  C["crash"]],
            [0.4,  "#EF9F27"],
            [0.7,  "#FAEEDA"],
            [1.0,  C["recovery"]],
        ],
        zmin=0.4, zmax=1.4,
        colorbar=dict(
            title=dict(text="Recovery<br>ratio", font=dict(size=10)),
            thickness=12,
            len=0.6,
            tickformat=".1f",
        ),
        hovertemplate=(
            "<b>%{location}</b><br>"
            f"Recovery ratio ({selected_year}): %{{z:.2f}}<br>"
            "(1.0 = matched 2007 volume)"
            "<extra></extra>"
        ),
    ))

    fig.update_geos(
        scope="usa",
        bgcolor=C["bg"],
        showlakes=False,
        showland=True, landcolor="#F1EFE8",
        showcoastlines=False,
    )

    fig.update_layout(
        height=360,
        margin=M_MAP,
        paper_bgcolor=C["bg"],
        uirevision="keep",
        transition=dict(duration=280, easing="cubic-in-out"),
        font=dict(family=FONT, size=11),
        geo=dict(bgcolor=C["bg"]),
        title=dict(
            text=f"Recovery ratio vs 2007 baseline — {selected_year}",
            font=dict(size=12), x=0.02, xanchor="left", y=0.97,
        ),
    )

    return fig


def fig_msa_scissor(df: pd.DataFrame) -> go.Figure:
    """
    Heatmap: median loan/income ratio per MSA per year.
    The 'scissor' — compression then re-expansion.
    """
    pivot = df.pivot(index="msa", columns="year", values="median_lti")
    pivot = pivot.sort_values(pivot.columns[-1], ascending=False)

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(y) for y in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[
            [0.0, "#E1F5EE"],
            [0.3, "#9FE1CB"],
            [0.6, "#EF9F27"],
            [1.0, C["crash"]],
        ],
        zmid=3.0,
        colorbar=dict(
            title=dict(text="Median<br>LTI ratio", font=dict(size=10)),
            thickness=12, len=0.8,
            tickformat=".1f",
        ),
        hovertemplate="%{y} (%{x}): %{z:.2f}x income<extra></extra>",
        text=[[f"{v:.1f}" for v in row] for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=9),
    ))

    # 3x safe zone reference line
    fig.add_shape(
        type="line",
        x0=-0.5, x1=len(pivot.columns) - 0.5,
        y0=-0.5, y1=len(pivot.index) - 0.5,
        line=dict(color=C["crash"], width=0),  # invisible — annotation only
    )
    fig.add_annotation(
        x=str(2007), y=pivot.index[-1],
        text="← 3× rule violated for most metros by 2007",
        showarrow=False,
        font=dict(size=8, color=C["crash"]),
        xanchor="left",
    )

    fig.update_layout(
        height=H_LG,
        margin=dict(l=110, r=60, t=36, b=44),
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["bg"],
        font=dict(family=FONT, size=11),
        title=dict(
            text="Income-price scissor — median loan/income ratio by metro area",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, tickcolor=C["border"], side="bottom"),
        yaxis=dict(showgrid=False, tickcolor=C["border"]),
    )

    return fig


# ─────────────────────────────────────────────────────────
# CHAPTER 6 — WHO GOT LEFT BEHIND
# ─────────────────────────────────────────────────────────

def fig_denial_heatmap(df: pd.DataFrame) -> go.Figure:
    """
    Side-by-side heatmaps: White vs Black denial rate by income band × year.
    The racial gap at the same income = the key insight.
    """
    races_to_show = ["White", "Black / African American"]
    band_order    = ["<50K", "50-80K", "80-100K", "100-150K", "150K+"]

    fig = go.Figure()

    for i, race in enumerate(races_to_show):
        sub = df[df["race"] == race].copy()
        sub["income_band"] = pd.Categorical(sub["income_band"],
                                             categories=band_order, ordered=True)
        sub = sub.sort_values(["income_band", "year"])
        pivot = sub.pivot(index="income_band", columns="year", values="denial_rate")
        pivot = pivot.reindex(band_order)

        fig.add_trace(go.Heatmap(
            z=pivot.values,
            x=[str(y) for y in pivot.columns],
            y=pivot.index.tolist(),
            colorscale=[
                [0.0, "#E1F5EE"],
                [0.3, "#FAEEDA"],
                [0.7, C["warning"]],
                [1.0, C["crash"]],
            ],
            zmin=0, zmax=0.65,
            showscale=(i == 1),
            colorbar=dict(
                title=dict(text="Denial<br>rate", font=dict(size=10)),
                thickness=12, len=0.8,
                tickformat=".0%",
                x=1.02,
            ),
            text=[[f"{v:.0%}" for v in row] for row in pivot.values],
            texttemplate="%{text}",
            textfont=dict(size=9),
            name=race,
            xaxis=f"x{i+1}",
            yaxis=f"y{i+1}" if i > 0 else "y",
            hovertemplate=f"{race}<br>%{{y}} income, %{{x}}: %{{z:.1%}} denial rate<extra></extra>",
        ))

    fig.update_layout(
        height=320,
        margin=dict(l=80, r=80, t=56, b=44),
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["bg"],
        font=dict(family=FONT, size=11),
        title=dict(
            text="Denial rates at the same income — White vs Black borrowers",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(domain=[0, 0.47], showgrid=False,
                   title=dict(text="White", font=dict(size=11, color=C["muted"])),
                   side="top"),
        yaxis=dict(showgrid=False, tickcolor=C["border"]),
        xaxis2=dict(domain=[0.53, 1.0], showgrid=False,
                    title=dict(text="Black / African American",
                               font=dict(size=11, color=C["crash"])),
                    side="top"),
        yaxis2=dict(showgrid=False, tickcolor=C["border"], showticklabels=False),
        grid=dict(rows=1, columns=2),
    )

    # Source note — interpolated data
    fig.add_annotation(
        text="Rates interpolated from CFPB Data Point 2014 & 2018, Urban Institute HFPC 2019 "
             "anchor points (2007 / 2010 / 2013 / 2017)",
        xref="paper", yref="paper", x=0, y=-0.18,
        showarrow=False,
        font=dict(size=8, color=C["muted"]),
        align="left",
    )

    return fig


def fig_origination_share_by_race(df: pd.DataFrame) -> go.Figure:
    """
    Ch 6: Share of total originations by race, 2007-2017.
    Real HMDA data — no estimates or interpolation.
    """
    race_colors = {
        "White":                  C["conventional"],
        "Black / African American": C["crash"],
        "Asian":                  C["fha"],
    }
    race_order = ["White", "Black / African American", "Asian"]

    fig = go.Figure()

    for race in race_order:
        sub = df[df["race"] == race].sort_values("year")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["share"],
            name=race,
            mode="lines+markers",
            line=dict(color=race_colors.get(race, C["muted"]), width=2.5),
            marker=dict(size=5),
            hovertemplate=f"{race}<br>%{{x}}: %{{y:.1%}} of originations<extra></extra>",
        ))

    # Annotate the observed Black-share change from 2007 to 2010 if available.
    b = df[df["race"] == "Black / African American"]
    if len(b[b["year"] == 2007]) and len(b[b["year"] == 2010]):
        b2007 = float(b[b["year"] == 2007]["share"].iloc[0])
        b2010 = float(b[b["year"] == 2010]["share"].iloc[0])
        drop = ((b2010 / b2007) - 1.0) if b2007 else 0.0
        fig.add_annotation(
            x=2010, y=b2010,
            text=f"{drop:.0%} vs 2007",
            showarrow=True, arrowhead=2, arrowcolor=C["crash"],
            arrowwidth=1.5, ax=40, ay=-30,
            font=dict(size=9, color=C["crash"]),
        )

    fig.update_layout(
        height=300,
        margin=dict(l=60, r=20, t=48, b=44),
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["bg"],
        font=dict(family=FONT, size=11),
        title=dict(
            text="Race share of originations over time (direct HMDA counts)",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, tickmode="linear", dtick=2),
        yaxis=dict(
            showgrid=True,
            gridcolor=C["border"],
            tickformat=".0%",
            title=dict(text="Share of all originations", font=dict(size=10)),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="left", x=0,
        ),
    )
    fig.add_annotation(
        text="Source: HMDA LAR 2007-2017 (CFPB). First-lien, owner-occupied, 1-4 family, purchase + refi.",
        xref="paper", yref="paper", x=0, y=-0.18,
        showarrow=False,
        font=dict(size=8, color=C["muted"]),
        align="left",
    )
    return fig


def fig_credit_desert(df: pd.DataFrame) -> go.Figure:
    """
    Dual-axis line: moderate-income denial rate (left) vs unemployment rate (right).
    The gap between curves after 2013 = the credit desert.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["year"], y=df["denial_rate_moderate_income"],
        name="Denial rate ($50–80K income)",
        yaxis="y1",
        mode="lines+markers",
        line=dict(color=C["crash"], width=2.5),
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor="rgba(226,75,74,0.08)",
        hovertemplate="%{x}: %{y:.1%} denial rate<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df["year"],
        y=df["unemployment_rate"] / 100,
        name="Unemployment rate",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color=C["muted"], width=1.5, dash="dash"),
        marker=dict(size=5),
        hovertemplate="%{x}: %{y:.1%} unemployment<extra></extra>",
    ))

    # Shade the divergence zone
    fig.add_vrect(
        x0=2013.5, x1=2017.5,
        fillcolor="rgba(83,74,183,0.06)",
        line_width=0,
        layer="below",
    )
    fig.add_annotation(
        x=2015.5, y=0.31,
        text="Jobs recovered<br>Credit stayed tight<br>→ the credit desert",
        showarrow=False,
        font=dict(size=9, color=C["veteran"]),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=C["veteran"], borderwidth=0.5, borderpad=4,
        align="center",
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 60,
        margin=dict(l=48, r=60, t=36, b=44),
        title=dict(
            text="The credit desert — denial rates outlasted unemployment (Harvard JCHS)",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickcolor=C["border"], dtick=1),
        yaxis=dict(
            gridcolor=C["grid"], zeroline=False,
            tickformat=".0%", title="Denial rate ($50–80K band)",
            range=[0.1, 0.45],
        ),
        yaxis2=dict(
            title="Unemployment rate",
            tickformat=".0%",
            overlaying="y", side="right",
            showgrid=False,
            range=[0.03, 0.12],
        ),
    ))

    return fig


def fig_homeownership_overlay(df: pd.DataFrame) -> go.Figure:
    """
    Dual-axis: purchase originations (bars) vs homeownership rate (line).
    They move together — HMDA purchase volume as a leading indicator.
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df["year"],
        y=df["purchase_originations"],
        name="Purchase originations",
        yaxis="y1",
        marker_color=C["purchase"],
        opacity=0.75,
        hovertemplate="%{x}: %{y:,.0f} purchase loans<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=df["year"],
        y=df["homeownership_rate"],
        name="Homeownership rate %",
        yaxis="y2",
        mode="lines+markers",
        line=dict(color=C["crash"], width=2.5),
        marker=dict(size=6),
        hovertemplate="%{x}: %{y:.1f}% homeownership<extra></extra>",
    ))

    # Annotation: the 2018 renter-majority cities fact
    fig.add_annotation(
        x=2017, y=df["homeownership_rate"].min() * 0.995,
        text="By 2018: renters outnumber<br>owners in 47% of major cities<br>(up from 21% in 2006)",
        showarrow=False,
        font=dict(size=9, color=C["crash"]),
        xanchor="right",
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=C["crash"], borderwidth=0.5, borderpad=4,
        align="right",
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 60,
        margin=dict(l=48, r=80, t=36, b=44),
        title=dict(
            text="Every denied mortgage created a future renter",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickcolor=C["border"], dtick=1),
        yaxis=dict(
            gridcolor=C["grid"], zeroline=False,
            tickformat=".2s", title="Purchase originations",
        ),
        yaxis2=dict(
            title="Homeownership rate %",
            overlaying="y", side="right",
            showgrid=False, range=[62, 69.5],
            ticksuffix="%",
        ),
        bargap=0.2,
    ))

    return fig


# ─────────────────────────────────────────────────────────
# CHAPTER 7 — THE NEW RULES
# ─────────────────────────────────────────────────────────

def fig_lender_bubble(df: pd.DataFrame, selected_year: int = 2017) -> go.Figure:
    """
    Bubble chart with clutter control:
    - major lenders (top 15): labeled
    - minor lenders: unlabeled, transparent points
    """
    import random
    random.seed(selected_year)
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    year_df = df[df["year"] == selected_year].copy()
    if year_df.empty:
        year_df = df[df["year"] == int(df["year"].max())].copy()
    year_df = year_df.dropna(subset=["originations", "institution", "lender_type"])
    year_df = year_df[year_df["originations"] > 0].copy()
    if year_df.empty:
        return fig

    year_df["x_pos"] = year_df["lender_type"].map({"Bank": 0.3, "Nonbank": 0.7})
    year_df["x_pos"] += [random.gauss(0, 0.06) for _ in range(len(year_df))]
    year_df["x_pos"] = year_df["x_pos"].clip(0.05, 0.95)
    year_df = year_df.sort_values("originations", ascending=False)
    major = year_df.head(15).copy()
    minor = year_df.iloc[15:].copy()

    color_map = {"Bank": C["bank"], "Nonbank": C["nonbank"]}

    for lt in ["Bank", "Nonbank"]:
        sub_minor = minor[minor["lender_type"] == lt]
        if not sub_minor.empty:
            fig.add_trace(go.Scatter(
                x=sub_minor["x_pos"],
                y=sub_minor["originations"],
                mode="markers",
                marker=dict(
                    size=(sub_minor["originations"] / sub_minor["originations"].max() * 14 + 5)
                    if sub_minor["originations"].max() > 0 else 6,
                    color=color_map[lt],
                    opacity=0.20,
                    line=dict(color="white", width=0.8),
                ),
                hovertemplate=(
                    "<b>%{customdata}</b><br>"
                    f"Type: {lt}<br>"
                    "Originations: %{y:,.0f}<extra></extra>"
                ),
                customdata=sub_minor["institution"],
                showlegend=False,
            ))

    for lt in ["Bank", "Nonbank"]:
        sub = major[major["lender_type"] == lt]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["x_pos"],
            y=sub["originations"],
            mode="markers+text",
            name=lt,
            text=sub["institution"],
            textposition="top center",
            textfont=dict(size=9, color=C["text"]),
            marker=dict(
                size=sub["originations"] / sub["originations"].max() * 60 + 12,
                color=color_map[lt],
                opacity=0.88,
                line=dict(color="white", width=1.5),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                f"Type: {lt}<br>"
                "Originations: %{y:,.0f}<extra></extra>"
            ),
        ))

    fig.update_layout(**_base_layout(
        height=H_LG,
        margin=dict(l=60, r=20, t=36, b=80),
        title=dict(
            text=f"Who is lending in {selected_year} - banks vs nonbanks",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(
            showgrid=False, zeroline=False,
            range=[0, 1],
            tickvals=[0.3, 0.7],
            ticktext=["<b>Banks</b>", "<b>Nonbanks</b>"],
            tickfont=dict(size=13),
        ),
        yaxis=dict(
            gridcolor=C["grid"], zeroline=False,
            tickformat=".2s", title="Annual originations",
        ),
        showlegend=False,
    ))
    fig.add_vline(x=0.5, line=dict(color=C["border"], width=1, dash="dot"))
    return fig

def fig_lender_trend(df: pd.DataFrame) -> go.Figure:
    """
    Chapter 7 primary signal: lender composition share over time.
    """
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    by_type = df.groupby(["year", "lender_type"], as_index=False)["originations"].sum()
    pivot = by_type.pivot(index="year", columns="lender_type", values="originations").fillna(0)
    if "Bank" not in pivot.columns:
        pivot["Bank"] = 0
    if "Nonbank" not in pivot.columns:
        pivot["Nonbank"] = 0
    pivot = pivot.reset_index().sort_values("year")
    total = (pivot["Bank"] + pivot["Nonbank"]).replace(0, pd.NA)
    pivot["bank_share"] = pivot["Bank"] / total
    pivot["nonbank_share"] = pivot["Nonbank"] / total

    fig.add_trace(go.Scatter(
        x=pivot["year"], y=pivot["bank_share"],
        mode="lines", name="Bank share",
        line=dict(color=C["bank"], width=2.0, shape="spline", smoothing=0.7),
        stackgroup="one", groupnorm="fraction", fill="tozeroy",
        hovertemplate="Banks<br>%{x}: %{y:.1%}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=pivot["year"], y=pivot["nonbank_share"],
        mode="lines", name="Nonbank share",
        line=dict(color=C["nonbank"], width=2.0, shape="spline", smoothing=0.7),
        stackgroup="one", groupnorm="fraction", fill="tonexty",
        hovertemplate="Nonbanks<br>%{x}: %{y:.1%}<extra></extra>",
    ))
    fig.add_annotation(
        x=float(pivot["year"].median()),
        y=0.88,
        text="Nonbanks grew from a small share to a major part of the market.",
        showarrow=False,
        font=dict(size=9, color=C["nonbank"]),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=C["nonbank"], borderwidth=0.5, borderpad=3,
    )

    fig.update_layout(**_base_layout(
        height=H,
        margin=dict(l=48, r=28, t=36, b=44),
        title=dict(
            text="Structural shift: bank vs nonbank share of originations",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickcolor=C["border"], dtick=1),
        yaxis=dict(gridcolor=C["grid"], zeroline=False,
                   tickformat=".0%", title="Share of originations", range=[0, 1]),
    ))

    return fig


def fig_top_lenders_split(df: pd.DataFrame, selected_year: int | None = None) -> go.Figure:
    """Chapter 7 supporting chart: top lenders split by bank/nonbank."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    year = int(df["year"].max()) if selected_year is None else int(selected_year)
    d = df[df["year"] == year].copy()
    if d.empty:
        d = df.copy()
        year = int(d["year"].max())

    d = (
        d.groupby(["institution", "lender_type"], as_index=False)["originations"]
        .sum()
        .dropna(subset=["institution", "originations", "lender_type"])
    )
    d = d[d["originations"] > 0].sort_values("originations", ascending=False).head(10)
    if d.empty:
        return fig

    color_map = {"Bank": C["bank"], "Nonbank": C["nonbank"]}
    d = d.sort_values("originations", ascending=True)
    fig.add_trace(go.Bar(
        x=d["originations"],
        y=d["institution"],
        orientation="h",
        marker_color=[color_map.get(t, C["muted"]) for t in d["lender_type"]],
        customdata=d["lender_type"],
        hovertemplate="<b>%{y}</b><br>Type: %{customdata}<br>Originations: %{x:,.0f}<extra></extra>",
    ))

    fig.update_layout(**_base_layout(
        height=H_SM + 80,
        margin=dict(l=220, r=24, t=44, b=50),
        title=dict(text=f"Top 10 lenders in {year} (banks vs nonbanks)", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=True, gridcolor=C["grid"], tickformat=".2s", title="Originations"),
        yaxis=dict(showgrid=False, tickcolor=C["border"], automargin=True),
        showlegend=False,
    ))
    return fig
# -----------------------------------------------------------------------------
# Smooth visual overrides for Chapters 1-3 (appended intentionally: last def wins)
# -----------------------------------------------------------------------------

def fig_ch1_scale_speed(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.sort_values("year").dropna(subset=["origination_rate"])
    if d.empty:
        return fig
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["origination_rate"], name="Approval rate",
        mode="lines+markers",
        line=dict(color=C["govt"], width=3, shape="spline", smoothing=0.7),
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor="rgba(11,79,138,0.12)",
        hovertemplate="%{x}: %{y:.1%}<extra></extra>",
    ))
    base_2007 = d[d["year"] == 2007]["origination_rate"]
    if len(base_2007):
        base = float(base_2007.iloc[0])
        fig.add_annotation(
            x=2007,
            y=base,
            text=f"Start: {base:.0%}",
            showarrow=True,
            arrowhead=2,
            ax=18,
            ay=-24,
            font=dict(size=9, color=C["muted"]),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=C["border"],
            borderwidth=0.5,
            borderpad=3,
        )
    pre = d[d["year"].isin([2007, 2008])]
    if len(pre) == 2:
        change = (float(pre[pre["year"] == 2008]["origination_rate"].iloc[0]) /
                  float(pre[pre["year"] == 2007]["origination_rate"].iloc[0])) - 1
        ann = "already declining before the crisis"
        fig.add_annotation(
            x=2008, y=float(pre[pre["year"] == 2008]["origination_rate"].iloc[0]),
            text=f"{change:.0%} vs 2007: {ann}",
            showarrow=True, arrowhead=2, ax=20, ay=-30,
            font=dict(size=9, color=C["warning"]),
        )

    trough = d.loc[d["origination_rate"].idxmin()]
    fig.add_annotation(
        x=trough["year"], y=trough["origination_rate"],
        text=f"Low: {trough['origination_rate']:.0%}",
        showarrow=True, arrowhead=2, ax=0, ay=-30,
        font=dict(size=9, color=C["crash"]),
    )

    ymin = float(d["origination_rate"].min())
    ymax = float(d["origination_rate"].max())
    if ymin == ymax:
        ymin = max(0.0, ymin - 0.06)
        ymax = min(1.05, ymax + 0.02)
    else:
        pad = max(0.02, (ymax - ymin) * 0.2)
        ymin = max(0.0, ymin - pad)
        ymax = min(1.05, ymax + pad)
    if float(d["origination_rate"].nunique()) == 1.0 and float(d["origination_rate"].iloc[0]) >= 0.99:
        fig.add_annotation(
            x=float(d["year"].median()), y=ymax - 0.01,
            text="Scoped file contains originated loans only; observed rate appears at 100%.",
            showarrow=False, font=dict(size=9, color=C["muted"]),
            bgcolor="rgba(255,255,255,0.9)", bordercolor=C["border"], borderwidth=0.5, borderpad=3,
        )

    fig.update_layout(**_base_layout(
        height=H_SM + 60,
        title=dict(text="Hidden softening: approval rates falling before the break", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, dtick=1, tickcolor=C["border"]),
        yaxis=dict(title="Approval rate", gridcolor=C["grid"], tickformat=".0%", range=[ymin, ymax]),
        showlegend=False,
    ))
    return fig


def fig_credit_access_index(df: pd.DataFrame) -> go.Figure:
    """Chapter 6 entry chart: indexed access by race (2007=100)."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    races = ["Black / African American", "White", "Asian"]
    colors = {
        "Black / African American": C["crash"],
        "White": C["conventional"],
        "Asian": C["fha"],
    }
    d = df.copy()
    y_vals = []
    for race in races:
        sub = d[d["race"] == race].sort_values("year")
        if sub.empty:
            continue
        base = sub[sub["year"] == 2007]["share"]
        if base.empty or float(base.iloc[0]) == 0:
            continue
        idx = (sub["share"] / float(base.iloc[0])) * 100.0
        y_vals.extend(idx.dropna().tolist())
        fig.add_trace(go.Scatter(
            x=sub["year"], y=idx,
            mode="lines+markers",
            name=race,
            line=dict(color=colors[race], width=2.8 if "Black" in race else 1.9, shape="spline", smoothing=0.7),
            marker=dict(size=5),
            hovertemplate=f"{race}<br>%{{x}}: %{{y:.0f}} (2007=100)<extra></extra>",
        ))
        if race == "Black / African American":
            v2010 = sub[sub["year"] == 2010]["share"]
            if not v2010.empty:
                idx2010 = float(v2010.iloc[0]) / float(base.iloc[0]) * 100.0
                fig.add_annotation(
                    x=2010, y=idx2010,
                    text="Black access index fell by more than half during the crash.",
                    showarrow=True, arrowhead=2, ax=35, ay=-30,
                    font=dict(size=9, color=C["crash"]),
                    bgcolor="rgba(255,255,255,0.9)", bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
                )

    fig.add_hline(y=100, line=dict(color=C["muted"], width=1, dash="dot"))
    if y_vals:
        y_min = min(y_vals)
        y_max = max(y_vals)
        pad = max(6.0, (y_max - y_min) * 0.16)
        y_range = [max(20, y_min - pad), min(220, y_max + pad)]
    else:
        y_range = [35, 125]
    fig.update_layout(**_base_layout(
        height=H_SM + 70,
        margin=dict(l=48, r=24, t=36, b=44),
        title=dict(text="Access collapse: indexed credit access by race (2007=100)", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], automargin=True),
        yaxis=dict(gridcolor=C["grid"], zeroline=False, title="Indexed access", range=y_range),
    ))
    return fig


def fig_denial_gap_income(df: pd.DataFrame) -> go.Figure:
    """Chapter 6 structural inequality: denial gaps at same income (latest year)."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    latest = int(df["year"].max())
    bands = ["50-80K", "80-100K"]
    races = ["White", "Black / African American"]
    sub = df[(df["year"] == latest) & (df["income_band"].isin(bands)) & (df["race"].isin(races))].copy()
    if sub.empty:
        return fig

    white = sub[sub["race"] == "White"].set_index("income_band")["denial_rate"].to_dict()
    black = sub[sub["race"] == "Black / African American"].set_index("income_band")["denial_rate"].to_dict()
    gaps = []
    for b in bands:
        if b in white and b in black:
            gaps.append((black[b] - white[b]) * 100.0)

    fig.add_trace(go.Bar(
        x=bands,
        y=[white.get(b, 0.0) for b in bands],
        name="White",
        marker_color=C["conventional"],
        hovertemplate="White<br>%{x}: %{y:.1%}<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=bands,
        y=[black.get(b, 0.0) for b in bands],
        name="Black / African American",
        marker_color=C["crash"],
        hovertemplate="Black / African American<br>%{x}: %{y:.1%}<extra></extra>",
    ))
    if gaps:
        avg_gap = sum(gaps) / len(gaps)
        fig.add_annotation(
            x=bands[-1], y=max([black.get(b, 0.0) for b in bands]) * 1.12,
            text=f"+{avg_gap:.0f} percentage points higher at the same income",
            showarrow=False, font=dict(size=9, color=C["crash"]),
            bgcolor="rgba(255,255,255,0.9)", bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
        )

    fig.update_layout(**_base_layout(
        height=H_SM + 70,
        margin=dict(l=48, r=24, t=36, b=44),
        title=dict(text=f"Structural inequality: denial rates at same income ({latest})", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, tickcolor=C["border"]),
        yaxis=dict(gridcolor=C["grid"], tickformat=".0%", title="Denial rate"),
        barmode="group",
    ))
    return fig


def fig_denial_persistence(df: pd.DataFrame) -> go.Figure:
    """Chapter 6 persistence: middle-income denial rates over time."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    band = "50-80K"
    sub = df[df["income_band"] == band].sort_values("year")
    w = sub[sub["race"] == "White"].sort_values("year")
    b = sub[sub["race"] == "Black / African American"].sort_values("year")
    if w.empty and b.empty:
        return fig

    if not w.empty:
        fig.add_trace(go.Scatter(
            x=w["year"], y=w["denial_rate"], name="White",
            mode="lines+markers", line=dict(color=C["conventional"], width=1.8, shape="spline", smoothing=0.7),
            marker=dict(size=4),
            hovertemplate="White<br>%{x}: %{y:.1%}<extra></extra>",
        ))
    if not b.empty:
        fig.add_trace(go.Scatter(
            x=b["year"], y=b["denial_rate"], name="Black / African American",
            mode="lines+markers", line=dict(color=C["crash"], width=2.6, shape="spline", smoothing=0.7),
            marker=dict(size=5),
            hovertemplate="Black / African American<br>%{x}: %{y:.1%}<extra></extra>",
        ))

    post = b[b["year"] >= 2012]["denial_rate"] if not b.empty else pd.Series(dtype=float)
    pre = b[b["year"] == 2007]["denial_rate"] if not b.empty else pd.Series(dtype=float)
    if len(post) and len(pre):
        delta_pp = (float(post.mean()) - float(pre.iloc[0])) * 100.0
        fig.add_annotation(
            x=2015, y=float(post.mean()),
            text=f"Post-2012 remained {delta_pp:+.0f} pp vs 2007 baseline",
            showarrow=False, font=dict(size=9, color=C["crash"]),
            bgcolor="rgba(255,255,255,0.9)", bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
        )

    fig.update_layout(**_base_layout(
        height=H_SM + 70,
        margin=dict(l=48, r=24, t=36, b=44),
        title=dict(text="Credit desert: denial persistence in middle-income applications", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"]),
        yaxis=dict(gridcolor=C["grid"], tickformat=".0%", title="Denial rate (50-80K income)"),
    ))
    return fig


def fig_homeownership_link(df: pd.DataFrame) -> go.Figure:
    """Chapter 6 outcome: homeownership trend with optional indexed purchase overlay."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.sort_values("year").copy()
    base_h = float(d[d["year"] == 2007]["homeownership_rate"].iloc[0]) if len(d[d["year"] == 2007]) else float(d["homeownership_rate"].iloc[0])
    base_p = float(d[d["year"] == 2007]["purchase_originations"].iloc[0]) if len(d[d["year"] == 2007]) else float(d["purchase_originations"].iloc[0])
    d["home_idx"] = (d["homeownership_rate"] / base_h) * 100.0 if base_h else 100.0
    d["purchase_idx"] = (d["purchase_originations"] / base_p) * 100.0 if base_p else 100.0

    fig.add_trace(go.Scatter(
        x=d["year"], y=d["home_idx"], name="Homeownership index",
        mode="lines+markers",
        line=dict(color=C["crash"], width=2.6, shape="spline", smoothing=0.7),
        marker=dict(size=5),
        hovertemplate="Homeownership index<br>%{x}: %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["purchase_idx"], name="Purchase originations index",
        mode="lines",
        line=dict(color=C["purchase"], width=1.4, dash="dot", shape="spline", smoothing=0.7),
        opacity=0.55,
        hovertemplate="Purchase index<br>%{x}: %{y:.1f}<extra></extra>",
    ))
    fig.add_hline(y=100, line=dict(color=C["muted"], width=1, dash="dot"))
    fig.add_annotation(
        x=2014, y=float(d["home_idx"].min()) + 1.0,
        text="Reduced credit access aligned with weaker entry into homeownership.",
        showarrow=False, font=dict(size=9, color=C["muted"]),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=C["border"], borderwidth=0.5, borderpad=3,
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 70,
        margin=dict(l=48, r=24, t=36, b=44),
        title=dict(text="Ownership impact: homeownership trend after tighter credit", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"]),
        yaxis=dict(gridcolor=C["grid"], title="Index (2007=100)"),
    ))
    return fig


def fig_ch6_credit_desert(df: pd.DataFrame, income_band: str = "<50K") -> go.Figure:
    """Chapter 6: low-income denial persistence with post-2012 focus."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df[df["income_band"] == income_band].copy().sort_values("year")
    if d.empty:
        return fig

    for race, color in [("White", C["white"]), ("Black / African American", C["black"])]:
        s = d[d["race"] == race]
        if s.empty:
            continue
        fig.add_trace(go.Scatter(
            x=s["year"], y=s["denial_rate"],
            mode="lines+markers",
            name=race,
            line=dict(color=color, width=2.8 if "Black" in race else 2.0, shape="spline", smoothing=0.65),
            marker=dict(size=5),
            hovertemplate=f"{race}<br>%{{x}}: %{{y:.1%}}<extra></extra>",
        ))

    fig.update_layout(**_base_layout(
        height=H_SM + 80,
        margin=dict(l=52, r=24, t=38, b=50),
        title=dict(text='The Stickiness of the "No": Persistent Racial Barriers in Lending', font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"]),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, tickformat=".0%", title="Denial Rate (%)"),
        legend=dict(
            x=0.98, y=0.98, xanchor="right", yanchor="top",
            bgcolor="rgba(255,255,255,0.85)", bordercolor=C["border"], borderwidth=0.5,
        ),
    ))
    return fig


def fig_ch7_shadow_bump(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Chapter 7: top-lender rank trajectories with highlight/mute styling."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = (
        df.groupby(["year", "institution", "lender_type"], as_index=False)["originations"]
        .sum()
        .dropna(subset=["year", "institution", "originations"])
    )
    if d.empty:
        return fig
    d = d.sort_values(["year", "originations"], ascending=[True, False])
    d["rank"] = d.groupby("year")["originations"].rank(method="first", ascending=False).astype(int)
    d = d[d["rank"] <= top_n].copy()
    if d.empty:
        return fig

    keep = d.groupby("institution")["year"].nunique().sort_values(ascending=False).head(top_n).index
    d = d[d["institution"].isin(keep)].copy()

    highlight_terms = ["rocket", "quicken", "loandepot", "united wholesale", "uwm"]
    bank_terms = ["wells fargo", "chase", "jpmorgan", "bank of america", "bofa", "citibank", "citi"]

    for inst, sub in d.groupby("institution"):
        inst_l = str(inst).lower()
        lt = str(sub["lender_type"].mode().iloc[0]) if "lender_type" in sub.columns and len(sub["lender_type"]) else "Bank"
        is_highlight = any(t in inst_l for t in highlight_terms)
        is_big_bank = any(t in inst_l for t in bank_terms)
        if is_highlight:
            color, width, op = C["nonbank"], 3.8, 0.95
        elif is_big_bank:
            color, width, op = "#8F949A", 2.2, 0.8
        else:
            color, width, op = ("#C5C9CE" if lt == "Bank" else "#D7B2A8"), 1.2, 0.4
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["rank"],
            mode="lines+markers",
            name=inst,
            line=dict(color=color, width=width, shape="spline", smoothing=0.55),
            marker=dict(size=4 if not is_highlight else 6),
            opacity=op,
            customdata=np.c_[sub["originations"], sub["lender_type"]],
            hovertemplate="<b>%{fullData.name}</b><br>Year: %{x}<br>Rank: %{y}<br>Originations: %{customdata[0]:,.0f}<br>Type: %{customdata[1]}<extra></extra>",
            showlegend=False,
        ))

    latest = int(d["year"].max())
    labels = d[d["year"] == latest].sort_values("rank")
    fig.add_trace(go.Scatter(
        x=labels["year"] + 0.12,
        y=labels["rank"],
        mode="text",
        text=labels["institution"],
        textposition="middle left",
        textfont=dict(size=9, color=C["text"]),
        hoverinfo="skip",
        showlegend=False,
    ))

    fig.update_layout(**_base_layout(
        height=H_LG,
        margin=dict(l=54, r=170, t=40, b=52),
        title=dict(text="The Great Decoupling: Markets Recovered, People Didn't", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], title="Year"),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, autorange="reversed", dtick=1, title="Rank (1 = largest)"),
    ))
    return fig


def fig_ch7_concentration_shift(df: pd.DataFrame) -> go.Figure:
    """Chapter 7: 100% stacked area for bank vs nonbank with HHI stat callout."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    by_type = df.groupby(["year", "lender_type"], as_index=False)["originations"].sum()
    piv = by_type.pivot(index="year", columns="lender_type", values="originations").fillna(0)
    if "Bank" not in piv.columns:
        piv["Bank"] = 0
    if "Nonbank" not in piv.columns:
        piv["Nonbank"] = 0
    piv = piv.reset_index().sort_values("year")
    total = (piv["Bank"] + piv["Nonbank"]).replace(0, np.nan)
    piv["nonbank_share"] = piv["Nonbank"] / total

    by_inst = df.groupby(["year", "institution"], as_index=False)["originations"].sum()
    by_inst["total"] = by_inst.groupby("year")["originations"].transform("sum")
    by_inst = by_inst[by_inst["total"] > 0].copy()
    by_inst["s"] = by_inst["originations"] / by_inst["total"]
    hhi = by_inst.groupby("year", as_index=False).apply(lambda g: (g["s"] ** 2).sum(), include_groups=False)
    hhi.columns = ["year", "hhi"]
    if not hhi.empty:
        hhi["hhi_idx"] = (hhi["hhi"] / hhi["hhi"].iloc[0]) * 100.0 if hhi["hhi"].iloc[0] else np.nan

    fig.add_trace(go.Scatter(
        x=piv["year"], y=(1 - piv["nonbank_share"]),
        mode="lines",
        name="Bank share",
        line=dict(color="#23364D", width=2.2, shape="spline", smoothing=0.6),
        stackgroup="one", groupnorm="fraction", fill="tozeroy",
        hovertemplate="Bank share<br>%{x}: %{y:.1%}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=piv["year"], y=piv["nonbank_share"],
        mode="lines",
        name="Nonbank share",
        line=dict(color=C["nonbank"], width=3.4, shape="spline", smoothing=0.6),
        stackgroup="one", groupnorm="fraction", fill="tonexty",
        hovertemplate="Nonbank share<br>%{x}: %{y:.1%}<extra></extra>",
    ))

    if not hhi.empty:
        hhi = hhi.sort_values("year")
        h2013 = float(hhi[hhi["year"] == 2013]["hhi"].iloc[0]) if len(hhi[hhi["year"] == 2013]) else float(hhi["hhi"].iloc[0])
        hlast = float(hhi["hhi"].iloc[-1]) if len(hhi) else h2013
        up = ((hlast / h2013) - 1.0) * 100.0 if h2013 else 0.0
        fig.add_annotation(
            x=0.98, y=0.95, xref="paper", yref="paper",
            text=f"Market concentration: {'up' if up >= 0 else 'down'} {abs(up):.0f}% since 2013",
            showarrow=False, xanchor="right", yanchor="top",
            font=dict(size=10, color=C["crash"] if up >= 0 else C["recovery"]),
            bgcolor="rgba(255,255,255,0.94)", bordercolor=C["border"], borderwidth=0.6, borderpad=4,
        )

    fig.update_layout(**_base_layout(
        height=H_SM + 90,
        margin=dict(l=54, r=24, t=40, b=52),
        title=dict(text="", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], title="Year"),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, tickformat=".0%", title="Share of originations", range=[0, 1]),
        legend=dict(orientation="h", x=0, y=1.02, xanchor="left", yanchor="bottom"),
    ))
    return fig


def fig_ch7_winners_losers_matrix(df_lender: pd.DataFrame, df_race_share: pd.DataFrame) -> go.Figure:
    """Chapter 7: winners-vs-losers shift matrix (2007 -> 2017)."""
    fig = go.Figure()
    if (df_lender is None or df_lender.empty) and (df_race_share is None or df_race_share.empty):
        return fig

    rows = []

    if df_lender is not None and not df_lender.empty:
        d = df_lender[df_lender["year"].isin([2007, 2017])].copy()
        g = d.groupby(["year", "lender_type"], as_index=False)["originations"].sum()
        totals = g.groupby("year", as_index=False)["originations"].sum().rename(columns={"originations": "year_total"})
        g = g.merge(totals, on="year", how="left")
        g["share"] = np.where(g["year_total"] > 0, g["originations"] / g["year_total"], 0.0)

        for typ in ["Bank", "Nonbank"]:
            r07 = g[(g["year"] == 2007) & (g["lender_type"] == typ)]
            r17 = g[(g["year"] == 2017) & (g["lender_type"] == typ)]
            if r07.empty or r17.empty:
                continue
            s07 = float(r07["share"].iloc[0])
            s17 = float(r17["share"].iloc[0])
            o07 = float(r07["originations"].iloc[0])
            o17 = float(r17["originations"].iloc[0])
            raw_participation = ((o17 / o07) - 1.0) * 100.0 if o07 > 0 else 0.0
            rows.append({
                "group": "Institutions",
                "entity": "Big Banks" if typ == "Bank" else "Nonbanks",
                "delta_share_pp": (s17 - s07) * 100.0,
                "delta_participation_pp": raw_participation,
                "size_2017": o17,
            })

    if df_race_share is not None and not df_race_share.empty:
        r = df_race_share[df_race_share["year"].isin([2007, 2017])].copy()
        for race in ["White", "Black / African American", "Asian"]:
            r07 = r[(r["year"] == 2007) & (r["race"] == race)]
            r17 = r[(r["year"] == 2017) & (r["race"] == race)]
            if r07.empty or r17.empty:
                continue
            s07 = float(r07["share"].iloc[0])
            s17 = float(r17["share"].iloc[0])
            c07 = float(r07["count"].iloc[0])
            c17 = float(r17["count"].iloc[0])
            raw_participation = ((c17 / c07) - 1.0) * 100.0 if c07 > 0 else 0.0
            rows.append({
                "group": "Borrowers",
                "entity": "Black households" if race.startswith("Black") else f"{race} households",
                "delta_share_pp": (s17 - s07) * 100.0,
                "delta_participation_pp": raw_participation,
                "size_2017": c17,
            })

    m = pd.DataFrame(rows)
    if m.empty:
        return fig

    m["size_plot"] = np.sqrt(np.maximum(m["size_2017"], 1.0))
    m["size_plot"] = 18 + 38 * (m["size_plot"] - m["size_plot"].min()) / (m["size_plot"].max() - m["size_plot"].min() + 1e-9)
    m["delta_participation_scaled"] = np.sign(m["delta_participation_pp"]) * np.log1p(np.abs(m["delta_participation_pp"]))

    # Consistent color: Success Green = Nonbanks + Asian; Crisis Red = Big Banks + Black; Neutral = White
    SUCCESS_GREEN = "#2E8B57"
    CRISIS_RED    = "#C23B31"
    NEUTRAL_GREY  = "#7A7A7A"
    COLOR_MAP = {
        "Nonbanks":          SUCCESS_GREEN,
        "Big Banks":         CRISIS_RED,
        "Asian households":  SUCCESS_GREEN,
        "Black households":  CRISIS_RED,
        "White households":  NEUTRAL_GREY,
    }
    m["color"] = m["entity"].map(COLOR_MAP).fillna(NEUTRAL_GREY)

    # --- Quadrant shading (Winners top-right, Losers bottom-left) ---
    BIG = 9999
    fig.add_shape(type="rect",
        x0=0, x1=BIG, y0=0, y1=BIG, xref="x", yref="y",
        fillcolor="rgba(46,139,87,0.07)", line=dict(width=0), layer="below")
    fig.add_shape(type="rect",
        x0=-BIG, x1=0, y0=-BIG, y1=0, xref="x", yref="y",
        fillcolor="rgba(199,37,42,0.07)", line=dict(width=0), layer="below")

    # Quadrant corner labels
    fig.add_annotation(x=0.97, y=0.97, xref="paper", yref="paper",
        text="<b>WINNERS</b>", showarrow=False, xanchor="right", yanchor="top",
        font=dict(size=11, color=SUCCESS_GREEN), opacity=0.55)
    fig.add_annotation(x=0.03, y=0.03, xref="paper", yref="paper",
        text="<b>LOSERS</b>", showarrow=False, xanchor="left", yanchor="bottom",
        font=dict(size=11, color=CRISIS_RED), opacity=0.55)

    # --- Nonbanks glow effect (wider, transparent circle underneath) ---
    nonb_glow = m[m["entity"] == "Nonbanks"]
    if not nonb_glow.empty:
        fig.add_trace(go.Scatter(
            x=nonb_glow["delta_share_pp"],
            y=nonb_glow["delta_participation_scaled"],
            mode="markers",
            showlegend=False,
            marker=dict(
                size=nonb_glow["size_plot"] * 2.2,
                color=SUCCESS_GREEN,
                opacity=0.12,
                symbol="circle",
                line=dict(width=0),
            ),
            hoverinfo="skip",
        ))

    # --- Main scatter traces ---
    for grp, sym in [("Institutions", "circle"), ("Borrowers", "diamond")]:
        d = m[m["group"] == grp]
        if d.empty:
            continue
        fig.add_trace(go.Scatter(
            x=d["delta_share_pp"],
            y=d["delta_participation_scaled"],
            mode="markers",
            name=grp,
            marker=dict(
                size=d["size_plot"],
                symbol=sym,
                color=d["color"],
                line=dict(width=1.2, color="rgba(17,24,39,0.30)"),
                opacity=0.93,
            ),
            customdata=np.stack([d["entity"], d["size_2017"], d["delta_participation_pp"]], axis=1),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Market Control shift: %{x:+.1f} pp<br>"
                "Systemic Access shift: %{customdata[2]:+.1f}%<br>"
                "2017 volume: %{customdata[1]:,.0f}<extra></extra>"
            ),
        ))

    # Zero axis lines
    fig.add_hline(y=0, line_width=1.2, line_dash="dot", line_color="rgba(17,24,39,0.25)")
    fig.add_vline(x=0, line_width=1.2, line_dash="dot", line_color="rgba(17,24,39,0.25)")

    # --- Leader-line annotations for every entity ---
    # Each gets an arrow pulling label clear of the bubble
    label_offsets = {
        "Nonbanks":          (92,  -68),
        "Big Banks":         (-90,  50),
        "Asian households":  (110, -26),
        "Black households":  (-130, 24),
        "White households":  (70,   40),
    }
    label_colors = {
        "Nonbanks":          SUCCESS_GREEN,
        "Big Banks":         CRISIS_RED,
        "Asian households":  SUCCESS_GREEN,
        "Black households":  CRISIS_RED,
        "White households":  NEUTRAL_GREY,
    }
    for _, row in m.iterrows():
        entity = str(row["entity"])
        ax_, ay_ = label_offsets.get(entity, (60, -40))
        lc = label_colors.get(entity, C["text"])
        fig.add_annotation(
            x=float(row["delta_share_pp"]),
            y=float(row["delta_participation_scaled"]),
            xref="x", yref="y",
            text=f"<b>{entity}</b>",
            showarrow=True, arrowhead=2, arrowwidth=1.2,
            arrowcolor=lc, ax=ax_, ay=ay_,
            font=dict(size=10, color=lc),
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor=lc, borderwidth=0.8, borderpad=3,
        )

    # "So What-" corner note
    fig.add_annotation(
        x=0.01, y=0.03, xref="paper", yref="paper",
        text="The recovery was an institutional success — but a demographic tragedy",
        showarrow=False, xanchor="left",
        font=dict(size=10, color=C["muted"], style="italic"),
        bgcolor="rgba(255,255,255,0.90)", bordercolor=C["border"], borderwidth=0.6, borderpad=5,
    )

    y_tick_raw = [-60, -40, -20, 0, 20, 50, 100, 200, 400]
    y_tick_vals = [float(np.sign(v) * np.log1p(abs(v))) for v in y_tick_raw]
    y_tick_text = [f"{v:+.0f}%" if v != 0 else "0%" for v in y_tick_raw]

    fig.update_layout(**_base_layout(
        height=H_SM + 140,
        margin=dict(l=70, r=36, t=52, b=96),
        title=dict(
            text="The Structural Divide: Who Gained Power, Who Lost Access",
            font=dict(size=13), x=0, xanchor="left",
        ),
        xaxis=dict(
            showgrid=True, gridcolor=C["grid"], zeroline=False,
            title="Market Control (Gained →)",
            tickformat="+.0f",
            ticksuffix=" pp",
        ),
        yaxis=dict(
            showgrid=True, gridcolor=C["grid"], zeroline=False,
            title="Systemic Access (Gained ↑)",
            tickmode="array",
            tickvals=y_tick_vals,
            ticktext=y_tick_text,
        ),
        legend=dict(orientation="h", x=0.5, y=-0.16, xanchor="center", yanchor="top"),
    ))
    return fig


def fig_ch6_funnel_leak(df_denial: pd.DataFrame, df_loan: pd.DataFrame, profile: str, year: int = 2017) -> go.Figure:
    """Chapter 6: applications->approved/denied->loan-type funnel for selected borrower profile."""
    fig = go.Figure()
    if df_denial is None or df_denial.empty or df_loan is None or df_loan.empty:
        return fig

    try:
        race, band = profile.split("|", 1)
    except ValueError:
        race, band = "White", "100-150K"

    den = df_denial[(df_denial["year"] == year) & (df_denial["race"] == race) & (df_denial["income_band"] == band)]
    if den.empty:
        return fig
    denial_rate = float(den["denial_rate"].iloc[0])
    applications = 10000.0
    denied = applications * denial_rate
    approved = applications - denied

    lt = df_loan[df_loan["year"] == year].copy()
    if lt.empty:
        return fig
    lt = lt.groupby("loan_type", as_index=False)["share"].sum()
    lt = lt[lt["loan_type"].isin(["Conventional", "FHA", "VA", "FSA/RHS"])].copy()
    if lt.empty:
        return fig
    lt["share_norm"] = lt["share"] / lt["share"].sum()
    lt["approved_flow"] = approved * lt["share_norm"]

    nodes = [f"Applications\n{race}, {band}", "Approved", "Denied"] + lt["loan_type"].tolist()
    source = [0, 0] + [1] * len(lt)
    target = [1, 2] + list(range(3, 3 + len(lt)))
    value = [approved, denied] + lt["approved_flow"].tolist()

    color_map = {
        "Conventional": C["conventional"],
        "FHA": C["fha"],
        "VA": C["va"],
        "FSA/RHS": C["fsa"],
    }
    node_colors = [C["muted"], C["recovery"], C["crash"]] + [color_map.get(t, C["muted"]) for t in lt["loan_type"]]

    fig.add_trace(go.Sankey(
        arrangement="snap",
        node=dict(
            label=nodes,
            color=node_colors,
            pad=18,
            thickness=16,
            line=dict(color="rgba(255,255,255,0.85)", width=0.8),
        ),
        link=dict(
            source=source,
            target=target,
            value=value,
            color=["rgba(44,122,90,0.45)", "rgba(215,38,30,0.45)"] + ["rgba(40,92,154,0.25)"] * len(lt),
            hovertemplate="%{source.label} -> %{target.label}<br>Flow: %{value:,.0f}<extra></extra>",
        ),
    ))

    fig.update_layout(**_base_layout(
        height=H_SM + 110,
        margin=dict(l=12, r=12, t=40, b=20),
        title=dict(text=f"Funnel leak ({year}): applications to outcomes", font=dict(size=13), x=0, xanchor="left"),
        showlegend=False,
    ))
    return fig


def fig_ch6_great_decoupling(df_ho: pd.DataFrame, df_collapse: pd.DataFrame) -> go.Figure:
    """Chapter 6: indexed homeownership vs indexed credit conditions (2007=100)."""
    fig = go.Figure()
    if df_ho is None or df_ho.empty or df_collapse is None or df_collapse.empty:
        return fig

    h = df_ho[["year", "homeownership_rate"]].dropna().copy()
    c = df_collapse[["year", "origination_rate"]].dropna().copy()
    d = h.merge(c, on="year", how="inner").sort_values("year")
    if d.empty:
        return fig

    h0 = d[d["year"] == 2007]["homeownership_rate"]
    c0 = d[d["year"] == 2007]["origination_rate"]
    if h0.empty or c0.empty or float(h0.iloc[0]) == 0 or float(c0.iloc[0]) == 0:
        return fig

    d["home_idx"] = (d["homeownership_rate"] / float(h0.iloc[0])) * 100.0
    d["credit_idx"] = (d["origination_rate"] / float(c0.iloc[0])) * 100.0
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["credit_idx"],
        mode="lines+markers",
        name="Credit conditions index",
        line=dict(color=C["govt"], width=2.6, shape="spline", smoothing=0.65),
        marker=dict(size=5),
        hovertemplate="Credit index<br>%{x}: %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["home_idx"],
        mode="lines+markers",
        name="Homeownership index",
        line=dict(color=C["warning"], width=2.6, shape="spline", smoothing=0.65),
        marker=dict(size=5),
        hovertemplate="Homeownership index<br>%{x}: %{y:.1f}<extra></extra>",
    ))

    post = d[d["year"] >= 2012]
    if not post.empty:
        fig.add_trace(go.Scatter(
            x=post["year"], y=post["credit_idx"],
            mode="lines",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=post["year"], y=post["home_idx"],
            mode="lines",
            fill="tonexty",
            fillcolor="rgba(215,38,30,0.10)",
            line=dict(width=0),
            hoverinfo="skip",
            showlegend=False,
        ))

    fig.add_hline(y=100, line=dict(color=C["muted"], width=1.1, dash="dot"))
    if (d["year"] == 2013).any():
        fig.add_vline(x=2013, line=dict(color=C["crash"], width=1.2, dash="dash"))
        fig.add_annotation(
            x=2013.1, y=0.95, xref="x", yref="paper",
            text="The Decoupling Point",
            showarrow=False, xanchor="left",
            font=dict(size=10, color=C["crash"]),
            bgcolor="rgba(255,255,255,0.92)", bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
        )
    fig.add_annotation(
        x=0.78, y=0.20, xref="paper", yref="paper",
        text="The Rent Gap:<br>markets recovered, people didn't.",
        showarrow=False, xanchor="center",
        font=dict(size=10, color=C["crash"]),
        bgcolor="rgba(255,255,255,0.92)", bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
    )
    fig.update_layout(**_base_layout(
        height=H_SM + 70,
        margin=dict(l=52, r=24, t=38, b=50),
        title=dict(text="", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"]),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, title="Index (Baseline 2007 = 100)"),
        legend=dict(
            x=0.98, y=0.98, xanchor="right", yanchor="top",
            bgcolor="rgba(255,255,255,0.85)", bordercolor=C["border"], borderwidth=0.5,
        ),
    ))
    return fig


def fig_ch1_risk_mix(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.copy()
    order = ["Conventional", "FHA", "VA", "FSA/RHS"]
    colors = {
        "Conventional": C["conventional"],
        "FHA": C["fha"],
        "VA": C["va"],
        "FSA/RHS": C["fsa"],
    }
    for i, lt in enumerate(order):
        sub = d[d["loan_type"] == lt].sort_values("year")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["share"], mode="lines", name=lt,
            line=dict(color=colors[lt], width=1.5, shape="spline", smoothing=0.7),
            stackgroup="one",
            groupnorm="fraction",
            fill="tonexty" if i > 0 else "tozeroy",
            hovertemplate=f"{lt}<br>%{{x}}: %{{y:.1%}}<extra></extra>",
        ))

    fig.update_layout(**_base_layout(
        height=H_SM + 80,
        title=dict(text="Market structure: loan-type composition", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, dtick=1, tickcolor=C["border"], automargin=True),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], tickformat=".0%", title="Share of originations", range=[0, 1.0], automargin=True),
        showlegend=False,
    ))
    return fig


def fig_ch1_demand_gap(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df is None or df.empty:
        return fig
    d = df.sort_values("year")
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["applications"], name="Applications",
        mode="lines", line=dict(color=C["muted"], width=2.0, shape="spline", smoothing=0.7),
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["originations"], name="Originations",
        mode="lines", line=dict(color=C["recovery"], width=2.4, shape="spline", smoothing=0.7),
        fill="tonexty", fillcolor="rgba(199,37,42,0.14)",
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
    ))
    fig.add_annotation(
        x=2011, y=float(d[d["year"] == 2011]["applications"].iloc[0]) if len(d[d["year"] == 2011]) else float(d["applications"].max()*0.7),
        text="Shaded gap = unmet demand",
        showarrow=False, font=dict(size=9, color=C["crash"]),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=C["crash"], borderwidth=0.5, borderpad=4,
    )
    fig.update_layout(**_base_layout(
        height=H_SM + 80,
        title=dict(text="Demand vs supply mechanism", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, dtick=1, tickcolor=C["border"]),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], tickformat=".2s", title="Loan count"),
    ))
    return fig


def fig_ch1_snapshot_pie(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df is None or df.empty:
        return fig
    d2007 = df[df["year"] == 2007].copy()
    if d2007.empty:
        d2007 = df.sort_values("year").head(4)
    fig.add_trace(go.Pie(
        labels=d2007["loan_type"],
        values=d2007["share"],
        hole=0.62,
        marker=dict(colors=[C["conventional"], C["fha"], C["va"], C["fsa"]]),
        textinfo="percent",
        textposition="inside",
        sort=False,
    ))
    conventional = d2007[d2007["loan_type"] == "Conventional"]["share"]
    gov = d2007[d2007["loan_type"].isin(["FHA", "VA", "FSA/RHS"])]["share"].sum()
    conv_txt = f"{float(conventional.iloc[0]):.1%}" if len(conventional) else "n/a"
    fig.add_annotation(
        x=0.5, y=0.52, xref="paper", yref="paper",
        text=f"<b>{conv_txt}</b><br>Conventional",
        showarrow=False,
        font=dict(size=11, color=C["text"]),
    )
    fig.add_annotation(
        x=0.5, y=0.17, xref="paper", yref="paper",
        text=f"Gov-backed safety net: {float(gov):.1%}",
        showarrow=False,
        font=dict(size=9, color=C["muted"]),
    )
    fig.update_layout(
        height=230,
        margin=dict(l=10, r=10, t=34, b=10),
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["bg"],
        font=dict(family=FONT, size=11, color=C["text"]),
        title=dict(text="The conventional monoculture (2007)", font=dict(size=12), x=0, xanchor="left"),
        showlegend=False,
    )
    return fig


def fig_ch1_toxic_tail(df: pd.DataFrame) -> go.Figure:
    """Chapter 1: 2007 LTI density with toxic-zone highlight."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.copy()
    year_col = "year" if "year" in d.columns else "as_of_year"
    if year_col not in d.columns or "lti_ratio" not in d.columns:
        return fig

    d = d[(d[year_col] == 2007) & d["lti_ratio"].notna()].copy()
    if d.empty:
        return fig

    full = d["lti_ratio"].astype(float)
    display = full.clip(lower=0, upper=8.0)
    safe = display[display <= 4.5]
    toxic = display[display > 4.5]
    tail_share = float((full > 4.5).mean())
    gt8_share = float((full > 8.0).mean())

    bins = dict(start=0.0, end=8.0, size=0.18)
    fig.add_trace(go.Histogram(
        x=safe,
        xbins=bins,
        histnorm="probability density",
        name="LTI <= 4.5",
        marker=dict(color="rgba(118,118,118,0.65)"),
        hovertemplate="Safe-zone density: %{y:.3f}<extra></extra>",
        showlegend=False,
    ))
    fig.add_trace(go.Histogram(
        x=toxic,
        xbins=bins,
        histnorm="probability density",
        name="LTI > 4.5 (toxic zone)",
        marker=dict(color="rgba(215,38,30,0.75)"),
        hovertemplate="Toxic-zone density: %{y:.3f}<extra></extra>",
        showlegend=False,
    ))

    fig.add_vline(x=4.5, line=dict(color=C["crash"], width=1.5, dash="dash"))
    fig.add_annotation(
        x=4.55, y=0.96, xref="x", yref="paper",
        text="Toxic threshold (LTI > 4.5)",
        showarrow=False, xanchor="left",
        font=dict(size=9, color=C["crash"]),
        bgcolor="rgba(255,255,255,0.92)", bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
    )
    fig.add_annotation(
        x=0.98, y=0.90, xref="paper", yref="paper",
        text=f">4.5 share: <b>{tail_share:.1%}</b><br>>8.0 share: {gt8_share:.1%}",
        showarrow=False, xanchor="right",
        font=dict(size=9, color=C["text"]),
        bgcolor="rgba(255,255,255,0.90)", bordercolor=C["border"], borderwidth=0.5, borderpad=4,
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 80,
        barmode="overlay",
        title=dict(text="The toxic tail: extreme leverage in the pre-crisis market (2007)", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(title="Loan-to-income (LTI) ratio", showgrid=False, range=[0, 8.0], tickcolor=C["border"]),
        yaxis=dict(title="Density of loans", showgrid=True, gridcolor=C["grid"], zeroline=False),
    ))
    return fig


def fig_collapse(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    if df is None or df.empty:
        return fig
    d = df.sort_values("year").copy()
    d["gap"] = d["applications"] - d["originations"]
    d["rejection_rate"] = d["gap"] / d["applications"]

    mortgage_rates = {
        2007: 6.34, 2008: 6.03, 2009: 5.04, 2010: 4.69, 
        2011: 4.45, 2012: 3.66, 2013: 3.98, 2014: 4.17, 
        2015: 3.85, 2016: 3.65, 2017: 3.99
    }
    unemployment_rates = {
        2007: 4.6,  2008: 5.8,  2009: 9.3,  2010: 9.6,  
        2011: 8.9,  2012: 8.1,  2013: 7.4,  2014: 6.2,  
        2015: 5.3,  2016: 4.9,  2017: 4.4
    }
    
    d["mortgage_rate"] = d["year"].map(mortgage_rates)
    d["unemployment_rate"] = d["year"].map(unemployment_rates)

    # 1. Originations (Bottom layer)
    fig.add_trace(go.Bar(
        x=d["year"], y=d["originations"],
        name="Originations (Approved)",
        marker_color=C["recovery"],
        marker_line_width=0,
        opacity=0.85,
        hovertemplate="Originated: %{y:,.0f}<extra></extra>",
    ))

    # 2. Unmet Demand (Top layer)
    fig.add_trace(go.Bar(
        x=d["year"], y=d["gap"],
        name="Unmet Demand (Gap)",
        marker=dict(
            color="rgba(199,37,42,0.15)",  # light red
            line=dict(color=C["crash"], width=1.5)
        ),
        hovertemplate="Unmet demand: %{y:,.0f}<extra></extra>",
    ))
    
    # 3. Mortgage Rate (Secondary Y-axis Line)
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["mortgage_rate"],
        name="30-Year Mortgage Rate",
        mode="lines+markers",
        yaxis="y2",
        line=dict(color="#DE9E36", width=2.5, dash="dot"),
        marker=dict(size=7, color="#DE9E36", symbol="diamond"),
        hovertemplate="Mortgage Rate: %{y:.2f}%<extra></extra>",
    ))
    
    # 4. Unemployment Rate (Secondary Y-axis Line)
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["unemployment_rate"],
        name="Unemployment Rate",
        mode="lines+markers",
        yaxis="y2",
        line=dict(color="#285C9A", width=2.5, dash="dash"),
        marker=dict(size=7, color="#285C9A", symbol="square"),
        hovertemplate="Unemployment: %{y:.1f}%<extra></extra>",
    ))

    # 5. Add rejection rate as text directly on top of the bars
    for i, row in d.iterrows():
        fig.add_annotation(
            x=row["year"],
            y=row["applications"],
            text=f"{row['rejection_rate']:.0%}",
            showarrow=False,
            yshift=12,
            font=dict(size=10, color=C["crash"], weight="bold")
        )

    # 6. Crisis line indicator
    fig.add_vline(x=2008, line=dict(color=C["crash"], width=1, dash="dash"))
    
    y_anno = float(d["applications"].max()) * 0.88
    fig.add_annotation(
        x=2015.5,
        y=y_anno,
        text="<b>The red box is UNMET DEMAND.</b><br>Notice how rejection rates spike post-2008.",
        showarrow=False,
        font=dict(size=11, color=C["crash"]),
        bgcolor="rgba(255,245,245,0.96)",
        bordercolor=C["crash"],
        borderwidth=0.5,
        borderpad=6,
        xanchor="center"
    )

    fig.update_layout(**_base_layout(
        height=H,
        barmode="stack",
        bargap=0.3,
        title=dict(text="Credit gap & Macro environment (Rates & Employment)", font=dict(size=14, weight="bold"), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], automargin=True),
        yaxis=dict(title="Loan count", gridcolor=C["grid"], zeroline=False, tickformat=".2s", automargin=True),
        yaxis2=dict(
            title="Rates (%)",
            overlaying="y",
            side="right",
            showgrid=False,
            zeroline=False,
            tickformat=".1f",
            range=[0, 11]  # Expanded to fit the ~10% unemployment peak
        ),
        legend=dict(orientation="h", y=1.05, x=0, xanchor="left", font=dict(size=11))
    ))
    return fig


def fig_origination_rate(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df is None or df.empty:
        return fig
    d = df.sort_values("year").dropna(subset=["origination_rate"])
    if d.empty:
        return fig

    fig.add_trace(go.Scatter(
        x=d["year"], y=d["origination_rate"],
        mode="lines+markers",
        name="Approval rate",
        line=dict(color=C["crash"], width=2.8, shape="spline", smoothing=0.7),
        marker=dict(size=6, color=C["crash"]),
        fill="tozeroy",
        fillcolor="rgba(226,75,74,0.08)",
        hovertemplate="%{x}: %{y:.1%}<extra></extra>",
    ))

    _pre = d[d["year"] == 2007]["origination_rate"]
    pre_crisis = _pre.values[0] if len(_pre) > 0 else None
    if pre_crisis is None:
        return fig

    fig.add_hline(
        y=pre_crisis,
        line=dict(color=C["muted"], width=1, dash="dot"),
        annotation_text=f"2007 baseline: {pre_crisis:.0%}",
        annotation_position="right",
        annotation_font=dict(size=9, color=C["muted"]),
    )

    bottom = d.loc[d["origination_rate"].idxmin()]
    fig.add_annotation(
        x=bottom["year"], y=bottom["origination_rate"],
        text=f"Bottom: {bottom['origination_rate']:.0%}",
        showarrow=True, arrowhead=2,
        ax=0, ay=-30,
        font=dict(size=9, color=C["crash"]),
    )

    ymin = float(d["origination_rate"].min())
    ymax = float(d["origination_rate"].max())
    if ymin == ymax:
        ymin = max(0.0, ymin - 0.06)
        ymax = min(1.05, ymax + 0.02)
    else:
        pad = max(0.02, (ymax - ymin) * 0.2)
        ymin = max(0.0, ymin - pad)
        ymax = min(1.05, ymax + pad)
    if float(d["origination_rate"].nunique()) == 1.0 and float(d["origination_rate"].iloc[0]) >= 0.99:
        fig.add_annotation(
            x=float(d["year"].median()), y=ymax - 0.01,
            text="Observed approval rate is flat at 100% in this scoped file.",
            showarrow=False, font=dict(size=9, color=C["muted"]),
            bgcolor="rgba(255,255,255,0.9)", bordercolor=C["border"], borderwidth=0.5, borderpad=3,
        )

    fig.update_layout(**_base_layout(
        height=H_SM,
        margin=dict(l=48, r=100, t=20, b=40),
        title=dict(
            text="Approval rate (originations / applications)",
            font=dict(size=12), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False, tickcolor=C["border"], dtick=1),
        yaxis=dict(gridcolor=C["grid"], zeroline=False, tickformat=".0%", range=[ymin, ymax]),
        showlegend=False,
    ))
    return fig


def fig_ch4_lti_income_groups(df: pd.DataFrame) -> go.Figure:
    """Chapter 4 primary: leverage by simplified income groups."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.copy()
    mapping = {
        "<50K": "Low income (<50K)",
        "50-80K": "Middle income (50-100K)",
        "80-100K": "Middle income (50-100K)",
        "100-150K": "Higher income (100K+)",
        "150K+": "Higher income (100K+)",
    }
    d["group"] = d["income_band"].map(mapping)
    d = d.dropna(subset=["group", "lti_ratio"])
    med = d.groupby(["year", "group"], as_index=False)["lti_ratio"].median()
    order = ["Low income (<50K)", "Middle income (50-100K)", "Higher income (100K+)"]
    colors = {
        "Low income (<50K)": "#9AA3AE",
        "Middle income (50-100K)": C["crash"],
        "Higher income (100K+)": "#4C78A8",
    }
    widths = {
        "Low income (<50K)": 1.8,
        "Middle income (50-100K)": 3.0,
        "Higher income (100K+)": 1.8,
    }
    for g in order:
        sub = med[med["group"] == g].sort_values("year")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["lti_ratio"],
            mode="lines+markers", name=g,
            line=dict(color=colors[g], width=widths[g], shape="spline", smoothing=0.7),
            marker=dict(size=5),
            hovertemplate=f"{g}<br>%{{x}}: %{{y:.2f}}x<extra></extra>",
        ))

    fig.add_hline(y=3.0, line=dict(color=C["muted"], width=1.2, dash="dot"))
    mid = med[med["group"] == "Middle income (50-100K)"]
    if not mid.empty:
        pk = mid.loc[mid["lti_ratio"].idxmax()]
        fig.add_annotation(
            x=pk["year"], y=pk["lti_ratio"],
            text="Leverage was highest among middle-income borrowers - not the poorest.",
            showarrow=True, arrowhead=2, ax=35, ay=-30,
            font=dict(size=9, color=C["crash"]),
            bgcolor="rgba(255,255,255,0.9)", bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
        )

    fig.update_layout(**_base_layout(
        height=H,
        title=dict(text="Leverage by income group (median loan-to-income)", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], automargin=True),
        yaxis=dict(gridcolor=C["grid"], zeroline=False, title="Median LTI (x income)", automargin=True),
    ))
    return fig


def fig_ch4_above_3x(df: pd.DataFrame) -> go.Figure:
    """Chapter 4 support: leverage-threshold composition over time (100% stacked)."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.copy().dropna(subset=["year", "lti_ratio"])
    d["bucket"] = pd.cut(
        d["lti_ratio"],
        bins=[-float("inf"), 3.0, 4.0, float("inf")],
        labels=["<3x", "3-4x", ">4x"],
        right=False,
    )
    s = (
        d.groupby(["year", "bucket"], as_index=False)
        .size()
        .rename(columns={"size": "count"})
    )
    totals = s.groupby("year", as_index=False)["count"].sum().rename(columns={"count": "total"})
    s = s.merge(totals, on="year", how="left")
    s["share"] = s["count"] / s["total"]

    order = ["<3x", "3-4x", ">4x"]
    colors = {"<3x": "#9AA3AE", "3-4x": C["warning"], ">4x": C["crash"]}
    for i, b in enumerate(order):
        sub = s[s["bucket"] == b].sort_values("year")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["year"],
            y=sub["share"],
            mode="lines",
            name=b,
            line=dict(color=colors[b], width=2.0, shape="spline", smoothing=0.7),
            stackgroup="one",
            groupnorm="fraction",
            fill="tonexty" if i > 0 else "tozeroy",
            hovertemplate=f"{b}<br>%{{x}}: %{{y:.1%}}<extra></extra>",
        ))

    hi = s[s["bucket"] == ">4x"].sort_values("year")
    if not hi.empty:
        pk = hi.loc[hi["share"].idxmax()]
        fig.add_annotation(
            x=pk["year"], y=0.92,
            text=f"High-stress share (>4x) peaks at {pk['share']:.0%}",
            showarrow=False, font=dict(size=9, color=C["crash"]),
            bgcolor="rgba(255,255,255,0.9)", bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
        )

    fig.update_layout(**_base_layout(
        height=H_SM + 80,
        title=dict(text="How widespread was high leverage- Loan mix by leverage threshold", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, tickcolor=C["border"], automargin=True, dtick=1),
        yaxis=dict(gridcolor=C["grid"], tickformat=".0%", title="Share of all loans", automargin=True, range=[0, 1]),
        legend=dict(orientation="h", x=0, y=1.02, xanchor="left", yanchor="bottom"),
    ))
    return fig


def fig_purchase_refi_share(df: pd.DataFrame) -> go.Figure:
    """Chapter 2: show composition shift with a clean Line Chart."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.sort_values("year").copy()

    # 1. New Home Purchases (Solid Line)
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["purchase"],
        name="New Home Purchases",
        mode="lines+markers",
        line=dict(color=C["purchase"], width=3),
        marker=dict(size=8, symbol="circle"),
        hovertemplate="Purchases: %{y:,.0f}<extra></extra>",
    ))

    # 2. Refinancing (Dashed Line)
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["refinance"],
        name="Refinancing",
        mode="lines+markers",
        line=dict(color=C["refi"], width=3, dash="dot"),
        marker=dict(size=8, symbol="square"),
        hovertemplate="Refinancing: %{y:,.0f}<extra></extra>",
    ))

    # 3. Annotate the 2012 Refi Boom
    max_refi = d.loc[d["refinance"].idxmax()]
    fig.add_annotation(
        x=max_refi["year"],
        y=max_refi["refinance"] + 250000,
        text=f"<b>A 'Fake' Recovery</b><br>Refinance applications spiked entirely independent of purchases.",
        showarrow=False,
        font=dict(size=11, color=C["crash"]),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor=C["crash"],
        borderwidth=0.5,
        borderpad=4
    )

    fig.update_layout(**_base_layout(
        height=H,
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], automargin=True),
        yaxis=dict(gridcolor=C["grid"], zeroline=False, tickformat=".1s", title="Absolute Loan Count", automargin=True),
        legend=dict(orientation="h", x=0, y=1.05, xanchor="left", yanchor="bottom")
    ))
    return fig


def fig_fha_phases(df: pd.DataFrame) -> go.Figure:
    """Chapter 3: simplified credit substitution view (private vs government-backed)."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.copy()
    gov = d[d["loan_type"].isin(["FHA", "VA", "FSA/RHS"])].groupby("year", as_index=False)["share"].sum()
    conv = d[d["loan_type"] == "Conventional"][["year", "share"]].rename(columns={"share": "conv_share"})
    m = gov.merge(conv, on="year", how="outer").fillna(0).sort_values("year")
    total = (m["share"] + m["conv_share"]).replace(0, pd.NA)
    m["gov_norm"] = m["share"] / total
    m["conv_norm"] = m["conv_share"] / total

    fig.add_trace(go.Scatter(
        x=m["year"], y=m["conv_norm"],
        mode="lines", name="Conventional (private)",
        line=dict(color=C["conventional"], width=2.0, shape="spline", smoothing=0.7),
        stackgroup="one", groupnorm="fraction", fill="tozeroy",
        hovertemplate="Conventional (private)<br>%{x}: %{y:.1%}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=m["year"], y=m["gov_norm"],
        mode="lines", name="Government-backed total",
        line=dict(color=C["govt"], width=2.0, shape="spline", smoothing=0.7),
        stackgroup="one", groupnorm="fraction", fill="tonexty",
        hovertemplate="Government-backed total<br>%{x}: %{y:.1%}<extra></extra>",
    ))

    fig.add_vline(x=2008, line=dict(color=C["border"], width=1.0, dash="dot"))

    fig.update_layout(**_base_layout(
        height=H,
        margin=dict(l=48, r=28, t=36, b=44),
        title=dict(text="Credit substitution: private to government-backed lending", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, tickcolor=C["border"], dtick=1, automargin=True),
        yaxis=dict(gridcolor=C["grid"], zeroline=False, tickformat=".0%", title="Share of lending", range=[0, 1.0], automargin=True),
        showlegend=False,
    ))

    return fig


def fig_ch4_refi_mirage(df_pr: pd.DataFrame, df_ho: pd.DataFrame) -> go.Figure:
    """Chapter 4: refinance surge vs homeownership floor."""
    fig = go.Figure()
    if df_pr is None or df_pr.empty:
        return fig

    d = df_pr.copy().sort_values("year")
    ho = df_ho[["year", "homeownership_rate"]].copy() if df_ho is not None and not df_ho.empty else pd.DataFrame(columns=["year", "homeownership_rate"])
    m = d.merge(ho, on="year", how="left")

    fig.add_trace(go.Scatter(
        x=m["year"], y=m["purchase"],
        mode="lines",
        name="Purchase",
        stackgroup="one",
        line=dict(color=C["purchase"], width=2.2, shape="spline", smoothing=0.65),
        fill="tozeroy",
        hovertemplate="Purchase: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=m["year"], y=m["refinance"],
        mode="lines",
        name="Refinance",
        stackgroup="one",
        line=dict(color=C["crash"], width=2.2, shape="spline", smoothing=0.65),
        fill="tonexty",
        hovertemplate="Refinance: %{y:,.0f}<extra></extra>",
    ))

    if "homeownership_rate" in m.columns and m["homeownership_rate"].notna().any():
        fig.add_trace(go.Scatter(
            x=m["year"], y=m["homeownership_rate"],
            mode="lines+markers",
            name="Homeownership floor",
            yaxis="y2",
            line=dict(color=C["muted"], width=2.0, dash="dash"),
            marker=dict(size=4),
            hovertemplate="Homeownership: %{y:.1f}%<extra></extra>",
        ))
        base = m[m["year"] == 2007]["homeownership_rate"]
        if not base.empty:
            fig.add_hline(y=float(base.iloc[0]), yref="y2", line=dict(color=C["muted"], width=1, dash="dot"))

    cond = (m["refinance"] > m["purchase"])
    if "homeownership_rate" in m.columns and m["homeownership_rate"].notna().any():
        h07 = m[m["year"] == 2007]["homeownership_rate"]
        if not h07.empty:
            cond = cond & (m["homeownership_rate"] <= float(h07.iloc[0]))
    years = m.loc[cond, "year"].tolist()
    if years:
        fig.add_vrect(
            x0=min(years) - 0.2, x1=max(years) + 0.2,
            fillcolor="rgba(215,38,30,0.08)", line_width=0,
        )
        fig.add_annotation(
            x=min(years), y=0.98, xref="x", yref="paper",
            text="Refi mirage zone: debt churn without ownership lift",
            showarrow=False, xanchor="left",
            font=dict(size=10, color=C["crash"]),
            bgcolor="rgba(255,255,255,0.92)", bordercolor=C["crash"], borderwidth=0.5, borderpad=3,
        )

    fig.update_layout(**_base_layout(
        height=H,
        margin=dict(l=54, r=52, t=40, b=48),
        title=dict(text="The refi mirage: volume rose while ownership stalled", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"]),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, tickformat=".2s", title="Loan count"),
        yaxis2=dict(
            overlaying="y", side="right", showgrid=False, zeroline=False,
            tickformat=".1f", title="Homeownership rate (%)",
        ),
        legend=dict(orientation="h", x=0, y=1.02, xanchor="left", yanchor="bottom"),
    ))
    return fig


def fig_ch6_funnel_compare(df_denial: pd.DataFrame, df_loan: pd.DataFrame, year: int = 2017) -> go.Figure:
    """Chapter 6: side-by-side funnel leak comparison for two borrower profiles."""
    fig = go.Figure()
    if df_denial is None or df_denial.empty or df_loan is None or df_loan.empty:
        return fig

    def profile_data(profile: str):
        race, band = profile.split("|", 1)
        den = df_denial[(df_denial["year"] == year) & (df_denial["race"] == race) & (df_denial["income_band"] == band)]
        if den.empty:
            return None
        denial_rate = float(den["denial_rate"].iloc[0])
        applications = 10000.0
        denied = applications * denial_rate
        approved = applications - denied
        conv = approved / applications if applications else 0.0
        lt = df_loan[df_loan["year"] == year].copy()
        lt = lt.groupby("loan_type", as_index=False)["share"].sum()
        lt = lt[lt["loan_type"].isin(["Conventional", "FHA", "VA", "FSA/RHS"])].copy()
        if lt.empty:
            return None
        lt["share_norm"] = lt["share"] / lt["share"].sum()
        lt["approved_flow"] = approved * lt["share_norm"]
        return race, band, approved, denied, conv, lt

    left = profile_data("White|100-150K")
    right = profile_data("Black / African American|<50K")
    if left is None or right is None:
        return fig

    for i, p in enumerate([left, right]):
        race, band, approved, denied, conv, lt = p
        nodes = [f"Applications\n{race}, {band}", "Approved", "Denied"] + lt["loan_type"].tolist()
        source = [0, 0] + [1] * len(lt)
        target = [1, 2] + list(range(3, 3 + len(lt)))
        value = [approved, denied] + lt["approved_flow"].tolist()
        domain_x = [0.00, 0.46] if i == 0 else [0.54, 1.00]

        fig.add_trace(go.Sankey(
            domain=dict(x=domain_x, y=[0.08, 0.95]),
            arrangement="snap",
            node=dict(
                label=nodes,
                color=[C["muted"], C["recovery"], C["crash"]] + [C["govt"]] * len(lt),
                pad=16,
                thickness=16,
                line=dict(color="rgba(255,255,255,0.85)", width=0.8),
            ),
            link=dict(
                source=source,
                target=target,
                value=value,
                color=["rgba(44,122,90,0.45)", "rgba(215,38,30,0.52)"] + ["rgba(40,92,154,0.24)"] * len(lt),
                hovertemplate="%{source.label} -> %{target.label}<br>Flow: %{value:,.0f}<extra></extra>",
            ),
        ))
        cx = (domain_x[0] + domain_x[1]) / 2.0
        fig.add_annotation(
            x=cx, y=1.02, xref="paper", yref="paper",
            text=f"{race}, {band}<br>Conversion rate: {conv:.0%}",
            showarrow=False, xanchor="center",
            font=dict(size=10, color=C["text"]),
            bgcolor="rgba(255,255,255,0.95)", bordercolor=C["border"], borderwidth=0.5, borderpad=3,
        )

    fig.add_annotation(
        x=0.87, y=0.52, xref="paper", yref="paper",
        text="Denied leak",
        showarrow=True, arrowhead=2, ax=40, ay=-20,
        font=dict(size=13, color=C["crash"]),
        bgcolor="rgba(255,255,255,0.95)", bordercolor=C["crash"], borderwidth=0.7, borderpad=3,
    )

    try:
        conv_white = float(left[4])
        conv_black = float(right[4])
        fig.add_annotation(
            x=0.50, y=0.02, xref="paper", yref="paper",
            text=f"Conversion gap: White {conv_white:.0%} vs Black {conv_black:.0%}",
            showarrow=False, xanchor="center",
            font=dict(size=10, color=C["crash"]),
            bgcolor="rgba(255,255,255,0.95)", bordercolor=C["crash"], borderwidth=0.6, borderpad=4,
        )
    except Exception:
        pass

    fig.update_layout(**_base_layout(
        height=H_SM + 170,
        margin=dict(l=10, r=10, t=44, b=18),
        title=dict(text="The Hidden Filter: Parallel Realities in Credit Access", font=dict(size=13), x=0, xanchor="left"),
        showlegend=False,
    ))
    return fig


def fig_ch7_handover_race(df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """Chapter 7: lender handover race (top lenders by share, animated by year)."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = (
        df.groupby(["year", "institution", "lender_type"], as_index=False)["originations"]
        .sum()
        .dropna(subset=["year", "institution", "originations"])
    )
    if d.empty:
        return fig

    total = d.groupby("year", as_index=False)["originations"].sum().rename(columns={"originations": "year_total"})
    d = d.merge(total, on="year", how="left")
    d["share"] = d["originations"] / d["year_total"].replace(0, np.nan)
    d = d.sort_values(["year", "share"], ascending=[True, False])
    d["rank"] = d.groupby("year")["share"].rank(method="first", ascending=False)
    d = d[d["rank"] <= top_n].copy()
    if d.empty:
        return fig

    years = sorted(d["year"].unique().tolist())
    color_map = {"Bank": "#59616C", "Nonbank": C["nonbank"]}

    def _frame_data(y):
        s = d[d["year"] == y].sort_values("share", ascending=True)
        return go.Bar(
            x=s["share"],
            y=s["institution"],
            orientation="h",
            marker=dict(color=[color_map.get(t, C["muted"]) for t in s["lender_type"]]),
            customdata=np.c_[s["lender_type"], s["originations"]],
            hovertemplate="<b>%{y}</b><br>Type: %{customdata[0]}<br>Share: %{x:.1%}<br>Originations: %{customdata[1]:,.0f}<extra></extra>",
        )

    fig.add_trace(_frame_data(years[0]))

    frames = []
    for y in years:
        frames.append(go.Frame(data=[_frame_data(y)], name=str(y)))
    fig.frames = frames

    # Structural annotations (static)
    by_type = d.groupby(["year", "lender_type"], as_index=False)["originations"].sum()
    piv = by_type.pivot(index="year", columns="lender_type", values="originations").fillna(0).reset_index().sort_values("year")
    if "Bank" not in piv.columns:
        piv["Bank"] = 0
    if "Nonbank" not in piv.columns:
        piv["Nonbank"] = 0
    denom = (piv["Bank"] + piv["Nonbank"]).replace(0, np.nan)
    piv["nonbank_share"] = piv["Nonbank"] / denom
    over = piv[piv["nonbank_share"] >= 0.5]
    crossover = int(over["year"].min()) if not over.empty else 2014
    share_2017 = float(piv[piv["year"] == 2017]["nonbank_share"].iloc[0]) if len(piv[piv["year"] == 2017]) else np.nan

    fig.add_annotation(
        x=0.02, y=0.98, xref="paper", yref="paper",
        text="2012: Basel III / Dodd-Frank impact",
        showarrow=False, xanchor="left", yanchor="top",
        font=dict(size=9, color=C["muted"]),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=C["border"], borderwidth=0.5, borderpad=3,
    )
    fig.add_annotation(
        x=0.98, y=0.98, xref="paper", yref="paper",
        text=f"Great Handover: nonbanks cross 50% in {crossover}; reach {share_2017:.0%} by 2017" if share_2017 == share_2017 else f"Great Handover: nonbanks cross 50% in {crossover}",
        showarrow=False, xanchor="right", yanchor="top",
        font=dict(size=9, color=C["nonbank"]),
        bgcolor="rgba(255,255,255,0.9)", bordercolor=C["nonbank"], borderwidth=0.5, borderpad=3,
    )

    # Static slide cue: where Quicken/Rocket ends up by 2017, even when slider is at 2007.
    d17 = d[d["year"] == 2017].sort_values("share", ascending=False).reset_index(drop=True)
    if not d17.empty:
        d17["rank_2017"] = np.arange(1, len(d17) + 1)
        q = d17[d17["institution"].str.contains("quicken|rocket", case=False, regex=True)]
        if not q.empty:
            qrow = q.iloc[0]
            fig.add_annotation(
                x=0.985, y=0.08, xref="paper", yref="paper",
                text=f"{qrow['institution']}: Rank #{int(qrow['rank_2017'])} in 2017",
                showarrow=False, xanchor="right", yanchor="bottom",
                font=dict(size=10, color=C["nonbank"]),
                bgcolor="rgba(255,255,255,0.96)", bordercolor=C["nonbank"], borderwidth=0.8, borderpad=4,
            )

    steps = []
    for y in years:
        steps.append(
            dict(
                label=str(y),
                method="animate",
                args=[[str(y)], {"mode": "immediate", "frame": {"duration": 220, "redraw": True}, "transition": {"duration": 120}}],
            )
        )

    fig.update_layout(**_base_layout(
        height=H_LG,
        margin=dict(l=220, r=24, t=34, b=52),
        title=dict(text="", x=0, xanchor="left"),
        xaxis=dict(showgrid=True, gridcolor=C["grid"], tickformat=".0%", title="Share of originations"),
        yaxis=dict(showgrid=False, tickcolor=C["border"], automargin=True),
        showlegend=False,
        updatemenus=[dict(
            type="buttons", showactive=False, direction="left",
            x=0.0, y=1.08, xanchor="left", yanchor="bottom",
            buttons=[
                dict(label="Play", method="animate", args=[None, {"fromcurrent": True, "frame": {"duration": 280, "redraw": True}, "transition": {"duration": 120}}]),
                dict(label="Pause", method="animate", args=[[None], {"mode": "immediate", "frame": {"duration": 0, "redraw": False}, "transition": {"duration": 0}}]),
            ],
        )],
        sliders=[dict(
            active=0,
            x=0.12, y=1.06, xanchor="left", yanchor="bottom",
            len=0.86,
            currentvalue=dict(prefix="Year: ", font=dict(size=11)),
            steps=steps,
        )],
    ))
    return fig


def fig_ch4_yield_attrition(df_col: pd.DataFrame, y0: int = 2007, y1: int = 2017) -> go.Figure:
    """Chapter 4: origination yield attrition (applications -> originations)."""
    fig = go.Figure()
    if df_col is None or df_col.empty:
        return fig

    d0 = df_col[df_col["year"] == y0]
    d1 = df_col[df_col["year"] == y1]
    if d0.empty or d1.empty:
        return fig

    a0, o0 = float(d0["applications"].iloc[0]), float(d0["originations"].iloc[0])
    a1, o1 = float(d1["applications"].iloc[0]), float(d1["originations"].iloc[0])
    yld0 = (o0 / a0) if a0 else 0.0
    yld1 = (o1 / a1) if a1 else 0.0

    fig.add_trace(go.Funnel(
        name=str(y0),
        y=["Applications", "Originations"],
        x=[a0, o0],
        textinfo="value+percent initial",
        marker=dict(color=["rgba(90,90,90,0.65)", "rgba(44,122,90,0.75)"]),
        hovertemplate=f"{y0} - %{{y}}: %{{x:,.0f}}<extra></extra>",
    ))
    fig.add_trace(go.Funnel(
        name=str(y1),
        y=["Applications", "Originations"],
        x=[a1, o1],
        textinfo="value+percent initial",
        marker=dict(color=["rgba(150,150,150,0.40)", "rgba(215,38,30,0.75)"]),
        hovertemplate=f"{y1} - %{{y}}: %{{x:,.0f}}<extra></extra>",
    ))

    fig.add_annotation(
        x=0.5, y=1.04, xref="paper", yref="paper",
        text=f"Yield: {y0}={yld0:.0%} vs {y1}={yld1:.0%}",
        showarrow=False,
        font=dict(size=10, color=C["text"]),
        bgcolor="rgba(255,255,255,0.92)", bordercolor=C["border"], borderwidth=0.5, borderpad=3,
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 90,
        margin=dict(l=54, r=24, t=42, b=34),
        title=dict(text="Efficiency gap: the funnel got thirstier", font=dict(size=13), x=0, xanchor="left"),
        funnelmode="group",
        xaxis=dict(showgrid=True, gridcolor=C["grid"], tickformat=".2s", title="Count"),
        yaxis=dict(showgrid=False),
        legend=dict(orientation="h", x=0, y=1.01, xanchor="left", yanchor="bottom"),
    ))
    return fig


# Chapter 4 overrides (last definition wins)
def fig_ch4_refi_mirage(df_pr: pd.DataFrame, df_ho: pd.DataFrame) -> go.Figure:
    """Slide 1: stacked purchase/refi area + bold homeownership floor line."""
    fig = go.Figure()
    if df_pr is None or df_pr.empty:
        return fig

    d = df_pr.copy().sort_values("year")
    ho = df_ho[["year", "homeownership_rate"]].copy() if df_ho is not None and not df_ho.empty else pd.DataFrame(columns=["year", "homeownership_rate"])
    m = d.merge(ho, on="year", how="left")

    fig.add_trace(go.Scatter(
        x=m["year"], y=m["purchase"],
        mode="lines", name="Purchase",
        stackgroup="one", fill="tozeroy",
        line=dict(color=C["purchase"], width=2.4, shape="spline", smoothing=0.65),
        hovertemplate="Purchase: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=m["year"], y=m["refinance"],
        mode="lines", name="Refinance",
        stackgroup="one", fill="tonexty",
        line=dict(color=C["crash"], width=2.4, shape="spline", smoothing=0.65),
        hovertemplate="Refinance: %{y:,.0f}<extra></extra>",
    ))

    if "homeownership_rate" in m.columns and m["homeownership_rate"].notna().any():
        fig.add_trace(go.Scatter(
            x=m["year"], y=m["homeownership_rate"],
            mode="lines+markers", name="Homeownership rate",
            yaxis="y2",
            line=dict(color="#111111", width=4.2),
            marker=dict(size=5, color="#111111"),
            hovertemplate="Homeownership: %{y:.1f}%<extra></extra>",
        ))

    # Big 2012 callout bubble
    c2012 = m[m["year"] == 2012]
    if not c2012.empty:
        row = c2012.iloc[0]
        total = float(row["purchase"] + row["refinance"])
        refi_share = (float(row["refinance"]) / total) if total else 0.0
        txt = f"2012 Peak: 72% Refinance Share<br>Volume hit 8.1M - but new purchase entry stayed limited"
        fig.add_annotation(
            x=2012, y=float(row["refinance"] + row["purchase"]) * 0.88,
            text=txt,
            showarrow=True, arrowhead=2, arrowwidth=1.4, ax=120, ay=-50,
            font=dict(size=11, color=C["crash"]),
            bgcolor="rgba(255,255,255,0.97)", bordercolor=C["crash"], borderwidth=1.2, borderpad=6,
        )

    # Decoupling annotation: volume recovered but homeownership kept falling
    if "homeownership_rate" in m.columns and m["homeownership_rate"].notna().any():
        ho_2012 = m.loc[m["year"] == 2012, "homeownership_rate"]
        ho_2017 = m.loc[m["year"] == 2017, "homeownership_rate"]
        if not ho_2012.empty and not ho_2017.empty:
            fig.add_annotation(
                x=2014.5, y=float(ho_2017.iloc[0]),
                xref="x", yref="y2",
                text="Homeownership fell 4.2pp<br>as volume recovered - decoupling",
                showarrow=True, arrowhead=2, arrowwidth=1.2, ax=0, ay=-50,
                font=dict(size=10, color="#111111"),
                bgcolor="rgba(255,255,255,0.95)", bordercolor="#111111", borderwidth=0.8, borderpad=5,
            )

    fig.update_layout(**_base_layout(
        height=H,
        margin=dict(l=54, r=64, t=52, b=48),
        title=dict(text="The Refi Mirage: Volume Recovered, Homeownership Stalled", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], title="Year (2007-2017)"),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, tickformat=".2s", title="Loan Volume (Millions)"),
        yaxis2=dict(
            overlaying="y", side="right", showgrid=False, zeroline=False,
            tickformat=".1f", title="Homeownership Rate (%)",
            range=[60, 72],
        ),
        legend=dict(orientation="h", x=0, y=1.02, xanchor="left", yanchor="bottom"),
    ))
    return fig


def fig_ch4_yield_attrition(df_col: pd.DataFrame, y0: int = 2007, y1: int = 2017) -> go.Figure:
    """Slide 2: side-by-side funnels and vanishing-market annotation."""
    fig = make_subplots(
        rows=1,
        cols=2,
        specs=[[{"type": "funnel"}, {"type": "funnel"}]],
        subplot_titles=(f"{y0} baseline", f"{y1} recovery year"),
        horizontal_spacing=0.12,
    )
    if df_col is None or df_col.empty:
        return fig

    d0 = df_col[df_col["year"] == y0]
    d1 = df_col[df_col["year"] == y1]
    if d0.empty or d1.empty:
        return fig

    a0, o0 = float(d0["applications"].iloc[0]), float(d0["originations"].iloc[0])
    a1, o1 = float(d1["applications"].iloc[0]), float(d1["originations"].iloc[0])
    yld0 = (o0 / a0) if a0 else 0.0
    yld1 = (o1 / a1) if a1 else 0.0
    vol_drop = o0 - o1

    fig.add_trace(go.Funnel(
        name=f"{y0}",
        y=["Applications", "Originations"],
        x=[a0, o0],
        textinfo="value+percent initial",
        marker=dict(color=["rgba(110,110,110,0.62)", "rgba(44,122,90,0.78)"]),
        hovertemplate=f"{y0} - %{{y}}: %{{x:,.0f}}<extra></extra>",
        showlegend=False,
    ), row=1, col=1)
    fig.add_trace(go.Funnel(
        name=f"{y1}",
        y=["Applications", "Originations"],
        x=[a1, o1],
        textinfo="value+percent initial",
        marker=dict(color=["rgba(160,160,160,0.40)", "rgba(215,38,30,0.80)"]),
        hovertemplate=f"{y1} - %{{y}}: %{{x:,.0f}}<extra></extra>",
        showlegend=False,
    ), row=1, col=2)
    fig.add_annotation(
        x=0.50, y=1.12, xref="paper", yref="paper",
        text=f"Conversion rate improved: {y0} {yld0:.0%}  →  {y1} {yld1:.0%}",
        showarrow=False, font=dict(size=10, color=C["text"]),
        bgcolor="rgba(255,255,255,0.95)", bordercolor=C["border"], borderwidth=0.5, borderpad=3,
    )
    fig.add_annotation(
        x=0.50, y=0.06, xref="paper", yref="paper",
        text=f"Originations down {vol_drop:,.0f} vs {y0} — the funnel got smaller even as conversion improved",
        showarrow=False, font=dict(size=10, color=C["crash"]),
        bgcolor="rgba(255,255,255,0.95)", bordercolor=C["crash"], borderwidth=0.8, borderpad=5,
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 110,
        margin=dict(l=54, r=24, t=62, b=48),
        title=dict(text="The Vanishing Market: Efficiency Rising, Access Falling", font=dict(size=13), x=0, xanchor="left"),
        funnelmode="stack",
        xaxis=dict(showgrid=False),
        xaxis2=dict(showgrid=False),
        yaxis=dict(showgrid=False),
        yaxis2=dict(showgrid=False),
        legend=dict(orientation="h", x=0, y=1.02, xanchor="left", yanchor="bottom"),
    ))
    return fig


def fig_ch4_lti_income_groups(df: pd.DataFrame) -> go.Figure:
    """Slide 3: middle-income emphasis with safety ceiling crossing."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.dropna(subset=["year", "income_band", "lti_ratio"]).copy()
    if d.empty:
        return fig

    d["group"] = d["income_band"].map({
        "<50K": "Low income (<50K)",
        "50-80K": "Middle income (50-100K)",
        "80-100K": "Middle income (50-100K)",
        "100-150K": "Higher income (100K+)",
        "150K+": "Higher income (100K+)",
    })
    d = d.dropna(subset=["group"])
    g = d.groupby(["year", "group"], as_index=False)["lti_ratio"].median().rename(columns={"lti_ratio": "median_lti"})

    series = {
        "Low income (<50K)": {"color": "#9A9A9A", "w": 1.8},
        "Higher income (100K+)": {"color": "#7E7E7E", "w": 1.8},
        "Middle income (50-100K)": {"color": C["warning"], "w": 3.6},
    }
    for name, st in series.items():
        s = g[g["group"] == name].sort_values("year")
        if s.empty:
            continue
        fig.add_trace(go.Scatter(
            x=s["year"], y=s["median_lti"],
            mode="lines+markers",
            name=name,
            line=dict(color=st["color"], width=st["w"], shape="spline", smoothing=0.65),
            marker=dict(size=5),
            hovertemplate=f"{name}<br>%{{x}}: %{{y:.2f}}x<extra></extra>",
        ))

    fig.add_hline(y=3.0, line=dict(color=C["crash"], width=2.4, dash="dash"))
    x_mid = float(g["year"].median()) if not g.empty else 2012
    fig.add_annotation(
        x=x_mid, y=3.0,
        text="<b>Safety Ceiling (LTI = 3.0×)</b>",
        showarrow=False,
        yshift=10,
        font=dict(size=11, color=C["crash"]),
        bgcolor="rgba(255,255,255,0.92)", bordercolor=C["crash"], borderwidth=0.8, borderpad=3,
    )

    mid = g[g["group"] == "Middle income (50-100K)"].sort_values("year")
    cross = mid[mid["median_lti"] >= 3.0]
    if not cross.empty:
        c = cross.iloc[0]
        fig.add_annotation(
            x=float(c["year"]), y=float(c["median_lti"]),
            text=f"Middle-income crosses ceiling ({int(c['year'])})",
            showarrow=True, arrowhead=2, ax=40, ay=-35,
            font=dict(size=10, color=C["warning"]),
            bgcolor="rgba(255,255,255,0.95)", bordercolor=C["warning"], borderwidth=0.7, borderpad=3,
        )

    latest_year = int(g["year"].max())
    latest = g[g["year"] == latest_year].copy()
    trough_year = int(mid.loc[mid["median_lti"].idxmin(), "year"]) if not mid.empty else latest_year
    trough_val = float(mid["median_lti"].min()) if not mid.empty else float("nan")
    if not latest.empty:
        latest_mid = latest[latest["group"] == "Middle income (50-100K)"]
        others = latest[latest["group"] != "Middle income (50-100K)"]
        if not latest_mid.empty and not others.empty:
            mid_v = float(latest_mid["median_lti"].iloc[0])
            rise = (mid_v - trough_val) if trough_val == trough_val else 0.0
            fig.add_annotation(
                x=latest_year, y=mid_v,
                text=f"Middle-income: +{rise:.2f}x since {trough_year} trough<br>Fastest-rising group — converging on 3.0× ceiling",
                showarrow=True, arrowhead=2, ax=-210, ay=-40,
                font=dict(size=10, color=C["warning"]),
                bgcolor="rgba(255,255,255,0.95)", bordercolor=C["warning"], borderwidth=0.9, borderpad=4,
            )

    # Delta since 2012 callouts (velocity signal)
    base_year = 2012
    deltas = []
    for grp in ["Low income (<50K)", "Middle income (50-100K)", "Higher income (100K+)"]:
        s = g[g["group"] == grp].sort_values("year")
        b = s[s["year"] == base_year]["median_lti"]
        l = s[s["year"] == latest_year]["median_lti"]
        if len(b) and len(l):
            deltas.append((grp, float(l.iloc[0] - b.iloc[0]), float(l.iloc[0])))
    if deltas:
        # Put middle-income first in annotation text
        order = {"Middle income (50-100K)": 0, "Higher income (100K+)": 1, "Low income (<50K)": 2}
        deltas = sorted(deltas, key=lambda t: order.get(t[0], 9))
        delta_txt = " | ".join([f"{gname.split(' ')[0]} Δ since 2012: {dv:+.2f}x" for gname, dv, _ in deltas])
        fig.add_annotation(
            x=0.02, y=0.98, xref="paper", yref="paper",
            text=delta_txt,
            showarrow=False, xanchor="left", yanchor="top",
            font=dict(size=9, color=C["muted"]),
            bgcolor="rgba(255,255,255,0.92)", bordercolor=C["border"], borderwidth=0.5, borderpad=3,
        )

    fig.update_layout(**_base_layout(
        height=H_SM + 100,
        margin=dict(l=54, r=24, t=52, b=48),
        title=dict(text="The Squeezed Middle: Leverage Accelerating Toward the Ceiling", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], title="Year (2007-2017)"),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, title="Median Loan-to-Income Ratio (×)", range=[1.5, 3.5]),
        legend=dict(orientation="h", x=0, y=1.02, xanchor="left", yanchor="bottom"),
    ))
    return fig


# Chapter 5 polish overrides (last definition wins)
def fig_recovery_map_discrete(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.copy()
    d["category_code"] = d["rvs_years"].apply(lambda v: 0 if v <= 2 else (1 if v <= 4 else 2))
    d["category_label"] = d["rvs_years"].apply(
        lambda v: "Fast (≤2 years)" if v <= 2 else ("Medium (3–4 years)" if v <= 4 else "Slow (5+ years)")
    )
    has_lti = "median_lti_2017" in d.columns
    if has_lti:
        d["lti_vs_2007_baseline"] = d["median_lti_2017"] - 3.0

    custom_cols = ["rvs_years", "category_label"] + (["median_lti_2017", "lti_vs_2007_baseline"] if has_lti else [])
    hover = (
        "<b>%{location}</b><br>"
        "Recovery time: %{customdata[0]} years<br>"
        "Category: %{customdata[1]}<br>"
    )
    if has_lti:
        hover += "Median LTI (2017): %{customdata[2]:.2f}×<br>vs 3.0× baseline: %{customdata[3]:+.2f}×"
    hover += "<extra></extra>"

    fig.add_trace(go.Choropleth(
        locations=d["state"],
        z=d["category_code"],
        locationmode="USA-states",
        colorscale=[
            [0.0,    "#2E8B57"], [0.3333, "#2E8B57"],   # Fast — green
            [0.3334, "#D9A441"], [0.6666, "#D9A441"],   # Medium — amber
            [0.6667, "#C23B31"], [1.0,    "#C23B31"],   # Slow — red
        ],
        zmin=0, zmax=2,
        marker_line_color="#FFFFFF",
        marker_line_width=0.8,
        colorbar=dict(
            title=dict(text="Recovery Speed", font=dict(size=10)),
            tickmode="array",
            tickvals=[0, 1, 2],
            ticktext=["Fast (≤2 yrs)", "Medium (3–4 yrs)", "Slow (5+ yrs)"],
            thickness=12,
            len=0.52,
            x=1.01,
            y=0.5,
        ),
        customdata=d[custom_cols],
        hovertemplate=hover,
    ))

    fig.update_geos(
        scope="usa",
        bgcolor=C["bg"],
        showlakes=False,
        showland=True,
        landcolor="#F2F0EC",   # faint off-white — "no data" states nearly invisible
        showcoastlines=False,
        showframe=False,
    )

    # Sun-Belt Sprint callout
    fig.add_annotation(
        x=0.35, y=0.10, xref="paper", yref="paper",
        text="Sun-Belt Sprint: Oil-state & Sun-Belt markets<br>bounced back in just 1–2 years",
        showarrow=False, xanchor="center",
        font=dict(size=9, color="#2E8B57"),
        bgcolor="rgba(255,255,255,0.93)", bordercolor="#2E8B57", borderwidth=0.7, borderpad=4,
    )

    # Florida L-shaped lag
    if (d["state"] == "FL").any():
        fig.add_annotation(
            x=0.80, y=0.22, xref="paper", yref="paper",
            text="<b>Florida:</b> L-shaped lag —<br>stalled by foreclosure backlogs",
            showarrow=True, arrowhead=2, arrowwidth=1.2, ax=55, ay=18,
            font=dict(size=9, color=C["crash"]),
            bgcolor="rgba(255,255,255,0.93)", bordercolor=C["crash"], borderwidth=0.7, borderpad=4,
        )

    fig.update_layout(
        height=390,
        margin=dict(l=10, r=80, t=52, b=28),
        paper_bgcolor=C["bg"],
        uirevision="keep",
        transition=dict(duration=280, easing="cubic-in-out"),
        font=dict(family=FONT, size=11),
        geo=dict(bgcolor=C["bg"]),
        title=dict(
            text="Geography of Resilience: The Velocity of Survival",
            font=dict(size=13),
            x=0.02, xanchor="left", y=0.98, yanchor="top",
        ),
    )
    return fig


def fig_bank_nonbank_slope(df: pd.DataFrame) -> go.Figure:
    bank    = df[df["lender_type"] == "Bank"].sort_values("year")
    nonbank = df[df["lender_type"] == "Nonbank"].sort_values("year")
    fig = go.Figure()

    # Banks — thinner, muted
    fig.add_trace(go.Scatter(
        x=bank["year"], y=bank["share"], name="Banks",
        mode="lines+markers",
        line=dict(color="#23364D", width=2.4),
        marker=dict(size=6),
        hovertemplate="Banks %{x}: %{y:.1%}<extra></extra>",
    ))
    # Nonbanks — thicker, vibrant (the new winners)
    fig.add_trace(go.Scatter(
        x=nonbank["year"], y=nonbank["share"], name="Nonbanks",
        mode="lines+markers",
        line=dict(color="#E07B1A", width=4.8),
        marker=dict(size=7, color="#E07B1A"),
        hovertemplate="Nonbanks %{x}: %{y:.1%}<extra></extra>",
    ))

    # Endpoint stat labels: "70%" at 2007, "31%" at 2017 for banks
    if not bank.empty:
        b_start = bank.iloc[0]; b_end = bank.iloc[-1]
        for row, lbl, ax_ in [(b_start, f"{float(b_start['share']):.0%}", -28), (b_end, f"{float(b_end['share']):.0%}", 28)]:
            fig.add_annotation(
                x=float(row["year"]), y=float(row["share"]),
                text=f"<b>{lbl}</b>", showarrow=False,
                font=dict(size=10, color="#23364D"), yshift=14,
            )
    if not nonbank.empty:
        n_start = nonbank.iloc[0]; n_end = nonbank.iloc[-1]
        for row in [n_start, n_end]:
            fig.add_annotation(
                x=float(row["year"]), y=float(row["share"]),
                text=f"<b>{float(row['share']):.0%}</b>", showarrow=False,
                font=dict(size=10, color="#E07B1A"), yshift=-18,
            )

    # 2013–2014 crossover line
    cross_year = None
    for i in range(len(bank) - 1):
        b0 = float(bank["share"].iloc[i]); b1 = float(bank["share"].iloc[i + 1])
        n0 = float(nonbank["share"].iloc[i]); n1 = float(nonbank["share"].iloc[i + 1])
        if (b0 > n0) != (b1 > n1):
            cross_year = int(bank["year"].iloc[i]); break
    if cross_year:
        fig.add_shape(
            type="line", x0=cross_year + 0.5, x1=cross_year + 0.5,
            y0=0.0, y1=1.0, xref="x", yref="paper",
            line=dict(color=C["crash"], width=1.6, dash="dash"),
        )
        fig.add_annotation(
            x=cross_year + 0.6, y=0.55,
            text=f"<b>2013–2014 Crossover</b><br>Banks lost majority share",
            showarrow=False, font=dict(size=10, color=C["crash"]), xanchor="left",
            bgcolor="rgba(255,255,255,0.92)", bordercolor=C["crash"], borderwidth=0.7, borderpad=4,
        )

    # Regulatory retreat: Basel III / Dodd-Frank 2010-2012
    fig.add_shape(
        type="rect", x0=2010, x1=2012,
        y0=0.0, y1=1.0, xref="x", yref="paper",
        fillcolor="rgba(35,54,77,0.07)", line=dict(width=0),
    )
    fig.add_annotation(
        x=2011, y=0.75,
        text="Basel III /<br>Dodd-Frank<br>Impact",
        showarrow=False, font=dict(size=9, color="#23364D"),
        bgcolor="rgba(255,255,255,0.88)", bordercolor="#23364D", borderwidth=0.5, borderpad=3,
    )

    # Stat callout
    fig.add_annotation(
        x=0.01, y=0.04, xref="paper", yref="paper",
        text="Banks: 70% → 31% of originations (2007–2017)",
        showarrow=False, xanchor="left",
        font=dict(size=10, color="#23364D"),
        bgcolor="rgba(255,255,255,0.92)", bordercolor="#23364D", borderwidth=0.6, borderpad=4,
    )

    # Footer — systemic risk note
    fig.add_annotation(
        x=0.01, y=-0.14, xref="paper", yref="paper",
        text="Note: Nonbanks operate without deposit insurance or Federal Reserve access — increasing systemic fragility",
        showarrow=False, xanchor="left",
        font=dict(size=9, color=C["muted"]),
    )

    fig.update_layout(**_base_layout(
        height=H + 30,
        margin=dict(l=54, r=48, t=52, b=64),
        title=dict(text="The Great Handover: Banks Exit, Nonbanks Enter", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], title="Year (2007-2017)"),
        yaxis=dict(gridcolor=C["grid"], zeroline=False, tickformat=".0%", title="Share of Originations (%)", range=[0.15, 0.90]),
        legend=dict(orientation="h", x=0, y=1.02, xanchor="left", yanchor="bottom"),
    ))
    return fig


def fig_recovery_vs_affordability(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    # Sort by LTI descending so highest-LTI state is at top
    d = df.copy().sort_values("median_lti_2017", ascending=True)

    # Color matches the map: Green=Fast, Amber=Medium, Red=Slow
    FAST_COLOR   = "#2E8B57"
    MEDIUM_COLOR = "#D9A441"
    SLOW_COLOR   = "#C23B31"
    colors = [FAST_COLOR if r <= 2 else (MEDIUM_COLOR if r <= 4 else SLOW_COLOR) for r in d["rvs_years"]]

    # Recovery speed label for hover
    speed_labels = ["Fast (≤2y)" if r <= 2 else ("Medium (3–4y)" if r <= 4 else "Slow (5+y)") for r in d["rvs_years"]]
    d = d.copy()
    d["speed_label"] = speed_labels

    fig.add_trace(go.Bar(
        x=d["median_lti_2017"],
        y=d["state"],
        orientation="h",
        marker_color=colors,
        marker_line_width=0,
        text=[f"{v:.2f}×" for v in d["median_lti_2017"]],
        textposition="outside",
        textfont=dict(size=10),
        customdata=list(zip(d["rvs_years"], d["speed_label"])),
        hovertemplate="<b>%{y}</b><br>Median LTI (2017): %{x:.2f}×<br>Recovery: %{customdata[0]} years (%{customdata[1]})<extra></extra>",
    ))

    # 3.0× affordability ceiling
    fig.add_vline(
        x=3.0,
        line=dict(color=C["crash"], width=2.0, dash="dash"),
    )
    fig.add_annotation(
        x=3.0, y=1.0, xref="x", yref="paper",
        text="<b>3.0× Affordability Threshold</b>",
        showarrow=False, xanchor="left", yanchor="top",
        font=dict(size=9, color=C["crash"]),
        bgcolor="rgba(255,255,255,0.90)", bordercolor=C["crash"], borderwidth=0.6, borderpad=3,
        xshift=4,
    )

    # Highlight CA, CO, TX as fast-recoverers above 3×
    fast_above = d[(d["rvs_years"] <= 2) & (d["median_lti_2017"] >= 3.0)]
    if not fast_above.empty:
        states_str = ", ".join(sorted(fast_above["state"].tolist()))
        fig.add_annotation(
            x=0.98, y=0.04, xref="paper", yref="paper",
            text=f"Fastest recoveries ({states_str}) all ended above 3.0×<br>Recovery and affordability moved in opposite directions",
            showarrow=False, xanchor="right",
            font=dict(size=9, color=FAST_COLOR),
            bgcolor="rgba(255,255,255,0.93)", bordercolor=FAST_COLOR, borderwidth=0.7, borderpad=4,
        )

    # Manual legend (matches map)
    for label, color, x_pos in [("Fast (≤2y)", FAST_COLOR, 0.01), ("Medium (3–4y)", MEDIUM_COLOR, 0.18), ("Slow (5+y)", SLOW_COLOR, 0.34)]:
        fig.add_annotation(
            x=x_pos, y=1.06, xref="paper", yref="paper",
            text=f"<span style='color:{color}'>■</span> {label}",
            showarrow=False, xanchor="left",
            font=dict(size=10),
        )

    n_states = len(d)
    bar_height = max(H, 60 + n_states * 30)

    fig.update_layout(**_base_layout(
        height=bar_height,
        margin=dict(l=54, r=72, t=60, b=52),
        title=dict(text="The Recovery Trap: Fast Recovery, Unaffordable Outcome", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(
            showgrid=True, gridcolor=C["grid"], zeroline=False,
            title="Median Loan-to-Income (LTI) Ratio (2017)",
            tickcolor=C["border"],
            range=[0, d["median_lti_2017"].max() * 1.18],
        ),
        yaxis=dict(
            showgrid=False, zeroline=False,
            title="State (Ranked by LTI)",
            tickfont=dict(size=11),
        ),
        showlegend=False,
    ))
    return fig


def fig_ch5_recovery_drivers(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df is None or df.empty:
        return fig
    need = {"state", "recovery_years", "employment_recovery_pct", "nonbank_accel_pp", "price_recovery_lag_years"}
    if not need.issubset(set(df.columns)):
        return fig
    d = df.dropna(subset=["recovery_years", "employment_recovery_pct"]).copy()
    if d.empty:
        return fig
    d["state"] = d["state"].astype(str).str.upper().replace({"MCO": "MO"})
    x_min = float(d["employment_recovery_pct"].min())
    x_max = float(d["employment_recovery_pct"].max())
    y_min = float(d["recovery_years"].min())
    y_max = float(d["recovery_years"].max())
    x_pad = max(0.25, (x_max - x_min) * 0.08)
    y_pad = max(0.25, (y_max - y_min) * 0.08)
    x_lo, x_hi = x_min - x_pad, x_max + x_pad
    y_lo, y_hi = y_min - y_pad, y_max + y_pad
    # Use midpoints so the four quadrants occupy equal chart area.
    x_med = (x_lo + x_hi) / 2.0
    y_med = (y_lo + y_hi) / 2.0
    c = d["recovery_years"].astype(float)
    cmin = float(c.min())
    cmax = float(c.max())
    cspan = cmax - cmin if cmax > cmin else 1.0
    c_norm = (c - cmin) / cspan
    custom = (
        d[["nonbank_accel_pp", "price_recovery_lag_years"]]
        .fillna(0.0)
        .astype(float)
        .to_numpy()
    )
    fig.add_trace(go.Scatter(
        x=d["employment_recovery_pct"],
        y=d["recovery_years"],
        mode="markers",
        text=d["state"],
        marker=dict(
            size=14,
            color=c_norm,
            colorscale=[[0.0, "#2C7A5A"], [0.5, "#F59E0B"], [1.0, "#D7261E"]],
            line=dict(color="rgba(17,17,17,0.45)", width=0.8),
            opacity=0.88,
            showscale=False,
        ),
        customdata=custom,
        hovertemplate="<b>%{text}</b><br>Employment recovery: %{x:.1f}%<br>Recovery years: %{y:.0f}<br>Nonbank acceleration: %{customdata[0]:+.1f} pp<br>Price recovery lag: %{customdata[1]:.1f} years<extra></extra>",
    ))
    fig.add_vline(x=x_med, line=dict(color="rgba(26,26,26,0.40)", width=1.2, dash="dash"))
    fig.add_hline(y=y_med, line=dict(color="rgba(26,26,26,0.40)", width=1.2, dash="dash"))
    # Label states with small vertical offsets where points overlap.
    d_plot = d.assign(
        x_round=d["employment_recovery_pct"].round(1),
        y_round=d["recovery_years"].round(1),
    )
    for (_, _), g in d_plot.groupby(["x_round", "y_round"], sort=False):
        shifts = [14, -14, 24, -24, 32, -32]
        for i, row in enumerate(g.itertuples(index=False)):
            base_shift = -14 if float(row.recovery_years) <= y_med else 12
            yshift = base_shift + shifts[i % len(shifts)]
            fig.add_annotation(
                x=row.employment_recovery_pct,
                y=row.recovery_years,
                text=str(row.state),
                showarrow=False,
                yshift=yshift,
                font=dict(size=12, color=C["text"]),
            )
    fig.add_annotation(
        x=0.78, y=0.88, xref="paper", yref="paper",
        text="Demand-led recovery",
        showarrow=False, font=dict(size=12, color=C["recovery"]),
    )
    fig.add_annotation(
        x=0.80, y=0.12, xref="paper", yref="paper",
        text="Friction-dominated (backlogs)",
        showarrow=False, font=dict(size=12, color=C["crash"]),
    )
    fig.add_annotation(
        x=0.12, y=0.86, xref="paper", yref="paper",
        text="Credit-driven recovery",
        showarrow=False, font=dict(size=12, color="#B54708"),
    )
    fig.add_annotation(
        x=0.01, y=1.04, xref="paper", yref="paper",
        text="Top = faster recovery",
        showarrow=False, xanchor="left", yanchor="top",
        font=dict(size=11, color=C["muted"]),
    )
    for st, label, ax, ay in [("FL", "High friction despite demand", 24, -26)]:
        s = d[d["state"] == st]
        if s.empty:
            continue
        r = s.iloc[0]
        fig.add_annotation(
            x=float(r["employment_recovery_pct"]),
            y=float(r["recovery_years"]),
            text=label,
            showarrow=True,
            arrowhead=2,
            arrowwidth=1.0,
            ax=ax,
            ay=ay,
            font=dict(size=10, color=C["text"]),
            bgcolor="rgba(255,255,255,0.92)",
            bordercolor=C["border"],
            borderwidth=0.6,
            borderpad=3,
        )
    fig.update_layout(**_base_layout(
        height=H,
        margin=dict(l=58, r=36, t=40, b=50),
        xaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, range=[x_lo, x_hi], title=dict(text="Employment recovery (% 2009-2013)", font=dict(size=16, color=C["text"])), tickfont=dict(size=16)),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, range=[y_hi, y_lo], title=dict(text="Time to Recover (Years)", font=dict(size=16, color=C["text"])), tickfont=dict(size=16)),
        font=dict(size=16, color=C["text"]),
    ))
    return fig


def fig_ch6_generation_split(df_age: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df_age is None or df_age.empty:
        return fig
    need = {"year", "home_25_34", "home_55_64"}
    if not need.issubset(set(df_age.columns)):
        return fig
    d = df_age.dropna(subset=["year", "home_25_34", "home_55_64"]).copy().sort_values("year")
    if d.empty:
        return fig

    start_year, end_year = 2007, 2017
    s = d[d["year"] == start_year]
    e = d[d["year"] == end_year]
    if s.empty:
        s = d.head(1)
        start_year = int(s["year"].iloc[0])
    if e.empty:
        e = d.tail(1)
        end_year = int(e["year"].iloc[0])
    p0 = s.iloc[0]
    p1 = e.iloc[0]

    young_start = float(p0["home_25_34"])
    young_end = float(p1["home_25_34"])
    older_start = float(p0["home_55_64"])
    older_end = float(p1["home_55_64"])
    g0 = older_start - young_start
    g1 = older_end - young_end

    x0, x1 = 0, 1

    fig.add_trace(go.Scatter(
        x=[x0, x1], y=[older_start, older_end],
        mode="lines+markers",
        name="Age 55-64 (boomer proxy)",
        line=dict(color=C["recovery"], width=3.0),
        marker=dict(size=9, color=C["recovery"]),
        hovertemplate="55-64<br>%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=[x0, x1], y=[young_start, young_end],
        mode="lines+markers",
        name="Age 25-34 (young proxy)",
        line=dict(color=C["crash"], width=3.0),
        marker=dict(size=9, color=C["crash"]),
        hovertemplate="25-34<br>%{x}: %{y:.1f}%<extra></extra>",
    ))

    # Gap markers at start/end years.
    fig.add_shape(type="line", x0=x0, x1=x0, y0=young_start, y1=older_start,
                  line=dict(color="rgba(26,26,26,0.45)", width=1.5, dash="dot"))
    fig.add_shape(type="line", x0=x1, x1=x1, y0=young_end, y1=older_end,
                  line=dict(color="rgba(26,26,26,0.45)", width=1.5, dash="dot"))

    # Endpoint labels
    fig.add_annotation(x=x0, y=older_start, text=f"Older: {older_start:.0f}%",
                       showarrow=False, xshift=38, yshift=10, font=dict(size=11, color=C["recovery"]))
    fig.add_annotation(x=x0, y=young_start, text=f"Young: {young_start:.0f}%",
                       showarrow=False, xshift=38, yshift=-10, font=dict(size=11, color=C["crash"]))
    fig.add_annotation(x=x1, y=older_end, text=f"Older: {older_end:.0f}%",
                       showarrow=False, xshift=-42, yshift=10, font=dict(size=11, color=C["recovery"]))
    fig.add_annotation(x=x1, y=young_end, text=f"Young: {young_end:.0f}%",
                       showarrow=False, xshift=-42, yshift=-10, font=dict(size=11, color=C["crash"]))

    # Gap labels
    fig.add_annotation(x=x0, y=(older_start + young_start) / 2.0, text=f"Gap: {g0:.1f}pp",
                       showarrow=False, xshift=52, font=dict(size=11, color=C["text"]),
                       bgcolor="rgba(255,255,255,0.94)", bordercolor=C["border"], borderwidth=0.6, borderpad=3)
    fig.add_annotation(x=x1, y=(older_end + young_end) / 2.0, text=f"Gap: {g1:.1f}pp",
                       showarrow=False, xshift=-56, font=dict(size=11, color=C["text"]),
                       bgcolor="rgba(255,255,255,0.94)", bordercolor=C["border"], borderwidth=0.6, borderpad=3)

    fig.update_layout(**_base_layout(
        height=H_SM + 80,
        margin=dict(l=54, r=24, t=36, b=46),
        xaxis=dict(type="linear", range=[-0.15, 1.15], tickmode="array", tickvals=[0, 1], ticktext=[str(start_year), str(end_year)], showgrid=False, zeroline=False, tickcolor=C["border"], tickfont=dict(size=16), title=dict(text="Before vs After", font=dict(size=16, color=C["text"]))),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, range=[34, 86], title=dict(text="Homeownership rate (%)", font=dict(size=16, color=C["text"])), tickfont=dict(size=16)),
        showlegend=False,
        font=dict(size=16, color=C["text"]),
    ))
    return fig


def fig_ch6_cost_access(df_pr: pd.DataFrame, df_mr: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df_pr is None or df_pr.empty:
        return fig
    need = {"year", "purchase", "refinance"}
    if not need.issubset(set(df_pr.columns)):
        return fig
    d = df_pr.copy().sort_values("year")
    mr = df_mr.copy().sort_values("year") if df_mr is not None and not df_mr.empty else pd.DataFrame(columns=["year", "mortgage_rate_30y"])
    m = d.merge(mr[["year", "mortgage_rate_30y"]] if "mortgage_rate_30y" in mr.columns else mr, on="year", how="left")
    if m.empty or "year" not in m.columns:
        return fig

    m = m.dropna(subset=["year"]).copy()
    m["year"] = m["year"].astype(int)
    base_row = m[m["year"] == 2007]
    if base_row.empty:
        base_row = m.head(1)
    base_rate = float(base_row["mortgage_rate_30y"].iloc[0]) if "mortgage_rate_30y" in base_row.columns else np.nan
    base_refi = float(base_row["refinance"].iloc[0])
    base_purch = float(base_row["purchase"].iloc[0])
    base_rate = base_rate if pd.notna(base_rate) and base_rate > 0 else float(m["mortgage_rate_30y"].dropna().iloc[0]) if "mortgage_rate_30y" in m.columns and len(m["mortgage_rate_30y"].dropna()) else 1.0
    base_refi = base_refi if base_refi > 0 else 1e-6
    base_purch = base_purch if base_purch > 0 else 1e-6

    m["cost_idx"] = (m["mortgage_rate_30y"] / base_rate) * 100.0
    m["refi_idx"] = (m["refinance"] / base_refi) * 100.0
    m["purchase_idx"] = (m["purchase"] / base_purch) * 100.0

    # Fill only positive refi-over-purchase spread to visualize the opportunity gap.
    m["gap_idx"] = m["refi_idx"] - m["purchase_idx"]
    m["opportunity_top"] = m["purchase_idx"] + m["gap_idx"].clip(lower=0.0)
    fig.add_trace(go.Scatter(
        x=m["year"], y=m["purchase_idx"],
        mode="lines",
        line=dict(width=0),
        hoverinfo="skip",
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=m["year"], y=m["opportunity_top"],
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(230, 90, 50, 0.16)",
        hoverinfo="skip",
        showlegend=False,
    ))

    fig.add_trace(go.Scatter(
        x=m["year"], y=m["cost_idx"],
        mode="lines+markers", name="Cost of borrowing",
        line=dict(color="#B54708", width=2.8, shape="spline", smoothing=0.65),
        marker=dict(size=5, color="#B54708"),
        hovertemplate="Cost of borrowing (index)<br>%{x}: %{y:.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=m["year"], y=m["refi_idx"],
        mode="lines+markers", name="Existing owners (refi volume)",
        line=dict(color=C["crash"], width=2.6, shape="spline", smoothing=0.65),
        marker=dict(size=5, color=C["crash"]),
        hovertemplate="Existing owners (refi volume index)<br>%{x}: %{y:.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=m["year"], y=m["purchase_idx"],
        mode="lines+markers", name="New buyers (purchase volume)",
        line=dict(color=C["govt"], width=2.6, shape="spline", smoothing=0.65),
        marker=dict(size=5, color=C["govt"]),
        hovertemplate="New buyers (purchase volume index)<br>%{x}: %{y:.0f}<extra></extra>",
    ))

    # Decoupling point = max refi-over-purchase spread.
    dec_row = m.loc[m["gap_idx"].idxmax()]
    dec_year = float(dec_row["year"])
    dec_refi = float(dec_row["refi_idx"])
    dec_purchase = float(dec_row["purchase_idx"])
    dec_gap = float(dec_row["gap_idx"])
    dec_mid = (dec_refi + dec_purchase) / 2.0

    fig.add_trace(go.Scatter(
        x=[dec_year], y=[dec_refi],
        mode="markers",
        marker=dict(size=9, color="#111111"),
        showlegend=False,
        hovertemplate="Decoupling point<br>%{x}: %{y:.0f}<extra></extra>",
    ))
    fig.add_shape(
        type="line",
        x0=dec_year, x1=dec_year,
        y0=dec_purchase, y1=dec_refi,
        line=dict(color="#111111", width=1.6, dash="dot"),
    )
    fig.add_annotation(
        x=dec_year, y=dec_mid,
        text=f"Decoupling point: {int(dec_year)}<br>Refi-Purchase gap = +{dec_gap:.1f}",
        showarrow=True, arrowhead=2, arrowwidth=1.0, ax=30, ay=-28,
        font=dict(size=10, color="#111111"),
    )
    fig.add_annotation(
        x=dec_year + 0.2, y=dec_mid + 10.0,
        text="Opportunity Gap",
        showarrow=False,
        font=dict(size=11, color="#B54708"),
    )
    fig.add_annotation(
        x=dec_year, y=dec_refi,
        text=f"Refinancing spike ({dec_refi:.0f})",
        showarrow=True, arrowhead=2, arrowwidth=1.0, ax=36, ay=-48,
        font=dict(size=10, color=C["crash"]),
    )

    if not m.empty:
        e = m.iloc[-1]
        fig.add_annotation(x=float(e["year"]), y=float(e["cost_idx"]), text=f"Cost of borrowing ({e['cost_idx']:.0f})", showarrow=False, xanchor="left", yshift=10, font=dict(size=11, color="#B54708"))
        fig.add_annotation(x=float(e["year"]), y=float(e["refi_idx"]), text=f"Refi volume ({e['refi_idx']:.0f})", showarrow=False, xanchor="left", yshift=-2, font=dict(size=11, color=C["crash"]))
        fig.add_annotation(x=float(e["year"]), y=float(e["purchase_idx"]), text=f"Purchase volume ({e['purchase_idx']:.0f})", showarrow=False, xanchor="left", yshift=-12, font=dict(size=11, color=C["govt"]))

    fig.add_hline(
        y=100, line=dict(color="#111111", width=2.2, dash="solid"),
        annotation_text="2007 baseline = 100", annotation_position="top left",
        annotation_font=dict(size=10, color="#111111"),
    )
    fig.update_layout(**_base_layout(
        height=H,
        margin=dict(l=54, r=150, t=34, b=46),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], tickfont=dict(size=16)),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, title=dict(text="Index (2007=100)", font=dict(size=16, color=C["text"])), tickfont=dict(size=16)),
        legend=dict(x=0.01, y=0.99, xanchor="left", yanchor="top", orientation="h"),
        font=dict(size=16, color=C["text"]),
    ))
    return fig


def fig_ch6_entry_gap(df_pr: pd.DataFrame, df_col: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if df_pr is None or df_pr.empty or df_col is None or df_col.empty or "purchase_pct" not in df_pr.columns:
        return fig
    pr = df_pr.copy().sort_values("year")
    col = df_col.copy().sort_values("year")
    m = pr[["year", "purchase_pct"]].merge(col[["year", "applications"]], on="year", how="inner").sort_values("year")
    if m.empty:
        return fig
    base = float(m.loc[m["year"] == 2007, "applications"].iloc[0]) if len(m[m["year"] == 2007]) else float(m["applications"].iloc[0])
    m["applications_idx"] = (m["applications"] / base) * 100.0 if base else 100.0
    fig.add_trace(go.Bar(
        x=m["year"], y=m["applications_idx"],
        name="Applications index",
        marker_color="rgba(40,92,154,0.28)",
        marker_line=dict(color=C["govt"], width=0.8),
        hovertemplate="Applications index<br>%{x}: %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=m["year"], y=m["purchase_pct"] * 100.0,
        mode="lines+markers", name="Purchase share",
        line=dict(color=C["recovery"], width=2.6, shape="spline", smoothing=0.65),
        marker=dict(size=5),
        yaxis="y2",
        hovertemplate="Purchase share<br>%{x}: %{y:.1f}%<extra></extra>",
    ))
    fig.add_hline(y=100, line=dict(color=C["border"], width=1, dash="dot"))
    fig.update_layout(**_base_layout(
        height=H_SM + 70,
        margin=dict(l=54, r=60, t=34, b=46),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], tickfont=dict(size=16)),
        yaxis=dict(showgrid=True, gridcolor=C["grid"], zeroline=False, title=dict(text="Applications index (2007=100)", font=dict(size=16, color=C["text"])), tickfont=dict(size=16)),
        yaxis2=dict(overlaying="y", side="right", showgrid=False, zeroline=False, title=dict(text="Purchase share (%)", font=dict(size=16, color=C["text"])), range=[0, 100], tickfont=dict(size=16)),
        font=dict(size=16, color=C["text"]),
    ))
    return fig


def fig_ch7_winner_redistribution(df_scores: pd.DataFrame) -> go.Figure:
    """
    Chapter 7 synthesis: one-chart view of who benefited from the post-crisis regime.
    Expects columns:
      - group
      - market_power
      - financing_edge
      - asset_capture
      - regulatory_fit
    """
    fig = go.Figure()
    if df_scores is None or df_scores.empty:
        return fig
    need = {"group", "market_power", "financing_edge", "asset_capture", "regulatory_fit"}
    if not need.issubset(set(df_scores.columns)):
        return fig

    d = df_scores.copy()
    comp_cols = ["market_power", "financing_edge", "asset_capture", "regulatory_fit"]
    # Normalize to a coherent 0-100 composite (each component contributes up to 25).
    for ccol in comp_cols:
        d[ccol] = d[ccol].clip(lower=0, upper=100) / 4.0
    d["total"] = d[comp_cols].sum(axis=1)
    d = d.sort_values("total", ascending=True)

    parts = [
        ("market_power", "Market Power Gain", "#334155"),
        ("financing_edge", "Cost / Financing Advantage", "#B45309"),
        ("asset_capture", "Asset Capture", "#0F766E"),
        ("regulatory_fit", "Regulatory Fit", "#BE123C"),
    ]
    for col, name, color in parts:
        fig.add_trace(go.Bar(
            x=d[col],
            y=d["group"],
            name=name,
            orientation="h",
            marker_color=color,
            marker_line=dict(color="rgba(17,17,17,0.15)", width=0.6),
            hovertemplate=f"{name}<br>%{{y}}: %{{x:.1f}} pts<extra></extra>",
        ))

    for row in d.itertuples(index=False):
        fig.add_annotation(
            x=float(row.total) + 1.5,
            y=row.group,
            text=f"{float(row.total):.1f}",
            showarrow=False,
            xanchor="left",
            font=dict(size=11, color=C["text"]),
        )

    fig.update_layout(**_base_layout(
        height=max(H, 320 + 18 * len(d)),
        margin=dict(l=220, r=40, t=36, b=44),
        barmode="stack",
        xaxis=dict(
            showgrid=True, gridcolor=C["grid"], zeroline=False,
            title=dict(text="Redistribution Advantage Index (0-100 composite)", font=dict(size=16, color=C["text"])),
            range=[0, 100],
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(size=14, color=C["text"]),
        ),
        legend=dict(orientation="h", y=-0.18, x=0.0, xanchor="left"),
        font=dict(size=16, color=C["text"]),
    ))
    fig.add_annotation(
        x=0, y=1.12, xref="paper", yref="paper",
        text="Higher total = larger post-crisis advantage (stacked components sum to 0-100)",
        showarrow=False, xanchor="left",
        font=dict(size=11, color=C["muted"]),
    )
    return fig




