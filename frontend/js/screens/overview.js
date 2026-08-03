import { api } from "../api.js";
import { esc, relTime, fmtDateTime } from "../format.js";

const EVENT_LABEL = (e) => (e || "").replace(/_/g, " ").toLowerCase()
  .replace(/\b\w/g, (c) => c.toUpperCase());

export async function render(view) {
  view.innerHTML = `<div class="page-head">
      <div class="kicker">System</div>
      <h2>Overview</h2>
      <div class="sub">Current sync status for DNS Syncer.</div>
    </div>
    <div id="ov"></div>`;
  await refresh();

  async function refresh() {
    const [status, records, logs] = await Promise.all([
      api.get("/status"),
      api.get("/records"),
      api.get("/logs?page_size=5"),
    ]);
    view.querySelector("#ov").innerHTML =
      commandPanel(status, records) + cards(status, records) + panels(status, logs, records);
    view.querySelectorAll("[data-go]").forEach(btn =>
      btn.addEventListener("click", () => { location.hash = `#${btn.dataset.go}`; }));
  }

  function cards(s, records) {
    const okCount = records.filter(r => ["synced", "updated"].includes(r.status)).length;
    return `<div class="grid grid-4 stat-grid">
      ${stat("Current IP", s.current_ip || "—", "Auto-detected")}
      ${stat("Last Sync", s.last_sync_at ? relTime(s.last_sync_at) : "Never", fmtDateTime(s.last_sync_at))}
      ${stat("Next Sync", nextSyncValue(s), nextSyncMeta(s))}
      ${stat("Records", records.length, `${okCount} OK`)}
    </div>`;
  }

  function commandPanel(s, records) {
    const [headline, tone] = statusHeadline(s);
    const enabled = records.filter(r => r.enabled !== false).length;
    return `<div class="command-panel spotlight ${tone}">
      <div class="command-copy">
        <div class="command-label"><span class="signal-dot ${tone}"></span>${esc(EVENT_LABEL(s.app_status || "system ready"))}</div>
        <h3>${esc(headline)}</h3>
        <p>${esc(commandMessage(s, records))}</p>
        ${commandAction(s, records)}
      </div>
      <div class="command-facts">
        ${fact("Automatic check", s.sync_interval_minutes ? `Every ${s.sync_interval_minutes} min` : "Unknown")}
        ${fact("Next run", s.sync_due ? "Due now" : relTime(s.next_sync_at))}
        ${fact("Enabled records", `${enabled} / ${records.length}`)}
      </div>
    </div>`;
  }

  function panels(s, logs, records) {
    return `<div class="cols">
      <div class="section-stack">
        <div class="card">
          <div class="card-title">Recent Activity</div>
          ${activity(logs.entries)}
        </div>
        <div class="card">
          <div class="card-title">Managed Records</div>
          ${recordPreview(records)}
        </div>
      </div>
      <div class="card">
        <div class="card-title">Health Summary</div>
        ${health(s)}
      </div>
    </div>`;
  }

  function activity(entries) {
    if (!entries.length) return `<div class="empty">No activity yet. Run a sync.</div>`;
    return `<div class="table-wrap"><table><tbody>` + entries.map(e => `<tr>
      <td class="cell-tight"><span class="dot ${esc(e.level)}"></span></td>
      <td class="mono trunc" title="${esc(e.event)}">${esc(EVENT_LABEL(e.event))}</td>
      <td class="trunc" title="${esc(e.message)}">${esc(e.message)}</td>
      <td class="mono cell-time" title="${esc(fmtDateTime(e.timestamp))}">${relTime(e.timestamp)}</td>
    </tr>`).join("") + `</tbody></table></div>`;
  }

  function recordPreview(records) {
    if (!records.length) return `<div class="empty">No records yet.</div>`;
    return `<div class="table-wrap"><table>
      <thead><tr><th>Type</th><th>Name</th><th>Value</th><th>Status</th><th>Updated</th></tr></thead>
      <tbody>` + records.slice(0, 5).map(r => `<tr>
        <td class="mono">${esc(r.type)}</td>
        <td>${esc(r.fqdn)}</td>
        <td class="mono">${esc(r.cloudflare_value || "—")}</td>
        <td>${statusPill(r.status)}</td>
        <td class="mono">${relTime(r.last_updated_at)}</td>
      </tr>`).join("") + `</tbody></table></div>`;
  }

  function health(s) {
    const rows = [
      ["Cloudflare API", s.token_status === "valid" ? ["Connected", "success"] :
        s.token_status === "missing" ? ["No token", "warning"] : ["Set", "info"]],
      ["Public IP Provider", s.current_ip ? ["Available", "success"] : ["Unknown", "warning"]],
      ["Systemd Timer", s.timer_status === "active" ? ["Active", "success"] : [s.timer_status, "warning"]],
      ["App Fallback", s.scheduler_status === "running" ? ["Running", "success"] :
        s.scheduler_status === "disabled" ? ["Disabled", "warning"] : [s.scheduler_status || "Unknown", "warning"]],
      ["Sync Interval", s.sync_interval_minutes ? [`Every ${s.sync_interval_minutes} min`, "success"] : ["Unknown", "warning"]],
      ["Log Writer", ["Ready", "success"]],
    ];
    return rows.map(([k, [v, kind]]) => `<div class="hrow">
      <span class="k">${esc(k)}</span>
      <span class="pill ${kind}"><span class="dot ${kind}"></span>${esc(v)}</span>
    </div>`).join("");
  }
}

