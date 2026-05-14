import { api } from "./api.js";
import { initChart, updateChart } from "./charts.js";
import { initRelay, reloadSchedule } from "./relay.js";

let currentDevice = null;
let currentHours = 24;

function getDeviceId() { return currentDevice; }

function showError(msg) { document.getElementById("error-banner").textContent = msg; }
function clearError()   { document.getElementById("error-banner").textContent = ""; }

async function loadDevices() {
  try {
    const { devices } = await api.devices();
    const select = document.getElementById("device-select");
    select.innerHTML = devices.map(d =>
      `<option value="${d.id}">${d.id}</option>`
    ).join("");
    if (devices.length) {
      currentDevice = devices[0].id;
      updateLastSeen(devices[0].last_seen);
    }
    clearError();
  } catch (e) {
    showError("Could not reach server: " + e.message);
  }
}

function updateLastSeen(ts) {
  const el = document.getElementById("last-seen");
  el.textContent = ts ? "Last seen: " + new Date(ts * 1000).toLocaleString() : "";
}

async function refresh() {
  if (!currentDevice) return;
  try {
    const { devices } = await api.devices();
    const dev = devices.find(d => d.id === currentDevice);
    if (dev) updateLastSeen(dev.last_seen);
    await updateChart(currentDevice, currentHours);
    clearError();
  } catch (e) {
    showError("Refresh failed: " + e.message);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  initChart();
  initRelay(getDeviceId);

  await loadDevices();
  await refresh();
  reloadSchedule();

  document.getElementById("device-select").addEventListener("change", async e => {
    currentDevice = e.target.value;
    await refresh();
    reloadSchedule();
  });

  document.querySelectorAll("#time-range button").forEach(btn => {
    btn.addEventListener("click", async () => {
      document.querySelectorAll("#time-range button").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentHours = parseInt(btn.dataset.hours, 10);
      await refresh();
    });
  });

  document.querySelectorAll("[data-sensor]").forEach(cb => {
    cb.addEventListener("change", refresh);
  });

  // Auto-refresh every 2 minutes
  setInterval(refresh, 120_000);
});
