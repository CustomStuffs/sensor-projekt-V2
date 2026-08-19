# Sensor Calibration Guide

Practical guide for reliable calibration of the sensors used in the Sensor Hub (pH, EC, temperature, humidity).  
Designed so calibration can be triggered from the web dashboard with a simple button / wizard while the actual math runs in the firmware background.

The calibration parameters are stored in `config.json` (or a dedicated calibration section) and applied on every reading.

---

## 1. pH Sensor

**Hardware:** ADS1115 AIN0 → voltage from pH probe (via LMP or direct analog front-end).

**Current firmware model** (`sensors/ph.py`):
```python
cal = { "v_at_ph4": float, "v_at_ph7": float }

slope = (7.0 - 4.0) / (v7 - v4)
ph = 7.0 + slope * (v - v7)
```
This is a classic **2-point linear calibration** between pH 4 and pH 7.

### Recommended procedure

1. **Prepare**
   - Fresh buffer solutions: pH 4.00 / 4.01 and pH 7.00 (optionally also pH 10.00 for 3-point).
   - Use separate clean containers. Never pour used buffer back into the bottle.
   - Rinse the probe thoroughly with distilled / deionized water between solutions. Gently blot dry (do not rub the glass bulb).

2. **Temperature**
   - Bring buffers and probe to the same temperature (ideally 20–25 °C).
   - The firmware does not yet apply Nernst temperature compensation on the slope. For best accuracy keep temperature close to the calibration temperature or add compensation later.

3. **Calibration steps (2-point)**
   - Immerse probe in **pH 7.00** buffer.
   - Wait until the voltage reading is stable (drift < ~1–2 mV over 30–60 s).
   - Record `v_at_ph7`.
   - Rinse → immerse in **pH 4.00 / 4.01** buffer → wait for stability → record `v_at_ph4`.

4. **Optional 3-point**
   - Add pH 10.00 buffer.
   - Firmware currently uses only two points. Extending to piecewise linear or least-squares fit is straightforward.

5. **Quality check**
   - After calibration, put the probe back into pH 7. It should read 7.00 ± 0.05.
   - Calculate slope: `(7-4)/(v7-v4)`. Typical healthy glass electrodes give roughly 50–60 mV per pH unit (≈ 0.05–0.06 V/pH depending on the front-end gain).

**Frequency:** Weekly during continuous use, or after any longer storage / cleaning.

**Storage tip:** Keep the pH probe wet in KCl storage solution when not in use.

---

## 2. EC / Conductivity Sensor

**Hardware:** LMP91200 AFE + ADS1115 AIN3 (signal) + AIN1 (NTC temperature compensation).  
Excitation via complementary PWM on GP13/GP14.

**Current firmware model** (`sensors/ec.py`):
```python
cal = {
    "cell_constant": float,   # K in cm⁻¹
    "ref_voltage": float,     # usually 1.65 V
    "ref_temp_c": float       # usually 25.0
}
```
Temperature compensation is already implemented at 2 %/°C relative to `ref_temp_c`.

### Recommended procedure

1. **Prepare**
   - Standard solutions, e.g. 1413 µS/cm (and optionally 12.88 mS/cm for a second point).
   - Distilled / deionized water for rinsing.
   - Ensure the sensor is clean and free of air bubbles.

2. **Dry / zero point (optional but recommended)**
   - Hold the probe in air (completely dry).
   - Confirm near-zero reading.

3. **Calibration steps**
   - Rinse thoroughly with distilled water until the reading is very low.
   - Immerse in the 1413 µS/cm solution. Gently move the probe to remove bubbles.
   - Wait for temperature equilibrium and stable voltage.
   - Record the raw voltage / calculate the required `cell_constant` so that the compensated result equals 1413 µS/cm at the measured temperature.
   - For higher accuracy, repeat with a second standard (e.g. 12.88 mS/cm) and average or use a linear fit.

4. **Temperature**
   - The NTC on AIN1 already provides compensation. Make sure the NTC is thermally coupled to the conductivity cell.

**Frequency:** Every 2–4 weeks or when readings look suspicious.

---

## 3. Temperature Sensor

**Hardware:** DS18B20 (1-Wire on GP8) + NTC on the EC board for local compensation.

### Recommended procedure

Most digital sensors (DS18B20) are factory-calibrated to ±0.5 °C. For higher accuracy:

