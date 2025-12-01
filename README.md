👥 Integrantes - Grupo "Spinlock Spartans"

- Blanco, Facundo
- Claver Gallino, Samira
- Cristaldo, Cristian Alejandro
- Echeverria Melgratti, Lautaro
- Yaya, Franco Gabriel

Materia: Sistemas Operativos

🛡️ TPI- Simulación de Planificación de CPU y Gestión de Memoria. 

📖 Descripción: Este software simula el comportamiento del Kernel de un Sistema Operativo monoprocesador. Realiza la carga de trabajos desde un lote externo, administra la Memoria Principal utilizando particiones fijas y planifica la CPU mediante algoritmos de corto y mediano plazo.

Desarrollado en Python utilizando *pandas* para la gestión de datos y *rich* para la visualización de tablas y eventos en tiempo real en la consola.

✅ Funcionalidades Implementadas
1. Gestión de Memoria
   - Esquema: Particiones Fijas (4 particiones de tamaños variados).
   - Algoritmo de Asignación: Best-Fit (Mejor Ajuste). Busca la partición libre más pequeña donde quepa el proceso para minimizar la fragmentación interna.

3. Planificación de CPU (Corto Plazo)
   - Algoritmo: SRTF (Shortest Remaining Time First).
   - Características: Apropiativo (Preemptive). Si llega un proceso con una ráfaga menor a la restante del proceso actual, se realiza un desalojo (context switch).

5. Planificación de Mediano Plazo (Swapping)
   - Mecanismo: Intercambio entre Memoria Principal y Disco (Cola de Suspendidos).
   - Criterio: Si la memoria está llena, se intercambia un proceso "lento" en memoria por uno "rápido" que esté esperando en disco, maximizando el rendimiento del sistema.

6. Interfaz y Reportes
   - Filtrado Inteligente: Validación de procesos (IDs duplicados, tamaño excedido, datos corruptos) antes de iniciar.
   - Visualización en Vivo: Tablas simultáneas de Cola de Listos, CPU, Memoria y Disco.
   - Informe Estadístico: Al finalizar, calcula y muestra el Tiempo de Retorno (TR) y Tiempo de Espera (TE) de cada proceso.

🚀 Instrucciones de Ejecución
- El proyecto se entrega compilado para facilitar su ejecución en Windows sin necesidad de instalar dependencias.
1. Descomprimir la carpeta del proyecto.
2. Ingresar a la carpeta Programa.
3. Ejecutar el archivo *SimuladorSO.exe*.
4. Al ejecutarse, el programa permitirá al usuario elegir uno de los archivos ubicados en la carpeta *ArchivosEjemplo* para su evaluación.

Nota: No mueva el ejecutable de su carpeta, ya que necesita los archivos adjuntos para funcionar.

