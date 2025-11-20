from importaciones import List
from clases import *
from varGlobal import GRADO_MAX_MULTIPROGRAMACION
# Este archivo contiene las funciones puras que deciden cómo se mueven los procesos 
# entre colas, memoria y CPU (Planificación a Corto y Mediano Plazo).
def buscar_particion_best_fit(proceso: Proceso, particiones: List[Particion]) -> int:
    mejor_particion_idx = -1                #Algoritmo de asignación de memoria BEST-FIT.
    min_fragmentacion = float('inf')        #Retorna el índice de la partición o -1 si no hay lugar.

    for i, part in enumerate(particiones):
        if part.id_part == "SO":            # Ignorar partición del Sistema Operativo
            continue
        if part.id_proceso is None and proceso.tamProceso <= part.tamano:        # Si está libre y el proceso entra:
            fragmentacion = part.tamano - proceso.tamProceso
            if fragmentacion < min_fragmentacion:               # ¿Es esta partición más ajustada que la que encontramos antes?
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
) -> tuple[List[str], int]:         #Etapa 1 del Ciclo: Verifica si el proceso en CPU terminó su tiempo de irrupción. Si termina:
    eventos = []                    # 1. Calcula tiempos estadísticos (tiempo de Retorno y tiemnpo de Espera).
    gdm_liberado = 0                # 2. Libera la CPU y la Partición de Memoria.
                                    # 3. Intenta 'Promocionar' (Swapp In) un proceso de Suspendidos a la memoria liberada.
    if not cpu.esta_libre() and cpu.tiempo_restante_irrupcion <= 0:
        proceso_actual = cpu.proceso_en_ejecucion
        eventos.append(f"[red]FINALIZACIÓN[/red] del proceso [bold]{proceso_actual.idProceso}[/bold].")
        proceso_actual.estado = "TERMINADO"
        # --- Cálculo de Estadísticas ---
        # T = Instante actual (Finalización)
        proceso_actual.tiempo_finalizacion = T 
        proceso_actual.tiempo_retorno = proceso_actual.tiempo_finalizacion - proceso_actual.TA_paraCalculo
        proceso_actual.tiempo_espera = proceso_actual.tiempo_retorno - proceso_actual.TI_original
        
        cola_terminados.append(proceso_actual)
        gdm_liberado = 1 # Se libera un espacio en el Grado de Multiprogramación
        cpu.proceso_en_ejecucion = None             # Liberar CPU
        cpu.tiempo_restante_irrupcion = 0           
        particion_liberada_idx = -1                 # Busca qué partición tenía este proceso para liberar la memoria
        for i, part in enumerate(particiones):
            if part.id_proceso == proceso_actual.idProceso:
                part.id_proceso = None
                part.fragmentacion = 0
                particion_liberada_idx = i
                eventos.append(f"    -> Partición [bold]{part.id_part}[/bold] liberada.")
                break
        # --- Lógica de Promoción (Swap In) ---
        if particion_liberada_idx != -1:    
            particion_liberada = particiones[particion_liberada_idx]
            mejor_candidato_ls = None                                   # Promoción basada en SRTF
            mejor_ti = float('inf')
            # Buscamos en la cola de Suspendidos el mejor candidato que quepa en la partición que se acaba de liberar
            for proc_ls in cola_ls:
                if proc_ls.tamProceso <= particion_liberada.tamano:
                    if proc_ls.TI < mejor_ti:
                        mejor_ti = proc_ls.TI
                        mejor_candidato_ls = proc_ls
            
            if mejor_candidato_ls:      # Si encontramos a alguien, lo traemos a Memoria
                if not mejor_candidato_ls.es_primer_arribo_listos:  # Capturar Tiempo Arribo A LISTOS, si es la primera vez
                    mejor_candidato_ls.TA_paraCalculo = T
                    mejor_candidato_ls.es_primer_arribo_listos = True

                mejor_candidato_ls.estado = "LISTO"
                cola_l.append(mejor_candidato_ls)
                cola_ls.remove(mejor_candidato_ls)
                
                particion_liberada.id_proceso = mejor_candidato_ls.idProceso        
                particion_liberada.fragmentacion = particion_liberada.tamano - mejor_candidato_ls.tamProceso 
                
                eventos.append(
                    f"[cyan]PROMOCIÓN (Listos/Suspendidos -> Listos)[/cyan] del[bold] proceso {mejor_candidato_ls.idProceso}[/bold]; "
                    f"Se lo asignó a la partición [bold]{particion_liberada.id_part}[/bold]."
                )            
    return eventos, gdm_liberado

