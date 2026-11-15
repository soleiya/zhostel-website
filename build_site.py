#!/usr/bin/env python3
"""Static site generator for the Z Hostel website (zhostel.com).

Content comes from data/site-data.json and data/blog.json (taken from the
current zhostel.com) and is laid out like the current site. Run:

    python3 build_site.py

It writes index.html and one folder per page (about-z/, rooms-and-services/,
events-and-activities/, gallery/, blog/ + one folder per post, careers/,
contact-us/), plus 404.html, sitemap.xml and robots.txt.

Every Book Now button goes to the website's own booking engine (/book/, built by
pages_booking.py); bookings are saved in Supabase and pushed to Cloudbeds by
cloudbeds-sync. Photos: only images that exist in the repo are used (wp-content/,
see fetch-images.sh); room photos come from Cloudbeds (data/cloudbeds-photos.json).
After build_site.py run pages_booking.py.
"""
import hashlib
import html
import json
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITE = "https://zhostel.com"
D = json.load(open(os.path.join(ROOT, "data/site-data.json"), encoding="utf-8"))
BLOG = json.load(open(os.path.join(ROOT, "data/blog.json"), encoding="utf-8"))
CBP = {k: v for k, v in json.load(open(os.path.join(ROOT, "data/cloudbeds-photos.json"), encoding="utf-8")).items() if not k.startswith("_")}


def have(src):
    """True if an image can be shown: a local file that exists in the repo, or an absolute URL."""
    if not src:
        return False
    if src.startswith("http"):
        return True
    return os.path.isfile(os.path.join(ROOT, src.split("?")[0].lstrip("/")))


def first(*srcs):
    return next((x for x in srcs if have(x)), None)

# Where Book Now goes. "/book/" = the website's own booking engine.
CLOUDBEDS_URL = "https://hotels.cloudbeds.com/reservation/oL7RdR"
BOOK_URL = os.environ.get("ZH_BOOK_URL", "/book/")  # the website's own booking engine
BOOK_EXTERNAL = BOOK_URL.startswith("http")
BOOK_NOTE = "(opens booking page)"

PHONE = "(632) 8856 0851"
MOBILE = "(63) 917 889 8531"
ADDRESS = "5660 Don Pedro St. Brgy. Poblacion, Makati City, Philippines 1210"
EMAIL = "reservations@zhostel.com"
FB = "https://www.facebook.com/zhostelph/"
IG = "https://www.instagram.com/zhostelph/"
YT = "https://www.youtube.com/channel/UCoSwV7kz69fka8q3sapHJUA"
MAP_EMBED = ("https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3861.618786689355!2d121.02919401431974!3d14.563779281883624"
             "!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3397c9aaf1f35e4f%3A0x7f6c432bba82e5b3!2sZ+Hostel!5e0!3m2!1sen!2sph!4v1553682211238")
MAP_LINK = "https://www.google.com/maps/search/?api=1&query=Z+Hostel+5660+Don+Pedro+St+Poblacion+Makati"
MENU_PDF = "/wp-content/uploads/2019/03/Menu-downloadable.pdf"
DIRECTIONS_PDF = "/wp-content/uploads/2018/08/DIRECTIONS-TO-Z.pdf"

# Bookable room types (villas.room_type, from Cloudbeds). from-price = zhostel.com published rate.
ROOMS = [
    ("4-bed-mixed-dorm", "4 Bed Mixed Dorm", 1350, "bed", "A good mix of privacy and sociability. 15 sqm."),
    ("6-bed-mixed-dorm", "6 Bed Mixed Dorm", 1300, "bed", "Big custom bunks, in-room sink. 30 sqm."),
    ("8-bed-mixed-dorm", "8 Bed Mixed Dorm", 1250, "bed", "Our best-value bed, in-room sink. 30 sqm."),
    ("6-bed-female-dorm", "6 Bed Female Dorm", 1300, "bed", "The all-female “Stiletto” dorm with vanity and big lockers."),
    ("social-fun-floor-dorm-4md", "Social Fun Floor – 4 Bed Dorm", 1350, "bed", "Right below the Roofdeck — for the social crowd."),
    ("social-fun-floor-dorm-6md", "Social Fun Floor – 6 Bed Dorm", 1300, "bed", "Right below the Roofdeck — for the social crowd."),
    ("private-room-standard", "Private Room", 3000, "room", "Queen bed, en-suite bathroom, top floors. Sleeps 2."),
    ("private-room-bunk-bed", "Private Room – Bunk Bed", 3000, "room", "A bunk-bed room for you and your buddy, en-suite. Sleeps 2."),
    ("social-fun-floor-private-room", "Social Fun Floor – Private Room", 3000, "room", "Private room just below the Roofdeck. Sleeps 2."),
    ("social-private-bunk-bed", "Social Private Bunk Bed", 3000, "room", "Private bunk-bed room on the Social Fun Floor. Sleeps 2."),
]
# rooms-and-services blocks (site-data ids) → bookable room types
ROOM_MAP = {"4-bed": ["4-bed-mixed-dorm"], "6-bed": ["6-bed-mixed-dorm"], "8-bed": ["8-bed-mixed-dorm"],
            "all-female": ["6-bed-female-dorm"], "private-room": ["private-room-standard"],
            "private-bunk": ["private-room-bunk-bed"],
            "fun-floor": ["social-fun-floor-dorm-4md", "social-fun-floor-dorm-6md", "social-fun-floor-private-room", "social-private-bunk-bed"]}
ROOM_NAME = {r[0]: r[1] for r in ROOMS}
TAGLINE = "The original Poblacion hostel"
GEO = (14.5637792, 121.0291940)


def book_url(room=None):
    return f"{BOOK_URL}?room={room}" if room and not BOOK_EXTERNAL else BOOK_URL


NAV = [("/", "Home"), ("/book/", "Book Now"), ("/about-z/", "About Z"), ("/rooms-and-services/", "Rooms & Services"),
       ("/events-and-activities/", "Events & Activities"), ("/blog/", "Blog"), ("/gallery/", "Gallery"),
       ("/faq/", "FAQ"), ("/careers/", "Careers"), ("/contact-us/", "Contact Us")]

e = lambda s: html.escape(str(s if s is not None else ""), quote=True)


