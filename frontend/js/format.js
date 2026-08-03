// Formatting helpers + a minimal HTML escaper (used everywhere we inject text).
export function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

export function relTime(iso) {
  if (!iso) return "—";
  const then = new Date(iso).getTime();
  if (isNaN(then)) return "—";
  const diff = Math.round((then - Date.now()) / 1000);
  const future = diff > 0;
  const s = Math.abs(diff);
  if (s < 5) return future ? "in 1s" : "just now";
  const value = s < 60 ? `${s}s`
    : s < 3600 ? `${Math.round(s / 60)}m`
      : s < 86400 ? `${Math.round(s / 3600)}h`
        : `${Math.round(s / 86400)}d`;
  return future ? `in ${value}` : `${value} ago`;
}

// "July 4, 2026 at 9:30 PM EDT" — browser's local timezone.
export function fmtDateTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d)) return "—";
  const date = d.toLocaleDateString(undefined, { month: "long", day: "numeric", year: "numeric" });
  const time = d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit", timeZoneName: "short" });
  return `${date} at ${time}`;
}

// Compact form for table cells: "Jul 4, 9:30 PM".
export function fmtShort(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d)) return "—";
  return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" });
}
