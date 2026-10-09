import os, sys, time
from google import genai
from google.genai import errors
from prompts import PROMPTS

MODEL = "gemini-3.6-flash"

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
    check    = sys.argv[1] if len(sys.argv) > 1 else "config_review"
    datafile = sys.argv[2] if len(sys.argv) > 2 else "data/router_sample.cfg"
    try:
        with open(datafile) as f:
            data = f.read()
        print(f"Check: {check}  |  Data: {datafile}\n" + "=" * 55)
        print(run_check(check, data))
    except FileNotFoundError:
        print(f"File nggak ketemu: {datafile}")
    except errors.ClientError as e:
        print(f"CLIENT ERROR ({e.code}): {e.message}")
    except errors.ServerError as e:
        print(f"SERVER ERROR ({e.code}): {e.message} - model overload, coba lagi nanti.")
    except Exception as e:
        print(f"ERROR {type(e).__name__}: {e}")
