"""
project_pico/main.py — Template / Vorlage
Zeigt wie uart_debug in die bestehende Firmware integriert wird.
WICHTIG: uart_debug muss als erster Import stehen.
"""
import uart_debug  # FIRST — hijacks sys.stdout before anything else runs

import utime

# Ab hier landen alle print()-Ausgaben auch auf UART → Machine Pico → PC
print("Project Pico booted")
print("Firmware: template v0.1")

counter = 0

while True:
    uart_debug.tick()           # sends heartbeat every 10 s

    # Dein Sensor-Code hier:
    print("tick", counter)
    counter += 1

    utime.sleep(5)
