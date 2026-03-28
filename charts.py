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
        fig_credit_desert, fig_homeownership_overlay,
        fig_lender_bubble,
    )
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# ─────────────────────────────────────────────────────────
# DESIGN TOKENS  — single source of truth for all charts
# ─────────────────────────────────────────────────────────
C = {
    "bg":          "rgba(0,0,0,0)",   # transparent — host provides bg
    "grid":        "rgba(0,0,0,0.06)",
    "border":      "rgba(0,0,0,0.12)",
    "text":        "#1A1A18",
    "muted":       "#6B6B67",
    "surface":     "#F8F7F4",

    # Semantic
    "crash":       "#E24B4A",
    "recovery":    "#1D9E75",
    "govt":        "#378ADD",
    "conventional":"#888780",
    "warning":     "#EF9F27",
    "purchase":    "#185FA5",
    "refi":        "#5DCAA5",
    "bank":        "#888780",
    "nonbank":     "#D85A30",
    "veteran":     "#534AB7",
    "fha":         "#378ADD",
    "va":          "#5DCAA5",
    "fsa":         "#9FE1CB",

    # Race palette
    "white":       "#888780",
    "black":       "#E24B4A",
    "hispanic":    "#EF9F27",
    "asian":       "#378ADD",
}

FONT  = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
H     = 380   # default chart height
H_SM  = 240   # small chart height
H_LG  = 440   # large chart height
M     = dict(l=48, r=28, t=36, b=44)    # default margins
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
        font=dict(family=FONT, size=12, color=C["text"]),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=1.02,
            xanchor="left",   x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
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
# CHAPTER 2 — THE COLLAPSE
# ─────────────────────────────────────────────────────────

def fig_collapse(df: pd.DataFrame) -> go.Figure:
    """
    Dual-fill area: Applications (muted) vs Originations (teal).
    The gap between them = denial pressure.
    Includes WaMu/IndyMac uncertainty band on 2008-2009.
    """
    fig = go.Figure()

    # ── Applications background fill ────────────────────
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["applications"],
        name="Applications filed",
        mode="lines",
        line=dict(color=C["muted"], width=1.2),
        fill="tozeroy",
        fillcolor="rgba(136,135,128,0.12)",
        hovertemplate="%{x}: %{y:,.0f} applications<extra></extra>",
    ))

    # ── Originations bold fill ───────────────────────────
    fig.add_trace(go.Scatter(
        x=df["year"], y=df["originations"],
        name="Loans originated",
        mode="lines",
        line=dict(color=C["recovery"], width=2.5),
        fill="tozeroy",
        fillcolor="rgba(29,158,117,0.22)",
        hovertemplate="%{x}: %{y:,.0f} originated<extra></extra>",
    ))

    # ── WaMu / IndyMac data gap band ────────────────────
    # Fed Bulletin 2010: 2008 data undercounts ~15% of volume
    gap_years = df[df["year"].isin([2008, 2009])].copy()
    low_bound  = gap_years["originations"] * 0.83   # -17% estimate
    x_band = (
        list(gap_years["year"]) +
        list(gap_years["year"].iloc[::-1])
    )
    y_band = (
        list(gap_years["originations"]) +
        list(low_bound.iloc[::-1])
    )
    fig.add_trace(go.Scatter(
        x=x_band, y=y_band,
        fill="toself",
        fillcolor="rgba(239,159,39,0.18)",
        line=dict(color=C["warning"], width=0.8, dash="dot"),
        name="Data gap: WaMu + IndyMac missing",
        hovertemplate="Estimated true range (WaMu/IndyMac absent)<extra></extra>",
        showlegend=True,
    ))

    # ── Annotation: WaMu label ───────────────────────────
    fig.add_annotation(
        x=2008.5,
        y=(df[df["year"] == 2008]["originations"].values[0] * 0.88) if len(df[df["year"] == 2008]) > 0 else 0,
        text="⚠ WaMu + IndyMac<br>did not file 2008 HMDA",
        showarrow=True,
        arrowhead=2, arrowwidth=1, arrowcolor=C["warning"],
        ax=60, ay=-40,
        font=dict(size=9, color=C["warning"]),
        align="left",
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=C["warning"],
        borderwidth=0.5,
        borderpad=4,
    )

    # ── Event lines ──────────────────────────────────────
    fig = _add_events(fig, df, "applications")

    # ── Highlight crash zone ─────────────────────────────
    fig.add_vrect(
        x0=2007.5, x1=2011.5,
        fillcolor="rgba(226,75,74,0.04)",
        line_width=0,
        annotation_text="Crisis period",
        annotation_position="top left",
        annotation_font=dict(size=9, color=C["crash"]),
    )

    fig.update_layout(**_base_layout(
        height=H,
        title=dict(
            text="Applications vs originations — the denial wall",
            font=dict(size=13, weight=500),
            x=0, xanchor="left",
        ),
        xaxis=dict(title=None, showgrid=False, zeroline=False,
                   tickcolor=C["border"], linecolor=C["border"],
                   dtick=1),
        yaxis=dict(title="Loan count", gridcolor=C["grid"],
                   zeroline=False, tickformat=".2s"),
    ))

    return fig


