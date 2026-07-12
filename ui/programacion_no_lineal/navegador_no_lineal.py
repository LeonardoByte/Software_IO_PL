# ui/programacion_no_lineal/navegador_no_lineal.py
"""
Enrutador del módulo de Programación No Lineal (PNL).
Sidebar con 4 categorías: Sin restr. 1-var / Sin restr. N-vars / Restringida-Cuadrática.
"""

from __future__ import annotations
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal

from ui.programacion_no_lineal.vista_ingreso_nl    import VistaIngresoNL
from ui.programacion_no_lineal.vista_historial_nl  import VistaHistorialNL
from ui.programacion_no_lineal.vista_grafico_1var  import VistaGrafico1Var
from ui.programacion_no_lineal.vista_seccion_aurea import VistaBiseccion
from ui.programacion_no_lineal.vista_newton        import VistaNewton
from ui.programacion_no_lineal.vista_gradiente          import VistaGradiente
from ui.programacion_no_lineal.vista_grafico_nvar       import VistaGraficoNVar
from ui.programacion_no_lineal.vista_restringida_lineal import VistaRestringidaLineal
from ui.programacion_no_lineal.vista_kkt                import VistaKKT

ACCENT        = "#7c3aed"
BG_RAIL       = "#0d0f1a"
BG_MAIN       = "#0f1117"
DIVIDER_COLOR = "#1e2130"
TEXT_DIM      = "#6b7280"

_IDX_INGRESO   = 0
_IDX_HIST      = 1
_IDX_GRAFICO   = 2
_IDX_BISEC     = 3
_IDX_NEWTON    = 4
_IDX_GRAD      = 5
_IDX_KKT       = 6
_IDX_GRAF_NV   = 7
_IDX_REST_LIN  = 8


@ft.component
def NavegadorNoLineal(controlador: ControladorNoLineal):
    selected_index, set_selected_index = ft.use_state(0)

    vista_ingreso_ref = ft.use_ref(None)
    if vista_ingreso_ref.current is None:
        vista_ingreso_ref.current = VistaIngresoNL(controlador, _show_fn(set_selected_index))

    def show_view(index: int) -> None:
        set_selected_index(index)

    def editar_problema(problema: ProblemaNoLineal) -> None:
        controlador.establecer_problema(problema)
        vista_ingreso_ref.current = None  # fuerza reconstrucción con campos pre-rellenos
        set_selected_index(_IDX_INGRESO)

    def create_view(index: int) -> ft.Control:
        match index:
            case 0: return vista_ingreso_ref.current
            case 1: return VistaHistorialNL(controlador, show_view, editar_problema)
            case 2: return VistaGrafico1Var(controlador)
            case 3: return VistaBiseccion(controlador)
            case 4: return VistaNewton(controlador)
            case 5: return VistaGradiente(controlador)
            case 6: return VistaKKT(controlador)
            case 7: return VistaGraficoNVar(controlador)
            case 8: return VistaRestringidaLineal(controlador)
            case _: return vista_ingreso_ref.current

    def _item(icono, etiqueta: str, idx: int) -> ft.Container:
        activo = idx == selected_index
        pill = ft.Container(
            content=ft.Icon(icono, size=18, color="white" if activo else TEXT_DIM),
            width=56, height=32,
            bgcolor=ACCENT if activo else "transparent",
            border_radius=16,
            alignment=ft.alignment.Alignment(0, 0),
        )
        return ft.Container(
            content=ft.Column(
                [
                    pill,
                    ft.Text(
                        etiqueta, size=11,
                        color=ACCENT if activo else TEXT_DIM,
                        text_align=ft.TextAlign.CENTER,
                        weight=ft.FontWeight.W_600 if activo else ft.FontWeight.NORMAL,
                    ),
                ],
                spacing=3,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=ft.Padding(left=4, right=4, top=6, bottom=6),
            on_click=lambda _, i=idx: show_view(i),
        )

    def _header(titulo: str) -> ft.Container:
        return ft.Container(
            content=ft.Text(
                titulo, size=8, color=ACCENT,
                weight=ft.FontWeight.W_700,
                text_align=ft.TextAlign.CENTER,
            ),
            padding=ft.Padding(left=4, right=4, top=10, bottom=2),
        )

    sidebar = ft.Container(
        content=ft.Column(
            controls=[
                _item(ft.Icons.EDIT_NOTE, "Ingresar",  _IDX_INGRESO),
                _item(ft.Icons.HISTORY,   "Historial", _IDX_HIST),

                ft.Divider(color=DIVIDER_COLOR, height=6),
                _header("SIN RESTR.\n1 VARIABLE"),
                _item(ft.Icons.SHOW_CHART,  "Gráfico",   _IDX_GRAFICO),
                _item(ft.Icons.AUTO_GRAPH,  "Bisección", _IDX_BISEC),
                _item(ft.Icons.FUNCTIONS,   "Newton",    _IDX_NEWTON),

                ft.Divider(color=DIVIDER_COLOR, height=6),
                _header("SIN RESTR.\nN VARIABLES"),
                _item(ft.Icons.BUBBLE_CHART,  "Gráfico",   _IDX_GRAF_NV),
                _item(ft.Icons.TRENDING_UP,   "Gradiente", _IDX_GRAD),

                ft.Divider(color=DIVIDER_COLOR, height=6),
                _header("RESTRINGIDA\nLINEALMENTE"),
                _item(ft.Icons.AREA_CHART,    "Gráfico",   _IDX_REST_LIN),

                ft.Divider(color=DIVIDER_COLOR, height=6),
                _header("RESTRINGIDA\nCUADRÁTICA"),
                _item(ft.Icons.ANALYTICS,     "KKT",       _IDX_KKT),
            ],
            spacing=2,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        ),
        bgcolor=BG_RAIL,
        padding=ft.Padding(left=4, right=4, top=8, bottom=8),
        width=92,
    )

    return ft.Row(
        controls=[
            sidebar,
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


def _show_fn(set_fn):
    def _inner(index: int) -> None:
        set_fn(index)
    return _inner
