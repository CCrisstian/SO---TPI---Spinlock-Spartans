import pandas as pd
import os
import sys
import time
from rich.console import Console, Group
from rich.table import Table, Column
from rich.panel import Panel
from rich import box
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from typing import List, Tuple

# --- 0. Configuración inicial ---
console = Console()
MAX_MEMORIA = 250 # Límite de memoria
GRADO_MAX_MULTIPROGRAMACION = 5 # Límite de procesos en el sistema

# --- 1. Funciones de Transición ---

def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def pausar_y_limpiar(mensaje="Presiona Enter para continuar..."):
    console.print(f"\n[dim italic]{mensaje}[/dim italic]")
    input() # Espera que el usuario presione Enter
    limpiar_pantalla()

# --- 2. Definición de Clases ---

class Proceso:
    def __init__(self, idProceso, tamProceso, TA, TI, estado="Nuevo"):
      self.idProceso = idProceso
      self.tamProceso = tamProceso
      self.estado = estado
      self.TA = TA
      self.TI = TI
    
    def __repr__(self):
        return (f"Proceso(ID={self.idProceso}, Tam={self.tamProceso}K, "
                f"Estado='{self.estado}', TA={self.TA}, TI={self.TI})")

class Particion:
    def __init__(self, id_part: str, dir_inicio: int, tamano: int, id_proceso: str | int = None, fragmentacion: int = 0):
      self.id_part = id_part
      self.dir_inicio = dir_inicio
      self.tamano = tamano
      self.id_proceso = id_proceso
      self.fragmentacion = fragmentacion
    
    def __repr__(self):
        return (f"Particion(ID='{self.id_part}', Inicio={self.dir_inicio}, "
                f"Tam={self.tamano}K, ProcID={self.id_proceso})")
    
class Cpu:
    def __init__(self):
        self.proceso_en_ejecucion: Proceso | None = None
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
    """Crea una tabla de procesos (5 columnas) desde una List[Proceso]."""
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
    """Crea la tabla para la Tabla de Particiones de Memoria."""
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

def mostrar_logo(archivo_logo: str, color_logo: str = "green"):
    """
    Lee un archivo de texto (ASCII art) y lo imprime en la consola
    línea por línea para un efecto de renderizado.
    """
    limpiar_pantalla()
    try:
        # 1. Leer el contenido del archivo y guardarlo en una variable
        with open(archivo_logo, 'r', encoding='utf-8') as f:
            lineas = f.readlines()
        
        # Mover el cursor un poco hacia abajo para centrarlo verticalmente
        console.print("\n\n")
        
        # 2. Renderizar línea a línea
        for linea in lineas:
            # Imprimir la línea sin saltos de línea extra y con color
            console.print(linea.rstrip('\n'), style=color_logo)
            # Pausa muy corta para el efecto de renderizado
            time.sleep(0.05) 
            
        # Pausa al final para admirar el logo
        time.sleep(1)

    except FileNotFoundError:
        # Manejar el error si el archivo .txt no se encuentra
        console.print(f"[bold yellow]Advertencia:[/bold yellow] No se encontró el archivo del logo: '{archivo_logo}'.")
        console.print("Asegúrate de que 'LogoSpinlock Spartans.txt' esté en la misma carpeta que el script.")
        time.sleep(3) # Pausa para que se pueda leer el error
    except Exception as e:
        console.print(f"[bold red]Error al leer el logo:[/bold red] {e}")
        time.sleep(3)


# --- 4. Funciones de Lógica del Simulador ---

def buscar_particion_best_fit(proceso: Proceso, particiones: List[Particion]) -> int:
    mejor_particion_idx = -1
    min_fragmentacion = float('inf') 

    for i, part in enumerate(particiones):
        if part.id_part == "SO":
            continue
        if part.id_proceso is None and proceso.tamProceso <= part.tamano:
            fragmentacion = part.tamano - proceso.tamProceso
            if fragmentacion < min_fragmentacion:
                min_fragmentacion = fragmentacion
                mejor_particion_idx = i
                
    return mejor_particion_idx

