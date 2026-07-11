# src/utils/programacion_lineal_entera/parser_sintactico.py

from fractions import Fraction
import re
from typing import List, Union, Optional

from src.models.entity.programacion_lineal.enums import SignoRestriccion
from src.models.entity.programacion_lineal.problema import Restriccion
from src.models.entity.programacion_lineal_entera.enums import (
    TipoVariable,
    OperadorLogico,
    OperadorMGrande,
    OperadorAsignacionLogica,
)
from src.models.entity.programacion_lineal_entera.problema import NodoLogico


def is_csv_format(text: str) -> bool:
    """Detecta si el formato de entrada de las restricciones es CSV."""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Si hay una coma fuera de paréntesis/corchetes, asumimos CSV
        paren_count = 0
        bracket_count = 0
        for char in line:
            if char == '(':
                paren_count += 1
            elif char == ')':
                paren_count -= 1
            elif char == '[':
                bracket_count += 1
            elif char == ']':
                bracket_count -= 1
            elif char == ',' and paren_count == 0 and bracket_count == 0:
                return True
    return False


def tokenize_csv(text: str) -> List[str]:
    """Tokeniza una línea CSV dividiendo por comas fuera de paréntesis/corchetes."""
    tokens = []
    current = []
    paren_count = 0
    bracket_count = 0
    for char in text:
        if char == '(':
            paren_count += 1
            current.append(char)
        elif char == ')':
            paren_count -= 1
            current.append(char)
        elif char == '[':
            bracket_count += 1
            current.append(char)
        elif char == ']':
            bracket_count -= 1
            current.append(char)
        elif char == ',' and paren_count == 0 and bracket_count == 0:
            tokens.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if current:
        tokens.append("".join(current).strip())
    return [t for t in tokens if t]


def tokenize_algebraic(text: str) -> List[str]:
    """Tokeniza una línea algebraica dividiendo por espacios fuera de paréntesis/corchetes."""
    tokens = []
    current = []
    paren_count = 0
    bracket_count = 0
    for char in text:
        if char == '(':
            paren_count += 1
            current.append(char)
        elif char == ')':
            paren_count -= 1
            current.append(char)
        elif char == '[':
            bracket_count += 1
            current.append(char)
        elif char == ']':
            bracket_count -= 1
            current.append(char)
        elif char.isspace() and paren_count == 0 and bracket_count == 0:
            if current:
                tokens.append("".join(current).strip())
                current = []
        else:
            current.append(char)
    if current:
        tokens.append("".join(current).strip())
    return [t for t in tokens if t]


