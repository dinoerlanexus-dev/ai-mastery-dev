"""
parser.py - STAGE 1 funnel: filter anomali dari syslog mentah.
GRATIS (no token). Tambah pattern baru = tambah di ANOMALY_PATTERNS.
"""
import re, sys

# Library pattern anomali (regex). Tambah di sini kalau mau tangkap event lain.
ANOMALY_PATTERNS = [
    r"%BGP-\d-",              # BGP adjacency / notification
    r"%OSPF-\d-",             # OSPF adjacency change
    r"%DUAL-\d-",             # EIGRP
    r"%LINK-3-UPDOWN",        # interface fisik down/up (severity 3)
    r"CRC",                   # CRC errors
    r"INPUT_ERRORS",          # input/CRC error counter
    r"hold time expired",     # BGP/OSPF hold timer
    r"err-?disable",          # port err-disabled
]

def parse_anomalies(lines):
    rx = re.compile("|".join(ANOMALY_PATTERNS), re.IGNORECASE)
    return [ln.rstrip("\n") for ln in lines if rx.search(ln)]

if __name__ == "__main__":
    infile = sys.argv[1] if len(sys.argv) > 1 else "data/syslog_raw.log"
    with open(infile) as f:
        lines = f.readlines()
    hits = parse_anomalies(lines)
    print(f"Total baris   : {len(lines)}")
    print(f"Anomali       : {len(hits)}   (buang {len(lines)-len(hits)} baris noise)")
    print("=" * 55)
    for h in hits:
        print(h)
