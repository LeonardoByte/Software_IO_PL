# src/models/metodos/programacion_no_lineal/kkt.py
"""
Solver KKT / Multiplicadores de Lagrange.
Usa scipy.optimize.minimize (SLSQP) para encontrar x*, luego calcula
los multiplicadores λ resolviendo el sistema de estacionariedad y
construye la tabla de condiciones KKT para mostrar en la vista.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Tuple

import numpy as np
from scipy.optimize import minimize as scipy_minimize

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal
from src.models.entity.programacion_no_lineal.respuesta import (
    CondicionKKT, IteracionNL, RespuestaNoLineal,
)
from src.models.metodos.programacion_no_lineal.evaluador import (
    construir_funcion_vec, gradiente_numerico,
)

_TOL_SAT = 1e-4   # tolerancia para marcar condición como satisfecha


class SolucionadorKKT:
    METODO   = "Multiplicadores de Lagrange / KKT"
    COLUMNAS = ["Iteración", "f(x)", "Violación restricciones", "‖∇L‖"]

    def resolver(self, problema: ProblemaNoLineal) -> RespuestaNoLineal:
        if problema.punto_inicial is None:
            return self._error("Debe especificar un punto inicial.")
        if not problema.tiene_restricciones:
            return self._error(
                "KKT/Lagrange requiere al menos una restricción. "
                "Para problemas irrestrictos usa Gradiente o Newton."
            )

        f_vec  = construir_funcion_vec(problema.funcion_str, problema.variables)
        es_max = problema.tipo == TipoOptimizacion.MAX
        f_opt  = (lambda x: -f_vec(x)) if es_max else f_vec

        x0 = np.array([float(v) for v in problema.punto_inicial], dtype=float)

        # Construir restricciones para SLSQP
        scipy_constraints = []
        g_funcs: List[callable] = []

        for r in problema.restricciones:
            from src.models.metodos.programacion_no_lineal.evaluador import construir_funcion_vec as cfv
            g_vec = cfv(r.expresion, problema.variables)
            g_funcs.append(g_vec)

            if r.signo == "==":
                scipy_constraints.append({"type": "eq",   "fun": g_vec})
            elif r.signo == "<=":
                # g(x) <= 0  →  SLSQP ineq: -g(x) >= 0
                g_v = g_vec
                scipy_constraints.append({"type": "ineq", "fun": lambda x, gv=g_v: -gv(x)})
            elif r.signo == ">=":
                scipy_constraints.append({"type": "ineq", "fun": g_vec})

        iteraciones: List[IteracionNL] = []
        callback_iters: List[Tuple[np.ndarray, float]] = []

        def _callback(xk):
            fk = float(f_vec(xk))
            viol = sum(max(0.0, float(g(xk))) for g in g_funcs
                       if problema.restricciones[g_funcs.index(g)].signo in ("<=", ">="))
            eq_viol = sum(abs(float(g(xk))) for g, r in zip(g_funcs, problema.restricciones)
                         if r.signo == "==")
            viol_total = viol + eq_viol
            lagr_grad_norm = float(np.linalg.norm(gradiente_numerico(f_opt, xk)))
            callback_iters.append((xk.copy(), fk, viol_total, lagr_grad_norm))

        result = scipy_minimize(
            f_opt, x0,
            method="SLSQP",
            constraints=scipy_constraints,
            callback=_callback,
            options={"ftol": problema.tolerancia, "maxiter": problema.max_iteraciones, "disp": False},
        )

        # Construir tabla de iteraciones desde el callback
        for k, (xk, fk, viol, lagr_n) in enumerate(callback_iters, start=1):
            iteraciones.append(IteracionNL(
                numero=k,
                datos={"Iteración": float(k), "f(x)": fk,
                       "Violación restricciones": viol, "‖∇L‖": lagr_n},
                descripcion=f"f(x) = {fk:.6g}",
            ))

        x_star = result.x
        z_star = float(f_vec(x_star))

        # Calcular multiplicadores λ resolviendo ∇f(x*) + G^T λ = 0
        grad_f = gradiente_numerico(f_opt if not es_max else lambda x: f_vec(x), x_star)
        G_matrix = np.zeros((len(problema.variables), len(g_funcs)))
        for j, g in enumerate(g_funcs):
            G_matrix[:, j] = gradiente_numerico(g, x_star)

        lambdas = np.zeros(len(g_funcs))
        if G_matrix.shape[1] > 0:
            try:
                lambdas, *_ = np.linalg.lstsq(G_matrix, -grad_f, rcond=None)
            except np.linalg.LinAlgError:
                pass

        multiplicadores: Dict[str, float] = {
            f"λ{i+1}": float(lambdas[i]) for i in range(len(lambdas))
        }

        # Construir condiciones KKT para mostrar en la vista
        condiciones: List[CondicionKKT] = []

        # 1. Estacionariedad
        lag_grad = grad_f + G_matrix @ lambdas
        for i, var in enumerate(problema.variables):
            val = float(lag_grad[i])
            condiciones.append(CondicionKKT(
                nombre=f"Estacionariedad ∂L/∂{var}",
                expresion=f"∂f/∂{var} + Σλⱼ·∂gⱼ/∂{var} = 0",
                valor=val,
                satisfecha=abs(val) < _TOL_SAT,
            ))

        # 2. Factibilidad primal + holgura complementaria
        for i, (r, g) in enumerate(zip(problema.restricciones, g_funcs)):
            gx = float(g(x_star))
            lam = float(lambdas[i]) if i < len(lambdas) else 0.0

            if r.signo == "==":
                condiciones.append(CondicionKKT(
                    nombre=f"Factibilidad primal g{i+1}(x*) = 0",
                    expresion=f"g{i+1}(x*)",
                    valor=gx,
                    satisfecha=abs(gx) < _TOL_SAT,
                ))
            else:
                # Factibilidad
                condiciones.append(CondicionKKT(
                    nombre=f"Factibilidad primal g{i+1}(x*) {r.signo} 0",
                    expresion=f"g{i+1}(x*)",
                    valor=gx,
                    satisfecha=(gx <= _TOL_SAT if r.signo == "<=" else gx >= -_TOL_SAT),
                ))
                # Dual feasibility λ ≥ 0
                condiciones.append(CondicionKKT(
                    nombre=f"Factibilidad dual λ{i+1} ≥ 0",
                    expresion=f"λ{i+1}",
                    valor=lam,
                    satisfecha=(lam >= -_TOL_SAT),
                ))
                # Complementary slackness
                cs_val = lam * gx
                condiciones.append(CondicionKKT(
                    nombre=f"Holgura complementaria λ{i+1}·g{i+1}(x*) = 0",
                    expresion=f"λ{i+1} · g{i+1}(x*)",
                    valor=cs_val,
                    satisfecha=abs(cs_val) < _TOL_SAT,
                ))

        todas_sat = all(c.satisfecha for c in condiciones)
        estado = EstadoProblema.OPTIMO if (result.success and todas_sat) else EstadoProblema.CONVERGENCIA_TOLERANCIA

        return RespuestaNoLineal(
            estado=estado,
            mensaje=(f"{'Solución KKT verificada' if todas_sat else 'Solución aproximada — revisar condiciones KKT'}. "
                     f"f(x*) = {z_star:.6g}"),
            metodo=self.METODO,
            z_optimo=z_star,
            punto_optimo=tuple(float(v) for v in x_star),
            iteraciones=iteraciones,
            columnas=self.COLUMNAS,
            multiplicadores=multiplicadores,
            condiciones_kkt=condiciones,
        )

    def _error(self, msg: str) -> RespuestaNoLineal:
        return RespuestaNoLineal(
            estado=EstadoProblema.ERROR_VALIDACION_ENTRADA,
            mensaje=msg,
            metodo=self.METODO,
            z_optimo=None, punto_optimo=None,
            iteraciones=[], columnas=self.COLUMNAS,
        )
