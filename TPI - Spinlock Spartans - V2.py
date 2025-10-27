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

# --- 2. Definición de Clases (MODIFICADA) ---
class Proceso:
    def __init__(self, idProceso, tamProceso, estado, TA, TI):
      self.idProceso = idProceso
      self.tamProceso = tamProceso
      self.estado = estado
      self.TA = TA
      self.TI = TI
    
    def __repr__(self):
        # (CAMBIO) Esta es una representación estándar para depuración.
        # Muestra todos los atributos del objeto.
        return (f"Proceso(ID={self.idProceso}, Tam={self.tamProceso}K, "
                f"Estado={self.estado}, TA={self.TA}, TI={self.TI})")

# --- 3. Función Tabla de Procesos leidos desde el archivo CSV ---
def crear_tabla_procesos(df_procs, titulo_tabla, estilo_header):
    """
    Toma un DataFrame y devuelve un objeto Table de rich.
    """
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
    
    # 2a. Leer el archivo CSV
    archivo_CSV = r"C:\Users\criss\Downloads\procesos.csv"
    try:
        df_procesos = pd.read_csv(archivo_CSV)
    except FileNotFoundError:
        console.print(f"\n[bold red]¡ERROR![/bold red] No se pudo encontrar el archivo: '{archivo_CSV}'")
        sys.exit()
    except Exception as e:
        console.print(f"\n[bold red]¡ERROR![/bold red] Ocurrió un error inesperado al leer el archivo: {e}")
        sys.exit()
    
    # 2b. Mostrar la Tabla de todos los Procesos
    tabla_todos = crear_tabla_procesos(df_procesos, "Procesos leídos del Archivo CSV", "bold blue")
    console.print(tabla_todos)

    # --- TRANSICIÓN 2 ---
    pausar_y_limpiar("Presiona Enter para Filtrar los Procesos...")

    # --- PANTALLA 3: Filtrado y Resultados ---

    # 3a. Mensaje de filtrado
    console.print(f"\n[bold yellow]Realizando Filtrado de Procesos (Memoria Máxima = {MAX_MEMORIA}K)...[/bold yellow]")
    time.sleep(1.5)
    
    # 3b. Lógica de Filtrado
    df_admitidos = df_procesos[df_procesos['Tamaño'] <= MAX_MEMORIA].copy()
    df_descartados = df_procesos[df_procesos['Tamaño'] > MAX_MEMORIA].copy()
    
    # 3c. Mostrar resultados
    if df_descartados.empty:
        console.print(f"\n[bold green]Procesos validados. Todos los procesos han sido admitidos.[/bold green]")
        tabla_admitidos = crear_tabla_procesos(df_admitidos, "Procesos Admitidos", "bold green")
        console.print(tabla_admitidos)
    else:
        msg = f"Los siguientes {len(df_descartados)} proceso(s) fueron rechazados porque superan el tamaño máximo de {MAX_MEMORIA}K."
        console.print(f"\n[bold red]¡Atención![/bold red] {msg}\n")
        
        tabla_admitidos = crear_tabla_procesos(df_admitidos, "Procesos Admitidos", "bold green")
        tabla_rechazados = crear_tabla_procesos(df_descartados, "Procesos Rechazados", "bold red")

        console.print(Columns([tabla_admitidos, tabla_rechazados], expand=True))

    # --- TRANSICIÓN 3: Ordenamiento ---
    # Solo continuamos si hay procesos que ordenar
    if not df_admitidos.empty:
        pausar_y_limpiar("Presiona Enter para ordenar los Procesos admitidos por Tiempo de Arribo...")
        
        # --- PANTALLA 4: Procesos Ordenados ---
        
        # 4a. Mensaje de ordenamiento
        console.print(f"\n[bold yellow]Ordenando Procesos admitidos por 'Tiempo de Arribo' (TA)...[/bold yellow]")
        time.sleep(1.5)
        
        # 4b. Lógica de Ordenamiento
        df_admitidos_ordenados = df_admitidos.sort_values(by='Arribo').copy()
        
        # 4c. Volver a mostrar la tabla, pero la versión ordenada
        tabla_ordenada = crear_tabla_procesos(
            df_admitidos_ordenados, 
            "Procesos Admitidos (Ordenados por Tiempo de Arribo)", 
            "bold cyan"
        )
        console.print(tabla_ordenada)
    else:
        # Si no hay procesos admitidos, no hay nada que ordenar
        console.print("\n\n[bold yellow]No hay procesos admitidos para ordenar.[/bold yellow]")

    # --- Fin de la simulación ---
    console.print("\n\n[bold green]Simulación de carga finalizada.[/bold green]")
    input("Presiona Enter para salir.")


if __name__ == "__main__":
    main()