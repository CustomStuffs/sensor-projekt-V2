"""Boot and scheduler loop for the Pico W sensor hub."""

import gc
import json
import time
from machine import I2C, SPI, Pin, PWM

from drivers.ads1115 import ADS1115
from drivers.lmp91200 import LMP91200
from drivers.relay import Relay
import sensors.ph as ph_sensor
import sensors.ec as ec_sensor
import sensors.temperature as temp_sensor
import sensors.humidity as hum_sensor
import sensors.light as light_sensor
import sensors.motion as motion_sensor
import sensors.soil as soil_sensor
import sensors.probe_temp as probe_temp_sensor
import sensors.water_level as water_level_sensor
from communication import wifi, time_sync, protocol
from storage.ringbuffer import RingBuffer
from power import manager as power
from automation.control import handle_relays

# On-board relays (hardware/docs/schematic.md): K1 via Q1 on GP10, K2 via Q3 on GP15
RELAY_PINS = {1: 10, 2: 15}


def load_config():
    with open("config.json") as f:
        return json.load(f)


def init_hardware(cfg):
    s = cfg["sensors"]
    ads = lmp = pwm_a = pwm_b = i2c = None

    needs_ads = s.get("ph", {}).get("enabled") or s.get("probe_temp", {}).get("enabled")
    needs_i2c = needs_ads or s.get("light", {}).get("enabled")
    if needs_i2c:
        i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
        if needs_ads:
            ads = ADS1115(i2c)

    if s.get("ec", {}).get("enabled"):
        spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
                  sck=Pin(6), mosi=Pin(5), miso=Pin(4))
        cs = Pin(7, Pin.OUT, value=1)
        lmp = LMP91200(spi, cs)
        pwm_a = PWM(Pin(13), freq=2000, duty_u16=0)
        pwm_b = PWM(Pin(14), freq=2000, duty_u16=0)

    if s.get("motion", {}).get("enabled"):
        motion_sensor.start(warmup_s=s["motion"].get("warmup_s", 60))

    max_on_s = cfg["relay"]["max_on_duration_s"]
    relays = {n: Relay(pin_num=pin, max_on_s=max_on_s) for n, pin in RELAY_PINS.items()}
    return ads, lmp, pwm_a, pwm_b, relays, i2c


def read_all_sensors(cfg, ads, lmp, pwm_a, pwm_b, i2c):
    s = cfg["sensors"]
    cal = cfg["calibration"]
    reading = {}

    if s["ph"]["enabled"]:
        reading["ph"] = ph_sensor.read(ads, cal["ph"], channel=s["ph"]["ads_channel"])

    if s["ec"]["enabled"]:
        reading["ec_us"] = ec_sensor.read(ads, lmp, cal["ec"], pwm_a, pwm_b)

    if s["temperature"]["enabled"]:
        reading["temp_c"] = temp_sensor.read()

    if s["humidity"]["enabled"]:
        h, t = hum_sensor.read()
        reading["humidity_pct"] = h
        if reading.get("temp_c") is None:
            reading["temp_c"] = t   # fallback if DS18B20 absent

    if s["light"]["enabled"]:
        reading["lux"] = light_sensor.read(i2c)

    if s["soil"]["enabled"]:
        reading["soil_pct"] = soil_sensor.read(s["soil"], cal["soil"])

    if s["motion"]["enabled"]:
        reading["motion"] = motion_sensor.read()

    if s.get("probe_temp", {}).get("enabled"):
        reading["probe_temp_c"] = probe_temp_sensor.read(
            ads, cal["probe_temp"], channel=s["probe_temp"].get("ads_channel", 1))

    if s.get("water_level", {}).get("enabled"):
        reading["water_level"] = water_level_sensor.read(s["water_level"])

    reading["ts"] = time.time()
    return reading


def run_upload_cycle(cfg, reading, buf, ack_id=None):
    """Connect WiFi, time-sync, upload buffer + current reading, poll commands.
    Returns (commands, new_interval_s) — new_interval_s is None if unchanged.
    """
    srv = cfg["server"]
    wifi_cfg = cfg["wifi"]

    vbus_mv = protocol.vsys_mv()  # measure before WiFi uses GPIO29

    connected = wifi.connect(wifi_cfg["ssid"], wifi_cfg["password"],
                             timeout_s=wifi_cfg["timeout_s"])
    if not connected:
        buf.push(reading)
        return [], None

    uptime = power.uptime_ms()
    new_cfg = time_sync.sync(srv["url"], cfg["device_id"], uptime, timeout_s=srv["timeout_s"])

    if ack_id is not None:
        protocol.ack_command(srv["url"], ack_id, srv)

    readings_to_send = buf.peek_all() + [reading]
    stored = protocol.upload_readings(
        srv["url"], cfg["device_id"], cfg["fw_version"],
        vbus_mv, readings_to_send, srv
    )
    if stored is not None:
        buf.clear()
    else:
        buf.push(reading)

    commands = protocol.poll_commands(srv["url"], cfg["device_id"], srv)
    wifi.disconnect()
    return commands, new_cfg


def main():
    led = Pin("LED", Pin.OUT)
    try:
        cfg = load_config()
    except Exception as e:
        print("config.json load failed:", e)
        while True:
            for _ in range(5):
                led.value(1); time.sleep_ms(100)
                led.value(0); time.sleep_ms(100)
            time.sleep_ms(2000)

    ads, lmp, pwm_a, pwm_b, relays, i2c = init_hardware(cfg)
    buf = RingBuffer(max_slots=cfg["storage"]["buffer_slots"])

    interval_s = cfg["poll_interval_s"]
    ack_id = None

    while True:
        try:
            led.value(1)
            reading = read_all_sensors(cfg, ads, lmp, pwm_a, pwm_b, i2c)
            print("Reading:", reading)

            commands, new_cfg = run_upload_cycle(cfg, reading, buf, ack_id)
            if new_cfg:
                if "interval_s" in new_cfg:
                    interval_s = new_cfg["interval_s"]
                if "relay_schedule" in new_cfg:
                    cfg["relay_schedule"] = new_cfg["relay_schedule"]
            ack_id = handle_relays(commands, relays, reading, cfg)
        except Exception as e:
            import sys
            sys.print_exception(e)
        finally:
            led.value(0)
            gc.collect()
            print("free mem:", gc.mem_free())

        power.sleep(interval_s, relays=relays.values())


main()
