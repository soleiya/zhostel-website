#!/usr/bin/env python3
"""Z Hostel booking pages: book/ (Book Your Stay) and pay/ (Pay & Upload Documents).

Ported from the Virgin Beach Resort booking engine (book-stay/ and pay/ in
virgin-beach-resort-website). The Supabase database is the same engine, so the
pages call the same functions:
  book/  → villas, public_villa_holds, public_closed_nights, quote_overnight(),
           quote_overnight_inquiry(), submit_overnight_booking(),
           submit_overnight_inquiry(), booking_ref(), log_code_attempt()
  pay/   → get_booking_uploads(), submit_payment_proof(), submit_booking_documents()
  both   → xendit-pay Edge Function for online payment.

A "unit" is one dorm bed (sleeps 1) or one private room (sleeps 2). The units
themselves come live from the `villas` table (loaded from Cloudbeds by
cloudbeds-sync "setup"); ROOM_TYPES below only adds the card text and photo for
each room_type. A room type in the database that is missing here is not shown.
Prices always come from the database (Cloudbeds rates); the "from" prices on
the cards are zhostel.com's published rates.

Run:  python3 pages_booking.py
"""
import os

from build_site import page, e, v, have, CBP, PHONE, MOBILE, EMAIL, FB, ROOT

# room_type (villas.room_type) → (name, description, photo, published price, unit)
ROOM_TYPES = [
    ("4-bed-mixed-dorm", "4 Bed Mixed Dorm",
     "A bed in a stylish 4-bed mixed dorm &mdash; a good mix of privacy and sociability. Breakfast included.",
     "/wp-content/uploads/2019/02/Z-Hostel-Rooms-Q1-2019-35-1000x666.jpg", 1350, "bed"),
    ("6-bed-mixed-dorm", "6 Bed Mixed Dorm",
     "A bed in a 6-bed mixed dorm &mdash; just the right number of people for a fun stay. Breakfast included.",
     "/wp-content/uploads/2019/02/Z-Hostel-Rooms-Q1-2019-25-1000x665.jpg", 1300, "bed"),
    ("8-bed-mixed-dorm", "8 Bed Mixed Dorm",
     "A bed in an 8-bed mixed dorm, near the elevators for easy access to the roof deck. Breakfast included.",
     "/wp-content/uploads/2019/02/Z-Hostel-Rooms-Q1-2019-55-1000x666.jpg", 1250, "bed"),
    ("6-bed-female-dorm", "6 Bed Female Dorm",
     "A bed in our all-female &ldquo;Stiletto&rdquo; dorm &mdash; <strong>female guests only</strong>. Breakfast included.",
     "/wp-content/uploads/2019/03/MG_0434-1-1000x667.jpg", 1300, "bed"),
    ("social-fun-floor-dorm-4md", "Social Fun Floor Dorm &ndash; 4 Bed Mixed",
     "A bed in a 4-bed mixed dorm on the Social Fun Floor, right below the roof deck. Breakfast included.",
     "/wp-content/uploads/2019/02/20190222-IMG_1889-1000x667.jpg", 1350, "bed"),
    ("social-fun-floor-dorm-6md", "Social Fun Floor Dorm &ndash; 6 Bed Mixed",
     "A bed in a 6-bed mixed dorm on the Social Fun Floor, right below the roof deck. Breakfast included.",
     "/wp-content/uploads/2019/02/Z-Hostel-Rooms-Q1-2019-10-1000x665.jpg", 1300, "bed"),
    ("private-room-standard", "Private Room Standard",
     "A private room for two on our highest floors. Breakfast for two included.",
     "/wp-content/uploads/2019/02/ZHostel-Interiors-24-A-1000x665.jpg", 3000, "room"),
    ("private-room-bunk-bed", "Private Room Bunk Bed",
     "A whole room for you and your buddy, with a bunk bed. Breakfast for two included.",
     "/wp-content/uploads/2019/02/ZHostel-Interiors-4-A-1000x665.jpg", 3000, "room"),
    ("social-fun-floor-private-room", "Social Fun Floor &ndash; Private Room",
     "A private room for two on the Social Fun Floor, right below the roof deck. Breakfast for two included.",
     "/wp-content/uploads/2019/03/Z-Hostel-Rooms-Q1-2019-17-1000x665.jpg", 3000, "room"),
    ("social-private-bunk-bed", "Social Private Bunk Bed",
     "A private bunk-bed room for two on the Social Fun Floor. Breakfast for two included.",
     "/wp-content/uploads/2019/02/ZHostel-Interiors-3-1000x665.jpg", 3000, "room"),
]

