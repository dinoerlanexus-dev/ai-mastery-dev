import sys
from parser import parse_anomalies
from engine import run_check
from google.genai import errors

def main():
    infile = sys.argv[1] if len(sys.argv) > 1 else "data/syslog_raw.log"
    check  = sys.argv[2] if len(sys.argv) > 2 else "bgp_rca"

    with open(infile) as f:
        lines = f.readlines()

    anomalies = parse_anomalies(lines)
    print(f"STAGE 1 (parser): {len(lines)} baris -> {len(anomalies)} anomali\n")

    if not anomalies:
        print("Nggak ada anomali. AI nggak dipanggil (hemat token).")
        return

    print("Anomali yang dikirim ke AI:")
    for a in anomalies:
        print("  " + a)
    print("\nSTAGE 2 (AI): menganalisa...\n" + "=" * 55)

    data = "\n".join(anomalies)
    try:
        print(run_check(check, data))
    except errors.ServerError as e:
        print(f"Model lagi overload ({e.code}). Anomali udah ke-filter & siap - coba lagi bentar.")
    except errors.ClientError as e:
        print(f"CLIENT ERROR ({e.code}): {e.message}")
    except RuntimeError as e:
        print(f"CONFIG ERROR: {e}")

if __name__ == "__main__":
    main()
