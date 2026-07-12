# src/utils/programacion_no_lineal/graficador_1var.py
"""
Genera el gráfico de f(x) en [a, b] para optimización de una variable.
Retorna una cadena data-URI base64 lista para ft.Image(src=...).
"""

from __future__ import annotations
from io import BytesIO
import base64
from typing import Optional

import numpy as np
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

from src.models.entity.programacion_lineal.enums import TipoOptimizacion
from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal
from src.models.entity.programacion_no_lineal.respuesta import RespuestaNoLineal
from src.models.metodos.programacion_no_lineal.evaluador import construir_funcion

_BG     = "#0f1117"
_PANEL  = "#161822"
_GRID   = "#2a2d3a"
_CURVE  = "#7c3aed"
_GREEN  = "#1d9e75"
_AMBER  = "#f6ad55"
_TEXT   = "#c0c4d0"


def generar_grafico_1var(
    problema: ProblemaNoLineal,
    respuesta: RespuestaNoLineal,
) -> Optional[str]:
    if problema.intervalo is None or respuesta.punto_optimo is None:
        return None

    a, b = float(problema.intervalo[0]), float(problema.intervalo[1])
    f = construir_funcion(problema.funcion_str, problema.variables)
    var_name = problema.variables[0]

    x_vals = np.linspace(a, b, 400)
    y_vals = np.array([f(xi) for xi in x_vals])

    mask = np.isfinite(y_vals)
    x_plot, y_plot = x_vals[mask], y_vals[mask]
    if len(x_plot) == 0:
        return None

    x_opt = float(respuesta.punto_optimo[0])
    y_opt = float(respuesta.z_optimo)
    opt_color = _AMBER if problema.tipo == TipoOptimizacion.MAX else _GREEN

    fig, ax = plt.subplots(figsize=(8, 4.2))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_PANEL)

    for spine in ax.spines.values():
        spine.set_edgecolor(_GRID)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    ax.grid(True, color=_GRID, linewidth=0.6, alpha=0.9)
    ax.tick_params(colors=_TEXT, labelsize=9)
    ax.xaxis.label.set_color(_TEXT)
    ax.yaxis.label.set_color(_TEXT)

    # Curva principal
    ax.plot(x_plot, y_plot, color=_CURVE, linewidth=2.5, zorder=3,
            label=f"f({var_name})")

    # Línea vertical en el óptimo
    ax.axvline(x_opt, color=opt_color, linewidth=1.5, linestyle='--', alpha=0.75, zorder=2)

    # Punto óptimo
    ax.scatter([x_opt], [y_opt], color=opt_color, s=90, zorder=5,
               label=f"{problema.tipo.value}: {var_name}* ≈ {x_opt:.4g},  f = {y_opt:.4g}")

    # Anotación
    ax.annotate(
        f"  {var_name}* ≈ {x_opt:.4g}",
        xy=(x_opt, y_opt),
        xytext=(x_opt, y_opt),
        color=opt_color, fontsize=9,
    )

    ax.set_xlabel(var_name, fontsize=10)
    ax.set_ylabel(f"f({var_name})", fontsize=10)
    ax.legend(facecolor=_PANEL, edgecolor=_GRID, labelcolor=_TEXT, fontsize=9, framealpha=1)

    plt.tight_layout()

    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=110, facecolor=_BG)
    plt.close(fig)

    encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"
