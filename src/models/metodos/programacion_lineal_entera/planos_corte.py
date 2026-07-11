from fractions import Fraction
import math
from typing import List, Optional, Tuple, Dict

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion, SignoRestriccion
from src.models.entity.programacion_lineal.problema import ProblemaPL, Restriccion
from src.models.entity.programacion_lineal.respuesta import IteracionTabular, RespuestaTabularPL
from src.models.entity.programacion_lineal_entera.enums import TipoVariable
from src.models.entity.programacion_lineal_entera.problema import ProblemaPLE
from src.models.entity.programacion_lineal_entera.respuesta import RespuestaPlanoCorte

# Importar resolutores continuos de base
from src.models.metodos.programacion_lineal_basica.simplex import SolucionadorSimplex
from src.models.metodos.programacion_lineal_basica.dos_fases import SolucionadorDosFases


class SolucionadorPlanosCorte:
    """
    Solucionador de Programación Lineal Entera Pura o Mixta utilizando
    el Algoritmo de Planos de Corte (Cortes de Gomory) en aritmética exacta (Fraction).
    """

    MAX_CORTES: int = 50

    def resolver(self, problema: ProblemaPLE) -> RespuestaPlanoCorte:
        # Convertir todo el problema a fracciones para evitar errores de precisión y usar solvers tabulares
        problema_frac = self._convertir_a_fracciones(problema)

        # Problema activo que irá creciendo con las restricciones de corte
        restricciones_actuales = list(problema_frac.restricciones)

        n_vars = problema_frac.total_variables
        tipos_variables = problema_frac.tipos_variables

        # Las variables BINARIA necesitan su cota superior X_j <= 1 explícita: a
        # diferencia de Branch and Bound (que la aplica vía variable shifting), este
        # solver nunca la inyectaría por sí solo, y la detección de "fraccionario"
        # (más abajo) solo dispara sobre valores no enteros — un valor entero fuera
        # de {0,1} (ej. X_j=3) pasaría inadvertido como "óptimo entero" válido.
        for j, tipo in enumerate(tipos_variables):
            if tipo == TipoVariable.BINARIA:
                coefs_cota = [Fraction(0)] * n_vars
                coefs_cota[j] = Fraction(1)
                restricciones_actuales.append(Restriccion(
                    coeficientes=coefs_cota,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=Fraction(1)
                ))

        iteraciones_totales: List[IteracionTabular] = []
        iteraciones_por_corte: List[int] = []

        for corte_idx in range(self.MAX_CORTES):
            # Construir problema actual
            problema_actual = ProblemaPL(
                tipo=problema_frac.tipo,
                objetivo=list(problema_frac.objetivo),
                restricciones=list(restricciones_actuales)
            )

            # Elegir solver tabular adecuado
            solver = self._elegir_solver(problema_actual)

            # Resolver
            res_tabular = solver.resolver(problema_actual)

            # SolucionadorSimplex exige forma canónica (solo '<=' y RHS >= 0). Si el
            # problema tiene RHS negativo en alguna restricción original, Simplex
            # reporta REQUIERE_OTRO_METODO en vez de intentar resolverlo: reintentar
            # con Dos Fases, que sí normaliza RHS negativo internamente.
            if res_tabular.estado == EstadoProblema.REQUIERE_OTRO_METODO and not isinstance(solver, SolucionadorDosFases):
                res_tabular = SolucionadorDosFases().resolver(problema_actual)

            # Guardar iteraciones
            if res_tabular.iteraciones:
                iteraciones_totales.extend(res_tabular.iteraciones)
                iteraciones_por_corte.append(len(res_tabular.iteraciones))

            # Si no es óptimo, el problema no tiene solución entera viable
            if res_tabular.estado != EstadoProblema.OPTIMO:
                return RespuestaPlanoCorte(
                    estado=res_tabular.estado,
                    mensaje=res_tabular.estado.value,
                    z_optimo=None,
                    variables_decision=None,
                    iteraciones=iteraciones_totales,
                    iteraciones_por_corte=iteraciones_por_corte
                )

            z_optimo = res_tabular.z_optimo
            variables_decision = res_tabular.variables_decision
            if variables_decision is None:
                return RespuestaPlanoCorte(
                    estado=EstadoProblema.ERROR_SISTEMA_INTERNO,
                    mensaje="Error en la solución",
                    z_optimo=None,
                    variables_decision=None,
                    iteraciones=iteraciones_totales,
                    iteraciones_por_corte=iteraciones_por_corte
                )

            # Buscar variables enteras/binarias que tengan valor fraccionario
            fractional_vars = []
            for j, val in enumerate(variables_decision):
                if tipos_variables[j] in (TipoVariable.ENTERA, TipoVariable.BINARIA):
                    val_frac = Fraction(val)
                    f_j = val_frac - Fraction(math.floor(val_frac))
                    if f_j != 0:
                        fractional_vars.append((j, f_j, val_frac))

            # Si no hay variables fraccionarias, hemos terminado
            if not fractional_vars:
                return RespuestaPlanoCorte(
                    estado=EstadoProblema.OPTIMO,
                    mensaje=EstadoProblema.OPTIMO.value,
                    z_optimo=z_optimo,
                    variables_decision=variables_decision,
                    iteraciones=iteraciones_totales,
                    iteraciones_por_corte=iteraciones_por_corte
                )

            # Seleccionar la variable fraccionaria con la parte fraccionaria más cercana a 0.5 (heurística estándar)
            fractional_vars.sort(key=lambda x: abs(x[1] - Fraction(1, 2)))
            idx_frac, f_k, val_k = fractional_vars[0]

            # Buscar la fila de la variable básica seleccionada en el último tableau
            final_iter = res_tabular.iteraciones[-1]
            tableau = final_iter.tabla
            headers = final_iter.encabezados

            # Encontrar el índice de la fila en la tabla donde columna 'Base' es la variable
            var_name = f"X{idx_frac + 1}"
            row_idx = None
            for i in range(1, tableau.shape[0]):
                if tableau[i, 0] == var_name:
                    row_idx = i
                    break

            if row_idx is None:
                # Si no se encuentra la fila (anomalía), terminamos indicando error
                return RespuestaPlanoCorte(
                    estado=EstadoProblema.ERROR_SISTEMA_INTERNO,
                    mensaje="Error interno: No se encontró la variable básica en el tableau.",
                    z_optimo=None,
                    variables_decision=None,
                    iteraciones=iteraciones_totales,
                    iteraciones_por_corte=iteraciones_por_corte
                )

            # Generar el corte de Gomory a partir de la fila row_idx
            # Fila: X_k + sum(a_kj * W_j) = b_k
            # Corte: sum( f_kj * W_j ) >= f_k  donde f_kj = a_kj - floor(a_kj)
            # Debemos mapear las holguras S_d en términos de las variables originales X_1..X_n
            slack_map = self._construir_mapa_holguras(problema_actual)

            # Coeficientes del corte en términos de las variables originales
            coefs_corte = [Fraction(0)] * n_vars
            rhs_corte = f_k

            # Recorrer columnas del tableau (excluyendo Base y RHS)
            for col_idx in range(1, len(headers) - 1):
                col_name = headers[col_idx]
                coef_tableau = Fraction(tableau[row_idx, col_idx])
                f_kj = coef_tableau - Fraction(math.floor(coef_tableau))

                if f_kj == 0:
                    continue

                if col_name.startswith("X"):
                    # Variable original
                    var_idx = int(col_name[1:]) - 1
                    coefs_corte[var_idx] += f_kj
                elif col_name.startswith("S"):
                    # Variable de holgura/exceso a sustituir
                    if col_name in slack_map:
                        const_val, expr_coefs = slack_map[col_name]
                        rhs_corte -= f_kj * const_val
                        for r in range(n_vars):
                            coefs_corte[r] += f_kj * expr_coefs[r]



            # Asegurar que el RHS sea no-negativo para cumplir con las hipótesis de los solucionadores continuos
            if rhs_corte < 0:
                coefs_corte = [-val for val in coefs_corte]
                rhs_corte = -rhs_corte
                signo_corte = SignoRestriccion.MENOR_IGUAL
            else:
                signo_corte = SignoRestriccion.MAYOR_IGUAL

            # Agregar el nuevo corte al conjunto de restricciones
            restricciones_actuales.append(Restriccion(
                coeficientes=coefs_corte,
                signo=signo_corte,
                rhs=rhs_corte
            ))

        # Si alcanza el límite de cortes sin converger
        return RespuestaPlanoCorte(
            estado=EstadoProblema.LIMITE_ITERACIONES,
            mensaje="Se alcanzó el límite de cortes de Gomory sin converger a una solución entera.",
            z_optimo=None,
            variables_decision=None,
            iteraciones=iteraciones_totales,
            iteraciones_por_corte=iteraciones_por_corte
        )

    def _convertir_a_fracciones(self, problema: ProblemaPLE) -> ProblemaPLE:
        objetivo_frac = [Fraction(c) for c in problema.objetivo]
        restricciones_frac = []
        for r in problema.restricciones:
            restricciones_frac.append(Restriccion(
                coeficientes=[Fraction(c) for c in r.coeficientes],
                signo=r.signo,
                rhs=Fraction(r.rhs)
            ))
        return ProblemaPLE(
            tipo=problema.tipo,
            objetivo=objetivo_frac,
            restricciones=restricciones_frac,
            tipos_variables=problema.tipos_variables
        )

    def _elegir_solver(self, problema: ProblemaPL):
        # Determinar si hay restricciones con signo >= o ==
        tiene_ge_eq = False
        for r in problema.restricciones:
            if r.signo in (SignoRestriccion.MAYOR_IGUAL, SignoRestriccion.IGUAL):
                tiene_ge_eq = True
                break

        if tiene_ge_eq:
            return SolucionadorDosFases()
        else:
            return SolucionadorSimplex()

    def _construir_mapa_holguras(self, problema: ProblemaPL) -> Dict[str, Tuple[Fraction, List[Fraction]]]:
        """
        Mapea cada variable de holgura/exceso 'S1', 'S2'... del tableau
        a su expresión en términos de las variables originales X1..Xn:
        S_d = const + sum(coef_r * X_r)
        Retorna un diccionario { "S1": (const, [coef_1, ..., coef_n]) }
        """
        slack_map = {}
        ineq_counter = 1
        for r in problema.restricciones:
            if r.signo in (SignoRestriccion.MENOR_IGUAL, SignoRestriccion.MAYOR_IGUAL):
                name = f"S{ineq_counter}"
                ineq_counter += 1
                
                # <= : S_d = b - sum(a_r * X_r)
                # >= : S_d = sum(a_r * X_r) - b
                if r.signo == SignoRestriccion.MENOR_IGUAL:
                    const_val = Fraction(r.rhs)
                    expr_coefs = [-Fraction(c) for c in r.coeficientes]
                else:
                    const_val = -Fraction(r.rhs)
                    expr_coefs = [Fraction(c) for c in r.coeficientes]
                    
                slack_map[name] = (const_val, expr_coefs)
        return slack_map
