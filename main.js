/* Godiva Facilities Management — main.js
   Small, dependency-free. Everything degrades gracefully without JS. */
(function () {
  "use strict";

  /* ---------- Header: mobile navigation ---------- */
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!open));
      toggle.querySelector(".nav-toggle__label").textContent = open ? "Menu" : "Close";
      nav.classList.toggle("is-open", !open);
      document.body.classList.toggle("nav-open", !open);
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("is-open")) toggle.click();
    });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 900 && nav.classList.contains("is-open")) toggle.click();
    });
  }

  /* ---------- Header: border on scroll ---------- */
  var header = document.querySelector(".site-header");
  if (header) {
    var onScroll = function () { header.classList.toggle("is-scrolled", window.scrollY > 8); };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  /* ---------- FAQ accordion ---------- */
  document.querySelectorAll(".faq__q").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var expanded = btn.getAttribute("aria-expanded") === "true";
      btn.setAttribute("aria-expanded", String(!expanded));
      var panel = document.getElementById(btn.getAttribute("aria-controls"));
      if (panel) panel.classList.toggle("is-open", !expanded);
    });
  });

  /* ---------- Forms ----------
     Forms with data-form-name post natively to Web3Forms (action + hidden
     access_key), which emails the submission and redirects to /thanks/.
     JS only validates and fills the redirect URL. To change the destination
     inbox, create a new key at web3forms.com and replace access_key. */
  document.querySelectorAll("form[data-gfm-form]").forEach(function (form) {
    var status = form.querySelector(".form__status");

    var showStatus = function (msg, isError) {
      if (!status) return;
      status.textContent = msg;
      status.classList.add("is-visible");
      status.classList.toggle("form__status--error", !!isError);
      status.setAttribute("tabindex", "-1");
      status.focus();
    };

    var validate = function () {
      var valid = true;
      form.querySelectorAll(".field").forEach(function (field) {
        var input = field.querySelector("input, select, textarea");
        if (!input) return;
        var ok = input.checkValidity();
        field.classList.toggle("is-invalid", !ok);
        input.setAttribute("aria-invalid", String(!ok));
        if (!ok && valid) { input.focus(); valid = false; }
      });
      return valid;
    };

    form.setAttribute("novalidate", "");
    form.addEventListener("input", function (e) {
      var field = e.target.closest(".field");
      if (field && field.classList.contains("is-invalid") && e.target.checkValidity()) {
        field.classList.remove("is-invalid");
        e.target.setAttribute("aria-invalid", "false");
      }
    });

    form.addEventListener("submit", function (e) {
      var hp = form.querySelector('[name="botcheck"]');
      if (hp && hp.checked) { e.preventDefault(); return; } // bot
      if (!validate()) {
        e.preventDefault();
        showStatus("Some fields need attention. Please check the highlighted fields and try again.", true);
        return;
      }
      var button = form.querySelector('[type="submit"]');

      // Netlify Forms: let the browser submit natively (POST, urlencoded). Netlify
      // records the submission, emails it, and redirects to the form's action page.
      if (form.hasAttribute("data-form-name")) {
        var redir = form.querySelector('input[name="redirect"]');
        if (redir) redir.value = window.location.origin + "/thanks/"; // works on preview and live domains
        button.disabled = true;
        button.textContent = "Sending…";
        return; // no preventDefault — native submit proceeds
      }

      // Custom endpoint (Formspree, HubSpot, serverless): POST JSON via fetch.
      e.preventDefault();
      var endpoint = form.getAttribute("data-endpoint");
      if (!endpoint) { showStatus("This form isn't connected yet, so your enquiry has not been sent.", true); return; }
      var data = {}; new FormData(form).forEach(function (v, k) { data[k] = v; });
      data.page = window.location.pathname; data.submittedAt = new Date().toISOString();
      button.disabled = true;
      fetch(endpoint, { method: "POST", headers: { "Content-Type": "application/json", "Accept": "application/json" }, body: JSON.stringify(data) })
        .then(function (r) { if (!r.ok) throw new Error("HTTP " + r.status); form.reset(); showStatus("Thanks — we've received your message and will be in touch shortly."); })
        .catch(function (err) { showStatus("Something went wrong and your message wasn't sent. Please try again. (" + err.message + ")", true); })
        .finally(function () { button.disabled = false; });
    });
  });

  /* ---------- Quote form: conditional field ---------- */
  var providerRadios = document.querySelectorAll('input[name="current_provider"]');
  var providerDetail = document.getElementById("field-current-provider-detail");
  if (providerRadios.length && providerDetail) {
    var syncProvider = function () {
      var yes = document.querySelector('input[name="current_provider"]:checked');
      providerDetail.hidden = !(yes && yes.value === "Yes");
    };
    providerRadios.forEach(function (r) { r.addEventListener("change", syncProvider); });
    syncProvider();
  }
})();
