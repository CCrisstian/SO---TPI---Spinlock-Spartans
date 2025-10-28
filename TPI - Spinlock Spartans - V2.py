import pandas as pd
import os
import sys
import time
from rich.console import Console, Group
from rich.table import Table
from rich.panel import Panel
from rich import box
from rich.text import Text
from rich.columns import Columns
from typing import List

# --- 0. Configuración inicial ---
console = Console()
MAX_MEMORIA = 250 # Límite de memoria

# --- 1. Funciones de Transición ---

def limpiar_pantalla():
    """Limpia la consola (multiplataforma)."""
    os.system('cls' if os.name == 'nt' else 'clear')

def pausar_y_limpiar(mensaje="Presiona Enter para continuar..."):
    """
    Muestra un mensaje, espera que el usuario presione Enter
    y luego limpia la pantalla.
    """
    console.print(f"\n[dim italic]{mensaje}[/dim italic]")
    input() # Espera que el usuario presione Enter
    limpiar_pantalla()


# --- 2. Definición de Clases ---
class Proceso:
    # El estado se inicializa como "Nuevo"
    def __init__(self, idProceso, tamProceso, TA, TI, estado="Nuevo"):
      self.idProceso = idProceso
      self.tamProceso = tamProceso
      self.estado = estado # <-- valor por defecto
      self.TA = TA
      self.TI = TI
    
    def __repr__(self):
        return (f"Proceso(ID={self.idProceso}, Tam={self.tamProceso}K, "
                f"Estado='{self.estado}', TA={self.TA}, TI={self.TI})")


# --- 3. Funciones de Creación de Tablas ---

def crear_tabla_procesos_df(df_procs, titulo_tabla, estilo_header):
    tabla = Table(
        title=titulo_tabla,
        box=box.ROUNDED,
        show_header=True,
        header_style=estilo_header
    )
    
    for columna in df_procs.columns:
        tabla.add_column(columna, justify="center")

    for index, row in df_procs.iterrows():
        tabla.add_row(
            str(row['ID']),
            f"{row['Tamaño']}K",
            str(row['Arribo']),
            str(row['Irrupcion'])
        )
    return tabla

def mostrar_cola_de_trabajo(cola_de_trabajo: List[Proceso]):
    tabla = Table(
        title="Cola de Trabajo",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )

    tabla.add_column("ID", justify="center")
    tabla.add_column("Tamaño", justify="center")
    tabla.add_column("Arribo", justify="center")
    tabla.add_column("Irrupción", justify="center")
    tabla.add_column("Estado", justify="center", style="yellow")

    # Iteramos sobre la lista de OBJETOS Proceso
    for proc in cola_de_trabajo:
        tabla.add_row(
            str(proc.idProceso),
            f"{proc.tamProceso}K",
            str(proc.TA),
            str(proc.TI),
            proc.estado
        )
    
    console.print(tabla)
    
