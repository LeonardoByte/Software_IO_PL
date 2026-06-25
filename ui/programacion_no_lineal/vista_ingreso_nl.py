# ui/programacion_no_lineal/vista_ingreso_nl.py
"""
Formulario de ingreso para Programación No Lineal.
El usuario define la función objetivo, variables, intervalo/punto inicial
y restricciones opcionales.  Al guardar, el problema queda activo y en historial.
"""

from __future__ import annotations
from typing import Callable, List, Optional
import flet as ft

from src.controller.controlador_no_lineal import ControladorNoLineal
from src.models.entity.programacion_lineal.enums import TipoOptimizacion
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal, RestriccionNL

# ── paleta ──────────────────────────────────────────────────────────────────────
ACCENT   = "#7c3aed"
BG_CARD  = "#161822"
BG_MAIN  = "#0f1117"
BORDER   = "#2a2d3a"
TEXT_P   = "#f0f0f0"
TEXT_M   = "#6b7280"
GREEN    = "#1d9e75"
RED      = "#ef645f"
AMBER    = "#f6ad55"


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


def _campo(label: str, hint: str, ref: ft.Ref, multiline=False, ancho: Optional[int] = None) -> ft.TextField:
    return ft.TextField(
        label=label, hint_text=hint, ref=ref,
        multiline=multiline, min_lines=1, max_lines=3 if multiline else 1,
        border_color=BORDER, focused_border_color=ACCENT,
        label_style=ft.TextStyle(color=TEXT_M, size=12),
        text_style=ft.TextStyle(color=TEXT_P, size=13),
        bgcolor="#1e2130", width=ancho,
    )


