<h1>Instalar liberías</h1>

Este es un proyecto para la materia de Sistemas Operativos, desarrollado en Python. El script simula la carga inicial, el filtrado y la organización de procesos leídos desde un archivo CSV, preparando el terreno para una simulación de asignación de memoria y planificación de CPU.

Utiliza `pandas` para el manejo de datos y `rich` para una presentación visual moderna y limpia en la terminal.

## 🚀 Características

* **Panel de Bienvenida:** Muestra una presentación del grupo "Spinlock Spartans" y sus integrantes.
* **Lectura de CSV:** Carga procesos desde un archivo `.csv` local usando `pandas`.
* **Filtrado de Memoria:** Valida los procesos leídos y descarta aquellos que exceden la memoria máxima del sistema (fijada en 250K).
* **Reporte Visual:** Muestra tablas lado a lado de los "Procesos Admitidos" y "Procesos Rechazados" para una fácil comparación.
* **Ordenamiento por Arribo:** Ordena la lista final de procesos admitidos por su Tiempo de Arribo (TA).
* **Interfaz Clara:** Guía al usuario paso a paso con transiciones que pausan y limpian la pantalla.

## 📦 Instalación

El proyecto requiere Python 3.x y las siguientes librerías:

1.  Instala las dependencias necesarias con un solo comando:
    ```bash
    pip install pandas rich
    ```
