"""
Enrutador raíz de la aplicación. Maneja el cambio de contexto global entre
las distintas familias de algoritmos (Lineal Continua vs Lineal Entera).
"""

import flet as ft
from src.controller.controlador_principal import ControladorPrincipal
from ui.programacion_lineal_basica.navegador_lineal import NavegadorLineal
from ui.programacion_lineal_entera.navegador_entera import NavegadorEntera
from ui.programacion_no_lineal.navegador_no_lineal import NavegadorNoLineal

BG_MAIN = "#0f1117"

@ft.component

def NavegadorPrincipal(controlador_fachada: ControladorPrincipal):
    selected_index, set_selected_index = ft.use_state(0)

    # Cache sub-navigators to persist their internal navigation states
    nav_lineal_ref = ft.use_ref(None)
    if nav_lineal_ref.current is None:
        nav_lineal_ref.current = NavegadorLineal(controlador_fachada.lineal)

    nav_entera_ref = ft.use_ref(None)
    if nav_entera_ref.current is None:
        nav_entera_ref.current = NavegadorEntera(controlador_fachada.entera)

    nav_no_lineal_ref = ft.use_ref(None)
    if nav_no_lineal_ref.current is None:
        nav_no_lineal_ref.current = NavegadorNoLineal(controlador_fachada.no_lineal)

    def cambiar_modulo(e: ft.ControlEvent) -> None:
        #Conmuta el sub-enrutador activo según la pestaña seleccionada
        indice = int(getattr(e.control, "selected_index", 0))
        set_selected_index(indice)

    tab_bar = ft.TabBar(
        tabs=[
            ft.Tab(label="Programación Lineal",         icon=ft.Icons.BAR_CHART),
            ft.Tab(label="Programación Lineal Entera",  icon=ft.Icons.ACCOUNT_TREE),
            ft.Tab(label="Programación No Lineal",      icon=ft.Icons.FUNCTIONS),
        ]
    )

    return ft.Tabs(
        length=3,
        selected_index=selected_index,
        on_change=cambiar_modulo,
        animation_duration=500,
        expand=True,
        content=ft.Column(
            expand=True,
            controls=[
                tab_bar,
                ft.TabBarView(
                    expand=True,
                    controls=[
                        ft.Container(content=nav_lineal_ref.current),
                        ft.Container(content=nav_entera_ref.current),
                        ft.Container(content=nav_no_lineal_ref.current),
                    ],
                ),
            ],
        ),
    )
