from importaciones import os, time, Panel, Text, Group, sys
from varGlobal import console

# --- FUNCIONES DE UTILIDAD E INTERFAZ ---
# Manejan la limpieza de consola, pausas y la presentación inicial (Splash Screen).

def limpiar_pantalla():
    """ Detecta el sistema operativo y ejecuta el comando de limpieza correspondiente. """
    os.system('cls' if os.name == 'nt' else 'clear')

def pausar_y_limpiar(mensaje=str):
    """ Pausa la ejecución esperando un Enter del usuario y luego limpia. """
    console.print(f"\n[italic]{mensaje}[/italic]")
    input()
    limpiar_pantalla()

def mostrar_logo(archivo_logo: str):    # Muestra por pantalla un logo personalizado que se abre desde un archivo .txt
    limpiar_pantalla()                  # Meticulosamente hecho por el Spartan B-312 Franco Yaya

    """
    Acá se lee un archivo .txt (arte ASCII) y lo imprime línea por línea 
    con un efecto de retardo para simular carga.
    """

    try:
        with open(archivo_logo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        for linea in lineas:
            console.print(linea.rstrip('\n'), style="bold green", justify="center")
            time.sleep(0.05) # Efecto de 'loading'
        
        console.print("\n")

    except FileNotFoundError:   #Si el archivo .txt no se encuentra, maneja el error
        console.print(f"[bold yellow]Advertencia:[/bold yellow] No se encontró el archivo de texto: '{archivo_logo}'.")
        console.print("Asegúrate de que 'Splashcreen.txt' esté en la misma carpeta que el script.")
        time.sleep(3)
    except Exception as e:
        console.print(f"[bold red]Error al leer el archivo de texto[/bold red] {e}")
        time.sleep(3)

def pantallaInicial():
    """
    Renderiza la carátula del proyecto, cargando el logo y mostrando
    el panel con los nombres de los integrantes.
    """ 
    limpiar_pantalla()
    
    # --- BLOQUE CORREGIDO PARA EXE ---
    if getattr(sys, 'frozen', False):
        # Si estamos en el .EXE, usamos la ruta del ejecutable
        directorio_actual = os.path.dirname(sys.executable)
    else:
        # Si estamos en Python normal, usamos __file__
        directorio_actual = os.path.dirname(os.path.abspath(__file__))
    # ---------------------------------

    ruta_splash = os.path.join(directorio_actual, "Splashcreen.txt")
    mostrar_logo(ruta_splash)

    integrantes = (
        "\nBLANCO, FACUNDO\n"
        "CLAVER GALLINO, SAMIRA\n"
        "CRISTALDO, CRISTIAN ALEJANDRO\n"
        "ECHEVERRIA MELGRATTI, LAUTARO\n"
        "YAYA, FRANCO GABRIEL\n"
    )

    contenido_panel = Group(Text(integrantes, style="white", justify="center"))
    console.print(
        Panel(
            contenido_panel,
            title="PROYECTO DE SIMULACIÓN",
            border_style="green"
        )
    )
    pausar_y_limpiar("Presiona Enter para cargar los procesos...")