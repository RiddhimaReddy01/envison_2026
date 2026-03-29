"""
app.py - Envision Hackathon 2026  (FINAL)
==========================================
Post-Crisis Lending Landscape: A Documentary in Data

Run:
    pip install dash plotly polars pandas
    python app.py
    Open: http://127.0.0.1:8050

When real data arrives:
    Open data_loader.py -> set USE_REAL_DATA = True
"""

from functools import lru_cache
import traceback

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd

import data_loader as dl
import charts as ch
import world_bank_data as wb

C = {
    "bg":"#F7F5F0",
    "surface":"#EFEDE7",
    "border":"rgba(20,20,20,0.16)",
    "text":"#1A1A1A",
    "muted":"#3F3F3F",
    "crash":"#D7261E",
    "recovery":"#2C7A5A",
    "govt":"#285C9A",
    "veteran":"#4F4B7A",
    "civilian":"#0F5A7A",
    "warning":"#A6761D",
    "nonbank":"#A84A34",
}
FONT  = "'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
FONT_SERIF = "'Libre Baskerville', Georgia, 'Times New Roman', serif"
YEARS = list(range(2007,2018))
FS_NOTE = "12px"
FS_BODY = "14px"
FS_HEAD = "16px"

app = dash.Dash(__name__, title="Post-Crisis Lending 2007-2017",
                suppress_callback_exceptions=True)
server = app.server

# Server-side memoized dataframe loaders for smoother callbacks.
# Restart the app to refresh these after data files change.
@lru_cache(maxsize=1)
def _df_collapse():
    return dl.collapse_data().to_pandas()

@lru_cache(maxsize=1)
def _df_loan_type_share():
    return dl.loan_type_share().to_pandas()

@lru_cache(maxsize=1)
def _df_purchase_refi():
    return dl.purchase_refi().to_pandas()

@lru_cache(maxsize=1)
def _df_lti_sample():
    return dl.lti_sample().to_pandas()

@lru_cache(maxsize=1)
def _df_rvs_scores():
    return dl.rvs_scores().to_pandas()

@lru_cache(maxsize=1)
def _df_state_year_originations():
    return dl.state_year_originations().to_pandas()


@lru_cache(maxsize=1)
def _df_denial_rates():
    return dl.denial_rates().to_pandas()

@lru_cache(maxsize=1)
def _df_origination_share_by_race():
    return dl.origination_share_by_race().to_pandas()

@lru_cache(maxsize=1)
def _df_moderate_income_denial():
    return dl.moderate_income_denial().to_pandas()

@lru_cache(maxsize=1)
def _df_purchase_homeownership():
    return dl.purchase_homeownership().to_pandas()

@lru_cache(maxsize=1)
def _df_mortgage_rates():
    return dl.mortgage_rate_series().to_pandas()

@lru_cache(maxsize=1)
def _df_homeownership_age():
    return dl.homeownership_by_age().to_pandas()

@lru_cache(maxsize=1)
def _df_lender_bubble():
    return dl.lender_bubble().to_pandas()

@lru_cache(maxsize=1)
def _df_bank_nonbank():
    return dl.bank_nonbank_survival().to_pandas()

@lru_cache(maxsize=1)
def _df_recovery_affordability():
    return dl.recovery_vs_affordability().to_pandas()

@lru_cache(maxsize=1)
def _df_recovery_drivers():
    return dl.recovery_drivers_state().to_pandas()

@lru_cache(maxsize=1)
def _ch5_pack():
    df_rvs = _df_rvs_scores()
    df_bn = _df_bank_nonbank()
    df_ra = _df_recovery_affordability()
    df_drv = _df_recovery_drivers()

    fast = int((df_rvs["rvs_years"] <= 2).sum()) if not df_rvs.empty else 0
    slow = int((df_rvs["rvs_years"] >= 5).sum()) if not df_rvs.empty else 0
    min_years = int(df_rvs["rvs_years"].min()) if not df_rvs.empty else 0
    max_years = int(df_rvs["rvs_years"].max()) if not df_rvs.empty else 0

    bank_share_2007 = float(df_bn[(df_bn["lender_type"] == "Bank") & (df_bn["year"] == 2007)]["share"].iloc[0]) if not df_bn.empty and len(df_bn[(df_bn["lender_type"] == "Bank") & (df_bn["year"] == 2007)]) else 0.0
    bank_share_2017 = float(df_bn[(df_bn["lender_type"] == "Bank") & (df_bn["year"] == 2017)]["share"].iloc[0]) if not df_bn.empty and len(df_bn[(df_bn["lender_type"] == "Bank") & (df_bn["year"] == 2017)]) else 0.0
    nonbank_share_2007 = 1.0 - bank_share_2007
    nonbank_share_2017 = 1.0 - bank_share_2017

    fast_lti = float(df_ra[df_ra["rvs_years"] <= 2]["median_lti_2017"].mean()) if not df_ra.empty and len(df_ra[df_ra["rvs_years"] <= 2]) else 0.0
    slow_lti = float(df_ra[df_ra["rvs_years"] >= 5]["median_lti_2017"].mean()) if not df_ra.empty and len(df_ra[df_ra["rvs_years"] >= 5]) else 0.0
    df_map = df_rvs.merge(df_ra[["state", "median_lti_2017"]], on="state", how="left") if (not df_rvs.empty and not df_ra.empty) else df_rvs

    return {
        "df_rvs": df_rvs,
        "df_bn": df_bn,
        "df_ra": df_ra,
        "df_drv": df_drv,
        "df_map": df_map,
        "fast": fast,
        "slow": slow,
        "min_years": min_years,
        "max_years": max_years,
        "nonbank_share_2007": nonbank_share_2007,
        "nonbank_share_2017": nonbank_share_2017,
        "fast_lti": fast_lti,
        "slow_lti": slow_lti,
    }

@lru_cache(maxsize=1)
def _ch6_pack():
    df_dr = _df_denial_rates()
    df_age = _df_homeownership_age()
    df_ho = _df_purchase_homeownership()
    df_col = _df_collapse()
    df_loan = _df_loan_type_share()

    white_low = df_dr[(df_dr["race"] == "White") & (df_dr["income_band"] == "<50K")].sort_values("year") if not df_dr.empty else pd.DataFrame()
    black_low = df_dr[(df_dr["race"] == "Black / African American") & (df_dr["income_band"] == "<50K")].sort_values("year") if not df_dr.empty else pd.DataFrame()
    post_w = float(white_low[white_low["year"] >= 2012]["denial_rate"].mean()) if not white_low.empty else 0.0
    post_b = float(black_low[black_low["year"] >= 2012]["denial_rate"].mean()) if not black_low.empty else 0.0
    gap_pp = (post_b - post_w) * 100.0
    ratio = (post_b / post_w) if post_w > 0 else 0.0
    h2007 = float(df_ho[df_ho["year"] == 2007]["homeownership_rate"].iloc[0]) if len(df_ho[df_ho["year"] == 2007]) else 0.0
    h2017 = float(df_ho[df_ho["year"] == 2017]["homeownership_rate"].iloc[0]) if len(df_ho[df_ho["year"] == 2017]) else 0.0

    return {
        "df_dr": df_dr,
        "df_age": df_age,
        "df_ho": df_ho,
        "df_col": df_col,
        "df_loan": df_loan,
        "post_w": post_w,
        "post_b": post_b,
        "gap_pp": gap_pp,
        "ratio": ratio,
        "h2007": h2007,
        "h2017": h2017,
    }