**1-point offset (simple)**
- Place sensor next to a trusted reference thermometer at room temperature.
- `offset = T_ref - T_sensor`
- Store and apply: `T_corrected = T_raw + offset`

**2-point (gain + offset)**
- Ice bath (0.0 °C) and boiling water (≈100 °C, correct for altitude) or two controlled baths.
- Calculate:
  ```
  gain   = (T_ref2 - T_ref1) / (T_raw2 - T_raw1)
  offset = T_ref1 - gain * T_raw1
  T_corrected = gain * T_raw + offset
  ```

Store `gain` and `offset` in the calibration config.

**Frequency:** Every few months or when comparing against a known good thermometer.

---

## 4. Humidity Sensor (DHT22 / similar)

### Recommended procedure – Saturated salt solutions

This is the most practical and reliable DIY method.

| Salt                        | Approx. % RH at 25 °C |
|-----------------------------|-----------------------|
| Lithium chloride (LiCl)     | ~11 %                 |
| Magnesium chloride (MgCl₂)  | ~33 %                 |
| Sodium chloride (NaCl)      | ~75 %                 |
| Potassium chloride (KCl)    | ~85 %                 |
| Potassium sulphate (K₂SO₄)  | ~97 %                 |

**Steps**
1. Make a saturated slurry (salt + a little distilled water) in a small container.
2. Place the slurry and the humidity sensor inside a sealed airtight box.
3. Leave for 12–24 hours so equilibrium is reached (temperature must be stable).
4. Record the sensor reading and the known RH value of the salt.
5. Calculate offset (and optionally gain if you do two points, e.g. 33 % + 75 %).

Apply linear correction in firmware the same way as for temperature.

**Frequency:** Every 1–3 months.

---

## Dashboard / One-Button Calibration Workflow

Goal: User only presses a button and follows simple on-screen instructions. All math and storage happen in the background.

### Suggested flow

1. User opens **Calibration** page / modal in the dashboard.
2. Selects the sensor (pH / EC / Temperature / Humidity).
3. Wizard appears:
   - Clear instruction (“Rinse probe → immerse in pH 7.00 buffer”).
   - Live raw reading + stability indicator (e.g. “Stable for 15 s”).
   - Button **“Capture this point”**.
4. After all required points are captured, firmware / server calculates the calibration coefficients.
5. Coefficients are written to persistent storage (`config.json` or a dedicated calibration file / database table).
6. Confirmation screen shows the new slope / offset / cell constant and a quick verification reading.
7. Optional: log calibration event with timestamp and previous values for audit trail.

### Implementation notes for this project

- Firmware already accepts calibration dictionaries for pH and EC.
- Extend `config.json` (or a separate `calibration.json`) with the fields shown above.
- Add a command endpoint (similar to the existing relay commands) that puts the device into “calibration mode” and accepts the captured points.
- On the dashboard side, a simple multi-step modal is enough; no complex state machine is required.
- Always apply temperature compensation where possible (already present for EC).

---

## Reliability Best Practices

- Always use **fresh** calibration solutions.
- Rinse thoroughly between points with distilled water.
- Wait for true stability (temperature + sensor drift).
- Record temperature of the calibration solutions.
- After calibration, verify with a third independent solution or known reference.
- Monitor slope / cell constant over time – large changes indicate aging or contamination of the sensor.
- Store calibration history (timestamp + coefficients) so drift can be tracked.
- For pH: never let the probe dry out.

---

## Quick Reference – Calibration Frequency

| Sensor       | Recommended interval          | Critical failure modes          |
|--------------|-------------------------------|---------------------------------|
| pH           | Weekly (or after storage)     | Electrode aging, contamination  |
| EC           | 2–4 weeks                     | Dirty cell, air bubbles         |
| Temperature  | Every few months              | Rare                            |
| Humidity     | 1–3 months                    | Drift, contamination            |

---

## Related files in this repository

- `firmware/src/sensors/ph.py` – 2-point pH math
- `firmware/src/sensors/ec.py` – EC + NTC temperature compensation
- `firmware/tests/test_calibration.py` – unit tests for the calibration formulas
- `firmware/src/config.json` – place to store calibration coefficients

Feel free to extend the firmware with a dedicated calibration state machine and corresponding dashboard UI. The math is already solid and tested.
