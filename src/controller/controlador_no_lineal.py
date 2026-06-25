# src/controller/controlador_no_lineal.py
"""
Controlador de Programación No Lineal.
Orquesta los solucionadores matemáticos y el historial de sesión.
"""

from __future__ import annotations
from typing import List, Optional, Union

from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal
from src.models.entity.programacion_no_lineal.respuesta import RespuestaNoLineal
from src.models.metodos.programacion_no_lineal.seccion_aurea import SolucionadorSeccionAurea
from src.models.metodos.programacion_no_lineal.newton import SolucionadorNewton
from src.models.metodos.programacion_no_lineal.gradiente import SolucionadorGradiente
from src.models.metodos.programacion_no_lineal.kkt import SolucionadorKKT
from src.models.metodos.programacion_no_lineal.historial_de_problemas import HistorialProblemasNL


# Opciones de método
OPCION_SECCION_AUREA = 1
OPCION_NEWTON        = 2
OPCION_GRADIENTE     = 3
OPCION_KKT           = 4


class ControladorNoLineal:
    """Punto de entrada para resolver, guardar y recuperar problemas no lineales."""

    _solver_aurea    = SolucionadorSeccionAurea()
    _solver_newton   = SolucionadorNewton()
    _solver_gradiente = SolucionadorGradiente()
    _solver_kkt      = SolucionadorKKT()
    _historial       = HistorialProblemasNL()

    def __init__(self) -> None:
        self._problema_activo: Optional[ProblemaNoLineal] = None

    # ── problema activo ────────────────────────────────────────────────────────

    @property
    def problema_activo(self) -> Optional[ProblemaNoLineal]:
        return self._problema_activo

    def establecer_problema(self, problema: ProblemaNoLineal) -> None:
        self._problema_activo = problema

    # ── resolución ─────────────────────────────────────────────────────────────

    def resolver_NL(
        self,
        problema: ProblemaNoLineal,
        opcion: int,
    ) -> Optional[RespuestaNoLineal]:
        match opcion:
            case 1: return self._solver_aurea.resolver(problema)
            case 2: return self._solver_newton.resolver(problema)
            case 3: return self._solver_gradiente.resolver(problema)
            case 4: return self._solver_kkt.resolver(problema)
            case _: return None

    # ── historial ──────────────────────────────────────────────────────────────

    def guardar_en_historial(self, problema: ProblemaNoLineal) -> None:
        self._historial.guardar(problema)

    def obtener_historial_completo(self) -> List[ProblemaNoLineal]:
        return self._historial.obtener_todos()

    def obtener_problema_por_indice(self, indice: int) -> None:
        """Carga el problema del historial como problema activo."""
        p = self._historial.obtener_por_indice(indice)
        if p is not None:
            self._problema_activo = p

    def eliminar_problema_por_indice(self, indice: int) -> None:
        self._historial.eliminar_por_indice(indice)
