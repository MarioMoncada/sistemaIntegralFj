"""
Punto de entrada del sistema integral de Software FJ.

Ejecucion:
    python main.py            -> abre la interfaz grafica (tkinter)
    python main.py --consola  -> solo corre la simulacion por consola
    python simulacion.py      -> equivalente a --consola
"""
import sys

from gestion.sistema import SistemaFJ
from utilidades.registro import iniciar_sesion_log, registrar_error, registrar_evento


def ejecutar_consola():
    from simulacion import ejecutar_simulacion

    _, reporte = ejecutar_simulacion(SistemaFJ())
    print(reporte)


def ejecutar_interfaz():
    import tkinter as tk
    from tkinter import messagebox

    from interfaz.ventana import VentanaPrincipal

    sistema = SistemaFJ()
    ventana = VentanaPrincipal(sistema)
    try:
        ventana.mainloop()
    except Exception as exc:  # ultima red de seguridad del programa
        registrar_error("Fallo critico en el bucle de la interfaz", exc)
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror("Error critico", f"La aplicacion encontro un error: {exc}")
        raiz.destroy()
    finally:
        registrar_evento("Cierre de la aplicacion")


def main():
    iniciar_sesion_log()
    if "--consola" in sys.argv:
        ejecutar_consola()
        return
    try:
        ejecutar_interfaz()
    except ImportError as exc:
        # si el entorno no tiene tkinter, el sistema sigue siendo utilizable
        registrar_error("tkinter no esta disponible, se usa la consola", exc)
        print("No fue posible abrir la interfaz grafica. Ejecutando en consola...\n")
        ejecutar_consola()


if __name__ == "__main__":
    main()
