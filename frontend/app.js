(() => {
"use strict";

const LANGS = {en: "English", hi: "हिन्दी", ta: "தமிழ்"};
const SPEECH = {en: "en-IN", hi: "hi-IN", ta: "ta-IN"};
const STATES = ["Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa","Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala","Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland","Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura","Uttar Pradesh","Uttarakhand","West Bengal","Andaman and Nicobar Islands","Chandigarh","Dadra and Nagar Haveli and Daman and Diu","Delhi","Jammu and Kashmir","Ladakh","Lakshadweep","Puducherry"];

const L = {
  en: {tab_check: "Check my case", tab_prepared: "Be prepared", tz_note: "Enter times in Indian time (IST).", yes: "Yes", no: "No", unsure: "Not sure",
    designated: "Designated", non_designated: "Not designated", not_sure: "Not sure", check: "Check my case", reset: "Start over", copy: "Copy summary", copied: "Copied", share: "Share",
    free_label: "Or describe what happened (optional)", free_ph: "Example: a car hit my father 2 hours ago and he is in a hospital", fill: "Fill the form from my words", mic: "Speak",
    filled: "We filled what we could. Please check every answer.", no_llm: "The description helper is not available now. Please use the form.", next_q: "Next question",
    choose_state: "Choose state", left: "left", passed: "time passed", loading: "Checking...", error: "Something went wrong. Please try again.",
    form_title: "Answer what you know. Leave the rest blank.", privacy: "Nothing you type is saved. Please do not enter names or phone numbers.", prep_title: "If a road accident happens"},
  hi: {tab_check: "मेरा मामला जाँचें", tab_prepared: "तैयार रहें", tz_note: "समय भारतीय समय (IST) में दर्ज करें।", yes: "हाँ", no: "नहीं", unsure: "पक्का नहीं",
    designated: "निर्धारित", non_designated: "निर्धारित नहीं", not_sure: "पक्का नहीं", check: "मेरा मामला जाँचें", reset: "फिर से शुरू करें", copy: "सारांश कॉपी करें", copied: "कॉपी हो गया", share: "शेयर करें",
    free_label: "या बताइए क्या हुआ (वैकल्पिक)", free_ph: "उदाहरण: 2 घंटे पहले एक कार ने मेरे पिता को टक्कर मारी और वे अस्पताल में हैं", fill: "मेरे शब्दों से फ़ॉर्म भरें", mic: "बोलें",
    filled: "जितना हो सका हमने भर दिया। कृपया हर उत्तर जाँच लें।", no_llm: "विवरण सहायक अभी उपलब्ध नहीं है। कृपया फ़ॉर्म का उपयोग करें।", next_q: "अगला प्रश्न",
    choose_state: "राज्य चुनें", left: "बाकी", passed: "समय बीत गया", loading: "जाँच हो रही है...", error: "कुछ गड़बड़ हुई। कृपया फिर कोशिश करें।",
    form_title: "जो पता है वह बताएँ। बाकी खाली छोड़ दें।", privacy: "आप जो लिखते हैं वह सहेजा नहीं जाता। कृपया नाम या फ़ोन नंबर न लिखें।", prep_title: "सड़क दुर्घटना होने पर"},
  ta: {tab_check: "என் வழக்கைச் சரிபார்", tab_prepared: "தயாராக இருங்கள்", tz_note: "நேரத்தை இந்திய நேரத்தில் (IST) உள்ளிடவும்.", yes: "ஆம்", no: "இல்லை", unsure: "உறுதியாகத் தெரியாது",
    designated: "நியமிக்கப்பட்டது", non_designated: "நியமிக்கப்படவில்லை", not_sure: "உறுதியாகத் தெரியாது", check: "என் வழக்கைச் சரிபார்", reset: "மீண்டும் தொடங்கு", copy: "சுருக்கத்தை நகலெடு", copied: "நகலெடுக்கப்பட்டது", share: "பகிர்",
    free_label: "அல்லது என்ன நடந்தது என்று விவரிக்கவும் (விருப்பம்)", free_ph: "எடுத்துக்காட்டு: 2 மணி நேரத்துக்கு முன் ஒரு கார் என் தந்தை மீது மோதியது, அவர் மருத்துவமனையில் இருக்கிறார்", fill: "என் வார்த்தைகளிலிருந்து படிவத்தை நிரப்பு", mic: "பேசுங்கள்",
    filled: "முடிந்தவரை நிரப்பியுள்ளோம். ஒவ்வொரு பதிலையும் சரிபார்க்கவும்.", no_llm: "விளக்க உதவி இப்போது கிடைக்கவில்லை. படிவத்தைப் பயன்படுத்தவும்.", next_q: "அடுத்த கேள்வி",
    choose_state: "மாநிலத்தைத் தேர்ந்தெடுக்கவும்", left: "மீதம்", passed: "நேரம் முடிந்தது", loading: "சரிபார்க்கிறது...", error: "ஏதோ தவறு நடந்தது. மீண்டும் முயற்சிக்கவும்.",
    form_title: "தெரிந்ததைப் பதிலளிக்கவும். மீதியை காலியாக விடவும்.", privacy: "நீங்கள் உள்ளிடுவது சேமிக்கப்படாது. பெயர் அல்லது தொலைபேசி எண்களை உள்ளிட வேண்டாம்.", prep_title: "சாலை விபத்து நடந்தால்"}
};

const PREP = {
  en: ["Call 112. They share details of the nearest designated hospital, pass your ambulance request to 108, and inform the local police station.",
       "Ask the hospital to treat the victim under the PM-RAHAT cashless scheme: up to ₹1.5 lakh or 7 days from the accident, whichever ends first.",
       "The victim should be admitted to hospital within 24 hours of the accident.",
       "The police must confirm the accident on the eDAR system within 24 hours of the hospital registering the patient (48 hours if the hospital marks the case life-threatening). Ask the hospital to check.",
       "A hit-and-run or an uninsured vehicle does not stop the cover. The hospital's payment then comes from a different government fund. If a designated hospital will not admit the victim, report it to the District Grievance Redressal Officer, and call 14555 for other problems.",
       "Keep copies of the police report or eDAR/accident number, hospital papers and bills."],
  hi: ["112 पर कॉल करें। वे निकटतम निर्धारित अस्पताल की जानकारी देते हैं, एम्बुलेंस का अनुरोध 108 को भेजते हैं और स्थानीय पुलिस स्टेशन को सूचित करते हैं।",
       "अस्पताल से कहें कि पीड़ित का इलाज PM-RAHAT कैशलेस योजना के तहत करे: ₹1.5 लाख तक या दुर्घटना से 7 दिन तक, जो पहले समाप्त हो।",
       "पीड़ित को दुर्घटना के 24 घंटे के भीतर अस्पताल में भर्ती होना चाहिए।",
       "अस्पताल द्वारा मरीज़ को दर्ज करने के 24 घंटे के भीतर पुलिस को eDAR सिस्टम पर दुर्घटना की पुष्टि करनी होती है (यदि अस्पताल मामले को जानलेवा चिह्नित करे तो 48 घंटे)। अस्पताल से जाँचने को कहें।",
       "हिट-एंड-रन या बिना बीमा वाहन होने से कवर नहीं रुकता। तब अस्पताल का भुगतान एक अलग सरकारी कोष से होता है। यदि निर्धारित अस्पताल पीड़ित को भर्ती न करे, तो जिला शिकायत निवारण अधिकारी को बताएँ; अन्य समस्याओं के लिए 14555 पर कॉल करें।",
       "पुलिस रिपोर्ट या eDAR/दुर्घटना संख्या, अस्पताल के कागज़ात और बिलों की प्रतियाँ रखें।"],
  ta: ["112-ஐ அழைக்கவும். அவர்கள் அருகிலுள்ள நியமிக்கப்பட்ட மருத்துவமனையின் விவரங்களைத் தருவார்கள், ஆம்புலன்ஸ் கோரிக்கையை 108-க்கு அனுப்புவார்கள், உள்ளூர் காவல் நிலையத்துக்கும் தெரிவிப்பார்கள்.",
       "PM-RAHAT பணமில்லா திட்டத்தின் கீழ் சிகிச்சை அளிக்குமாறு மருத்துவமனையிடம் கேளுங்கள்: ₹1.5 லட்சம் வரை அல்லது விபத்திலிருந்து 7 நாட்கள் வரை, எது முதலில் முடிகிறதோ அது.",
       "விபத்து நடந்த 24 மணி நேரத்துக்குள் பாதிக்கப்பட்டவர் மருத்துவமனையில் அனுமதிக்கப்பட வேண்டும்.",
       "மருத்துவமனை நோயாளியைப் பதிவு செய்த 24 மணி நேரத்துக்குள் காவல்துறை eDAR அமைப்பில் விபத்தை உறுதிப்படுத்த வேண்டும் (மருத்துவமனை வழக்கை உயிருக்கு ஆபத்தானது என்று குறித்தால் 48 மணி நேரம்). சரிபார்க்க மருத்துவமனையிடம் கேளுங்கள்.",
       "ஹிட்-அண்ட்-ரன் அல்லது காப்பீடு இல்லாத வாகனம் என்றாலும் காப்பீடு நிற்காது. அப்போது மருத்துவமனைக்கான கட்டணம் வேறு அரசு நிதியிலிருந்து வழங்கப்படும். நியமிக்கப்பட்ட மருத்துவமனை அனுமதிக்க மறுத்தால் மாவட்ட குறைதீர்ப்பு அதிகாரியிடம் தெரிவிக்கவும்; பிற பிரச்சினைகளுக்கு 14555-ஐ அழைக்கவும்.",
       "காவல்துறை அறிக்கை அல்லது eDAR/விபத்து எண், மருத்துவமனை ஆவணங்கள் மற்றும் பில்களின் நகல்களை வைத்திருங்கள்."]
};

const FIELDS = [
  {k: "accident_at", t: "dt"},
  {k: "motor_vehicle", t: "tri"},
  {k: "life_threatening", t: "tri"},
  {k: "hospitalised_at", t: "dt"},
  {k: "hospital_type", t: "hosp"},
  {k: "police_informed", t: "tri"},
  {k: "police_informed_at", t: "dt", when: () => values.police_informed === "yes"},
  {k: "hit_and_run", t: "tri", when: () => values.motor_vehicle !== "no"},
  {k: "insured", t: "tri", when: () => values.motor_vehicle !== "no"},
  {k: "state", t: "state"}
];

const $ = (id) => document.getElementById(id);
let lang = initialLang();
let S = null;
let values = {};
let llmAvailable = false;
let timers = [];
let checked = false;
let preparedLogged = false;

function initialLang() {
  const q = new URLSearchParams(location.search).get("lang");
  if (q && LANGS[q]) return q;
  const n = (navigator.language || "en").slice(0, 2);
  return LANGS[n] ? n : "en";
}

function el(tag, attrs, ...kids) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === "class") e.className = v;
    else if (k === "text") e.textContent = v;
    else if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (v === true) e.setAttribute(k, "");
    else if (v !== false && v != null) e.setAttribute(k, v);
  }
  for (const c of kids.flat()) if (c != null) e.append(c);
  return e;
}

