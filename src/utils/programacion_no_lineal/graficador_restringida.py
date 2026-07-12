# src/utils/programacion_no_lineal/graficador_restringida.py
"""
Genera un contour plot con la región factible sombreada y el óptimo marcado.
Para problemas NL restringidos linealmente con exactamente 2 variables.
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

_BG     = "#0f1117"
_PANEL  = "#161822"
_GRID   = "#2a2d3a"
_CURVE  = "#7c3aed"
_GREEN  = "#1d9e75"
_AMBER  = "#f6ad55"
_TEXT   = "#c0c4d0"
_BOUND  = "#f6ad55"   # color de las fronteras de restricción


def generar_grafico_restringida(
    problema: ProblemaNoLineal,
    respuesta: RespuestaNoLineal,
) -> Optional[str]:
    if len(problema.variables) != 2:
        return None
    if respuesta.punto_optimo is None or len(respuesta.punto_optimo) < 2:
        return None

    x1n, x2n = problema.variables
    f_vec = construir_funcion_vec(problema.funcion_str, problema.variables)

    xo1, xo2 = float(respuesta.punto_optimo[0]), float(respuesta.punto_optimo[1])
    pad = 2.5
    x1_min, x1_max = xo1 - pad * 2, xo1 + pad * 2
    x2_min, x2_max = xo2 - pad * 2, xo2 + pad * 2

    # Ampliar rango si hay punto inicial
    if respuesta.iteraciones:
        x1_vals = [it.datos[x1n] for it in respuesta.iteraciones if x1n in it.datos]
        x2_vals = [it.datos[x2n] for it in respuesta.iteraciones if x2n in it.datos]
        if x1_vals:
            x1_min = min(x1_min, min(x1_vals) - pad)
            x1_max = max(x1_max, max(x1_vals) + pad)
        if x2_vals:
            x2_min = min(x2_min, min(x2_vals) - pad)
            x2_max = max(x2_max, max(x2_vals) + pad)

    X1, X2 = np.meshgrid(
        np.linspace(x1_min, x1_max, 220),
        np.linspace(x2_min, x2_max, 220),
    )
    Z = np.vectorize(lambda a, b: f_vec(np.array([a, b])))(X1, X2)
    Z = np.where(np.isfinite(Z), Z, np.nan)

    # Región factible
    factible = np.ones(X1.shape, dtype=bool)
    rest_funcs = []
    for rest in problema.restricciones:
        g = construir_funcion_vec(rest.expresion, problema.variables)
        G = np.vectorize(lambda a, b, _g=g: _g(np.array([a, b])))(X1, X2)
        rest_funcs.append((G, rest.signo))
        if rest.signo == "<=":
            factible &= (G <= 1e-9)
        elif rest.signo == ">=":
            factible &= (G >= -1e-9)
        elif rest.signo == "==":
            factible &= (np.abs(G) <= 0.05)

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

    # Curvas de nivel
    contf = ax.contourf(X1, X2, Z, levels=25, cmap='plasma', alpha=0.45)
    ax.contour(X1, X2, Z, levels=25, colors='white', alpha=0.15, linewidths=0.5)

    cbar = fig.colorbar(contf, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.tick_params(colors=_TEXT, labelsize=8)
    cbar.set_label(f"f({x1n},{x2n})", color=_TEXT, fontsize=9)

    # Región factible sombreada
    ax.contourf(X1, X2, factible.astype(float), levels=[0.5, 1.5],
                colors=[_GREEN], alpha=0.20)

    # Fronteras de restricción
    for G, _ in rest_funcs:
        try:
            ax.contour(X1, X2, G, levels=[0], colors=[_BOUND], linewidths=1.8, alpha=0.9)
        except Exception:
            pass

    # Trayectoria de iteraciones si hay
    if respuesta.iteraciones:
        x1_path = [it.datos[x1n] for it in respuesta.iteraciones if x1n in it.datos]
        x2_path = [it.datos[x2n] for it in respuesta.iteraciones if x2n in it.datos]
        if len(x1_path) > 1:
            ax.plot(x1_path, x2_path, color=_CURVE, linewidth=1.5, alpha=0.7, zorder=3)
            ax.scatter([x1_path[0]], [x2_path[0]], color=_AMBER, s=70, zorder=5,
                       marker='D', label=f"x₀ = ({x1_path[0]:.3g}, {x2_path[0]:.3g})")

    # Óptimo
    opt_color = _AMBER if problema.tipo == TipoOptimizacion.MAX else _GREEN
    ax.scatter([xo1], [xo2], color=opt_color, s=160, zorder=8, marker='*',
               label=f"x* = ({xo1:.4g}, {xo2:.4g}),  f = {respuesta.z_optimo:.4g}")

    ax.set_xlabel(x1n, fontsize=10)
    ax.set_ylabel(x2n, fontsize=10)
    ax.set_title(
        f"{problema.tipo.value}  f({x1n}, {x2n}) — Región Factible y Óptimo",
        color=_TEXT, fontsize=10, pad=8,
    )
    ax.legend(facecolor=_PANEL, edgecolor=_GRID, labelcolor=_TEXT, fontsize=9, framealpha=1)

    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=110, facecolor=_BG)
    plt.close(fig)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
