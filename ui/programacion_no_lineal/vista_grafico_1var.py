# ui/programacion_no_lineal/vista_grafico_1var.py
"""
Vista del Método Gráfico para funciones de una sola variable.
Muestra un gráfico real de f(x) en [a, b] con el punto óptimo marcado.
"""

from __future__ import annotations
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal, OPCION_GRAFICO_1VAR
from src.utils.programacion_no_lineal.graficador_1var import generar_grafico_1var
from ui.programacion_no_lineal._utils_vistas import (
    sin_problema, encabezado_resultado,
)

BORDER  = "#2a2d3a"
BG_CARD = "#161822"
TEXT_M  = "#6b7280"
RED     = "#ef645f"


@ft.component
def VistaGrafico1Var(controlador: ControladorNoLineal):
    problema = controlador.problema_activo

    if problema is None:
        return sin_problema(
            "Gráfico (1 Variable)",
            "Define y guarda un problema con intervalo [a, b] en «Ingresar PNL» primero.",
        )

    respuesta = controlador.resolver_NL(problema, OPCION_GRAFICO_1VAR)
    if respuesta is None:
        return sin_problema("Gráfico (1 Variable)", "Error al ejecutar el solucionador.")

    header = encabezado_resultado(
        titulo="Gráfico — f(x) en el intervalo [a, b]",
        subtitulo=(
            f"{problema.tipo.value} f({', '.join(problema.variables)}) = {problema.funcion_str}  ·  "
            f"Intervalo [{problema.intervalo[0] if problema.intervalo else '?'}, "
            f"{problema.intervalo[1] if problema.intervalo else '?'}]"
        ),
        respuesta=respuesta,
    )

    # Generar el gráfico matplotlib
    img_b64 = generar_grafico_1var(problema, respuesta)

    if img_b64:
        img_control = ft.Image(src=img_b64, fit=ft.BoxFit.CONTAIN)
    else:
        img_control = ft.Column([
            ft.Icon(ft.Icons.SHOW_CHART, color=TEXT_M, size=40),
            ft.Text("No fue posible generar el gráfico.", color=RED, size=12,
                    text_align=ft.TextAlign.CENTER),
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    grafico_container = ft.Container(
        content=img_control,
        alignment=ft.alignment.Alignment(0, 0),
        padding=16,
        border_radius=12,
        bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
            left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
        ),
        expand=True,
    )

    return ft.Column(
        [header, ft.Divider(color=BORDER, height=1), grafico_container],
        spacing=16, expand=True, scroll=ft.ScrollMode.AUTO,
    )
