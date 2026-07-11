# src/models/entity/programacion_lineal_entera/enums.py
from enum import Enum, unique

@unique
class TipoVariable(Enum):
    """
    Categoría de cada variable de decisión.
    NOTA: todo el sistema (solvers tabulares, Branch and Bound, Planos de Corte)
    asume x >= 0 para las tres categorías; no existe forma de declarar una
    variable CONTINUA o ENTERA libre/negativa.
    """
    CONTINUA = "CONTINUA"
    ENTERA = "ENTERA"
    BINARIA = "BINARIA"


@unique
class OperadorLogico(Enum):
    """
    Operadores del álgebra booleana permitidos para modelar restricciones lógicas puras.
    Mapea de forma finita y estricta las relaciones proposicionales entre variables binarias.
    El solver filtra las soluciones permitiendo ÚNICAMENTE los escenarios donde el operador da 1.

    --------------------------------------------------------------------------------
    1. NEGACION (Incompatibilidad) -> Sintaxis: x1 NOT x2
       Concepto: Evita que ambas variables se activen a la vez. Permite que ninguna ocurra.
       Ecuación: x1 + x2 <= 1
       Tabla de verdad:
       | x1 | x2 | Resultado | ¿Permitido por el Solver? |
       | 0  | 0  |     1     | SI (No se hace ninguna)   |
       | 1  | 0  |     1     | SI (Solo x1)              |
       | 0  | 1  |     1     | SI (Solo x2)              |
       | 1  | 1  |     0     | NO (Incompatible)         |
    ----------------------------------------------------------------"""
    NEGACION = "NEGACION"
    
    """--------------------------------------------------------------------------------
    2. CONJUNCION (Obligación Simultánea) -> Sintaxis: x1 Y x2
       Concepto: Exige el cumplimiento obligatorio de todas las variables involucradas.
       Ecuación: x1 = 1, x2 = 1
       Tabla de verdad:
       | x1 | x2 | Resultado | ¿Permitido por el Solver? |
       | 0  | 0  |     0     | NO                        |
       | 1  | 0  |     0     | NO                        |
       | 0  | 1  |     0     | NO                        |
       | 1  | 1  |     1     | SI (Ambas obligadas a 1)  |
    ----------------------------------------------------------------"""
    CONJUNCION = "CONJUNCION"
    
    """--------------------------------------------------------------------------------
    3. DISYUNCION (Al menos una) -> Sintaxis: x1 O x2
       Concepto: Al menos una variable debe ser 1 (pueden ser ambas, pero nunca ninguna).
       Ecuación: x1 + x2 >= 1
       Tabla de verdad:
       | x1 | x2 | Resultado | ¿Permitido por el Solver? |
       | 0  | 0  |     0     | NO (Ninguna activa)       |
       | 1  | 0  |     1     | SI                        |
       | 0  | 1  |     1     | SI                        |
       | 1  | 1  |     1     | SI                        |
    ----------------------------------------------------------------"""
    DISYUNCION = "DISYUNCION"
    
    """--------------------------------------------------------------------------------
    4. EXCLUSION_MUTUA (Alternativa Única) -> Sintaxis: O x1 O x2
       Concepto: Se debe elegir exactamente una opción del catálogo. Nunca ambas, nunca ninguna.
       Ecuación: x1 + x2 = 1
       Tabla de verdad:
       | x1 | x2 | Resultado | ¿Permitido por el Solver? |
       | 0  | 0  |     0     | NO (Ninguna activa)       |
       | 1  | 0  |     1     | SI (Exactamente x1)       |
       | 0  | 1  |     1     | SI (Exactamente x2)       |
       | 1  | 1  |     0     | NO (Ambas activas)        |
    ----------------------------------------------------------------"""
    EXCLUSION_MUTUA = "EXCLUSION_MUTUA"
    
    """--------------------------------------------------------------------------------
    5. IMPLICACION (Condicional Directo) -> Sintaxis: x1 -> x2
       Concepto: Si ocurre el origen (x1), obliga la ocurrencia del destino (x2).
                 Si el origen no ocurre (0), el destino queda completamente libre.
       Ecuación: x1 - x2 <= 0
       Tabla de verdad:
       | x1 | x2 | Resultado | ¿Permitido por el Solver? |
       | 0  | 0  |     1     | SI (Origen 0, destino 0)  |
       | 0  | 1  |     1     | SI (Origen 0, destino 1)  |
       | 1  | 0  |     0     | NO (Se activó x1 pero no x2)|
       | 1  | 1  |     1     | SI (Se activó x1 y obligó x2)|
    ----------------------------------------------------------------"""
    IMPLICACION = "IMPLICACION"
    
    """--------------------------------------------------------------------------------
    6. EQUIVALENCIA (Co-requisito) -> Sintaxis: x1 == x2
       Concepto: Ambas variables quedan encadenadas. O actúan juntas o ninguna ocurre.
       Ecuación: x1 - x2 = 0
       Tabla de verdad:
       | x1 | x2 | Resultado | ¿Permitido por el Solver? |
       | 0  | 0  |     1     | SI (Ninguna ocurre)       |
       | 1  | 0  |     0     | NO                        |
       | 0  | 1  |     0     | NO                        |
       | 1  | 1  |     1     | SI (Ambas ocurren juntas) |
    ----------------------------------------------------------------"""
    EQUIVALENCIA = "EQUIVALENCIA"


