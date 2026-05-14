import { api } from "./api.js";

let _getDeviceId = null;
let _schedule = [];

export function initRelay(getDeviceId) {
  _getDeviceId = getDeviceId;

  document.getElementById("btn-relay-on").addEventListener("click", async () => {
    const id = _getDeviceId();
    if (!id) return;
    const duration = parseInt(document.getElementById("relay-duration").value, 10) || 300;
    await api.relayOn(id, duration);
    flash("Relay ON command queued");
  });

  document.getElementById("btn-relay-off").addEventListener("click", async () => {
    const id = _getDeviceId();
    if (!id) return;
    await api.relayOff(id);
    flash("Relay OFF command queued");
  });

  document.getElementById("slot-condition").addEventListener("change", (e) => {
    const show = e.target.value === "soil";
    document.getElementById("slot-condition-value").classList.toggle("hidden", !show);
    document.getElementById("slot-condition-unit").classList.toggle("hidden", !show);
  });

  document.getElementById("btn-add-slot").addEventListener("click", addSlot);
  document.getElementById("btn-save-schedule").addEventListener("click", saveSchedule);

  renderSchedule();  // show empty state immediately; loadSchedule() called from app.js after device loads
}

export function reloadSchedule() {
  loadSchedule();
}

async function loadSchedule() {
  const id = _getDeviceId();
  if (!id) return;
  try {
    const data = await api.getSchedule(id);
    _schedule = data.schedule || [];
  } catch {
    _schedule = [];
  }
  renderSchedule();
}

function renderSchedule() {
  const tbody = document.getElementById("schedule-rows");
  tbody.innerHTML = "";

  if (_schedule.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="empty-row">No schedule entries yet.</td></tr>';
    return;
  }

  _schedule.forEach((slot, i) => {
    const duration = Math.round(slot.duration_s / 60) + " min";
    const condition = slot.skip_if
      ? `${slot.skip_if.sensor} ${slot.skip_if.op} ${slot.skip_if.value}`
      : "—";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${slot.time}</td>
      <td>${duration}</td>
      <td class="days-cell">${dayBadges(slot.days)}</td>
      <td class="condition-cell">${condition}</td>
      <td><button class="btn-remove" data-i="${i}">×</button></td>`;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll(".btn-remove").forEach(btn =>
    btn.addEventListener("click", () => {
      _schedule.splice(parseInt(btn.dataset.i), 1);
      renderSchedule();
    })
  );
}

function dayBadges(days) {
  return ["mon","tue","wed","thu","fri","sat","sun"].map(d =>
    `<span class="day-badge ${days.includes(d) ? "on" : ""}">${d[0].toUpperCase() + d.slice(1)}</span>`
  ).join("");
}

function addSlot() {
  const time = document.getElementById("slot-time").value;
  const durationMin = parseInt(document.getElementById("slot-duration").value, 10) || 10;
  const days = [...document.querySelectorAll(".day-checkbox:checked")].map(cb => cb.value);

  if (!time)         return flash("Set a time first", "err");
  if (!days.length)  return flash("Select at least one day", "err");

  const slot = { time, duration_s: durationMin * 60, days, skip_if: null };

  const condType = document.getElementById("slot-condition").value;
  if (condType === "soil") {
    const val = parseFloat(document.getElementById("slot-condition-value").value) || 60;
    slot.skip_if = { sensor: "soil_pct", op: ">=", value: val };
  } else if (condType === "no_water") {
    slot.skip_if = { sensor: "water_level", op: "==", value: 0.0 };
  }

  _schedule.push(slot);
  renderSchedule();
}

async function saveSchedule() {
  const id = _getDeviceId();
  if (!id) return;
  try {
    await api.saveSchedule(id, _schedule);
    flash("Saved — device receives it on next sync");
  } catch (e) {
    flash("Save failed: " + e.message, "err");
  }
}

function flash(msg, type = "ok") {
  const el = document.createElement("p");
  el.textContent = msg;
  el.className = "flash " + type;
  const status = document.getElementById("schedule-status");
  status.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}
