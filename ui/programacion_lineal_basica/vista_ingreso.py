# ui/vista_ingreso.py
"""
vista_ingreso.py
================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Implementa un entorno flexible de entrada de datos para modelos de PL.
"""

from __future__ import annotations
from typing import List, Optional, cast
import flet as ft

from src.models.entity.programacion_lineal.enums import TipoOptimizacion, SignoRestriccion
from src.models.entity.programacion_lineal.problema import ProblemaPL, Restriccion
from src.utils.programacion_lineal_basica.parser import MotorParsing
from src.controller.controlador_lineal import ControladorLineal

# Paleta de colores institucional
ACCENT_COLOR: str = "#7c3aed"
BG_CARD: str = "#161822"
BG_FIELD: str = "#1e2130"
BORDER_COLOR: str = "#2a2d3a"
TEXT_MUTED: str = "#6b7280"
TEXT_PRIMARY: str = "#f0f0f0"
GREEN: str = "#1d9e75"
AMBER: str = "#f6ad55"
RED: str = "#ef645f"

_MODOS_LABELS = ["Tradicional por Celdas", "Lenguaje Natural (Algebraico)", "Coeficientes planos (CSV)"]


def _crear_campo_ui(label: str, valor: str = "") -> ft.TextField:
    """Factory function para generar campos de texto estandarizados."""
    return ft.TextField(
        label=label,
        value=str(valor),
        width=90,
        text_align=ft.TextAlign.CENTER,
        border_color=BORDER_COLOR,
        focused_border_color=ACCENT_COLOR,
        cursor_color=ACCENT_COLOR,
        bgcolor=BG_FIELD,
        color=TEXT_PRIMARY,
        label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
        keyboard_type=ft.KeyboardType.TEXT,
        hint_text="0",
        border_radius=8,
    )


def _crear_boton_ui(texto: str, icono: ft.Icons, on_click, color: Optional[str] = None) -> ft.ElevatedButton:
    """Factory function para generar botones con iconografía homogénea."""
    bg_color = color if color is not None else ACCENT_COLOR
    return ft.ElevatedButton(
        content=ft.Row(
            [
                ft.Icon(cast(ft.IconData, icono), size=15, color="white"),
                ft.Text(texto, size=12, color="white")
            ],
            tight=True,
            spacing=6,
        ),
        bgcolor=bg_color,
        on_click=on_click,
    )


def _estado_inicial_desde_problema(problema: ProblemaPL) -> dict:
    """Construye el estado inicial del formulario a partir de un ProblemaPL."""
    return {
        "tipo": problema.tipo.value,
        "objetivo": [str(c) for c in problema.objetivo],
        "restricciones": [
            {
                "coeficientes": [str(c) for c in r.coeficientes],
                "signo": r.signo.value,
                "rhs": str(r.rhs),
            }
            for r in problema.restricciones
        ],
        "objetivo_avanzado": "",
        "restricciones_avanzado": "",
    }


def _estado_inicial_vacio() -> dict:
    return {
        "tipo": "MAX",
        "objetivo": ["", ""],
        "restricciones": [
            {
                "coeficientes": ["", ""],
                "signo": "<=",
                "rhs": "",
            }
        ],
        "objetivo_avanzado": "",
        "restricciones_avanzado": "",
    }


