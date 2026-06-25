# src/models/metodos/programacion_no_lineal/newton.py
"""
Método de Newton para optimización de una sola variable.
Itera x_{k+1} = x_k − f'(x_k) / f''(x_k) hasta |f'(x)| < tol.
"""

from __future__ import annotations
from typing import List

from src.models.entity.programacion_lineal.enums import EstadoProblema
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal
from src.models.entity.programacion_no_lineal.respuesta import IteracionNL, RespuestaNoLineal
from src.models.metodos.programacion_no_lineal.evaluador import (
    construir_funcion, derivada, segunda_derivada,
)


class SolucionadorNewton:
    METODO   = "Método de Newton (1 Variable)"
    COLUMNAS = ["n", "x_k", "f(x_k)", "f'(x_k)", "f''(x_k)", "|f'(x_k)|", "x_{k+1}"]

    def resolver(self, problema: ProblemaNoLineal) -> RespuestaNoLineal:
        if not problema.es_univariable:
            return self._error("Newton 1D requiere exactamente 1 variable.")
        if problema.punto_inicial is None:
            return self._error("Debe especificar un punto inicial x₀.")

        f_raw = construir_funcion(problema.funcion_str, problema.variables)
        f     = lambda x: f_raw(x)

        x        = float(problema.punto_inicial[0])
        tol      = problema.tolerancia
        max_iter = problema.max_iteraciones
        iteraciones: List[IteracionNL] = []

        for n in range(1, max_iter + 1):
            fx   = f(x)
            fpx  = derivada(f, x)
            fppx = segunda_derivada(f, x)
            abs_fp = abs(fpx)

            if abs(fppx) < 1e-14:
                iteraciones.append(IteracionNL(
                    numero=n,
                    datos={"x_k": x, "f(x_k)": fx, "f'(x_k)": fpx,
                           "f''(x_k)": fppx, "|f'(x_k)|": abs_fp, "x_{k+1}": float("nan")},
                    descripcion="f''(x) ≈ 0 — posible punto de inflexión o silla de montar.",
                ))
                return RespuestaNoLineal(
                    estado=EstadoProblema.PUNTO_ENSILLADURA,
                    mensaje=f"f''(x) ≈ 0 en x = {x:.6g}. No se puede continuar.",
                    metodo=self.METODO,
                    z_optimo=fx, punto_optimo=(x,),
                    iteraciones=iteraciones, columnas=self.COLUMNAS,
                )

            x_new = x - fpx / fppx

            iteraciones.append(IteracionNL(
                numero=n,
                datos={"x_k": x, "f(x_k)": fx, "f'(x_k)": fpx,
                       "f''(x_k)": fppx, "|f'(x_k)|": abs_fp, "x_{k+1}": x_new},
                descripcion=f"x_{n+1} = {x:.6g} − ({fpx:.6g})/({fppx:.6g}) = {x_new:.6g}",
            ))

            if abs_fp < tol:
                return RespuestaNoLineal(
                    estado=EstadoProblema.OPTIMO,
                    mensaje=f"Newton convergió en {n} iteraciones. |f'(x)| = {abs_fp:.2e} < {tol:.0e}",
                    metodo=self.METODO,
                    z_optimo=fx, punto_optimo=(x,),
                    iteraciones=iteraciones, columnas=self.COLUMNAS,
                )

            if abs(x_new - x) < tol * 1e-3:
                x = x_new
                break

            x = x_new

        fx = f(x)
        return RespuestaNoLineal(
            estado=EstadoProblema.CONVERGENCIA_TOLERANCIA,
            mensaje=f"Newton se detuvo tras {len(iteraciones)} iteraciones. x* ≈ {x:.6g}",
            metodo=self.METODO,
            z_optimo=fx, punto_optimo=(x,),
            iteraciones=iteraciones, columnas=self.COLUMNAS,
        )

    def _error(self, msg: str) -> RespuestaNoLineal:
        return RespuestaNoLineal(
            estado=EstadoProblema.ERROR_VALIDACION_ENTRADA,
            mensaje=msg,
            metodo=self.METODO,
            z_optimo=None, punto_optimo=None,
            iteraciones=[], columnas=self.COLUMNAS,
        )
