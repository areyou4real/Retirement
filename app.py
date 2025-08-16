import streamlit as st
import pandas as pd
import numpy as np
from streamlit.components.v1 import html as st_html
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import pytz
import time, hashlib  # <-- for anti-spam/idempotency

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
            --bg:#f7f8fc; --card:#ffffff; --card-2:#fbfcff; --text:#0e1321; --muted:#5d6473; --ring:#e7eaf3; --chip:#eef2ff;
            --accent:#2563EB; --accent-hover:#1E40AF; --warn:#fbbc04; --danger:#ff6b6b; --ok:#34d399;
          }
          @media (prefers-color-scheme: dark) {
            :root { --bg:#0b0f1a; --card:#12182a; --card-2:#0e1424; --text:#e8edf5; --muted:#9aa4b2; --ring:#27304a; --chip:#1b2340;
                    --accent:#3B82F6; --accent-hover:#2563EB; }
          }

          html, body, [class*="css"] { background:var(--bg); color:var(--text); font-family:'Plus Jakarta Sans',system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif; font-size:16px; line-height:1.6; }
          .mono { font-family:'JetBrains Mono',ui-monospace,SFMono-Regular,Menlo,monospace; font-variant-numeric:tabular-nums; font-feature-settings:"tnum"; }
          .num  { font-family:'Space Grotesk','Plus Jakarta Sans',system-ui,sans-serif; font-variant-numeric:tabular-nums; font-feature-settings:"tnum"; }

          /* HERO */
          .hero{ padding:20px 18px; border:1px solid var(--ring); border-radius:14px;
                 background: radial-gradient(1200px 600px at 12% -10%, rgba(110,231,183,.12) 0%, transparent 50%),
                             radial-gradient(900px 500px at 95% 10%, rgba(138,180,248,.10) 0%, transparent 50%),
                             linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,0)); max-width:760px; margin:0 auto; text-align:center; transition:.25s; }
          .hero:hover{ transform:scale(1.02); box-shadow:0 4px 18px rgba(0,0,0,.08); }
          .hero .title{ font-size:clamp(1.6rem,1.1vw + 1.1rem,2.0rem); font-weight:700; letter-spacing:.2px; }
          .hero .subtitle{ color:var(--muted); margin-top:6px; }

          /* Cards */
          .card{ background:var(--card); border:1px solid var(--ring); border-radius:12px; padding:14px 16px; width:100%; max-width:760px; margin:0 auto 10px; box-sizing:border-box; transition:.25s; }
          .card:hover{ transform:translateY(-4px); box-shadow:0 4px 18px rgba(0,0,0,.08); }
          .card h3{ margin:0 0 8px 0; font-weight:600; font-size:22px; letter-spacing:.2px; text-align:center; }

          /* KPI */
          .kpi{ background:var(--card-2); border:1px solid var(--ring); border-radius:12px; padding:14px; text-align:center; transition:.25s; min-height:112px; box-sizing:border-box; }
          .kpi:hover{ transform:translateY(-4px); box-shadow:0 4px 18px rgba(0,0,0,.08); }
          .kpi .label{ color:var(--muted); font-size:.95rem; }
          .kpi .value{ font-size:1.35rem; font-weight:700; margin-top:2px; }
          .kpi .sub{ color:var(--muted); font-size:.85rem; }

          /* Row-3 animation */
          .kpi.row3{ transition:all .28s ease; }
          .kpi.row3.hidden{ max-height:0; opacity:0; margin:0!important; padding-top:0!important; padding-bottom:0!important; border-width:0!important; min-height:0!important; height:0!important; overflow:hidden; }
          .kpi.row3.show{ opacity:1; transform:translateY(0); }
          .kpi.row3.ghost{ visibility:hidden; }

          /* Snapshot metric */
          .snap-metric{ margin:6px 0 10px; }
          .snap-metric .label{ color:var(--muted); font-size:.92rem; }
          .snap-metric .value{ font-size:1.2rem; font-weight:700; margin-top:2px; }

          .badge{ padding:3px 8px; border-radius:9999px; font-weight:700; font-size:.78rem; border:1px solid var(--ring); }
          .badge.ok{ background:rgba(52,211,153,.12); color:var(--ok); }
          .badge.warn{ background:rgba(251,188,4,.12); color:var(--warn); }
          .badge.bad{ background:rgba(255,107,107,.12); color:var(--danger); }

          /* Inputs */
          .stNumberInput, .stTextInput, .stTextArea{ width:100%!important; }
          .stNumberInput input, .stTextInput input, textarea{
            border:1px solid var(--ring)!important; border-radius:10px!important; padding:10px 12px!important; width:100%!important; height:44px!important; box-sizing:border-box; transition:.25s;
            font-family:'Space Grotesk','Plus Jakarta Sans',system-ui,sans-serif!important; font-weight:500; letter-spacing:.2px;
          }
          .stNumberInput input:hover, .stTextInput input:hover, textarea:hover{ border-color:var(--accent); box-shadow:0 0 0 3px rgba(37,99,235,.15); }
          .stNumberInput input:focus, .stTextInput input:focus, textarea:focus{ border-color:var(--accent)!important; box-shadow:0 0 0 3px rgba(37,99,235,.25)!important; }

          /* Sticky summary bar */
          .sticky-summary{ position:sticky; bottom:0; z-index:100; background:var(--card-2); border-top:1px solid var(--ring); padding:8px 12px; border-radius:12px 12px 0 0; max-width:760px; margin:0 auto; transition:.25s; }
          .summary-grid{ display:grid; gap:10px; grid-template-columns:repeat(3, minmax(0,1fr)); }
          @media (max-width:900px){ .summary-grid{ grid-template-columns:1fr; } }

          /* CTA */
          div.cta-wrap{ text-align:center; }
          div.cta-wrap button[kind="primary"]{ margin:12px auto 18px; padding:12px 24px; font-size:16px; font-weight:600; border:none; border-radius:9999px; background-color:var(--accent); color:#fff; cursor:pointer; text-align:center; transition:.25s; display:inline-block; }
          div.cta-wrap button[kind="primary"]::before{ content:""; }
          div.cta-wrap button[kind="primary"]:hover{ background-color:var(--accent-hover); transform:scale(1.04); filter:brightness(1.06); box-shadow:0 3px 12px rgba(0,0,0,.12); }

          .section{ max-width:760px; margin:0 auto 10px; }

          /* Old wrapper shape (iframe inside div[data-testid="stIFrame"]) – keep collapsed */
          div[data-testid="stIFrame"]{ margin:0!important; padding:0!important; height:0!important; min-height:0!important; border:0!important; overflow:hidden!important; }
          div[data-testid="stIFrame"] > iframe[title="st.iframe"]{ display:block!important; height:0!important; min-height:0!important; width:0!important; border:0!important; margin:0!important; padding:0!important; overflow:hidden!important; }
          div[data-testid="stIFrame"] + div{ margin-top:0!important; }

          /* Panels */
          .panel{ background:var(--card); border:1px solid var(--ring); border-radius:12px; padding:14px 16px; width:100%; max-width:760px; margin:0 auto 10px; box-sizing:border-box; transition:.25s; text-align:center; }
          .panel:hover{ transform:translateY(-4px); box-shadow:0 4px 18px rgba(0,0,0,.08); }
          .panel.kpi-surface{ background:var(--card-2); }

          /* === CURRENT DOM: iframe is a DIRECT CHILD of stElementContainer === */
          div[data-testid="stElementContainer"]:has(> iframe.stIFrame){
            margin:0!important; padding:0!important; height:0!important; min-height:0!important; line-height:0!important;
          }
          iframe.stIFrame{
            display:block!important; height:0!important; min-height:0!important; width:0!important; border:0!important; margin:0!important; padding:0!important; overflow:hidden!important;
            position:absolute!important; left:-10000px!important; top:auto!important;
          }
          div[data-testid="stElementContainer"]:has(> iframe.stIFrame) + div[data-testid="stElementContainer"]{ margin-top:0!important; }
          .element-container:has(> iframe.stIFrame){ margin:0!important; padding:0!important; height:0!important; min-height:0!important; line-height:0!important; }
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

def append_final_snapshot_to_gsheet_minimal(row: list) -> bool:
    try:
        ws = get_ws()
        ws.append_row(row, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"Could not write final snapshot to Google Sheet: {e}")
        return False

# =========================
# Indian Number Formatting
# =========================
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

def number_to_words_short(n: float) -> str:
    try:
        n = float(n)
    except:
        return ""
    absn = abs(n)
    if absn >= 1e7:  # crore
        return f"{absn/1e7:.2f} crore"
    if absn >= 1e5:  # lakh
        return f"{absn/1e5:.2f} lakh"
    if absn >= 1e3:  # thousand
        return f"{absn/1e3:.2f} thousand"
    return f"{absn:.0f}"

# =========================
# SIMPLE SIGN-IN GATE (Autofill-aware)
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
            first_name = st.text_input("First name", key="si_first_name")
        with c2:
            last_name = st.text_input("Last name", key="si_last_name")

        c3, c4 = st.columns(2)
        with c3:
            email = st.text_input("Email address", key="si_email")
        with c4:
            phone = st.text_input("Phone number", key="si_phone")

        # ---- Autofill sync: ensure browser/Google autofill is seen by Streamlit without pressing Enter
        st_html(
            """
            <script>
              (function(){
                // Fire synthetic 'input' events for any non-empty autofilled fields
                function nudgeInputs(){
                  const root = window.parent.document;
                  const sel = 'input[type="text"],input[type="email"],input[type="tel"],input:not([type])';
                  const nodes = root.querySelectorAll(sel);
                  nodes.forEach((el)=>{
                    if (el && el.value && el.value.length){
                      el.dispatchEvent(new Event('input', {bubbles:true}));
                      el.dispatchEvent(new Event('change', {bubbles:true}));
                    }
                  });
                }
                // Run a few times to catch late autofill
                nudgeInputs();
                let t=0, id=setInterval(()=>{ nudgeInputs(); if(++t>8) clearInterval(id); }, 250);
                document.addEventListener('visibilitychange', ()=>{ if(!document.hidden) nudgeInputs(); });
                window.addEventListener('pageshow', nudgeInputs);
                window.addEventListener('focus', nudgeInputs, true);
                // Also on blur of any field
                window.addEventListener('blur', (e)=>{ if(e && e.target && e.target.tagName==='INPUT') nudgeInputs(); }, true);
              })();
            </script>
            """,
            height=0,
        )

        submit = st.button("Sign in & continue", type="primary")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if submit:
        # Pull the latest values from session_state (populated by JS-triggered input events)
        first_name = st.session_state.get("si_first_name", "").strip()
        last_name  = st.session_state.get("si_last_name", "").strip()
        email      = st.session_state.get("si_email", "").strip()
        phone      = st.session_state.get("si_phone", "").strip()

        if not first_name or not last_name or not email or not phone:
            st.warning("Please fill First name, Last name, Email, and Phone.")
        else:
            ok = append_signin_to_gsheet(first_name, last_name, email, phone)
            if ok:
                st.session_state.signed_in = True
                st.session_state.user_first_name = first_name
                st.session_state.user_last_name  = last_name
                st.session_state.user_email      = email
                st.session_state.user_phone      = phone
                st.success("You're signed in. Loading planner…")
                st.rerun()

    st.markdown("<div style='text-align:center; color:var(--muted); font-size:0.85rem;'>v8.4 — Autofill-friendly sign-in + row3 sizing/animations</div>", unsafe_allow_html=True)
    st.stop()

# =====================================================================
# CALCULATOR PAGE
# =====================================================================
user_first = st.session_state.get("user_first_name", "")
title_text = f"{user_first}'s Retirement Planner" if user_first else "Retirement Planner"

st.markdown(f"""
    <div class='hero'>
      <div class='title'>{title_text}</div>
      <div class='subtitle'>Please follow the instructions below</div>
    </div>
""", unsafe_allow_html=True)
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
        life_expectancy = st.number_input("Life expectancy", min_value=max(0, min_life_exp), max_value=max_life_exp, value=default_life, step=1)

    years_left = max(0, age_retire - age_now)
    st.caption(f"Years to retirement: **{years_left}** • Years after retirement: **{max(life_expectancy-age_retire,0)}**")

    # Row 2
    r2c1, r2c2, r2c3 = st.columns(3)
    with r2c1:
        infl_pct = st.number_input("Inflation (% p.a.)", min_value=0.0, max_value=20.0, value=5.0, step=1.0)
    with r2c2:
        st.number_input("Return on investments (% p.a.) — fixed", value=12.0, step=0.0, disabled=True, format="%.1f")
        ret_exist_pct = 12.0
    with r2c3:
        monthly_exp = st.number_input("Current monthly expenses (₹)", min_value=0.0, max_value=5_000_000.0, value=50_000.0, step=1_000.0, format="%.0f")
        st.caption(f"≈ {number_to_words_short(monthly_exp)}")

    # Row 3
    r3c1, r3c2, r3c3 = st.columns(3)
    with r3c1:
        yearly_exp = monthly_exp * 12.0
        st.number_input("Yearly expenses (₹)", value=float(yearly_exp), step=0.0, disabled=True, format="%.0f")
        st.caption(f"≈ {number_to_words_short(yearly_exp)}")
    with r3c2:
        current_invest = st.number_input("Current investments (₹)", min_value=0.0, max_value=1_000_000_000.0, value=0.0, step=10_000.0, format="%.0f")
        st.caption(f"≈ {number_to_words_short(current_invest)}")
    with r3c3:
        legacy_goal = st.number_input("Inheritance to leave (₹)", min_value=0.0, max_value=1_000_000_000.0, value=0.0, step=10_000.0, format="%.0f")
        st.caption(f"≈ {number_to_words_short(legacy_goal)}")

    st.caption("Taxes are not modeled in this version.")
    st.markdown("</div>", unsafe_allow_html=True)

# Map UI -> internal vars
F3, F4, F6 = age_now, age_retire, life_expectancy
F5 = years_left
ret_pre_pct = 12.0
ret_post_pct = 6.0
F7, F8, F9, F10 = infl_pct/100.0, ret_pre_pct/100.0, ret_post_pct/100.0, ret_exist_pct/100.0
F11, F12, F13, F14 = monthly_exp, yearly_exp, current_invest, legacy_goal

# =========================
# CALCS (inheritance excluded from base SIP/Lumpsum)
# =========================
F17 = (F9 - F7) / (1.0 + F7)             # Net real return during retirement
F18 = FV(F7, (F4 - F3), 0.0, -F12, 1)    # Annual expenses at retirement start

# Base corpus (excluding inheritance)
F19_base = PV(F17, (F6 - F4), -F18, 0.0, 1)

# FV of existing investments by retirement
FV_existing_at_ret = FV(F10, (F5), 0.0, -F13, 1)

# Base gap -> drives base SIP/Lumpsum
F20_base = F19_base - FV_existing_at_ret

# Base SIP/Lumpsum
F21_raw = PMT(F8 / 12.0, (F4 - F3) * 12.0, 0.0, -F20_base, 1)
F22_raw = PV(F8, (F4 - F3), 0.0, -F20_base, 1)
F21_display = max(F21_raw, 0.0)
F22_display = max(F22_raw, 0.0)

# Inheritance-specific (background)
F24 = PV(F9, (F6 - F4), 0.0, -F14, 1)   # corpus needed at retirement for inheritance
F25 = PMT(F8 / 12.0, (F4 - F3) * 12.0, 0.0, -F24, 1)  # Additional SIP
F26 = PMT(F8, (F4 - F3), 0.0, -F24, 1)                 # Additional Lumpsum

# Displayed corpus = base + inheritance piece (if any)
F19 = F19_base + (F24 if F14 > 0 else 0.0)

# Coverage vs displayed corpus
coverage = 0.0 if F19 == 0 else max(0.0, min(1.0, FV_existing_at_ret / F19))
status_class = "ok" if coverage >= 0.85 else ("warn" if coverage >= 0.5 else "bad")
status_text = "Strong" if status_class == "ok" else ("Moderate" if status_class == "warn" else "Low")

# Totals (only shown if additional > 0)
total_monthly_sip = max(F21_display, 0.0) + max(F25, 0.0)
total_lumpsum     = max(F22_display, 0.0) + max(F26, 0.0)
show_totals = (F25 > 1e-6) or (F26 > 1e-6)
prev_show = st.session_state.get("prev_show_totals", False)

# =========================
# KPI ROWS (aligned + animations)
# =========================
if "prev_F19" not in st.session_state: st.session_state.prev_F19 = 0
if "prev_F21" not in st.session_state: st.session_state.prev_F21 = 0
if "prev_F22" not in st.session_state: st.session_state.prev_F22 = 0
if "prev_F25" not in st.session_state: st.session_state.prev_F25 = 0
if "prev_F26" not in st.session_state: st.session_state.prev_F26 = 0
if "prev_total_monthly" not in st.session_state: st.session_state.prev_total_monthly = 0
if "prev_total_lumpsum" not in st.session_state: st.session_state.prev_total_lumpsum = 0
if "prev_snap_fv" not in st.session_state: st.session_state.prev_snap_fv = 0
if "prev_snap_gap" not in st.session_state: st.session_state.prev_snap_gap = 0

# Row 1
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Required corpus at retirement</div>"
        f"<div id='kpi1' class='value'>{fmt_money_indian(st.session_state.get('prev_F19', 0))}</div>"
        f"<div class='sub'>Base need {'+ inheritance' if F14>0 else ''}</div>"
        f"</div>", unsafe_allow_html=True,
    )
