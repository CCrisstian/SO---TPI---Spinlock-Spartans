
# Creamos clases para tratar proceso, partición y CPU como objetos. Cada clase tiene una funcion que devuelve su estado actual
class Proceso:
    def __init__(self, idProceso, tamProceso, TA, TI, estado="NUEVO"):
        self.idProceso = idProceso          #Atributos del proceos
        self.tamProceso = tamProceso
        self.estado = estado
        self.TA = TA
        self.TI = TI    # TI se usará para el TI Restante (SRTF)       
        # Atributos para estadísticas
        self.TI_original: int = TI            # Guardamos el TI original
        self.tiempo_finalizacion: int = 0     # El instante de tiempo T en el que termina
        self.tiempo_retorno: int = 0          # TR = TF - TA
        self.tiempo_espera: int = 0           # TE = TR - TI_original
        self.es_primer_arribo_listos: bool = False # Bandera
        self.TA_paraCalculo: int = 0          # El TA cuando entró a Listos por 1ra vez
   
    def __repr__(self):
        return (f"Proceso (ID={self.idProceso}, Tam={self.tamProceso}K, "
                f"Estado='{self.estado}', TA={self.TA}, TI={self.TI})")

class Particion:    # Clase que representa una partición de memoria
    def __init__(self, id_part: str, dir_inicio: int, tamano: int, id_proceso: str | int = None, fragmentacion: int = 0):
      self.id_part = id_part
      self.dir_inicio = dir_inicio
      self.tamano = tamano
      self.id_proceso = id_proceso
      self.fragmentacion = fragmentacion
    
    def __repr__(self):     
        return (f"Particion (ID='{self.id_part}', Inicio={self.dir_inicio}, "
                f"Tam={self.tamano}K, ProcID={self.id_proceso})")
    
class Cpu:          # Clase que representa el CPU, que trata los procesos entrantes
    def __init__(self):
        self.proceso_en_ejecucion: Proceso | None = None
        self.tiempo_restante_irrupcion: int = 0
    
    def esta_libre(self) -> bool:               # Función para determinar si el objeto está libre
        return self.proceso_en_ejecucion is None

    def __repr__(self):                         # Función que determina que proceso está en ejecución
        if self.proceso_en_ejecucion:
            return f"CPU (Ejecutando ID: {self.proceso_en_ejecucion.idProceso}, TR: {self.tiempo_restante_irrupcion})"
        return "CPU (Libre)"
