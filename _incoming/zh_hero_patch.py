#!/usr/bin/env python3
"""One-time patch (run by .github/workflows/zh-hero.yml):
home hero = entrance photo + the striped Z logo, headline "Good Vibes Only",
sub "The OG Hostel in Poblacion, the one who started it all."; the building
shot replaces the Getting There banner on the home page. Fails loudly if the
code it expects isn't there."""
import re, shutil, os
os.makedirs("assets/img", exist_ok=True)
shutil.move("_incoming/zhostel-entrance.jpg", "assets/img/zhostel-entrance.jpg")
shutil.move("_incoming/z-hostel-building.jpg", "assets/img/z-hostel-building.jpg")

p = "build_site.py"; s = open(p, encoding="utf-8").read()

def sub1(old, new):
    global s
    assert s.count(old) == 1, f"expected exactly one match for: {old[:70]!r} (found {s.count(old)})"
    s = s.replace(old, new)

# home hero: entrance photo, proper logo, headline + subtext
sub1("""    if key == "home":
        return f\"\"\"<header class="hero hero--home"{bg}>{vid}
{logo}<p class="hero-kicker">Z Hostel &middot; Poblacion, Makati</p><h1>The Original Poblacion Hostel</h1>
<p class="sub">Good vibes only &mdash; in Poblacion since 2015.</p>""",
"""    if key == "home":
        bg = ' style="background-image:url(\\'/assets/img/zhostel-entrance.jpg\\')"'
        vid = ""
        logo = '<img class="logo logo--brand" src="/wp-content/uploads/2018/08/Logo.png" alt="Z Hostel" width="150" height="150">'
        return f\"\"\"<header class="hero hero--home"{bg}>{vid}
{logo}<p class="hero-kicker">Z Hostel &middot; Poblacion, Makati</p><h1>Good Vibes Only</h1>
<p class="sub">The OG Hostel in Poblacion, the one who started it all.</p>""")

# building shot: replaces the Getting There banner on the home page
sub1("{banner(D['ul']['gettingThere'])}",
"""<section class="section section--grey" id="getting-there"><div class="container"><div class="split building-split">
<img src="/assets/img/z-hostel-building.jpg" alt="The Z Hostel building in Poblacion, Makati, with the roofdeck on top" width="880" height="1184" loading="lazy">
<div><h2 class="section-title">Getting There</h2><p><strong>{ADDRESS}</strong></p>
<p>Look for the big Z on the building &mdash; the roofdeck is on top, the entrance is on Don Pedro St., right off Kalayaan Ave.</p>
<p><a class="btn btn-dark" href="{MAP_LINK}" target="_blank" rel="noopener">Open in Google Maps</a> <a class="btn btn-outline" href="{DIRECTIONS_PDF}" target="_blank" rel="noopener">Directions (PDF)</a></p></div></div></div></section>""")

# share image for the home page
s = re.sub(r'body, "home", image=CBP\["private-room-standard"\]\[0\]\)', 'body, "home", image="/assets/img/zhostel-entrance.jpg")', s)
open(p, "w", encoding="utf-8").write(s)

c = "assets/css/site.css"
css = open(c, encoding="utf-8").read()
css += """
/* zh-hero: entrance photo hero, striped Z logo, building shot */
.hero--home { background-position: center 60%; }
.hero .logo--brand { border-radius: 50%; box-shadow: 0 6px 24px rgba(0,0,0,.35); }
.building-split img { width: 100%; max-height: 640px; object-fit: cover; object-position: center top; }
.building-split { align-items: center; }
"""
open(c, "w", encoding="utf-8").write(css)
print("patched")