async function api(path, body) {
  const opts = body ? {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(body)} : undefined;
  const r = await fetch(path, opts);
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}

function track(event) {
  fetch("/api/event", {method: "POST", headers: {"Content-Type": "application/json"},
    body: JSON.stringify({event: event, lang: lang}), keepalive: true}).catch(() => {});
}

function stopTimers() { timers.forEach(clearInterval); timers = []; }

async function setLang(next) {
  lang = next;
  S = await api("/api/strings/" + lang);
  const t = L[lang];
  document.documentElement.lang = lang;
  $("emergency").textContent = S.ui.emergency;
  $("footer").textContent = S.ui.footer;
  $("tab-check").textContent = t.tab_check;
  $("tab-prepared").textContent = t.tab_prepared;
  $("privacy").textContent = t.privacy;
  $("form-title").textContent = t.form_title;
  $("tz-note").textContent = t.tz_note;
  $("btn-check").textContent = t.check;
  $("btn-reset").textContent = t.reset;
  $("free-label").textContent = t.free_label;
  $("freetext").placeholder = t.free_ph;
  $("btn-fill").textContent = t.fill;
  $("btn-mic").textContent = t.mic;
  renderLangs();
  renderForm();
  renderPrepared();
  if (checked) await check();
}

function renderLangs() {
  const box = $("langs");
  box.replaceChildren();
  for (const [code, name] of Object.entries(LANGS)) {
    box.append(el("button", {type: "button", "aria-pressed": String(code === lang), text: name, lang: code,
      onclick: async () => { if (code !== lang) { await setLang(code); track("language_changed"); } }}));
  }
}

