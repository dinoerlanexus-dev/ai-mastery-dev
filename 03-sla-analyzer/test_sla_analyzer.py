"""
test_sla_analyzer.py - Smoke test usecase 03-sla-analyzer.

Usecase ini paling "deterministic-heavy": SEMUA angka SLA dihitung CODE, AI cuma nulis narasi.
Jadi test di sini mostly REAL math (gratis, pasti) + 1 wiring test prompt pakai MOCK.
Regression pin: data/incidents.csv = 4 incident, 28 menit downtime. Kalau CSV di-edit
sengaja, update angka pin di bawah.

Jalanin: cd "03-sla-analyzer" && pytest test_sla_analyzer.py -v
"""
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
for _m in ("prompts", "sla_analyzer"):
    sys.modules.pop(_m, None)

# Script asli (versi lo, gak diubah) langsung STOP kalau GEMINI_API_KEY kosong.
# Jadi test pasang key PALSU dulu sebelum import. Semua panggilan AI di-mock,
# jadi key palsu ini gak pernah dipake ke Gemini (nol token, nol biaya).
os.environ["GEMINI_API_KEY"] = "dummy-key-test-only"

import prompts
import sla_analyzer as sla

DATA = os.path.join(HERE, "data", "incidents.csv")
PERIOD_MIN = 30 * 24 * 60   # 43200


# ---------- load_incidents ----------

def test_load_sample_csv_regression_pin():
    inc = sla.load_incidents(DATA)
    assert [i["minutes"] for i in inc] == [12, 4, 5, 7]


def test_load_handles_incident_across_midnight(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("start,end,severity,description\n"
                 "2026-08-03 23:50,2026-08-04 00:10,High,core down lewat tengah malam\n")
    assert sla.load_incidents(str(f))[0]["minutes"] == 20


# ---------- compute_sla (angka pasti) ----------

def test_compute_sla_on_sample_is_breach():
    m = sla.compute_sla(sla.load_incidents(DATA))
    assert m["period"] == PERIOD_MIN
    assert m["n"] == 4
    assert m["downtime"] == 28
    assert m["mttr"] == pytest.approx(7.0)
    assert m["avail"] == pytest.approx((PERIOD_MIN - 28) / PERIOD_MIN * 100)   # ~99.9352%
    assert m["budget"] == pytest.approx(4.32)          # 99.99% x 30 hari = 4.32 menit
    assert m["used"] == pytest.approx(28 / 4.32 * 100)  # ~648% error budget
    assert m["breach"] is True


def test_compute_sla_zero_incident():
    m = sla.compute_sla([])
    assert m["avail"] == 100
    assert m["mttr"] == 0          # gak boleh ZeroDivisionError
    assert m["used"] == 0
    assert m["breach"] is False


def test_compute_sla_budget_boundary():
    # budget 99.99%/30 hari = 4.32 menit -> 4 menit masih OK, 5 menit breach
    assert sla.compute_sla([{"minutes": 4}])["breach"] is False
    assert sla.compute_sla([{"minutes": 5}])["breach"] is True


# ---------- format_metrics + prompt wiring ----------

def test_format_metrics_contains_status_and_incidents():
    inc = sla.load_incidents(DATA)
    text = sla.format_metrics(sla.compute_sla(inc), inc)
    assert "BREACH" in text
    assert "Jumlah incident   : 4" in text
    assert "BGP flap Gi0/1 BR-JKT-03" in text
    assert "MTTR              : 7.0 menit" in text


def test_prompt_guardrails_present():
    p = prompts.PROMPTS["sla_report"]
    assert "{data}" in p
    assert "JANGAN hitung ulang" in p
    assert "JANGAN mengarang angka" in p
    assert "(verify)" in p


def test_metrics_flow_into_prompt_via_mock(monkeypatch):
    captured = {}
    monkeypatch.setattr(sla, "ask_ai", lambda p: captured.setdefault("p", p) and "MOCK")
    inc = sla.load_incidents(DATA)
    metrics = sla.format_metrics(sla.compute_sla(inc), inc)
    sla.ask_ai(prompts.PROMPTS["sla_report"].replace("{data}", metrics))
    assert "Availability      : 99.9352%" in captured["p"]
    assert "{data}" not in captured["p"]