@lru_cache(maxsize=1)
def _ch8_pack():
    lt = _df_loan_type_share()
    pr = _df_purchase_refi()
    dr = _df_denial_rates()

    top_share_2007 = 0.0
    if not lt.empty and {"year", "share"}.issubset(set(lt.columns)):
        s07 = lt[lt["year"] == 2007]
        if len(s07):
            top_share_2007 = float(s07["share"].max())

    decoupling_gap_idx = 0.0
    if not pr.empty and {"year", "purchase", "refinance"}.issubset(set(pr.columns)):
        x = pr[["year", "purchase", "refinance"]].copy().sort_values("year")
        b = x[x["year"] == 2007]
        if len(b):
            bp = float(b["purchase"].iloc[0])
            br = float(b["refinance"].iloc[0])
        else:
            bp = float(x["purchase"].iloc[0]) if len(x) else 0.0
            br = float(x["refinance"].iloc[0]) if len(x) else 0.0
        if bp > 0 and br > 0 and len(x):
            x["purchase_idx"] = (x["purchase"] / bp) * 100.0
            x["refi_idx"] = (x["refinance"] / br) * 100.0
            decoupling_gap_idx = float((x["refi_idx"] - x["purchase_idx"]).max())

    denial_gap_pp = 0.0
    if not dr.empty and {"year", "race", "income_band", "denial_rate"}.issubset(set(dr.columns)):
        wl = dr[(dr["race"] == "White") & (dr["income_band"] == "<50K") & (dr["year"] >= 2012)]
        bl = dr[(dr["race"] == "Black / African American") & (dr["income_band"] == "<50K") & (dr["year"] >= 2012)]
        post_w = float(wl["denial_rate"].mean()) if len(wl) else 0.0
        post_b = float(bl["denial_rate"].mean()) if len(bl) else 0.0
        denial_gap_pp = (post_b - post_w) * 100.0

    score = pd.DataFrame([
        {
            "lesson": "Channel diversification",
            "current": top_share_2007 * 100.0,
            "target": 70.0,
            "direction": "lower_better",
        },
        {
            "lesson": "Refi-purchase opportunity gap",
            "current": decoupling_gap_idx,
            "target": 30.0,
            "direction": "lower_better",
        },
        {
            "lesson": "Same-income denial disparity",
            "current": denial_gap_pp,
            "target": 10.0,
            "direction": "lower_better",
        },
    ])

    return {
        "top_share_2007": top_share_2007,
        "decoupling_gap_idx": decoupling_gap_idx,
        "denial_gap_pp": denial_gap_pp,
        "score": score,
    }

@lru_cache(maxsize=8)
def _df_global_shockwave(cache_sig: str):
    return wb.load_global_shockwave_summary()

@lru_cache(maxsize=8)
def _ch9_pack(cache_sig: str):
    df_global, source = _df_global_shockwave(cache_sig)
    df = df_global.copy()

    worst_gdp = df.loc[df["gdp_growth_2009"].idxmin()] if not df.empty and df["gdp_growth_2009"].notna().any() else None
    largest_jobs = df.loc[df["unemployment_change_peak"].idxmax()] if not df.empty and df["unemployment_change_peak"].notna().any() else None
    export_worst_pool = df[df["export_growth_2009"].notna()]
    export_worst = export_worst_pool.loc[export_worst_pool["export_growth_2009"].idxmin()] if not export_worst_pool.empty else None

    return {
        "df_global": df,
        "source": source,
        "worst_gdp": worst_gdp,
        "largest_jobs": largest_jobs,
        "export_worst": export_worst,
    }

def card(children, pad="24px 28px", mb="16px"):
    return html.Div(children, className="card-soft", style={
        "background":C["bg"],"border":f"0.5px solid {C['border']}",
        "borderRadius":"10px","padding":pad,"marginBottom":mb,
    })

def kpi(number, label, color=None, note=None):
    return html.Div([
        html.Div(number, style={"fontSize":"24px","fontWeight":"500",
                                "lineHeight":"1.1","color":color or C["text"]}),
        html.Div(label,  style={"fontSize":"13px","color":C["muted"],"marginTop":"4px"}),
        html.Div(note,   style={"fontSize":"11px","color":C["muted"],"marginTop":"2px",
                                "fontStyle":"italic"}) if note else None,
    ], className="kpi-soft", style={"background":C["surface"],"borderRadius":"6px",
              "padding":"14px 16px","flex":"1","minWidth":"130px","border":f"0.5px solid {C['border']}"})

def kpi_row(items, center=False):
    style = {
        "display":"flex",
        "gap":"10px",
        "flexWrap":"wrap",
        "marginBottom":"20px",
        "alignItems":"stretch",
    }
    if center:
        style.update({
            "justifyContent":"center",
            "maxWidth":"980px",
            "margin":"0 auto 20px",
        })
    return html.Div(items, style=style)

def chapter_title(num, title, subtitle):
    return html.Div([
        html.Div([
            html.Span(str(num), style={
                "display":"inline-flex","alignItems":"center","justifyContent":"center",
                "width":"28px","height":"28px","borderRadius":"50%",
                "background":"#FCE9E7","color":C["crash"],
                "fontSize":"12px","fontWeight":"500","marginRight":"10px","flexShrink":"0",
                "border":f"0.5px solid {C['border']}",
            }),
            html.Span(title, style={"fontSize":"22px","fontWeight":"700","fontFamily":FONT_SERIF,"letterSpacing":"0.01em"}),
        ], style={"display":"flex","alignItems":"center","marginBottom":"5px"}),
        html.P(subtitle, style={"fontSize":FS_BODY,"color":C["muted"],"margin":"0 0 20px 38px"}),
    ])

def ann(civilian, veteran=None, mode=None):
    return html.Div(civilian, style={
        "padding":"10px 14px","borderRadius":"8px","marginTop":"12px",
        "fontSize":FS_BODY,"fontWeight":"500","color":C["civilian"],
        "lineHeight":"1.5","background":"#E1F5EE50",
        "border":"0.5px solid #1D9E7550",
    })

def src(*labels):
    return html.Div([
        html.Span(l, style={"fontSize":"10px","padding":"2px 8px","borderRadius":"5px",
            "background":"#F1EFE8","color":C["muted"],"border":"0.5px solid rgba(0,0,0,0.10)",
            "marginRight":"6px","display":"inline-block"}) for l in labels
    ], style={"marginTop":"8px"})

def data_note(text):
    return html.Div([html.Span("Warning  ",style={"color":C["warning"],"fontWeight":"500",
        "fontSize":"11px"}), html.Span(text,style={"fontSize":"11px","color":C["muted"]})],
        style={"padding":"8px 12px","borderRadius":"6px","marginTop":"10px",
               "background":"rgba(239,159,39,0.06)","border":"0.5px solid rgba(239,159,39,0.4)"})

def insight_chip(text, color=None):
    clean = (text or "").strip()
    if clean.lower().startswith("so what:"):
        clean = clean.split(":", 1)[1].strip()
    return html.Div([
        html.Span("Takeaway: ", style={"fontWeight":"700", "color":C["text"]}),
        clean
    ], style={
        "fontSize":"13px","fontWeight":"600","color":color or C["text"],
        "padding":"8px 12px","borderRadius":"999px","display":"inline-block",
        "background":"#F4F1E8","border":"0.5px solid rgba(17,24,39,0.16)",
        "marginBottom":"14px",
    })

def key_insight(text):
    return html.Div([
        card([
            html.Div("Key Insight", style={
                "fontSize":"11px", "fontWeight":"700", "color":C["warning"], 
                "letterSpacing":"0.06em", "textTransform":"uppercase", "marginBottom":"6px"
            }),
            html.Div(text, style={"fontSize":"15px", "fontWeight":"500", "fontStyle":"italic", "lineHeight":"1.5", "color":C["text"]})
        ], pad="16px 20px")
    ], style={"borderTop": f"3px solid {C['warning']}", "marginTop":"24px", "borderRadius":"12px"})

