from importaciones import List
from clases import *
from varGlobal import GRADO_MAX_MULTIPROGRAMACION

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
        eventos.append(f"[red]FINALIZÓ[/red] el proceso [bold]{proceso_actual.idProceso}[/bold].")
        
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
                    f"[cyan]PROMOCIÓN (Listos/Suspendidos -> Listos)[/cyan] del[bold] proceso {mejor_candidato_ls.idProceso}[/bold]; "
                    f"Se lo asignó a la partición [bold]{particion_liberada.id_part}[/bold]."
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
                    eventos.append(f"[green]ARRIBO [/green]del proceso [bold]{proceso_llegado.idProceso}[/bold], ingresó a memoria y fue asignado a la partición [bold]{particion_asignada.id_part}[/bold].")
                    proceso_llegado.estado = "Listo"
                    cola_l.append(proceso_llegado)
                    colaDeTrabajo.remove(proceso_llegado)
                    particion_asignada.id_proceso = proceso_llegado.idProceso
                    particion_asignada.fragmentacion = particion_asignada.tamano - proceso_llegado.tamProceso
                else:
                    eventos.append(f"[green]ARRIBO [/green]del proceso [bold]{proceso_llegado.idProceso}[/bold]; [yellow]No existe memoria suficiente [/yellow]para albergarlo entonces pasa a 'Listos/Suspendidos'.")
                    proceso_llegado.estado = "Listo y Suspendido"
                    cola_ls.append(proceso_llegado)
                    colaDeTrabajo.remove(proceso_llegado)
                
                gdm_agregado += 1
            else:
                eventos.append(f"[yellow]Arribo Bloqueado[/yellow] del proceso [bold]{proceso_llegado.idProceso}[/bold], se alcanzó el grado máximo de multiprogramación ({GRADO_MAX_MULTIPROGRAMACION}). Proceso en espera.")

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
        eventos.append(f"[magenta]CARGA [/magenta]del proceso [bold]{proceso_a_cargar.idProceso}[/bold] con TI = {proceso_a_cargar.TI} a la CPU.")

    # 2. Lógica de APROPIACIÓN (cuando la CPU está OCUPADA)
    elif not cpu.esta_libre() and cola_l:
        proceso_en_cpu = cpu.proceso_en_ejecucion
        proceso_mas_corto_listo = cola_l[0]     # El mejor de la Cola de Listos
        
        # Comprobar si hay un Proceso en "Listos" con un TI más corto que el *TI restante* del Proceso en CPU
        if proceso_mas_corto_listo.TI < cpu.tiempo_restante_irrupcion:
            # El nuevo es MÁS CORTO
            # Ocurre la apropiación
            eventos.append(
                f"[magenta]SRTF Apropiación:[/magenta] Proceso [bold]{proceso_mas_corto_listo.idProceso}[/bold] con TI = {proceso_mas_corto_listo.TI} "
                f"desaloja al Proceso [bold]{proceso_en_cpu.idProceso}[/bold] con TR = {cpu.tiempo_restante_irrupcion}."
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

def ejecutar_tick_cpu(cpu: Cpu, unidades: int = 1):
    # Descuenta unidades de tiempo a la ráfaga del proceso en CPU.
    
    if not cpu.esta_libre():
        # Descontamos el tiempo que pasó (el salto)
        cpu.tiempo_restante_irrupcion -= unidades
        
        # Por seguridad, evitamos negativos (aunque la lógica de MAIN debería prevenirlo)
        if cpu.tiempo_restante_irrupcion < 0:
            cpu.tiempo_restante_irrupcion = 0
            
        # Actualizamos el TI del objeto Proceso para que SRTF y las tablas vean el valor actual
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