COUNTRIES = [
    "Philippines", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia",
    "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Belarus", "Belgium",
    "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei",
    "Bulgaria", "Burkina Faso", "Burundi", "Cambodia", "Cameroon", "Canada", "Chile", "China",
    "Colombia", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czechia", "Denmark", "Dominican Republic",
    "Ecuador", "Egypt", "El Salvador", "Estonia", "Ethiopia", "Fiji", "Finland", "France", "Georgia",
    "Germany", "Ghana", "Greece", "Guatemala", "Honduras", "Hong Kong", "Hungary", "Iceland", "India",
    "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan",
    "Kazakhstan", "Kenya", "Kuwait", "Laos", "Latvia", "Lebanon", "Libya", "Liechtenstein",
    "Lithuania", "Luxembourg", "Macao", "Malaysia", "Maldives", "Malta", "Mexico", "Moldova",
    "Monaco", "Mongolia", "Montenegro", "Morocco", "Myanmar", "Nepal", "Netherlands",
    "New Zealand", "Nigeria", "North Korea", "North Macedonia", "Norway", "Oman", "Pakistan",
    "Panama", "Papua New Guinea", "Paraguay", "Peru", "Poland", "Portugal", "Qatar", "Romania",
    "Russia", "Rwanda", "Saudi Arabia", "Senegal", "Serbia", "Singapore", "Slovakia", "Slovenia",
    "South Africa", "South Korea", "Spain", "Sri Lanka", "Sweden", "Switzerland", "Taiwan",
    "Tajikistan", "Tanzania", "Thailand", "Tunisia", "Turkey", "Ukraine", "United Arab Emirates",
    "United Kingdom", "United States", "Uruguay", "Uzbekistan", "Venezuela", "Vietnam", "Yemen",
]

TEL_MOBILE = "tel:+639178898531"
TEL_LANDLINE = "tel:+63288560851"


def js(name):
    return f'<script src="/assets/js/{name}?v={v("assets/js/" + name)}"></script>'


def write(path, title, desc, body, scripts):
    """Lay the page out with the site chrome (build_site.page), then add booking.css
    and this page's scripts (after config.js, which holds window.SUPABASE_CONFIG)."""
    page(path, title, desc, body, plain=True)
    full = os.path.join(ROOT, path.strip("/"), "index.html")
    html = open(full, encoding="utf-8").read()
    css = f'<link rel="stylesheet" href="/assets/css/booking.css?v={v("assets/css/booking.css")}">\n'
    html = html.replace("</head>", css + '<meta name="robots" content="noindex">\n</head>' if path == "/pay/" else css + "</head>", 1)
    cfg = f'<script src="/assets/js/config.js?v={v("assets/js/config.js")}"></script>\n'
    assert cfg in html, "config.js tag not found in footer"
    html = html.replace(cfg, cfg + "\n".join(scripts) + "\n", 1)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(html)
    print("wrote", path)


def contact_band(heading, text):
    return f"""<section class="section section--grey booking"><div class="booking-wrap center">
<h2 class="section-title">{heading}</h2>
<p>{text}</p>
<p><a class="text-link" href="{TEL_LANDLINE}">{PHONE}</a> &middot; <a class="text-link" href="{TEL_MOBILE}">{MOBILE}</a> &middot;
<a class="text-link" href="mailto:{EMAIL}">{EMAIL}</a></p></div></section>"""


