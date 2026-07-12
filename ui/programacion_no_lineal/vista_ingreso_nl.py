# ui/programacion_no_lineal/vista_ingreso_nl.py
"""
Formulario de ingreso para Programación No Lineal.
Los campos se pre-rellenan desde el problema activo (para edición).
Al guardar, navega automáticamente al Gráfico.
"""

from __future__ import annotations
from typing import Callable, Optional
import re
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal
from src.models.entity.programacion_lineal.enums import TipoOptimizacion
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal, RestriccionNL

ACCENT   = "#7c3aed"
BG_CARD  = "#161822"
BG_MAIN  = "#0f1117"
BORDER   = "#2a2d3a"
TEXT_P   = "#f0f0f0"
TEXT_M   = "#6b7280"
GREEN    = "#1d9e75"
RED      = "#ef645f"
AMBER    = "#f6ad55"

_MATH_NAMES = {
    "sin", "cos", "tan", "arcsin", "arccos", "arctan",
    "exp", "log", "log10", "log2", "sqrt", "abs",
    "pi", "e", "inf", "nan", "floor", "ceil", "round",
}


def _seccion(titulo: str, controles: list) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Text(titulo, size=12, weight=ft.FontWeight.W_700, color=ACCENT),
            ft.Divider(height=1, color=BORDER),
            *controles,
        ], spacing=10),
        padding=16, border_radius=10, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER), bottom=ft.BorderSide(1, BORDER),
            left=ft.BorderSide(1, BORDER), right=ft.BorderSide(1, BORDER),
        ),
    )


def _campo(label: str, hint: str, value: str, on_change,
           multiline=False, ancho: Optional[int] = None) -> ft.TextField:
    return ft.TextField(
        label=label, hint_text=hint,
        value=value,
        on_change=on_change,
        multiline=multiline, min_lines=1, max_lines=3 if multiline else 1,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_M, size=12),
        text_style=ft.TextStyle(color=TEXT_P, size=13),
        bgcolor="#1e2130", width=ancho,
    )


