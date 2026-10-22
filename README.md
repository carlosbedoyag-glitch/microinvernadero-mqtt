# Microinvernadero MQTT

Proyecto para simular sensores de ambiente y vibración en un microinvernadero, publicar los datos con MQTT y analizar el comportamiento del procesamiento en modos secuencial y paralelo.

## Descripción

Este proyecto tiene tres componentes principales:

- `sim_ambiente_01.py`: publica datos de temperatura, humedad y luz.
- `sim_vib_01.py`: genera ventanas de vibración con 100 muestras cada una.
- `suscriptor_analizador.py`: recibe y valida los mensajes, analiza la vibración y calcula métricas de rendimiento.

La idea es comparar cómo se comporta el sistema al procesar la misma carga con:

- procesamiento secuencial
- procesamiento paralelo usando `ProcessPoolExecutor`

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
source .venv/bin/activate    # Linux/macOS
# o en Windows:
# .venv\Scripts\activate

pip install -r requirements.txt
```

## Iniciar el broker

### Linux / macOS

```bash
mosquitto -v
```

### Windows

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

## Configuración del modo

En `suscriptor_analizador.py` puedes cambiar el modo de procesamiento:

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

Por cada ventana se calcula:

- RMS
- valor pico máximo
- desviación estándar

Por cada corrida (10 ventanas):

- promedio de tiempo
- lista de tiempos individuales

Al finalizar la prueba:

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

Este benchmark demuestra que, con tareas pequeñas y con overhead de coordinación, el modo paralelo no siempre mejora el rendimiento. En este proyecto, el costo de crear procesos, serializar datos y sincronizar resultados puede superar el beneficio computacional real.

## Licencia

Este proyecto se distribuye bajo la licencia MIT.
