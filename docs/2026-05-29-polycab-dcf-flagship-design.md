# Polycab DCF Flagship — Design Spec

**Date:** 2026-05-29
**Status:** Draft for review
**Build:** 1 of 2 (this = DCF flagship; Build 2 = screener + comps engine, separate spec)
**Target file:** `polycab_dashboard/app.py` tab6 (replaces the "DCF *(soon)*" stub at lines ~585–600), plus a new pure module `polycab_dashboard/dcf.py` and tests `polycab_dashboard/tests/test_dcf.py`.

---

## 1. Goal

Turn the dashboard's empty DCF tab into a defensible, interactive valuation engine for Polycab India — a **two-stage FCFF DCF with a CAPM WACC build-up**, a **reverse DCF** (market-implied expectations), a **WACC × terminal-growth sensitivity heatmap**, and a **football-field**. The model must be something the user can defend line-by-line in an IB/AM interview.

## 2. The finding that shapes this design (read first)

A plain forward DCF on Polycab does **not** produce "buy." This is not a bug — it is the central insight, and the design is built around showing it honestly:

- Polycab trades at ~49× EV/EBITDA and ~70× earnings (₹9,664 price, ₹1.45 lakh Cr mcap on FY25 EBITDA ₹2,960 Cr / PAT ₹2,045 Cr).
- It reinvests heavily (₹6,000–8,000 Cr capex planned over 5 yrs; working-capital-intensive cables business), so near-term FCFF is thin.
- A two-stage FCFF DCF at India's real cost of capital (Ke ≈ 14%, because the 10-yr G-sec is ~7%) values it at **₹1,624/sh (Gordon)** to **₹3,883/sh (18× exit)** — a 60–83% gap to market.

The professional response is **not** to fudge assumptions until the model prints ₹9,664. It is to **flip to a reverse DCF** and state what the price implies:

