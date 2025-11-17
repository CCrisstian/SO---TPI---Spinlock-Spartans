from importaciones import os, time, Panel, Text, Group
from varGlobal import console

#FUNCIONES PARA LIMPIAR PANTALLA
def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def pausar_y_limpiar(mensaje=str):
    console.print(f"\n[italic]{mensaje}[/italic]")
    input()
    limpiar_pantalla()

def mostrar_logo(archivo_logo: str):    #Muestra por pantalla un logo personalizado que se abre desde un archivo .txt
    limpiar_pantalla()                  #Meticulosamente hecho por el Spartan B-312 Franco Yaya
    try:
        with open(archivo_logo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()

        for linea in lineas:
            console.print(linea.rstrip('\n'), style="bold green", justify="center")
            time.sleep(0.05)
        
        console.print("\n")

    except FileNotFoundError:   #Si el archivo .txt no se encuentra, maneja el error
        console.print(f"[bold yellow]Advertencia:[/bold yellow] No se encontró el archivo de texto: '{archivo_logo}'.")
        console.print("Asegúrate de que 'Splashcreen.txt' esté en la misma carpeta que el script.")
        time.sleep(3)
    except Exception as e:
        console.print(f"[bold red]Error al leer el archivo de texto[/bold red] {e}")
        time.sleep(3)

def pantallaInicial(): 
    limpiar_pantalla()
    mostrar_logo("Programa/Splashcreen.txt")
    time.sleep(0.5)

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