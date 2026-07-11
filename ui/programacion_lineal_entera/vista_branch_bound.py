"""
Componente visual de la interfaz de usuario desarrollado sobre Flet (v0.85).
Responsable del renderizado del árbol de ramificación y poda (Branch & Bound).
"""

from __future__ import annotations
from fractions import Fraction
from typing import Any, List, Optional
import flet as ft

from src.models.entity.programacion_lineal.enums import EstadoProblema
from src.models.entity.programacion_lineal_entera.enums import TipoVariable
from src.models.entity.programacion_lineal_entera.respuesta import RespuestaBranchAndBound, NodoBranchAndBound
from src.controller.controlador_entera import ControladorEntera

ACCENT_COLOR = "#7c3aed"
BG_CARD      = "#161822"
BG_TABLE     = "#0d0f1a"
BORDER_COLOR = "#2a2d3a"
TEXT_MUTED   = "#6b7280"
TEXT_PRIMARY = "#f0f0f0"
GREEN        = "#7dd3a8"
AMBER        = "#f6ad55"
RED          = "#ef645f"
BLUE         = "#63b3ed"

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

def _fmt(valor: Any) -> str:
    if hasattr(valor, "item"):
        valor = valor.item()
    if isinstance(valor, Fraction):
        if valor.denominator == 1:
            return str(valor.numerator)
        return f"{valor.numerator}/{valor.denominator}"
    if isinstance(valor, float):
        texto = f"{valor:.6f}".rstrip("0").rstrip(".")
        return texto if texto else "0"
    return str(valor)

def _crear_alerta_status(mensaje: str, color: str, icono=None) -> ft.Row:
    if icono is None:
        icono = ft.Icons.CHECK_CIRCLE if color == GREEN else ft.Icons.WARNING_AMBER
    return ft.Row([
        ft.Container(
            content=ft.Row(
                [ft.Icon(icono, color=color, size=15),
                 ft.Text(mensaje, color=color, size=12)],
                spacing=8,
            ),
            padding=14, border_radius=8, bgcolor=color + "18",
            border=ft.Border(
                top=ft.BorderSide(1, color + "44"), bottom=ft.BorderSide(1, color + "44"),
                left=ft.BorderSide(1, color + "44"), right=ft.BorderSide(1, color + "44"),
            ),
        )
    ])

# Colores, etiquetas y color de texto sobre fondo sólido para cada estado de nodo
_ESTADO_CFG = {
    "optimo":              (GREEN,        "Óptimo entero",      "#0d2a1a"),
    "podado_cota":         (RED,          "Podado · cota",      "#ffffff"),
    "podado_infactible":   (RED,          "Podado · infactible","#ffffff"),
    "podado":              (RED,          "Podado",             "#ffffff"),
    "ramificado":          (ACCENT_COLOR, "Ramificado",         "#ffffff"),
    "activo":              (BLUE,         "Activo",             "#ffffff"),
}

def _badge_estado(estado: str) -> ft.Container:
    cfg = _ESTADO_CFG.get(estado, (TEXT_MUTED, estado, "#ffffff"))
    color, label, text_color = cfg
    return ft.Container(
        content=ft.Text(label, size=10, color=text_color, weight=ft.FontWeight.W_700),
        padding=ft.Padding(left=8, right=8, top=5, bottom=5),
        bgcolor=color,
        border_radius=99,
    )

