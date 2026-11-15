-- zh-001: adapt the VBR engine (exact copy of live VBR, 14 Nov 2026) to Z Hostel.
-- Run once after the VBR replay. Safe on an empty database (removes only VBR seed rows).
drop table if exists public.add_ons_backup_v32;
delete from public.booking_cabanas where booking_id is not null;
delete from public.cabana_blocks where id is not null;
delete from public.cabanas where id is not null;
delete from public.booking_villas where id is not null;
delete from public.villas where id is not null;          -- VBR casitas; Z Hostel rooms/beds come from Cloudbeds
delete from public.add_ons where slug is not null;       -- VBR add-ons
delete from public.peak_dates where night is not null;
delete from public.discount_codes where code is not null; -- VBR starter codes
-- No meal package, pets or floor mattresses at the hostel. Check-in / out: confirm with the front desk.
update public.overnight_rates set meal_adult = 0, meal_child = 0, extra_bed = 0, pet_per_night = 0,
  check_in_time = '2:00 PM', check_out_time = '12:00 NN', max_nights = 30 where id = 1;
-- Website bookings only from zhostel.com; prices and open nights always follow Cloudbeds.
update public.booking_settings set
  allowed_origins = array['https://zhostel.com','https://www.zhostel.com'],
  cloudbeds_rates = true, cloudbeds_rates_from = (now() at time zone 'Asia/Manila')::date,
  villa_bookings_open_until = ((now() at time zone 'Asia/Manila')::date + 365),
  requests_open_until = null, readonly_staff_emails = '{}'::text[], updated_by = 'zh-001'
 where id = 1;
-- Rebrand texts inside functions (identifiers untouched: \m..\M treats "_" as a word character).
do $$ declare r record; d text; begin
  for r in select p.oid from pg_proc p where p.pronamespace = 'public'::regnamespace and p.prokind = 'f'
           and pg_get_functiondef(p.oid) ~ 'VBR|Virgin Beach|[Cc]asita' loop
    d := pg_get_functiondef(r.oid);
    d := replace(d, 'Virgin Beach Resort', 'Z Hostel');
    d := regexp_replace(d, '\mVBR-', 'ZH-', 'g');
    d := regexp_replace(d, '\mVBR\M', 'ZH', 'g');
    d := regexp_replace(d, '\mcasitas\M', 'rooms', 'g');
    d := regexp_replace(d, '\mcasita\M', 'room', 'g');
    d := regexp_replace(d, '\mCasitas\M', 'Rooms', 'g');
    d := regexp_replace(d, '\mCasita\M', 'Room', 'g');
    execute d;
  end loop;
end $$;
-- No zero-peso meal / pet / mattress lines on hostel quotes.
do $$ declare r record; d text; begin
  for r in select p.oid from pg_proc p where p.pronamespace='public'::regnamespace and p.proname in ('quote_overnight','quote_overnight_inquiry') loop
    d := pg_get_functiondef(r.oid);
    if position('v_before := round(' in d) = 0 then continue; end if;
    d := regexp_replace(d, '(\n\s*)(v_before := round\()',
      E'\\1-- zh-001: hostel stays have no meal package / pet / mattress charges\\1lines := coalesce((select jsonb_agg(x) from jsonb_array_elements(lines) x where not (x->>''kind'' in (''meal'',''pet'',''extra_bed'') and coalesce((x->>''amount'')::numeric, 0) = 0)), ''[]''::jsonb);\\1\\2');
    execute d;
  end loop;
end $$;
-- Cloudbeds stays in test mode until go-live.
select cb_state_set('push_enabled', 'false'::jsonb);
