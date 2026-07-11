"""
Módulo de backend para la resolución paso a paso de problemas de
Programación Lineal mediante el Método Simplex Tabular Estándar.

Restricciones de diseño:
    - Orientación a Objetos pura y Tipado Estático Estricto.
    - Sin diccionarios, sin prints, sin scipy, sin usar hasattr.
    - Todo el álgebra se realiza con fractions.Fraction para exactitud.
    - Las matrices NumPy usan dtype=object para alojar Fraction.

Orden de columnas en cada tableau:
    [X1 ... Xn | S1 ... Sm | RHS]
    donde n = variables de decisión, m = variables de holgura.

La fila Z siempre es la PRIMERA fila del tableau (índice 0).

Autor: Backend Module — MVC Simplex Optimizer
"""

from __future__ import annotations
from fractions import Fraction
import numpy as np
from typing import List, Optional

# Importaciones estrictas de las entidades de dominio orientadas a objetos
from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion, SignoRestriccion
from src.models.entity.programacion_lineal.problema import ProblemaPL
from src.models.entity.programacion_lineal.respuesta import RespuestaTabularPL, IteracionTabular, NumericoTabular


class SolucionadorSimplex:
    """
    Implementa el algoritmo Simplex tabular estándar paso a paso utilizando objetos de dominio.
    """

    # Límite de iteraciones para evitar ciclos infinitos en problemas degenerados
    MAX_ITERACIONES: int = 200

    def __init__(self) -> None:
        """Inicializa las variables estructurales del solucionador."""
        self._n_vars: int = 0               # Cantidad de variables de decisión originales
        self._n_restricciones: int = 0      # Cantidad de restricciones (equivalente a holguras)
        self._es_max: bool = True           # Bandera para determinar si es Maximización
        self._base: List[int] = []          # Índices de columna correspondientes a la base de cada fila
        self._nombres_cols: List[str] = []  # Encabezados de las columnas de datos (sin incluir 'Base')

    def resolver(self, problema: ProblemaPL) -> RespuestaTabularPL:
        """
        Resuelve el problema de programación lineal mediante Simplex Tabular algebraico exacto.

        Parámetros
        ----------
        problema : ProblemaPL
            Entidad inmutable que contiene el modelo matemático formal.

        Retorna
        -------
        RespuestaTabularPL
            Entidad inmutable con el resultado final y el historial de tableaus autodescriptivos.
        """
        # --- 1. Inicialización y extracción segura de atributos de dominio ---
        self._n_vars = problema.total_variables
        self._n_restricciones = problema.total_restricciones
        self._es_max = (problema.tipo == TipoOptimizacion.MAX)

        # --- 2. Validar restricciones del algoritmo Simplex Estándar ---
        for restriccion in problema.restricciones:
            if restriccion.signo != SignoRestriccion.MENOR_IGUAL:
                return RespuestaTabularPL(
                    estado=EstadoProblema.REQUIERE_OTRO_METODO,
                    mensaje=EstadoProblema.REQUIERE_OTRO_METODO.value
                )

        # --- 3. Detectar RHS negativo: la base canónica de holguras no sería factible,
        # pero eso NO implica que el problema en sí sea inviable (ej. -x1 <= -5 equivale
        # a x1 >= 5). Este método tabular estándar no soporta ese caso; se delega a otro.
        for restriccion in problema.restricciones:
            if Fraction(restriccion.rhs) < Fraction(0):
                return RespuestaTabularPL(
                    estado=EstadoProblema.REQUIERE_OTRO_METODO,
                    mensaje=EstadoProblema.REQUIERE_OTRO_METODO.value
                )

        # --- 4. Construcción estructural del Tableau inicial ---
        self._nombres_cols = self._construir_encabezados()
        tableau = self._construir_tableau(problema)

        # --- 5. Ejecución funcional de las iteraciones ---
        return self._iterar(tableau)

    def _construir_encabezados(self) -> List[str]:
        """Genera la lista de nombres de columnas de datos en el orden canónico."""
        cols: List[str] = []
        for i in range(1, self._n_vars + 1):
            cols.append(f"X{i}")
        for j in range(1, self._n_restricciones + 1):
            cols.append(f"S{j}")
        cols.append("RHS")
        return cols

    def _construir_tableau(self, problema: ProblemaPL) -> np.ndarray:
        """Construye la matriz inicial con variables de holgura y coeficientes exactos."""
        total_cols = self._n_vars + self._n_restricciones + 1
        total_filas = self._n_restricciones + 1

        T = np.full((total_filas, total_cols), Fraction(0), dtype=object)

        # --- Fila Z (Índice 0) ---
        signo_z = Fraction(1) if self._es_max else Fraction(-1)
        for j, coef in enumerate(problema.objetivo):
            T[0, j] = Fraction(-coef) * signo_z

        # --- Filas de Restricciones (Índices 1 a m) ---
        for i, restriccion in enumerate(problema.restricciones):
            fila = i + 1
            for j, coef in enumerate(restriccion.coeficientes):
                T[fila, j] = Fraction(coef)
            
            T[fila, self._n_vars + i] = Fraction(1)  # Variable de holgura (Matriz identidad)
            T[fila, total_cols - 1] = Fraction(restriccion.rhs)

        # Las holguras son la base inicial; guardamos sus índices de columna
        self._base = [self._n_vars + i for i in range(self._n_restricciones)]
        return T

    def _iterar(self, tableau: np.ndarray) -> RespuestaTabularPL:
        """Ejecuta el bucle del algoritmo registrando objetos de iteración inmutables."""
        iteraciones: List[IteracionTabular] = []

        for _ in range(self.MAX_ITERACIONES):
            # 1. Condición de optimalidad: coeficientes en la fila Z deben ser >= 0
            col_pivote = self._seleccionar_columna_pivote(tableau)
            if col_pivote is None:
                iteraciones.append(self._crear_snapshot(tableau, None, None, "Solución óptima encontrada"))
                return self._construir_respuesta_exitosa(EstadoProblema.OPTIMO, tableau, iteraciones)

            # 2. Condición de acotamiento: prueba del cociente mínimo
            fila_pivote = self._seleccionar_fila_pivote(tableau, col_pivote)
            if fila_pivote is None:
                iteraciones.append(self._crear_snapshot(tableau, None, col_pivote, "Problema no acotado: no existe cociente mínimo."))
                return RespuestaTabularPL(
                    estado=EstadoProblema.NO_ACOTADO,
                    mensaje=EstadoProblema.NO_ACOTADO.value,
                    iteraciones=iteraciones
                )

            # 3. Registrar estado actual antes de aplicar transformaciones lineales
            var_entra = self._nombres_cols[col_pivote]
            var_sale = self._nombres_cols[self._base[fila_pivote - 1]]
            mensaje_pivote = f"Entra {var_entra}, sale {var_sale}."
            iteraciones.append(self._crear_snapshot(tableau, fila_pivote, col_pivote, mensaje_pivote))

            # 4. Operaciones elementales de fila (Pivoteo)
            tableau = self._pivotear(tableau, fila_pivote, col_pivote)

            # 5. Intercambio formal de variables en la base (fila_pivote - 1 compensa la fila Z)
            self._base[fila_pivote - 1] = col_pivote

        # Límite alcanzado sin convergencia
        iteraciones.append(self._crear_snapshot(tableau, None, None, "Límite de iteraciones alcanzado."))
        return RespuestaTabularPL(
            estado=EstadoProblema.LIMITE_ITERACIONES,
            mensaje=EstadoProblema.LIMITE_ITERACIONES.value,
            iteraciones=iteraciones
        )

    def _seleccionar_columna_pivote(self, T: np.ndarray) -> Optional[int]:
        """Selecciona la columna con el costo reducido más negativo."""
        fila_z = T[0, :-1]
        min_val = Fraction(0)
        col_pivote = None

        for j, val in enumerate(fila_z):
            if val < min_val:
                min_val = val
                col_pivote = j

        return col_pivote

    def _seleccionar_fila_pivote(self, T: np.ndarray, col_pivote: int) -> Optional[int]:
        """Aplica la prueba del cociente mínimo para determinar la variable de salida."""
        min_ratio = None
        fila_pivote = None

        for i in range(1, self._n_restricciones + 1):
            elemento = T[i, col_pivote]
            if elemento > Fraction(0):
                ratio = T[i, -1] / elemento
                if min_ratio is None or ratio < min_ratio:
                    min_ratio = ratio
                    fila_pivote = i

        return fila_pivote

    def _pivotear(self, T: np.ndarray, fila_p: int, col_p: int) -> np.ndarray:
        """Genera una nueva matriz aplicando eliminación de Gauss-Jordan exacta."""
        T = T.copy()
        pivote = T[fila_p, col_p]

        # Normalizar fila pivote
        T[fila_p, :] = [v / pivote for v in T[fila_p, :]]

        # Hacer cero el resto de elementos de la columna pivote
        for i in range(T.shape[0]):
            if i != fila_p:
                factor = T[i, col_p]
                if factor != Fraction(0):
                    T[i, :] = [T[i, k] - factor * T[fila_p, k] for k in range(T.shape[1])]

        return T

    def _crear_snapshot(self, T: np.ndarray, fila_p: Optional[int], col_p: Optional[int], mensaje: str) -> IteracionTabular:
        """
        Construye una instancia inmutable de IteracionTabular anteponiendo la columna 'Base' 
        de forma explícita a la matriz visualizada.
        """
        encabezados_visualizacion = ["Base"] + self._nombres_cols
        
        # Estructurar la columna de variables básicas actual
        variables_base_actuales: List[str] = [self._nombres_cols[self._base[i]] for i in range(self._n_restricciones)]
        columna_base: List[str] = ["Z"] + variables_base_actuales

        n_filas, n_cols_datos = T.shape
        tabla_completa = np.empty((n_filas, n_cols_datos + 1), dtype=object)
        
        for i in range(n_filas):
            tabla_completa[i, 0] = columna_base[i]
            for j in range(n_cols_datos):
                tabla_completa[i, j + 1] = T[i, j]

        return IteracionTabular(
            tabla=tabla_completa,
            encabezados=encabezados_visualizacion,
            variables_base=variables_base_actuales,
            mensaje=mensaje,
            fila_pivote=fila_p,
            col_pivote=col_p,
            fase=None
        )

    def _construir_respuesta_exitosa(self, estado: EstadoProblema, T: np.ndarray, iteraciones: List[IteracionTabular]) -> RespuestaTabularPL:
        """Extrae el vector solución óptimo y el valor de Z para construir la entidad de respuesta."""
        z_raw = T[0, -1]
        z_optimo = z_raw if self._es_max else -z_raw

        variables_decision: List[NumericoTabular] = []
        for j in range(self._n_vars):
            if j in self._base:
                idx_base = self._base.index(j)
                fila_tableau = idx_base + 1
                variables_decision.append(T[fila_tableau, -1])
            else:
                variables_decision.append(Fraction(0))

        return RespuestaTabularPL(
            estado=estado,
            mensaje=estado.value,
            z_optimo=z_optimo,
            variables_decision=variables_decision,
            iteraciones=iteraciones
        )
    