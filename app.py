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
      /* Fonts */
      @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=DM+Sans:wght@400;700&family=Space+Grotesk:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

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

      html, body, [class*="css"] { background: var(--bg); color: var(--text); font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
      h1,h2,h3,h4 { font-family: 'Space Grotesk', Inter, sans-serif; letter-spacing:.2px; }
      .mono { font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace; }

      .hero {
        padding: 22px 22px; border: 1px solid var(--ring); border-radius: 16px;
        background:
          radial-gradient(1200px 600px at 12% -10%, rgba(110,231,183,0.12) 0%, transparent 50%),
          radial-gradient(900px 500px at 95% 10%, rgba(138,180,248,0.10) 0%, transparent 50%),
          linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
      }
      .title { font-size: clamp(1.6rem, 1.2vw + 1.1rem, 2.3rem); font-weight: 800; letter-spacing:.2px; }
      .subtitle { color: var(--muted); margin-top: 6px; font-family: 'DM Sans', Inter, sans-serif; }

      .pill { display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:999px; border:1px solid var(--ring); background: var(--chip); color: var(--text); font-size:.9rem; }

      .grid { display:grid; gap: 14px; }
      .grid.cols-3 { grid-template-columns: repeat(3, minmax(0,1fr)); }
      .grid.cols-2 { grid-template-columns: repeat(2, minmax(0,1fr)); }

      .card { background: var(--card); border:1px solid var(--ring); border-radius: 16px; padding: 16px; }
      .card h3 { margin:0 0 6px 0; font-weight:700; }
      .hint { color: var(--muted); font-size:.9rem; }

      .kpi { background: var(--card-2); border:1px solid var(--ring); border-radius: 14px; padding: 16px; }
      .kpi .label { color: var(--muted); font-size: .95rem; }
      .kpi .value { font-size: 1.35rem; font-weight: 800; margin-top: 2px; }
      .kpi .sub { color: var(--muted); font-size: .85rem; }

      .badge { padding: 3px 8px; border-radius: 999px; font-weight: 700; font-size:.78rem; border:1px solid var(--ring); }
      .badge.ok { background: rgba(52,211,153,.12); color: var(--ok); }
      .badge.warn { background: rgba(251,188,4,.12); color: var(--warn); }
      .badge.bad { background: rgba(255,107,107,.12); color: var(--danger); }

      .divider { height:1px; background: var(--ring); margin: 12px 0; }
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
# INPUTS — clean, minimalist (no F-codes shown)
# =========================

# Timeline
st.markdown(
    f"""
    <div class='hero'>
      <div class='title'>Financial Independence Planner</div>
      <div class='subtitle'>Minimal inputs. Clear outputs. Calculations follow Excel's PV/FV/PMT with payments at the beginning where applicable.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

col_overview = st.container()
with col_overview:
    st.markdown("### Your Plan")
    st.caption("Fill these once — everything else updates live.")

    st.markdown("<div class='grid cols-3'>", unsafe_allow_html=True)

    # Card 1 — Timeline
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>Timeline</h3>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        age_now = st.number_input("Current age", min_value=16, max_value=80, value=25, step=1)
    with c2:
        age_fi = st.number_input("Target FI age", min_value=age_now+1, max_value=90, value=60, step=1)
    with c3:
        life_expectancy = st.number_input("Life expectancy", min_value=age_fi+1, max_value=110, value=90, step=1)
    years_left = age_fi - age_now
    st.caption(f"Years to FI: **{years_left}** • Years post‑FI: **{max(life_expectancy-age_fi,0)}**")
    st.markdown("</div>", unsafe_allow_html=True)

    # Card 2 — Rates
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>Rates (% p.a.)</h3>", unsafe_allow_html=True)
    r1, r2, r3 = st.columns(3)
    with r1:
        infl_pct = st.number_input("Expense inflation", min_value=0.0, max_value=20.0, value=5.0, step=0.1, format="%.1f", help="Expected inflation for expenses")
    with r2:
        ret_pre_pct = st.number_input("Return before FI", min_value=0.0, max_value=30.0, value=10.0, step=0.1, format="%.1f")
    with r3:
        ret_post_pct = st.number_input("Return after FI", min_value=0.0, max_value=20.0, value=7.0, step=0.1, format="%.1f")
    r4, _ = st.columns(2)
    with r4:
        ret_exist_pct = st.number_input("Return on existing investments", min_value=0.0, max_value=20.0, value=8.0, step=0.1, format="%.1f")
    st.markdown("</div>", unsafe_allow_html=True)

    # Card 3 — Cash flows
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<h3>Cash flows (₹)</h3>", unsafe_allow_html=True)
    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        monthly_exp = st.number_input("Current monthly expenses", min_value=0.0, value=50000.0, step=1000.0)
    with cf2:
        use_mx12 = st.checkbox("Set yearly = monthly × 12", value=True)
        yearly_exp_default = monthly_exp * 12.0
        yearly_exp = st.number_input("Yearly expenses", min_value=0.0, value=yearly_exp_default if use_mx12 else max(yearly_exp_default, 600000.0), step=5000.0)
    with cf3:
        current_invest = st.number_input("Current investments", min_value=0.0, value=1000000.0, step=10000.0)
    _, cf4 = st.columns([2,1])
    with cf4:
        legacy_goal = st.number_input("Inheritance to leave", min_value=0.0, value=0.0, step=10000.0)
    st.caption("Taxes not modeled in this version.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# Map UI -> internal F-variables (hidden from user)
# =========================
F3, F4, F6 = age_now, age_fi, life_expectancy
F5 = years_left
F7, F8, F9, F10 = infl_pct/100.0, ret_pre_pct/100.0, ret_post_pct/100.0, ret_exist_pct/100.0
F11, F12, F13, F14 = monthly_exp, yearly_exp, current_invest, legacy_goal

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

coverage = 0.0 if F19 == 0 else max(0.0, min(1.0, FV_existing_at_FI / F19))
status_class = "ok" if coverage >= 0.85 else ("warn" if coverage >= 0.5 else "bad")
status_text = "Strong" if status_class == "ok" else ("Moderate" if status_class == "warn" else "Low")

def fmt_money(x):
    try:
        return f"₹{x:,.0f}"
    except Exception:
        return str(x)

# =========================
# KPIs
# =========================
col_k1, col_k2, col_k3 = st.columns(3)
with col_k1:
    st.markdown("<div class='kpi'><div class='label'>Required corpus at FI</div><div class='value'>" + fmt_money(F19) + "</div><div class='sub'>Covers expenses till life expectancy</div></div>", unsafe_allow_html=True)
with col_k2:
    st.markdown("<div class='kpi'><div class='label'>Monthly SIP needed</div><div class='value'>" + fmt_money(F21) + "</div><div class='sub'>Contributed at the start of each month</div></div>", unsafe_allow_html=True)
with col_k3:
    st.markdown("<div class='kpi'><div class='label'>Lumpsum needed today</div><div class='value'>" + fmt_money(F22) + "</div><div class='sub'>If you prefer a one‑time investment</div></div>", unsafe_allow_html=True)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# Coverage section
st.markdown("<div class='card'>", unsafe_allow_html=True)
colA, colB = st.columns([1.2, 1])
with colA:
    st.markdown("### Readiness gauge")
    st.caption("How much of the required corpus is already covered by your existing investments (grown to FI)")
    st.progress(coverage)
    st.markdown(f"<span class='badge {status_class}'>Coverage: {coverage*100:.1f}% — {status_text}</span>", unsafe_allow_html=True)
with colB:
    st.markdown("### Snapshot")
    st.metric("Existing corpus at FI (future value)", fmt_money(FV_existing_at_FI))
    gap = max(F20, 0.0)
    st.metric("Gap to fund", fmt_money(gap))
    if F20 < 0:
        st.caption("You have a **surplus** based on current settings. SIP/Lumpsum may be 0.")

st.markdown("</div>", unsafe_allow_html=True)

# =========================
# Tabs: Overview • Methodology
# =========================

t1, t3 = st.tabs(["Overview", "Methodology"])

with t1:
    c1, c2 = st.columns([1.4, 1])
    with c1:
        st.markdown("#### Key numbers")
        tbl = pd.DataFrame(
            {
                "Metric": [
                    "Net real return after FI",
                    "Annual expenses at FI",
                    "Required corpus at FI",
                    "Future value of current investments at FI",
                    "Gap to fund",
                    "Monthly SIP needed",
                    "Lumpsum needed today",
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
        st.markdown("#### Export")
        export = tbl.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download overview (CSV)", data=export, file_name="fi_overview.csv", mime="text/csv")
        st.caption("Tip: Re‑run with different assumptions and keep multiple CSVs.")

with t3:
    st.markdown("#### Notes & assumptions")
    st.info(
        """
        • Calculations mirror Excel: `PV`, `FV`, and `PMT` with payments at the **beginning** of the period where applicable.  
        • All rates are annual; the app converts to decimals internally.  
        • Signs follow Excel cash‑flow convention.  
        • Inheritance/legacy is captured for future logic but not yet applied.  
        • Constraints enforced: Target FI age > current age; Life expectancy > FI age.
        """
    )

st.caption("Made with Streamlit • Minimal UI • F-series engine under the hood • v2.0")
