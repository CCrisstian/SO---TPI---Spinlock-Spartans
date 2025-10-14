import sys # Se usa para ingresar parámetros por la línea de comandos y detener el programa.
import os # Se usa para limpiar la pantalla de la consola, gestionar archivos o navegar por directorios.
from types import NoneType # Sirve para hacer comprobaciones sobre si una variable es nula.
from colorama import init, Fore, Back, Style # Componentes de la librería para poder mostrar texto con colores en la consola.
init() # Inicializamos la librería.

#------------ Definicion de "Clases" ------------

# La clase 'Particion' representa cada una de las Particiones de Memoria,
# como se describe en la "Tabla de Particiones".
    # idParticion: Id de partición. 
    # dirInicio: dirección de comienzo de partición. 
    # tamaPart: tamaño de la partición. 
    # proc: El objeto Proceso completo asignado a la partición. 'None' si está libre.
    # idProceso: id de proceso asignado a la partición 
    # fragmentacion: fragmentación interna.

class Particion:
  def __init__(self, idParticion, dirInicio, tamaPart, proc, idProceso, fragmentacion):
      self.idParticion = idParticion
      self.dirInicio = dirInicio
      self.tamaPart = tamaPart
      self.proc = proc
      self.idProceso = idProceso
      self.fragmentacion=fragmentacion
  def __repr__(self):
        return repr((self.idParticion, self.dirInicio, self.tamaPart, self.proc, self.idProceso, self.fragmentacion))

# La clase 'Proceso' representa cada uno de los Procesos.
    # idProceso: Id de proceso.
    # tamProceso: tamaño del proceso.
    # estado: Estado actual del proceso.
    # TA: tiempo de arribo.
    # TI: tiempo de irrupción.

class Proceso:
    def __init__(self, idProceso, tamProceso, estado, TA, TI):
      self.idProceso = idProceso
      self.tamProceso = tamProceso
      self.estado = estado
      self.TA = TA
      self.TI = TI
    def __repr__(self):
        return repr((self.idProceso, self.tamProceso, self.estado, self.TA, self.TI))

# La clase 'Cpu' representa el estado y comportamiento de la CPU en un instante de tiempo.
# Actúa como un contenedor para saber: (1)Qué 'Proceso' se está ejecutando y (2)Cuánto tiempo le queda.
#   idProceso (int): El ID del 'Proceso' que está actualmente en ejecución. 'None' si está libre.
#   estado (str): Indica si la CPU está "Ocupada" o "Libre".
#   TI (int): El Tiempo de Irrupción *restante* del 'Proceso' en ejecución.
#   procesosTerminados (int): Un contador para el número total de 'Procesos' finalizados.

class Cpu:
    def __init__(self, idProceso, estado, TI, procesosTerminados):
      self.idProceso = idProceso
      self.estado = estado
      self.TI = TI
      self.procesosTerminados=procesosTerminados

    # Este método implementa la lógica de selección del algoritmo S.R.T.F. (Shortest Remaining Time First).
    # Decide qué 'Proceso' de los que están en Memoria debe ejecutarse.
    def addProceso(self):
      pos=-1        # Posición de la partición con el Proceso más corto
      p=0           # Iterador para la posición de la Partición
      if self.estado==0:    # Solo se ejecuta si la CPU está libre. 0 es 'Libre' y 1 es 'Ocupado'
        minTI= sys.maxsize        # Inicializamos con un valor muy alto para la comparación

        # Recorremos todas las particiones para encontrar el 'Proceso' con el menor TI
        for k in particiones:
          if k.proc!=None and k.proc.TI < minTI:
            minTI=k.proc.TI
            pos=p
          elif k.proc!=None and k.proc.TI == minTI: 
            #caso que tengan mismo TI tenemos en cuenta el TA
            if k.proc.TA < particiones[pos].proc.TA:
              pos=p
          p=p+1
        if particiones[pos].proc != None:
          #carga proceso a CPU
          self.idProceso=particiones[pos].idProceso

          # Mostrar por pantalla qué 'Proceso' entra a la CPU
          vistaProceso= ' EJECUCION: Ingresa a la CPU el Proceso '+ str(self.idProceso)
          print(format('+','-<56')+'+')
          print('|'+'\033[1m' + format(vistaProceso, '<55') + '\033[0m'+'|')
          print(format('+','-<56')+'+\n')
          self.TI=particiones[pos].proc.TI
          self.estado=1

    # Este método simula el paso de una unidad de tiempo y maneja la finalización o la expropiación (preemption) de un 'Proceso'.            
    def dropProceso(self):
      self.TI=self.TI-1 # Decrementamos el tiempo restante del 'Proceso' en ejecución

      if self.TI<=0:    # CASO 1: El 'Proceso' ha terminado su ejecución
        # Sacamos el 'Proceso' de la 'Lista de Procesos'
        for j in colaDeTrabajo:
          if j.idProceso == self.idProceso:
            colaDeTrabajo.remove(j)
            self.procesosTerminados=self.procesosTerminados +1
        # Sacamos el 'Proceso' de la 'Particion'
        for i in particiones:
          if i.idProceso == self.idProceso:
            i.fragmentacion=0
            i.proc=None
            i.idProceso=0
        # Ponemos la CPU en valores iniciales de nuevo
        self.estado=0
        self.idProceso=0
        self.TI=0
      
      # CASO 2: El 'Proceso' aún no ha terminado
      elif self.TI > 0:
        # Lógica de EXPROPIACIÓN (Preemption) del SRTF
        # Observamos si hay otro 'Proceso' que tiene un TI menor
        p=0
        for n in particiones: 
          # Recorremos las Particiones
          # Si existe un 'Proceso' en otra Partición que sea más corto que el que le queda al actual
          if n.proc!= None and n.proc.TI < self.TI:
            # Ocurre un cambio de contexto

            #Se muestra el 'Proceso' que abandona la CPU
            vistaProceso= ' EJECUCION: Sale de la CPU el Proceso '+ str(self.idProceso)
            print(format('+','-<56')+'+')
            print('|'+'\033[1m' + format(vistaProceso, '<55') + '\033[0m'+'|')
            print(format('+','-<56')+'+\n')

            # Actualizamos la CPU con el nuevo 'Proceso' (más corto)
            self.idProceso=particiones[p].idProceso
            # Mensaje de ingreso del nuevo 'Proceso'
            vistaProceso= ' EJECUCION: Ingresa a la CPU el Proceso '+ str(self.idProceso)
            print(format('+','-<56')+'+')
            print('|'+'\033[1m' + format(vistaProceso, '<55') + '\033[0m'+'|')
            print(format('+','-<56')+'+\n')
            self.TI=particiones[p].proc.TI
          p=p+1
        
        
