"""
dashboard_app.py - COMBINED dashboard, root repo.
Tool 1: Network RCA (01-network-rca)
Tool 2: Config Review - RAG grounded ke OJK/SEOJK (02-config-review)

Kenapa digabung: biar Dili cuma buka 1 app, pilih tool via selector.
PENTING soal sys.path: 01-network-rca DULU baru 02-config-review.
engine.py (01) butuh "from prompts import PROMPTS" resolve ke prompts.py
folder 01. config_review_rag.py (02) TIDAK import "prompts" sama sekali,
jadi nggak akan collide walau 02-config-review juga punya prompts.py sendiri
(itu punya baseline non-RAG config_review.py, nggak dipakai di sini).
"""
import os
import sys
import streamlit as st

BASE = os.path.dirname(os.path.abspath(__file__))
RCA_DIR = os.path.join(BASE, "01-network-rca")
CR_DIR  = os.path.join(BASE, "02-config-review")

# --- urutan WAJIB: RCA dulu (biar "prompts" yg ke-cache di sys.modules punya milik RCA) ---
sys.path.insert(0, RCA_DIR)
from parser import ANOMALY_PATTERNS, parse_anomalies      # noqa: E402
from engine import run_check                               # noqa: E402

sys.path.insert(0, CR_DIR)
from config_review_rag import review_config                # noqa: E402

st.set_page_config(page_title="AI Network Usecase Dashboard", page_icon="🛰️", layout="wide")

# ============================== SIDEBAR ==============================
with st.sidebar:
    st.markdown("## 🛰️ AI Network Usecase")
    st.caption("Dili Noerlan — AI Mastery Program")

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        st.success("GEMINI_API_KEY: terpasang ✅")
    else:
        st.error("GEMINI_API_KEY belum di-set")
        st.code("export GEMINI_API_KEY='...'", language="bash")

    st.divider()
    tool = st.radio(
        "Pilih tool",
        ["🔎 Tool 1 — Network RCA", "🔐 Tool 2 — Config Review (RAG)"],
        index=0,
    )
    st.divider()

    if tool.startswith("🔎"):
        st.markdown("**Stage 1 — Anomaly filter (gratis, no token)**")
        for p in ANOMALY_PATTERNS:
            st.code(p, language="text")
    else:
        st.markdown("**RAG source**")
        st.caption("ChromaDB shared: `04-ojk-rag/chroma_db` (POJK 11/2022, SEOJK 29/2022, dll)")

# ============================== TOOL 1: NETWORK RCA ==============================
if tool.startswith("🔎"):
    st.title("🔎 Tool 1 — Network RCA")
    st.caption("Stage 1: filter anomali dari syslog mentah (regex, gratis) → Stage 2: AI root-cause analysis (Gemini)")

    col_input, col_control = st.columns([2, 1])

    with col_control:
        st.markdown("### Kontrol")
        # exclude "config_review" - itu punya Tool 2, format inputnya beda (config, bukan log)
        check = st.selectbox("Jenis analisa", ["bgp_rca", "ospf_rca"])
        source = st.radio("Sumber log", ["Sample bawaan", "Upload file", "Paste manual"])

        raw_text = ""
        if source == "Sample bawaan":
            sample_file = os.path.join(RCA_DIR, "data", "bgp_sample.log" if check == "bgp_rca" else "syslog_raw.log")
            if os.path.exists(sample_file):
                with open(sample_file) as f:
                    raw_text = f.read()
                st.caption(f"Pakai: `{os.path.basename(sample_file)}`")
            else:
                st.warning(f"Sample file nggak ketemu: {sample_file}")
        elif source == "Upload file":
            up = st.file_uploader("Upload log (.log/.txt)", type=["log", "txt"])
            if up is not None:
                raw_text = up.read().decode("utf-8", errors="ignore")
        else:
            raw_text = st.text_area("Paste log di sini", height=200)

        run_btn = st.button("🚀 Jalankan RCA", type="primary", use_container_width=True)

    with col_input:
        st.markdown("### Hasil")
        if raw_text:
            lines = raw_text.splitlines(keepends=True)
            anomalies = parse_anomalies(lines)

            m1, m2, m3 = st.columns(3)
            m1.metric("Total baris", len(lines))
            m2.metric("Anomali", len(anomalies))
            m3.metric("Noise dibuang", len(lines) - len(anomalies))

            with st.expander(f"Lihat {len(anomalies)} baris anomali (Stage 1 output)"):
                st.code("\n".join(anomalies) if anomalies else "(kosong)", language="text")

            if run_btn:
                if not anomalies:
                    st.warning("Nggak ada anomali ke-filter — nggak ada yang dikirim ke AI.")
                else:
                    with st.spinner("AI lagi analisa (Gemini)..."):
                        try:
                            result = run_check(check, "\n".join(anomalies))
                            st.markdown("### 🧠 AI Root Cause Analysis")
                            st.markdown(result)
                        except RuntimeError as e:
                            st.error(f"CONFIG ERROR: {e}")
                        except Exception as e:
                            st.error(f"{type(e).__name__}: {e}")
        else:
            st.info("Pilih sumber log dulu di panel kanan.")

# ============================== TOOL 2: CONFIG REVIEW (RAG) ==============================
else:
    st.title("🔐 Tool 2 — Config Review (RAG-grounded ke OJK/SEOJK)")
    st.caption("Retrieve pasal OJK relevan dari ChromaDB → AI review config terhadap best-practice DAN regulasi asli (bukan ngarang)")

    col_input, col_control = st.columns([2, 1])

    with col_control:
        st.markdown("### Kontrol")
        source = st.radio("Sumber config", ["Sample bawaan", "Upload file", "Paste manual"])

        config_text = ""
        if source == "Sample bawaan":
            sample_file = os.path.join(CR_DIR, "data", "router_sample.cfg")
            if os.path.exists(sample_file):
                with open(sample_file) as f:
                    config_text = f.read()
                st.caption("Pakai: `router_sample.cfg`")
            else:
                st.warning(f"Sample file nggak ketemu: {sample_file}")
        elif source == "Upload file":
            up = st.file_uploader("Upload config (.cfg/.txt)", type=["cfg", "txt", "conf"])
            if up is not None:
                config_text = up.read().decode("utf-8", errors="ignore")
        else:
            config_text = st.text_area("Paste `show running-config` di sini", height=200)

        run_btn = st.button("🚀 Jalankan Config Review", type="primary", use_container_width=True)

    with col_input:
        st.markdown("### Hasil")
        if config_text:
            with st.expander("Lihat config yang di-review"):
                st.code(config_text, language="text")

            if run_btn:
                with st.spinner("Retrieve pasal OJK + AI review (Gemini)..."):
                    try:
                        out = review_config(config_text)

                        st.markdown("### 📚 Grounding — pasal OJK yang di-retrieve")
                        for m in out["sources"]:
                            st.caption(f"• {m.get('source', '?')} (chunk {m.get('chunk', '?')})")

                        st.markdown("### 🧠 AI Review (grounded ke OJK)")
                        st.markdown(out["result"])
                        st.caption("Temuan tanpa dasar regulasi di atas ditandai **(verify)** — bukan best-practice fabrikasi.")
                    except RuntimeError as e:
                        st.error(f"CONFIG ERROR: {e}")
                    except FileNotFoundError as e:
                        st.error(f"ChromaDB / file nggak ketemu: {e}")
                    except Exception as e:
                        st.error(f"{type(e).__name__}: {e}")
        else:
            st.info("Pilih sumber config dulu di panel kanan.")
