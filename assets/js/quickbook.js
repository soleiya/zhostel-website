/* Booking boxes (hero + footer): pick dates → /book/ with them filled in.
   Without JavaScript the form still works (plain GET to /book/). */
(function () {
  "use strict";
  function today() { return new Date().toLocaleDateString("en-CA", { timeZone: "Asia/Manila" }); }
  function addDays(s, n) { var d = new Date(s + "T00:00:00Z"); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
  var last = {};
  try { last = JSON.parse(sessionStorage.getItem("zh.qb") || "{}") || {}; } catch (e) { last = {}; }

  Array.prototype.forEach.call(document.querySelectorAll("form[data-quickbook]"), function (form) {
    var inEl = form.querySelector("[data-qb-in]"), outEl = form.querySelector("[data-qb-out]");
    var guests = form.querySelector("select[name=guests]"), room = form.querySelector("select[name=room]");
    var err = form.querySelector(".qb-error");
    var t = today();
    inEl.min = t; outEl.min = addDays(t, 1);
    if (last.in && last.in >= t) { inEl.value = last.in; outEl.min = addDays(last.in, 1); }
    if (last.out && inEl.value && last.out > inEl.value) outEl.value = last.out;
    if (last.guests) guests.value = last.guests;
    inEl.addEventListener("change", function () {
      if (!inEl.value) return;
      outEl.min = addDays(inEl.value, 1);
      if (!outEl.value || outEl.value <= inEl.value) outEl.value = addDays(inEl.value, 1);
    });
    function fail(msg, el) { err.textContent = msg; err.hidden = false; if (el) el.focus(); }
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      err.hidden = true;
      var a = inEl.value, b = outEl.value, now = today();
      if (!a || a < now) return fail("Pick your check-in date.", inEl);
      if (!b || b <= a) return fail("Pick a check-out date after check-in.", outEl);
      try { sessionStorage.setItem("zh.qb", JSON.stringify({ in: a, out: b, guests: guests.value })); } catch (x) {}
      var q = "?in=" + a + "&out=" + b + "&guests=" + encodeURIComponent(guests.value) + (room.value ? "&room=" + encodeURIComponent(room.value) : "");
      location.href = form.getAttribute("action") + q;
    });
  });
})();
