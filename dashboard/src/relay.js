import { api } from "./api.js";

export function initRelay(getDeviceId) {
  document.getElementById("btn-relay-on").addEventListener("click", async () => {
    const id = getDeviceId();
    if (!id) return;
    const duration = parseInt(document.getElementById("relay-duration").value, 10) || 300;
    await api.relayOn(id, duration);
    flash("Relay ON command queued");
  });

  document.getElementById("btn-relay-off").addEventListener("click", async () => {
    const id = getDeviceId();
    if (!id) return;
    await api.relayOff(id);
    flash("Relay OFF command queued");
  });
}

function flash(msg) {
  const el = document.createElement("p");
  el.textContent = msg;
  el.className = "flash";
  document.getElementById("relay-controls").appendChild(el);
  setTimeout(() => el.remove(), 3000);
}