function renderForm(focusSel) {
  const box = $("form");
  const t = L[lang];
  box.replaceChildren();
  for (const f of FIELDS) {
    if (f.when && !f.when()) continue;
    const id = "f-" + f.k;
    const wrap = el("div", {class: "field", "data-key": f.k});
    if (f.t === "dt") {
      wrap.append(el("label", {for: id, text: S.question[f.k]}));
      wrap.append(el("input", {type: "datetime-local", id: id, value: values[f.k] || "",
        oninput: (e) => { values[f.k] = e.target.value; }}));
    } else if (f.t === "state") {
      wrap.append(el("label", {for: id, text: S.question[f.k]}));
      const sel = el("select", {id: id, onchange: (e) => { values[f.k] = e.target.value; }},
        el("option", {value: "", text: t.choose_state}),
        STATES.map((s) => el("option", {value: s, text: s, selected: values[f.k] === s})));
      wrap.append(sel);
    } else {
      const opts = f.t === "tri"
        ? [["yes", t.yes], ["no", t.no], ["unsure", t.unsure]]
        : [["designated", t.designated], ["non_designated", t.non_designated], ["not_sure", t.not_sure]];
      wrap.append(el("div", {class: "q", id: id + "-l", text: S.question[f.k]}));
      wrap.append(el("div", {class: "seg", role: "group", "aria-labelledby": id + "-l"},
        opts.map(([v, label]) => el("button", {type: "button", "data-v": v, "aria-pressed": String(values[f.k] === v), text: label,
          onclick: () => { values[f.k] = values[f.k] === v ? "" : v; renderForm('.field[data-key="' + f.k + '"] button[data-v="' + v + '"]'); }}))));
    }
    box.append(wrap);
  }
  if (focusSel) { const b = document.querySelector(focusSel); if (b) b.focus(); }
}

