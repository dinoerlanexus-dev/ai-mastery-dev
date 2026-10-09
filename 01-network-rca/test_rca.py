"""
test_rca.py - Smoke test buat usecase 01-network-rca (build order #1, automation pipeline).

Prinsip:
- parser.py: real test, deterministic, gratis (no API call).
- engine.py / network_rca.py: wiring test pakai MOCK ask_ai() - validasi funnel
  nyambung bener (parser -> prompt -> AI call -> output) TANPA hit Gemini API
  beneran. GEMINI_API_KEY sengaja nggak disimpen di folder synced (keamanan),
  jadi CI nggak boleh depend ke key asli.
- Live end-to-end (manggil AI beneran) tetep manual run lokal, bukan bagian CI.

Jalanin: cd "01-network-rca" && pytest test_rca.py -v
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import parser
import engine
import network_rca


# ---------- STAGE 1: parser.py (real, deterministic, gratis) ----------

def test_parse_anomalies_catches_bgp():
    lines = ["Aug 18 %BGP-5-ADJCHANGE: neighbor 10.1.1.1 Down\n"]
    assert parser.parse_anomalies(lines) == [lines[0].rstrip("\n")]


def test_parse_anomalies_catches_ospf():
    lines = ["Aug 18 %OSPF-5-ADJCHG: Process 1, Nbr 10.1.1.1 FULL to DOWN\n"]
    assert parser.parse_anomalies(lines) == [lines[0].rstrip("\n")]


def test_parse_anomalies_catches_link_updown_and_crc():
    lines = [
        "Aug 18 %LINK-3-UPDOWN: Interface Gi0/1 changed state to down\n",
        "Aug 18 %CONTROLLER-4-INPUT_ERRORS: CRC errors incrementing\n",
    ]
    assert parser.parse_anomalies(lines) == [ln.rstrip("\n") for ln in lines]


def test_parse_anomalies_ignores_noise():
    lines = [
        "Aug 18 %SYS-5-CONFIG_I: Configured from console by admin\n",
        "Aug 18 %NTP-6-PEERSYNC: NTP synced to peer 10.1.1.1\n",
        "Aug 18 %SEC_LOGIN-5-LOGIN_SUCCESS: Login Success user admin\n",
    ]
    assert parser.parse_anomalies(lines) == []


def test_parse_anomalies_case_insensitive():
    lines = ["Aug 18 something err-disabled on Gi0/1\n"]
    assert parser.parse_anomalies(lines) == [lines[0].rstrip("\n")]


def test_parse_anomalies_real_bgp_sample():
    """Regression pin - data/bgp_sample.log dikurasi semua-anomali (9/9 baris)."""
    path = os.path.join(os.path.dirname(__file__), "data", "bgp_sample.log")
    with open(path) as f:
        lines = f.readlines()
    anomalies = parser.parse_anomalies(lines)
    assert len(lines) == 9
    assert len(anomalies) == 9, (
        "Jumlah anomali di bgp_sample.log berubah dari 9 - kalau ini sengaja "
        "(data file di-update), update angka pin di test ini juga."
    )


def test_parse_anomalies_real_syslog_raw():
    """Regression pin - data/syslog_raw.log campur noise+anomali (10/25 baris)."""
    path = os.path.join(os.path.dirname(__file__), "data", "syslog_raw.log")
    with open(path) as f:
        lines = f.readlines()
    anomalies = parser.parse_anomalies(lines)
    assert len(lines) == 25
    assert len(anomalies) == 10, (
        "Jumlah anomali di syslog_raw.log berubah dari 10 - kalau ini sengaja "
        "(data file di-update), update angka pin di test ini juga."
    )
    assert len(anomalies) < len(lines), "Harusnya sebagian noise ke-filter, bukan semua lolos"


# ---------- STAGE 2: engine.py (mock ask_ai, no API call) ----------

def test_run_check_unknown_check_no_api_call(monkeypatch):
    """Check yang gak ada di PROMPTS harus reject SEBELUM nyampe ask_ai() -> zero token cost."""
    def boom(*a, **kw):
        raise AssertionError("ask_ai() dipanggil padahal check-nya invalid - harusnya di-reject duluan")
    monkeypatch.setattr(engine, "ask_ai", boom)

    result = engine.run_check("nonexistent_check", "some data")
    assert "nggak ada" in result
    assert "bgp_rca" in result  # nunjukin daftar pilihan yang valid


def test_run_check_builds_prompt_and_calls_ask_ai(monkeypatch):
    """Validasi funnel: run_check() masukin `data` ke template prompt & manggil ask_ai() sekali."""
    captured = {}

    def fake_ask_ai(prompt, retries=3):
        captured["prompt"] = prompt
        return "MOCKED AI RESPONSE"

    monkeypatch.setattr(engine, "ask_ai", fake_ask_ai)

    result = engine.run_check("bgp_rca", "SAMPLE_LOG_LINE_XYZ")
    assert result == "MOCKED AI RESPONSE"
    assert "SAMPLE_LOG_LINE_XYZ" in captured["prompt"]
    assert "{data}" not in captured["prompt"]  # placeholder harus udah ke-replace


def test_ask_ai_raises_clear_error_without_api_key(monkeypatch):
    """Kalau GEMINI_API_KEY belum di-set (client=None), harus RuntimeError yang jelas, bukan crash aneh."""
    monkeypatch.setattr(engine, "client", None)
    try:
        engine.ask_ai("test prompt")
        assert False, "Harusnya raise RuntimeError"
    except RuntimeError as e:
        assert "GEMINI_API_KEY" in str(e)


# ---------- END-TO-END WIRING: network_rca.py (mock run_check, no API call) ----------

def test_main_no_anomalies_skips_ai_call(monkeypatch, tmp_path, capsys):
    """Log tanpa anomali -> run_check() SAMA SEKALI GAK dipanggil (hemat token, sesuai komentar di kode)."""
    logfile = tmp_path / "clean.log"
    logfile.write_text("Aug 18 %SYS-5-CONFIG_I: Configured from console\n")

    def boom(*a, **kw):
        raise AssertionError("run_check() dipanggil padahal gak ada anomali")
    monkeypatch.setattr(network_rca, "run_check", boom)
    monkeypatch.setattr(sys, "argv", ["network_rca.py", str(logfile), "bgp_rca"])

    network_rca.main()
    out = capsys.readouterr().out
    assert "Nggak ada anomali" in out


def test_main_with_anomalies_calls_run_check(monkeypatch, tmp_path, capsys):
    """Log dengan anomali -> parser jalan, run_check() dipanggil, hasilnya keprint."""
    logfile = tmp_path / "anomaly.log"
    logfile.write_text("Aug 18 %BGP-5-ADJCHANGE: neighbor 10.1.1.1 Down\n")

    monkeypatch.setattr(network_rca, "run_check", lambda check, data: "MOCKED RCA OUTPUT")
    monkeypatch.setattr(sys, "argv", ["network_rca.py", str(logfile), "bgp_rca"])

    network_rca.main()
    out = capsys.readouterr().out
    assert "MOCKED RCA OUTPUT" in out
    assert "1 baris -> 1 anomali" in out
