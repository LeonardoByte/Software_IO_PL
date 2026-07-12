# src/models/metodos/programacion_no_lineal/restringida_lineal.py
"""
Optimización NL con restricciones lineales usando SLSQP (scipy).
Registra la trayectoria iteración a iteración via callback.
"""

from __future__ import annotations
from typing import Dict, List

import numpy as np
from scipy.optimize import minimize

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal
from src.models.entity.programacion_no_lineal.respuesta import IteracionNL, RespuestaNoLineal
from src.models.metodos.programacion_no_lineal.evaluador import construir_funcion_vec


class SolucionadorRestringidaLineal:
    METODO = "SLSQP — Restricciones Lineales"

    def resolver(self, problema: ProblemaNoLineal) -> RespuestaNoLineal:
        columnas = ["n"] + list(problema.variables) + ["f(x)"]

        if problema.punto_inicial is None:
            return self._error(problema, columnas, "Debe especificar un punto inicial.")
        if not problema.restricciones:
            return self._error(problema, columnas, "Agrega al menos una restricción lineal.")

        f_vec = construir_funcion_vec(problema.funcion_str, problema.variables)
        es_max = problema.tipo == TipoOptimizacion.MAX
        obj = (lambda x: -f_vec(x)) if es_max else f_vec

        constraints = []
        for rest in problema.restricciones:
            g = construir_funcion_vec(rest.expresion, problema.variables)
            if rest.signo == "<=":
                constraints.append({'type': 'ineq', 'fun': lambda x, _g=g: -_g(x)})
            elif rest.signo == ">=":
                constraints.append({'type': 'ineq', 'fun': lambda x, _g=g: _g(x)})
            elif rest.signo == "==":
                constraints.append({'type': 'eq',   'fun': lambda x, _g=g: _g(x)})

        x0 = np.array([float(v) for v in problema.punto_inicial], dtype=float)
        history: List[np.ndarray] = [x0.copy()]

        def _cb(x):
            history.append(x.copy())

        result = minimize(
            obj, x0,
            method='SLSQP',
            constraints=constraints,
            callback=_cb,
            tol=problema.tolerancia,
            options={'maxiter': problema.max_iteraciones, 'disp': False},
        )

        iteraciones: List[IteracionNL] = []
        for n, x_n in enumerate(history, start=1):
            fx = f_vec(x_n)
            datos: Dict[str, float] = {"n": float(n), "f(x)": fx}
            for var, val in zip(problema.variables, x_n):
                datos[var] = float(val)
            iteraciones.append(IteracionNL(numero=n, datos=datos, descripcion=""))

        x_opt  = result.x
        fx_opt = float(f_vec(x_opt))

        estado = EstadoProblema.OPTIMO if result.success else EstadoProblema.LIMITE_ITERACIONES
        return RespuestaNoLineal(
            estado=estado,
            mensaje=result.message,
            metodo=self.METODO,
            z_optimo=fx_opt,
            punto_optimo=tuple(float(v) for v in x_opt),
            iteraciones=iteraciones,
            columnas=columnas,
        )

    def _error(self, problema: ProblemaNoLineal, columnas: List[str], msg: str) -> RespuestaNoLineal:
        return RespuestaNoLineal(
            estado=EstadoProblema.ERROR_VALIDACION_ENTRADA,
            mensaje=msg, metodo=self.METODO,
            z_optimo=None, punto_optimo=None,
            iteraciones=[], columnas=columnas,
        )
