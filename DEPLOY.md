# Deploying the Z Hostel website (Cloudflare)

The site is plain static files. Cloudflare builds it from this repo on every push to `main`.

## One-time: connect the repo (Cloudflare dashboard, account owner)
1. Cloudflare → **Workers & Pages** → **Create** → **Import a repository** → GitHub →
   pick `soleiya/zhostel-website` (install / allow the Cloudflare GitHub app for it if asked).
2. Project name: `zhostel` (must match `name` in wrangler.jsonc). Production branch: `main`.
3. Build command: `python3 export_public.py` · Deploy command: `npx wrangler deploy` (default).
   `wrangler.jsonc` publishes `./public`, which the build fills with the public site only
   (no SQL, function code or scripts).
4. Save and deploy. The staging link is `https://zhostel.<your-account>.workers.dev`
   (shown on the project page). Every other branch gets its own preview link.

## Photos
The photos (`wp-content/`) are downloaded from the current zhostel.com by `./fetch-images.sh`
and committed. Run it on a machine that can reach zhostel.com, then commit `wp-content/`.

## Going live on zhostel.com
- Cloudflare → the project → **Settings → Domains & Routes** → add `zhostel.com` and `www.zhostel.com`.
- In `wrangler.jsonc` set `workers_dev` and `preview_urls` to `false` (as VBR did).
- book/ and pay/ are built by `python3 pages_booking.py` (after `build_site.py`).
- Book Now → own engine: `ZH_BOOK_URL=/book/ python3 build_site.py && python3 pages_booking.py`, commit.
