# ui/programacion_no_lineal/vista_seccion_aurea.py
"""
Vista del método de Sección Áurea.
Muestra la tabla de reducción de intervalo iteración a iteración.
"""

from __future__ import annotations
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal, OPCION_SECCION_AUREA
from src.models.entity.programacion_lineal.enums import EstadoProblema
from src.models.entity.programacion_no_lineal.respuesta import RespuestaNoLineal
from ui.programacion_no_lineal._utils_vistas import (
    sin_problema, encabezado_resultado, tabla_iteraciones, panel_sin_datos,
)

ACCENT  = "#7c3aed"
BORDER  = "#2a2d3a"
TEXT_P  = "#f0f0f0"
TEXT_M  = "#6b7280"
GREEN   = "#1d9e75"
RED     = "#ef645f"
AMBER   = "#f6ad55"
BG_CARD = "#161822"


@ft.component
def VistaSeccionAurea(controlador: ControladorNoLineal):
    problema = controlador.problema_activo

    if problema is None:
        return sin_problema("Sección Áurea", "Define y guarda un problema en «Ingresar PNL» primero.")

    respuesta: RespuestaNoLineal = controlador.resolver_NL(problema, OPCION_SECCION_AUREA)

    if respuesta is None:
        return sin_problema("Sección Áurea", "Error al ejecutar el solucionador.")

    # ── cabecera y resultado ────────────────────────────────────────────────────
    header = encabezado_resultado(
        titulo="Sección Áurea — Reducción de Intervalo",
        subtitulo=(
            f"{problema.tipo.value} f({', '.join(problema.variables)}) = {problema.funcion_str}  ·  "
            f"Intervalo [{problema.intervalo[0] if problema.intervalo else '?'}, "
            f"{problema.intervalo[1] if problema.intervalo else '?'}]  ·  "
            f"tol = {problema.tolerancia:.0e}"
        ),
        respuesta=respuesta,
    )

    # ── tabla de iteraciones ────────────────────────────────────────────────────
    tabla = tabla_iteraciones(respuesta)

    # ── nota educativa ──────────────────────────────────────────────────────────
    nota = ft.Container(
        content=ft.Column([
            ft.Text("Cómo funciona", size=12, weight=ft.FontWeight.W_700, color=ACCENT),
            ft.Text(
                "φ = (√5 − 1) / 2 ≈ 0.618  (razón áurea)\n"
                "En cada iteración: x₁ = b − φ(b−a),  x₂ = a + φ(b−a)\n"
                "Se elimina el subintervalo que NO puede contener el óptimo.\n"
                "El intervalo se reduce por un factor φ en cada paso.",
                size=12, color=TEXT_M,
            ),
        ], spacing=6),
        padding=14, border_radius=10, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
            left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
        ),
    )

    return ft.Column(
        [header, ft.Divider(color=BORDER, height=1), nota, tabla],
        spacing=16, expand=True, scroll=ft.ScrollMode.AUTO,
    )
