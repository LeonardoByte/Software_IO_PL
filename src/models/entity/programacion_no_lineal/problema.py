# src/models/entity/programacion_no_lineal/problema.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple

from src.models.entity.programacion_lineal.enums import TipoOptimizacion


@dataclass(frozen=True)
class RestriccionNL:
    """Restricción no lineal: expresion(vars) signo 0.
    La expresión se escribe movida al lado izquierdo: g(x) == 0, g(x) <= 0, g(x) >= 0."""
    expresion: str   # e.g. "x1 + x2 - 1"
    signo: str       # "==", "<=", ">="


@dataclass(frozen=True)
class ProblemaNoLineal:
    """Modelo completo de un problema de programación no lineal."""
    tipo:          TipoOptimizacion       # MAX | MIN
    funcion_str:   str                    # "3*x1**2 - 2*x1 + 5"
    variables:     Tuple[str, ...]        # ("x1",) o ("x1", "x2")

    # Para métodos de intervalo (Sección Áurea)
    intervalo:     Optional[Tuple[float, float]] = None   # (a, b)

    # Para métodos iterativos (Newton, Gradiente, KKT)
    punto_inicial: Optional[Tuple[float, ...]] = None     # (x1_0, x2_0, ...)

    # Restricciones (Lagrange / KKT)
    restricciones: Tuple[RestriccionNL, ...] = ()

    # Hiperparámetros del método
    tolerancia:       float = 1e-6
    max_iteraciones:  int   = 100

    @property
    def n_variables(self) -> int:
        return len(self.variables)

    @property
    def es_univariable(self) -> bool:
        return self.n_variables == 1

    @property
    def tiene_restricciones(self) -> bool:
        return len(self.restricciones) > 0
