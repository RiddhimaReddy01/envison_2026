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

# ─────────────────────────────────────────────────────────
# DESIGN TOKENS  — single source of truth for all charts
# ─────────────────────────────────────────────────────────
C = {
    "bg":          "rgba(0,0,0,0)",   # transparent — host provides bg
    "grid":        "rgba(26,26,26,0.12)",
    "border":      "rgba(26,26,26,0.22)",
    "text":        "#1A1A1A",
    "muted":       "#5A5A5A",
    "surface":     "#F1F3F2",

    # Semantic
    "crash":       "#D7261E",
    "recovery":    "#2C7A5A",
    "govt":        "#285C9A",
    "conventional":"#767676",
    "warning":     "#A6761D",
    "purchase":    "#285C9A",
    "refi":        "#3D8B6D",
    "bank":        "#767676",
    "nonbank":     "#A84A34",
    "veteran":     "#4F4B7A",
    "fha":         "#285C9A",
    "va":          "#3D8B6D",
    "fsa":         "#84BDAA",

    # Race palette
    "white":       "#767676",
    "black":       "#D7261E",
    "hispanic":    "#A6761D",
    "asian":       "#285C9A",
}

FONT  = "'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
FONT_SERIF = "'Merriweather', Georgia, 'Times New Roman', serif"
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
        transition=dict(duration=120, easing="linear"),
        font=dict(family=FONT, size=12, color=C["text"]),
        title=dict(font=dict(family=FONT_SERIF, size=14, color=C["text"]), x=0, xanchor="left"),
        hoverlabel=dict(font=dict(family=FONT, size=11), bgcolor="rgba(255,255,255,0.97)", bordercolor=C["border"]),
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
        title=dict(text="Credit access: approval rate (originations / applications)", font=dict(size=13), x=0, xanchor="left"),
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
        hole=0.45,
        marker=dict(colors=[C["conventional"], C["fha"], C["va"], C["fsa"]]),
        textinfo="percent",
        textposition="inside",
        sort=False,
    ))
    fig.update_layout(
        height=230,
        margin=dict(l=10, r=10, t=34, b=10),
        paper_bgcolor=C["bg"],
        plot_bgcolor=C["bg"],
        font=dict(family=FONT, size=11, color=C["text"]),
        title=dict(text="2007 snapshot", font=dict(size=12), x=0, xanchor="left"),
        showlegend=False,
    )
    return fig


def fig_collapse(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    if df is None or df.empty:
        return fig
    d = df.sort_values("year")

    fig.add_trace(go.Scatter(
        x=d["year"], y=d["applications"],
        name="Applications",
        mode="lines",
        line=dict(color="#1E4D8B", width=3.2, shape="spline", smoothing=0.7),
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["originations"],
        name="Originations",
        mode="lines",
        line=dict(color=C["crash"], width=3.4, shape="spline", smoothing=0.7),
        fill="tonexty",
        fillcolor="rgba(215,38,30,0.24)",
        hovertemplate="%{x}: %{y:,.0f}<extra></extra>",
    ))

    fig.add_vline(x=2008, line=dict(color=C["crash"], width=1.2, dash="dash"))
    y_anno = float(d["applications"].max()) * 0.86
    fig.add_annotation(
        x=2011,
        y=y_anno,
        text="The shaded gap is unmet credit demand.",
        showarrow=False,
        font=dict(size=10, color="#8F1D1A"),
        bgcolor="rgba(255,245,245,0.96)",
        bordercolor=C["crash"],
        borderwidth=0.5,
        borderpad=4,
    )

    fig.update_layout(**_base_layout(
        height=H,
        title=dict(text="Credit gap: applications vs originations", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], automargin=True),
        yaxis=dict(title="Loan count", gridcolor=C["grid"], zeroline=False, tickformat=".2s", automargin=True),
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
        title=dict(text="How widespread was high leverage? Loan mix by leverage threshold", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, tickcolor=C["border"], automargin=True, dtick=1),
        yaxis=dict(gridcolor=C["grid"], tickformat=".0%", title="Share of all loans", automargin=True, range=[0, 1]),
        legend=dict(orientation="h", x=0, y=1.02, xanchor="left", yanchor="bottom"),
    ))
    return fig


def fig_purchase_refi_share(df: pd.DataFrame) -> go.Figure:
    """Chapter 2: show composition shift with purchase/refinance shares."""
    fig = go.Figure()
    if df is None or df.empty:
        return fig

    d = df.sort_values("year").copy()
    total = d["purchase"] + d["refinance"]
    d["purchase_share"] = d["purchase"] / total.replace(0, pd.NA)
    d["refi_share"] = d["refinance"] / total.replace(0, pd.NA)

    fig.add_trace(go.Scatter(
        x=d["year"], y=d["purchase_share"],
        mode="lines", name="Purchase share",
        line=dict(color=C["purchase"], width=1.8, shape="spline", smoothing=0.7),
        stackgroup="one", groupnorm="fraction", fill="tozeroy",
        hovertemplate="Purchase share<br>%{x}: %{y:.1%}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=d["year"], y=d["refi_share"],
        mode="lines", name="Refinance share",
        line=dict(color=C["refi"], width=1.8, shape="spline", smoothing=0.7),
        stackgroup="one", groupnorm="fraction", fill="tonexty",
        hovertemplate="Refinance share<br>%{x}: %{y:.1%}<extra></extra>",
    ))

    fig.add_annotation(
        x=2013,
        y=0.88,
        text="Post-crisis recovery was dominated by refinancing rather than new purchases.",
        showarrow=False,
        font=dict(size=10, color=C["warning"]),
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor=C["warning"],
        borderwidth=0.5,
        borderpad=4,
    )

    fig.update_layout(**_base_layout(
        height=H,
        title=dict(text="The rebound was refinancing, not home buying", font=dict(size=13), x=0, xanchor="left"),
        xaxis=dict(showgrid=False, zeroline=False, dtick=1, tickcolor=C["border"], automargin=True),
        yaxis=dict(gridcolor=C["grid"], zeroline=False, tickformat=".0%", title="Share of mortgage activity", range=[0, 1], automargin=True),
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




