import streamlit as st
import pandas as pd
import numpy as np

# =========================
# App Config & Global Styles
# =========================
st.set_page_config(
    page_title="Retirement FI Calculator",
    page_icon="🧮",
    layout="wide",
)

st.markdown(
    """
    <style>
      :root {
        --bg: #0b0f1a;
        --card: #12182a;
        --card-2: #0e1424;
        --muted: #9aa4b2;
        --text: #e8edf5;
        --accent: #6ee7b7;
        --accent-2: #8ab4f8;
        --warn: #fbbc04;
        --danger: #ff6b6b;
        --ok: #34d399;
        --ring: #27304a;
        --chip: #1b2340;
      }
      html, body, [class*="css"] { background: var(--bg); color: var(--text); }
      .hero {
        padding: 18px 18px; border: 1px solid var(--ring); border-radius: 16px;
        background:
          radial-gradient(1200px 600px at 12% -10%, rgba(110,231,183,0.12) 0%, transparent 50%),
          radial-gradient(900px 500px at 95% 10%, rgba(138,180,248,0.10) 0%, transparent 50%),
          linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
      }
      .title { font-size: clamp(1.6rem, 1.2vw + 1.1rem, 2.2rem); font-weight: 800; letter-spacing:.2px; }
      .subtitle { color: var(--muted); margin-top: 4px; }

      .kpi-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; }
      .kpi { background: var(--card); border:1px solid var(--ring); border-radius: 14px; padding: 14px; }
      .kpi .label { color: var(--muted); font-size: .9rem; }
      .kpi .value { font-size: 1.3rem; font-weight: 800; margin-top: 2px; }
      .kpi .sub { color: var(--muted); font-size: .85rem; }

      .pill { display:inline-flex; align-items:center; gap:8px; padding:4px 10px; border-radius:999px; border:1px solid var(--ring); background: var(--chip); color: var(--text); font-size:.85rem; }
      .ok { color: var(--ok); }
      .warn { color: var(--warn); }
      .bad { color: var(--danger); }

      .section { background: var(--card-2); border:1px solid var(--ring); border-radius: 16px; padding: 16px; }
      .section h3 { margin:0 0 6px 0; }

      .stTabs [data-baseweb="tab-list"] { gap: 6px; }
      .stTabs [data-baseweb="tab"] { background: var(--card); border-radius: 10px; padding: 8px 12px; }
      .stTabs [aria-selected="true"] { box-shadow: 0 0 0 1px var(--ring) inset; }

      .badge { padding: 3px 8px; border-radius: 999px; font-weight: 700; font-size:.78rem; border:1px solid var(--ring); }
      .badge.ok { background: rgba(52,211,153,.12); color: var(--ok); }
      .badge.warn { background: rgba(251,188,4,.12); color: var(--warn); }
      .badge.bad { background: rgba(255,107,107,.12); color: var(--danger); }

      .divider { height:1px; background: var(--ring); margin: 10px 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# =========================
# Excel‑style time value helpers (with 'type' = 0 end / 1 beginning)
# =========================

def _pow1p(x, n):
    return (1.0 + x) ** n


def FV(rate: float, nper: float, pmt: float = 0.0, pv: float = 0.0, typ: int = 0) -> float:
    if abs(rate) < 1e-12:
        return -(pv + pmt * nper)
    g = _pow1p(rate, nper)
    return -(pv * g + pmt * (1 + rate * typ) * (g - 1) / rate)


def PV(rate: float, nper: float, pmt: float = 0.0, fv: float = 0.0, typ: int = 0) -> float:
    if abs(rate) < 1e-12:
        return -(fv + pmt * nper)
    g = _pow1p(rate, nper)
    return -(fv + pmt * (1 + rate * typ) * (g - 1) / rate) / g


def PMT(rate: float, nper: float, pv: float = 0.0, fv: float = 0.0, typ: int = 0) -> float:
    if nper <= 0:
        return 0.0
    if abs(rate) < 1e-12:
        return -(fv + pv) / nper
    g = _pow1p(rate, nper)
    return -(rate * (pv * g + fv)) / ((1 + rate * typ) * (g - 1))

# =========================
# Sidebar — Inputs (F3–F14)
# =========================
with st.sidebar:
    st.markdown("<div class='title'>🧮 FI Inputs</div>", unsafe_allow_html=True)
    st.caption("Excel‑parity model • Enter annual rates as % (e.g., 7 for 7%)")

    c1, c2 = st.columns(2)
    with c1:
        F3 = st.number_input("F3 • Current age", min_value=16, max_value=80, value=25, step=1, help="Your age today")
    with c2:
        F4 = st.number_input("F4 • Target FI age", min_value=F3+1, max_value=90, value=60, step=1, help="Age when you want financial independence")

    F5 = F4 - F3
    st.markdown(f"<span class='pill'>F5 • Years left: <b>{F5}</b></span>", unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        F6 = st.number_input("F6 • Life expectancy", min_value=F4+1, max_value=110, value=90, step=1, help="Planning horizon")
    with c4:
        use_mx12 = st.checkbox("Set yearly expenses = monthly × 12", value=True)

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    st.subheader("Rates (% p.a.)")
    r1, r2, r3 = st.columns(3)
    with r1:
        F7_pct = st.number_input("F7 • Expense inflation %", min_value=0.0, max_value=20.0, value=5.0, step=0.1, format="%.1f", help="Expected annual inflation for expenses")
    with r2:
        F8_pct = st.number_input("F8 • Return before FI %", min_value=0.0, max_value=30.0, value=10.0, step=0.1, format="%.1f", help="Annual portfolio return till FI")
    with r3:
        F9_pct = st.number_input("F9 • Return after FI %", min_value=0.0, max_value=20.0, value=7.0, step=0.1, format="%.1f", help="Annual return during retirement")

    r4, _ = st.columns(2)
    with r4:
        F10_pct = st.number_input("F10 • Return on existing %", min_value=0.0, max_value=20.0, value=8.0, step=0.1, format="%.1f", help="Annual return on current investments")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    st.subheader("Cash flows (₹)")
    F11 = st.number_input("F11 • Current monthly expenses", min_value=0.0, value=50000.0, step=1000.0)
    F12_default = F11 * 12.0
    F12 = st.number_input("F12 • Yearly expenses", min_value=0.0, value=F12_default if use_mx12 else max(F12_default, 600000.0), step=5000.0)
    F13 = st.number_input("F13 • Current investments", min_value=0.0, value=1000000.0, step=10000.0)
    F14 = st.number_input("F14 • Inheritance to leave (not applied yet)", min_value=0.0, value=0.0, step=10000.0)

# Convert percentage inputs to decimals
F7 = F7_pct / 100.0
F8 = F8_pct / 100.0
F9 = F9_pct / 100.0
F10 = F10_pct / 100.0

# =========================
# Core Calculations (F17–F22)
# =========================
F17 = (F9 - F7) / (1.0 + F7)
F18 = FV(F7, (F4 - F3), 0.0, -F12, 1)
F19 = PV(F17, (F6 - F4), -F18, 0.0, 1)
FV_existing_at_FI = FV(F10, (F5), 0.0, -F13, 1)
F20 = F19 - FV_existing_at_FI
F21 = PMT(F8 / 12.0, (F4 - F3) * 12.0, 0.0, -F20, 1)
F22 = PV(F8, (F4 - F3), 0.0, -F20, 1)

# Derived UI helpers
coverage = 0.0 if F19 == 0 else max(0.0, min(1.0, FV_existing_at_FI / F19))
status_class = "ok" if coverage >= 0.85 else ("warn" if coverage >= 0.5 else "bad")
status_text = "Strong" if status_class == "ok" else ("Moderate" if status_class == "warn" else "Low")

def fmt_money(x):
    try:
        return f"₹{x:,.0f}"
    except Exception:
        return str(x)

# =========================
# Hero + KPIs
# =========================
st.markdown(
    f"""
    <div class='hero'>
      <div class='title'>Financial Independence Planner</div>
      <div class='subtitle'>Excel‑parity engine (F3–F22) with clean visuals. Tune inputs on the left; results update live.</div>
      <div style='margin-top:12px; display:flex; gap:10px; flex-wrap:wrap;'>
        <span class='pill'>Years to FI: <b>{F5}</b></span>
        <span class='pill'>Life horizon post‑FI: <b>{max(F6-F4,0)}</b> years</span>
        <span class='pill'>Coverage now: <b>{coverage*100:.1f}%</b> <span class='{status_class}'>●</span></span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
with c_kpi1:
    st.markdown("<div class='kpi'><div class='label'>Required Corpus at FI (F19)</div><div class='value'>" + fmt_money(F19) + "</div><div class='sub'>Covers expenses till life expectancy</div></div>", unsafe_allow_html=True)
with c_kpi2:
    st.markdown("<div class='kpi'><div class='label'>Monthly SIP Needed (F21)</div><div class='value'>" + fmt_money(F21) + "</div><div class='sub'>Contribute at start of each month</div></div>", unsafe_allow_html=True)
with c_kpi3:
    st.markdown("<div class='kpi'><div class='label'>Lumpsum Needed Today (F22)</div><div class='value'>" + fmt_money(F22) + "</div><div class='sub'>If you prefer a one‑time investment</div></div>", unsafe_allow_html=True)

# Coverage / Gap visual
st.markdown("<div class='section'>", unsafe_allow_html=True)
colA, colB = st.columns([1.2, 1])
with colA:
    st.markdown("### Readiness Gauge")
    st.caption("How much of the required corpus is already covered by your existing investments (grown to FI)")
    st.progress(coverage)
    st.markdown(f"<span class='badge {status_class}'>Coverage: {coverage*100:.1f}% — {status_text}</span>", unsafe_allow_html=True)

with colB:
    st.markdown("### Snapshot")n    
    st.metric("Existing corpus at FI (FV)", fmt_money(FV_existing_at_FI))
    gap = max(F20, 0.0)
    st.metric("Gap to fund (F20)", fmt_money(gap))
    if F20 < 0:
        st.caption("You have a **surplus** based on current settings. SIP/Lumpsum may be 0.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# Tabs: Overview • Inputs • Methodology
# =========================

t1, t2, t3 = st.tabs(["Overview", "Inputs & Results", "Methodology"])

with t1:
    c1, c2 = st.columns([1.4, 1])
    with c1:
        st.markdown("#### Key Numbers")
        tbl = pd.DataFrame(
            {
                "Metric": [
                    "F17 Net real return post‑FI",
                    "F18 Annual expenses at FI",
                    "F19 Required corpus at FI",
                    "FV of current investments at FI",
                    "F20 Gap to fund",
                    "F21 Monthly SIP needed",
                    "F22 Lumpsum needed today",
                ],
                "Value": [
                    f"{F17*100:.2f}%",
                    fmt_money(F18),
                    fmt_money(F19),
                    fmt_money(FV_existing_at_FI),
                    fmt_money(F20),
                    fmt_money(F21),
                    fmt_money(F22),
                ],
            }
        )
        st.dataframe(tbl, use_container_width=True, height=300)

    with c2:
        st.markdown("#### Actions")
        st.write("Download a copy of your results for record‑keeping.")
        export = tbl.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download overview (CSV)", data=export, file_name="fi_overview.csv", mime="text/csv")
        st.caption("Tip: Re‑run with different assumptions and keep multiple CSVs.")

with t2:
    st.markdown("#### Audit: F‑Series Fields")
    data = {
        "Field": [
            "F3 Current age", "F4 FI age", "F5 Years left", "F6 Life expectancy",
            "F7 Inflation (p.a.)", "F8 Return pre‑FI (p.a.)", "F9 Return post‑FI (p.a.)", "F10 Return existing (p.a.)",
            "F11 Monthly expenses", "F12 Yearly expenses", "F13 Current investments", "F14 Inheritance (not used)",
            "F17 Net real return post‑FI", "F18 Annual expenses at FI", "F19 Required corpus", "FV existing at FI",
            "F20 Gap to fund", "F21 SIP (monthly)", "F22 Lumpsum today",
        ],
        "Value": [
            F3, F4, F5, F6,
            F7, F8, F9, F10,
            F11, F12, F13, F14,
            F17, F18, F19, FV_existing_at_FI,
            F20, F21, F22,
        ],
    }
    df = pd.DataFrame(data)

    def _fmt(field, val):
        if isinstance(val, (int,)):
            return f"{val}"
        if any(field.startswith(x) for x in ["F7 ", "F8 ", "F9 ", "F10 ", "F17 "]):
            return f"{val*100:.2f}%"
        if any(field.startswith(x) for x in ["F11 ", "F12 ", "F13 ", "F14 ", "F18 ", "F19 ", "F20 ", "F21 ", "F22 "]):
            return f"{val:,.0f}"
        return f"{val}"

    df_display = pd.DataFrame({"Field": data["Field"], "Value": [ _fmt(f, v) for f, v in zip(data["Field"], data["Value"]) ]})
    st.dataframe(df_display, use_container_width=True, height=420)

    csv_bytes = df_display.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download F‑series (CSV)", data=csv_bytes, file_name="fi_results_F3_F22.csv", mime="text/csv")

with t3:
    st.markdown("#### Notes & Assumptions")
    st.info(
        """
        • **Excel parity**: `PV`, `FV`, and `PMT` mirror Excel behaviour with payments at the **beginning** of the period (`type=1`) where your formulas specify it.  
        • **Rates**: Enter annual percentages; the model converts to decimals internally.  
        • **Signs**: We follow Excel cash‑flow sign convention.  
        • **Inheritance (F14)**: Captured for future extension (e.g., target legacy corpus) but **not** applied yet.  
        • **Validation**: Enforced `F4 > F3` and `F6 > F4` via input bounds.
        """
    )
    with st.expander("What each output means", expanded=False):
        st.markdown(
            """
            - **F17**: Net *real* return after FI — used to discount post‑retirement cash flows.  
            - **F18**: Annual expenses at FI, inflated from today at F7.  
            - **F19**: Present value (at FI) of all future expenses until life expectancy.  
            - **F20**: Portion of F19 not covered by your current investments (grown to FI).  
            - **F21**: Monthly SIP required (paid at **start** of month) to close the gap by FI.  
            - **F22**: Lumpsum needed today to close the gap by FI.
            """
        )

st.caption("Made with Streamlit • F3–F22 engine • v1.5 UI refresh")
