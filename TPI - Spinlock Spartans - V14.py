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
from statistics import mean # Para calcular promedios


#DEFINICIONES INICIALES
console = Console()
MAX_MEMORIA = 250 # Límite de memoria
GRADO_MAX_MULTIPROGRAMACION = 5 # Límite de procesos en el sistema

#FUNCIONES DE TRANSICION
def limpiar_pantalla():
    os.system('cls' if os.name == 'nt' else 'clear')

def pausar_y_limpiar(mensaje=str):
    console.print(f"\n[italic]{mensaje}[/italic]")
    input()
    limpiar_pantalla()

#DEFINICIONES DE CLASES
class Proceso:
    def __init__(self, idProceso, tamProceso, TA, TI, estado="Nuevo"):
      self.idProceso = idProceso
      self.tamProceso = tamProceso
      self.estado = estado
      self.TA = TA
      
      # TI se usará para el TI *restante* (para SRTF)
      self.TI = TI 
      
      # Atributos para estadísticas
      self.TI_original: int = TI            # Guardamos el TI original
      self.tiempo_finalizacion: int = 0     # El instante de tiempo T en el que termina
      self.tiempo_retorno: int = 0          # TR = TF - TA
      self.tiempo_espera: int = 0           # TE = TR - TI_original
    
    def __repr__(self):
        return (f"Proceso (ID={self.idProceso}, Tam={self.tamProceso}K, "
                f"Estado='{self.estado}', TA={self.TA}, TI={self.TI})")

class Particion:
    def __init__(self, id_part: str, dir_inicio: int, tamano: int, id_proceso: str | int = None, fragmentacion: int = 0):
      self.id_part = id_part
      self.dir_inicio = dir_inicio
      self.tamano = tamano
      self.id_proceso = id_proceso
      self.fragmentacion = fragmentacion
    
    def __repr__(self):
        return (f"Particion (ID='{self.id_part}', Inicio={self.dir_inicio}, "
                f"Tam={self.tamano}K, ProcID={self.id_proceso})")
    
class Cpu:
    def __init__(self):
        self.proceso_en_ejecucion: Proceso | None = None
        self.tiempo_restante_irrupcion: int = 0
    
    def esta_libre(self) -> bool:
        return self.proceso_en_ejecucion is None

    def __repr__(self):
        if self.proceso_en_ejecucion:
            return f"CPU (Ejecutando ID: {self.proceso_en_ejecucion.idProceso}, TR: {self.tiempo_restante_irrupcion})"
        return "CPU(Libre)"
    
#FUNCIONES PARA CREAR LAS DIFERENTES TABLAS

def crear_tabla_procesos_df(df_procs, titulo_tabla, estilo_header):     #Toma un DataFrame de PANDAS y devuelve un objeto Table de rich
    tabla = Table(
        title=titulo_tabla,
        box=box.ROUNDED,
        show_header=True,
        header_style=estilo_header
    )
    tabla.add_column("ID", justify="center")
    tabla.add_column("TAMAÑO", justify="center")
    tabla.add_column("ARRIBO", justify="center")
    tabla.add_column("IRRUPCION", justify="center")

    for index, row in df_procs.iterrows():
        tabla.add_row(
            str(row['ID']),
            f"{row['Tamaño']}K",
            str(row['Arribo']),
            str(row['Irrupcion'])
        )
    return tabla

def crear_tabla_rechazados_df(df_procs, titulo_tabla, estilo_header):   #Toma un DataFrame de PANDAS de procesos rechazados y muestra la Razón
    tabla = Table(
        title=titulo_tabla,
        box=box.ROUNDED,
        show_header=True,
        header_style=estilo_header
    )
    tabla.add_column("ID", justify="center")
    tabla.add_column("TAMAÑO", justify="center")
    tabla.add_column("ARRIBO", justify="center")
    tabla.add_column("IRRUPCION", justify="center")
    tabla.add_column("RAZON DE RECHAZO", justify="center", style="yellow")

    for index, row in df_procs.iterrows():
        id_str = str(row.get('ID', 'N/A'))
        tam_str = str(row.get('Tamaño', 'N/A'))
        arr_str = str(row.get('Arribo', 'N/A'))
        irr_str = str(row.get('Irrupcion', 'N/A'))
        
        tabla.add_row(          #Creacion de una linea por cada proceso
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
    estilo_estado: str
) -> Table:                     #Crea una tabla de procesos de 5 columnas, desde una List (Proceso)
    tabla = Table(
        title=titulo,
        box=box.ROUNDED,
        show_header=True,
        header_style=estilo_header
    )
    tabla.add_column("ID", justify="center")
    tabla.add_column("TAMAÑO", justify="center")
    tabla.add_column("ARRIBO", justify="center")
    tabla.add_column("IRRUPCION", justify="center")
    tabla.add_column("ESTADO", justify="center", style=estilo_estado)

    if not lista_procesos:
        tabla.add_row("Vacía...", "-", "-", "-", "-")
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