@ft.component
def VistaIngresoNL(controlador: ControladorNoLineal, navegar_a: Callable = None):
    # Pre-rellenar desde problema activo (se usa solo en la primera renderización)
    activo = controlador.problema_activo

    # ── estado de cada campo ────────────────────────────────────────────────────
    funcion_val,  set_funcion  = ft.use_state(activo.funcion_str if activo else "")
    vars_val,     set_vars     = ft.use_state(", ".join(activo.variables) if activo else "")
    tipo_val,     set_tipo     = ft.use_state(activo.tipo.value if activo else "MIN")
    a_val,        set_a        = ft.use_state(
        str(activo.intervalo[0]) if activo and activo.intervalo else "")
    b_val,        set_b        = ft.use_state(
        str(activo.intervalo[1]) if activo and activo.intervalo else "")
    p0_val,       set_p0       = ft.use_state(
        ", ".join(str(v) for v in activo.punto_inicial)
        if activo and activo.punto_inicial else "")
    tol_val,      set_tol      = ft.use_state(
        str(activo.tolerancia) if activo else "1e-6")
    maxiter_val,  set_maxiter  = ft.use_state(
        str(activo.max_iteraciones) if activo else "100")
    restricciones_raw, set_rest = ft.use_state(
        [(r.expresion, r.signo) for r in activo.restricciones] if activo else [])

    status_msg, set_status = ft.use_state(("", ""))

    # ── guardar problema ────────────────────────────────────────────────────────
    def guardar(_e):
        funcion = funcion_val.strip()
        vars_texto = vars_val.strip() or "x"

        if not funcion:
            set_status(("Escribe la función objetivo antes de guardar.", RED))
            return

        # Rechazar variables de una sola letra (x, y, z…); exigir x1, x2, etc.
        declared_vars = set(v.strip() for v in vars_texto.replace(",", " ").split() if v.strip())
        single_letter = [v for v in declared_vars if len(v) == 1 and v.isalpha()]
        if single_letter:
            set_status((
                f"Variable(s) '{', '.join(sorted(single_letter))}' no permitida(s). "
                "Usa x1 aunque sea una sola variable (x1, x2, …).",
                RED,
            ))
            return

        # Validar que los tokens de la expresión coincidan con las variables declaradas
        expr_tokens = set(re.findall(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\b', funcion))
        unknown = expr_tokens - declared_vars - _MATH_NAMES
        if unknown:
            set_status((
                f"Advertencia: la expresión usa '{', '.join(sorted(unknown))}' "
                f"que no está en las variables declaradas ({', '.join(sorted(declared_vars))}). "
                "¿Olvidaste agregar la variable o usaste un nombre diferente?",
                AMBER,
            ))
            return

        variables = tuple(v.strip() for v in vars_texto.replace(",", " ").split() if v.strip()) or ("x",)
        tipo = TipoOptimizacion.MAX if tipo_val == "MAX" else TipoOptimizacion.MIN

        intervalo = None
        if a_val.strip() and b_val.strip():
            try:
                intervalo = (float(a_val), float(b_val))
            except ValueError:
                pass

        punto_inicial = None
        if p0_val.strip():
            try:
                punto_inicial = tuple(float(v) for v in p0_val.replace(",", " ").split() if v.strip())
            except ValueError:
                pass
            if punto_inicial is not None and len(punto_inicial) != len(variables):
                set_status((
                    f"El punto inicial debe tener exactamente {len(variables)} valor(es) "
                    f"(uno por variable: {', '.join(variables)}). "
                    f"Recibidos: {len(punto_inicial)}.",
                    RED,
                ))
                return

        rests = tuple(
            RestriccionNL(expresion=expr.strip(), signo=signo)
            for expr, signo in restricciones_raw
            if expr.strip()
        )

        try:
            tol = float(tol_val or "1e-6")
        except ValueError:
            tol = 1e-6
        try:
            max_iter = max(1, int(float(maxiter_val or "100")))
        except ValueError:
            max_iter = 100

        problema = ProblemaNoLineal(
            tipo=tipo,
            funcion_str=funcion,
            variables=variables,
            intervalo=intervalo,
            punto_inicial=punto_inicial,
            restricciones=rests,
            tolerancia=tol,
            max_iteraciones=max_iter,
        )

        controlador.establecer_problema(problema)
        controlador.guardar_en_historial(problema)
        set_status(("Problema guardado y activado correctamente.", GREEN))

        if navegar_a:
            navegar_a(2)  # ir al Gráfico

    def limpiar(_e):
        set_funcion("")
        set_vars("")
        set_tipo("MIN")
        set_a("")
        set_b("")
        set_p0("")
        set_tol("1e-6")
        set_maxiter("100")
        set_rest([])
        set_status(("Campos vaciados.", AMBER))

    # ── restricciones dinámicas ────────────────────────────────────────���────────
    def agregar_restriccion(_e):
        set_rest(lambda lst: lst + [("", "<=")])

    def actualizar_rest_expr(idx: int, valor: str):
        def _upd(lst):
            copia = list(lst)
            if idx < len(copia):
                copia[idx] = (valor, copia[idx][1])
            return copia
        set_rest(_upd)

    def actualizar_rest_signo(idx: int, valor: str):
        def _upd(lst):
            copia = list(lst)
            if idx < len(copia):
                copia[idx] = (copia[idx][0], valor)
            return copia
        set_rest(_upd)

    def eliminar_rest(idx: int, _e=None):
        def _upd(lst):
            copia = list(lst)
            if idx < len(copia):
                copia.pop(idx)
            return copia
        set_rest(_upd)

    # ── filas de restricciones ──────────────────────────────────────────────────
    filas_rest = []
    for i, (expr, signo) in enumerate(restricciones_raw):
        filas_rest.append(
            ft.Row([
                ft.TextField(
                    label=f"g{i+1}(x)", hint_text="x1 + x2 - 1",
                    value=expr,
                    on_change=lambda e, idx=i: actualizar_rest_expr(idx, e.control.value),
                    expand=True,
                    border_color=BORDER, focused_border_color=ACCENT,
                    label_style=ft.TextStyle(color=TEXT_M, size=12),
                    text_style=ft.TextStyle(color=TEXT_P, size=13),
                    bgcolor="#1e2130",
                ),
                ft.Dropdown(
                    options=[
                        ft.dropdown.Option("<="), ft.dropdown.Option("=="),
                        ft.dropdown.Option(">="),
                    ],
                    value=signo, width=90,
                    on_select=lambda e, idx=i: actualizar_rest_signo(idx, e.control.value),
                    bgcolor="#1e2130", border_color=BORDER,
                ),
                ft.Text("0", size=14, color=TEXT_P),
                ft.IconButton(
                    ft.Icons.DELETE_OUTLINE, icon_color=RED, icon_size=18,
                    on_click=lambda e, idx=i: eliminar_rest(idx, e),
                ),
            ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        )

    # ── barra de estado ─────────────────────────────────────────────────────────
    if status_msg[0]:
        color = status_msg[1]
        icono = ft.Icons.CHECK_CIRCLE if color == GREEN else (
            ft.Icons.WARNING_AMBER if color == AMBER else ft.Icons.ERROR_OUTLINE
        )
        barra_estado = ft.Container(
            content=ft.Row([
                ft.Icon(icono, color=color, size=16),
                ft.Text(status_msg[0], color=color, size=12, expand=True),
            ], spacing=8),
            padding=12, border_radius=8,
            bgcolor=color + "18",
            border=ft.Border(
                top=ft.BorderSide(1, color + "44"), bottom=ft.BorderSide(1, color + "44"),
                left=ft.BorderSide(1, color + "44"), right=ft.BorderSide(1, color + "44"),
            ),
        )
    else:
        barra_estado = ft.Container()

    # ── layout ─────────────────────────────────────────────────────────────────
    return ft.Column(
        controls=[
            ft.Column([
                ft.Text("Definir Problema No Lineal", size=20, weight=ft.FontWeight.BOLD, color=TEXT_P),
                ft.Text(
                    "Los nombres de variable en la expresión deben coincidir exactamente con los declarados.\n"
                    "Ej: si declaras 'x1, x2' → escribe  x1**2 + 3*x2 - 1  (no uses 'x' ni 'y').\n"
                    "Operadores: +  -  *  **  /   |   Funciones: sin, cos, exp, log, sqrt, abs",
                    size=11, color=TEXT_M,
                ),
            ], spacing=2),
            ft.Divider(color=BORDER, height=1),
            barra_estado,

            _seccion("FUNCIÓN OBJETIVO", [
                _campo("f(x1) o f(x1, x2, …)", "x1**2 - 4*x1  ó  x1**2 + x2**2",
                       funcion_val, lambda e: set_funcion(e.control.value)),
                ft.Row([
                    _campo("Variables (separadas por coma)", "x1, x2",
                           vars_val, lambda e: set_vars(e.control.value), ancho=260),
                    ft.Dropdown(
                        label="Tipo",
                        options=[ft.dropdown.Option("MIN"), ft.dropdown.Option("MAX")],
                        value=tipo_val,
                        on_select=lambda e: set_tipo(e.control.value),
                        width=110,
                        bgcolor="#1e2130", border_color=BORDER,
                        label_style=ft.TextStyle(color=TEXT_M, size=12),
                    ),
                ], spacing=12),
            ]),

            _seccion("INTERVALO  ·  Bisección", [
                ft.Text("Para funciones de 1 variable sobre un intervalo [a, b].", size=11, color=TEXT_M),
                ft.Row([
                    _campo("a", "0.0", a_val, lambda e: set_a(e.control.value), ancho=130),
                    _campo("b", "1.0", b_val, lambda e: set_b(e.control.value), ancho=130),
                ], spacing=12),
            ]),

            _seccion("PUNTO INICIAL  ·  Newton / Gradiente / KKT", [
                ft.Text(
                    "Valores iniciales de cada variable, separados por coma o espacio (en el mismo orden).",
                    size=11, color=TEXT_M,
                ),
                _campo("x₀ (punto inicial)", "0.5  o  0.5, 1.0  o  0, 0",
                       p0_val, lambda e: set_p0(e.control.value)),
            ]),

            _seccion("RESTRICCIONES  ·  KKT / Lagrange  (opcional)", [
                ft.Text("Escribe g(x) en el campo. El signo indica la relación con 0: g(x) ≤ 0.", size=11, color=TEXT_M),
                *filas_rest,
                ft.ElevatedButton(
                    content=ft.Row([
                        ft.Icon(ft.Icons.ADD, size=14, color="white"),
                        ft.Text("Añadir restricción", size=12, color="white"),
                    ], spacing=5, tight=True),
                    bgcolor="#374151", on_click=agregar_restriccion,
                ),
            ]),

            _seccion("PARÁMETROS NUMÉRICOS", [
                ft.Row([
                    _campo("Tolerancia", "1e-6", tol_val, lambda e: set_tol(e.control.value), ancho=160),
                    _campo("Máx. iteraciones", "100", maxiter_val, lambda e: set_maxiter(e.control.value), ancho=160),
                ], spacing=12),
            ]),

            ft.Container(
                content=ft.Row([
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SAVE_ALT, size=16, color="white"),
                            ft.Text("Guardar y Activar Problema", size=13, color="white"),
                        ], spacing=6, tight=True),
                        bgcolor=GREEN, on_click=guardar,
                    ),
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.REFRESH, size=16, color="white"),
                            ft.Text("Vaciar Campos", size=13, color="white"),
                        ], spacing=6, tight=True),
                        bgcolor="#374151", on_click=limpiar,
                    ),
                ], spacing=12),
                padding=ft.Padding(left=0, right=0, top=4, bottom=4),
            ),
        ],
        spacing=16,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
