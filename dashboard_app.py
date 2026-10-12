"""
dashboard_app_v3.py - "Dinoerla NetOps" (redesign 10 Okt 2026, dari mockup canvas).

Yang BERUBAH dibanding dashboard_app.py (v2):
  - Tampilan: home page dengan 4 tile berikon (bahasa Inggris), bukan sidebar radio.
  - Tiap tool: tombol "All tools", kontrol di KIRI (di HP otomatis di ATAS), hasil di kanan/bawah.
  - Daftar regex / info teknis pindah ke expander "Technical details".
  - Error AI yang ramah: 429 (kuota harian habis) dan 503 (server Gemini sibuk).
  - Footer: Built by Dili Noerlan · Built with Claude & Gemini.

Yang TIDAK berubah:
  - Semua logika tool (parse_anomalies, run_check, review_config, sla.*, ojk.*) dipanggil persis
    sama seperti v2. File usecase 01-04 tidak disentuh.
  - Secrets bridge (Streamlit Cloud) dan _load_tool_module() sama persis.
  - Urutan sys.path: 01-network-rca DULU, baru 02-config-review (lihat catatan di v2).
"""
import os
import sys
import importlib
import tempfile
import streamlit as st

# Streamlit Cloud: key disimpan di menu "Secrets" -> salin ke env var, karena kode usecase baca os.environ.
# Di laptop (gak ada secrets.toml) blok ini dilewati, key tetap dari read -s / export.
try:
    if not os.environ.get("GEMINI_API_KEY") and "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
except Exception:
    pass

BASE = os.path.dirname(os.path.abspath(__file__))
RCA_DIR = os.path.join(BASE, "01-network-rca")
CR_DIR  = os.path.join(BASE, "02-config-review")

# --- urutan WAJIB: RCA dulu (biar "prompts" yg ke-cache di sys.modules punya milik RCA) ---
sys.path.insert(0, RCA_DIR)
from parser import ANOMALY_PATTERNS, parse_anomalies      # noqa: E402
from engine import run_check                               # noqa: E402

sys.path.insert(0, CR_DIR)
from config_review_rag import review_config                # noqa: E402

SLA_DIR = os.path.join(BASE, "03-sla-analyzer")
OJK_DIR = os.path.join(BASE, "04-ojk-rag")


def _load_tool_module(name, folder, own_prompts=False):
    """Sama persis dengan v2: import Tool 3/4 secara aman, return (modul, pesan_error)."""
    if name in sys.modules:
        return sys.modules[name], None
    if not os.environ.get("GEMINI_API_KEY"):
        return None, "GEMINI_API_KEY is not set. Stop the app (Ctrl+C), set the key, start again."
    saved_prompts = sys.modules.pop("prompts", None) if own_prompts else None
    sys.path.insert(0, folder)
    try:
        return importlib.import_module(name), None
    except SystemExit as e:
        return None, str(e)
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    finally:
        if folder in sys.path:
            sys.path.remove(folder)
        if own_prompts:
            sys.modules.pop("prompts", None)
            if saved_prompts is not None:
                sys.modules["prompts"] = saved_prompts


def show_ai_error(e):
    """Pesan error AI yang bisa dibaca manusia. 429 = kuota, 503 = server sibuk, sisanya apa adanya."""
    msg = str(e)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
        st.warning("**Daily AI limit reached.** The free Gemini quota resets in a few hours. "
                   "The non-AI results above still work.")
    elif "503" in msg or "UNAVAILABLE" in msg:
        st.warning("**The AI service is busy right now.** Wait a minute and press the button again.")
    elif isinstance(e, RuntimeError):
        st.error(f"Configuration error: {msg}")
    else:
        st.error(f"{type(e).__name__}: {msg}")


st.set_page_config(page_title="Dinoerla NetOps", page_icon="🛰️", layout="wide",
                   initial_sidebar_state="collapsed")

