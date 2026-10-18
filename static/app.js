const $ = (id) => document.getElementById(id);

const SAMPLES = {
  fake: "SHOCKING!!! Sources say the government has been hiding a miracle cure that doctors hate. " +
    "Mainstream media will never tell you the truth about this, and it has been banned in 12 countries. " +
    "You won't believe what happens next. Share before it gets deleted!",
  real: "The city council approved the 2026 budget on Tuesday by a vote of 7 to 2. " +
    "Council member Anita Rao said the plan funds road repairs on three main streets and two new " +
    "branch libraries. The budget takes effect on 1 January, and a public hearing on the library " +
    "sites is scheduled for next month.",
};

const text = $("text");
const max = text.maxLength;

text.addEventListener("input", () => {
  $("count").textContent = `${text.value.length} of ${max} characters`;
  $("count").classList.toggle("near-limit", text.value.length > max * 0.9);
  showError("");
});
$("sample-fake").addEventListener("click", () => loadSample("fake"));
$("sample-real").addEventListener("click", () => loadSample("real"));
$("edit").addEventListener("click", () => setMode("edit"));
$("go").addEventListener("click", check);
$("clear").addEventListener("click", clearText);
$("history-link").addEventListener("click", (event) => {
  event.preventDefault();
  document.querySelector("#history").scrollIntoView({ behavior: "smooth", block: "center" });
});

function loadSample(key) {
  text.value = SAMPLES[key];
  text.dispatchEvent(new Event("input"));
  setMode("edit");
  text.focus();
}

function clearText() {
  text.value = "";
  text.dispatchEvent(new Event("input"));
  setMode("edit");
  $("result").hidden = true;
  $("empty").hidden = false;
  $("report-status").textContent = "Ready";
  text.focus();
}

function setMode(mode) {
  const reading = mode === "read";
  text.hidden = reading;
  $("doc").hidden = !reading;
  $("legend").hidden = !reading;
  $("count").hidden = reading;
  $("input-help").hidden = reading;
  $("edit").hidden = !reading;
  $("sample-fake").hidden = reading;
  $("sample-real").hidden = reading;
  $("go").hidden = reading;
  $("clear").hidden = reading;
  document.querySelector(".examples").hidden = reading;
}

function showError(msg) {
  const el = $("error");
  el.textContent = msg;
  el.hidden = !msg;
}

async function check() {
  showError("");
  if (!text.value.trim()) {
    showError("Paste an article or choose an example before analyzing.");
    text.focus();
    return;
  }
  const btn = $("go");
  const label = btn.querySelector("span");
  btn.disabled = true;
  label.textContent = "Analyzing article…";
  $("report-status").textContent = "Analyzing";
  $("report-status").classList.add("is-loading");
  $("empty").hidden = false;
  $("empty").classList.add("is-loading");
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text.value }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Something went wrong.");
    render(text.value.trim(), data);
    $("report-status").textContent = "Complete";
  } catch (err) {
    showError(err.message || "Could not analyze this text. Please try again.");
    $("report-status").textContent = "Error";
  } finally {
    btn.disabled = false;
    label.textContent = "Analyze article";
    $("report-status").classList.remove("is-loading");
    $("empty").classList.remove("is-loading");
  }
}

/* Find the spans of the text to mark, using the word lists the backend matched. */
function findMarks(source, f) {
  const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const marks = [];
  const collect = (re, type) => {
    let m;
    while ((m = re.exec(source))) marks.push({ start: m.index, end: m.index + m[0].length, type });
  };
  const loaded = [...(f.sensational_found || []), ...(f.clickbait_found || [])];
  if (loaded.length) collect(new RegExp("\\b(?:" + loaded.map(esc).join("|") + ")\\b", "gi"), "loaded");
  if ((f.vague_found || []).length) collect(new RegExp("\\b(?:" + f.vague_found.map(esc).join("|") + ")\\b", "gi"), "vague");
  collect(/\b[A-Z]{3,}\b/g, "loaded");

  marks.sort((a, b) => a.start - b.start || b.end - a.end);
  const kept = [];
  let last = 0;
  for (const m of marks) {
    if (m.start >= last) { kept.push(m); last = m.end; }
  }
  return kept;
}

function renderDoc(source, marks) {
  const box = $("doc");
  box.replaceChildren();
  let pos = 0;
  marks.forEach((m, i) => {
    if (m.start > pos) box.append(document.createTextNode(source.slice(pos, m.start)));
    const span = document.createElement("span");
    span.className = `mark ${m.type} on`;
    span.style.setProperty("--i", i);
    span.textContent = source.slice(m.start, m.end);
    box.append(span);
    pos = m.end;
  });
  if (pos < source.length) box.append(document.createTextNode(source.slice(pos)));
}

function fillList(id, items, emptyMsg) {
  const ul = $(id);
  ul.replaceChildren();
  const safeItems = Array.isArray(items) ? items : [];
  (safeItems.length ? safeItems : [emptyMsg]).forEach((item) => {
    const li = document.createElement("li");
    li.textContent = item;
    if (!safeItems.length) li.className = "none";
    ul.appendChild(li);
  });
}

function render(source, d) {
  renderDoc(source, findMarks(source, d.features || {}));
  setMode("read");

  $("empty").hidden = true;
  $("result").hidden = false;

  const score = Math.max(0, Math.min(100, Number(d.score) || 0));
  const v = $("verdict");
  v.textContent = d.verdict || "Analysis complete";
  v.className = "verdict " + (score <= 25 ? "good" : score <= 50 ? "warn" : "bad");
  $("verdict-card").className = "verdict-card " + (score <= 25 ? "good" : score <= 50 ? "warn" : "bad");
  $("verdict-symbol").textContent = score <= 25 ? "✓" : score <= 50 ? "?" : "!";
  $("score-value").textContent = score;
  $("score-fill").style.width = score + "%";
  $("pin").style.left = score + "%";
  $("score-level").textContent = score <= 25 ? "Lower signal" : score <= 50 ? "Review" : "Higher signal";
  $("score-line").textContent = "Higher scores indicate more language-based signals associated with potentially misleading content.";
  $("summary").textContent = (d.summary || "") + (d.verifiable === false ? " There are few checkable claims, so treat this score with caution." : "");
  $("reasoning").textContent = d.reasoning || "No additional reasoning was returned.";

  fillList("flags", d.red_flags, "No specific red flags found.");
  fillList("claims", d.claims_to_verify, "No checkable claims found.");
  $("flag-count").textContent = Array.isArray(d.red_flags) ? d.red_flags.length : 0;

  const f = d.features || {};
  const rows = [
    ["Language model score", d.llm_score ?? "—"],
    ["Text statistics score", d.heuristic_score ?? "—"],
    ["Words", f.word_count ?? "—"],
    ["Average sentence length", f.avg_sentence_len ?? "—"],
    ["Sensational words", (f.sensational_found || []).join(", ") || "none"],
    ["Clickbait phrases", (f.clickbait_found || []).join(", ") || "none"],
    ["Vague sourcing", (f.vague_found || []).join(", ") || "none"],
    ["Top keywords", (f.top_keywords || []).join(", ") || "none"],
  ];
  const dl = $("stats");
  dl.replaceChildren();
  rows.forEach(([k, val]) => {
    const dt = document.createElement("dt");
    dt.textContent = k;
    const dd = document.createElement("dd");
    dd.textContent = val;
    dl.append(dt, dd);
  });
}
