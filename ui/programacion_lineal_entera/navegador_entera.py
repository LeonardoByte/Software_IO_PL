# ui/programacion_lineal_entera/navegador_entera.py
"""
navegador_entera.py
===================
Enrutador especializado para la familia de Programación Lineal Entera (PI).
"""

import flet as ft
from src.controller.controlador_entera import ControladorEntera

# Importaciones de las nuevas vistas de PLE
from ui.programacion_lineal_entera.vista_ingreso_pi import VistaIngresoPi
from ui.programacion_lineal_entera.vista_historial_pi import VistaHistorialPi
from ui.programacion_lineal_entera.vista_branch_bound import VistaBranchBound
from ui.programacion_lineal_entera.vista_cortes_gomory import VistaCortesGomory
from ui.programacion_lineal_entera.vista_enumeracion_balas import VistaEnumeracionBalas

ACCENT_COLOR, BG_RAIL, BG_MAIN, DIVIDER_COLOR = "#7c3aed", "#0d0f1a", "#0f1117", "#1e2130"

@ft.component
def NavegadorEntera(controlador: ControladorEntera):
    selected_index, set_selected_index = ft.use_state(0)

    # Callback para cambiar vistas
    def show_view(index: int) -> None:
        set_selected_index(index)

    def on_nav_change(e: ft.ControlEvent) -> None:
        nav_rail = e.control
        indice = int(nav_rail.selected_index)
        show_view(indice)

    def create_view(index: int) -> ft.Control:
        match index:
            case 0: return VistaIngresoPi(controlador, show_view)
            case 1: return VistaHistorialPi(controlador, show_view)
            case 2: return VistaBranchBound(controlador)
            case 3: return VistaCortesGomory(controlador)
            case 4: return VistaEnumeracionBalas(controlador)
            # Fallback en caso de que vuelva a cargar vista ingreso
            case _: return VistaIngresoPi(controlador, show_view)

    destinations = [
        ft.NavigationRailDestination(icon=ft.Icons.EDIT_NOTE, label="Ingresar PI"),
        ft.NavigationRailDestination(icon=ft.Icons.HISTORY, label="Historial PI"),
        ft.NavigationRailDestination(icon=ft.Icons.ACCOUNT_TREE, label="Branch & Bound"),
        ft.NavigationRailDestination(icon=ft.Icons.TABLE_ROWS, label="Cortes Gomory"),
        ft.NavigationRailDestination(icon=ft.Icons.LAYERS, label="Enum. Balas"),
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
                bgcolor=BG_MAIN
            ),
        ],
        spacing=0,
        expand=True,
    )
