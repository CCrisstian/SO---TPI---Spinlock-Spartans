from rich.table import Table, Column
from varGlobal import console
from clases import *
from importaciones import box, List, pd

# Este archivo se encarga exclusivamente de generar las tablas visuales utilizando la librería 'rich'
# para mostrar el estado del sistema en la consola.
# La mayoria de los nombres son autoexplicativos.

def crear_tabla_procesos_df(df_procs, titulo_tabla, estilo_header):     # Toma un DataFrame de PANDAS (usado en la carga inicial) y devuelve un objeto Table de rich.
    tabla = Table(                                                      # Se utiliza para mostrar la lista cruda de procesos antes de la simulación.
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

def crear_tabla_rechazados_df(df_procs, titulo_tabla, estilo_header):   # Acá se genera la tabla específica para los procesos 
    tabla = Table(                                                      # que no pasaron los diferentes filtros.
        title=titulo_tabla,                                             # Incluye una columna extra 'RAZON DE RECHAZO'.
        box=box.ROUNDED,
        show_header=True,
        header_style=estilo_header
    )
    tabla.add_column("ID", justify="center")
    tabla.add_column("TAMAÑO", justify="center")
    tabla.add_column("ARRIBO", justify="center")
    tabla.add_column("IRRUPCION", justify="center")
    tabla.add_column("RAZON DE RECHAZO", justify="center", style="yellow")

    for index, row in df_procs.iterrows():          # Uso de .get() para evitar errores si falta algun dato en el CSV corrupto
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
    estilo_estado: str
) -> Table:                             # Creo una tabla dinámica basada en una Lista de objetos 'Proceso'.
    tabla = Table(                      # Se utiliza durante la simulación para mostrar: 
        title=titulo,                   # Cola de Listos, Suspendidos y Terminados.
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
        tabla.add_row("Vacía...", "-", "-", "-", "-")       # En caso de que no haya nada que mostrar
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
    tabla = Table(                          # Se crea la tabla que permite visualizar el estado de la Memoria Principal.
        title="PARTICIONES DE MEMORIA",     # Muestra qué proceso ocupa qué partición y su fragmentación interna.
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan"
    )
    tabla.add_column("ID PARTICION", justify="center")
    tabla.add_column("DIR. INICIAL", justify="center")
    tabla.add_column("TAMAÑO", justify="center")
    tabla.add_column("ID PROCESO", justify="center")
    tabla.add_column("FRAG. INTERNA", justify="center")

    for p in particiones:               # Resaltar la partición del Sistema Operativo
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

def crear_tabla_cpu(cpu: Cpu) -> Table:         # Tabla del proceso que está actualmente en ejecución en la CPU
    tabla = Table(                              # y su tiempo restante de irrupción.
        title="CPU",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta"
    )
    tabla.add_column("ID PROCESO", justify="center")
    tabla.add_column("ESTADO", justify="center")
    tabla.add_column("TIEMPO RESTANTE", justify="center")

    if cpu.esta_libre():
        tabla.add_row("LIBRE", "-", "-")
    else:
        tabla.add_row(
            str(cpu.proceso_en_ejecucion.idProceso),
            "[magenta]EN EJECUCIÓN[/magenta]",
            str(cpu.tiempo_restante_irrupcion)
        )
    return tabla