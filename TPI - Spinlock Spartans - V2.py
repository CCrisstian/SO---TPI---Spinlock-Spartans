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
    
class Cpu:
    def __init__(self):
        self.proceso_en_ejecucion: Proceso | None = None # El objeto Proceso
        self.tiempo_restante_irrupcion: int = 0
    
    def esta_libre(self) -> bool:
        return self.proceso_en_ejecucion is None

    def __repr__(self):
        if self.proceso_en_ejecucion:
            return f"CPU(Ejecutando ID: {self.proceso_en_ejecucion.idProceso}, TR: {self.tiempo_restante_irrupcion})"
        return "CPU(Libre)"
    
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

def crear_tabla_cpu(cpu: Cpu) -> Table:
    """Crea la tabla para mostrar el estado de la CPU."""
    tabla = Table(
        title="CPU",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    tabla.add_column("ID Proceso", justify="center")
    tabla.add_column("Estado", justify="center")
    tabla.add_column("Tiempo Restante", justify="center")

    if cpu.esta_libre():
        tabla.add_row("[dim]Libre[/dim]", "[dim]-[/dim]", "[dim]-[/dim]")
    else:
        tabla.add_row(
            str(cpu.proceso_en_ejecucion.idProceso),
            "[magenta]En Ejecución[/magenta]",
            str(cpu.tiempo_restante_irrupcion)
        )
    return tabla

# --- 4. Funciones de Lógica del Simulador ---

def gestor_memoria_best_fit(
    cola_ls: List[Proceso], 
    cola_l: List[Proceso], 
    particiones: List[Particion]
) -> List[str]:
    """
    Implementa Best-Fit. Intenta mover procesos de 'Listos/Suspendidos' a 'Listos'
    si encuentra una partición adecuada.
    Devuelve una lista de mensajes de eventos.
    """
    eventos = []
    
    for proceso in cola_ls[:]:
        mejor_particion_idx = -1
        min_fragmentacion = float('inf')

        # 1. Encontrar la mejor partición (Best-Fit)
        for i, part in enumerate(particiones):
            # No usar la partición del SO
            if part.id_part == "SO":
                continue
                
            # Comprobar si la partición está libre y si el proceso cabe
            if part.id_proceso is None and proceso.tamProceso <= part.tamano:
                fragmentacion = part.tamano - proceso.tamProceso
                
                # Comprobar si es la "mejor" hasta ahora
                if fragmentacion < min_fragmentacion:
                    min_fragmentacion = fragmentacion
                    mejor_particion_idx = i
        
        # 2. Si se encontró una partición, asignar el proceso
        if mejor_particion_idx != -1:
            particion_asignada = particiones[mejor_particion_idx]
            
            # Actualizar estado y colas
            proceso.estado = "Listo"
            cola_l.append(proceso) # Mover a Cola de Listos
            cola_ls.remove(proceso) # Sacar de Cola de Listos/Suspendidos
            
            # Ocupar la partición
            particion_asignada.id_proceso = proceso.idProceso
            particion_asignada.fragmentacion = min_fragmentacion
            
            eventos.append(
                f"[cyan]Best-Fit:[/cyan] Proceso [bold]{proceso.idProceso}[/bold] asignado a partición [bold]{particion_asignada.id_part}[/bold] (Frag. {min_fragmentacion}K)."
            )       
    return eventos

def gestor_cpu_srtf(
    cpu: Cpu, 
    cola_l: List[Proceso]
) -> List[str]:
    """
    Implementa SRTF. Decide qué proceso debe estar en la CPU.
    Maneja la carga inicial y la apropiación.
    Devuelve una lista de mensajes de eventos.
    """
    eventos = []
    
    # 1. Ordenar Cola de Listos por SRTF (menor TI restante)
    # (El proceso en CPU no está en esta cola, así que no compite aquí)
    cola_l.sort(key=lambda p: p.TI)
    
    # 2. Si la CPU está libre y hay procesos en "Listos"
    if cpu.esta_libre() and cola_l:
        proceso_a_cargar = cola_l.pop(0) # Sacar el más corto de "Listos"
        proceso_a_cargar.estado = "En Ejecución"
        cpu.proceso_en_ejecucion = proceso_a_cargar
        cpu.tiempo_restante_irrupcion = proceso_a_cargar.TI
        
        eventos.append(
            f"[magenta]SRTF Carga:[/magenta] Proceso [bold]{proceso_a_cargar.idProceso}[/bold] (TI = {proceso_a_cargar.TI}) entra a la CPU."
        )

    # 3. Lógica de APROPIACIÓN (Preemption)
    # (Como dijo el profesor: solo un proceso que *recién llega* a 'Listos'
    # puede causar apropiación. Nuestro 'gestor_memoria_best_fit' ya los movió a 'cola_l', y ya la ordenamos.)
    
    # Si la CPU está ocupada y hay procesos en "Listos"
    elif not cpu.esta_libre() and cola_l:
        proceso_en_cpu = cpu.proceso_en_ejecucion
        proceso_mas_corto_listo = cola_l[0] # El más corto en "Listos"
        
        # Comprobar si el de "Listos" es más corto que el *restante* en CPU
        if proceso_mas_corto_listo.TI < cpu.tiempo_restante_irrupcion:
            eventos.append(
                f"[magenta]SRTF Apropiación:[/magenta] Proceso [bold]{proceso_mas_corto_listo.idProceso}[/bold] (TI = {proceso_mas_corto_listo.TI}) "
                f"desaloja al Proceso [bold]{proceso_en_cpu.idProceso}[/bold] (TR = {cpu.tiempo_restante_irrupcion})."
            )
            
            # Devolver el proceso de la CPU a "Listos"
            proceso_en_cpu.estado = "Listo"
            proceso_en_cpu.TI = cpu.tiempo_restante_irrupcion # Actualizar su TI restante
            cola_l.append(proceso_en_cpu)
            
            # Cargar el nuevo proceso (el más corto)
            proceso_nuevo = cola_l.pop(0) # (Será el que acabamos de mirar)
            proceso_nuevo.estado = "En Ejecución"
            cpu.proceso_en_ejecucion = proceso_nuevo
            cpu.tiempo_restante_irrupcion = proceso_nuevo.TI
    return eventos

def ejecutar_tick_cpu(
    cpu: Cpu, 
    cola_l: List[Proceso], 
    cola_terminados: List[Proceso],
    particiones: List[Particion]
) -> List[str]:
    """
    Decrementa TI.
    Si un proceso termina, lo mueve a 'Terminados' y libera la partición.
    Devuelve una lista de mensajes de eventos.
    """
    eventos = []
    
    if not cpu.esta_libre():
        cpu.tiempo_restante_irrupcion -= 1
        proceso_actual = cpu.proceso_en_ejecucion
        
        if cpu.tiempo_restante_irrupcion <= 0:
            # --- Proceso TERMINADO ---
            eventos.append(
                f"[red]Proceso Terminado:[/red] Proceso [bold]{proceso_actual.idProceso}[/bold] ha finalizado."
            )
            
            # 1. Mover a Cola de Terminados
            proceso_actual.estado = "Terminado"
            proceso_actual.TI = 0 # Su TI ahora es 0
            cola_terminados.append(proceso_actual)
            
            # 2. Liberar Partición de Memoria
            for part in particiones:
                if part.id_proceso == proceso_actual.idProceso:
                    part.id_proceso = None
                    part.fragmentacion = 0
                    eventos.append(f"    -> Partición [bold]{part.id_part}[/bold] liberada.")
                    break
            
            # 3. Vaciar la CPU
            cpu.proceso_en_ejecucion = None
            cpu.tiempo_restante_irrupcion = 0
            
        else:
            # --- Proceso AÚN EN EJECUCIÓN ---
            pass 
    return eventos


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
    
    # --- TRANSICIÓN ---
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

    # --- TRANSICIÓN ---
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

    # --- TRANSICIÓN ---
    if not df_aceptados.empty:
        pausar_y_limpiar("Presiona Enter para crear la 'Cola de Trabajo' ordenada...")
        
        # --- PANTALLA 4: Cola de Trabajo ---
        
        console.print(f"\n[bold yellow]Ordenando procesos por 'Tiempo de Arribo' (TA) y creando 'Cola de Trabajo'...[/bold yellow]")
        time.sleep(1.5)
        console.print()
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

    # --- PANTALLA 5: BUCLE PRINCIPAL DE SIMULACIÓN ---
    
    # --- 1. Inicialización de variables de simulación ---
    T = 0 # Variable global de Tiempo
    cola_listos_suspendidos: List[Proceso] = []
    cola_listos: List[Proceso] = []
    cola_terminados: List[Proceso] = []
    
    procesos_totales_count = len(colaDeTrabajo)
    procesos_terminados_count = 0
    
    cpu = Cpu()
    tabla_particiones: List[Particion] = [
        Particion(id_part="SO", dir_inicio=0, tamano=100, id_proceso="SO"),
        Particion(id_part="Grandes", dir_inicio=100, tamano=250),
        Particion(id_part="Medianos", dir_inicio=350, tamano=150),
        Particion(id_part="Pequeños", dir_inicio=500, tamano=50)
    ]
    

    # --- 2. Inicio del Bucle Principal ---
    while procesos_terminados_count < procesos_totales_count:
        
        # --- 2a. LÓGICA DE EVENTOS PRIMERO ---
        eventos_T = []
        go_to_best_fit = False
        
        # --- (Evento 1: Arribos) ---
        procesos_llegados_en_T = [p for p in colaDeTrabajo if p.TA <= T]
        if procesos_llegados_en_T:
            for proceso_llegado in procesos_llegados_en_T:
                if (len(cola_listos) + len(cola_listos_suspendidos) + (1 if not cpu.esta_libre() else 0)) < GRADO_MAX_MULTIPROGRAMACION:
                    eventos_T.append(f"[green]Arribo:[/green] Proceso [bold]{proceso_llegado.idProceso}[/bold] (TA = {proceso_llegado.TA}). Pasa a 'Listos/Suspendidos'.")
                    proceso_llegado.estado = "Listo y Suspendido"
                    cola_listos_suspendidos.append(proceso_llegado)
                    colaDeTrabajo.remove(proceso_llegado)
                else:
                    eventos_T.append(f"[yellow]Arribo Bloqueado:[/yellow] Proceso [bold]{proceso_llegado.idProceso}[/bold], GDM ({GRADO_MAX_MULTIPROGRAMACION}) lleno. Espera.")
        
        # --- (Evento 2: Ejecutar Tick de CPU) ---
        eventos_tick = ejecutar_tick_cpu(cpu, cola_listos, cola_terminados, tabla_particiones)
        if eventos_tick:
            if "Proceso Terminado" in eventos_tick[0]:
                procesos_terminados_count += 1
            eventos_T.extend(eventos_tick)

        # --- (Evento 3: Gestión de Memoria Best-Fit) ---
        eventos_mem = gestor_memoria_best_fit(cola_listos_suspendidos, cola_listos, tabla_particiones)
        if eventos_mem:
            eventos_T.extend(eventos_mem)

        # --- (Evento 4: Algoritmo de CPU SRTF) ---
        eventos_cpu = gestor_cpu_srtf(cpu, cola_listos)
        if eventos_cpu:
            eventos_T.extend(eventos_cpu)

        # --- (Lógica de 'go_to_best_fit' - SI NO HAY ARRIBOS) ---
        if not procesos_llegados_en_T:
            if (len(cola_listos) + len(cola_listos_suspendidos) + (1 if not cpu.esta_libre() else 0)) > 0:
                 # Si no hay arribos Y el sistema está ocupado
                 eventos_T.append("[dim]... (No hay nuevos arribos. Esperando...) ...[/dim]")
            else:
                 # Si no hay arribos Y el sistema está vacío
                 eventos_T.append("[dim]Sistema vacío, esperando arribos...[/dim]")


# --- 2b. SALIDAS POR PANTALLA ---
        limpiar_pantalla()
        
        # Título
        console.print(f"[bold white on blue] Instante de Tiempo T = {T} [/bold white on blue]", justify="center")

        # Cola de Trabajo
        tabla_ct_render = crear_tabla_procesos(colaDeTrabajo, "Cola de Trabajo (Nuevos)", "bold cyan", "yellow")
        console.print(tabla_ct_render, justify="left")
        console.print()

        # Separador "Simulador"
        console.print(Rule("Simulador"))
        
        # Eventos
        if not eventos_T:
             if not colaDeTrabajo and len(cola_listos) == 0 and len(cola_listos_suspendidos) == 0 and cpu.esta_libre():
                 eventos_T.append("[dim]... (Simulación estancada, revisando fin) ...[/dim]")
             else:
                 eventos_T.append("[dim]... (Nada que reportar) ...[/dim]")
        for evento in eventos_T:
            console.print(evento)
            
        
        console.print()
        
        # 1. Crear tablas (el orden de creación no importa)
        tabla_cl_render = crear_tabla_procesos(cola_listos, "Cola de Listos", "bold green", "green")
        tabla_tp_render = crear_tabla_particiones(tabla_particiones)
        tabla_cls_render = crear_tabla_procesos(cola_listos_suspendidos, "Cola de Listos/Suspendidos", "bold yellow", "yellow")
        tabla_cpu_render = crear_tabla_cpu(cpu)
        tabla_term_render = crear_tabla_procesos(cola_terminados, "Procesos Terminados", "dim", "dim")
        
        # 2. Imprimir en el layout (el orden de impresión sí importa)
        
        # Cola de Listos/Suspendidos (Izquierda) | Tabla de Particiones (Derecha)
        console.print(Columns([tabla_cls_render, tabla_tp_render], expand=True, equal=True))
        
        # Cola de Listos (Izquierda) | CPU (Derecha)
        console.print(Columns([tabla_cl_render, tabla_cpu_render], expand=True, equal=True))
        
        # Procesos Terminados (Izquierda)
        console.print()
        console.print(tabla_term_render, justify="left")

        # --- Condición de Fin del Bucle ---
        if go_to_best_fit:
            console.print("\n[bold magenta]... (Se detiene el reloj para Módulo Best-Fit) ...[/bold magenta]")
            break

        if procesos_terminados_count >= procesos_totales_count:
            # Esta es la condición de fin principal
            break

        # --- Pausa para avanzar T ---
        try:
            input(f"\nPresione Enter para avanzar a T = {T+1}...")
        except KeyboardInterrupt:
            console.print("\n[red]Simulación interrumpida por el usuario.[/red]")
            sys.exit()
            
        T += 1

    # --- Fin de la simulación ---
    limpiar_pantalla()
    console.print(f"[bold green on black] Simulación Finalizada en T = {T} [/bold green on black]")    
    console.print("\n--- Estado Final del Sistema ---", style="dim")
    console.print()
    tabla_tp_render = crear_tabla_particiones(tabla_particiones)
    console.print(tabla_tp_render)
    console.print()
    tabla_term_render = crear_tabla_procesos(cola_terminados, "Procesos Terminados", "bold green", "dim")
    console.print(tabla_term_render)
    
    input("\nPresiona Enter para salir.")

if __name__ == "__main__":
    main()