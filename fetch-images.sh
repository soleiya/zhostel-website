#!/usr/bin/env bash
# Re-download the photos/PDFs the site uses from the current zhostel.com (they aren't in the code
# archive because of their size), then shrink the large ones exactly like the original build did.
set -e
cd "$(dirname "$0")"
while read -r f; do
  [ -f "$f" ] && continue
  src="$f"; [ "$f" = "wp-content/uploads/2018/09/facade2-1400x933.jpg" ] && src="wp-content/uploads/2018/09/facade2-1400x933.png"
  mkdir -p "$(dirname "$src")"; curl -fsSL "https://zhostel.com/$src" -o "$src" || echo "missing: $src"
done < wp-content-files.txt
python3 - <<'PY'
import os
from PIL import Image
png = "wp-content/uploads/2018/09/facade2-1400x933.png"
if os.path.exists(png):
    Image.open(png).convert("RGB").save(png[:-4] + ".jpg", quality=80, optimize=True, progressive=True); os.remove(png)
for root, _, fs in os.walk("wp-content"):
    for f in fs:
        p = os.path.join(root, f); ext = f.lower().rsplit(".", 1)[-1]
        if ext not in ("jpg", "jpeg", "png") or os.path.getsize(p) < 250_000: continue
        im = Image.open(p); im.load()
        if max(im.size) > 1600: im.thumbnail((1600, 1600))
        (im.convert("RGB").save(p, quality=80, optimize=True, progressive=True) if ext != "png" else im.save(p, optimize=True))
PY
echo "images ready: $(find wp-content -type f | wc -l) files"
