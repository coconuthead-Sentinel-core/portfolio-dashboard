// Portfolio Dashboard — vanilla JS, no build chain.
const $  = (q) => document.querySelector(q);
const $$ = (q) => document.querySelectorAll(q);

// ── Tab routing ─────────────────────────────────────────────────────
$$(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    $$(".tab-btn").forEach((b) => b.classList.remove("active"));
    $$(".tab-pane").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(btn.dataset.tab).classList.add("active");
    if (btn.dataset.tab === "codex") loadCodex();
  });
});

// ── Stat card helper ────────────────────────────────────────────────
const card = (label, value) =>
  `<div class="stat-card"><div class="label">${label}</div><div class="value">${value}</div></div>`;

// ── API ─────────────────────────────────────────────────────────────
async function api(path, opts = {}) {
  const r = await fetch(path, {
    headers: { "Content-Type": "application/json" }, ...opts,
  });
  if (!r.ok) throw new Error(`${path}: ${r.status}`);
  return r.json();
}

// ── Overview ───────────────────────────────────────────────────────
async function loadOverview() {
  const snap = await api("/api/snapshot");
  $("#overview-stats").innerHTML = [
    card("Canon entries",       snap.canon.total),
    card("GitHub published",    snap.canon.github_published),
    card("Aggregate tests",     snap.canon.aggregate_tests_passing.toLocaleString()),
    card("Media artifacts",     snap.media.total_artifacts.toLocaleString()),
    card("Diagram-grade",       snap.media.diagram_grade.toLocaleString()),
    card("Disciplines active",  snap.disciplines.total),
  ].join("");
}

$("#diag-go").addEventListener("click", async () => {
  const kw = $("#diag-keyword").value.trim();
  if (!kw) return;
  $("#diag-out").textContent = "Running audit...";
  const r = await api(`/api/diagrams/${encodeURIComponent(kw)}?limit=10`);
  if (!r.results.length) {
    $("#diag-out").textContent = `No diagram-grade hits for '${kw}'.`;
    return;
  }
  $("#diag-out").textContent = r.results.map((d, i) =>
    `${i + 1}. ${d.filename}\n   kind=${d.kind}  cats=${d.categories.join(", ")}  glyphs=${d.glyph_tags}`
  ).join("\n\n");
});

// ── Canon ───────────────────────────────────────────────────────────
async function loadCanon() {
  const c = await api("/api/canon");
  $("#canon-stats").innerHTML = [
    card("Total",              c.total),
    card("GitHub published",   c.github_published),
    card("With tests",         c.with_tests),
    card("Aggregate passing",  c.aggregate_tests_passing.toLocaleString()),
  ].join("");
  const tbody = $("#canon-table tbody");
  tbody.innerHTML = c.entries.map((e) => `
    <tr>
      <td>${e.id}</td>
      <td>${escapeHtml(e.name)}</td>
      <td>${escapeHtml(e.tier)}</td>
      <td>${escapeHtml(e.tests)}</td>
      <td>${e.url.startsWith("https://")
        ? `<a href="${e.url}" target="_blank">repo</a>` : escapeHtml(e.url)}</td>
    </tr>`).join("");
}

// ── Media ───────────────────────────────────────────────────────────
async function loadMedia() {
  const m = await api("/api/media");
  $("#media-stats").innerHTML = [
    card("Total artifacts",  m.total_artifacts.toLocaleString()),
    card("Diagram-grade",    m.diagram_grade.toLocaleString()),
    ...Object.entries(m.by_kind || {}).map(([k, n]) => card(k, n)),
  ].join("");
}

// ── Disciplines ─────────────────────────────────────────────────────
async function loadDisciplines() {
  const d = await api("/api/disciplines");
  $("#discipline-stats").innerHTML = card("Active", d.total);
  $("#discipline-list").innerHTML = (d.list || [])
    .map((x) => `<li>${escapeHtml(x)}</li>`).join("");
}

// ── Codex Intake ────────────────────────────────────────────────────
async function loadCodex() {
  const stats = await api("/api/codex/stats");
  $("#codex-stats").innerHTML = [
    card("Artifacts",       stats.artifacts),
    card("Memories",        stats.memories),
    card("Open actions",    stats.actions_open),
    card("Closed actions",  stats.actions_closed),
    card("Skill seeds",     stats.skills),
  ].join("");

  const arts = await api("/api/codex/artifacts");
  $("#artifacts-table tbody").innerHTML = arts.map((a) => `
    <tr><td>${a.artifact_id}</td><td>${escapeHtml(a.label)}</td>
        <td>${escapeHtml(a.kind)}</td><td>${escapeHtml(a.status || "")}</td>
        <td>${escapeHtml(a.practical_role || "")}</td></tr>`).join("");

  const mems = await api("/api/codex/memories");
  $("#memories-table tbody").innerHTML = mems.map((m) => `
    <tr><td>${m.memory_id}</td><td>${escapeHtml(m.topic)}</td>
        <td>${escapeHtml(truncate(m.memory_value, 100))}</td>
        <td>${m.confidence}</td></tr>`).join("");

  const acts = await api("/api/codex/actions?status=open");
  $("#actions-table tbody").innerHTML = acts.map((a) => `
    <tr><td>${a.sequence_no}</td>
        <td>${escapeHtml(truncate(a.action_text, 120))}</td>
        <td>${escapeHtml(a.source_artifact || "")}</td>
        <td>${escapeHtml(a.status)}</td></tr>`).join("");

  const skills = await api("/api/codex/skills");
  $("#skills-table tbody").innerHTML = skills.map((s) => `
    <tr><td>${s.seed_id}</td><td>${escapeHtml(s.skill_name)}</td>
        <td>${escapeHtml(truncate(s.purpose, 120))}</td>
        <td>${escapeHtml(s.status)}</td></tr>`).join("");
}

$("#ingest-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const fd = new FormData(ev.target);
  const legendLines = (fd.get("legend") || "").toString()
    .split("\n").map((l) => l.trim()).filter(Boolean);
  const body = {
    label:        fd.get("label"),
    source_path:  fd.get("source_path"),
    title:        fd.get("title"),
    usefulness:   fd.get("usefulness"),
    legend:       legendLines,
  };
  $("#ingest-out").textContent = "Ingesting...";
  try {
    const r = await api("/api/codex/ingest", {
      method: "POST", body: JSON.stringify(body),
    });
    $("#ingest-out").textContent = JSON.stringify(r, null, 2);
    ev.target.reset();
    loadCodex();
  } catch (e) {
    $("#ingest-out").textContent = "ERROR: " + e.message;
  }
});

// ── Helpers ────────────────────────────────────────────────────────
function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}
function truncate(s, n) {
  s = String(s ?? "");
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

// ── Initial load ───────────────────────────────────────────────────
(async () => {
  await loadOverview();
  await loadCanon();
  await loadMedia();
  await loadDisciplines();
})();
