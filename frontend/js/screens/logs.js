import { api } from "../api.js";
import { esc, relTime, absTime } from "../format.js";
import { toast, modal } from "../state.js";

const FILTERS = [
  ["all", "All"], ["sync", "Sync"], ["token", "Token"],
  ["integration", "Integration"], ["warnings", "Warnings"], ["errors", "Errors"],
];

export async function render(view) {
  view.innerHTML = `<div class="kicker">Operations</div>
    <h2>Logs</h2>
    <div class="sub">Full event history for DNS Syncer.</div>
    <div class="toolbar">
      <div class="chips" id="chips">${FILTERS.map(([id, l]) =>
        `<button class="chip ${id === "all" ? "active" : ""}" data-f="${id}">${l}</button>`).join("")}</div>
      <div class="spacer"></div>
      <input type="text" id="search" placeholder="Search logs…">
      <a class="btn btn-secondary" href="/api/logs/export">Export CSV</a>
    </div>
    <div class="cols">
      <div class="card" style="padding:0"><div id="tbl"></div></div>
      <div class="card"><div class="card-title">Log Summary</div><div id="summary"></div></div>
    </div>`;

  let state = { filter: "all", q: "", page: 1 };
  let entries = [];

  view.querySelector("#chips").addEventListener("click", (e) => {
    const b = e.target.closest("[data-f]"); if (!b) return;
    view.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
    b.classList.add("active"); state.filter = b.dataset.f; state.page = 1; load();
  });
  let t; view.querySelector("#search").addEventListener("input", (e) => {
    clearTimeout(t); t = setTimeout(() => { state.q = e.target.value; state.page = 1; load(); }, 250);
  });

  async function load() {
    const p = new URLSearchParams({ filter: state.filter, page: state.page, page_size: 50 });
    if (state.q) p.set("q", state.q);
    const data = await api.get("/logs?" + p);
    entries = data.entries;
    draw(data);
  }

  function draw(data) {
    const tbl = view.querySelector("#tbl");
    if (!entries.length) { tbl.innerHTML = `<div class="empty">No log entries match.</div>`; }
    else {
      tbl.innerHTML = `<div class="table-wrap"><table>
        <thead><tr><th>Time</th><th>Level</th><th>Event</th><th>Message</th><th>Record</th><th></th></tr></thead>
        <tbody>${entries.map((e, i) => `<tr>
          <td class="mono" title="${esc(absTime(e.timestamp))}">${relTime(e.timestamp)}</td>
          <td><span class="dot ${esc(e.level)}"></span> ${esc(e.level)}</td>
          <td class="mono">${esc(e.event)}</td>
          <td>${esc(e.message)}</td>
          <td class="mono">${esc(e.record || "—")}</td>
          <td><button class="btn btn-ghost btn-sm" data-i="${i}">Details</button></td>
        </tr>`).join("")}</tbody></table></div>${pager(data)}`;
      tbl.querySelectorAll("[data-i]").forEach(el => el.addEventListener("click",
        () => details(entries[el.dataset.i])));
      const pg = tbl.querySelector("#pager");
      if (pg) pg.addEventListener("click", (e) => {
        const b = e.target.closest("[data-page]"); if (!b) return;
        state.page = +b.dataset.page; load();
      });
    }
    const c = data.counts;
    view.querySelector("#summary").innerHTML = [
      ["Total logs", c.total], ["Info", c.INFO], ["Debug", c.DEBUG],
      ["Warnings", c.WARN], ["Errors", c.ERROR],
    ].map(([k, v]) => `<div class="hrow"><span class="k">${k}</span><span class="mono">${v}</span></div>`).join("")
      + `<button class="btn btn-danger btn-sm" id="clear" style="margin-top:var(--space-4)">Clear logs</button>`;
    view.querySelector("#clear").addEventListener("click", async () => {
      if (!confirm("Clear all logs? This cannot be undone.")) return;
      await api.del("/logs"); toast("Logs cleared"); load();
    });
  }

  function pager(data) {
    const pages = Math.ceil(data.total / data.page_size);
    if (pages <= 1) return "";
    return `<div id="pager" style="display:flex;gap:8px;justify-content:center;padding:var(--space-3)">
      ${data.page > 1 ? `<button class="btn btn-ghost btn-sm" data-page="${data.page - 1}">← Prev</button>` : ""}
      <span class="mono" style="align-self:center;color:var(--text-3)">${data.page} / ${pages}</span>
      ${data.page < pages ? `<button class="btn btn-ghost btn-sm" data-page="${data.page + 1}">Next →</button>` : ""}
    </div>`;
  }

  function details(e) {
    const json = JSON.stringify(e, null, 2);
    const m = modal(`<h3>Log Detail</h3>
      <div class="field"><label>Event</label><div class="mono">${esc(e.event)}</div></div>
      <div class="field"><label>Timestamp</label><div class="mono">${esc(absTime(e.timestamp))}</div></div>
      <div class="field"><label>Message</label><div>${esc(e.message)}</div></div>
      <div class="field"><label>Details JSON</label><pre class="json">${esc(json)}</pre></div>
      <div class="modal-actions">
        <button class="btn btn-secondary" id="copy">Copy JSON</button>
        <button class="btn btn-primary" id="ok">Close</button>
      </div>`);
    m.el.querySelector("#ok").addEventListener("click", m.close);
    m.el.querySelector("#copy").addEventListener("click", () => {
      navigator.clipboard.writeText(json); toast("Copied");
    });
  }

  await load();
}
