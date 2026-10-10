"""
dashboard_app.py - COMBINED dashboard, root repo.
Tool 1: Network RCA (01-network-rca)
Tool 2: Config Review - RAG grounded ke OJK/SEOJK (02-config-review)
Tool 3: SLA Analyzer - angka dihitung code, narasi ditulis AI (03-sla-analyzer)   [6 Okt 2026]
Tool 4: OJK RAG - tanya regulasi, jawaban + sumber dokumen (04-ojk-rag)           [6 Okt 2026]

Kenapa digabung: biar Dili cuma buka 1 app, pilih tool via selector.
PENTING soal sys.path: 01-network-rca DULU baru 02-config-review.
engine.py (01) butuh "from prompts import PROMPTS" resolve ke prompts.py
folder 01. config_review_rag.py (02) TIDAK import "prompts" sama sekali,
jadi nggak akan collide walau 02-config-review juga punya prompts.py sendiri
(itu punya baseline non-RAG config_review.py, nggak dipakai di sini).

Tool 3 & 4: script aslinya (sla_analyzer.py, ask_ojk.py) TIDAK diubah. Dua-duanya
langsung berhenti (SystemExit) kalau GEMINI_API_KEY kosong, dan 03 punya prompts.py
sendiri. Jadi di sini mereka di-load BELAKANGAN lewat _load_tool_module() - baru
di-import pas tab-nya dibuka, dan cuma kalau key udah ada.
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
    """
    Import modul Tool 3/4 secara aman. Return (modul, pesan_error).
    - Udah pernah di-load -> pakai yang ada (Streamlit rerun script tiap klik).
    - Key kosong -> JANGAN import (script aslinya bakal SystemExit), balikin pesan.
    - own_prompts=True (03): modul itu butuh prompts.py miliknya sendiri. "prompts" punya
      RCA disimpen dulu, dikeluarin dari cache, lalu DIBALIKIN setelah import selesai -
      biar Tool 1 nggak ketuker prompt-nya.
    """
    if name in sys.modules:
        return sys.modules[name], None
    if not os.environ.get("GEMINI_API_KEY"):
        return None, "GEMINI_API_KEY belum di-set. Stop dashboard (Ctrl+C), export key, jalanin lagi."
    saved_prompts = sys.modules.pop("prompts", None) if own_prompts else None
    sys.path.insert(0, folder)
    try:
        return importlib.import_module(name), None
    except SystemExit as e:                      # script asli nolak jalan tanpa key
        return None, str(e)
    except Exception as e:                       # misal library belum ke-install
        return None, f"{type(e).__name__}: {e}"
    finally:
        if folder in sys.path:
            sys.path.remove(folder)
        if own_prompts:
            sys.modules.pop("prompts", None)
            if saved_prompts is not None:
                sys.modules["prompts"] = saved_prompts

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
        ["🔎 Tool 1 — Network RCA", "🔐 Tool 2 — Config Review (RAG)",
         "📈 Tool 3 — SLA Analyzer", "📚 Tool 4 — OJK RAG (tanya regulasi)"],
        index=0,
    )
    st.divider()

    if tool.startswith("🔎"):
        st.markdown("**Stage 1 — Anomaly filter (gratis, no token)**")
        for p in ANOMALY_PATTERNS:
            st.code(p, language="text")
    elif tool.startswith("📈"):
        st.markdown("**Angka dihitung CODE, bukan AI**")
        st.caption("Availability, MTTR, error budget = hitungan pasti. AI cuma nulis narasi buat manajemen.")
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
elif tool.startswith("🔐"):
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

# ============================== TOOL 3: SLA ANALYZER ==============================
elif tool.startswith("📈"):
    st.title("📈 Tool 3 — SLA Analyzer")
    st.caption("Stage 1: hitung availability / MTTR / error budget dari daftar incident (code, angka pasti) → Stage 2: AI tulis laporan manajemen (Gemini)")

    sla, err = _load_tool_module("sla_analyzer", SLA_DIR, own_prompts=True)
    if sla is None:
        st.error(f"Tool 3 belum bisa dipakai: {err}")
    else:
        col_input, col_control = st.columns([2, 1])

        with col_control:
            st.markdown("### Kontrol")
            source = st.radio("Sumber data incident", ["Sample bawaan", "Upload CSV"])
            target = st.number_input("Target SLA (%)", min_value=90.0, max_value=99.999,
                                     value=99.99, step=0.01, format="%.3f")
            days = st.number_input("Periode (hari)", min_value=1, max_value=366, value=30, step=1)

            csv_path = None
            if source == "Sample bawaan":
                csv_path = os.path.join(SLA_DIR, "data", "incidents.csv")
                st.caption("Pakai: `incidents.csv`")
            else:
                up = st.file_uploader("Upload CSV", type=["csv"])
                st.caption("Kolom wajib: `start,end,severity,description` — format waktu `YYYY-MM-DD HH:MM`")
                if up is not None:
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                    tmp.write(up.read()); tmp.close()
                    csv_path = tmp.name

            run_btn = st.button("🚀 Buat laporan SLA (AI)", type="primary", use_container_width=True)

        with col_input:
            st.markdown("### Hasil")
            if csv_path and os.path.exists(csv_path):
                try:
                    # target & periode dari UI dipasang ke modul (compute_sla baca dari situ)
                    sla.SLA_TARGET = float(target)
                    sla.PERIOD_DAYS = int(days)
                    incidents = sla.load_incidents(csv_path)
                    m = sla.compute_sla(incidents)

                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Availability", f"{m['avail']:.4f}%")
                    m2.metric("Total downtime", f"{m['downtime']:.0f} mnt")
                    m3.metric("MTTR", f"{m['mttr']:.1f} mnt")
                    m4.metric("Error budget kepakai", f"{m['used']:.0f}%")

                    if m["breach"]:
                        st.error(f"BREACH — availability di bawah target {target}%. "
                                 f"Budget downtime cuma {m['budget']:.2f} menit, kepakai {m['downtime']:.0f} menit.")
                    else:
                        st.success(f"OK — memenuhi target {target}%. Sisa budget {m['budget'] - m['downtime']:.2f} menit.")

                    with st.expander(f"Lihat {m['n']} incident (input)"):
                        st.dataframe(
                            [{"start": i["start"], "end": i["end"], "menit": round(i["minutes"]),
                              "severity": i["severity"], "description": i["description"]} for i in incidents],
                            use_container_width=True,
                        )

                    if run_btn:
                        metrics_text = sla.format_metrics(m, incidents)
                        with st.spinner("AI lagi nulis laporan (Gemini)..."):
                            try:
                                report = sla.ask_ai(sla.PROMPTS["sla_report"].replace("{data}", metrics_text))
                                st.markdown("### 🧠 Laporan SLA untuk manajemen")
                                st.markdown(report)
                                st.caption("Semua angka di laporan berasal dari hitungan code di atas. "
                                           "Rujukan regulasi ditandai **(verify)** — cek ke dokumen asli.")
                            except Exception as e:
                                st.error(f"{type(e).__name__}: {e}")
                except (KeyError, ValueError) as e:
                    st.error(f"Format CSV nggak cocok ({type(e).__name__}: {e}). "
                             "Butuh kolom start,end,severity,description dan waktu YYYY-MM-DD HH:MM.")
                except Exception as e:
                    st.error(f"{type(e).__name__}: {e}")
            else:
                st.info("Pilih sumber data dulu di panel kanan.")

# ============================== TOOL 4: OJK RAG ==============================
else:
    st.title("📚 Tool 4 — OJK RAG (tanya regulasi)")
    st.caption("Pertanyaan → embed → cari pasal paling relevan di ChromaDB → AI jawab HANYA dari kutipan itu + sebut sumber")

    ojk, err = _load_tool_module("ask_ojk", OJK_DIR)
    if ojk is None:
        st.error(f"Tool 4 belum bisa dipakai: {err}")
    else:
        import chromadb                                    # noqa: E402
        OJK_DB = os.path.join(OJK_DIR, "chroma_db")       # path absolut: aman dijalanin dari folder mana pun

        col_input, col_control = st.columns([2, 1])

        with col_control:
            st.markdown("### Kontrol")
            contoh = st.selectbox("Contoh pertanyaan", [
                "(ketik sendiri)",
                "Apa kewajiban bank terkait Disaster Recovery Center (DRC)?",
                "Apa kewajiban bank kalau terjadi insiden siber?",
                "Apa yang diatur soal penempatan sistem elektronik dan data center?",
                "Apa kewajiban bank dalam manajemen risiko teknologi informasi?",
            ])
            question = st.text_area("Pertanyaan", value="" if contoh.startswith("(") else contoh, height=110)
            run_btn = st.button("🚀 Tanya regulasi OJK", type="primary", use_container_width=True)
            st.caption(f"Ambil {ojk.TOP_K} kutipan paling relevan per pertanyaan.")

        with col_input:
            st.markdown("### Hasil")
            if not os.path.isdir(OJK_DB):
                st.warning("ChromaDB belum ada. Jalanin dulu: `cd 04-ojk-rag && python ingest.py`")
            elif run_btn and question.strip():
                with st.spinner("Retrieve pasal OJK + AI jawab (Gemini)..."):
                    try:
                        col = chromadb.PersistentClient(path=OJK_DB).get_or_create_collection(ojk.COLLECTION)
                        if col.count() == 0:
                            st.warning("Database regulasi kosong. Jalanin dulu: `cd 04-ojk-rag && python ingest.py`")
                        else:
                            res = col.query(query_embeddings=[ojk.embed(question.strip())], n_results=ojk.TOP_K)
                            docs, metas = res["documents"][0], res["metadatas"][0]
                            context = "\n\n---\n\n".join(f"[Sumber: {mt['source']}]\n{d}" for d, mt in zip(docs, metas))
                            prompt = ojk.PROMPT.replace("{context}", context).replace("{question}", question.strip())
                            answer = ojk.ask_ai(prompt)

                            st.markdown("### 📚 Grounding — kutipan yang di-retrieve")
                            for mt in metas:
                                st.caption(f"• {mt.get('source', '?')} (chunk {mt.get('chunk', '?')})")
                            with st.expander("Lihat isi kutipan (bukti grounding)"):
                                for d, mt in zip(docs, metas):
                                    st.markdown(f"**{mt.get('source', '?')} — chunk {mt.get('chunk', '?')}**")
                                    st.code(d, language="text")

                            st.markdown("### 🧠 Jawaban (grounded ke dokumen asli)")
                            st.markdown(answer)
                            st.caption("Nomor pasal/ayat di jawaban WAJIB dicek ke PDF asli sebelum dipakai ke klien atau audit.")
                    except Exception as e:
                        st.error(f"{type(e).__name__}: {e}")
            elif run_btn:
                st.warning("Pertanyaannya masih kosong.")
            else:
                st.info("Pilih contoh atau ketik pertanyaan di panel kanan, lalu klik tombolnya.")