# --- FUNCIÓN PRINCIPAL ---
def main():
    # --- PANTALLA 1: Presentación ---
    limpiar_pantalla() 
    integrantes_str = (
        "\nIntegrantes:\n"
        "  Blanco, Facundo\n"
        "  Claver Gallino, Samira\n"
        "  Cristaldo, Cristian Alejandro\n"
        "  Echeverria Melgratti, Lautaro\n"
        "  Yaya, Franco Gabriel"
    )
    text_integrantes = Text(integrantes_str, style="white", justify="left")
    contenido_panel = Group(text_integrantes)
    console.print(
        Panel(
            contenido_panel,
            title="Proyecto de Simulación - Grupo Spinlock Spartans",
            border_style="green"
        )
    )
    
    # --- TRANSICIÓN 1 ---
    pausar_y_limpiar("Presiona Enter para cargar los procesos...")

    # --- PANTALLA 2: Procesos Leídos ---
    
    # Leer el archivo CSV
    archivo_CSV = r"C:\Users\criss\Downloads\procesos.csv"
    try:
        df_procesos = pd.read_csv(archivo_CSV)
    except FileNotFoundError:
        console.print(f"\n[bold red]¡ERROR![/bold red] No se pudo encontrar el archivo: '{archivo_CSV}'")
        sys.exit()
    except Exception as e:
        console.print(f"\n[bold red]¡ERROR![/bold red] Ocurrió un error inesperado al leer el archivo: {e}")
        sys.exit()
    
    # Mostrar la Tabla de todos los Procesos
    tabla_todos = crear_tabla_procesos_df(df_procesos, "Procesos leídos del Archivo CSV", "bold blue")
    console.print(tabla_todos)

    # --- TRANSICIÓN 2 ---
    pausar_y_limpiar("Presiona Enter para Filtrar los Procesos...")

    # --- PANTALLA 3: Filtrado y Resultados ---

    # Mensaje de filtrado
    console.print(f"\n[bold yellow]Realizando Filtrado de Procesos (Memoria Máxima = {MAX_MEMORIA}K)...[/bold yellow]")
    time.sleep(1.5)
    
    # Lógica de Filtrado
    df_aceptados = df_procesos[df_procesos['Tamaño'] <= MAX_MEMORIA].copy()
    df_descartados = df_procesos[df_procesos['Tamaño'] > MAX_MEMORIA].copy()
    
    # Mostrar resultados
    if df_descartados.empty:
        console.print(f"\n[bold green]Procesos validados. Todos los procesos han sido admitidos.[/bold green]")
        tabla_admitidos = crear_tabla_procesos_df(df_aceptados, "Procesos Admitidos", "bold green")
        console.print(tabla_admitidos)
    else:
        msg = f"Los siguientes {len(df_descartados)} proceso(s) fueron rechazados porque superan el tamaño máximo de {MAX_MEMORIA}K."
        console.print(f"\n[bold red]¡Atención![/bold red] {msg}\n")
        
        tabla_admitidos = crear_tabla_procesos_df(df_aceptados, "Procesos Aceptadps", "bold green")
        tabla_rechazados = crear_tabla_procesos_df(df_descartados, "Procesos Rechazados", "bold red")

        console.print(Columns([tabla_admitidos, tabla_rechazados], expand=True))

    # --- TRANSICIÓN 3: Ordenamiento ---
    if not df_aceptados.empty:
        pausar_y_limpiar("Presiona Enter para crear la 'Cola de Trabajo' ordenada...")
        
        # --- PANTALLA 4: Cola de Trabajo ---
        
        console.print(f"\n[bold yellow]Ordenando procesos por 'Tiempo de Arribo' (TA) y creando 'Cola de Trabajo'...[/bold yellow]")
        time.sleep(1.5)
        
        # Lógica de Ordenamiento
        df_aceptados_ordenados = df_aceptados.sort_values(by='Arribo').copy()
        
        # Creación de la colaDeTrabajo
        colaDeTrabajo: List[Proceso] = []
        for index, row in df_aceptados_ordenados.iterrows():
            proc = Proceso(
                idProceso=row['ID'],
                tamProceso=row['Tamaño'],
                TA=row['Arribo'],
                TI=row['Irrupcion']
            )
            colaDeTrabajo.append(proc)
        
        # Mostrar la nueva tabla
        mostrar_cola_de_trabajo(colaDeTrabajo)
        
        console.print(f"\n[bold green]¡Listo![/bold green] La 'Cola de Trabajo' está preparada.")
    else:
        # Si no hay procesos admitidos, no hay nada que ordenar
        console.print("\n\n[bold yellow]No hay procesos admitidos para la simulación.[/bold yellow]")

    # --- Fin de la fase de carga ---
    console.print("\n[bold green]Simulación de carga finalizada.[/bold green]")
    console.print("[dim]El siguiente paso sería iniciar el bucle principal del simulador (tiempo T).[/dim]")
    input("\nPresiona Enter para salir.")


if __name__ == "__main__":
    main()