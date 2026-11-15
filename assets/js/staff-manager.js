/* Z Hostel — manager summary (manager/index.html). Ported from the VBR manager page.
   The passcode is checked by the database (manager_summary / manager_check_passcode), never here. */
(function () {
  var cfg = window.SUPABASE_CONFIG || {};
  var KEY = "zh.mgr";
  var code = null, view = "day", anchor = today(), data = null, cache = {};
  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function iso(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
  function today() { var n = new Date(); return new Date(n.getFullYear(), n.getMonth(), n.getDate()); }
  function addDays(d, k) { var x = new Date(d); x.setDate(x.getDate() + k); return x; }
  function parse(s) { var p = s.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); }
  function peso(n) { return n == null ? "" : "₱" + Number(n).toLocaleString("en-PH", { maximumFractionDigits: 0 }); }
  function fmt(d, o) { return d.toLocaleDateString("en-PH", o); }
  function plural(n, a, b) { return n + " " + (n === 1 ? a : (b || a + "s")); }

  function range() {
    var a = anchor, from, to;
    if (view === "day") { from = to = a; }
    else if (view === "week") { from = addDays(a, -((a.getDay() + 6) % 7)); to = addDays(from, 6); }
    else { from = new Date(a.getFullYear(), a.getMonth(), 1); to = new Date(a.getFullYear(), a.getMonth() + 1, 0); }
    return { from: from, to: to };
  }
  function rangeLabel(r) {
    if (view === "day") return fmt(r.from, { weekday: "long", month: "long", day: "numeric", year: "numeric" });
    if (view === "week") return fmt(r.from, { month: "short", day: "numeric" }) + " – " + fmt(r.to, { month: "short", day: "numeric", year: "numeric" });
    return fmt(r.from, { month: "long", year: "numeric" });
  }

  function call(from, to) {
    return fetch(cfg.url + "/rest/v1/rpc/manager_summary", {
      method: "POST",
      headers: { "Content-Type": "application/json", apikey: cfg.anonKey, Authorization: "Bearer " + cfg.anonKey },
      body: JSON.stringify({ p_code: code, p_from: iso(from), p_to: iso(to) }),
    }).then(function (res) {
      return res.json().then(function (j) {
        if (!res.ok) throw new Error((j && (j.message || j.hint)) || "Couldn't load");
        return j;
      });
    });
  }

  // ---------- passcode ----------
  function unlock(c, quiet) {
    code = c;
    var r = range();
    $("lockBtn").disabled = true;
    return call(r.from, r.to).then(function (j) {
      $("lockBtn").disabled = false;
      if (!j.ok) { code = null; $("lockErr").textContent = j.error || "Wrong passcode"; try { sessionStorage.removeItem(KEY); } catch (e) {} return; }
      try { sessionStorage.setItem(KEY, c); } catch (e) {}
      $("lock").hidden = true; $("app").hidden = false;
      cache = {}; cache[iso(r.from) + iso(r.to)] = j;
      render(j);
    }).catch(function (e) { $("lockBtn").disabled = false; code = null; if (!quiet) $("lockErr").textContent = e.message; });
  }
  $("lockForm").addEventListener("submit", function (e) { e.preventDefault(); $("lockErr").textContent = ""; var c = $("code").value.trim(); if (c) unlock(c); });
  $("outBtn").addEventListener("click", function () { try { sessionStorage.removeItem(KEY); } catch (e) {} code = null; cache = {}; $("app").hidden = true; $("lock").hidden = false; $("code").value = ""; $("code").focus(); });

  // ---------- navigation ----------
  Array.prototype.forEach.call(document.querySelectorAll(".seg button"), function (b) {
    b.addEventListener("click", function () {
      view = b.getAttribute("data-v");
      Array.prototype.forEach.call(document.querySelectorAll(".seg button"), function (x) { x.classList.toggle("on", x === b); });
      load();
    });
  });
  function step(k) {
    if (view === "day") anchor = addDays(anchor, k);
    else if (view === "week") anchor = addDays(anchor, 7 * k);
    else anchor = new Date(anchor.getFullYear(), anchor.getMonth() + k, 1);
    load();
  }
  $("prevBtn").addEventListener("click", function () { step(-1); });
  $("nextBtn").addEventListener("click", function () { step(1); });
  $("todayBtn").addEventListener("click", function () { anchor = today(); load(); });
  document.addEventListener("keydown", function (e) { if ($("app").hidden || e.target.tagName === "INPUT") return; if (e.key === "ArrowLeft") step(-1); if (e.key === "ArrowRight") step(1); });

  function load() {
    var r = range(), k = iso(r.from) + iso(r.to);
    $("rangeLbl").textContent = rangeLabel(r);
    if (cache[k]) return render(cache[k]);
    $("list").innerHTML = '<div id="loading">Loading…</div>';
    call(r.from, r.to).then(function (j) {
      if (!j.ok) { $("outBtn").click(); $("lockErr").textContent = j.error || "Please enter the passcode again."; return; }
      cache[k] = j; render(j);
    }).catch(function (e) { $("list").innerHTML = '<div class="empty">' + esc(e.message) + "</div>"; });
  }

  // ---------- render ----------
  var TYPE = { overnight: "Stay", day_trip: "Day visit", half_day: "Day visit", corporate: "Group" };
  function statusPill(b) {
    if (b.type === "overnight" && b.cb_status === "checked_in") return '<span class="pill in">In-house</span>';
    if (b.status === "confirmed") return '<span class="pill ok">Confirmed</span>';
    if (b.status === "completed") return '<span class="pill">Completed</span>';
    if (b.status === "pending_payment") return '<span class="pill wait">Payment to verify</span>';
    return '<span class="pill wait">Awaiting payment</span>';
  }
  function party(b) { return (b.adults || 0) + (b.kids612 || 0) + (b.kids05 || 0); }
  function partyText(b) {
    var t = [plural(b.adults || 0, "adult")];
    if (b.kids612) t.push(plural(b.kids612, "kid") + " 6–12");
    if (b.kids05) t.push(plural(b.kids05, "kid") + " 0–5");
    var x = t.join(", ");
    var sp = [];
    if (b.seniors) sp.push(b.seniors + " senior/PWD");
    if (b.pwd_kids) sp.push(b.pwd_kids + " PWD kid" + (b.pwd_kids === 1 ? "" : "s"));
    return x + (sp.length ? " (incl. " + sp.join(", ") + ")" : "");
  }
  function nights(b) { return b.check_out ? Math.round((parse(b.check_out) - parse(b.check_in)) / 864e5) : 1; }
  function chips(b) {
    var c = [];
    if (b.type === "overnight") {
      if (b.villas) b.villas.split(", ").forEach(function (v) { c.push('<span class="k">' + esc(v) + "</span>"); });
      else c.push('<span class="k">Room to assign</span>');
      c.push("<span>" + plural(nights(b), "night") + " · " + fmt(parse(b.check_in), { month: "short", day: "numeric" }) + " → " + fmt(parse(b.check_out), { month: "short", day: "numeric" }) + "</span>");
    } else {
      if (b.type === "corporate") c.push("<span>Corporate / group</span>");
    }
    if (b.add_ons) c.push("<span>" + esc(b.add_ons) + "</span>");
    if (b.occasion) c.push("<span>🎉 " + esc(b.occasion) + "</span>");
    return '<div class="chips">' + c.join("") + "</div>";
  }
  function card(b, tag) {
    var names = b.party_names && b.party_names !== b.guest ? b.party_names.replace(new RegExp("^" + b.guest.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ",\\s*"), "") : "";
    var amt = b.total != null ? peso(b.total) + (b.paid != null && b.total > 0 ? " <small>· " + (Number(b.paid) >= Number(b.total) - 0.5 ? "paid" : Number(b.paid) > 0 ? peso(b.paid) + " paid" : "unpaid") + "</small>" : "") : "";
    if (b.sheet && b.status === "confirmed" && !Number(b.paid)) amt = (b.total != null ? peso(b.total) + " " : "") + "<small>· paid (sheet)</small>";
    return '<div class="bk"><div class="bk-1"><b>' + esc(b.guest || "—") + '</b><span class="code">' + esc(b.code || "") + "</span>" + statusPill(b) +
      (tag ? '<span class="pill">' + tag + "</span>" : "") + '<span class="bk-amt">' + amt + "</span></div>" +
      '<div class="bk-party">' + esc(TYPE[b.type] || b.type_label || "") + " · " + esc(partyText(b)) + "</div>" +
      (names ? '<div class="bk-names">With: ' + esc(names) + "</div>" : "") + chips(b) + "</div>";
  }

  function render(j) {
    var r = range(), days = [], bk = j.bookings || [];
    for (var d = new Date(r.from); d <= r.to; d = addDays(d, 1)) days.push(new Date(d));
    var nDays = days.length;

    // KPIs (range)
    var guestNights = 0, dayGuests = 0, arrivals = 0, arrGuests = 0, roomNights = 0, value = 0, pending = 0, inRange = 0;
    var fromS = iso(r.from), toS = iso(r.to);
    bk.forEach(function (b) {
      var startsIn = b.check_in >= fromS && b.check_in <= toS;
      if (b.type === "overnight") {
        var units = b.villas ? b.villas.split(", ").length : 1;
        days.forEach(function (d) { var s = iso(d); if (s >= b.check_in && s < b.check_out) { roomNights += units; guestNights += party(b); } });
        if (startsIn) { arrivals++; arrGuests += party(b); }
      } else if (startsIn) { dayGuests += party(b); }
      if (startsIn) { inRange++; value += Number(b.total) || 0; if (b.status === "pending" || b.status === "pending_payment") pending++; }
    });
    var occ = j.casitas_total ? Math.round(roomNights / (j.casitas_total * nDays) * 100) : null;
    $("kpis").innerHTML = [
      ["Arriving guests", arrGuests, plural(arrivals, "booking")],
      ["Guest-nights", guestNights, "in-house in this " + view],
      ["Bed/room-nights", roomNights, occ != null ? occ + "% occupancy" : ""],
      ["Bookings", inRange, pending ? pending + " awaiting payment" : "all settled"],
      ["Booked value", peso(value), "by arrival date"],
      ["Beds & rooms", j.casitas_total || "—", "in total"],
    ].map(function (k) { return '<div class="kpi"><span>' + k[0] + "</span><b>" + k[1] + "</b><em>" + k[2] + "</em></div>"; }).join("");

    // per day
    var out = "";
    days.forEach(function (d) {
      var s = iso(d);
      var arriving = [], staying = [], dayt = [];
      bk.forEach(function (b) {
        if (b.type === "overnight") {
          if (b.check_in === s) arriving.push(b);
          else if (b.check_in < s && b.check_out > s) staying.push(b);
        } else if (b.check_in === s) dayt.push(b);
      });
      if (view !== "day" && !arriving.length && !dayt.length && !staying.length) return;
      var dg = dayt.reduce(function (t, b) { return t + party(b); }, 0);
      var og = arriving.concat(staying).reduce(function (t, b) { return t + party(b); }, 0);
      var h = '<div class="day"><div class="day-h"><h3>' + esc(fmt(d, { weekday: "short", month: "short", day: "numeric" })) + "</h3>" +
        '<span class="sum">' + [og ? plural(og, "guest") : "", dayt.length ? plural(dg, "other guest") : ""].filter(Boolean).join(" · ") + "</span></div>";
      if (arriving.length) h += '<div class="grp">Arriving</div>' + arriving.map(function (b) { return card(b); }).join("");
      if (staying.length && view === "day") h += '<div class="grp">Staying over</div>' + staying.map(function (b) { return card(b, "night " + (Math.round((d - parse(b.check_in)) / 864e5) + 1) + " of " + nights(b)); }).join("");
      else if (staying.length) h += '<div class="grp">Staying over: ' + esc(staying.map(function (b) { return b.guest; }).join(", ")) + "</div>";
      if (dayt.length) h += '<div class="grp">Other bookings</div>' + dayt.map(function (b) { return card(b); }).join("");
      if (!arriving.length && !staying.length && !dayt.length) h += '<div class="empty">No bookings on this day.</div>';
      out += h + "</div>";
    });
    $("list").className = view === "month" ? "compact" : "";
    $("list").innerHTML = out || '<div class="empty">No bookings in this ' + view + ".</div>";
  }

  // remember the passcode for this browser tab only
  var saved = null;
  try { saved = sessionStorage.getItem(KEY); } catch (e) {}
  $("rangeLbl").textContent = rangeLabel(range());
  if (saved) unlock(saved, true);
})();