function factsPayload() {
  const o = {};
  for (const f of FIELDS) {
    if (f.when && !f.when()) continue;
    let v = values[f.k];
    if (!v) continue;
    if (f.t === "dt" && v.length === 16) v += ":00+05:30";
    o[f.k] = v;
  }
  return o;
}

async function check() {
  const out = $("result");
  out.replaceChildren(el("p", {class: "muted", text: L[lang].loading}));
  try {
    const d = await api("/api/evaluate", {facts: factsPayload(), lang: lang});
    checked = true;
    renderResult(d);
  } catch (e) {
    out.replaceChildren(el("p", {class: "err", role: "alert", text: L[lang].error}));
  }
}

function section(title, ...content) { return el("section", {class: "card"}, el("h2", {text: title}), ...content); }

function fmtLeft(s) {
  const p = (n) => String(n).padStart(2, "0");
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60), x = s % 60;
  return (d ? d + "d " : "") + p(h) + ":" + p(m) + ":" + p(x);
}

function countdown(iso) {
  const at = Date.parse(iso.replace(/(\.\d{3})\d+/, "$1"));
  const span = el("span", {class: "cd"});
  const tick = () => {
    const s = Math.floor((at - Date.now()) / 1000);
    span.textContent = s <= 0 ? L[lang].passed : fmtLeft(s) + " " + L[lang].left;
    span.classList.toggle("over", s <= 0);
  };
  tick();
  timers.push(setInterval(tick, 1000));
  return span;
}

function highlight(key) {
  document.querySelectorAll(".field.focus").forEach((e) => e.classList.remove("focus"));
  const w = document.querySelector('.field[data-key="' + key + '"]');
  if (w) w.classList.add("focus");
  return w;
}

async function copyText(txt, btn) {
  try { await navigator.clipboard.writeText(txt); }
  catch (e) {
    const ta = el("textarea", {});
    ta.value = txt; document.body.append(ta); ta.select();
    try { document.execCommand("copy"); } catch (e2) { /* ignore */ }
    ta.remove();
  }
  const old = btn.textContent;
  btn.textContent = L[lang].copied;
  setTimeout(() => { btn.textContent = old; }, 1500);
  track("summary_copied");
}

function shareText(txt) {
  track("summary_shared");
  if (navigator.share) navigator.share({text: txt}).catch(() => {});
  else window.open("https://wa.me/?text=" + encodeURIComponent(txt), "_blank", "noopener");
}

function shareButtons(txt) {
  const c = el("button", {type: "button", text: L[lang].copy});
  c.addEventListener("click", () => copyText(txt, c));
  const s = el("button", {type: "button", class: "primary", text: L[lang].share, onclick: () => shareText(txt)});
  return el("div", {class: "actions"}, c, s);
}