with k2:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Monthly SIP needed</div>"
        f"<div id='kpi2' class='value'>{fmt_money_indian(st.session_state.get('prev_F21', 0))}</div>"
        f"<div class='sub'>Excludes inheritance; start of month</div>"
        f"</div>", unsafe_allow_html=True,
    )
with k3:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Lumpsum needed today</div>"
        f"<div id='kpi3' class='value'>{fmt_money_indian(st.session_state.get('prev_F22', 0))}</div>"
        f"<div class='sub'>Excludes inheritance; one-time</div>"
        f"</div>", unsafe_allow_html=True,
    )

# Gap between row 1 and row 2
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# Row 2
a1, a2, a3 = st.columns(3)
with a1:
    st.markdown(
        "<div class='kpi'>"
        "<div class='label'>Pick one</div>"
        "<div class='value'>Monthly SIP / Lumpsum Today</div>"
        "<div class='sub'>&nbsp;</div>"
        "</div>",
        unsafe_allow_html=True,
    )
with a2:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Additional SIP</div>"
        f"<div id='kpi4' class='value'>{fmt_money_indian(st.session_state.get('prev_F25', 0))}</div>"
        f"<div class='sub'>For inheritance only</div>"
        f"</div>", unsafe_allow_html=True,
    )
with a3:
    st.markdown(
        f"<div class='kpi'>"
        f"<div class='label'>Additional Lumpsum</div>"
        f"<div id='kpi5' class='value'>{fmt_money_indian(st.session_state.get('prev_F26', 0))}</div>"
        f"<div class='sub'>For inheritance only</div>"
        f"</div>", unsafe_allow_html=True,
    )

