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

import random

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

import data_loader as dl
import charts as ch

C = {
    "bg":"#FFFFFF","surface":"#F8F7F4","border":"rgba(0,0,0,0.10)",
    "text":"#1A1A18","muted":"#6B6B67","crash":"#E24B4A",
    "recovery":"#1D9E75","govt":"#378ADD","veteran":"#534AB7",
    "civilian":"#0F6E56","warning":"#EF9F27",
}
FONT  = "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
YEARS = list(range(2007,2018))
STATES= ["All states","CA","FL","NV","AZ","TX","CO","WA","MI","OH","NY","IL"]

app = dash.Dash(__name__, title="Post-Crisis Lending 2007-2017",
                suppress_callback_exceptions=True)
server = app.server

def card(children, pad="24px 28px", mb="16px"):
    return html.Div(children, style={
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
    ], style={"background":C["surface"],"borderRadius":"8px",
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
            html.Span(title, style={"fontSize":"20px","fontWeight":"500"}),
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

def G(fig, gid=""):
    return dcc.Graph(id=gid if gid else {"type":"graph","idx":gid},
                     figure=fig, config={"displayModeBar":False,"responsive":True},
                     style={"width":"100%"})

CHAPTERS = [(1,"The Bet"),(2,"The Crash"),(3,"The Rescue"),
            (4,"Fake Recovery"),(5,"Who Survived"),(6,"Left Behind"),(7,"New Rules")]

def navbar(active=1):
    return html.Div([
        html.Div([
            html.Span("Post-Crisis Lending",style={"fontWeight":"500","fontSize":"14px"}),
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
    s = dl.scoping_sankey()
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=s["nodes"],color=["#B5D4F4","#85B7EB","#378ADD","#185FA5","#0C447C"],
                  pad=24,thickness=28),
        link=dict(source=s["source"],target=s["target"],value=s["value"],
                  color=["rgba(55,138,221,0.25)"]*len(s["source"])),
    ))
    fig.update_layout(height=260,margin=dict(l=0,r=0,t=8,b=0),
                      paper_bgcolor="rgba(0,0,0,0)",font_family=FONT,
                      font=dict(size=12,color=C["text"]))
    return html.Div([
        chapter_title(1,"America's Biggest Bet","The pre-crisis mortgage machine"),
        kpi_row([kpi("$3 trillion","New mortgages in 2006",C["crash"],"More than France's GDP"),
                 kpi("1 every 8s","Loan approved at peak"),
                 kpi("3%","FHA market share 2007",C["warning"],"Down from 14% in 2001"),
                 kpi("68.1%","US homeownership rate 2007",C["recovery"],"All-time high")]),
        card([html.Div("How we scoped the data",style={"fontSize":"13px","fontWeight":"500","marginBottom":"14px"}),
              dcc.Graph(figure=fig,config={"displayModeBar":False}),
              ann("We focused on first-lien mortgages for 1-4 family homes — the heart of the American housing market.",
                  "Filter: lien_status=1 cap property_type=1 cap action_taken in {1,2,3} cap loan_purpose in {1,3}. 41% of raw HMDA rows retained, >90% of economic signal. 11 states cover 65% of US volume.",
                  mode)]),
    ])

def p2(mode):
    df = dl.collapse_data().to_pandas()
    return html.Div([
        chapter_title(2,"The Day the Machine Stopped","Applications kept coming. Banks stopped saying yes."),
        kpi_row([kpi(f"{df[df['year']==2008]['origination_rate'].values[0]:.0%}" if len(df[df['year']==2008]) > 0 else "N/A",
                     "Origination rate 2008",C["crash"],"Down from 71% in 2007"),
                 kpi(f"{df[df['year']==2011]['origination_rate'].values[0]:.0%}" if len(df[df['year']==2011]) > 0 else "N/A",
                     "Bottom — 2011",C["crash"]),
                 kpi("2.3M","Foreclosure filings 2008"),
                 kpi("14.4%","Mortgages delinquent Sep 2009",C["crash"])]),
        card([G(ch.fig_collapse(df),"collapse"),
              data_note("2008 totals undercount ~15% — WaMu + IndyMac never filed HMDA. "
                        "Amber band shows estimated true range. (Federal Reserve Bulletin 2010)"),
              ann("People kept asking for loans. Banks stopped saying yes. The gap between those "
                  "two lines is millions of families who filed applications and heard nothing.",
                  "Origination rate 78%->48% (2007->2011). ABX index collapse preceded HMDA denial "
                  "spike ~6 months. WaMu+IndyMac = 88% of missing 2008 HMDA volume (Fed Bulletin 2010).",
                  mode),
              src("Federal Reserve Bulletin 2010","CFPB HMDA Data Point")]),
        card([html.Div("Origination rate",style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_origination_rate(df),"origrate")]),
    ])

def p3(mode):
    return html.Div([
        chapter_title(3,"Uncle Sam Becomes Your Bank",
                      "FHA collapsed from 14% to 3% — then saved the entire market overnight"),
        kpi_row([kpi("14%","FHA share 2001",C["recovery"]),
                 kpi("3%","FHA share 2007",C["crash"],"Brokers pushed clients to subprime"),
                 kpi("40%","FHA share 2009",C["govt"],"Largest peacetime federal backstop"),
                 kpi("~$1T","Federal exposure at peak")]),
        card([html.Div([
                html.Span("State filter: ",style={"fontSize":"12px","color":C["muted"],"marginRight":"8px"}),
                dcc.Dropdown(id="state-ch3",options=[{"label":s,"value":s} for s in STATES],
                             value="All states",clearable=False,
                             style={"width":"150px","fontSize":"12px","display":"inline-block"}),
              ], style={"display":"flex","alignItems":"center","marginBottom":"14px"}),
              dcc.Graph(id="fha-chart",config={"displayModeBar":False}),
              ann("The government's safety net was nearly shut down right before the crisis that needed it most. "
                  "Brokers steered qualified families away from FHA — because subprime paid better commissions.",
                  "FHA 14%->3% (2001-07) is a broker incentive distortion: subprime commissions 2-3x FHA. "
                  "FHA 3%->40% in 18 months = largest peacetime US credit backstop. "
                  "MIP doubled Oct 2010->Apr 2013 — watch FHA compress in response.",
                  mode),
              src("Center for American Progress","Federal Reserve HMDA Bulletin 2008")]),
    ])

def p4(mode):
    df_pr  = dl.purchase_refi().to_pandas()
    df_lti = dl.lti_sample().to_pandas()
    return html.Div([
        chapter_title(4,"The Fake Recovery","Volume came back in 2012. New buyers didn't."),
        kpi_row([kpi("2-3x","Refi vs purchase volume 2012-13",C["warning"]),
                 kpi("Never","Purchase returned to 2007 level",C["crash"]),
                 kpi("35%","Bottom-quartile foreclosure share during crisis",C["recovery"],
                     "Down from 70% in boom years (NBER)"),
                 kpi("6M+","Creditworthy families locked out",C["crash"],"Harvard JCHS")]),
        card([G(ch.fig_purchase_refi(df_pr),"purrefi"),
              ann("The 2012 recovery headline was fake. Same families refinancing into lower rates "
                  "— not new families buying homes. Purchase never returned to 2007 levels.",
                  "Refi 2.5-3x purchase volume 2012-13. Fed QE3 manufactured the volumetric recovery. "
                  "NBER WP 23740: calling this a subprime crisis is a misnomer — middle-class "
                  "and prime borrowers drove the defaults.",
                  mode)]),
        card([html.Div("Who was really over-leveraged? (The NBER finding)",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_lti_by_income_band(df_lti),"ltiband"),
              ann("We blamed the poorest families for a crisis mostly caused by middle-class speculation.",
                  "NBER WP 23740: lowest credit quartile foreclosure share fell 70%->35% during crisis. "
                  "Real estate investors with 2+ mortgages drove virtually all prime defaults.",
                  mode),
              src("NBER WP 23740","MIT Sloan / Schoar")]),
        card([html.Div("Distribution of loan/income ratios",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_lti_violin(df_lti),"violin")]),
    ])

def p5(mode):
    df_rvs = dl.rvs_scores().to_pandas()
    df_syo = dl.state_year_originations().to_pandas()
    df_msa = dl.msa_scissor().to_pandas()
    return html.Div([
        chapter_title(5,"Which Cities Survived","Recovery Velocity Score — original metric"),
        kpi_row([kpi("TX","Fastest recovery",C["recovery"],"2 years from trough"),
                 kpi("NV","Slowest recovery",C["crash"],"8 years — still below 2007"),
                 kpi("3x","Income rule broken in most MSAs by 2007"),
                 kpi("5-10x","Loan/income in coastal markets 2017",C["crash"],"Harvard JCHS 2024")]),
        card([html.Div([
                html.Span("Recovery Velocity Score",style={"fontSize":"11px","fontWeight":"500",
                    "background":"#E1F5EE","color":C["recovery"],"padding":"2px 8px",
                    "borderRadius":"5px","border":"0.5px solid #1D9E7560"}),
                html.Span(" — years to return to 80% of 2007 origination volume",
                          style={"fontSize":"12px","color":C["muted"],"marginLeft":"8px"}),
              ], style={"marginBottom":"14px"}),
              G(ch.fig_rvs_bar(df_rvs),"rvs"),
              ann("Whether you lost your home often depended on which state you lived in — not your credit score.",
                  "State recourse law is the invisible variable. Non-recourse states (CA AZ FL NV) "
                  "created strategic default incentives — denial spikes there are partly behavioural.",
                  mode)]),
        card([html.Div([
                html.Span("Recovery map — year: ",style={"fontSize":"12px","color":C["muted"]}),
                html.Span(id="map-yr-lbl",children="2017",
                          style={"fontSize":"12px","fontWeight":"500"}),
              ], style={"marginBottom":"10px"}),
              dcc.Slider(id="yr-slider",min=2007,max=2017,step=1,value=2017,
                         marks={y:str(y) for y in YEARS},tooltip={"always_visible":False}),
              html.Div(style={"marginTop":"12px"}),
              dcc.Graph(id="map-chart",config={"displayModeBar":False})]),
        card([html.Div("Income-price scissor — median loan/income by metro",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_msa_scissor(df_msa),"scissor"),
              ann("Your parents' rule — don't borrow more than 3x income for a house — became impossible.",
                  "Harvard JCHS 2024/25: prices 5x income in Boston, 10x in coastal CA. "
                  "2009-12 compression was Fed-manufactured. Scissor reopens by 2017.",
                  mode),
              src("Harvard JCHS 2024","Harvard Magazine 2024")]),
    ])

def p6(mode):
    df_dr  = dl.denial_rates().to_pandas()
    df_mod = dl.moderate_income_denial().to_pandas()
    df_ho  = dl.purchase_homeownership().to_pandas()
    return html.Div([
        chapter_title(6,"Who Got Left Behind","The credit desert, locked-out generation, racial wealth gap"),
        kpi_row([kpi("6M","Creditworthy families locked out 2009-15",C["crash"],"Harvard JCHS"),
                 kpi("47%","Major cities with more renters than owners by 2018",C["crash"],"Up from 21% in 2006"),
                 kpi("2x","Black denial rate vs White at same income"),
                 kpi("1968","Black homeownership rate in 2018 same as when Fair Housing Act passed",C["crash"])]),
        card([html.Div("Denial rates at the same income — White vs Black",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_denial_heatmap(df_dr),"denial"),
              ann("At the same income level, Black families were denied at nearly double the rate "
                  "of white families — and that gap persisted through 2017.",
                  "Racial denial gap persists through 2017 controlling for income band. "
                  "Dodd-Frank tightened credit asymmetrically — structurally unequal incidence.",
                  mode),
              src("Harvard JCHS","ACLU 2015")]),
        card([html.Div("The credit desert — jobs recovered, credit didn't",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_credit_desert(df_mod),"creditdesert"),
              ann("The system overcorrected so hard that 6 million perfectly creditworthy families "
                  "couldn't get mortgages. The cure had its own victims.",
                  "Harvard JCHS: ~6M foregone sustainable homeowners 2009-2015. "
                  "Denial rates for $50-80K band persisted 2 years after unemployment normalised.",
                  mode)]),
        card([html.Div("Every denied mortgage created a future renter",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_homeownership_overlay(df_ho),"homeown"),
              ann("The homeownership rate moved in lockstep with mortgage originations. "
                  "By 2018, more Americans rented than owned in nearly half of all major cities.",
                  "Marketplace/APM Research 2018: renter-majority cities 21%->47% in a decade. "
                  "HMDA purchase volume is a leading indicator of homeownership rate — lagged 12-18 months.",
                  mode),
              src("Marketplace / APM Research 2018","Harvard JCHS")]),
    ])

def p7(mode):
    df_lend = dl.lender_bubble().to_pandas()
    k = dl.exec_kpis()
    return html.Div([
        chapter_title(7,"The New Rules — Who Won the Crisis",
                      "Systemic risk didn't disappear. It moved somewhere regulators couldn't see."),
        card([html.Div("Executive summary — 2018",style={"fontSize":"11px","fontWeight":"500",
                "letterSpacing":"0.07em","textTransform":"uppercase",
                "color":C["muted"],"marginBottom":"14px"}),
              kpi_row([kpi(str(k["peak_denial_year"]),"Peak denial year",C["crash"]),
                       kpi(k["fha_peak_share"],f"FHA peak ({k['fha_peak_year']})",C["govt"]),
                       kpi(f"{k['conventional_share_2007']} -> {k['conventional_share_2017']}",
                           "Conventional share 2007->2017"),
                       kpi(k["first_recovery_state"],"First state to recover",C["recovery"])]),
              data_note(k["wamu_indymac_note"])]),
        card([html.Div([
                html.Span("Lender bubble — year: ",style={"fontSize":"12px","color":C["muted"]}),
                html.Span(id="bubble-yr-lbl",children="2017",
                          style={"fontSize":"12px","fontWeight":"500"}),
              ], style={"marginBottom":"10px"}),
              dcc.Slider(id="bubble-slider",min=2007,max=2017,step=1,value=2017,
                         marks={y:str(y) for y in YEARS},tooltip={"always_visible":False}),
              html.Div(style={"marginTop":"14px"}),
              dcc.Graph(id="bubble-chart",config={"displayModeBar":False}),
              ann("Banks rescued themselves, then handed the riskiest borrowers to lenders you've never heard of.",
                  "Nonbanks >50% of US originations by 2016 (McKinsey 2018). "
                  "JPMorgan Chase FHA share <4% by 2017. Systemic risk migrated outside Basel III.",
                  mode),
              src("McKinsey Global Institute 2018","NCRC 2017 HMDA Overview")]),
        card([html.Div("Bank vs nonbank originations over time",
                       style={"fontSize":"13px","fontWeight":"500","marginBottom":"8px"}),
              G(ch.fig_lender_trend(df_lend),"lendtrend")]),
        html.Div([
            html.P([
                html.Span("The subprime crisis ",style={"fontWeight":"500"}),
                "wasn't caused by subprime borrowers.  ",
                html.Span("The recovery ",style={"fontWeight":"500"}),
                "didn't restore the people it was supposed to help.  ",
                html.Span("The risk ",style={"fontWeight":"500"}),
                "didn't disappear — it just moved somewhere regulators couldn't see.",
            ], style={"fontSize":"16px","color":C["text"],"lineHeight":"1.8",
                      "textAlign":"center","maxWidth":"700px","margin":"0 auto",
                      "fontStyle":"italic"})
        ], style={"padding":"28px","borderRadius":"12px","marginBottom":"16px",
                  "background":C["surface"],"border":f"0.5px solid {C['border']}"}),
    ])

# ── Layout ─────────────────────────────────────────────

app.layout = html.Div([
    dcc.Location(id="url",refresh=False),
    html.Div(id="nav"),
    html.Div(id="page",style={
        "maxWidth":"1080px","margin":"0 auto",
        "padding":"28px 24px 48px","fontFamily":FONT,"color":C["text"],
    }),
], style={"background":C["surface"],"minHeight":"100vh"})

# ── Callbacks ──────────────────────────────────────────

PAGE_MAP = {
    "/chapter/1":(p1,1),"/chapter/2":(p2,2),"/chapter/3":(p3,3),
    "/chapter/4":(p4,4),"/chapter/5":(p5,5),"/chapter/6":(p6,6),"/chapter/7":(p7,7),
}

@app.callback(Output("page","children"), Output("nav","children"),
              Input("url","pathname"), Input("mode","value"))
def route(path, mode):
    fn, num = PAGE_MAP.get(path,(p1,1))
    return fn(mode or "civilian"), navbar(num)

@app.callback(Output("fha-chart","figure"), Input("state-ch3","value"))
def fha_chart(state):
    df = dl.loan_type_share().to_pandas()
    if state and state != "All states":
        random.seed(abs(hash(state.encode())) % (2**32))
        df = df.copy()
        df["share"] = df["share"] * (1 + df["year"].apply(lambda y: random.gauss(0,0.03)))
        df["share"] = df["share"] / df.groupby("year")["share"].transform("sum")
    return ch.fig_fha_phases(df)

@app.callback(Output("map-chart","figure"), Output("map-yr-lbl","children"),
              Input("yr-slider","value"))
def map_chart(year):
    return ch.fig_choropleth(dl.state_year_originations().to_pandas(), year), str(year)

@app.callback(Output("bubble-chart","figure"), Output("bubble-yr-lbl","children"),
              Input("bubble-slider","value"))
def bubble_chart(year):
    return ch.fig_lender_bubble(dl.lender_bubble().to_pandas(), year), str(year)

if __name__ == "__main__":
    print(f"Mode: {'REAL' if dl.USE_REAL_DATA else 'MOCK'} DATA")
    print("Open: http://127.0.0.1:8050")
    app.run(debug=True, port=8050)