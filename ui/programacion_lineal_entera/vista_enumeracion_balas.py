"""
vista_enumeracion_balas.py
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Responsable de renderizar las iteraciones y podas del algoritmo de Enumeración Implícita (Balas).
"""

from __future__ import annotations
from typing import Any, List, Optional
import flet as ft

from src.models.entity.programacion_lineal.enums import EstadoProblema
from src.models.entity.programacion_lineal_entera.enums import TipoVariable
from src.models.entity.programacion_lineal_entera.respuesta import RespuestaEnumeracionImplicita, PasoEnumeracion
from src.controller.controlador_entera import ControladorEntera

# Paleta de colores institucional
ACCENT_COLOR: str = "#7c3aed"
BG_CARD: str = "#161822"
BG_TABLE: str = "#0d0f1a"
BORDER_COLOR: str = "#2a2d3a"
TEXT_MUTED: str = "#6b7280"
TEXT_PRIMARY: str = "#f0f0f0"
GREEN: str = "#7dd3a8"
AMBER: str = "#f6ad55"
RED: str = "#ef645f"
BLUE: str = "#63b3ed"

def _formatear_fo(tipo: str, objetivo: list) -> str:
    if not objetivo:
        return f"{tipo} Z = 0"
    terminos = []
    for i, coef in enumerate(objetivo):
        try:
            c = float(coef)
        except Exception:
            c = 0.0
        if c == 0:
            continue
        var = f"X{i+1}"
        if c > 0:
            terminos.append(
                f"{'+ ' if terminos else ''}{c:.4g}{var}"
                if abs(c) != 1 else f"{'+ ' if terminos else ''}{var}"
            )
        else:
            terminos.append(
                f"- {abs(c):.4g}{var}" if abs(c) != 1 else f"- {var}"
            )
    return f"{tipo} Z = {' '.join(terminos) or '0'}"

def _crear_alerta_status(mensaje: str, color_hex: str, icono: ft.Icons = ft.Icons.WARNING_AMBER) -> ft.Row:
    return ft.Row([
        ft.Container(
            content=ft.Row([ft.Icon(icono, color=color_hex, size=15), ft.Text(mensaje, color=color_hex, size=12)], spacing=8),
            padding=14, border_radius=8, bgcolor=color_hex + "18",
            border=ft.Border(
                top=ft.BorderSide(1, color_hex + "44"), bottom=ft.BorderSide(1, color_hex + "44"),
                left=ft.BorderSide(1, color_hex + "44"), right=ft.BorderSide(1, color_hex + "44")
            ),
        )
    ])

def _formatear_combinacion(combinacion: List[Optional[int]]) -> str:
    parts = []
    for idx, val in enumerate(combinacion):
        if val is None:
            parts.append(f"X{idx+1}=Libre")
        else:
            parts.append(f"X{idx+1}={val}")
    return ", ".join(parts)

def _crear_tabla_visual_pasos(pasos: List[PasoEnumeracion], num_original_vars: int) -> ft.Control:
    columns = [
        ft.DataColumn(ft.Text("Paso", weight=ft.FontWeight.BOLD, size=12, color="white")),
        ft.DataColumn(ft.Text("Combinación", weight=ft.FontWeight.BOLD, size=12, color="white")),
        ft.DataColumn(ft.Text("Z Local", weight=ft.FontWeight.BOLD, size=12, color="white")),
        ft.DataColumn(ft.Text("Factible", weight=ft.FontWeight.BOLD, size=12, color="white")),
        ft.DataColumn(ft.Text("Decisión / Acción", weight=ft.FontWeight.BOLD, size=12, color="white")),
    ]

    rows = []
    for idx, paso in enumerate(pasos, start=1):
        # Filtrar combinación a mostrar solo para variables originales
        combinacion_filtrada = paso.combinacion[:num_original_vars]
        comb_str = _formatear_combinacion(combinacion_filtrada)
        
        z_str = f"{paso.z_local:.4g}"
        fact_str = "Sí" if paso.factible else "No"
        fact_color = GREEN if paso.factible else RED
        
        cells = [
            ft.DataCell(ft.Text(str(idx), size=12, weight=ft.FontWeight.BOLD, color=BLUE)),
            ft.DataCell(ft.Text(comb_str, size=12, color=TEXT_PRIMARY)),
            ft.DataCell(ft.Text(z_str, size=12, color=AMBER, weight=ft.FontWeight.BOLD)),
            ft.DataCell(ft.Container(
                content=ft.Text(fact_str, size=10, color="white", weight=ft.FontWeight.W_600),
                padding=6, bgcolor=fact_color, border_radius=4
            )),
            ft.DataCell(ft.Text(paso.decision, size=12, color=TEXT_MUTED, italic=True)),
        ]
        
        rows.append(ft.DataRow(cells=cells, color={"": BG_TABLE}))

    tabla = ft.DataTable(
        columns=columns,
        rows=rows,
        border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "55"), bottom=ft.BorderSide(1, ACCENT_COLOR + "55"), left=ft.BorderSide(1, ACCENT_COLOR + "55"), right=ft.BorderSide(1, ACCENT_COLOR + "55")),
        heading_row_color={"": ACCENT_COLOR},
        data_row_color={"": BG_TABLE}, 
        heading_row_height=42,
        divider_thickness=0.5,
    )

    return ft.Container(
        content=ft.Row([tabla], scroll=ft.ScrollMode.AUTO),
        padding=12, border_radius=10, bgcolor=BG_TABLE,
        border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
    )

