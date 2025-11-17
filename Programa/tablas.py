from rich.table import Table, Column
from varGlobal import console
from clases import *
from importaciones import box, List, pd


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