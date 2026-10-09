import os, sys, csv, time
from datetime import datetime
from google import genai
from google.genai import errors
from prompts import PROMPTS

MODEL       = "gemini-3.6-flash"
SLA_TARGET  = 99.99      # persen (ubah sesuai kontrak)
PERIOD_DAYS = 30

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise SystemExit("set dulu: export GEMINI_API_KEY='...'")
client = genai.Client(api_key=api_key)

def ask_ai(prompt: str, retries: int = 3) -> str:
    for attempt in range(1, retries + 1):
        try:
            return client.models.generate_content(model=MODEL, contents=prompt).text
        except errors.ServerError as e:
            if attempt < retries:
                wait = 5 * attempt
                print(f"[retry] Server sibuk ({e.code}), coba lagi {wait}s ({attempt}/{retries})...")
                time.sleep(wait)
            else:
                raise

def load_incidents(path):
    rows = []
    with open(path) as f:
        for r in csv.DictReader(f):
            start = datetime.strptime(r["start"].strip(), "%Y-%m-%d %H:%M")
            end   = datetime.strptime(r["end"].strip(),   "%Y-%m-%d %H:%M")
            r["minutes"] = (end - start).total_seconds() / 60
            rows.append(r)
    return rows

def compute_sla(incidents):
    period = PERIOD_DAYS * 24 * 60
    downtime = sum(i["minutes"] for i in incidents)
    n = len(incidents)
    avail = (period - downtime) / period * 100
    mttr = downtime / n if n else 0
    budget = period * (1 - SLA_TARGET / 100)         # menit yang "boleh" down
    used = (downtime / budget * 100) if budget else 0
    return dict(period=period, downtime=downtime, n=n, avail=avail,
                mttr=mttr, budget=budget, used=used, breach=avail < SLA_TARGET)

def format_metrics(m, inc):
    out = [
        f"Periode           : {PERIOD_DAYS} hari ({m['period']:.0f} menit)",
        f"Target SLA        : {SLA_TARGET}%  (budget downtime {m['budget']:.2f} menit)",
        f"Jumlah incident   : {m['n']}",
        f"Total downtime    : {m['downtime']:.0f} menit",
        f"Availability      : {m['avail']:.4f}%",
        f"MTTR              : {m['mttr']:.1f} menit",
        f"Error budget kepakai: {m['used']:.0f}%  ({'BREACH' if m['breach'] else 'OK'})",
        "",
        "Daftar incident:",
    ]
    for i in inc:
        out.append(f"- {i['start']} -> {i['end']} ({i['minutes']:.0f} min) [{i['severity']}] {i['description']}")
    return "\n".join(out)

if __name__ == "__main__":
    datafile = sys.argv[1] if len(sys.argv) > 1 else "data/incidents.csv"
    try:
        inc = load_incidents(datafile)
        m = compute_sla(inc)
        metrics = format_metrics(m, inc)
        print("=== METRIK (dihitung CODE, angka pasti) ===")
        print(metrics)
        print("\n=== LAPORAN (ditulis AI) ===")
        print(ask_ai(PROMPTS["sla_report"].replace("{data}", metrics)))
    except FileNotFoundError:
        print(f"File nggak ketemu: {datafile}")
    except errors.ClientError as e:
        print(f"CLIENT ERROR ({e.code}): {e.message}")
    except errors.ServerError as e:
        print(f"SERVER ERROR ({e.code}): {e.message} - model overload, coba lagi nanti.")
    except Exception as e:
        print(f"ERROR {type(e).__name__}: {e}")
