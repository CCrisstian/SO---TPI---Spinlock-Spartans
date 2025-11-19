from varGlobal import console
from importaciones import *

# Calcula y muestra la tabla de estadísticas finales y promedios.
def mostrar_informe_estadistico(procesos_terminados: List[Proceso], tiempo_total: int):

    console.print(Rule("\n\nInforme Estadístico Final\n"))

    # 1. Crear Tabla de Tiempos por Proceso
    tabla_tiempos = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold green"
    )
    tabla_tiempos.add_column("ID", justify="center")
    tabla_tiempos.add_column("TA (Sistema)", justify="center") # TA Original
    tabla_tiempos.add_column("TA (Listos)", justify="center")  # TA para Calculo
    tabla_tiempos.add_column("T. Irrupción (TI)", justify="center")
    tabla_tiempos.add_column("T. Finalización (TF)", justify="center")
    tabla_tiempos.add_column("T. Retorno (TR = TF - TA)", justify="center")
    tabla_tiempos.add_column("T. Espera (TE = TR - TI)", justify="center")

    tiempos_retorno = []
    tiempos_espera = []

    # Ordenar por ID
    procesos_terminados.sort(key=lambda p: p.idProceso)

    # cargamos los procesos en la tabla creada
    for proc in procesos_terminados:
        tabla_tiempos.add_row(
            str(proc.idProceso),
            str(proc.TA),               # TA Original
            str(proc.TA_paraCalculo),   # TA para calculo
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
    
    tabla_promedios.add_row("Tiempo de Simulación Total", f"{tiempo_total} u.t.")
    tabla_promedios.add_row("Tiempo de Retorno Promedio (TRP)", f"[cyan]{trp:.2f} u.t.[/cyan]")
    tabla_promedios.add_row("Tiempo de Espera Promedio (TEP)", f"[yellow]{tep:.2f} u.t.[/yellow]")
    tabla_promedios.add_row("Rendimiento del Sistema", f"[green]{rendimiento:.3f} procesos/u.t.[/green]")
    
    console.print(tabla_promedios, justify="left")

