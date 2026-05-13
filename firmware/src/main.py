"""Boot and scheduler loop for the Pico W sensor hub."""

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
from communication import wifi, time_sync, protocol
from storage.ringbuffer import RingBuffer
from power import manager as power
from automation.rules import evaluate


def load_config():
    with open("config.json") as f:
        return json.load(f)


def init_hardware(cfg):
    i2c = I2C(1, sda=Pin(2), scl=Pin(3), freq=400_000)
    ads = ADS1115(i2c)

    spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
              sck=Pin(6), mosi=Pin(5), miso=Pin(4))
    cs = Pin(7, Pin.OUT, value=1)
    lmp = LMP91200(spi, cs)

    pwm_a = PWM(Pin(13), freq=2000, duty_u16=32768)
    pwm_b = PWM(Pin(14), freq=2000, duty_u16=32768)

    relay = Relay(pin_num=10, max_on_s=cfg["relay"]["max_on_duration_s"])

    return ads, lmp, pwm_a, pwm_b, relay, i2c


def read_all_sensors(cfg, ads, lmp, pwm_a, pwm_b, i2c):
    s = cfg["sensors"]
    cal = cfg["calibration"]
    reading = {}

    if s["ph"]["enabled"]:
        reading["ph"] = ph_sensor.read(ads, cal["ph"])

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
        reading["soil_pct"] = soil_sensor.read(ads, cal["soil"],
                                               channel=s["soil"]["ads_channel"])

    if s["motion"]["enabled"]:
        detected = motion_sensor.read(scan_duration_s=s["motion"]["scan_duration_s"])
        reading["motion"] = detected

    reading["ts"] = time.time()
    return reading


def run_upload_cycle(cfg, reading, buf):
    """Connect WiFi, time-sync, upload buffer + current reading, poll commands."""
    srv = cfg["server"]
    wifi_cfg = cfg["wifi"]

    connected = wifi.connect(wifi_cfg["ssid"], wifi_cfg["password"],
                             timeout_s=wifi_cfg["timeout_s"])
    if not connected:
        buf.push(reading)
        return []

    uptime = power.uptime_ms()
    time_sync.sync(srv["url"], cfg["device_id"], uptime, timeout_s=srv["timeout_s"])

    readings_to_send = buf.peek_all() + [reading]
    stored = protocol.upload_readings(
        srv["url"], cfg["device_id"], cfg["fw_version"],
        protocol.vbus_mv(), readings_to_send, srv
    )
    if stored is not None:
        buf.clear()
    else:
        buf.push(reading)

    commands = protocol.poll_commands(srv["url"], cfg["device_id"], srv)
    wifi.disconnect()
    return commands


def handle_relay(commands, relay, reading, cfg):
    """Execute server command (manual override) or fire auto-rules."""
    if commands:
        cmd = commands[0]
        action = cmd.get("action")
        duration = cmd.get("duration_s", 60)
        if action == "relay_on":
            relay.on(duration)
        elif action == "relay_off":
            relay.off()
        # ACK is sent next cycle when WiFi reconnects; command id stored would
        # need a small queue — kept simple here by polling after each cycle.
        return

    rule = evaluate(cfg["relay_rules"], reading)
    if rule and rule["action"] == "relay_on":
        relay.on(rule["duration_s"])


def main():
    led = Pin("LED", Pin.OUT)
    cfg = load_config()
    ads, lmp, pwm_a, pwm_b, relay, i2c = init_hardware(cfg)
    buf = RingBuffer(max_slots=cfg["storage"]["buffer_slots"])

    interval_s = cfg["poll_interval_s"]

    while True:
        led.value(1)
        reading = read_all_sensors(cfg, ads, lmp, pwm_a, pwm_b, i2c)
        print("Reading:", reading)

        commands = run_upload_cycle(cfg, reading, buf)
        handle_relay(commands, relay, reading, cfg)

        led.value(0)
        power.sleep(interval_s, relay=relay)


main()