def crear_tabla_particiones(particiones: List[Particion]) -> Table:     #Crea la Tabla de Particiones de Memoria
    tabla = Table(
        title="PARTICIONES DE MEMORIA",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    tabla.add_column("ID PARTICION", justify="center")
    tabla.add_column("DIR. INICIAL", justify="center")
    tabla.add_column("TAMAÑO", justify="center")
    tabla.add_column("ID PROCESO", justify="center")
    tabla.add_column("FRAG. INTERNA", justify="center")

    for p in particiones:
        estilo = "on grey30" if p.id_part == "SO" else ""
        id_proc_str = str(p.id_proceso) if p.id_proceso is not None else "LIBRE"
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

def crear_tabla_cpu(cpu: Cpu) -> Table:         #Crea la tabla para mostrar el estado de la CPU
    tabla = Table(
        title="CPU",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    tabla.add_column("ID PROCESO", justify="center")
    tabla.add_column("ESTADO", justify="center")
    tabla.add_column("TIEMPO RESTANTE", justify="center")

    if cpu.esta_libre():
        tabla.add_row("Libre", "-", "-")
    else:
        tabla.add_row(
            str(cpu.proceso_en_ejecucion.idProceso),
            "[magenta]En Ejecución[/magenta]",
            str(cpu.tiempo_restante_irrupcion)
        )
    return tabla

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

def mostrar_informe_estadistico(procesos_terminados: List[Proceso], tiempo_total: int):
    """
    Calcula y muestra la tabla de estadísticas finales y promedios.
    """
    console.print()
    console.print(Rule("Informe Estadístico Final"))
    console.print()

    # 1. Crear Tabla de Tiempos por Proceso
    tabla_tiempos = Table(
        title="Tiempos por Proceso",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold green"
    )
    tabla_tiempos.add_column("ID", justify="center")
    tabla_tiempos.add_column("T. Arribo (TA)", justify="center")
    tabla_tiempos.add_column("T. Irrupción (TI)", justify="center")
    tabla_tiempos.add_column("T. Finalización (TF)", justify="center")
    tabla_tiempos.add_column("T. Retorno (TR = TF - TA)", justify="center")
    tabla_tiempos.add_column("T. Espera (TE = TR - TI)", justify="center")

    tiempos_retorno = []
    tiempos_espera = []

    # Ordenar por ID
    procesos_terminados.sort(key=lambda p: p.idProceso)

    for proc in procesos_terminados:
        tabla_tiempos.add_row(
            str(proc.idProceso),
            str(proc.TA),
            str(proc.TI_original), # Mostrar el TI Original
            str(proc.tiempo_finalizacion),
            f"[cyan]{proc.tiempo_retorno}[/cyan]",
            f"[yellow]{proc.tiempo_espera}[/yellow]"
        )
        tiempos_retorno.append(proc.tiempo_retorno)
        tiempos_espera.append(proc.tiempo_espera)

    console.print(tabla_tiempos)
    console.print()

    # 2. Calcular Promedios y Rendimiento
    if procesos_terminados: # Evitar división por cero
        n = len(procesos_terminados)
        # mean() toma una lista de números, los suma y los divide por la cantidad que hay en la lista
        trp = mean(tiempos_retorno)
        tep = mean(tiempos_espera)
        # Rendimiento = Trabajos / Tiempo Total
        rendimiento = n / tiempo_total 
    else:
        trp = 0
        tep = 0
        rendimiento = 0

    # 3. Crear Tabla de Promedios
    tabla_promedios = Table(
        title="Estadísticas Globales",
        box=box.ROUNDED,
        show_header=False,
        width=60
    )
    tabla_promedios.add_column("Métrica", justify="left", style="bold")
    tabla_promedios.add_column("Valor", justify="right")
    
    tabla_promedios.add_row("Tiempo de Simulación Total", f"{tiempo_total} ticks")
    tabla_promedios.add_row("Procesos Completados", f"{n} procesos")
    tabla_promedios.add_row("Tiempo de Retorno Promedio (TRP)", f"[cyan]{trp:.2f} ticks[/cyan]")
    tabla_promedios.add_row("Tiempo de Espera Promedio (TEP)", f"[yellow]{tep:.2f} ticks[/yellow]")
    tabla_promedios.add_row("Rendimiento del Sistema", f"[green]{rendimiento:.3f} procesos/tick[/green]")
    
    console.print(tabla_promedios, justify="left")

#FUNCIONES PARA LA LOGICA DEL SIMULADOR
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
    T: int,
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
        
        # Capturamos el instante de tiempo T cuando el Proceso abandona la CPU
        proceso_actual.tiempo_finalizacion = T 
        # Calculamos TR y TE usando el TI_original
        proceso_actual.tiempo_retorno = proceso_actual.tiempo_finalizacion - proceso_actual.TA
        proceso_actual.tiempo_espera = proceso_actual.tiempo_retorno - proceso_actual.TI_original
        
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
        
        if particion_liberada_idx != -1:    #Promocion basada en SRTF
            particion_liberada = particiones[particion_liberada_idx]
            
            mejor_candidato_ls = None       # 1. Encontrar al más corto en ListoSuspendido que quepa
            mejor_ti = float('inf')
            
            for proc_ls in cola_ls:
                if proc_ls.tamProceso <= particion_liberada.tamano:
                    if proc_ls.TI < mejor_ti:
                        mejor_ti = proc_ls.TI
                        mejor_candidato_ls = proc_ls
            
            if mejor_candidato_ls:      # 2. Si encontramos un candidato, promoverlo a la cola Listo
                mejor_candidato_ls.estado = "Listo"
                cola_l.append(mejor_candidato_ls)
                cola_ls.remove(mejor_candidato_ls)
                
                particion_liberada.id_proceso = mejor_candidato_ls.idProceso        # Asignar la partición libre
                particion_liberada.fragmentacion = particion_liberada.tamano - mejor_candidato_ls.tamProceso    #Calculo de fragmentacion de particion de memoria
                
                eventos.append(
                    f"[cyan]Promoción (Listos/Suspendidos -> Listos):[/cyan] [bold]Proceso {mejor_candidato_ls.idProceso}[/bold] "
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
        
    if procesos_llegados_en_T:          # Ordenar por TA y luego por ID
        procesos_llegados_en_T.sort(key=lambda p: (p.TA, p.idProceso))
        
        for proceso_llegado in procesos_llegados_en_T:          # GDM se calcula en cada iteración para ser preciso
            if (procesos_en_simulador_count + gdm_agregado) < GRADO_MAX_MULTIPROGRAMACION:
                idx_particion = buscar_particion_best_fit(proceso_llegado, particiones)
                
                if idx_particion != -1:
                    particion_asignada = particiones[idx_particion]
                    eventos.append(f"[green]Arribo:[/green] Proceso [bold]{proceso_llegado.idProceso}[/bold]. Asignado a [bold]{particion_asignada.id_part}[/bold].")
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

    # 1. Ordena la Cola de Listos (el más corto primero, menor TI restante)
    cola_l.sort(key=lambda p: p.TI)
    
    # Si la CPU está libre, carga al más corto
    if cpu.esta_libre() and cola_l:
        proceso_a_cargar = cola_l.pop(0) 
        proceso_a_cargar.estado = "En Ejecución"
        cpu.proceso_en_ejecucion = proceso_a_cargar
        cpu.tiempo_restante_irrupcion = proceso_a_cargar.TI
        eventos.append(f"[magenta]SRTF Carga:[/magenta] Proceso [bold]{proceso_a_cargar.idProceso}[/bold] (TI = {proceso_a_cargar.TI}) entra a la CPU.")

    # 2. Lógica de APROPIACIÓN (cuando la CPU está OCUPADA)
    elif not cpu.esta_libre() and cola_l:
        proceso_en_cpu = cpu.proceso_en_ejecucion
        proceso_mas_corto_listo = cola_l[0]     # El mejor de la Cola de Listos
        
        # Comprobar si hay un Proceso en "Listos" con un TI más corto que el *TI restante* del Proceso en CPU
        if proceso_mas_corto_listo.TI < cpu.tiempo_restante_irrupcion:
            # El nuevo es MÁS CORTO
            # Ocurre la apropiación
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
        # Si la condición 'if' NO se cumple:
        # El proceso nuevo se queda al principio de la 'cola_l' y el proceso en la CPU continúa ejecutándose.
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
) -> List[str]:         #Intenta intercambiar un proceso de Listos/Suspendidos (alta prioridad, TI corto)
    eventos = []        #por un proceso en memoria (baja prioridad, TI largo).
        
    if not cola_ls:         # 1. ¿Hay procesos esperando en LS para competir?
        return eventos # No hay nadie para intercambiar

    cola_ls.sort(key=lambda p: p.TI)        # 2. Encontrar al mejor "Candidato" (el más corto en LS)
    candidato = cola_ls[0]

    victima = None      # 3. Encontrar "Víctima", con el TI más largo en Memoria y que NO esté en la CPU)
    particion_victima = None    
    ti_victima_max = -1 # Buscamos el TI más largo

    particiones_trabajo = [p for p in particiones if p.id_part != "SO"]
    
    for part in particiones_trabajo:
        if part.id_proceso is None:
            continue
            
        if not cpu.esta_libre() and part.id_proceso == cpu.proceso_en_ejecucion.idProceso:
            continue
            
        proceso_en_particion = None         # Encontrar el objeto Proceso "víctima" (que está en cola_l)
        for p_listo in cola_l:
             if p_listo.idProceso == part.id_proceso:
                 proceso_en_particion = p_listo
                 break
        
        if proceso_en_particion:            # Comparamos el TI (tiempo restante)
            if proceso_en_particion.TI > ti_victima_max:
                ti_victima_max = proceso_en_particion.TI
                victima = proceso_en_particion
                particion_victima = part

    if victima and candidato.TI < victima.TI:       # 4. ¿Encontramos una víctima? ¿Vale la pena el intercambio?
        if candidato.tamProceso <= particion_victima.tamano:
            eventos.append(                         # --- Ejecutar SWAP ---
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
            particion_victima.id_proceso = candidato.idProceso
            particion_victima.fragmentacion = particion_victima.tamano - candidato.tamProceso
    return eventos

def main():     # --- FUNCIÓN PRINCIPAL ---

    limpiar_pantalla()
    mostrar_logo("Splashcreen.txt")
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
    
    tabla_todos = crear_tabla_procesos_df(df_procesos, "\nProcesos leídos del Archivo CSV", "bold blue")
    console.print(tabla_todos)
    pausar_y_limpiar("Presiona Enter para Filtrar los Procesos...")

    # --- PANTALLA 3: Filtrado y Resultados ---
    console.print(f"\n[bold yellow]Realizando Filtrado y Validación de Procesos[/bold yellow]")
    numeric_cols = ['Tamaño', 'Arribo', 'Irrupcion']    #Columnas numericas
    
    # Crear una copia del DataFrame original para no modificarlo
    df_validado = df_procesos.copy()
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
        console.print(f"\n[bold green]Procesos validados. Todos los procesos han sido Aceptados.[/bold green]\n")
        tabla_admitidos = crear_tabla_procesos_df(df_aceptados, "Procesos Aceptados", "bold green")
        console.print(tabla_admitidos)
    else:
        msg = f"Se rechazaron {len(df_descartados)} proceso(s) por errores en los datos."
        console.print(f"\n[bold red]¡Atención![/bold red] {msg}\n")
        tabla_admitidos = crear_tabla_procesos_df(df_aceptados, "PROCESOS ACEPTADOS", "bold green")
        tabla_rechazados = crear_tabla_rechazados_df(df_descartados, "PROCESOS RECHAZADOS", "bold red")
        console.print(Columns([tabla_admitidos, tabla_rechazados], expand=True))

    # --- PANTALLA 4: Cola de Trabajo ---
    if not df_aceptados.empty:
        pausar_y_limpiar("Presiona Enter para crear la 'Cola de Trabajo' ordenada...")
        
        console.print(f"\n[bold yellow]Ordenando procesos por Tiempo de Arribo (TA) y creando Cola de Trabajo...[/bold yellow]\n")
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
            "COLA DE TRABAJO",
            "bold cyan",
            "yellow"
        )
        console.print(tabla_ct_completa)
        
        console.print(f"\n[bold green]¡Listo![/bold green] La Cola de Trabajo está preparada.")
    else:
        console.print("\n\n[bold yellow]No hay procesos admitidos para la simulación.[/bold yellow]")
        input("\nPresiona Enter para salir.")
        sys.exit()

    pausar_y_limpiar("Presiona Enter para inicia la Simulacion (T = 0)...")

    # --- PANTALLA 5: BUCLE PRINCIPAL DE SIMULACIÓN ---
    
    #VARIABLES DE LAS SIMULACION
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
        # (Pasamos 'T' para que sepa el tiempo de finalización)
        eventos_final, gdm_liberado = procesar_finalizaciones_y_promociones(
            T, cpu, cola_listos, cola_listos_suspendidos, cola_terminados, tabla_particiones
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
                 eventos_T.append("... No hay eventos. Esperando ...")
             elif not colaDeTrabajo:
                 pass
             else:
                 eventos_T.append("Sistema vacío, esperando arribos...")

        # --- 2b. SALIDAS POR PANTALLA ---

        limpiar_pantalla()
        
        console.print(f"[bold white on blue] Instante de Tiempo T = {T} [/bold white on blue]", justify="center")
        console.print()

        # Fila 1: Cola de Trabajo (Izquierda) | Procesos Terminados (Derecha)
        tabla_ct_render = crear_tabla_procesos(colaDeTrabajo, "COLA DE TRABAJO", "bold cyan", "yellow")
        tabla_term_render = crear_tabla_procesos(cola_terminados, "PROCESO TERMINADO", "bold red", "red")
        console.print(Columns([tabla_ct_render, tabla_term_render], expand=True, equal=True))

        console.print()

        console.print(Rule("Simulador"))
        
        if not eventos_T:
             if not colaDeTrabajo and len(cola_listos) == 0 and len(cola_listos_suspendidos) == 0 and cpu.esta_libre():
                 eventos_T.append("... (Simulación estancada, revisando fin) ...")
             else:
                 eventos_T.append("... (Nada que reportar) ...")
        for evento in eventos_T:
            console.print(evento)
            
        console.print()
        
        # Fila 2: Cola de Listos/Suspendidos (Izquierda) | Tabla de Particiones (Derecha)
        tabla_cls_render = crear_tabla_procesos(cola_listos_suspendidos, "COLA DE LISTOS/SUSPENDIDOS", "bold yellow", "yellow")
        tabla_tp_render = crear_tabla_particiones(tabla_particiones)
        console.print(Columns([tabla_cls_render, tabla_tp_render], expand=True, equal=True))
        
        console.print()
        
        # Fila 3: Cola de Listos (Izquierda) | CPU (Derecha)
        tabla_cl_render = crear_tabla_procesos(cola_listos, "COLA DE LISTOS", "bold green", "green")
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
    console.print(Rule("ESTADO FINAL DEL SISTEMA"))    
    console.print(f"[bold green on black]Simulación finalizada en T = {T} [/bold green on black]\n")
    
    # Fila 1: Tabla de Particiones (Izquierda) | Procesos Terminados (Derecha)
    tabla_tp_render = crear_tabla_particiones(tabla_particiones)
    tabla_term_render = crear_tabla_procesos(cola_terminados, "PROCESOS TERMINADOS", "yellow", "green")
    console.print(Columns([tabla_tp_render, tabla_term_render], expand=True, equal=True))

    # Fila 2: Informe Estadístico
    mostrar_informe_estadistico(cola_terminados, T)
    
    input("\nPresiona Enter para salir")

if __name__ == "__main__":
    main()