#-- Definicion de funciones

def showProcesos(lista_procesos):
    id_w = 7
    tam_w = 10
    ta_w = 18
    ti_w = 24

    # --- Creación de la línea separadora de la tabla ---
    linea_superior = f"+{'-' * id_w}+{'-' * tam_w}+{'-' * ta_w}+{'-' * ti_w}+"
    
    # --- Impresión de la Tabla de Procesos ---

    titulo_width = len(linea_superior) - 2 
    
    print(linea_superior)
    print(f"|{'Tabla de Procesos':^{titulo_width}}|")
    print(linea_superior)

    # --- Encabezados de las columnas ---
    print(f"|{'ID':^{id_w}}|{'Tamaño':^{tam_w}}|{'Tiempo de arribo':^{ta_w}}|{'Tiempo de interrupción':^{ti_w}}|")
    print(linea_superior)
    
    # --- Fila del Sistema Operativo ---
    init(autoreset=True)
    so_id = Fore.CYAN + f"{'SO':^{id_w}}"
    so_tam = Fore.CYAN + f"{'100K':^{tam_w}}"
    so_ta = Fore.CYAN + f"{'NULL':^{ta_w}}"
    so_ti = Fore.CYAN + f"{'NULL':^{ti_w}}"
    print(f"|{so_id}|{so_tam}|{so_ta}|{so_ti}|")

    # --- Filas de los 'Procesos' ---
    for proceso in lista_procesos:
        id_str = f"{proceso.idProceso}"
        tam_str = f"{proceso.tamProceso}K"
        ta_str = f"{proceso.TA}"
        ti_str = f"{proceso.TI}"
        print(f"|{id_str:^{id_w}}|{tam_str:^{tam_w}}|{ta_str:^{ta_w}}|{ti_str:^{ti_w}}|")

    # --- Cierre de la tabla ---
    print(linea_superior + '\n')
    
  
def showParticiones(lista):
  m=2
  print(format('+','-<56')+'+')
  print('|'+format('Tabla de Particiones', '^55')+'|')
  print(format('+','-<56')+'+')
  print('| ID PART |   TP   |  PID  |  PT  |  FRGI  | Dir Inicio |')
  print(format('+','-<56')+'+')
  init(autoreset=True) #Para que el texto de abajo no cambie de color
  print('|'+ Fore.CYAN + '    0    |  100   |  OS   | 100  |  NULL  |     0      '+ Fore.WHITE+'|')
  #Set recorrido en orden de ID particion 
  while m >= 0:
      if particiones[m].proc != None:
        showTamProc = particiones[m].proc.tamProceso
      else:
        showTamProc = 0
      print('|   ',particiones[m].idParticion,'   |'+format(str(particiones[m].tamaPart), '^8') +'|'+format(str(particiones[m].idProceso), '^7')+'|'+format(str(showTamProc), '^6')+'|'+format(str(particiones[m].fragmentacion), '^8')+'|'+format(str(particiones[m].dirInicio), '^12')+'|')
      m=m-1
  print(format('+','-<56')+'+\n')
  
  if colaLS:
    print(Style.BRIGHT + Fore.WHITE + ' Cola de Listos-Suspendidos: ', colaLS, '\n')
  else:
    print(Style.BRIGHT + Fore.WHITE + ' Cola de Listos-Suspendidos: no hay procesos suspendidos \n')
  init(autoreset=True)
  