- **Implied expected return ≈ 6.8%** vs. a ~14% cost of equity → the buyer is underwriting a ~7-point-too-low return.
- **To justify ₹9,664** you need either **~56% revenue growth for 5 years** (absurd for a cables maker) **or a ~50× perpetual exit multiple** (≈ today's 49× held forever).

This forward-vs-reverse framing is the flagship's differentiator. The deliverable teaches a real lesson: a forward DCF is the wrong *sole* tool for a high-multiple reinvesting compounder; relative valuation (Build 2 comps) and expectations analysis complete the picture.

## 3. Verified base-year inputs (FY25, year ended Mar 2025)

All figures sourced and verified (see §13). FY25 is the last **audited** year and is the DCF base year (`Year 0`).

| Input | Value | Notes / source |
|---|---|---|
| Revenue₀ | ₹22,408 Cr | +24% YoY (consolidated) |
| EBITDA / margin | ₹2,960 Cr / **13.2%** | |
| PAT | ₹2,045 Cr | +13.5% YoY |
| EPS | ₹133 | standalone basis |
| D&A | ~₹300 Cr (~1.4% of rev) | +21.7% YoY; **verify exact from AR2025** |
| Net cash | **+₹1,432 Cr** (Mar-25) | net-debt = −₹1,432 Cr; add in bridge |
| CFO (FY25) | ₹1,800 Cr | +39.5% YoY (CFO < PAT confirms WC drag) |
| Shares outstanding | 15.04 cr | mcap ₹1,44,738 Cr ÷ ₹9,664 ✓ |
| Tax rate | 25.17% | India new regime |
| Current price | live via `fetch_price()`; fallback ₹9,664 | 52-wk ₹5,760–9,696 |

## 4. Data correction (narrow, honest)

`app.py` has `FISCAL_YEARS = ["FY23","FY24","FY25","FY26"]`. The **FY23–FY25 actuals are correct** (FY25 PAT ₹2,046 ≈ reality). Only the **FY26 column (₹28,884 Cr / ₹2,708 Cr) is an estimate**, not an actual.

Required changes:
1. Relabel the FY26 series entry as **"FY26E"** in `FISCAL_YEARS` (and any chart text), so estimates are not shown as actuals.
2. Optionally true-up FY25 EBITDA margin from 14.0 → 13.2% to match the AR (low priority; cosmetic).
3. The DCF **anchors on FY25 actuals (₹22,408 Cr)** — never the FY26 estimate.

## 5. Architecture

Extract the valuation math into a **pure module with zero Streamlit imports**, unit-tested with `pytest`. `app.py` imports it and owns only UI. This makes a sign error catchable offline (the failure mode that broke the dashboard before) and lets Build 2's comps engine reuse the discounting helpers.

```
polycab_dashboard/
  app.py            # tab6 UI calls into dcf.py; reuses theme (_dark, kpi_card, GOLD…)
  dcf.py            # NEW — pure functions + dataclasses, no streamlit
  tests/
    test_dcf.py     # NEW — unit + golden-master
```

## 6. `dcf.py` interface (concrete)

```python
from dataclasses import dataclass

@dataclass
class WACCInputs:
    rf: float = 0.070          # India 10-yr G-sec
    erp: float = 0.075         # India equity risk premium (Damodaran)
    beta: float = 0.95         # verify; Polycab is a quality large-cap
    cost_of_debt: float = 0.080
    tax: float = 0.2517
    equity_weight: float = 0.95  # near debt-free / net cash
    debt_weight: float = 0.05

@dataclass
class DCFInputs:
    rev0: float = 22408.0
    ebitda_margin: float = 0.132
    da_pct: float = 0.014          # D&A as % of revenue
    tax: float = 0.2517
    capex_pct_stage1: float = 0.055   # heavy expansion phase
    capex_pct_terminal: float = 0.035 # maintenance level
    nwc_pct: float = 0.18          # ΔNWC as % of Δrevenue
    growth_stage1: float = 0.16    # yrs 1..N1
    growth_terminal: float = 0.05  # perpetuity g (also fade target)
    years_stage1: int = 5
    years_fade: int = 5            # linear fade growth_stage1 → growth_terminal
    exit_multiple: float = 18.0    # EV/EBITDA for exit-multiple TV
    net_cash: float = 1432.0       # + = net cash
    shares: float = 15.04

def compute_wacc(w: WACCInputs) -> dict          # {"ke","cost_of_debt_at","wacc"}
def growth_path(d: DCFInputs) -> list[float]     # len = years_stage1 + years_fade
def project_fcff(d: DCFInputs) -> list[dict]     # per yr: t,growth,revenue,ebit,nopat,da,capex,dnwc,fcff,ebitda
def terminal_value_gordon(fcff_last, g, wacc) -> float    # raises/inf-guard if wacc<=g
def terminal_value_exit(ebitda_last, multiple) -> float
def intrinsic_value(d: DCFInputs, wacc: float, tv_method: str) -> dict
    # {"pv_fcff","pv_tv","enterprise_value","equity_value","per_share","tv_pct_of_ev"}; tv_method in {"gordon","exit"}
def sensitivity_grid(d, waccs: list[float], g_terms: list[float], tv_method="gordon") -> list[list[float]]  # per-share

# Reverse DCF — each returns a value OR None when no solution exists in range
def implied_return(d, price, tv_method="gordon", lo=None, hi=0.40) -> float|None
    # solve wacc s.t. per_share==price. For gordon, lo defaults to growth_terminal+ε (singularity guard).
def implied_growth_stage1(d, wacc, price, cap=0.60) -> float|None
    # solve growth_stage1; None if even `cap` can't reach price.
def implied_exit_multiple(d, wacc, price, lo=1.0, hi=200.0) -> float|None
    # solve exit_multiple s.t. per_share==price.

def _bisect(f, lo, hi, tol=1e-4, max_iter=200) -> float|None
    # MUST return None when sign(f(lo))==sign(f(hi)) (no root in range) — do NOT return a boundary.
```

## 7. Forward DCF mechanics

- **Two-stage projection.** Stage 1: `years_stage1` years at `growth_stage1`. Fade: `years_fade` years where growth interpolates linearly from `growth_stage1` to `growth_terminal`. Total explicit horizon = 10 yrs default.
- Per year: `Rev_t = Rev_{t-1}×(1+g_t)` → `EBIT = Rev_t×(ebitda_margin − da_pct)` → `NOPAT = EBIT×(1−tax)` → `FCFF = NOPAT + D&A − Capex − ΔNWC`, where `Capex = Rev_t×capex_pct` (stage1 vs terminal pct), `D&A = Rev_t×da_pct`, `ΔNWC = (Rev_t − Rev_{t-1})×nwc_pct`.
- Discount each FCFF at `wacc`. Sum = `pv_fcff`.
- **Terminal value, both methods:** Gordon = `FCFF_last×(1+g_term)/(wacc − g_term)`; Exit = `EBITDA_last × exit_multiple`. Discount TV at `(1+wacc)^horizon`.
- **Bridge:** `EV = pv_fcff + pv_tv` → `Equity = EV + net_cash` → `per_share = Equity / shares`.

## 8. Reverse DCF (market-implied expectations)

Three angles on "what does ₹9,664 require?", each computed by root-finding and each handling no-solution gracefully (display the insight, not a misleading number):

1. **Implied expected return** (primary): the discount rate that sets intrinsic = price. Headline: *"~6.8% vs a ~14% cost of equity."* Gordon search bounded above `growth_terminal`.
2. **Implied perpetual exit multiple:** the EV/EBITDA (held into terminal) that justifies the price at base WACC. Headline: *"~50× — i.e., today's 49× held forever."*
3. **Implied Stage-1 growth:** the 5-yr revenue CAGR that justifies the price at base WACC, capped at 60%. Headline: *"~56% for 5 years — implausible."* When the cap can't reach the price, render *"no realistic solution — price unjustifiable on growth alone."*

## 9. Sensitivity heatmap

Plotly heatmap, dark/gold theme. Rows = WACC (computed center ±1.5%, 5 steps). Cols = terminal g (3%–7%). Cells = intrinsic ₹/share (Gordon). Annotate cells with values; mark the base-case cell. (Decision: cells show ₹/share, not % upside — absolute value reads cleaner against the football-field.)

## 10. Football-field

Horizontal bars on a shared ₹/share axis:
- DCF range (Gordon, across the heatmap WACC×g corners) — low.
- DCF range (exit-multiple, 18× → 34×) — ₹3,883 → ₹6,740.
- **Comps-implied — placeholder/empty slot, filled by Build 2.**
- 52-week range (₹5,760 → ₹9,696).
- Weighted scenario target (₹10,490, existing).
- Vertical line at current price (live).

## 11. UI layout (tab6, reuses existing theme)

- **Left control column:** CAPM build-up inputs (Rf, ERP, β, Kd, weights) → live-computed WACC shown prominently; then DCF driver sliders (growth_stage1, EBITDA margin, tax, capex % stage1/terminal, ΔNWC %, terminal g, exit multiple, horizon). `da_pct` stays a fixed minor assumption, not a slider.
- **Main column:** KPI cards (`kpi_card`) for WACC, intrinsic ₹/share (Gordon & exit), upside/downside %, implied expected return. Then the 10-yr FCFF table, the sensitivity heatmap, and the full-width football-field.
- A short, bold **"Reverse DCF / what the price implies"** callout box stating the three implied metrics.
- All charts via the existing `_dark(fig, title)` helper; colors `GOLD/STEEL/GREEN/RED`.

## 12. Default assumptions & validated expected outputs (golden-master anchors)

With the §6 defaults: **Ke = 14.1%, WACC = 13.7%.** Intrinsic (Gordon) ≈ **₹1,624**, (exit 18×) ≈ **₹3,883**; TV ≈ 63% of EV. Implied return ≈ **6.8%**; implied exit multiple ≈ **50×**; implied Stage-1 growth ≈ **56%**. These are the golden-master test targets (lock to final pinned D&A/capex; assert within ±1%).

## 13. Testing strategy (`tests/test_dcf.py`)

- `compute_wacc` returns Ke 14.1% / WACC 13.7% for defaults.
- `project_fcff` length = 10; growth_path ends exactly at `growth_terminal`; FCFF signs sane.
- `terminal_value_gordon` matches hand-calc; guards `wacc<=g`.
- `intrinsic_value` golden master (Gordon ≈ ₹1,624, exit ≈ ₹3,883 within tol).
- **Reverse no-solution tests:** `_bisect` returns `None` when `f(lo)`/`f(hi)` share sign; `implied_return` excludes the Gordon singularity; `implied_growth_stage1` returns `None` when cap insufficient.
- `sensitivity_grid` shape and monotonicity (value falls as WACC rises, rises as g rises).

## 14. Out of scope (YAGNI)

No live financials API (base year hardcoded from AR). No Monte Carlo. No comps (Build 2). No WACC manual override (heatmap covers stress). No multi-company (this build is Polycab-only).

## 15. Acceptance criteria

1. `dcf.py` is import-clean with no Streamlit dependency; `pytest tests/test_dcf.py` passes.
2. tab6 renders: CAPM panel, driver sliders, KPI cards, FCFF table, sensitivity heatmap, football-field, reverse-DCF callout — all in the dark/gold theme.
3. Moving any slider live-recomputes every output.
4. FY26 is labeled "FY26E" wherever shown.
5. App runs clean under the deploy Python (3.12) via the offline mocked-Streamlit dry-run before push.

## 16. Sources

- Price / mcap / shares: [stockanalysis.com](https://stockanalysis.com/quote/nse/POLYCAB/market-cap/), [tickertape.in](https://www.tickertape.in/stocks/polycab-india-POLC)
- FY25 results (rev/EBITDA/PAT/EPS): [CableCommunity](https://cablecommunity.com/polycab-india-fy25-financials-revenue-grows-24-pat-jumps-13/), [Equitymaster AR analysis](https://www.equitymaster.com/research-it/annual-results-analysis/POLI/POLYCAB-INDIA-2024-25-Annual-Report-Analysis/12221), [Polycab AR2025](https://polycab.com/ar2025)
- Cash flow / capex / net cash: [Equitymaster](https://www.equitymaster.com/research-it/annual-results-analysis/POLI/POLYCAB-INDIA-2024-25-Annual-Report-Analysis/12221), [Q4FY25 earnings deck](https://cms.polycab.com/media/kc2k4qwv/q4fy25-earnings-presentation.pdf)
