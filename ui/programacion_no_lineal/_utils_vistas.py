# ui/programacion_no_lineal/_utils_vistas.py
"""
Helpers visuales compartidos por las vistas de resultado no lineal.
"""

from __future__ import annotations
from typing import List
import flet as ft

from src.models.entity.programacion_lineal.enums import EstadoProblema
from src.models.entity.programacion_no_lineal.respuesta import RespuestaNoLineal

ACCENT   = "#7c3aed"
BG_CARD  = "#161822"
BORDER   = "#2a2d3a"
TEXT_P   = "#f0f0f0"
TEXT_M   = "#6b7280"
GREEN    = "#1d9e75"
RED      = "#ef645f"
AMBER    = "#f6ad55"
BLUE     = "#3b82f6"

_ESTADO_COLOR = {
    EstadoProblema.OPTIMO:                     (GREEN,  "Óptimo"),
    EstadoProblema.CONVERGENCIA_TOLERANCIA:    (AMBER,  "Convergencia"),
    EstadoProblema.LIMITE_ITERACIONES:         (AMBER,  "Límite iter."),
    EstadoProblema.PUNTO_ENSILLADURA:          (AMBER,  "Silla de montar"),
    EstadoProblema.ERROR_VALIDACION_ENTRADA:   (RED,    "Error entrada"),
    EstadoProblema.INVIABLE:                   (RED,    "Inviable"),
    EstadoProblema.DIVERGENCIA:                (RED,    "Divergencia"),
    EstadoProblema.DIFICULTADES_NUMERICAS:     (RED,    "Error numérico"),
}


# ── sin problema activo ─────────────────────────────────────────────────────────

def sin_problema(metodo: str, instruccion: str) -> ft.Column:
    return ft.Column([
        ft.Text(metodo, size=20, weight=ft.FontWeight.BOLD, color=TEXT_P),
        ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INFO_OUTLINE, color=ACCENT, size=36),
                ft.Text(instruccion, size=13, color=TEXT_M, text_align=ft.TextAlign.CENTER),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
                left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
            ),
            alignment=ft.alignment.Alignment(0, 0),
        ),
    ], spacing=16, expand=True)


# ── encabezado con resultado óptimo ────────────────────────────────────────────

def encabezado_resultado(titulo: str, subtitulo: str, respuesta: RespuestaNoLineal) -> ft.Column:
    color, etiqueta = _ESTADO_COLOR.get(respuesta.estado, (TEXT_M, respuesta.estado.name))

    badge_estado = ft.Container(
        content=ft.Text(etiqueta, size=10, color="white", weight=ft.FontWeight.W_700),
        padding=ft.Padding(left=10, right=10, top=5, bottom=5),
        bgcolor=color, border_radius=99,
    )

    # resultado óptimo
    if respuesta.z_optimo is not None and respuesta.punto_optimo is not None:
        vars_str = "  ·  ".join(
            f"x{i+1}* = {v:.6g}" if i >= 1 else f"x* = {v:.6g}"
            for i, v in enumerate(respuesta.punto_optimo)
        )
        resultado_card = ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text("Valor óptimo", size=11, color=TEXT_M),
                    ft.Text(f"f(x*) = {respuesta.z_optimo:.8g}",
                            size=20, weight=ft.FontWeight.BOLD, color=color),
                ], spacing=2),
                ft.VerticalDivider(color=BORDER),
                ft.Column([
                    ft.Text("Punto óptimo", size=11, color=TEXT_M),
                    ft.Text(vars_str, size=14, color=TEXT_P, weight=ft.FontWeight.W_500),
                ], spacing=2),
            ], spacing=20),
            padding=16, border_radius=10, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, color + "66"),
                bottom=ft.BorderSide(1, color + "66"),
                left=ft.BorderSide(3, color),
                right=ft.BorderSide(1, color + "66"),
            ),
        )
    else:
        resultado_card = ft.Container()

    mensaje_card = ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.INFO_OUTLINE if color != RED else ft.Icons.WARNING_AMBER,
                    color=color, size=16),
            ft.Text(respuesta.mensaje, size=12, color=color, expand=True),
        ], spacing=8),
        padding=12, border_radius=8, bgcolor=color + "18",
        border=ft.Border(
            top=ft.BorderSide(1, color + "44"), bottom=ft.BorderSide(1, color + "44"),
            left=ft.BorderSide(1, color + "44"), right=ft.BorderSide(1, color + "44"),
        ),
    )

    return ft.Column([
        ft.Row([
            ft.Text(titulo, size=20, weight=ft.FontWeight.BOLD, color=TEXT_P),
            badge_estado,
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Text(subtitulo, size=11, color=TEXT_M),
        resultado_card,
        mensaje_card,
    ], spacing=10)


# ── tabla de iteraciones ────────────────────────────────────────────────────────

def tabla_iteraciones(respuesta: RespuestaNoLineal) -> ft.Container:
    if not respuesta.iteraciones:
        return panel_sin_datos("Sin iteraciones registradas.")

    columnas_display = [c for c in respuesta.columnas if c != "n"]

    encabezados = [
        ft.DataColumn(ft.Text("n", size=11, weight=ft.FontWeight.W_700, color=ACCENT)),
        *[
            ft.DataColumn(ft.Text(col, size=11, weight=ft.FontWeight.W_700, color=TEXT_M))
            for col in columnas_display
        ],
        ft.DataColumn(ft.Text("Acción", size=11, weight=ft.FontWeight.W_700, color=TEXT_M)),
    ]

    filas = []
    for it in respuesta.iteraciones:
        celdas = [ft.DataCell(ft.Text(str(it.numero), size=11, color=TEXT_P))]
        for col in columnas_display:
            val = it.datos.get(col, float("nan"))
            try:
                texto = f"{val:.6g}"
            except Exception:
                texto = str(val)
            celdas.append(ft.DataCell(ft.Text(texto, size=11, color=TEXT_P)))
        celdas.append(ft.DataCell(ft.Text(it.descripcion, size=10, color=TEXT_M)))
        filas.append(ft.DataRow(cells=celdas))

    return ft.Container(
        content=ft.Column([
            ft.Text(f"Tabla de Iteraciones  ({len(respuesta.iteraciones)} pasos)",
                    size=13, weight=ft.FontWeight.W_600, color=TEXT_P),
            ft.DataTable(
                columns=encabezados,
                rows=filas,
                border=ft.border.all(1, BORDER),
                border_radius=8,
                heading_row_color="#1e2130",
                data_row_min_height=36,
                column_spacing=18,
            ),
        ], spacing=10, scroll=ft.ScrollMode.AUTO),
        padding=16, border_radius=10, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
            left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
        ),
    )


# ── panel vacío ─────────────────────────────────────────────────────────────────

def panel_sin_datos(msg: str) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Icon(ft.Icons.TABLE_ROWS_OUTLINED, color=TEXT_M, size=32),
            ft.Text(msg, size=12, color=TEXT_M, text_align=ft.TextAlign.CENTER),
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=30, border_radius=10, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
            left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
        ),
        alignment=ft.alignment.Alignment(0, 0),
    )