def showTime(tiempo):
  vistaTiempo = 'TIEMPO = '+ str(tiempo) 
  print(format('+','-<79')+'+')
  print('|',format(vistaTiempo, '^76'),'|' )
  print(format('+','-<79')+'+\n')

# Gestion de cola listo-suspendido
def gestionCLS(colaDeTrabajo, colaLS):
  for i in colaDeTrabajo:
    if i not in colaLS: 
      if i.estado == 0 and tiempo > i.TA:
        colaLS.append(i)
    else:
      if i.estado == 1:
        colaLS.remove(i)
      
      
def crearProceso(idProceso):
  if idProceso==1:
    proc= Proceso(idProceso, tamProceso, 0, TA, TI)
    procesos.append(proc)
  elif idProceso==2:
    proc= Proceso(idProceso, tamProceso, 0, TA, TI)
    procesos.append(proc)
  elif idProceso==3:
    proc= Proceso(idProceso, tamProceso, 0, TA, TI)
    procesos.append(proc)
  elif idProceso==4:
    proc= Proceso(idProceso, tamProceso, 0, TA, TI)
    procesos.append(proc)
  elif idProceso==5:
    proc= Proceso(idProceso, tamProceso, 0, TA, TI)
    procesos.append(proc)
  elif idProceso==6:
    proc= Proceso(idProceso, tamProceso, 0, TA, TI)
    procesos.append(proc)
  elif idProceso==7:
    proc= Proceso(idProceso, tamProceso, 0, TA, TI)
    procesos.append(proc)
  elif idProceso==8:
    proc= Proceso(idProceso, tamProceso, 0, TA, TI)
    procesos.append(proc)
  elif idProceso==9:
    proc= Proceso(idProceso, tamProceso, 0, TA, TI)
    procesos.append(proc)
  elif idProceso==10:
    proc= Proceso(idProceso, tamProceso, 0, TA, TI)
    procesos.append(proc)

def calcTiempo (lista):
  sumaDeTiempo=0
  for i in lista:
    sumaDeTiempo= sumaDeTiempo + i.TI + i.TA
  return sumaDeTiempo


#-- BLOQUE PRINCIPAL --

# Definicion de VARIABLES
N=10 #numero maximo de procesos
band=1
idProceso=0
cont = 0 #cantidad de procesos
procesos = []
colaLS = []

#-- Bloque de ejecucion
while band != 0: 
  idProceso=idProceso+1
  b=False
  os.system('cls')
  print(format('+','-<79')+'+')
  print('|'+ format('Simulador de Asignación de Memoria y planificación de Procesos', '^78') +'|')
  print('|'+ format('GRUPO: Spinlock Spartans', '^78') +'|')
  print('|'+ format('Ingrese los procesos para poder iniciarlo', '^78') +'|')
  print(format('+','-<79')+'+')
  init(autoreset=True)
  print('|' + Fore.RED + format(' Limitaciones:','<78') + Fore.WHITE+'|')
  print('|' + Fore.RED + format('       --El tamaño maximo de los Procesos es de 250K','<78') + Fore.WHITE+'|')
  print('|' + Fore.RED + format('       --Solo se admiten hasta 10 Procesos','<78') + Fore.WHITE+'|')
  print(format('+','-<79')+'+')
  while b==False:
    tamProceso=int(input( 'Ingrese el tamaño del Proceso: '))
    if tamProceso>250:
      print(Back.WHITE + Fore.RED +'\n ¡¡ERROR!!, el tamaño ingresado debe ser menor a 250k\n')
      os.system('pause')    
    else:
      b=True   
  TA=int(input('Ingrese el tiempo de arribo del proceso: '))   
  TI=int(input('Ingrese el tiempo de irrupcion del proceso: '))
  crearProceso(idProceso)
  cont=cont+1
  if cont < N:
    band=int(input('Desea agregar otro proceso? SI: 1 | NO: 0  '))
    os.system('cls')
    if band == 0:
      break
  else:
    print('\n ERROR, se alcanzo la maxima cantidad de procesos\n')
    band=0

showProcesos(procesos)
os.system('pause')
os.system('cls')

#-- Cola de procesos
colaDeTrabajo=sorted(procesos, key=lambda proc: proc.TA)

