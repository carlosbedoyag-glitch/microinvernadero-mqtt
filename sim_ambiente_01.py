import json
import random
import time

import paho.mqtt.client as mqtt

BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883
TOPIC_AMBIENTE = "emergentes/microinvernadero/ambiente/sim_ambiente_01"

client = mqtt.Client(
    callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    client_id="sim_ambiente_01",
)

try:
    client.connect(BROKER_ADDRESS, BROKER_PORT)
    print("[AMBIENTE] Conectado al broker MQTT.")
except Exception as exc:
    print(f"[AMBIENTE][ERROR] No se pudo conectar: {exc}")
    raise SystemExit(1)

client.loop_start()

print("[AMBIENTE] Publicando datos de ambiente...")

sequence = 1
try:
    while True:
        payload = {
            "node_id": "sim_ambiente_01",
            "sequence": sequence,
            "temperature_c": round(20 + random.uniform(-5, 15), 2),
            "humidity_pct": round(40 + random.uniform(0, 50), 2),
            "light_pct": round(random.uniform(0, 100), 2),
            "timestamp": time.time(),
        }

        client.publish(TOPIC_AMBIENTE, json.dumps(payload), qos=1)
        print(
            f"[AMBIENTE #{sequence}] "
            f"temp={payload['temperature_c']} | "
            f"hum={payload['humidity_pct']} | "
            f"luz={payload['light_pct']}"
        )

        sequence += 1
        time.sleep(2)
except KeyboardInterrupt:
    print("\n[AMBIENTE] Deteniendo simulador...")
finally:
    client.loop_stop()
    client.disconnect()
