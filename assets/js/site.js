/* Z Hostel — public site behaviour: menu, carousels, reviews, lightbox,
   video, contact + careers forms (send-contact-email Edge Function). */
(function () {
  "use strict";
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }

  // ---- menu
  var overlay = $("#navOverlay");
  $$("[data-menu-open]").forEach(function (b) { b.addEventListener("click", function () { overlay.classList.add("open"); overlay.setAttribute("aria-hidden", "false"); $(".close", overlay).focus(); }); });
  $$("[data-menu-close]").forEach(function (b) { b.addEventListener("click", closeMenu); });
  function closeMenu() { overlay.classList.remove("open"); overlay.setAttribute("aria-hidden", "true"); }
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") { closeMenu(); closeLb(); } });

  // ---- carousels
  $$(".carousel").forEach(function (c) {
    var track = $(".slides", c), slides = $$("figure", c), i = 0, n = slides.length;
    if (n < 2) return;
    var dots = document.createElement("div"); dots.className = "dots";
    slides.forEach(function (_, k) { var d = document.createElement("button"); d.type = "button"; d.setAttribute("aria-label", "Photo " + (k + 1)); d.addEventListener("click", function () { go(k); }); dots.appendChild(d); });
    c.appendChild(dots);
    var ctrl = document.createElement("div"); ctrl.className = "ctrl";
    ctrl.innerHTML = '<button type="button" aria-label="Previous photo">&#8249;</button><button type="button" aria-label="Next photo">&#8250;</button>';
    c.appendChild(ctrl);
    ctrl.children[0].addEventListener("click", function () { go(i - 1); });
    ctrl.children[1].addEventListener("click", function () { go(i + 1); });
    function go(k) { i = (k + n) % n; track.style.transform = "translateX(" + (-100 * i) + "%)"; $$("button", dots).forEach(function (d, j) { d.setAttribute("aria-current", j === i ? "true" : "false"); }); }
    var x0 = null;
    c.addEventListener("touchstart", function (e) { x0 = e.touches[0].clientX; }, { passive: true });
    c.addEventListener("touchend", function (e) { if (x0 === null) return; var dx = e.changedTouches[0].clientX - x0; if (Math.abs(dx) > 40) go(i + (dx < 0 ? 1 : -1)); x0 = null; });
    go(0);
  });

  // ---- reviews
  $$(".review-set").forEach(function (set) {
    var items = $$(".review-slide", set), i = 0;
    function show(k) { i = (k + items.length) % items.length; items.forEach(function (it, j) { it.classList.toggle("active", j === i); }); }
    var p = $("[data-prev]", set.parentNode), n = $("[data-next]", set.parentNode);
    if (p) p.addEventListener("click", function () { show(i - 1); });
    if (n) n.addEventListener("click", function () { show(i + 1); });
    show(0);
  });

  // ---- lightbox (gallery)
  var lb = $("#lightbox"), lbImg = lb && $("img", lb), group = [], gi = 0;
  $$("[data-lightbox]").forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      group = $$('[data-lightbox="' + a.getAttribute("data-lightbox") + '"]'); gi = group.indexOf(a); openLb();
    });
  });
  function openLb() { if (!lb) return; lbImg.src = group[gi].href; lbImg.alt = $("img", group[gi]).alt || ""; lb.classList.add("open"); }
  function closeLb() { if (lb) lb.classList.remove("open"); }
  if (lb) {
    $(".x", lb).addEventListener("click", closeLb);
    $(".prev", lb).addEventListener("click", function () { gi = (gi - 1 + group.length) % group.length; openLb(); });
    $(".next", lb).addEventListener("click", function () { gi = (gi + 1) % group.length; openLb(); });
    lb.addEventListener("click", function (e) { if (e.target === lb) closeLb(); });
  }

  // ---- "Z in 1 minute" video
  $$("[data-video]").forEach(function (b) {
    b.addEventListener("click", function () {
      var f = document.createElement("iframe");
      f.src = b.getAttribute("data-video"); f.title = "Z Hostel in 1 minute";
      f.allow = "autoplay; encrypted-media; picture-in-picture"; f.allowFullscreen = true;
      b.parentNode.replaceWith(f);
    });
  });

  // ---- map: load the Google map only when it scrolls into view
  $$("iframe[data-src]").forEach(function (f) {
    var load = function () { f.src = f.getAttribute("data-src"); f.removeAttribute("data-src"); };
    if (!("IntersectionObserver" in window)) return load();
    var io = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { load(); io.disconnect(); } });
    io.observe(f);
  });

  // ---- forms → send-contact-email Edge Function (falls back to email app)
  var cfg = window.SUPABASE_CONFIG || {};
  $$("form[data-contact]").forEach(function (form) {
    var status = $(".status", form);
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (!form.reportValidity()) return;
      var fd = new FormData(form);
      if (fd.get("website")) return; // honeypot
      var kind = form.getAttribute("data-contact");
      var btn = $("button[type=submit]", form); btn.disabled = true;
      status.className = "status"; status.textContent = "Sending…";
      var done = function (ok, msg) { btn.disabled = false; status.className = "status " + (ok ? "ok" : "err"); status.textContent = msg; if (ok) form.reset(); };
      if (!cfg.url) {
        var to = kind === "careers" ? "hr@zhostel.com" : "reservations@zhostel.com";
        location.href = "mailto:" + to + "?subject=" + encodeURIComponent(fd.get("subject") || fd.get("position") || "Website message") +
          "&body=" + encodeURIComponent((fd.get("message") || "") + "\n\n" + (fd.get("name") || "") + " " + (fd.get("phone") || ""));
        return done(true, "Your email app should open with the message ready to send.");
      }
      var send = function (body) {
        return fetch(cfg.url + "/functions/v1/send-contact-email", {
          method: "POST",
          headers: { "Content-Type": "application/json", apikey: cfg.anonKey, Authorization: "Bearer " + cfg.anonKey },
          body: JSON.stringify(body),
        }).then(function (r) { return r.json().catch(function () { return {}; }).then(function (j) { if (!r.ok || j.error) throw new Error(j.error || "failed"); return j; }); });
      };
      var body = { kind: kind, name: fd.get("name"), email: fd.get("email"), phone: fd.get("phone"), subject: fd.get("subject") || fd.get("position"), message: fd.get("message"), page: location.pathname };
      var file = fd.get("cv");
      var p = Promise.resolve();
      if (kind === "careers" && file && file.size) {
        if (file.size > 5 * 1024 * 1024) return done(false, "Your CV is over 5 MB — please send a smaller file.");
        p = new Promise(function (res, rej) {
          var rd = new FileReader();
          rd.onload = function () { body.attachment = { name: file.name, type: file.type, data: String(rd.result).split(",")[1] }; res(); };
          rd.onerror = rej; rd.readAsDataURL(file);
        });
      }
      p.then(function () { return send(body); })
        .then(function () { done(true, kind === "careers" ? "Thank you! Your application was sent to our HR team." : "Thank you! We'll get back to you soon."); })
        .catch(function () { done(false, "Sorry, that didn't go through. Please email " + (kind === "careers" ? "hr@zhostel.com" : "reservations@zhostel.com") + "."); });
    });
  });
})();
