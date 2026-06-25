# src/models/metodos/programacion_no_lineal/evaluador.py
"""
Utilidades de evaluación segura de expresiones y diferenciación numérica.
Todas las funciones de esta capa son puras (sin estado).
"""

from __future__ import annotations
import math
from typing import Callable, Tuple

import numpy as np


# ─── namespace seguro para eval ────────────────────────────────────────────────
_SAFE_NS: dict = {
    "__builtins__": {},
    "sin":   np.sin,   "cos":   np.cos,   "tan":   np.tan,
    "exp":   np.exp,   "log":   np.log,   "sqrt":  np.sqrt,
    "ln":    np.log,   "log2":  np.log2,  "log10": np.log10,
    "abs":   np.abs,   "pi":    math.pi,  "e":     math.e,
    "sinh":  np.sinh,  "cosh":  np.cosh,  "tanh":  np.tanh,
}


def construir_funcion(funcion_str: str, variables: Tuple[str, ...]) -> Callable:
    """
    Devuelve un callable f(*valores) que evalúa funcion_str dado un valor por variable.
    Ejemplo: f = construir_funcion("x1**2 + x2", ("x1","x2"))
             f(1.0, 2.0)  → 3.0
    """
    def f(*valores):
        ns = dict(_SAFE_NS)
        for var, val in zip(variables, valores):
            ns[var] = float(val)
        try:
            return float(eval(funcion_str, ns))  # noqa: S307
        except Exception:
            return float("nan")
    return f


def construir_funcion_vec(funcion_str: str, variables: Tuple[str, ...]) -> Callable:
    """Igual que construir_funcion pero acepta un array 1-D como único argumento."""
    f_scalar = construir_funcion(funcion_str, variables)
    return lambda x: f_scalar(*x)


# ─── diferenciación numérica ────────────────────────────────────────────────────

def derivada(f: Callable, x: float, h: float = 1e-7) -> float:
    """Primera derivada por diferencias centrales."""
    return (f(x + h) - f(x - h)) / (2.0 * h)


def segunda_derivada(f: Callable, x: float, h: float = 1e-5) -> float:
    """Segunda derivada por diferencias centrales."""
    return (f(x + h) - 2.0 * f(x) + f(x - h)) / h ** 2


def gradiente_numerico(f_vec: Callable, x: np.ndarray, h: float = 1e-6) -> np.ndarray:
    """Gradiente ∇f(x) por diferencias centrales. f_vec recibe array 1-D."""
    n = len(x)
    grad = np.zeros(n)
    for i in range(n):
        xf, xb = x.copy(), x.copy()
        xf[i] += h
        xb[i] -= h
        grad[i] = (f_vec(xf) - f_vec(xb)) / (2.0 * h)
    return grad


def hessiana_numerica(f_vec: Callable, x: np.ndarray, h: float = 1e-4) -> np.ndarray:
    """Hessiana H(x) por diferencias centrales de orden 4."""
    n = len(x)
    H = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            xpp, xpm, xmp, xmm = x.copy(), x.copy(), x.copy(), x.copy()
            xpp[i] += h; xpp[j] += h
            xpm[i] += h; xpm[j] -= h
            xmp[i] -= h; xmp[j] += h
            xmm[i] -= h; xmm[j] -= h
            H[i, j] = (f_vec(xpp) - f_vec(xpm) - f_vec(xmp) + f_vec(xmm)) / (4.0 * h ** 2)
    return H
