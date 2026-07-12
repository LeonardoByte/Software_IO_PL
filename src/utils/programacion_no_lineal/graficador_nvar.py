# src/utils/programacion_no_lineal/graficador_nvar.py
"""
Genera un contour plot con la trayectoria del gradiente para f(x1, x2).
Solo funciona con exactamente 2 variables.
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
from src.models.metodos.programacion_no_lineal.evaluador import construir_funcion_vec

_BG    = "#0f1117"
_PANEL = "#161822"
_GRID  = "#2a2d3a"
_CURVE = "#7c3aed"
_GREEN = "#1d9e75"
_AMBER = "#f6ad55"
_TEXT  = "#c0c4d0"


def generar_grafico_nvar(
    problema: ProblemaNoLineal,
    respuesta: RespuestaNoLineal,
) -> Optional[str]:
    if len(problema.variables) != 2:
        return None
    if not respuesta.iteraciones:
        return None

    x1n, x2n = problema.variables
    f_vec = construir_funcion_vec(problema.funcion_str, problema.variables)

    x1_path = [it.datos[x1n] for it in respuesta.iteraciones if x1n in it.datos]
    x2_path = [it.datos[x2n] for it in respuesta.iteraciones if x2n in it.datos]
    if not x1_path or not x2_path:
        return None

    pad1 = max(1.0, (max(x1_path) - min(x1_path)) * 0.5) + 0.5
    pad2 = max(1.0, (max(x2_path) - min(x2_path)) * 0.5) + 0.5
    x1_min, x1_max = min(x1_path) - pad1, max(x1_path) + pad1
    x2_min, x2_max = min(x2_path) - pad2, max(x2_path) + pad2

    X1, X2 = np.meshgrid(
        np.linspace(x1_min, x1_max, 220),
        np.linspace(x2_min, x2_max, 220),
    )
    Z = np.vectorize(lambda a, b: f_vec(np.array([a, b])))(X1, X2)
    Z = np.where(np.isfinite(Z), Z, np.nan)

    fig, ax = plt.subplots(figsize=(8, 5.5))
    fig.patch.set_facecolor(_BG)
    ax.set_facecolor(_PANEL)
    for spine in ax.spines.values():
        spine.set_edgecolor(_GRID)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors=_TEXT, labelsize=9)
    ax.xaxis.label.set_color(_TEXT)
    ax.yaxis.label.set_color(_TEXT)
    ax.grid(True, color=_GRID, linewidth=0.5, alpha=0.7)

    contf = ax.contourf(X1, X2, Z, levels=25, cmap='plasma', alpha=0.55)
    ax.contour(X1, X2, Z, levels=25, colors='white', alpha=0.2, linewidths=0.5)

    cbar = fig.colorbar(contf, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.tick_params(colors=_TEXT, labelsize=8)
    cbar.set_label(f"f({x1n},{x2n})", color=_TEXT, fontsize=9)

    # Trayectoria
    ax.plot(x1_path, x2_path, color=_CURVE, linewidth=2, zorder=3, alpha=0.9)
    if len(x1_path) > 2:
        ax.scatter(x1_path[1:-1], x2_path[1:-1], color=_CURVE, s=18, zorder=4, alpha=0.6)

    # Punto inicial
    ax.scatter([x1_path[0]], [x2_path[0]], color=_AMBER, s=90, zorder=6, marker='D',
               label=f"x₀ = ({x1_path[0]:.3g}, {x2_path[0]:.3g})")

    # Punto óptimo
    opt_color = _AMBER if problema.tipo == TipoOptimizacion.MAX else _GREEN
    if respuesta.punto_optimo and len(respuesta.punto_optimo) >= 2:
        xo1, xo2 = float(respuesta.punto_optimo[0]), float(respuesta.punto_optimo[1])
        ax.scatter([xo1], [xo2], color=opt_color, s=150, zorder=7, marker='*',
                   label=f"x* = ({xo1:.4g}, {xo2:.4g}),  f = {respuesta.z_optimo:.4g}")

    ax.set_xlabel(x1n, fontsize=10)
    ax.set_ylabel(x2n, fontsize=10)
    ax.set_title(
        f"{problema.tipo.value}  f({x1n}, {x2n}) — Trayectoria del Gradiente",
        color=_TEXT, fontsize=10, pad=8,
    )
    ax.legend(facecolor=_PANEL, edgecolor=_GRID, labelcolor=_TEXT, fontsize=9, framealpha=1)

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=110, facecolor=_BG)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
