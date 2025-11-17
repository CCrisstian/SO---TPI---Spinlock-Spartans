from importaciones import *
from varGlobal import *
from tratarProcesos import cargarProcesos, filtrarProcesos, crearColaDeTrabajo

def main():
    pantallaInicial()
    procesos = cargarProcesos()
    procesos_aceptados = filtrarProcesos(procesos)
    colaDeTrabajo = crearColaDeTrabajo(procesos_aceptados)

    # ---> SIMULACIÓN PRINCIPAL <---
    # VARIABLES DE LAS SIMULACION

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
            console.print("\n[bold red]   --->>> Todos los procesos finalizaron con éxito. <<<---   [/bold red]")
            time.sleep(3)
            limpiar_pantalla()
            
            break

        # --- Pausa para avanzar T ---
        try:
            input(f"\nPresione Enter para avanzar a T = {T+1}...")
        except KeyboardInterrupt:
            console.print("\n[red]Simulación interrumpida por el usuario.[/red]")
            sys.exit()
            
        T += 1
    # --- Fin de la simulación ---


    # limpiar_pantalla()
    # console.print(Rule("ESTADO FINAL DEL SISTEMA"))
    console.print(f"[bold green on black]\nSimulación finalizada en T = {T} [/bold green on black]\n")
    
    # Fila 1: Tabla de Particiones (Izquierda) | Procesos Terminados (Derecha)
    # tabla_tp_render = crear_tabla_particiones(tabla_particiones)
    # tabla_term_render = crear_tabla_procesos(cola_terminados, "PROCESOS TERMINADOS", "yellow", "green")
    # console.print(Columns([tabla_tp_render, tabla_term_render], expand=True, equal=True))

    # Fila 2: Informe Estadístico
    mostrar_informe_estadistico(cola_terminados, T)
    
    input("\nPresiona Enter para salir")

if __name__ == "__main__":
    main()