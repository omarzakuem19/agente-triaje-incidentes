# Agente multimodal de triaje de incidentes de seguridad

Práctica 2 de Inteligencia Artificial. Es un agente que funciona en local con Ollama y
LangChain. Le pasas una evidencia de un incidente (una captura de pantalla, un registro
de eventos o un informe en PDF) y te devuelve un informe de triaje. Además puedes hacerle
preguntas de seguimiento sobre la misma evidencia.

## Qué hace

Cubre tres escenarios:

1. Diagnóstico de una captura de pantalla de una alerta (imagen).
2. Análisis de un registro de eventos y extracción de indicadores de compromiso (CSV o log).
3. Resumen de un informe de vulnerabilidades (PDF).

Por debajo usa dos modelos. qwen2.5:3b hace de orquestador, decide qué herramienta usar y
admite tool calling, y llava:7b se encarga de mirar las imágenes.

## Requisitos

- Python 3.12
- Ollama instalado y en marcha

## Puesta en marcha

Creas el entorno e instalas las dependencias:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Descargas los modelos (la primera vez tarda un rato):

```bash
ollama pull qwen2.5:3b
ollama pull llava:7b
```

## Cómo ejecutarlo

La interfaz con Streamlit, que es la que uso para la demo:

```bash
streamlit run src/app.py
```

También hay una versión por terminal:

```bash
python -m src.cli --check
python -m src.cli --file ruta/a/tu/evidencia.pdf
```

En la terminal, con cargar y la ruta de un archivo cambias de evidencia, y con salir cierras.

## Configuración

Si quieres cambiar los modelos o la dirección de Ollama, lo puedes hacer con variables de
entorno sin tocar el código (están en src/config.py): OLLAMA_BASE_URL, ORCHESTRATOR_MODEL,
VISION_MODEL y AGENT_TEMPERATURE.
