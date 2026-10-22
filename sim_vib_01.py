import json
import math
import random
import time

import paho.mqtt.client as mqtt

BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883
TOPIC_VIBRACION = "emergentes/microinvernadero/vibracion/sim_vib_01"

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="sim_vib_01",
)

try:
    client.connect(BROKER_ADDRESS, BROKER_PORT)
    print("[VIBRACION] Conectado al broker MQTT.")
except Exception as exc:
    print(f"[VIBRACION][ERROR] No se pudo conectar: {exc}")
    raise SystemExit(1)

client.loop_start()

sequence = 1
run_index = 1
ventanas_en_corrida = 0

print("[VIBRACION] Generando ventanas de vibración...")

try:
    while True:
        samples_g = []
        for i in range(100):
            t = i / 100.0
            value = 0.5 * math.sin(2 * math.pi * 10 * t) + random.gauss(0, 0.05)

            if random.random() < 0.05:
                value += random.choice([-1.2, 1.2])

            samples_g.append(round(value, 4))

        run_id = f"run_{run_index:02d}"

        payload = {
            "node_id": "sim_vib_01",
            "run_id": run_id,
            "sequence": sequence,
            "uptime_ms": int(time.time() * 1000),
            "sample_rate_hz": 100,
            "samples_g": samples_g,
            "timestamp": time.time(),
        }

        client.publish(TOPIC_VIBRACION, json.dumps(payload), qos=1)
        print(f"[VIBRACION #{sequence}] run_id={run_id} | ventana enviada")

        sequence += 1
        ventanas_en_corrida += 1

        if ventanas_en_corrida == 10:
            print(f"\n=== FIN CORRIDA {run_id} ===")
            run_index += 1
            ventanas_en_corrida = 0

        time.sleep(1)
except KeyboardInterrupt:
    print("\n[VIBRACION] Deteniendo simulador...")
finally:
    client.loop_stop()
    client.disconnect()