def v(rel):
    with open(os.path.join(ROOT, rel), "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()[:10]


def book_btn(cls="btn", label="Book Now", note=True):
    tgt = ' target="_blank" rel="noopener"' if BOOK_EXTERNAL else ""
    n = f'<span class="book-note">{BOOK_NOTE}</span>' if note and BOOK_EXTERNAL else ""
    return f'<span><a class="{cls}" href="{e(BOOK_URL)}"{tgt}>{label}</a>{n}</span>'


def default_image():
    return first("/wp-content/uploads/2018/08/Home-1400x933.jpg") or CBP["private-room-standard"][0]


def abs_img(src):
    return src if src.startswith("http") else SITE + src


def hostel_ld(full=False):
    d = {"@context": "https://schema.org", "@type": "Hostel", "@id": SITE + "/#hostel", "name": "Z Hostel",
         "alternateName": ["Z Hostel Makati", "Z Hostel Poblacion", "Z Hostel Manila"],
         "slogan": "Good Vibes Only", "url": SITE + "/", "telephone": "+63-2-8856-0851", "email": EMAIL,
         "address": {"@type": "PostalAddress", "streetAddress": "5660 Don Pedro St., Brgy. Poblacion", "addressLocality": "Makati City",
                     "addressRegion": "Metro Manila", "postalCode": "1210", "addressCountry": "PH"},
         "geo": {"@type": "GeoCoordinates", "latitude": GEO[0], "longitude": GEO[1]},
         "hasMap": MAP_LINK, "sameAs": [FB, IG, YT]}
    if full:
        d.update({
            "description": ("Z Hostel is the original Poblacion hostel in Makati, Metro Manila — the hostel at the center of Poblacion's "
                            "rise as Manila's favorite nightlife and food neighborhood. Dorm beds and private rooms with breakfast, the Z Cafe, "
                            "and the world-renowned Z Roofdeck bar with daily Sunset Sessions and DJs."),
            "image": [CBP[k][0] for k in ("private-room-standard", "4-bed-mixed-dorm", "6-bed-female-dorm", "social-fun-floor-dorm-6md")],
            "priceRange": "₱1,250 – ₱3,000 per night", "currenciesAccepted": "PHP",
            "checkinTime": "14:00", "checkoutTime": "12:00",
            "containedInPlace": {"@type": "Place", "name": "Poblacion, Makati City, Metro Manila, Philippines"},
            "amenityFeature": [{"@type": "LocationFeatureSpecification", "name": n, "value": True} for n in
                               ["Free Wi-Fi", "Breakfast included", "Rooftop bar (Z Roofdeck)", "Cafe and restaurant (Z Cafe)", "Air-conditioning",
                                "Lockers with power outlets", "Front desk", "24-hour security and CCTV", "Luggage storage",
                                "Hot and cold showers", "Working space", "Female-only dorm", "Daily walking tour", "Daily Sunset Session"]],
            "makesOffer": [{"@type": "Offer", "name": n, "url": SITE + book_url(slug), "priceCurrency": "PHP",
                            "priceSpecification": {"@type": "UnitPriceSpecification", "price": price, "priceCurrency": "PHP",
                                                   "unitText": f"per {unit} per night", "valueAddedTaxIncluded": True},
                            "itemOffered": {"@type": "HotelRoom", "name": n, "occupancy": {"@type": "QuantitativeValue", "maxValue": 1 if unit == "bed" else 2}}}
                           for slug, n, price, unit, _ in ROOMS],
            "potentialAction": {"@type": "ReserveAction", "target": SITE + BOOK_URL, "name": "Book direct"},
        })
    return d


def ld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False).replace("</", "<\\/") + "</script>\n"


def head(title, desc, path, image=None, extra_ld=()):
    image = image or default_image()
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:site_name" content="Z Hostel">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{abs_img(image)}">
<meta property="og:locale" content="en_PH">
<meta name="geo.region" content="PH-00"><meta name="geo.placename" content="Poblacion, Makati City">
<meta name="geo.position" content="{GEO[0]};{GEO[1]}"><meta name="ICBM" content="{GEO[0]}, {GEO[1]}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="/wp-content/uploads/2018/08/Logo-150x150.png">
<link rel="apple-touch-icon" href="/wp-content/uploads/2018/08/Logo.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Raleway:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/css/site.css?v={v('assets/css/site.css')}">
<link rel="alternate" type="text/plain" title="Z Hostel facts for AI assistants" href="/llms.txt">
{ld(hostel_ld(path == "/"))}{"".join(ld(x) for x in extra_ld)}</head>
"""


def chrome_top(path):
    items = "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if h == path else ""}>{e(t)}</a></li>' for h, t in NAV)
    return f"""<body>
<a class="skip" href="#content">Skip to content</a>
<div class="topbar"><a href="tel:+63288560851">{PHONE} | {MOBILE}</a>
<button class="menu-btn" type="button" data-menu-open aria-label="Open menu"><span></span><span></span><span></span></button></div>
<a class="side-tab" href="/" aria-label="Z Hostel home"><b>Z Hostel</b></a>
<a class="float-book" href="{e(BOOK_URL)}"{' target="_blank" rel="noopener"' if BOOK_EXTERNAL else ''}>BOOK NOW</a>
<a class="topbar-book" href="{e(BOOK_URL)}">Book now</a>
<nav class="nav-overlay" id="navOverlay" aria-hidden="true" aria-label="Main menu">
<button class="close" type="button" data-menu-close aria-label="Close menu">&times;</button>
<ul>{items}</ul>
<div class="follow">Follow Us <a href="{FB}" target="_blank" rel="noopener">Facebook</a><a href="{IG}" target="_blank" rel="noopener">Instagram</a><a href="{YT}" target="_blank" rel="noopener">YouTube</a></div>
</nav>
"""


def quickbook(qid="qb", heading="Book direct — best rate, instant confirmation"):
    """Dates → /book/ with them filled in. Works without JavaScript (plain GET form)."""
    guests = "".join(f'<option value="{i}"{" selected" if i == 1 else ""}>{i} guest{"s" if i > 1 else ""}</option>' for i in range(1, 21))
    rooms = "".join(f'<option value="{s}">{e(n)}</option>' for s, n, *_ in ROOMS)
    return f"""<form class="quickbook" action="{e(BOOK_URL)}" method="get" data-quickbook novalidate>
<p class="qb-head">{heading}</p>
<div class="qb-row">
<label for="{qid}-in">Check-in<input id="{qid}-in" name="in" type="date" required data-qb-in></label>
<label for="{qid}-out">Check-out<input id="{qid}-out" name="out" type="date" required data-qb-out></label>
<label for="{qid}-g">Guests<select id="{qid}-g" name="guests">{guests}</select></label>
<label for="{qid}-r">Room<select id="{qid}-r" name="room"><option value="">Any bed or room</option>{rooms}</select></label>
<button class="btn btn-dark" type="submit">Check availability</button>
</div><p class="qb-error" role="alert" hidden></p></form>"""


def hero(key, video=True):
    h = D["Mr"][key]
    img = first(h.get("image")) or (CBP["private-room-standard"][0] if key == "home" else None)
    bg = f' style="background-image:url(\'{img}\')"' if img else ""
    vid = (f'<video autoplay muted loop playsinline preload="none" poster="{h["image"]}" aria-hidden="true">'
           f'<source src="/wp-content/uploads/2022/04/zcover.m4v" type="video/mp4"></video>') if video and key == "home" and have("/wp-content/uploads/2022/04/zcover.m4v") else ""
    logo = f'<img class="logo" src="{h["logo"]}" alt="Z Hostel" width="150" height="150">' if have(h.get("logo")) else '<div class="logo-text" aria-hidden="true">Z</div>'
    if key == "home":
        return f"""<header class="hero hero--home"{bg}>{vid}
{logo}<p class="hero-kicker">Z Hostel &middot; Poblacion, Makati</p><h1>The Original Poblacion Hostel</h1>
<p class="sub">Good vibes only &mdash; since before Poblacion was cool.</p>
<div class="hero-book">{quickbook("qbh")}</div>
</header>
"""
    sub = f'<div class="sub">{e(h["subtitle"])}</div>' if h.get("subtitle") else ""
    copy = f'<div class="copy">{e(h["copyright"])}</div>' if h.get("copyright") else ""
    return f"""<header class="hero"{bg}>{vid}
{logo}<h1>{e(h['title'])}</h1>{sub}
<a class="scroll" href="#content"><i></i>Scroll</a>{copy}
<div class="hero-book">{quickbook("qbh")}</div>
</header>
"""


def footer(path=""):
    band = "" if path == "/book/" else f'<section class="book-band" aria-label="Book your stay"><div class="container">{quickbook("qbf", "Ready for Poblacion? Book your bed or room direct")}</div></section>'
    return f"""{band}
