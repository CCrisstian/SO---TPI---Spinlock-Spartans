from varGlobal import console, MAX_MEMORIA
from importaciones import *

# Máximo tiempo permitido, ya sea de irrupción o de arribo.
MAX_VALOR_PERMITIDO = 10000

def cargarProcesos():
    """
    Localiza y lee el archivo 'procesos.csv'.
    Maneja errores de ruta o archivo no encontrado.
    """
    # --- PANTALLA 2: Procesos Leídos ---
    # Rutas relativas para encontrar el CSV independientemente de dónde se instale el proyecto
    carpeta_programa = os.path.dirname(os.path.abspath(__file__))
    carpeta_raiz = os.path.dirname(carpeta_programa)
    archivo_CSV = os.path.join(carpeta_raiz, "ArchivosEjemplo", "procesos.csv")

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
    
    return df_procesos

def filtrarProcesos(df_procesos):
    """
    Aplica filtros para validar los datos.
    Genera dos DataFrames: Aceptados (para simulación) y Rechazados (para reporte).
    """
    # --- PANTALLA 3: Filtrado y Resultados ---
    console.print(f"\n[bold yellow]Se realizará un filtrado y validación de los procesos cargados. [/bold yellow]")
    numeric_cols = ['Tamaño', 'Arribo', 'Irrupcion']    
    
    # Trabajamos sobre una copia para no alterar la lectura original
    df_validado = df_procesos.copy()
    df_validado['Rechazo_Razon'] = ''

    # 1. FILTRO: El ID no puede estar vacío
    mask_id_vacio = df_validado['ID'].isnull()
    df_validado.loc[mask_id_vacio, 'Rechazo_Razon'] = 'ID vacío' 

    # 2. FILTRO: Los campos numéricos deben ser números validos
    for col in numeric_cols:
        df_validado[col] = pd.to_numeric(df_validado[col], errors='coerce') 

    # Detección de errores específicos (decimales, nulos, números gigantes)
    mask_decimales = (df_validado[col] % 1 != 0) & (df_validado[col].notnull())
    mask_nan = df_validado[numeric_cols].isnull().any(axis=1) 
    mask_muy_grande = (df_validado['Arribo'] > MAX_VALOR_PERMITIDO) | (df_validado['Irrupcion'] > MAX_VALOR_PERMITIDO)
    
    df_validado.loc[mask_nan & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = 'Campo vacío o no numérico'
    df_validado.loc[mask_decimales & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = f'Tiempo de {col} es decimal'
    df_validado.loc[mask_muy_grande & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = f'Excede el límite de tiempo permitido de {MAX_VALOR_PERMITIDO}'

    # 3. FILTRO: No existen tiempos o tamaños negativos
    mask_no_positivo = (df_validado['Tamaño'] <= 0) | (df_validado['Irrupcion'] <= 0) | (df_validado['Arribo'] < 0)
    df_validado.loc[mask_no_positivo & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = 'Valor negativo'

    # 4. FILTRO: Límites Físicos y Lógicos
    mask_memoria = df_validado['Tamaño'] > MAX_MEMORIA
    mask_duplicados = df_validado.duplicated(subset=['ID'], keep='first') # IDs únicos
    
    df_validado.loc[mask_memoria & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = f'Excede Memoria Máx. ({MAX_MEMORIA}K)'
    df_validado.loc[mask_duplicados & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = 'ID Duplicado'
    
    # --- Separación de Aceptados vs Descartados ---
    df_aceptados = df_validado[df_validado['Rechazo_Razon'] == ''].copy()
    df_descartados = df_validado[df_validado['Rechazo_Razon'] != ''].copy()

    # Conversión a entero (estética)
    for col in numeric_cols:
        df_aceptados[col] = df_aceptados[col].astype('Int64')

    # 5. FILTRO: Límite de procesos en la simulación (Max 10)
    if len(df_aceptados) > 10:
        df_sobrantes = df_aceptados.iloc[10:].copy()
        df_sobrantes['Rechazo_Razon'] = 'Excede límite de 10 procesos admitidos'
        
        df_aceptados = df_aceptados.head(10).copy()
        df_descartados = pd.concat([df_descartados, df_sobrantes], ignore_index=True)

    # --- Informe visual del filtrado ---
    if df_descartados.empty:
        console.print(f"\n[bold green]Procesos validados. Todos los procesos han sido Aceptados.[/bold green]\n")
        tabla_admitidos = crear_tabla_procesos_df(df_aceptados, "Procesos Aceptados", "bold green")
        console.print(tabla_admitidos)
    else:
        msg = f"Se rechazaron {len(df_descartados)} proceso(s) por errores en los datos o porque se excedió el limite de procesos admitidos."
        console.print(f"\n[bold red]¡Atención![/bold red] {msg}\n")
        tabla_admitidos = crear_tabla_procesos_df(df_aceptados, "PROCESOS ACEPTADOS", "bold green")
        tabla_rechazados = crear_tabla_rechazados_df(df_descartados, "PROCESOS RECHAZADOS", "bold red")
        console.print(Columns([tabla_admitidos, tabla_rechazados], expand=True))

    return df_aceptados

def crearColaDeTrabajo(df_aceptados):
    """
    Convierte el DataFrame validado en una Lista de Objetos 'Proceso'
    y la ordena por Tiempo de Arribo. Esto simula la cola de entrada al sistema.
    """
    if not df_aceptados.empty:
        pausar_y_limpiar("Presione 'Enter' para ordenar y crear la Cola de Trabajo...")
        
        console.print(f"\n[bold yellow]Se ordenaron los procesos por Tiempo de Arribo (TA) y se creó la Cola de Trabajo...[/bold yellow]\n")
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
    else:
        console.print("\n\n[bold yellow]No hay procesos admitidos para la simulación.[/bold yellow]")
        input("\nPresione 'Enter' para salir.")
        sys.exit()

    pausar_y_limpiar("Presione 'Enter' para iniciar la Simulación...")

    return colaDeTrabajo