# ui/programacion_no_lineal/vista_newton.py
"""
Vista del Método de Newton para optimización de una variable.
"""

from __future__ import annotations
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal, OPCION_NEWTON
from ui.programacion_no_lineal._utils_vistas import (
    sin_problema, encabezado_resultado, tabla_iteraciones,
)

ACCENT  = "#7c3aed"
BORDER  = "#2a2d3a"
TEXT_P  = "#f0f0f0"
TEXT_M  = "#6b7280"
BG_CARD = "#161822"


@ft.component
def VistaNewton(controlador: ControladorNoLineal):
    problema = controlador.problema_activo

    if problema is None:
        return sin_problema("Newton (1 Variable)", "Define y guarda un problema en «Ingresar PNL» primero.")

    respuesta = controlador.resolver_NL(problema, OPCION_NEWTON)
    if respuesta is None:
        return sin_problema("Newton (1 Variable)", "Error al ejecutar el solucionador.")

    header = encabezado_resultado(
        titulo="Newton — Optimización 1 Variable",
        subtitulo=(
            f"{problema.tipo.value} f({', '.join(problema.variables)}) = {problema.funcion_str}  ·  "
            f"x₀ = {problema.punto_inicial[0] if problema.punto_inicial else '?'}  ·  "
            f"tol = {problema.tolerancia:.0e}"
        ),
        respuesta=respuesta,
    )

    tabla = tabla_iteraciones(respuesta)

    return ft.Column(
        [header, ft.Divider(color=BORDER, height=1), tabla],
        spacing=16, expand=True, scroll=ft.ScrollMode.AUTO,
    )