function statusHeadline(s) {
  if (s.app_status === "healthy") return ["DNS Syncer is watching your records", "success"];
  if (s.app_status === "degraded") return ["DNS Syncer needs attention", "warning"];
  return ["Finish setup to start automatic syncing", "warning"];
}

function commandMessage(s, records) {
  if (s.token_status === "missing") return "Add your Cloudflare token, choose a zone, then run a manual sync once.";
  if (!records.length) return "Add at least one DNS record so automatic checks have something to protect.";
  if (s.sync_due) return "The next automatic run is due now. Manual sync is available from the command bar.";
  if (s.next_sync_at) return `Next automatic check: ${fmtDateTime(s.next_sync_at)}.`;
  return "Automatic checks are enabled; waiting for the first scheduled run.";
}

function commandAction(s, records) {
  if (s.token_status === "missing") {
    return `<button class="btn btn-primary command-action" data-go="settings">Open Settings</button>`;
  }
  if (!records.length) {
    return `<button class="btn btn-secondary command-action" data-go="records">Add a Record</button>`;
  }
  return `<button class="btn btn-secondary command-action" data-go="logs">View Logs</button>`;
}

function nextSyncValue(s) {
  if (s.sync_due) return "Due now";
  return relTime(s.next_sync_at);
}

function nextSyncMeta(s) {
  if (!s.next_sync_at) return "Waiting for first sync";
  return fmtDateTime(s.next_sync_at);
}

function stat(label, value, meta) {
  return `<div class="card stat spotlight">
    <div class="label">${esc(label)}</div>
    <div class="value">${esc(value)}</div>
    <div class="meta">${meta}</div>
  </div>`;
}

function fact(label, value) {
  return `<div class="command-fact">
    <span>${esc(label)}</span>
    <strong>${esc(value)}</strong>
  </div>`;
}

export function statusPill(status) {
  const map = {
    synced: ["Synced", "success"], updated: ["Updated", "info"],
    failed: ["Failed", "danger"], paused: ["Paused", "neutral"],
    unchanged: ["Synced", "success"], unknown: ["Unknown", "neutral"],
  };
  const [t, k] = map[status] || ["Unknown", "neutral"];
  return `<span class="pill ${k}">${t}</span>`;
}