def fig_origination_rate(df: pd.DataFrame) -> go.Figure:
    """
    Line: origination rate % over time.
    Shows the credit tightening in one clean signal.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df["year"], y=df["origination_rate"],
        mode="lines+markers",
        name="Origination rate",
        line=dict(color=C["crash"], width=2.5),
        marker=dict(size=6, color=C["crash"]),
        fill="tozeroy",
        fillcolor="rgba(226,75,74,0.08)",
        hovertemplate="%{x}: %{y:.1%}<extra></extra>",
    ))

    # Pre-crisis baseline
    _pre = df[df["year"] == 2007]["origination_rate"]
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

    # Bottom annotation
    bottom = df.loc[df["origination_rate"].idxmin()]
    fig.add_annotation(
        x=bottom["year"], y=bottom["origination_rate"],
        text=f"Bottom: {bottom['origination_rate']:.0%}",
        showarrow=True, arrowhead=2,
        ax=0, ay=-30,
        font=dict(size=9, color=C["crash"]),
    )

    fig.update_layout(**_base_layout(
        height=H_SM,
        margin=dict(l=48, r=100, t=20, b=40),
        title=dict(
            text="Origination rate (loans originated / applications filed)",
            font=dict(size=12), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickcolor=C["border"], dtick=1),
        yaxis=dict(gridcolor=C["grid"], zeroline=False,
                   tickformat=".0%", range=[0.4, 0.8]),
        showlegend=False,
    ))

    return fig


# ─────────────────────────────────────────────────────────
# CHAPTER 3 — FHA TWO-PHASE STORY
# ─────────────────────────────────────────────────────────

def fig_fha_phases(df: pd.DataFrame) -> go.Figure:
    """
    100% stacked bar: loan type share by year.
    Clearly shows FHA near-death (2007) then explosion (2009-10).
    """
    color_map = {
        "Conventional": C["conventional"],
        "FHA":          C["fha"],
        "VA":           C["va"],
        "FSA/RHS":      C["fsa"],
    }

    fig = go.Figure()

    for lt, color in color_map.items():
        sub = df[df["loan_type"] == lt].sort_values("year")
        fig.add_trace(go.Bar(
            x=sub["year"],
            y=sub["share"],
            name=lt,
            marker_color=color,
            hovertemplate=f"{lt}: %{{y:.1%}}<extra></extra>",
        ))

    # ── Phase annotations ────────────────────────────────
    # Phase 1: FHA near-death
    fig.add_vrect(
        x0=2006.5, x1=2007.5,
        fillcolor="rgba(226,75,74,0.07)",
        line_width=0,
        layer="below",
    )
    fig.add_annotation(
        x=2007, y=1.06,
        text="FHA: 3%<br>near-death",
        showarrow=False,
        font=dict(size=9, color=C["crash"]),
        yref="paper",
    )

    # Phase 2: Government rescue
    fig.add_vrect(
        x0=2007.5, x1=2010.5,
        fillcolor="rgba(55,138,221,0.06)",
        line_width=0,
        layer="below",
    )
    fig.add_annotation(
        x=2009, y=1.06,
        text="Government rescue",
        showarrow=False,
        font=dict(size=9, color=C["govt"]),
        yref="paper",
    )

    # Phase 3: MIP increases slow FHA
    fig.add_vrect(
        x0=2010.5, x1=2013.5,
        fillcolor="rgba(136,135,128,0.05)",
        line_width=0,
        layer="below",
    )
    fig.add_annotation(
        x=2012, y=1.06,
        text="MIP increases<br>slow FHA",
        showarrow=False,
        font=dict(size=9, color=C["muted"]),
        yref="paper",
    )

    # Arrow pointing to FHA peak
    peak_row = df[df["loan_type"] == "FHA"].sort_values("share", ascending=False).iloc[0]
    fig.add_annotation(
        x=peak_row["year"],
        y=peak_row["share"] * 0.5,
        text=f"FHA peak:<br>{peak_row['share']:.0%}",
        showarrow=True,
        arrowhead=2, arrowwidth=1, arrowcolor=C["govt"],
        ax=50, ay=0,
        font=dict(size=9, color=C["govt"]),
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor=C["govt"], borderwidth=0.5, borderpad=3,
    )

    fig.update_layout(**_base_layout(
        height=H,
        margin=dict(l=48, r=28, t=56, b=44),
        barmode="stack",
        title=dict(
            text="Loan type share — the FHA near-death and rescue story",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickcolor=C["border"], dtick=1),
        yaxis=dict(gridcolor=C["grid"], zeroline=False,
                   tickformat=".0%", title="Share of originations",
                   range=[0, 1.12]),
        bargap=0.15,
    ))

    return fig


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
            text="Loan-to-income ratio — how much were borrowers stretching?",
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
            text="Median loan/income ratio by income band — who was really over-leveraged?",
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

def fig_rvs_bar(df: pd.DataFrame) -> go.Figure:
    """
    Horizontal bar: Recovery Velocity Score per state.
    Color-coded: green (fast) → amber → red (slow/never).
    """
    df = df.sort_values("rvs_years", ascending=True)

    def color(r):
        if r <= 3:  return C["recovery"]
        if r <= 5:  return C["warning"]
        return C["crash"]

    fig = go.Figure(go.Bar(
        x=df["rvs_years"],
        y=df["state"],
        orientation="h",
        marker_color=[color(r) for r in df["rvs_years"]],
        text=[f"{r} yr{'s' if r != 1 else ''}" for r in df["rvs_years"]],
        textposition="outside",
        hovertemplate="%{y}: %{x} years to recover<extra></extra>",
    ))

    # Reference line: 4 years = "normal" post-recession recovery
    fig.add_vline(
        x=4,
        line=dict(color=C["muted"], width=1, dash="dot"),
        annotation_text="4yr benchmark",
        annotation_position="top",
        annotation_font=dict(size=9, color=C["muted"]),
    )

    fig.update_layout(**_base_layout(
        height=H_SM + 80,
        margin=dict(l=48, r=80, t=36, b=44),
        title=dict(
            text="Recovery Velocity Score — years to return to 80% of 2007 volume",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(
            showgrid=True, gridcolor=C["grid"], zeroline=False,
            tickcolor=C["border"], title="Years from trough (2009)",
        ),
        yaxis=dict(showgrid=False, zeroline=False, tickcolor=C["border"]),
        showlegend=False,
        bargap=0.25,
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
    Bubble chart: top lenders by origination volume.
    X = bank vs nonbank. Size = volume. Color = type.
    Shows Quicken overtaking Wells Fargo by 2017.
    """
    import random
    random.seed(selected_year)

    year_df = df[df["year"] == selected_year].copy()
    year_df["x_pos"] = year_df["lender_type"].map({"Bank": 0.3, "Nonbank": 0.7})
    year_df["x_pos"] += [random.gauss(0, 0.06) for _ in range(len(year_df))]
    year_df["x_pos"] = year_df["x_pos"].clip(0.05, 0.95)

    color_map = {"Bank": C["bank"], "Nonbank": C["nonbank"]}

    fig = go.Figure()

    for lt in ["Bank", "Nonbank"]:
        sub = year_df[year_df["lender_type"] == lt]
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
                opacity=0.8,
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
            text=f"Who is lending in {selected_year} — banks vs nonbanks",
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

    # Add dividing line
    fig.add_vline(x=0.5, line=dict(color=C["border"], width=1, dash="dot"))

    return fig


