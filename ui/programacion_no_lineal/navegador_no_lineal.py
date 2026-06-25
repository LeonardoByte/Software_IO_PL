# ui/programacion_no_lineal/navegador_no_lineal.py
"""
Enrutador del módulo de Programación No Lineal (PNL).
Barra lateral izquierda con 6 destinos: Ingresar, Historial y 4 métodos.
"""

from __future__ import annotations
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal

from ui.programacion_no_lineal.vista_ingreso_nl     import VistaIngresoNL
from ui.programacion_no_lineal.vista_historial_nl   import VistaHistorialNL
from ui.programacion_no_lineal.vista_seccion_aurea  import VistaSeccionAurea
from ui.programacion_no_lineal.vista_newton         import VistaNewton
from ui.programacion_no_lineal.vista_gradiente      import VistaGradiente
from ui.programacion_no_lineal.vista_kkt            import VistaKKT

ACCENT_COLOR  = "#7c3aed"
BG_RAIL       = "#0d0f1a"
BG_MAIN       = "#0f1117"
DIVIDER_COLOR = "#1e2130"


@ft.component
def NavegadorNoLineal(controlador: ControladorNoLineal):
    selected_index, set_selected_index = ft.use_state(0)

    def show_view(index: int) -> None:
        set_selected_index(index)

    # Cache del formulario de ingreso para preservar los campos mientras se navega
    vista_ingreso_ref = ft.use_ref(None)
    if vista_ingreso_ref.current is None:
        vista_ingreso_ref.current = VistaIngresoNL(controlador, show_view)

    def on_nav_change(e: ft.ControlEvent) -> None:
        indice = int(e.control.selected_index)
        show_view(indice)

    def create_view(index: int) -> ft.Control:
        match index:
            case 0: return vista_ingreso_ref.current
            case 1: return VistaHistorialNL(controlador, show_view)
            case 2: return VistaSeccionAurea(controlador)
            case 3: return VistaNewton(controlador)
            case 4: return VistaGradiente(controlador)
            case 5: return VistaKKT(controlador)
            case _: return vista_ingreso_ref.current

    destinations = [
        ft.NavigationRailDestination(icon=ft.Icons.EDIT_NOTE,      label="Ingresar PNL"),
        ft.NavigationRailDestination(icon=ft.Icons.HISTORY,        label="Historial PNL"),
        ft.NavigationRailDestination(icon=ft.Icons.AUTO_GRAPH,     label="Sección Áurea"),
        ft.NavigationRailDestination(icon=ft.Icons.SHOW_CHART,     label="Newton"),
        ft.NavigationRailDestination(icon=ft.Icons.TRENDING_UP,    label="Gradiente"),
        ft.NavigationRailDestination(icon=ft.Icons.FUNCTIONS,      label="KKT / Lagrange"),
    ]

    nav = ft.NavigationRail(
        selected_index=selected_index,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=80,
        extended=False,
        bgcolor=BG_RAIL,
        indicator_color=ACCENT_COLOR,
        destinations=destinations,
        on_change=on_nav_change,
        selected_label_text_style=ft.TextStyle(color=ACCENT_COLOR, size=11),
        unselected_label_text_style=ft.TextStyle(color="#6b7280", size=11),
    )

    return ft.Row(
        controls=[
            nav,
            ft.VerticalDivider(width=1, color=DIVIDER_COLOR),
            ft.Container(
                content=create_view(selected_index),
                expand=True,
                padding=20,
                bgcolor=BG_MAIN,
            ),
        ],
        spacing=0,
        expand=True,
    )
