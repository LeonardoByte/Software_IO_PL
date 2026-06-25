# ui/programacion_no_lineal/vista_historial_nl.py
"""
Historial de problemas no lineales guardados en la sesión.
"""

from __future__ import annotations
from typing import Callable, List
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal

ACCENT   = "#7c3aed"
BG_CARD  = "#161822"
BORDER   = "#2a2d3a"
TEXT_P   = "#f0f0f0"
TEXT_M   = "#6b7280"
GREEN    = "#1d9e75"
RED      = "#ef645f"
AMBER    = "#f6ad55"


def _badge(texto: str, color: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(texto, size=10, color="white", weight=ft.FontWeight.W_600),
        padding=ft.Padding(left=8, right=8, top=4, bottom=4),
        bgcolor=color, border_radius=99,
    )


def _boton(texto: str, icono, on_click, color: str = ACCENT) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        content=ft.Row([
            ft.Icon(icono, size=14, color="white"),
            ft.Text(texto, size=11, color="white"),
        ], spacing=5, tight=True),
        bgcolor=color, on_click=on_click,
    )


def _resumen_vars(p: ProblemaNoLineal) -> str:
    partes = []
    if p.intervalo:
        partes.append(f"[{p.intervalo[0]:.4g}, {p.intervalo[1]:.4g}]")
    if p.punto_inicial:
        partes.append(f"x₀ = ({', '.join(f'{v:.4g}' for v in p.punto_inicial)})")
    if p.tiene_restricciones:
        partes.append(f"{len(p.restricciones)} restricción(es)")
    return " · ".join(partes) if partes else "Sin parámetros adicionales"


@ft.component
def VistaHistorialNL(controlador: ControladorNoLineal, navegar_a: Callable = None):
    refresh, set_refresh = ft.use_state(0)
    status_msg, set_status = ft.use_state(("", ""))

    historial: List[ProblemaNoLineal] = controlador.obtener_historial_completo()

    def cargar(idx: int):
        controlador.obtener_problema_por_indice(idx)
        set_status(("Problema cargado como activo.", GREEN))
        if navegar_a:
            navegar_a(0)

    def eliminar(idx: int):
        controlador.eliminar_problema_por_indice(idx)
        set_status(("Problema eliminado.", RED))
        set_refresh(lambda x: x + 1)

    def crear_tarjeta(idx: int, p: ProblemaNoLineal) -> ft.Container:
        tipo_color = "#1d9e75" if p.tipo.value == "MAX" else "#2563eb"
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(f"Problema PNL #{idx+1}", size=14,
                            weight=ft.FontWeight.W_600, color=TEXT_P),
                    _badge(p.tipo.value, tipo_color),
                    _badge(f"{p.n_variables} variable(s)", "#374151"),
                ], spacing=8),
                ft.Container(
                    content=ft.Text(
                        f"{p.tipo.value} f({', '.join(p.variables)}) = {p.funcion_str}",
                        size=13, color=TEXT_P, weight=ft.FontWeight.W_500, selectable=True,
                    ),
                    padding=12, bgcolor="#1e2130", border_radius=8,
                    border=ft.Border(
                        top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
                        left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
                    ),
                ),
                ft.Text(_resumen_vars(p), size=11, color=TEXT_M),
                ft.Row([
                    _boton("Cargar y Activar", ft.Icons.UPLOAD,
                           lambda _e, i=idx: cargar(i)),
                    _boton("Eliminar", ft.Icons.DELETE_OUTLINE,
                           lambda _e, i=idx: eliminar(i), color="#7f1d1d"),
                ], spacing=8),
            ], spacing=10),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
                left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
            ),
        )

    # estado
    if status_msg[0]:
        color = status_msg[1]
        icono = ft.Icons.CHECK_CIRCLE if color == GREEN else ft.Icons.DELETE
        barra = ft.Container(
            content=ft.Row([
                ft.Icon(icono, color=color, size=15),
                ft.Text(status_msg[0], color=color, size=12),
            ], spacing=8),
            padding=14, border_radius=8, bgcolor=color + "18",
            border=ft.Border(
                top=ft.BorderSide(1, color + "44"), bottom=ft.BorderSide(1, color + "44"),
                left=ft.BorderSide(1, color + "44"), right=ft.BorderSide(1, color + "44"),
            ),
        )
    else:
        barra = ft.Container()

    if not historial:
        contenido = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INBOX, color=TEXT_M, size=40),
                ft.Text("No hay problemas guardados.", color=TEXT_M, size=13,
                        text_align=ft.TextAlign.CENTER),
                ft.Text("Define un problema en «Ingresar PNL» y presiona «Guardar».",
                        color="#4a4f66", size=11, text_align=ft.TextAlign.CENTER),
            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
                left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
            ),
            alignment=ft.alignment.Alignment(0, 0),
        )
    else:
        contenido = ft.Column(
            [crear_tarjeta(i, p) for i, p in enumerate(historial)],
            spacing=10, expand=True,
        )

    return ft.Column(
        [
            ft.Column([
                ft.Text("Historial de Problemas PNL", size=20,
                        weight=ft.FontWeight.BOLD, color=TEXT_P),
                ft.Text("Problemas no lineales guardados en esta sesión.",
                        size=12, color=TEXT_M),
            ], spacing=2),
            ft.Divider(color=BORDER, height=1),
            barra,
            contenido,
        ],
        spacing=16, expand=True, scroll=ft.ScrollMode.AUTO,
    )
