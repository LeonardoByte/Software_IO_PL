# ui/programacion_no_lineal/vista_restringida_lineal.py
"""
Vista para optimización NL con restricciones lineales (SLSQP).
Muestra gráfico de contorno + región factible (solo 2 variables)
y tabla de iteraciones.
"""

from __future__ import annotations
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal, OPCION_RESTRINGIDA_LINEAL
from src.utils.programacion_no_lineal.graficador_restringida import generar_grafico_restringida
from ui.programacion_no_lineal._utils_vistas import (
    sin_problema, encabezado_resultado, tabla_iteraciones,
)

BORDER  = "#2a2d3a"
BG_CARD = "#161822"
TEXT_M  = "#6b7280"
RED     = "#ef645f"
ACCENT  = "#7c3aed"


@ft.component
def VistaRestringidaLineal(controlador: ControladorNoLineal):
    problema = controlador.problema_activo

    if problema is None:
        return sin_problema(
            "Restringida Linealmente",
            "Define y guarda un problema con restricciones en «Ingresar PNL» primero.",
        )

    if not problema.restricciones:
        return sin_problema(
            "Restringida Linealmente",
            "Agrega al menos una restricción lineal en «Ingresar PNL» antes de continuar.",
        )

    if problema.punto_inicial is None:
        return sin_problema(
            "Restringida Linealmente",
            "Especifica el punto inicial x₀ en «Ingresar PNL».",
        )

    respuesta = controlador.resolver_NL(problema, OPCION_RESTRINGIDA_LINEAL)
    if respuesta is None:
        return sin_problema("Restringida Linealmente", "Error al ejecutar el solucionador.")

    p0_str = ", ".join(f"{v:.4g}" for v in problema.punto_inicial)
    rest_str = "  |  ".join(
        f"g{i+1}: {r.expresion} {r.signo} 0"
        for i, r in enumerate(problema.restricciones)
    )

    header = encabezado_resultado(
        titulo="SLSQP — Restricciones Lineales",
        subtitulo=(
            f"{problema.tipo.value} f({', '.join(problema.variables)}) = {problema.funcion_str}  ·  "
            f"x₀ = ({p0_str})  ·  tol = {problema.tolerancia:.0e}\n"
            f"{rest_str}"
        ),
        respuesta=respuesta,
    )

    controles = [header, ft.Divider(color=BORDER, height=1)]

    # Gráfico solo para 2 variables
    if len(problema.variables) == 2:
        img_b64 = generar_grafico_restringida(problema, respuesta)
        if img_b64:
            grafico_card = ft.Container(
                content=ft.Image(src=img_b64, fit=ft.BoxFit.CONTAIN),
                alignment=ft.alignment.Alignment(0, 0),
                padding=16, border_radius=12, bgcolor=BG_CARD,
                border=ft.Border(
                    top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
                    left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
                ),
                expand=True,
            )
            controles.append(grafico_card)
        else:
            controles.append(ft.Text("No fue posible generar el gráfico.", color=RED, size=12))
    else:
        controles.append(ft.Container(
            content=ft.Text(
                "El gráfico de contorno está disponible solo para 2 variables.",
                color=TEXT_M, size=12,
            ),
            padding=8,
        ))

    controles.append(tabla_iteraciones(respuesta))

    return ft.Column(
        controles,
        spacing=16, expand=True, scroll=ft.ScrollMode.AUTO,
    )
