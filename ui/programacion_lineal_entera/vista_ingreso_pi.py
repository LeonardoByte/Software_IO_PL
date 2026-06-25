# ui/programacion_lineal_entera/vista_ingreso_pi.py
"""
vista_ingreso_pi.py
===================
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Implementa un entorno flexible de entrada de datos para modelos de PLE (PI),
soportando ingreso Tradicional, Algebraico y CSV.
"""

from __future__ import annotations
import re
from fractions import Fraction
from typing import List, Optional, Union, cast
import flet as ft

from src.models.entity.programacion_lineal.enums import TipoOptimizacion, SignoRestriccion
from src.models.entity.programacion_lineal.problema import Restriccion
from src.models.entity.programacion_lineal_entera.enums import (
    TipoVariable,
    OperadorLogico,
    OperadorMGrande,
    OperadorAsignacionLogica,
)
from src.models.entity.programacion_lineal_entera.problema import (
    ProblemaPLE,
    ProblemaModeladoLogico,
    NodoLogico,
)
from src.utils.programacion_lineal_entera.parser_sintactico import ParserSintactico
from src.utils.programacion_lineal_entera.compilador_logica import CompiladorLogico
from src.controller.controlador_entera import ControladorEntera
from src.utils.programacion_lineal_entera.manual_sintaxis import obtener_manual_algebraico, obtener_manual_csv

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

_MODOS_LABELS_PI = ["Tradicional por Celdas", "Lenguaje Natural (Algebraico)", "Coeficientes planos (CSV)"]

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

def _crear_dropdown_tipo_var(indice: int, valor: str = "Entera", on_select=None) -> ft.Dropdown:
    """Dropdown para definir el tipo de variable: Continua / Entera / Binaria."""
    return ft.Dropdown(
        label=f"X{indice + 1}",
        value=valor,
        options=[
            ft.dropdown.Option("Continua"),
            ft.dropdown.Option("Entera"),
            ft.dropdown.Option("Binaria"),
        ],
        width=120,
        border_color=BORDER_COLOR,
        focused_border_color=ACCENT_COLOR,
        bgcolor=BG_FIELD,
        color=TEXT_PRIMARY,
        border_radius=8,
        on_select=on_select,
    )

