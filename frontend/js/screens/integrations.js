import { api } from "../api.js";
import { esc } from "../format.js";
import { toast, modal } from "../state.js";

const TRIGGERS = [
  { id: "RECORD_UPDATED", label: "DNS record changed", desc: "Send only when Cloudflare is updated to a new IP." },
  { id: "RECORD_UPDATE_FAILED", label: "Record update failed", desc: "Send when a specific DNS record could not be updated." },
  { id: "SYNC_FAILED", label: "Sync failed", desc: "Send when DNS Syncer could not complete a sync run." },
  { id: "TOKEN_INVALID", label: "Token invalid", desc: "Send when the Cloudflare API token fails verification." },
  { id: "SYNC_COMPLETE", label: "Every sync check", desc: "Sends after every scheduled check, even when nothing changed." },
  { id: "SERVICE_STARTED", label: "Service started", desc: "Sends when the DNS Syncer web service starts or restarts." },
];

const DEFAULT_TRIGGERS = ["RECORD_UPDATED"];

const PRESETS = {
  webhook: { name: "Generic Webhook", body: {
    source: "dns-syncer", product: "DNS Syncer by DataDreamer", event: "{{event}}",
    message: "{{message}}", old_ip: "{{old_ip}}", new_ip: "{{new_ip}}",
    record: "{{record_name}}", zone: "{{zone}}", records_updated: "{{records_updated}}",
    records_failed: "{{records_failed}}", timestamp: "{{timestamp}}" } },
  discord: { name: "Discord alerts", body: { content: "**DNS Syncer**\n{{message}}\nCurrent IP: `{{new_ip}}`" } },
  slack: { name: "Slack alerts", body: { text: "*DNS Syncer* — {{message}} (current IP: `{{new_ip}}`)" } },
  teams: { name: "Teams alerts", body: { text: "DNS Syncer — {{message}} (current IP: {{new_ip}})" } },
};

export async function render(view) {
  view.innerHTML = `<div class="page-head">
      <div class="kicker">Notifications</div>
      <h2>Integrations</h2>
      <div class="sub">Send DNS Syncer events to any API or notification platform.</div>
    </div>
    <div class="toolbar">
      <div class="spacer"></div>
      <button class="btn btn-secondary" data-add="webhook">+ Generic Webhook</button>
      <button class="btn btn-secondary" data-add="discord">+ Discord</button>
      <button class="btn btn-secondary" data-add="slack">+ Slack</button>
      <button class="btn btn-secondary" data-add="teams">+ Teams</button>
    </div>
    <div class="grid grid-2" id="list"></div>`;

  view.querySelectorAll("[data-add]").forEach(b =>
    b.addEventListener("click", () => editor(null, b.dataset.add, load)));

  async function load() {
    const items = await api.get("/integrations");
    const list = view.querySelector("#list");
    if (!items.length) { list.innerHTML = `<div class="empty">No integrations yet.</div>`; return; }
    list.innerHTML = items.map(card).join("");
    list.querySelectorAll("[data-test]").forEach(el => el.addEventListener("click", async (e) => {
      e.target.disabled = true; e.target.textContent = "Sending…";
      try { const r = await api.post(`/integrations/${e.target.dataset.test}/test`);
        toast(r.ok ? "Test sent" : "Test failed: " + r.error, r.ok ? "success" : "error"); }
      catch (err) { toast(err.message, "error"); }
      e.target.disabled = false; e.target.textContent = "Test";
    }));
    list.querySelectorAll("[data-edit]").forEach(el => el.addEventListener("click",
      () => editor(items.find(i => i.id === el.dataset.edit), null, load)));
    list.querySelectorAll("[data-del]").forEach(el => el.addEventListener("click", async (e) => {
      if (!confirm("Delete this integration?")) return;
      await api.del(`/integrations/${e.target.dataset.del}`); toast("Deleted"); load();
    }));
  }

  function card(i) {
    const conn = i.connected
      ? `<span class="pill success"><span class="dot success"></span>Connected</span>`
      : `<span class="pill warning">Not connected</span>`;
    return `<div class="card int-card">
      <div class="card-row-head">
        <div><div class="name">${esc(i.name)}</div>
          <div class="desc">${esc(i.type)} · ${(i.trigger_events || []).length} event(s)</div></div>
        ${conn}
      </div>
      <div class="event-summary">${eventSummary(i.trigger_events || [])}</div>
      <div class="foot">
        <button class="btn btn-ghost btn-sm" data-edit="${esc(i.id)}">Configure</button>
        <button class="btn btn-ghost btn-sm" data-test="${esc(i.id)}">Test</button>
        <button class="btn btn-ghost btn-sm" data-del="${esc(i.id)}">Delete</button>
      </div>
    </div>`;
  }

  await load();
}

