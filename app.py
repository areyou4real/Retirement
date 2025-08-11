import streamlit as st
import pandas as pd

# =========================
# Page Config
# =========================
st.set_page_config(
    page_title="Retirement FI Calculator",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# =========================
# Theme state & CSS injector
# =========================
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light"  # default

def inject_css(mode: str = "Light"):
    # Color tokens per your spec
    if mode == "Light":
        bg = "#FFFFFF"
        surface = "#F7F8FA"
        text = "#111827"
        muted = "#6B7280"
        border = "#E5E7EB"
        accent = "#2563EB"
        accent_hover = "#1E40AF"
        zebra = "rgba(0,0,0,.02)"
    else:
        bg = "#0B0F14"
        surface = "#121820"
        text = "#E5E7EB"
        muted = "#9CA3AF"
        border = "#243041"
        accent = "#3B82F6"
        accent_hover = "#3B82F6"  # small apps: reuse for hover
        zebra = "rgba(255,255,255,.03)"

    st.markdown(
        f"""
        <style>
          @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

          :root {{
            --bg: {bg};
            --surface: {surface};
            --text: {text};
            --muted: {muted};
            --border: {border};
            --accent: {accent};
            --accent-hover: {accent_hover};

            --success: #16A34A;
            --warning: #D97706;
            --error:   #DC2626;

            --radius-card: 12px;
            --radius-input: 10px;
            --radius-pill: 9999px;

            --shadow-1: 0 1px 2px rgba(0,0,0,.06), 0 8px 24px rgba(0,0,0,.04);
            --zebra: {zebra};

            --maxw: 72rem; /* 1152px */
            --gutter: 24px;
          }}

          html, body, [class*="css"] {{
            background: var(--bg);
            color: var(--text);
            font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif;
            font-size: 16px; /* base */
            line-height: 1.6; /* body */
          }}

          h1, h2, h3, h4, h5, h6 {{ line-height: 1.25; font-weight: 600; }}
          .label, button {{ letter-spacing: 0.2px; }}
          .tnum {{ font-feature-settings: "tnum"; font-variant-numeric: tabular-nums; }}

          /* Inputs */
          .stTextInput input, .stNumberInput input, .stSelectbox select, .stTextArea textarea {{
            border: 1px solid var(--border);
            border-radius: var(--radius-input) !important;
            padding: 12px !important;
            box-shadow: none !important;
            outline: none !important;
          }}
          .stNumberInput button {{ border-radius: 8px !important; }}
          .stNumberInput > div > div > input:focus,
          .stTextInput input:focus,
          .stSelectbox div:focus,
          .stTextArea textarea:focus {{
            box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 40%, transparent) !important;
            border-color: var(--accent) !important;
          }}

          /* Buttons */
          .btn-primary button {{
            background: var(--accent) !important;
            color: white !important;
            border: none !important;
            border-radius: var(--radius-pill) !important;
            padding: 10px 16px !important;
            font-weight: 500;
          }}
          .btn-primary button:hover {{ background: var(--accent-hover) !important; }}
          .btn-link button {{
            background: transparent !important;
            color: var(--accent) !important;
            border: none !important;
            text-decoration: underline;
          }}

          /* Cards */
          .card {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: var(--radius-card);
            padding: 24px;
            box-shadow: var(--shadow-1);
          }}
          .card h3 {{ margin: 0 0 8px 0; }}

          /* KPI */
          .kpi {{ display:flex; flex-direction:column; gap:6px; align-items:flex-start; }}
          .kpi .label {{ color: var(--muted); font-size: 14px; }}
          .kpi .value {{ font-weight: 600; font-size: 24px; }}
          .kpi .sub {{ color: var(--muted); font-size: 14px; }}

          /* Two-pane wrapper */
          .wrap {{
            max-width: var(--maxw);
            margin: 0 auto;
            padding: 24px;
          }}
          .twocol {{
            display: grid;
            grid-template-columns: 1fr 1.25fr;
            gap: var(--gutter);
          }}

          /* Table zebra + numerals */
          .stDataFrame tbody tr:nth-child(odd) td {{ background: var(--zebra) !important; }}
          .stDataFrame, .stDataFrame * {{ font-variant-numeric: tabular-nums; font-feature-settings: "tnum"; }}

          /* Sticky summary */
          .sticky {{
            position: sticky; bottom: 0; z-index: 5;
            background: var(--surface);
            border-top: 1px solid var(--border);
            padding: 12px 16px;
            border-radius: 12px 12px 0 0;
          }}

          /* Reduced motion */
          @media (prefers-reduced-motion: reduce) {{
            * {{ transition: none !important; animation: none !important; }}
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )

# Top bar with theme toggle
top_l, top_c, top_r = st.columns([1, 6, 1])
with top_c:
    st.markdown(
        "<h1 class='tnum' style='margin: 12px 0 0 0;'>Financial Independence Planner</h1>"
        "<div style='color: var(--muted); margin-bottom: 8px;'>"
        "Minimal inputs. Clear outputs. Excel‑parity PV/FV/PMT (payments at period start where applicable)."
        "</div>",
        unsafe_allow_html=True,
    )
with top_r:
    st.selectbox(
        "Theme",
        ["Light", "Dark"],
        index=0 if st.session_state.theme_mode == "Light" else 1,
        key="theme_mode",
        label_visibility="collapsed",
    )

inject_css(st.session_state.theme_mode)

# =========================
# Excel-parity helpers
# =========================
def _pow1p(x: float, n: float) -> float:
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
    # Excel: PMT = -(r*(pv*g + fv)) / ((1 + r*type)*(g - 1))
    return -(rate * (pv * g + fv)) / ((1 + rate * typ) * (g - 1))

# =========================
# Two‑pane layout
# =========================
st.markdown("<div class='wrap'>", unsafe_allow_html=True)
st.markdown("<div class='twocol'>", unsafe_allow_html=True)

# ---------- LEFT: INPUTS ----------
with st.container():
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### Your Inputs")

    # Timeline
    c1, c2, c3 = st.columns(3)
    with c1:
        age_now = st.number_input("Current age", min_value=16, max_value=80, value=25, step=1)
    with c2:
        age_fi = st.number_input("Target FI age", min_value=age_now + 1, max_value=90, value=60, step=1)
    with c3:
        life_expectancy = st.number_input("Life expectancy", min_value=age_fi + 1, max_value=110, value=90, step=1)
    years_left = max(0, age_fi - age_now)
    st.caption(f"Years to FI: **{years_left}** · Years post‑FI: **{max(life_expectancy - age_fi, 0)}**")

    # Rates (% p.a.)
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        infl_pct = st.number_input("Expense inflation (% p.a.)", min_value=0.0, max_value=20.0, value=5.0, step=0.1, format="%.1f")
    with r2:
        ret_pre_pct = st.number_input("Return before FI (% p.a.)", min_value=0.0, max_value=30.0, value=10.0, step=0.1, format="%.1f")
    with r3:
        ret_post_pct = st.number_input("Return after FI (% p.a.)", min_value=0.0, max_value=20.0, value=7.0, step=0.1, format="%.1f")
    with r4:
        ret_exist_pct = st.number_input("Return on existing investments (% p.a.)", min_value=0.0, max_value=20.0, value=8.0, step=0.1, format="%.1f")

    # Cash flows
    cf1, cf2, cf3 = st.columns(3)
    with cf1:
        monthly_exp = st.number_input("Current monthly expenses (₹)", min_value=0.0, value=50_000.0, step=1_000.0, format="%.0f")
    with cf2:
        # Sync yearly with monthly on first render; keep user edits after
        default_yearly = monthly_exp * 12.0
        yearly_exp = st.number_input("Yearly expenses (₹)", min_value=0.0, value=default_yearly, step=5_000.0, format="%.0f")
    with cf3:
        current_invest = st.number_input("Current investments (₹)", min_value=0.0, value=1_000_000.0, step=10_000.0, format="%.0f")

    legacy_goal = st.number_input("Inheritance to leave (₹)", min_value=0.0, value=0.0, step=10_000.0, format="%.0f")
    st.caption("Note: Taxes are not modeled in this version.")
    st.markdown("</div>", unsafe_allow_html=True)

# ---------- RIGHT: OUTPUTS ----------
with st.container():
    # Core calculations (Excel parity, using your F3–F22 logic)
    F7 = infl_pct / 100.0
    F8 = ret_pre_pct / 100.0
    F9 = ret_post_pct / 100.0
    F10 = ret_exist_pct / 100.0

    F17 = (F9 - F7) / (1.0 + F7)  # Net real return post-FI
    F18 = FV(F7, years_left, 0.0, -yearly_exp, 1)  # Annual expenses at FI (inflated)
    F19 = PV(F17, (life_expectancy - age_fi), -F18, 0.0, 1)  # Required corpus at FI till life expectancy
    FV_existing_at_FI = FV(F10, years_left, 0.0, -current_invest, 1)  # FV of current investments at FI
    F20 = F19 - FV_existing_at_FI  # Gap to fund
    F21 = PMT(F8 / 12.0, years_left * 12.0, 0.0, -F20, 1)  # Monthly SIP (beginning of month)
    F22 = PV(F8, years_left, 0.0, -F20, 1)  # Lumpsum today

    coverage = 0.0 if F19 == 0 else max(0.0, min(1.0, FV_existing_at_FI / F19))

    # KPI row
    k1, k2, k3 = st.columns(3)
    with k1:
        st.markdown("<div class='card kpi'>", unsafe_allow_html=True)
        st.markdown("<div class='label'>Required corpus at FI</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='value tnum'>₹{F19:,.0f}</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub'>Covers expenses till life expectancy</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with k2:
        st.markdown("<div class='card kpi'>", unsafe_allow_html=True)
        st.markdown("<div class='label'>Monthly SIP needed</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='value tnum'>₹{F21:,.0f}</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub'>Contributed at the start of each month</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with k3:
        st.markdown("<div class='card kpi'>", unsafe_allow_html=True)
        st.markdown("<div class='label'>Lumpsum needed today</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='value tnum'>₹{F22:,.0f}</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub'>If you prefer a one‑time investment</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

    # Readiness + Snapshot
    gA, gB = st.columns([1.2, 1.0])
    with gA:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Readiness gauge")
        st.caption("How much of the required corpus is already covered by your existing investments (grown to FI)")
        st.progress(coverage)
        label = "Strong" if coverage >= 0.85 else ("Moderate" if coverage >= 0.5 else "Low")
        st.write(f"Coverage: **{coverage*100:.1f}%** — {label}")
        st.markdown("</div>", unsafe_allow_html=True)

    with gB:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Snapshot")
        gap = max(F20, 0.0)
        st.metric("Existing corpus at FI (future value)", f"₹{FV_existing_at_FI:,.0f}")
        st.metric("Gap to fund", f"₹{gap:,.0f}")
        if F20 < 0:
            st.caption("You have a **surplus** based on current settings. SIP/Lumpsum may be 0.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div style='height: 8px'></div>", unsafe_allow_html=True)

    # Overview table + export
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### Overview")
    table = pd.DataFrame(
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
                f"₹{F18:,.0f}",
                f"₹{F19:,.0f}",
                f"₹{FV_existing_at_FI:,.0f}",
                f"₹{F20:,.0f}",
                f"₹{F21:,.0f}",
                f"₹{F22:,.0f}",
            ],
        }
    )
    st.dataframe(table, use_container_width=True, height=300)
    csv_bytes = table.to_csv(index=False).encode("utf-8")
    col_dl1, col_dl2 = st.columns([1, 3])
    with col_dl1:
        st.download_button(
            "⬇️ Download overview (CSV)",
            data=csv_bytes,
            file_name="fi_overview.csv",
            mime="text/csv",
            key="dl_overview",
        )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)  # .twocol
st.markdown("</div>", unsafe_allow_html=True)  # .wrap

# Sticky summary footer
st.markdown(
    f"""
    <div class="sticky tnum">
      <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;">
        <div><div style="color:var(--muted);font-size:14px;">Corpus at FI</div><div style="font-weight:600;font-size:20px;">₹{F19:,.0f}</div></div>
        <div><div style="color:var(--muted);font-size:14px;">Monthly SIP</div><div style="font-weight:600;font-size:20px;">₹{F21:,.0f}</div></div>
        <div><div style="color:var(--muted);font-size:14px;">Coverage now</div><div style="font-weight:600;font-size:20px;">{coverage*100:.1f}%</div></div>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)