def _crear_nodo_card(nodo: NodoBranchAndBound, num_original_vars: int) -> ft.Control:
    nodo_id = nodo.id_nodo
    estado = "activo"

    # Determinar estado semántico
    msg_l = nodo.mensaje.lower()
    if "factible" in msg_l:
        estado = "optimo"
    elif "cota" in msg_l:
        estado = "podado_cota"
    elif "inviable" in msg_l or "contradicción" in msg_l or "no óptima" in msg_l:
        estado = "podado_infactible"
    elif "podado" in msg_l:
        estado = "podado"
    elif "ramificación" in msg_l:
        estado = "ramificado"

    color_estado, _, _tc = _ESTADO_CFG.get(estado, (BORDER_COLOR, "", "#ffffff"))
    es_podado = "podado" in estado
    z_str = _fmt(nodo.z_local) if nodo.z_local is not None else "N/D"

    encabezado_items: list[ft.Control] = [
        ft.Text(f"N{nodo_id}", size=12, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
    ]
    if nodo.ramificacion is not None:
        ram = nodo.ramificacion
        op = "≤" if ram.es_limite_superior else "≥"
        condicion = f"X{ram.indice_variable + 1} {op} {_fmt(ram.cota)}"
        encabezado_items.append(
            ft.Container(
                content=ft.Text(condicion, size=9, color=BLUE, weight=ft.FontWeight.W_500),
                padding=4,
                bgcolor=BLUE + "18",
                border_radius=4,
                border=ft.Border(
                    top=ft.BorderSide(1, BLUE + "44"),
                    bottom=ft.BorderSide(1, BLUE + "44"),
                    left=ft.BorderSide(1, BLUE + "44"),
                    right=ft.BorderSide(1, BLUE + "44"),
                ),
            )
        )
    encabezado_items.append(_badge_estado(estado))

    # Variables originales compactadas en una línea
    variables_a_mostrar = (nodo.variables_locales or [])[:num_original_vars]
    vars_text = ("  ".join(f"X{i+1}={_fmt(v)}" for i, v in enumerate(variables_a_mostrar))) if variables_a_mostrar else "—"

    contenido = ft.Column(
        [
            ft.Row(encabezado_items, spacing=4, wrap=True),
            ft.Divider(height=1, color=BORDER_COLOR),
            ft.Row([
                ft.Text("Z:", size=10, color=TEXT_MUTED),
                ft.Text(
                    z_str,
                    size=14,
                    color=GREEN if estado == "optimo" else BLUE,
                    weight=ft.FontWeight.BOLD,
                ),
            ], spacing=4),
            ft.Text(vars_text, size=10, color=TEXT_MUTED),
            ft.Text(nodo.mensaje, size=10, color=TEXT_MUTED, italic=True, max_lines=2) if nodo.mensaje else ft.Container(height=0),
        ],
        spacing=4,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )

    return ft.Container(
        content=contenido,
        padding=10,
        border_radius=10,
        bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, color_estado + ("66" if es_podado else "55")),
            bottom=ft.BorderSide(1, color_estado + ("66" if es_podado else "55")),
            left=ft.BorderSide(3, color_estado + ("66" if es_podado else "55")),
            right=ft.BorderSide(1, BORDER_COLOR),
        ),
        width=240,
    )

def _tarjeta_resumen(resultado: RespuestaBranchAndBound, num_original_vars: int, problema: any) -> ft.Container:
    tipo = problema.tipo.value
    objetivo = problema.objetivo
    fo_str = _formatear_fo(tipo, objetivo)

    z_str = _fmt(resultado.z_optimo) if resultado.z_optimo is not None else "N/D"
    
    variables_filtradas = (resultado.variables_decision or [])[:num_original_vars]
    vars_str = ", ".join(f"X{i+1}={_fmt(v)}" for i, v in enumerate(variables_filtradas)) or "N/D"

    n_expl = len(resultado.arbol_nodos)
    n_pod = sum(1 for n in resultado.arbol_nodos if "podado" in n.mensaje.lower() or "inviable" in n.mensaje.lower() or "no óptima" in n.mensaje.lower())

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

    cuerpo: list[ft.Control] = [
        ft.Text(fo_str, size=14, color=TEXT_PRIMARY, weight=ft.FontWeight.W_600, selectable=True),
        ft.Row([
            _stat("Z óptimo entero", z_str, GREEN),
            _stat("Variables óptimas", vars_str, TEXT_PRIMARY),
            _stat("Nodos explorados", str(n_expl), BLUE),
            _stat("Nodos podados", str(n_pod), RED),
        ], spacing=8, wrap=True),
    ]
    if resultado.mensaje:
        cuerpo.append(ft.Text(f"Resultado del solver: {resultado.mensaje}", size=11, color=TEXT_MUTED, italic=True))

    return ft.Container(
        content=ft.Column(cuerpo, spacing=10),
        padding=16, border_radius=12, bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, ACCENT_COLOR + "66"), bottom=ft.BorderSide(1, ACCENT_COLOR + "66"),
            left=ft.BorderSide(1, ACCENT_COLOR + "66"), right=ft.BorderSide(1, ACCENT_COLOR + "66"),
        ),
    )