# Same gap before row 3
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# Row 3 (totals) — uses SAME st.columns + .kpi cards; JS toggles classes for animation
c0, c1, c2 = st.columns(3)
with c0:
    st.markdown(
        f"<div id='row3card0' class='kpi row3 {'ghost' if show_totals else 'hidden'}'>&nbsp;</div>",
        unsafe_allow_html=True,
    )
with c1:
    st.markdown(
        f"<div id='row3card1' class='kpi row3 {'show' if show_totals else 'hidden'}'>"
        f"<div class='label'>Total Monthly SIP (incl. additional)</div>"
        f"<div id='kpi6' class='value'>{fmt_money_indian(st.session_state.get('prev_total_monthly', 0))}</div>"
        f"<div class='sub'>Base SIP + additional</div>"
        f"</div>",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"<div id='row3card2' class='kpi row3 {'show' if show_totals else 'hidden'}'>"
        f"<div class='label'>Total Lumpsum (incl. additional)</div>"
        f"<div id='kpi7' class='value'>{fmt_money_indian(st.session_state.get('prev_total_lumpsum', 0))}</div>"
        f"<div class='sub'>Base lumpsum + additional</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

# JS toggler so appear/disappear animates smoothly even across reruns
st_html(
    f"""
    <script>
      (function(){{
        var wantOpen = {"true" if show_totals else "false"};
        var p  = window.parent.document.getElementById('row3card0');
        var c1 = window.parent.document.getElementById('row3card1');
        var c2 = window.parent.document.getElementById('row3card2');
        if(!p || !c1 || !c2) return;

        function toHidden(el) {{
          el.classList.remove('show','ghost');
          el.classList.add('hidden');
        }}
        function toShow(el) {{
          el.classList.remove('hidden');
          void el.offsetHeight;
          el.classList.add('show');
        }}
        function toGhost(el) {{
          el.classList.remove('hidden');
          void el.offsetHeight;
          el.classList.add('ghost');
        }}

        if (wantOpen) {{
          toGhost(p);
          toShow(c1);
          toShow(c2);
        }} else {{
          toHidden(c1);
          toHidden(c2);
          toHidden(p);
        }}
      }})();
    </script>
    """,
    height=0,
)

# CountUp animations
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
        run('kpi4', {int(max(F25, 0))}, {int(st.session_state.get('prev_F25', 0))});
        run('kpi5', {int(max(F26, 0))}, {int(st.session_state.get('prev_F26', 0))});

        // KPI row 3 (totals)
        run('kpi6', {int(max(total_monthly_sip, 0))}, {int(st.session_state.get('prev_total_monthly', 0))});
        run('kpi7', {int(max(total_lumpsum, 0))}, {int(st.session_state.get('prev_total_lumpsum', 0))});

        // Snapshot
        run('snap1', {int(FV_existing_at_ret)}, {int(st.session_state.get('prev_snap_fv', 0))});
        run('snap2', {int(max(F20_base, 0))}, {int(st.session_state.get('prev_snap_gap', 0))});
      }})();
    </script>
    """,
    height=0,
)

# Save previous KPI values + show state
st.session_state.prev_F19 = int(F19)
st.session_state.prev_F21 = int(max(F21_display, 0))
st.session_state.prev_F22 = int(max(F22_display, 0))
st.session_state.prev_F25 = int(max(F25, 0))
st.session_state.prev_F26 = int(max(F26, 0))
st.session_state.prev_total_monthly = int(max(total_monthly_sip, 0))
st.session_state.prev_total_lumpsum = int(max(total_lumpsum, 0))
st.session_state.prev_show_totals = show_totals

# Reduced space before Status/Snapshot
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

# Status of Retirement Goal & Snapshot
cA, cB = st.columns([1.2, 1])
with cA:
    st.markdown("<div class='panel kpi-surface'><h3>Status of Retirement Goal</h3>", unsafe_allow_html=True)
    st.caption("Portion of the (base + inheritance if any) corpus covered by your investments grown to retirement")
    st.progress(coverage)
    st.markdown(f"<span class='badge {status_class}'>Coverage: {coverage*100:.1f}% — {status_text}</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with cB:
    st.markdown("<div class='panel kpi-surface'><h3>Snapshot</h3>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='snap-metric'><div class='label'>Existing corpus at retirement (future value)</div>"
        f"<div id='snap1' class='value'>{fmt_money_indian(st.session_state.prev_snap_fv)}</div></div>",
        unsafe_allow_html=True,
    )
    gap = max(F20_base, 0.0)  # base gap (aligns with base SIP/Lumpsum)
    st.markdown(
        f"<div class='snap-metric'><div class='label'>Gap to fund</div>"
        f"<div id='snap2' class='value'>{fmt_money_indian(st.session_state.prev_snap_gap)}</div></div>",
        unsafe_allow_html=True,
    )
    if F20_base < 0:
        st.caption("You have a **surplus** for the base goal; SIP/Lumpsum may be 0. Inheritance is handled as additional.")
    st.markdown("</div>", unsafe_allow_html=True)

# Update prev snapshot values
st.session_state.prev_snap_fv = int(FV_existing_at_ret)
st.session_state.prev_snap_gap = int(gap)

# =========================
# CTA: Save + Redirect (anti-spam + idempotency)
# =========================
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

if "saving" not in st.session_state:
    st.session_state.saving = False
if "last_save_time" not in st.session_state:
    st.session_state.last_save_time = 0.0
if "last_payload_sig" not in st.session_state:
    st.session_state.last_payload_sig = ""

cooldown_sec = 8  # disable button briefly after a save

# Prepare the payload row
ist = pytz.timezone("Asia/Kolkata")
now_ist = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
row = [
    now_ist,
    st.session_state.get("user_first_name", ""),
    st.session_state.get("user_last_name", ""),
    st.session_state.get("user_email", ""),
    st.session_state.get("user_phone", ""),
    int(F3), int(F4), int(F6),
    float(infl_pct), 12.0,
    float(F11), float(F12), float(F13), float(F14),
    float(F19),                         # displayed corpus (base + inheritance if any)
    float(FV_existing_at_ret),          # FV existing corpus
    float(max(F20_base, 0.0)),          # base gap
    float(max(F21_display, 0.0)),       # base SIP
    float(max(F22_display, 0.0)),       # base lumpsum
    float(max(F25, 0.0)),               # additional SIP (inheritance)
    float(max(F26, 0.0)),               # additional lumpsum (inheritance)
    float(round(coverage * 100.0, 1)),  # coverage %
]

# Signature to avoid duplicate writes when nothing changed (exclude timestamp)
sig_basis = row[1:].copy()
sig_str = "|".join(map(str, sig_basis))
payload_sig = hashlib.sha256(sig_str.encode("utf-8")).hexdigest()

# Button state & label
time_since_last = time.time() - st.session_state.last_save_time
cooldown_active = time_since_last < cooldown_sec
disabled = st.session_state.saving or cooldown_active

if disabled and cooldown_active:
    remaining = max(1, int(round(cooldown_sec - time_since_last)))
    btn_label = f"Please wait… ({remaining}s)"
elif st.session_state.saving:
    btn_label = "Saving…"
else:
    btn_label = "Save & Open Ventura"

st.markdown("<div class='cta-wrap'>", unsafe_allow_html=True)
save_clicked = st.button(btn_label, type="primary", key="cta_submit", disabled=disabled)
st.markdown("</div>", unsafe_allow_html=True)

if save_clicked and not disabled:
    if payload_sig == st.session_state.last_payload_sig:
        st.info("No changes since last save. Skipping duplicate write.")
        st_html(
            """
            <script>
              try { window.open('https://www.venturasecurities.com/', '_blank', 'noopener'); }
              catch(e) {}
            </script>
            """,
            height=0,
        )
    else:
        try:
            st.session_state.saving = True
            ok = append_final_snapshot_to_gsheet_minimal(row)
            if ok:
                st.session_state.last_payload_sig = payload_sig
                st.session_state.last_save_time = time.time()
                st.success("Saved! Opening Ventura in a new tab…")
                st_html(
                    """
                    <script>
                      try { window.open('https://www.venturasecurities.com/', '_blank', 'noopener'); }
                      catch(e) {}
                    </script>
                    """,
                    height=0,
                )
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
            else:
                st.error("Could not save. Please try again.")
        finally:
            st.session_state.saving = False

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

# Version label + fixed-rate captions at the bottom
st.caption("Return before retirement (% p.a.) — **fixed at 12.0%**")
st.caption("Return after retirement (% p.a.) — **fixed at 6.0%**")
st.markdown("<div style='text-align:center; color:var(--muted); font-size:0.85rem;'>v8.4 — Autofill sign-in + anti-spam save + row3 animations/sizing preserved</div>", unsafe_allow_html=True)
