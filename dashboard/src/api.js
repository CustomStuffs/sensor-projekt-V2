const BASE = "";   // same origin; update to "http://<tailscale-ip>:8080" if needed

async function req(method, path, body) {
  const opts = { method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const resp = await fetch(BASE + path, opts);
  if (!resp.ok) throw new Error(`${method} ${path} → ${resp.status}`);
  return resp.json();
}

export const api = {
  devices: ()                               => req("GET", "/api/devices"),
  readings: (deviceId, from, to, limit=500) => req("GET",
    `/api/readings?device_id=${deviceId}&from=${from}&to=${to}&limit=${limit}`),
  relayOn:  (deviceId, relay, duration_s)   => req("POST", "/api/commands",
    { device_id: deviceId, action: "relay_on", duration_s, relay }),
  relayOff: (deviceId, relay)               => req("POST", "/api/commands",
    { device_id: deviceId, action: "relay_off", relay }),
  getSchedule:  (deviceId)                  => req("GET",  `/api/schedule/${deviceId}`),
  saveSchedule: (deviceId, schedule)        => req("POST", `/api/schedule/${deviceId}`, { schedule }),
};
