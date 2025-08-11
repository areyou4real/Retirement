import streamlit as st
import pandas as pd
import numpy as np

# =========================
# App Config
# =========================
st.set_page_config(
    page_title="Retirement Savings Calculator",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- Theme Toggle (Light / Dark via CSS variables) ---
if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = "Dark"

with st.container():
    top_cols = st.columns([1, 1, 1, 1, 1])
    with top_cols[-1]:
        st.session_state.ui_theme = st.selectbox("Theme", ["Dark", "Light"], index=0 if st.session_state.ui_theme=="Dark" else 1)

def inject_css(theme: str = "Dark"):
    if theme == "Light":
        bg = "#f7f8fc"; card = "#ffffff"; card2 = "#fbfcff"; text = "#0e1321"; muted = "#5d6473"; ring = "#e7eaf3"; chip = "#eef2ff"
    else:
        bg = "#0b0f1a"; card = "#12182a"; card2 = "#0e1424"; text = "#e8edf5"; muted = "#9aa4b2"; ring = "#27304a"; chip = "#1b2340"

    st.markdown(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
          :root {{
            --bg: {bg};
            --card: {card};
            --card-2: {card2};
            --muted: {muted};
            --text: {text};
            --accent: #6ee7b7;
            --accent-2: #8ab4f8;
            --warn: #fbbc04;
            --danger: #ff6b6b;
            --ok: #34d399;
            --ring: {ring};
            --chip: {chip};
          }}
          html, body, [class*="css"] {{ background: var(--bg); color: var(--text); font-family: 'Inter', system-ui, -apple-system, Segoe UI, Roboto, sans-serif; font-size:16px; line-height:1.6; }}
          h1,h2,h3,h4 {{ font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif; letter-spacing:.2px; font-weight:600; }}
          .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }}

          .hero {{
            padding: 26px 22px; border: 1px solid var(--ring); border-radius: 16px;
            background:
              radial-gradient(1200px 600px at 12% -10%, rgba(110,231,183,0.12) 0%, transparent 50%),
              radial-gradient(900px 500px at 95% 10%, rgba(138,180,248,0.10) 0%, transparent 50%),
              linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
          }}
          .title {{ font-size: clamp(1.6rem, 1.2vw + 1.1rem, 2.2rem); font-weight: 800; letter-spacing:.2px; }}
          .subtitle {{ color: var(--muted); margin-top: 6px; }}

          .pill {{ display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:999px; border:1px solid var(--ring); background: var(--chip); color: var(--text); font-size:.9rem; }}

          .card {{ background: var(--card); border:1px solid var(--ring); border-radius: 16px; padding: 16px; }}
          .card h3 {{ margin:0 0 6px 0; font-weight:600; font-size:20px; letter-spacing:.2px; }}
          .hint {{ color: var(--muted); font-size:.9rem; }}

          .kpi {{ background: var(--card-2); border:1px solid var(--ring); border-radius: 14px; padding: 16px; }}
          .kpi .label {{ color: var(--muted); font-size: .95rem; }}
          .kpi .value {{ font-size: 1.35rem; font-weight: 800; margin-top: 2px; }}
          .kpi .sub {{ color: var(--muted); font-size: .85rem; }}

          .badge {{ padding: 3px 8px; border-radius: 999px; font-weight: 700; font-size:.78rem; border:1px solid var(--ring); }}
          .badge.ok {{ background: rgba(52,211,153,.12); color: var(--ok); }}
          .badge.warn {{ background: rgba(251,188,4,.12); color: var(--warn); }}
          .badge.bad {{ background: rgba(255,107,107,.12); color: var(--danger); }}

          .divider {{ height:1px; background: var(--ring); margin: 12px 0; }}

          /* Sticky summary bar */
          .sticky-summary {{
            position: sticky; bottom: 0; z-index: 100;
            background: var(--card-2); border-top:1px solid var(--ring);
            padding: 10px 14px; border-radius: 12px 12px 0 0;
          }}
          .summary-grid {{ display:grid; gap:10px; grid-template-columns: repeat(3, minmax(0,1fr)); }}
          @media (max-width: 900px) {{ .summary-grid {{ grid-template-columns: 1fr; }} }}
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css(st.session_state.ui_theme)

# =========================
# Excel-style helpers (Excel parity)
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
# HERO
# =========================
st.markdown(
    f"""
    <div class='hero'>
      <div class='title'>Retirement Planner</div>
      <div class='subtitle'>Minimal inputs. Clear outputs. Excel‑parity PV/FV/PMT with payments at period start where applicable.</div>
      <div style='margin-top:10px; display:flex; gap:10px; flex-wrap:wrap;'>
        <span class='pill'>Theme: <b>{st.session_state.ui_theme}</b></span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# =========================
# HORIZONTAL FLOW: Inputs (top) • Outputs (bottom)
# =========================

# ---------- INPUTS (Single card) ----------
with st.container():
    st.markdown("<div class='card'><h3>Inputs</h3>", unsafe_allow_html=True)

    # Timeline
    c1, c2, c3 = st.columns(3)
    with c1:
        age_now = st.number_input("Current age", min_value=16, max_value=80, value=25, step=1)
    with c2:
        age_retire = st.number_input("Target retirement age", min_value=age_now+1, max_value=90, value=60, step=1)
    with c3:
        life_expectancy = st.number_input("Life expectancy", min_value=age_retire+1, max_value=110, value=90, step=1)
    years_left = max(0, age_retire - age_now)
    st.caption(f"Years to retirement: **{years_left}** • Years after retirement: **{max(life_expectancy-age_retire,0)}**")

    # Rates (% p.a.) — with fixed returns before/after retirement
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        infl_pct = st.number_input("Expense inflation (% p.a.)", min_value=0.0, max_value=20.0, value=5.0, step=0.1, format="%.1f")
    with r2:
        st.number_input("Return before retirement (% p.a.) — fixed", value=12.0, step=0.0, disabled=True, format="%.1f")
    with r3:
        st.number_input("Return after retirement (% p.a.) — fixed", value=6.0, step=0.0, disabled=True, format="%.1f")
    with r4:
        ret_exist_pct = st.number_input("Return on existing investments (% p.a.)", min_value=0.0, max_value=20.0, value=8.0, step=0.1, format="%.1f")

    # Cash flows row — single line, yearly auto = 12×monthly
    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        monthly_exp = st.number_input("Current monthly expenses (₹)", min_value=0.0, value=50_000.0, step=1_000.0, format="%.0f")
    with cf2:
        yearly_exp = monthly_exp * 12.0
        st.number_input("Yearly expenses (₹)", value=float(yearly_exp), step=0.0, disabled=True, format="%.0f")
    with cf3:
        current_invest = st.number_input("Current investments (₹)", min_value=0.0, value=1_000_000.0, step=10_000.0, format="%.0f")

    legacy_goal = st.number_input("Inheritance to leave (₹)", min_value=0.0, value=0.0, step=10_000.0, format="%.0f")
    st.caption("Taxes are not modeled in this version.")
    st.markdown("</div>", unsafe_allow_html=True)

# Map UI -> internal variables (hidden mapping)
F3, F4, F6 = age_now, age_retire, life_expectancy
F5 = years_left
# Fixed returns as requested
ret_pre_pct = 12.0
ret_post_pct = 6.0
F7, F8, F9, F10 = infl_pct/100.0, ret_pre_pct/100.0, ret_post_pct/100.0, ret_exist_pct/100.0
F11, F12, F13, F14 = monthly_exp, yearly_exp, current_invest, legacy_goal

# ---------- CORE CALCS (unchanged math) ----------
F17 = (F9 - F7) / (1.0 + F7)
F18 = FV(F7, (F4 - F3), 0.0, -F12, 1)
F19 = PV(F17, (F6 - F4), -F18, 0.0, 1)
FV_existing_at_ret = FV(F10, (F5), 0.0, -F13, 1)
F20 = F19 - FV_existing_at_ret
F21 = PMT(F8 / 12.0, (F4 - F3) * 12.0, 0.0, -F20, 1)
F22 = PV(F8, (F4 - F3), 0.0, -F20, 1)

coverage = 0.0 if F19 == 0 else max(0.0, min(1.0, FV_existing_at_ret / F19))
status_class = "ok" if coverage >= 0.85 else ("warn" if coverage >= 0.5 else "bad")
status_text = "Strong" if status_class == "ok" else ("Moderate" if status_class == "warn" else "Low")

def fmt_money(x):
    try:
        return f"₹{x:,.0f}"
    except Exception:
        return str(x)

# ---------- OUTPUTS (below inputs) ----------

# KPI row
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown("<div class='kpi'><div class='label'>Required corpus at retirement</div><div class='value'>" + fmt_money(F19) + "</div><div class='sub'>Covers expenses till life expectancy</div></div>", unsafe_allow_html=True)
with k2:
    st.markdown("<div class='kpi'><div class='label'>Monthly SIP needed</div><div class='value'>" + fmt_money(F21) + "</div><div class='sub'>Contributed at the start of each month</div></div>", unsafe_allow_html=True)
with k3:
    st.markdown("<div class='kpi'><div class='label'>Lumpsum needed today</div><div class='value'>" + fmt_money(F22) + "</div><div class='sub'>If you prefer a one‑time investment</div></div>", unsafe_allow_html=True)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# Coverage & Snapshot
cA, cB = st.columns([1.2, 1])
with cA:
    st.markdown("<div class='card'><h3>Readiness gauge</h3>", unsafe_allow_html=True)
    st.caption("How much of the required corpus is already covered by your existing investments (grown to retirement)")
    st.progress(coverage)
    st.markdown(f"<span class='badge {status_class}'>Coverage: {coverage*100:.1f}% — {status_text}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
with cB:
    st.markdown("<div class='card'><h3>Snapshot</h3>", unsafe_allow_html=True)
    st.metric("Existing corpus at retirement (future value)", fmt_money(FV_existing_at_ret))
    gap = max(F20, 0.0)
    st.metric("Gap to fund", fmt_money(gap))
    if F20 < 0:
        st.caption("You have a **surplus** based on current settings. SIP/Lumpsum may be 0.")
    st.markdown("</div>", unsafe_allow_html=True)

# =========================
# Sticky Summary Footer (updated wording)
# =========================
st.markdown(
    f"""
    <div class='sticky-summary'>
      <div class='summary-grid'>
        <div><div class='hint'>Corpus at retirement</div><div class='mono' style='font-weight:800; font-size:1.1rem;'>{fmt_money(F19)}</div></div>
        <div><div class='hint'>Monthly SIP</div><div class='mono' style='font-weight:800; font-size:1.1rem;'>{fmt_money(F21)}</div></div>
        <div><div class='hint'>Coverage now</div><div class='mono' style='font-weight:800; font-size:1.1rem;'>{coverage*100:.1f}%</div></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption("Made with Streamlit • Horizontal flow • Retirement wording • v4.0")
