# AI Mastery — Dev Workspace

Kumpulan AI usecase buat networking / banking. Tiap usecase = 1 folder bernomor.

## Setup (WAJIB, sekali tiap buka terminal baru)
    cd ~/Documents/COWORK\ CLAUDE/07.\ CODE/ai-mastery-dev
    source venv/bin/activate          # muncul (venv) di prompt
    export GEMINI_API_KEY='...'        # paste key Gemini lo (jangan di-screenshot)

## Daftar usecase
- 01-network-rca/     -> AI RCA dari syslog (funnel parser -> AI). Lihat README di dalam.
- 02-config-review/   -> AI review config vs best-practice / OJK. Lihat README di dalam.

## Aturan folder
- venv SHARED: 1 environment buat semua usecase. Aktifin sekali dari folder ini.
- Nama file .py pakai underscore (_), BUKAN hyphen (-). Hyphen bikin nggak bisa di-import.
- API key lewat env var (export). Jangan hardcode, jangan commit ke git.
- Usecase baru = folder baru: 03-xxx/, 04-xxx/.