def fig_lender_trend(df: pd.DataFrame) -> go.Figure:
    """
    Line chart: bank vs nonbank total originations over time.
    Shows the structural shift clearly.
    """
    by_type = (
        df.groupby(["year", "lender_type"])["originations"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        by_type, x="year", y="originations",
        color="lender_type",
        color_discrete_map={"Bank": C["bank"], "Nonbank": C["nonbank"]},
        markers=True,
        labels={"originations": "Total originations", "year": "Year",
                "lender_type": "Lender type"},
    )
    fig.update_traces(line_width=2.5, marker_size=6)

    # Crossover annotation
    crossover_years = by_type[by_type["lender_type"] == "Nonbank"]
    crossover_years = crossover_years[
        crossover_years["originations"] >=
        by_type[by_type["lender_type"] == "Bank"].set_index("year")["originations"].reindex(crossover_years["year"].values).values
    ]
    if len(crossover_years):
        cx = crossover_years["year"].min()
        cy = crossover_years[crossover_years["year"] == cx]["originations"].values[0]
        fig.add_annotation(
            x=cx, y=cy,
            text="Nonbanks overtake<br>banks in originations",
            showarrow=True, arrowhead=2, arrowcolor=C["nonbank"],
            ax=60, ay=-30,
            font=dict(size=9, color=C["nonbank"]),
            bgcolor="rgba(255,255,255,0.9)",
            bordercolor=C["nonbank"], borderwidth=0.5, borderpad=3,
        )

    fig.update_layout(**_base_layout(
        height=H_SM + 40,
        margin=dict(l=48, r=28, t=36, b=44),
        title=dict(
            text="Bank vs nonbank originations — the structural shift",
            font=dict(size=13, weight=500), x=0, xanchor="left",
        ),
        xaxis=dict(showgrid=False, zeroline=False,
                   tickcolor=C["border"], dtick=1),
        yaxis=dict(gridcolor=C["grid"], zeroline=False,
                   tickformat=".2s"),
    ))

    return fig