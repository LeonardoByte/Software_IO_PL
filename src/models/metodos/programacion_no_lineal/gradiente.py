# src/models/metodos/programacion_no_lineal/gradiente.py
"""
Método del Gradiente (Steepest Ascent / Steepest Descent).
Para optimización irrestricta de funciones multivariable.
Usa búsqueda de paso por retroceso (backtracking) en cada iteración.
"""

from __future__ import annotations
from typing import Dict, List

import numpy as np

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal
from src.models.entity.programacion_no_lineal.respuesta import IteracionNL, RespuestaNoLineal
from src.models.metodos.programacion_no_lineal.evaluador import (
    construir_funcion_vec, gradiente_numerico,
)


def _backtrack(f_desc: callable, x: np.ndarray, direction: np.ndarray,
               alpha0: float = 1.0, rho: float = 0.5, max_ls: int = 60) -> float:
    """
    Busca el paso α que garantice f_desc(x + α·d) < f_desc(x).
    f_desc es siempre una función a MINIMIZAR (negar f para MAX).
    """
    alpha = alpha0
    f0 = f_desc(x)
    for _ in range(max_ls):
        if f_desc(x + alpha * direction) < f0:
            return alpha
        alpha *= rho
    return 1e-6   # paso mínimo de emergencia


class SolucionadorGradiente:
    METODO = "Gradiente (Steepest Ascent/Descent)"

    def resolver(self, problema: ProblemaNoLineal) -> RespuestaNoLineal:
        if problema.punto_inicial is None:
            return self._error(problema, "Debe especificar un punto inicial.")

        f_vec  = construir_funcion_vec(problema.funcion_str, problema.variables)
        es_max = problema.tipo == TipoOptimizacion.MAX

        # Para maximizar, minimizamos −f
        f_desc = (lambda x: -f_vec(x)) if es_max else f_vec

        x        = np.array([float(v) for v in problema.punto_inicial], dtype=float)
        tol      = problema.tolerancia
        max_iter = problema.max_iteraciones

        columnas = ["n"] + list(problema.variables) + ["f(x)", "‖∇f‖", "α"]
        iteraciones: List[IteracionNL] = []

        for n in range(1, max_iter + 1):
            fx        = f_vec(x)
            grad_desc = gradiente_numerico(f_desc, x)   # ∇f_desc
            norm_grad = float(np.linalg.norm(grad_desc))

            datos: Dict[str, float] = {"n": float(n), "f(x)": fx, "‖∇f‖": norm_grad}
            for var, val in zip(problema.variables, x):
                datos[var] = float(val)

            direction = -grad_desc   # descenso de f_desc → ascenso de f si es_max

            alpha = _backtrack(f_desc, x, direction)
            datos["α"] = alpha

            iteraciones.append(IteracionNL(
                numero=n,
                datos=datos,
                descripcion=f"‖∇f‖ = {norm_grad:.4e}, α = {alpha:.4g}",
            ))

            if norm_grad < tol:
                return RespuestaNoLineal(
                    estado=EstadoProblema.OPTIMO,
                    mensaje=f"Gradiente convergió en {n} iteraciones. ‖∇f‖ < {tol:.0e}",
                    metodo=self.METODO,
                    z_optimo=float(fx), punto_optimo=tuple(float(v) for v in x),
                    iteraciones=iteraciones, columnas=columnas,
                )

            x = x + alpha * direction

        fx = float(f_vec(x))
        norm_final = float(np.linalg.norm(gradiente_numerico(f_desc, x)))
        estado = (EstadoProblema.CONVERGENCIA_TOLERANCIA
                  if norm_final < tol else EstadoProblema.LIMITE_ITERACIONES)

        return RespuestaNoLineal(
            estado=estado,
            mensaje=f"Gradiente se detuvo tras {len(iteraciones)} iteraciones. ‖∇f‖ = {norm_final:.4e}",
            metodo=self.METODO,
            z_optimo=fx, punto_optimo=tuple(float(v) for v in x),
            iteraciones=iteraciones, columnas=columnas,
        )

    def _error(self, problema: ProblemaNoLineal, msg: str) -> RespuestaNoLineal:
        columnas = ["n"] + list(problema.variables) + ["f(x)", "‖∇f‖", "α"]
        return RespuestaNoLineal(
            estado=EstadoProblema.ERROR_VALIDACION_ENTRADA,
            mensaje=msg,
            metodo=self.METODO,
            z_optimo=None, punto_optimo=None,
            iteraciones=[], columnas=columnas,
        )