def _tarjeta_resumen(resultado: RespuestaEnumeracionImplicita, num_original_vars: int, problema: any) -> ft.Container:
    tipo = problema.tipo.value
    objetivo = problema.objetivo
    fo_str = _formatear_fo(tipo, objetivo)

    z_str = f"{resultado.z_optimo}" if resultado.z_optimo is not None else "N/D"
    
    variables_filtradas = (resultado.variables_decision or [])[:num_original_vars]
    vars_str = ", ".join(f"X{i+1}={v}" for i, v in enumerate(variables_filtradas)) or "N/D"
    steps_count = len(resultado.pasos)

    def _stat(titulo: str, valor: str, color: str) -> ft.Container:
        return ft.Container(
            content=ft.Column([
                ft.Text(titulo, size=10, color=TEXT_MUTED),
                ft.Text(valor, size=17, color=color, weight=ft.FontWeight.BOLD),
            ], spacing=2),
            padding=14, border_radius=8, bgcolor="#1e2130",
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
                left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR),
            ),
        )

    return ft.Container(
        content=ft.Column([
            ft.Text(fo_str, size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
            ft.Row([
                _stat("Z óptimo binario", z_str, GREEN),
                _stat("Variables óptimas", vars_str, TEXT_PRIMARY),
                _stat("Pasos realizados", str(steps_count), BLUE),
            ], spacing=8, wrap=True),
        ], spacing=10),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"),
            left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66"),
        ),
    )

@ft.component
def VistaEnumeracionBalas(controlador: ControladorEntera):
    resultado_ref = ft.use_ref(None)
    problema_ref  = ft.use_ref(None)

    problema_actual = controlador.problema_activo

    # Solo resolver si el problema cambió Y es todo binario
    es_todo_binario = (
        problema_actual is not None and
        all(t == TipoVariable.BINARIA for t in problema_actual.tipos_variables)
    )
    if (resultado_ref.current is None or problema_ref.current is not problema_actual) and es_todo_binario:
        problema_ref.current = problema_actual
        try:
            resultado_ref.current = controlador.resolver_PLE(problema_actual, 3)
        except Exception:
            resultado_ref.current = None
    elif problema_ref.current is not problema_actual:
        problema_ref.current = problema_actual
        resultado_ref.current = None

    problema = problema_actual
    resultado = resultado_ref.current

    header = ft.Column([
        ft.Text("Enumeración Implícita (Balas)", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Text("Resolución mediante el algoritmo aditivo de Balas para modelos binarios.", size=12, color=TEXT_MUTED),
    ], spacing=2)

    # 1. Caso sin problema activo
    if problema is None:
        status_row = _crear_alerta_status("Ingresa o selecciona un problema binario primero.", AMBER, ft.Icons.INFO_OUTLINE)
        placeholder = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.TABLE_CHART, color=TEXT_MUTED, size=48),
                ft.Text("Sin modelo activo en la sesión.", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=48, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)), alignment=ft.alignment.Alignment(0, 0),
        )
        return ft.Column(
            [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, placeholder],
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
        )

    # 2. Validar que todas las variables de decisión sean binarias
    if not all(t == TipoVariable.BINARIA for t in problema.tipos_variables):
        status_row = _crear_alerta_status("El algoritmo de Balas requiere que TODAS las variables de decisión sean Binarias (B).", AMBER, ft.Icons.WARNING_AMBER)
        placeholder = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.LOCK, color=AMBER, size=48),
                ft.Text("Algoritmo no disponible", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
                ft.Text("Edita tu modelo en Ingresar PI para definir todas las variables como Binarias.", color=TEXT_MUTED, size=11, text_align=ft.TextAlign.CENTER),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=48, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)), alignment=ft.alignment.Alignment(0, 0),
        )
        return ft.Column(
            [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, placeholder],
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
        )

    # 3. Excepción
    if resultado is None:
        status_row = _crear_alerta_status("El motor matemático interrumpió el proceso inesperadamente.", RED, ft.Icons.ERROR_OUTLINE)
        error_container = ft.Container(
            content=ft.Text("Excepción en la obtención de la enumeración binaria.", color=RED),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, RED + "44"), bottom=ft.BorderSide(1, RED + "44"), left=ft.BorderSide(1, RED + "44"), right=ft.BorderSide(1, RED + "44")),
        )
        return ft.Column(
            [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, error_container],
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
        )

    # 5. Estado
    if resultado.estado == EstadoProblema.OPTIMO:
        status_row = _crear_alerta_status("Óptimo binario global alcanzado con éxito.", GREEN, ft.Icons.CHECK_CIRCLE)
    elif resultado.estado == EstadoProblema.INVIABLE:
        status_row = _crear_alerta_status("Inviabilidad: No hay solución binaria factible.", RED, ft.Icons.ERROR_OUTLINE)
    else:
        status_row = _crear_alerta_status(f"Conclusión: {resultado.estado.value}", AMBER, ft.Icons.INFO_OUTLINE)

    num_original_vars = len(problema.objetivo)
    
    resultados_column = ft.Column([
        _tarjeta_resumen(resultado, num_original_vars, problema),
        ft.Text("Pasos de la enumeración y ramificaciones de combinaciones", size=12, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
        _crear_tabla_visual_pasos(resultado.pasos, num_original_vars)
    ], spacing=14)

    return ft.Column(
        [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, resultados_column],
        expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
    )
