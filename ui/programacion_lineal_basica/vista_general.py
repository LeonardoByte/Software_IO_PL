"""
Refactorizado con Cobertura del 100% de Datos Extra
"""

from __future__ import annotations
from typing import List, Optional
import flet as ft

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.programacion_lineal.problema import ProblemaPL
from src.models.entity.programacion_lineal.respuesta import RespuestaSciPyPL
from src.controller.controlador_lineal import ControladorLineal

# Paleta de colores institucional
ACCENT_COLOR: str = "#7c3aed"
BG_CARD: str = "#161822"
BORDER_COLOR: str = "#2a2d3a"
TEXT_MUTED: str = "#6b7280"
TEXT_PRIMARY: str = "#f0f0f0"
GREEN: str = "#7dd3a8"
AMBER: str = "#f6ad55"
RED: str = "#ef645f"
BLUE: str = "#63b3ed"


def _formatear_funcion_objetivo_ui(tipo: TipoOptimizacion, objetivo: List[float | int]) -> str:
    if not objetivo:
        return f"{tipo.value} Z = 0"
    terminos: List[str] = []
    for i, coef in enumerate(objetivo):
        val_float = float(coef)
        if val_float == 0.0:
            continue
        variable = f"X{i+1}"
        if val_float > 0.0:
            prefijo = "+ " if terminos else ""
            coef_str = f"{val_float:.4g}" if val_float != 1.0 else ""
            terminos.append(f"{prefijo}{coef_str}{variable}")
        else:
            coef_str = f"{abs(val_float):.4g}" if abs(val_float) != 1.0 else ""
            terminos.append(f"- {coef_str}{variable}")
    return f"{tipo.value} Z = {' '.join(terminos) or '0'}"


def _formatear_valor_numerico(valor: Optional[float]) -> str:
    if valor is None:
        return "N/D"
    val_float = float(valor)
    if val_float.is_integer():
        return str(int(val_float))
    texto_formateado = f"{val_float:.6f}".rstrip("0").rstrip(".")
    return texto_formateado if texto_formateado else "0"


def _crear_tarjeta_metrica_ui(titulo: str, valor: str, color_hex: str) -> ft.Container:
    return ft.Container(
        content=ft.Column(
            [
                ft.Text(titulo, size=10, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                ft.Text(valor, size=18, color=color_hex, weight=ft.FontWeight.BOLD),
            ],
            spacing=4
        ),
        padding=16,
        border_radius=10,
        bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
            left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)
        ),
        expand=True,
    )


def _crear_alerta_status(mensaje: str, color_hex: str, icono: ft.Icons = ft.Icons.WARNING_AMBER) -> ft.Row:
    return ft.Row([
        ft.Container(
            content=ft.Row([ft.Icon(icono, color=color_hex, size=15), ft.Text(mensaje, color=color_hex, size=12)], spacing=8),
            padding=14,
            border_radius=8,
            bgcolor=color_hex + "18",
            border=ft.Border(
                top=ft.BorderSide(1, color_hex + "44"), bottom=ft.BorderSide(1, color_hex + "44"),
                left=ft.BorderSide(1, color_hex + "44"), right=ft.BorderSide(1, color_hex + "44")
            ),
        )
    ])