def _fmt_pct(value):
    return "n/a" if value is None or value != value else f"{value:.1f}%"

def _fmt_pp(value):
    return "n/a" if value is None or value != value else f"{value:+.1f} pp"

def _global_shockwave_source_note(source):
    notes = {
        "api": "World Bank API data fetched and cached locally for this page.",
        "cache": "World Bank API data loaded from local cache to avoid repeated refresh calls.",
        "backup": "World Bank API fetch was unavailable, so this page is using the built-in backup snapshot for the same countries and years.",
    }
    return notes.get(source, "World Bank source status unavailable.")

def _global_shockwave_table(df):
    header_style = {"textAlign":"left","fontSize":"10px","color":C["muted"],"padding":"0 8px 8px 0","borderBottom":f"0.5px solid {C['border']}"}
    cell_style = {"padding":"10px 8px 10px 0","fontSize":"12px","color":C["text"],"borderBottom":"0.5px solid rgba(20,20,20,0.08)","verticalAlign":"top"}
    rows = []
    for row in df.itertuples(index=False):
        peak_label = "n/a"
        if row.unemployment_peak is not None and row.unemployment_peak == row.unemployment_peak and row.unemployment_peak_year:
            peak_label = f"{row.unemployment_peak:.1f}% ({int(row.unemployment_peak_year)})"
        rows.append(html.Tr([
            html.Td(row.country, style=cell_style),
            html.Td(_fmt_pct(row.gdp_growth_2009), style=cell_style),
            html.Td(_fmt_pp(row.unemployment_change_peak), style=cell_style),
            html.Td(peak_label, style=cell_style),
            html.Td(_fmt_pct(row.export_growth_2009), style=cell_style),
            html.Td(row.crisis_channel, style=cell_style),
        ]))

    return html.Table([
        html.Thead(html.Tr([
            html.Th("Country", style=header_style),
            html.Th("GDP growth (2009)", style=header_style),
            html.Th("Unemployment shock", style=header_style),
            html.Th("Peak unemployment", style=header_style),
            html.Th("Export growth (2009)", style=header_style),
            html.Th("Main crisis channel", style=header_style),
        ])),
        html.Tbody(rows),
    ], style={"width":"100%","borderCollapse":"collapse","tableLayout":"fixed"})

def G(fig, gid="", keep_legend=False, keep_title=False):
    fig_out = go.Figure(fig)
    # Consistent contract: charts own legend behavior unless explicitly forced on.
    if keep_legend:
        fig_out.update_layout(showlegend=True)
    if not keep_title:
        fig_out.update_layout(title=dict(text=""))
    return dcc.Graph(id=gid if gid else {"type":"graph","idx":gid},
                     figure=fig_out, animate=False,
                     config={"displayModeBar":False,"responsive":True},
                     style={"width":"100%"})

CHAPTERS = [(1,"The Bet"),(2,"The Crash"),(3,"The Rescue"),
            (4,"Fake Recovery"),(5,"Who Survived"),(6,"Left Behind"),(7,"New Rules"),(8,"Lessons"),(9,"Global Shockwave")]

def navbar(active=1):
    return html.Div([
        html.Div([
            html.Span("Post-Crisis Lending",style={"fontWeight":"700","fontSize":"15px","fontFamily":FONT_SERIF}),
            html.Span(" 2007-2017",style={"fontSize":"13px","color":C["muted"]}),
        ], style={"flex":"0 0 auto"}),
        html.Div([
            dcc.Link(f"{n}. {lbl}", href=f"/chapter/{n}", style={
                "padding":"5px 10px","borderRadius":"6px","fontSize":"12px",
                "textDecoration":"none","whiteSpace":"nowrap",
                "color":C["text"] if n==active else C["muted"],
                "background":C["surface"] if n==active else "transparent",
                "fontWeight":"500" if n==active else "400",
            }) for n,lbl in CHAPTERS
        ], style={"display":"flex","gap":"2px","alignItems":"center",
                  "flex":"1","flexWrap":"wrap","justifyContent":"center"}),
        html.Div([
            html.A("Export PDF", href="/export/print", style={
                "padding":"7px 12px","borderRadius":"8px","fontSize":"12px",
                "textDecoration":"none","whiteSpace":"nowrap","fontWeight":"600",
                "color":"white","background":C["civilian"],
                "border":"0.5px solid rgba(15,90,122,0.45)",
                "boxShadow":"0 4px 12px rgba(15,90,122,0.16)",
            }),
        ], style={"display":"flex","alignItems":"center","flex":"0 0 auto"}),
    ], style={"display":"flex","alignItems":"center","gap":"16px","padding":"10px 28px",
              "background":C["bg"],"borderBottom":f"0.5px solid {C['border']}",
              "position":"sticky","top":"0","zIndex":"100","fontFamily":FONT})


