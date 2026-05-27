import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime, timezone, timedelta

# ── PAGE CONFIG ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="POLYCAB · Equity Research Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── COLOUR PALETTE ─────────────────────────────────────────────────────────────
BG    = "#0d1117"
CARD  = "#161b22"
TEXT  = "#e6edf3"
GOLD  = "#C5A55A"
STEEL = "#2D6DA8"
GREEN = "#27AE60"
RED   = "#E74C3C"
GRID  = "rgba(255,255,255,0.08)"

# ── DATA BLOCK ─────────────────────────────────────────────────────────────────
FISCAL_YEARS      = ["FY23", "FY24", "FY25", "FY26"]
REVENUE_CR        = [13912, 18260, 22052, 28884]
EBITDA_CR         = [1530,  2190,  3090,  4069]
EBITDA_MARGIN_PCT = [11.0,  12.0,  14.0,  14.1]
PAT_CR            = [1272,  1787,  2046,  2708]
EPS_INR           = [85,    120,   140,   173]
WC_REV_CR         = [12100, 15600, 18524, 24400]
FMEG_REV_CR       = [730,   1100,  1654,  2069]
FMEG_PROFIT_CR    = [-80.0, -50.0, -38.9, 54.8]

SCENARIOS = {
    "bull": {"label": "Bull Case", "prob": 30, "fy28_rev": 43500, "ebitda_m": 15.8, "eps": 305, "target": 13700, "color": GREEN},
    "base": {"label": "Base Case", "prob": 50, "fy28_rev": 40900, "ebitda_m": 14.5, "eps": 260, "target": 10400, "color": "#4A9EDF"},
    "bear": {"label": "Bear Case", "prob": 20, "fy28_rev": 35000, "ebitda_m": 12.8, "eps": 197, "target": 6900,  "color": RED},
}
CURRENT_PRICE   = 9199
WEIGHTED_TARGET = 10490

PEERS = pd.DataFrame([
    {"Company": "Polycab India",  "Cables Mkt Share": "~27%", "P/E": "44.8x", "ROCE": "29.7%", "ROE": "21.4%"},
    {"Company": "Havells India",  "Cables Mkt Share": "~8%",  "P/E": "65.4x", "ROCE": "—",     "ROE": "—"},
    {"Company": "KEI Industries", "Cables Mkt Share": "~12%", "P/E": "49.1x", "ROCE": "21.3%", "ROE": "15.6%"},
    {"Company": "Finolex Cables", "Cables Mkt Share": "~6%",  "P/E": "—",     "ROCE": "—",     "ROE": "—"},
])

SWING_FACTORS = [
    "**Copper & aluminium prices** — directly compress W&C gross margins",
    "**FMEG margin progression** — Project Spring targets 8–10% EBITDA margin by FY30",
    "**Government capex execution** — RDSS, PLI, EV infra, housing schemes",
    "**IT investigation resolution** — FY24 income tax search cloud not fully cleared",
    "**KEI Industries share gains** — monitor order book commentary each quarter",
]