def procesar_finalizaciones_y_promociones(
    cpu: Cpu, 
    cola_l: List[Proceso], 
    cola_ls: List[Proceso], 
    cola_terminados: List[Proceso],
    particiones: List[Particion]
) -> tuple[List[str], int]:

    eventos = []
    gdm_liberado = 0 
    
    if not cpu.esta_libre() and cpu.tiempo_restante_irrupcion <= 0:
        proceso_actual = cpu.proceso_en_ejecucion
        eventos.append(f"[red]Proceso Terminado:[/red] Proceso [bold]{proceso_actual.idProceso}[/bold] ha finalizado.")
        
        proceso_actual.estado = "Terminado"
        proceso_actual.TI = 0
        cola_terminados.append(proceso_actual)
        gdm_liberado = 1 
        
        cpu.proceso_en_ejecucion = None
        cpu.tiempo_restante_irrupcion = 0
        
        particion_liberada_idx = -1
        for i, part in enumerate(particiones):
            if part.id_proceso == proceso_actual.idProceso:
                part.id_proceso = None
                part.fragmentacion = 0
                particion_liberada_idx = i
                eventos.append(f"    -> Partición [bold]{part.id_part}[/bold] liberada.")
                break
        
        # --- Promoción basada en SRTF ---
        if particion_liberada_idx != -1:
            particion_liberada = particiones[particion_liberada_idx]
            
            # 1. Encontrar al más corto en ListoSuspendido que quepa
            mejor_candidato_ls = None
            mejor_ti = float('inf')
            
            for proc_ls in cola_ls:
                if proc_ls.tamProceso <= particion_liberada.tamano:
                    if proc_ls.TI < mejor_ti:
                        mejor_ti = proc_ls.TI
                        mejor_candidato_ls = proc_ls
            
            # 2. Si encontramos un candidato, promoverlo
            if mejor_candidato_ls:
                # Mover de ListoSuspendido a Listo
                mejor_candidato_ls.estado = "Listo"
                cola_l.append(mejor_candidato_ls)
                cola_ls.remove(mejor_candidato_ls)
                
                # Asignar la partición
                particion_liberada.id_proceso = mejor_candidato_ls.idProceso
                particion_liberada.fragmentacion = particion_liberada.tamano - mejor_candidato_ls.tamProceso
                
                eventos.append(
                    f"[cyan]Promoción (Listos/Suspendidos -> Listos):[/cyan] Proceso (SRTF) [bold]{mejor_candidato_ls.idProceso}[/bold] "
                    f"movido a 'Cola de Listos' y asignado a partición [bold]{particion_liberada.id_part}[/bold]."
                )            
    return eventos, gdm_liberado

def procesar_arribos(
    T: int,
    colaDeTrabajo: List[Proceso], 
    cola_l: List[Proceso], 
    cola_ls: List[Proceso], 
    particiones: List[Particion],
    cpu: Cpu,
    procesos_en_simulador_count: int
) -> tuple[List[str], int]:
    eventos = []
    gdm_agregado = 0
    
    procesos_llegados_en_T = [p for p in colaDeTrabajo if p.TA <= T]
        
    if procesos_llegados_en_T:
        # Ordenar por TA y luego por ID
        procesos_llegados_en_T.sort(key=lambda p: (p.TA, p.idProceso))
        
        for proceso_llegado in procesos_llegados_en_T:
            # GDM se calcula en cada iteración para ser preciso
            if (procesos_en_simulador_count + gdm_agregado) < GRADO_MAX_MULTIPROGRAMACION:
                
                idx_particion = buscar_particion_best_fit(proceso_llegado, particiones)
                
                if idx_particion != -1:
                    particion_asignada = particiones[idx_particion]
                    eventos.append(f"[green]Arribo (Memoria OK):[/green] Proceso [bold]{proceso_llegado.idProceso}[/bold]. Asignado a [bold]{particion_asignada.id_part}[/bold].")
                    proceso_llegado.estado = "Listo"
                    cola_l.append(proceso_llegado)
                    colaDeTrabajo.remove(proceso_llegado)
                    particion_asignada.id_proceso = proceso_llegado.idProceso
                    particion_asignada.fragmentacion = particion_asignada.tamano - proceso_llegado.tamProceso
                else:
                    eventos.append(f"[yellow]Arribo (Sin Memoria):[/yellow] Proceso [bold]{proceso_llegado.idProceso}[/bold]. Pasa a 'Listos/Suspendidos'.")
                    proceso_llegado.estado = "Listo y Suspendido"
                    cola_ls.append(proceso_llegado)
                    colaDeTrabajo.remove(proceso_llegado)
                
                gdm_agregado += 1
            else:
                eventos.append(f"[yellow]Arribo Bloqueado:[/yellow] Proceso [bold]{proceso_llegado.idProceso}[/bold], GDM ({GRADO_MAX_MULTIPROGRAMACION}) lleno. Espera.")

    return eventos, gdm_agregado

