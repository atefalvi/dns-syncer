import { api } from "../api.js";
import { esc } from "../format.js";
import { toast } from "../state.js";

export async function render(view) {
  const s = await api.get("/settings");
  const status = await api.get("/status");
  const adv = s.advanced || {};

  view.innerHTML = `<div class="kicker">Configuration</div>
    <h2>Settings</h2>
    <div class="sub">Configure DNS Syncer behavior. Cloudflare token lives here.</div>

    ${section("Cloudflare", `
      <div class="field"><label>API Token <span id="tokbadge">${tokenBadge(status.token_status)}</span></label>
        <div class="row">
          <input type="password" id="token" placeholder="${status.token_masked || "Paste Cloudflare API token"}" style="flex:4">
          <button class="btn btn-secondary" id="reveal" style="flex:0 0 auto">Show</button>
        </div>
        <div class="hint">Needs Zone:Read + DNS:Edit. Stored encrypted, never shown again.</div>
      </div>
      <div class="row" style="margin-bottom:var(--space-4)">
        <button class="btn btn-secondary" id="savetok">Save Token</button>
        <button class="btn btn-secondary" id="verify">Verify Token</button>
      </div>
      <div class="field"><label>Selected Zone</label>
        <div class="row">
          <select id="zone" style="flex:4"><option>${esc(s.cloudflare_zone_name || "— refresh zones —")}</option></select>
          <button class="btn btn-secondary" id="refresh" style="flex:0 0 auto">Refresh</button>
        </div>
      </div>`)}

    ${section("Sync Behavior", `
      <div class="row">
        <div class="field"><label>Sync Interval</label>
          <select id="interval">${[5, 15, 30, 60].map(n =>
            `<option value="${n}" ${s.sync_interval_minutes === n ? "selected" : ""}>${n} minutes</option>`).join("")}</select></div>
        <div class="field"><label>Run on startup</label>
          <select id="startup"><option value="true" ${s.run_on_startup ? "selected" : ""}>Yes</option>
            <option value="false" ${!s.run_on_startup ? "selected" : ""}>No</option></select></div>
      </div>
      <div class="hint">Interval changes take effect after: <span class="mono">sudo systemctl restart dns-syncer.timer</span></div>`)}

    ${section("Public IP Source", `
      <div class="row">
        <div class="field"><label>Provider</label><input type="text" id="ipname" value="${esc(s.ip_provider)}"></div>
        <div class="field" style="flex:3"><label>Custom URL</label><input type="text" id="ipurl" value="${esc(s.ip_provider_url)}"></div>
      </div>`)}

    ${section("Logging", `
      <div class="row">
        <div class="field"><label>Max entries</label><input type="number" id="maxlog" value="${s.max_log_entries}"></div>
        <div class="field"><label>Retention days</label><input type="number" id="retention" value="${s.log_retention_days}"></div>
      </div>`)}

    ${section("Local App", `
      <div class="row">
        <div class="field"><label>Bind host</label>
          <select id="host"><option ${s.ui_bind_host === "0.0.0.0" ? "selected" : ""}>0.0.0.0</option>
            <option ${s.ui_bind_host === "127.0.0.1" ? "selected" : ""}>127.0.0.1</option></select></div>
        <div class="field"><label>Port</label><input type="number" id="port" value="${s.ui_port}"></div>
      </div>
      <div class="hint" style="color:var(--warning)">This app stores infrastructure credentials. Only expose it on trusted networks. Host/port changes need a service restart.</div>`)}

    ${section("Advanced", `
      <div class="row">
        <div class="field" style="flex:2"><label>Custom user agent</label><input type="text" id="ua" value="${esc(adv.user_agent || "")}" disabled></div>
        <div class="field"><label>Retry attempts</label><input type="number" id="retries" value="${adv.retry_attempts || 3}" disabled></div>
        <div class="field"><label>Retry delays</label><input type="text" value="${(adv.retry_delays || [2, 5]).join(", ")}s" disabled></div>
      </div>`)}

    <button class="btn btn-primary" id="save" style="margin-top:var(--space-3)">Save Settings</button>`;

  // Token controls
  view.querySelector("#reveal").addEventListener("click", (e) => {
    const t = view.querySelector("#token"); const show = t.type === "password";
    t.type = show ? "text" : "password"; e.target.textContent = show ? "Hide" : "Show";
  });
  view.querySelector("#savetok").addEventListener("click", async () => {
    const token = view.querySelector("#token").value.trim();
    if (!token) return toast("Enter a token first", "error");
    try { await api.post("/cloudflare/token", { token }); toast("Token saved", "success");
      view.querySelector("#token").value = ""; }
    catch (err) { toast(err.message, "error"); }
  });
  view.querySelector("#verify").addEventListener("click", async (e) => {
    e.target.disabled = true;
    try { const r = await api.post("/cloudflare/token/verify");
      view.querySelector("#tokbadge").innerHTML = tokenBadge(r.valid ? "valid" : "missing");
      toast(r.valid ? "Token valid" : "Invalid: " + r.message, r.valid ? "success" : "error"); }
    catch (err) { toast(err.message, "error"); }
    e.target.disabled = false;
  });
  view.querySelector("#refresh").addEventListener("click", async () => {
    try {
      const { zones } = await api.get("/cloudflare/zones");
      const sel = view.querySelector("#zone");
      sel.innerHTML = zones.map(z => `<option value="${esc(z.id)}|${esc(z.name)}" ${z.id === s.cloudflare_zone_id ? "selected" : ""}>${esc(z.name)}</option>`).join("");
      toast(`${zones.length} zone(s) loaded`);
    } catch (err) { toast(err.message, "error"); }
  });

  view.querySelector("#save").addEventListener("click", async () => {
    const zoneVal = view.querySelector("#zone").value.split("|");
    const payload = {
      sync_interval_minutes: +view.querySelector("#interval").value,
      run_on_startup: view.querySelector("#startup").value === "true",
      ip_provider: view.querySelector("#ipname").value.trim(),
      ip_provider_url: view.querySelector("#ipurl").value.trim(),
      max_log_entries: +view.querySelector("#maxlog").value,
      log_retention_days: +view.querySelector("#retention").value,
      ui_bind_host: view.querySelector("#host").value,
      ui_port: +view.querySelector("#port").value,
    };
    if (zoneVal.length === 2) { payload.cloudflare_zone_id = zoneVal[0]; payload.cloudflare_zone_name = zoneVal[1]; }
    try { await api.patch("/settings", payload); toast("Settings saved", "success"); }
    catch (err) { toast(err.message, "error"); }
  });
}

function section(title, inner) {
  return `<div class="card" style="margin-bottom:var(--space-4)">
    <div class="card-title">${esc(title)}</div>${inner}</div>`;
}

function tokenBadge(status) {
  const map = { valid: ["Valid", "success"], missing: ["Not set", "warning"], set: ["Saved", "info"] };
  const [t, k] = map[status] || ["Unknown", "warning"];
  return `<span class="pill ${k}">${t}</span>`;
}