# ============================== STYLE ==============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@500&display=swap');
/* Font cuma di .stApp (bukan [class*="st-"]) -> ikon expander (Material Symbols) tetap utuh, nggak jadi tulisan "keyboard_arrow_down" */
.stApp { font-family: 'IBM Plex Sans', system-ui, sans-serif; }
[data-testid="stIconMaterial"], .material-symbols-rounded { font-family: 'Material Symbols Rounded' !important; }
h1, h2, h3 { font-family: 'Sora', system-ui, sans-serif !important; letter-spacing: -0.01em; }
/* Heading di hasil AI jangan raksasa */
[data-testid="stMarkdownContainer"] h1 { font-size: 1.6rem !important; }
[data-testid="stMarkdownContainer"] h2 { font-size: 1.35rem !important; }
[data-testid="stMarkdownContainer"] h3 { font-size: 1.2rem !important; }
/* Padding atas cukup lebar biar nggak ketutup header Streamlit (tombol Deploy) */
.block-container { padding-top: 4.5rem !important; max-width: 1200px; }
.dn-top { display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:8px; }
.dn-logo { display:flex; align-items:center; gap:10px; }
.dn-logo-mark { width:36px; height:36px; border-radius:10px; background:#12324A; border:1px solid #2DD4BF;
                display:flex; align-items:center; justify-content:center; }