function renderResult(d) {
  stopTimers();
  const out = $("result");
  const ui = d.ui;
  out.replaceChildren();
  out.append(el("div", {class: "status s-" + d.status.code, role: "status"},
    el("span", {class: "lbl", text: ui.status}), el("strong", {text: d.status.label})));
  if (d.next_question) {
    const w = highlight(d.next_question.key);
    out.append(el("button", {type: "button", class: "nextq",
      onclick: () => { if (w) w.scrollIntoView({block: "center", behavior: "smooth"}); },
      text: L[lang].next_q + ": " + d.next_question.text}));
  } else { highlight("__none__"); }
  out.append(section(ui.why, el("ul", {}, d.reasons.map((r) => el("li", {class: "sev-" + r.severity, text: r.text})))));
  if (d.deadlines.length) {
    out.append(section(ui.deadlines, el("ul", {}, d.deadlines.map((x) =>
      el("li", {}, el("div", {text: x.label}), el("div", {class: "muted", text: x.at_text}), x.basis ? el("div", {class: "muted", text: x.basis}) : null, x.safe_text ? el("div", {class: "muted", text: x.safe_text}) : null, countdown(x.at_iso))))));
  }
  out.append(section(ui.next_steps, el("ol", {}, d.next_steps.map((s) => el("li", {text: s})))));
  out.append(section(ui.escalation, el("p", {text: d.escalation.text})));
  if (d.help && d.help.length) out.append(section(ui.help_title, el("ul", {}, d.help.map((h) => el("li", {text: h})))));
  out.append(section(ui.documents, el("p", {class: "muted", text: ui.checklist_note}),
    d.checklist.map((g) => el("details", {}, el("summary", {text: g.title}), el("ul", {}, g.items.map((i) => el("li", {text: i})))))));
  out.append(section(ui.summary_title, el("pre", {class: "summary", text: d.summary_text}), shareButtons(d.summary_text)));
  out.append(el("p", {class: "muted", text: ui.disclaimer}));
  out.append(el("p", {class: "muted", text: ui.source_note}));
}

function renderPrepared() {
  const box = $("prepared");
  const items = PREP[lang];
  const txt = [L[lang].prep_title, S.ui.emergency, ""].concat(items.map((x, i) => (i + 1) + ". " + x))
    .concat(["", S.ui.disclaimer, S.ui.footer]).join("\n");
  box.replaceChildren(
    el("div", {class: "card"}, el("h2", {text: L[lang].prep_title}), el("ol", {}, items.map((x) => el("li", {text: x})))),
    shareButtons(txt),
    el("p", {class: "muted", text: S.ui.disclaimer}),
    el("p", {class: "muted", text: S.ui.source_note}));
}

function showTab(which) {
  const prepared = which === "prepared";
  $("view-check").hidden = prepared;
  $("view-prepared").hidden = !prepared;
  $("tab-check").setAttribute("aria-selected", String(!prepared));
  $("tab-prepared").setAttribute("aria-selected", String(prepared));
  if (prepared && !preparedLogged) { preparedLogged = true; track("prepared_viewed"); }
}

function applyExtracted(f) {
  const TRI = ["yes", "no", "unsure"], HOSP = ["designated", "non_designated", "not_sure"];
  for (const fld of FIELDS) {
    const v = f[fld.k];
    if (typeof v !== "string") continue;
    if (fld.t === "tri" && TRI.includes(v)) values[fld.k] = v;
    else if (fld.t === "hosp" && HOSP.includes(v)) values[fld.k] = v;
    else if (fld.t === "dt" && /^\d{4}-\d\d-\d\dT\d\d:\d\d/.test(v)) values[fld.k] = v.slice(0, 16);
    else if (fld.t === "state") { const m = STATES.find((s) => s.toLowerCase() === v.toLowerCase()); if (m) values[fld.k] = m; }
  }
  renderForm();
}

async function extract() {
  const txt = $("freetext").value.trim();
  const msg = $("freemsg");
  if (txt.length < 3) return;
  msg.textContent = L[lang].loading;
  try {
    const d = await api("/api/extract", {text: txt, lang: lang});
    if (!d.facts) { msg.textContent = L[lang].no_llm; return; }
    applyExtracted(d.facts);
    msg.textContent = L[lang].filled;
  } catch (e) { msg.textContent = L[lang].error; }
}

function setupMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const b = $("btn-mic");
  if (!SR) { b.hidden = true; return; }
  b.addEventListener("click", () => {
    const r = new SR();
    r.lang = SPEECH[lang];
    r.interimResults = false;
    r.onresult = (e) => { $("freetext").value = ($("freetext").value + " " + e.results[0][0].transcript).trim(); };
    r.start();
  });
}

async function init() {
  try { llmAvailable = (await api("/api/config")).llm_available; } catch (e) { llmAvailable = false; }
  $("freebox").hidden = !llmAvailable;
  $("btn-check").addEventListener("click", check);
  $("btn-reset").addEventListener("click", () => { values = {}; checked = false; stopTimers(); $("result").replaceChildren(); renderForm(); });
  $("btn-fill").addEventListener("click", extract);
  $("tab-check").addEventListener("click", () => showTab("check"));
  $("tab-prepared").addEventListener("click", () => showTab("prepared"));
  setupMic();
  await setLang(lang);
  track("session_started");
}

init();
})();
