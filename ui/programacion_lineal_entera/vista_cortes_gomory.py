# ui/programacion_lineal_entera/vista_cortes_gomory.py
"""
vista_cortes_gomory.py
======================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Responsable del renderizado de la tabla de iteraciones de los Cortes de Gomory.
"""

from __future__ import annotations
from typing import List, Optional
import flet as ft
import numpy as np

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion
from src.models.entity.programacion_lineal.respuesta import IteracionTabular
from src.models.entity.programacion_lineal_entera.respuesta import RespuestaPlanoCorte
from src.utils.programacion_lineal_basica.herramientas_calculo import AnalizadorMatematico
from src.utils.programacion_lineal_basica.localizador_ui import LocalizadorUI
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

def _formatear_funcion_objetivo_ui(tipo: TipoOptimizacion, objetivo: List[any]) -> str:
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

def _crear_tabla_visual(iteracion: IteracionTabular) -> ft.Control:
    filas_matriz = iteracion.tabla.tolist()
    encabezado = iteracion.encabezados

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
            texto_valor = AnalizadorMatematico.formatear_valor_pedagogico(valor_crudo, evaluar_m=False)
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

# Límite duro de tablas construidas en un solo render, incluso dentro de una
# única página/corte: un corte patológico con cientos de pasos de pivoteo no
# debe poder congelar la vista por sí solo.
MAX_TABLAS_POR_PAGINA: int = 30

def _calcular_paginas(resultado: RespuestaPlanoCorte) -> List[List[IteracionTabular]]:
    """
    Agrupa las iteraciones planas de la respuesta en una lista de páginas,
    una por corte de Gomory (o por la relajación inicial, en la página 0).
    """
    if not resultado.iteraciones:
        return []
    if not resultado.iteraciones_por_corte or sum(resultado.iteraciones_por_corte) != len(resultado.iteraciones):
        # Respaldo defensivo si el conteo por corte no está disponible o no cuadra:
        # tratar todo como una sola página en vez de fallar.
        return [resultado.iteraciones]

    paginas: List[List[IteracionTabular]] = []
    cursor = 0
    for cantidad in resultado.iteraciones_por_corte:
        paginas.append(resultado.iteraciones[cursor:cursor + cantidad])
        cursor += cantidad
    return paginas

def _renderizar_pagina(pagina: List[IteracionTabular], indice_pagina: int, offset_paso: int) -> List[ft.Control]:
    controles: List[ft.Control] = []

    mostrar = pagina
    truncado = len(pagina) > MAX_TABLAS_POR_PAGINA
    if truncado:
        mitad = MAX_TABLAS_POR_PAGINA // 2
        mostrar = pagina[:mitad]

    for offset, iteracion in enumerate(mostrar):
        idx = offset_paso + offset + 1
        controles.append(_renderizar_tarjeta_paso(iteracion, idx))

    if truncado:
        n_omitidos = len(pagina) - MAX_TABLAS_POR_PAGINA
        controles.append(
            _crear_alerta_status(
                f"{n_omitidos} pasos intermedios omitidos en este corte para mantener la vista responsiva.",
                AMBER, ft.Icons.MORE_HORIZ
            )
        )
        for offset, iteracion in enumerate(pagina[-(MAX_TABLAS_POR_PAGINA - mitad):]):
            idx = offset_paso + (len(pagina) - (MAX_TABLAS_POR_PAGINA - mitad)) + offset + 1
            controles.append(_renderizar_tarjeta_paso(iteracion, idx))

    return controles

def _renderizar_tarjeta_paso(iteracion: IteracionTabular, idx: int) -> ft.Control:
    fase_num = iteracion.fase
    msg_iter = iteracion.mensaje

    componentes_titulo = [ft.Text(f"Paso {idx}", size=14, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY)]
    if fase_num is not None:
        color_fase = "#1d9e75" if fase_num == 1 else "#2563eb"
        componentes_titulo.append(
            ft.Container(
                content=ft.Text(f"Fase {fase_num}", size=10, color="white", weight=ft.FontWeight.W_600),
                padding=8, bgcolor=color_fase, border_radius=99,
            )
        )

    return ft.Container(
        content=ft.Column([
            ft.Row(componentes_titulo, spacing=8),
            ft.Text(msg_iter, size=12, color=TEXT_MUTED) if msg_iter else ft.Container(),
            _crear_tabla_visual(iteracion),
        ], spacing=10),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
    )

def _renderizar_resumen(resultado: RespuestaPlanoCorte, problema: any) -> ft.Control:
    fo_str = _formatear_funcion_objetivo_ui(problema.tipo, problema.objetivo)

    # Mostrar solo variables originales
    variables_originales = (resultado.variables_decision or [])[:len(problema.objetivo)]
    z_val = AnalizadorMatematico.formatear_valor_pedagogico(resultado.z_optimo) if resultado.z_optimo is not None else "N/D"
    texto_vars = ", ".join(f"X{i+1} = {AnalizadorMatematico.formatear_valor_pedagogico(v)}" for i, v in enumerate(variables_originales)) if variables_originales else "N/D"

    return ft.Container(
        content=ft.Column([
            ft.Text(fo_str, size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("Z óptimo (Gomory)", size=10, color=TEXT_MUTED),
                        ft.Text(z_val, size=18, color=GREEN, weight=ft.FontWeight.BOLD),
                    ], spacing=2),
                    padding=16, border_radius=8, bgcolor="#1e2130", border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Variables Enteras óptimas", size=10, color=TEXT_MUTED),
                        ft.Text(texto_vars, size=13, color=TEXT_PRIMARY),
                    ], spacing=2),
                    padding=16, border_radius=8, bgcolor="#1e2130", border=ft.Border(top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR), left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR)),
                ),
            ], spacing=8, wrap=True),
            ft.Text(f"Estado de parada: {resultado.estado.value}", size=11, color=TEXT_MUTED, italic=True),
        ], spacing=10),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"), left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66")),
    )