def p1(mode):
    collapse = _df_collapse()
    risk = _df_loan_type_share()
    a2007 = collapse[collapse["year"] == 2007]
    approval_2007 = float(a2007["origination_rate"].iloc[0]) if len(a2007) else 0.0
    conv = risk[risk["loan_type"] == "Conventional"].sort_values("year")
    conv_2007 = float(conv[conv["year"] == 2007]["share"].iloc[0]) if len(conv[conv["year"] == 2007]) else 0.0
    conv_2007_plus = "90%+" if conv_2007 >= 0.90 else f"{conv_2007:.0%}"
    r2007 = risk[risk["year"] == 2007].sort_values("share", ascending=False)
    top1 = float(r2007["share"].iloc[0]) if len(r2007) else 0.0
    top2 = float(r2007["share"].iloc[1]) if len(r2007) > 1 else 0.0
    conc_gap_pp = (top1 - top2) * 100.0
    gov_2007 = float(r2007[r2007["loan_type"].isin(["FHA", "VA", "FSA/RHS"])]["share"].sum()) if len(r2007) else 0.0
    pre_2007 = collapse[collapse["year"] == 2007]["origination_rate"]
    pre_2008 = collapse[collapse["year"] == 2008]["origination_rate"]
    is_proxy = bool(a2007["is_proxy"].iloc[0]) if len(a2007) and "is_proxy" in a2007.columns else False
    pre_msg = "Approval trend before the break is flat in the current scoped series."
    vet_msg = "This panel uses your current action-taken coverage."
    if len(pre_2007) and len(pre_2008) and float(pre_2007.iloc[0]) > 0:
        delta = (float(pre_2008.iloc[0]) / float(pre_2007.iloc[0])) - 1.0
        if delta < -0.005:
            pre_msg = f"Approval rates were already softening before the break ({delta:.1%} vs 2007)."
            vet_msg = "Pre-crisis approval drift is visible in the yearly application-originations ratio."
        elif delta > 0.005:
            pre_msg = f"Approval rates were rising pre-break in this series ({delta:.1%} vs 2007)."
            vet_msg = "This panel reflects your current scoped denominator and action-taken coverage."
    if is_proxy:
        pre_msg = f"{pre_msg} (Proxy series from anchored denial rates due to scoped originated-loan HMDA file.)"
        vet_msg = "Because this run is originated-loans scoped, approval trend is proxy-estimated from documented denial anchors."

    return html.Div([
        chapter_title(1, "Before It Broke", "Scale was visible. Fragility was hidden in plain sight."),
        kpi_row([
            kpi(f"{approval_2007:.0%}", "Approval rate in 2007", C["govt"], "Originations / applications"),
            kpi(conv_2007_plus, "Conventional share in 2007", C["warning"], "Private-market dominance"),
        ]),
        card([
            html.Div("Credit Access (Primary Signal)", style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px"}),
            G(ch.fig_ch1_scale_speed(collapse), "ch1-access"),
            ann(
                pre_msg,
                vet_msg,
                mode,
            )
        ]),
        insight_chip("So what: The credit engine was already softening before the official break, indicating lenders were quietly retreating first.", C["govt"]),
        card([
            html.Div("2007 Snapshot", style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px"}),
            G(ch.fig_ch1_snapshot_pie(risk), "ch1-snapshot"),
            ann(
                "The market was a monoculture: conventional loans dominated while the government-backed safety net remained tiny.",
                "This donut is computed directly from 2007 HMDA loan-type shares.",
                mode,
            ),
        ], pad="18px 18px"),
        insight_chip(f"So what: The top channel led the runner-up by {conc_gap_pp:.0f} percentage points, with only {gov_2007:.1%} in the government-backed safety net.", C["warning"]),
        
        key_insight("Before the crash, concentration risk was already extreme: one private channel carried almost the whole system, with only a thin public backstop."),
    ])

def p2(mode):
    df = _df_collapse()
    apps_2008 = int(df[df["year"] == 2008]["applications"].iloc[0]) if len(df[df["year"] == 2008]) else 0
    gap_2012 = int((df[df["year"] == 2012]["applications"].iloc[0] - df[df["year"] == 2012]["originations"].iloc[0])) if len(df[df["year"] == 2012]) else 0
    rate_2012 = float(df[df["year"] == 2012]["origination_rate"].iloc[0]) if len(df[df["year"] == 2012]) else 0.0
    rate_2007 = float(df[df["year"] == 2007]["origination_rate"].iloc[0]) if len(df[df["year"] == 2007]) else 0.0
    rate_change = ((rate_2012 / rate_2007) - 1.0) if rate_2007 else 0.0
    stat_note = f"Origination rate {rate_2007:.0%}->{rate_2012:.0%} (2007->2012)." if rate_2007 else "Origination rate trend unavailable."
    apps_2012 = int(df[df["year"] == 2012]["applications"].iloc[0]) if len(df[df["year"] == 2012]) else 0
    gap_share_2012 = (gap_2012 / apps_2012) if apps_2012 else 0.0

    return html.Div([
        chapter_title(2,"The Day the Machine Stopped","Demand persisted, but approval capacity broke."),
        kpi_row([kpi(f"{apps_2008:,.0f}","Applications in 2008",C["warning"],"Demand stayed present"),
                 kpi(f"{gap_2012:,.0f}","Credit gap in 2012",C["crash"],"Applications - originations"),
                 kpi(f"{rate_2012:.0%}","Approval rate in 2012",C["crash"],"Originations / applications")]),
        insight_chip(f"So what: In 2012, about {gap_share_2012:.0%} of applications did not convert into originations.", C["crash"]),
        card([G(ch.fig_collapse(df),"collapse"),
              ann("The shock was institutional triage: lenders rationed approvals faster than households reduced demand.",
                  f"{stat_note} The widening gap tracks credit rationing, not a disappearance of would-be borrowers.",
                  mode),
              src("Federal Reserve Bulletin 2010","CFPB HMDA Data Point")]),
              
        key_insight("The system didn't just slow down; it broke structurally. Lenders rationed approvals aggressively, stranding millions of credit-worthy borrowers in an unmet demand gap."),
    ])

def p3(mode):
    lt = _df_loan_type_share()
    conv = lt[lt["loan_type"] == "Conventional"].sort_values("year")
    gov = lt[lt["loan_type"].isin(["FHA", "VA", "FSA/RHS"])].groupby("year", as_index=False)["share"].sum().sort_values("year")
    conv_2007 = float(conv[conv["year"] == 2007]["share"].iloc[0]) if len(conv[conv["year"] == 2007]) else 0.0
    conv_2017 = float(conv[conv["year"] == 2017]["share"].iloc[0]) if len(conv[conv["year"] == 2017]) else 0.0
    gov_2007 = float(gov[gov["year"] == 2007]["share"].iloc[0]) if len(gov[gov["year"] == 2007]) else 0.0
    gov_2017 = float(gov[gov["year"] == 2017]["share"].iloc[0]) if len(gov[gov["year"] == 2017]) else 0.0
    gov_delta_pp = (gov_2017 - gov_2007) * 100.0
    gov_peak_row = gov.loc[gov["share"].idxmax()] if not gov.empty else {"year": 2009, "share": 0.0}
    return html.Div([
        chapter_title(3,"Uncle Sam Becomes Your Bank",
                      "Private balance sheets pulled back; public guarantees filled the vacuum."),
        kpi_row([kpi(f"{conv_2007:.0%}->{conv_2017:.0%}","Conventional share 2007->2017",C["warning"],"Private channel contracted"),
                 kpi(f"{gov_2007:.0%}->{gov_2017:.0%}","Gov-backed share 2007->2017",C["govt"],"FHA + VA + FSA/RHS"),
                 kpi(f"{float(gov_peak_row['share']):.0%}",f"Gov-backed peak ({int(gov_peak_row['year'])})",C["recovery"],"Shift in lending ownership")]),
        insight_chip(f"So what: Government-backed lending gained {gov_delta_pp:+.0f} percentage points from 2007 to 2017.", C["govt"]),
        card([
            html.Div([
                html.Div([
                    G(ch.fig_fha_phases(lt), "ch3-substitution"),
                ], style={"flex":"2.1","minWidth":"420px"}),
                html.Div([
                    html.Div("Loan-Type Legend", style={"fontSize":"12px","fontWeight":"600","margin":"2px 0 8px"}),
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Type", style={"textAlign":"left","fontSize":"10px","color":C["muted"],"paddingBottom":"6px","paddingRight":"8px"}),
                            html.Th("Included Loans", style={"textAlign":"left","fontSize":"10px","color":C["muted"],"paddingBottom":"6px","paddingRight":"8px"}),
                            html.Th("Interpretation", style={"textAlign":"left","fontSize":"10px","color":C["muted"],"paddingBottom":"6px"}),
                        ])),
                        html.Tbody([
                            html.Tr([html.Td("Conventional (private)"), html.Td("Conventional"), html.Td("Private balance-sheet credit")]),
                            html.Tr([html.Td("Government-backed total"), html.Td("FHA + VA + FSA/RHS"), html.Td("Publicly supported credit channel")]),
                        ]),
                    ], style={
                        "width":"100%",
                        "fontSize":"10.5px",
                        "lineHeight":"1.3",
                        "tableLayout":"fixed",
                        "borderCollapse":"separate",
                        "borderSpacing":"0 6px",
                    }),
                ], style={"flex":"1","minWidth":"280px"}),
            ], style={"display":"flex","gap":"12px","flexWrap":"wrap","alignItems":"flex-start"}),
        ]),
        key_insight("Recovery was a direct handoff: private balance sheets refused the risk, forcing public guarantees (like FHA) to fill the vacuum and subsidize the market's floor."),
    ])

