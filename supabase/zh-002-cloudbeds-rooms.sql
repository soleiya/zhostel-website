-- zh-002: Cloudbeds rooms → villas. Z Hostel's units (each dorm bed, each private room) are
-- created from Cloudbeds by cloudbeds-sync "setup" instead of being typed in by hand like VBR's casitas.
-- Dorm beds sleep 1, private rooms 2. weekday/weekend_rate = zhostel.com published price, used only as
-- an estimate (prices always come from Cloudbeds while booking_settings.cloudbeds_rates is on).
create or replace function cb_set_rooms(p jsonb) returns jsonb
language plpgsql security definer set search_path = public as $$
declare x jsonb; v uuid; v_matched text[] := '{}'; v_created text[] := '{}'; v_type text; v_tname text; v_rate numeric; v_occ int;
begin
  for x in select * from jsonb_array_elements(p) loop
    select id into v from villas where cb_room_id = x->>'room_id';
    if v is null then
      select id into v from villas where cb_norm(unit_label) = cb_norm(x->>'room_name') and cb_room_id is null limit 1;
    end if;
    if v is null then
      v_tname := coalesce(nullif(trim(x->>'room_type_name'), ''), 'Room');
      v_type := trim(both '-' from regexp_replace(lower(v_tname), '[^a-z0-9]+', '-', 'g'));
      v_occ := case when v_tname ~* 'dorm|bed\M' and v_tname !~* 'private' then 1 else 2 end;
      v_rate := case when v_tname ~* 'private' then 3000 when v_tname ~* '4 ?bed|4MD' then 1350
                     when v_tname ~* '8 ?bed|8MD' then 1250 else 1300 end;
      insert into villas (unit_label, room_type, room_type_name, base_occupancy, max_extra, weekday_rate, weekend_rate, sort, active,
                          cb_room_id, cb_room_type_id, cb_room_type_name)
      values (coalesce(x->>'room_name', 'Unit ' || (x->>'room_id')), v_type, v_tname, v_occ, 0, v_rate, v_rate,
              (select coalesce(max(sort), 0) + 1 from villas), true, x->>'room_id', x->>'room_type_id', x->>'room_type_name');
      v_created := v_created || (x->>'room_name');
    else
      update villas set cb_room_id = null where cb_room_id = x->>'room_id' and id <> v;
      update villas set cb_room_id = x->>'room_id', cb_room_type_id = x->>'room_type_id', cb_room_type_name = x->>'room_type_name' where id = v;
      v_matched := v_matched || (x->>'room_name');
    end if;
  end loop;
  return jsonb_build_object('matched', coalesce(array_length(v_matched, 1), 0), 'created', coalesce(array_length(v_created, 1), 0),
    'unmatched', '[]'::jsonb,
    'villas_without_cloudbeds_room', (select coalesce(jsonb_agg(unit_label order by sort), '[]'::jsonb) from villas where active and cb_room_id is null));
end;
$$;
revoke all on function cb_set_rooms(jsonb) from public, anon, authenticated;
