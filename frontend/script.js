/* PharmaStock front-end — talks to the Flask API in app.py */
(async () => {
  "use strict";

  // ------------------------------------------------------------------ icons (Lucide-style)
  const ICONS = {
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
    upload: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
    download: '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
    switch: '<path d="m16 3 4 4-4 4"/><path d="M20 7H4"/><path d="m8 21-4-4 4-4"/><path d="M4 17h16"/>',
    chevronDown: '<path d="m6 9 6 6 6-6"/>',
    chevronLeft: '<path d="m15 18-6-6 6-6"/>',
    chevronRight: '<path d="m9 18 6-6-6-6"/>',
    sort: '<path d="m21 16-4 4-4-4"/><path d="M17 20V4"/><path d="m3 8 4-4 4 4"/><path d="M7 4v16"/>',
    up: '<path d="m5 12 7-7 7 7"/><path d="M12 19V5"/>',
    down: '<path d="m19 12-7 7-7-7"/><path d="M12 5v14"/>',
    store: '<path d="M3 10 12 3l9 7v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M9 22v-8h6v8"/>',
    box: '<path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/><path d="M12 22V12"/><path d="m3.3 7 8.7 5 8.7-5"/>',
    globe: '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    activity: '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    tag: '<path d="M12.6 2.6A2 2 0 0 0 11.2 2H4a2 2 0 0 0-2 2v7.2a2 2 0 0 0 .6 1.4l8.7 8.7a2.4 2.4 0 0 0 3.4 0l6.6-6.6a2.4 2.4 0 0 0 0-3.4z"/><circle cx="7.5" cy="7.5" r="1"/>',
    layers: '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    building: '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01M12 6h.01M16 6h.01M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01"/>',
    flask: '<path d="M10 2v7.3"/><path d="M14 9.3V2"/><path d="M8.5 2h7"/><path d="M14 9.3a6.5 6.5 0 1 1-4 0"/><path d="M5.5 16h13"/>',
    calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
    file: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8M16 17H8M10 9H8"/>',
    alphabet: '<path d="m3 15 4-8 4 8"/><path d="M4 13h6"/><path d="M15 11h4.5a2 2 0 0 1 0 4H15V7h4a2 2 0 0 1 0 4"/>',
    x: '<path d="M18 6 6 18M6 6l12 12"/>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
    cloud: '<path d="M17.5 19H9a7 7 0 1 1 6.71-9h1.79a4.5 4.5 0 1 1 0 9Z"/>',
    database: '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    arrowRight: '<path d="M5 12h14M12 5l7 7-7 7"/>',
    eye: '<path d="M2.06 12.35a1 1 0 0 1 0-.7 10.75 10.75 0 0 1 19.88 0 1 1 0 0 1 0 .7 10.75 10.75 0 0 1-19.88 0"/><circle cx="12" cy="12" r="3"/>',
    eyeOff: '<path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c4.84 0 8.29 3.13 9.94 7a10.8 10.8 0 0 1-1.44 2.49"/><path d="M14.08 14.16a3 3 0 0 1-4.17-4.17"/><path d="M17.48 17.5A10.75 10.75 0 0 1 2.06 12a10.8 10.8 0 0 1 4.45-5.48"/><path d="m2 2 20 20"/>',
    key: '<rect x="3" y="11" width="18" height="11" rx="2.5"/><path d="M7 11V7.5a5 5 0 0 1 9.6-1.9"/><circle cx="12" cy="16.5" r="1.4"/><path d="M12 17.9v1.6"/>',
    chart: '<path d="M3 3v18h18"/><path d="M7 16v-4M12 16V8M17 16v-7"/>',
    history: '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l4 2"/>',
    trash: '<path d="M3 6h18"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/><path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M10 11v6M14 11v6"/>',
    alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4Z"/>',
  };
  const icon = (name) => `<svg class="ic" viewBox="0 0 24 24" aria-hidden="true">${ICONS[name] || ""}</svg>`;
  // Glossy 3D artwork for the logo and the table icon. Each copy gets its own gradient ids,
  // because gradients defined inside a hidden screen would not render elsewhere.
  let artSeq = 0;
  function capsule(u) {
    return `<defs>
      <linearGradient id="cw${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#eceaff"/><stop offset="1" stop-color="#bdb9f5"/></linearGradient>
      <linearGradient id="cl${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#d4d1ff"/><stop offset=".5" stop-color="#a6a2f6"/><stop offset="1" stop-color="#6c67d8"/></linearGradient>
      <filter id="cs${u}" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="3" stdDeviation="2.4" flood-color="#04061c" flood-opacity=".55"/></filter>
    </defs>
    <g transform="rotate(-45 32 32)" filter="url(#cs${u})">
      <rect x="9" y="21" width="46" height="22" rx="11" fill="url(#cw${u})"/>
      <path d="M32 21h12a11 11 0 0 1 0 22H32z" fill="url(#cl${u})"/>
      <path d="M32 21v22" stroke="#7d79e0" stroke-opacity=".45" stroke-width="1"/>
      <rect x="13" y="24.5" width="16" height="4.2" rx="2.1" fill="#fff" opacity=".95"/>
      <rect x="35" y="24.5" width="13" height="3.4" rx="1.7" fill="#fff" opacity=".5"/>
    </g>`;
  }
  const ART = {
    orb(u) {
      return `<svg viewBox="0 0 64 64" aria-hidden="true"><defs>
        <radialGradient id="ob${u}" cx=".32" cy=".28" r=".85"><stop offset="0" stop-color="#7b78ea"/><stop offset=".55" stop-color="#4a48b8"/><stop offset="1" stop-color="#262770"/></radialGradient>
        <linearGradient id="or${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#c9c6ff" stop-opacity=".9"/><stop offset="1" stop-color="#6d6ad8" stop-opacity=".25"/></linearGradient></defs>
        <circle cx="32" cy="32" r="30" fill="url(#ob${u})"/>
        <circle cx="32" cy="32" r="29.2" fill="none" stroke="url(#or${u})" stroke-width="1.6"/>
        <ellipse cx="24" cy="15" rx="14" ry="6" fill="#fff" opacity=".12"/>
        <g transform="translate(32 32) scale(.78) translate(-32 -32)">${capsule(u)}</g></svg>`;
    },
    pill(u) { return `<svg viewBox="0 0 64 64" aria-hidden="true">${capsule(u)}</svg>`; },
    cross(u) {
      return `<svg viewBox="0 0 64 64" aria-hidden="true"><defs>
        <radialGradient id="xb${u}" cx=".32" cy=".28" r=".9"><stop offset="0" stop-color="#7b78ea"/><stop offset=".55" stop-color="#4a48b8"/><stop offset="1" stop-color="#262770"/></radialGradient>
        <linearGradient id="xw${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#eceaff"/><stop offset="1" stop-color="#bdb9f5"/></linearGradient>
        <filter id="xs${u}" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="2.5" stdDeviation="2" flood-color="#04061c" flood-opacity=".5"/></filter></defs>
        <rect x="3" y="3" width="58" height="58" rx="18" fill="url(#xb${u})"/>
        <rect x="3.7" y="3.7" width="56.6" height="56.6" rx="17.3" fill="none" stroke="#c9c6ff" stroke-opacity=".5" stroke-width="1.4"/>
        <ellipse cx="24" cy="14" rx="15" ry="6" fill="#fff" opacity=".1"/>
        <path d="M26 14h12v12h12v12H38v12H26V38H14V26h12Z" fill="url(#xw${u})" filter="url(#xs${u})"/>
        <path d="M26 14h12v12h12v6H14v-6h12Z" fill="#fff" opacity=".35"/></svg>`;
    },
    cube(u) {
      // C2 · glowing cube — no tile behind it
      return `<svg viewBox="0 0 40 40" aria-hidden="true"><defs>
        <radialGradient id="cg${u}" cx=".5" cy=".55" r=".5"><stop offset="0" stop-color="#9d9af4" stop-opacity=".55"/><stop offset="1" stop-color="#9d9af4" stop-opacity="0"/></radialGradient>
        <linearGradient id="ct${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f1f0ff"/><stop offset="1" stop-color="#c3c0ff"/></linearGradient>
        <linearGradient id="cl${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#aaa6f8"/><stop offset="1" stop-color="#6e6ad9"/></linearGradient>
        <linearGradient id="cr${u}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7f7be6"/><stop offset="1" stop-color="#46429f"/></linearGradient></defs>
        <circle cx="20" cy="22" r="19" fill="url(#cg${u})"/>
        <path d="M20 6 33 13.5 20 21 7 13.5Z" fill="url(#ct${u})"/>
        <path d="M7 13.5 20 21V35L7 27.5Z" fill="url(#cl${u})"/>
        <path d="M33 13.5V27.5L20 35V21Z" fill="url(#cr${u})"/>
        <path d="M11 12 24 19.5" stroke="#fff" stroke-opacity=".6" stroke-width="1.3" stroke-linecap="round"/></svg>`;
    },
  };

  function hydrate(root = document) {
    root.querySelectorAll("i[data-icon]").forEach((el) => { el.outerHTML = icon(el.dataset.icon); });
    root.querySelectorAll("[data-logo]").forEach((el) => {
      if (!el.firstChild) el.innerHTML = (ART[el.dataset.logo] || ART.cross)(++artSeq);
    });
  }

  // ------------------------------------------------------------------ helpers
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => [...document.querySelectorAll(s)];
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const cap = (s) => (s ? String(s).charAt(0).toUpperCase() + String(s).slice(1) : "");
  // Highlight the current search text inside a value (escapes everything else).
  function hl(v) {
    const text = String(v ?? "");
    const q = state.q;
    if (!q) return esc(text);
    const re = new RegExp(q.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"), "gi");
    let out = "", last = 0;
    for (const m of text.matchAll(re)) {
      out += esc(text.slice(last, m.index)) + `<mark>${esc(m[0])}</mark>`;
      last = m.index + m[0].length;
    }
    return out + esc(text.slice(last));
  }
  // Under the name, say where the search matched when it wasn't the name itself.
  function matchNote(r) {
    const q = state.q.toLowerCase();
    if (!q || r.med_name.toLowerCase().includes(q)) return "";
    const where = [["Ingredient", r.ingredients], ["Illness", r.illness_name], ["Pharma", r.pharma_name],
      ["Type", r.type], ["Form", r.form]].filter(([, v]) => (v || "").toLowerCase().includes(q)).map(([k]) => k);
    return where.length ? `<span class="sub match-note">Matched in ${esc(where.join(", ").toLowerCase())}</span>` : "";
  }
  const money = (v) => (v == null ? "—" : Number(v).toFixed(2));
  const debounce = (fn, ms) => { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; };
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem("pharmastock." + k)); } catch { return null; } },
    set(k, v) { try { localStorage.setItem("pharmastock." + k, JSON.stringify(v)); } catch { /* ignore */ } },
    del(k) { try { localStorage.removeItem("pharmastock." + k); } catch { /* ignore */ } },
  };

  async function api(url, opts = {}) {
    const res = await fetch(url, opts);
    const data = await res.json().catch(() => ({}));
    if (res.status === 401 && data.signed_out && state.pharmacy) { signedOut("Your sign-in expired. Please sign in again."); }
    if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
    return data;
  }
  const json = (body) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

  function toast(msg, isError = false) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.toggle("error", isError);
    t.hidden = false;
    clearTimeout(toast.t);
    toast.t = setTimeout(() => { t.hidden = true; }, 3800);
  }

  // ------------------------------------------------------------------ configuration
  // Warning limits per medicine form — loaded from app.py (FORM_LIMITS) at start-up.
  let limits = { forms: {}, default: { qty_yellow: 25, qty_red: 10, exp_yellow: 60, exp_red: 30 } };
  const limitsFor = (form) => limits.forms[String(form || "").toLowerCase()] || limits.default;
  function daysLeft(iso) {
    const [y, m, d] = iso.split("-").map(Number);
    const now = new Date();
    return Math.round((Date.UTC(y, m - 1, d) - Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())) / 864e5);
  }
  // "lvl-red" / "lvl-yellow" / "" for a quantity or an expiry date of a given form.
  function qtyLevel(qty, form) {
    if (qty == null || qty === "") return "";
    const l = limitsFor(form);
    return qty < l.qty_red ? "lvl-red" : qty < l.qty_yellow ? "lvl-yellow" : "";
  }
  function expLevel(date, form) {
    if (!date) return "";
    const l = limitsFor(form);
    const left = daysLeft(date);
    return left <= l.exp_red ? "lvl-red" : left <= l.exp_yellow ? "lvl-yellow" : "";
  }

  // Inline-editable table cell (price / quantity / expiry date): saves on Enter or when leaving the field.
  function editCell(r, field, value, o = {}) {
    return `<input class="cell-edit ${o.cls || ""}" type="${o.type || "number"}" value="${esc(value)}"
      data-id="${r.med_id}" data-field="${field}" data-form="${esc(r.form || "")}" data-orig="${esc(value)}"
      ${o.step ? `step="${o.step}"` : ""} ${o.min ? `min="${o.min}"` : ""} ${o.size ? `style="width:${o.size + 4}ch"` : ""}
      aria-label="${field.replace("_", " ")} of ${esc(r.med_name)}">`;
  }

  const TABS = {
    med: {
      label: "Medicines", single: "Medicine", search: "Search medicines, names, ingredients…",
      orders: [["id", "ID (Default)"], ["alphabet", "Alphabet"], ["price", "Price"], ["schedule", "Schedule"]],
      cols: [
        ["id", "ID", (r) => r.med_id],
        ["name", "Name", (r) => hl(r.med_name) + matchNote(r), "name"],
        ["price", "Price ($)", (r) => editCell(r, "price", money(r.price), { step: "0.01", min: "0", size: 7 }), "edit"],
        ["quantity", "Quantity", (r) => editCell(r, "quantity", r.quantity ?? "", {
          step: "1", min: "0", size: 5, cls: qtyLevel(r.quantity, r.form),
        }), "edit"],
        ["illness", "Illness", (r) => hl(r.illness_name || "—")],
        ["type", "Type", (r) => hl(cap(r.type) || "—")],
        ["form", "Form", (r) => hl(cap(r.form) || "—")],
        ["pharma", "Pharma", (r) => hl(r.pharma_name || "—")],
        ["country", "Country", (r) => esc(r.pharma_country || "—")],
        ["ingredients", "Ingredients", (r) => hl(r.ingredients || "—"), "wrap"],
        ["dosage", "Dosage", (r) => `${esc(r.dosage_strength || "—")}${r.times_per_day ? `<span class="sub">${r.times_per_day}× a day</span>` : ""}`],
        ["expiry", "Expiry Date", (r) => editCell(r, "expiry_date", r.expiry_date || "", {
          type: "date", cls: expLevel(r.expiry_date, r.form),
        }), "edit"],
        ["rx", "Pre Required", (r) => (r.prescription_required ? '<span class="pill yes">Yes</span>' : '<span class="pill no">No</span>')],
      ],
      fields: [
        ["med_name", "Name", "text", { required: true }],
        ["price", "Price", "number", { required: true, step: "0.01", min: "0" }],
        ["quantity", "Quantity", "number", { min: "0", step: "1", value: "0" }],
        ["illness_name", "Illness", "text", { list: "illness" }],
        ["type", "Type", "text", { list: "type", placeholder: "vitamin, probiotic, painkiller…" }],
        ["form", "Form", "text", { list: "form", placeholder: "tablet, capsule, syrup…" }],
        ["pharma_name", "Pharma", "text", { list: "pharma" }],
        ["pharma_country", "Country (new pharma only)", "text", { list: "country" }],
        ["ingredients", "Ingredients (comma separated)", "text", { list: "ingredient", full: true }],
        ["dosage_strength", "Dosage", "text", { placeholder: "500 mg" }],
        ["times_per_day", "Schedule (times a day)", "number", { min: "1", max: "10", step: "1" }],
        ["expiry_date", "Expiry date", "date", {}],
        ["prescription_required", "Prescription required", "checkbox", {}],
      ],
    },
    pharma: {
      label: "Pharma", single: "Pharma", search: "Search pharma companies, countries…",
      orders: [["id", "ID (Default)"], ["alphabet", "Alphabet"], ["country", "Country"], ["market_value", "Market value"]],
      cols: [
        ["id", "ID", (r) => r.pharma_id],
        ["name", "Name", (r) => hl(r.pharma_name), "name"],
        ["country", "Country", (r) => esc(r.pharma_country || "—")],
        ["market_value", "Market Value ($M)", (r) => (r.pharma_market_value == null ? "—" : Number(r.pharma_market_value).toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 })), "num"],
        ["created", "Created", (r) => r.pharma_origin_year ?? "—", "num"],
      ],
      fields: [
        ["pharma_name", "Name", "text", { required: true }],
        ["pharma_country", "Country", "text", { list: "country" }],
        ["pharma_market_value", "Market value", "number", { step: "0.01", min: "0" }],
        ["pharma_origin_year", "Created (year)", "number", { min: "1800", max: "2100", step: "1" }],
      ],
    },
    ingredient: {
      label: "Ingredients", single: "Ingredient", search: "Search ingredients, types…",
      orders: [["id", "ID (Default)"], ["alphabet", "Alphabet"], ["value", "Value"], ["type", "Type"]],
      cols: [
        ["id", "ID", (r) => r.ingredient_id],
        ["name", "Name", (r) => hl(r.ingredient_name), "name"],
        ["value", "Value", (r) => money(r.ingredient_value), "num"],
        ["type", "Type", (r) => esc(cap(r.ingredient_type) || "—")],
      ],
      fields: [
        ["ingredient_name", "Name", "text", { required: true }],
        ["ingredient_value", "Value", "number", { step: "0.01", min: "0" }],
        ["ingredient_type", "Type", "text", { placeholder: "vitamin, probiotic, painkiller…" }],
      ],
    },
    illness: {
      label: "Illnesses", single: "Illness", search: "Search illnesses, types…",
      orders: [["id", "ID (Default)"], ["alphabet", "Alphabet"], ["value", "Value"]],
      cols: [
        ["id", "ID", (r) => r.illness_id],
        ["name", "Name", (r) => hl(r.illness_name), "name"],
        ["type", "Type", (r) => esc(cap(r.illness_type) || "—")],
        ["danger", "Danger", (r) => (r.illness_danger_level ? `<span class="pill ${esc(r.illness_danger_level)}">${esc(cap(r.illness_danger_level))}</span>` : "—")],
        ["rx", "Pre Required", (r) => (r.illness_pre_required ? '<span class="pill yes">Yes</span>' : '<span class="pill no">No</span>')],
      ],
      fields: [
        ["illness_name", "Name", "text", { required: true }],
        ["illness_type", "Type", "text", { placeholder: "allergy, pain, digestive…" }],
        ["illness_danger_level", "Danger level", "select", { options: ["low", "moderate", "high"] }],
        ["illness_pre_required", "Meds need a prescription", "checkbox", {}],
      ],
    },
  };

  const CATEGORIES = [
    ["illness", "Illness", "activity"], ["type", "Type", "tag"],
    ["form", "Form", "layers"], ["pharma", "Pharma", "building"], ["country", "Country", "globe"],
    ["ingredients", "Ingredients", "flask"], ["stock_status", "Stock Status", "box"],
    ["expiry_status", "Expiry Status", "calendar"], ["prescription", "Prescription", "file"],
  ];

  // ------------------------------------------------------------------ state
  const state = {
    pharmacy: null,
    stock: store.get("stock") || "web",
    tab: "med", q: "", watch: false, order: "id", showBy: "alphabet", group: null,
    sort: null, dir: "asc", page: 1, perPage: 10,
    groups: [], groupsOpen: true,
  };
  let lookups = null;
  let loadSeq = 0;

  function showScreen(id) {
    $$(".screen").forEach((s) => s.classList.toggle("active", s.id === id));
    window.scrollTo(0, 0);
  }

  // ------------------------------------------------------------------ screen 1 & 2
  async function loadPharmacyList() {
    try {
      const list = await api("/api/pharmacies");
      $("#pharmacy-list").innerHTML = list.map((n) => `<option value="${esc(n)}">`).join("");
    } catch { /* optional */ }
  }

  // Sign-in: step 1 = pharmacy name, step 2 = password ("login", "set" = first password, "create" = new pharmacy)
  let signStep = "name";
  function showSignStep(step, name) {
    signStep = step;
    const pw = step !== "name";
    $("#pw-step").hidden = !pw;
    $("#pw-confirm-wrap").hidden = step === "name" || step === "login";
    $("#pw-back").hidden = !pw;
    $("#pharmacy-input").readOnly = pw;
    $("#pw-input").value = ""; $("#pw-confirm").value = "";
    $("#pw-input").autocomplete = step === "login" ? "current-password" : "new-password";
    const hints = {
      login: `Enter the password for ${name}.`,
      set: `${name} has no password yet. Create one (at least 8 characters) — you'll use it from now on.`,
      create: `${name} is a new pharmacy. Create a password (at least 8 characters). It starts with the demo stock.`,
    };
    $("#pw-hint").textContent = hints[step] || "";
    $("#pharmacy-submit-label").textContent = { name: "Continue", login: "Sign in", set: "Save password", create: "Create pharmacy" }[step];
    if (pw) $("#pw-input").focus();
  }
  function signedOut(message = "") {
    state.pharmacy = null;
    $$(".modal").forEach((m) => { m.hidden = true; });
    $("#pharmacy-input").value = "";
    showSignStep("name");
    $("#pharmacy-error").textContent = message;
    loadPharmacyList();
    showScreen("screen-welcome");
  }

  $("#pharmacy-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    $("#pharmacy-error").textContent = "";
    const name = $("#pharmacy-input").value.trim();
    try {
      if (signStep === "name") {
        const r = await api("/api/pharmacy/check", json({ name }));
        $("#pharmacy-input").value = r.name;
        showSignStep(r.step, r.name);
        return;
      }
      const password = $("#pw-input").value;
      if (signStep !== "login") {
        if (password.length < 8) { $("#pharmacy-error").textContent = "Password must be at least 8 characters."; return; }
        if (password !== $("#pw-confirm").value) { $("#pharmacy-error").textContent = "The two passwords don't match."; return; }
      }
      const p = await api("/api/login", json({ name, password, confirm: $("#pw-confirm").value }));
      state.pharmacy = p;
      showSignStep("name");
      $("#intro-pharmacy").textContent = p.pharmacy_name;
      showScreen("screen-intro");
    } catch (err) {
      $("#pharmacy-error").textContent = err.message === "Failed to fetch" ? "Cannot reach the server — is app.py running?" : err.message;
    }
  });
  $("#pw-back").addEventListener("click", () => { $("#pharmacy-error").textContent = ""; showSignStep("name"); $("#pharmacy-input").focus(); });

  // Show / hide password (eye button)
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-eye]");
    if (!b) return;
    const input = document.getElementById(b.dataset.eye);
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    b.innerHTML = icon(show ? "eyeOff" : "eye");
    b.setAttribute("aria-label", show ? "Hide password" : "Show password");
  });

  $$("[data-pick]").forEach((b) => b.addEventListener("click", () => openApp(b.dataset.pick)));

  function openApp(stock) {
    setStock(stock, false);
    $("#pharmacy-name").textContent = state.pharmacy.pharmacy_name;
    $("#avatar").textContent = state.pharmacy.pharmacy_name.trim().charAt(0).toUpperCase();
    showScreen("app");
    renderChrome();
    refresh();
  }

  // ------------------------------------------------------------------ dashboard chrome
  function setStock(stock, reload = true) {
    state.stock = stock === "local" ? "local" : "web";
    store.set("stock", state.stock);
    state.page = 1; state.group = null;
    $$("[data-stock]").forEach((b) => b.classList.toggle("active", b.dataset.stock === state.stock));
    const local = state.stock === "local";
    if (!local && state.watch) { state.watch = false; }
    $("#btn-watch").classList.toggle("active", state.watch);
    $("#btn-watch").setAttribute("aria-pressed", String(state.watch));
    for (const id of ["#btn-import", "#btn-download", "#btn-delete", "#btn-watch"]) {
      $(id).disabled = !local;
      $(id).title = local ? "" : "Available in Local Stock";
    }
    if (reload) { renderChrome(); refresh(); }
  }

  function renderChrome() {
    const t = TABS[state.tab];
    $$("[data-tab]").forEach((b) => b.classList.toggle("active", b.dataset.tab === state.tab));
    $("#search").placeholder = t.search;
    $("#order-by").innerHTML = t.orders.map(([v, l]) => `<option value="${v}">${l}</option>`).join("");
    $("#order-by").value = state.order;
    $("#btn-add-label").textContent = `Add ${t.single}`;
    $("#show-by").value = state.showBy;
    const isMed = state.tab === "med";
    $("#show-by").disabled = !isMed;
    $("#category-note").hidden = isMed;
    $("#cat-list").style.opacity = isMed ? "" : ".45";
    renderCategories();
  }

  function renderCategories() {
    const isMed = state.tab === "med";
    $("#cat-list").innerHTML = CATEGORIES.map(([key, label, ic]) => {
      const active = isMed && key === state.showBy;
      let groups = "";
      if (active && state.groupsOpen && state.groups.length) {
        groups = `<ul class="groups">${state.groups.map((g) => `
          <li><button data-group="${esc(g.name)}" class="${g.name === state.group ? "active" : ""}">
            <span>${esc(cap(g.name))}</span><span class="count">${g.count}</span></button></li>`).join("")}</ul>`;
      }
      return `<li class="${active ? "active" : ""}"><button data-cat="${key}" ${isMed ? "" : "disabled"}>${icon(ic)} ${label}</button>${groups}</li>`;
    }).join("");
  }

  $("#cat-list").addEventListener("click", (e) => {
    const g = e.target.closest("[data-group]");
    if (g) {
      state.group = state.group === g.dataset.group ? null : g.dataset.group;
      state.page = 1;
      renderCategories();
      loadRows();
      return;
    }
    const c = e.target.closest("[data-cat]");
    if (!c) return;
    if (c.dataset.cat === state.showBy) { state.groupsOpen = !state.groupsOpen; renderCategories(); return; }
    setShowBy(c.dataset.cat);
  });
  $("#show-by").addEventListener("change", (e) => setShowBy(e.target.value));

  function setShowBy(v) {
    state.showBy = v; state.group = null; state.page = 1; state.groupsOpen = true;
    $("#show-by").value = v;
    refresh();
  }

  $$("[data-stock]").forEach((b) => b.addEventListener("click", () => setStock(b.dataset.stock)));
  $("#switch-stock").addEventListener("click", () => setStock(state.stock === "local" ? "web" : "local"));

  $$("[data-tab]").forEach((b) => b.addEventListener("click", () => {
    if (b.dataset.tab === state.tab) return;
    state.tab = b.dataset.tab;
    state.order = "id"; state.sort = null; state.page = 1; state.group = null;
    renderChrome();
    refresh();
  }));

  $("#search").addEventListener("input", debounce((e) => {
    state.q = e.target.value.trim(); state.page = 1;
    refresh();
  }, 250));
  $("#order-by").addEventListener("change", (e) => {
    state.order = e.target.value; state.sort = null; state.page = 1;
    loadRows();
  });

  $("#pharmacy-btn").addEventListener("click", (e) => { e.stopPropagation(); $("#pharmacy-menu").hidden = !$("#pharmacy-menu").hidden; });
  document.addEventListener("click", () => { $("#pharmacy-menu").hidden = true; });
  $("#btn-sign-out").addEventListener("click", async () => {
    try { await api("/api/logout", { method: "POST" }); } catch { /* signed out anyway */ }
    signedOut();
  });
  $("#btn-change-pw").addEventListener("click", () => {
    $("#password-form").reset();
    $("#password-error").textContent = "";
    $$("#password-form input").forEach((i) => { i.type = "password"; });
    $$("#password-form [data-eye]").forEach((b) => { b.innerHTML = icon("eye"); });
    openModal("#modal-password");
  });
  $("#password-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = { current: $("#pw-current").value, new: $("#pw-new").value, confirm: $("#pw-new2").value };
    if (body.new !== body.confirm) { $("#password-error").textContent = "The two new passwords don't match."; return; }
    try {
      await api("/api/password", json(body));
      closeModal(e.target);
      toast("Password changed");
    } catch (err) { $("#password-error").textContent = err.message; }
  });

  // ------------------------------------------------------------------ data loading
  function params(extra = {}) {
    const p = new URLSearchParams({
      stock: state.stock, pharmacy_id: state.pharmacy?.pharmacy_id ?? 0,
      q: state.q, order: state.order, page: state.page, per_page: state.perPage,
    });
    if (state.tab === "med") p.set("show_by", state.showBy);
    if (state.tab === "med" && state.watch) p.set("watch", "1");
    if (state.sort) { p.set("sort", state.sort); p.set("dir", state.dir); }
    for (const [k, v] of Object.entries(extra)) { if (v == null) p.delete(k); else p.set(k, v); }
    return p;
  }

  function refresh() {
    loadRows();
    if (state.tab === "med") loadGroups(); else { state.groups = []; renderCategories(); }
  }

  async function loadGroups() {
    try {
      state.groups = await api("/api/meds/groups?" + params({ page: null, per_page: null, sort: null, dir: null }));
    } catch { state.groups = []; }
    renderCategories();
  }

  async function loadRows() {
    const seq = ++loadSeq;
    const t = TABS[state.tab];
    const url = state.tab === "med" ? "/api/meds?" : `/api/table/${state.tab}?`;
    const extra = state.tab === "med" && state.group != null ? { group: state.group } : {};
    $(".table-card").classList.add("loading");
    $("#table-title").textContent = `${state.stock === "local" ? "Local" : "Web"} Stock — ${t.label}`;
    renderHead();
    renderChip();
    try {
      const data = await api(url + params(extra));
      if (seq !== loadSeq) return;
      renderBody(data);
      renderPager(data.total);
      const from = data.total ? (data.page - 1) * data.per_page + 1 : 0;
      const to = Math.min(data.page * data.per_page, data.total);
      $("#showing").textContent = `Showing ${from}–${to} of ${data.total.toLocaleString()}`;
    } catch (err) {
      if (seq !== loadSeq) return;
      $("#tbody").innerHTML = "";
      showEmpty(`<strong>Could not load data</strong>${esc(err.message === "Failed to fetch" ? "Cannot reach the server — is app.py running?" : err.message)}`);
      $("#pager").innerHTML = "";
      $("#showing").textContent = "";
    } finally {
      if (seq === loadSeq) $(".table-card").classList.remove("loading");
    }
  }

  function renderChip() {
    const chips = [];
    if (state.tab === "med" && state.watch) {
      chips.push(`<span class="chip chip-warn">${icon("alert")} Watchlist · most urgent first <button data-clear="watch" aria-label="Turn off Watchlist">${icon("x")}</button></span>`);
    }
    if (state.tab === "med" && state.group != null) {
      const label = CATEGORIES.find((c) => c[0] === state.showBy)?.[1] || "";
      chips.push(`<span class="chip">${esc(label)}: ${esc(cap(state.group))} <button data-clear="group" aria-label="Clear filter">${icon("x")}</button></span>`);
    }
    $("#filter-chip").innerHTML = chips.join("");
    $("#filter-chip").hidden = !chips.length;
  }

  // Watchlist: show only medicines with a red or yellow warning (Local Stock only)
  function setWatch(on) {
    state.watch = on;
    $("#btn-watch").classList.toggle("active", on);
    $("#btn-watch").setAttribute("aria-pressed", String(on));
    state.page = 1;
    if (on && state.tab !== "med") { state.tab = "med"; state.order = "id"; state.group = null; renderChrome(); }
    refresh();
  }
  async function openWatchlist() {
    openModal("#modal-watch");
    $("#watch-body").innerHTML = '<p class="muted">Loading…</p>';
    try {
      const d = await api(`/api/watchlist?pharmacy_id=${state.pharmacy.pharmacy_id}`);
      const section = (level, title, sub, rows) => `
        <section class="watch-sec watch-${level}">
          <h4><span class="dot"></span>${title} <span class="count">${rows.length}</span></h4>
          <p class="muted small">${sub}</p>
          ${rows.length ? `<div class="table-scroll"><table><thead><tr><th>ID</th><th>Name</th><th>Form</th><th>Quantity</th><th>Expiry Date</th><th>Reason</th></tr></thead><tbody>
            ${rows.map((r) => `<tr><td>${r.med_id}</td><td class="name">${esc(r.med_name)}</td><td>${esc(cap(r.form) || "—")}</td>
              <td class="num"><span class="${qtyLevel(r.quantity, r.form)}">${r.quantity}</span></td>
              <td class="num"><span class="${expLevel(r.expiry_date, r.form)}">${r.expiry_date || "—"}</span></td>
              <td>${esc(r.reasons.join(" · "))}</td></tr>`).join("")}
          </tbody></table></div>` : '<p class="muted small">None.</p>'}
        </section>`;
      const red = d.rows.filter((r) => r.level === "red");
      const yellow = d.rows.filter((r) => r.level === "yellow");
      $("#watch-body").innerHTML = d.rows.length
        ? section("red", "Red", "Out of stock, very low, expired or expiring very soon.", red)
          + section("yellow", "Yellow", "Low stock or expiring soon.", yellow)
        : '<p class="empty"><strong>Nothing on your watchlist</strong>No medicine is low on stock or close to expiring.</p>';
    } catch (err) { $("#watch-body").innerHTML = `<p class="form-error">${esc(err.message)}</p>`; }
  }
  $("#btn-watch").addEventListener("click", openWatchlist);
  $("#filter-chip").addEventListener("click", (e) => {
    const b = e.target.closest("[data-clear]");
    if (!b) return;
    if (b.dataset.clear === "watch") { setWatch(false); return; }
    state.group = null; state.page = 1;
    renderCategories(); loadRows();
  });

  function renderHead() {
    const cols = TABS[state.tab].cols;
    $("#thead").innerHTML = "<tr>" + cols.map(([, label]) => `<th>${esc(label)}</th>`).join("") + "</tr>";
  }

  // inline editing of price / quantity / expiry date
  async function saveCell(input) {
    const value = input.value.trim();
    if (value === input.dataset.orig) return;
    input.disabled = true;
    try {
      const r = await api(`/api/meds/${input.dataset.id}`, {
        method: "PATCH", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ field: input.dataset.field, value, stock: state.stock, pharmacy_id: state.pharmacy.pharmacy_id }),
      });
      const shown = input.dataset.field === "price" ? money(r.value) : (r.value ?? "");
      input.value = input.dataset.orig = shown;
      if (input.dataset.field !== "price") {
        const lvl = input.dataset.field === "quantity" ? qtyLevel(r.value, input.dataset.form) : expLevel(r.value, input.dataset.form);
        input.classList.remove("lvl-red", "lvl-yellow");
        if (lvl) input.classList.add(lvl);
      }
      input.classList.add("saved");
      setTimeout(() => input.classList.remove("saved"), 1200);
      if (state.tab === "med" && ["stock_status", "expiry_status"].includes(state.showBy)) loadGroups();
    } catch (err) {
      input.value = input.dataset.orig;
      toast(err.message, true);
    } finally { input.disabled = false; }
  }
  $("#tbody").addEventListener("change", (e) => { if (e.target.matches(".cell-edit")) saveCell(e.target); });
  $("#tbody").addEventListener("keydown", (e) => {
    if (!e.target.matches(".cell-edit")) return;
    if (e.key === "Enter") { e.preventDefault(); e.target.blur(); }
    if (e.key === "Escape") { e.target.value = e.target.dataset.orig; e.target.blur(); }
  });

  function renderBody(data) {
    const t = TABS[state.tab];
    let html = "";
    for (const r of data.rows) {
      html +="<tr>" + t.cols.map(([, , fmt, cls]) => `<td class="${cls || ""}">${fmt(r)}</td>`).join("") + "</tr>";
    }
    $("#tbody").innerHTML = html;
    if (data.rows.length) { $("#empty").hidden = true; return; }

    if (state.watch && state.tab === "med" && !state.q && state.group == null) {
      showEmpty("<strong>Nothing on your watchlist</strong>No medicine is low on stock or close to expiring.");
    } else if (state.q || state.group != null || state.watch) {
      showEmpty("<strong>No matches</strong>Try a different search or clear the category filter.");
    } else if (state.stock === "local") {
      showEmpty(`<strong>Local stock is empty</strong>Import your Excel, CSV or text file, or add rows by hand.
        <br><button class="btn btn-primary" data-empty-import>${icon("upload")} Import Stock</button>`);
    } else {
      showEmpty("<strong>Web Stock is empty for now</strong>The big medicines dataset will be added here later. You can add rows by hand meanwhile.");
    }
  }
  function showEmpty(html) { $("#empty").innerHTML = html; $("#empty").hidden = false; }
  $("#empty").addEventListener("click", (e) => { if (e.target.closest("[data-empty-import]")) openImport(); });

  function renderPager(total) {
    const pages = Math.max(1, Math.ceil(total / state.perPage));
    const cur = Math.min(state.page, pages);
    const nums = new Set([1, pages, cur - 1, cur, cur + 1]);
    if (cur <= 3) [2, 3, 4, 5].forEach((n) => nums.add(n));
    if (cur >= pages - 2) [pages - 4, pages - 3, pages - 2].forEach((n) => nums.add(n));
    const list = [...nums].filter((n) => n >= 1 && n <= pages).sort((a, b) => a - b);
    let html = `<button data-page="${cur - 1}" ${cur <= 1 ? "disabled" : ""} aria-label="Previous page">${icon("chevronLeft")}</button>`;
    let prev = 0;
    for (const n of list) {
      if (n - prev > 1) html += '<span class="gap">…</span>';
      html += `<button data-page="${n}" class="${n === cur ? "active" : ""}">${n}</button>`;
      prev = n;
    }
    html += `<button data-page="${cur + 1}" ${cur >= pages ? "disabled" : ""} aria-label="Next page">${icon("chevronRight")}</button>`;
    $("#pager").innerHTML = total ? html : "";
  }
  $("#pager").addEventListener("click", (e) => {
    const b = e.target.closest("[data-page]");
    if (!b || b.disabled) return;
    state.page = Number(b.dataset.page);
    loadRows();
    $(".table-card").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  // ------------------------------------------------------------------ modals
  function openModal(id) { $(id).hidden = false; $(id).querySelector("input:not([type=hidden]), select")?.focus(); }
  function closeModal(el) { el.closest(".modal").hidden = true; }
  $$(".modal").forEach((m) => {
    m.addEventListener("click", (e) => { if (e.target === m || e.target.closest("[data-close]")) closeModal(m.firstElementChild); });
  });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") $$(".modal").forEach((m) => { m.hidden = true; }); });

  // add row
  $("#btn-add").addEventListener("click", async () => {
    const t = TABS[state.tab];
    if (!lookups) { try { lookups = await api("/api/lookups"); } catch { lookups = {}; } }
    $("#add-title").textContent = `Add ${t.single}`;
    $("#add-sub").textContent = state.tab === "med"
      ? `Adds to ${state.stock === "local" ? `${state.pharmacy.pharmacy_name}'s Local Stock` : "the Web Stock"}. New pharma, illness and ingredient names are created automatically.`
      : `Adds a new ${t.single.toLowerCase()} to the database.`;
    $("#add-error").textContent = "";
    $("#add-fields").innerHTML = t.fields.map(([name, label, type, o]) => {
      const id = "f-" + name;
      if (type === "checkbox") return `<label class="field check"><input type="checkbox" id="${id}" name="${name}"> ${label}</label>`;
      if (type === "select") {
        return `<div class="field"><label for="${id}">${label}</label><span class="select-wrap"><select id="${id}" name="${name}">
          <option value="">—</option>${o.options.map((v) => `<option value="${v}">${cap(v)}</option>`).join("")}</select>${icon("chevronDown")}</span></div>`;
      }
      const attrs = ["required", "step", "min", "max", "placeholder", "value"].filter((k) => o[k] != null)
        .map((k) => (k === "required" ? "required" : `${k}="${esc(o[k])}"`)).join(" ");
      const list = o.list && lookups[o.list] ? `list="dl-${name}"` : "";
      const dl = list ? `<datalist id="dl-${name}">${lookups[o.list].map((v) => `<option value="${esc(v)}">`).join("")}</datalist>` : "";
      return `<div class="field ${o.full ? "full" : ""}"><label for="${id}">${label}${o.required ? " *" : ""}</label>
        <input id="${id}" name="${name}" type="${type}" ${attrs} ${list} autocomplete="off">${dl}</div>`;
    }).join("");
    openModal("#modal-add");
  });

  $("#add-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {};
    for (const el of e.target.querySelectorAll("[name]")) body[el.name] = el.type === "checkbox" ? el.checked : el.value;
    try {
      if (state.tab === "med") {
        Object.assign(body, { stock: state.stock, pharmacy_id: state.pharmacy.pharmacy_id });
        const r = await api("/api/meds", json(body));
        toast(r.status === "updated" ? "Medicine updated" : "Medicine added");
      } else {
        Object.assign(body, { stock: state.stock, pharmacy_id: state.pharmacy.pharmacy_id });
        await api(`/api/table/${state.tab}`, json(body));
        toast(`${TABS[state.tab].single} added — it shows in this stock once one of its medicines is in it`);
      }
      lookups = null;
      closeModal(e.target);
      refresh();
    } catch (err) { $("#add-error").textContent = err.message; }
  });

  // import
  function openImport() {
    $("#import-form").reset();
    $("#drop-text").textContent = "Choose a file or drop it here";
    $("#import-result").hidden = true;
    $("#import-submit").disabled = false;
    openModal("#modal-import");
  }
  $("#btn-import").addEventListener("click", openImport);
  $("#import-file").addEventListener("change", (e) => { $("#drop-text").textContent = e.target.files[0]?.name || "Choose a file or drop it here"; });
  const drop = $("#drop");
  ["dragenter", "dragover"].forEach((ev) => drop.addEventListener(ev, (e) => { e.preventDefault(); drop.classList.add("over"); }));
  ["dragleave", "drop"].forEach((ev) => drop.addEventListener(ev, () => drop.classList.remove("over")));
  drop.addEventListener("drop", (e) => {
    e.preventDefault();
    if (e.dataTransfer.files.length) { $("#import-file").files = e.dataTransfer.files; $("#drop-text").textContent = e.dataTransfer.files[0].name; }
  });
  $("#import-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const file = $("#import-file").files[0];
    if (!file) return;
    const fd = new FormData();
    fd.append("file", file);
    fd.append("pharmacy_id", state.pharmacy.pharmacy_id);
    fd.append("stock", "local");
    $("#import-submit").disabled = true;
    const box = $("#import-result");
    box.hidden = false;
    box.textContent = "Importing…";
    try {
      const r = await api("/api/import", { method: "POST", body: fd });
      box.innerHTML = `<strong>${r.added}</strong> added · <strong>${r.updated}</strong> updated · <strong>${r.skipped}</strong> skipped
        <div class="muted small">Columns used: ${esc(r.mapped.join(", "))}</div>
        ${r.errors.length ? `<ul>${r.errors.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}`;
      lookups = null;
      refresh();
    } catch (err) {
      box.innerHTML = `<span style="color:var(--red)">${esc(err.message)}</span>`;
    } finally { $("#import-submit").disabled = false; }
  });

  // download
  $("#btn-download").addEventListener("click", () => { $("#download-error").textContent = ""; openModal("#modal-download"); });
  $("#download-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const tables = $$("#download-form input[name=t]:checked").map((c) => c.value);
    if (!tables.length) { $("#download-error").textContent = "Tick at least one table."; return; }
    const a = document.createElement("a");
    a.href = `/api/export?pharmacy_id=${state.pharmacy.pharmacy_id}&tables=${tables.join(",")}`;
    a.download = "";
    document.body.appendChild(a);
    a.click();
    a.remove();
    closeModal(e.target);
  });

  // history
  const HISTORY_KINDS = {
    seed: ["Starter data", "database"], import: ["Import", "upload"], download: ["Download", "download"],
    add: ["Added", "plus"], edit: ["Edited", "edit"], delete: ["Deleted", "trash"],
  };
  let historyRows = [];
  let historyFilter = "all";

  function renderHistory() {
    const rows = historyRows.filter((h) => historyFilter === "all" || h.action === historyFilter
      || (historyFilter === "import" && h.action === "seed"));
    $("#history-filters").innerHTML = [["all", "All"], ["import", "Imports"], ["download", "Downloads"],
      ["add", "Added"], ["edit", "Edited"], ["delete", "Deleted"]]
      .map(([k, l]) => `<button type="button" data-hf="${k}" class="${k === historyFilter ? "active" : ""}">${l}</button>`).join("");
    $("#history-list").innerHTML = rows.length ? rows.map((h) => {
      const [label, ic] = HISTORY_KINDS[h.action] || [h.action, "file"];
      const when = new Date(h.at);
      return `<li class="h-${esc(h.action)}"><span class="h-icon">${icon(ic)}</span>
        <div><p>${esc(h.summary)}</p><span class="muted small">${esc(label)} · ${when.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" })}</span></div></li>`;
    }).join("") : `<li class="h-empty muted">Nothing here yet.</li>`;
  }
  $("#history-filters").addEventListener("click", (e) => {
    const b = e.target.closest("[data-hf]");
    if (b) { historyFilter = b.dataset.hf; renderHistory(); }
  });
  $("#btn-history").addEventListener("click", async () => {
    $("#history-title").textContent = `History — ${state.stock === "local" ? "Local" : "Web"} Stock`;
    historyFilter = "all";
    historyRows = [];
    $("#history-list").innerHTML = '<li class="h-empty muted">Loading…</li>';
    openModal("#modal-history");
    try { historyRows = await api(`/api/history?stock=${state.stock}&pharmacy_id=${state.pharmacy.pharmacy_id}`); }
    catch (err) { toast(err.message, true); }
    renderHistory();
  });

  // delete whole local stock
  $("#btn-delete").addEventListener("click", () => {
    $("#delete-form").reset();
    $("#delete-error").textContent = "";
    $("#delete-name").textContent = state.pharmacy.pharmacy_name;
    $("#delete-submit").disabled = true;
    openModal("#modal-delete");
  });
  $("#delete-confirm").addEventListener("input", (e) => {
    $("#delete-submit").disabled = e.target.value.trim().toLowerCase() !== state.pharmacy.pharmacy_name.trim().toLowerCase();
  });
  $("#delete-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      const r = await api("/api/stock/clear", json({ pharmacy_id: state.pharmacy.pharmacy_id, confirm: $("#delete-confirm").value }));
      closeModal(e.target);
      toast(`Local stock deleted (${r.deleted.toLocaleString()} medicines)`);
      state.page = 1; state.group = null;
      refresh();
    } catch (err) { $("#delete-error").textContent = err.message; }
  });

  // ------------------------------------------------------------------ dashboard
  // Categorical order for forms (validated dark-surface palette); 8th slot is "Other".
  const CAT = ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181", "#008300", "#9085e9"];
  const OTHER = "#6c7086";
  const INK = "#c9cbef", MUTED = "#8b90c2", GRID = "rgba(139,144,194,.16)", SURFACE = "#171b3d";
  const charts = {};
  const fmtMoney = (v) => "$" + Number(v).toLocaleString("en-US", { maximumFractionDigits: 0 });
  const fmtMoneyShort = (v) => (v >= 1e6 ? `$${(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `$${(v / 1e3).toFixed(0)}K` : fmtMoney(v));

  // Keep at most 7 named slices; fold the rest into "Other (n forms)".
  function foldSlices(rows, key) {
    const sorted = [...rows].sort((a, b) => b[key] - a[key]);
    if (sorted.length <= 8) return sorted.map((r) => ({ name: r.name, v: r[key] }));
    const top = sorted.slice(0, 7).map((r) => ({ name: r.name, v: r[key] }));
    const rest = sorted.slice(7);
    top.push({ name: `Other: ${rest.length} more forms`, v: rest.reduce((s, r) => s + r[key], 0), detail: rest.map((r) => r.name).join(", ") });
    return top;
  }

  function draw(id, config) {
    charts[id]?.destroy();
    charts[id] = new Chart(document.getElementById(id), config);
  }

  function pie(id, slices, fmt) {
    const total = slices.reduce((s, x) => s + x.v, 0) || 1;
    draw(id, {
      type: "doughnut",
      data: {
        labels: slices.map((s) => s.name),
        datasets: [{
          data: slices.map((s) => s.v),
          backgroundColor: slices.map((s, i) => (s.name.startsWith("Other") ? OTHER : CAT[i % CAT.length])),
          borderColor: SURFACE, borderWidth: 2, hoverOffset: 6,
        }],
      },
      options: {
        cutout: "58%", maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "right",
            labels: {
              color: INK, boxWidth: 10, boxHeight: 10, usePointStyle: true, pointStyle: "rectRounded", padding: 10,
              generateLabels: (chart) => chart.data.labels.map((l, i) => ({
                text: `${l.length > 22 ? l.slice(0, 21) + "…" : l}  ${fmt(chart.data.datasets[0].data[i])}`,
                fillStyle: chart.data.datasets[0].backgroundColor[i], strokeStyle: "transparent",
                fontColor: INK, index: i, hidden: !chart.getDataVisibility(i),
              })),
            },
          },
          tooltip: { callbacks: {
            label: (c) => ` ${c.label}: ${fmt(c.raw)} (${Math.round((c.raw / total) * 100)}%)`,
            afterLabel: (c) => (slices[c.dataIndex].detail ? ` ${slices[c.dataIndex].detail}` : ""),
          } },
        },
      },
    });
  }

  function hbar(id, rows) {
    draw(id, {
      type: "bar",
      data: { labels: rows.map((r) => r.name), datasets: [{ data: rows.map((r) => r.count), backgroundColor: "#9d9af4", borderRadius: 4, borderSkipped: "start", barPercentage: 0.7, categoryPercentage: 0.9 }] },
      options: {
        indexAxis: "y", maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${c.raw} medicines` } } },
        scales: {
          x: { beginAtZero: true, grid: { color: GRID }, border: { display: false }, ticks: { color: MUTED, precision: 0 } },
          y: { grid: { display: false }, border: { display: false }, ticks: { color: INK, autoSkip: false } },
        },
      },
    });
  }

  function line(id, rows) {
    const labels = rows.map((r) => new Date(r.month + "-01T00:00").toLocaleString("en-US", { month: "short" }));
    draw(id, {
      type: "line",
      data: { labels, datasets: [{ data: rows.map((r) => r.count), borderColor: "#b0adf9", backgroundColor: "#b0adf9", borderWidth: 2, pointRadius: 4, pointHoverRadius: 6, pointBorderColor: SURFACE, pointBorderWidth: 2, tension: 0.25 }] },
      options: {
        maintainAspectRatio: false, interaction: { mode: "index", intersect: false },
        plugins: { legend: { display: false }, tooltip: { callbacks: { label: (c) => ` ${c.raw} medicines expire` } } },
        scales: {
          x: { grid: { display: false }, border: { color: GRID }, ticks: { color: MUTED } },
          y: { beginAtZero: true, grid: { color: GRID }, border: { display: false }, ticks: { color: MUTED, precision: 0 } },
        },
      },
    });
  }

  $("#btn-dashboard").addEventListener("click", async () => {
    $("#dash-title").textContent = `Dashboard — ${state.stock === "local" ? `${state.pharmacy.pharmacy_name}'s Local Stock` : "Web Stock"}`;
    openModal("#modal-dashboard");
    if (!window.Chart) { $("#dash-empty").hidden = false; $("#dash-empty").textContent = "Charts need an internet connection to load the chart library."; return; }
    try {
      const d = await api(`/api/dashboard?stock=${state.stock}&pharmacy_id=${state.pharmacy.pharmacy_id}`);
      const empty = !d.totals.medicines;
      $(".dash-grid").hidden = empty;
      $("#dash-empty").hidden = !empty;
      $("#dash-empty").innerHTML = "<strong>No medicines in this stock yet</strong>Import or add medicines to see the dashboard.";
      if (empty) return;
      $("#dash-total").textContent = d.totals.medicines.toLocaleString();
      $("#dash-total-sub").textContent = `${d.totals.packs.toLocaleString()} packs · ${fmtMoney(d.totals.value)} stock value`;
      $("#dash-expired").textContent = d.expired ? `${d.expired} already expired (not shown)` : "";
      pie("ch-form-count", foldSlices(d.by_form, "count"), (v) => v.toLocaleString());
      pie("ch-form-value", foldSlices(d.by_form, "value"), fmtMoneyShort);
      line("ch-expiry", d.expiry);
      hbar("ch-illness", d.illness);
      hbar("ch-type", d.by_type);
    } catch (err) { toast(err.message, true); }
  });

  // ------------------------------------------------------------------ boot
  hydrate();
  try { limits = await api("/api/form-limits"); } catch { /* keep defaults */ }
  store.del("pharmacy"); // older versions remembered the pharmacy in the browser; the server session does that now
  try {
    state.pharmacy = await api("/api/me"); // still signed in (30-day session)?
    openApp(state.stock);
  } catch {
    loadPharmacyList();
  }
})();