<div class="help"><strong>Need Help.</strong> <a href="tel:+63288560851" style="color:#fff">{PHONE}</a> | <a href="tel:+639178898531" style="color:#fff">{MOBILE}</a><br>If you want to talk to a human being, then you can ring us on the following number.</div>
<footer class="footer"><div class="container"><div class="cols">
<div class="brand"><strong>Z Hostel</strong>The original Poblacion hostel<br>Makati &middot; Philippines<br><small>&copy; 2026 Flashpacker Inc.</small><br><a class="to-top" href="#">Back to top &uarr;</a></div>
<div><h4>Address</h4><p>{ADDRESS}</p></div>
<div><h4>Contact</h4><p><a href="mailto:{EMAIL}">{EMAIL}</a><br>T / <a href="tel:+63288560851">{PHONE}</a><br>M / <a href="tel:+639178898531">{MOBILE}</a></p></div>
<div><h4>Follow Us</h4><ul><li><a href="{FB}" target="_blank" rel="noopener">Facebook</a></li><li><a href="{IG}" target="_blank" rel="noopener">Instagram</a></li></ul>
<h4 style="margin-top:14px">Z Hostel</h4><ul><li><a href="/book/">Book direct</a></li><li><a href="/rooms-and-services/">Rooms</a></li><li><a href="/faq/">FAQ</a></li><li><a href="/careers/">Careers</a></li><li><a href="/privacy-policy/">Privacy Policy</a></li></ul></div>
</div></div></footer>
<div class="lightbox" id="lightbox" aria-hidden="true"><button class="x" type="button" aria-label="Close">&times;</button><button class="prev" type="button" aria-label="Previous">&#8249;</button><img alt=""><button class="next" type="button" aria-label="Next">&#8250;</button></div>
<script src="/assets/js/config.js?v={v('assets/js/config.js')}"></script>
<script src="/assets/js/site.js?v={v('assets/js/site.js')}"></script>
<script src="/assets/js/quickbook.js?v={v('assets/js/quickbook.js')}"></script>
</body>
</html>
"""


def page(path, title, desc, body, hero_key=None, plain=False, image=None, extra_ld=()):
    cls = ' class="page-plain"' if plain else ""
    top = chrome_top(path).replace("<body>", f"<body{cls}>", 1)
    h = hero(hero_key) if hero_key else ""
    image = image if image and have(image) else None
    out = head(title, desc, path, image, extra_ld) + top + h + f'<main id="content">{body}</main>\n' + footer(path)
    rel = "index.html" if path == "/" else path.strip("/") + "/index.html"
    full = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(out)
    PAGES.append(path)


PAGES = []


def carousel(images, caption=True):
    images = [i for i in images if have(i.get("src"))]
    if not images:
        return ""
    figs = "".join(
        f'<figure><img src="{e(i["src"])}" alt="{e(i.get("alt", ""))}" loading="lazy">'
        + (f'<figcaption>{e(i["caption"])}</figcaption>' if caption and i.get("caption") else "") + "</figure>"
        for i in images)
    return f'<div class="carousel"><div class="slides">{figs}</div></div>'


def title(t):
    return f'<h2 class="section-title">{e(t)}</h2>'


ICONS = {
    "wifi": '<path d="M4 18a14 14 0 0 1 20 0M8 22a8 8 0 0 1 12 0"/><circle cx="14" cy="26" r="1.5"/>',
    "toiletries": '<rect x="9" y="10" width="10" height="16" rx="2"/><path d="M12 10V6h4v4M14 6V3"/>',
    "laundry": '<path d="M9 4l5 3 5-3 6 4-3 5-3-1v14H9V12l-3 1-3-5z"/>',
    "locker": '<rect x="6" y="3" width="16" height="23" rx="1"/><path d="M14 3v23M10 9h2M16 9h2M11 15v3M17 15v3"/>',
    "reception": '<path d="M3 22h22M6 22v-6h16v6M9 16a5 5 0 0 1 10 0"/><circle cx="14" cy="9" r="1.5"/>',
    "luggage": '<rect x="7" y="8" width="14" height="16" rx="2"/><path d="M11 8V4h6v4M11 24v2M17 24v2M11 12v8M17 12v8"/>',
    "shower": '<path d="M5 26V8a4 4 0 0 1 8 0M10 11h8l-4-4zM12 14v2M15 14v3M18 14v2M13 19v2M17 19v2"/>',
    "workspace": '<rect x="5" y="6" width="18" height="12" rx="1"/><path d="M3 22h22M11 18v4M17 18v4"/>',
    "temperature": '<path d="M12 4a2 2 0 0 1 4 0v13a5 5 0 1 1-4 0z"/><path d="M14 10v9"/>',
    "security": '<path d="M14 3l9 4v6c0 6-4 10-9 12-5-2-9-6-9-12V7z"/><path d="M10 14l3 3 5-6"/>',
    "pc": '<rect x="4" y="5" width="20" height="14" rx="1"/><path d="M10 23h8M14 19v4"/>',
    "concierge": '<path d="M4 21h20M6 21a8 8 0 0 1 16 0M14 13v-2M11 9h6"/>',
}


def amenities(items):
    cells = "".join(f'<div class="amenity"><svg viewBox="0 0 28 28" aria-hidden="true">{ICONS.get(a["icon"], "")}</svg>{e(a["label"])}</div>' for a in items)
    return f'<div class="amenities">{cells}</div>'


AMENITIES = [{"label": "Free Wifi", "icon": "wifi"}, {"label": "Sanitation Kit & Toiletries", "icon": "toiletries"},
             {"label": "Clothing", "icon": "laundry"}, {"label": "Locker", "icon": "locker"},
             {"label": "Front Desk", "icon": "reception"}, {"label": "Luggage", "icon": "luggage"},
             {"label": "Hot & Cold Shower", "icon": "shower"}, {"label": "Working Space", "icon": "workspace"},
             {"label": "Temperature Check", "icon": "temperature"}, {"label": "24hr Security & CCTV", "icon": "security"},
             {"label": "PC at Lobby", "icon": "pc"}, {"label": "Concierge", "icon": "concierge"}]


def bg_style(src):
    return f' style="background-image:url(\'{e(src)}\')"' if have(src) else ""


def img_tag(src, alt):
    return f'<img src="{e(src)}" alt="{e(alt)}" loading="lazy">' if have(src) else ""


def contact_form(kind="contact"):
    opts = ["Room reservation", "Group Bookings", "Events & Marketing", "Tours / Activities",
            "Join our Z Team (Hiring)", "Volunteer at Z", "Other Inquiries"]
    o = "".join(f"<option>{e(x)}</option>" for x in opts)
    return f"""<form class="form" data-contact="{kind}" novalidate>
