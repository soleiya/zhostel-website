# Z Hostel database (Supabase project `vsfuliexdlhgdlvlhqzy`, soleiya's Org)

## How it was built (15 Nov 2026)

1. **Exact copy of the VBR booking engine.** Every VBR database update (SETUP-BOOKING.md
   blocks 1–6, cabana seed, email trigger, change email, v3 … v72, in VBR's run order) was
   loaded from the VBR repo at commit `3fe32ac`, with the project ref and domain swapped
   (`dokscqjvqtyhecmbshqd` → `vsfuliexdlhgdlvlhqzy`, `virginbeachresort.com` → `zhostel.com`).
   Columns VBR had added by hand were added first. Only v26 (cabana renumbering) was skipped.
   Result checked against the live VBR database: same 31 tables, 437 columns, 44 policies,
   57 triggers, 6 cron jobs, and all 163 functions byte-identical (after the swap).
   The load log is in the `_replay.q` table.
2. **`zh-001-hostel.sql`** — the Z Hostel changes on top (this folder).
3. **`zh-002-cloudbeds-rooms.sql`** — `cb_set_rooms()`: Z Hostel's units come from Cloudbeds.
   cloudbeds-sync (`functions/cloudbeds-sync`) is deployed and syncing property 6309; its "setup"
   run loaded 106 units into `villas` (10 room types: dorm beds sleep 1, private rooms 2).

## Still to do before going live
- Edge Functions: send-booking-email, xendit-pay, campaigns, sync-alerts,
  send-contact-email — rebranded for Z Hostel — plus their secrets (entered by the owner
  in Supabase → Edge Functions → Secrets): SMTP_PASSWORD, CLOUDBEDS_API_KEY,
  CLOUDBEDS_PROPERTY_ID, XENDIT_SECRET_KEY, XENDIT_CALLBACK_TOKEN, ANTHROPIC_API_KEY,
  and the vault secret `booking_email_webhook_secret`.
- Website pages: book/, pay/, staff/, manager/ (ported from VBR, hostel wording).
- Staging site: website bookings are accepted only from `booking_settings.allowed_origins`
  (zhostel.com). Add the Cloudflare staging address there to test bookings on staging.
- Cloudbeds stays in test mode until `select cb_go_live();`.
