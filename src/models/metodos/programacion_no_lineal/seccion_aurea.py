# src/models/metodos/programacion_no_lineal/seccion_aurea.py
"""
Búsqueda de la Sección Áurea (Golden Section Search).
Minimiza o maximiza una función unimodal de una variable en [a, b].
"""

from __future__ import annotations
import math
from typing import List

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal
from src.models.entity.programacion_no_lineal.respuesta import IteracionNL, RespuestaNoLineal
from src.models.metodos.programacion_no_lineal.evaluador import construir_funcion

PHI = (math.sqrt(5) - 1) / 2  # ≈ 0.6180339887


class SolucionadorSeccionAurea:
    METODO   = "Sección Áurea"
    COLUMNAS = ["n", "a", "x₁", "x₂", "b", "f(x₁)", "f(x₂)", "b − a"]

    def resolver(self, problema: ProblemaNoLineal) -> RespuestaNoLineal:
        if not problema.es_univariable:
            return self._error("La Sección Áurea requiere exactamente 1 variable.")
        if problema.intervalo is None:
            return self._error("Debe especificar un intervalo [a, b].")
        if problema.intervalo[0] >= problema.intervalo[1]:
            return self._error("El intervalo debe cumplir a < b.")

        f   = construir_funcion(problema.funcion_str, problema.variables)
        a, b = float(problema.intervalo[0]), float(problema.intervalo[1])
        es_max   = problema.tipo == TipoOptimizacion.MAX
        tol      = problema.tolerancia
        max_iter = problema.max_iteraciones

        iteraciones: List[IteracionNL] = []

        for n in range(1, max_iter + 1):
            ancho = b - a
            # Puntos interiores según la razón áurea
            x1 = b - PHI * ancho   # ≈ a + 0.382(b-a)
            x2 = a + PHI * ancho   # ≈ a + 0.618(b-a)
            f1, f2 = f(x1), f(x2)

            # Decisión de eliminación
            if es_max:
                eliminar_derecha = f1 >= f2
            else:
                eliminar_derecha = f1 <= f2

            descripcion = (
                f"f(x₁)={f1:.6g} {'≥' if es_max else '≤'} f(x₂)={f2:.6g} → "
                f"{'eliminar [x₂,b]' if eliminar_derecha else 'eliminar [a,x₁]'}"
            )

            iteraciones.append(IteracionNL(
                numero=n,
                datos={"a": a, "x₁": x1, "x₂": x2, "b": b,
                       "f(x₁)": f1, "f(x₂)": f2, "b − a": ancho},
                descripcion=descripcion,
            ))

            if ancho < tol:
                break

            if eliminar_derecha:
                b = x2
            else:
                a = x1

        x_opt = (a + b) / 2
        z_opt = f(x_opt)

        return RespuestaNoLineal(
            estado=EstadoProblema.OPTIMO,
            mensaje=f"Sección Áurea convergió en {len(iteraciones)} iteraciones. "
                    f"Intervalo final: [{a:.6g}, {b:.6g}]",
            metodo=self.METODO,
            z_optimo=z_opt,
            punto_optimo=(x_opt,),
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
