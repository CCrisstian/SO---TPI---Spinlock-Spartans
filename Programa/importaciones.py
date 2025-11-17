import pandas as pd
import os
import sys
import time
from rich.console import Console, Group
from rich.table import Table, Column
from rich.panel import Panel
from rich import box
from rich.text import Text
from rich.columns import Columns
from rich.rule import Rule
from typing import List, Tuple
from statistics import mean # Para calcular promedios
from clases import Proceso, Particion, Cpu  # importamos las clases a ocupar.
from informe import mostrar_informe_estadistico
from tablas import *
from pantalla import *
from logica import *
