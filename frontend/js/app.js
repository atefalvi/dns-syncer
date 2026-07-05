import { api } from "./api.js";
import { toast, icons } from "./state.js";
import * as overview from "./screens/overview.js";
import * as records from "./screens/records.js";
import * as logs from "./screens/logs.js";
import * as integrations from "./screens/integrations.js";
import * as settings from "./screens/settings.js";

const SCREENS = {
  overview: { label: "Overview", mod: overview },
  records: { label: "Records", mod: records },
  logs: { label: "Logs", mod: logs },
  integrations: { label: "Integrations", mod: integrations },
  settings: { label: "Settings", mod: settings },
};

const view = document.getElementById("view");
let refreshTimer = null;

// Build sidebar nav.
document.getElementById("nav").innerHTML = Object.entries(SCREENS).map(([id, s]) =>
  `<a href="#${id}" data-screen="${id}">${icons[id]}<span>${s.label}</span></a>`).join("");

async function route() {
  const id = (location.hash.slice(1) || "overview");
  const screen = SCREENS[id] || SCREENS.overview;
  document.querySelectorAll("#nav a").forEach(a =>
    a.classList.toggle("active", a.dataset.screen === id));

  clearInterval(refreshTimer);
  view.innerHTML = `<div class="empty">Loading…</div>`;
  try { await screen.mod.render(view); }
  catch (e) { view.innerHTML = `<div class="empty">Failed to load: ${e.message}</div>`; }

  // Overview refreshes every 30s only while open (§24.4).
  if (id === "overview") refreshTimer = setInterval(() => screen.mod.render(view).catch(() => {}), 30000);
}

async function refreshHealth() {
  const el = document.getElementById("health");
  try {
    const s = await api.get("/status");
    const map = { healthy: ["Healthy", "success"], degraded: ["Degraded", "warning"],
      setup: ["Setup needed", "warning"] };
    const [t, k] = map[s.app_status] || ["Unknown", "neutral"];
    el.className = "pill " + k;
    el.innerHTML = `<span class="dot ${k}"></span>${t}`;
  } catch (_) { el.className = "pill danger"; el.textContent = "Offline"; }
}

document.getElementById("btn-sync").addEventListener("click", async (e) => {
  e.target.disabled = true; e.target.textContent = "Syncing…";
  try { const r = await api.post("/sync/run");
    toast(`Sync done: ${r.records_updated} updated, ${r.records_failed} failed`,
      r.records_failed ? "error" : "success"); }
  catch (err) { toast(err.message, "error"); }
  e.target.disabled = false; e.target.textContent = "Run Sync";
  refreshHealth(); route();
});

document.getElementById("btn-verify").addEventListener("click", async (e) => {
  e.target.disabled = true;
  try { const r = await api.post("/cloudflare/token/verify");
    toast(r.valid ? "Token valid" : "Token invalid: " + r.message, r.valid ? "success" : "error"); }
  catch (err) { toast(err.message, "error"); }
  e.target.disabled = false; refreshHealth();
});

// Real version in the sidebar footer.
api.get("/health").then(h => {
  document.querySelector(".sidebar-foot").innerHTML = `DNS Syncer<br>v${h.version}`;
}).catch(() => {});

window.addEventListener("hashchange", route);
route();
refreshHealth();
setInterval(refreshHealth, 30000);