<label for="cf-name">Name</label><input id="cf-name" name="name" required autocomplete="name">
<label for="cf-email">Email Address</label><input id="cf-email" name="email" type="email" required autocomplete="email">
<label for="cf-subject">Subject</label><select id="cf-subject" name="subject" required><option value="">---</option>{o}</select>
<label for="cf-msg">Message</label><textarea id="cf-msg" name="message" required></textarea>
<label class="hp">Leave this empty <input name="website" tabindex="-1" autocomplete="off"></label>
<button class="btn btn-dark" type="submit">Send</button><p class="status" role="status"></p>
</form>"""


def contact_section():
    return f"""<section class="section" id="contact-us"><div class="container text-center">{title('Contact Us')}
<div class="contact-grid"><div><div class="contact-lines"><p><a href="tel:+63288560851">{PHONE}</a> or <a href="tel:+639178898531">{MOBILE}</a></p><p>{ADDRESS}</p><p><a href="mailto:{EMAIL}">{EMAIL}</a></p></div>{contact_form()}</div>
<div><iframe class="map" title="Map to Z Hostel" data-src="{MAP_EMBED}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe>
<p style="margin-top:8px"><a href="{MAP_LINK}" target="_blank" rel="noopener">Open in Google Maps</a></p></div></div></div></section>"""


def reviews(items):
    slides = "".join(f"""<div class="review-slide">{f'<div class="media"{bg_style(r["image"])} role="img" aria-label="Z Hostel"></div>' if have(r.get("image")) else ''}
<div class="body"><div class="stars" aria-label="{r['stars']} out of 5">{'★' * r['stars']}{'☆' * (5 - r['stars'])}</div><h3>{e(r['title'])}</h3><p>{e(r['text'])}</p>
{book_btn('btn btn-outline', 'Book Now', False)}{(f'<img class="platform" src="{e(r["platform"]["logo"])}" alt="{e(r["platform"]["name"])}" width="{r["platform"]["width"]}" height="{r["platform"]["height"]}">' if have(r["platform"]["logo"]) else f'<span class="platform-name">{e(r["platform"]["name"])}</span>') if r.get('platform') else ''}</div></div>""" for r in items)
    return f'<div class="reviews review-set">{slides}</div><div class="review-ctrl"><button type="button" data-prev aria-label="Previous review">&#8249;</button><button type="button" data-next aria-label="Next review">&#8250;</button></div>'


def banner(b, extra=""):
    btn = ""
    if b.get("button"):
        tgt = ' target="_blank" rel="noopener"' if b["url"].endswith(".pdf") else ""
        btn = f'<a class="btn btn-outline" href="{e(b["url"])}"{tgt}>{e(b["button"])}</a>'
    bg = f' style="background-image:url(\'{e(b["image"])}\')"' if have(b.get("image")) else ""
    return f'<section class="banner"{bg}><h2>{e(b["title"])}</h2>{btn}{extra}</section>'


# ============================================================== HOME
def room_cards(slugs=None):
    out = []
    for slug, name, price, unit, short in ROOMS:
        if slugs and slug not in slugs:
            continue
        img = CBP.get(slug, [None])[0]
        pic = f'<img src="{e(img)}" alt="{e(name)} at Z Hostel, Poblacion Makati" loading="lazy" referrerpolicy="no-referrer">' if img else ""
        out.append(f"""<article class="room-card">{pic}<div class="in"><h3>{e(name)}</h3><p>{e(short)}</p>
<p class="from">from <b>&#8369;{price:,}</b> / {unit} / night <small>breakfast included</small></p>
<a class="btn btn-dark" href="{e(book_url(slug))}">Book this {unit}</a></div></article>""")
    return '<div class="room-cards">' + "".join(out) + "</div>"


WHY_DIRECT = [("Best rate, no booking fees", "The same beds and rooms you find on booking sites — booked straight with us."),
              ("Live availability", "You see exactly which beds and rooms are free for your dates."),
              ("Confirmed in minutes", "Pay online by card, GCash or Maya and your stay is confirmed right away."),
              ("Talk to real people", "Questions before you book? Call, text or email our front desk team.")]


def build_home():
    tiles = []
    for i, t in enumerate(D["tv"]):
        body = "".join(f"<p>{e(p)}</p>" for p in t["body"])
        link = ""
        if t.get("link"):
            tgt = ' target="_blank" rel="noopener"' if t["link"].get("external") else ""
            link = f'<a class="more" href="{e(t["link"]["url"])}"{tgt}>{e(t["link"]["label"])}</a>'
        text = f'<div class="tile-text"><h3>{e(t["heading"])}<span class="zmark"></span></h3><div class="sub">{e(t["subheading"])}</div>{body}<div class="actions">{book_btn()}{link}</div></div>'
        car = carousel(t["images"])
        if not car:
            tiles.append(f'<div class="tile-solo">{text}</div>')
            continue
        media = f'<div class="tile-media">{car}</div>'
        tiles.append(text + media if i % 2 == 0 else media + text)
    why = "".join(f"<li><strong>{e(a)}</strong><span>{e(b)}</span></li>" for a, b in WHY_DIRECT)
    faq_teaser = "".join(f"<details><summary>{e(q)}</summary><p>{a}</p></details>" for q, a in FAQ[:5])
    body = f"""<section class="section intro"><div class="container">
