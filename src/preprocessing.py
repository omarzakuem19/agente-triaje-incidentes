"""Carga de los documentos de entrada (imagen, PDF, CSV o log).

Cada tipo de archivo se lee con la librería que mejor le va, pero todos acaban en el mismo objeto LoadedDocument para que el resto del programa los trate igual. Las
imágenes se guardan en base64, que es lo que espera el modelo y el resto de documentos se quedan como texto plano. """

import base64
import io
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp"}
PDF_EXTS = {".pdf"}
CSV_EXTS = {".csv"}
TEXT_EXTS = {".log", ".txt", ".json", ".md"}


@dataclass
class LoadedDocument:
    """Un documento ya cargado en memoria. Guarda el tipo, la ruta de origen y el contenido. Si es una imagen, el contenido viaja en los campos image_b64 y mime, en los demás casos, en el campo text."""

    kind: str
    path: str
    text: str = ""
    image_b64: str = None
    mime: str = None


def detect_kind(filename):
    """Decide el tipo de documento mirando la extensión del archivo."""
    ext = Path(filename).suffix.lower()
    if ext in IMAGE_EXTS:
        return "image"
    if ext in PDF_EXTS:
        return "pdf"
    if ext in CSV_EXTS:
        return "csv"
    if ext in TEXT_EXTS:
        return "text"
    raise ValueError(f"Extensión no soportada: {ext}")


def encode_image(data, ext):
    """Codifica una imagen en base64 y devuelve el par (base64, tipo MIME).

    El modelo de visión recibe la imagen incrustada en el propio mensaje, así que ecesitamos tanto los bytes codificados como el MIME para construir el data URL.
    """
    ext = ext.lower()
    mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else f"image/{ext.lstrip('.')}"
    return base64.b64encode(data).decode("utf-8"), mime


def pdf_to_text(data):
    """Extrae todo el texto de un PDF que tenemos en memoria, usando PyMuPDF."""
    import fitz

    texto = ""
    with fitz.open(stream=data, filetype="pdf") as doc:
        for pagina in doc:
            texto += pagina.get_text()
    return texto.strip()


def csv_to_text(data, max_rows=50):
    """Convierte un CSV en un resumen de texto que el modelo pueda leer cómodamente.

    En lugar de volcar el archivo entero, le damos las dimensiones, los nombres de la columnas y solo las primeras filas, que es suficiente para el triaje y evita
    saturar el contexto del modelo con tablas enomes."""
    df = pd.read_csv(io.BytesIO(data))
    partes = [
        f"El conjunto tiene {len(df)} filas y {len(df.columns)} columnas.",
        f"Columnas: {', '.join(map(str, df.columns))}.",
        "Primeras filas:",
        df.head(max_rows).to_string(index=False),
    ]
    return "\n".join(partes)


def load_document(path):
    """Lee un archivo del disco y lo deja convertido en un LoadedDocument.
    Es el único punto de entrada del módulo: detecta el tipo, lo procesa con la función correspodiente y devuelve el objeto común con el que trabaja el agente."""
    ruta = Path(path)
    if not ruta.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    kind = detect_kind(ruta.name)
    data = ruta.read_bytes()

    if kind == "image":
        b64, mime = encode_image(data, ruta.suffix)
        return LoadedDocument(kind, str(ruta), image_b64=b64, mime=mime)
    if kind == "pdf":
        return LoadedDocument(kind, str(ruta), text=pdf_to_text(data))
    if kind == "csv":
        return LoadedDocument(kind, str(ruta), text=csv_to_text(data))
    return LoadedDocument(kind, str(ruta), text=data.decode("utf-8", errors="replace").strip())
