# ui/programacion_no_lineal/vista_kkt.py
"""
Vista de Multiplicadores de Lagrange / Condiciones KKT.
Muestra el proceso de optimización restringida y la tabla de condiciones KKT.
"""

from __future__ import annotations
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal, OPCION_KKT
from src.models.entity.programacion_no_lineal.respuesta import CondicionKKT
from ui.programacion_no_lineal._utils_vistas import (
    sin_problema, encabezado_resultado, tabla_iteraciones, panel_sin_datos,
)

ACCENT   = "#7c3aed"
BORDER   = "#2a2d3a"
TEXT_P   = "#f0f0f0"
TEXT_M   = "#6b7280"
BG_CARD  = "#161822"
GREEN    = "#1d9e75"
RED      = "#ef645f"


def _tabla_kkt(condiciones: list[CondicionKKT]) -> ft.Container:
    if not condiciones:
        return panel_sin_datos("Sin condiciones KKT calculadas.")

    encabezados = [
        ft.DataColumn(ft.Text("Condición KKT", size=11, weight=ft.FontWeight.W_700, color=TEXT_M)),
        ft.DataColumn(ft.Text("Expresión", size=11, weight=ft.FontWeight.W_700, color=TEXT_M)),
        ft.DataColumn(ft.Text("Valor", size=11, weight=ft.FontWeight.W_700, color=TEXT_M)),
        ft.DataColumn(ft.Text("¿Satisfecha?", size=11, weight=ft.FontWeight.W_700, color=TEXT_M)),
    ]

    filas = []
    for c in condiciones:
        color_sat = GREEN if c.satisfecha else RED
        icono     = "✓" if c.satisfecha else "✗"
        filas.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(c.nombre,    size=11, color=TEXT_P)),
            ft.DataCell(ft.Text(c.expresion, size=11, color=TEXT_M)),
            ft.DataCell(ft.Text(f"{c.valor:.6g}", size=11, color=TEXT_P)),
            ft.DataCell(ft.Container(
                content=ft.Text(f"{icono}  {'Sí' if c.satisfecha else 'No'}",
                                size=10, color="white", weight=ft.FontWeight.W_700),
                padding=ft.Padding(left=8, right=8, top=4, bottom=4),
                bgcolor=color_sat, border_radius=99,
            )),
        ]))

    return ft.Container(
        content=ft.Column([
            ft.Text("Condiciones KKT", size=13, weight=ft.FontWeight.W_600, color=TEXT_P),
            ft.DataTable(
                columns=encabezados, rows=filas,
                border=ft.Border(
                    top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
                    left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
                ),
                border_radius=8,
                heading_row_color="#1e2130",
                data_row_min_height=38,
                column_spacing=16,
            ),
        ], spacing=10, scroll=ft.ScrollMode.AUTO),
        padding=16, border_radius=10, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
            left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
        ),
    )


def _panel_multiplicadores(multiplicadores: dict | None) -> ft.Container:
    if not multiplicadores:
        return ft.Container()

    chips = [
        ft.Container(
            content=ft.Text(f"{nombre} = {valor:.6g}", size=12, color=TEXT_P),
            padding=ft.Padding(left=12, right=12, top=8, bottom=8),
            bgcolor="#1e2130", border_radius=8,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
                left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
            ),
        )
        for nombre, valor in multiplicadores.items()
    ]

    return ft.Container(
        content=ft.Column([
            ft.Text("Multiplicadores de Lagrange (λ)", size=12,
                    weight=ft.FontWeight.W_700, color=ACCENT),
            ft.Row(chips, spacing=8, wrap=True),
        ], spacing=8),
        padding=14, border_radius=10, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
            left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
        ),
    )


@ft.component
def VistaKKT(controlador: ControladorNoLineal):
    problema = controlador.problema_activo

    if problema is None:
        return sin_problema("KKT / Lagrange",
                            "Define y guarda un problema con restricciones en «Ingresar PNL» primero.")

    if not problema.tiene_restricciones:
        return sin_problema("KKT / Lagrange",
                            "Este método requiere restricciones. "
                            "Añade al menos una restricción en «Ingresar PNL».")

    respuesta = controlador.resolver_NL(problema, OPCION_KKT)
    if respuesta is None:
        return sin_problema("KKT / Lagrange", "Error al ejecutar el solucionador.")

    rests_str = "  ·  ".join(
        f"g{i+1}: {r.expresion} {r.signo} 0"
        for i, r in enumerate(problema.restricciones)
    )

    p0_str = (", ".join(f"{v:.4g}" for v in problema.punto_inicial)
              if problema.punto_inicial else "?")

    header = encabezado_resultado(
        titulo="Multiplicadores de Lagrange / KKT",
        subtitulo=(
            f"{problema.tipo.value} f({', '.join(problema.variables)}) = {problema.funcion_str}  ·  "
            f"x₀ = ({p0_str})\n{rests_str}"
        ),
        respuesta=respuesta,
    )

    mult_panel = _panel_multiplicadores(respuesta.multiplicadores)

    kkt_tabla = _tabla_kkt(respuesta.condiciones_kkt or [])

    iter_tabla = tabla_iteraciones(respuesta)

    nota = ft.Container(
        content=ft.Column([
            ft.Text("Condiciones KKT", size=12, weight=ft.FontWeight.W_700, color=ACCENT),
            ft.Text(
                "1. Estacionariedad:  ∇f(x*) + Σλⱼ·∇gⱼ(x*) = 0\n"
                "2. Factibilidad primal:  gⱼ(x*) ≤ 0  (o = 0 para igualdad)\n"
                "3. Factibilidad dual:  λⱼ ≥ 0  (restricciones de desigualdad)\n"
                "4. Holgura complementaria:  λⱼ · gⱼ(x*) = 0",
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
        [header, ft.Divider(color=BORDER, height=1), nota, mult_panel, kkt_tabla, iter_tabla],
        spacing=16, expand=True, scroll=ft.ScrollMode.AUTO,
    )
