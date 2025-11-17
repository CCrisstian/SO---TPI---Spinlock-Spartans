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
        
        # --- ETAPA 5: CÁLCULO DEL SIGUIENTE EVENTO ---

        # 1. Calculamos el siguiente candidato de ARRIBO
        proximo_arribo_t = float('inf')
        id_proximo_arribo = None
        
        # Buscamos el proceso con el menor TA que sea mayor al T actual
        candidatos_arribo = [p for p in colaDeTrabajo if p.TA > T]
        if candidatos_arribo:
            # Encontramos el proceso más cercano
            proceso_mas_cercano = min(candidatos_arribo, key=lambda p: p.TA)
            proximo_arribo_t = proceso_mas_cercano.TA
            id_proximo_arribo = proceso_mas_cercano.idProceso

        # 2. Calcular candidato FIN DE CPU
        fin_cpu_t = float('inf')
        id_proceso_cpu = None
        if not cpu.esta_libre():
            fin_cpu_t = T + cpu.tiempo_restante_irrupcion
            id_proceso_cpu = cpu.proceso_en_ejecucion.idProceso

        # 3. Determinar el GANADOR (El evento más cercano)
        proximo_evento_t = float('inf')
        razon_salto = ""
        icono_evento = ""

        if proximo_arribo_t < fin_cpu_t:
            # Gana el Arribo
            proximo_evento_t = proximo_arribo_t
            razon_salto = f"Arribo del proceso {id_proximo_arribo}"
            icono_evento = "[green]➔ [/green]"
        elif fin_cpu_t < proximo_arribo_t:
            # Gana el Fin de CPU
            proximo_evento_t = fin_cpu_t
            razon_salto = f"Fin de del proceso {id_proceso_cpu} en CPU"
            icono_evento = "[red]➔ [/red]"
        elif proximo_arribo_t == fin_cpu_t and proximo_arribo_t != float('inf'):
            # Empate (Simultáneos)
            proximo_evento_t = proximo_arribo_t
            razon_salto = f"Arribo P{id_proximo_arribo} y Fin CPU P{id_proceso_cpu}"
            icono_evento = "[yellow]➔ [/yellow]"
        else:
            # No hay eventos futuros definidos (solo queda avanzar por defecto)
            razon_salto = "Paso de tiempo (Sin eventos)"
            icono_evento = "[grey]➔ [/grey]"

        # 4. Calcular la magnitud del salto
        if proximo_evento_t == float('inf'):
             salto_tiempo = 1
        else:
             salto_tiempo = proximo_evento_t - T
        
        if salto_tiempo < 1: 
            salto_tiempo = 1
            razon_salto = "Continuar ejecución"

        # --- Lógica de Mensajes de Espera (Ahora mucho más clara) ---
        if not eventos_final and not eventos_arribo and not eventos_srtf and not eventos_swap:
             # Agregamos el mensaje informativo al log de eventos para que se vea en el centro
             msg_avance = f"{icono_evento} Avanzamos [bold]{salto_tiempo} u.t.[/bold] porque esperamos: [bold]{razon_salto}[/bold]"
             eventos_T.append(msg_avance)

        # --- 2b. SALIDAS POR PANTALLA ---

        limpiar_pantalla()

        # Fila 1: Cola de Trabajo (Izquierda) | Procesos Terminados (Derecha)
        tabla_ct_render = crear_tabla_procesos(colaDeTrabajo, "COLA DE TRABAJO", "bold cyan", "yellow")
        tabla_term_render = crear_tabla_procesos(cola_terminados, "PROCESO TERMINADO", "bold red", "red")
        console.print(Columns([tabla_ct_render, tabla_term_render], expand=True, equal=True))

        console.print(Rule("Simulador"))
        console.print(f"[bold white on blue] \nInstante de Tiempo T = {T} [/bold white on blue]\n", justify="center")
        
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
            console.print("\n[bold green]\n\n Finalizaron todos los procesos :). [/bold green]")
            input("Presione 'Enter' para realizar el informe estadístico.")
            limpiar_pantalla()
            
            break

        # --- Pausa y Actualización de T ---
        try:
            mensaje_input = (
                f"\n[bold cyan]Próximo Evento:[/bold cyan] {razon_salto}\n"
                f"Presione Enter para avanzar [bold]{salto_tiempo} u.t.[/bold] (T -> {T + salto_tiempo})..."
            )
            console.print(mensaje_input, end="")
            input()
        except KeyboardInterrupt:
            console.print("\n[red]Simulación interrumpida por el usuario.[/red]")
            sys.exit()
            
        ejecutar_tick_cpu(cpu, unidades=salto_tiempo)

        # APLICAMOS EL SALTO
        T += salto_tiempo

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