def gestor_cpu_srtf(
    cpu: Cpu, 
    cola_l: List[Proceso]
) -> List[str]:

    eventos = []
    
    # Ordenar Cola de Listos por SRTF (menor TI restante)
    cola_l.sort(key=lambda p: p.TI)
    
    if cpu.esta_libre() and cola_l:
        proceso_a_cargar = cola_l.pop(0) 
        proceso_a_cargar.estado = "En Ejecución"
        cpu.proceso_en_ejecucion = proceso_a_cargar
        cpu.tiempo_restante_irrupcion = proceso_a_cargar.TI
        
        eventos.append(
            f"[magenta]SRTF Carga:[/magenta] Proceso [bold]{proceso_a_cargar.idProceso}[/bold] (TI = {proceso_a_cargar.TI}) entra a la CPU."
        )

    elif not cpu.esta_libre() and cola_l:
        proceso_en_cpu = cpu.proceso_en_ejecucion
        proceso_mas_corto_listo = cola_l[0] 
        
        # Comprobar si hay un Proceso en "Listos" con un TI más corto que el *TI restante* del Proceso en CPU
        if proceso_mas_corto_listo.TI < cpu.tiempo_restante_irrupcion:
            eventos.append(
                f"[magenta]SRTF Apropiación:[/magenta] Proceso [bold]{proceso_mas_corto_listo.idProceso}[/bold] (TI = {proceso_mas_corto_listo.TI}) "
                f"desaloja al Proceso [bold]{proceso_en_cpu.idProceso}[/bold] (TR = {cpu.tiempo_restante_irrupcion})."
            )
            
            proceso_en_cpu.estado = "Listo"
            # Actualizar su TI restante para que compita justamente
            proceso_en_cpu.TI = cpu.tiempo_restante_irrupcion 
            cola_l.append(proceso_en_cpu)
            
            proceso_nuevo = cola_l.pop(0) 
            proceso_nuevo.estado = "En Ejecución"
            cpu.proceso_en_ejecucion = proceso_nuevo
            cpu.tiempo_restante_irrupcion = proceso_nuevo.TI
    return eventos

def ejecutar_tick_cpu(cpu: Cpu):
    if not cpu.esta_libre():
        cpu.tiempo_restante_irrupcion -= 1
        # Actualizamos el TI del Proceso para que SRTF siempre vea el valor restante
        cpu.proceso_en_ejecucion.TI = cpu.tiempo_restante_irrupcion

def gestor_intercambio_swap(
    cola_l: List[Proceso], 
    cola_ls: List[Proceso], 
    particiones: List[Particion],
    cpu: Cpu
) -> List[str]:
    """
    Intenta intercambiar un proceso de Listos/Suspendidos (alta prioridad, TI corto)
    por un proceso en memoria (baja prioridad, TI largo).
    """
    eventos = []
    
    # 1. ¿Hay procesos esperando en LS para competir?
    if not cola_ls:
        return eventos # No hay nadie para intercambiar

    # 2. Encontrar al mejor "Candidato" (el más corto en LS)
    cola_ls.sort(key=lambda p: p.TI)
    candidato = cola_ls[0]

    # 3. Encontrar "Víctima", con el TI más largo en Memoria y que NO esté en la CPU)
    victima = None
    particion_victima = None
    ti_victima_max = -1 # Buscamos el TI más largo

    particiones_trabajo = [p for p in particiones if p.id_part != "SO"]
    
    for part in particiones_trabajo:
        if part.id_proceso is None:
            continue
            
        if not cpu.esta_libre() and part.id_proceso == cpu.proceso_en_ejecucion.idProceso:
            continue
            
        proceso_en_particion = None
        # Encontrar el objeto Proceso "víctima" (que está en cola_l)
        for p_listo in cola_l:
             if p_listo.idProceso == part.id_proceso:
                 proceso_en_particion = p_listo
                 break
        
        if proceso_en_particion:
            # Comparamos el TI (tiempo restante)
            if proceso_en_particion.TI > ti_victima_max:
                ti_victima_max = proceso_en_particion.TI
                victima = proceso_en_particion
                particion_victima = part

    # 4. ¿Encontramos una víctima? ¿Vale la pena el intercambio?
    
    if victima and candidato.TI < victima.TI:

        # REGLA DE SEGURIDAD: ¿El candidato cabe en la partición de la víctima?
        if candidato.tamProceso <= particion_victima.tamano:
            
            # --- Ejecutar SWAP ---
            eventos.append(
                f"[red]Swap Out:[/red] Proceso [bold]{victima.idProceso}[/bold] (TI = {victima.TI}) "
                f"sale de Partición '{particion_victima.id_part}' y vuelve a 'Listos/Suspendidos'."
            )
            cola_l.remove(victima)
            victima.estado = "Listo y Suspendido"
            cola_ls.append(victima)
            
            eventos.append(
                f"[green]Swap In:[/green] Proceso [bold]{candidato.idProceso}[/bold] (TI = {candidato.TI}) "
                f"entra a Partición '{particion_victima.id_part}'."
            )
            cola_ls.remove(candidato)
            candidato.estado = "Listo"
            cola_l.append(candidato)
            
            # Actualizar la partición
            particion_victima.id_proceso = candidato.idProceso
            particion_victima.fragmentacion = particion_victima.tamano - candidato.tamProceso
    
    return eventos


