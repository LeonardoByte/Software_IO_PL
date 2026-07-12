# ui/programacion_no_lineal/vista_gradiente.py
"""
Vista del Método del Gradiente (Steepest Ascent / Descent).
"""

from __future__ import annotations
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal, OPCION_GRADIENTE
from ui.programacion_no_lineal._utils_vistas import (
    sin_problema, encabezado_resultado, tabla_iteraciones,
)

ACCENT  = "#7c3aed"
BORDER  = "#2a2d3a"
TEXT_P  = "#f0f0f0"
TEXT_M  = "#6b7280"
BG_CARD = "#161822"


@ft.component
def VistaGradiente(controlador: ControladorNoLineal):
    problema = controlador.problema_activo

    if problema is None:
        return sin_problema("Método del Gradiente",
                            "Define y guarda un problema en «Ingresar PNL» primero.")

    respuesta = controlador.resolver_NL(problema, OPCION_GRADIENTE)
    if respuesta is None:
        return sin_problema("Método del Gradiente", "Error al ejecutar el solucionador.")

    p0_str = (", ".join(f"{v:.4g}" for v in problema.punto_inicial)
              if problema.punto_inicial else "?")

    header = encabezado_resultado(
        titulo=f"Gradiente — Steepest {'Ascent' if problema.tipo.value == 'MAX' else 'Descent'}",
        subtitulo=(
            f"{problema.tipo.value} f({', '.join(problema.variables)}) = {problema.funcion_str}  ·  "
            f"x₀ = ({p0_str})  ·  tol = {problema.tolerancia:.0e}"
        ),
        respuesta=respuesta,
    )

    tabla = tabla_iteraciones(respuesta)

    return ft.Column(
        [header, ft.Divider(color=BORDER, height=1), tabla],
        spacing=16, expand=True, scroll=ft.ScrollMode.AUTO,
    )
