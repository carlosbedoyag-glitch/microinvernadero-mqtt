import json
import math
import statistics
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

import paho.mqtt.client as mqtt
import psutil

BROKER_ADDRESS = "localhost"
BROKER_PORT = 1883

TOPIC_AMBIENTE = "emergentes/microinvernadero/ambiente/sim_ambiente_01"
TOPIC_VIBRACION = "emergentes/microinvernadero/vibracion/sim_vib_01"

MODO_PROCESAMIENTO = "SECUENCIAL"
NUM_WORKERS = 4
MAX_CORRIDAS = 5
VENTANAS_POR_CORRIDA = 10

executor = None
run_times = defaultdict(list)
secuencias_recibidas = set()
tiempos_procesamiento = []
corridas_completadas = 0
wall_start = None


def iniciar_medicion_cpu():
    global wall_start
    psutil.cpu_percent(interval=None)
    wall_start = time.perf_counter()


def finalizar_medicion_cpu():
    if wall_start is None:
        return 0.0
    return psutil.cpu_percent(interval=0.5)


def analizar_ventana(samples):
    rms = math.sqrt(sum(x ** 2 for x in samples) / len(samples))
    pico = max(abs(x) for x in samples)
    std_dev = statistics.stdev(samples) if len(samples) > 1 else 0.0

    trabajo = 0.0
    for _ in range(5000):
        for x in samples:
            trabajo += math.sin(x) ** 2 + math.cos(x) ** 2
            trabajo *= 1.0001

    return {
        "rms": rms,
        "pico": pico,
        "std_dev": std_dev,
        "trabajo": trabajo,
    }


def validar_mensaje(topic, payload):
    if topic not in (TOPIC_AMBIENTE, TOPIC_VIBRACION):
        return False, "Tema no válido"

    node_id = payload.get("node_id")
    if node_id not in ("sim_ambiente_01", "sim_vib_01"):
        return False, f"node_id no válido: {node_id}"

    seq = payload.get("sequence")
    if not isinstance(seq, int):
        return False, "sequence no es entero"

    if topic == TOPIC_AMBIENTE:
        for campo in ["temperature_c", "humidity_pct", "light_pct"]:
            if campo not in payload:
                return False, f"Falta campo {campo}"
    elif topic == TOPIC_VIBRACION:
        if payload.get("sample_rate_hz") != 100:
            return False, "sample_rate_hz debe ser 100"
        samples = payload.get("samples_g")
        if not isinstance(samples, list):
            return False, "samples_g debe ser lista"
        if len(samples) != 100:
            return False, f"samples_g debe tener 100 elementos, tiene {len(samples)}"

    return True, "OK"


def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("[ANALIZADOR] Conectado al broker MQTT.")
        client.subscribe([(TOPIC_AMBIENTE, 0), (TOPIC_VIBRACION, 0)])
    else:
        print(f"[ANALIZADOR][ERROR] Error de conexión MQTT: {rc}")


def on_message(client, userdata, msg):
    global executor, corridas_completadas

    try:
        data = json.loads(msg.payload.decode("utf-8"))
    except json.JSONDecodeError:
        print("[ANALIZADOR][ERROR] JSON inválido.")
        return

    ok, detalle = validar_mensaje(msg.topic, data)
    if not ok:
        print(f"[ANALIZADOR][VALIDACION FALLIDA] {msg.topic} | {detalle}")
        return

    if msg.topic == TOPIC_AMBIENTE:
        print(
            f"\n[AMBIENTE] "
            f"Temp={data.get('temperature_c')} | "
            f"Hum={data.get('humidity_pct')} | "
            f"Luz={data.get('light_pct')}"
        )
        return

    if msg.topic == TOPIC_VIBRACION:
        seq = data.get("sequence")
        if seq in secuencias_recibidas:
            print(f"[ALERTA] Secuencia duplicada: #{seq}")
        secuencias_recibidas.add(seq)

        samples = data.get("samples_g", [])
        t_inicio = time.perf_counter()

        if MODO_PROCESAMIENTO == "SECUENCIAL":
            res = analizar_ventana(samples)
        elif MODO_PROCESAMIENTO == "PARALELO":
            future = executor.submit(analizar_ventana, samples)
            res = future.result()
        else:
            raise ValueError(f"Modo no soportado: {MODO_PROCESAMIENTO}")

        t_fin = time.perf_counter()
        duracion_ms = (t_fin - t_inicio) * 1000
        tiempos_procesamiento.append(duracion_ms)

        run_id = data.get("run_id")
        run_times[run_id].append(duracion_ms)

        print(
            f"[VIB #{seq}] run_id={run_id} "
            f"tiempo={duracion_ms:.3f} ms | "
            f"RMS={res['rms']:.4f} | "
            f"Pico={res['pico']:.4f} | "
            f"Std={res['std_dev']:.4f}"
        )

        if len(run_times[run_id]) == VENTANAS_POR_CORRIDA:
            promedio_corrida = statistics.mean(run_times[run_id])
            print(f"\n=== RESUMEN {run_id} ===")
            print(f"Promedio corrida: {promedio_corrida:.3f} ms")
            print(f"Valores: {run_times[run_id]}")

            corridas_completadas += 1
            print(f"Corridas completadas: {corridas_completadas}/{MAX_CORRIDAS}")

            run_times.pop(run_id, None)

            if corridas_completadas >= MAX_CORRIDAS:
                print("\n=== SE COMPLETARON 5 CORRIDAS ===")
                cpu_promedio = finalizar_medicion_cpu()
                print(f"Ventanas procesadas: {len(tiempos_procesamiento)}")
                print(f"Tiempo medio: {statistics.mean(tiempos_procesamiento):.3f} ms")
                print(f"Tiempo mediano: {statistics.median(tiempos_procesamiento):.3f} ms")
                print(f"CPU del sistema promedio: {cpu_promedio:.2f}%")
                print("Deteniendo la prueba.")
                client.loop_stop()
                client.disconnect()
                return


if __name__ == "__main__":
    iniciar_medicion_cpu()

    if MODO_PROCESAMIENTO == "PARALELO":
        executor = ProcessPoolExecutor(max_workers=NUM_WORKERS)

    cliente = mqtt.Client(
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
        client_id="suscriptor_analizador",
    )
    cliente.on_connect = on_connect
    cliente.on_message = on_message

    try:
        cliente.connect(BROKER_ADDRESS, BROKER_PORT)
    except Exception as exc:
        print(f"[ANALIZADOR][ERROR] No se pudo conectar al broker: {exc}")
        raise SystemExit(1)

    print(f"\n=== Modo de procesamiento: {MODO_PROCESAMIENTO} ===")
    print("Escuchando temas...")

    try:
        cliente.loop_forever()
    except KeyboardInterrupt:
        print("\n[ANALIZADOR] Interrupción por teclado.")
        if executor is not None:
            executor.shutdown(wait=True)
        cliente.disconnect()
