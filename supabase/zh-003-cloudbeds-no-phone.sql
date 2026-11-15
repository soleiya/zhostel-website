-- zh-003: Cloudbeds → website import failed for OTA guests with no phone (or e-mail) in Cloudbeds
-- (booking_requests.guest_phone / guest_email are NOT NULL; VBR guests always had one).
-- cb_apply_reservation now stores '' instead of NULL for a missing phone / e-mail on insert.
do $$ declare d text; begin
  d := pg_get_functiondef('public.cb_apply_reservation'::regproc);
  if position($q$nullif(trim(p->>'guest_email'), ''), nullif(trim(p->>'guest_phone'), ''),$q$ in d) = 0 then
    raise notice 'zh-003: already applied or function changed'; return;
  end if;
  d := replace(d, $q$nullif(trim(p->>'guest_email'), ''), nullif(trim(p->>'guest_phone'), ''),$q$,
                  $q$coalesce(nullif(trim(p->>'guest_email'), ''), ''), coalesce(nullif(trim(p->>'guest_phone'), ''), ''),$q$);
  execute d;
end $$;