def p4(mode):
    df_lti = _df_lti_sample()
    pr = _df_purchase_refi()
    ho = _df_purchase_homeownership()
    col = _df_collapse()

    refi_share_peak = 0.0
    peak_year = 2012
    if not pr.empty and "purchase_pct" in pr.columns:
        tmp = pr.copy()
        tmp["refi_share"] = 1.0 - tmp["purchase_pct"]
        peak = tmp.loc[tmp["refi_share"].idxmax()] if len(tmp) else None
        if peak is not None:
            refi_share_peak = float(peak["refi_share"])
            peak_year = int(peak["year"])

    h2007 = float(ho[ho["year"] == 2007]["homeownership_rate"].iloc[0]) if len(ho[ho["year"] == 2007]) else 0.0
    h2017 = float(ho[ho["year"] == 2017]["homeownership_rate"].iloc[0]) if len(ho[ho["year"] == 2017]) else 0.0
    home_growth = ((h2017 - h2007) / h2007) if h2007 else 0.0

    y2007 = float(col[col["year"] == 2007]["origination_rate"].iloc[0]) if len(col[col["year"] == 2007]) else 0.0
    y2017 = float(col[col["year"] == 2017]["origination_rate"].iloc[0]) if len(col[col["year"] == 2017]) else 0.0

    hollow_index = refi_share_peak / max(abs(home_growth), 0.01)

    return html.Div([
        chapter_title(4, "The Refi Mirage", "Volume recovered, but ownership formation did not keep pace."),
        kpi_row([
            kpi(f"{refi_share_peak:.0%}", f"Peak refinance share ({peak_year})", C["crash"], "Share of total mortgage activity"),
            kpi(f"{h2007:.1f}% -> {h2017:.1f}%", "Homeownership rate (2007->2017)", C["warning"]),
            kpi(f"{y2007:.0%} -> {y2017:.0%}", "Origination yield (2007->2017)", C["govt"], "Originations / applications"),
            kpi(f"{hollow_index:.1f}", "Hollow Index", C["crash"], "Refi share / |homeownership growth|"),
        ]),
        insight_chip("The recovery looked large in volume, but much of it was refinance churn rather than new ownership access.", C["crash"]),

        card([
            html.Div("The Refi Mirage: Activity Roared, Ownership Stalled",
                     style={"fontSize": "16px", "fontWeight": "700", "marginBottom": "2px"}),
            html.Div("Post-crisis volume rebounded, but much of it was existing owners recycling debt rather than new household entry.",
                     style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px", "color": "#1A1A1A"}),
            G(ch.fig_ch4_refi_mirage(pr, ho), "ch4-refi-mirage"),
            ann(
                "Volume recovery was refinance-led, not ownership-led, so activity and access diverged.",
                "Peak-volume years were debt rotation years, not broad household entry years.",
                mode,
            ),
        ]),

        card([
            html.Div("The Thirstier Funnel: Better Conversion, Smaller Participation",
                     style={"fontSize": "16px", "fontWeight": "700", "marginBottom": "2px"}),
            html.Div("Approval efficiency improved while the applicant pool shrank, revealing a narrower market rather than broader access.",
                     style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px", "color": "#1A1A1A"}),
            G(ch.fig_ch4_yield_attrition(col, 2007, 2017), "ch4-yield"),
            ann(
                "The funnel became more selective: stronger conversion rates masked falling participation.",
                "Efficiency improved on paper, while the addressable market thinned in practice.",
                mode,
            ),
        ]),

        card([
            html.Div("The Squeezed Middle: Leverage Pressure Moved into the Core",
                     style={"fontSize": "16px", "fontWeight": "700", "marginBottom": "2px"}),
            html.Div("By the end of recovery, middle-income borrowers were climbing fastest toward higher loan-to-income stress.",
                     style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px", "color": "#1A1A1A"}),
            G(ch.fig_ch4_lti_income_groups(df_lti), "ch4-lti-groups"),
            ann(
                "Leverage risk migrated from the fringe toward the center of the income distribution.",
                "The risk center moved toward the middle of the distribution even without being the absolute highest line.",
                mode,
            ),
        ]),
    ])
def p5(mode):
    pack = _ch5_pack()
    df_rvs = pack["df_rvs"]
    df_bn = pack["df_bn"]
    df_ra = pack["df_ra"]
    df_drv = pack["df_drv"]
    df_map = pack["df_map"]
    fast = pack["fast"]
    slow = pack["slow"]
    min_years = pack["min_years"]
    max_years = pack["max_years"]
    nonbank_share_2007 = pack["nonbank_share_2007"]
    nonbank_share_2017 = pack["nonbank_share_2017"]
    fast_lti = pack["fast_lti"]
    slow_lti = pack["slow_lti"]

    return html.Div([
        chapter_title(5, "Who Survived — And What It Cost Them",
                      "Recovery speed, structural handoff, and the affordability trap."),
        kpi_row([
            kpi(f"{min_years}–{max_years} yrs", "Recovery range by state", C["warning"],
                "Years to return to 80% of 2007 volume"),
            kpi(str(fast), "Fast-recovery states", C["recovery"], "Recovered in ≤2 years"),
            kpi(str(slow), "Slow-recovery states", C["crash"],    "Took 5+ years"),
            kpi(f"{nonbank_share_2017:.0%}", "Nonbank share by 2017", C["nonbank"],
                f"Up from {nonbank_share_2007:.0%} in 2007"),
        ]),
        insight_chip(
            f"Fast-recovery states hit median LTI {fast_lti:.2f}x by 2017 "
            f"vs {slow_lti:.2f}x in slow-recovery states — they recovered into unaffordability.",
            C["crash"],
        ),

        # Chart 1 — RVS choropleth
        card([
            html.Div("Patchwork Recovery: Geography Decided the Clock",
                     style={"fontSize":"16px","fontWeight":"700","marginBottom":"2px"}),
            html.Div("Recovery speed varied sharply by state, creating early winners and long-delay markets.",
                     style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px","color":"#1A1A1A"}),
            G(ch.fig_recovery_map_discrete(df_map), "ch5-map"),
            ann("Geography determined survival speed. Oil-state and sun-belt markets bounced back in 1–2 years. "
                "Sand states — Nevada, Arizona, Florida — took 3–7 years.",
                "RVS = years from trough (2009) to first year originations exceed 80% of 2007 baseline. "
                "Computed from rvs_full.parquet.",
                mode),
            src("HMDA LAR 2007-2017 (CFPB)"),
        ]),

        # Chart 2 — Bank vs nonbank slope
        card([
            html.Div("The Great Handover: Banks Retreated, Nonbanks Took Control",
                     style={"fontSize":"16px","fontWeight":"700","marginBottom":"2px"}),
            html.Div("Post-crisis credit returned through a different channel: nonbanks became the dominant origination engine.",
                     style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px","color":"#1A1A1A"}),
            G(ch.fig_bank_nonbank_slope(df_bn), "ch5-bnslope"),
            ann("Banks went from 70% to 31% of originations. Nonbanks filled the void — "
                "but they operate without deposit insurance, without Fed access, and with thinner capital buffers.",
                "Structural handoff: agency_code=7 (HUD-supervised nonbanks) vs all others. "
                "Crossover occurs 2013–2014. By 2017 nonbanks originate 2 in every 3 mortgages.",
                mode),
            src("HMDA LAR 2007-2017 (CFPB)"),
        ]),

        # Chart 3 — Recovery vs affordability scatter
        card([
            html.Div("Recovered but Priced Out: Speed Came with an Affordability Bill",
                     style={"fontSize":"16px","fontWeight":"700","marginBottom":"2px"}),
            html.Div("The fastest-recovering states often ended with higher leverage requirements for buyers.",
                     style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px","color":"#1A1A1A"}),
            G(ch.fig_recovery_vs_affordability(df_ra), "ch5-recov-afford"),
            ann("States that recovered fastest — CA, CO, TX — ended up with median LTI above 3x by 2017. "
                "Recovery and affordability moved in opposite directions.",
                f"Scatter: RVS years (x) vs median LTI 2017 (y). "
                f"Fast states (≤2yr): avg LTI {fast_lti:.2f}x. "
                f"Slow states (≥5yr): avg LTI {slow_lti:.2f}x. n={len(df_ra)} states.",
                mode),
            src("HMDA LAR 2007-2017 (CFPB)"),
        ]),
        card([
            html.Div("Why Some States Recovered Faster",
                     style={"fontSize":"16px","fontWeight":"700","marginBottom":"2px"}),
            html.Div("Recovery speed depended on demand, credit return, and structural frictions",
                     style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px","color":"#1A1A1A"}),
            G(ch.fig_ch5_recovery_drivers(df_drv), "ch5-recovery-drivers"),
            ann("Stronger job recovery generally led to faster housing recovery—unless blocked by structural frictions.",
                "Quadrants use median job growth and median recovery time; top is faster recovery, and color runs green (fast) to red (slow).",
                mode),
            src("BLS LAUS API", "FHFA State HPI", "HMDA LAR 2007-2017 (CFPB)"),
        ]),
    ])

def p6(mode):
    pack = _ch6_pack()
    df_dr = pack["df_dr"]
    df_age = pack["df_age"]
    df_ho = pack["df_ho"]
    df_col = pack["df_col"]
    df_loan = pack["df_loan"]
    post_w = pack["post_w"]
    post_b = pack["post_b"]
    gap_pp = pack["gap_pp"]
    ratio = pack["ratio"]
    h2007 = pack["h2007"]
    h2017 = pack["h2017"]

    return html.Div([
        chapter_title(6, "Who Got Left Behind", "The recovery was K-shaped: access improved for some and stayed constrained for others."),
        kpi_row([
            kpi(f"{post_b:.0%}", "Post-2012 denial rate (<50K, Black)", C["crash"]),
            kpi(f"{post_w:.0%}", "Post-2012 denial rate (<50K, White)", C["muted"]),
            kpi(f"{ratio:.1f}x", "Denial ratio (Black/White)", C["warning"], f"+{gap_pp:.0f} pp gap"),
            kpi(f"{h2007:.1f}% -> {h2017:.1f}%", "Homeownership rate (2007->2017)", C["recovery"]),
        ]),
        insight_chip("Persistently high denial rates meant fewer households could transition into homeownership.", C["crash"]),
        card([
            html.Div("The Generational Split: Older Owners Held Ground, Younger Buyers Slipped",
                     style={"fontSize":"16px","fontWeight":"700","marginBottom":"2px"}),
            html.Div("Homeownership gains remained concentrated among older owners during the recovery era", style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px","color":"#1A1A1A"}),
            G(ch.fig_ch6_generation_split(df_age), "ch6-gen-gap", keep_legend=True),
            ann(
                "The age gap widened because younger household ownership fell more sharply than older-owner ownership.",
                "Two-point slopegraph: age 25-34 (young proxy) vs 55-64 (boomer proxy).",
                mode,
            ),
            src("FRED / BLS Consumer Expenditure Survey age homeownership series"),
        ]),
        card([
            html.Div("The Funnel Leak: Same Economy, Unequal Passage to Ownership",
                     style={"fontSize":"16px","fontWeight":"700","marginBottom":"2px"}),
            html.Div("At the same period endpoint, low-income applicants lose a larger share before origination.",
                     style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px","color":"#1A1A1A"}),
            G(ch.fig_ch6_funnel_compare(df_dr, df_loan, 2017), "ch6-sankey"),
            ann(
                "The leakage is structural: lower-income households convert from application to origination at much lower rates.",
                "Conversion rate is shown directly on each funnel to quantify the disparity.",
                mode,
            ),
        ]),
        card([
            html.Div("THE DECOUPLING: How Low Rates Fueled a Wealth Boom for Owners while Creating a 'Nation of Renters'", style={"fontSize":"16px","fontWeight":"700","marginBottom":"2px"}),
            html.Div("Falling rates fueled refinancing while new buyer purchasing lagged, creating a widening opportunity gap.", style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px","color":"#1A1A1A"}),
            G(ch.fig_ch6_great_decoupling(df_ho, df_col), "ch6-decoupling"),
            ann(
                "Refinancing drove the recovery peak - purchase activity followed later but did not lead it.",
                "Both lines are indexed to 2007=100 to make recovery divergence directly comparable.",
                mode,
            ),
            src("Census homeownership series", "HMDA aggregates"),
        ]),
    ])

def p7(mode):
    df_lend = _df_lender_bubble()
    df_race = _df_origination_share_by_race()
    df_pr = _df_purchase_refi()
    df_age = _df_homeownership_age()
    df_dr = _df_denial_rates()
    by = df_lend.groupby(["year", "lender_type"], as_index=False)["originations"].sum() if not df_lend.empty else None
    nonbank_2007 = nonbank_2017 = 0.0
    crossover_year = None
    if by is not None and not by.empty:
        piv = by.pivot(index="year", columns="lender_type", values="originations").fillna(0).reset_index().sort_values("year")
        if "Bank" not in piv.columns:
            piv["Bank"] = 0
        if "Nonbank" not in piv.columns:
            piv["Nonbank"] = 0
        total = (piv["Bank"] + piv["Nonbank"]).replace(0, 1)
        piv["nonbank_share"] = piv["Nonbank"] / total
        if len(piv[piv["year"] == 2007]):
            nonbank_2007 = float(piv[piv["year"] == 2007]["nonbank_share"].iloc[0])
        if len(piv[piv["year"] == 2017]):
            nonbank_2017 = float(piv[piv["year"] == 2017]["nonbank_share"].iloc[0])
        over = piv[piv["Nonbank"] >= piv["Bank"]]
        if not over.empty:
            crossover_year = int(over["year"].min())

    nonbank_gain_pp = (nonbank_2017 - nonbank_2007) * 100.0
    black_2007 = black_2017 = 0.0
    if not df_race.empty:
        b07 = df_race[(df_race["year"] == 2007) & (df_race["race"] == "Black / African American")]
        b17 = df_race[(df_race["year"] == 2017) & (df_race["race"] == "Black / African American")]
        if len(b07):
            black_2007 = float(b07["share"].iloc[0])
        if len(b17):
            black_2017 = float(b17["share"].iloc[0])

    # Synthesis metrics for one-chart "who won" scorecard (directional, chapter-backed proxies).
    refi_peak_share = 0.0
    if not df_pr.empty and "purchase_pct" in df_pr.columns:
        tmp = df_pr.copy()
        tmp["refi_share"] = 1.0 - tmp["purchase_pct"]
        refi_peak_share = float(tmp["refi_share"].max()) if len(tmp) else 0.0

    gap_widen_pp = 0.0
    if not df_age.empty and {"year", "home_25_34", "home_55_64"}.issubset(set(df_age.columns)):
        a07 = df_age[df_age["year"] == 2007]
        a17 = df_age[df_age["year"] == 2017]
        if len(a07) and len(a17):
            g07 = float(a07["home_55_64"].iloc[0] - a07["home_25_34"].iloc[0])
            g17 = float(a17["home_55_64"].iloc[0] - a17["home_25_34"].iloc[0])
            gap_widen_pp = g17 - g07

    denial_ratio = 1.0
    if not df_dr.empty:
        wl = df_dr[(df_dr["race"] == "White") & (df_dr["income_band"] == "<50K") & (df_dr["year"] >= 2012)]
        bl = df_dr[(df_dr["race"] == "Black / African American") & (df_dr["income_band"] == "<50K") & (df_dr["year"] >= 2012)]
        post_w = float(wl["denial_rate"].mean()) if len(wl) else 0.0
        post_b = float(bl["denial_rate"].mean()) if len(bl) else 0.0
        denial_ratio = (post_b / post_w) if post_w > 0 else 1.0

    def _clip(v, lo=0.0, hi=100.0):
        return max(lo, min(hi, float(v)))

    nonbank_power = _clip((nonbank_gain_pp / 40.0) * 100.0)
    refi_boost = _clip(((refi_peak_share - 0.45) / 0.30) * 100.0)
    exclusion_pressure = _clip(((denial_ratio - 1.0) / 1.0) * 100.0)

    df_winners = pd.DataFrame([
        {
            "group": "Nonbank Lenders",
            "market_power": nonbank_power,
            "financing_edge": 74,
            "asset_capture": 34,
            "regulatory_fit": 86,
        },
        {
            "group": "Existing Homeowners",
            "market_power": 22,
            "financing_edge": refi_boost,
            "asset_capture": _clip(68 + gap_widen_pp * 6.0),
            "regulatory_fit": 64,
        },
        {
            "group": "Institutional Investors",
            "market_power": 78,
            "financing_edge": 63,
            "asset_capture": 90,
            "regulatory_fit": 58,
        },
        {
            "group": "QM-Compliant Borrowers",
            "market_power": 18,
            "financing_edge": 56,
            "asset_capture": 42,
            "regulatory_fit": _clip(82 + exclusion_pressure * 0.15),
        },
        {
            "group": "Big Banks",
            "market_power": _clip(52 + (nonbank_2017 * 30.0)),
            "financing_edge": 50,
            "asset_capture": 36,
            "regulatory_fit": 82,
        },
    ])

    return html.Div([
        chapter_title(7, "The New Rules: Who Won the Crisis", "Systemic risk was redistributed, not resolved."),
        insight_chip(f"So what: Nonbank share rose {nonbank_gain_pp:+.0f} percentage points from 2007 to 2017.", C["nonbank"]),
        kpi_row([
            kpi(f"{nonbank_2007:.0%} -> {nonbank_2017:.0%}", "Nonbank share (2007->2017)", C["nonbank"]),
            kpi(str(crossover_year) if crossover_year else "N/A", "First nonbank>=bank year", C["warning"]),
            kpi(f"{black_2007:.1%} -> {black_2017:.1%}", "Black origination share", C["crash"], "Participation share"),
        ], center=True),
        card([
            html.Div("Who Actually Won the Crisis", style={"fontSize":FS_HEAD,"fontWeight":"700","marginBottom":"2px"}),
            html.Div("Directional composite (not causal): market power, financing edge, asset capture, and regulatory fit", style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px","color":"#1A1A1A"}),
            G(ch.fig_ch7_winner_redistribution(df_winners), "ch7-winner-onechart", keep_legend=True),
            ann(
                "Post-crisis protections reduced systemic risk partly by favoring institutions and borrower profiles already closest to safety.",
                "Each component is normalized to 0-25, summing to a 0-100 composite. Use this as a narrative synthesis, not a causal estimate.",
                mode,
            ),
            src("HMDA 2007-2017", "BLS/FRED age homeownership"),
        ]),
        card([
            html.Div("The Great Handover: banks to shadow banks", style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px"}),
            G(ch.fig_ch7_handover_race(df_lend), "ch7-handover"),
            ann(
                "Watch the handover: banks dominate in 2007, then nonbanks overtake through the post-crisis rule regime.",
                "This is institutional redistribution of market power, not a neutral recovery.",
                mode,
            ),
        ]),
        html.Div([
            html.P([
                html.Span("The subprime crisis ", style={"fontWeight": "500"}),
                "wasn't caused by subprime borrowers.  ",
                html.Span("The recovery ", style={"fontWeight": "500"}),
                "didn't restore the people it was supposed to help.  ",
                html.Span("The risk ", style={"fontWeight": "500"}),
                "didn't disappear. It migrated into a less-visible part of the system.",
            ], style={"fontSize": "16px", "color": C["text"], "lineHeight": "1.8", "textAlign": "center", "maxWidth": "700px", "margin": "0 auto", "fontStyle": "italic"})
        ], style={"padding": "28px", "borderRadius": "12px", "marginBottom": "16px", "background": C["surface"], "border": f"0.5px solid {C['border']}"}),
    ])

def p8(mode):
    pack = _ch8_pack()
    top_share_2007 = pack["top_share_2007"]
    decoupling_gap_idx = pack["decoupling_gap_idx"]
    denial_gap_pp = pack["denial_gap_pp"]
    score = pack["score"]

    return html.Div([
        chapter_title(8, "Lessons for the Next Cycle", "Build resilience without rebuilding exclusion."),
        kpi_row([
            kpi(f"{top_share_2007:.0%}", "Top channel share (2007)", C["warning"], "Higher concentration = higher systemic fragility"),
            kpi(f"{decoupling_gap_idx:.1f}", "Peak refi-purchase gap index", C["crash"], "Largest divergence from 2007-indexed activity"),
            kpi(f"{denial_gap_pp:.1f} pp", "Post-2012 denial gap (<50K)", C["crash"], "Black minus White denial rate"),
        ]),
        insight_chip("A safer system needs three guardrails at once: diversified credit channels, a narrower owner-vs-buyer divergence, and reduced same-income denial gaps.", C["warning"]),
        card([
            html.Div("The Next-Cycle Scorecard: What to Protect, What to Repair", style={"fontSize":"16px","fontWeight":"700","marginBottom":"2px"}),
            html.Div("Each KPI is converted to % of target (100 = meets guardrail) for apples-to-apples comparison", style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px","color":"#1A1A1A"}),
            G(ch.fig_ch8_lessons_scorecard(score), "ch8-scorecard", keep_legend=True),
            ann(
                "The risk is not one number; it is a combination of concentration, weak entry, owner-biased recovery, and persistent disparity.",
                "Targets are directional guardrails for policy design, not fixed thresholds from regulation.",
                mode,
            ),
        ]),
        card([
            html.Div("Four Lessons from the Crisis", style={"fontSize":"16px","fontWeight":"700","marginBottom":"10px"}),
            html.Div([
                html.Div([
                    html.Div("1) Do not rebuild a monoculture.", style={"fontWeight":"700","marginBottom":"4px"}),
                    html.Div("If one channel dominates origination, a single funding shock can freeze the entire market."),
                ], style={"marginBottom":"10px"}),
                html.Div([
                    html.Div("2) Track access, not just volume.", style={"fontWeight":"700","marginBottom":"4px"}),
                    html.Div("Refinance waves can inflate activity while first-entry ownership remains constrained."),
                ], style={"marginBottom":"10px"}),
                html.Div([
                    html.Div("3) Cheap money is not equal opportunity.", style={"fontWeight":"700","marginBottom":"4px"}),
                    html.Div("Falling rates help incumbents most unless entry constraints are addressed directly."),
                ], style={"marginBottom":"10px"}),
                html.Div([
                    html.Div("4) Recovery quality must be distribution-aware.", style={"fontWeight":"700","marginBottom":"4px"}),
                    html.Div("A durable recovery narrows same-income denial gaps instead of simply shifting risk channels."),
                ]),
            ], style={"fontSize":"14px","color":C["text"],"lineHeight":"1.5"}),
        ]),
    ])

def p9(mode):
    cache_sig = wb.global_shockwave_cache_signature()
    pack = _ch9_pack(cache_sig)
    df_global = pack["df_global"]
    source = pack["source"]
    worst_gdp = pack["worst_gdp"]
    largest_jobs = pack["largest_jobs"]
    export_worst = pack["export_worst"]

    return html.Div([
        chapter_title(9, "The Global Shockwave", "How the 2008 crisis propagated across economies through different channels."),
        data_note(_global_shockwave_source_note(source)),
        kpi_row([
            kpi(_fmt_pct(worst_gdp["gdp_growth_2009"]) if worst_gdp is not None else "n/a", f"Deepest GDP hit: {worst_gdp['country']}" if worst_gdp is not None else "Deepest GDP hit", C["crash"], "2009 growth rate"),
            kpi(_fmt_pp(largest_jobs["unemployment_change_peak"]) if largest_jobs is not None else "n/a", f"Largest labor shock: {largest_jobs['country']}" if largest_jobs is not None else "Largest labor shock", C["warning"], "Rise from 2007 to peak"),
            kpi(_fmt_pct(export_worst["export_growth_2009"]) if export_worst is not None else "n/a", f"Worst export collapse: {export_worst['country']}" if export_worst is not None else "Worst export collapse", C["govt"], "2009 export growth"),
        ]),
        insight_chip("The same crisis moved through different channels: housing and finance in the U.S., banking stress in Iceland, debt stress in Greece, and trade shocks in export-linked economies.", C["govt"]),
        card([
            html.Div("Country snapshot (2007-2011)", style={"fontSize":"13px","fontWeight":"500","marginBottom":"10px"}),
            html.Div(_global_shockwave_table(df_global), style={"overflowX":"auto"}),
            html.Div("Note: Some country-year series may be missing from the World Bank pull; the table leaves those cells as n/a.", style={"fontSize":"11px","color":C["muted"],"marginTop":"10px"}),
        ]),
        html.Div([
            html.Div([
                card([
                    html.Div("Output shock vs trade shock", style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
                    G(ch.fig_ch9_growth_exports(df_global), "ch9-growth-exports"),
                ], mb="0"),
            ], style={"flex":"1.2","minWidth":"360px"}),
            html.Div([
                card([
                    html.Div("Where labor-market pain peaked", style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
                    G(ch.fig_ch9_unemployment_shock(df_global), "ch9-unemployment"),
                ], mb="0"),
            ], style={"flex":"0.9","minWidth":"320px"}),
        ], style={"display":"flex","gap":"12px","flexWrap":"wrap","alignItems":"stretch"}),
        card([
            html.Div("Final takeaway", style={"fontSize":"11px","fontWeight":"700","letterSpacing":"0.06em","textTransform":"uppercase","color":C["warning"],"marginBottom":"8px"}),
            html.Div(
                "The crisis was global, but not uniform. Financially concentrated economies were hit early, trade-linked economies absorbed external demand shocks, and labor-market scars lasted beyond the initial panic.",
                style={"fontSize":"15px","fontWeight":"500","fontStyle":"italic","lineHeight":"1.6","color":C["text"]},
            ),
        ], pad="18px 22px"),
    ])

def export_print_view():
    sections = [
        p1("civilian"),
        p2("civilian"),
        p3("civilian"),
        p4("civilian"),
        p5("civilian"),
        p6("civilian"),
        p7("civilian"),
        p8("civilian"),
        p9("civilian"),
    ]

    wrappers = []
    for idx, section in enumerate(sections, start=1):
        wrappers.append(html.Div(
            section,
            style={
                "background":"white",
                "border":"0.5px solid rgba(20,20,20,0.12)",
                "borderRadius":"16px",
                "padding":"24px 28px",
                "marginBottom":"20px",
                "pageBreakAfter":"always" if idx < len(sections) else "auto",
                "breakAfter":"page" if idx < len(sections) else "auto",
                "boxShadow":"0 10px 24px rgba(20,20,20,0.04)",
            },
        ))

    return html.Div([
        html.Div([
            html.Div("Export All 9 Chapters", style={"fontSize":"20px","fontWeight":"700","fontFamily":FONT_SERIF,"marginBottom":"6px"}),
            html.Div("Use the button below, then choose Save as PDF in the browser print dialog. The export page is optimized for one continuous local PDF.", style={"fontSize":"13px","color":C["muted"],"lineHeight":"1.6","marginBottom":"14px"}),
            html.Div([
                html.Button("Print / Save as PDF", id="print-pdf-btn", n_clicks=0, style={
                    "padding":"9px 14px","borderRadius":"10px","fontSize":"13px","fontWeight":"700",
                    "border":"0.5px solid rgba(15,90,122,0.35)","background":C["civilian"],"color":"white",
                    "cursor":"pointer",
                }),
                dcc.Link("Back to app", href="/chapter/1", style={
                    "padding":"9px 14px","borderRadius":"10px","fontSize":"13px","fontWeight":"600",
                    "textDecoration":"none","border":f"0.5px solid {C['border']}",
                    "color":C["text"],"background":"white",
                }),
            ], style={"display":"flex","gap":"10px","flexWrap":"wrap"}),
            html.Div(id="print-pdf-dummy", style={"display":"none"}),
        ], style={
            "background":"rgba(255,255,255,0.92)",
            "border":"0.5px solid rgba(20,20,20,0.12)",
            "borderRadius":"16px",
            "padding":"20px 24px",
            "marginBottom":"18px",
            "position":"sticky",
            "top":"10px",
            "zIndex":"10",
        }),
        *wrappers,
    ], style={"maxWidth":"1120px","margin":"0 auto","padding":"20px 24px 36px","fontFamily":FONT,"color":C["text"]})


app.layout = html.Div([
    dcc.Location(id="url",refresh=False),
    html.Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2-family=Libre+Baskerville:wght@700&family=Source+Sans+3:wght@400;500;600;700&display=swap",
    ),
    html.Div(id="nav", children=navbar(1)),
    html.Div(id="page",style={
        "maxWidth":"1120px","margin":"0 auto",
        "padding":"26px 24px 48px","fontFamily":FONT,"color":C["text"],
    }),
], style={"background":C["surface"],"minHeight":"100vh"})


PAGE_MAP = {
    "/chapter/1":(p1,1),"/chapter/2":(p2,2),"/chapter/3":(p3,3),
    "/chapter/4":(p4,4),"/chapter/5":(p5,5),"/chapter/6":(p6,6),"/chapter/7":(p7,7),"/chapter/8":(p8,8),"/chapter/9":(p9,9),
}

@lru_cache(maxsize=16)
def _render_page_cached(path: str):
    if path == "/export/print":
        return export_print_view()
    fn, _ = PAGE_MAP.get(path,(p1,1))
    return fn("civilian")

def _render_page(path: str):
    # Page-level cache avoids rebuilding the same chart tree on repeated navigation.
    return _render_page_cached(path)

@app.callback(Output("page","children"), Input("url","pathname"))
def route(path):
    try:
        return _render_page(path or "/chapter/1")
    except Exception:
        err = traceback.format_exc(limit=8)
        print(err)
        return card([
            html.Div("Render error", style={"fontSize":"14px","fontWeight":"600","marginBottom":"8px","color":C["crash"]}),
            html.Pre(err, style={"whiteSpace":"pre-wrap","fontSize":"11px","color":C["text"],"margin":"0"}),
        ], pad="18px 20px")

@app.callback(Output("nav","children"), Input("url","pathname"))
def render_nav(path):
    if path == "/export/print":
        return html.Div()
    _, num = PAGE_MAP.get(path, (p1, 1))
    return navbar(num)

app.clientside_callback(
    """
    function(n_clicks) {
        if (!n_clicks) { return ""; }
        window.print();
        return "";
    }
    """,
    Output("print-pdf-dummy", "children"),
    Input("print-pdf-btn", "n_clicks"),
    prevent_initial_call=True,
)


if __name__ == "__main__":
    print(f"Mode: {'REAL' if dl.USE_REAL_DATA else 'MOCK'} DATA")
    print("Open: http://127.0.0.1:8050")
    app.run(debug=False, port=8050)
