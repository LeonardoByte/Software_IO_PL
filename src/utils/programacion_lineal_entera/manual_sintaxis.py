# src/utils/programacion_lineal_entera/manual_sintaxis.py

def obtener_manual_algebraico() -> str:
   """Devuelve el manual de usuario para el ingreso en lenguaje natural/algebraico."""
   return """
================================================================================
          MANUAL DE SINTAXIS PARA EL INGRESO ALGEBRAICO (P.L. ENTERA)
================================================================================

Este módulo permite modelar problemas de optimización combinando ecuaciones 
matemáticas tradicionales con reglas lógicas avanzadas y uso de paréntesis ().

--------------------------------------------------------------------------------
SECCIÓN 1: CONFIGURACIÓN DE VARIABLES (Función Objetivo)
--------------------------------------------------------------------------------
En la segunda línea de la sección de la Función Objetivo, se debe declarar 
obligatoriamente el tipo de cada variable usando:
  * C = Continua (Permite decimales, ej: litros, kilogramos)
  * E = Entera (Solo números enteros, ej: camiones, personal)
  * B = Binaria (Solo valores 0 o 1, ej: decisiones de SÍ/NO)

Ejemplo de Ingreso:
  MAX Z = 50x1 + 80x2 + 30x3
  x1=C x2=E x3=B

⚠️ NOTA: Las tres categorías (C, E, B) asumen siempre x >= 0. No existe forma
de modelar una variable continua o entera libre/negativa.

--------------------------------------------------------------------------------
SECCIÓN 2: RESTRICCIONES LÓGICAS PURAS (OperadorLogico)
--------------------------------------------------------------------------------
⚠️ REGLA DE ORO: Estas reglas aplican ÚNICAMENTE para relacionar variables 
BINARIAS (B) entre sí. Filtran el espacio de soluciones permitiendo solo los 
casos donde la expresión completa da VERDADERO (1).

1. NEGACION (Incompatibilidad) -> Sintaxis: x1 NOT x2
   * El solver prohíbe que ambas ocurran juntas. Permite que ninguna ocurra.
   * Ecuación: x1 + x2 <= 1

2. CONJUNCION (Obligación Simultánea) -> Sintaxis: x1 Y x2
   * El solver obliga de forma estricta a que ambas variables sean 1.
   * Ecuación: x1 = 1, x2 = 1

3. DISYUNCION (Al menos una) -> Sintaxis: x1 O x2
   * Obliga a elegir al menos una de las opciones. Permite que sean ambas.
   * Ecuación: x1 + x2 >= 1

4. EXCLUSION_MUTUA (Alternativa Única) -> Sintaxis: O x1 O x2
   * Obliga a elegir exactamente una sola opción. Nunca ambas, nunca ninguna.
   * Ecuación: x1 + x2 = 1

5. IMPLICACION (Condicional Directo) -> Sintaxis: x1 -> x2
   * Si se activa x1, obliga a activar x2. Si x1 es 0, x2 queda libre.
   * Ecuación: x1 - x2 <= 0

6. EQUIVALENCIA (Co-requisito) -> Sintaxis: x1 == x2
   * Ambas variables quedan amarradas: u ocurren las dos juntas, o ninguna.
   * Ecuación: x1 - x2 = 0

--------------------------------------------------------------------------------
SECCIÓN 3: RESTRICCIONES AVANZADAS DE CAMPAÑA (OperadorMGrande)
--------------------------------------------------------------------------------
💡 NOTA: Estas reglas modifican ecuaciones completas e inecuaciones algebraicas. 
Soportan CUALQUIER tipo de variable (C, E, B) mediante la M Grande (10**9).

💡 REGLA IMPLÍCITA: Si escribes una variable BINARIA sola (ej: x3), el motor 
asumirá automáticamente 'x3 = 1'. Para variables C o E, se exige la ecuación completa.

1. CONJUNCION_RESTRICCIONES -> Sintaxis: (Ecuación1) Y (Ecuación2)
   * Obliga a que todas las inecuaciones del bloque se cumplan simultáneamente.

2. DISYUNCION_RESTRICCIONES -> Sintaxis: (Ecuación1) O (Ecuación2)
   * Exige que al menos una de las inecuaciones se cumpla de forma estricta.

3. SELECCION_K_DE_N -> Sintaxis: CUMPLIR K DE [ (Ecuación1), ..., (EcuaciónN) ]
   * Obliga a que se cumplan AL MENOS 'K' restricciones del paquete (las N-K
     restantes quedan libres, pero podrían cumplirse igual por su cuenta).

4. ACTIVACION_UMBRAL -> Sintaxis: x1 ACTIVADO_POR x2
   * Vincula una variable continua/entera (x1) a una binaria (x2). 
   * Si x2 = 0, entonces x1 se bloquea en 0. Si x2 = 1, x1 opera libremente.

5. CONDICIONAL_COMPUESTO -> Sintaxis: SI (EcuaciónA) ENTONCES (EcuaciónB)
   * Si el solver valida la EcuaciónA, se vuelve obligatorio cumplir la EcuaciónB.

6. VALORES_DISJUNTOS -> Sintaxis: x1 EN [Valor1, Valor2, Valor3]
   * Restringe a una variable continua o entera a tomar únicamente un valor del lote.

--------------------------------------------------------------------------------
SECCIÓN 4: ASIGNACIÓN Y EVALUACIÓN LÓGICA (OperadorAsignacionLogica)
--------------------------------------------------------------------------------
💡 NOTA: Miden el estado lógico de variables binarias SIN forzar sus valores 
originales, guardando el resultado en un contenedor (directo o artificial).

* Caso 1 (Suelto): x3 = (x1 AND_EVAL x2) -> Asigna el resultado directo a x3.
* Caso 2 (Anidado): SI (x1 AND_EVAL x2) ENTONCES ... -> Genera una variable 
  intermedia interna (a_i) automática para evaluar el bloque sin obligar a x1 ni x2.

1. AND_EVAL -> Sintaxis: x3 = (x1 AND_EVAL x2)
   * El destino será 1 si y solo si ambas variables de origen se activan de forma libre.

2. OR_EVAL  -> Sintaxis: x3 = (x1 OR_EVAL x2)
   * El destino será 1 si al menos una de las variables de origen se activa libremente.

3. XOR_EVAL -> Sintaxis: x3 = (x1 XOR_EVAL x2)
   * El destino será 1 si exactamente una de las dos variables se activa (nunca ambas).

--------------------------------------------------------------------------------
EJEMPLO DE MODELADO AVANZADO Y COMPLEJO:
--------------------------------------------------------------------------------
Puedes anidar expresiones complejas usando paréntesis de forma natural:

  SI (produccion_total > 500) ENTONCES (O x1 O x2)
  x3 = (proveedorA AND_EVAL proveedorB)
  SI x1 ENTONCES x3
"""


