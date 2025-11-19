from importaciones import *
from varGlobal import *
from tratarProcesos import cargarProcesos, filtrarProcesos, crearColaDeTrabajo

# --- FUNCIÓN PRINCIPAL (MAIN) ---
#  En este archivo se ejecuta la simulación principal y se realizan los saltos de tiempo para ir por eventos.

def main():
    pantallaInicial()
    
    # --- FASE DE CARGA Y PREPARACIÓN ---
    procesos = cargarProcesos()
    procesos_aceptados = filtrarProcesos(procesos)
    colaDeTrabajo = crearColaDeTrabajo(procesos_aceptados)

    # --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
    T = 0 # Tiempo actual
    
    # Colas de estados de procesos
    cola_listos_suspendidos: List[Proceso] = [] # Procesos en la memoria secundaria
    cola_listos: List[Proceso] = []             # Procesos en la memoria principal
    cola_terminados: List[Proceso] = []         # Procesos terminados
    
    procesos_totales_count = len(colaDeTrabajo)
    procesos_terminados_count = 0
    procesos_en_simulador_count = 0 # Controla el Grado de Multiprogramación actual
    
    cpu = Cpu()
    
    # Definición de Particiones Fijas
    tabla_particiones: List[Particion] = [
        Particion(id_part="SO", dir_inicio=0, tamano=100, id_proceso="SO"),
        Particion(id_part="Grandes", dir_inicio=100, tamano=250),
        Particion(id_part="Medianos", dir_inicio=350, tamano=150),
        Particion(id_part="Pequeños", dir_inicio=500, tamano=50)
    ]
    
    # --- BUCLE PRINCIPAL DE SIMULACIÓN ---
    # Se ejecuta mientras existan procesos pendientes de finalizar.
    while procesos_terminados_count < procesos_totales_count:
        
        eventos_T = [] # Lista con los logs de eventos ocurridos en este instante T
        
        # --- ETAPA 1: Finalización de Procesos ---
        # Verificamos si el proceso en CPU ha terminado su ráfaga justo ahora.
        eventos_final, gdm_liberado = procesar_finalizaciones_y_promociones(
            T, cpu, cola_listos, cola_listos_suspendidos, cola_terminados, tabla_particiones
        )
        if eventos_final:
            eventos_T.extend(eventos_final)
            procesos_terminados_count += gdm_liberado
            procesos_en_simulador_count -= gdm_liberado 

        # --- ETAPA 2: Intercambio ---
        # Si la memoria está llena, verificamos si alguien en Disco (Suspendido)
        # tiene mayor prioridad (menos TI) que alguien en RAM para hacer un swapp.
        eventos_swap = gestor_intercambio_swap(
            cola_listos, cola_listos_suspendidos, tabla_particiones, cpu
        )
        if eventos_swap:
            eventos_T.extend(eventos_swap)

        # --- ETAPA 3: Arribo de Nuevos Procesos ---
        # Ingresan procesos cuyo TA coincide con T.
        # Se asignan a memoria (si hay lugar) o a disco (si no).
        eventos_arribo, gdm_agregado = procesar_arribos(
            T, colaDeTrabajo, cola_listos, cola_listos_suspendidos, 
            tabla_particiones,
            cpu, 
            procesos_en_simulador_count 
        )
        if eventos_arribo:
            eventos_T.extend(eventos_arribo)
            procesos_en_simulador_count += gdm_agregado

        # --- ETAPA 4: Planificación de CPU con algoritmo SRTF ---
        eventos_srtf = gestor_cpu_srtf(cpu, cola_listos)
        if eventos_srtf:
            eventos_T.extend(eventos_srtf)
        
        # --- ETAPA 5: CÁLCULO DEL PRÓXIMO EVENTO ---
        # En lugar de avanzar T de 1 en 1 (lo cual sería lento si no pasa nada),
        # calculamos cuándo ocurrirá el próximo evento importante para saltar directo a él.

        # A. ¿Cuándo es el próximo ARRIBO?
        proximo_arribo_t = float('inf')
        id_proximo_arribo = None
        candidatos_arribo = [p for p in colaDeTrabajo if p.TA > T]
        if candidatos_arribo:
            proceso_mas_cercano = min(candidatos_arribo, key=lambda p: p.TA)
            proximo_arribo_t = proceso_mas_cercano.TA
            id_proximo_arribo = proceso_mas_cercano.idProceso

        # B. ¿Cuándo termina el proceso actual en CPU?
        fin_cpu_t = float('inf')
        id_proceso_cpu = None
        if not cpu.esta_libre():
            fin_cpu_t = T + cpu.tiempo_restante_irrupcion
            id_proceso_cpu = cpu.proceso_en_ejecucion.idProceso

        # C. Determinar el GANADOR (El evento más cercano)
        proximo_evento_t = float('inf')
        razon_salto = ""
        icono_evento = ""

        if proximo_arribo_t < fin_cpu_t:
            proximo_evento_t = proximo_arribo_t
            razon_salto = f"Arribo del proceso {id_proximo_arribo}"
            icono_evento = "[green]➔ [/green]"
        elif fin_cpu_t < proximo_arribo_t:
            proximo_evento_t = fin_cpu_t
            razon_salto = f"Fin de del proceso {id_proceso_cpu} en CPU"
            icono_evento = "[red]➔ [/red]"
        elif proximo_arribo_t == fin_cpu_t and proximo_arribo_t != float('inf'):
            proximo_evento_t = proximo_arribo_t
            razon_salto = f"Arribo P{id_proximo_arribo} y Fin CPU P{id_proceso_cpu}"
            icono_evento = "[yellow]➔ [/yellow]"
        else:
            razon_salto = "Paso de tiempo (Sin eventos)"
            icono_evento = "[grey]➔ [/grey]"

        # D. Calcular la magnitud del salto
        if proximo_evento_t == float('inf'):
             salto_tiempo = 1 # Si no hay eventos futuros, avanzamos de a 1
        else:
             salto_tiempo = proximo_evento_t - T
        
        if salto_tiempo < 1: 
            salto_tiempo = 1
            razon_salto = "Continuar ejecución"

        # Feedback visual si "no pasó nada" importante en este ciclo pero avanzamos
        if not eventos_final and not eventos_arribo and not eventos_srtf and not eventos_swap:
             msg_avance = f"{icono_evento} Avanzamos [bold]{salto_tiempo} u.t.[/bold] porque esperamos: [bold]{razon_salto}[/bold]"
             eventos_T.append(msg_avance)

        # --- RENDERIZADO POR PANTALLA ---

        limpiar_pantalla()

        # Fila 1: Cola de Trabajo vs Terminados
        tabla_ct_render = crear_tabla_procesos(colaDeTrabajo, "COLA DE TRABAJO", "bold cyan", "yellow")
        tabla_term_render = crear_tabla_procesos(cola_terminados, "PROCESO TERMINADO", "bold red", "red")
        console.print(Columns([tabla_ct_render, tabla_term_render], expand=True, equal=True))
        console.print()
        
        console.print(Rule("Simulador"))
        console.print(f"[bold white on blue] \nInstante de Tiempo T = {T} [/bold white on blue]\n", justify="center")
        
        # Impresión de Logs de Eventos
        if not eventos_T:
             if not colaDeTrabajo and len(cola_listos) == 0 and len(cola_listos_suspendidos) == 0 and cpu.esta_libre():
                 eventos_T.append("... (Simulación estancada, revisando fin) ...")
             else:
                 eventos_T.append("... (Nada que reportar) ...")
        for evento in eventos_T:
            console.print(evento)
            
        console.print()
        
        # Fila 2: Listos/Suspendidos vs Memoria
        tabla_cls_render = crear_tabla_procesos(cola_listos_suspendidos, "COLA DE LISTOS/SUSPENDIDOS", "bold yellow", "yellow")
        tabla_tp_render = crear_tabla_particiones(tabla_particiones)
        console.print(Columns([tabla_cls_render, tabla_tp_render], expand=True, equal=True))
        
        console.print()
        
        # Fila 3: Listos vs CPU
        tabla_cl_render = crear_tabla_procesos(cola_listos, "COLA DE LISTOS", "bold green", "green")
        tabla_cpu_render = crear_tabla_cpu(cpu)
        console.print(Columns([tabla_cl_render, tabla_cpu_render], expand=True, equal=True))
        
        # Comprobar condición de salida
        if procesos_terminados_count >= procesos_totales_count:
            console.print("\n[bold green]\n\n Finalizaron todos los procesos :). [/bold green]")
            input("Presione 'Enter' para realizar el informe estadístico.")
            limpiar_pantalla()
            break

        # Input del usuario para avanzar al siguiente paso
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
            
        # --- AVANCE DEL RELOJ ---
        ejecutar_tick_cpu(cpu, unidades=salto_tiempo) # Descontamos ráfaga en CPU
        T += salto_tiempo # Avanzamos el tiempo global

    # --- FIN DE LA SIMULACIÓN Y REPORTE ---
    
    console.print(f"[bold green on black]\nSimulación finalizada en T = {T} [/bold green on black]\n")
    
    # Estado final de particiones y terminados
    tabla_tp_render = crear_tabla_particiones(tabla_particiones)
    tabla_term_render = crear_tabla_procesos(cola_terminados, "PROCESOS TERMINADOS", "yellow", "green")
    console.print(Columns([tabla_tp_render, tabla_term_render], expand=True, equal=True))
    console.print()
    
    # Generación de Estadísticas
    mostrar_informe_estadistico(cola_terminados, T)
    
    input("\nPresiona Enter para salir")

if __name__ == "__main__":
    main()