.dn-mono { font-family:'IBM Plex Mono', monospace; font-size:12px; color:#6B85A6; }
.dn-chip { font-family:'IBM Plex Mono', monospace; font-size:12px; padding:5px 10px; border-radius:999px; white-space:nowrap; }
.dn-chip.ok  { color:#6EE7B7; background:#0F2E2A; border:1px solid #1E5A4F; }
.dn-chip.bad { color:#FB7185; background:#2E1520; border:1px solid #5A2433; }
.dn-eyebrow { font-family:'IBM Plex Mono', monospace !important; font-size:12px !important; letter-spacing:.14em; text-transform:uppercase; color:#2DD4BF; margin:18px 0 8px; }
.dn-title { font-family:'Sora', sans-serif !important; font-weight:800; font-size:clamp(30px, 4.5vw, 42px) !important; line-height:1.05; letter-spacing:-0.02em; margin:0 0 12px; color:#E6EDF6; }
.dn-sub { font-size:16px !important; line-height:1.55; color:#9FB3CC; margin:0 0 24px; }
.dn-card { background:#12233B; border:1px solid #22426A; border-radius:18px; padding:20px 18px;
           display:flex; flex-direction:column; gap:12px; min-height:255px; box-sizing:border-box; }
.dn-icon { width:56px; height:56px; border-radius:14px; display:flex; align-items:center; justify-content:center; }
.dn-card-title { font-family:'Sora', sans-serif; font-weight:700; font-size:18px; color:#E6EDF6; }
.dn-card-desc { font-size:14px; line-height:1.5; color:#9FB3CC; }
.dn-card-meta { margin-top:auto; font-family:'IBM Plex Mono', monospace; font-size:11.5px; color:#6B85A6; }
.dn-note { background:#0F1E33; border:1px dashed #22426A; border-radius:12px; padding:12px 14px;
           font-size:13px; color:#9FB3CC; margin-top:16px; }
.dn-footer { margin-top:40px; padding-top:16px; border-top:1px solid #1B3252; display:flex; flex-wrap:wrap;
             justify-content:space-between; gap:8px; font-family:'IBM Plex Mono', monospace; font-size:12px; color:#6B85A6; }
.dn-footer b { color:#9FB3CC; font-weight:500; }
.dn-tool-head { display:flex; align-items:center; gap:14px; margin:6px 0 4px; }
.dn-tool-title { font-family:'Sora', sans-serif !important; font-weight:800; font-size:clamp(24px, 3vw, 30px) !important; line-height:1.1; margin:0; color:#E6EDF6; }
.dn-step { font-family:'IBM Plex Mono', monospace; font-size:15px !important; font-weight:600; letter-spacing:.1em; text-transform:uppercase; color:#2DD4BF; margin:4px 0 2px; }
.dn-card { transition:border-color .15s, transform .15s; }
/* Tile klik-able: st.button transparan ditumpuk di atas kartu HTML */
div[class*="st-key-tile_"] { position:relative; gap:0 !important; }
div[class*="st-key-tile_"]:hover .dn-card { border-color:#2DD4BF; transform:translateY(-3px); }
div[class*="st-key-tile_"] div[data-testid="stElementContainer"]:has(button),
div[class*="st-key-tile_"] div.element-container:has(button) { position:absolute !important; inset:0; z-index:5; margin:0 !important; }
div[class*="st-key-tile_"] div[data-testid="stElementContainer"]:has(button) *,
div[class*="st-key-tile_"] div.element-container:has(button) * { width:100% !important; height:100% !important; }
div[class*="st-key-tile_"] button { opacity:0 !important; cursor:pointer; }
/* ===== KHUSUS HP (layar <= 640px): kartu ringkas, ikon di kiri, teks lebih besar, ada jarak antar kartu ===== */
@media (max-width: 640px) {
  .dn-card { min-height:auto !important; padding:16px !important; display:grid !important;
             grid-template-columns:52px 1fr; column-gap:14px; row-gap:4px; }
  .dn-card .dn-icon { width:52px !important; height:52px !important; grid-row:1 / span 3; }
  .dn-card-title { font-size:20px !important; }
  .dn-card-desc { font-size:15.5px !important; line-height:1.45; }
  .dn-card-meta { margin-top:2px !important; font-size:12px !important; }
  div[class*="st-key-tile_"] { margin-bottom:14px; }
}
div[data-testid="stMetricValue"] { font-family:'Sora', sans-serif; }
</style>
""", unsafe_allow_html=True)

# ============================== DATA: 4 TOOLS ==============================
ICON = {
    "rca": ('#0E3A3A', '#2DD4BF', '<path d="M3 12h3l2-5 3 10 2-5h2"/><circle cx="17.5" cy="15.5" r="3.5"/><path d="M20 18l2 2"/>'),
    "config": ('#2E2A16', '#F4B860', '<path d="M12 3l7 3v5c0 4.5-3 8.3-7 10-4-1.7-7-5.5-7-10V6z"/><path d="M8.5 12l2.5 2.5 4.5-5"/>'),
    "sla": ('#16304F', '#7FB3FF', '<path d="M4 17a8 8 0 1 1 16 0"/><path d="M12 17l4-5"/><circle cx="12" cy="17" r="1.3"/><path d="M6.5 11.5l1 .8M12 8v1.2M17.5 11.5l-1 .8"/>'),
    "ojk": ('#2A1F3A', '#C4A5FF', '<path d="M4 5.5A1.5 1.5 0 0 1 5.5 4H12v15H5.5A1.5 1.5 0 0 0 4 20.5z"/><path d="M12 4h6.5A1.5 1.5 0 0 1 20 5.5V11"/><circle cx="17" cy="16" r="2.8"/><path d="M19 18l2 2"/>'),
}
TOOLS = [
    ("rca", "Network RCA", "Syslog in, root cause out. A free regex filter runs first, AI only sees the anomalies.", "BGP · OSPF · CRC"),
    ("config", "Config Review", "Router config checked against best practice and SEOJK 29/2022, ranked by severity.", "RAG · severity"),
    ("sla", "SLA Analyzer", "Availability, MTTR and error budget in code. AI writes the summary.", "Uptime · MTTR"),
    ("ojk", "OJK Regulation Q&A", "Ask about POJK 11/2022. Answers quote the source, or say \"not found\".", "RAG · guardrail"),
]
TOOL_NAME = {k: name for k, name, _, _ in TOOLS}


def icon_html(key, size=56, svg=30):
    bg, stroke, paths = ICON[key]
    return (f'<div class="dn-icon" style="width:{size}px;height:{size}px;background:{bg}">'
            f'<svg width="{svg}" height="{svg}" viewBox="0 0 24 24" fill="none" stroke="{stroke}" stroke-width="1.7" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{paths}</svg></div>')


def go(tool_key):
    st.session_state["tool"] = tool_key


def top_bar():
    ok = bool(os.environ.get("GEMINI_API_KEY"))
    chip = '<span class="dn-chip ok">● AI online</span>' if ok else '<span class="dn-chip bad">● AI key missing</span>'
    st.markdown(f"""
<div class="dn-top">
  <div class="dn-logo">
    <div class="dn-logo-mark"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="5" cy="12" r="2.2"/><circle cx="19" cy="5" r="2.2"/><circle cx="19" cy="19" r="2.2"/><path d="M7 11l10-5M7 13l10 5"/></svg></div>
    <span class="dn-mono">v3 · demo</span>
  </div>
  {chip}
</div>""", unsafe_allow_html=True)


def footer():
    st.markdown("""
<div class="dn-footer">
  <span>Built by Dili Noerlan · CCIE SP #44832</span>
  <span>Built with <b>Claude &amp; Gemini</b> · ChromaDB · Streamlit · GitHub Actions</span>
</div>""", unsafe_allow_html=True)


def tool_header(key, subtitle):
    st.button("← All tools", on_click=go, args=(None,), key=f"back_{key}")
    st.markdown(f"""
<div class="dn-tool-head">
  {icon_html(key, size=48, svg=26)}
  <div class="dn-tool-title">{TOOL_NAME[key]}</div>
</div>""", unsafe_allow_html=True)
    st.caption(subtitle)


if "tool" not in st.session_state:
    st.session_state["tool"] = None
tool = st.session_state["tool"]

top_bar()

# ============================== HOME ==============================
if tool is None:
    st.markdown("""
<div class="dn-eyebrow">AI-augmented network operations · banking &amp; telco</div>
<div class="dn-title">Dinoerla NetOps</div>
<div class="dn-sub">AI for network operations. Code does the math, AI writes the analysis, and every regulation claim cites its source.</div>
""", unsafe_allow_html=True)

    cols = st.columns(4)
    for col, (key, name, desc, meta) in zip(cols, TOOLS):
        with col, st.container(key=f"tile_{key}"):
            st.markdown(f"""
<div class="dn-card">
  {icon_html(key)}
  <div class="dn-card-title">{name}</div>
  <div class="dn-card-desc">{desc}</div>
  <div class="dn-card-meta">{meta}</div>
</div>""", unsafe_allow_html=True)
            st.button(f"Open {name}", key=f"open_{key}", on_click=go, args=(key,),
                      use_container_width=True)

    st.markdown('<div class="dn-note">Demo uses synthetic logs and configs. No customer data is used.</div>',
                unsafe_allow_html=True)

# ============================== TOOL 1: NETWORK RCA ==============================
elif tool == "rca":
    tool_header("rca", "Stage 1: regex filter on raw syslog (free, no AI) → Stage 2: AI root-cause analysis (Gemini)")
    col_control, col_result = st.columns([1, 2], gap="large")

    with col_control:
        st.markdown('<div class="dn-step">1 · Choose input</div>', unsafe_allow_html=True)
        check = st.selectbox("Analysis type", ["bgp_rca", "ospf_rca"],
                             format_func=lambda c: {"bgp_rca": "BGP root cause", "ospf_rca": "OSPF adjacency"}[c])
        source = st.radio("Log source", ["Sample", "Upload", "Paste"], horizontal=True)

        raw_text = ""
        if source == "Sample":
            sample_file = os.path.join(RCA_DIR, "data", "bgp_sample.log" if check == "bgp_rca" else "syslog_raw.log")
            if os.path.exists(sample_file):
                with open(sample_file) as f:
                    raw_text = f.read()
                st.caption(f"Using `{os.path.basename(sample_file)}`")
            else:
                st.warning(f"Sample file not found: {sample_file}")
        elif source == "Upload":
            up = st.file_uploader("Upload a log (.log / .txt)", type=["log", "txt"])
            if up is not None:
                raw_text = up.read().decode("utf-8", errors="ignore")
        else:
            raw_text = st.text_area("Paste syslog lines here", height=200)

        run_btn = st.button("Run analysis", type="primary", use_container_width=True)

        with st.expander("Technical details"):
            st.caption("Stage 1 keeps only log lines that match these patterns (regex, no AI cost):")
            explain = {
                r"%BGP-\d-": "All BGP events (neighbor up/down, notifications)",
                r"%OSPF-\d-": "All OSPF events (adjacency changes)",
                r"%DUAL-\d-": "All EIGRP events (neighbor changes)",
                r"%LINK-3-UPDOWN": "Physical interface went down or up",
                r"CRC": "CRC errors (bad cable, fiber or SFP)",
                r"INPUT_ERRORS": "Input error counters",
                r"hold time expired": "BGP/OSPF neighbor timed out",
                r"err-?disable": "Switch port shut down by protection (err-disable)",
            }
            st.markdown("\n".join(f"- `{pat}` → {explain.get(pat, 'custom pattern')}" for pat in ANOMALY_PATTERNS))

    with col_result:
        st.markdown('<div class="dn-step">2 · Results</div>', unsafe_allow_html=True)
        if raw_text:
            lines = raw_text.splitlines(keepends=True)
            anomalies = parse_anomalies(lines)

            m1, m2, m3 = st.columns(3)
            m1.metric("Log lines", len(lines))
            m2.metric("Anomalies", len(anomalies))
            m3.metric("Noise dropped", len(lines) - len(anomalies))

            with st.expander(f"See the {len(anomalies)} anomaly lines (Stage 1 output)"):
                st.code("\n".join(anomalies) if anomalies else "(empty)", language="text")

            if run_btn:
                if not anomalies:
                    st.warning("No anomalies found, so nothing was sent to the AI.")
                else:
                    with st.spinner("AI is analysing (Gemini)..."):
                        try:
                            result = run_check(check, "\n".join(anomalies))
                            st.markdown("### Root cause report")
                            st.markdown(result)
                        except Exception as e:
                            show_ai_error(e)
        else:
            st.info("Choose a log source to start.")

# ============================== TOOL 2: CONFIG REVIEW (RAG) ==============================
elif tool == "config":
    tool_header("config", "Retrieve the relevant SEOJK clauses from ChromaDB → AI reviews the config against best practice and the actual regulation")
    col_control, col_result = st.columns([1, 2], gap="large")

    with col_control:
        st.markdown('<div class="dn-step">1 · Choose input</div>', unsafe_allow_html=True)
        source = st.radio("Config source", ["Sample", "Upload", "Paste"], horizontal=True)

        config_text = ""
        if source == "Sample":
            sample_file = os.path.join(CR_DIR, "data", "router_sample.cfg")
            if os.path.exists(sample_file):
                with open(sample_file) as f:
                    config_text = f.read()
                st.caption("Using `router_sample.cfg`")
            else:
                st.warning(f"Sample file not found: {sample_file}")
        elif source == "Upload":
            up = st.file_uploader("Upload a config (.cfg / .txt)", type=["cfg", "txt", "conf"])
            if up is not None:
                config_text = up.read().decode("utf-8", errors="ignore")
        else:
            config_text = st.text_area("Paste `show running-config` here", height=200)

        run_btn = st.button("Run config review", type="primary", use_container_width=True)

        with st.expander("Technical details"):
            st.caption("Regulation source: shared ChromaDB `04-ojk-rag/chroma_db` (POJK 11/2022, SEOJK 29/2022 and summaries).")

    with col_result:
        st.markdown('<div class="dn-step">2 · Results</div>', unsafe_allow_html=True)
        if config_text:
            with st.expander("See the config under review"):
                st.code(config_text, language="text")

            if run_btn:
                with st.spinner("Retrieving OJK clauses + AI review (Gemini)..."):
                    try:
                        out = review_config(config_text)

                        st.markdown("### Grounding: clauses retrieved")
                        for m in out["sources"]:
                            st.caption(f"• {m.get('source', '?')} (chunk {m.get('chunk', '?')})")

                        st.markdown("### Review")
                        st.markdown(out["result"])
                        st.caption("Findings without a regulatory basis are marked **(verify)**.")
                    except FileNotFoundError as e:
                        st.error(f"ChromaDB or file not found: {e}")
                    except Exception as e:
                        show_ai_error(e)
        else:
            st.info("Choose a config source to start.")

# ============================== TOOL 3: SLA ANALYZER ==============================
elif tool == "sla":
    tool_header("sla", "Stage 1: availability, MTTR and error budget computed in code (exact numbers) → Stage 2: AI writes the management report (Gemini)")

    sla, err = _load_tool_module("sla_analyzer", SLA_DIR, own_prompts=True)
    if sla is None:
        st.error(f"SLA Analyzer is not available: {err}")
    else:
        col_control, col_result = st.columns([1, 2], gap="large")

        with col_control:
            st.markdown('<div class="dn-step">1 · Choose input</div>', unsafe_allow_html=True)
            source = st.radio("Incident data", ["Sample", "Upload CSV"], horizontal=True)
            target = st.number_input("SLA target (%)", min_value=90.0, max_value=99.999,
                                     value=99.99, step=0.01, format="%.3f")
            days = st.number_input("Period (days)", min_value=1, max_value=366, value=30, step=1)

            csv_path = None
            if source == "Sample":
                csv_path = os.path.join(SLA_DIR, "data", "incidents.csv")
                st.caption("Using `incidents.csv`")
            else:
                up = st.file_uploader("Upload CSV", type=["csv"])
                st.caption("Required columns: `start,end,severity,description`, time as `YYYY-MM-DD HH:MM`")
                if up is not None:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                    tmp.write(up.read()); tmp.close()
                    csv_path = tmp.name

            run_btn = st.button("Write SLA report", type="primary", use_container_width=True)

            with st.expander("Technical details"):
                st.caption("Availability, MTTR and error budget are exact calculations in code. "
                           "The AI only writes the narrative for management.")

        with col_result:
            st.markdown('<div class="dn-step">2 · Results</div>', unsafe_allow_html=True)
            if csv_path and os.path.exists(csv_path):
                try:
                    sla.SLA_TARGET = float(target)
                    sla.PERIOD_DAYS = int(days)
                    incidents = sla.load_incidents(csv_path)
                    m = sla.compute_sla(incidents)

                    m1, m2 = st.columns(2)
                    m1.metric("Availability", f"{m['avail']:.4f}%")
                    m2.metric("Total downtime", f"{m['downtime']:.0f} min")
                    m3, m4 = st.columns(2)
                    m3.metric("MTTR", f"{m['mttr']:.1f} min")
                    m4.metric("Error budget used", f"{m['used']:.0f}%")

                    if m["breach"]:
                        st.error(f"BREACH: availability is below the {target}% target. "
                                 f"Downtime budget was {m['budget']:.2f} min, {m['downtime']:.0f} min used.")
                    else:
                        st.success(f"OK: meets the {target}% target. {m['budget'] - m['downtime']:.2f} min of budget left.")

                    with st.expander(f"See the {m['n']} incidents (input)"):
                        st.dataframe(
                            [{"start": i["start"], "end": i["end"], "minutes": round(i["minutes"]),
                              "severity": i["severity"], "description": i["description"]} for i in incidents],
                            use_container_width=True,
                        )

                    if run_btn:
                        metrics_text = sla.format_metrics(m, incidents)
                        with st.spinner("AI is writing the report (Gemini)..."):
                            try:
                                report = sla.ask_ai(sla.PROMPTS["sla_report"].replace("{data}", metrics_text))
                                st.markdown("### SLA report for management")
                                st.markdown(report)
                                st.caption("Every number in the report comes from the calculation above. "
                                           "Regulation references are marked **(verify)**.")
                            except Exception as e:
                                show_ai_error(e)
                except (KeyError, ValueError) as e:
                    st.error(f"CSV format does not match ({type(e).__name__}: {e}). "
                             "Needs columns start,end,severity,description and time as YYYY-MM-DD HH:MM.")
                except Exception as e:
                    st.error(f"{type(e).__name__}: {e}")
            else:
                st.info("Choose incident data to start.")

# ============================== TOOL 4: OJK RAG ==============================
else:
    tool_header("ojk", "Question → embed → find the closest clauses in ChromaDB → AI answers ONLY from those quotes and names the source")

    ojk, err = _load_tool_module("ask_ojk", OJK_DIR)
    if ojk is None:
        st.error(f"OJK Regulation Q&A is not available: {err}")
    else:
        import chromadb                                    # noqa: E402
        OJK_DB = os.path.join(OJK_DIR, "chroma_db")

        col_control, col_result = st.columns([1, 2], gap="large")

        with col_control:
            st.markdown('<div class="dn-step">1 · Ask</div>', unsafe_allow_html=True)
            contoh = st.selectbox("Example questions", [
                "(type your own)",
                "Apa kewajiban bank terkait Disaster Recovery Center (DRC)?",
                "Apa kewajiban bank kalau terjadi insiden siber?",
                "Apa yang diatur soal penempatan sistem elektronik dan data center?",
                "Apa kewajiban bank dalam manajemen risiko teknologi informasi?",
            ])
            question = st.text_area("Question", value="" if contoh.startswith("(") else contoh, height=110)
            run_btn = st.button("Ask the regulation", type="primary", use_container_width=True)
            st.caption(f"Retrieves the {ojk.TOP_K} most relevant quotes per question. Documents are in Indonesian.")

        with col_result:
            st.markdown('<div class="dn-step">2 · Answer</div>', unsafe_allow_html=True)
            if not os.path.isdir(OJK_DB):
                st.warning("The regulation database is missing. Run: `cd 04-ojk-rag && python ingest.py`")
            elif run_btn and question.strip():
                with st.spinner("Retrieving clauses + AI answer (Gemini)..."):
                    try:
                        col = chromadb.PersistentClient(path=OJK_DB).get_or_create_collection(ojk.COLLECTION)
                        if col.count() == 0:
                            st.warning("The regulation database is empty. Run: `cd 04-ojk-rag && python ingest.py`")
                        else:
                            res = col.query(query_embeddings=[ojk.embed(question.strip())], n_results=ojk.TOP_K)
                            docs, metas = res["documents"][0], res["metadatas"][0]
                            context = "\n\n---\n\n".join(f"[Sumber: {mt['source']}]\n{d}" for d, mt in zip(docs, metas))
                            prompt = ojk.PROMPT.replace("{context}", context).replace("{question}", question.strip())
                            answer = ojk.ask_ai(prompt)

                            st.markdown("### Grounding: quotes retrieved")
                            for mt in metas:
                                st.caption(f"• {mt.get('source', '?')} (chunk {mt.get('chunk', '?')})")
                            with st.expander("See the quoted text (grounding evidence)"):
                                for d, mt in zip(docs, metas):
                                    st.markdown(f"**{mt.get('source', '?')} · chunk {mt.get('chunk', '?')}**")
                                    st.code(d, language="text")

                            st.markdown("### Answer")
                            st.markdown(answer)
                            st.caption("Check article and clause numbers against the original PDF before using them with a client or auditor.")
                    except Exception as e:
                        show_ai_error(e)
            elif run_btn:
                st.warning("The question is empty.")
            else:
                st.info("Pick an example or type a question, then press the button.")

footer()