# --- FUNCIÓN PRINCIPAL ---
def main():

    # --- PANTALLA 1: Presentación ---
    limpiar_pantalla() 

    # 1. Mostrar el logo leyéndolo desde el archivo
    mostrar_logo("Splashceen.txt", color_logo="bold green")
    
    # 2. Transición a integrantes
    pausar_y_limpiar("Presiona Enter para ver los integrantes del grupo...")

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
    pausar_y_limpiar("Presiona Enter para cargar los procesos...")

    # --- PANTALLA 2: Procesos Leídos ---
    archivo_CSV = "procesos.csv" 
    try:
        df_procesos = pd.read_csv(archivo_CSV)
    except FileNotFoundError:
        console.print(f"\n[bold red]¡ERROR![/bold red] No se pudo encontrar el archivo: '{archivo_CSV}'")
        console.print("Asegúrate de que 'procesos.csv' esté en la misma carpeta.")
        sys.exit()
    except Exception as e:
        console.print(f"\n[bold red]¡ERROR![/bold red] Ocurrió un error inesperado al leer el archivo: {e}")
        sys.exit()
    
    tabla_todos = crear_tabla_procesos_df(df_procesos, "Procesos leídos del Archivo CSV", "bold blue")
    console.print(tabla_todos)
    pausar_y_limpiar("Presiona Enter para Filtrar los Procesos...")

    # --- PANTALLA 3: Filtrado y Resultados ---
    console.print(f"\n[bold yellow]Realizando Filtrado y Validación de Procesos[/bold yellow]")
        
    # Definir qué columnas deben ser tratadas como números
    numeric_cols = ['Tamaño', 'Arribo', 'Irrupcion']
    
    # Crear una copia del DataFrame original para no modificarlo
    df_validado = df_procesos.copy()
    
    # 1. Crear una columna vacía para guardar la razón del rechazo
    df_validado['Rechazo_Razon'] = ''

    # 2. FILTRO (ID vacío): Encontrar filas donde 'ID' es nulo
    mask_id_vacio = df_validado['ID'].isnull()
    # Marcar esas filas con el motivo del rechazo
    df_validado.loc[mask_id_vacio, 'Rechazo_Razon'] = 'ID vacío'

    # 3. FILTRO (No numérico): Intentar convertir columnas a número
    for col in numeric_cols:
        # 'errors='coerce'' convierte texto en 'NaN' (Not a Number)
        df_validado[col] = pd.to_numeric(df_validado[col], errors='coerce')
    
    # Encontrar filas que tengan 'NaN' en CUALQUIERA de las columnas numéricas
    mask_nan = df_validado[numeric_cols].isnull().any(axis=1)
    # Marcar esas filas (solo si no tienen ya un error)
    df_validado.loc[mask_nan & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = 'Campo vacío o no numérico'

    # 4. FILTRO (Valor no positivo):
    # Tamaño e Irrupción deben ser > 0, Arribo puede ser 0
    mask_no_positivo = (df_validado['Tamaño'] <= 0) | (df_validado['Irrupcion'] <= 0) | (df_validado['Arribo'] < 0)
    # Marcar esas filas (solo si no tienen ya un error)
    df_validado.loc[mask_no_positivo & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = 'Valor negativo'

    # 5. FILTRO (Memoria Máxima):
    mask_memoria = df_validado['Tamaño'] > MAX_MEMORIA
    # Marcar esas filas (solo si no tienen ya un error)
    df_validado.loc[mask_memoria & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = f'Excede Memoria Máx. ({MAX_MEMORIA}K)'
    
    # 6. Crear el DataFrame de ACEPTADOS
    df_aceptados = df_validado[df_validado['Rechazo_Razon'] == ''].copy()

    # 7. Crear el DataFrame de DESCARTADOS
    df_descartados = df_validado[df_validado['Rechazo_Razon'] != ''].copy()

    # 8. Limpieza: Asegurarse de que los datos aceptados sean Enteros
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
        tabla_admitidos = crear_tabla_procesos_df(df_aceptados, "Procesos Aceptados", "bold green")
        tabla_rechazados = crear_tabla_rechazados_df(df_descartados, "Procesos Rechazados", "bold red")
        console.print(Columns([tabla_admitidos, tabla_rechazados], expand=True))

    # --- PANTALLA 4: Cola de Trabajo ---
    if not df_aceptados.empty:
        pausar_y_limpiar("Presiona Enter para crear la 'Cola de Trabajo' ordenada...")
        
        console.print(f"\n[bold yellow]Ordenando procesos por 'Tiempo de Arribo' (TA) y creando 'Cola de Trabajo'...[/bold yellow]")
        console.print()
        df_aceptados_ordenados = df_aceptados.sort_values(by='Arribo').copy()
        
        colaDeTrabajo: List[Proceso] = []
        for index, row in df_aceptados_ordenados.iterrows():
            proc = Proceso(
                idProceso=row['ID'],
                tamProceso=row['Tamaño'],
                TA=row['Arribo'],
                TI=row['Irrupcion']
            )
            colaDeTrabajo.append(proc)
        
        tabla_ct_completa = crear_tabla_procesos(
            colaDeTrabajo, 
            "Cola de Trabajo",
            "bold cyan",
            "yellow"
        )
        console.print(tabla_ct_completa)
        
        console.print(f"\n[bold green]¡Listo![/bold green] La 'Cola de Trabajo' está preparada.")
    else:
        console.print("\n\n[bold yellow]No hay procesos admitidos para la simulación.[/bold yellow]")
        input("\nPresiona Enter para salir.")
        sys.exit()

    pausar_y_limpiar("Presiona Enter para INICIAR LA SIMULACIÓN (T = 0)...")

    # --- PANTALLA 5: BUCLE PRINCIPAL DE SIMULACIÓN ---
    
    # --- 1. Inicialización de variables de simulación ---
    T = 0 
    cola_listos_suspendidos: List[Proceso] = []
    cola_listos: List[Proceso] = []
    cola_terminados: List[Proceso] = []
    
    procesos_totales_count = len(colaDeTrabajo)
    procesos_terminados_count = 0
    procesos_en_simulador_count = 0 
    
    cpu = Cpu()
    tabla_particiones: List[Particion] = [
        Particion(id_part="SO", dir_inicio=0, tamano=100, id_proceso="SO"),
        Particion(id_part="Grandes", dir_inicio=100, tamano=250),
        Particion(id_part="Medianos", dir_inicio=350, tamano=150),
        Particion(id_part="Pequeños", dir_inicio=500, tamano=50)
    ]
    
# --- 2. Inicio del Bucle Principal ---
    while procesos_terminados_count < procesos_totales_count:
        
        eventos_T = []
        
        # --- (Etapa 1 & 2: Finalizaciones y Promociones) ---
        # (Esto libera GDM y memoria)
        eventos_final, gdm_liberado = procesar_finalizaciones_y_promociones(
            cpu, cola_listos, cola_listos_suspendidos, cola_terminados, tabla_particiones
        )
        if eventos_final:
            eventos_T.extend(eventos_final)
            procesos_terminados_count += gdm_liberado
            procesos_en_simulador_count -= gdm_liberado 

        # --- (Etapa 2.5: Intercambio / Swap) ---
        # (Se ejecuta si la memoria sigue llena pero hay un proceso de alta prioridad en LS)
        eventos_swap = gestor_intercambio_swap(
            cola_listos, cola_listos_suspendidos, tabla_particiones, cpu
        )
        if eventos_swap:
            eventos_T.extend(eventos_swap)

        # --- (Etapa 3: Arribos nuevos) ---
        # (Ahora GDM y Memoria están actualizados antes de que lleguen los nuevos)
        eventos_arribo, gdm_agregado = procesar_arribos(
            T, colaDeTrabajo, cola_listos, cola_listos_suspendidos, 
            tabla_particiones,
            cpu, 
            procesos_en_simulador_count 
        )
        if eventos_arribo:
            eventos_T.extend(eventos_arribo)
            procesos_en_simulador_count += gdm_agregado

        # --- (Etapa 4: Planificación SRTF) ---
        eventos_srtf = gestor_cpu_srtf(cpu, cola_listos)
        if eventos_srtf:
            eventos_T.extend(eventos_srtf)
        
        # --- (Etapa 5: Ejecución de 1 unidad de tiempo) ---
        ejecutar_tick_cpu(cpu)

        # --- Lógica de Mensajes de Espera ---
        if not eventos_final and not eventos_arribo and not eventos_srtf and not eventos_swap:
             if procesos_en_simulador_count > 0:
                 eventos_T.append("[dim]... No hay eventos. Esperando ...[/dim]")
             elif not colaDeTrabajo:
                 pass
             else:
                 eventos_T.append("[dim]Sistema vacío, esperando arribos...[/dim]")

        # --- 2b. SALIDAS POR PANTALLA ---

        limpiar_pantalla()
        
        console.print(f"[bold white on blue] Instante de Tiempo T = {T} [/bold white on blue]", justify="center")
        console.print()

        # Fila 1: Cola de Trabajo (Izquierda) | Procesos Terminados (Derecha)
        tabla_ct_render = crear_tabla_procesos(colaDeTrabajo, "Cola de Trabajo", "bold cyan", "yellow")
        tabla_term_render = crear_tabla_procesos(cola_terminados, "Procesos Terminados", "bold red", "red")
        console.print(Columns([tabla_ct_render, tabla_term_render], expand=True, equal=True))

        console.print()

        console.print(Rule("Simulador"))
        
        if not eventos_T:
             if not colaDeTrabajo and len(cola_listos) == 0 and len(cola_listos_suspendidos) == 0 and cpu.esta_libre():
                 eventos_T.append("[dim]... (Simulación estancada, revisando fin) ...[/dim]")
             else:
                 eventos_T.append("[dim]... (Nada que reportar) ...[/dim]")
        for evento in eventos_T:
            console.print(evento)
            
        console.print()
        
        # Fila 2: Cola de Listos/Suspendidos (Izquierda) | Tabla de Particiones (Derecha)
        tabla_cls_render = crear_tabla_procesos(cola_listos_suspendidos, "Cola de Listos/Suspendidos", "bold yellow", "yellow")
        tabla_tp_render = crear_tabla_particiones(tabla_particiones)
        console.print(Columns([tabla_cls_render, tabla_tp_render], expand=True, equal=True))
        
        console.print()
        
        # Fila 3: Cola de Listos (Izquierda) | CPU (Derecha)
        tabla_cl_render = crear_tabla_procesos(cola_listos, "Cola de Listos", "bold green", "green")
        tabla_cpu_render = crear_tabla_cpu(cpu)
        console.print(Columns([tabla_cl_render, tabla_cpu_render], expand=True, equal=True))
        
        # --- Condición de Fin del Bucle ---
        if procesos_terminados_count >= procesos_totales_count:
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
    limpiar_pantalla()
    console.print(Rule("Estado Final del Sistema"))    
    console.print(f"[bold green on black]Simulación Finalizada en T = {T} [/bold green on black]")
    console.print()
    tabla_tp_render = crear_tabla_particiones(tabla_particiones)
    console.print(tabla_tp_render)
    console.print()
    tabla_term_render = crear_tabla_procesos(cola_terminados, "Procesos Terminados", "dim", "dim")
    console.print(tabla_term_render)
    
    input("\nPresiona Enter para salir.")

if __name__ == "__main__":
    main()