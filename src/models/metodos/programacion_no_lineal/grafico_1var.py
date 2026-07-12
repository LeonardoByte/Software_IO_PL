# src/models/metodos/programacion_no_lineal/grafico_1var.py
"""
Método Gráfico para una variable: evalúa f(x) en N puntos igualmente espaciados
en [a, b], identifica el óptimo aproximado y las zonas crecientes / decrecientes.
"""

from __future__ import annotations
from typing import List

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal
from src.models.entity.programacion_no_lineal.respuesta import IteracionNL, RespuestaNoLineal
from src.models.metodos.programacion_no_lineal.evaluador import construir_funcion, derivada

N_PUNTOS = 25


class SolucionadorGrafico1Var:
    METODO   = "Gráfico (1 Variable)"
    COLUMNAS = ["n", "x", "f(x)", "f'(x)"]

    def resolver(self, problema: ProblemaNoLineal) -> RespuestaNoLineal:
        if not problema.es_univariable:
            return self._error("El método Gráfico (1 var) requiere exactamente 1 variable.")
        if problema.intervalo is None:
            return self._error("Debe especificar un intervalo [a, b].")
        a_val, b_val = float(problema.intervalo[0]), float(problema.intervalo[1])
        if a_val >= b_val:
            return self._error("El intervalo debe cumplir a < b.")

        f      = construir_funcion(problema.funcion_str, problema.variables)
        es_max = problema.tipo == TipoOptimizacion.MAX
        paso   = (b_val - a_val) / (N_PUNTOS - 1)

        best_x = a_val
        best_f = f(a_val)
        iteraciones: List[IteracionNL] = []

        for i in range(N_PUNTOS):
            x   = a_val + i * paso
            fx  = f(x)
            fpx = derivada(f, x)

            if es_max:
                if fx > best_f:
                    best_f, best_x = fx, x
            else:
                if fx < best_f:
                    best_f, best_x = fx, x

            if abs(fpx) < 1e-3:
                obs = "f'≈0 (extremo)"
            elif fpx > 0:
                obs = "Creciente ↑"
            else:
                obs = "Decreciente ↓"

            iteraciones.append(IteracionNL(
                numero=i + 1,
                datos={"x": x, "f(x)": fx, "f'(x)": fpx},
                descripcion=obs,
            ))

        return RespuestaNoLineal(
            estado=EstadoProblema.OPTIMO,
            mensaje=(
                f"Evaluación en {N_PUNTOS} puntos, paso h = {paso:.4g}. "
                f"{'Máximo' if es_max else 'Mínimo'} aproximado en x ≈ {best_x:.6g}."
            ),
            metodo=self.METODO,
            z_optimo=best_f,
            punto_optimo=(best_x,),
            iteraciones=iteraciones,
            columnas=self.COLUMNAS,
        )

    def _error(self, msg: str) -> RespuestaNoLineal:
        return RespuestaNoLineal(
            estado=EstadoProblema.ERROR_VALIDACION_ENTRADA,
            mensaje=msg,
            metodo=self.METODO,
            z_optimo=None, punto_optimo=None,
            iteraciones=[], columnas=self.COLUMNAS,
        )