def procesar_arribos(
    T: int,                         # Si el entra a Listos directamente, guardamos T en TA_paraCalculo.
    colaDeTrabajo: List[Proceso], 
    cola_l: List[Proceso], 
    cola_ls: List[Proceso], 
    particiones: List[Particion],
    cpu: Cpu,
    procesos_en_simulador_count: int
) -> tuple[List[str], int]:     # Etapa 3: Maneja la llegada de procesos nuevos en el tiempo T actual.
    eventos = []    # El planificador a Largo Plazo decide si el proceso va a Memoria (Listo) o a Disco (Listo/Suspendido).
    gdm_agregado = 0
    # Filtrar procesos cuyo Tiempo de Arribo (TA) sea menor o igual al tiempo actual
    procesos_llegados_en_T = [p for p in colaDeTrabajo if p.TA <= T]
        
    if procesos_llegados_en_T:
        procesos_llegados_en_T.sort(key=lambda p: (p.TA, p.idProceso))  # Ordenar por TA para procesar en orden
        
        for proceso_llegado in procesos_llegados_en_T:          
            if (procesos_en_simulador_count + gdm_agregado) < GRADO_MAX_MULTIPROGRAMACION:      # Verifica GRADO DE MULTIPROGRAMACIÓN
                idx_particion = buscar_particion_best_fit(proceso_llegado, particiones)         # Intento asignar memoria
                
                if idx_particion != -1:
                    particion_asignada = particiones[idx_particion]     # CASO 1: Entra en Memoria -> Cola de Listos
                    proceso_llegado.TA_paraCalculo = T
                    proceso_llegado.es_primer_arribo_listos = True

                    eventos.append(f"[green]ARRIBO [/green]del proceso [bold]{proceso_llegado.idProceso}[/bold], ingresó a memoria y fue asignado a la partición [bold]{particion_asignada.id_part}[/bold].")
                    proceso_llegado.estado = "LISTO"
                    cola_l.append(proceso_llegado)
                    colaDeTrabajo.remove(proceso_llegado)
                    particion_asignada.id_proceso = proceso_llegado.idProceso
                    particion_asignada.fragmentacion = particion_asignada.tamano - proceso_llegado.tamProceso
                else:       # CASO 2: No hay partición disponible -> Listos/Suspendidos
                    eventos.append(f"[green]ARRIBO [/green]del proceso [bold]{proceso_llegado.idProceso}[/bold], [yellow]no existe memoria suficiente [/yellow]para albergarlo entonces pasa a 'Listos/Suspendidos'.")
                    proceso_llegado.estado = "LISTO Y SUSPENDIDO"
                    cola_ls.append(proceso_llegado)
                    colaDeTrabajo.remove(proceso_llegado)
                
                gdm_agregado += 1
            else:       #CASO 3: Sistema saturado (GDM Máximo) -> Esperar afuera
                eventos.append(f"[yellow]ARRIBO BLOQUEADO[/yellow] del proceso [bold]{proceso_llegado.idProceso}[/bold], se alcanzó el grado máximo de multiprogramación ({GRADO_MAX_MULTIPROGRAMACION}). Proceso en espera.")

    return eventos, gdm_agregado

def gestor_cpu_srtf(
    cpu: Cpu, 
    cola_l: List[Proceso]
) -> List[str]:
    eventos = []                            # Planificador a Corto Plazo con algoritmo SRTF

    cola_l.sort(key=lambda p: p.TI)         # 1. Ordena la Cola de Listos por tiempo de irrupción
    
    if cpu.esta_libre() and cola_l:         # CASO A: CPU Libre -> Cargamos el primero de la lista (el más corto)
        proceso_a_cargar = cola_l.pop(0) 
        proceso_a_cargar.estado = "EN EJECUCIÓN"
        cpu.proceso_en_ejecucion = proceso_a_cargar
        cpu.tiempo_restante_irrupcion = proceso_a_cargar.TI
        eventos.append(f"[magenta]CARGA [/magenta]del proceso [bold]{proceso_a_cargar.idProceso}[/bold] con TI = {proceso_a_cargar.TI} a la CPU.")
    # CASO B: APROPIACIÓN. Si la CPU está ocupada, comprobamos si el mejor de la cola de listos es MEJOR que el actual.
    elif not cpu.esta_libre() and cola_l:
        proceso_en_cpu = cpu.proceso_en_ejecucion
        proceso_mas_corto_listo = cola_l[0]     # El candidato retador
        
        # Comparacion: ¿Es el nuevo estrictamente más corto que lo que le falta al actual?
        if proceso_mas_corto_listo.TI < cpu.tiempo_restante_irrupcion:
            eventos.append(         # Si ocurre la apropiacion
                f"[magenta]SRTF APROPIACION:[/magenta] Proceso [bold]{proceso_mas_corto_listo.idProceso}[/bold] con TI = {proceso_mas_corto_listo.TI} "
                f"desaloja al Proceso [bold]{proceso_en_cpu.idProceso}[/bold] con TI = {cpu.tiempo_restante_irrupcion}."
            )
            
            proceso_en_cpu.estado = "LISTO"                     # El actual vuelve a 'Listo'
            proceso_en_cpu.TI = cpu.tiempo_restante_irrupcion   # Guardamos su progreso
            cola_l.append(proceso_en_cpu)
            proceso_nuevo = cola_l.pop(0)                       # El nuevo sube a CPU
            proceso_nuevo.estado = "EN EJECUCIÓN"
            cpu.proceso_en_ejecucion = proceso_nuevo
            cpu.tiempo_restante_irrupcion = proceso_nuevo.TI
    return eventos          # Si no fuera el más corto, el proceso en CPU continúa tranquilamente.

