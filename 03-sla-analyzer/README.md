# 03 — SLA & Performance Analyzer (AI-assisted)

Fungsi: baca daftar incident -> CODE hitung SLA (availability, MTTR, error budget) ->
AI tulis laporan exec. Pola hands+brain: math oleh code (pasti), narasi oleh AI.

## Cara jalanin
1) Setup dari folder induk: activate venv + export key.
2) Masuk folder & jalanin:

    cd 03-sla-analyzer
    python sla_analyzer.py                 # default: data/incidents.csv
    python sla_analyzer.py data/incidents.csv

## Isi folder
- sla_analyzer.py -> RUN INI. Hitung metrik + panggil AI.
- prompts.py      -> prompt laporan SLA (AI nulis narasi, bukan ngitung).
- data/incidents.csv -> data incident contoh (start,end,severity,description).

## Setting (di sla_analyzer.py)
- SLA_TARGET   : target SLA persen (default 99.99)
- PERIOD_DAYS  : periode laporan (default 30 hari)

## Format data (CSV)
    start,end,severity,description
    2026-08-03 02:10,2026-08-03 02:22,High,deskripsi singkat