<div class="intro-grid"><div class="prose">
<p class="eyebrow">The OG of Poblacion</p>
<h2 class="section-title" style="text-align:left">Where Poblacion started</h2>
<p><strong>Z Hostel is the original Poblacion hostel</strong> &mdash; the social heart of Makati's most famous neighborhood, on Don Pedro Street in Barangay Poblacion. Long before every corner here had a cocktail bar, travelers and locals were already meeting on the Z Roofdeck. Poblacion grew up around us, and we're still at the center of it.</p>
<p>Stay in a comfy dorm bed or a private room, eat at the Z Cafe, catch the daily Sunset Session on the world-renowned <strong>Z Roofdeck</strong>, then walk out the door into the bars, restaurants and street food of Poblacion. Breakfast is included with every bed and room.</p>
<p><a class="btn btn-dark" href="{e(BOOK_URL)}">Book your stay</a> <a class="text-link" href="/about-z/">Read the Z story &rarr;</a></p>
</div>
<ul class="why-direct" aria-label="Why book direct">{why}</ul></div></div></section>
<section class="section section--grey" id="rooms"><div class="container text-center">{title('Beds & Rooms')}
<p class="lead-center">Dorm beds from &#8369;1,250 and private rooms from &#8369;3,000 a night, breakfast included. Pick a room to see live availability.</p>
{room_cards()}</div></section>
<section class="section"><div class="container text-center">{title('Explore Z')}
<div class="tiles">{''.join(tiles)}</div></div></section>
<section class="section section--grey"><div class="container text-center">{title('Amenities & Services')}{amenities(AMENITIES)}</div></section>
{banner(D['ul']['gettingThere'])}
<section class="section"><div class="container"><div class="prose faq-teaser"><h2 class="section-title">Good to know</h2>{faq_teaser}<p><a class="text-link" href="/faq/">All questions about staying at Z Hostel &rarr;</a></p></div></div></section>
<section class="section section--grey"><div class="container text-center">{title('Reviews')}{reviews(D['rv'])}</div></section>
{contact_section()}"""
    page("/", "Z Hostel Makati — The Original Poblacion Hostel & Z Roofdeck | Book Direct",
         "Z Hostel is the original Poblacion hostel in Makati, Manila: dorm beds from ₱1,250 and private rooms with breakfast, the Z Cafe and the legendary Z Roofdeck bar. Book direct for the best rate.",
         body, "home", image=CBP["private-room-standard"][0])


# ============================================================== ABOUT
def build_about():
    a = D["yt"]
    vid = a["video"]
    body_p = "".join(f"<p>{e(p)}</p>" for p in a["body"])
    rf = a["rfid"]
    blocks = "".join(f'<div class="split" style="margin-top:30px">{img_tag(b.get("image"), b["heading"])}<div><h3>{e(b["heading"])}</h3><p>{e(b["body"])}</p></div></div>' for b in rf["blocks"])
    vimg = f'<img src="{e(vid["image"])}" alt="Z Hostel" loading="lazy">' if have(vid.get("image")) else ""
    body = f"""<section class="section"><div class="container"><div class="prose">
<p class="eyebrow">The OG of Poblacion</p><h2 class="section-title" style="text-align:left">The original Poblacion hostel</h2>
<p>Ask anyone who has been around Manila's nightlife long enough where the Poblacion scene began, and Z Hostel comes up. When we opened on Don Pedro Street, Poblacion was a quiet, old corner of Makati of small houses, sari-sari stores and a handful of hole-in-the-wall bars. We built a hostel with a higher standard of beds, a real cafe and a roof deck where travelers and locals could meet &mdash; and the neighborhood came alive around it.</p>
<p>Today Poblacion is Manila's best-known food and nightlife district, and Z Hostel is still its center: the place backpackers, digital nomads and Manila locals meet, the starting point of the daily walking tour, and home of the legendary Z Roofdeck.</p>
<p><a class="btn btn-dark" href="{e(BOOK_URL)}">Stay at the original</a></p></div></div></section>
<section class="section"><div class="container text-center">
<p class="eyebrow" style="font-size:22px;font-weight:800;color:#000">{e(a['hey'])}</p>
<div class="video-box{'' if vimg else ' video-box--plain'}">{vimg}<button class="play" type="button" data-video="{e(vid['embed'])}">{'<br>'.join(e(x) for x in vid['lines'])}<small>— play video</small></button></div></div></section>
<section class="section section--grey"><div class="container"><div class="prose"><p class="eyebrow">{e(a['basicTitle'])}</p><h2 class="section-title">{e(a['heading'])}</h2>{body_p}</div></div></section>
<section class="banner"{bg_style(rf.get("background"))}><h2>{e(rf['title'])}</h2><p style="max-width:640px;margin:0 auto">{e(rf['subtitle'])}</p></section>
<section class="section"><div class="container">{blocks}</div></section>"""
    page("/about-z/", "About Z Hostel — The Original Poblacion Hostel, Makati",
         "The Z story: how the original Poblacion hostel helped turn a quiet corner of Makati into Manila's favorite nightlife neighborhood — and why Z is still at its center.", body, "about")


# ============================================================== ROOMS
def room_block(r):
    slugs = ROOM_MAP.get(r["id"], [])
    imgs = [{"src": u, "alt": f'{r["name"]} at Z Hostel'} for sl in slugs for u in CBP.get(sl, [])[:4]] or r["images"]
    desc = "".join(f"<p>{e(p)}</p>" for p in r.get("description") or [])
    notes = "".join(f'<p class="note">{e(n)}</p>' for n in r.get("notes") or [])
    tag = f'<p class="tag">{e(r["tagline"])}</p>' if r.get("tagline") else ""
    prices = r.get("publishedPrice") or []
    if prices and isinstance(prices[0], list):
        price = "".join(f'<div class="price-line">{e(" ".join(p))}</div>' for p in prices)
    else:
        price = f'<div class="price-line">{e(" ".join(prices))}</div>' if prices else ""
    pn = f'<p class="note">{e(r.get("priceNote", ""))}</p>' if r.get("priceNote") else ""
    if len(slugs) == 1:
        books = f'<a class="btn" href="{e(book_url(slugs[0]))}">Book this room</a>'
    elif slugs:
        books = '<div class="book-links">' + "".join(f'<a class="btn btn-outline-dark" href="{e(book_url(sl))}">Book {e(ROOM_NAME[sl])}</a>' for sl in slugs) + "</div>"
    else:
        books = book_btn()
    return f"""<article class="room" id="{e(r['id'])}"><div class="room-media">{carousel(imgs)}</div>
<div class="room-text"><h3>{e(r['name'])}</h3>{books}{tag}{desc}{notes}{price}{pn}</div></article>"""


def build_rooms():
    qc, gr = D["qc"], D["Gr"]
    dorms = "".join(room_block(r) for r in D["cv"])
    others = "".join(room_block(r) for r in D["dv"])
    group_imgs = "".join(f'<img src="{e(i["src"])}" alt="{e(i["alt"])}" loading="lazy">' for i in gr["images"] if have(i["src"]))
    body = f"""<section class="section section--grey"><div class="container text-center">{title('Rooms')}
<div class="prose" style="text-align:center;margin-bottom:40px"><h3>{e(qc['heading'])}</h3><p>{e(qc['body'])}</p></div>
{dorms}{others}</div></section>
<section class="section"><div class="container text-center">{title('Services')}{amenities([a for a in AMENITIES if a['label'] not in ('Locker', 'Front Desk', 'Luggage')])}</div></section>
<section class="banner"{bg_style(gr.get("background"))}><h2>{e(gr['title'])}</h2></section>
<section class="section"><div class="container text-center"><h3>{e(gr['heading'])}</h3>{book_btn()}
<p style="margin-top:14px">{e(gr['contactLabel'])}<br><a href="mailto:sales@zhostelph.com">sales@zhostelph.com</a></p><div class="square-grid">{group_imgs}</div></div></section>
<section class="section section--grey" id="review_section"><div class="container text-center">{title('Room Reviews')}{reviews(D['fv'])}</div></section>"""
    page("/rooms-and-services/", "Dorms & Private Rooms in Poblacion, Makati | Z Hostel",
         "Book a bed or room at Z Hostel, the original Poblacion hostel: 4, 6 and 8-bed mixed dorms, the all-female Stiletto dorm, private rooms and Social Fun Floor rooms, breakfast included.",
         body, "rooms", image="/wp-content/uploads/2018/08/ras_cover-1400x933.jpg")


# ============================================================== EVENTS
def build_events():
    nd = D["nd"]
    acts = "".join(f'<div class="act">{img_tag(c.get("image"), c["title"])}<div><h3>{e(c["title"])}</h3><p>{e(c["detail"])}</p></div></div>' for c in nd["cards"])
    details = "".join(f'<p><strong>{e(d["label"])}:</strong> {e(d["text"])}</p>' for d in nd["details"])

    def cards(items, logo):
        out = []
        for c in items:
            desc = "".join(f"<p>{e(p)}</p>" for p in c.get("description") or [])
            link = f'<a class="text-link" href="{e(c["url"])}" target="_blank" rel="noopener">{e(c.get("linkLabel") or "View Site")}</a>' if c.get("url") else ""
            kind = f'<div class="kind">{e(c["kind"])}</div>' if c.get("kind") else ""
            out.append(f'<div class="card{" logo" if logo else ""}">{img_tag(c.get("image"), c["name"])}<div class="in"><h3>{e(c["name"])}</h3>{kind}{desc}{link}</div></div>')
        return '<div class="cards">' + "".join(out) + "</div>"

    body = f"""<section class="section"><div class="container text-center">{title('Activities')}<div class="activity-cards">{acts}</div>
