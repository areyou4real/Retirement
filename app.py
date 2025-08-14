import streamlit as st
import pandas as pd
import numpy as np
from streamlit.components.v1 import html as st_html
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import re

# =========================
# App Config
# =========================
st.set_page_config(
    page_title="Retirement Savings Calculator",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# One-time redirect guard (harmless)
if st.session_state.get("_redirect_once"):
    st.session_state["_redirect_once"] = False

# =========================
# CSS / Theme
# =========================
def inject_css():
    st.markdown(
        """
        <style>
          /* Fonts */
          @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600&family=Space+Grotesk:wght@400;500;700&family=JetBrains+Mono:wght@400;600&display=swap');

          :root {
            /* Light tokens (default) */
            --bg: #f7f8fc; --card: #ffffff; --card-2: #fbfcff; --text: #0e1321; --muted: #5d6473; --ring: #e7eaf3; --chip: #eef2ff;
            --accent: #2563EB; --accent-hover: #1E40AF; --warn: #fbbc04; --danger: #ff6b6b; --ok: #34d399;
          }
          @media (prefers-color-scheme: dark) {
            :root { --bg: #0b0f1a; --card: #12182a; --card-2: #0e1424; --text: #e8edf5; --muted: #9aa4b2; --ring: #27304a; --chip: #1b2340;
                    --accent: #3B82F6; --accent-hover: #2563EB; }
          }

          html, body, [class*="css"] { background: var(--bg); color: var(--text); font-family: 'Plus Jakarta Sans', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; font-size:16px; line-height:1.6; }
          .mono { font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Menlo, monospace; font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }
          .num  { font-family: 'Space Grotesk', 'Plus Jakarta Sans', system-ui, sans-serif; font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }

          /* HERO */
          .hero {
            padding: 20px 18px; border: 1px solid var(--ring); border-radius: 14px;
            background:
              radial-gradient(1200px 600px at 12% -10%, rgba(110,231,183,0.12) 0%, transparent 50%),
              radial-gradient(900px 500px at 95% 10%, rgba(138,180,248,0.10) 0%, transparent 50%),
              linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0));
            max-width: 760px; margin: 0 auto; text-align: center; transition: all 0.25s ease;
          }
          .hero:hover { transform: scale(1.02); box-shadow: 0 4px 18px rgba(0,0,0,0.08); }
          .hero .title { font-size: clamp(1.6rem, 1.1vw + 1.1rem, 2.0rem); font-weight: 700; letter-spacing:.2px; }
          .hero .subtitle { color: var(--muted); margin-top: 6px; }

          /* Cards */
          .card {
            background: var(--card); border:1px solid var(--ring); border-radius: 12px; padding: 14px 16px;
            width: 100%; max-width: 760px; margin: 0 auto 10px; box-sizing: border-box; transition: all 0.25s ease;
          }
          .card:hover { transform: translateY(-4px); box-shadow: 0 4px 18px rgba(0,0,0,0.08); }
          .card h3 { margin:0 0 8px 0; font-weight:600; font-size:22px; letter-spacing:.2px; text-align:center; }

          /* KPI */
          .kpi {
            background: var(--card-2); border:1px solid var(--ring); border-radius: 12px; padding: 14px; text-align:center; transition: all 0.25s ease;
          }
          .kpi:hover { transform: translateY(-4px); box-shadow: 0 4px 18px rgba(0,0,0,0.08); }
          .kpi .label { color: var(--muted); font-size: .95rem; }
          .kpi .value { font-size: 1.35rem; font-weight: 700; margin-top: 2px; }
          .kpi .sub { color: var(--muted); font-size: .85rem; }

          /* Snapshot metric */
          .snap-metric { margin: 6px 0 10px; }
          .snap-metric .label { color: var(--muted); font-size:.92rem; }
          .snap-metric .value { font-size: 1.2rem; font-weight: 700; margin-top: 2px; }

          .badge { padding: 3px 8px; border-radius: 9999px; font-weight: 700; font-size:.78rem; border:1px solid var(--ring); }
          .badge.ok { background: rgba(52,211,153,.12); color: var(--ok); }
          .badge.warn { background: rgba(251,188,4,.12); color: var(--warn); }
          .badge.bad { background: rgba(255,107,107,.12); color: var(--danger); }

          /* Inputs (Streamlit) */
          .stNumberInput, .stTextInput, .stTextArea { width: 100% !important; }
          .stNumberInput input, .stTextInput input, textarea {
            border:1px solid var(--ring) !important; border-radius: 10px !important; padding: 10px 12px !important; width: 100% !important; height: 44px !important; box-sizing: border-box; transition: all 0.25s ease;
            font-family: 'Space Grotesk', 'Plus Jakarta Sans', system-ui, sans-serif !important; font-weight: 500; letter-spacing: 0.2px;
          }
          .stNumberInput input:hover, .stTextInput input:hover, textarea:hover { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(37,99,235,0.15); }
          .stNumberInput input:focus, .stTextInput input:focus, textarea:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.25) !important; }

          /* Our custom money inputs */
          .money-wrap input {
            border:1px solid var(--ring) !important; border-radius: 10px !important;
            padding: 10px 12px !important; width: 100% !important; height: 44px !important; box-sizing: border-box;
            transition: all 0.25s ease;
            font-family: 'Space Grotesk', 'Plus Jakarta Sans', system-ui, sans-serif !important; font-weight: 500; letter-spacing: 0.2px;
          }
          .money-wrap input:hover { border-color: var(--accent); box-shadow: 0 0 0 3px rgba(37,99,235,0.15); }
          .money-wrap input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.25) !important; }

          /* Sticky summary bar */
          .sticky-summary {
            position: sticky; bottom: 0; z-index: 100; background: var(--card-2); border-top:1px solid var(--ring); padding: 8px 12px; border-radius: 12px 12px 0 0; max-width: 760px; margin: 0 auto; transition: all 0.25s ease;
          }
          .summary-grid { display:grid; gap:10px; grid-template-columns: repeat(3, minmax(0,1fr)); }
          @media (max-width: 900px) { .summary-grid { grid-template-columns: 1fr; } }

          /* CTA (centered Streamlit button) */
          .cta-wrap {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 8px 0 12px;
          }
          .cta-wrap .stButton > button {
            padding: 12px 24px;
            font-size: 16px; font-weight: 600;
            border: none; border-radius: 9999px;
            background-color: var(--accent); color: #fff;
            cursor: pointer; text-align: center; transition: all 0.25s ease;
            display: inline-block;
          }
          .cta-wrap .stButton > button:hover {
            background-color: var(--accent-hover);
            transform: scale(1.04);
            filter: brightness(1.06);
            box-shadow: 0 3px 12px rgba(0,0,0,0.12);
          }

          /* Section width limiter + note-card */
          .section { max-width: 760px; margin: 0 auto 10px; }
          .note-card {
            background: var(--card); border:1px solid var(--ring); border-radius: 10px; padding: 8px 12px;
            max-width: 460px; margin: 6px auto 10px; text-align:center; color: var(--muted);
            font-weight: 600; letter-spacing: .2px;
          }

          /* Collapse spacing from Streamlit HTML iframes (used by st_html / CountUp) */
          div[data-testid="stIFrame"]{ margin:0 !important; padding:0 !important; }
          div[data-testid="stIFrame"] > iframe[title="st.iframe"]{
            height:0 !important; min-height:0 !important; border:0 !important; display:block !important; margin:0 !important; padding:0 !important; overflow:hidden !important;
          }
          div[data-testid="stIFrame"] + div{ margin-top:0 !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )

inject_css()

# =========================
# Google Sheets helpers
# =========================
def get_ws():
    sa_info = st.secrets["gcp_service_account"]
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
    gc = gspread.authorize(creds)
    sheet_url = st.secrets["gsheets"]["sheet_url"]
    ws_name   = st.secrets["gsheets"].get("worksheet", "Leads")
    sh = gc.open_by_url(sheet_url)
    return sh.worksheet(ws_name)

def append_signin_to_gsheet(first_name: str, last_name: str, email: str, phone: str) -> bool:
    try:
        ws = get_ws()
        ist = pytz.timezone("Asia/Kolkata")
        now_ist = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
        ws.append_row([now_ist, first_name.strip(), last_name.strip(), email.strip(), phone.strip(), "SIGNIN"], value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"Could not write sign-in to Google Sheet: {e}")
        return False

def append_final_snapshot_to_gsheet_minimal(row_values: list) -> bool:
    try:
        ws = get_ws()
        ws.append_row(row_values, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"Could not write final snapshot to Google Sheet: {e}")
        return False

# =========================
# Helpers: Indian number formatting & custom money inputs
# =========================
def fmt_indian_plain(x):
    """Indian comma format without currency symbol."""
    try:
        n = int(round(float(x)))
    except Exception:
        return str(x)
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
    return ("-" if n < 0 else "") + out

def fmt_money_indian(x):
    return f"₹{fmt_indian_plain(x)}"

def parse_money_input(s: str) -> float:
    """Parse Indian formatted numeric string to float."""
    if s is None:
        return 0.0
    # Remove anything except digits and dot
    cleaned = re.sub(r"[^\d.]", "", str(s))
    if cleaned == "" or cleaned == ".":
        return 0.0
    try:
        return float(cleaned)
    except:
        return 0.0

def money_input(label: str, value: float, min_value: float, max_value: float, key: str):
    """Text input with Indian commas. Returns clamped float."""
    # Prepare default text (persist per session)
    default_txt = st.session_state.get(f"{key}_txt", fmt_indian_plain(value))
    st.markdown("<div class='money-wrap'>", unsafe_allow_html=True)
    txt = st.text_input(label, value=default_txt, key=key)
    st.markdown("</div>", unsafe_allow_html=True)

    # Parse & clamp
    parsed = parse_money_input(txt)
    parsed = max(min_value, min(max_value, parsed))

    # Re-format text to keep commas consistent in UI
    formatted = fmt_indian_plain(parsed)
    if txt != formatted:
        st.session_state[f"{key}_txt"] = formatted

    return float(parsed)

def html_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
         .replace('"', "&quot;")
         .replace("'", "&#39;")
    )

# =========================
# SIMPLE SIGN-IN GATE
# =========================
if "signed_in" not in st.session_state:
    st.session_state.signed_in = False

if not st.session_state.signed_in:
    st.markdown("""
        <div class='hero'>
          <div class='title'>Welcome</div>
          <div class='subtitle'>Sign in to continue to the Retirement Planner</div>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.markdown("<div class='card'><h3>Your details</h3>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("First name")
        with c2:
            last_name = st.text_input("Last name")
        c3, c4 = st.columns(2)
        with c3:
            email = st.text_input("Email address")
        with c4:
            phone = st.text_input("Phone number")
        submit = st.button("Sign in & continue", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if submit:
        if not first_name or not last_name or not email or not phone:
            st.warning("Please fill First name, Last name, Email, and Phone.")
        else:
            ok = append_signin_to_gsheet(first_name, last_name, email, phone)
            if ok:
                st.session_state.signed_in = True
                st.session_state.user_first_name = first_name.strip()
                st.session_state.user_last_name = last_name.strip()
                st.session_state.user_email = email.strip()
                st.session_state.user_phone = phone.strip()
                st.success("You're signed in. Loading planner…")
                st.rerun()

    st.markdown("<div style='text-align:center; color:var(--muted); font-size:0.85rem;'>v7.8 — Money inputs with Indian commas + limits</div>", unsafe_allow_html=True)
    st.stop()

# =====================================================================
# CALCULATOR PAGE
# =====================================================================
# Personalized title using first name
fname = st.session_state.get("user_first_name", "").strip()
fname_display = html_escape(fname) if fname else "Your"
possessive = (fname_display + "&#39;s") if fname_display else "Your"
st.markdown(
    f"""
    <div class='hero'>
      <div class='title'>{possessive} Retirement Planner</div>
      <div class='subtitle'>Please follow the instructions below</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# Excel parity helpers
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
# INPUTS (3-per-row, robust clamping)
# =========================
MAX_MONTHLY = 5_000_000       # 50,00,000
MAX_BIG     = 1_000_000_000   # 1,00,00,00,000

with st.container():
    st.markdown("<div class='section'>", unsafe_allow_html=True)

    # Row 1
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        age_now = st.number_input("Current age", min_value=16, max_value=80, value=25, step=1)
    with r1c2:
        min_retire_age = age_now + 1
        hard_max_retire = 90
        max_retire_age = max(min_retire_age, hard_max_retire)
        default_retire_age = min(max(60, min_retire_age), max_retire_age)
        age_retire = st.number_input("Target retirement age", min_value=min_retire_age, max_value=max_retire_age, value=default_retire_age, step=1)
    with r1c3:
        min_life_exp = age_retire + 1
        hard_max_life = 110
        max_life_exp = max(min_life_exp, hard_max_life)
        default_life = min(max(90, min_life_exp), max_life_exp)
        life_expectancy = st.number_input("Life expectancy", min_value=min_life_exp, max_value=max_life_exp, value=default_life, step=1)

    years_left = max(0, age_retire - age_now)
    st.caption(f"Years to retirement: **{years_left}** • Years after retirement: **{max(life_expectancy-age_retire,0)}**")

    # Row 2
    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        infl_pct = st.number_input("Expense inflation (% p.a.)", min_value=0.0, max_value=20.0, value=5.0, step=0.1, format="%.1f")
    with r2c2:
        st.number_input("Return on existing investments (% p.a.) — fixed", value=12.0, step=0.0, disabled=True, format="%.1f")
        ret_exist_pct = 12.0
    with r2c3:
        monthly_exp = money_input("Current monthly expenses (₹)", value=50_000.0, min_value=0.0, max_value=MAX_MONTHLY, key="monthly_exp")

    # Fixed caption under row 2
    st.caption("Return after retirement (% p.a.) — **fixed at 6.0%**")

    # Row 3
    r3c1, r3c2, r3c3 = st.columns(3)
    with r3c1:
        yearly_exp = float(monthly_exp) * 12.0
        # Disabled display with commas
        st.text_input("Yearly expenses (₹)", value=fmt_indian_plain(yearly_exp), disabled=True, key="yearly_exp_display")
    with r3c2:
        current_invest = money_input("Current investments (₹)", value=1_000_000.0, min_value=0.0, max_value=MAX_BIG, key="current_invest")
    with r3c3:
        legacy_goal = money_input("Inheritance to leave (₹)", value=0.0, min_value=0.0, max_value=MAX_BIG, key="legacy_goal")

    st.caption("Taxes are not modeled in this version.")
    st.markdown("</div>", unsafe_allow_html=True)

# Map UI -> internal vars
F3, F4, F6 = age_now, age_retire, life_expectancy
F5 = years_left
ret_pre_pct = 12.0
ret_post_pct = 6.0
F7, F8, F9, F10 = infl_pct/100.0, ret_pre_pct/100.0, ret_post_pct/100.0, (ret_exist_pct/100.0)
F11, F12, F13, F14 = float(monthly_exp), float(yearly_exp), float(current_invest), float(legacy_goal)

# CALCS
F17 = (F9 - F7) / (1.0 + F7)             # Net real return during retirement
F18 = FV(F7, (F4 - F3), 0.0, -F12, 1)    # Annual expenses at retirement start
F19 = PV(F17, (F6 - F4), -F18, -F14, 1)  # Required corpus at retirement (incl. inheritance as terminal)
FV_existing_at_ret = FV(F10, (F5), 0.0, -F13, 1)
F20 = F19 - FV_existing_at_ret
F21_raw = PMT(F8 / 12.0, (F4 - F3) * 12.0, 0.0, -F20, 1)
F22_raw = PV(F8, (F4 - F3), 0.0, -F20, 1)
F21_display = max(F21_raw, 0.0)  # never negative
F22_display = max(F22_raw, 0.0)  # never negative

# Inheritance-specific
F24 = PV(F9, (F6 - F4), 0.0, -F14, 1)
F25 = PMT(F8 / 12.0, (F4 - F3) * 12.0, 0.0, -F24, 1)
F26 = PMT(F8, (F4 - F3), 0.0, -F24, 1)

coverage = 0.0 if F19 == 0 else max(0.0, min(1.0, FV_existing_at_ret / F19))
status_class = "ok" if coverage >= 0.85 else ("warn" if coverage >= 0.5 else "bad")
status_text = "Strong" if status_class == "ok" else ("Moderate" if status_class == "warn" else "Low")

# =========================
# KPI ROWS (aligned + animations)
# =========================
if "prev_F19" not in st.session_state: st.session_state.prev_F19 = 0
if "prev_F21" not in st.session_state: st.session_state.prev_F21 = 0
if "prev_F22" not in st.session_state: st.session_state.prev_F22 = 0
if "prev_F25" not in st.session_state: st.session_state.prev_F25 = 0
if "prev_F26" not in st.session_state: st.session_state.prev_F26 = 0
if "prev_snap_fv" not in st.session_state: st.session_state.prev_snap_fv = 0
if "prev_snap_gap" not in st.session_state: st.session_state.prev_snap_gap = 0

# Small "Pick one" card above SIP & Lumpsum
st.markdown("<div class='note-card'>Pick one: <b>Monthly SIP</b> or <b>Lumpsum Today</b></div>", unsafe_allow_html=True)

# Row 1: Corpus | Monthly SIP | Lumpsum
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Required corpus at retirement</div>"
        f"<div id='kpi1' class='value'>{fmt_money_indian(st.session_state.get('prev_F19', 0))}</div>"
        f"<div class='sub'>Covers expenses till life expectancy incl. inheritance</div>"
        f"</div>", unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Monthly SIP needed</div>"
        f"<div id='kpi2' class='value'>{fmt_money_indian(st.session_state.get('prev_F21', 0))}</div>"
        f"<div class='sub'>Contributed at the start of each month</div>"
        f"</div>", unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Lumpsum needed today</div>"
        f"<div id='kpi3' class='value'>{fmt_money_indian(st.session_state.get('prev_F22', 0))}</div>"
        f"<div class='sub'>One‑time investment</div>"
        f"</div>", unsafe_allow_html=True,
    )

# Tiny space BETWEEN KPI rows
st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

# Row 2: (spacer) | Additional SIP | Additional Lumpsum
a1, a2, a3 = st.columns(3)
with a1:
    st.markdown("&nbsp;", unsafe_allow_html=True)
with a2:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Additional SIP (for inheritance)</div>"
        f"<div id='kpi4' class='value'>{fmt_money_indian(st.session_state.get('prev_F25', 0))}</div>"
        f"<div class='sub'>Extra monthly to fund legacy</div>"
        f"</div>", unsafe_allow_html=True,
    )
with a3:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Additional Lumpsum (for inheritance)</div>"
        f"<div id='kpi5' class='value'>{fmt_money_indian(st.session_state.get('prev_F26', 0))}</div>"
        f"<div class='sub'>As per your formula</div>"
        f"</div>", unsafe_allow_html=True,
    )

# Single COUNTUP block to avoid extra iframe gaps
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
          }} catch (e) {{ return "₹" + num; }}
        }}
        function run(id, end, start) {{
          const el = window.parent.document.getElementById(id);
          if (!el || typeof countUp === 'undefined') return;
          const opts = {{ duration: 1.0, formattingFn: formatIndian }};
          try {{ new countUp.CountUp(el, end, {{...opts, startVal: start}}).start(); }} catch (e) {{}}
        }}

        // KPI row 1
        run('kpi1', {int(F19)}, {int(st.session_state.get('prev_F19', 0))});
        run('kpi2', {int(max(F21_display, 0))}, {int(st.session_state.get('prev_F21', 0))});
        run('kpi3', {int(max(F22_display, 0))}, {int(st.session_state.get('prev_F22', 0))});

        // KPI row 2 (additional)
        run('kpi4', {int(F25)}, {int(st.session_state.get('prev_F25', 0))});
        run('kpi5', {int(F26)}, {int(st.session_state.get('prev_F26', 0))});

        // Snapshot
        run('snap1', {int(FV_existing_at_ret)}, {int(st.session_state.get('prev_snap_fv', 0))});
        run('snap2', {int(max(F20, 0))}, {int(st.session_state.get('prev_snap_gap', 0))});
      }})();
    </script>
    """,
    height=0,
)

# Save previous KPI values
st.session_state.prev_F19 = int(F19)
st.session_state.prev_F21 = int(max(F21_display, 0))
st.session_state.prev_F22 = int(max(F22_display, 0))
st.session_state.prev_F25 = int(F25)
st.session_state.prev_F26 = int(F26)

# Reduced space before Status/Snapshot
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# Status of Retirement Goal & Snapshot
cA, cB = st.columns([1.2, 1])
with cA:
    st.markdown("<div class='card'><h3>Status of Retirement Goal</h3>", unsafe_allow_html=True)
    st.caption("Portion of the required corpus (incl. inheritance) already covered by your investments grown to retirement")
    st.progress(coverage)
    st.markdown(f"<span class='badge {status_class}'>Coverage: {coverage*100:.1f}% — {status_text}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with cB:
    st.markdown("<div class='card'><h3>Snapshot</h3>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='snap-metric'><div class='label'>Existing corpus at retirement (future value)</div>"
        f"<div id='snap1' class='value'>{fmt_money_indian(st.session_state.prev_snap_fv)}</div></div>",
        unsafe_allow_html=True,
    )
    gap = max(F20, 0.0)
    st.markdown(
        f"<div class='snap-metric'><div class='label'>Gap to fund</div>"
        f"<div id='snap2' class='value'>{fmt_money_indian(st.session_state.prev_snap_gap)}</div></div>",
        unsafe_allow_html=True,
    )
    if F20 < 0:
        st.caption("You have a **surplus** based on current settings. SIP/Lumpsum may be 0.")
    st.markdown("</div>", unsafe_allow_html=True)

# Update prev snapshot values
st.session_state.prev_snap_fv = int(FV_existing_at_ret)
st.session_state.prev_snap_gap = int(gap)

# Reduced space before CTA
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# --- Replace your current CTA block (clicked handling & redirect) with this ---

# Centered CTA wrapper (keeps your styling)
st.markdown("<div class='cta-wrap'>", unsafe_allow_html=True)
save_clicked = st.button("Save & get Ventura link", type="primary", key="cta_submit")
st.markdown("</div>", unsafe_allow_html=True)

if save_clicked:
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

    # Build the minimal ordered row you wanted
    row = [
        now_ist,
        st.session_state.get("user_first_name", ""),
        st.session_state.get("user_last_name", ""),
        st.session_state.get("user_email", ""),
        st.session_state.get("user_phone", ""),
        int(F3), int(F4), int(F6),
        float(infl_pct), 12.0,
        float(F11), float(F12), float(F13), float(F14),
        float(F19), float(FV_existing_at_ret), float(max(F20, 0.0)),
        float(max(F21_display, 0.0)), float(max(F22_display, 0.0)),
        float(F25), float(F26),
        float(round(coverage * 100.0, 1)),
    ]

    ok = append_final_snapshot_to_gsheet_minimal(row)
    if ok:
        st.success("Saved! Click the button below to open Ventura in a new tab.")

        # A *real* anchor link (user click opens new tab reliably)
        st.markdown(
            """
            <div class='cta-wrap'>
              <a class='start-btn' href='https://www.venturasecurities.com/' target='_blank' rel='noopener'>
                Open Ventura
              </a>
            </div>
            """,
            unsafe_allow_html=True,
        )


# Sticky Summary
st.markdown(
    f"""
    <div class='sticky-summary'>
      <div class='summary-grid'>
        <div><div class='hint'>Corpus at retirement</div><div class='mono' style='font-weight:800; font-size:1.05rem;'>{fmt_money_indian(F19)}</div></div>
        <div><div class='hint'>Monthly SIP</div><div class='mono' style='font-weight:800; font-size:1.05rem;'>{fmt_money_indian(F21_display)}</div></div>
        <div><div class='hint'>Coverage now</div><div class='mono' style='font-weight:800; font-size:1.05rem;'>{coverage*100:.1f}%</div></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Version + fixed before‑retirement caption
st.markdown("<div style='text-align:center; color:var(--muted); font-size:0.85rem;'>v7.8 — Money inputs w/ Indian commas, limits, Pick-one card, new title</div>", unsafe_allow_html=True)
st.caption("Return before retirement (% p.a.) — **fixed at 12.0%**")
