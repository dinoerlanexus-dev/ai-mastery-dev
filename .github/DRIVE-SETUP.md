# Drive backup setup — rclone OAuth (sekali, ~10 menit)

## Kenapa BUKAN service account
Service account gak punya storage quota. Upload ke folder My Drive (akun @gmail.com)
yang di-share ke SA -> 403 "Service Accounts do not have storage quota".
Fix resmi Google = Shared Drive / domain-wide delegation -> dua-duanya cuma ada di
Google Workspace, bukan Gmail personal. Jadi pakai OAuth user (akun lo sendiri) via rclone.
Scope `drive.file` = rclone cuma bisa liat/ubah file yang DIA bikin, bukan seluruh Drive lo.

## Langkah (di Terminal Mac)
1. Install:            brew install rclone
2. Config:             rclone config
   - n                 (new remote)
   - name>             gdrive
   - Storage>          drive
   - client_id>        (Enter, kosong)
   - client_secret>    (Enter, kosong)
   - scope>            drive.file        <- ketik persis ini
   - service_account_file> (Enter, kosong)
   - Edit advanced config? n
   - Use web browser to automatically authenticate? y  -> login akun Google lo, Allow
   - Configure this as a Shared Drive? n
   - Keep this "gdrive" remote? y   -> lalu q
   - JANGAN set config password (CI gak bisa decrypt).
3. Test:               rclone mkdir gdrive:AI-Mastery-Deliverables && rclone lsd gdrive:
4. Simpen ke GitHub Secret:
   - Pakai gh CLI:     gh secret set RCLONE_CONF -R dinoerlanexus-dev/ai-mastery-dev < ~/.config/rclone/rclone.conf
   - Atau manual:      cat ~/.config/rclone/rclone.conf -> copy SEMUA isinya ->
                       GitHub repo > Settings > Secrets and variables > Actions >
                       New repository secret > Name: RCLONE_CONF > paste > Add secret

## Security notes
- rclone.conf berisi refresh token. Treat kayak password: jangan commit, jangan screenshot.
- Revoke kapan aja: myaccount.google.com > Security > Third-party connections > rclone > Remove.
- Hasil di Drive: AI-Mastery-Deliverables/<usecase>/latest/ (README, test-report.xml, MANIFEST.txt)
