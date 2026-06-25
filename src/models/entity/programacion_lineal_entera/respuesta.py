# src/models/entity/programacion_lineal_entera/respuesta.py

from dataclasses import dataclass
from fractions import Fraction
from typing import List, Optional, Union
from src.models.entity.programacion_lineal.enums import EstadoProblema
from src.models.entity.programacion_lineal.respuesta import NumericoTabular
from src.models.entity.programacion_lineal.respuesta import IteracionTabular


# Método de Ramificación y Acotamiento (Branch and Bound)
@dataclass(frozen=True)
class RamificacionVariable:
    """
    Representa la cota matemática impuesta a una variable al ramificar.
    Ejemplo: X1 <= 2  -> indice_variable=0, cota=2, es_limite_superior=True
             X2 >= 4  -> indice_variable=1, cota=4, es_limite_superior=False
    """
    indice_variable: int              # Posición de la variable (0 para X1, 1 para X2...)
    cota: NumericoTabular             # El valor entero de corte (Fraction o int)
    es_limite_superior: bool          # True si es <= (cota superior), False si es >= (cota inferior)


@dataclass(frozen=True)
class NodoBranchAndBound:
    """Representa un estado/subproblema absoluto dentro del árbol de exploración."""
    id_nodo: int
    id_padre: Optional[int]
    ramificacion: Optional[RamificacionVariable]        # None para el nodo raíz
    z_local: Optional[NumericoTabular]                  # Puede ser Fraction si la relajación usa Simplex
    variables_locales: Optional[List[NumericoTabular]]  # Valores óptimos (fraccionarios o enteros) en este nodo
    estado_nodo: EstadoProblema                         # OPTIMO, INVIABLE, u otro estado semántico
    mensaje: str                                        # Explicación (ej: "Podado por cota", "Solución entera")


@dataclass(frozen=True)
class RespuestaBranchAndBound:
    estado: EstadoProblema
    mensaje: str
    z_optimo: Optional[NumericoTabular]
    variables_decision: Optional[List[NumericoTabular]]
    arbol_nodos: List[NodoBranchAndBound] # Lista secuencial de cómo se exploró el árbol


# Algoritmo del Plano de Corte (Cortes de Gomory)
@dataclass(frozen=True)
class RespuestaPlanoCorte:
    estado: EstadoProblema
    mensaje: str
    z_optimo: Optional[NumericoTabular]
    variables_decision: Optional[List[NumericoTabular]]
    # Recicla tu estructura exacta: cada iteración puede ser un tableau normal o uno con una fila de corte
    iteraciones: List[IteracionTabular]


# Método de Enumeración Implícita (Balas)
@dataclass(frozen=True)
class PasoEnumeracion:
    combinacion: List[Optional[int]]  # Ej: [1, 0, None] donde None significa variable libre
    z_local: float
    factible: bool
    decision: str                     # Ej: "Se genera mejor cota", "Poda por inviabilidad"


@dataclass(frozen=True)
class RespuestaEnumeracionImplicita:
    estado: EstadoProblema
    mensaje: str
    z_optimo: Optional[Union[int, Fraction]]  # Puede ser Fraction si se calculó con aritmética exacta
    variables_decision: Optional[List[int]]
    pasos: List[PasoEnumeracion]