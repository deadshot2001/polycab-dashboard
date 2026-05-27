import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Polycab India — Stock Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── COLOUR PALETTE ────────────────────────────────────────────────────────────
NAVY  = "#1B2A4A"
STEEL = "#4A6FA5"
GOLD  = "#C5A55A"
GREEN = "#27AE60"
RED   = "#C0392B"
GRAY  = "#6C757D"

# ── DATA BLOCK ────────────────────────────────────────────────────────────────
# All Polycab numbers. Edit these to update the dashboard — no other code changes needed.

FISCAL_YEARS      = ["FY23", "FY24", "FY25", "FY26"]
REVENUE_CR        = [13912, 18260, 22052, 28884]   # ₹ Crore
EBITDA_CR         = [1530,  2190,  3090,  4069]    # ₹ Crore
EBITDA_MARGIN_PCT = [11.0,  12.0,  14.0,  14.1]   # %
PAT_CR            = [1272,  1787,  2046,  2708]    # ₹ Crore
EPS_INR           = [85,    120,   140,   173]     # ₹ per share

WC_REV_CR      = [12100, 15600, 18524, 24400]      # Wires & Cables ₹ Crore
FMEG_REV_CR    = [730,   1100,  1654,  2069]       # FMEG ₹ Crore
FMEG_PROFIT_CR = [-80.0, -50.0, -38.9, 54.8]      # ₹ Crore (negative = loss)

SCENARIOS = {
    "bull": {"label": "Bull Case", "prob": 30, "fy28_rev": 43500, "ebitda_m": 15.8, "eps": 305, "target": 13700, "color": GREEN},
    "base": {"label": "Base Case", "prob": 50, "fy28_rev": 40900, "ebitda_m": 14.5, "eps": 260, "target": 10400, "color": STEEL},
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

# ── LIVE PRICE ────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_price():
    try:
        t  = yf.Ticker("POLYCAB.NS")
        fi = t.fast_info
        price = round(float(fi.last_price), 2)
        prev  = round(float(fi.previous_close), 2)
        delta = round(price - prev, 2)
        pct   = round(delta / prev * 100, 2)
        return {"price": price, "delta": delta, "pct": pct, "live": True}
    except Exception:
        return {"price": CURRENT_PRICE, "delta": None, "pct": None, "live": False}

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Overview",
    "💰 Financials",
    "🏭 Segments",
    "🎯 Scenarios",
    "👥 Peers",
    "📐 DCF  *(soon)*",
])

with tab1:
    st.title("Polycab India Ltd  ·  NSE: POLYCAB")
    st.caption(
        "India's largest wires & cables manufacturer  ·  "
        "FY26 Revenue: ₹28,884 Cr (+31% YoY)  ·  "
        "FMEG turned profitable for the first time in FY26"
    )

    if st.button("🔄 Refresh live price"):
        st.cache_data.clear()

    price_data = fetch_price()

    col_price, col_target, col_spacer = st.columns([1.2, 1.2, 3])
    with col_price:
        if price_data["live"]:
            st.metric(
                label="Current Price (POLYCAB.NS)",
                value=f"₹{price_data['price']:,.2f}",
                delta=f"₹{price_data['delta']:+.2f}  ({price_data['pct']:+.2f}%)",
            )
        else:
            st.metric(label="Last Known Price", value=f"₹{price_data['price']:,}")
            st.caption("⚠️ Live price unavailable — showing last known ₹9,199")
    with col_target:
        upside_pct = round((WEIGHTED_TARGET / price_data["price"] - 1) * 100, 1)
        st.metric(
            label="Probability-Weighted Target",
            value=f"₹{WEIGHTED_TARGET:,}",
            delta=f"+{upside_pct}% implied upside",
        )

    st.divider()

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("FY26 Revenue",  "₹28,884 Cr", "+31% YoY")
    k2.metric("FY26 PAT",      "₹2,708 Cr",  "+32% YoY")
    k3.metric("ROCE",          "29.7%",       "vs KEI 21.3%")
    k4.metric("FY26 EPS",      "₹173",        "+44% vs FY24 ₹120")

    st.divider()
    st.caption(
        "Data as of FY26 (March 2026).  "
        "Analysis based on company filings, NSE disclosures, and broker reports.  "
        "Not investment advice."
    )