@unique
class OperadorMGrande(Enum):
    """
    Operadores lógicos avanzados para el modelado de inecuaciones y condicionales.
    Requieren la inyección automática de variables binarias artificiales de control (y)
    y penalizaciones matemáticas mediante el método de la M Grande (M = 10**9) en el backend.
    
    A diferencia de los operadores puros, estos interceptan y modifican las filas 
    algebraicas y los lados derechos (RHS) de la matriz del problema lineal.

    REGLA IMPLÍCITA DE ENTRADA:
    Si una variable de tipo BINARIA se declara sola sin un operador relacional (ej: 'x1' en vez de 'x1 = 1'),
    el CompiladorLogico asumirá automáticamente que la restricción buscada es 'x1 = 1'.
    Para variables de tipo ENTERA o CONTINUA esta asunción está prohibida y se exigirá la ecuación completa.

    --------------------------------------------------------------------------------
    1. CONJUNCTION_RESTRICCIONES -> Sintaxis UI: (Ecuación1) Y (Ecuación2)
       Concepto: Obliga al cumplimiento simultáneo de todas las inecuaciones del bloque.
       Variables implicadas: Cualquier combinación (CONTINUA, ENTERA, BINARIA).
       Mecanismo Backend: Inyecta las restricciones algebraicas directamente en la matriz 
                          manteniendo sus fronteras originales intactas.
    --------------------------------------------------------------------------------"""
    CONJUNCION_RESTRICCIONES = "CONJUNCION_RESTRICCIONES"

    """--------------------------------------------------------------------------------
    2. DISYUNCION_RESTRICCIONES -> Sintaxis UI: (Ecuación1) O (Ecuación2)
       Concepto: Exige que al menos una de las inecuaciones del bloque se cumpla de forma estricta.
       Variables implicadas: Cualquier combinación (CONTINUA, ENTERA, BINARIA).
       Mecanismo Backend: Asocia un interruptor binario 'y_i' a cada restricción f_i(x) <= b_i.
                          Si y_i = 1 -> Se cumple f_i(x) <= b_i
                          Si y_i = 0 -> Se apaga mediante f_i(x) <= b_i + M
                          Inyecta la fila de control: sum(y_i) >= 1
    --------------------------------------------------------------------------------"""
    DISYUNCION_RESTRICCIONES = "DISYUNCION_RESTRICCIONES"
    
    """--------------------------------------------------------------------------------
    3. SELECCION_K_DE_N -> Sintaxis UI: CUMPLIR K DE [ (Ecuación1), ..., (EcuaciónN) ]
       Concepto: Paquete de N restricciones donde se activan 'y_i' de control para K de ellas.
                 ⚠️ Garantiza que AL MENOS K restricciones se cumplan (las y_i=1 lo fuerzan);
                 las N-K restantes quedan relajadas (y_i=0), pero nada impide que también se
                 cumplan por sí solas si el resto del modelo así lo permite. No es "exactamente K".
       Variables implicadas: Cualquier combinación (CONTINUA, ENTERA, BINARIA).
       Mecanismo Backend: Asocia un interruptor binario 'y_i' a cada una de las N restricciones.
                          Aplica la holgura con M a las filas: f_i(x) <= b_i + M(1 - y_i)
                          Inyecta la fila de control estricto: sum(y_i) == K
    --------------------------------------------------------------------------------"""
    SELECCION_K_DE_N = "SELECCION_K_DE_N"
    
    """--------------------------------------------------------------------------------
    4. ACTIVACION_UMBRAL -> Sintaxis UI: x1 ACTIVADO_POR x2
       Concepto: Vincula una variable continua/entera (x1) a una decisión binaria (x2).
                 Si x2 = 0 -> x1 se bloquea en 0. Si x2 = 1 -> x1 puede producirse libremente.
       Variables implicadas: Origen (CONTINUA o ENTERA) -> Destino (BINARIA).
       Mecanismo Backend: Inyecta la inecuación de acotamiento superior en la matriz:
                          x1 <= M * x2  ==>  x1 - 10**9 * x2 <= 0
    --------------------------------------------------------------------------------"""
    ACTIVACION_UMBRAL = "ACTIVACION_UMBRAL"
    
    """--------------------------------------------------------------------------------
    5. CONDICIONAL_COMPUESTO -> Sintaxis UI: SI (EcuaciónA) ENTONCES (EcuaciónB)
       Concepto: Si el solver valida la EcuaciónA, se activa la obligación de cumplir la EcuaciónB.
                 Si la EcuaciónA es falsa, la EcuaciónB queda completamente libre.
       Variables implicadas: Ecuaciones condicionales con cualquier tipo de variable.
       Mecanismo Backend: Usa un interruptor binario artificial para evaluar la EcuaciónA.
                          Si la condición se cumple, el interruptor remueve la penalización M 
                          de la fila de la EcuaciónB, forzando al Simplex a respetarla.
    --------------------------------------------------------------------------------"""
    CONDICIONAL_COMPUESTO = "CONDICIONAL_COMPUESTO"
    
    """--------------------------------------------------------------------------------
    6. VALORES_DISJUNTOS -> Sintaxis UI: x1 EN [Valor1, Valor2, Valor3]
       Concepto: Restringe a una variable continua o entera a tomar únicamente valores de un lote.
       Variables implicadas: Una única variable de tipo CONTINUA o ENTERA.
       Mecanismo Backend: Crea un interruptor 'y_i' por cada valor comercial del conjunto.
                          Para cada opción inyecta un par de inecuaciones de igualdad forzada:
                          x1 - Valor_i <= M(1 - y_i)  AND  Valor_i - x1 <= M(1 - y_i)
                          Inyecta la fila de control de opción única: sum(y_i) == 1
    --------------------------------------------------------------------------------"""
    VALORES_DISJUNTOS = "VALORES_DISJUNTOS"