@ft.component
def VistaGeneral(controlador: ControladorLineal, navegar_a=None):
    problema: Optional[ProblemaPL] = controlador.problema_activo

    header = ft.Column([
        ft.Text("Solución Rápida", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Text("Resultado óptimo global calculado de forma analítica mediante algoritmos HiGHS de alto rendimiento.", size=12, color=TEXT_MUTED),
    ], spacing=2)

    # 1. Caso sin problema activo
    if problema is None:
        status_row = _crear_alerta_status("No se encuentra ningún modelo lineal activo. Ingresa parámetros primero.", AMBER, ft.Icons.INFO_OUTLINE)
        placeholder = ft.Container(
            content=ft.Column(
                [
                    ft.Icon(ft.Icons.CALCULATE, color=TEXT_MUTED, size=48),
                    ft.Text("Esperando un modelo matemático activo...", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=48, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
            alignment=ft.alignment.Alignment(0, 0),
        )
        return ft.Column(
            [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, placeholder],
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
        )

    # 2. Resolver problema
    resultado: Optional[RespuestaSciPyPL] = controlador.resolver_LP(problema, 1)

    # 3. Caso sin convergencia óptima
    if resultado is None or resultado.estado != EstadoProblema.OPTIMO:
        mensaje_error = resultado.mensaje if resultado is not None else "Respuesta del motor de cálculo nula."
        status_row = _crear_alerta_status("El modelo ingresado no posee una convergencia óptima.", AMBER, ft.Icons.ERROR_OUTLINE)
        error_container = ft.Container(
            content=ft.Text(mensaje_error, color=AMBER, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.W_500),
            padding=20, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, AMBER + "44"), bottom=ft.BorderSide(1, AMBER + "44"), left=ft.BorderSide(1, AMBER + "44"), right=ft.BorderSide(1, AMBER + "44")),
        )
        return ft.Column(
            [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, error_container],
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
        )

    # 4. Caso óptimo exitoso
    status_row = _crear_alerta_status("Optimización completada con éxito matemático absoluto.", GREEN, ft.Icons.CHECK_CIRCLE)

    fo_formateada = _formatear_funcion_objetivo_ui(problema.tipo, problema.objetivo)
    z_optimo_str = _formatear_valor_numerico(resultado.fun)
    vector_solucion: List[float] = resultado.x if resultado.x is not None else []
    vector_holguras: List[float] = resultado.slack if resultado.slack is not None else []

    # --- Bloque 1: Tarjetas de Métricas Globales ---
    tarjetas_metricas = ft.Row(
        [
            _crear_tarjeta_metrica_ui("Valor Óptimo Z", z_optimo_str, GREEN),
            _crear_tarjeta_metrica_ui("Iteraciones Ejecutadas", str(resultado.nit), BLUE),
            _crear_tarjeta_metrica_ui("Variables / Restr.", f"{problema.total_variables} / {problema.total_restricciones}", AMBER),
        ],
        spacing=10
    )

    # --- Bloque 2: Desglose de las Variables de Decisión Óptimas ---
    tarjeta_valores_variables = ft.Container(
        content=ft.Column(
            [
                ft.Text("Variables de Decisión Óptimas", size=12, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                ft.Row(
                    [
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(f"X{i+1}", size=11, color=TEXT_MUTED),
                                    ft.Text(_formatear_valor_numerico(v), size=16, color=TEXT_PRIMARY, weight=ft.FontWeight.BOLD),
                                ],
                                spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                            ),
                            padding=16, border_radius=8, bgcolor="#1e2130",
                            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                        )
                        for i, v in enumerate(vector_solucion)
                    ],
                    wrap=True, spacing=8
                ),
            ],
            spacing=10
        ),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
    )

    # --- Bloque 3: Desglose de Variables de Holgura y Exceso ---
    controles_holguras = []
    if vector_holguras:
        controles_holguras = [
            ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"Holgura S{j+1}", size=11, color=TEXT_MUTED),
                        ft.Text(_formatear_valor_numerico(h), size=14, color=AMBER if float(h) > 0 else TEXT_MUTED, weight=ft.FontWeight.BOLD),
                    ],
                    spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER
                ),
                padding=12, border_radius=8, bgcolor="#1a1c29",
                border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
            )
            for j, h in enumerate(vector_holguras)
        ]
    
    tarjeta_valores_holguras = ft.Container(
        content=ft.Column(
            [
                ft.Text("Variables de Holgura / Exceso (Slack)", size=12, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                ft.Row(controles_holguras, wrap=True, spacing=8) if controles_holguras else ft.Text("No aplican holguras para este modelo.", size=11, color=TEXT_MUTED, italic=True),
            ],
            spacing=10
        ),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
    )

    # --- Bloque 4: Esqueleto de Ecuación Matemática ---
    tarjeta_fo = ft.Container(
        content=ft.Column(
            [
                ft.Text(fo_formateada, size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
                ft.Text(f"Mensaje del motor: {resultado.mensaje}", size=11, color=TEXT_MUTED, italic=True)
            ],
            spacing=6
        ),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"), left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66")),
    )

    return ft.Column(
        [
            header,
            ft.Divider(color=BORDER_COLOR, height=1),
            status_row,
            tarjeta_fo,
            tarjetas_metricas,
            tarjeta_valores_variables,
            tarjeta_valores_holguras
        ],
        expand=True,
        spacing=16,
        scroll=ft.ScrollMode.AUTO
    )
