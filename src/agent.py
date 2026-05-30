"""Agente de triaje de incidentes, montado sobre LangChain y Ollama.
---------------------------------------------------------------------- OUSSAMA MARZAK FAROIT - INTELIGENCIA ARTIFICIAL / 2025-2026 ---------------------------------------------------------------
La idea es sencilla: un modelo de texto con tool calling hace de orquestador y, según la evidencia que haya cargada, decide cuál de las tres herramientas llamar. Las imágenes las
atiende un modelo de visión aparte. Todo el historial de la conversación se guarda en lapropia instancia, que es lo que permite responder a preguntas de seguimiento sin volver acargar el documento.
"""

import requests
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

from . import config
from .preprocessing import load_document
from .prompts import IMAGE_PROMPT, LOG_PROMPT, PDF_PROMPT, SYSTEM_PROMPT

# Recortamos el contenido que mandamos al modelo para no desbordar su ventana de contexto
# con documentos largos. Es un límite generoso pero seguro para los modelos pequeños.
MAX_CONTENT_CHARS = 12000

# Pequeña pista que añadimos a cada pregunta para que el orquestador sepa, de un vistazo, qué evidencia hay activa y qué herramienta le corresponde.
ETIQUETAS = {
    "image": "una imagen (usa diagnosticar_captura)",
    "csv": "un CSV de eventos (usa analizar_registro)",
    "text": "un log de texto (usa analizar_registro)",
    "pdf": "un PDF (usa resumir_informe)",
}


def check_ollama(require_models=True):
    """Comprueba que Ollama está en marcha y que los modelos están descargados. Devuelve una tupla para que la interfaz pueda mostrar un aviso claro en lugar de fallar a mitad de una consulta cuando el servidor no responde."""
    try:
        resp = requests.get(f"{config.OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return False, f"No se puede contactar con Ollama en {config.OLLAMA_BASE_URL} ({exc})."

    if not require_models:
        return True, "Servidor de Ollama disponible."

    # Comparamos solo por el nombre base del modelo (lo que va antes de los dos puntos), porque la etiqueta de la versión puede variar entre instalaciones.
    instalados = [m["name"] for m in resp.json().get("models", [])]
    faltan = []
    for modelo in (config.ORCHESTRATOR_MODEL, config.VISION_MODEL):
        base = modelo.split(":")[0] 
        if not any(nombre.startswith(base) for nombre in instalados):
            faltan.append(modelo)
    if faltan:
        return False, "Faltan modelos por descargar: " + ", ".join(faltan) + "."
    return True, "Servidor y modelos de Ollama disponibles."


class TriageAgent:
    """Agente que mantiene una evidencia cargada y responde consultas de triaje sobre ella."""

    def __init__(self):
        self.documento = None
        self.chat_history = []
        self.text_llm = ChatOllama(
            model=config.ORCHESTRATOR_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=config.TEMPERATURE,
        )
        self.vision_llm = ChatOllama(
            model=config.VISION_MODEL,
            base_url=config.OLLAMA_BASE_URL,
            temperature=config.TEMPERATURE,
        )
        self.agent = create_agent(self.text_llm, self._tools(), system_prompt=SYSTEM_PROMPT)

    def cargar_documento(self, path):
        """Carga una evidencia desde disco y devuelve el tipo que se ha detectado."""
        self.documento = load_document(path)
        return self.documento.kind

    def estado_actual(self):
        """Describe en una frase qué evidencia hay cargada ahora mismo."""
        if self.documento is None:
            return "No hay ninguna evidencia cargada."
        return f"Evidencia cargada: {self.documento.kind} ({self.documento.path})."

    def reset(self):
        """Olvida la evidencia y vacía el historial para empezar una conversación nueva."""
        self.documento = None
        self.chat_history = []

    def _tools(self):
        # Las herramientas necesitan llegar al documento que tenga cargado el agente en cada momento, así que las definimos aquí dentro y capturamos la instancia en 'agente'.
        agente = self

        @tool
        def diagnosticar_captura(instruccion=""):
            """Analiza la captura de pantalla cargada y propone un diagnóstico de seguridad."""
            doc = agente.documento
            if doc is None or doc.kind != "image":
                return "No hay ninguna imagen cargada."
            # La imagen viaja incrustada en el mensaje como data URL, que es como el modelo de visión espera recibirla.
            contenido = [
                {"type": "text", "text": IMAGE_PROMPT.format(instruccion=instruccion)},
                {"type": "image_url", "image_url": f"data:{doc.mime};base64,{doc.image_b64}"},
            ]
            return agente.vision_llm.invoke([HumanMessage(content=contenido)]).content

        @tool
        def analizar_registro(instruccion=""):
            """Analiza el log o el CSV cargado y extrae los indicadores de compromiso."""
            doc = agente.documento
            if doc is None or doc.kind not in ("text", "csv"):
                return "No hay ningún registro cargado."
            mensaje = LOG_PROMPT.format(contenido=doc.text[:MAX_CONTENT_CHARS], instruccion=instruccion)
            return agente.text_llm.invoke(mensaje).content

        @tool
        def resumir_informe(instruccion=""):
            """Resume el informe de vulnerabilidades en PDF que esté cargado."""
            doc = agente.documento
            if doc is None or doc.kind != "pdf":
                return "No hay ningún PDF cargado."
            mensaje = PDF_PROMPT.format(contenido=doc.text[:MAX_CONTENT_CHARS], instruccion=instruccion)
            return agente.text_llm.invoke(mensaje).content

        return [diagnosticar_captura, analizar_registro, resumir_informe]

    def preguntar(self, texto):
        """Responde una consulta del analista sin perder el contexto de la conversación.

        Antes de pasar la pregunta al agente le anteponemos una etiqueta con la evidencia
        activa, para que el orquestador elija la herramienta correcta o, si no hay nada
        cargado, lo pida. La respuesta se acumula en el historial para los seguimientos.
        """
        if self.documento is None:
            etiqueta = "[Evidencia activa: ninguna, no hay documento cargado]"
        else:
            etiqueta = f"[Evidencia activa: {ETIQUETAS.get(self.documento.kind, self.documento.kind)}]"
        self.chat_history.append(HumanMessage(content=f"{etiqueta}\n{texto}"))
        resultado = self.agent.invoke({"messages": self.chat_history})
        self.chat_history = resultado["messages"]
        return self.chat_history[-1].content
