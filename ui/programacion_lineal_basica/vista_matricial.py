# ui/programacion_lineal_basica/vista_matricial.py
"""
vista_matricial.py
==================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Responsable del renderizado paso a paso de los solucionadores algebraicos
tabulares (Simplex, Gran M y Dos Fases).
"""

from __future__ import annotations
from typing import List, Optional
import flet as ft

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.programacion_lineal.problema import ProblemaPL
from src.models.entity.programacion_lineal.respuesta import RespuestaTabularPL, IteracionTabular
from src.utils.programacion_lineal_basica.herramientas_calculo import AnalizadorMatematico
from src.utils.programacion_lineal_basica.localizador_ui import LocalizadorUI
from src.controller.controlador_lineal import ControladorLineal

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


def _crear_tabla_visual(iteracion: IteracionTabular, opcion_resolucion: int) -> ft.Control:
    filas_matriz = iteracion.tabla.tolist()
    encabezado = iteracion.encabezados
    evaluar_gran_m = (opcion_resolucion == 3)

    if not filas_matriz:
        return ft.Container(
            content=ft.Text("Iteración sin matriz de datos.", color=TEXT_MUTED, italic=True),
            padding=12, border_radius=10, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
        )

    columns = [
        ft.DataColumn(ft.Text(str(col), weight=ft.FontWeight.BOLD, size=12, color="white"))
        for col in encabezado
    ]

    rows = []
    for idx_fila, fila_datos in enumerate(filas_matriz):
        cells = []
        for idx_col, valor_crudo in enumerate(fila_datos):
            texto_valor = AnalizadorMatematico.formatear_valor_pedagogico(valor_crudo, evaluar_m=evaluar_gran_m)
            color_texto = TEXT_PRIMARY
            peso_texto = ft.FontWeight.NORMAL
            bg_celda = None

            if idx_col == 0:
                peso_texto = ft.FontWeight.BOLD
                color_texto = BLUE if idx_fila == 0 else GREEN

            es_pivote = LocalizadorUI.es_celda_pivote(iteracion, idx_fila, idx_col)
            if es_pivote:
                color_texto = "white"
                peso_texto = ft.FontWeight.BOLD
                bg_celda = AMBER + "44"

            texto_ui = ft.Text(texto_valor, size=12, color=color_texto, weight=peso_texto)
            if bg_celda:
                content_celda = ft.Container(content=texto_ui, bgcolor=bg_celda, padding=4, border_radius=4)
            else:
                content_celda = texto_ui

            cells.append(ft.DataCell(content_celda))
        
        es_fila_objetivo = (idx_fila == 0)
        color_fila_base = ACCENT_COLOR + "33" if es_fila_objetivo else None
        
        rows.append(ft.DataRow(
            cells=cells,
            color={"": color_fila_base} if color_fila_base else {"": BG_TABLE},
        ))

    tabla_control = ft.DataTable(
        columns=columns,
        rows=rows,
        border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "55"), bottom=ft.BorderSide(1, ACCENT_COLOR + "55"), left=ft.BorderSide(1, ACCENT_COLOR + "55"), right=ft.BorderSide(1, ACCENT_COLOR + "55")),
        heading_row_color={"": ACCENT_COLOR},
        data_row_color={"": BG_TABLE}, 
        heading_row_height=42,
        data_row_max_height=44,
        data_row_min_height=40,
        horizontal_margin=12,
        column_spacing=20,
        divider_thickness=0.5,
    )

    return ft.Container(
        content=ft.Row([tabla_control], scroll=ft.ScrollMode.AUTO),
        padding=12, border_radius=10, bgcolor=BG_TABLE,
        border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
    )


