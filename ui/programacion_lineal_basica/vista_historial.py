# vista_historial.py
"""
vista_historial.py
==================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Se encarga de renderizar de forma elegante y asíncrona el histórico de modelos.
"""

from __future__ import annotations
from typing import List
import flet as ft

from src.models.entity.programacion_lineal.enums import TipoOptimizacion
from src.models.entity.programacion_lineal.problema import ProblemaPL, Restriccion
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


def _formatear_funcion_objetivo_pedagogica(tipo: TipoOptimizacion, objetivo: List[float | int]) -> str:
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


def _badge_ui(texto: str, color_hex: str) -> ft.Container:
    return ft.Container(
        content=ft.Text(texto, size=10, color="white", weight=ft.FontWeight.W_600),
        padding=ft.Padding.all(6),
        bgcolor=color_hex,
        border_radius=99,
    )


def _boton_accion_ui(texto: str, icono: ft.Icons, on_click, color: str = ACCENT_COLOR) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(icono, size=14, color="white"), 
                ft.Text(texto, size=11, color="white")
            ],
            spacing=5, 
            tight=True,
        ),
        bgcolor=color,
        on_click=on_click,
    )


@ft.component
def VistaHistorial(controlador: ControladorLineal, navegar_a=None, ir_a_ingreso=None):
    refresh_trigger, set_refresh_trigger = ft.use_state(0)
    status_text_val, set_status_text_val = ft.use_state(("", "")) # (message, color)

    historial: List[ProblemaPL] = controlador.obtener_historial_completo()

    def manejador_cargar_problema(indice: int) -> None:
        controlador.obtener_problema_por_indice(indice)
        set_status_text_val(("Modelo cargado como problema activo en la sesión.", GREEN))
        if navegar_a:
            navegar_a(2)
        else:
            set_refresh_trigger(lambda x: x + 1)

    def manejador_clonar_y_editar(indice: int) -> None:
        controlador.obtener_problema_por_indice(indice)
        set_status_text_val(("Modelo clonado. Puedes alterar sus celdas en la ventana de ingreso.", AMBER))
        if ir_a_ingreso:
            ir_a_ingreso()
        elif navegar_a:
            navegar_a(0)
        else:
            set_refresh_trigger(lambda x: x + 1)

    def manejador_eliminar_problema(indice: int) -> None:
        controlador.eliminar_problema_por_indice(indice)
        set_status_text_val(("✕ El problema seleccionado ha sido eliminado de la memoria.", RED))
        set_refresh_trigger(lambda x: x + 1)

    def formatear_restricciones_preview(restricciones: List[Restriccion]) -> str:
        partes: List[str] = []
        for r in restricciones[:3]:
            terminos = " + ".join(
                f"{float(c):.4g}X{i+1}" 
                for i, c in enumerate(r.coeficientes) 
                if float(c) != 0.0
            ).replace("+ -", "- ")
            partes.append(f"{terminos} {r.signo.value} {float(r.rhs):.4g}")
            
        if len(restricciones) > 3:
            partes.append(f"... y {len(restricciones) - 3} restricciones más.")
            
        return "\n".join(partes)

    def crear_tarjeta_problema(indice: int, problema: ProblemaPL) -> ft.Container:
        fo_algebraica = _formatear_funcion_objetivo_pedagogica(problema.tipo, problema.objetivo)
        badge_color = "#1d9e75" if problema.tipo == TipoOptimizacion.MAX else "#2563eb"

        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Row([
                        ft.Text(f"Problema #{indice+1}", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                        _badge_ui(problema.tipo.value, badge_color),
                        _badge_ui(f"{problema.total_variables} variables", "#374151"),
                        _badge_ui(f"{problema.total_restricciones} restricciones", "#374151"),
                    ], spacing=8),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),

                ft.Container(
                    content=ft.Text(
                        fo_algebraica, size=13, color=TEXT_PRIMARY, 
                        weight=ft.FontWeight.W_500, selectable=True
                    ),
                    padding=12,
                    bgcolor="#1e2130",
                    border_radius=8,
                    border=ft.Border(
                        top=ft.BorderSide(1, "#2a2d3a"), bottom=ft.BorderSide(1, "#2a2d3a"), 
                        left=ft.BorderSide(1, "#2a2d3a"), right=ft.BorderSide(1, "#2a2d3a")
                    ),
                ),

                ft.Text(
                    formatear_restricciones_preview(problema.restricciones),
                    size=11, color=TEXT_MUTED,
                ),

                ft.Row([
                    _boton_accion_ui(
                        "Cargar y Activar", ft.Icons.UPLOAD, 
                        lambda _e, idx=indice: manejador_cargar_problema(idx)
                    ),
                    _boton_accion_ui(
                        "Clonar y Editar", ft.Icons.CONTENT_COPY,
                        lambda _e, idx=indice: manejador_clonar_y_editar(idx), color="#374151"
                    ),
                    _boton_accion_ui(
                        "Eliminar", ft.Icons.DELETE_OUTLINE,
                        lambda _e, idx=indice: manejador_eliminar_problema(idx), color="#7f1d1d"
                    ),
                ], spacing=8, wrap=True),
            ], spacing=10),
            padding=16,
            border_radius=12,
            bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), 
                left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)
            ),
        )

    # 1. Cabecera
    header = ft.Column([
        ft.Text("Historial de Problemas", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Text("Consulta, carga, clona/edita o elimina problemas guardados desde los objetos de dominio.", size=12, color=TEXT_MUTED),
    ], spacing=2)

    # 2. Barra de Estado
    if status_text_val[0]:
        icono = ft.Icons.CHECK_CIRCLE if status_text_val[1] == GREEN else (
            ft.Icons.DELETE if status_text_val[1] == RED else ft.Icons.INFO
        )
        status_row = ft.Row([
            ft.Container(
                content=ft.Row([ft.Icon(icono, color=status_text_val[1], size=15), ft.Text(status_text_val[0], color=status_text_val[1], size=12)], spacing=8),
                padding=14, border_radius=8, bgcolor=status_text_val[1] + "18",
                border=ft.Border(
                    top=ft.BorderSide(1, status_text_val[1] + "44"), bottom=ft.BorderSide(1, status_text_val[1] + "44"), 
                    left=ft.BorderSide(1, status_text_val[1] + "44"), right=ft.BorderSide(1, status_text_val[1] + "44")
                ),
            )
        ])
    else:
        status_row = ft.Container()

    # 3. Listado de tarjetas
    if not historial:
        cards_layout = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.INBOX, color=TEXT_MUTED, size=40),
                ft.Text("No existen modelos registrados en el historial de sesión.", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
                ft.Text("Construye y valida un problema desde la ventana de ingreso para persistirlo.", color="#4a4f66", size=11, text_align=ft.TextAlign.CENTER),
            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
                left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)
            ),
            alignment=ft.alignment.Alignment(0, 0),
        )
    else:
        cards_layout = ft.Column(
            [crear_tarjeta_problema(i, p) for i, p in enumerate(historial)],
            spacing=10, expand=True
        )

    return ft.Column(
        [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, cards_layout],
        expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
    )
