import { api } from "./api.js";

const SENSOR_META = {
  temp_c:       { label: "Temp (°C)",   color: "#e74c3c", yAxis: "y" },
  humidity_pct: { label: "Humidity (%)", color: "#3498db", yAxis: "y" },
  ph:           { label: "pH",          color: "#2ecc71", yAxis: "y" },
  ec_us:        { label: "EC (µS/cm)",  color: "#f39c12", yAxis: "y2" },
  lux:          { label: "Light (lux)", color: "#9b59b6", yAxis: "y2" },
  soil_pct:     { label: "Soil (%)",    color: "#1abc9c", yAxis: "y" },
  water_level:  { label: "Water",       color: "#5dade2", yAxis: "y" },
};

let chart = null;

export function initChart() {
  const ctx = document.getElementById("sensor-chart").getContext("2d");
  chart = new Chart(ctx, {
    type: "line",
    data: { datasets: [] },
    options: {
      animation: false,
      parsing: false,
      scales: {
        x: { type: "time", time: { unit: "hour" } },
        y:  { position: "left",  title: { display: true, text: "Primary" } },
        y2: { position: "right", title: { display: true, text: "EC / Lux" }, grid: { drawOnChartArea: false } },
      },
      plugins: { legend: { display: false } },
    },
  });
}

export async function updateChart(deviceId, hours) {
  const now = Math.floor(Date.now() / 1000);
  const from = now - hours * 3600;
  const limit = Math.min(hours * 4, 2000);   // 4 readings/hr headroom, server max 2000
  const { readings } = await api.readings(deviceId, from, now, limit);

  const active = new Set(
    [...document.querySelectorAll("[data-sensor]:checked")].map(el => el.dataset.sensor)
  );

  chart.data.datasets = Object.entries(SENSOR_META)
    .filter(([key]) => active.has(key))
    .map(([key, meta]) => ({
      label: meta.label,
      borderColor: meta.color,
      backgroundColor: meta.color + "22",
      yAxisID: meta.yAxis,
      data: readings
        .filter(r => r[key] !== null && r[key] !== undefined)
        .map(r => ({ x: r.ts * 1000, y: r[key] }))
        .reverse(),
      pointRadius: 2,
      borderWidth: 1.5,
      tension: 0.2,
    }));

  chart.update();
}