def _renderizar_paneles_resultados(resultado: RespuestaTabularPL, problema: ProblemaPL, opcion_resolucion: int) -> List[ft.Control]:
    controles: List[ft.Control] = []

    fo_str = _formatear_funcion_objetivo_ui(problema.tipo, problema.objetivo)
    variables = resultado.variables_decision or []
    z_val = AnalizadorMatematico.formatear_valor_pedagogico(resultado.z_optimo) if resultado.z_optimo is not None else "N/D"
    texto_vars = ", ".join(f"X{i+1} = {AnalizadorMatematico.formatear_valor_pedagogico(v)}" for i, v in enumerate(variables)) if variables else "N/D"

    controles.append(
        ft.Container(
            content=ft.Column([
                ft.Text(fo_str, size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
                ft.Row([
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Z óptimo (Matricial)", size=10, color=TEXT_MUTED),
                            ft.Text(z_val, size=18, color=GREEN, weight=ft.FontWeight.BOLD),
                        ], spacing=2),
                        padding=16, border_radius=8, bgcolor="#1e2130", border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                    ),
                    ft.Container(
                        content=ft.Column([
                            ft.Text("Variables Evaluadas", size=10, color=TEXT_MUTED),
                            ft.Text(texto_vars, size=13, color=TEXT_PRIMARY),
                        ], spacing=2),
                        padding=16, border_radius=8, bgcolor="#1e2130", border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                    ),
                ], spacing=8, wrap=True),
                ft.Text(f"Motivo de parada: {resultado.estado.value}", size=11, color=TEXT_MUTED, italic=True),
            ], spacing=10),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"), left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66")),
        )
    )

    if not resultado.iteraciones:
        return controles

    for idx, iteracion in enumerate(resultado.iteraciones, start=1):
        fase_num = iteracion.fase
        msg_iter = iteracion.mensaje

        componentes_titulo = [ft.Text(f"Iteración {idx}", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)]
        if fase_num is not None:
            color_fase = "#1d9e75" if fase_num == 1 else "#2563eb"
            componentes_titulo.append(
                ft.Container(
                    content=ft.Text(f"Fase {fase_num}", size=10, color="white", weight=ft.FontWeight.W_600),
                    padding=8, bgcolor=color_fase, border_radius=99,
                )
            )

        controles.append(
            ft.Container(
                content=ft.Column([
                    ft.Row(componentes_titulo, spacing=8),
                    ft.Text(msg_iter, size=12, color=TEXT_MUTED) if msg_iter else ft.Container(),
                    _crear_tabla_visual(iteracion, opcion_resolucion),
                ], spacing=10),
                padding=16, border_radius=12, bgcolor=BG_CARD,
                border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
            )
        )

    return controles


@ft.component
def VistaMatricial(controlador: ControladorLineal, opcion_resolucion: int, titulo: str, descripcion: str, navegar_a=None):
    problema: Optional[ProblemaPL] = controlador.problema_activo

    header = ft.Column([
        ft.Text(titulo, size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Text(descripcion, size=12, color=TEXT_MUTED),
    ], spacing=2)

    # 1. Caso sin problema activo
    if problema is None:
        status_row = _crear_alerta_status("Ingresa o selecciona un problema matemático primero.", AMBER, ft.Icons.INFO_OUTLINE)
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

    # 2. Resolver
    resultado: Optional[RespuestaTabularPL] = controlador.resolver_LP(problema, opcion_resolucion)

    # 3. Excepción
    if resultado is None:
        status_row = _crear_alerta_status("El motor matemático interrumpió el proceso inesperadamente.", RED, ft.Icons.ERROR_OUTLINE)
        error_container = ft.Container(
            content=ft.Text("Excepción en la obtención de resultados algebraicos.", color=RED),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, RED + "44"), bottom=ft.BorderSide(1, RED + "44"), left=ft.BorderSide(1, RED + "44"), right=ft.BorderSide(1, RED + "44")),
        )
        return ft.Column(
            [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, error_container],
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
        )

    # 4. Traducción de estado
    if resultado.estado == EstadoProblema.OPTIMO:
        status_row = _crear_alerta_status("Proceso concluido. Óptimo alcanzado.", GREEN, ft.Icons.CHECK_CIRCLE)
        controles_resultado = [header, ft.Divider(color=BORDER_COLOR, height=1), status_row,
                               ft.Column(_renderizar_paneles_resultados(resultado, problema, opcion_resolucion), spacing=14)]
        return ft.Column(controles_resultado, expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)
    elif resultado.estado == EstadoProblema.REQUIERE_OTRO_METODO:
        status_row = _crear_alerta_status("Desajuste de algoritmo: Las restricciones del modelo no encajan con este método.", AMBER, ft.Icons.WARNING_AMBER)
    else:
        status_row = _crear_alerta_status(f"Conclusión: {resultado.estado.value}", AMBER, ft.Icons.INFO_OUTLINE)

    # Estado no óptimo
    return ft.Column(
        [header, ft.Divider(color=BORDER_COLOR, height=1), status_row],
        expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
    )