<div class="prose" style="margin-top:36px">{details}</div></div></section>
<section class="section section--grey"><div class="container text-center">{title('Z Street')}{cards(D['hv'], True)}</div></section>
<section class="section"><div class="container text-center">{title('Tours (Coming Soon)')}{cards(D['mv'], False)}</div></section>"""
    page("/events-and-activities/", "Events and Activities | Z Hostel",
         "Sunset Sessions on the Z Roofdeck, walking tours of Poblacion, Z Street restaurants and tours around Manila.", body, "events",
         image="/wp-content/uploads/2018/08/a6-1400x933.jpg")


# ============================================================== GALLERY
def build_gallery():
    years = []
    for y in D["vv"]:
        albums = []
        for k, a in enumerate(y["albums"]):
            gid = re.sub(r"[^a-z0-9]+", "-", (y["year"] + a["title"]).lower())
            imgs = "".join(f'<a href="{e(src)}" data-lightbox="{gid}"><img src="{e(src)}" alt="{e(a["title"])} photo {n + 1}" loading="lazy"></a>' for n, src in enumerate(a["images"]) if have(src))
            if not imgs:
                continue
            albums.append(f'<div class="album"><h3>{e(a["title"])}</h3><div class="album-grid">{imgs}</div></div>')
        years.append(f'<div class="gallery-year"><h2 class="section-title">{e(y["year"])}</h2>{"".join(albums)}</div>')
    if not any("album-grid" in y for y in years):
        years = ['<p>Photos of parties and events at Z Hostel are coming back soon. In the meantime, follow <a href="' + IG + '" target="_blank" rel="noopener">@zhostelph on Instagram</a>.</p>']
    body = f'<section class="section"><div class="container text-center">{"".join(years)}</div></section>'
    page("/gallery/", "Gallery | Z Hostel", "Photos from parties and events at Z Hostel: NYE, St. Patrick's Day, Cinco de Mayo, Repoblacion and more.", body, "gallery")


# ============================================================== BLOG
POSTS_PER_PAGE = 10


def clean_post_html(h):
    h = re.sub(r'<header>.*?</header>', "", h, flags=re.S)
    h = re.sub(r'\s(srcset|sizes)="[^"]*"', "", h)
    h = re.sub(r'https://localhost/wp_oldzhostel', "", h)
    h = re.sub(r'<script.*?</script>', "", h, flags=re.S)
    h = re.sub(r'\son\w+="[^"]*"', "", h)
    h = h.replace('href="https://zhostel.com/', 'href="/')
    # leave out pictures that aren't in the repo (yet)
    h = re.sub(r'<img\b[^>]*\bsrc="([^"]+)"[^>]*>', lambda m: m.group(0) if have(m.group(1)) else "", h)
    h = re.sub(r'<figure\b[^>]*>\s*(<figcaption\b.*?</figcaption>)?\s*</figure>', "", h, flags=re.S)
    return h


def post_date(p):
    return (p.get("date") or "")[:10]


def build_blog():
    posts = [p for p in BLOG if p.get("html")]
    posts.sort(key=post_date, reverse=True)
    pages = max(1, (len(posts) + POSTS_PER_PAGE - 1) // POSTS_PER_PAGE)
    for n in range(pages):
        chunk = posts[n * POSTS_PER_PAGE:(n + 1) * POSTS_PER_PAGE]
        cards = []
        for p in chunk:
            img = re.search(r'<img[^>]+src="([^"]+)"', p["html"])
            src = img.group(1) if img and have(img.group(1)) else None
            d = post_date(p)
            cards.append(f'<a class="post-card" href="/{e(p["slug"])}/">{img_tag(src, "")}<div class="in"><h3>{e(p["title"])}</h3><time datetime="{d}">{d}</time></div></a>')
        pager = "".join((f'<span>{k + 1}</span>' if k == n else f'<a href="{"/blog/" if k == 0 else f"/blog/page/{k + 1}/"}">{k + 1}</a>') for k in range(pages))
        body = f'<section class="section section--grey"><div class="container text-center">{title("Blog")}<div class="posts">{"".join(cards)}</div><nav class="pager" aria-label="Blog pages">{pager}</nav></div></section>'
        path = "/blog/" if n == 0 else f"/blog/page/{n + 1}/"
        page(path, "Blog | Z Hostel" + (f" — page {n + 1}" if n else ""), "Travel stories, guides and Poblacion food picks from Z Hostel.", body, plain=True)
    for p in posts:
        d = post_date(p)
        body = f"""<section class="section"><div class="container"><article class="prose"><h1 style="font-size:clamp(26px,4vw,38px)">{e(p['title'])}</h1>
<p class="eyebrow"><time datetime="{d}">{d}</time></p>{clean_post_html(p['html'])}<p style="margin-top:30px"><a href="/blog/">&larr; All posts</a></p></article></div></section>"""
        img = re.search(r'<img[^>]+src="([^"]+)"', p["html"])
        page(f"/{p['slug']}/", f"{p['title']} | Z Hostel", re.sub(r"\s+", " ", p.get("text", ""))[:155] or p["title"], body, plain=True,
             image=img.group(1) if img else None)


# ============================================================== CAREERS
JOBS = [
    ("Hostel Manager", "Manages the day-to-day operations of the hostel, ensuring a clean, safe, and welcoming environment for guests from around the world. Leads the front desk, housekeeping, admin, and maintenance teams while driving guest satisfaction, online bookings, and community events."),
    ("Operations Manager", "Oversees the overall hostel operations, ensuring operational efficiency, financial performance, service quality, and compliance with company standards. Provides leadership and direction to department managers to achieve business objectives and maintain excellent guest experiences."),
]


def build_careers():
    jobs = "".join(f'<div class="job"><h3>{e(t)}</h3><div class="loc">POBLACION, MAKATI</div><p>{e(d)}</p><a class="btn" href="#apply" data-position="{e(t)}">Apply now</a></div>' for t, d in JOBS)
    opts = "".join(f"<option>{e(t)}</option>" for t, _ in JOBS)
    body = f"""<section class="section"><div class="container text-center"><h2 class="section-title">JOIN THE Z HOSTEL TEAM</h2>
