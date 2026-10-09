# 01 — Network RCA (AI-assisted)

Fungsi: baca syslog -> filter anomali (parser) -> AI kasih Root Cause Analysis.

## Cara jalanin
1) Setup dulu dari folder induk (lihat README induk): activate venv + export key.
2) Masuk folder ini & jalanin:

    cd 01-network-rca
    python network_rca.py                                  # default: data/syslog_raw.log, check bgp_rca

   Bentuk eksplisit (pilih file & check):
    python network_rca.py <file_log> <check>
    python network_rca.py data/syslog_raw.log bgp_rca

## Isi folder
- network_rca.py  -> RUN INI. Funnel: parser -> AI.
- parser.py       -> Stage 1: filter baris anomali (regex). Gratis, no token.
- engine.py       -> Stage 2: panggil AI (ask_ai + retry 503).
- prompts.py      -> library prompt: bgp_rca, ospf_rca, config_review.
- data/           -> log contoh: bgp_sample.log, syslog_raw.log.

## Ganti input
    python network_rca.py data/log_baru.log