@ft.component
def VistaIngresoPi(controlador: ControladorEntera, navegar_a=None):
    modo_ingreso_actual, set_modo_ingreso_actual = ft.use_state(0) # 0: Tradicional, 1: Natural, 2: CSV
    refresh_trigger, set_refresh_trigger = ft.use_state(0)
    ayuda_modo, set_ayuda_modo = ft.use_state(0) # 0: cerrado, 1: algebraico, 2: csv

    # Declarative dialog construction for Flet v0.85.0
    dialog_control = None
    if ayuda_modo > 0:
        manual_text = obtener_manual_algebraico() if ayuda_modo == 1 else obtener_manual_csv()
        dialog_control = ft.AlertDialog(
            title=ft.Text(
                "Manual de Sintaxis PLE" if ayuda_modo == 1 else "Manual de Sintaxis CSV",
                weight=ft.FontWeight.BOLD
            ),
            content=ft.Column(
                [ft.Text(manual_text, size=11, font_family="monospace", color=TEXT_PRIMARY)],
                scroll=ft.ScrollMode.AUTO,
                height=400,
                width=600
            ),
            actions=[
                ft.TextButton("Cerrar", on_click=lambda _: set_ayuda_modo(0))
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    ft.use_dialog(dialog_control)

    # --- REFERENCIA PERSISTENTE ORIENTADA A DATOS NATIVOS ---
    valores_ingreso_ref = ft.use_ref(None)
    if valores_ingreso_ref.current is None:
        # Si ya hay un problema activo en el controlador, lo clonamos si es posible
        prob_activo = controlador.problema_activo
        if prob_activo is not None:
            # Recomponer
            tipo_inicial = prob_activo.tipo.value
            obj_vals = [str(c) for c in prob_activo.objetivo]
            types_vals = []
            for t in getattr(prob_activo, "tipos_variables", []):
                if t == TipoVariable.CONTINUA: types_vals.append("Continua")
                elif t == TipoVariable.ENTERA: types_vals.append("Entera")
                elif t == TipoVariable.BINARIA: types_vals.append("Binaria")
            if not types_vals:
                types_vals = ["Continua"] * len(obj_vals)

            rest_vals = []
            for r in prob_activo.restricciones:
                rest_vals.append({
                    "coeficientes": [str(c) for c in r.coeficientes],
                    "signo": r.signo.value,
                    "rhs": str(r.rhs)
                })
            if not rest_vals:
                rest_vals = [{"coeficientes": [""] * len(obj_vals), "signo": "<=", "rhs": ""}]

            valores_ingreso_ref.current = {
                "tipo": tipo_inicial,
                "objetivo": obj_vals,
                "tipos_var": types_vals,
                "restricciones": rest_vals,
                "restricciones_logicas": [],
                "objetivo_avanzado": "",
                "restricciones_avanzado": ""
            }
        else:
            valores_ingreso_ref.current = {
                "tipo": "MAX",
                "objetivo": ["", ""],
                "tipos_var": ["Entera", "Entera"],
                "restricciones": [
                    {
                        "coeficientes": ["", ""],
                        "signo": "<=",
                        "rhs": ""
                    }
                ],
                "restricciones_logicas": [],
                "objetivo_avanzado": "",
                "restricciones_avanzado": ""
            }

    # Handlers para actualizar los datos nativos en tiempo real
    def cambiar_tipo(e: ft.ControlEvent) -> None:
        valores_ingreso_ref.current["tipo"] = e.control.value

    def cambiar_objetivo(idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["objetivo"][idx] = e.control.value
        return handler

    def cambiar_tipo_var(idx: int):
        def handler(e: ft.ControlEvent) -> None:
            valores_ingreso_ref.current["tipos_var"][idx] = e.control.value
            # Forzar refresco para actualizar dropdowns de restricciones lógicas
            set_refresh_trigger(lambda x: x + 1)
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

    # --- Handlers para actualizar las restricciones lógicas ---
    def agregar_relacion_logica(categoria: str, op_defecto: str) -> None:
        binarias = []
        for idx, t in enumerate(valores_ingreso_ref.current["tipos_var"]):
            if t == "Binaria":
                binarias.append(f"x{idx + 1}")
        todas = [f"x{idx + 1}" for idx in range(len(valores_ingreso_ref.current["objetivo"]))]
        
        v1 = todas[0] if (categoria in ("Activación Umbral", "M Grande") and todas) else (binarias[0] if binarias else "")
        valores_ingreso_ref.current.setdefault("restricciones_logicas", []).append({
            "categoria": categoria,
            "op": op_defecto,
            "var1": v1,
            "var2": binarias[0] if binarias else "",
            "var_dest": binarias[0] if binarias else ""
        })
        set_refresh_trigger(lambda x: x + 1)

    def eliminar_relacion_logica(idx: int) -> None:
        if 0 <= idx < len(valores_ingreso_ref.current.get("restricciones_logicas", [])):
            valores_ingreso_ref.current["restricciones_logicas"].pop(idx)
            set_refresh_trigger(lambda x: x + 1)

    def cambiar_propiedad_logica(idx: int, clave: str, valor: str) -> None:
        if 0 <= idx < len(valores_ingreso_ref.current.get("restricciones_logicas", [])):
            valores_ingreso_ref.current["restricciones_logicas"][idx][clave] = valor
            set_refresh_trigger(lambda x: x + 1)

    # --- Acciones logísticas sobre los datos ---
    def accion_agregar_variable(_e) -> None:
        valores_ingreso_ref.current["objetivo"].append("")
        valores_ingreso_ref.current["tipos_var"].append("Continua")
        for fila in valores_ingreso_ref.current["restricciones"]:
            fila["coeficientes"].append("")
        set_refresh_trigger(lambda x: x + 1)

    def accion_eliminar_variable(e: ft.ControlEvent) -> None:
        if len(valores_ingreso_ref.current["objetivo"]) > 1:
            valores_ingreso_ref.current["objetivo"].pop()
            valores_ingreso_ref.current["tipos_var"].pop()
            for fila in valores_ingreso_ref.current["restricciones"]:
                if fila["coeficientes"]:
                    fila["coeficientes"].pop()
            set_refresh_trigger(lambda x: x + 1)
        else:
            mostrar_snack_bar(e.control.page, "Operación inválida: El modelo debe tener al menos una variable.", RED)

    def accion_agregar_restriccion(_e) -> None:
        num_vars = len(valores_ingreso_ref.current["objetivo"])
        valores_ingreso_ref.current["restricciones"].append({
            "coeficientes": [""] * num_vars,
            "signo": "<=",
            "rhs": ""
        })
        set_refresh_trigger(lambda x: x + 1)

    def accion_eliminar_restriccion(e: ft.ControlEvent) -> None:
        if len(valores_ingreso_ref.current["restricciones"]) > 1:
            valores_ingreso_ref.current["restricciones"].pop()
            set_refresh_trigger(lambda x: x + 1)
        else:
            mostrar_snack_bar(e.control.page, "Operación inválida: El modelo debe tener al menos una restricción.", RED)

    def manejador_vaciar_valores(e: ft.ControlEvent) -> None:
        if modo_ingreso_actual == 0:
            for i in range(len(valores_ingreso_ref.current["objetivo"])):
                valores_ingreso_ref.current["objetivo"][i] = ""
            for fila in valores_ingreso_ref.current["restricciones"]:
                for i in range(len(fila["coeficientes"])):
                    fila["coeficientes"][i] = ""
                fila["rhs"] = ""
            valores_ingreso_ref.current["restricciones_logicas"] = []
        else:
            valores_ingreso_ref.current["objetivo_avanzado"] = ""
            valores_ingreso_ref.current["restricciones_avanzado"] = ""
            
        mostrar_snack_bar(e.control.page, "Campos vaciados.", AMBER)
        set_refresh_trigger(lambda x: x + 1)

    def manejador_restablecer_todo(e: ft.ControlEvent) -> None:
        valores_ingreso_ref.current = {
            "tipo": "MAX",
            "objetivo": ["", ""],
            "tipos_var": ["Entera", "Entera"],
            "restricciones": [
                {
                    "coeficientes": ["", ""],
                    "signo": "<=",
                    "rhs": ""
                }
            ],
            "restricciones_logicas": [],
            "objetivo_avanzado": "",
            "restricciones_avanzado": ""
        }
        mostrar_snack_bar(e.control.page, "Estructura reseteada por completo.", AMBER)
        set_refresh_trigger(lambda x: x + 1)

    # --- SnackBar helper ---
    def mostrar_snack_bar(page: ft.Page, mensaje: str, color: str) -> None:
        page.snack_bar = ft.SnackBar(
            content=ft.Text(mensaje, color="white", weight=ft.FontWeight.W_600),
            bgcolor=color,
            duration=4000
        )
        page.snack_bar.open = True
        page.update()

    # --- Modals de ayuda con compatibilidad Flet v0.85 ---
    def abrir_ayuda(e: ft.ControlEvent, modo: int) -> None:
        set_ayuda_modo(modo)

    # --- Compilación y Parsing del Problema ---
    def parsear_texto_a_primitivo(valor_crudo: str) -> Fraction:
        texto = valor_crudo.strip().replace(",", ".")
        if not texto:
            return Fraction(0)
        if "/" in texto:
            num, den = texto.split("/", 1)
            return Fraction(int(num), int(den))
        if "." in texto:
            return Fraction(float(texto)).limit_denominator()
        return Fraction(int(texto))

    def compilar_modo_tradicional_a_objeto() -> ProblemaPLE:
        tipo_enum = TipoOptimizacion(valores_ingreso_ref.current["tipo"])
        vector_objetivo = [parsear_texto_a_primitivo(val) for val in valores_ingreso_ref.current["objetivo"]]

        lista_restricciones: List[Restriccion] = []
        for fila in valores_ingreso_ref.current["restricciones"]:
            coefs = [parsear_texto_a_primitivo(val) for val in fila["coeficientes"]]
            signo_enum = SignoRestriccion(fila["signo"])
            rhs_val = parsear_texto_a_primitivo(fila["rhs"])
            lista_restricciones.append(Restriccion(coeficientes=coefs, signo=signo_enum, rhs=rhs_val))

        tipos_mapeados = []
        for t in valores_ingreso_ref.current["tipos_var"]:
            if t == "Continua": tipos_mapeados.append(TipoVariable.CONTINUA)
            elif t == "Entera": tipos_mapeados.append(TipoVariable.ENTERA)
            elif t == "Binaria": tipos_mapeados.append(TipoVariable.BINARIA)

        # Mapeo de restricciones lógicas ingresadas por celdas
        arboles_logicos: List[NodoLogico] = []
        for r_log in valores_ingreso_ref.current.get("restricciones_logicas", []):
            op_str = r_log["op"]
            op_enum = None
            if r_log["categoria"] == "Lógica Pura":
                op_enum = OperadorLogico(op_str)
            elif r_log["categoria"] == "Activación Umbral":
                op_enum = OperadorMGrande(op_str)
            else:
                op_enum = OperadorAsignacionLogica(op_str)

            var1_name = r_log["var1"]
            var2_name = r_log["var2"]
            var_dest_name = r_log["var_dest"] if r_log["categoria"] == "Asignación Lógica" else None

            # Construir NodoLogico
            nodo = NodoLogico(
                operador=op_enum,
                hijos=[var1_name, var2_name],
                variable_control_asociada=var_dest_name
            )
            arboles_logicos.append(nodo)

        if arboles_logicos:
            problema_logico = ProblemaModeladoLogico(
                tipo=tipo_enum,
                objetivo=vector_objetivo,
                restricciones=lista_restricciones,
                tipos_variables=tipos_mapeados,
                arboles_logicos=arboles_logicos
            )
            compiler = CompiladorLogico()
            return compiler.compilar(problema_logico)
        else:
            return ProblemaPLE(
                tipo=tipo_enum,
                objetivo=vector_objetivo,
                restricciones=lista_restricciones,
                tipos_variables=tipos_mapeados
            )

    def parsear_algebraico_completo() -> ProblemaPLE:
        texto_obj = valores_ingreso_ref.current["objetivo_avanzado"].strip()
        lines = [line.strip() for line in texto_obj.splitlines() if line.strip()]
        if not lines:
            raise ValueError("La función objetivo está vacía.")
        
        # Linea 1: Fórmula
        line_formula = lines[0].replace(" ", "")
        match_tipo = re.match(r"^(MAX|MIN)", line_formula, re.IGNORECASE)
        if not match_tipo:
            raise ValueError("La función objetivo natural debe iniciar con 'Max' o 'Min'.")
        tipo_enum = TipoOptimizacion(match_tipo.group(1).upper())
        
        cuerpo_obj = re.sub(r"^(MAX|MIN)[^=]*=", "", line_formula, flags=re.IGNORECASE)
        patron_monomio = re.compile(r"([+-]?(?:\d+(?:\.\d+)?(?:/\d+)?)?)[xX](\d+)")
        monomios_obj = patron_monomio.findall(cuerpo_obj)
        if not monomios_obj:
            raise ValueError("No se detectaron variables válidas (ej. x1, x2) en la función objetivo.")
            
        max_var = max(int(idx) for _, idx in monomios_obj)
        objetivo_coefs = [Fraction(0)] * max_var
        for coef_str, idx_str in monomios_obj:
            idx_pos = int(idx_str) - 1
            if not coef_str or coef_str == "+":
                val = Fraction(1)
            elif coef_str == "-":
                val = Fraction(-1)
            else:
                val = Fraction(coef_str)
            objetivo_coefs[idx_pos] = val
            
        # Linea 2: Tipos de variables (opcional)
        tipos_var_list = [TipoVariable.CONTINUA] * max_var
        if len(lines) > 1:
            decl_line = lines[1]
            tokens = decl_line.split()
            for tok in tokens:
                match = re.match(r"[xX](\d+)=([CEB])", tok.strip(), re.IGNORECASE)
                if match:
                    var_idx = int(match.group(1)) - 1
                    t_char = match.group(2).upper()
                    if var_idx < max_var:
                        if t_char == 'C': tipos_var_list[var_idx] = TipoVariable.CONTINUA
                        elif t_char == 'E': tipos_var_list[var_idx] = TipoVariable.ENTERA
                        elif t_char == 'B': tipos_var_list[var_idx] = TipoVariable.BINARIA

        # Restricciones
        texto_res = valores_ingreso_ref.current["restricciones_avanzado"].strip()
        parser = ParserSintactico()
        arboles = parser.parse_restricciones(texto_res, max_var, tipos_var_list)

        problema_logico = ProblemaModeladoLogico(
            tipo=tipo_enum,
            objetivo=objetivo_coefs,
            restricciones=[],
            tipos_variables=tipos_var_list,
            arboles_logicos=arboles
        )

        compiler = CompiladorLogico()
        return compiler.compilar(problema_logico)

    def parsear_csv_completo() -> ProblemaPLE:
        texto_obj = valores_ingreso_ref.current["objetivo_avanzado"].strip()
        lines = [line.strip() for line in texto_obj.splitlines() if line.strip()]
        if not lines:
            raise ValueError("La función objetivo CSV está vacía.")
        
        # Linea 1: Fórmula
        partes_obj = [p.strip() for p in lines[0].split(",") if p.strip()]
        if not partes_obj:
            raise ValueError("La función objetivo CSV está vacía.")
            
        try:
            tipo_enum = TipoOptimizacion(partes_obj[0].upper())
        except ValueError:
            raise ValueError(f"El tipo de optimización CSV debe ser MAX o MIN. Recibido: '{partes_obj[0]}'")
            
        objetivo_coefs = [Fraction(c) for c in partes_obj[1:]]
        max_var = len(objetivo_coefs)
        if max_var == 0:
            raise ValueError("La función objetivo CSV no contiene coeficientes.")
            
        # Linea 2: Tipos
        tipos_var_list = [TipoVariable.CONTINUA] * max_var
        if len(lines) > 1:
            partes_types = [p.strip().upper() for p in lines[1].split(",") if p.strip()]
            for idx, t_char in enumerate(partes_types):
                if idx < max_var:
                    if t_char == 'C': tipos_var_list[idx] = TipoVariable.CONTINUA
                    elif t_char == 'E': tipos_var_list[idx] = TipoVariable.ENTERA
                    elif t_char == 'B': tipos_var_list[idx] = TipoVariable.BINARIA

        # Restricciones
        texto_res = valores_ingreso_ref.current["restricciones_avanzado"].strip()
        parser = ParserSintactico()
        arboles = parser.parse_restricciones(texto_res, max_var, tipos_var_list)

        problema_logico = ProblemaModeladoLogico(
            tipo=tipo_enum,
            objetivo=objetivo_coefs,
            restricciones=[],
            tipos_variables=tipos_var_list,
            arboles_logicos=arboles
        )

        compiler = CompiladorLogico()
        return compiler.compilar(problema_logico)

    def manejador_guardar_problema(e: ft.ControlEvent) -> None:
        try:
            problema_entidad: Optional[ProblemaPLE] = None

            if modo_ingreso_actual == 0:
                problema_entidad = compilar_modo_tradicional_a_objeto()
            elif modo_ingreso_actual == 1:
                problema_entidad = parsear_algebraico_completo()
            else:
                problema_entidad = parsear_csv_completo()

            if problema_entidad is not None:
                controlador.ingresar_problema(problema_entidad)
                mostrar_snack_bar(e.control.page, "Problema PLE validado, compilado y guardado en historial con éxito.", GREEN)
                if navegar_a:
                    navegar_a(2)
            else:
                raise ValueError("Estructura de datos nula generada.")

        except Exception as error_capturado:
            mostrar_snack_bar(e.control.page, f"Error de Validación: {error_capturado}", RED)

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

    # Selector de modo como Dropdown (igual que PL)
    def on_tab_click(index_modo: int) -> None:
        set_modo_ingreso_actual(index_modo)
        set_refresh_trigger(lambda x: x + 1)

    formato_dropdown = ft.Dropdown(
        value=_MODOS_LABELS_PI[modo_ingreso_actual],
        options=[ft.dropdown.Option(label) for label in _MODOS_LABELS_PI],
        width=280,
        border_color=BORDER_COLOR,
        focused_border_color=ACCENT_COLOR,
        bgcolor=BG_FIELD,
        color=TEXT_PRIMARY,
        border_radius=8,
        label="Formato de Ingreso",
        label_style=ft.TextStyle(color=TEXT_MUTED, size=11),
        on_select=lambda e: on_tab_click(_MODOS_LABELS_PI.index(e.control.value)),
    )

    # Construcción de variables binarias y de todas las variables
    binarias_list = []
    for idx, t in enumerate(valores_ingreso_ref.current["tipos_var"]):
        if t == "Binaria":
            binarias_list.append(f"x{idx + 1}")
    todas_list = [f"x{idx + 1}" for idx in range(len(valores_ingreso_ref.current["objetivo"]))]

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

        dropdowns_tipo = []
        for idx, t_var in enumerate(valores_ingreso_ref.current["tipos_var"]):
            dd = _crear_dropdown_tipo_var(idx, t_var, on_select=cambiar_tipo_var(idx))
            dropdowns_tipo.append(dd)
            
        tarjeta_tipo_var = render_bloque_contenedor(
            "Tipos de Variables",
            ft.Column(
                [
                    ft.Text("Define si cada variable es Continua (R), Entera (Z) o Binaria (0/1):", size=11, color=TEXT_MUTED),
                    ft.Row(dropdowns_tipo, wrap=True, spacing=10),
                ],
                spacing=8
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

        # Construcción de la sección de restricciones lógicas por celdas
        columna_restricciones_logicas = ft.Column(spacing=14)
        
        # Verificar que existan variables binarias
        if not binarias_list:
            columna_restricciones_logicas.controls.append(
                ft.Container(
                    content=ft.Text("⚠️ Define al menos una variable de tipo 'Binaria' arriba para configurar restricciones lógicas.", color=AMBER, size=12, weight=ft.FontWeight.W_500),
                    padding=10, border_radius=6, bgcolor=AMBER + "15",
                    border=ft.Border(top=ft.BorderSide(1, AMBER + "33"), bottom=ft.BorderSide(1, AMBER + "33"), left=ft.BorderSide(1, AMBER + "33"), right=ft.BorderSide(1, AMBER + "33"))
                )
            )
        else:
            # 3 Listas para cada categoría de lógica
            logica_pura_rows = []
            m_grande_rows = []
            asignacion_rows = []

            master_logica = valores_ingreso_ref.current.setdefault("restricciones_logicas", [])

            for idx, fila in enumerate(master_logica):
                categoria = fila["categoria"]
                v1_options = todas_list if categoria in ("Activación Umbral", "M Grande") else binarias_list
                v2_options = binarias_list
                dest_options = binarias_list

                # Sanitizar variables guardadas
                if fila.get("var1") not in v1_options:
                    fila["var1"] = v1_options[0] if v1_options else ""
                if fila.get("var2") not in v2_options:
                    fila["var2"] = v2_options[0] if v2_options else ""
                if fila.get("var_dest") not in dest_options:
                    fila["var_dest"] = dest_options[0] if dest_options else ""

                # Generar manejadores únicos usando clausuras (closures)
                def crear_on_change_prop(pos, clave):
                    return lambda e: cambiar_propiedad_logica(pos, clave, e.control.value)

                def crear_on_click_del(pos):
                    return lambda _e: eliminar_relacion_logica(pos)

                var1_dd = ft.Dropdown(
                    value=fila["var1"],
                    options=[ft.dropdown.Option(v) for v in v1_options],
                    width=120,
                    border_color=BORDER_COLOR,
                    focused_border_color=ACCENT_COLOR,
                    bgcolor=BG_FIELD,
                    color=TEXT_PRIMARY,
                    border_radius=8,
                    on_select=crear_on_change_prop(idx, "var1"),
                )

                var2_dd = ft.Dropdown(
                    value=fila["var2"],
                    options=[ft.dropdown.Option(v) for v in v2_options],
                    width=120,
                    border_color=BORDER_COLOR,
                    focused_border_color=ACCENT_COLOR,
                    bgcolor=BG_FIELD,
                    color=TEXT_PRIMARY,
                    border_radius=8,
                    on_select=crear_on_change_prop(idx, "var2"),
                )

                btn_del = ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_color=RED,
                    icon_size=18,
                    on_click=crear_on_click_del(idx),
                    tooltip="Eliminar restricción lógica"
                )

                if categoria == "Lógica Pura":
                    ops = ["NEGACION", "CONJUNCION", "DISYUNCION", "EXCLUSION_MUTUA", "IMPLICACION", "EQUIVALENCIA"]
                    if fila.get("op") not in ops:
                        fila["op"] = "NEGACION"

                    op_dd = ft.Dropdown(
                        value=fila["op"],
                        options=[ft.dropdown.Option(o) for o in ops],
                        width=170,
                        border_color=BORDER_COLOR,
                        focused_border_color=ACCENT_COLOR,
                        bgcolor=BG_FIELD,
                        color=TEXT_PRIMARY,
                        border_radius=8,
                        on_select=crear_on_change_prop(idx, "op"),
                    )

                    logica_pura_rows.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"Restricción #{len(logica_pura_rows)+1}:", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500, width=80),
                                var1_dd,
                                op_dd,
                                var2_dd,
                                btn_del
                            ], spacing=8, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=6, border_radius=6, bgcolor="#131520"
                        )
                    )

                elif categoria in ("Activación Umbral", "M Grande"):
                    # Solo ACTIVACION_UMBRAL soportado por celdas
                    ops = ["ACTIVACION_UMBRAL"]
                    if fila.get("op") not in ops:
                        fila["op"] = "ACTIVACION_UMBRAL"

                    op_dd = ft.Dropdown(
                        value=fila["op"],
                        options=[ft.dropdown.Option(o) for o in ops],
                        width=170,
                        border_color=BORDER_COLOR,
                        focused_border_color=ACCENT_COLOR,
                        bgcolor=BG_FIELD,
                        color=TEXT_PRIMARY,
                        border_radius=8,
                        on_select=crear_on_change_prop(idx, "op"),
                    )

                    m_grande_rows.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"Restricción #{len(m_grande_rows)+1}:", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500, width=80),
                                var1_dd,
                                op_dd,
                                var2_dd,
                                btn_del
                            ], spacing=8, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=6, border_radius=6, bgcolor="#131520"
                        )
                    )

                elif categoria == "Asignación Lógica":
                    ops = ["AND_EVAL", "OR_EVAL", "XOR_EVAL"]
                    if fila.get("op") not in ops:
                        fila["op"] = "AND_EVAL"

                    op_dd = ft.Dropdown(
                        value=fila["op"],
                        options=[ft.dropdown.Option(o) for o in ops],
                        width=120,
                        border_color=BORDER_COLOR,
                        focused_border_color=ACCENT_COLOR,
                        bgcolor=BG_FIELD,
                        color=TEXT_PRIMARY,
                        border_radius=8,
                        on_select=crear_on_change_prop(idx, "op"),
                    )

                    dest_dd = ft.Dropdown(
                        value=fila["var_dest"],
                        options=[ft.dropdown.Option(v) for v in dest_options],
                        width=120,
                        border_color=BORDER_COLOR,
                        focused_border_color=ACCENT_COLOR,
                        bgcolor=BG_FIELD,
                        color=TEXT_PRIMARY,
                        border_radius=8,
                        on_select=crear_on_change_prop(idx, "var_dest"),
                    )

                    asignacion_rows.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Text(f"Restricción #{len(asignacion_rows)+1}:", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500, width=80),
                                dest_dd,
                                ft.Text("=", color=TEXT_MUTED, size=13, weight=ft.FontWeight.BOLD),
                                ft.Text("(", color=TEXT_MUTED, size=13),
                                var1_dd,
                                op_dd,
                                var2_dd,
                                ft.Text(")", color=TEXT_MUTED, size=13),
                                btn_del
                            ], spacing=6, alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                            padding=6, border_radius=6, bgcolor="#131520"
                        )
                    )

            # Construir los controles de los ExpansionTiles
            col_pura = ft.Column(logica_pura_rows + [
                ft.Row([
                    _crear_boton_ui("Añadir Relación Lógica Pura", ft.Icons.ADD, lambda _: agregar_relacion_logica("Lógica Pura", "NEGACION")),
                ], alignment=ft.MainAxisAlignment.START)
            ], spacing=8)
            
            col_mgrande = ft.Column(m_grande_rows + [
                ft.Row([
                    _crear_boton_ui("Añadir Relación M Grande", ft.Icons.ADD, lambda _: agregar_relacion_logica("Activación Umbral", "ACTIVACION_UMBRAL")),
                ], alignment=ft.MainAxisAlignment.START)
            ], spacing=8)
            
            col_asignacion = ft.Column(asignacion_rows + [
                ft.Row([
                    _crear_boton_ui("Añadir Asignación Lógica (Reificación)", ft.Icons.ADD, lambda _: agregar_relacion_logica("Asignación Lógica", "AND_EVAL")),
                ], alignment=ft.MainAxisAlignment.START)
            ], spacing=8)

            tile_pura = ft.ExpansionTile(
                title=ft.Text("1. Relaciones Lógicas Puras (OperadorLogico)", size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                subtitle=ft.Text("Fuerza incompatibilidades, condicionales simples y equivalencias entre variables binarias.", size=11, color=TEXT_MUTED),
                controls=[col_pura],
                controls_padding=10,
                expanded=len(logica_pura_rows) > 0,
            )

            tile_mgrande = ft.ExpansionTile(
                title=ft.Text("2. Modelado M Grande (OperadorMGrande)", size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                subtitle=ft.Text("Activa o desactiva cotas en variables usando interruptores binarios.", size=11, color=TEXT_MUTED),
                controls=[col_mgrande],
                controls_padding=10,
                expanded=len(m_grande_rows) > 0,
            )

            tile_asignacion = ft.ExpansionTile(
                title=ft.Text("3. Evaluación y Asignación Lógica (OperadorAsignacionLogica)", size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                subtitle=ft.Text("Calcula el resultado de operaciones booleanas y las guarda en una variable binaria.", size=11, color=TEXT_MUTED),
                controls=[col_asignacion],
                controls_padding=10,
                expanded=len(asignacion_rows) > 0,
            )

            columna_restricciones_logicas.controls.extend([tile_pura, tile_mgrande, tile_asignacion])
        tarjeta_restricciones_logicas = render_bloque_contenedor("Restricciones Lógicas (M Grande y Asignación)", columna_restricciones_logicas)

        scrollable_body = ft.Column([tarjeta_fo, tarjeta_tipo_var, tarjeta_restricciones, tarjeta_restricciones_logicas], spacing=16)
    else:
        # Modo algebraico o CSV
        titulo_seccion = "Ingreso en Formato Algebraico Natural (PI)" if modo_ingreso_actual == 1 else "Ingreso en Formato Coeficientes CSV (PI)"
        
        # Objetivo (2 líneas)
        label_obj = (
            "Función Objetivo (Línea 1: Fórmula Z, Línea 2: Tipos ej: x1=C x2=E)"
            if modo_ingreso_actual == 1 else
            "Coeficientes Objetivo (Línea 1: MAX,3,5 , Línea 2: C,E)"
        )
        text_hint = (
            "L1: MAX Z = 3x1 + 5x2\nL2: x1=C x2=E"
            if modo_ingreso_actual == 1 else
            "L1: MAX, 3, 5\nL2: C, E"
        )
        
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
            multiline=True,
            min_lines=2,
            max_lines=2,
            border_radius=8,
            on_change=cambiar_objetivo_avanzado,
        )

        # Restricciones
        label_res = "Escribe las Restricciones y Reglas Lógicas (Una por línea)" if modo_ingreso_actual == 1 else "Ingresa las Restricciones CSV (Una por línea)"
        text_hint_res = "Ej: 2x1 + x2 <= 10\nx1 NOT x2" if modo_ingreso_actual == 1 else "Ej: 2, 1, <=, 10\n1, NOT, 2"
        
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

        btn_info = ft.IconButton(
            icon=ft.Icons.INFO_OUTLINE,
            icon_color=ACCENT_COLOR,
            icon_size=20,
            tooltip="Ver manual de sintaxis",
            on_click=lambda e: abrir_ayuda(e, modo_ingreso_actual)
        )

        tarjeta_avanzada = render_bloque_contenedor(
            titulo_seccion,
            ft.Column(
                [
                    ft.Row([ft.Text("Parámetros del Modelo", size=12, color=TEXT_MUTED), btn_info], spacing=6, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    input_objetivo_avanzado,
                    input_restricciones_avanzado
                ],
                spacing=14,
                expand=True,
            )
        )

        scrollable_body = tarjeta_avanzada

    # Cabecera con título a la izquierda y formato a la derecha (igual que PL)
    cabecera_row = ft.Row(
        [
            ft.Column(
                [
                    ft.Text("Configuración del Modelo Entero (PI)", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text("Digita los parámetros del problema entero/mixto usando el formato que te sea más cómodo.", size=12, color=TEXT_MUTED),
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

    return ft.Column(
        [
            cabecera_row,
            ft.Divider(color=BORDER_COLOR, height=1),
            scrollable_body,
            ft.Divider(color=BORDER_COLOR, height=1),
            barra_botones_inferior,
        ],
        spacing=16,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )