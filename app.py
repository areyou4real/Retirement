import streamlit as st
import pandas as pd
import numpy as np
from streamlit.components.v1 import html as st_html

# =========================
# App Config
# =========================
st.set_page_config(
    page_title="Retirement Savings Calculator",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================
# System theme via prefers-color-scheme (no toggle)
# =========================
def inject_css():
    st.markdown(
        """
        <style>
          /* Fonts */
          @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600&family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap');

          :root {
            /* Light tokens (default) */
            --bg: #f7f8fc;
            --card: #ffffff;
            --card-2: #fbfcff;
            --text: #0e1321;
            --muted: #5d6473;
            --ring: #e7eaf3;
            --chip: #eef2ff;
            --accent: #2563EB;          /* blue-600 */
            --accent-hover: #1E40AF;    /* blue-800 */
            --warn: #fbbc04;
            --danger: #ff6b6b;
            --ok: #34d399;
          }

          @media (prefers-color-scheme: dark) {
            :root {
              /* Dark tokens */
              --bg: #0b0f1a;
              --card: #12182a;
              --card-2: #0e1424;
              --text: #e8edf5;
              --muted: #9aa4b2;
              --ring: #27304a;
              --chip: #1b2340;
              --accent: #3B82F6;        /* brighter for dark */
              --accent-hover: #2563EB;
              --warn: #fbbc04;
              --danger: #ff6b6b;
              --ok: #34d399;
            }
          }

          html, body, [class*="css"] {
            background: var(--bg);
            color: var(--text);
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
            font-size:16px; line-height:1.6;
          }

          /* Numbers */
          .mono { font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace; font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }
          .num  { font-family: 'Space Grotesk', 'Plus Jakarta Sans', system-ui, sans-serif; font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }

          /* === HERO (exactly as provided) === */
          .hero {
            padding: 20px 18px; border: 1px solid var(--ring); border-radius: 14px;
            background:
              radial-gradient(1200px 600px at 12% -10%, rgba(110,231,183,0.12) 0%, transparent 50%),
              radial-gradient(900px 500px at 95% 10%, rgba(138,180,248,0.10) 0%, transparent 50%),
              linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
            max-width: 760px;
            margin: 0 auto;
            text-align: center;
            transition: all 0.25s ease;
          }
          .hero:hover { transform: scale(1.02); box-shadow: 0 4px 18px rgba(0,0,0,0.08); }

          .hero .title { font-size: clamp(1.6rem, 1.1vw + 1.1rem, 2.0rem); font-weight: 700; letter-spacing:.2px; }
          .hero .subtitle { color: var(--muted); margin-top: 6px; }

          /* Smaller cards */
          .card {
            background: var(--card);
            border:1px solid var(--ring);
            border-radius: 12px;
            padding: 14px 16px;
            width: 100%;
            max-width: 760px;
            margin: 0 auto 12px;
            box-sizing: border-box;
            transition: all 0.25s ease;
          }
          .card:hover { transform: translateY(-4px); box-shadow: 0 4px 18px rgba(0,0,0,0.08); }

          .card h3 {
            margin:0 0 8px 0;
            font-weight:600;
            font-size:22px;
            letter-spacing:.2px;
            text-align:center;
          }

          /* EXACT KPI styles */
          .kpi {
            background: var(--card-2);
            border:1px solid var(--ring);
            border-radius: 12px;
            padding: 14px;
            text-align:center;
            transition: all 0.25s ease;
          }
          .kpi:hover { transform: translateY(-4px); box-shadow: 0 4px 18px rgba(0,0,0,0.08); }
          .kpi .label { color: var(--muted); font-size: .95rem; }
          .kpi .value { font-size: 1.35rem; font-weight: 700; margin-top: 2px; }
          .kpi .sub { color: var(--muted); font-size: .85rem; }

          /* Snapshot metric styles */
          .snap-metric { margin: 6px 0 10px; }
          .snap-metric .label { color: var(--muted); font-size:.92rem; }
          .snap-metric .value { font-size: 1.2rem; font-weight: 700; margin-top: 2px; }

          .badge { padding: 3px 8px; border-radius: 9999px; font-weight: 700; font-size:.78rem; border:1px solid var(--ring); }
          .badge.ok { background: rgba(52,211,153,.12); color: var(--ok); }
          .badge.warn { background: rgba(251,188,4,.12); color: var(--warn); }
          .badge.bad { background: rgba(255,107,107,.12); color: var(--danger); }

          /* Inputs */
          .stNumberInput, .stTextInput { width: 100% !important; }
          .stNumberInput input, .stTextInput input {
            border:1px solid var(--ring) !important; border-radius: 10px !important;
            padding: 10px 12px !important; width: 100% !important;
            height: 44px !important;
            box-sizing: border-box;
            transition: all 0.25s ease;
            font-family: 'Space Grotesk', 'Plus Jakarta Sans', system-ui, sans-serif !important;
            font-weight: 500; letter-spacing: 0.2px;
          }
          .stNumberInput input:hover { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(37,99,235,0.15); }
          .stNumberInput input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.25) !important; }

          /* Sticky summary bar */
          .sticky-summary {
            position: sticky; bottom: 0; z-index: 100;
            background: var(--card-2); border-top:1px solid var(--ring);
            padding: 10px 14px; border-radius: 12px 12px 0 0; max-width: 760px; margin: 0 auto;
            transition: all 0.25s ease;
          }
          .sticky-summary:hover { transform: scale(1.01); box-shadow: 0 -2px 10px rgba(0,0,0,0.08); }
          .summary-grid { display:grid; gap:10px; grid-template-columns: repeat(3, minmax(0,1fr)); }
          @media (max-width: 900px) { .summary-grid { grid-template-columns: 1fr; } }

          /* CTA button */
          a { text-decoration: none; }
          .start-btn {
            display:block;
            margin:20px auto 40px;
            padding:14px 28px;
            font-size:18px; font-weight:600;
            border:none; border-radius:9999px;
            background-color:var(--accent); color:#fff;
            cursor:pointer; text-align:center;
            transition: all 0.25s ease;
          }
          .start-btn:hover {
            background-color:var(--accent-hover);
            transform: scale(1.05);
            filter: brightness(1.08);
            box-shadow: 0 4px 14px rgba(0,0,0,0.15);
          }

          /* Width limiter for inputs (no card) */
          .section { max-width: 760px; margin: 0 auto 12px; }
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css()

# =========================
# Excel-style helpers (Excel parity)
# =========================
def _pow1p(x, n): return (1.0 + x) ** n
def FV(rate, nper, pmt=0.0, pv=0.0, typ=0):
    if abs(rate) < 1e-12: return -(pv + pmt * nper)
    g = _pow1p(rate, nper); return -(pv * g + pmt * (1 + rate * typ) * (g - 1) / rate)
def PV(rate, nper, pmt=0.0, fv=0.0, typ=0):
    if abs(rate) < 1e-12: return -(fv + pmt * nper)
    g = _pow1p(rate, nper); return -(fv + pmt * (1 + rate * typ) * (g - 1) / rate) / g
def PMT(rate, nper, pv=0.0, fv=0.0, typ=0):
    if nper <= 0: return 0.0
    if abs(rate) < 1e-12: return -(fv + pv) / nper
    g = _pow1p(rate, nper); return -(rate * (pv * g + fv)) / ((1 + rate * typ) * (g - 1))

# =========================
# Number formatting (Indian system)
# =========================
def fmt_money_indian(x):
    """Format numbers as ₹ in Indian numbering system (##,##,###)."""
    try:
        n = int(round(float(x)))
    except Exception:
        return f"₹{x}"
    s = str(abs(n))
    if len(s) <= 3:
        out = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        out = ",".join(parts) + "," + last3
    sign = "-" if n < 0 else ""
    return f"₹{sign}{out}"

# --- Logo at top (robust inline SVG) ---
import base64, os

def render_svg_logo(path="assets/ventura-logo.svg", width_px=180):
    if not os.path.exists(path):
        # try a couple fallbacks
        for alt in ("/mnt/data/ventura-logo.svg", "ventura-logo.svg"):
            if os.path.exists(alt):
                path = alt
                break
    try:
        with open(path, "rb") as f:
            svg_bytes = f.read()
        # Option A: inline raw SVG (keeps it crisp + stylable)
        svg_text = svg_bytes.decode("utf-8")
        # constrain width without distorting
        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom:16px;">
              <div style="display:inline-block; max-width:{width_px}px; width:100%;">{svg_text}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        # Option B (fallback): base64 <img> if decode fails
        b64 = base64.b64encode(svg_bytes).decode()
        st.markdown(
            f"""
            <div style="text-align:center; margin-bottom:16px;">
              <img src="data:image/svg+xml;base64,{b64}" alt="Ventura Logo" style="max-width:{width_px}px;">
            </div>
            """,
            unsafe_allow_html=True,
        )

# Call this right before the HERO section:
render_svg_logo("assets/ventura-logo.svg", width_px=180)

# =========================
# HERO
# =========================
st.markdown(
    """
    <div class='hero'>
      <div class='title'>Retirement Planner</div>
      <div class='subtitle'>Please follow the instructions below</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# =========================
# INPUTS (NO title card; same width, same rows)
# =========================
with st.container():
    st.markdown("<div class='section'>", unsafe_allow_html=True)

    # Row 1
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        age_now = st.number_input("Current age", min_value=16, max_value=80, value=25, step=1)
    with r1c2:
        age_retire = st.number_input("Target retirement age", min_value=age_now+1, max_value=90, value=60, step=1)
    with r1c3:
        life_expectancy = st.number_input("Life expectancy", min_value=age_retire+1, max_value=110, value=90, step=1)

    years_left = max(0, age_retire - age_now)
    st.caption(f"Years to retirement: **{years_left}** • Years after retirement: **{max(life_expectancy-age_retire,0)}**")

    # Row 2
    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        infl_pct = st.number_input("Expense inflation (% p.a.)", min_value=0.0, max_value=20.0, value=5.0, step=0.1, format="%.1f")
    with r2c2:
        ret_exist_pct = st.number_input("Return on existing investments (% p.a.)", min_value=0.0, max_value=20.0, value=8.0, step=0.1, format="%.1f")
    with r2c3:
        monthly_exp = st.number_input("Current monthly expenses (₹)", min_value=0.0, value=50_000.0, step=1_000.0, format="%.0f")

    # Fixed return captions (after second row)
    st.caption("Return before retirement (% p.a.) — **fixed at 12.0%**")
    st.caption("Return after retirement (% p.a.) — **fixed at 6.0%**")

    # Row 3
    r3c1, r3c2, r3c3 = st.columns(3)
    with r3c1:
        yearly_exp = monthly_exp * 12.0
        st.number_input("Yearly expenses (₹)", value=float(yearly_exp), step=0.0, disabled=True, format="%.0f")
    with r3c2:
        current_invest = st.number_input("Current investments (₹)", min_value=0.0, value=1_000_000.0, step=10_000.0, format="%.0f")
    with r3c3:
        legacy_goal = st.number_input("Inheritance to leave (₹)", min_value=0.0, value=0.0, step=10_000.0, format="%.0f")

    st.caption("Taxes are not modeled in this version.")
    st.markdown("</div>", unsafe_allow_html=True)

# Map UI -> internal variables
F3, F4, F6 = age_now, age_retire, life_expectancy
F5 = years_left
ret_pre_pct = 12.0
ret_post_pct = 6.0
F7, F8, F9, F10 = infl_pct/100.0, ret_pre_pct/100.0, ret_post_pct/100.0, ret_exist_pct/100.0
F11, F12, F13, F14 = monthly_exp, yearly_exp, current_invest, legacy_goal

# ---------- CORE CALCS ----------
# Net real return during retirement
F17 = (F9 - F7) / (1.0 + F7)
# Annual expenses in the retirement year
F18 = FV(F7, (F4 - F3), 0.0, -F12, 1)
# REQUIRED CORPUS at retirement (INCLUDES inheritance goal as terminal value)
F19 = PV(F17, (F6 - F4), -F18, -F14, 1)
# Future value of current investments at retirement
FV_existing_at_ret = FV(F10, (F5), 0.0, -F13, 1)
# Gap, SIP and Lumpsum
F20 = F19 - FV_existing_at_ret
F21 = PMT(F8 / 12.0, (F4 - F3) * 12.0, 0.0, -F20, 1)
F22 = PV(F8, (F4 - F3), 0.0, -F20, 1)

coverage = 0.0 if F19 == 0 else max(0.0, min(1.0, FV_existing_at_ret / F19))
status_class = "ok" if coverage >= 0.85 else ("warn" if coverage >= 0.5 else "bad")
status_text = "Strong" if status_class == "ok" else ("Moderate" if status_class == "warn" else "Low")

# =========================
# OUTPUTS (below inputs)
# =========================

# --- KPI Row (rendered in main DOM) ---
if "prev_F19" not in st.session_state: st.session_state.prev_F19 = 0
if "prev_F21" not in st.session_state: st.session_state.prev_F21 = 0
if "prev_F22" not in st.session_state: st.session_state.prev_F22 = 0

k1, k2, k3 = st.columns(3)

def fmt_money_indian(x):
    try:
        n = int(round(float(x)))
    except Exception:
        return f"₹{x}"
    s = str(abs(n))
    if len(s) <= 3:
        out = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        out = ",".join(parts) + "," + last3
    sign = "-" if n < 0 else ""
    return f"₹{sign}{out}"

with k1:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Required corpus at retirement</div>"
        f"<div id='kpi1' class='value'>{fmt_money_indian(st.session_state.get('prev_F19', 0))}</div>"
        f"<div class='sub'>Covers expenses till life expectancy and inheritance</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Monthly SIP needed</div>"
        f"<div id='kpi2' class='value'>{fmt_money_indian(st.session_state.get('prev_F21', 0))}</div>"
        f"<div class='sub'>Contributed at the start of each month</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Lumpsum needed today</div>"
        f"<div id='kpi3' class='value'>{fmt_money_indian(st.session_state.get('prev_F22', 0))}</div>"
        f"<div class='sub'>If you prefer a one‑time investment</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

# Add spacing between KPI row and Preparedness/Snapshot row
st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

# --- Preparedness & Snapshot ---
cA, cB = st.columns([1.2, 1])
with cA:
    st.markdown("<div class='card'><h3>Preparedness</h3>", unsafe_allow_html=True)
    st.caption("Portion of the required corpus (incl. inheritance) already covered by your investments grown to retirement")
    st.progress(coverage)
    st.markdown(f"<span class='badge {status_class}'>Coverage: {coverage*100:.1f}% — {status_text}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Keep previous snapshot values for animation
if "prev_snap_fv" not in st.session_state: st.session_state.prev_snap_fv = 0
if "prev_snap_gap" not in st.session_state: st.session_state.prev_snap_gap = 0

with cB:
    st.markdown("<div class='card'><h3>Snapshot</h3>", unsafe_allow_html=True)
    # Existing corpus
    st.markdown(
        f"<div class='snap-metric'>"
        f"<div class='label'>Existing corpus at retirement (future value)</div>"
        f"<div id='snap1' class='value'>{fmt_money_indian(st.session_state.prev_snap_fv)}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    # Gap to fund
    gap = max(F20, 0.0)
    st.markdown(
        f"<div class='snap-metric'>"
        f"<div class='label'>Gap to fund</div>"
        f"<div id='snap2' class='value'>{fmt_money_indian(st.session_state.prev_snap_gap)}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    if F20 < 0:
        st.caption("You have a **surplus** based on current settings. SIP/Lumpsum may be 0.")
    st.markdown("</div>", unsafe_allow_html=True)

# Animate numbers (CountUp with Indian formatter) for KPIs + Snapshot
st_html(
    f"""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/countup.js/2.8.0/countUp.umd.js"></script>
    <script>
      (function() {{
        function formatIndian(num) {{
          try {{
            num = Math.round(num);
            const sign = num < 0 ? "-" : "";
            let s = Math.abs(num).toString();
            if (s.length <= 3) return "₹" + sign + s;
            const last3 = s.slice(-3);
            let rest = s.slice(0, -3);
            const parts = [];
            while (rest.length > 2) {{
              parts.unshift(rest.slice(-2));
              rest = rest.slice(0, -2);
            }}
            if (rest.length) parts.unshift(rest);
            return "₹" + sign + parts.join(",") + "," + last3;
          }} catch (e) {{
            return "₹" + num;
          }}
        }}

        function run(id, end, start) {{
          const el = window.parent.document.getElementById(id);
          if (!el || typeof countUp === 'undefined') return;
          const opts = {{
            duration: 1.2,
            formattingFn: formatIndian
          }};
          try {{
            const a = new countUp.CountUp(el, end, {{...opts, startVal: start}});
            a.start();
          }} catch (e) {{}}
        }}

        // KPIs
        run('kpi1', {int(F19)}, {int(st.session_state.get('prev_F19', 0))});
        run('kpi2', {int(F21)}, {int(st.session_state.get('prev_F21', 0))});
        run('kpi3', {int(F22)}, {int(st.session_state.get('prev_F22', 0))});

        // Snapshot
        run('snap1', {int(FV_existing_at_ret)}, {int(st.session_state.get('prev_snap_fv', 0))});
        run('snap2', {int(gap)}, {int(st.session_state.get('prev_snap_gap', 0))});
      }})();
    </script>
    """,
    height=0,
)

# Update prev values for next run (for smooth animation)
st.session_state.prev_F19 = int(F19)
st.session_state.prev_F21 = int(F21)
st.session_state.prev_F22 = int(F22)
st.session_state.prev_snap_fv = int(FV_existing_at_ret)
st.session_state.prev_snap_gap = int(gap)

st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# CTA: Start Investing (centered, with hover animation)
st.markdown(
    """<a href='https://www.venturasecurities.com/' target='_blank' aria-label='Start Investing at Ventura Securities'>
          <button class='start-btn'>Start Investing Now</button>
       </a>""",
    unsafe_allow_html=True,
)

# Sticky Summary Footer
st.markdown(
    f"""
    <div class='sticky-summary'>
      <div class='summary-grid'>
        <div><div class='hint'>Corpus at retirement</div><div class='mono' style='font-weight:800; font-size:1.1rem;'>{fmt_money_indian(F19)}</div></div>
        <div><div class='hint'>Monthly SIP</div><div class='mono' style='font-weight:800; font-size:1.1rem;'>{fmt_money_indian(F21)}</div></div>
        <div><div class='hint'>Coverage now</div><div class='mono' style='font-weight:800; font-size:1.1rem;'>{coverage*100:.1f}%</div></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Centered version label
st.markdown("<div style='text-align:center; color:var(--muted); font-size:0.85rem;'>v5.1 — Inheritance goal included in corpus</div>", unsafe_allow_html=True)
