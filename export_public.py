#!/usr/bin/env python3
"""Cloudflare build step: copy only the public website into ./public.

Cloudflare → Workers & Pages → zhostel-website → Settings → Build:
  Build command:          python3 export_public.py
  Deploy command:         npx wrangler deploy   (default)

The site is every top-level page folder (one per page / blog post) plus assets/ and
wp-content/ (photos). Repository-only material — SQL, Edge Function code, the page
builder, data files, notes — stays out of the live site.
"""
import os
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "public")

SKIP_DIRS = {"public", "supabase", "data", "node_modules", "__pycache__"}
SITE_FILES = ["index.html", "404.html", "robots.txt", "llms.txt", "sitemap.xml", "_headers", "_redirects", "favicon.ico"]
SKIP_EXT = {".py", ".pyc", ".sql", ".md", ".gs", ".ts", ".map", ".sh", ".txt", ".jsonc"}

if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)

n = 0
for d in sorted(os.listdir(ROOT)):
    src = os.path.join(ROOT, d)
    if not os.path.isdir(src) or d.startswith(".") or d in SKIP_DIRS:
        continue
    for root, dirs, files in os.walk(src):
        dirs[:] = [x for x in dirs if not x.startswith(".") and x != "__pycache__"]
        for f in files:
            if f.startswith(".") or os.path.splitext(f)[1].lower() in SKIP_EXT:
                continue
            rel = os.path.relpath(os.path.join(root, f), ROOT)
            dst = os.path.join(OUT, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(root, f), dst)
            n += 1
for f in SITE_FILES:
    if os.path.isfile(os.path.join(ROOT, f)):
        shutil.copy2(os.path.join(ROOT, f), os.path.join(OUT, f))
        n += 1
print(f"public/: {n} files")
