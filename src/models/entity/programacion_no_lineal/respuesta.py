# src/models/entity/programacion_no_lineal/respuesta.py

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from src.models.entity.programacion_lineal.enums import EstadoProblema


@dataclass(frozen=True)
class IteracionNL:
    """Captura el estado de una iteración del método numérico."""
    numero:      int
    datos:       Dict[str, float]  # pares columna → valor
    descripcion: str               # texto breve de la decisión tomada


@dataclass(frozen=True)
class CondicionKKT:
    """Estado de una condición KKT individual para mostrar en la vista."""
    nombre:      str    # "Estacionariedad ∂L/∂x1"
    expresion:   str    # "∂f/∂x1 + λ₁·∂g₁/∂x1 = 0"
    valor:       float  # valor numérico evaluado en x*
    satisfecha:  bool


@dataclass(frozen=True)
class RespuestaNoLineal:
    """Resultado completo de cualquier método de optimización no lineal."""
    estado:        EstadoProblema
    mensaje:       str
    metodo:        str
    z_optimo:      Optional[float]
    punto_optimo:  Optional[Tuple[float, ...]]   # (x1*, x2*, ...)
    iteraciones:   List[IteracionNL]
    columnas:      List[str]                     # cabeceras de la tabla de iteraciones
    multiplicadores: Optional[Dict[str, float]] = None  # λ para Lagrange/KKT
    condiciones_kkt: Optional[List[CondicionKKT]] = None