@ft.component
def VistaIngreso(controlador: ControladorLineal, navegar_a=None):
    modo_ingreso_actual, set_modo_ingreso_actual = ft.use_state(0)  # 0: Tradicional, 1: Natural, 2: CSV
    status_text_val, set_status_text_val = ft.use_state(("", ""))  # (message, color)
    refresh_trigger, set_refresh_trigger = ft.use_state(0)

    # --- REFERENCIA PERSISTENTE ORIENTADA A DATOS NATIVOS ---
    valores_ingreso_ref = ft.use_ref(None)
    if valores_ingreso_ref.current is None:
        # Poblar desde el problema activo si existe (necesario para clonar desde historial)
        prob_activo = controlador.problema_activo
        if prob_activo is not None:
            valores_ingreso_ref.current = _estado_inicial_desde_problema(prob_activo)
        else:
            valores_ingreso_ref.current = _estado_inicial_vacio()

    # Handlers para actualizar los datos nativos en tiempo real
    def cambiar_tipo(e: ft.ControlEvent) -> None:
        valores_ingreso_ref.current["tipo"] = e.control.value

    def cambiar_objetivo(idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["objetivo"][idx] = e.control.value
        return handler

    def cambiar_coef_restriccion(fila_idx: int, coef_idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["restricciones"][fila_idx]["coeficientes"][coef_idx] = e.control.value
        return handler

    def cambiar_signo_restriccion(fila_idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["restricciones"][fila_idx]["signo"] = e.control.value
        return handler

    def cambiar_rhs_restriccion(fila_idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["restricciones"][fila_idx]["rhs"] = e.control.value
        return handler

    def cambiar_objetivo_avanzado(e: ft.ControlEvent) -> None:
        valores_ingreso_ref.current["objetivo_avanzado"] = e.control.value

    def cambiar_restricciones_avanzado(e: ft.ControlEvent) -> None:
        valores_ingreso_ref.current["restricciones_avanzado"] = e.control.value

    # --- Acciones logísticas sobre los datos ---
    def accion_agregar_variable(_e) -> None:
        valores_ingreso_ref.current["objetivo"].append("")
        for fila in valores_ingreso_ref.current["restricciones"]:
            fila["coeficientes"].append("")
        set_refresh_trigger(lambda x: x + 1)

    def accion_eliminar_variable(_e) -> None:
        if len(valores_ingreso_ref.current["objetivo"]) > 1:
            valores_ingreso_ref.current["objetivo"].pop()
            for fila in valores_ingreso_ref.current["restricciones"]:
                if fila["coeficientes"]:
                    fila["coeficientes"].pop()
            set_refresh_trigger(lambda x: x + 1)
        else:
            set_status_text_val(("Operación inválida: El modelo debe tener al menos una variable.", RED))

    def accion_agregar_restriccion(_e) -> None:
        num_vars = len(valores_ingreso_ref.current["objetivo"])
        valores_ingreso_ref.current["restricciones"].append({
            "coeficientes": [""] * num_vars,
            "signo": "<=",
            "rhs": "",
        })
        set_refresh_trigger(lambda x: x + 1)

    def accion_eliminar_restriccion(_e) -> None:
        if len(valores_ingreso_ref.current["restricciones"]) > 1:
            valores_ingreso_ref.current["restricciones"].pop()
            set_refresh_trigger(lambda x: x + 1)
        else:
            set_status_text_val(("Operación inválida: El modelo debe tener al menos una restricción.", RED))

    def manejador_vaciar_valores(_e) -> None:
        if modo_ingreso_actual == 0:
            for i in range(len(valores_ingreso_ref.current["objetivo"])):
                valores_ingreso_ref.current["objetivo"][i] = ""
            for fila in valores_ingreso_ref.current["restricciones"]:
                for i in range(len(fila["coeficientes"])):
                    fila["coeficientes"][i] = ""
                fila["rhs"] = ""
        else:
            valores_ingreso_ref.current["objetivo_avanzado"] = ""
            valores_ingreso_ref.current["restricciones_avanzado"] = ""

        set_status_text_val(("Campos vaciados.", AMBER))
        set_refresh_trigger(lambda x: x + 1)

    def manejador_restablecer_todo(_e) -> None:
        valores_ingreso_ref.current = _estado_inicial_vacio()
        set_status_text_val(("Estructura reseteada por completo.", AMBER))
        set_refresh_trigger(lambda x: x + 1)

    # --- Compilación y Parsing del Problema ---
    def compilar_modo_tradicional_a_objeto() -> ProblemaPL:
        def parsear_texto_a_primitivo(valor_crudo: str) -> float:
            texto = valor_crudo.strip().replace(",", ".")
            if not texto:
                return 0.0
            if "/" in texto:
                from fractions import Fraction
                return float(Fraction(texto))
            return float(texto)

        tipo_enum = TipoOptimizacion(valores_ingreso_ref.current["tipo"])
        vector_objetivo = [parsear_texto_a_primitivo(val) for val in valores_ingreso_ref.current["objetivo"]]

        lista_restricciones: List[Restriccion] = []
        for fila in valores_ingreso_ref.current["restricciones"]:
            coefs = [parsear_texto_a_primitivo(val) for val in fila["coeficientes"]]
            signo_enum = SignoRestriccion(fila["signo"])
            rhs_val = parsear_texto_a_primitivo(fila["rhs"])
            lista_restricciones.append(Restriccion(coeficientes=coefs, signo=signo_enum, rhs=rhs_val))

        return ProblemaPL(tipo=tipo_enum, objetivo=vector_objetivo, restricciones=lista_restricciones)

    def manejador_guardar_problema(_e) -> None:
        try:
            problema_entidad: Optional[ProblemaPL] = None

            if modo_ingreso_actual == 0:
                problema_entidad = compilar_modo_tradicional_a_objeto()
            else:
                texto_obj = valores_ingreso_ref.current["objetivo_avanzado"].strip()
                lineas_res = valores_ingreso_ref.current["restricciones_avanzado"].split("\n")

                if modo_ingreso_actual == 1:
                    problema_entidad = MotorParsing.natural_a_entidades(texto_obj, lineas_res)
                else:
                    problema_entidad = MotorParsing.csv_a_entidades(texto_obj, lineas_res)

            if problema_entidad is not None:
                controlador.ingresar_problema(problema_entidad)
                set_status_text_val(("Problema matemáticamente validado, guardado y activado con éxito.", GREEN))
                if navegar_a:
                    navegar_a(2)
            else:
                raise ValueError("Estructura de datos nula generada.")

        except Exception as error_capturado:
            set_status_text_val((f"Error de Validación: {error_capturado}", RED))

    # --- Renderizado Layout ---
    def render_bloque_contenedor(titulo: str, contenido: ft.Control) -> ft.Container:
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(titulo, size=13, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    contenido,
                ],
                spacing=12,
            ),
            expand=True,
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
                left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR),
            ),
        )

    # Selector de modo como Dropdown
    def on_tab_click(index_modo: int) -> None:
        set_modo_ingreso_actual(index_modo)
        set_status_text_val(("", ""))

    formato_dropdown = ft.Dropdown(
        value=_MODOS_LABELS[modo_ingreso_actual],
        options=[ft.dropdown.Option(label) for label in _MODOS_LABELS],
        width=280,
        border_color=BORDER_COLOR,
        focused_border_color=ACCENT_COLOR,
        bgcolor=BG_FIELD,
        color=TEXT_PRIMARY,
        border_radius=8,
        label="Formato de Ingreso",
        label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
        on_select=lambda e: on_tab_click(_MODOS_LABELS.index(e.control.value)),
    )

    # Cuerpo central
    if modo_ingreso_actual == 0:
        controles_fo = [ft.Text("Z =", color=TEXT_MUTED, size=13)]
        for idx, val in enumerate(valores_ingreso_ref.current["objetivo"]):
            campo = _crear_campo_ui(f"X{idx+1}", val)
            campo.on_change = cambiar_objetivo(idx)
            controles_fo.append(campo)
            if idx < len(valores_ingreso_ref.current["objetivo"]) - 1:
                controles_fo.append(ft.Text("+", color=TEXT_MUTED, size=14))

        tipo_dropdown = ft.Dropdown(
            label="Optimización",
            value=valores_ingreso_ref.current["tipo"],
            options=[ft.dropdown.Option("MAX"), ft.dropdown.Option("MIN")],
            width=160,
            border_color=BORDER_COLOR,
            focused_border_color=ACCENT_COLOR,
            bgcolor=BG_FIELD,
            color=TEXT_PRIMARY,
            border_radius=8,
            on_select=cambiar_tipo,
        )

        tarjeta_fo = render_bloque_contenedor(
            "Función Objetivo",
            ft.Column(
                [
                    tipo_dropdown,
                    ft.Row(controles_fo, wrap=True, spacing=6),
                    ft.Row(
                        [
                            _crear_boton_ui("Añadir variable", ft.Icons.ADD, accion_agregar_variable),
                            _crear_boton_ui("Eliminar variable", ft.Icons.REMOVE, accion_eliminar_variable, color="#374151"),
                        ],
                        spacing=8
                    ),
                ],
                spacing=10
            )
        )

        columna_restricciones = ft.Column(spacing=10)
        for posicion, fila in enumerate(valores_ingreso_ref.current["restricciones"], start=1):
            controles_fila = []
            for j, val in enumerate(fila["coeficientes"]):
                campo_coef = _crear_campo_ui(f"X{j+1}", val)
                campo_coef.on_change = cambiar_coef_restriccion(posicion - 1, j)
                controles_fila.append(campo_coef)
                if j < len(fila["coeficientes"]) - 1:
                    controles_fila.append(ft.Text("+", color=TEXT_MUTED, size=12))

            signo_dropdown = ft.Dropdown(
                value=fila["signo"],
                options=[ft.dropdown.Option("<="), ft.dropdown.Option(">="), ft.dropdown.Option("==")],
                width=90,
                border_color=BORDER_COLOR,
                focused_border_color=ACCENT_COLOR,
                bgcolor=BG_FIELD,
                color=TEXT_PRIMARY,
                border_radius=8,
                on_select=cambiar_signo_restriccion(posicion - 1),
            )

            rhs_field = _crear_campo_ui("RHS", fila["rhs"])
            rhs_field.on_change = cambiar_rhs_restriccion(posicion - 1)

            bloque_fila = ft.Container(
                content=ft.Column(
                    [
                        ft.Text(f"Restricción {posicion}", size=12, weight=ft.FontWeight.BOLD, color=ACCENT_COLOR),
                        ft.Row(controles_fila + [signo_dropdown, rhs_field], wrap=True, spacing=6),
                    ],
                    spacing=8
                ),
                padding=12, border_radius=10, bgcolor="#12141f",
                border=ft.Border(
                    top=ft.BorderSide(1, "#252836"), bottom=ft.BorderSide(1, "#252836"),
                    left=ft.BorderSide(1, "#252836"), right=ft.BorderSide(1, "#252836")
                )
            )
            columna_restricciones.controls.append(bloque_fila)

        columna_restricciones.controls.append(
            ft.Row(
                [
                    _crear_boton_ui("Añadir restricción", ft.Icons.ADD_CIRCLE_OUTLINE, accion_agregar_restriccion),
                    _crear_boton_ui("Eliminar restricción", ft.Icons.REMOVE_CIRCLE_OUTLINE, accion_eliminar_restriccion, color="#374151"),
                ],
                spacing=8
            )
        )
        tarjeta_restricciones = render_bloque_contenedor("Restricciones Lineales", columna_restricciones)

        cuerpo = ft.Column([tarjeta_fo, tarjeta_restricciones], spacing=16)
    else:
        titulo_seccion = "Ingreso en Formato Algebraico Natural" if modo_ingreso_actual == 1 else "Ingreso en Formato Coeficientes CSV"
        label_obj = "Escribe la Función Objetivo" if modo_ingreso_actual == 1 else "Ingresa los Coeficientes Objetivo por comas"
        label_res = "Escribe las Restricciones (Una por línea)" if modo_ingreso_actual == 1 else "Ingresa las Restricciones CSV (Una por línea)"

        text_hint = "Ej: Max Z = 3x1 + 5x2" if modo_ingreso_actual == 1 else "Ej: Max, 3, 5"
        input_objetivo_avanzado = ft.TextField(
            label=label_obj,
            value=valores_ingreso_ref.current["objetivo_avanzado"],
            hint_text=text_hint,
            border_color=BORDER_COLOR,
            focused_border_color=ACCENT_COLOR,
            bgcolor=BG_FIELD,
            color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
            expand=True,
            border_radius=8,
            on_change=cambiar_objetivo_avanzado,
        )

        text_hint_res = "Ej: 2x1 + x2 <= 10" if modo_ingreso_actual == 1 else "Ej: 2, 1, <=, 10"
        input_restricciones_avanzado = ft.TextField(
            label=label_res,
            value=valores_ingreso_ref.current["restricciones_avanzado"],
            hint_text=text_hint_res,
            border_color=BORDER_COLOR,
            focused_border_color=ACCENT_COLOR,
            bgcolor=BG_FIELD,
            color=TEXT_PRIMARY,
            label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
            border_radius=8,
            multiline=True,
            expand=True,
            min_lines=4,
            on_change=cambiar_restricciones_avanzado,
        )

        cuerpo = render_bloque_contenedor(
            titulo_seccion,
            ft.Column(
                [
                    input_objetivo_avanzado,
                    input_restricciones_avanzado,
                ],
                spacing=14,
                expand=True,
            )
        )

    # Cabecera con título a la izquierda y formato a la derecha (misma altura)
    cabecera_row = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("Configuración del Modelo Lineal", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text("Digita los parámetros del problema usando el formato que te sea más cómodo.", size=12, color=TEXT_MUTED),
                ],
                spacing=2,
                expand=True,
            ),
            formato_dropdown,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    barra_botones_inferior = ft.Row(
        [
            _crear_boton_ui("Guardar y Activar Problema", ft.Icons.SAVE, manejador_guardar_problema, color=GREEN),
            _crear_boton_ui("Vaciar Campos", ft.Icons.REFRESH, manejador_vaciar_valores, color="#374151"),
            _crear_boton_ui("Reiniciar Estructura", ft.Icons.RESTART_ALT, manejador_restablecer_todo, color="#374151"),
        ],
        spacing=8, wrap=True
    )

    status_text_widget = ft.Text(
        status_text_val[0],
        size=12,
        color=status_text_val[1],
        visible=bool(status_text_val[0])
    )

    # Todo en una columna scrollable (incluye header, cuerpo y botones)
    return ft.Column(
        [
            cabecera_row,
            ft.Divider(color=BORDER_COLOR, height=1),
            cuerpo,
            ft.Divider(color=BORDER_COLOR, height=1),
            barra_botones_inferior,
            status_text_widget,
        ],
        spacing=16,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
