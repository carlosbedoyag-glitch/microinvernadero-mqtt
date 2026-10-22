# Microinvernadero MQTT

Proyecto para simular sensores de ambiente y vibración en un microinvernadero, publicar los datos mediante MQTT y evaluar el rendimiento del procesamiento en modos secuencial y paralelo.

## Descripción

Este proyecto está compuesto por tres módulos principales:

- `sim_ambiente_01.py`: publica datos de temperatura, humedad y luz.
- `sim_vib_01.py`: genera ventanas de vibración con 100 muestras cada una.
- `suscriptor_analizador.py`: recibe y valida los mensajes, analiza la vibración y calcula métricas de rendimiento.

La idea principal es comparar el comportamiento del sistema al procesar la misma carga bajo dos estrategias:

- procesamiento secuencial
- procesamiento paralelo con `ProcessPoolExecutor`

## Arquitectura

```text
+---------------------+        MQTT        +----------------------+
| sim_ambiente_01     | -----------------> | Broker Mosquitto     |
| (sensor ambiente)    |                    | localhost:1883       |
+---------------------+                    +----------------------+
          |                                               |
          | publish                                       | subscribe
          v                                               v
+---------------------+                    +---------------------------+
| sim_vib_01          | -----------------> | suscriptor_analizador      |
| (sensor vibración)   |                    | (valida, procesa y mide)  |
+---------------------+                    +---------------------------+
```

## Tópicos MQTT

### Ambiente
`emergentes/microinvernadero/ambiente/sim_ambiente_01`

### Vibración
`emergentes/microinvernadero/vibracion/sim_vib_01`

## Requisitos

- Python 3.10+
- Mosquitto
- `paho-mqtt`
- `psutil`

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate
# En Windows PowerShell:
# .\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

## Iniciar el broker

```bash
mosquitto -v
```

Si el broker no está en el PATH, abre la carpeta de instalación de Mosquitto y ejecuta el binario manualmente.

## Ejecutar el sistema

1. Inicia Mosquitto.
2. Ejecuta el simulador de ambiente:

```bash
python sim_ambiente_01.py
```

3. Ejecuta el simulador de vibración:

```bash
python sim_vib_01.py
```

4. Ejecuta el analizador:

```bash
python suscriptor_analizador.py
```

## Configuración del modo de procesamiento

En `suscriptor_analizador.py` puedes cambiar el modo de ejecución:

```python
MODO_PROCESAMIENTO = "SECUENCIAL"
# o
MODO_PROCESAMIENTO = "PARALELO"
```

Parámetros relevantes:

```python
NUM_WORKERS = 4
MAX_CORRIDAS = 5
VENTANAS_POR_CORRIDA = 10
```

## Métricas calculadas

Por cada ventana se evalúan:

- RMS
- valor pico máximo
- desviación estándar

Por cada corrida (10 ventanas):

- promedio de tiempo
- lista de tiempos individuales

Al finalizar la prueba se calculan:

- tiempo medio total
- mediana total
- CPU promedio del sistema

## Estructura del proyecto

```text
microinvernadero-mqtt/
├── .gitignore
├── README.md
├── requirements.txt
├── sim_ambiente_01.py
├── sim_vib_01.py
├── suscriptor_analizador.py
└── .venv/
```

## Observación importante

Este benchmark demuestra que, con tareas pequeñas y con overhead de coordinación, el modo paralelo no siempre mejora el rendimiento. En este proyecto, el costo de crear procesos, serializar datos y sincronizar resultados puede compensar el beneficio de distribuir el trabajo. Por ello, comparar ambos enfoques resulta clave para seleccionar la estrategia más adecuada.

## Licencia

Este proyecto se distribuye bajo la licencia MIT.