def obtener_manual_csv() -> str:
   """Devuelve el manual de usuario para el ingreso en formato de coeficientes planos CSV."""
   return """
================================================================================
            MANUAL DE SINTAXIS PARA EL INGRESO CSV (P.L. ENTERA)
================================================================================

Este módulo permite ingresar problemas de optimización combinando coeficientes 
numéricos planos con reglas lógicas y agrupaciones separadas por comas (,).

--------------------------------------------------------------------------------
SECCIÓN 1: CONFIGURACIÓN DE VARIABLES (Función Objetivo)
--------------------------------------------------------------------------------
En la caja de texto de la Función Objetivo, debes declarar el tipo de cada 
variable en la segunda línea en el orden exacto del vector, usando comas:
  * C = Continua (Permite decimales, ej: litros, kilogramos)
  * E = Entera (Solo números enteros, ej: camiones, personal)
  * B = Binaria (Solo valores 0 o 1, ej: decisiones de SÍ/NO)

Ejemplo de Ingreso:
  MAX, 50, 80, 30
  C, E, B

--------------------------------------------------------------------------------
SECCIÓN 2: RESTRICCIONES LÓGICAS PURAS (OperadorLogico)
--------------------------------------------------------------------------------
⚠️ REGLA DE ORO: Estas reglas aplican ÚNICAMENTE para relacionar variables 
BINARIAS (B) entre sí a través de sus índices. Filtran el espacio de soluciones 
permitiendo solo los casos donde la expresión completa da VERDADERO (1).

1. NEGACION (Incompatibilidad) -> Sintaxis: [índice1], NOT, [índice2]
   * El solver prohíbe que ambas ocurran juntas. Permite que ninguna ocurra.
   * Ejemplo: 1, NOT, 2  (Equivale a: x1 + x2 <= 1)

2. CONJUNCION (Obligación Simultánea) -> Sintaxis: [índice1], Y, [índice2]
   * El solver obliga de forma estricta a que ambas variables sean 1.
   * Ejemplo: 1, Y, 2  (Equivale a: x1 = 1, x2 = 1)

3. DISYUNCION (Al menos una) -> Sintaxis: [índice1], O, [índice2]
   * Obliga a elegir al menos una de las opciones. Permite que sean ambas.
   * Ejemplo: 1, O, 2  (Equivale a: x1 + x2 >= 1)

4. EXCLUSION_MUTUA (Alternativa Única) -> Sintaxis: O, [índice1], O, [índice2]
   * Obliga a elegir exactamente una sola opción. Nunca ambas, nunca ninguna.
   * Ejemplo: O, 1, O, 2  (Equivale a: x1 + x2 = 1)

5. IMPLICACION (Condicional Directo) -> Sintaxis: [índice1], ->, [índice2]
   * Si se activa el origen, obliga al destino. Si el origen es 0, el destino queda libre.
   * Ejemplo: 1, ->, 2  (Equivale a: x1 - x2 <= 0)

6. EQUIVALENCIA (Co-requisito) -> Sintaxis: [índice1], ==, [índice2]
   * Ambas variables quedan amarradas: u ocurren las dos juntas, o ninguna.
   * Ejemplo: 1, ==, 2  (Equivale a: x1 - x2 = 0)

--------------------------------------------------------------------------------
SECCIÓN 3: RESTRICCIONES AVANZADAS DE CAMPAÑA (OperadorMGrande)
--------------------------------------------------------------------------------
💡 NOTA: Estas reglas modifican vectores de coeficientes planos. Soportan CUALQUIER 
tipo de variable (C, E, B) mediante la M Grande de backend (Fraction(10**9)).

💡 REGLA IMPLÍCITA: Si escribes un índice de variable BINARIA solo (ej: 3), el motor 
asumirá automáticamente 'x3 = 1'. Para variables C o E, se exige la fila de coeficientes completa.

1. CONJUNCION_RESTRICCIONES -> Sintaxis: (Fila_Coeficientes1, Signo1, RHS1) Y (Fila_Coeficientes2, Signo2, RHS2)
   * Ejemplo: (2, 0, <=, 40) Y (0, 3, <=, 60)

2. DISYUNCION_RESTRICCIONES -> Sintaxis: (Fila_Coeficientes1, Signo1, RHS1) O (Fila_Coeficientes2, Signo2, RHS2)
   * Ejemplo: (2, 0, <=, 40) O (0, 3, <=, 60)

3. SELECCION_K_DE_N -> Sintaxis: CUMPLIR, K, DE, [ (Fila1, Signo1, RHS1), ..., (FilaN, SignoN, RHSN) ]
   * Ejemplo: CUMPLIR, 2, DE, [ (1, 0, <=, 10), (0, 1, <=, 15) ]

4. ACTIVACION_UMBRAL -> Sintaxis: [índice_var_continua], ACTIVADO_POR, [índice_var_binaria]
   * Ejemplo: 1, ACTIVADO_POR, 2

5. CONDICIONAL_COMPUESTO -> Sintaxis: SI, (FilaA, SignoA, RHSA), ENTONCES, (FilaB, SignoB, RHSB)
   * Ejemplo: SI, (0, 1, >=, 100), ENTONCES, (1, 0, <=, 20)

6. VALORES_DISJUNTOS -> Sintaxis: [índice_variable], EN, [Valor1, Valor2, Valor3]
   * Ejemplo: 1, EN, [50, 100, 150]

--------------------------------------------------------------------------------
SECCIÓN 4: ASIGNACIÓN Y EVALUACIÓN LÓGICA (OperadorAsignacionLogica)
--------------------------------------------------------------------------------
💡 NOTA: Miden el estado lógico de variables binarias mediante índices SIN forzar 
sus valores originales, guardando el resultado en un contenedor (directo o artificial).

* Caso 1 (Suelto): [índice3], =, ([índice1], AND_EVAL, [índice2]) -> Asigna resultado directo.
* Caso 2 (Anidado): SI, ([índice1], AND_EVAL, [índice2]), ENTONCES, ... -> Genera una variable 
  intermedia interna (a_i) automática para evaluar el bloque sin obligar a los orígenes.

1. AND_EVAL -> Sintaxis: 3, =, (1, AND_EVAL, 2)
   * El destino será 1 si y solo si ambas variables de origen se activan de forma libre.

2. OR_EVAL  -> Sintaxis: 3, =, (1, OR_EVAL, 2)
   * El destino será 1 si al menos una de las variables de origen se activa libremente.

3. XOR_EVAL -> Sintaxis: 3, =, (1, XOR_EVAL, 2)
   * El destino será 1 si exactamente una de las dos variables se activa (nunca ambas).

--------------------------------------------------------------------------------
EJEMPLO DE MODELADO AVANZADO Y COMPLEJO EN CSV:
--------------------------------------------------------------------------------
Puedes anidar expresiones numéricas y de índices usando paréntesis de forma lineal:

  SI, (0, 1, >, 500), ENTONCES, (O, 1, O, 2)
  3, =, (4, AND_EVAL, 5)
  SI, 1, ENTONCES, 3
"""