from fractions import Fraction
from typing import List, Union, Optional, Dict

from src.models.entity.programacion_lineal_entera.problema import ProblemaPLE, Restriccion, ProblemaModeladoLogico, NodoLogico
from src.models.entity.programacion_lineal_entera.enums import TipoVariable, OperadorLogico, OperadorMGrande, OperadorAsignacionLogica
from src.models.entity.programacion_lineal.enums import SignoRestriccion
from src.models.entity.programacion_lineal.problema import Numerico


class CompiladorLogico:
    """
    Servicio encargado de traducir un árbol de expresiones lógicas (AST)
    a restricciones lineales equivalentes usando penalizaciones de la M Grande.
    """
    
    def __init__(self, M: float = 1_000_000_000.0) -> None:
        self.M = Fraction(M)
        self.artificial_vars: Dict[str, int] = {}

    def compilar(self, problema_logico: ProblemaModeladoLogico) -> ProblemaPLE:
        # Reiniciar el mapa de variables artificiales
        self.artificial_vars = {}
        
        # 1. Copiar las restricciones algebraicas base que el usuario ingresó normalmente
        restricciones_finales = list(problema_logico.restricciones)
        tipos_variables_finales = list(problema_logico.tipos_variables)
        
        # Copia de la función objetivo original
        coeficientes_objetivo = list(problema_logico.objetivo)
        
        # 2. Recorrer y aplanar cada árbol lógico del bosque
        for arbol in problema_logico.arboles_logicos:
            self._procesar_nodo(arbol, restricciones_finales, tipos_variables_finales, coeficientes_objetivo)

        # Alinear todas las restricciones para que tengan coeficientes de la misma longitud que la cantidad final de variables
        final_len = len(tipos_variables_finales)
        padded_restricciones = []
        for r in restricciones_finales:
            if len(r.coeficientes) < final_len:
                padded_coefs = [Fraction(c) for c in r.coeficientes] + [Fraction(0)] * (final_len - len(r.coeficientes))
                padded_restricciones.append(Restriccion(
                    coeficientes=padded_coefs,
                    signo=r.signo,
                    rhs=Fraction(r.rhs)
                ))
            else:
                padded_restricciones.append(r)

        # 3. Retornar el problema listo para los solucionadores numéricos
        return ProblemaPLE(
            tipo=problema_logico.tipo,
            objetivo=coeficientes_objetivo,
            restricciones=padded_restricciones,
            tipos_variables=tipos_variables_finales
        )

    def _procesar_nodo(self, nodo: NodoLogico, restricciones: List[Restriccion], 
                       tipos_vars: List[TipoVariable], objetivo: List[Numerico]) -> None:
        """Método para desarmar el árbol lógico inyectando la M Grande."""
        y = self._compilar_nodo_recursivo(nodo, restricciones, tipos_vars, objetivo)
        # Forzar que la condición del árbol raíz sea verdadera (y == 1)
        # Excepto si es una asignación lógica directa en la raíz o una activación de umbral
        if isinstance(nodo, NodoLogico) and (
            isinstance(nodo.operador, OperadorAsignacionLogica) or 
            nodo.operador == OperadorMGrande.ACTIVACION_UMBRAL
        ):
            return
        coefs = [Fraction(0)] * len(tipos_vars)
        coefs[y] = Fraction(1)
        restricciones.append(Restriccion(
            coeficientes=coefs,
            signo=SignoRestriccion.IGUAL,
            rhs=Fraction(1)
        ))

    def _compilar_nodo_recursivo(self, nodo: Union[Restriccion, NodoLogico, str], restricciones: List[Restriccion], 
                                 tipos_vars: List[TipoVariable], objetivo: List[Numerico]) -> int:
        if isinstance(nodo, str):
            if nodo.startswith("x") and nodo[1:].isdigit():
                return int(nodo[1:]) - 1
            elif nodo.startswith("a_"):
                return self.artificial_vars[nodo]
            else:
                raise ValueError(f"Identificador de variable no válido en el compilador: {nodo}")

        if isinstance(nodo, Restriccion):
            # Intentar detectar si la restricción es simplemente la afirmación de una variable binaria
            nonzero_indices = [idx for idx, coef in enumerate(nodo.coeficientes) if coef != 0]
            if len(nonzero_indices) == 1:
                idx = nonzero_indices[0]
                coef = Fraction(nodo.coeficientes[idx])
                if idx < len(tipos_vars) and tipos_vars[idx] == TipoVariable.BINARIA:
                    if coef == 1:
                        if nodo.signo in (SignoRestriccion.MAYOR_IGUAL, SignoRestriccion.IGUAL) and Fraction(nodo.rhs) == 1:
                            return idx
                        if nodo.signo in (SignoRestriccion.MENOR_IGUAL, SignoRestriccion.IGUAL) and Fraction(nodo.rhs) == 0:
                            # NOT X_j: y + X_j = 1
                            y = len(tipos_vars)
                            tipos_vars.append(TipoVariable.BINARIA)
                            objetivo.append(Fraction(0))
                            self.artificial_vars[f"a_{len(self.artificial_vars) + 1}"] = y
                            coefs_eq = [Fraction(0)] * len(tipos_vars)
                            coefs_eq[y] = Fraction(1)
                            coefs_eq[idx] = Fraction(1)
                            restricciones.append(Restriccion(
                                coeficientes=coefs_eq,
                                signo=SignoRestriccion.IGUAL,
                                rhs=Fraction(1)
                            ))
                            return y

            # Crear variable binaria de control para esta restricción
            y = len(tipos_vars)
            tipos_vars.append(TipoVariable.BINARIA)
            objetivo.append(Fraction(0))
            self.artificial_vars[f"a_{len(self.artificial_vars) + 1}"] = y
            
            coefs = [Fraction(c) for c in nodo.coeficientes]
            # Rellenar con ceros temporales
            coefs += [Fraction(0)] * (len(tipos_vars) - len(coefs))
            
            if nodo.signo == SignoRestriccion.MENOR_IGUAL:
                # a^T X <= b + M(1 - y) => a^T X + M * y <= b + M
                coefs[y] = self.M
                restricciones.append(Restriccion(
                    coeficientes=coefs,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=Fraction(nodo.rhs) + self.M
                ))
            elif nodo.signo == SignoRestriccion.MAYOR_IGUAL:
                # a^T X >= b - M(1 - y) => a^T X - M * y >= b - M
                # Multiplicamos por -1 para asegurar RHS positivo: -a^T X + M * y <= M - b
                coefs_neg = [-c for c in coefs]
                coefs_neg[y] = self.M
                restricciones.append(Restriccion(
                    coeficientes=coefs_neg,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=self.M - Fraction(nodo.rhs)
                ))
            elif nodo.signo == SignoRestriccion.IGUAL:
                # Se desdobla en <= y >= para modelar la igualdad condicional
                coefs_le = list(coefs)
                coefs_le[y] = self.M
                restricciones.append(Restriccion(
                    coeficientes=coefs_le,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=Fraction(nodo.rhs) + self.M
                ))
                coefs_ge = [-c for c in coefs]
                coefs_ge[y] = self.M
                restricciones.append(Restriccion(
                    coeficientes=coefs_ge,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=self.M - Fraction(nodo.rhs)
                ))
            return y
        
        elif isinstance(nodo, NodoLogico):
            # 2. Caso especial: ACTIVACION_UMBRAL (Costo fijo o activación)
            if nodo.operador == OperadorMGrande.ACTIVACION_UMBRAL:
                # El último hijo es la variable binaria trigger
                trigger_var = nodo.hijos[-1]
                y = self._compilar_nodo_recursivo(trigger_var, restricciones, tipos_vars, objetivo)
                
                # Los demás hijos son los restringidos
                for hijo in nodo.hijos[:-1]:
                    if isinstance(hijo, Restriccion):
                        for idx, coef in enumerate(hijo.coeficientes):
                            if coef != 0:
                                coefs = [Fraction(0)] * len(tipos_vars)
                                coefs[idx] = Fraction(1)
                                coefs[y] = -self.M
                                restricciones.append(Restriccion(
                                    coeficientes=coefs,
                                    signo=SignoRestriccion.MENOR_IGUAL,
                                    rhs=Fraction(0)
                                ))
                    elif isinstance(hijo, (NodoLogico, str)):
                        w = self._compilar_nodo_recursivo(hijo, restricciones, tipos_vars, objetivo)
                        coefs = [Fraction(0)] * len(tipos_vars)
                        coefs[w] = Fraction(1)
                        coefs[y] = -self.M
                        restricciones.append(Restriccion(
                            coeficientes=coefs,
                            signo=SignoRestriccion.MENOR_IGUAL,
                            rhs=Fraction(0)
                        ))
                return y

            # 1. Determinar el índice de la variable de control 'y'
            # y es asignada si variable_control_asociada es de tipo 'xN' (Caso Suelto)
            # o si ya fue creada como 'a_i'. Si es None, creamos variable artificial intermedia.
            y: int
            if nodo.operador == OperadorMGrande.SELECCION_K_DE_N:
                # variable_control_asociada contiene K (un número), no un nombre de variable
                y = len(tipos_vars)
                tipos_vars.append(TipoVariable.BINARIA)
                objetivo.append(Fraction(0))
                art_name = f"a_{len(self.artificial_vars) + 1}"
                self.artificial_vars[art_name] = y
            elif nodo.variable_control_asociada is not None:
                name = nodo.variable_control_asociada
                if name.startswith("x"):
                    y = int(name[1:]) - 1
                elif name.startswith("a_"):
                    if name not in self.artificial_vars:
                        # Si no está en el mapa, la creamos
                        y_new = len(tipos_vars)
                        tipos_vars.append(TipoVariable.BINARIA)
                        objetivo.append(Fraction(0))
                        self.artificial_vars[name] = y_new
                    y = self.artificial_vars[name]
                else:
                    raise ValueError(f"Nombre de variable de control desconocido: {name}")
            else:
                # Generamos una nueva variable artificial y guardamos su nombre como a_i
                y = len(tipos_vars)
                tipos_vars.append(TipoVariable.BINARIA)
                objetivo.append(Fraction(0))
                art_name = f"a_{len(self.artificial_vars) + 1}"
                self.artificial_vars[art_name] = y

            # Procesar hijos recursivamente para obtener sus índices de variables de control
            child_vars = [
                self._compilar_nodo_recursivo(hijo, restricciones, tipos_vars, objetivo)
                for hijo in nodo.hijos
            ]
            
            op = nodo.operador
            
            if op == OperadorLogico.NEGACION:
                # Incompatibilidad binaria: w1 + w2 <= 1 (con condicional y => w1 + w2 + M * y <= 1 + M)
                coefs = [Fraction(0)] * len(tipos_vars)
                coefs[child_vars[0]] = Fraction(1)
                coefs[child_vars[1]] = Fraction(1)
                coefs[y] = self.M
                restricciones.append(Restriccion(
                    coeficientes=coefs,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=Fraction(1) + self.M
                ))
                
            elif op in (OperadorLogico.CONJUNCION, OperadorMGrande.CONJUNCION_RESTRICCIONES):
                # y <= w_r => y - w_r <= 0
                for w in child_vars:
                    coefs = [Fraction(0)] * len(tipos_vars)
                    coefs[y] = Fraction(1)
                    coefs[w] = Fraction(-1)
                    restricciones.append(Restriccion(
                        coeficientes=coefs,
                        signo=SignoRestriccion.MENOR_IGUAL,
                        rhs=Fraction(0)
                    ))
                # y >= sum(w_r) - (k - 1) => y - sum(w_r) >= 1 - k
                # Si k > 1, el RHS es negativo. Multiplicamos por -1 para asegurar RHS positivo: -y + sum(w_r) <= k - 1
                coefs = [Fraction(0)] * len(tipos_vars)
                coefs[y] = Fraction(-1)
                for w in child_vars:
                    coefs[w] = Fraction(1)
                restricciones.append(Restriccion(
                    coeficientes=coefs,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=Fraction(len(child_vars) - 1)
                ))
                
            elif op in (OperadorLogico.DISYUNCION, OperadorMGrande.DISYUNCION_RESTRICCIONES):
                # y >= w_r => y - w_r >= 0
                for w in child_vars:
                    coefs = [Fraction(0)] * len(tipos_vars)
                    coefs[y] = Fraction(1)
                    coefs[w] = Fraction(-1)
                    restricciones.append(Restriccion(
                        coeficientes=coefs,
                        signo=SignoRestriccion.MAYOR_IGUAL,
                        rhs=Fraction(0)
                    ))
                # y <= sum(w_r) => y - sum(w_r) <= 0
                coefs = [Fraction(0)] * len(tipos_vars)
                coefs[y] = Fraction(1)
                for w in child_vars:
                    coefs[w] = Fraction(-1)
                restricciones.append(Restriccion(
                    coeficientes=coefs,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=Fraction(0)
                ))
                
            elif op in (OperadorLogico.EXCLUSION_MUTUA, OperadorMGrande.VALORES_DISJUNTOS):
                # sum(w_r) = y
                coefs = [Fraction(0)] * len(tipos_vars)
                coefs[y] = Fraction(-1)
                for w in child_vars:
                    coefs[w] = Fraction(1)
                restricciones.append(Restriccion(
                    coeficientes=coefs,
                    signo=SignoRestriccion.IGUAL,
                    rhs=Fraction(0)
                ))
                
            elif op in (OperadorLogico.IMPLICACION, OperadorMGrande.CONDICIONAL_COMPUESTO):
                # child_vars[0] => child_vars[1]
                # w1 - w2 + y <= 1
                coefs = [Fraction(0)] * len(tipos_vars)
                coefs[child_vars[0]] = Fraction(1)
                coefs[child_vars[1]] = Fraction(-1)
                coefs[y] = Fraction(1)
                restricciones.append(Restriccion(
                    coeficientes=coefs,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=Fraction(1)
                ))
                
            elif op == OperadorLogico.EQUIVALENCIA:
                # w1 <=> w2
                # w1 - w2 + y <= 1
                coefs1 = [Fraction(0)] * len(tipos_vars)
                coefs1[child_vars[0]] = Fraction(1)
                coefs1[child_vars[1]] = Fraction(-1)
                coefs1[y] = Fraction(1)
                restricciones.append(Restriccion(
                    coeficientes=coefs1,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=Fraction(1)
                ))
                # w2 - w1 + y <= 1
                coefs2 = [Fraction(0)] * len(tipos_vars)
                coefs2[child_vars[0]] = Fraction(-1)
                coefs2[child_vars[1]] = Fraction(1)
                coefs2[y] = Fraction(1)
                restricciones.append(Restriccion(
                    coeficientes=coefs2,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=Fraction(1)
                ))
                
            elif op == OperadorMGrande.SELECCION_K_DE_N:
                K = int(nodo.variable_control_asociada) if nodo.variable_control_asociada is not None else 1
                # sum(w_r) + M * y <= K + M
                coefs_le = [Fraction(0)] * len(tipos_vars)
                coefs_le[y] = self.M
                for w in child_vars:
                    coefs_le[w] = Fraction(1)
                restricciones.append(Restriccion(
                    coeficientes=coefs_le,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=Fraction(K) + self.M
                ))
                # sum(w_r) - M * y >= K - M
                # Multiplicamos por -1 para asegurar RHS positivo: -sum(w_r) + M * y <= M - K
                coefs_ge = [Fraction(0)] * len(tipos_vars)
                coefs_ge[y] = self.M
                for w in child_vars:
                    coefs_ge[w] = Fraction(-1)
                restricciones.append(Restriccion(
                    coeficientes=coefs_ge,
                    signo=SignoRestriccion.MENOR_IGUAL,
                    rhs=self.M - Fraction(K)
                ))

            # 3. Operadores de Asignación Lógica Booleana (Reificación)
            elif op == OperadorAsignacionLogica.AND_EVAL:
                # y = AND(x1, x2)
                # 1. y <= x1 => y - x1 <= 0
                coefs1 = [Fraction(0)] * len(tipos_vars)
                coefs1[y] = Fraction(1)
                coefs1[child_vars[0]] = Fraction(-1)
                restricciones.append(Restriccion(coefs1, SignoRestriccion.MENOR_IGUAL, Fraction(0)))
                # 2. y <= x2 => y - x2 <= 0
                coefs2 = [Fraction(0)] * len(tipos_vars)
                coefs2[y] = Fraction(1)
                coefs2[child_vars[1]] = Fraction(-1)
                restricciones.append(Restriccion(coefs2, SignoRestriccion.MENOR_IGUAL, Fraction(0)))
                # 3. x1 + x2 - y <= 1
                coefs3 = [Fraction(0)] * len(tipos_vars)
                coefs3[child_vars[0]] = Fraction(1)
                coefs3[child_vars[1]] = Fraction(1)
                coefs3[y] = Fraction(-1)
                restricciones.append(Restriccion(coefs3, SignoRestriccion.MENOR_IGUAL, Fraction(1)))

            elif op == OperadorAsignacionLogica.OR_EVAL:
                # y = OR(x1, x2)
                # 1. y >= x1 => x1 - y <= 0
                coefs1 = [Fraction(0)] * len(tipos_vars)
                coefs1[child_vars[0]] = Fraction(1)
                coefs1[y] = Fraction(-1)
                restricciones.append(Restriccion(coefs1, SignoRestriccion.MENOR_IGUAL, Fraction(0)))
                # 2. y >= x2 => x2 - y <= 0
                coefs2 = [Fraction(0)] * len(tipos_vars)
                coefs2[child_vars[1]] = Fraction(1)
                coefs2[y] = Fraction(-1)
                restricciones.append(Restriccion(coefs2, SignoRestriccion.MENOR_IGUAL, Fraction(0)))
                # 3. x1 + x2 - y >= 0 => -x1 - x2 + y <= 0
                coefs3 = [Fraction(0)] * len(tipos_vars)
                coefs3[child_vars[0]] = Fraction(-1)
                coefs3[child_vars[1]] = Fraction(-1)
                coefs3[y] = Fraction(1)
                restricciones.append(Restriccion(coefs3, SignoRestriccion.MENOR_IGUAL, Fraction(0)))

            elif op == OperadorAsignacionLogica.XOR_EVAL:
                # y = XOR(x1, x2)
                # 1. y <= x1 + x2 => y - x1 - x2 <= 0
                coefs1 = [Fraction(0)] * len(tipos_vars)
                coefs1[y] = Fraction(1)
                coefs1[child_vars[0]] = Fraction(-1)
                coefs1[child_vars[1]] = Fraction(-1)
                restricciones.append(Restriccion(coefs1, SignoRestriccion.MENOR_IGUAL, Fraction(0)))
                # 2. y >= x1 - x2 => x1 - x2 - y <= 0
                coefs2 = [Fraction(0)] * len(tipos_vars)
                coefs2[child_vars[0]] = Fraction(1)
                coefs2[child_vars[1]] = Fraction(-1)
                coefs2[y] = Fraction(-1)
                restricciones.append(Restriccion(coefs2, SignoRestriccion.MENOR_IGUAL, Fraction(0)))
                # 3. y >= x2 - x1 => -x1 + x2 - y <= 0
                coefs3 = [Fraction(0)] * len(tipos_vars)
                coefs3[child_vars[0]] = Fraction(-1)
                coefs3[child_vars[1]] = Fraction(1)
                coefs3[y] = Fraction(-1)
                restricciones.append(Restriccion(coefs3, SignoRestriccion.MENOR_IGUAL, Fraction(0)))
                # 4. y <= 2 - x1 - x2 => x1 + x2 + y <= 2
                coefs4 = [Fraction(0)] * len(tipos_vars)
                coefs4[child_vars[0]] = Fraction(1)
                coefs4[child_vars[1]] = Fraction(1)
                coefs4[y] = Fraction(1)
                restricciones.append(Restriccion(coefs4, SignoRestriccion.MENOR_IGUAL, Fraction(2)))
                
            return y
        
        else:
            raise TypeError("Tipo de nodo lógico no soportado.")