function editor(existing, presetType, onDone) {
  const type = existing ? existing.type : presetType;
  const preset = PRESETS[type] || PRESETS.webhook;
  const body = existing?.body_template && Object.keys(existing.body_template).length
    ? existing.body_template : preset.body;
  const triggers = existing?.trigger_events || DEFAULT_TRIGGERS;

  const m = modal(`<h3>${existing ? "Configure" : "New"} ${esc(type)} integration</h3>
    <div class="field"><label>Integration Name</label>
      <input type="text" id="name" value="${esc(existing?.name || preset.name)}"></div>
    <label class="switch"><input type="checkbox" id="enabled" ${existing?.enabled !== false ? "checked" : ""}>&nbsp;Enabled</label>
    <div class="field field-spaced"><label>Trigger Events</label>
      <div class="hint">For change-only notifications, keep <strong>DNS record changed</strong> selected and uncheck every other event.</div>
      <div class="event-options">${TRIGGERS.map(t => `<label class="event-option">
        <input type="checkbox" value="${t.id}" ${triggers.includes(t.id) ? "checked" : ""}>
        <span><strong>${esc(t.label)}</strong><small>${esc(t.id)} · ${esc(t.desc)}</small></span>
      </label>`).join("")}</div>
    </div>
    <div class="row">
      <div class="field"><label>Method</label><select id="method">
        ${["POST", "PUT", "PATCH"].map(x => `<option ${existing?.method === x ? "selected" : ""}>${x}</option>`).join("")}</select></div>
      <div class="field field-wide"><label>URL ${existing ? "(leave blank to keep)" : ""}</label>
        <input type="text" id="url" placeholder="https://…"></div>
    </div>
    <div class="field"><label>Headers (JSON)</label>
      <textarea id="headers" class="textarea-sm">${esc(JSON.stringify(existing?.headers || {}, null, 2))}</textarea></div>
    <div class="field"><label>Body Template (JSON)</label>
      <textarea id="body">${esc(JSON.stringify(body, null, 2))}</textarea>
      <div class="hint">Variables: {{event}} {{message}} {{old_ip}} {{new_ip}} {{record_name}} {{record_type}} {{zone}} {{records_checked}} {{records_updated}} {{records_unchanged}} {{records_failed}} {{records}} {{timestamp}}</div></div>
    <div class="modal-actions">
      <button class="btn btn-secondary" id="cancel">Cancel</button>
      <button class="btn btn-primary" id="save">Save Integration</button>
    </div>`);

  m.el.querySelector("#cancel").addEventListener("click", m.close);
  m.el.querySelector("#save").addEventListener("click", async (e) => {
    let headers, bodyTpl;
    try { headers = JSON.parse(m.el.querySelector("#headers").value || "{}");
          bodyTpl = JSON.parse(m.el.querySelector("#body").value || "{}"); }
    catch (_) { return toast("Headers/Body must be valid JSON", "error"); }
    const payload = {
      name: m.el.querySelector("#name").value.trim(), type,
      enabled: m.el.querySelector("#enabled").checked,
      trigger_events: [...m.el.querySelectorAll(".event-options input:checked")].map(c => c.value),
      method: m.el.querySelector("#method").value,
      url: m.el.querySelector("#url").value.trim(),
      headers, body_template: bodyTpl,
    };
    e.target.disabled = true;
    try {
      if (existing) await api.patch(`/integrations/${existing.id}`, payload);
      else await api.post("/integrations", payload);
      toast("Saved", "success"); m.close(); onDone();
    } catch (err) { toast(err.message, "error"); e.target.disabled = false; }
  });
}

function eventSummary(events) {
  if (!events.length) return "No triggers";
  if (events.length === 1 && events[0] === "RECORD_UPDATED") return "Change-only notifications";
  const labels = events.map(id => TRIGGERS.find(t => t.id === id)?.label || id);
  return labels.join(", ");
}
