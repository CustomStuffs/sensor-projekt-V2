"""Relay control: apply a server command, then the schedule, then the sensor rules.

Priority per relay: manual server command > time schedule > sensor threshold rules.
A command for one relay does not stop the automation of the other relay.
Commands, slots and rules carry an optional "relay": 1 | 2 (default 1).
"""

from automation.rules import evaluate, evaluate_schedule, relay_of


def handle_relays(commands, relays, reading, cfg):
    """
    relays: {relay number: Relay}. Returns the executed command id (to ack on the next
    upload), or None if no server command ran this cycle.
    """
    ack_id = None
    commanded = set()

    # Manual override from the server (one command per cycle, acked next cycle)
    if commands:
        cmd = commands[0]
        ack_id = cmd.get("id")
        n = relay_of(cmd)
        relay = relays.get(n)
        if relay is None:
            print("command for unknown relay", n, "- ignored, acked")
        else:
            action = cmd.get("action")
            if action == "relay_on":
                relay.on(cmd.get("duration_s") or 60)
            elif action == "relay_off":
                relay.off()
            commanded.add(n)

    # Time-based schedule (highest priority after manual commands)
    scheduled = set()
    for hit in evaluate_schedule(cfg.get("relay_schedule", []), reading, reading.get("ts", 0)):
        n = hit["relay"]
        if n in relays and n not in commanded:
            relays[n].on(hit["duration_s"])
            scheduled.add(n)

    # Sensor threshold rules — relay_off checked first inside evaluate()
    for n, relay in relays.items():
        if n in commanded or n in scheduled:
            continue
        rule = evaluate(cfg.get("relay_rules", []), reading, relay=n)
        if rule:
            if rule["action"] == "relay_on":
                relay.on(rule["duration_s"])
            elif rule["action"] == "relay_off":
                relay.off()

    return ack_id