# ── BLOOMBERG CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* Remove Streamlit chrome */
  #MainMenu, header, footer,
  [data-testid="stToolbar"],
  [data-testid="stDecoration"],
  [data-testid="stStatusWidget"] { display: none !important; }

  /* Global dark canvas */
  .stApp,
  [data-testid="stAppViewContainer"],
  [data-testid="stMain"],
  .main { background-color: #0d1117 !important; }

  [data-testid="stSidebar"] { background-color: #0d1117 !important; }

  .block-container {
    padding-top: 0 !important;
    padding-bottom: 2rem !important;
    max-width: 100% !important;
  }

  /* Body text */
  body, p, span, div, label, li, td, th {
    color: #e6edf3 !important;
    font-family: 'Courier New', Courier, monospace !important;
  }

  h1, h2, h3, h4, h5, h6 { color: #e6edf3 !important; }

  /* Tab bar */
  [data-testid="stTabs"] button {
    color: rgba(230,237,243,0.45) !important;
    background: transparent !important;
    font-family: 'Courier New', monospace !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.09em !important;
    text-transform: uppercase !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 4px !important;
  }
  [data-testid="stTabs"] button[aria-selected="true"] {
    color: #C5A55A !important;
    border-bottom: 2px solid #C5A55A !important;
  }
  [data-testid="stTabs"] button:hover {
    color: rgba(197,165,90,0.7) !important;
  }
  [data-testid="stTabs"] [role="tablist"] {
    border-bottom: 1px solid rgba(197,165,90,0.18) !important;
    gap: 20px !important;
    background: transparent !important;
  }

  /* st.metric dark cards */
  [data-testid="stMetric"] {
    background: #161b22 !important;
    border: 1px solid rgba(197,165,90,0.15) !important;
    border-radius: 6px !important;
    padding: 14px 16px !important;
  }
  [data-testid="stMetricLabel"] {
    color: rgba(230,237,243,0.45) !important;
    font-size: 10px !important;
    text-transform: uppercase !important;
    letter-spacing: 0.07em !important;
  }
  [data-testid="stMetricValue"] {
    color: #e6edf3 !important;
    font-size: 21px !important;
    font-weight: 700 !important;
    font-family: 'Courier New', monospace !important;
  }
  [data-testid="stMetricDelta"] {
    color: rgba(39,174,96,0.9) !important;
    font-size: 11px !important;
  }
  [data-testid="stMetricDelta"] svg { display: none !important; }

  /* Buttons */
  .stButton > button {
    background: transparent !important;
    border: 1px solid #C5A55A !important;
    color: #C5A55A !important;
    font-family: 'Courier New', monospace !important;
    font-size: 10px !important;
    letter-spacing: 0.08em !important;
    padding: 5px 14px !important;
    border-radius: 3px !important;
  }
  .stButton > button:hover { background: rgba(197,165,90,0.1) !important; }

  /* Divider */
  hr { border-color: rgba(197,165,90,0.15) !important; }

  /* Alert / info boxes */
  [data-testid="stAlert"] {
    background: #161b22 !important;
    border: 1px solid rgba(197,165,90,0.22) !important;
    border-radius: 4px !important;
  }
  [data-testid="stAlert"] p { color: #e6edf3 !important; }

  /* Caption */
  [data-testid="stCaptionContainer"],
  .stCaptionContainer {
    color: rgba(230,237,243,0.3) !important;
    font-size: 10px !important;
    font-family: 'Courier New', monospace !important;
  }

  /* Dataframe */
  [data-testid="stDataFrame"] { background: #161b22 !important; }

  /* Inputs */
  input, select, textarea {
    background: #161b22 !important;
    color: #e6edf3 !important;
    border-color: rgba(197,165,90,0.25) !important;
  }

  /* Scrollbar */
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: #0d1117; }
  ::-webkit-scrollbar-thumb { background: rgba(197,165,90,0.3); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ── HELPERS ────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_price():
    try:
        fi    = yf.Ticker("POLYCAB.NS").fast_info
        price = round(float(fi.last_price), 2)
        prev  = round(float(fi.previous_close), 2)
        delta = round(price - prev, 2)
        pct   = round(delta / prev * 100, 2)
        return {"price": price, "delta": delta, "pct": pct, "live": True}
    except Exception:
        return {"price": CURRENT_PRICE, "delta": None, "pct": None, "live": False}


def nse_status():
    ist     = timezone(timedelta(hours=5, minutes=30))
    now     = datetime.now(ist)
    open_t  = now.replace(hour=9,  minute=15, second=0, microsecond=0)
    close_t = now.replace(hour=15, minute=30, second=0, microsecond=0)
    is_open = now.weekday() < 5 and open_t <= now <= close_t
    return ("NSE OPEN", GREEN) if is_open else ("NSE CLOSED", RED)


def kpi_card(label, value, delta="", positive=True):
    dcol  = GREEN if positive else RED
    dhtml = (f'<div style="color:{dcol};font-size:12px;margin-top:6px;">{delta}</div>'
             if delta else "")
    return f"""
    <div style="background:{CARD};border-top:3px solid {GOLD};border-radius:6px;
                padding:18px 16px;text-align:center;height:100%;">
      <div style="color:rgba(230,237,243,0.45);font-size:10px;text-transform:uppercase;
                  letter-spacing:0.08em;margin-bottom:8px;">{label}</div>
      <div style="color:{TEXT};font-size:23px;font-weight:700;
                  font-family:'Courier New',monospace;">{value}</div>
      {dhtml}
    </div>"""


# Plotly layout defaults
DARK = dict(
    paper_bgcolor=CARD,
    plot_bgcolor=BG,
    font=dict(color=TEXT, size=11, family="'Courier New', monospace"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
    margin=dict(t=52, b=44, l=64, r=64),
    title_font=dict(color=TEXT, size=13),
)
DARK_AX = dict(
    gridcolor=GRID,
    linecolor="rgba(255,255,255,0.1)",
    zerolinecolor="rgba(255,255,255,0.07)",
    tickfont=dict(color=TEXT, size=11),
    titlefont=dict(color=TEXT, size=11),
)

# ── HEADER BAND ────────────────────────────────────────────────────────────────
price_data       = fetch_price()
mkt_txt, mkt_col = nse_status()
ist_now          = datetime.now(timezone(timedelta(hours=5, minutes=30)))
timestamp        = ist_now.strftime("%d %b %Y  %H:%M IST")
price_str        = f"₹{price_data['price']:,.2f}"

if price_data["live"] and price_data["delta"] is not None:
    _dc       = GREEN if price_data["delta"] >= 0 else RED
    delta_html = (f' <span style="color:{_dc};font-size:13px;">'
                  f'{price_data["delta"]:+.2f} ({price_data["pct"]:+.2f}%)</span>')
else:
    delta_html = (' <span style="color:rgba(230,237,243,0.3);font-size:11px;">'
                  '(indicative)</span>')

st.markdown(f"""
<div style="background:{CARD};border-bottom:2px solid {GOLD};padding:12px 28px;
            display:flex;justify-content:space-between;align-items:center;
            margin-bottom:2px;">
  <div>
    <span style="color:{GOLD};font-size:16px;font-weight:800;letter-spacing:0.12em;
                 font-family:'Courier New',monospace;">POLYCAB INDIA</span>
    <span style="color:rgba(230,237,243,0.4);font-size:12px;letter-spacing:0.04em;">
      &nbsp;·&nbsp;NSE: POLYCAB&nbsp;·&nbsp;EQUITY RESEARCH TERMINAL</span>
  </div>
  <div style="text-align:right;font-family:'Courier New',monospace;">
    <span style="color:{TEXT};font-size:17px;font-weight:700;">{price_str}</span>
    {delta_html}
    &nbsp;&nbsp;
    <span style="background:{mkt_col}22;color:{mkt_col};border:1px solid {mkt_col};
                 padding:2px 9px;border-radius:3px;font-size:9px;font-weight:700;
                 letter-spacing:0.12em;">{mkt_txt}</span>
    &nbsp;&nbsp;
    <span style="color:rgba(230,237,243,0.28);font-size:10px;">{timestamp}</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── TABS ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Overview",
    "💰 Financials",
    "🏭 Segments",
    "🎯 Scenarios",
    "👥 Peers",
    "📐 DCF  *(soon)*",
])

# ── TAB 1 · OVERVIEW ──────────────────────────────────────────────────────────
with tab1:
    st.markdown(
        f"<h2 style='color:{GOLD};margin-top:22px;letter-spacing:0.04em;'>"
        "Polycab India Ltd &nbsp;·&nbsp; NSE: POLYCAB</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:rgba(230,237,243,0.45);font-size:12px;margin-top:-10px;'>"
        "India's largest wires &amp; cables manufacturer &nbsp;·&nbsp; "
        "FY26 Revenue: ₹28,884 Cr (+31% YoY) &nbsp;·&nbsp; "
        "FMEG turned profitable for the first time in FY26</p>",
        unsafe_allow_html=True,
    )

    if st.button("⟳  REFRESH PRICE"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Price + target cards
    c1, c2, _spacer = st.columns([1.2, 1.2, 2.6])
    with c1:
        if price_data["live"] and price_data["delta"] is not None:
            delta_txt = f'₹{price_data["delta"]:+.2f}  ({price_data["pct"]:+.2f}%)'
            is_pos    = price_data["delta"] >= 0
        else:
            delta_txt = "indicative — live feed unavailable"
            is_pos    = True
        st.markdown(kpi_card("POLYCAB.NS — LIVE PRICE", price_str, delta_txt, is_pos),
                    unsafe_allow_html=True)
    with c2:
        upside_pct = round((WEIGHTED_TARGET / price_data["price"] - 1) * 100, 1)
        st.markdown(
            kpi_card("PROBABILITY-WEIGHTED TARGET",
                     f"₹{WEIGHTED_TARGET:,}",
                     f"+{upside_pct}% implied upside", True),
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.markdown(kpi_card("FY26 REVENUE",  "₹28,884 Cr", "+31% YoY",         True), unsafe_allow_html=True)
    with k2: st.markdown(kpi_card("FY26 PAT",      "₹2,708 Cr",  "+32% YoY",         True), unsafe_allow_html=True)
    with k3: st.markdown(kpi_card("ROCE",          "29.7%",       "vs KEI 21.3%",     True), unsafe_allow_html=True)
    with k4: st.markdown(kpi_card("FY26 EPS",      "₹173",        "+44% vs FY24 ₹120", True), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:rgba(230,237,243,0.25);font-size:10px;'>"
        "Data as of FY26 (March 2026). Analysis based on company filings, NSE disclosures, "
        "and broker reports. Not investment advice.</p>",
        unsafe_allow_html=True,
    )

# ── TAB 2 · FINANCIALS ────────────────────────────────────────────────────────
with tab2:
    st.markdown(
        f"<h3 style='color:{GOLD};margin-top:22px;'>Financial Performance — FY23 to FY26</h3>",
        unsafe_allow_html=True,
    )

    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(
        x=FISCAL_YEARS, y=REVENUE_CR,
        name="Revenue (₹ Cr)", marker_color=STEEL,
        text=[f"₹{v:,}" for v in REVENUE_CR],
        textposition="outside", textfont=dict(color=TEXT, size=11),
    ))
    fig_rev.add_trace(go.Scatter(
        x=FISCAL_YEARS, y=EBITDA_MARGIN_PCT,
        name="EBITDA Margin %", yaxis="y2",
        mode="lines+markers+text",
        line=dict(color=GOLD, width=3), marker=dict(size=9, color=GOLD),
        text=[f"{v}%" for v in EBITDA_MARGIN_PCT],
        textposition="top center", textfont=dict(color=GOLD, size=11),
    ))
    fig_rev.update_layout(
        **DARK,
        title="Revenue (₹ Crore) vs EBITDA Margin %",
        xaxis=dict(**DARK_AX),
        yaxis=dict(**DARK_AX, title="Revenue (₹ Crore)"),
        yaxis2=dict(**DARK_AX, title="EBITDA Margin %",
                    overlaying="y", side="right", range=[8, 20], showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
    )
    st.plotly_chart(fig_rev, use_container_width=True)
    st.caption("Source: Company filings, NSE disclosures")

    st.divider()

    fig_pat = go.Figure()
    fig_pat.add_trace(go.Bar(
        x=FISCAL_YEARS, y=PAT_CR,
        name="PAT (₹ Cr)", marker_color=GOLD,
        text=[f"₹{v:,} Cr" for v in PAT_CR],
        textposition="outside", textfont=dict(color=TEXT, size=11),
    ))
    fig_pat.update_layout(
        **DARK,
        title="Net Profit After Tax (₹ Crore) — FY23 to FY26",
        xaxis=dict(**DARK_AX),
        yaxis=dict(**DARK_AX, title="PAT (₹ Crore)"),
        showlegend=False,
    )
    st.plotly_chart(fig_pat, use_container_width=True)

    m1, m2, m3, m4 = st.columns(4)
    for col, yr, rev, pat in zip([m1, m2, m3, m4], FISCAL_YEARS, REVENUE_CR, PAT_CR):
        col.metric(f"{yr} PAT Margin", f"{round(pat / rev * 100, 1)}%")
    st.caption("Source: Company filings, NSE disclosures")

# ── TAB 3 · SEGMENTS ──────────────────────────────────────────────────────────
with tab3:
    st.markdown(
        f"<h3 style='color:{GOLD};margin-top:22px;'>Segment Revenue Breakdown</h3>",
        unsafe_allow_html=True,
    )

    fig_seg = go.Figure()
    fig_seg.add_trace(go.Bar(
        x=FISCAL_YEARS, y=WC_REV_CR, name="Wires & Cables", marker_color=STEEL,
        text=[f"₹{v:,}" for v in WC_REV_CR],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(color="white", size=11),
    ))
    fig_seg.add_trace(go.Bar(
        x=FISCAL_YEARS, y=FMEG_REV_CR, name="FMEG", marker_color=GOLD,
        text=[f"₹{v:,}" for v in FMEG_REV_CR],
        textposition="inside", insidetextanchor="middle",
        textfont=dict(color="#0d1117", size=11),
    ))
    fig_seg.update_layout(
        **DARK,
        title="Revenue by Segment (₹ Crore) — Wires & Cables vs FMEG",
        barmode="stack",
        xaxis=dict(**DARK_AX),
        yaxis=dict(**DARK_AX, title="Revenue (₹ Crore)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02,
                    xanchor="right", x=1,
                    bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT)),
    )
    st.plotly_chart(fig_seg, use_container_width=True)
    st.info(
        "**FMEG (Fast-Moving Electrical Goods):** fans, switches, lighting, solar products, "
        "home appliances. Grew from ~5% to ~7% of total revenue. Solar delivered ~2x YoY "
        "growth in FY26 and became the largest FMEG category."
    )

    st.divider()
    st.markdown(
        f"<h4 style='color:{GOLD};'>FMEG Profitability — The Key Inflection</h4>",
        unsafe_allow_html=True,
    )

    dot_colors = [RED if v < 0 else GREEN for v in FMEG_PROFIT_CR]
    fig_fmeg = go.Figure()
    fig_fmeg.add_trace(go.Scatter(
        x=FISCAL_YEARS, y=FMEG_PROFIT_CR,
        mode="lines+markers+text",
        line=dict(color=GOLD, width=3),
        marker=dict(size=12, color=dot_colors, line=dict(color=CARD, width=2)),
        text=[f"₹{v} Cr" for v in FMEG_PROFIT_CR],
        textposition="top center", textfont=dict(color=TEXT, size=11),
        name="FMEG Profit / Loss",
    ))
    fig_fmeg.add_hline(y=0, line_dash="dash",
                       line_color="rgba(255,255,255,0.28)",
                       annotation_text="Break-even", annotation_position="left",
                       annotation_font_color="rgba(230,237,243,0.45)")
    fig_fmeg.add_annotation(
        x="FY26", y=54.8, text="✅ First profitable year",
        showarrow=True, arrowhead=2, ax=60, ay=-50,
        font=dict(color=GREEN, size=13), arrowcolor=GREEN,
    )
    fig_fmeg.update_layout(
        **DARK,
        title="FMEG Segment Profit / Loss (₹ Crore)",
        xaxis=dict(**DARK_AX),
        yaxis=dict(**DARK_AX, title="Profit / Loss (₹ Crore)"),
        showlegend=False,
    )
    st.plotly_chart(fig_fmeg, use_container_width=True)
    st.caption("Project Spring targets FMEG EBITDA margins of 8–10% by FY30")

# ── TAB 4 · SCENARIOS ─────────────────────────────────────────────────────────
with tab4:
    st.markdown(
        f"<h3 style='color:{GOLD};margin-top:22px;'>Bull / Base / Bear Scenario Framework — FY28E</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:rgba(230,237,243,0.45);font-size:12px;margin-top:-10px;'>"
        "Bottoms-up segment revenue builds. Each scenario shows assumptions, not just a price range.</p>",
        unsafe_allow_html=True,
    )

    card_cols = st.columns(3)
    for col, sc in zip(card_cols, SCENARIOS.values()):
        with col:
            st.markdown(f"""
            <div style="background:{CARD};border:2px solid {sc['color']};border-radius:8px;
                        padding:22px 18px;text-align:center;">
              <h3 style="color:{sc['color']};margin:0 0 4px 0;font-size:17px;
                         letter-spacing:0.06em;">{sc['label']}</h3>
              <p style="font-size:11px;color:rgba(230,237,243,0.4);margin:0 0 12px 0;">
                Probability:&nbsp;
                <b style="color:{sc['color']};font-size:13px;">{sc['prob']}%</b>
              </p>
              <hr style="border-color:{sc['color']}44;margin:10px 0 14px 0;">
              <p style="margin:10px 0;color:rgba(230,237,243,0.6);font-size:11px;text-transform:uppercase;letter-spacing:0.06em;">FY28E Revenue</p>
              <b style="font-size:19px;font-family:'Courier New',monospace;color:{TEXT};">₹{sc['fy28_rev']:,} Cr</b>
              <p style="margin:10px 0 0 0;color:rgba(230,237,243,0.6);font-size:11px;text-transform:uppercase;letter-spacing:0.06em;">EBITDA Margin</p>
              <b style="font-size:19px;font-family:'Courier New',monospace;color:{TEXT};">{sc['ebitda_m']}%</b>
              <p style="margin:10px 0 0 0;color:rgba(230,237,243,0.6);font-size:11px;text-transform:uppercase;letter-spacing:0.06em;">FY28E EPS</p>
              <b style="font-size:19px;font-family:'Courier New',monospace;color:{TEXT};">₹{sc['eps']}</b>
              <hr style="border-color:{sc['color']}44;margin:16px 0 10px 0;">
              <p style="font-size:11px;color:rgba(230,237,243,0.4);margin:0;">Price Target</p>
              <p style="font-size:26px;font-weight:800;color:{sc['color']};
                         font-family:'Courier New',monospace;margin:4px 0 0 0;">
                ₹{sc['target']:,}</p>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    fig_sc = go.Figure()
    for sc in SCENARIOS.values():
        fig_sc.add_trace(go.Bar(
            y=[sc["label"]], x=[sc["target"]], orientation="h",
            marker_color=sc["color"],
            text=f"  ₹{sc['target']:,}  ({sc['prob']}% prob)",
            textposition="outside", textfont=dict(color=TEXT, size=11),
            name=sc["label"],
        ))
    fig_sc.add_vline(x=CURRENT_PRICE, line_dash="dash",
                     line_color="rgba(255,255,255,0.4)", line_width=2,
                     annotation_text=f"Current ₹{CURRENT_PRICE:,}",
                     annotation_position="top",
                     annotation_font_color=TEXT)
    fig_sc.add_vline(x=WEIGHTED_TARGET, line_dash="dot",
                     line_color=GOLD, line_width=2,
                     annotation_text=f"Weighted target ₹{WEIGHTED_TARGET:,}",
                     annotation_position="bottom",
                     annotation_font_color=GOLD)
    fig_sc.update_layout(
        **DARK,
        title="FY28E Price Targets vs Current Price (₹)",
        xaxis=dict(**DARK_AX, title="Price (₹)", range=[0, 16500]),
        yaxis=dict(**DARK_AX),
        showlegend=False, height=280,
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    upside = round((WEIGHTED_TARGET / CURRENT_PRICE - 1) * 100, 1)
    st.metric(
        "Probability-Weighted Target", f"₹{WEIGHTED_TARGET:,}",
        delta=f"+{upside}% from ₹{CURRENT_PRICE:,}  ·  calc: (13700×30%) + (10400×50%) + (6900×20%)",
    )

    st.divider()
    st.markdown(
        f"<h4 style='color:{GOLD};'>Key Swing Factors — What Determines the Outcome</h4>",
        unsafe_allow_html=True,
    )
    for factor in SWING_FACTORS:
        st.markdown(f"- {factor}")

# ── TAB 5 · PEERS ─────────────────────────────────────────────────────────────
with tab5:
    st.markdown(
        f"<h3 style='color:{GOLD};margin-top:22px;'>Peer Comparison — Indian Cables & FMEG Universe</h3>",
        unsafe_allow_html=True,
    )

    def highlight_polycab(row):
        if row["Company"] == "Polycab India":
            return [f"background-color:rgba(197,165,90,0.14);font-weight:bold;color:{GOLD}"] * len(row)
        return [f"color:{TEXT}"] * len(row)

    st.dataframe(
        PEERS.style.apply(highlight_polycab, axis=1),
        use_container_width=True, hide_index=True,
    )

    st.markdown(f"""
    <div style="background:{CARD};border:1px solid rgba(197,165,90,0.2);border-radius:6px;
                padding:18px 22px;margin-top:16px;line-height:1.75;">
      <span style="color:{GOLD};font-weight:700;">Valuation context:&nbsp;</span>
      <span style="color:rgba(230,237,243,0.85);">
        Polycab trades at 44.8x trailing P/E — a <b>44% premium to the industry average (31.2x)</b>
        but a significant discount to Havells (65.4x), which is further along in its FMEG journey.
        Polycab's ROCE of <b>29.7% vs KEI's 21.3%</b> partly justifies the premium.
        The central question for the next 3–5 years: does Polycab's FMEG trajectory re-rate it
        toward a Havells-like multiple? If yes, the bull case target expands materially beyond ₹13,700.
      </span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()
    st.caption(
        "Source: NSE data, broker reports, Trade Brains, MarketsMojo | May 2026  |  "
        "Industry P/E average: 31.2x"
    )

# ── TAB 6 · DCF ───────────────────────────────────────────────────────────────
with tab6:
    st.markdown(
        f"<h3 style='color:{GOLD};margin-top:22px;'>DCF & Growth Analysis</h3>",
        unsafe_allow_html=True,
    )
    st.markdown(f"""
    <div style="background:{CARD};border:1px solid rgba(197,165,90,0.22);border-radius:6px;
                padding:24px 28px;margin-top:8px;">
      <p style="color:{GOLD};font-size:14px;font-weight:700;margin:0 0 8px 0;">
        🚧 &nbsp;COMING SOON</p>
      <p style="color:rgba(230,237,243,0.65);margin:0 0 16px 0;">
        Interactive DCF model, terminal value sensitivity heatmap, and revenue growth decomposition.</p>
      <hr style="border-color:rgba(197,165,90,0.14);margin:0 0 16px 0;">
      <p style="color:{TEXT};font-weight:700;margin:0 0 10px 0;">Planned features:</p>
      <ul style="color:rgba(230,237,243,0.6);line-height:2.1;margin:0;padding-left:20px;">
        <li>Interactive DCF with adjustable WACC (8–14%) and terminal growth rate (3–8%)</li>
        <li>Sensitivity heatmap: implied price for every WACC × terminal growth combination</li>
        <li>Revenue growth decomposition: volume vs price vs mix</li>
        <li>Historical implied growth rate vs current market pricing</li>
        <li>Comparison of intrinsic value vs current market price</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)
    st.caption("To request early access, ping the author via LinkedIn.")
