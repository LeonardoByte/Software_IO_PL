# ui/programacion_no_lineal/vista_grafico_nvar.py
"""
Gráfico de curvas de nivel con trayectoria del gradiente para f(x1, x2).
Solo disponible con exactamente 2 variables.
"""

from __future__ import annotations
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal, OPCION_GRADIENTE
from src.utils.programacion_no_lineal.graficador_nvar import generar_grafico_nvar
from ui.programacion_no_lineal._utils_vistas import sin_problema, encabezado_resultado

BORDER  = "#2a2d3a"
BG_CARD = "#161822"
TEXT_M  = "#6b7280"
RED     = "#ef645f"
ACCENT  = "#7c3aed"


def _aviso_n_vars() -> ft.Control:
    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.SHOW_CHART, color=TEXT_M, size=44),
            ft.Text(
                "El gráfico de contorno solo está disponible para 2 variables.",
                color=TEXT_M, size=13, text_align=ft.TextAlign.CENTER,
            ),
            ft.Text(
                "Para más de 2 variables usa la tabla de iteraciones del Gradiente.",
                color=TEXT_M, size=11, text_align=ft.TextAlign.CENTER,
            ),
        ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.Alignment(0, 0),
        expand=True,
    )


@ft.component
def VistaGraficoNVar(controlador: ControladorNoLineal):
    problema = controlador.problema_activo

    if problema is None:
        return sin_problema(
            "Gráfico N Variables",
            "Define y guarda un problema con punto inicial en «Ingresar PNL» primero.",
        )

    if len(problema.variables) != 2:
        return _aviso_n_vars()

    respuesta = controlador.resolver_NL(problema, OPCION_GRADIENTE)
    if respuesta is None:
        return sin_problema("Gráfico N Variables", "Error al ejecutar el solucionador.")

    p0_str = (", ".join(f"{v:.4g}" for v in problema.punto_inicial)
              if problema.punto_inicial else "?")

    header = encabezado_resultado(
        titulo="Gráfico — Curvas de Nivel + Trayectoria del Gradiente",
        subtitulo=(
            f"{problema.tipo.value} f({', '.join(problema.variables)}) = {problema.funcion_str}  ·  "
            f"x₀ = ({p0_str})  ·  tol = {problema.tolerancia:.0e}"
        ),
        respuesta=respuesta,
    )

    img_b64 = generar_grafico_nvar(problema, respuesta)

    if img_b64:
        contenido = ft.Image(src=img_b64, fit=ft.BoxFit.CONTAIN)
    else:
        contenido = ft.Column([
            ft.Icon(ft.Icons.SHOW_CHART, color=TEXT_M, size=40),
            ft.Text("No fue posible generar el gráfico.", color=RED, size=12,
                    text_align=ft.TextAlign.CENTER),
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    grafico_card = ft.Container(
        content=contenido,
        alignment=ft.alignment.Alignment(0, 0),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
            left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
        ),
        expand=True,
    )

    return ft.Column(
        [header, ft.Divider(color=BORDER, height=1), grafico_card],
        spacing=16, expand=True, scroll=ft.ScrollMode.AUTO,
    )
