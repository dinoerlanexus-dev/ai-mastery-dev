"""
dashboard_app.py - UI layer di atas parser.py + engine.py yang udah ada.
Nggak ada logic AI baru di sini - dashboard cuma "nge-render" funnel yang sama
kayak network_rca.py, biar ada 1 source of truth (rule taxonomy: Code HANYA di CODE).

Jalanin:
    streamlit run dashboard_app.py
"""
import os
import streamlit as st
from parser import parse_anomalies, ANOMALY_PATTERNS
from engine import run_check
from prompts import PROMPTS
from google.genai import errors

st.set_page_config(page_title="Network RCA - AI Mastery", page_icon="🛰️", layout="wide")

st.title("🛰️ Network RCA — AI-Assisted Root Cause Analysis")
st.caption("2-stage funnel: regex filter (gratis, no token) → Gemini AI (root cause analysis)")

# ---------- Sidebar: status + referensi ----------
with st.sidebar:
    st.header("Status")
    if os.environ.get("GEMINI_API_KEY"):
        st.success("GEMINI_API_KEY terdeteksi")
    else:
        st.error("GEMINI_API_KEY belum di-set")
        st.code("export GEMINI_API_KEY='...'", language="bash")
        st.caption("Set di Terminal SEBELUM jalanin `streamlit run`, lalu refresh halaman ini.")

    st.markdown("---")
    st.markdown("**Pattern anomali yang dideteksi (Stage 1):**")
    for p in ANOMALY_PATTERNS:
        st.code(p, language=None)

# ---------- Input ----------
col_input, col_control = st.columns([2, 1])

with col_input:
    source = st.radio("Sumber log", ["Sample bawaan", "Upload file", "Paste manual"], horizontal=True)
    log_text = None

    if source == "Sample bawaan":
        sample = st.selectbox("Pilih sample", ["data/bgp_sample.log", "data/syslog_raw.log"])
        if os.path.exists(sample):
            with open(sample, encoding="utf-8") as f:
                log_text = f.read()
        else:
            st.warning(f"File nggak ketemu: {sample}")

    elif source == "Upload file":
        uploaded = st.file_uploader("Upload syslog (.log / .txt)", type=["log", "txt"])
        if uploaded is not None:
            log_text = uploaded.read().decode("utf-8", errors="ignore")

    else:
        log_text = st.text_area("Paste log di sini", height=200, placeholder="%BGP-5-ADJCHANGE: ...")

    if log_text:
        with st.expander("Preview log mentah"):
            st.text(log_text[:5000] + ("\n... (dipotong)" if len(log_text) > 5000 else ""))

with col_control:
    check = st.selectbox("Jenis analisa", list(PROMPTS.keys()))
    run = st.button("Jalankan Analisa", type="primary", use_container_width=True)
    st.caption("Stage 1 (parser) selalu jalan gratis. Stage 2 (AI) cuma dipanggil kalau ada anomali.")

st.markdown("---")

# ---------- Run funnel ----------
if run:
    if not log_text or not log_text.strip():
        st.warning("Log kosong — pilih sample, upload file, atau paste log dulu.")
    else:
        lines = log_text.splitlines(keepends=True)
        anomalies = parse_anomalies(lines)

        st.subheader("Stage 1 — Parser")
        m1, m2, m3 = st.columns(3)
        m1.metric("Total baris", len(lines))
        m2.metric("Anomali terdeteksi", len(anomalies))
        m3.metric("Noise di-filter", len(lines) - len(anomalies))

        if not anomalies:
            st.info("Nggak ada anomali — AI nggak dipanggil (hemat token, sama kayak versi CLI).")
        else:
            with st.expander(f"Lihat {len(anomalies)} baris anomali yang dikirim ke AI", expanded=False):
                for a in anomalies:
                    st.code(a, language=None)

            st.subheader("Stage 2 — AI Root Cause Analysis")
            data = "\n".join(anomalies)
            try:
                with st.spinner(f"Gemini lagi analisa ({check})..."):
                    result = run_check(check, data)
                st.markdown(result)
            except errors.ServerError as e:
                st.error(f"Model lagi overload ({e.code}). Anomali udah ke-filter & siap — coba lagi bentar.")
            except errors.ClientError as e:
                st.error(f"CLIENT ERROR ({e.code}): {e.message}")
            except RuntimeError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"ERROR {type(e).__name__}: {e}")

st.markdown("---")
st.caption("AI Mastery Program · Network RCA usecase · dashboard v1 · code: 07. CODE/ai-mastery-dev/01-network-rca")