@unique
class OperadorAsignacionLogica(Enum):
    """
    Operadores de Evaluación y Reificación Booleana.
    Permiten medir el estado lógico de variables binarias SIN forzar u obligar sus valores originales.
    Guardan el resultado booleano (0 o 1) para ser usado de forma libre o en estructuras superiores.

    COMPORTAMIENTO ESTRUCTURAL EN EL COMPILADOR (AST):
    - Caso 1 (Como restricción directa): Usado suelto en una línea (ej. x3 = (x1 AND_EVAL x2)),
      el resultado de la evaluación se asigna directamente a la variable binaria declarada a la izquierda.
    - Caso 2 (Dentro de un condicional): Usado anidado dentro de un operador de M Grande 
      (ej. SI (x1 AND_EVAL x2) ENTONCES ...), el CompiladorLogico generará automáticamente 
      una variable binaria artificial intermedia (a_i) para capturar la evaluación del bloque.
    """

    """--------------------------------------------------------------------------------
    1. AND_EVAL -> Sintaxis UI: x3 = (x1 AND_EVAL x2)  ó  SI (x1 AND_EVAL x2) ENTONCES ...
       Concepto: Conjunción libre. El destino (directo o artificial) será 1 si y solo si 
                 ambas variables de origen son 1.
       Ecuaciones generadas en la matriz (donde 'dest' es x3 o la variable artificial a_i):
         1. dest <= x1
         2. dest <= x2
         3. x1 + x2 - dest <= 1
    --------------------------------------------------------------------------------"""
    AND_EVAL = "AND_EVAL"

    """--------------------------------------------------------------------------------
    2. OR_EVAL -> Sintaxis UI: x3 = (x1 OR_EVAL x2)  ó  SI (x1 OR_EVAL x2) ENTONCES ...
       Concepto: Disyunción libre. El destino (directo o artificial) será 1 si al menos 
                 una de las variables de origen es 1.
       Ecuaciones generadas en la matriz (donde 'dest' es x3 o la variable artificial a_i):
         1. dest >= x1
         2. dest >= x2
         3. x1 + x2 - dest >= 0
    --------------------------------------------------------------------------------"""
    OR_EVAL = "OR_EVAL"

    """--------------------------------------------------------------------------------
    3. XOR_EVAL -> Sintaxis UI: x3 = (x1 XOR_EVAL x2)  ó  SI (x1 XOR_EVAL x2) ENTONCES ...
       Concepto: Exclusión mutua libre. El destino (directo o artificial) será 1 si y solo si 
                 exactamente una de las dos variables de origen es 1 (nunca ambas, nunca ninguna).
       Ecuaciones generadas en la matriz (donde 'dest' es x3 o la variable artificial a_i):
         1. dest <= x1 + x2
         2. dest >= x1 - x2
         3. dest >= x2 - x1
         4. dest <= 2 - x1 - x2
    --------------------------------------------------------------------------------"""
    XOR_EVAL = "XOR_EVAL"