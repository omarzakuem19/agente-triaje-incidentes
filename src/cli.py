"""comprobar que Ollama responde y para cargar una evidencia y hacerle preguntas desde la terminal. 
    
Para hacer check:    python -m src.cli --check && python -m src.cli --file data/ejemplos/escenario2_eventos.csv
"""

import argparse
import sys

from .agent import TriageAgent, check_ollama


def main():
    parser = argparse.ArgumentParser(description="Agente de triaje de incidentes.")
    parser.add_argument("--file", help="Ruta de la evidencia a cargar.")
    parser.add_argument("--check", action="store_true", help="Solo comprueba Ollama y termina.")
    args = parser.parse_args()

    # Antes de nada nos aseguramos de que Ollama y los modelos están disponibles, pq sin ellos no se puede hacer nada.
    ok, mensaje = check_ollama()
    print(mensaje)
    if args.check:
        return 0 if ok else 1
    if not ok:
        return 1

    agente = TriageAgent()
    if args.file:
        tipo = agente.cargar_documento(args.file)
        print(f"Evidencia cargada ({tipo}): {args.file}")

    print("Escribe tu consulta. 'cargar <ruta>' cambia de evidencia y 'salir' termina.")
    while True:
        try:
            texto = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            # Salida limpia si el usuario pulsa Ctrl+D o Ctrl+C.
            print()
            break
        if not texto:
            continue 
        if texto.lower() in {"salir", "exit", "quit"}:
            break
        if texto.lower().startswith("cargar "):
            ruta = texto[7:].strip()
            try:
                tipo = agente.cargar_documento(ruta)
                print(f"Evidencia cargada ({tipo}): {ruta}")
            except (FileNotFoundError, ValueError) as exc:
                print(f"Error al cargar: {exc}")
            continue
        print("\n" + agente.preguntar(texto))

    return 0


if __name__ == "__main__":
    sys.exit(main())
