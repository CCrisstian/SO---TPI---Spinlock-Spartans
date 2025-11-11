<h1>Información General</h1>

Proyecto para la materia de Sistemas Operativos, desarrollado en Python.
Este script simula un "mini Sistema Operativo", realizando la carga inicial, el filtrado y la organización de procesos leídos desde un archivo CSV, preparando el terreno para la asignación de memoria y planificación de un CPU.

Utiliza `pandas` para el manejo de datos y `rich` para una presentación visual moderna y limpia en la terminal.

## ✅ Características

* **Pantalla de Bienvenida:** Muestra una presentación del grupo "Spinlock Spartans" y sus integrantes.
* **Interfaz Clara:** Guía al usuario paso a paso con transiciones que pausan y limpian la pantalla.
* **Lectura de CSV:** Carga procesos desde un archivo `.csv` local usando `pandas`.
* **Filtrado de Memoria:** Valida los procesos leídos y descarta aquellos que exceden la memoria máxima del sistema (fijada en 250K).
* **Reporte Visual:** Muestra tablas lado a lado de los "Procesos Admitidos" y "Procesos Rechazados" para una fácil comparación.
* **Ordenamiento por Arribo:** Ordena la lista final de procesos admitidos por su Tiempo de Arribo (TA).

## 📦 Instalación

El proyecto requiere Python 3.x y las siguientes librerías:

1.  Instala las dependencias necesarias con un solo comando:
    ```bash
    pip install pandas rich
    ```
