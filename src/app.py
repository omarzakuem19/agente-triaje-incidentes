"""Interfaz gráfica del agente con Streamlit. le da al agente una estética de consola de triaje de seguridad: tema oscuro, acento rojo y tipografía más interesante"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st

from src.agent import TriageAgent, check_ollama
from src.preprocessing import IMAGE_EXTS

st.set_page_config(
    page_title="Triaje de incidentes de seguridad",
    layout="wide",
)

# Hoja de estilo con todo el aspecto visual: tipografía, fondo, cabecera, barra lateral
# y burbujas de chat. Se inyecta una sola vez al arrancar la aplicación.
ESTILO = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="st-"], button, input, textarea {
    font-family: 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif;
}
/* La regla anterior no debe pisar la fuente de iconos de Streamlit, o sus
   ligaduras (keyboard_double_arrow_left, upload...) se quedan como texto. */
[data-testid="stIconMaterial"] { font-family: 'Material Symbols Rounded' !important; }

/* Fondo general con un degradado muy sutil. */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1200px 600px at 80% -10%, rgba(225,29,42,0.08), transparent 60%),
        #0A0C10;
}
[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"] { padding-top: 1.2rem; max-width: 1100px; }

/* Cabecera de la aplicacion. */
.app-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.9rem 1.2rem; margin-bottom: 1.1rem;
    border: 1px solid #1E2532; border-radius: 0.7rem;
    background: linear-gradient(180deg, rgba(20,25,36,0.9), rgba(13,16,23,0.9));
}
.app-brand { display: flex; align-items: center; gap: 0.8rem; }
.app-title { font-size: 1.18rem; font-weight: 700; letter-spacing: 0.02em; line-height: 1.1; }
.app-sub { font-size: 0.78rem; color: #8A93A6; letter-spacing: 0.16em; text-transform: uppercase; }

/* Pildora de estado del servidor. */
.pill {
    display: inline-flex; align-items: center; gap: 0.5rem;
    padding: 0.4rem 0.8rem; border-radius: 999px;
    font-size: 0.78rem; font-weight: 600; letter-spacing: 0.04em;
    border: 1px solid #232b3a; background: #0E1219;
}
.pill .dot { width: 8px; height: 8px; border-radius: 50%; }
.pill.ok { color: #34D399; } .pill.ok .dot { background: #34D399; box-shadow: 0 0 8px #34D399; }
.pill.ko { color: #F87171; } .pill.ko .dot { background: #F87171; box-shadow: 0 0 8px #F87171; }

/* Barra lateral. */
[data-testid="stSidebar"] {
    background: #0C0F16; border-right: 1px solid #1A2130;
}
.side-label {
    font-size: 0.72rem; font-weight: 700; letter-spacing: 0.18em;
    text-transform: uppercase; color: #6E7888; margin: 0.2rem 0 0.6rem;
}
.ev-card {
    border: 1px solid #1E2532; border-radius: 0.55rem; background: #0E121A;
    padding: 0.7rem 0.85rem; font-size: 0.84rem; color: #C4CBD8;
    display: flex; align-items: center; gap: 0.6rem;
}
.ev-card .dot { width: 9px; height: 9px; border-radius: 50%; flex: none; }
.ev-on .dot { background: #34D399; box-shadow: 0 0 7px #34D399; }
.ev-off .dot { background: #4B5566; }

/* Leyenda de severidad. */
.sev-row { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.sev {
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.03em;
    padding: 0.2rem 0.55rem; border-radius: 999px; border: 1px solid transparent;
}
.sev.c { color: #F87171; background: rgba(248,113,113,0.12); border-color: rgba(248,113,113,0.35); }
.sev.a { color: #FB923C; background: rgba(251,146,60,0.12); border-color: rgba(251,146,60,0.35); }
.sev.m { color: #FACC15; background: rgba(250,204,21,0.12); border-color: rgba(250,204,21,0.35); }
.sev.b { color: #34D399; background: rgba(52,211,153,0.12); border-color: rgba(52,211,153,0.35); }

/* Burbujas de chat. */
[data-testid="stChatMessage"] {
    background: #0F131C; border: 1px solid #1C2331; border-radius: 0.7rem;
    padding: 0.4rem 0.6rem;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
    border-left: 3px solid #E11D2A;
}
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    border-left: 3px solid #3B82F6; background: #0C1019;
}
[data-testid="stChatMessageAvatarAssistant"] { background: #E11D2A !important; color: #fff !important; }
[data-testid="stChatMessageAvatarUser"] { background: #1E293B !important; }

/* Estado vacio. */
.empty {
    text-align: center; color: #7E889A; padding: 2.4rem 1rem;
    border: 1px dashed #232b3a; border-radius: 0.8rem; background: rgba(14,18,25,0.5);
}
.empty h3 { color: #C4CBD8; font-weight: 600; margin-bottom: 0.4rem; }
.empty .modes { margin-top: 0.9rem; display: flex; gap: 0.5rem; justify-content: center; flex-wrap: wrap; }
.empty .mode {
    font-size: 0.78rem; color: #AEB6C4; padding: 0.35rem 0.7rem;
    border: 1px solid #232b3a; border-radius: 0.5rem; background: #0E121A;
}

/* Boton primario a rojo solido. */
[data-testid="stBaseButton-primary"] {
    background: #E11D2A; border: 1px solid #E11D2A;
}
[data-testid="stBaseButton-primary"]:hover { background: #C2161F; border-color: #C2161F; }

/* Zona de subida de archivos. */
[data-testid="stFileUploaderDropzone"] {
    background: #0E121A; border: 1px dashed #2A3344; border-radius: 0.55rem;
    padding: 1rem 0.9rem;
}
[data-testid="stFileUploaderDropzoneInstructions"] span { font-size: 0.82rem; color: #C4CBD8; }
[data-testid="stFileUploaderDropzoneInstructions"] small { color: #6E7888; }
/* Oculta el icono Material del uploader: si la fuente de iconos no carga, su
   ligadura "upload" se queda como texto y se solapa con la etiqueta del botón. */
[data-testid="stFileUploaderDropzone"] [data-testid="stIconMaterial"] { display: none; }
[data-testid="stFileUploaderDropzone"] button {
    border: 1px solid #2A3344; background: #161B26; color: #C4CBD8;
    padding: 0.35rem 1rem;
}
[data-testid="stFileUploaderDropzone"] button:hover {
    border-color: #E11D2A; color: #fff;
}

/* Ocultamos la barra de herramientas (botón Deploy, menú), pero dejamos visible el
   botón de reabrir la barra lateral, que por desgracia vive dentro de ella. */
footer, [data-testid="stToolbar"] { visibility: hidden; }
[data-testid="stExpandSidebarButton"] { visibility: visible; }
</style>
"""