def _leyenda() -> ft.Container:
    estados = ["ramificado", "activo", "optimo", "podado_cota", "podado_infactible"]
    return ft.Container(
        content=ft.Row(
            [ft.Text("Leyenda:", size=11, color=TEXT_MUTED, weight=ft.FontWeight.W_500)]
            + [_badge_estado(e) for e in estados],
            spacing=8,
            wrap=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        padding=10,
        border_radius=8,
        bgcolor=BG_CARD,
        border=ft.Border(
            top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
            left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR),
        ),
    )

# Renderizar cada nodo del árbol produce varios controles Flet anidados (tarjeta +
# conectores). Para modelos con muchas variables enteras/binarias y poda débil, el
# árbol de Branch & Bound puede crecer a miles de nodos: intentar dibujarlos todos
# genera decenas de miles de controles anidados centrados dentro de una fila con
# scroll, lo que hace que el layout del cliente se congele al montar/desmontar la
# vista. Por eso se limita la cantidad de nodos que se dibujan visualmente.
MAX_NODOS_ARBOL_VISUAL = 150

def _renderizar_arbol(resultado: RespuestaBranchAndBound, num_original_vars: int, problema: any) -> list[ft.Control]:
    controles: list[ft.Control] = [
        _tarjeta_resumen(resultado, num_original_vars, problema),
    ]

    total_nodos = len(resultado.arbol_nodos)
    if total_nodos > MAX_NODOS_ARBOL_VISUAL:
        controles.append(
            _crear_alerta_status(
                f"El árbol de exploración tiene {total_nodos} nodos: es demasiado grande para "
                f"dibujarse completo. Se muestra únicamente el resumen del resultado.",
                AMBER,
                ft.Icons.WARNING_AMBER,
            )
        )
        return controles

    nodos_por_id = {nodo.id_nodo: nodo for nodo in resultado.arbol_nodos}
    hijos_por_padre: dict[int, list[NodoBranchAndBound]] = {}
    for nodo in resultado.arbol_nodos:
        padre = nodo.id_padre if nodo.id_padre is not None else 0
        hijos_por_padre.setdefault(padre, []).append(nodo)

    CONNECTOR_COLOR = "#3a3d4a"

    def _renderizar_subarbol(nodo_id: int) -> ft.Control:
        nodo = nodos_por_id.get(nodo_id)
        if nodo is None:
            return ft.Container()

        card = _crear_nodo_card(nodo, num_original_vars)
        # Ordenar hijos por ID para que salgan de izquierda a derecha en orden
        hijos = sorted(hijos_por_padre.get(nodo_id, []), key=lambda n: n.id_nodo)

        if not hijos:
            return ft.Column(
                [card],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        if len(hijos) == 1:
            # Un solo hijo: solo línea vertical
            return ft.Column(
                [
                    ft.Row([card], alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row(
                        [ft.Container(width=2, height=36, bgcolor=CONNECTOR_COLOR)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    _renderizar_subarbol(hijos[0].id_nodo),
                ],
                spacing=0,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )

        # Múltiples hijos: el borde superior del Container actúa como línea horizontal
        child_cols = [
            ft.Column(
                [
                    ft.Row(
                        [ft.Container(width=2, height=20, bgcolor=CONNECTOR_COLOR)],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    _renderizar_subarbol(hijo.id_nodo),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=0,
            )
            for hijo in hijos
        ]

        return ft.Column(
            [
                ft.Row([card], alignment=ft.MainAxisAlignment.CENTER),
                ft.Row(
                    [ft.Container(width=2, height=20, bgcolor=CONNECTOR_COLOR)],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.Container(
                    content=ft.Row(
                        child_cols,
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.START,
                        spacing=24,
                    ),
                    border=ft.Border(top=ft.BorderSide(2, CONNECTOR_COLOR)),
                ),
            ],
            spacing=0,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )

    raiz = next((n for n in resultado.arbol_nodos if n.id_padre is None), None)
    if raiz is not None:
        tree_widget = _renderizar_subarbol(raiz.id_nodo)
        controles.append(
            ft.Container(
                content=ft.Row(
                    [tree_widget],
                    scroll=ft.ScrollMode.AUTO,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=16,
            )
        )

    return controles

@ft.component

def VistaBranchBound(controlador: ControladorEntera):
    resultado_ref = ft.use_ref(None)
    problema_ref  = ft.use_ref(None)

    problema_actual = controlador.problema_activo
    # Solo resolver si el problema cambió
    if resultado_ref.current is None or problema_ref.current is not problema_actual:
        problema_ref.current = problema_actual
        if problema_actual:
            try:
                resultado_ref.current = controlador.resolver_PLE(problema_actual, 1)
            except Exception:
                resultado_ref.current = None
        else:
            resultado_ref.current = None

    resultado = resultado_ref.current
    
    problema = controlador.problema_activo

    header = ft.Column([
        ft.Text("Branch & Bound", size=20, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
        ft.Text("Resolución paso a paso mediante Ramificación y Acotamiento.", size=12, color=TEXT_MUTED),
    ], spacing=2)

    # 1. Sin problema activo
    if problema is None:
        status_row = _crear_alerta_status("Ingresa o selecciona un problema entero primero.", AMBER, ft.Icons.INFO_OUTLINE)
        placeholder = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.DEVICE_HUB, color=TEXT_MUTED, size=48),
                ft.Text("Sin modelo activo en la sesión.", color=TEXT_MUTED, size=13, text_align=ft.TextAlign.CENTER),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=48, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, BORDER_COLOR), bottom=ft.BorderSide(1, BORDER_COLOR),
                left=ft.BorderSide(1, BORDER_COLOR), right=ft.BorderSide(1, BORDER_COLOR),
            ),
            alignment=ft.alignment.Alignment(0, 0),
        )
        return ft.Column([header, ft.Divider(color=BORDER_COLOR, height=1), status_row, placeholder], expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)

    # 2. Sin variables enteras definidas
    if not any(t in (TipoVariable.ENTERA, TipoVariable.BINARIA) for t in problema.tipos_variables):
        status_row = _crear_alerta_status("No hay variables enteras o binarias definidas en el modelo actual.", AMBER, ft.Icons.INFO_OUTLINE)
        placeholder = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.WARNING_AMBER, color=AMBER, size=40),
                ft.Text("El modelo no contiene restricciones de integridad.\nUsa variables Enteras (E) o Binarias (B) en la vista de ingreso.", color=AMBER, text_align=ft.TextAlign.CENTER, size=13),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
            padding=40, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, AMBER + "44"), bottom=ft.BorderSide(1, AMBER + "44"),
                left=ft.BorderSide(1, AMBER + "44"), right=ft.BorderSide(1, AMBER + "44"),
            ),
            alignment=ft.alignment.Alignment(0, 0),
        )
        return ft.Column([header, ft.Divider(color=BORDER_COLOR, height=1), status_row, placeholder], expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)

    # 3. Usar resultado cacheado
    resultado = resultado_ref.current

    # 4. Sin resultado
    if resultado is None:
        status_row = _crear_alerta_status("El motor matemático interrumpió el proceso inesperadamente.", RED)
        placeholder = ft.Container(
            content=ft.Text("No se pudo obtener solución para Branch & Bound.", color=RED),
            padding=16, border_radius=12, bgcolor=BG_CARD,
            border=ft.Border(
                top=ft.BorderSide(1, RED + "44"), bottom=ft.BorderSide(1, RED + "44"),
                left=ft.BorderSide(1, RED + "44"), right=ft.BorderSide(1, RED + "44"),
            ),
        )
        return ft.Column([header, ft.Divider(color=BORDER_COLOR, height=1), status_row, placeholder], expand=True, spacing=16, scroll=ft.ScrollMode.AUTO)

    # 5. Con resultado
    if resultado.estado == EstadoProblema.OPTIMO:
        status_row = _crear_alerta_status("Óptimo entero global alcanzado con éxito.", GREEN, ft.Icons.CHECK_CIRCLE)
    elif resultado.estado == EstadoProblema.INVIABLE:
        status_row = _crear_alerta_status("Inviabilidad: El problema no tiene solución entera factible.", RED, ft.Icons.ERROR_OUTLINE)
    else:
        status_row = _crear_alerta_status(f"Conclusión: {resultado.estado.value}", AMBER)

    # Número original de variables de decisión
    num_original_vars = len(problema.objetivo)

    arbol_controls = ft.Column(_renderizar_arbol(resultado, num_original_vars, problema), spacing=12)

    return ft.Column(
        [header, ft.Divider(color=BORDER_COLOR, height=1), status_row, arbol_controls],
        expand=False, spacing=16, scroll=ft.ScrollMode.AUTO
    )
