// =============================================================================
// cloudbeds-photos (Z Hostel) — copies Cloudbeds' room-type and property photo
// links + descriptions into cb_sync_state.photos, so the website can show them.
// Called (POST, header x-webhook-secret = the vault secret cloudbeds-sync uses),
// e.g. from SQL:  select cb_photos_call();
// Uses the same Edge Function secrets as cloudbeds-sync: CLOUDBEDS_API_KEY,
// CLOUDBEDS_PROPERTY_ID. Deploy with "Verify JWT" OFF.
// =============================================================================
// deno-lint-ignore-file no-explicit-any
type Any = any;
const env = (k: string, d = "") => (globalThis as Any).Deno?.env.get(k) ?? d;
const CB = "https://api.cloudbeds.com/api/v1.3";
const PROPERTY = () => env("CLOUDBEDS_PROPERTY_ID", "6309");
const SB_URL = () => env("SUPABASE_URL");
const SR = () => env("SUPABASE_SERVICE_ROLE_KEY");

async function rpc(name: string, args: Record<string, unknown> = {}): Promise<Any> {
  const res = await fetch(`${SB_URL()}/rest/v1/rpc/${name}`, {
    method: "POST",
    headers: { apikey: SR(), Authorization: `Bearer ${SR()}`, "Content-Type": "application/json" },
    body: JSON.stringify(args),
  });
  const text = await res.text();
  if (!res.ok) throw new Error(`${name}: ${res.status} ${text.slice(0, 300)}`);
  return text ? JSON.parse(text) : null;
}

async function cb(path: string, params: Record<string, string> = {}): Promise<Any> {
  const key = env("CLOUDBEDS_API_KEY");
  if (!key) throw new Error("CLOUDBEDS_API_KEY is not set");
  const q = new URLSearchParams({ propertyID: PROPERTY(), ...params });
  const res = await fetch(`${CB}/${path}?${q}`, { headers: { "x-api-key": key, Accept: "application/json" } });
  const text = await res.text();
  try { return JSON.parse(text); } catch { throw new Error(`${path}: HTTP ${res.status} ${text.slice(0, 200)}`); }
}

function urls(v: Any): string[] {
  const out: string[] = [];
  const walk = (x: Any) => {
    if (!x) return;
    if (typeof x === "string") { if (/^https?:\/\//.test(x)) out.push(x); return; }
    if (Array.isArray(x)) { x.forEach(walk); return; }
    if (typeof x === "object") walk(x.image ?? x.url ?? x.original ?? x.thumb);
  };
  walk(v);
  return [...new Set(out)];
}

async function run() {
  const rt = await cb("getRoomTypes", { propertyIDs: PROPERTY(), pageSize: "100" });
  if (rt.success === false) throw new Error(`getRoomTypes: ${rt.message || "failed"}`);
  const types = (rt.data || []).map((t: Any) => ({
    room_type_id: String(t.roomTypeID ?? ""),
    room_type_name: String(t.roomTypeName ?? ""),
    description: String(t.roomTypeDescription ?? ""),
    photos: urls(t.roomTypePhotos ?? t.photos),
    raw_photo_keys: Object.keys(t).filter((k) => /photo|image/i.test(k)),
  }));
  let property: Any = {};
  try {
    const d = (await cb("getHotelDetails")).data || {};
    property = { name: d.propertyName ?? null, description: d.propertyDescription ?? null,
                 photos: urls([d.propertyImage, d.propertyAdditionalPhotos]) };
  } catch (e) { property = { error: String((e as Error)?.message || e) }; }
  const value = { at: new Date().toISOString(), types, property };
  await rpc("cb_state_set", { p_key: "photos", p_value: value });
  return { types: types.length, type_photos: types.reduce((n: number, t: Any) => n + t.photos.length, 0),
           property_photos: (property.photos || []).length };
}

(globalThis as Any).Deno.serve(async (req: Request) => {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });
  const s = await rpc("cb_webhook_secret").catch(() => null);
  if (!s || (req.headers.get("x-webhook-secret") || "") !== s) return new Response("Unauthorized", { status: 401 });
  try {
    const r = await run();
    return new Response(JSON.stringify(r), { headers: { "Content-Type": "application/json" } });
  } catch (e) {
    await rpc("cb_state_set", { p_key: "photos_error", p_value: { at: new Date().toISOString(), error: String((e as Error)?.message || e) } }).catch(() => null);
    return new Response(JSON.stringify({ error: String((e as Error)?.message || e) }), { status: 500 });
  }
});
