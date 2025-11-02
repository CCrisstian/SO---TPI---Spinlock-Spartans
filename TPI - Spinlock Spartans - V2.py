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
from rich.rule import Rule
from typing import List

# --- 0. Configuración inicial ---
console = Console()
MAX_MEMORIA = 250 # Límite de memoria
GRADO_MAX_MULTIPROGRAMACION = 5 # Límite de procesos en el sistema

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

class Particion:
    def __init__(self, id_part: str, dir_inicio: int, tamano: int, id_proceso: str | int = None, fragmentacion: int = 0):
        self.id_part = id_part           # "SO", "Grandes", "Medianos", "Pequeños"
        self.dir_inicio = dir_inicio     # 0, 100, 350, 500
        self.tamano = tamano             # 100, 250, 150, 50
        self.id_proceso = id_proceso     # None si está libre, o el ID del proceso
        self.fragmentacion = fragmentacion # tamano - tamProceso
    
    def __repr__(self):
        return (f"Particion(ID='{self.id_part}', Inicio={self.dir_inicio}, "
                f"Tam={self.tamano}K, ProcID={self.id_proceso})")
    

# --- 3. Funciones de Creación de Tablas ---

def crear_tabla_procesos_df(df_procs, titulo_tabla, estilo_header):
    """Toma un DataFrame de PANDAS y devuelve un objeto Table de rich."""
    tabla = Table(
        title=titulo_tabla,
        box=box.ROUNDED,
        show_header=True,
        header_style=estilo_header
    )
    tabla.add_column("ID", justify="center")
    tabla.add_column("Tamaño", justify="center")
    tabla.add_column("Arribo", justify="center")
    tabla.add_column("Irrupcion", justify="center")

    for index, row in df_procs.iterrows():
        tabla.add_row(
            str(row['ID']),
            f"{row['Tamaño']}K",
            str(row['Arribo']),
            str(row['Irrupcion'])
        )
    return tabla

def crear_tabla_rechazados_df(df_procs, titulo_tabla, estilo_header):
    """Toma un DataFrame de PANDAS de procesos rechazados y muestra la Razón."""
    tabla = Table(
        title=titulo_tabla,
        box=box.ROUNDED,
        show_header=True,
        header_style=estilo_header
    )
    tabla.add_column("ID", justify="center")
    tabla.add_column("Tamaño", justify="center")
    tabla.add_column("Arribo", justify="center")
    tabla.add_column("Irrupción", justify="center")
    tabla.add_column("Razón de Rechazo", justify="left", style="yellow")

    for index, row in df_procs.iterrows():
        id_str = str(row.get('ID', 'N/A'))
        tam_str = str(row.get('Tamaño', 'N/A'))
        arr_str = str(row.get('Arribo', 'N/A'))
        irr_str = str(row.get('Irrupcion', 'N/A'))
        
        tabla.add_row(
            id_str,
            f"{tam_str}K" if pd.notnull(row.get('Tamaño')) else tam_str,
            arr_str,
            irr_str,
            str(row['Rechazo_Razon'])
        )
    return tabla

def crear_tabla_procesos(
    lista_procesos: List[Proceso], 
    titulo: str, 
    estilo_header: str, 
    estilo_estado: str = "yellow"
) -> Table:
    
    tabla = Table(
        title=titulo,
        box=box.ROUNDED,
        show_header=True,
        header_style=estilo_header
    )
    tabla.add_column("ID", justify="center")
    tabla.add_column("Tamaño", justify="center")
    tabla.add_column("Arribo", justify="center")
    tabla.add_column("Irrupción", justify="center")
    tabla.add_column("Estado", justify="center", style=estilo_estado)

    if not lista_procesos:
        tabla.add_row("[dim]Vacía...[/dim]", "-", "-", "-", "-")
    else:
        for proc in lista_procesos:
            tabla.add_row(
                str(proc.idProceso),
                f"{proc.tamProceso}K",
                str(proc.TA),
                str(proc.TI),
                proc.estado
            )
    return tabla

