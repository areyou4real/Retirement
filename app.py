import streamlit as st
import pandas as pd
import numpy as np

# =========================
# App Config & Styling
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
        --bg: #0f1116;
        --card: #141824;
        --muted: #a0a6b4;
        --accent: #6ee7b7;
        --accent-2: #8ab4f8;
        --warn: #fbbc04;
        --danger: #ff6b6b;
        --ok: #34d399;
        --ring: #2c3344;
      }
      .app-title { font-size: 2.0rem; font-weight: 800; letter-spacing:.2px; }
      .muted { color: var(--muted); }
      .F { font-variant-numeric: tabular-nums; }
      .stTabs [data-baseweb="tab-list"] { gap: 0.25rem; }
      .stTabs [data-baseweb="tab"] { background: var(--card); border-radius: 10px; padding: 8px 10px; }
      .stAlert { border: 1px solid #2b3242; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div class='app-title'>🧮 Retirement / Financial Independence Planner</div>", unsafe_allow_html=True)
st.caption("Implements the F3–F22 logic exactly as specified (Excel-equivalent PV/FV/PMT with payments at beginning). All rates are annual; enter as percentages (e.g., 7 for 7%).")

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
# Inputs (F3–F14)
# =========================
with st.sidebar:
    st.header("Inputs (F3–F14)")
    c1, c2 = st.columns(2)
    with c1:
        F3 = st.number_input("F3 • Current age", min_value=16, max_value=80, value=25, step=1)
    with c2:
        F4 = st.number_input("F4 • Age for Financial Independence", min_value=F3+1, max_value=90, value=60, step=1)

    # Derived
    F5 = F4 - F3
    st.caption(f"F5 • Years Left (auto): {F5}")

    c3, c4 = st.columns(2)
    with c3:
        F6 = st.number_input("F6 • Life Expectancy (age)", min_value=F4+1, max_value=110, value=90, step=1)
    with c4:
        use_mx12 = st.checkbox("Set yearly expenses = monthly × 12", value=True)

    st.subheader("Rates (% per annum)")
    r1, r2, r3 = st.columns(3)
    with r1:
        F7_pct = st.number_input("F7 • Inflation for Expenses %", min_value=0.0, max_value=20.0, value=5.0, step=0.1, format="%.1f")
    with r2:
        F8_pct = st.number_input("F8 • Returns before FI %", min_value=0.0, max_value=30.0, value=10.0, step=0.1, format="%.1f")
    with r3:
        F9_pct = st.number_input("F9 • Returns after FI %", min_value=0.0, max_value=20.0, value=7.0, step=0.1, format="%.1f")
    r4, r5 = st.columns(2)
    with r4:
        F10_pct = st.number_input("F10 • Returns on existing investments %", min_value=0.0, max_value=20.0, value=8.0, step=0.1, format="%.1f")

    st.subheader("Cash Flows (₹)")
    F11 = st.number_input("F11 • Current Monthly Expenses", min_value=0.0, value=50000.0, step=1000.0)
    F12_default = F11 * 12.0
    F12 = st.number_input("F12 • Expenses for the Year", min_value=0.0, value=F12_default if use_mx12 else max(F12_default, 600000.0), step=5000.0)
    F13 = st.number_input("F13 • Current Investments", min_value=0.0, value=1000000.0, step=10000.0)
    F14 = st.number_input("F14 • Inheritance to leave (not used yet)", min_value=0.0, value=0.0, step=10000.0)

# Convert percentages to decimals
F7 = F7_pct / 100.0
F8 = F8_pct / 100.0
F9 = F9_pct / 100.0
F10 = F10_pct / 100.0

# =========================
# Calculations (F17–F22)
# =========================
# F17: Net Returns to be considered for Corpus Planning = (F9 - F7) / (1 + F7)
F17 = (F9 - F7) / (1.0 + F7)

# F18: Yearly Expenses in the year you Retire = FV(F7, (F4 - F3), 0, -F12, 1)
F18 = FV(F7, (F4 - F3), 0.0, -F12, 1)

# F19: Corpus accumulated until Life expectancy = PV(F17, (F6 - F4), -F18, 0, 1)
F19 = PV(F17, (F6 - F4), -F18, 0.0, 1)

# F20: Current Investments Utilized = F19 - FV(F10, F5, 0, -F13, 1)
F20 = F19 - FV(F10, F5, 0.0, -F13, 1)

# F21: SIP = PMT(F8/12, (F4 - F3)*12, 0, -F20, 1)
F21 = PMT(F8 / 12.0, (F4 - F3) * 12.0, 0.0, -F20, 1)

# F22: Lumpsum = PV(F8, (F4 - F3), 0, -F20, 1)
F22 = PV(F8, (F4 - F3), 0.0, -F20, 1)

# =========================
# Layout & Output
# =========================
left, right = st.columns([1.15, 1])
with left:
    st.subheader("Key Outputs (F17–F22)")
    k1, k2, k3 = st.columns(3)
    k1.metric("F17 • Net real return post‑FI", f"{F17*100:.2f}%")
    k2.metric("F18 • Annual expenses at FI (₹)", f"{F18:,.0f}")
    k3.metric("F19 • Corpus needed till life expectancy (₹)", f"{F19:,.0f}")

    k4, k5, k6 = st.columns(3)
    k4.metric("F20 • Current investments utilized (₹)", f"{F20:,.0f}")
    k5.metric("F21 • Monthly SIP needed (₹)", f"{F21:,.0f}")
    k6.metric("F22 • Lumpsum needed today (₹)", f"{F22:,.0f}")

    st.divider()
    st.markdown("**Audit Table** — inputs and computed values")
    data = {
        "Field": [
            "F3 Current age", "F4 FI age", "F5 Years left", "F6 Life expectancy",
            "F7 Inflation (p.a.)", "F8 Return pre-FI (p.a.)", "F9 Return post-FI (p.a.)", "F10 Return existing (p.a.)",
            "F11 Monthly expenses", "F12 Yearly expenses", "F13 Current investments", "F14 Inheritance (not used)",
            "F17 Net real return post-FI", "F18 Annual expenses at FI", "F19 Required corpus", "F20 Utilized current inv.",
            "F21 SIP (monthly)", "F22 Lumpsum today",
        ],
        "Value": [
            F3, F4, F5, F6,
            F7, F8, F9, F10,
            F11, F12, F13, F14,
            F17, F18, F19, F20,
            F21, F22,
        ],
    }
    df = pd.DataFrame(data)

    fmt = {
        "Value": lambda v: (f"{v:.2%}" if isinstance(v, float) and 0 <= v <= 1 and data["Field"][data["Value"].index(v)].startswith("F7") else v)
    }
    # Render nicely with types
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

    # Download
    csv_bytes = df_display.to_csv(index=False).encode("utf-8")
    st.download_button("Download results (CSV)", data=csv_bytes, file_name="fi_results_F3_F22.csv", mime="text/csv")

with right:
    st.subheader("Notes & Assumptions")
    st.info(
        """
        • **Excel parity**: PV/FV/PMT match Excel, with payments at the **beginning** of period (type=1) wherever specified in your formulas.  
        • **Rates**: Enter annual percentages; the model converts to decimals internally.  
        • **Signs**: We mirror your sign convention (negative cash flows in the Excel calls).  
        • **Inheritance (F14)**: Captured for future use (e.g., adjusting target corpus), but not yet applied to formulas F17–F22.  
        • **Validation**: F4 > F3, F6 > F4 enforced via input bounds.
        """
    )

    with st.expander("What each output means", expanded=False):
        st.markdown(
            """
            - **F17**: Net *real* return after FI — used to discount post‑retirement cash flows.
            - **F18**: Your annual expenses at the time you hit FI, inflated from today at F7.
            - **F19**: Present value (at FI) of all future expenses until life expectancy.
            - **F20**: Portion of required corpus covered by your current investments growing at F10.
            - **F21**: Monthly SIP needed (paid at the **start** of each month) to bridge the gap by FI.
            - **F22**: Lumpsum you’d need to invest today (instead of SIP) to bridge the gap by FI.
            """
        )

st.caption("Paste into app.py and run: `streamlit run app.py` • v1.0 F3–F22 parity")