def _crear_boton_paginacion(icono: ft.Icons, on_click, deshabilitado: bool) -> ft.IconButton:
    return ft.IconButton(
        icon=icono, icon_color=TEXT_PRIMARY if not deshabilitado else TEXT_MUTED,
        disabled=deshabilitado, on_click=on_click, icon_size=20,
    )

def _renderizar_controles_paginacion(indice_pagina: int, total_paginas: int, ir_a: "any") -> ft.Row:
    etiqueta = "Relajación inicial" if indice_pagina == 0 else f"Corte {indice_pagina}"
    return ft.Row(
        [
            _crear_boton_paginacion(ft.Icons.FIRST_PAGE, lambda _: ir_a(0), indice_pagina == 0),
            _crear_boton_paginacion(ft.Icons.CHEVRON_LEFT, lambda _: ir_a(indice_pagina - 1), indice_pagina == 0),
            ft.Container(
                content=ft.Text(
                    f"{etiqueta}  •  Página {indice_pagina + 1} de {total_paginas}",
                    size=12, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600
                ),
                padding=ft.Padding(12, 6, 12, 6), border_radius=8, bgcolor="#1e2130",
            ),
            _crear_boton_paginacion(ft.Icons.CHEVRON_RIGHT, lambda _: ir_a(indice_pagina + 1), indice_pagina >= total_paginas - 1),
            _crear_boton_paginacion(ft.Icons.LAST_PAGE, lambda _: ir_a(total_paginas - 1), indice_pagina >= total_paginas - 1),
        ],
        spacing=4, alignment=ft.MainAxisAlignment.CENTER,
    )

@ft.component
def VistaCortesGomory(controlador: ControladorEntera):
    resultado_ref = ft.use_ref(None)
    problema_ref  = ft.use_ref(None)
    pagina_actual, set_pagina_actual = ft.use_state(0)

    problema_actual = controlador.problema_activo

    # Solo resolver si el problema cambió
    if resultado_ref.current is None or problema_ref.current is not problema_actual:
        problema_ref.current = problema_actual
        if problema_actual:
            try:
                resultado_ref.current = controlador.resolver_PLE(problema_actual, 2)
            except Exception:
                resultado_ref.current = None
        else:
            resultado_ref.current = None
        # Nuevo problema/resultado: volver siempre a la primera página.
        if pagina_actual != 0:
            pagina_actual = 0
            set_pagina_actual(0)

    problema = problema_actual
    resultado = resultado_ref.current

    header = ft.Column([
        ft.Text("Cortes de Gomory", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Text("Resolución paso a paso mediante inserción de Planos de Corte de Gomory.", size=12, color=TEXT_MUTED),
    ], spacing=2)

    # 1. Caso sin problema activo
    if problema is None:
        status_row = _crear_alerta_status("Ingresa o selecciona un problema entero primero.", AMBER, ft.Icons.INFO_OUTLINE)
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

    # 2. Excepción
    if resultado is None:
        status_row = _crear_alerta_status("El motor matemático interrumpió el proceso inesperadamente.", RED, ft.Icons.ERROR_OUTLINE)
        error_container = ft.Container(
            content=ft.Text("Excepción en la obtención de cortes algebraicos.", color=RED),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(top=ft.BorderSide(1, RED + "44"), bottom=ft.BorderSide(1, RED + "44"), left=ft.BorderSide(1, RED + "44"), right=ft.BorderSide(1, RED + "44")),
        )
        return ft.Column(
            [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, error_container],
            expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
        )

    # 4. Traducción de estado
    if resultado.estado == EstadoProblema.OPTIMO:
        status_row = _crear_alerta_status("Proceso concluido. Óptimo entero alcanzado.", GREEN, ft.Icons.CHECK_CIRCLE)
    elif resultado.estado == EstadoProblema.INVIABLE:
        status_row = _crear_alerta_status("Inviabilidad: No hay solución entera factible.", RED, ft.Icons.ERROR_OUTLINE)
    else:
        status_row = _crear_alerta_status(f"Conclusión: {resultado.estado.value}", AMBER, ft.Icons.INFO_OUTLINE)

    paginas = _calcular_paginas(resultado)
    total_paginas = len(paginas)

    controles_resultado: List[ft.Control] = [_renderizar_resumen(resultado, problema)]

    if total_paginas > 0:
        indice_pagina = max(0, min(pagina_actual, total_paginas - 1))

        def ir_a_pagina(nueva: int) -> None:
            nueva = max(0, min(nueva, total_paginas - 1))
            set_pagina_actual(nueva)

        offset_paso = sum(len(p) for p in paginas[:indice_pagina])

        if total_paginas > 1:
            controles_resultado.append(_renderizar_controles_paginacion(indice_pagina, total_paginas, ir_a_pagina))

        controles_resultado.extend(_renderizar_pagina(paginas[indice_pagina], indice_pagina, offset_paso))

        if total_paginas > 1:
            controles_resultado.append(_renderizar_controles_paginacion(indice_pagina, total_paginas, ir_a_pagina))

    resultados_column = ft.Column(controles_resultado, spacing=14)

    return ft.Column(
        [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, resultados_column],
        expand=True, spacing=16, scroll=ft.ScrollMode.AUTO
    )
