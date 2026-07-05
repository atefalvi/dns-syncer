import { api } from "../api.js";
import { esc, relTime, fmtDateTime } from "../format.js";

const EVENT_LABEL = (e) => (e || "").replace(/_/g, " ").toLowerCase()
  .replace(/\b\w/g, (c) => c.toUpperCase());

export async function render(view) {
  view.innerHTML = `<div class="kicker">System</div>
    <h2>Overview</h2>
    <div class="sub">Current sync status for DNS Syncer.</div>
    <div id="ov"></div>`;
  await refresh();

  async function refresh() {
    const [status, records, logs] = await Promise.all([
      api.get("/status"),
      api.get("/records"),
      api.get("/logs?page_size=5"),
    ]);
    view.querySelector("#ov").innerHTML =
      setupBanner(status) + cards(status, records) + panels(status, logs, records);
    const go = view.querySelector("#go-settings");
    if (go) go.addEventListener("click", () => { location.hash = "#settings"; });
  }

  function setupBanner(s) {
    if (s.token_status !== "missing") return "";
    return `<div class="card banner" style="margin-bottom:var(--space-4)">
      <div>
        <div class="card-title" style="margin-bottom:4px">Get started</div>
        <div style="color:var(--text-2);font-size:13px">
          1. Add your Cloudflare token &nbsp;→&nbsp; 2. Verify &amp; pick a zone &nbsp;→&nbsp; 3. Add a record &nbsp;→&nbsp; 4. Run Sync
        </div>
      </div>
      <button class="btn btn-primary" id="go-settings">Open Settings</button>
    </div>`;
  }

  function cards(s, records) {
    const okCount = records.filter(r => ["synced", "updated"].includes(r.status)).length;
    return `<div class="grid grid-4" style="margin-bottom:var(--space-4)">
      ${stat("Current IP", s.current_ip || "—", "Auto-detected")}
      ${stat("Last Sync", s.last_sync_at ? relTime(s.last_sync_at) : "Never", fmtDateTime(s.last_sync_at))}
      ${stat("Records", records.length, `${okCount} OK`)}
      ${stat("Token", s.token_masked || "Not set", tokenBadge(s.token_status))}
    </div>`;
  }

  function panels(s, logs, records) {
    return `<div class="cols">
      <div class="grid" style="gap:var(--space-4)">
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
      <td style="width:1px"><span class="dot ${esc(e.level)}"></span></td>
      <td class="mono trunc" style="width:140px" title="${esc(e.event)}">${esc(EVENT_LABEL(e.event))}</td>
      <td class="trunc" title="${esc(e.message)}">${esc(e.message)}</td>
      <td class="mono" style="width:80px;text-align:right" title="${esc(fmtDateTime(e.timestamp))}">${relTime(e.timestamp)}</td>
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
      ["Log Writer", ["Ready", "success"]],
    ];
    return rows.map(([k, [v, kind]]) => `<div class="hrow">
      <span class="k">${esc(k)}</span>
      <span class="pill ${kind}"><span class="dot ${kind}"></span>${esc(v)}</span>
    </div>`).join("");
  }
}

function stat(label, value, meta) {
  return `<div class="card stat">
    <div class="label">${esc(label)}</div>
    <div class="value">${esc(value)}</div>
    <div class="meta">${meta}</div>
  </div>`;
}

function tokenBadge(status) {
  const map = { valid: ["Valid", "success"], missing: ["Not set", "warning"], set: ["Set", "info"] };
  const [t, k] = map[status] || ["Unknown", "warning"];
  return `<span class="pill ${k}">${t}</span>`;
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