@ft.component
def VistaIngresoNL(controlador: ControladorNoLineal, navegar_a: Callable = None):
    # ── estado ──────────────────────────────────────────────────────────────────
    status_msg,   set_status   = ft.use_state(("", ""))        # (texto, color)
    restricciones_raw, set_rest = ft.use_state([])              # lista de (expr, signo)

    # ── refs de los campos ──────────────────────────────────────────────────────
    ref_funcion  = ft.Ref[ft.TextField]()
    ref_vars     = ft.Ref[ft.TextField]()
    ref_tipo     = ft.Ref[ft.Dropdown]()
    ref_a        = ft.Ref[ft.TextField]()
    ref_b        = ft.Ref[ft.TextField]()
    ref_p0       = ft.Ref[ft.TextField]()
    ref_tol      = ft.Ref[ft.TextField]()
    ref_maxiter  = ft.Ref[ft.TextField]()

    # ── helpers de parsing ──────────────────────────────────────────────────────
    def _leer_str(ref: ft.Ref[ft.TextField], default: str = "") -> str:
        return (ref.current.value or "").strip() if ref.current else default

    def _leer_float(ref: ft.Ref[ft.TextField], default: float = 0.0) -> float:
        try:
            return float(_leer_str(ref))
        except ValueError:
            return default

    def _parsear_variables(texto: str) -> tuple:
        partes = [v.strip() for v in texto.replace(",", " ").split() if v.strip()]
        return tuple(partes) if partes else ("x",)

    def _parsear_punto(texto: str) -> tuple:
        try:
            return tuple(float(v) for v in texto.replace(",", " ").split() if v.strip())
        except ValueError:
            return ()

    # ── guardar problema ────────────────────────────────────────────────────────
    def guardar(_e):
        funcion = _leer_str(ref_funcion)
        vars_texto = _leer_str(ref_vars, "x")
        if not funcion:
            set_status(("Escribe la función objetivo antes de guardar.", RED))
            return

        variables = _parsear_variables(vars_texto)
        tipo = (TipoOptimizacion.MAX
                if (ref_tipo.current and ref_tipo.current.value == "MAX")
                else TipoOptimizacion.MIN)

        # intervalo
        a_str = _leer_str(ref_a)
        b_str = _leer_str(ref_b)
        intervalo = None
        if a_str and b_str:
            try:
                intervalo = (float(a_str), float(b_str))
            except ValueError:
                pass

        # punto inicial
        p0_str = _leer_str(ref_p0)
        punto_inicial = _parsear_punto(p0_str) or None

        # restricciones
        rests = tuple(
            RestriccionNL(expresion=expr.strip(), signo=signo)
            for expr, signo in restricciones_raw
            if expr.strip()
        )

        tol = _leer_float(ref_tol, 1e-6)
        max_iter = int(_leer_float(ref_maxiter, 100))

        try:
            tol = float(_leer_str(ref_tol) or "1e-6")
        except ValueError:
            tol = 1e-6

        problema = ProblemaNoLineal(
            tipo=tipo,
            funcion_str=funcion,
            variables=variables,
            intervalo=intervalo,
            punto_inicial=punto_inicial,
            restricciones=rests,
            tolerancia=tol,
            max_iteraciones=max(1, max_iter),
        )

        controlador.establecer_problema(problema)
        controlador.guardar_en_historial(problema)
        set_status(("Problema guardado y activado. Navega a un método para resolverlo.", GREEN))

    # ── restricciones dinámicas ─────────────────────────────────────────────────
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

    # ── construir filas de restricciones ────────────────────────────────────────
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
        icono = ft.Icons.CHECK_CIRCLE if color == GREEN else ft.Icons.ERROR_OUTLINE
        barra_estado = ft.Container(
            content=ft.Row([
                ft.Icon(icono, color=color, size=16),
                ft.Text(status_msg[0], color=color, size=12),
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

    # ── problema activo badge ───────────────────────────────────────────────────
    activo = controlador.problema_activo
    badge_activo = ft.Container()
    if activo:
        badge_activo = ft.Container(
            content=ft.Row([
                ft.Icon(ft.Icons.BOLT, color=AMBER, size=14),
                ft.Text(
                    f"Activo: {activo.tipo.value} f({', '.join(activo.variables)}) = {activo.funcion_str}",
                    size=11, color=AMBER,
                ),
            ], spacing=6),
            padding=10, border_radius=8, bgcolor=AMBER + "14",
            border=ft.Border(
                top=ft.BorderSide(1, AMBER + "44"), bottom=ft.BorderSide(1, AMBER + "44"),
                left=ft.BorderSide(1, AMBER + "44"), right=ft.BorderSide(1, AMBER + "44"),
            ),
        )

    # ── layout ─────────────────────────────────────────────────────────────────
    return ft.Column(
        controls=[
            ft.Column([
                ft.Text("Definir Problema No Lineal", size=20, weight=ft.FontWeight.BOLD, color=TEXT_P),
                ft.Text(
                    "Escribe la función objetivo en Python (usa **, *, /, +, -, sin, cos, exp, log, sqrt…).",
                    size=12, color=TEXT_M,
                ),
            ], spacing=2),
            ft.Divider(color=BORDER, height=1),
            badge_activo,
            barra_estado,

            # ── Función objetivo
            _seccion("FUNCIÓN OBJETIVO", [
                _campo("f(x₁, x₂, …)", "3*x1**2 - 2*x1*x2 + x2", ref_funcion),
                ft.Row([
                    _campo("Variables (separadas por coma)", "x1, x2", ref_vars, ancho=260),
                    ft.Dropdown(
                        ref=ref_tipo,
                        label="Tipo",
                        options=[ft.dropdown.Option("MIN"), ft.dropdown.Option("MAX")],
                        value="MIN", width=110,
                        bgcolor="#1e2130", border_color=BORDER,
                        label_style=ft.TextStyle(color=TEXT_M, size=12),
                    ),
                ], spacing=12),
            ]),

            # ── Intervalo (métodos de 1 variable)
            _seccion("INTERVALO  ·  Sección Áurea", [
                ft.Text("Para funciones de 1 variable sobre un intervalo [a, b].", size=11, color=TEXT_M),
                ft.Row([
                    _campo("a", "0.0", ref_a, ancho=130),
                    _campo("b", "1.0", ref_b, ancho=130),
                ], spacing=12),
            ]),

            # ── Punto inicial (métodos iterativos)
            _seccion("PUNTO INICIAL  ·  Newton / Gradiente / KKT", [
                ft.Text(
                    "Valores iniciales de cada variable, separados por coma o espacio (en el mismo orden).",
                    size=11, color=TEXT_M,
                ),
                _campo("x₀ (punto inicial)", "0.5  o  0.5, 1.0  o  0, 0", ref_p0),
            ]),

            # ── Restricciones (KKT / Lagrange)
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

            # ── Parámetros numéricos
            _seccion("PARÁMETROS NUMÉRICOS", [
                ft.Row([
                    _campo("Tolerancia", "1e-6", ref_tol, ancho=160),
                    _campo("Máx. iteraciones", "100", ref_maxiter, ancho=160),
                ], spacing=12),
            ]),

            # ── Botones de acción
            ft.Container(
                content=ft.Row([
                    ft.ElevatedButton(
                        content=ft.Row([
                            ft.Icon(ft.Icons.SAVE_ALT, size=16, color="white"),
                            ft.Text("Guardar problema", size=13, color="white"),
                        ], spacing=6, tight=True),
                        bgcolor=ACCENT, on_click=guardar,
                    ),
                ], spacing=12),
                padding=ft.Padding(left=0, right=0, top=4, bottom=4),
            ),

            ft.Container(
                content=ft.Text(
                    "Después de guardar, navega desde el menú lateral al método que deseas usar.",
                    size=11, color=TEXT_M, italic=True,
                ),
            ),
        ],
        spacing=16,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )
