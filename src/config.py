"""Configuración del agente: modelos, servidor de Ollama y temperatura.

Todos los valores se pueden ajustar con variables de entorno así que no hace falta tocar el código para cambiar de modelo.
"""

import os

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

ORCHESTRATOR_MODEL = os.getenv("ORCHESTRATOR_MODEL", "qwen2.5:3b") # Modelo de texto que dirige el agente. Tiene que admitir tool calling, porque es quien decide qué herramienta llamar en cada momento.



VISION_MODEL = os.getenv("VISION_MODEL", "llava:7b") # Modelo de visión que se encarga de interpretar las capturas de pantalla.


TEMPERATURE = float(os.getenv("AGENT_TEMPERATURE", "0.1"))# Mantenemos la temperatura baja para que el triaje sea estable y repetible.
