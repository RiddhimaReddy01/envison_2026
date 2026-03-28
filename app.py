"""
app.py â€” Envision Hackathon 2026  (FINAL)
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

import data_loader as dl
import charts as ch

C = {
    "bg":"#F7F5F0",
    "surface":"#EFEDE7",
    "border":"rgba(20,20,20,0.16)",
    "text":"#1A1A1A",
    "muted":"#5B5B5B",
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
def _df_lender_bubble():
    return dl.lender_bubble().to_pandas()

@lru_cache(maxsize=1)
def _df_bank_nonbank():
    return dl.bank_nonbank_survival().to_pandas()

@lru_cache(maxsize=1)
def _df_recovery_affordability():
    return dl.recovery_vs_affordability().to_pandas()

def card(children, pad="24px 28px", mb="16px"):
    return html.Div(children, className="card-soft", style={
        "background":C["bg"],"border":f"0.5px solid {C['border']}",
        "borderRadius":"10px","padding":pad,"marginBottom":mb,
    })

def kpi(number, label, color=None, note=None):
    return html.Div([
        html.Div(number, style={"fontSize":"24px","fontWeight":"500",
                                "lineHeight":"1.1","color":color or C["text"]}),
        html.Div(label,  style={"fontSize":"12px","color":C["muted"],"marginTop":"4px"}),
        html.Div(note,   style={"fontSize":"10px","color":C["muted"],"marginTop":"2px",
                                "fontStyle":"italic"}) if note else None,
    ], className="kpi-soft", style={"background":C["surface"],"borderRadius":"6px",
              "padding":"14px 16px","flex":"1","minWidth":"130px","border":f"0.5px solid {C['border']}"})

def kpi_row(items):
    return html.Div(items, style={"display":"flex","gap":"10px",
                                  "flexWrap":"wrap","marginBottom":"20px"})

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
    clean = (text or "").strip()
    if clean.lower().startswith("so what:"):
        clean = clean.split(":", 1)[1].strip()
    return html.Div([
        html.Span("Takeaway: ", style={"fontWeight":"700", "color":C["text"]}),
        clean
    ], style={
        "fontSize":"12px","fontWeight":"600","color":color or C["text"],
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

# â”€â”€ Pages â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
        
        key_insight("The key pre-crisis fact was concentration: one private channel carried almost all mortgage risk. Growth masked systemic fragility."),
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
            G(ch.fig_ch4_refi_mirage(pr, ho), "ch4-refi-mirage"),
            ann(
                "When refinance dominates and homeownership stalls, activity is not the same as access.",
                "Peak-volume years were debt rotation years, not broad household entry years.",
                mode,
            ),
        ]),

        card([
            G(ch.fig_ch4_yield_attrition(col, 2007, 2017), "ch4-yield"),
            ann(
                "The funnel got smaller even as conversion improved, which means fewer total participants made it through.",
                "Efficiency improved on paper, while the addressable market thinned in practice.",
                mode,
            ),
        ]),

        card([
            html.Div("The Squeezed Middle: middle-income leverage is accelerating fastest", style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px"}),
            G(ch.fig_ch4_lti_income_groups(df_lti), "ch4-lti-groups"),
            ann(
                "Middle-income leverage has climbed the fastest from trough and is now closest to the safety ceiling.",
                "The risk center moved toward the middle of the distribution even without being the absolute highest line.",
                mode,
            ),
        ]),
    ])
def p5(mode):
    df_rvs  = _df_rvs_scores()
    df_bn   = _df_bank_nonbank()
    df_ra   = _df_recovery_affordability()

    fast      = int((df_rvs["rvs_years"] <= 2).sum()) if not df_rvs.empty else 0
    slow      = int((df_rvs["rvs_years"] >= 5).sum()) if not df_rvs.empty else 0
    min_years = int(df_rvs["rvs_years"].min()) if not df_rvs.empty else 0
    max_years = int(df_rvs["rvs_years"].max()) if not df_rvs.empty else 0

    # Bank vs nonbank crossover year
    bank_share_2017 = float(df_bn[(df_bn["lender_type"] == "Bank") & (df_bn["year"] == 2017)]["share"].iloc[0]) if not df_bn.empty and len(df_bn[(df_bn["lender_type"] == "Bank") & (df_bn["year"] == 2017)]) else 0.0
    nonbank_share_2017 = 1.0 - bank_share_2017

    # Recovery trap insight
    fast_lti = float(df_ra[df_ra["rvs_years"] <= 2]["median_lti_2017"].mean()) if not df_ra.empty and len(df_ra[df_ra["rvs_years"] <= 2]) else 0.0
    slow_lti = float(df_ra[df_ra["rvs_years"] >= 5]["median_lti_2017"].mean()) if not df_ra.empty and len(df_ra[df_ra["rvs_years"] >= 5]) else 0.0

    return html.Div([
        chapter_title(5, "Who Survived — And What It Cost Them",
                      "Recovery speed, structural handoff, and the affordability trap."),
        kpi_row([
            kpi(f"{min_years}–{max_years} yrs", "Recovery range by state", C["warning"],
                "Years to return to 80% of 2007 volume"),
            kpi(str(fast), "Fast-recovery states", C["recovery"], "Recovered in ≤2 years"),
            kpi(str(slow), "Slow-recovery states", C["crash"],    "Took 5+ years"),
            kpi(f"{nonbank_share_2017:.0%}", "Nonbank share by 2017", C["nonbank"],
                f"Up from {1 - bank_share_2017 - nonbank_share_2017 + nonbank_share_2017:.0%} — was 30% in 2007"),
        ]),
        insight_chip(
            f"Fast-recovery states hit median LTI {fast_lti:.2f}x by 2017 "
            f"vs {slow_lti:.2f}x in slow-recovery states — they recovered into unaffordability.",
            C["crash"],
        ),

        # Chart 1 — RVS choropleth
        card([
            html.Div("Where recovery happened — and how fast",
                     style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
            G(ch.fig_recovery_map_discrete(df_rvs.merge(df_ra[["state", "median_lti_2017"]], on="state", how="left") if (not df_rvs.empty and not df_ra.empty) else df_rvs), "ch5-map"),
            ann("Geography determined survival speed. Oil-state and sun-belt markets bounced back in 1–2 years. "
                "Sand states — Nevada, Arizona, Florida — took 3–7 years.",
                "RVS = years from trough (2009) to first year originations exceed 80% of 2007 baseline. "
                "Computed from rvs_full.parquet.",
                mode),
            src("HMDA LAR 2007-2017 (CFPB)"),
        ]),

        # Chart 2 — Bank vs nonbank slope
        card([
            html.Div("Who survived — banks handed the market to nonbanks",
                     style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
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
            html.Div("The recovery trap — fast recovery, unaffordable outcome",
                     style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
            G(ch.fig_recovery_vs_affordability(df_ra), "ch5-recov-afford"),
            ann("States that recovered fastest — CA, CO, TX — ended up with median LTI above 3x by 2017. "
                "Recovery and affordability moved in opposite directions.",
                f"Scatter: RVS years (x) vs median LTI 2017 (y). "
                f"Fast states (≤2yr): avg LTI {fast_lti:.2f}x. "
                f"Slow states (≥5yr): avg LTI {slow_lti:.2f}x. n={len(df_ra)} states.",
                mode),
            src("HMDA LAR 2007-2017 (CFPB)"),
        ]),
    ])

def p6(mode):
    df_dr = _df_denial_rates()
    df_ho = _df_purchase_homeownership()
    df_col = _df_collapse()

    white_low = df_dr[(df_dr["race"] == "White") & (df_dr["income_band"] == "<50K")].sort_values("year")
    black_low = df_dr[(df_dr["race"] == "Black / African American") & (df_dr["income_band"] == "<50K")].sort_values("year")
    post_w = float(white_low[white_low["year"] >= 2012]["denial_rate"].mean()) if not white_low.empty else 0.0
    post_b = float(black_low[black_low["year"] >= 2012]["denial_rate"].mean()) if not black_low.empty else 0.0
    gap_pp = (post_b - post_w) * 100.0
    ratio = (post_b / post_w) if post_w > 0 else 0.0
    h2007 = float(df_ho[df_ho["year"] == 2007]["homeownership_rate"].iloc[0]) if len(df_ho[df_ho["year"] == 2007]) else 0.0
    h2017 = float(df_ho[df_ho["year"] == 2017]["homeownership_rate"].iloc[0]) if len(df_ho[df_ho["year"] == 2017]) else 0.0

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
            G(ch.fig_ch6_credit_desert(df_dr, income_band="<50K"), "ch6-credit-desert"),
            ann(
                "Low-income denial rates remained elevated after 2012, with a persistent racial spread.",
                "This chart holds income constant and tracks persistence in the post-crisis era.",
                mode,
            ),
            src("CFPB Data Point 2014 & 2018", "Urban Institute HFPC 2019"),
        ]),
        card([
            html.Div("Funnel Leak", style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px"}),
            G(ch.fig_ch6_funnel_compare(df_dr, _df_loan_type_share(), 2017), "ch6-sankey"),
            ann(
                "Side-by-side funnels make the leak visible: the low-income profile loses far more applicants before origination.",
                "Conversion rate is shown directly on each funnel to quantify the disparity.",
                mode,
            ),
        ]),
        card([
            G(ch.fig_ch6_great_decoupling(df_ho, df_col), "ch6-decoupling"),
            ann(
                "Credit conditions recovered faster than ownership outcomes, producing a sustained decoupling.",
                "Both lines are indexed to 2007=100 to make recovery divergence directly comparable.",
                mode,
            ),
            src("Census homeownership series", "HMDA aggregates"),
        ]),
    ])

def p7(mode):
    df_lend = _df_lender_bubble()
    df_race = _df_origination_share_by_race()
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

    return html.Div([
        chapter_title(7, "The New Rules: Who Won the Crisis", "Systemic risk was redistributed, not resolved."),
        insight_chip(f"So what: Nonbank share rose {nonbank_gain_pp:+.0f} percentage points from 2007 to 2017.", C["nonbank"]),
        kpi_row([
            kpi(f"{nonbank_2007:.0%} -> {nonbank_2017:.0%}", "Nonbank share (2007->2017)", C["nonbank"]),
            kpi(str(crossover_year) if crossover_year else "N/A", "First nonbank>=bank year", C["warning"]),
            kpi(f"{black_2007:.1%} -> {black_2017:.1%}", "Black origination share", C["crash"], "Participation share"),
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
        card([
            html.Div("Winners vs Losers: who gained power, who lost access", style={"fontSize": "13px", "fontWeight": "500", "marginBottom": "8px"}),
            G(ch.fig_ch7_winners_losers_matrix(df_lend, df_race), "ch7-shift-matrix"),
            ann(
                "Upper-right points are winners: share and participation both rose. Lower-left points are groups left behind.",
                "In this sample, nonbanks moved into the winner quadrant while Black borrower participation moved the other way.",
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
# â”€â”€ Layout â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

app.layout = html.Div([
    dcc.Location(id="url",refresh=False),
    html.Link(
        rel="stylesheet",
        href="https://fonts.googleapis.com/css2?family=Libre+Baskerville:wght@700&family=Source+Sans+3:wght@400;500;600;700&display=swap",
    ),
    html.Div(id="nav", children=navbar(1)),
    html.Div(id="page",style={
        "maxWidth":"1120px","margin":"0 auto",
        "padding":"26px 24px 48px","fontFamily":FONT,"color":C["text"],
    }),
], style={"background":C["surface"],"minHeight":"100vh"})

# â”€â”€ Callbacks â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

PAGE_MAP = {
    "/chapter/1":(p1,1),"/chapter/2":(p2,2),"/chapter/3":(p3,3),
    "/chapter/4":(p4,4),"/chapter/5":(p5,5),"/chapter/6":(p6,6),"/chapter/7":(p7,7),
}

def _render_page(path: str, mode: str):
    fn, _ = PAGE_MAP.get(path,(p1,1))
    return fn(mode or "civilian")

@app.callback(Output("page","children"), Input("url","pathname"), Input("mode","value"))
def route(path, mode):
    try:
        return _render_page(path or "/chapter/1", mode or "civilian")
    except Exception:
        err = traceback.format_exc(limit=8)
        print(err)
        return card([
            html.Div("Render error", style={"fontSize":"14px","fontWeight":"600","marginBottom":"8px","color":C["crash"]}),
            html.Pre(err, style={"whiteSpace":"pre-wrap","fontSize":"11px","color":C["text"],"margin":"0"}),
        ], pad="18px 20px")

@app.callback(Output("nav","children"), Input("url","pathname"))
def render_nav(path):
    _, num = PAGE_MAP.get(path, (p1, 1))
    return navbar(num)


if __name__ == "__main__":
    print(f"Mode: {'REAL' if dl.USE_REAL_DATA else 'MOCK'} DATA")
    print("Open: http://127.0.0.1:8050")
    app.run(debug=False, port=8050)