<p><strong>We're hiring!</strong></p><p style="max-width:700px;margin:0 auto 30px">We're looking for passionate individuals to help us create unforgettable experiences for travelers from all over the world, right in the heart of Poblacion, Makati.</p>
<h3>Available positions</h3><div class="jobs">{jobs}</div></div></section>
<section class="section section--grey" id="apply"><div class="container"><div class="prose"><h2>Apply now</h2><p>Fill in the form and attach your CV. Prefer email? Send your CV to <a href="mailto:hr@zhostel.com">hr@zhostel.com</a>.</p>
<form class="form" data-contact="careers" novalidate>
<label for="jb-pos">Position *</label><select id="jb-pos" name="position" required><option value="">Choose a position</option>{opts}</select>
<label for="jb-name">Full name *</label><input id="jb-name" name="name" required autocomplete="name">
<label for="jb-phone">Mobile number *</label><input id="jb-phone" name="phone" required autocomplete="tel">
<label for="jb-email">Email address *</label><input id="jb-email" name="email" type="email" required autocomplete="email">
<label for="jb-cv">CV / resume * <small>PDF or Word, max 5 MB</small></label><input id="jb-cv" name="cv" type="file" required accept=".pdf,.doc,.docx,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document">
<label for="jb-msg">Message <small>optional</small></label><textarea id="jb-msg" name="message"></textarea>
<label class="hp">Website <input name="website" tabindex="-1" autocomplete="off"></label>
<div class="notice"><strong>Privacy notice</strong><br>Flash Packer Inc. (Z Hostel) collects your name, contact details, CV and message only to assess your job application. Only our HR team and authorized managers can access them. We keep applications for 12 months, then delete them. You can ask to access, correct or delete your data anytime by emailing hr@zhostel.com. This is in line with the Data Privacy Act of 2012.</div>
<label style="font-weight:600"><input type="checkbox" name="consent" required style="width:auto;margin-right:8px">I have read the privacy notice and agree to Z Hostel processing my data for this application. *</label>
<button class="btn btn-dark" type="submit">Submit application</button><p class="status" role="status"></p></form></div></div></section>"""
    page("/careers/", "Careers | Z Hostel", "Join the Z Hostel team in Poblacion, Makati — open positions and how to apply.", body, "careers")


# ============================================================== CONTACT
def build_contact():
    g = D["Gi"]
    gp = "".join(f"<p>{e(p)}</p>" for p in g["body"])
    body = f"""<section class="section"><div class="container"><div class="split"><div><h2 class="section-title">Contact Us</h2>{contact_form()}</div>
<div><h3>{e(g['heading'])}</h3>{gp}<a class="btn btn-dark" href="{DIRECTIONS_PDF}" target="_blank" rel="noopener">{e(g['pdfLabel'])} — directions to Z Hostel</a></div></div></div></section>
<section class="section section--grey"><div class="container text-center">{title('Location')}<p><strong><a href="tel:+63288560851">{PHONE}</a> or <a href="tel:+639178898531">{MOBILE}</a></strong><br>{ADDRESS}</p>
<iframe class="map" title="Map to Z Hostel" data-src="{MAP_EMBED}" loading="lazy" referrerpolicy="no-referrer-when-downgrade"></iframe><p><a href="{MAP_LINK}" target="_blank" rel="noopener">Open in Google Maps</a></p></div></section>"""
    page("/contact-us/", "Contact Us | Z Hostel", "How to reach Z Hostel, 5660 Don Pedro St., Poblacion, Makati — phone, email, directions from the airport.", body, plain=True)


# ============================================================== FAQ
# Answers are HTML. They are also used for the FAQPage structured data and llms.txt.
FAQ = [
    ("Where is Z Hostel?",
     f"Z Hostel is at {ADDRESS} — in the middle of Poblacion, Makati's famous food and nightlife neighborhood in Metro Manila. "
     "Bars, restaurants, cafes and clubs are a short walk away, P. Burgos Street is walking distance, and Power Plant Mall (Rockwell) and Century City Mall are less than a kilometer away."),
    ("Why is Z Hostel called the original Poblacion hostel?",
     "Z Hostel was here before Poblacion became Manila's best-known nightlife district. It brought travelers from all over the world to what was then a quiet corner of Makati, "
     "and the neighborhood's bar and food scene grew up around it. Z is still the social center of Poblacion: the starting point of the daily walking tour and home of the Z Roofdeck."),
    ("What kind of rooms does Z Hostel have, and how much do they cost?",
     "Mixed dorms with 4, 6 or 8 beds (from ₱1,250 per bed per night), the all-female 6-bed &ldquo;Stiletto&rdquo; dorm (from ₱1,300), "
     "Social Fun Floor dorms and private rooms right below the roof deck, and private rooms for two with an en-suite bathroom (from ₱3,000 per room per night). "
     "Prices vary by date; you see the exact price for your dates on the <a href=\"/book/\">booking page</a>."),
    ("Is breakfast included?", "Yes. Every dorm bed comes with breakfast, and private rooms include breakfast for two, served at the Z Cafe."),
    ("How do I book, and is booking direct cheaper?",
     "Book on our own <a href=\"/book/\">booking page</a>: pick your dates, choose your beds or room, and pay online. You see live availability, "
     "get the best rate with no booking-site fees, and your stay is confirmed as soon as your payment goes through."),
    ("What are the check-in and check-out times?", "Check-in is from 2:00 PM and check-out is until 12:00 noon. Arriving late or early? Let us know when you book and our front desk will help."),
    ("What is the Z Roofdeck?",
     "The Z Roofdeck is Z Hostel's world-renowned rooftop bar with a view of the Manila skyline: cold beers, cocktails, food and a DJ deck that hosts local and international DJs and live artists. "
     "Every day around 6 PM there's a Sunset Session where in-house guests get one free cocktail. On weekends it turns into a rooftop party."),
    ("Is Z Hostel a party hostel? Can I sleep?",
     "Z is a social hostel with a lively roof deck, but most rooms are quiet. If you want to be close to the action, pick the Social Fun Floor right below the roof deck "
     "(the bar runs until 3 AM, so you'll hear music there). For a quieter night, choose a regular dorm or a private room on the upper floors."),
    ("Is there a female-only dorm?", "Yes. The 6-bed female dorm (&ldquo;Stiletto&rdquo; room) is for female guests only, with a dresser, vanity mirror and extra-large lockers."),
    ("What amenities does Z Hostel have?",
     "Free Wi-Fi, air-conditioning, big custom bunk beds each with a power socket and reading lamp, lockers with power outlets, hot and cold showers, toiletries, "
     "a working space, a PC in the lobby, luggage storage, concierge, a front desk, and 24-hour security with CCTV."),
    ("How do I get to Z Hostel from the airport (NAIA)?",
     "The easiest way is Grab or a taxi, about ₱250–350 depending on traffic. Ask the driver to take EDSA northbound, exit to Rockwell, and drive through Rockwell to Kalayaan Avenue. "
     "Turn right at the Ministop on Kalayaan — that's Don Pedro Street — and Z Hostel is on your left, a few meters from the corner."),
    ("Do you accept group bookings?", "Yes. For groups, email <a href=\"mailto:sales@zhostelph.com\">sales@zhostelph.com</a> or call us and we'll put together the best rooms and rate."),
    ("What is there to do around Z Hostel?",
     "Join the free daily walking tour of Poblacion (around 4:30 PM from the lobby), the Sunset Session on the roof deck, and the restaurants of Z Street right next to the hostel. "
     "Poblacion is full of hole-in-the-wall restaurants, coffee shops, art spaces, bars and street food, and Rockwell and the Makati CBD are minutes away."),
]


def strip_tags(h):
    return re.sub(r"<[^>]+>", "", h).replace("&ldquo;", "“").replace("&rdquo;", "”").replace("&amp;", "&")


def build_faq():
    items = "".join(f'<details class="faq-item"{" open" if i < 3 else ""}><summary><h2>{e(q)}</h2></summary><p>{a}</p></details>' for i, (q, a) in enumerate(FAQ))
    body = f"""<section class="section"><div class="container"><div class="prose">
