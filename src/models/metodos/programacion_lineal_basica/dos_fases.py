# src/models/metodos/dos_fases.py
"""
Módulo de backend para la resolución paso a paso de problemas de
Programación Lineal mediante el Método de las Dos Fases (Two-Phase Simplex).

Restricciones de diseño:
    - Orientación a Objetos pura y Tipado Estático Estricto.
    - Sin diccionarios, sin prints, sin scipy, sin usar hasattr.
    - Todo el álgebra se realiza con fractions.Fraction para exactitud exacta.
    - Las matrices NumPy usan dtype=object para alojar Fraction.
    - Fila 0 es SIEMPRE la función objetivo (W en Fase 1, Z en Fase 2).

Orden de columnas en Fase 1:
    [X1…Xn | S1…Sk | A1…Ap | RHS]

Orden de columnas en Fase 2 (artificiales eliminadas):
    [X1…Xn | S1…Sk | RHS]

Autor: Backend Module — MVC Two-Phase Simplex Optimizer
"""

from __future__ import annotations
from fractions import Fraction
import numpy as np
from typing import cast, List, Optional, Dict, Any, Tuple

# Importaciones estrictas de las entidades de dominio orientadas a objetos
from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion, SignoRestriccion
from src.models.entity.programacion_lineal.problema import ProblemaPL, Restriccion
from src.models.entity.programacion_lineal.respuesta import RespuestaTabularPL, IteracionTabular, NumericoTabular


class SolucionadorDosFases:
    """
    Implementa el Método de las Dos Fases tabular, paso a paso, utilizando objetos de dominio.
    """

    MAX_ITERACIONES: int = 300

    def __init__(self) -> None:
        """Inicializa las variables estructurales y de reindexación del solucionador."""
        # ── Dimensiones del problema ───────────────────────────────────
        self._n_vars: int = 0
        self._n_restricciones: int = 0
        self._n_holguras: int = 0
        self._n_artificiales: int = 0

        # ── Metadatos del problema ─────────────────────────────────────
        self._es_max: bool = True
        self._objetivo_original: List[Fraction] = []

        # ── Estado del tableau ─────────────────────────────────────────
        self._base: List[int] = []

        # ── Nombres de columnas independientes por fase ────────────────
        self._nombres_f1: List[str] = []
        self._nombres_f2: List[str] = []

        # ── Índices de las artificiales en el tableau de Fase 1 ───────
        self._idx_artificiales_f1: List[int] = []

        # ── Mapa de reindexación Fase 1 → Fase 2 ──────────────────────
        self._mapa_col: Dict[int, Optional[int]] = {}

    def resolver(self, problema: ProblemaPL) -> RespuestaTabularPL:
        """
        Resuelve el problema completo mediante el algoritmo de Dos Fases exacto.

        Parámetros
        ----------
        problema : ProblemaPL
            Entidad inmutable que contiene el modelo matemático formal.

        Retorna
        -------
        RespuestaTabularPL
            Entidad inmutable con el resultado final y las iteraciones autodescriptivas.
        """
        # --- 1. Inicialización y extracción de atributos de dominio ---
        self._n_vars = problema.total_variables
        self._n_restricciones = problema.total_restricciones
        self._es_max = (problema.tipo == TipoOptimizacion.MAX)
        self._objetivo_original = [Fraction(c) for c in problema.objetivo]

        self._base = []
        self._idx_artificiales_f1 = []
        self._mapa_col = {}

        # --- 2. Planificar variables auxiliares ---
        plan = self._planificar_variables(problema.restricciones)

        # --- 3. Construir encabezados y tableau de Fase 1 ---
        self._nombres_f1 = self._construir_encabezados_f1(plan)
        tableau_f1 = self._construir_tableau_f1(problema, plan)

        # --- 4. Algebraizar fila W (Fila de penalización artificial) ---
        tableau_f1 = self._algebraizar_fila_w(tableau_f1)

        # ── FASE 1: Minimización de la suma de artificiales ───────────
        resultado_f1, iteraciones_f1, tableau_f1_final = self._ejecutar_fase(
            tableau_f1, fase=1
        )

        # T[0,-1] = -W_min en esta implementación; inviable cuando W_min > 0 ↔ T[0,-1] < 0
        if resultado_f1 == EstadoProblema.INVIABLE or (tableau_f1_final is not None and tableau_f1_final[0, -1] < Fraction(0)):
            return RespuestaTabularPL(
                estado=EstadoProblema.INVIABLE,
                mensaje=EstadoProblema.INVIABLE.value,
                iteraciones=iteraciones_f1
            )

        if resultado_f1 == EstadoProblema.NO_ACOTADO:
            return RespuestaTabularPL(
                estado=EstadoProblema.NO_ACOTADO,
                mensaje=EstadoProblema.NO_ACOTADO.value,
                iteraciones=iteraciones_f1
            )

        # ── FASE 2: Optimización del modelo lineal original ───────────
        tableau_f2 = self._construir_tableau_f2(tableau_f1_final)
        tableau_f2 = self._algebraizar_fila_z(tableau_f2)

        resultado_f2, iteraciones_f2, tableau_f2_final = self._ejecutar_fase(
            tableau_f2, fase=2
        )

        iteraciones_totales = iteraciones_f1 + iteraciones_f2

        if resultado_f2 == EstadoProblema.NO_ACOTADO:
            return RespuestaTabularPL(
                estado=EstadoProblema.NO_ACOTADO,
                mensaje=EstadoProblema.NO_ACOTADO.value,
                iteraciones=iteraciones_totales
            )

        return self._construir_resultado_final(resultado_f2, tableau_f2_final, iteraciones_totales)

    def _planificar_variables(self, restricciones: List[Restriccion]) -> List[Dict[str, Any]]:
        """Mapea las necesidades de variables de holgura, exceso y artificiales por restricción."""
        col = self._n_vars
        plan: List[Dict[str, Any]] = []
        n_holguras = 0
        n_artificiales = 0

        for r in restricciones:
            entrada: Dict[str, Any] = {
                "signo": r.signo,
                "holgura": None,
                "artificial": None,
            }

            if r.signo == SignoRestriccion.MENOR_IGUAL:
                entrada["holgura"] = col
                col += 1
                n_holguras += 1

            elif r.signo == SignoRestriccion.MAYOR_IGUAL:
                entrada["holgura"] = col        # Exceso (coeficiente -1)
                col += 1
                n_holguras += 1
                entrada["artificial"] = col
                self._idx_artificiales_f1.append(col)
                col += 1
                n_artificiales += 1

            elif r.signo == SignoRestriccion.IGUAL:
                entrada["artificial"] = col
                self._idx_artificiales_f1.append(col)
                col += 1
                n_artificiales += 1

            plan.append(entrada)

        self._n_holguras = n_holguras
        self._n_artificiales = n_artificiales
        return plan

    def _construir_encabezados_f1(self, plan: List[Dict[str, Any]]) -> List[str]:
        """Genera la lista ordenada de variables para las columnas de la Fase 1."""
        cols: List[str] = [f"X{i+1}" for i in range(self._n_vars)]
        mapa: Dict[int, str] = {}
        cs, ca = 1, 1

        for entrada in plan:
            if entrada["holgura"] is not None:
                mapa[entrada["holgura"]] = f"S{cs}"
                cs += 1
            if entrada["artificial"] is not None:
                mapa[entrada["artificial"]] = f"A{ca}"
                ca += 1

        for col_idx in sorted(mapa.keys()):
            cols.append(mapa[col_idx])

        cols.append("RHS")
        return cols

    def _construir_tableau_f1(self, problema: ProblemaPL, plan: List[Dict[str, Any]]) -> np.ndarray:
        """Construye la matriz inicial para minimizar la suma de variables artificiales."""
        m = self._n_restricciones
        total_cols = len(self._nombres_f1)
        total_filas = m + 1

        T = np.full((total_filas, total_cols), Fraction(0), dtype=object)

        # Fila 0 (W): Coeficiente de penalización 1 en las columnas artificiales
        for idx_col in self._idx_artificiales_f1:
            T[0, idx_col] = Fraction(1)

        # Filas 1…m: Restricciones mapeadas linealmente
        for i, (r, entrada) in enumerate(zip(problema.restricciones, plan)):
            fila = i + 1
            for j, coef in enumerate(r.coeficientes):
                T[fila, j] = Fraction(coef)

            if entrada["holgura"] is not None:
                T[fila, entrada["holgura"]] = (
                    Fraction(1) if entrada["signo"] == SignoRestriccion.MENOR_IGUAL else Fraction(-1)
                )

            if entrada["artificial"] is not None:
                T[fila, entrada["artificial"]] = Fraction(1)

            T[fila, -1] = Fraction(r.rhs)

        # Base inicial canónica
        for entrada in plan:
            if entrada["signo"] == SignoRestriccion.MENOR_IGUAL:
                self._base.append(entrada["holgura"])
            else:
                self._base.append(entrada["artificial"])

        return T

    def _algebraizar_fila_w(self, T: np.ndarray) -> np.ndarray:
        """Ajusta la fila W restando las filas artificiales para lograr coeficientes cero en la base."""
        T = T.copy()
        for i, col_base in enumerate(self._base):
            if col_base in self._idx_artificiales_f1:
                fila_restr = i + 1
                factor = T[0, col_base]
                if factor != Fraction(0):
                    T[0, :] = [T[0, k] - factor * T[fila_restr, k] for k in range(T.shape[1])]
        return T

    def _construir_tableau_f2(self, T_f1: np.ndarray) -> np.ndarray:
        """Expulsa las columnas artificiales y recompone las filas con los costos reales originales."""
        n_cols_f1 = T_f1.shape[1]

        nuevos_nombres: List[str] = []
        self._mapa_col = {}
        nuevo_idx = 0
        
        for j in range(n_cols_f1):
            nombre_j = self._nombres_f1[j]
            if j in self._idx_artificiales_f1:
                self._mapa_col[j] = None
            else:
                self._mapa_col[j] = nuevo_idx
                nuevos_nombres.append(nombre_j)
                nuevo_idx += 1

        self._nombres_f2 = nuevos_nombres

        n_cols_f2 = len(self._nombres_f2)
        m = self._n_restricciones
        T_f2 = np.full((m + 1, n_cols_f2), Fraction(0), dtype=object)

        # Traspaso matricial de restricciones optimizadas de Fase 1 hacia Fase 2
        for i in range(1, m + 1):
            for j_f1 in range(n_cols_f1):
                j_f2 = self._mapa_col[j_f1]
                if j_f2 is not None:
                    T_f2[i, j_f2] = T_f1[i, j_f1]

        # Inyección de la Función Objetivo original en la Fila Z (Fila 0)
        signo_z = Fraction(1) if self._es_max else Fraction(-1)
        for j, c in enumerate(self._objetivo_original):
            T_f2[0, j] = Fraction(-c) * signo_z

        # Reindexación estricta de las variables básicas vigentes
        self._base = cast(List[int], [
            self._mapa_col[col_f1] for col_f1 in self._base 
            if self._mapa_col[col_f1] is not None
        ])

        return T_f2

    def _algebraizar_fila_z(self, T: np.ndarray) -> np.ndarray:
        """Ajusta la fila Z eliminando coeficientes en las columnas de variables básicas vigentes."""
        T = T.copy()
        for i, col_base in enumerate(self._base):
            fila_restr = i + 1
            factor = T[0, col_base]
            if factor != Fraction(0):
                T[0, :] = [T[0, k] - factor * T[fila_restr, k] for k in range(T.shape[1])]
        return T

    def _ejecutar_fase(self, tableau: np.ndarray, fase: int) -> Tuple[EstadoProblema, List[IteracionTabular], np.ndarray]:
        """Orquesta las iteraciones Simplex de una fase específica construyendo entidades IteracionTabular."""
        iteraciones: List[IteracionTabular] = []
        nombres = self._nombres_f1 if fase == 1 else self._nombres_f2

        for _ in range(self.MAX_ITERACIONES):

            col_pivote = self._columna_pivote(tableau)
            if col_pivote is None:
                iteraciones.append(self._crear_snapshot(tableau, None, None, f"FASE {fase} — Óptimo alcanzado.", fase, nombres))
                if fase == 1 and tableau[0, -1] < Fraction(0):
                    return EstadoProblema.INVIABLE, iteraciones, tableau
                return EstadoProblema.OPTIMO, iteraciones, tableau

            fila_pivote = self._fila_pivote(tableau, col_pivote)
            if fila_pivote is None:
                iteraciones.append(self._crear_snapshot(tableau, None, col_pivote, f"FASE {fase} — Problema no acotado.", fase, nombres))
                return EstadoProblema.NO_ACOTADO, iteraciones, tableau

            var_entra = nombres[col_pivote]
            var_sale = nombres[self._base[fila_pivote - 1]]
            mensaje_pivote = f"FASE {fase} — Entra {var_entra}, sale {var_sale}."
            iteraciones.append(self._crear_snapshot(tableau, fila_pivote, col_pivote, mensaje_pivote, fase, nombres))

            tableau = self._pivotear(tableau, fila_pivote, col_pivote)
            self._base[fila_pivote - 1] = col_pivote

        iteraciones.append(self._crear_snapshot(tableau, None, None, f"FASE {fase} — Límite de iteraciones alcanzado.", fase, nombres))
        return EstadoProblema.LIMITE_ITERACIONES, iteraciones, tableau

    def _columna_pivote(self, T: np.ndarray) -> Optional[int]:
        """Selecciona la columna con el costo reducido más negativo."""
        fila_obj = T[0, :-1]
        min_val = Fraction(0)
        col_pivote: Optional[int] = None

        for j, val in enumerate(fila_obj):
            if val < min_val:
                min_val = val
                col_pivote = j

        return col_pivote

    def _fila_pivote(self, T: np.ndarray, col_pivote: int) -> Optional[int]:
        """Aplica la prueba del cociente mínimo."""
        min_ratio: Optional[Fraction] = None
        fila_pivote: Optional[int] = None

        for i in range(1, self._n_restricciones + 1):
            elemento = T[i, col_pivote]
            if elemento > Fraction(0):
                ratio = T[i, -1] / elemento
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
                    fila_pivote = i

        return fila_pivote

    def _pivotear(self, T: np.ndarray, fila_p: int, col_p: int) -> np.ndarray:
        """Aplica las transformaciones elementales Gauss-Jordan en la columna pivotante."""
        T = T.copy()
        pivote = T[fila_p, col_p]

        T[fila_p, :] = [v / pivote for v in T[fila_p, :]]

        for i in range(T.shape[0]):
            if i != fila_p:
                factor = T[i, col_p]
                if factor != Fraction(0):
                    T[i, :] = [T[i, k] - factor * T[fila_p, k] for k in range(T.shape[1])]

        return T

    def _crear_snapshot(self, T: np.ndarray, fila_p: Optional[int], col_p: Optional[int], mensaje: str, fase: int, nombres: List[str]) -> IteracionTabular:
        """Construye una instancia inmutable de IteracionTabular auto-encapsulando encabezados y la fase actual."""
        n_filas, n_data_cols = T.shape

        etiqueta_obj = "W" if fase == 1 else "Z"
        n_base = len(self._base)
        variables_base_actuales: List[str] = [nombres[self._base[i]] for i in range(n_base)]
        col_base: List[str] = [etiqueta_obj] + variables_base_actuales
        # Pad por si self._base tiene menos entradas que filas del tableau (caso degenerado)
        while len(col_base) < n_filas:
            col_base.append("?")

        tabla_completa = np.empty((n_filas, n_data_cols + 1), dtype=object)
        for i in range(n_filas):
            tabla_completa[i, 0] = col_base[i]
            for j in range(n_data_cols):
                tabla_completa[i, j + 1] = T[i, j]

        return IteracionTabular(
            tabla=tabla_completa,
            encabezados=["Base"] + nombres,
            variables_base=variables_base_actuales,
            mensaje=mensaje,
            fila_pivote=fila_p,
            col_pivote=col_p,
            fase=fase
        )

    def _construir_resultado_final(self, estado: EstadoProblema, tableau_final: Optional[np.ndarray], iteraciones: List[IteracionTabular]) -> RespuestaTabularPL:
        """Extrae el vector óptimo y compila la RespuestaTabularPL definitiva para el controlador."""
        z_optimo: Optional[Fraction] = None
        variables_decision: List[NumericoTabular] = []

        if estado == EstadoProblema.OPTIMO and tableau_final is not None:
            z_raw = tableau_final[0, -1]
            z_optimo = z_raw if self._es_max else -z_raw

            for j in range(self._n_vars):
                if j in self._base:
                    idx = self._base.index(j)
                    variables_decision.append(tableau_final[idx + 1, -1])
                else:
                    variables_decision.append(Fraction(0))
        else:
            variables_decision = [Fraction(0)] * self._n_vars

        return RespuestaTabularPL(
            estado=estado,
            mensaje=estado.value,
            z_optimo=z_optimo,
            variables_decision=variables_decision,
            iteraciones=iteraciones
        )
    