def crear_tabla_particiones(particiones: List[Particion]) -> Table:
    tabla = Table(
        title="Tabla de Particiones de Memoria",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    tabla.add_column("ID Partición", justify="left")
    tabla.add_column("Dir. Inicio", justify="center")
    tabla.add_column("Tamaño", justify="center")
    tabla.add_column("ID Proceso", justify="center")
    tabla.add_column("Frag. Interna", justify="center")

    for p in particiones:
        estilo = "on grey30" if p.id_part == "SO" else ""
        id_proc_str = str(p.id_proceso) if p.id_proceso is not None else "[dim]Libre[/dim]"
        frag_str = f"{p.fragmentacion}K" if p.fragmentacion > 0 else "0K"
        
        tabla.add_row(
            p.id_part,
            str(p.dir_inicio),
            f"{p.tamano}K",
            id_proc_str,
            frag_str,
            style=estilo
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
    
    # Leer el archivo CSV
    archivo_CSV = r"\Users\criss\Desktop\SO - Spinlock Spartans\procesos.csv"
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
    console.print(f"\n[bold yellow]Realizando Filtrado y Validación de Procesos[/bold yellow]")
    time.sleep(1.5)
    
    # --- Lógica de Validación y Filtrado ---
    
    # Columnas que deben ser números
    numeric_cols = ['Tamaño', 'Arribo', 'Irrupcion']
    
    df_validado = df_procesos.copy()
    
    # Creamos la nueva columna para la razón del rechazo
    df_validado['Rechazo_Razon'] = ''

    # --- Rechazar campos vacíos (ID) ---
    mask_id_vacio = df_validado['ID'].isnull()
    df_validado.loc[mask_id_vacio, 'Rechazo_Razon'] = 'ID vacío'

    # --- Rechazar campos vacíos o no numéricos (Tamaño, Arribo, Irrupcion) ---
    for col in numeric_cols:
        df_validado[col] = pd.to_numeric(df_validado[col], errors='coerce')
    
    # Ahora, 'NaN' significa que el campo estaba vacío O que no era un número
    mask_nan = df_validado[numeric_cols].isnull().any(axis=1)
    df_validado.loc[mask_nan & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = 'Campo vacío o no numérico'

    # --- Rechazar valores no positivos ---
    # Tamaño e Irrupción deben ser > 0
    mask_no_positivo = (df_validado['Tamaño'] <= 0) | (df_validado['Irrupcion'] <= 0) | (df_validado['Arribo'] < 0)
    df_validado.loc[mask_no_positivo & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = 'Valor negativo'

    # --- Rechazar por MAX_MEMORIA ---
    mask_memoria = df_validado['Tamaño'] > MAX_MEMORIA
    df_validado.loc[mask_memoria & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = f'Excede Memoria Máx. ({MAX_MEMORIA}K)'

    df_aceptados = df_validado[df_validado['Rechazo_Razon'] == ''].copy()
    df_descartados = df_validado[df_validado['Rechazo_Razon'] != ''].copy()

    for col in numeric_cols:
        df_aceptados[col] = df_aceptados[col].astype('Int64')

    # --- Mostrar resultados ---
    if df_descartados.empty:
        console.print(f"\n[bold green]Procesos validados. Todos los procesos han sido Aceptados.[/bold green]")
        tabla_admitidos = crear_tabla_procesos_df(df_aceptados, "Procesos Aceptados", "bold green")
        console.print(tabla_admitidos)
    else:
        msg = f"Se rechazaron {len(df_descartados)} proceso(s) por errores en los datos."
        console.print(f"\n[bold red]¡Atención![/bold red] {msg}\n")
        
        # Tabla de Admitidos (usa la función de DataFrame)
        tabla_admitidos = crear_tabla_procesos_df(df_aceptados, "Procesos Aceptados", "bold green")

        # Tabla de Rechazados (usa la función de DataFrame de Rechazados)
        tabla_rechazados = crear_tabla_rechazados_df(df_descartados, "Procesos Rechazados", "bold red")
        
        # Mostrar tablas lado a lado
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
        
        # Mostrar Cola de Trabajo
        tabla_ct_completa = crear_tabla_procesos(
            colaDeTrabajo, 
            "Cola de Trabajo",
            "bold cyan",
            "yellow"
        )
        console.print(tabla_ct_completa)
        
        console.print(f"\n[bold green]¡Listo![/bold green] La 'Cola de Trabajo' está preparada.")
    else:
        # Si no hay procesos admitidos, no hay nada que ordenar
        console.print("\n\n[bold yellow]No hay procesos admitidos para la simulación.[/bold yellow]")
        input("\nPresiona Enter para salir.")
        sys.exit()

    # --- FIN DE LA FASE DE CARGA ---
    
    pausar_y_limpiar("Presiona Enter para INICIAR LA SIMULACIÓN (T = 0)...")

    # --- PANTALLA 5: BUCLE PRINCIPAL DE SIMULACIÓN (v7 - Lógica primero) ---
    
    # --- Inicialización de variables de simulación ---
    T = 0 # Variable global de Tiempo
    cola_listos_suspendidos: List[Proceso] = []
    cola_listos: List[Proceso] = []
    procesos_en_simulador_count = 0 
    
    tabla_particiones: List[Particion] = [
        Particion(id_part="SO", dir_inicio=0, tamano=100, id_proceso="SO"),
        Particion(id_part="Grandes", dir_inicio=100, tamano=250),
        Particion(id_part="Medianos", dir_inicio=350, tamano=150),
        Particion(id_part="Pequeños", dir_inicio=500, tamano=50)
    ]
    
    # --- Inicio del Bucle Principal ---
    while True:
        # --- LÓGICA DE EVENTOS PRIMERO ---
        # Guardaremos los mensajes de eventos en esta lista para mostrarlos después
        eventos_T = []
        go_to_best_fit = False
        
        procesos_llegados_en_T = [p for p in colaDeTrabajo if p.TA <= T]
        
        if not procesos_llegados_en_T:
            # --- NO (No hay arribos) ---
            if procesos_en_simulador_count == 0:
                eventos_T.append("[dim]Sistema vacío, esperando arribos...[/dim]")
            else:
                #--- Condicion provisional para respetar MULTIPROGRAMACION ---
                if procesos_en_simulador_count == GRADO_MAX_MULTIPROGRAMACION:
                    eventos_T.append(f"[yellow]Se llego al máximo de Multi-Programación.[/yellow].")
                    go_to_best_fit = True
                    break
                else:
                    eventos_T.append("[bold magenta]No hay nuevos arribos en este instante. Esperando..[/bold magenta]")
        else:
            # --- SI (Hay arribos) ---
            for proceso_llegado in procesos_llegados_en_T:
                if procesos_en_simulador_count < GRADO_MAX_MULTIPROGRAMACION:
                    eventos_T.append(f"[green]Llega Proceso [bold]{proceso_llegado.idProceso}[/bold] (TA = {proceso_llegado.TA}).[/green] Pasa a 'Listos/Suspendidos'.")
                    proceso_llegado.estado = "Listo y Suspendido"
                    cola_listos_suspendidos.append(proceso_llegado)
                    colaDeTrabajo.remove(proceso_llegado) # Sacar de Cola de trabajo
                    procesos_en_simulador_count += 1  # Ingresa un Proceso al Simulador
                    
                    eventos_T.append(f"[dim]Procesos en sistema: {procesos_en_simulador_count}/{GRADO_MAX_MULTIPROGRAMACION}[/dim]")
                else:
                    eventos_T.append(f"[yellow]Llega Proceso [bold]{proceso_llegado.idProceso}[/bold], no puede ingresar porque se llegó al máximo de Multi-Programación.[/yellow].")
                    go_to_best_fit = True
                    break

        # --- SALIDAS POR PANTALLA ---        
        
        limpiar_pantalla()
        
        # Título
        console.print(f"[bold white on blue] Instante de Tiempo T = {T} [/bold white on blue]", justify="center")

        # Cola de Trabajo 
        tabla_ct_render = crear_tabla_procesos(
            colaDeTrabajo,
            "Cola de Trabajo",
            "bold cyan",
            "yellow"
        )
        console.print(tabla_ct_render)
        console.print() # Salto de línea

        # Separador "Simulador"
        console.print(Rule("Simulador"))
        
        # Mostramos los mensajes guardados
        for evento in eventos_T:
            console.print(evento)
        
        console.print() # Salto de línea

        # Tablas
        tabla_cls_render = crear_tabla_procesos(
            cola_listos_suspendidos,
            "Cola de Listos/Suspendidos",
            "bold yellow",
            "yellow"
        )

        tabla_tp_render = crear_tabla_particiones(tabla_particiones)

        tabla_cl_render = crear_tabla_procesos(
            cola_listos,
            "Cola de Listos",
            "bold green",
            "green"
        )

        console.print(Columns([tabla_cls_render, tabla_tp_render], expand=True))
        console.print(tabla_cl_render)

        # --- Condición de Fin del Bucle (Provisional) ---
        if go_to_best_fit:
            console.print("\n[bold magenta]... Siguiente paso Módulo Best-Fit ...[/bold magenta]")
            break

        if not colaDeTrabajo and procesos_en_simulador_count == 0:
            console.print("\n[bold green]... (Todos los procesos han sido procesados) ...[/bold green]")
            break

        # --- Pausa para avanzar T ---
        try:
            input(f"\nPresione Enter para avanzar a T = {T+1}...")
        except KeyboardInterrupt:
            console.print("\n[red]Simulación interrumpida por el usuario.[/red]")
            sys.exit()
            
        T += 1

    # --- Fin de la simulación ---
    input("\nPresiona Enter para salir.")

if __name__ == "__main__":
    main()