with tab2:
    st.header("Financial Performance — FY23 to FY26")

    fig_rev = go.Figure()
    fig_rev.add_trace(go.Bar(
        x=FISCAL_YEARS, y=REVENUE_CR,
        name="Revenue (₹ Cr)", marker_color=NAVY,
        text=[f"₹{v:,} Cr" for v in REVENUE_CR], textposition="outside",
    ))
    fig_rev.add_trace(go.Scatter(
        x=FISCAL_YEARS, y=EBITDA_MARGIN_PCT,
        name="EBITDA Margin %", yaxis="y2",
        mode="lines+markers+text",
        line=dict(color=GOLD, width=3), marker=dict(size=8),
        text=[f"{v}%" for v in EBITDA_MARGIN_PCT], textposition="top center",
    ))
    fig_rev.update_layout(
        title="Revenue (₹ Crore) vs EBITDA Margin %",
        yaxis=dict(title="Revenue (₹ Crore)", showgrid=True, gridcolor="#E9ECEF"),
        yaxis2=dict(title="EBITDA Margin %", overlaying="y", side="right", range=[8, 20], showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(color=NAVY),
    )
    st.plotly_chart(fig_rev, use_container_width=True)
    st.caption("Source: Company filings, NSE disclosures")

    st.divider()

    fig_pat = go.Figure()
    fig_pat.add_trace(go.Bar(
        x=FISCAL_YEARS, y=PAT_CR,
        marker_color=STEEL,
        text=[f"₹{v:,} Cr" for v in PAT_CR], textposition="outside",
        name="PAT (₹ Cr)",
    ))
    fig_pat.update_layout(
        title="Net Profit After Tax (₹ Crore) — FY23 to FY26",
        yaxis_title="PAT (₹ Crore)",
        yaxis=dict(showgrid=True, gridcolor="#E9ECEF"),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(color=NAVY), showlegend=False,
    )
    st.plotly_chart(fig_pat, use_container_width=True)

    m1, m2, m3, m4 = st.columns(4)
    for col, yr, rev, pat in zip([m1, m2, m3, m4], FISCAL_YEARS, REVENUE_CR, PAT_CR):
        col.metric(f"{yr} PAT Margin", f"{round(pat / rev * 100, 1)}%")
    st.caption("Source: Company filings, NSE disclosures")

with tab3:
    st.header("Segment Revenue Breakdown")

    fig_seg = go.Figure()
    fig_seg.add_trace(go.Bar(
        x=FISCAL_YEARS, y=WC_REV_CR, name="Wires & Cables", marker_color=NAVY,
        text=[f"₹{v:,}" for v in WC_REV_CR], textposition="inside", insidetextanchor="middle",
    ))
    fig_seg.add_trace(go.Bar(
        x=FISCAL_YEARS, y=FMEG_REV_CR, name="FMEG", marker_color=GOLD,
        text=[f"₹{v:,}" for v in FMEG_REV_CR], textposition="inside", insidetextanchor="middle",
    ))
    fig_seg.update_layout(
        title="Revenue by Segment (₹ Crore) — Wires & Cables vs FMEG",
        barmode="stack", yaxis_title="Revenue (₹ Crore)",
        yaxis=dict(showgrid=True, gridcolor="#E9ECEF"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(color=NAVY),
    )
    st.plotly_chart(fig_seg, use_container_width=True)
    st.info(
        "**FMEG (Fast-Moving Electrical Goods):** fans, switches, lighting, solar products, "
        "home appliances. Grew from ~5% to ~7% of total revenue. Solar delivered ~2x YoY "
        "growth in FY26 and became the largest FMEG category."
    )

    st.divider()
    st.subheader("FMEG Profitability — The Key Inflection")

    dot_colors = [RED if v < 0 else GREEN for v in FMEG_PROFIT_CR]
    fig_fmeg = go.Figure()
    fig_fmeg.add_trace(go.Scatter(
        x=FISCAL_YEARS, y=FMEG_PROFIT_CR,
        mode="lines+markers+text",
        line=dict(color=STEEL, width=3),
        marker=dict(size=12, color=dot_colors, line=dict(color="white", width=2)),
        text=[f"₹{v} Cr" for v in FMEG_PROFIT_CR], textposition="top center",
        name="FMEG Profit / Loss",
    ))
    fig_fmeg.add_hline(y=0, line_dash="dash", line_color=GRAY,
                       annotation_text="Break-even", annotation_position="left")
    fig_fmeg.add_annotation(
        x="FY26", y=54.8, text="✅ First profitable year",
        showarrow=True, arrowhead=2, ax=60, ay=-50,
        font=dict(color=GREEN, size=13), arrowcolor=GREEN,
    )
    fig_fmeg.update_layout(
        title="FMEG Segment Profit / Loss (₹ Crore)",
        yaxis_title="Profit / Loss (₹ Crore)",
        yaxis=dict(showgrid=True, gridcolor="#E9ECEF"),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(color=NAVY), showlegend=False,
    )
    st.plotly_chart(fig_fmeg, use_container_width=True)
    st.caption("Project Spring targets FMEG EBITDA margins of 8–10% by FY30")

with tab4:
    st.header("Bull / Base / Bear Scenario Framework — FY28E")
    st.caption("Bottoms-up segment revenue builds. Each scenario shows assumptions, not just a price range.")

    card_cols = st.columns(3)
    for col, sc in zip(card_cols, SCENARIOS.values()):
        with col:
            st.markdown(
                f"""
                <div style="border:2px solid {sc['color']};border-radius:10px;
                            padding:18px 14px;text-align:center;background:white;">
                    <h3 style="color:{sc['color']};margin:0 0 4px 0">{sc['label']}</h3>
                    <p style="font-size:11px;color:#666;margin:0 0 10px 0">
                        Probability: <b>{sc['prob']}%</b></p>
                    <hr style="border-color:{sc['color']};margin:8px 0">
                    <p style="margin:6px 0">FY28E Revenue<br>
                        <b style="font-size:16px">₹{sc['fy28_rev']:,} Cr</b></p>
                    <p style="margin:6px 0">EBITDA Margin<br>
                        <b style="font-size:16px">{sc['ebitda_m']}%</b></p>
                    <p style="margin:6px 0">FY28E EPS<br>
                        <b style="font-size:16px">₹{sc['eps']}</b></p>
                    <p style="margin:10px 0 0 0;font-size:20px;font-weight:bold;color:{sc['color']}">
                        Target: ₹{sc['target']:,}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()

    fig_sc = go.Figure()
    for sc in SCENARIOS.values():
        fig_sc.add_trace(go.Bar(
            y=[sc["label"]], x=[sc["target"]], orientation="h",
            marker_color=sc["color"],
            text=f"  ₹{sc['target']:,}  ({sc['prob']}% prob)", textposition="outside",
            name=sc["label"],
        ))
    fig_sc.add_vline(x=CURRENT_PRICE, line_dash="dash", line_color=NAVY, line_width=2,
                     annotation_text=f"Current ₹{CURRENT_PRICE:,}", annotation_position="top",
                     annotation_font_color=NAVY)
    fig_sc.add_vline(x=WEIGHTED_TARGET, line_dash="dot", line_color=GOLD, line_width=2,
                     annotation_text=f"Weighted target ₹{WEIGHTED_TARGET:,}",
                     annotation_position="bottom", annotation_font_color=GOLD)
    fig_sc.update_layout(
        title="FY28E Price Targets vs Current Price (₹)",
        xaxis_title="Price (₹)", xaxis=dict(range=[0, 16500]),
        plot_bgcolor="white", paper_bgcolor="white", font=dict(color=NAVY),
        showlegend=False, height=280,
    )
    st.plotly_chart(fig_sc, use_container_width=True)

    upside = round((WEIGHTED_TARGET / CURRENT_PRICE - 1) * 100, 1)
    st.metric(
        "Probability-Weighted Target", f"₹{WEIGHTED_TARGET:,}",
        delta=f"+{upside}% from ₹{CURRENT_PRICE:,}  ·  calc: (13700×30%) + (10400×50%) + (6900×20%)",
    )

    st.divider()
    st.subheader("Key Swing Factors — What Determines the Outcome")
    for factor in SWING_FACTORS:
        st.markdown(f"- {factor}")

with tab5:
    st.header("Peer Comparison — Indian Cables & FMEG Universe")

    def highlight_polycab(row):
        if row["Company"] == "Polycab India":
            return ["background-color: #E8F4FD; font-weight: bold"] * len(row)
        return [""] * len(row)

    st.dataframe(PEERS.style.apply(highlight_polycab, axis=1), use_container_width=True, hide_index=True)

    st.markdown("""
    **Valuation context:**
    Polycab trades at 44.8x trailing P/E — a **44% premium to the industry average (31.2x)** but a
    significant discount to Havells (65.4x), which is further along in its FMEG journey.
    Polycab's ROCE of **29.7% vs KEI's 21.3%** partly justifies the premium.
    The central question for the next 3–5 years: does Polycab's FMEG trajectory re-rate it
    toward a Havells-like multiple? If yes, the bull case target expands materially beyond ₹13,700.
    """)

    st.divider()
    st.caption("Source: NSE data, broker reports, Trade Brains, MarketsMojo | May 2026  |  Industry P/E average: 31.2x")

with tab6:
    st.header("DCF & Growth Analysis")
    st.info(
        "🚧 **Coming soon.** This tab will contain an interactive DCF model, "
        "terminal value sensitivity heatmap, and revenue growth decomposition."
    )
    st.markdown("""
    **Planned features:**
    - Interactive DCF with adjustable WACC (8–14%) and terminal growth rate (3–8%)
    - Sensitivity heatmap: implied price for every WACC × terminal growth combination
    - Revenue growth decomposition: volume vs price vs mix
    - Historical implied growth rate vs current market pricing
    - Comparison of intrinsic value vs current market price
    """)
    st.caption("To request early access, ping the author via LinkedIn.")