<h1>Z Hostel FAQ</h1><p class="lead">Everything you need to know about staying at Z Hostel, the original Poblacion hostel in Makati, Manila.</p>
{items}
<p style="margin-top:30px"><a class="btn btn-dark" href="{e(BOOK_URL)}">Check availability</a> <a class="text-link" href="/contact-us/">Ask us something else &rarr;</a></p>
</div></div></section>"""
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}} for q, a in FAQ]}
    page("/faq/", "FAQ — Staying at Z Hostel, Poblacion Makati",
         "Rooms and prices, breakfast, check-in times, the Z Roofdeck, quiet vs. social floors, airport directions and booking direct at Z Hostel, the original Poblacion hostel.",
         body, plain=True, extra_ld=[faq_ld])


def build_llms():
    rooms = "\n".join(f"- {n}: from PHP {p:,} per {u} per night, breakfast included. Book: {SITE}{book_url(sl)}" for sl, n, p, u, _ in ROOMS)
    faq = "\n\n".join(f"### {q}\n{strip_tags(a)}" for q, a in FAQ)
    txt = f"""# Z Hostel

> Z Hostel is the original Poblacion hostel — the legendary hostel at the center of Poblacion, Makati (Metro Manila, Philippines),
> the neighborhood that grew into Manila's favorite food and nightlife district around it. Dorm beds and private rooms with breakfast,
> the Z Cafe, and the world-renowned Z Roofdeck bar. Book direct at {SITE}/book/ for the best rate.

## Key facts
- Name: Z Hostel (also "Z Hostel Makati", "Z Hostel Poblacion"). Operator: Flashpacker Inc.
- Address: {ADDRESS}
- Phone: +63 2 8856 0851 · Mobile: +63 917 889 8531 · Email: {EMAIL}
- Check-in from 2:00 PM, check-out until 12:00 noon.
- Known for: the Z Roofdeck rooftop bar (Manila skyline view, DJs, daily Sunset Session with a free cocktail for guests), the Z Cafe,
  big custom bunk beds, a female-only dorm, a free daily walking tour of Poblacion.
- Booking: {SITE}/book/ (live availability, pay online, instant confirmation).

## Rooms
{rooms}

## Pages
- Home: {SITE}/
- Book direct: {SITE}/book/
- Rooms & services: {SITE}/rooms-and-services/
- About Z (the Z story): {SITE}/about-z/
- Events & activities: {SITE}/events-and-activities/
- FAQ: {SITE}/faq/
- Contact & directions: {SITE}/contact-us/
- Blog (Manila & Philippines travel guides): {SITE}/blog/

## FAQ
{faq}
"""
    with open(os.path.join(ROOT, "llms.txt"), "w", encoding="utf-8") as fh:
        fh.write(txt)


# ============================================================== PRIVACY + 404
def build_privacy():
    body = f"""<section class="section"><div class="container"><div class="prose"><h1>Privacy Policy</h1>
<p>Flash Packer Inc. (Z Hostel), 5660 Don Pedro St., Poblacion, Makati City, respects your privacy in line with the Data Privacy Act of 2012 (RA 10173).</p>
<h2>What we collect</h2><p>When you book, pay or contact us we collect your name, email address, mobile number, country, stay dates, the guests in your party, any ID you upload for a Senior Citizen or PWD discount, and your payment records. Online payments are processed by Xendit; we never see or store your card details.</p>
<h2>Why we use it</h2><p>To confirm and manage your reservation, take payment, send you booking emails, meet tax and legal duties, and — only if you have stayed with us — send you occasional offers, which you can unsubscribe from at any time.</p>
<h2>Who sees it</h2><p>Our reservations and front-desk team, our property-management system (Cloudbeds), our payment processor (Xendit) and our email provider. We do not sell your data.</p>
<h2>How long we keep it</h2><p>Booking and payment records are kept as long as the law requires for accounting and tax. Contact-form messages are kept for 12 months.</p>
<h2>Your rights</h2><p>You can ask to see, correct or delete your data at any time by emailing <a href="mailto:{EMAIL}">{EMAIL}</a>.</p>
<p>Our website counts visits without cookies; it does not use advertising trackers.</p></div></div></section>"""
    page("/privacy-policy/", "Privacy Policy | Z Hostel", "How Z Hostel collects and uses your personal data.", body, plain=True)


def build_404():
    body = f'<section class="section"><div class="container text-center"><h1>Page not found</h1><p>Sorry, that page isn\'t here any more.</p><p><a class="btn" href="/">Go to the home page</a> {book_btn("btn btn-dark", "Book Now", False)}</p></div></section>'
    page("/404-tmp/", "Page not found | Z Hostel", "Page not found.", body, plain=True)
    src = os.path.join(ROOT, "404-tmp/index.html")
    os.replace(src, os.path.join(ROOT, "404.html"))
    os.rmdir(os.path.join(ROOT, "404-tmp"))
    PAGES.remove("/404-tmp/")


def build_meta():
    import datetime
    today = datetime.date.today().isoformat()
    pages = PAGES + ["/book/"]
    urls = "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod></url>" for p in pages)
    with open(os.path.join(ROOT, "sitemap.xml"), "w") as fh:
        fh.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n')
    with open(os.path.join(ROOT, "robots.txt"), "w") as fh:
        fh.write(f"# AI assistants and search engines are welcome. Facts for LLMs: {SITE}/llms.txt\n"
                 f"User-agent: *\nAllow: /\nDisallow: /staff/\nDisallow: /manager/\nDisallow: /pay/\nSitemap: {SITE}/sitemap.xml\n")


if __name__ == "__main__":
    build_home(); build_about(); build_rooms(); build_events(); build_gallery(); build_blog()
    build_careers(); build_contact(); build_faq(); build_privacy(); build_404(); build_llms(); build_meta()
    print(f"{len(PAGES)} pages built; Book Now → {BOOK_URL}")