# ====================================================================== book/
def build_book():
    cards = ""
    for slug, name, desc, img, price, unit in ROOM_TYPES:
        img = img if have(img) else (CBP.get(slug) or [None])[0]
        pic = f'<img src="{img}" alt="{name} at Z Hostel" loading="lazy">' if img else '<div class="vt-noimg" aria-hidden="true"></div>'
        cards += f"""
      <div class="villa-type" data-type="{slug}">
        {pic}
        <div>
          <h3>{name}</h3>
          <div class="vt-meta">{desc} &middot; <span class="vt-occ"></span></div>
          <div class="vt-rate">from <b>&#8369;{price:,}</b> <span class="muted">per {unit} / night</span></div>
          <div class="vt-avail">Pick your dates to check availability</div>
        </div>
        <div class="stepper" role="group" aria-label="Number of {name} {unit}s">
          <button type="button" class="st-minus" aria-label="One fewer {name} {unit}">&minus;</button>
          <output class="st-count">0</output>
          <button type="button" class="st-plus" aria-label="One more {name} {unit}">+</button>
        </div>
      </div>"""
    countries = "\n".join(f'<option value="{c}"{" selected" if c == "Philippines" else ""}>{c}</option>' for c in COUNTRIES)

    body = f"""
<header class="page-head">
  <span class="eyebrow">Book direct &middot; Poblacion, Makati</span>
  <h1>Book Your Stay</h1>
  <p>Pick your dates and your beds or private room, tell us who's coming, and book and pay online in minutes &mdash; your stay is confirmed as soon as your payment goes through.</p>
</header>

<section class="section booking">
  <div class="booking-wrap">
    <div id="stayFormWrap">
      <form class="inquiry" id="stayForm" novalidate>

        <div class="stay-step">
          <div class="stay-step-head"><span class="stay-step-num">1</span><div><h2>Your dates</h2><p>Check-in from 2:00 PM &middot; check-out by 12:00 noon</p></div></div>
          <div class="row-2">
            <div><label for="checkIn">Check-in</label><input id="checkIn" type="date" required data-booking-date="checkin"></div>
            <div><label for="checkOut">Check-out</label><input id="checkOut" type="date" required data-booking-date="checkout"></div>
          </div>
          <div class="stay-cal" id="stayCal" hidden></div>
          <p class="stay-nights" id="nightsLine"></p>
          <div class="request-banner" id="requestBanner" role="status" hidden>
            <p class="rb-title">Booking request &mdash; not an instant booking</p>
            <p>Online booking is open for stays through <strong class="js-stay-until"></strong>. For these dates you can <strong>send us a booking request</strong> (for stays up to <span class="js-request-until"></span>): our reservations team will review it and reply by email to confirm availability and the final rate.</p>
            <ul>
              <li>Prices shown are our published rates, for reference only &mdash; <strong>rates for these dates may change</strong>.</li>
              <li>This is an <strong>inquiry only</strong>: no bed or room is reserved and nothing is charged until we confirm.</li>
            </ul>
          </div>
        </div>

        <div class="stay-step">
          <div class="stay-step-head"><span class="stay-step-num">2</span><div><h2>Choose your beds or room</h2><p>Dorms are booked per bed &mdash; one bed per guest. Private rooms sleep two. Travelling as a group? Add as many beds as you need.</p></div></div>
          <p class="field-hint" id="availStatus" style="margin:0;">Pick your dates above to see what's free.</p>
          <div class="villa-type-list" id="villaTypes">{cards}
          </div>
          <p class="villa-picked-note" id="pickedNote" hidden></p>
        </div>

        <div class="stay-step">
          <div class="stay-step-head"><span class="stay-step-num">3</span><div><h2>Who's staying</h2><p>Every guest shows a valid ID at check-in, so we need everyone's full name.</p></div></div>
          <div class="row-2">
            <div><label for="guestName">Your full name (primary guest)</label><input id="guestName" type="text" autocomplete="name" required></div>
            <div><label for="guestPhone">Mobile number</label><input id="guestPhone" type="tel" autocomplete="tel" required></div>
          </div>
          <div class="row-2">
            <div><label for="guestEmail">Email</label><input id="guestEmail" type="email" autocomplete="email" required></div>
            <div><label for="country">Country</label><select id="country">{countries}</select></div>
          </div>
          <label class="inline-check"><input type="checkbox" id="primarySenior"> I'm a Senior Citizen or PWD (20% discount with a valid ID)</label>
          <div>
            <label for="partySize">How many guests in total, including you?</label>
            <div class="stepper">
              <button type="button" id="partyMinus" aria-label="One fewer guest">&minus;</button>
              <output id="partySize">2</output>
              <button type="button" id="partyPlus" aria-label="One more guest">+</button>
            </div>
          </div>
          <div>
            <label>Your companions</label>
            <div class="guest-list" id="guestList"></div>
            <p class="field-hint" style="margin-top:8px;">Full name (first and last) as it appears on their ID.</p>
          </div>
          <div class="capacity-meter" id="capacityMeter" hidden></div>
        </div>

        <div class="stay-step">
          <div class="stay-step-head"><span class="stay-step-num">4</span><div><h2>A few more details</h2></div></div>
          <div id="seniorIdWrap" hidden>
            <label for="seniorIdFiles">Senior Citizen / PWD ID photo(s)</label>
            <input id="seniorIdFiles" type="file" accept="image/*" multiple>
            <p class="field-hint" style="margin-top:6px;">One photo per senior citizen / PWD (or one photo with all IDs) &mdash; needed for the 20% discount. Please bring the ID(s) too.</p>
          </div>
          <div class="row-2">
            <div>
              <label for="occasion">Celebrating anything?</label>
              <select id="occasion">
                <option value="">Nothing in particular</option>
                <option value="birthday">Birthday</option>
                <option value="anniversary">Anniversary</option>
                <option value="honeymoon">Honeymoon</option>
                <option value="reunion">Reunion</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div>
              <label for="hearAbout">How did you hear about us?</label>
              <select id="hearAbout">
                <option value="">Prefer not to say</option>
                <option value="facebook">Facebook / Instagram</option>
                <option value="google">Google Search</option>
                <option value="referral">Friend / Family Referral</option>
                <option value="repeat_guest">I've stayed before</option>
                <option value="travel_agent">Travel Agent</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>
          <div><label for="notes">Special requests</label><textarea id="notes" placeholder="Arrival time, a bottom bunk, anything we should know&hellip;"></textarea></div>
        </div>

        <div class="stay-step" id="addonStep" hidden>
          <div class="stay-step-head"><span class="stay-step-num">5</span><div><h2>Extras</h2><p>Optional &mdash; reserve these now, or arrange them at the front desk during your stay.</p></div></div>
          <div class="addon-list" id="addonList"></div>
        </div>

        <div class="stay-step">
          <div class="stay-step-head"><span class="stay-step-num">&#10003;</span><div><h2 id="summaryTitle">Your booking summary</h2></div></div>
          <div class="code-row" id="codeRow">
            <label for="discountCode">Discount code <span class="muted">(optional)</span></label>
            <div class="code-input"><input id="discountCode" type="text" autocomplete="off" autocapitalize="characters" spellcheck="false" maxlength="30" placeholder="Enter code"><button type="button" class="btn btn-ghost" id="applyCode">Apply</button></div>
            <p class="code-msg" id="codeMsg" hidden></p>
          </div>
          <div id="billSummary" class="bill-summary"><div class="bill-lines"><div class="bill-row"><span>Choose dates, beds or room, and guests to see your total</span><span>&mdash;</span></div></div></div>
          <label class="inline-check request-agree" id="requestAgreeWrap" hidden><input type="checkbox" id="requestAgree"><span>I understand this is a <strong>booking inquiry only</strong>, not a confirmed reservation. Availability and the final rate are subject to review and may change, and nothing is charged until Z Hostel confirms my booking.</span></label>
          <label class="inline-check"><input type="checkbox" id="agreeTerms"> <span>I confirm these booking details are correct, that every guest will show a valid ID at check-in, and I agree to the <a class="text-link" href="/privacy-policy/" target="_blank" rel="noopener">Privacy Policy</a>.</span></label>
          <label class="inline-check" style="font-size:13px;color:#666;"><input type="checkbox" id="marketingOptIn"> Send me occasional promos and updates from Z Hostel.</label>
          <div class="form-error-box" id="formError" hidden></div>
          <button class="btn btn-primary" type="submit" id="submitBtn">Book Now</button>
          <p class="field-hint" id="submitHint" style="margin:0;">Your beds or room are held for 24 hours while you pay. Right after booking you can <strong>pay in full online</strong> &mdash; card, GCash, Maya and more, through our secure payment partner Xendit &mdash; and your stay is confirmed as soon as it goes through.</p>
        </div>
      </form>
    </div>
    <div id="stayStatus" class="form-status" hidden></div>
  </div>
</section>

<section class="section booking"><div class="booking-wrap center">
  <span class="eyebrow">Already booked?</span>
  <h2>Pay for your booking</h2>
  <p>Pay online with the Booking ID from your booking email, and upload any Senior Citizen / PWD IDs.</p>
  <a class="btn btn-ghost" href="/pay/">Pay online</a>
</div></section>
{contact_band("Prefer to talk?", "Call, message us on <a class=\"text-link\" href=\"" + FB + "\" target=\"_blank\" rel=\"noopener\">Facebook</a>, or email our reservations team.")}
"""
    write("/book/", "Book Your Stay | Z Hostel",
          "Book a dorm bed or private room at Z Hostel, Poblacion, Makati directly — live availability and instant online booking.",
          body, [
              js("track.js"),
              '<script src="/assets/js/vendor/supabase-js-2.117.3.js"></script>',
              js("booking-window.js"), js("xendit-pay.js"), js("stay-calendar.js"), js("stay-booking.js"),
          ])


