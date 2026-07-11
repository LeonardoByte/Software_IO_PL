# src/models/metodos/programacion_lineal_entera/enumeracion_implicita.py

from fractions import Fraction
from typing import List, Optional, Tuple, Union

from src.models.entity.programacion_lineal.enums import EstadoProblema, TipoOptimizacion, SignoRestriccion
from src.models.entity.programacion_lineal.problema import Restriccion
from src.models.entity.programacion_lineal_entera.enums import TipoVariable
from src.models.entity.programacion_lineal_entera.problema import ProblemaPLE
from src.models.entity.programacion_lineal_entera.respuesta import (
    RespuestaEnumeracionImplicita,
    PasoEnumeracion,
)


class SolucionadorEnumeracionImplicita:
    """
    Solucionador de Programación Lineal Binaria Pura utilizando el algoritmo
    de Enumeración Implícita (Algoritmo Aditivo de Balas) ampliado para max/min
    y coeficientes negativos mediante sustitución de variables.
    """

    MAX_STEPS: int = 1000

    def resolver(self, problema: ProblemaPLE) -> RespuestaEnumeracionImplicita:
        # 1. Validar que todas las variables del problema sean binarias
        for j, tipo in enumerate(problema.tipos_variables):
            if tipo != TipoVariable.BINARIA:
                return RespuestaEnumeracionImplicita(
                    estado=EstadoProblema.REQUIERE_OTRO_METODO,
                    mensaje="El método de enumeración implícita de Balas sólo soporta variables 100% binarias.",
                    z_optimo=None,
                    variables_decision=None,
                    pasos=[]
                )

        n = problema.total_variables

        # 2. Estandarizar a Minimización con coeficientes de costo >= 0
        # C_j son los coeficientes de la función objetivo para minimizar sum(C_j * X_j)
        C = [Fraction(-c) if problema.tipo == TipoOptimizacion.MAX else Fraction(c) for c in problema.objetivo]
        
        # substituted[j] es True si sustituimos X_j = 1 - Y_j, False si X_j = Y_j
        substituted = [C[j] < 0 for j in range(n)]
        
        # Coeficientes objetivo ajustados para Y: c_prime >= 0
        c_prime = [-C[j] if substituted[j] else C[j] for j in range(n)]

        # 3. Estandarizar restricciones a la forma sum(a_prime_ij * Y_j) >= b_prime_i
        a_balas: List[List[Fraction]] = []
        b_balas: List[Fraction] = []

        for r in problema.restricciones:
            # Reemplazar X_j por 1 - Y_j o Y_j
            # sum(a_ij * X_j) = sum_{not sub} a_ij * Y_j - sum_{sub} a_ij * Y_j + sum_{sub} a_ij
            a_prime = [-Fraction(r.coeficientes[j]) if substituted[j] else Fraction(r.coeficientes[j]) for j in range(n)]
            rhs_shift = sum(Fraction(r.coeficientes[j]) for j in range(n) if substituted[j])
            b_prime = Fraction(r.rhs) - rhs_shift

            # Convertir signo a >=
            if r.signo == SignoRestriccion.MENOR_IGUAL:
                # <= : multiplicar por -1
                a_balas.append([-val for val in a_prime])
                b_balas.append(-b_prime)
            elif r.signo == SignoRestriccion.MAYOR_IGUAL:
                # >= : queda igual
                a_balas.append(a_prime)
                b_balas.append(b_prime)
            elif r.signo == SignoRestriccion.IGUAL:
                # == : se divide en dos desigualdades
                a_balas.append(a_prime)
                b_balas.append(b_prime)
                a_balas.append([-val for val in a_prime])
                b_balas.append(-b_prime)

        # 4. Bucle principal de Enumeración Implícita (DFS)
        # Cada elemento de la pila es comb_Y (List[Optional[int]]) de tamaño n
        stack: List[List[Optional[int]]] = [[None] * n]
        pasos: List[PasoEnumeracion] = []
        
        Z_best_Y: Optional[Fraction] = None
        best_Y: Optional[List[int]] = None

        steps_count = 0

        while stack and steps_count < self.MAX_STEPS:
            steps_count += 1
            comb_Y = stack.pop()

            # Mapear comb_Y a comb_X (combinación de variables originales)
            comb_X = [None] * n
            for j in range(n):
                if comb_Y[j] is not None:
                    comb_X[j] = (1 - comb_Y[j]) if substituted[j] else comb_Y[j]

            # Calcular z_local para el paso
            z_local = sum(Fraction(problema.objetivo[j]) * (comb_X[j] if comb_X[j] is not None else 0) for j in range(n))
            z_local_val = float(z_local)

            # A. Verificar inviabilidad de las restricciones
            is_infeasible = False
            for i in range(len(a_balas)):
                # lhs_max es el valor máximo posible para la restricción i
                # sum_{fixed} a_ij * Y_j + sum_{free, a_ij > 0} a_ij
                lhs_max = Fraction(0)
                for j in range(n):
                    if comb_Y[j] is not None:
                        lhs_max += a_balas[i][j] * comb_Y[j]
                    elif a_balas[i][j] > 0:
                        lhs_max += a_balas[i][j]
                if lhs_max < b_balas[i]:
                    is_infeasible = True
                    break

            if is_infeasible:
                pasos.append(PasoEnumeracion(
                    combinacion=list(comb_X),
                    z_local=z_local_val,
                    factible=False,
                    decision="Poda por inviabilidad"
                ))
                continue

            # B. Verificar si es factible con las variables libres en 0
            is_feasible_zero = True
            for i in range(len(a_balas)):
                lhs_zero = sum(a_balas[i][j] * (comb_Y[j] if comb_Y[j] is not None else 0) for j in range(n))
                if lhs_zero < b_balas[i]:
                    is_feasible_zero = False
                    break

            if is_feasible_zero:
                # Solución completa factible encontrada asignando 0 a las libres
                complete_Y = [val if val is not None else 0 for val in comb_Y]
                complete_X = [(1 - complete_Y[j]) if substituted[j] else complete_Y[j] for j in range(n)]
                
                # Calcular Z real
                z_actual = sum(Fraction(problema.objetivo[j]) * complete_X[j] for j in range(n))
                z_actual_val = float(z_actual)
                
                # Calcular Z en términos de Y (para comparar)
                z_Y = sum(c_prime[j] * complete_Y[j] for j in range(n))

                if Z_best_Y is None or z_Y < Z_best_Y:
                    Z_best_Y = z_Y
                    best_Y = complete_Y
                    pasos.append(PasoEnumeracion(
                        combinacion=list(complete_X),
                        z_local=z_actual_val,
                        factible=True,
                        decision="Se genera mejor cota"
                    ))
                else:
                    pasos.append(PasoEnumeracion(
                        combinacion=list(complete_X),
                        z_local=z_actual_val,
                        factible=True,
                        decision="Podado por cota"
                    ))
                continue

            # C. Verificar poda por cota
            # Costo acumulado mínimo para esta rama: sum_{fixed} c_prime_j * Y_j
            cost_bound = sum(c_prime[j] * comb_Y[j] for j in range(n) if comb_Y[j] is not None)
            if Z_best_Y is not None and cost_bound >= Z_best_Y:
                pasos.append(PasoEnumeracion(
                    combinacion=list(comb_X),
                    z_local=z_local_val,
                    factible=False,
                    decision="Podado por cota"
                ))
                continue

            # D. Ramificar
            # Heurística de Balas: Elegir variable libre k que maximice v_k
            # v_k = sum_{i violated} min(d_i, max(0, a_prime_ik))
            best_k = None
            max_v = Fraction(-1)

            for k in range(n):
                if comb_Y[k] is None:
                    # Calcular v_k
                    v_k = Fraction(0)
                    for i in range(len(a_balas)):
                        lhs_zero = sum(a_balas[i][j] * (comb_Y[j] if comb_Y[j] is not None else 0) for j in range(n))
                        if lhs_zero < b_balas[i]:
                            # Restricción violada
                            d_i = b_balas[i] - lhs_zero
                            help_val = max(Fraction(0), a_balas[i][k])
                            v_k += min(d_i, help_val)
                    
                    if v_k > max_v:
                        max_v = v_k
                        best_k = k
                    elif v_k == max_v and best_k is not None:
                        # Desempate por menor costo o menor índice
                        if c_prime[k] < c_prime[best_k]:
                            best_k = k

            if best_k is None or max_v == 0:
                # Si ninguna variable libre ayuda a reducir el déficit, es inviable
                pasos.append(PasoEnumeracion(
                    combinacion=list(comb_X),
                    z_local=z_local_val,
                    factible=False,
                    decision="Poda por inviabilidad (sin variables de ayuda)"
                ))
                continue

            # Registrar paso de ramificación
            pasos.append(PasoEnumeracion(
                combinacion=list(comb_X),
                z_local=z_local_val,
                factible=False,
                decision=f"Ramificación en Y{best_k + 1}"
            ))

            # Crear y empujar ramas
            # Y_k = 0 e Y_k = 1
            comb_Y_0 = list(comb_Y)
            comb_Y_0[best_k] = 0
            
            comb_Y_1 = list(comb_Y)
            comb_Y_1[best_k] = 1

            # Empujar 0 primero y luego 1, para explorar 1 primero (LIFO)
            stack.append(comb_Y_0)
            stack.append(comb_Y_1)

        # 5. Formular respuesta final
        if best_Y is None:
            # Si se agotó el presupuesto de pasos sin explorar todo el árbol, no se
            # puede afirmar que el problema sea inviable: solo que no se alcanzó a
            # encontrar (ni descartar) ninguna solución factible a tiempo.
            if steps_count >= self.MAX_STEPS:
                return RespuestaEnumeracionImplicita(
                    estado=EstadoProblema.LIMITE_ITERACIONES,
                    mensaje="Se alcanzó el límite de pasos sin encontrar una solución factible.",
                    z_optimo=None,
                    variables_decision=None,
                    pasos=pasos
                )
            return RespuestaEnumeracionImplicita(
                estado=EstadoProblema.INVIABLE,
                mensaje=EstadoProblema.INVIABLE.value,
                z_optimo=None,
                variables_decision=None,
                pasos=pasos
            )

        best_X = [(1 - best_Y[j]) if substituted[j] else best_Y[j] for j in range(n)]
        z_final = sum(Fraction(problema.objetivo[j]) * best_X[j] for j in range(n))

        estado_final = EstadoProblema.OPTIMO
        mensaje_final = EstadoProblema.OPTIMO.value
        if steps_count >= self.MAX_STEPS:
            estado_final = EstadoProblema.LIMITE_ITERACIONES
            mensaje_final = "Se alcanzó el límite de pasos sin completar la exploración."

        return RespuestaEnumeracionImplicita(
            estado=estado_final,
            mensaje=mensaje_final,
            z_optimo=z_final,
            variables_decision=best_X,
            pasos=pasos
        )
