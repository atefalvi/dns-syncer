import { api } from "../api.js";
import { esc, relTime, fmtDateTime } from "../format.js";
import { toast, modal } from "../state.js";
import { statusPill } from "./overview.js";

export async function render(view) {
  view.innerHTML = `<div class="kicker">DNS</div>
    <h2>Records</h2>
    <div class="sub">Manage DNS records synced by DNS Syncer.</div>
    <div class="toolbar">
      <input type="text" id="search" placeholder="Search records…">
      <div class="spacer"></div>
      <button class="btn btn-secondary" id="add">Add Record</button>
      <button class="btn btn-primary" id="run">Run Sync</button>
    </div>
    <div class="card" style="padding:0"><div id="tbl"></div></div>`;

  let records = [];
  const load = async () => { records = await api.get("/records"); draw(); };

  view.querySelector("#search").addEventListener("input", draw);
  view.querySelector("#run").addEventListener("click", async (e) => {
    e.target.disabled = true; e.target.textContent = "Syncing…";
    try { const r = await api.post("/sync/run"); toast(`Sync: ${r.records_updated} updated, ${r.records_failed} failed`, "success"); }
    catch (err) { toast(err.message, "error"); }
    e.target.disabled = false; e.target.textContent = "Run Sync";
    await load();
  });
  view.querySelector("#add").addEventListener("click", () => addModal(load));

  function draw() {
    const q = view.querySelector("#search").value.toLowerCase();
    const rows = records.filter(r => !q || JSON.stringify(r).toLowerCase().includes(q));
    const tbl = view.querySelector("#tbl");
    if (!rows.length) { tbl.innerHTML = `<div class="empty">No records. Add one to start syncing.</div>`; return; }
    tbl.innerHTML = `<div class="table-wrap"><table>
      <thead><tr><th>On</th><th>Type</th><th>Name</th><th>Zone</th><th>Current IP</th>
        <th>Target IP</th><th>Status</th><th>Updated</th><th></th></tr></thead>
      <tbody>${rows.map(row).join("")}</tbody></table></div>`;

    tbl.querySelectorAll("[data-toggle]").forEach(el => el.addEventListener("change", async (e) => {
      try { await api.patch(`/records/${e.target.dataset.toggle}`, { enabled: e.target.checked }); await load(); }
      catch (err) { toast(err.message, "error"); }
    }));
    tbl.querySelectorAll("[data-del]").forEach(el => el.addEventListener("click", async (e) => {
      if (!confirm("Delete this record from DNS Syncer? (Cloudflare record is kept)")) return;
      try { await api.del(`/records/${e.target.dataset.del}`); toast("Record removed"); await load(); }
      catch (err) { toast(err.message, "error"); }
    }));
  }

  function row(r) {
    return `<tr>
      <td><input type="checkbox" ${r.enabled ? "checked" : ""} data-toggle="${esc(r.id)}"></td>
      <td class="mono">${esc(r.type)}</td>
      <td>${esc(r.fqdn)}</td>
      <td class="mono">${esc(r.zone_name)}</td>
      <td class="mono">${esc(r.cloudflare_value || "—")}</td>
      <td class="mono">${esc(r.target_ip || "—")}</td>
      <td>${statusPill(r.enabled ? r.status : "paused")}</td>
      <td class="mono" title="${esc(fmtDateTime(r.last_updated_at))}">${relTime(r.last_updated_at)}</td>
      <td><button class="btn btn-ghost btn-sm" data-del="${esc(r.id)}">Delete</button></td>
    </tr>`;
  }

  await load();
}

async function addModal(onDone) {
  let zones = [];
  try { zones = (await api.get("/cloudflare/zones")).zones; } catch (_) {}
  const settings = await api.get("/settings");
  const zoneOpts = zones.length
    ? zones.map(z => `<option value="${esc(z.id)}|${esc(z.name)}" ${z.id === settings.cloudflare_zone_id ? "selected" : ""}>${esc(z.name)}</option>`).join("")
    : `<option value="${esc(settings.cloudflare_zone_id)}|${esc(settings.cloudflare_zone_name)}">${esc(settings.cloudflare_zone_name || "Set token first")}</option>`;

  const m = modal(`<h3>Add Record</h3>
    <div class="field"><label>Zone</label><select id="zone">${zoneOpts}</select></div>
    <div class="field"><label>Hostname</label>
      <input type="text" id="host" placeholder="home (use @ for root)"></div>
    <div class="row">
      <div class="field"><label>Type</label><select id="type"><option>A</option><option>AAAA</option></select></div>
      <div class="field"><label>Proxied</label><select id="proxied"><option value="true">Yes</option><option value="false">No</option></select></div>
    </div>
    <label class="switch"><input type="checkbox" id="enabled" checked>&nbsp;Enabled</label>
    <div class="modal-actions">
      <button class="btn btn-secondary" id="cancel">Cancel</button>
      <button class="btn btn-primary" id="save">Save Record</button>
    </div>`);

  m.el.querySelector("#cancel").addEventListener("click", m.close);
  m.el.querySelector("#save").addEventListener("click", async (e) => {
    const [zone_id, zone_name] = m.el.querySelector("#zone").value.split("|");
    e.target.disabled = true; e.target.textContent = "Saving…";
    try {
      await api.post("/records", {
        zone_id, zone_name,
        hostname: m.el.querySelector("#host").value.trim(),
        type: m.el.querySelector("#type").value,
        proxied: m.el.querySelector("#proxied").value === "true",
        enabled: m.el.querySelector("#enabled").checked,
      });
      toast("Record added", "success"); m.close(); onDone();
    } catch (err) {
      toast(err.message, "error"); e.target.disabled = false; e.target.textContent = "Save Record";
    }
  });
}