def cabecera(ok, mensaje):
    """Dibuja la barra superior con el título y la pastilla de estado del servidor. La pastilla cambia de color y de texto según Ollama esté disponible o no, para que sevea de un vistazo si la aplicación puede funcuionar."""
    clase = "ok" if ok else "ko"
    etiqueta = "Ollama disponible" if ok else "Ollama no disponible"
    st.markdown(
        f"""
        <div class="app-header">
          <div class="app-brand">
            <div>
              <div class="app-title">Triaje de incidentes de seguridad</div>
              <div class="app-sub">Asistente local con Ollama y LangChain</div>
            </div>
          </div>
          <div class="pill {clase}"><span class="dot"></span>{etiqueta}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not ok:
        st.error(mensaje)


def tarjeta_evidencia(agente):
    """Muestra en la barra lateral qué evidencia hay activa, con un indicador de color."""
    if agente.documento is None:
        st.markdown(
            '<div class="ev-card ev-off"><span class="dot"></span>'
            "Sin evidencia cargada</div>",
            unsafe_allow_html=True,
        )
    else:
        nombre = Path(agente.documento.path).name
        st.markdown(
            f'<div class="ev-card ev-on"><span class="dot"></span>'
            f"<b>{agente.documento.kind.upper()}</b>&nbsp;·&nbsp;{nombre}</div>",
            unsafe_allow_html=True,
        )


def guardar_temporal(archivo):
    """Vuelca el archivo que sbe el usuario a un fichero temporal y devuelve su ruta.

    El agente trabaja con rutas de disco, mientras que Streamlit entrega el archivo en memoria, así que necesitamos este paso intermedio para enlazar los dos.
    """
    sufijo = Path(archivo.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as tmp:
        tmp.write(archivo.getbuffer())
        return tmp.name


def main():
    st.markdown(ESTILO, unsafe_allow_html=True)

    ok, mensaje = check_ollama()
    cabecera(ok, mensaje)
    if not ok:
        st.stop()

    if "agente" not in st.session_state:
        st.session_state.agente = TriageAgent()
        st.session_state.mensajes = []
    agente = st.session_state.agente

    with st.sidebar:
        st.markdown('<div class="side-label">Evidencia</div>', unsafe_allow_html=True)
        archivo = st.file_uploader(
            "Captura, PDF, CSV o log",
            type=["png", "jpg", "jpeg", "pdf", "csv", "log", "txt", "json"],
            label_visibility="collapsed",
        )
        if archivo is not None and st.button("Cargar evidencia", type="primary", use_container_width=True):
            tipo = agente.cargar_documento(guardar_temporal(archivo))
            st.session_state.ultimo_archivo = archivo
            st.toast(f"Evidencia cargada como '{tipo}'.")

        tarjeta_evidencia(agente)

        ultimo = st.session_state.get("ultimo_archivo")
        if ultimo is not None and Path(ultimo.name).suffix.lower() in IMAGE_EXTS:
            st.image(ultimo, use_container_width=True)

        if st.button("Reiniciar conversación", use_container_width=True):
            agente.reset()
            st.session_state.mensajes = []
            st.session_state.pop("ultimo_archivo", None)
            st.rerun()

        st.markdown('<div class="side-label" style="margin-top:1.2rem">Severidad</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="sev-row">'
            '<span class="sev c">Crítica</span><span class="sev a">Alta</span>'
            '<span class="sev m">Media</span><span class="sev b">Baja</span></div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="app-sub" style="margin-top:1.4rem">Local · Ollama · LangChain</div>',
            unsafe_allow_html=True,
        )

    if not st.session_state.mensajes:
        st.markdown(
            '<div class="empty"><h3>Listo para el triaje</h3>'
            "Carga una evidencia en el panel izquierdo y formula tu consulta."
            '<div class="modes"><span class="mode">Diagnóstico de captura</span>'
            '<span class="mode">Análisis de registro</span>'
            '<span class="mode">Resumen de informe</span></div></div>',
            unsafe_allow_html=True,
        )

    for rol, contenido in st.session_state.mensajes:
        with st.chat_message(rol):
            st.markdown(contenido)

    if consulta := st.chat_input("Escribe tu consulta de triaje"):
        st.session_state.mensajes.append(("user", consulta))
        with st.chat_message("user"):
            st.markdown(consulta)
        with st.chat_message("assistant"):
            with st.spinner("Analizando evidencia..."):
                respuesta = agente.preguntar(consulta)
            st.markdown(respuesta)
        st.session_state.mensajes.append(("assistant", respuesta))
        # Volvemos a ejecutar para que la conversación se pinte limpia desde el historial
        # y desaparezca el mensaje de bienvenida en cuanto hay un intercambio.
        st.rerun()


if __name__ == "__main__":
    main()
