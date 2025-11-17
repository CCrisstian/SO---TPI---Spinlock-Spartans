from varGlobal import console, MAX_MEMORIA
from importaciones import *

def cargarProcesos():
    # --- PANTALLA 2: Procesos Leídos ---
    archivo_CSV = "ArchivosEjemplo/procesos.csv" 
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

    # --- PANTALLA 3: Filtrado y Resultados ---
    console.print(f"\n[bold yellow]Realizando Filtrado y Validación de Procesos[/bold yellow]")
    numeric_cols = ['Tamaño', 'Arribo', 'Irrupcion']    #Columnas numericas
    
    # Crear una copia del DataFrame original para no modificarlo
    df_validado = df_procesos.copy()
    df_validado['Rechazo_Razon'] = ''

    # 2. FILTRO (ID vacío): Encontrar filas donde 'ID' es nulo
    mask_id_vacio = df_validado['ID'].isnull()
    df_validado.loc[mask_id_vacio, 'Rechazo_Razon'] = 'ID vacío' # Marcar esas filas con el motivo del rechazo

    
    # 3. FILTRO (No numérico): Intentar convertir columnas a número
    for col in numeric_cols:
        df_validado[col] = pd.to_numeric(df_validado[col], errors='coerce') # 'errors='coerce'' convierte texto en 'NaN' (Not a Number)

    mask_nan = df_validado[numeric_cols].isnull().any(axis=1) # Encontrar filas y las marcamos
    df_validado.loc[mask_nan & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = 'Campo vacío o no numérico'

    # 4. FILTRO (Valor no positivo):
    mask_no_positivo = (df_validado['Tamaño'] <= 0) | (df_validado['Irrupcion'] <= 0) | (df_validado['Arribo'] < 0)
    df_validado.loc[mask_no_positivo & (df_validado['Rechazo_Razon'] == ''), 'Rechazo_Razon'] = 'Valor negativo'

    # 5. FILTRO (Memoria Máxima):
    mask_memoria = df_validado['Tamaño'] > MAX_MEMORIA
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

    return df_aceptados

def crearColaDeTrabajo(df_aceptados):

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

    return colaDeTrabajo