def ejecutar_tick_cpu(cpu: Cpu, unidades: int = 1):  # Avanza el reloj interno de la CPU, descontando ráfaga al proceso actual
    if not cpu.esta_libre():
        cpu.tiempo_restante_irrupcion -= unidades       # Descontamos el tiempo que pasó (el salto)

        if cpu.tiempo_restante_irrupcion < 0:           # Proceso de seguridad para evitar numeros negativos
            cpu.tiempo_restante_irrupcion = 0

        cpu.proceso_en_ejecucion.TI = cpu.tiempo_restante_irrupcion     # Sincronizamos el objeto proceso con el estado de la CPU

def gestor_intercambio_swap(
    T: int,                     # Si entra a Listos por Swap, guardamos T en TA_paraCalculo
    cola_l: List[Proceso], 
    cola_ls: List[Proceso], 
    particiones: List[Particion],
    cpu: Cpu
) -> List[str]:                     # Planificador a Mediano Plazo (Swapping). Si hay procesos suspendidos que tienen
    eventos = []                    # menor TI que los que están en Memoria ocupando lugar, se realiza un intercambio.
    if not cola_ls:         
        return eventos              # No hay nadie en disco queriendo entrar.

    cola_ls.sort(key=lambda p: p.TI)        # 1. Encontrar al mejor "Candidato" en disco (el más corto)
    candidato = cola_ls[0]
    
    victima = None                          # 2. Encontrar "Víctima" en Memoria para echarla
    particion_victima = None                # Criterio: Buscamos al proceso con MAYOR TI que no esté en CPU.
    ti_victima_max = -1 

    particiones_trabajo = [p for p in particiones if p.id_part != "SO"]
    
    for part in particiones_trabajo:
        if part.id_proceso is None: # Si está vacía, no es swap, es carga normal
            continue
        if not cpu.esta_libre() and part.id_proceso == cpu.proceso_en_ejecucion.idProceso:
            continue                # No se echa al proceso que está usando la CPU, se lo continua ejecutando

        proceso_en_particion = None             # Buscamos el objeto proceso asociado a esta partición
        for p_listo in cola_l:
             if p_listo.idProceso == part.id_proceso:
                 proceso_en_particion = p_listo
                 break

        if proceso_en_particion:                # Si lo encontramos, evaluamos si es la peor víctima (TI más grande)
            if proceso_en_particion.TI > ti_victima_max:
                ti_victima_max = proceso_en_particion.TI
                victima = proceso_en_particion
                particion_victima = part
                                                                # 3. ¿Vale la pena el intercambio?
    if victima and candidato.TI < victima.TI:                   # Solo si el candidato de disco tiene menor TI que la víctima en RAM.
        if candidato.tamProceso <= particion_victima.tamano:    # Y si cabe físicamente
            if not candidato.es_primer_arribo_listos:
                candidato.TA_paraCalculo = T                    # Capturar Tiempo Arribo A LISTOS, si es la primera vez
                candidato.es_primer_arribo_listos = True

            eventos.append(             # Se ejecuta el SWAP OUT                  
                f"[red]SWAP OUTt:[/red] Proceso [bold]{victima.idProceso}[/bold] (TI = {victima.TI}) "
                f"sale de la Partición '{particion_victima.id_part}' y va a 'Listos/Suspendidos'."
            )
            cola_l.remove(victima)
            victima.estado = "LISTO Y SUSPENDIDO"
            cola_ls.append(victima)

            eventos.append(             # Se ejecuta el SWAP OUT  
                f"[green]SWAP IN:[/green] Proceso [bold]{candidato.idProceso}[/bold] (TI = {candidato.TI}) "
                f"entra a la Partición '{particion_victima.id_part}'."
            )
            cola_ls.remove(candidato)
            candidato.estado = "LISTO"
            cola_l.append(candidato)
            particion_victima.id_proceso = candidato.idProceso
            particion_victima.fragmentacion = particion_victima.tamano - candidato.tamProceso
    return eventos