class ParserSintactico:
    """
    Parser sintáctico para construir el Árbol de Sintaxis Abstracta (AST) de NodoLogico
    a partir de expresiones algebraicas o en formato CSV.
    """

    def parse_restricciones(
        self, texto: str, total_variables: int, tipos_variables: List[TipoVariable]
    ) -> List[NodoLogico]:
        arboles = []
        is_csv = is_csv_format(texto)

        for numero_linea, line_original in enumerate(texto.splitlines(), start=1):
            line = line_original.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue

            try:
                if is_csv:
                    tokens = tokenize_csv(line)
                else:
                    tokens = tokenize_algebraic(line)

                node = self._parse_tokens(tokens, total_variables, tipos_variables, is_csv)

                # Estandarizar el nodo de retorno a NodoLogico
                if isinstance(node, Restriccion):
                    node = NodoLogico(OperadorMGrande.CONJUNCION_RESTRICCIONES, hijos=[node])
                elif isinstance(node, str):
                    # Regla Implícita: si aparece sola una variable BINARIA, asumimos var = 1
                    idx = int(node[1:]) - 1
                    if idx < len(tipos_variables) and tipos_variables[idx] == TipoVariable.BINARIA:
                        coefs = [Fraction(0)] * total_variables
                        coefs[idx] = Fraction(1)
                        restr = Restriccion(coefs, SignoRestriccion.IGUAL, Fraction(1))
                        node = NodoLogico(OperadorMGrande.CONJUNCION_RESTRICCIONES, hijos=[restr])
                    else:
                        raise ValueError(
                            f"La variable continua/entera '{node}' no se puede declarar sola."
                        )
            except Exception as error_linea:
                # Re-lanzar con contexto de línea y contenido exacto: sin esto, errores como
                # IndexError/KeyError internos llegan al usuario sin indicar qué línea falló.
                raise ValueError(
                    f"Error de sintaxis en la línea {numero_linea} (\"{line}\"): {error_linea}"
                ) from error_linea

            arboles.append(node)

        return arboles

    def _parse_tokens(
        self, tokens: List[str], total_variables: int, tipos_variables: List[TipoVariable], is_csv: bool
    ) -> Union[Restriccion, NodoLogico, str]:
        if not tokens:
            raise ValueError("Expresión vacía encontrada en el parser.")

        # Limpiar paréntesis exteriores innecesarios si todo el bloque está envuelto
        if len(tokens) == 1:
            tok = tokens[0]
            if tok.startswith("(") and tok.endswith(")"):
                # Verificar si es una inecuación CSV de tipo (c1, c2, signo, rhs)
                if is_csv and "," in tok and any(s in tok for s in ("<=", ">=", "==", "=")):
                    return self._parse_csv_constraint(tok, total_variables)
                else:
                    # Es un paréntesis lógico normal, quitarlo y volver a tokenizar
                    sub_text = tok[1:-1].strip()
                    sub_tokens = tokenize_csv(sub_text) if is_csv else tokenize_algebraic(sub_text)
                    return self._parse_tokens(sub_tokens, total_variables, tipos_variables, is_csv)
            
            # Si es una variable
            if tok.startswith("x") and tok[1:].isdigit():
                return tok
            if tok.isdigit():
                # Si es CSV, se ingresan índices directos (1-indexed)
                return f"x{tok}"

            # Si es un conjunto de valores en corchetes, o inecuación CSV directa
            if tok.startswith("[") and tok.endswith("]"):
                return tok

            # En caso contrario, es una inecuación algebraica simple
            return self._parse_algebraic_constraint(tok, total_variables)

        # 1. CONDICIONAL_COMPUESTO (SI ... ENTONCES ...)
        if "SI" in tokens and "ENTONCES" in tokens:
            idx_si = tokens.index("SI")
            idx_entonces = tokens.index("ENTONCES")
            cond_tokens = tokens[idx_si + 1 : idx_entonces]
            conseq_tokens = tokens[idx_entonces + 1 :]
            cond_node = self._parse_tokens(cond_tokens, total_variables, tipos_variables, is_csv)
            conseq_node = self._parse_tokens(conseq_tokens, total_variables, tipos_variables, is_csv)
            return NodoLogico(OperadorMGrande.CONDICIONAL_COMPUESTO, hijos=[cond_node, conseq_node])

        # 2. SELECCION_K_DE_N (CUMPLIR K DE [ ... ])
        if "CUMPLIR" in tokens and "DE" in tokens:
            idx_cumplir = tokens.index("CUMPLIR")
            idx_de = tokens.index("DE")
            K = tokens[idx_cumplir + 1].strip()
            arr_token = tokens[idx_de + 1].strip()
            if arr_token.startswith("[") and arr_token.endswith("]"):
                arr_content = arr_token[1:-1].strip()
                # Separar los elementos por comas
                child_exprs = tokenize_csv(arr_content)
                hijos = [
                    self._parse_tokens([expr], total_variables, tipos_variables, is_csv)
                    for expr in child_exprs
                ]
                return NodoLogico(OperadorMGrande.SELECCION_K_DE_N, hijos=hijos, variable_control_asociada=K)

        # 3. Asignación lógica reificada (x3 = expression)
        if "=" in tokens:
            idx_eq = tokens.index("=")
            left_tokens = tokens[:idx_eq]
            right_tokens = tokens[idx_eq + 1 :]
            left_var = self._parse_tokens(left_tokens, total_variables, tipos_variables, is_csv)
            if not isinstance(left_var, str):
                raise ValueError("La parte izquierda de una asignación debe ser una variable única.")
            right_node = self._parse_tokens(right_tokens, total_variables, tipos_variables, is_csv)
            if not isinstance(right_node, NodoLogico):
                raise ValueError("La parte derecha de una asignación debe ser una operación evaluativa.")
            
            # Crear copia del NodoLogico con variable_control_asociada asignada
            return NodoLogico(
                operador=right_node.operador,
                hijos=right_node.hijos,
                variable_control_asociada=left_var,
            )

        # 4. NEGACION (Incompatibilidad: x1 NOT x2)
        if "NOT" in tokens:
            idx_not = tokens.index("NOT")
            left = self._parse_tokens(tokens[:idx_not], total_variables, tipos_variables, is_csv)
            right = self._parse_tokens(tokens[idx_not + 1 :], total_variables, tipos_variables, is_csv)
            return NodoLogico(OperadorLogico.NEGACION, hijos=[left, right])

        # 5. Y (CONJUNCION / CONJUNCION_RESTRICCIONES)
        if "Y" in tokens:
            idx_y = tokens.index("Y")
            left = self._parse_tokens(tokens[:idx_y], total_variables, tipos_variables, is_csv)
            right = self._parse_tokens(tokens[idx_y + 1 :], total_variables, tipos_variables, is_csv)
            
            # Si ambos son variables binarias aisladas, usar OperadorLogico
            if isinstance(left, str) and isinstance(right, str):
                return NodoLogico(OperadorLogico.CONJUNCION, hijos=[left, right])
            else:
                return NodoLogico(OperadorMGrande.CONJUNCION_RESTRICCIONES, hijos=[left, right])

        # 6. O (DISYUNCION / DISYUNCION_RESTRICCIONES / EXCLUSION_MUTUA)
        # Manejar EXCLUSION_MUTUA cuando la expresión empieza con O: "O x1 O x2" o "O, 1, O, 2"
        if tokens[0] == "O" and len(tokens) > 2 and "O" in tokens[1:]:
            idx_o2 = tokens.index("O", 1)
            var1 = self._parse_tokens(tokens[1:idx_o2], total_variables, tipos_variables, is_csv)
            var2 = self._parse_tokens(tokens[idx_o2 + 1 :], total_variables, tipos_variables, is_csv)
            return NodoLogico(OperadorLogico.EXCLUSION_MUTUA, hijos=[var1, var2])

        if "O" in tokens:
            idx_o = tokens.index("O")
            left = self._parse_tokens(tokens[:idx_o], total_variables, tipos_variables, is_csv)
            right = self._parse_tokens(tokens[idx_o + 1 :], total_variables, tipos_variables, is_csv)
            if isinstance(left, str) and isinstance(right, str):
                return NodoLogico(OperadorLogico.DISYUNCION, hijos=[left, right])
            else:
                return NodoLogico(OperadorMGrande.DISYUNCION_RESTRICCIONES, hijos=[left, right])

        # 7. IMPLICACION (x1 -> x2)
        if "->" in tokens:
            idx_arr = tokens.index("->")
            left = self._parse_tokens(tokens[:idx_arr], total_variables, tipos_variables, is_csv)
            right = self._parse_tokens(tokens[idx_arr + 1 :], total_variables, tipos_variables, is_csv)
            return NodoLogico(OperadorLogico.IMPLICACION, hijos=[left, right])

        # 8. EQUIVALENCIA (x1 == x2) vs. restricción algebraica/CSV de igualdad (x1+x2==10 / 2,1,==,10)
        # '==' es ambiguo: es tanto el operador de co-requisito lógico entre DOS
        # VARIABLES SUELTAS como el signo de igualdad matemática estándar. Solo se
        # interpreta como EQUIVALENCIA cuando ambos lados son exactamente una
        # referencia de variable suelta (sin coeficientes, sin '+'/'-', sin constantes);
        # cualquier otra cosa (ej. una expresión con varios términos o un RHS numérico)
        # es una restricción algebraica/CSV de igualdad ordinaria.
        if "==" in tokens:
            idx_eq2 = tokens.index("==")
            izq_tokens = tokens[:idx_eq2]
            der_tokens = tokens[idx_eq2 + 1:]

            es_equivalencia_logica = (
                len(izq_tokens) == 1 and len(der_tokens) == 1
                and self._es_token_variable_suelta(izq_tokens[0], is_csv)
                and self._es_token_variable_suelta(der_tokens[0], is_csv)
                # Con una sola variable declarada, un índice CSV suelto y un
                # coeficiente CSV de una restricción de un solo término son
                # indistinguibles por forma: se prioriza la lectura algebraica.
                and not (is_csv and total_variables == 1)
            )

            if es_equivalencia_logica:
                left = self._parse_tokens(izq_tokens, total_variables, tipos_variables, is_csv)
                right = self._parse_tokens(der_tokens, total_variables, tipos_variables, is_csv)
                return NodoLogico(OperadorLogico.EQUIVALENCIA, hijos=[left, right])

            if is_csv:
                return self._construir_restriccion_csv(tokens, total_variables)
            return self._parse_algebraic_constraint(" ".join(tokens), total_variables)

        # 9. ACTIVACION_UMBRAL (x1 ACTIVADO_POR x2)
        if "ACTIVADO_POR" in tokens:
            idx_act = tokens.index("ACTIVADO_POR")
            left = self._parse_tokens(tokens[:idx_act], total_variables, tipos_variables, is_csv)
            right = self._parse_tokens(tokens[idx_act + 1 :], total_variables, tipos_variables, is_csv)
            return NodoLogico(OperadorMGrande.ACTIVACION_UMBRAL, hijos=[left, right])

        # 10. VALORES_DISJUNTOS (x1 EN [v1, v2])
        if "EN" in tokens:
            idx_en = tokens.index("EN")
            var = self._parse_tokens(tokens[:idx_en], total_variables, tipos_variables, is_csv)
            if not isinstance(var, str):
                raise ValueError("La parte izquierda del operador EN debe ser una variable única.")
            
            arr_token = tokens[idx_en + 1].strip()
            if arr_token.startswith("[") and arr_token.endswith("]"):
                arr_content = arr_token[1:-1].strip()
                val_tokens = [Fraction(v.strip()) for v in arr_content.split(",") if v.strip()]
                var_idx = int(var[1:]) - 1

                # Generar una lista de igualdades: var == valor_i
                hijos = []
                for val in val_tokens:
                    coefs = [Fraction(0)] * total_variables
                    coefs[var_idx] = Fraction(1)
                    hijos.append(Restriccion(coefs, SignoRestriccion.IGUAL, val))

                return NodoLogico(OperadorMGrande.VALORES_DISJUNTOS, hijos=hijos)

        # 11. Operadores de Asignación/Evaluación Booleana (AND_EVAL, OR_EVAL, XOR_EVAL)
        if "AND_EVAL" in tokens:
            idx_and = tokens.index("AND_EVAL")
            left = self._parse_tokens(tokens[:idx_and], total_variables, tipos_variables, is_csv)
            right = self._parse_tokens(tokens[idx_and + 1 :], total_variables, tipos_variables, is_csv)
            return NodoLogico(OperadorAsignacionLogica.AND_EVAL, hijos=[left, right])

        if "OR_EVAL" in tokens:
            idx_or = tokens.index("OR_EVAL")
            left = self._parse_tokens(tokens[:idx_or], total_variables, tipos_variables, is_csv)
            right = self._parse_tokens(tokens[idx_or + 1 :], total_variables, tipos_variables, is_csv)
            return NodoLogico(OperadorAsignacionLogica.OR_EVAL, hijos=[left, right])

        if "XOR_EVAL" in tokens:
            idx_xor = tokens.index("XOR_EVAL")
            left = self._parse_tokens(tokens[:idx_xor], total_variables, tipos_variables, is_csv)
            right = self._parse_tokens(tokens[idx_xor + 1 :], total_variables, tipos_variables, is_csv)
            return NodoLogico(OperadorAsignacionLogica.XOR_EVAL, hijos=[left, right])

        if is_csv:
            try:
                return self._construir_restriccion_csv(tokens, total_variables)
            except Exception:
                pass
        else:
            joined = " ".join(tokens)
            if any(op in joined for op in (">=", "<=", "==", ">", "<", "=")):
                try:
                    return self._parse_algebraic_constraint(joined, total_variables)
                except Exception:
                    pass

        raise ValueError(f"No se pudo parsear la expresión: {' '.join(tokens)}")

    def _es_token_variable_suelta(self, tok: str, is_csv: bool) -> bool:
        """
        True si 'tok' es una referencia de variable suelta: sin coeficientes, sin
        operadores aritméticos, sin constantes numéricas. Siempre 'xN'; en modo CSV
        también un índice numérico plano ('N'), ya que allí las variables se
        referencian por su posición directa (ver 'Regla Implícita' del manual).
        """
        if tok.startswith("x") and tok[1:].isdigit():
            return True
        if is_csv and tok.isdigit():
            return True
        return False

    def _construir_restriccion_csv(self, parts: List[str], total_variables: int) -> Restriccion:
        """
        Construye una Restriccion a partir de una lista de campos CSV ya separados
        por comas: [coef1, ..., coefN, signo, rhs]. Usado tanto para bloques CSV
        parentizados como para líneas CSV planas de nivel superior (ej. '2, 1, <=, 10').
        """
        if len(parts) < 2:
            raise ValueError(
                f"Restricción CSV incompleta: se esperaban coeficientes, signo y RHS, se recibió: {', '.join(parts)}"
            )

        sign_str = parts[-2]
        rhs_str = parts[-1]
        coefs_str = parts[:-2]

        if sign_str == "<=":
            sign = SignoRestriccion.MENOR_IGUAL
        elif sign_str == ">=":
            sign = SignoRestriccion.MAYOR_IGUAL
        elif sign_str in ("==", "="):
            sign = SignoRestriccion.IGUAL
        else:
            raise ValueError(f"Signo de restricción no soportado: {sign_str}")

        coefs = [Fraction(c) for c in coefs_str]
        if len(coefs) < total_variables:
            coefs += [Fraction(0)] * (total_variables - len(coefs))

        return Restriccion(coefs, sign, Fraction(rhs_str))

    def _parse_csv_constraint(self, token: str, total_variables: int) -> Restriccion:
        """Parsea una restricción en formato CSV: (2, 0, <=, 40)"""
        token = token.strip("()")
        parts = [p.strip() for p in token.split(",") if p.strip()]
        return self._construir_restriccion_csv(parts, total_variables)

    def _parse_algebraic_constraint(self, text: str, total_variables: int) -> Restriccion:
        """Parsea una restricción en formato algebraico: 2x1 - 3x2 <= 10"""
        # Encontrar el operador relacional
        operators = (">=", "<=", "==", ">", "<", "=")
        op_found = None
        for op in operators:
            if op in text:
                op_found = op
                break

        if not op_found:
            raise ValueError(f"No se encontró operador de relación en: {text}")

        lhs_text, rhs_text = text.split(op_found, 1)
        lhs_text = lhs_text.replace(" ", "")
        rhs_val = Fraction(rhs_text.strip())

        # Mapear el operador
        if op_found in (">=", ">"):
            sign = SignoRestriccion.MAYOR_IGUAL
        elif op_found in ("<=", "<"):
            sign = SignoRestriccion.MENOR_IGUAL
        else:
            sign = SignoRestriccion.IGUAL

        # Parsear coeficientes de la parte izquierda (LHS)
        # Regex para buscar pares de coeficiente y variable, ej: -3x2, +x3, 5x1
        pattern = re.compile(r'([+-]?(?:[0-9]+(?:\.[0-9]+)?(?:/[0-9]+)?)?)(x([0-9]+))')
        matches = pattern.findall(lhs_text)

        coefs = [Fraction(0)] * total_variables
        for coef_str, _, var_num_str in matches:
            var_idx = int(var_num_str) - 1
            if var_idx >= total_variables:
                continue

            if not coef_str or coef_str == "+":
                coef_val = Fraction(1)
            elif coef_str == "-":
                coef_val = Fraction(-1)
            else:
                coef_val = Fraction(coef_str)
            coefs[var_idx] = coef_val

        return Restriccion(coefs, sign, rhs_val)