# ====================================================================== pay/
def build_pay():
    body = f"""
<header class="page-head">
  <span class="eyebrow">Payment</span>
  <h1>Pay &amp; Upload Documents</h1>
  <p>Find your booking to see your balance, then pay online &mdash; card, GCash, Maya and more, through Xendit &mdash; and add any Senior Citizen / PWD IDs your booking needs.</p>
</header>

<section class="section booking">
  <div class="booking-wrap" style="max-width:660px;">
    <div id="payFormWrap">
      <form class="inquiry" id="payForm">
        <div class="pay-step-head"><span class="pay-step-num">1</span><h2>Find your booking</h2></div>
        <div class="row-2">
          <div>
            <label for="orderCode">Booking ID</label>
            <input id="orderCode" type="text" required placeholder="e.g. ZH-1042" autocapitalize="characters" autocomplete="off">
          </div>
          <div>
            <label for="payEmail">Email used on your booking</label>
            <input id="payEmail" type="email" required autocomplete="email">
          </div>
        </div>
        <p class="field-hint">Both are in your booking email.</p>
        <button class="btn btn-ghost" type="button" id="payFindBtn" style="justify-self:start;">Find my booking</button>
        <div class="pay-lookup" id="payLookup" hidden></div>

        <div id="payUploadPart" hidden>
        <div class="pay-step-head"><span class="pay-step-num">2</span><h2>What are you paying?</h2></div>
        <fieldset class="pay-kind" id="payKindWrap" hidden>
          <legend class="sr-only">Payment</legend>
          <div class="pay-kind-opts" id="payKindOpts"></div>
          <p class="field-hint" id="payKindHint"></p>
        </fieldset>
        <div id="payOnline" hidden>
          <button class="btn btn-primary" type="button" id="payOnlineBtn">Pay now</button>
          <p class="field-hint" style="margin-top:8px;">Secure checkout by our payment partner <strong>Xendit</strong> &mdash; card, GCash, Maya, QR Ph and more. Your booking is confirmed as soon as the payment goes through.</p>
          <p class="pay-now-error" id="payOnlineError" hidden></p>
        </div>
        <div class="pay-step-head" id="payStep3"><span class="pay-step-num">3</span><h2 id="payStep3Title">Upload your proof</h2></div>
        <div id="payProofWrap">
          <label>Payment screenshot</label>
          <label class="upload-drop" for="payFile">
            Tap to choose an image (JPG or PNG, under 10MB)
            <input id="payFile" type="file" accept="image/*">
          </label>
          <img id="payPreview" class="upload-preview" alt="">
          <p class="field-hint" id="payFileHint" hidden style="margin-top:6px;">Not paid yet? You can upload your documents now and come back for the payment.</p>
        </div>
        <div id="docSeniorWrap" hidden>
          <label for="docSeniorFiles">Senior Citizen / PWD ID photo(s)</label>
          <input id="docSeniorFiles" type="file" accept="image/*" multiple>
          <p class="field-hint" id="docSeniorHint" style="margin-top:6px;">One photo per senior citizen / PWD (or one photo with all IDs) &mdash; needed for the 20% discount. Please bring the ID(s) at check-in too.</p>
        </div>
        <button class="btn btn-primary" type="submit" id="paySubmitBtn">Upload</button>
        </div>
        <p class="field-hint" style="margin-top:4px;">Our reservations team reviews uploads and updates your booking &mdash; you'll hear back by email.</p>
      </form>
    </div>
    <div id="payStatus" class="form-status" hidden></div>
  </div>
</section>
{contact_band("Trouble paying?", "Message us on <a class=\"text-link\" href=\"" + FB + "\" target=\"_blank\" rel=\"noopener\">Facebook</a>, or email your Booking ID and question to our reservations team.")}
"""
    write("/pay/", "Pay & Upload Documents | Z Hostel",
          "Pay online and upload Senior Citizen / PWD IDs for your Z Hostel booking using your Booking ID.",
          body, [
              js("track.js"),
              '<script src="/assets/js/vendor/supabase-js-2.117.3.js"></script>',
              js("xendit-pay.js"), js("payment-upload.js"),
          ])


if __name__ == "__main__":
    build_book()
    build_pay()
