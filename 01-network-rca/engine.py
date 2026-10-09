import os, sys, time
from google import genai
from google.genai import errors
from prompts import PROMPTS

MODEL = "gemini-3.6-flash"   # kalau 503 terus, ganti model dari daftar AI Studio

api_key = os.environ.get("GEMINI_API_KEY")
# Lazy init: jangan crash pas di-import (misal dari dashboard_app.py) kalau key belum di-set.
# Error yang jelas baru muncul pas ask_ai() beneran dipanggil.
client = genai.Client(api_key=api_key) if api_key else None

def ask_ai(prompt: str, retries: int = 3) -> str:
    """Kirim prompt ke AI. Kalau server 503 (overload), retry otomatis (kayak TCP retransmit)."""
    if client is None:
        raise RuntimeError("GEMINI_API_KEY belum di-set. Jalankan: export GEMINI_API_KEY='...'")
    for attempt in range(1, retries + 1):
        try:
            return client.models.generate_content(model=MODEL, contents=prompt).text
        except errors.ServerError as e:
            if attempt < retries:
                wait = 5 * attempt
                print(f"[retry] Server sibuk ({e.code}), coba lagi dalam {wait}s ({attempt}/{retries})...")
                time.sleep(wait)
            else:
                raise

def run_check(check: str, data: str) -> str:
    if check not in PROMPTS:
        return f"Check '{check}' nggak ada. Pilihan: {', '.join(PROMPTS)}"
    prompt = PROMPTS[check].replace("{data}", data)
    return ask_ai(prompt)

if __name__ == "__main__":
    check    = sys.argv[1] if len(sys.argv) > 1 else "bgp_rca"
    datafile = sys.argv[2] if len(sys.argv) > 2 else "data/bgp_sample.log"
    try:
        with open(datafile) as f:
            data = f.read()
        print(f"Check: {check}  |  Data: {datafile}\n" + "=" * 50)
        print(run_check(check, data))
    except FileNotFoundError:
        print(f"File nggak ketemu: {datafile}")
    except errors.ClientError as e:
        print(f"CLIENT ERROR ({e.code}): {e.message}")
    except errors.ServerError as e:
        print(f"SERVER ERROR ({e.code}): {e.message} - model overload, coba lagi nanti.")
    except Exception as e:
        print(f"ERROR {type(e).__name__}: {e}")
