¡Obvio\! Acá tenés todo armadito en un solo bloque listo para copiar y pegar en tu archivo `README.md` (o `LEEME.txt`).

**Solo un recordatorio antes de copiar:** Acordate de ejecutar `pip freeze > requirements.txt` en tu terminal primero, así se crea el archivo que tus compañeros van a necesitar instalar.

Acá va el texto:

````markdown
# 🛡️ SO - Spinlock Spartans (TPI)

Simulador de Sistema Operativo desarrollado en Python para la cátedra de Sistemas Operativos.

## 📋 Requisitos previos
* Tener **Python 3.10** (o superior) instalado.
* Se recomienda usar **Visual Studio Code**.

---

## 🚀 Guía de Instalación (Paso a paso)

Para evitar problemas de versiones y conflictos, este proyecto utiliza un **Entorno Virtual**. Sigue estos pasos para configurarlo la primera vez:

### 1. Clonar o descargar el repositorio
Descarga la carpeta del proyecto y abre una terminal dentro de la carpeta `Programa` (o la raíz del proyecto donde esté el código).

### 2. Crear el Entorno Virtual
Esto crea una carpeta aislada para instalar las librerías del proyecto.
Ejecuta:
```bash
python -m venv venv_tpi
````

### 3\. Activar el Entorno

Dependiendo de tu terminal, el comando cambia un poco:

  * **En PowerShell (VS Code por defecto):**

    ```powershell
    .\venv_tpi\Scripts\Activate
    ```

    > *Si te sale error de "scripts deshabilitados" en rojo, ejecuta esto primero:*
    > `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process`

  * **En CMD (Símbolo del sistema):**

    ```cmd
    venv_tpi\Scripts\activate.bat
    ```

  * **En Git Bash:**

    ```bash
    source venv_tpi/Scripts/activate
    ```

💡 **Nota:** Sabrás que funcionó cuando veas `(venv_tpi)` en color verde al principio de la línea de comandos.

### 4\. Instalar las Dependencias

Con el entorno activado, instala todas las librerías necesarias (Pandas, Rich, etc.) de una sola vez:

```bash
pip install -r requirements.txt
```

-----

## ▶️ Ejecución del Simulador

Para correr el programa, asegúrate de tener el entorno activado y ejecuta:

```bash
python MAIN.py
```

*(Si el archivo principal tiene otro nombre, reemplaza `MAIN.py` por el nombre correcto).*

-----

## 📦 Crear el Ejecutable (.exe)

Si desean generar el archivo `.exe` portable:

1.  Asegúrate de estar en el entorno activado (`venv_tpi`).
2.  Ejecuta:
    ```bash
    pyinstaller --onefile --clean --name "SimuladorSO" MAIN.py
    ```
3.  El ejecutable aparecerá en la carpeta `dist/`.
4.  **IMPORTANTE:** Para que funcione, debes MOVER el `.exe` generado a la carpeta raíz del proyecto (al lado de la carpeta `ArchivosEjemplo`).

-----

## ⚠️ Solución de Problemas

**Error: "Path too long" o errores al instalar en OneDrive**
Si el proyecto está dentro de OneDrive y Windows tira error por rutas largas al instalar librerías:

1.  Abrir PowerShell como Administrador.
2.  Ejecutar el siguiente comando para habilitar rutas largas en Windows:
    ```powershell
    New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
    ```
3.  Reiniciar la PC e intentar instalar de nuevo.

<!-- end list -->

```
```