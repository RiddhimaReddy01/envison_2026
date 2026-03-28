"""
app.py — Envision Hackathon 2026  (FINAL)
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

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

import data_loader as dl
import charts as ch

C = {
    "bg":"#FAFAF7","surface":"#F1F3F2","border":"rgba(17,24,39,0.14)",
    "text":"#1F252D","muted":"#5F6976","crash":"#C7252A",
    "recovery":"#1E6B4A","govt":"#0B4F8A","veteran":"#4F4B7A",
    "civilian":"#0F5A7A","warning":"#B36A00","nonbank":"#A84A34",
}
FONT  = "'Source Sans 3', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
FONT_SERIF = "'Merriweather', Georgia, 'Times New Roman', serif"
YEARS = list(range(2007,2018))

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
def _df_msa_scissor():
    return dl.msa_scissor().to_pandas()

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
def _df_lender_bubble():
    return dl.lender_bubble().to_pandas()

def card(children, pad="24px 28px", mb="16px"):
    return html.Div(children, className="card-soft", style={
        "background":C["bg"],"border":f"0.5px solid {C['border']}",
        "borderRadius":"12px","padding":pad,"marginBottom":mb,
    })

def kpi(number, label, color=None, note=None):
    return html.Div([
        html.Div(number, style={"fontSize":"24px","fontWeight":"500",
                                "lineHeight":"1.1","color":color or C["text"]}),
        html.Div(label,  style={"fontSize":"12px","color":C["muted"],"marginTop":"4px"}),
        html.Div(note,   style={"fontSize":"10px","color":C["muted"],"marginTop":"2px",
                                "fontStyle":"italic"}) if note else None,
    ], className="kpi-soft", style={"background":C["surface"],"borderRadius":"8px",
              "padding":"14px 16px","flex":"1","minWidth":"130px"})

def kpi_row(items):
    return html.Div(items, style={"display":"flex","gap":"10px",
                                  "flexWrap":"wrap","marginBottom":"20px"})

def chapter_title(num, title, subtitle):
    bg = {1:"#FCEBEB",2:"#FAEEDA",3:"#E1F5EE",4:"#E6F1FB",
          5:"#EEEDFE",6:"#FAECE7",7:"#EAF3DE"}
    fc = {1:"#A32D2D",2:"#854F0B",3:"#0F6E56",4:"#185FA5",
          5:"#534AB7", 6:"#993C1D",7:"#3B6D11"}
    return html.Div([
        html.Div([
            html.Span(str(num), style={
                "display":"inline-flex","alignItems":"center","justifyContent":"center",
                "width":"28px","height":"28px","borderRadius":"50%",
                "background":bg.get(num,C["surface"]),"color":fc.get(num,C["text"]),
                "fontSize":"12px","fontWeight":"500","marginRight":"10px","flexShrink":"0",
            }),
            html.Span(title, style={"fontSize":"21px","fontWeight":"700","fontFamily":FONT_SERIF}),
        ], style={"display":"flex","alignItems":"center","marginBottom":"5px"}),
        html.P(subtitle, style={"fontSize":"13px","color":C["muted"],"margin":"0 0 20px 38px"}),
    ])

def ann(civilian, veteran, mode):
    if mode == "veteran":
        return html.Div([
            html.Span("Veteran  ", style={"fontSize":"10px","fontWeight":"500",
                "letterSpacing":"0.07em","textTransform":"uppercase","color":C["veteran"]}),
            html.Span(veteran, style={"fontSize":"13px","color":C["muted"]}),
        ], style={"padding":"10px 14px","borderRadius":"8px","marginTop":"12px",
                  "background":"#EEEDFE08","border":"0.5px solid #534AB740"})
    return html.Div(civilian, style={
        "padding":"10px 14px","borderRadius":"8px","marginTop":"12px",
        "fontSize":"14px","fontWeight":"500","color":C["civilian"],
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
    return html.Div(text, style={
        "fontSize":"12px","fontWeight":"600","color":color or C["text"],
        "padding":"8px 12px","borderRadius":"999px","display":"inline-block",
        "background":"#F4F1E8","border":"0.5px solid rgba(17,24,39,0.16)",
        "marginBottom":"14px",
    })

def G(fig, gid=""):
    return dcc.Graph(id=gid if gid else {"type":"graph","idx":gid},
                     figure=fig, animate=False,
                     config={"displayModeBar":False,"responsive":True},
                     style={"width":"100%"})

CHAPTERS = [(1,"The Bet"),(2,"The Crash"),(3,"The Rescue"),
            (4,"Fake Recovery"),(5,"Who Survived"),(6,"Left Behind"),(7,"New Rules")]

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
            html.Span("View:",style={"fontSize":"11px","color":C["muted"],"marginRight":"8px"}),
            dcc.RadioItems(id="mode",
                options=[{"label":"Newcomer","value":"civilian"},
                         {"label":"Veteran","value":"veteran"}],
                value="civilian", inline=True,
                inputStyle={"marginRight":"4px","cursor":"pointer"},
                labelStyle={"marginRight":"14px","cursor":"pointer",
                            "fontSize":"12px","userSelect":"none"}),
        ], style={"display":"flex","alignItems":"center","flex":"0 0 auto"}),
    ], style={"display":"flex","alignItems":"center","gap":"16px","padding":"10px 28px",
              "background":C["bg"],"borderBottom":f"0.5px solid {C['border']}",
              "position":"sticky","top":"0","zIndex":"100","fontFamily":FONT})

# ── Pages ──────────────────────────────────────────────

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
    pre_2007 = collapse[collapse["year"] == 2007]["origination_rate"]
    pre_2008 = collapse[collapse["year"] == 2008]["origination_rate"]
    pre_msg = "Approval trend before the break is flat in the current scoped series."
    vet_msg = "If your denial patch is loaded, this panel will show pre-crisis weakening directly."
    if len(pre_2007) and len(pre_2008) and float(pre_2007.iloc[0]) > 0:
        delta = (float(pre_2008.iloc[0]) / float(pre_2007.iloc[0])) - 1.0
        if delta < -0.005:
            pre_msg = f"Approval rates were already softening before the break ({delta:.1%} vs 2007)."
            vet_msg = "Pre-crisis approval drift is visible directly from the yearly application-originations ratio."
        elif delta > 0.005:
            pre_msg = f"Approval rates were rising pre-break in this series ({delta:.1%} vs 2007)."
            vet_msg = "This panel reflects your current scoped denominator and action-taken coverage."

    return html.Div([
        chapter_title(1, "Before It Broke", "Scale was visible. Fragility was hidden in plain sight."),
        kpi_row([
            kpi(f"{approval_2007:.0%}", "Approval rate in 2007", C["govt"], "Originations / applications"),
            kpi(conv_2007_plus, "Conventional share in 2007", C["warning"], "Private-market dominance"),
        ]),
        insight_chip(f"So what: In 2007, the largest channel exceeded the runner-up by {conc_gap_pp:.0f} percentage points.", C["warning"]),
        card([
            html.Div("Credit Access (Primary Signal)", style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px"}),
            G(ch.fig_ch1_scale_speed(collapse), "ch1-access"),
            ann(
                pre_msg,
                vet_msg,
                mode,
            )
        ]),
        html.Div([
            html.Div([
                card([
                    html.Div("Market Structure", style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px"}),
                    G(ch.fig_ch1_risk_mix(risk), "ch1-structure"),
                    ann(
                        "This was a monoculture: one dominant credit channel with no serious backup. Concentration, not just size, made the system brittle.",
                        "The composition is direct from HMDA loan-type shares by year; fragility here is structural concentration.",
                        mode,
                    ),
                    html.Div("Semantic Legend For Market Structure", style={"fontSize": "12px", "fontWeight": "600", "margin": "10px 0 6px"}),
                    html.Table([
                        html.Thead(html.Tr([
                            html.Th("Loan Type", style={"textAlign": "left", "fontSize": "10px", "color": C["muted"], "paddingBottom": "6px", "paddingRight": "8px"}),
                            html.Th("Economic Role", style={"textAlign": "left", "fontSize": "10px", "color": C["muted"], "paddingBottom": "6px", "paddingRight": "8px"}),
                            html.Th("System Implication", style={"textAlign": "left", "fontSize": "10px", "color": C["muted"], "paddingBottom": "6px"}),
                        ])),
                        html.Tbody([
                            html.Tr([html.Td("Conventional"), html.Td("Private bank lending"), html.Td("Core system, high exposure")]),
                            html.Tr([html.Td("FHA"), html.Td("Government-insured"), html.Td("Safety net")]),
                            html.Tr([html.Td("VA"), html.Td("Targeted lending"), html.Td("Policy support")]),
                            html.Tr([html.Td("FSA/RHS"), html.Td("Rural programs"), html.Td("Minimal systemic role")]),
                        ]),
                    ], style={
                        "width": "100%",
                        "fontSize": "10.5px",
                        "lineHeight": "1.3",
                        "tableLayout": "fixed",
                        "borderCollapse": "separate",
                        "borderSpacing": "0 6px",
                    }),
                ])
            ], style={"flex": "2", "minWidth": "360px"}),
            html.Div([
                card([
                    html.Div("2007 Snapshot", style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px"}),
                    G(ch.fig_ch1_snapshot_pie(risk), "ch1-snapshot"),
                ], pad="18px 18px")
            ], style={"flex": "1.1", "minWidth": "260px"}),
        ], style={"display": "flex", "gap": "12px", "flexWrap": "wrap"}),
        card([
            html.Div(
                "The key pre-crisis fact was concentration: one private channel carried almost all mortgage risk.",
                style={"fontSize": "15px", "fontWeight": "500", "fontStyle": "italic", "textAlign": "center"},
            )
        ], pad="16px 22px"),
    ])

def p2(mode):
    df = _df_collapse()
    apps_2008 = int(df[df["year"] == 2008]["applications"].iloc[0]) if len(df[df["year"] == 2008]) else 0
    gap_2011 = int((df[df["year"] == 2011]["applications"].iloc[0] - df[df["year"] == 2011]["originations"].iloc[0])) if len(df[df["year"] == 2011]) else 0
    rate_2011 = float(df[df["year"] == 2011]["origination_rate"].iloc[0]) if len(df[df["year"] == 2011]) else 0.0
    rate_2007 = float(df[df["year"] == 2007]["origination_rate"].iloc[0]) if len(df[df["year"] == 2007]) else 0.0
    rate_change = ((rate_2011 / rate_2007) - 1.0) if rate_2007 else 0.0
    stat_note = f"Origination rate {rate_2007:.0%}->{rate_2011:.0%} (2007->2011)." if rate_2007 else "Origination rate trend unavailable."
    apps_2011 = int(df[df["year"] == 2011]["applications"].iloc[0]) if len(df[df["year"] == 2011]) else 0
    gap_share_2011 = (gap_2011 / apps_2011) if apps_2011 else 0.0

    return html.Div([
        chapter_title(2,"The Day the Machine Stopped","Demand persisted, but approval capacity broke."),
        kpi_row([kpi(f"{apps_2008:,.0f}","Applications in 2008",C["warning"],"Demand stayed present"),
                 kpi(f"{gap_2011:,.0f}","Credit gap in 2011",C["crash"],"Applications - originations"),
                 kpi(f"{rate_2011:.0%}","Approval rate in 2011",C["crash"],"Originations / applications")]),
        insight_chip(f"So what: In 2011, about {gap_share_2011:.0%} of applications did not convert into originations.", C["crash"]),
        card([G(ch.fig_collapse(df),"collapse"),
              ann("The shock was institutional triage: lenders rationed approvals faster than households reduced demand.",
                  f"{stat_note} The widening gap tracks credit rationing, not a disappearance of would-be borrowers.",
                  mode),
              src("Federal Reserve Bulletin 2010","CFPB HMDA Data Point")]),
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
        card([
            html.Div(
                "Recovery was a handoff: mortgage risk migrated from private underwriting to publicly backed channels.",
                style={"fontSize":"15px","fontWeight":"500","fontStyle":"italic","textAlign":"center"},
            )
        ], pad="16px 22px"),
    ])

def p4(mode):
    df_lti = _df_lti_sample()
    pr = _df_purchase_refi()
    if not df_lti.empty:
        d = df_lti.copy()
        d["group"] = d["income_band"].map({
            "<50K": "Low income (<50K)",
            "50-80K": "Middle income (50-100K)",
            "80-100K": "Middle income (50-100K)",
            "100-150K": "Higher income (100K+)",
            "150K+": "Higher income (100K+)",
        })
        d = d.dropna(subset=["group", "lti_ratio"])
    else:
        d = df_lti

    median_lti = float(d["lti_ratio"].median()) if not d.empty else 0.0
    mid_peak = float(d[d["group"] == "Middle income (50-100K)"]["lti_ratio"].max()) if not d.empty and len(d[d["group"] == "Middle income (50-100K)"]) else 0.0
    pct_above3 = float((d["lti_ratio"] > 3).mean()) if not d.empty else 0.0
    if not d.empty:
        x = d.copy()
        x["gt3"] = x["lti_ratio"] > 3
        contrib = x.groupby("group")["gt3"].sum()
        top_group = str(contrib.idxmax()) if len(contrib) else "Middle income (50-100K)"
        top_share = float(contrib.max() / contrib.sum()) if len(contrib) and contrib.sum() else 0.0
        middle_share = float(x[x["group"] == "Middle income (50-100K)"]["gt3"].sum() / x["gt3"].sum()) if x["gt3"].sum() else 0.0
    else:
        top_group = "Middle income (50-100K)"
        top_share = 0.0
        middle_share = 0.0

    return html.Div([
        chapter_title(4,"A 'Fake' Recovery","High leverage was not confined to the poorest borrowers."),
        kpi_row([kpi(f"{median_lti:.1f}x","Median LTI (sample)",C["warning"]),
                 kpi(f"{mid_peak:.1f}x","Middle-income peak LTI",C["crash"]),
                 kpi(f"{pct_above3:.0%}","Borrowers above 3x threshold",C["crash"]),
                 kpi(f"{top_share:.0%}",f"Largest >3x share: {top_group}",C["recovery"],"Share of all high-leverage loans")]),
        insight_chip(f"So what: Middle-income borrowers account for {middle_share:.0%} of all loans above 3x income in this sample.", C["crash"]),
        
        card([html.Div("Recovery for whom? Refinance replaced purchase",style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_purchase_refi_share(pr),"ch4-purchase-refi")]),
        
        card([html.Div("Who carried the highest leverage?",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_ch4_lti_income_groups(df_lti),"ch4-lti-groups"),
              ann("The uncomfortable finding: middle-income borrowers were not insulated; they carried a large block of >3x leverage.",
                  "This separates intensity from volume: high ratios exist broadly, but the middle contributes more high-leverage mass.",
                  mode),
              src("NBER WP 23740","MIT Sloan / Schoar")]),
        card([html.Div("How widespread was high leverage?",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_ch4_above_3x(df_lti),"ch4-above3")]),
        card([
            html.Div(
                "Leverage risk was distributed across the ladder, with middle-income households central to the exposure base.",
                style={"fontSize":"15px","fontWeight":"500","fontStyle":"italic","textAlign":"center"},
            )
        ], pad="16px 22px"),
    ])

def p5(mode):
    df_rvs = _df_rvs_scores()
    df_msa = _df_msa_scissor()
    fast = int((df_rvs["rvs_years"] <= 2).sum()) if not df_rvs.empty else 0
    medium = int(((df_rvs["rvs_years"] >= 3) & (df_rvs["rvs_years"] <= 4)).sum()) if not df_rvs.empty else 0
    slow = int((df_rvs["rvs_years"] >= 5).sum()) if not df_rvs.empty else 0
    min_years = int(df_rvs["rvs_years"].min()) if not df_rvs.empty else 0
    max_years = int(df_rvs["rvs_years"].max()) if not df_rvs.empty else 0
    latest_msa_year = int(df_msa["year"].max()) if not df_msa.empty else 2017
    lti_over3 = int((df_msa[df_msa["year"] == latest_msa_year]["median_lti"] > 3).sum()) if not df_msa.empty else 0
    bridge_text = "The markets that recovered fastest often saw the largest increases in loan-to-income ratios."
    bridge_note = "Pattern statement"
    if not df_rvs.empty and not df_msa.empty:
        latest = int(df_msa["year"].max())
        m = df_msa[df_msa["year"] == latest][["msa", "median_lti"]].copy()
        m["msa"] = m["msa"].astype(str)
        m = m[m["msa"].str.len() == 2]
        j = df_rvs.merge(m, left_on="state", right_on="msa", how="inner")
        if len(j) >= 4:
            fast_mean = float(j[j["rvs_years"] <= 2]["median_lti"].mean()) if len(j[j["rvs_years"] <= 2]) else float("nan")
            slow_mean = float(j[j["rvs_years"] >= 5]["median_lti"].mean()) if len(j[j["rvs_years"] >= 5]) else float("nan")
            corr = float(j["rvs_years"].corr(j["median_lti"])) if j["median_lti"].nunique() > 1 else 0.0
            if fast_mean == fast_mean and slow_mean == slow_mean:
                if fast_mean > slow_mean:
                    bridge_text = f"Fast-recovery states show higher latest LTI on average ({fast_mean:.2f}x) than slow-recovery states ({slow_mean:.2f}x)."
                else:
                    bridge_text = f"Latest LTI is not higher in fast-recovery states ({fast_mean:.2f}x) than slow-recovery states ({slow_mean:.2f}x)."
            bridge_note = f"Computed on state overlap (n={len(j)}), corr(recovery years, LTI)={corr:.2f}"
    spread_years = max_years - min_years

    return html.Div([
        chapter_title(5,"Recovery Was Uneven and Not Always Better","Location shaped both recovery speed and affordability pressure."),
        kpi_row([
            kpi(f"{min_years}-{max_years} years","Recovery range",C["warning"],"Years to return to pre-crisis lending scale"),
            kpi(str(fast),"Fast-recovery states",C["recovery"],"Recovered in 2 years or less"),
            kpi(str(slow),"Slow-recovery states",C["crash"],"Took 5 years or longer"),
            kpi(str(lti_over3),f"Markets above LTI=3 ({latest_msa_year})",C["crash"],"Affordability pressure in recovered areas"),
        ]),
        insight_chip(f"So what: Recovery timing spans {spread_years} years between fastest and slowest states in the sample.", C["warning"]),
        card([
            G(ch.fig_recovery_map_discrete(df_rvs), "ch5-map"),
        ]),
        html.Div(
            bridge_text,
            style={"fontSize":"14px","fontWeight":"500","color":C["text"],"margin":"6px 2px 12px"},
        ),
        html.Div(bridge_note, style={"fontSize":"11px","color":C["muted"],"margin":"-6px 2px 10px"}),
        html.Div([
            html.Div([
                card([G(ch.fig_rvs_bar(df_rvs), "rvs")], mb="0px")
            ], style={"flex":"1","minWidth":"300px"}),
            html.Div([
                card([G(ch.fig_lti_affordability(df_msa), "lti-affordability")], mb="0px")
            ], style={"flex":"1","minWidth":"300px"}),
        ], style={"display":"flex","gap":"12px","flexWrap":"wrap"}),
    ])

def p6(mode):
    df_dr   = _df_denial_rates()
    df_ho   = _df_purchase_homeownership()
    df_race = _df_origination_share_by_race()

    black = df_race[df_race["race"] == "Black / African American"].sort_values("year")
    b2007 = float(black[black["year"] == 2007]["share"].iloc[0]) if len(black[black["year"] == 2007]) else 0.0
    b2017 = float(black[black["year"] == 2017]["share"].iloc[0]) if len(black[black["year"] == 2017]) else 0.0
    black_drop = ((b2017 / b2007) - 1.0) if b2007 else 0.0

    latest_denial_year = int(df_dr["year"].max()) if not df_dr.empty else 2017
    w_mid = df_dr[(df_dr["year"] == latest_denial_year) & (df_dr["race"] == "White") & (df_dr["income_band"] == "50-80K")]
    b_mid = df_dr[(df_dr["year"] == latest_denial_year) & (df_dr["race"] == "Black / African American") & (df_dr["income_band"] == "50-80K")]
    denial_ratio = float(b_mid["denial_rate"].iloc[0] / w_mid["denial_rate"].iloc[0]) if len(w_mid) and len(b_mid) and float(w_mid["denial_rate"].iloc[0]) > 0 else 0.0
    denial_gap_pp = ((float(b_mid["denial_rate"].iloc[0]) - float(w_mid["denial_rate"].iloc[0])) * 100.0) if len(w_mid) and len(b_mid) else 0.0

    b_mid_series = df_dr[(df_dr["race"] == "Black / African American") & (df_dr["income_band"] == "50-80K")].sort_values("year")
    post2012 = b_mid_series[b_mid_series["year"] >= 2012]["denial_rate"]
    base2007 = b_mid_series[b_mid_series["year"] == 2007]["denial_rate"]
    persistence_pp = ((float(post2012.mean()) - float(base2007.iloc[0])) * 100.0) if len(post2012) and len(base2007) else 0.0

    h2007 = float(df_ho[df_ho["year"] == 2007]["homeownership_rate"].iloc[0]) if len(df_ho[df_ho["year"] == 2007]) else 0.0
    h2017 = float(df_ho[df_ho["year"] == 2017]["homeownership_rate"].iloc[0]) if len(df_ho[df_ho["year"] == 2017]) else 0.0

    return html.Div([
        chapter_title(6,"Who Got Left Behind","Credit tightened asymmetrically, and inequality in access hardened."),
        kpi_row([kpi(f"{b2007:.1%} -> {b2017:.1%}", "Black share of originations (2007->2017)", C["crash"], f"{black_drop:.0%} change"),
                 kpi(f"{denial_ratio:.1f}x", "Denial gap at same income", C["warning"], f"~{denial_gap_pp:.0f} pp higher ({latest_denial_year}, 50-80K)"),
                 kpi(f"{persistence_pp:+.0f} pp", "Post-2012 denial persistence", C["crash"], "Black 50-80K vs 2007 baseline"),
                 kpi(f"{h2007:.1f}% -> {h2017:.1f}%", "Homeownership rate (2007->2017)", C["recovery"], "National trend")]),
        insight_chip(f"So what: At the same income in {latest_denial_year}, denial odds are about {denial_ratio:.1f}x higher for Black applicants.", C["crash"]),
        card([G(ch.fig_credit_access_index(df_race),"ch6-access-index"),
              ann("This is not a temporary dip story; it is a relative-access reset that never fully re-equalized.",
                  "Indexed paths isolate the distributional break: who lost ground and who recovered it.",
                  mode),
              src("HMDA LAR 2007-2017 (CFPB)")]),
        card([G(ch.fig_denial_gap_income(df_dr),"ch6-denial-gap"),
              ann("Income parity did not buy approval parity. The spread at equal bands points to structural underwriting inequality.",
                  "Rates use published benchmark years with interpolation for annual continuity.",
                  mode),
              src("CFPB Data Point 2014 & 2018","Urban Institute HFPC 2019")]),
        card([G(ch.fig_denial_persistence(df_dr),"ch6-persistence"),
              ann("Labor recovery and credit recovery decoupled; employment normalization did not restore lending symmetry.",
                  "Persistence is tracked in the same middle-income band through the cycle.",
                  mode)]),
        html.Div(
            "Persistently high denial rates meant fewer households could transition into homeownership.",
            style={"fontSize":"14px","fontWeight":"500","color":C["text"],"margin":"6px 2px 12px"},
        ),
        card([G(ch.fig_homeownership_link(df_ho),"ch6-homeownership"),
              ann("Ownership erosion followed the approval squeeze: fewer accepted borrowers means fewer first-step owners.",
                  "Shown as temporal linkage rather than single-factor causation.",
                  mode),
              src("Census homeownership series","HMDA purchase activity")]),
    ])

def p7(mode):
    df_lend = _df_lender_bubble()
    k = dl.exec_kpis()
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

    return html.Div([
        chapter_title(7,"The New Rules: Who Won the Crisis",
                      "Systemic risk was redistributed, not resolved."),
        insight_chip(f"So what: Nonbank share rose {nonbank_gain_pp:+.0f} percentage points from 2007 to 2017.", C["nonbank"]),
        card([html.Div("Executive summary — 2018",style={"fontSize":"11px","fontWeight":"500",
                "letterSpacing":"0.07em","textTransform":"uppercase",
                "color":C["muted"],"marginBottom":"14px"}),
              kpi_row([kpi(f"{nonbank_2007:.0%} -> {nonbank_2017:.0%}","Nonbank share (2007->2017)",C["nonbank"],"Share of originations"),
                       kpi(str(crossover_year) if crossover_year else "N/A","Nonbank-bank crossover year",C["warning"]),
                       kpi(k["fha_peak_share"],f"FHA peak ({k['fha_peak_year']})",C["govt"]),
                       kpi(str(k["peak_denial_year"]),"Peak denial year",C["crash"])]),
              data_note(k["wamu_indymac_note"])]),
        card([html.Div("Structural shift in lending ownership",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_lender_trend(df_lend),"lendtrend")]),
        card([html.Div("Top lenders: banks vs nonbanks",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_top_lenders_split(df_lend),"toplenders"),
              ann("Market power rotated: the center of gravity shifted from deposit-funded banks to fee-driven nonbanks.",
                  "The top-lender mix shows a structural ownership change, not a cyclical blip.",
                  mode)]),
        html.Div([
            html.P([
                html.Span("The subprime crisis ",style={"fontWeight":"500"}),
                "wasn't caused by subprime borrowers.  ",
                html.Span("The recovery ",style={"fontWeight":"500"}),
                "didn't restore the people it was supposed to help.  ",
                html.Span("The risk ",style={"fontWeight":"500"}),
                "didn't disappear. It migrated into a less-visible part of the system.",
            ], style={"fontSize":"16px","color":C["text"],"lineHeight":"1.8",
                      "textAlign":"center","maxWidth":"700px","margin":"0 auto",
                      "fontStyle":"italic"})
        ], style={"padding":"28px","borderRadius":"12px","marginBottom":"16px",
                  "background":C["surface"],"border":f"0.5px solid {C['border']}"}),
    ])

# ── Layout ─────────────────────────────────────────────

app.layout = html.Div([
    dcc.Location(id="url",refresh=False),
    html.Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Merriweather:wght@500;700&family=Source+Sans+3:wght@400;500;600;700&display=swap",
    ),
    html.Div(id="nav", children=navbar(1)),
    html.Div(id="page",style={
        "maxWidth":"1120px","margin":"0 auto",
        "padding":"26px 24px 48px","fontFamily":FONT,"color":C["text"],
    }),
], style={"background":C["surface"],"minHeight":"100vh"})

# ── Callbacks ──────────────────────────────────────────

PAGE_MAP = {
    "/chapter/1":(p1,1),"/chapter/2":(p2,2),"/chapter/3":(p3,3),
    "/chapter/4":(p4,4),"/chapter/5":(p5,5),"/chapter/6":(p6,6),"/chapter/7":(p7,7),
}

@lru_cache(maxsize=16)
def _render_page(path: str, mode: str):
    fn, _ = PAGE_MAP.get(path,(p1,1))
    return fn(mode or "civilian")

@app.callback(Output("page","children"), Input("url","pathname"), Input("mode","value"))
def route(path, mode):
    return _render_page(path or "/chapter/1", mode or "civilian")

@app.callback(Output("nav","children"), Input("url","pathname"))
def render_nav(path):
    _, num = PAGE_MAP.get(path, (p1, 1))
    return navbar(num)

if __name__ == "__main__":
    print(f"Mode: {'REAL' if dl.USE_REAL_DATA else 'MOCK'} DATA")
    print("Open: http://127.0.0.1:8050")
    app.run(debug=True, port=8050)