#--Asignacion en Memoria
frag=0 
tiempo = 0 
tiempotot= calcTiempo(procesos) 
#contiene el total de instantes o tiempos necesarios para que se ejecuten todos los procesos
particiones=[Particion(3,470,60,None,0,0),Particion(2,350,120,None,0,0), Particion(1,100,250,None,0,0)]
cpu=Cpu(0,0,0,0) #valores iniciales de la CPU

while tiempo < tiempotot:
  if cpu.estado==1:
    showTime(tiempo)
    cpu.dropProceso()
  if cpu.procesosTerminados == len(procesos): break 
  #-- Si la variable procesosTerminados = a la longitud lista de procesos ingresados, 
  #-- entonces se trataron todos los procesos, y termina el while
	
  # Gestor de COLA DE TRABAJO
  for i in colaDeTrabajo:
    if i.TA <= tiempo and i.estado==0:
      minfrag= sys.maxsize # --asigna valor maximo a la variable
      pos= -1
      p=0 # indicar la posicion de la particion
      for j in particiones:
        frag = j.tamaPart - i.tamProceso
        if frag >=0 and frag < minfrag and j.proc is None:
          # Best Fit donde mejor se acomode el proceso
          minfrag=frag
          pos=p
        # para dos procesos con mismo TA pero TI menor
        if frag >=0 and frag < minfrag and j.proc != None: 
          if j.proc.TI > i.TI:
            band=1
            minfrag=frag
            pos=p
        p=p+1
      if pos>=0:
        if band==1:
          particiones[pos].proc.estado=0
          band=0
        particiones[pos].proc=i
        particiones[pos].proc.estado=1
        # Visibilidad de Tiempo actual y proceso cargado en MP
        os.system('cls')
        showTime(tiempo)
        print(format('+','-<79')+'+')
        vistaProceso = '| EJECUCION: el proceso '+str(i.idProceso)+' de '+str(i.tamProceso)+'K, se coloca en la particion '+str(particiones[pos].idParticion)+' de tamaño '+str(particiones[pos].tamaPart)+'K.'
        print('\033[1m' + format(vistaProceso, '<79') + '\033[0m'+ '|')
        print(format('+','-<79')+'+\n')
        os.system('pause')
        os.system('cls')
        particiones[pos].idProceso=i.idProceso
        particiones[pos].fragmentacion=minfrag
        showTime(tiempo)
  
  gestionCLS(colaDeTrabajo, colaLS)
  colaLS=sorted(colaLS, key=lambda colaDeTrabajo: colaDeTrabajo.TI)
  
  if cpu.estado==0: 
    # si la cpu esta vacia agregamos un proceso
    cpu.addProceso()
    
  if cpu.idProceso==0: 
    # si el PID es igual a 0 la cpu no tiene ningun proceso, no se muestra nada, no hay acciones
    print(' ')
    # Increento el instante de tiempo
    tiempo=tiempo+1
    os.system('pause')
    os.system('cls')
  else:
    showParticiones(particiones)
    # incluimos la visibilidad de TI actual y restante 
    print(format('+','-<56')+'+')
    format(vistaProceso, '<55')
    print('|'+format('EJECUCION DE CPU' , '^55')+'|')
    print(format('+','-<56')+'+')
    print('|'+'\033[1m'+format('  --Se esta ejecutando el proceso:'+ str(cpu.idProceso), '<55')+'\033[0m'+'|')
    print('|'+'\033[1m'+format('  --Tiempo de Irrupcion actual:'+ str(cpu.TI), '<55')+'\033[0m'+'|')
    print('|'+'\033[1m'+format('  --Tiempo de Irrupcion restante:'+ str(cpu.TI-1), '<55')+'\033[0m'+'|')
    print(format('+','-<56')+'+\n')
    
    # Actualizo el TI restante del proceso cargado en Array de procesos 
    procesos[cpu.idProceso-1].TI= cpu.TI-1
    
    showProcesos(procesos)
    # espera a enter para continuar
    os.system('pause')
    os.system('cls')
    tiempo=tiempo+1
  
  
# saco ultimo proceso
cpu.dropProceso() 

# ultima ejecucion
os.system('cls')
init(autoreset=True) 
vistaTiempo = 'TIEMPO = '+ str(tiempo) 
print(Fore.GREEN + format('+','-<79')+'+')
print(Fore.GREEN + '|',format(vistaTiempo, '^76'),Fore.GREEN + '|' )
print(Fore.GREEN + format('+','-<79')+'+')
print(Fore.GREEN + '|',format('La Tabla de Particiones de memoria se encuentra vacía', '^76'),Fore.GREEN + '|' )
print(Fore.GREEN + '|',format('Todos los procesos fueron ejecutados exitosamente', '^76'),Fore.GREEN + '|' )
print(Fore.GREEN + format('+','-<79')+'+\n')
showParticiones(particiones)
showProcesos(procesos)
os.system('pause')