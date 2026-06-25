# src/models/entity/programacion_no_lineal/enums.py

from enum import Enum, unique


@unique
class TipoMetodoNL(Enum):
    SECCION_AUREA = "Sección Áurea"
    NEWTON        = "Newton (1 Variable)"
    GRADIENTE     = "Gradiente (Steepest)"
    LAGRANGE      = "Multiplicadores de Lagrange"
    KKT           = "Condiciones KKT"


@unique
class TipoRestriccionNL(Enum):
    IGUALDAD         = "=="
    DESIGUALDAD_MEI  = "<="
    DESIGUALDAD_MAI  = ">="
