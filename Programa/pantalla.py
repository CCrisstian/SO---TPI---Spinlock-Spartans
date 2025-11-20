from importaciones import os, time, Panel, Text, Group, sys
from varGlobal import console

# Distintas funciones que manejan la limpieza de consola, pausas y la pantalla de inicio.

def limpiar_pantalla(): # Ejecuta el comando de limpieza correspondiente segun el sistema operativo del usuario.
    os.system('cls' if os.name == 'nt' else 'clear')

def pausar_y_limpiar(mensaje=str):                  # Funcion con parametros para mostrar un mensaje esperando
    console.print(f"\n[italic]{mensaje}[/italic]")  # que el usuario interactue, para luego limpiar la pantalla
    input()
    limpiar_pantalla()

def mostrar_logo(archivo_logo: str):    # Muestra por pantalla un logo personalizado que se abre desde un archivo .txt
    limpiar_pantalla()                  # Meticulosamente hecho por el SPARTAN B-312 Franco Yaya

    try:
        with open(archivo_logo, 'r', encoding='utf-8') as f:        # Carga del archivo que contiene el arte ASCII de inicio
            lineas = f.readlines()

        for linea in lineas:            # Muestra el contenido del archivo linea por linea
            console.print(linea.rstrip('\n'), style="bold green", justify="center")
            time.sleep(0.05)
        
        console.print("\n")

    except FileNotFoundError:   #Si el archivo .txt no se encuentra, o no puede abrirse, muestra el error correspondiente
        console.print(f"[bold yellow]ADVERTENCIA:[/bold yellow] No se encontró el archivo de texto: '{archivo_logo}'.")
        console.print("Por favor compruebe que el archivo 'Splashcreen.txt' esté en la misma carpeta que el programa.")
        time.sleep(3)
    except Exception as e:
        console.print(f"[bold red]ERROR AL LEER EL ARCHIVO DE TEXTO[/bold red] {e}")
        time.sleep(3)

def pantallaInicial():                      # Pantalla inicial del programa.
    limpiar_pantalla()
    if getattr(sys, 'frozen', False):       # Si se ejecuta desde el binario, usamos la ruta del mismo
        directorio_actual = os.path.dirname(sys.executable)
    else:                                   # Si se ejecuta desde Python, usamos __file__
        directorio_actual = os.path.dirname(os.path.abspath(__file__))

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