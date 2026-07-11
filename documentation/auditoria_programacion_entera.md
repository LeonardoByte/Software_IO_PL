# Auditoría de Correctitud — Módulo de Programación Lineal Entera (PLE)

Fecha: 2026-07-10
**Actualización 2026-07-10: los 10 hallazgos originales fueron corregidos y verificados con pruebas ejecutables end-to-end (parser → compilador → solver). Ver "Estado de corrección" al final de cada hallazgo y el Adendo con un bug adicional descubierto durante la verificación.**
**Actualización 2026-07-10 (2): reporte de usuario sobre freeze en la UI de Cortes de Gomory, `==` no reconocido en PLE, y guardado silencioso sin alerta llevó a 4 hallazgos adicionales (#12-#15), todos corregidos. Ver "Adendo 2" al final del documento.**
Alcance revisado: `src/utils/programacion_lineal_entera/`, `src/models/metodos/programacion_lineal_entera/`, `src/models/entity/programacion_lineal_entera/`, más las dependencias de las que depende su correctitud (`src/models/metodos/programacion_lineal_basica/*`, `src/models/entity/programacion_lineal/*`, `src/utils/programacion_lineal_entera/parser_sintactico.py`).

Metodología: lectura línea por línea de cada archivo, re-derivación matemática de cada algoritmo (Branch and Bound, Cortes de Gomory, Enumeración de Balas, compilación lógica a Big-M), y construcción de contraejemplos numéricos concretos para cada hallazgo marcado como reproducible. No se modificó ningún archivo — esta es una auditoría de solo lectura.

---

## Resumen ejecutivo

Se confirmaron **10 hallazgos**. Los dos más graves (#1 y #2) hacen que el solver devuelva **respuestas incorrectas de forma silenciosa** en escenarios de modelado razonables y alcanzables desde la UI/parser actual — no son casos límite teóricos. El método de **Branch and Bound es el más confiable de los tres** (evita deliberadamente el bug #1, y el bug de floats de `floor`/`ceil` es de bajo riesgo práctico). **Planos de Corte y el Compilador Lógico son los que requieren atención prioritaria.**

| # | Hallazgo | Severidad | Archivo | Estado |
|---|---|---|---|---|
| 1 | Planos de Corte reporta INVIABLE en problemas factibles con RHS negativo en restricciones `<=` | **Crítica** | `planos_corte.py` | ✅ Corregido |
| 2 | `SI...ENTONCES` con antecedente de inecuación no obliga realmente la implicación | **Alta** | `compilador_logica.py` | ✅ Corregido |
| 3 | `EXCLUSION_MUTUA`/`VALORES_DISJUNTOS` anidado restringe de más (equality en vez de reificación) | **Alta** | `compilador_logica.py` | ✅ Corregido |
| 4 | Branch and Bound calcula floor/ceil convirtiendo `Fraction` a `float` | Media | `branch_and_bound.py` | ✅ Corregido |
| 5 | Enumeración Implícita reporta INVIABLE cuando en realidad se agotó el límite de pasos | Media | `enumeracion_implicita.py` | ✅ Corregido |
| 6 | `SolucionadorSimplex` confunde "RHS negativo" con "inviable" (causa raíz de #1) | Baja | `simplex.py` | ✅ Corregido |
| 7 | B&B con `metodo_lineal=2` heredaría el bug #6 en subproblemas — no alcanzable desde la UI | Baja | `branch_and_bound.py` | ✅ Corregido |
| 8 | `SELECCION_K_DE_N` implementa "al menos K", la documentación dice "exactamente K" | Baja | `compilador_logica.py` / `enums.py` | ✅ Corregido (doc) |
| 9 | Variable muerta `const_obj` en Enumeración Implícita | Baja | `enumeracion_implicita.py` | ✅ Corregido |
| 10 | No-negatividad de variables `CONTINUA` asumida en todo el sistema, sin documentar | Baja | `branch_and_bound.py` / `resolucion_rapida.py` | ✅ Corregido (doc) |
| 11 | *(Descubierto en verificación)* Artificial degenerada-básica descartada en Fase 2, desalinea filas | **Crítica** | `dos_fases.py` | ✅ Corregido |

---

## CRÍTICO

### 1. Planos de Corte reporta INVIABLE en problemas factibles con RHS negativo

**Archivo:** `planos_corte.py:194-205` (`_elegir_solver`) — causa raíz en `simplex.py:74-80`

**Descripción:** `_elegir_solver` de `SolucionadorPlanosCorte` elige `SolucionadorSimplex` cada vez que el problema no tiene restricciones `>=`/`==`, sin verificar el signo del RHS. `SolucionadorSimplex.resolver` (pasos de validación, líneas 74-80) devuelve `EstadoProblema.INVIABLE` de inmediato si **cualquier** restricción tiene `rhs < 0`. Eso es incorrecto: una restricción `<=` con RHS negativo no implica inviabilidad del problema (ej. `-x1 <= -5` equivale a `x1 >= 5`, perfectamente factible). Se confirmó que no existe ninguna validación previa que lo impida: `Restriccion.__post_init__` solo exige que la lista de coeficientes no esté vacía, y `ProblemaPLE.__post_init__` solo valida dimensiones. El parser (`parser_sintactico.py:355-399`) tampoco restringe el signo del RHS al construir la `Restriccion`.

**Contraejemplo verificado:**
```
MAX x1 + x2
x1 - 2x2 <= -1
x1 <= 5
x2 <= 5
x1, x2 enteras
```
Es factible (x1=5, x2=5 → 5-10=-5 ≤ -1) y el óptimo real es Z=10 en x1=x2=5. Al resolver con **Planos de Corte**, como todas las restricciones son `<=`, se despacha a `SolucionadorSimplex`, que ve `rhs=-1 < 0` y devuelve INVIABLE de inmediato — **sin siquiera intentar resolver**. El mismo modelo resuelto con **Branch and Bound** sí devuelve la respuesta correcta, porque `branch_and_bound.py` evita deliberadamente este camino (ver contraste en el hallazgo #7).

**Por qué los cortes de Gomory en sí no agravan el problema:** se verificó que la normalización de cada corte (líneas 154-160: si `rhs_corte < 0`, se invierten signos) garantiza que todo corte agregado tenga RHS no-negativo. El riesgo viene exclusivamente de las restricciones **originales** que ingresa el usuario.

**Corrección sugerida:** en `planos_corte._elegir_solver`, usar `SolucionadorDosFases` también cuando exista una restricción con `rhs < 0` (o, más simple, usar siempre Dos Fases como ya hace `branch_and_bound.py`). Idealmente corregir la causa raíz en `simplex.py` (hallazgo #6).

**Estado: ✅ Corregido.** Se aplicó la causa raíz (#6, ver abajo) más un reintento automático: `planos_corte.resolver` ahora detecta `EstadoProblema.REQUIERE_OTRO_METODO` y reintenta con `SolucionadorDosFases` antes de rendirse. Verificado con el contraejemplo exacto del hallazgo: ahora devuelve `OPTIMO`, Z=10.

---

## ALTA

### 2. `SI...ENTONCES` con antecedente de inecuación no fuerza realmente la implicación

**Archivo:** `compilador_logica.py:300-311` (rama `CONDICIONAL_COMPUESTO`), interactuando con la compilación de `Restriccion` en líneas 122-156

**Descripción:** Cuando la sintaxis `SI (EcuaciónA) ENTONCES (EcuaciónB)` usa inecuaciones (no variables binarias sueltas) como antecedente, cada una se compila a un control binario `w` mediante un Big-M **unidireccional**: `w=1 ⟹ se cumple la restricción`, pero el converso **no** se impone — nada obliga a `w=1` cuando la restricción ya se cumple de hecho. Por ejemplo, para `x1 >= 1` la fila generada es `-x1 + M·w <= M-1`; con x1=1, `w` queda libre en {0,1}. El nodo condicional luego solo exige `w_A <= w_B`. Como el solver puede fijar libremente `w_A=0` aunque la condición A sea verdadera, la implicación completa queda **vacía** cada vez que conviene a la función objetivo.

**Alcanzabilidad confirmada en el parser:** `parser_sintactico.py:178-185` construye `CONDICIONAL_COMPUESTO` parseando recursivamente el antecedente y el consecuente sin restringir su tipo — una `Restriccion` (inecuación) es un resultado perfectamente válido para ambos lados.

**Contraejemplo verificado:**
```
SI (x1 >= 1) ENTONCES (x2 >= 1)
MAX x1
x1, x2 binarias
```
La intención es: si x1=1, entonces x2 debe ser 1. El modelo compilado permite x1=1 con `w_A=0 → w_B=0 →` x2 sin restricción real → el solver puede devolver x1=1, x2=0, violando la regla que el usuario pidió modelar.

**Nota importante:** `x1 -> x2` entre variables binarias sueltas (sin inecuaciones) **sí es correcto** — en ese caso `child_vars` son índices reales de variable y el resultado es `x1 <= x2`, la implicación estándar. El bug es específico a antecedentes que son inecuaciones/controles reificados dentro de `CONDICIONAL_COMPUESTO` (y por extensión, a `NEGACION`/`CONJUNCION`/`DISYUNCION`/`EQUIVALENCIA` cuando aparecen como antecedente de un condicional, ya que comparten el mismo patrón de reificación unidireccional).

**Corrección sugerida:** una restricción usada como antecedente necesita la reificación inversa también (`se cumple la restricción ⟹ w=1`), es decir una doble implicación (iff), no un Big-M de una sola dirección.

**Estado: ✅ Corregido** en `compilador_logica.py`, con una precisión importante encontrada durante el diseño de la corrección: el ejemplo original del hallazgo (`SI (x1>=1) ENTONCES (x2>=1)` entre binarias sueltas) en realidad **ya funcionaba** — el atajo de "afirmación binaria suelta" (líneas 89-95) evita crear una variable artificial y devuelve directamente el índice de x1, que ya es un indicador verdadero. El bug real solo se dispara cuando el antecedente genera una variable artificial (ej. `SI (x1 + x2 >= 1) ENTONCES (x3 >= 1)`), caso con el que se verificó la corrección. Se agregó un parámetro `reificar_completo` que activa la dirección inversa del Big-M únicamente en el antecedente (`hijos[0]`) de `SI...ENTONCES`, con derivación exacta (sin tolerancia arbitraria) para `Restriccion`, `NEGACION`, `IMPLICACION` y `EQUIVALENCIA`. Para restricciones con variables `CONTINUA` como antecedente, se decidió **fallar explícitamente con `ValueError`** en vez de compilar un modelo no seguro: no existe una cota exacta para "a·x > b" sobre los reales, y para una herramienta didáctica es preferible un error claro a un resultado silenciosamente incorrecto.

### 3. `EXCLUSION_MUTUA`/`VALORES_DISJUNTOS` anidado sobre-restringe el espacio factible

**Archivo:** `compilador_logica.py:288-298`

**Descripción:** Estos operadores compilan a una única igualdad `sum(w_r) = y`. En la **raíz** del árbol, `_procesar_nodo` (líneas 61-74) fuerza `y=1`, dando `sum(w_r)=1` — la semántica correcta de "exactamente una opción". Pero cuando el nodo aparece **anidado** (por ejemplo como parte de un `SI...ENTONCES`), `y` no se fuerza a 1: sin embargo, como `y` está declarada `BINARIA`, la igualdad `sum(w_r) = y` sigue forzando incondicionalmente `sum(w_r) ∈ {0,1}` — es decir, "a lo sumo una opción activa" **siempre**, sin importar el valor real que debería tomar `y` como reificación libre. Esto es inconsistente con el patrón correcto usado por `AND_EVAL`/`OR_EVAL`/`XOR_EVAL` y por `SELECCION_K_DE_N`, que sí relajan completamente el bloque cuando su control vale 0.

**Alcanzabilidad confirmada:** el propio manual de sintaxis (`manual_sintaxis.py`, sección de operadores avanzados) documenta el ejemplo anidado `SI (...) ENTONCES (O x1 O x2)`, y el parser (`parser_sintactico.py:243-247`) construye `EXCLUSION_MUTUA` de forma completamente recursiva — no es un camino muerto, es un caso de uso documentado.

**Contraejemplo verificado (conceptual):**
```
(O x1 O x2) O (x3 >= 5)
MAX x1 + x2
x1, x2 binarias; x3 entera
```
"Exactamente una de x1/x2 — O — se cumple x3≥5". Lógicamente, si x3≥5 se satisface, x1 y x2 deberían quedar libres (podrían ser ambas 1). Pero como el bloque de exclusión mutua compila a `x1+x2=y_excl` con `y_excl<=1` de forma incondicional, `x1+x2=2` queda prohibido sin importar x3, y el solver pierde la solución óptima x1=x2=1.

**Corrección sugerida:** reificar con condicionamiento Big-M (igual que hace `SELECCION_K_DE_N`, líneas 336-358) para que `y=0` relaje completamente el bloque, y agregar la implicación inversa si se necesita un indicador verdadero (iff).

**Estado: ✅ Corregido.** La igualdad incondicional `sum(w_r)=y` fue reemplazada por el mismo par de inecuaciones Big-M condicionadas que usa `SELECCION_K_DE_N` (con K=1): fuerza `sum(w_r)=1` solo cuando `y=1`, y relaja el bloque por completo cuando `y=0`. Verificado con el contraejemplo del hallazgo (`(O x1 O x2) O (x3 >= 5)`): ahora devuelve correctamente Z=2 (x1=x2=1, habilitado por x3≥5) en vez de la solución subóptima Z=1.

---

## MEDIA

### 4. Branch and Bound calcula floor/ceil convirtiendo `Fraction` a `float`

**Archivo:** `branch_and_bound.py:199-200`

**Descripción:** `floor_val = math.floor(float(val_frac))` y el `ceil` equivalente convierten el `Fraction` exacto a `float` (mantisa de 53 bits) antes de redondear. Si el numerador/denominador de `val_frac` excede aproximadamente 2⁵³ y el valor cae muy cerca de un límite entero, la conversión a `float` puede cruzar ese límite y producir un floor/ceil erróneo por una unidad, corrompiendo silenciosamente las cotas de ramificación (`L`/`U`) y pudiendo podar la rama que contiene el óptimo real. Esto contradice la convención del proyecto (ver `CLAUDE.md`) de usar aritmética exacta con `Fraction` en todo cálculo que alimente los solvers tabulares.

**Evaluación de riesgo práctico:** requiere que los determinantes de la base del tableau empujen denominadores más allá de ~9×10¹⁵, algo que no ocurre en los problemas pequeños tipo "material didáctico" para los que está pensada esta herramienta. La prueba de fraccionalidad en sí (`_obtener_variable_fraccionaria`, línea 375) sí es exacta (`denominator != 1`) — solo el cálculo del floor/ceil se ve afectado. Riesgo real pero de baja probabilidad de disparo con los tamaños de problema típicos.

**Corrección sugerida:** usar floor/ceil enteros exactos sobre el propio `Fraction`: `floor = val_frac.numerator // val_frac.denominator`; `ceil = -((-val_frac.numerator) // val_frac.denominator)`.

**Estado: ✅ Corregido.** `branch_and_bound.py` ahora calcula floor/ceil exactos vía división entera sobre `numerator`/`denominator`, sin pasar por `float`. Verificado con una `Fraction` de numerador/denominador ~2⁶⁰ diseñada para que `float()` la redondee exactamente a un entero (perdiendo la fraccionalidad): el cálculo exacto sigue detectando correctamente floor=1, ceil=2.

### 5. Enumeración Implícita reporta INVIABLE cuando en realidad se agotó el límite de pasos

**Archivo:** `enumeracion_implicita.py:237-244` (en combinación con el límite `MAX_STEPS=1000` de la línea 92)

**Descripción:** Si la búsqueda DFS agota `MAX_STEPS` antes de encontrar cualquier solución entera factible, `best_Y` sigue siendo `None`, y el código devuelve `EstadoProblema.INVIABLE` — afirmando que el problema no tiene solución — en vez de un estado de "límite alcanzado / desconocido". Con n variables binarias el árbol puede llegar a ~2^(n+1) nodos, así que para n ≳ 10 el presupuesto de pasos puede agotarse antes de encontrar la primera hoja factible, etiquetando erróneamente como inviable un problema que sí tiene solución (incluso óptima).

**Corrección sugerida:** cuando `steps_count >= MAX_STEPS` y `best_Y is None`, devolver `EstadoProblema.LIMITE_ITERACIONES` (desconocido), no `INVIABLE`.

**Estado: ✅ Corregido.** Se agregó exactamente esa distinción. Verificado forzando `MAX_STEPS=1` sobre un problema factible: ahora devuelve `LIMITE_ITERACIONES` en vez de `INVIABLE`.

---

## BAJA

### 6. `SolucionadorSimplex` confunde "RHS negativo" con "inviable" (causa raíz de #1)

**Archivo:** `simplex.py:74-80`

Confirmado: `-x1 <= -5` (es decir, x1≥5) es factible pero el solver devuelve INVIABLE sin intentar resolverlo. `SolucionadorDosFases._normalizar_rhs_negativo` (`dos_fases.py:145-174`) muestra el manejo correcto de este caso (voltea el signo de la fila); `SolucionadorSimplex` carece de ese mecanismo. Severidad baja como hallazgo aislado porque su único impacto alcanzable desde el módulo de PLE es a través del hallazgo #1.

**Estado: ✅ Corregido.** `simplex.py` ahora devuelve `EstadoProblema.REQUIERE_OTRO_METODO` (no `INVIABLE`) cuando detecta RHS negativo, igual que ya hacía para restricciones `>=`/`==`. La UI de PL básica (`vista_matricial.py`) ya renderizaba ese estado con un mensaje amigable de "desajuste de algoritmo", así que el cambio no requirió tocar la UI. Verificado: un modelo `<=` con RHS negativo ahora reporta `REQUIERE_OTRO_METODO` en vez de `INVIABLE`, y un modelo canónico normal sigue resolviendo `OPTIMO` sin cambios.

### 7. B&B con `metodo_lineal=2` heredaría el mismo bug en subproblemas — no alcanzable desde la UI

**Archivo:** `branch_and_bound.py:293-294`

El *variable shifting* de `_construir_subproblema` (líneas 340-349) puede producir filas con RHS negativo incluso si el problema original solo tiene `<=`. Si se invoca `SolucionadorBranchAndBound(metodo_lineal=2)` explícitamente, `_elegir_solver` devolvería `SolucionadorSimplex`, heredando el bug #6 y podando subárboles factibles. Se verificó que la UI nunca dispara este camino: `vista_branch_bound.py` llama a `resolver_PLE(problema, 1)` sin `metodo_lineal`, y el controlador usa la autodetección (líneas 313-319 de `branch_and_bound.py`), que siempre elige `SolucionadorDosFases` — precisamente para evitar este problema (ver el comentario ya presente en el código). Solo alcanzable mediante uso directo de la API con esa opción explícita.

**Estado: ✅ Corregido.** `_resolver_relajacion` ahora reintenta con `SolucionadorDosFases` cuando el solver elegido (incluyendo un `metodo_lineal` explícito) devuelve `REQUIERE_OTRO_METODO`, en vez de podar el nodo como si fuera irresoluble.

### 8. `SELECCION_K_DE_N` implementa "al menos K", la documentación dice "exactamente K"

**Archivo:** `compilador_logica.py:336-358`; docstring en `enums.py:139` ("sum(y_i) == K"); `manual_sintaxis.py` ("número exacto K")

Se fuerzan exactamente K controles `w_i` a 1 (`sum(w)=K`), y cada `w_i=1 ⟹` se cumple la restricción i. Pero las N-K restricciones restantes solo quedan *relajadas* (su `w=0`) — no se prohíbe que también se cumplan por sí solas. El número de restricciones **realmente satisfechas** puede entonces ser mayor que K. El comportamiento real es "al menos K", pedagógicamente aceptable pero distinto de lo que documentan el enum y el manual.

**Estado: ✅ Corregido (documentación).** Se decidió no intentar forzar "exactamente K" (requeriría negar inecuaciones arbitrarias con la misma técnica de red exacta del hallazgo #2, aumentando el riesgo para un beneficio marginal) y en su lugar corregir el docstring de `enums.py` y `manual_sintaxis.py` para que digan explícitamente "al menos K", incluyendo la advertencia de que las N-K restantes pueden cumplirse igual.

### 9. Variable muerta `const_obj` en Enumeración Implícita

**Archivo:** `enumeracion_implicita.py:53`

Confirmado que es código muerto y no un término perdido: `const_obj` se calcula siguiendo la derivación estándar de Balas (desplazamiento de costo) pero nunca se usa. El código recalcula Z directamente desde los coeficientes originales del objetivo en las líneas 103, 144 y 247, usando las variables reconstruidas en el espacio original (`comb_X`/`complete_X`/`best_X`). Se verificó que ese recálculo directo es correcto tanto en MAX como en MIN — la transformación de Balas (C, c_prime, Z_best_Y) solo se usa para dirigir la búsqueda y la poda en el espacio de minimización estandarizado; el valor reportado evalúa el objetivo original en el punto encontrado, así que no se pierde ningún término. Se puede eliminar `const_obj` con seguridad.

**Estado: ✅ Corregido.** Variable eliminada de `enumeracion_implicita.py`.

### 10. No-negatividad de variables `CONTINUA` asumida en todo el sistema, sin documentar

**Archivo:** `branch_and_bound.py:62-64` (L=0 para variables continuas), `resolucion_rapida.py:190-192` (`bounds=(0, None)`), y la forma estándar de los solvers tabulares

No existe soporte para variables continuas libres/negativas — todos los solvers y el *shifting* de B&B asumen `x >= 0`. `TipoVariable.CONTINUA` no tiene ningún campo de cota inferior. Si un modelador pretende que una variable continua tome valores negativos, el resultado es silenciosamente incorrecto. Es una asunción de modelado consistente en todo el proyecto, pero implícita — no está documentada ni se advierte al usuario en la UI o el manual de sintaxis.

**Estado: ✅ Corregido (documentación).** Se agregó la advertencia al docstring de `TipoVariable` (`enums.py`) y a la sección de configuración de variables de `manual_sintaxis.py`. No se cambió el comportamiento (seguiría siendo un cambio de arquitectura mayor soportar variables libres/negativas en los solvers tabulares).

---

## Verificaciones que NO resultaron ser bugs

Se investigaron explícitamente y se descartaron como correctos:

- **Alineación de columnas de holgura entre Simplex y Dos Fases en Planos de Corte** (`planos_corte.py:121-167, 207-231`): se re-derivó que la numeración `S1, S2, …` de `_construir_mapa_holguras` (por orden de restricción, saltando `==`) coincide exactamente con el orden de columnas que produce cada solver tabular, incluso cuando `_elegir_solver` cambia de Simplex a Dos Fases entre una iteración de corte y la siguiente (por ejemplo al aparecer un corte `>=`). También se verificó que la normalización de RHS negativo en Dos Fases (que voltea `<=` a `>=`) preserva la definición algebraica de la variable de holgura, así que el mapeo de vuelta a variables originales sigue siendo correcto.
- **La fórmula del corte de Gomory en sí** (`f_kj = a_kj − floor(a_kj)`, RHS `f_k`, sentido `≥`): estándar y correcta; solo contribuyen columnas no básicas (las básicas tienen entradas enteras/identidad → parte fraccionaria 0 → se omiten correctamente).
- **Poda por cota en B&B con `es_max` y mezcla Fraction/float** (`branch_and_bound.py:156-178`): `is_float` se decide una sola vez al inicio y determina el tipo de todos los cálculos subsecuentes, por lo que `z_real` y `z_optimo` siempre son del mismo tipo — no hay comparaciones mixtas. La poda con `<=`/`>=` estrictos descarta empates pero nunca el valor óptimo real.
- **`NEGACION` como consecuente de un condicional** (`compilador_logica.py:231-241`): correcto — usa un Big-M condicional apropiado (`y=1 ⟹ w1+w2≤1`, relajado cuando `y=0`), a diferencia de la igualdad incondicional del hallazgo #3. (Su uso como *antecedente* sí es problemático, pero es el mismo defecto sistémico del hallazgo #2, no un bug adicional de `NEGACION` en particular.)
- **`historial_de_problemas.py`**: revisado completo — es un wrapper simple de lista en memoria; sin problemas de correctitud, sin implementaciones a medias, sin errores silenciados.
- **Entidades `respuesta.py` / `problema.py`**: no se encontraron discrepancias de tipo entre lo que los solvers realmente pueblan y lo que declaran los dataclasses; los campos nativos adicionales de `RespuestaSciPyPL` son un passthrough intencional de `scipy.optimize.linprog`, no un descuido.

---

## Priorización sugerida (histórico, previo a la corrección)

1. **Corregir #1** (Planos de Corte + RHS negativo) — es el único hallazgo que produce una respuesta incorrecta en un modelo simple, común, sin sintaxis lógica avanzada de por medio. Fix de una línea: aplicar en `planos_corte._elegir_solver` la misma protección que ya existe en `branch_and_bound._elegir_solver`.
2. **Corregir #2 y #3** si el módulo de modelado lógico (`compilador_logica.py`) se considera listo para producción — ambos afectan únicamente a la sintaxis avanzada (`SI...ENTONCES`, `O...O` anidado), no a los tres algoritmos numéricos base.
3. **#4, #5, #8, #9, #10** son mejoras de robustez/documentación de menor urgencia; **#6/#7** quedan resueltos indirectamente si se aplica el fix de #1.

---

## Adendo — bug adicional descubierto durante la verificación de las correcciones (#11)

Al construir una prueba ejecutable para el hallazgo #3 (`(O x1 O x2) O (x3 >= 5)`), la resolución vía Branch and Bound falló con una excepción interna (`ValueError: Inconsistencia en filas básicas`) proveniente de `dos_fases.py`, no de `compilador_logica.py`. Se investigó y es un bug real, independiente, en el solver de Dos Fases.

**Archivo:** `dos_fases.py:284-325` (`_construir_tableau_f2`)

**Descripción:** al terminar la Fase 1, si una variable artificial queda **básica con valor 0** en alguna fila (empate degenerado — común cuando el compilador de M Grande genera muchas restricciones, algunas redundantes entre sí), `_construir_tableau_f2` descartaba **todas** las columnas artificiales sin verificar si alguna seguía siendo básica. Al reindexar `self._base` filtrando esas columnas (`self._mapa_col[col_f1] is None`), la fila correspondiente a esa artificial degenerada desaparecía de la lista, desalineando el resto de `self._base` respecto a las filas reales del tableau — y el constructor de `IteracionTabular` lo detectaba como una inconsistencia estructural y lanzaba una excepción, tumbando la resolución completa.

**Corrección aplicada:** técnica estándar de libro de texto para este caso. Se agregó `_expulsar_artificiales_basicas`, que se ejecuta entre la Fase 1 y la Fase 2: para cada fila cuya variable básica sigue siendo artificial, intenta un pivote degenerado (RHS=0) hacia cualquier columna real/holgura con coeficiente no nulo en esa fila. Si existe, la artificial se expulsa de la base. Si la fila es totalmente redundante (ningún coeficiente no nulo fuera de las columnas artificiales), la artificial se **conserva** como básica; `_construir_tableau_f2` fue ajustado para no descartar una columna artificial que siga en `self._base`, evitando así el desajuste de filas.

**Estado: ✅ Corregido y verificado** — el mismo modelo que producía la excepción ahora resuelve correctamente (`OPTIMO`, Z=2), y los 11 tests end-to-end (incluidos los 11 tests preexistentes de `tests/test_parser_compilador.py`) pasan sin regresiones.

---

## Verificación

Todas las correcciones fueron probadas ejecutando el pipeline real (parser → compilador lógico → solver) contra los contraejemplos concretos de cada hallazgo, más pruebas de no-regresión sobre operadores ya correctos (`CONJUNCION`, `DISYUNCION`, `AND_EVAL`/`OR_EVAL`/`XOR_EVAL`) y sobre el módulo de Programación Lineal básica. La suite preexistente `tests/test_parser_compilador.py` (11 tests) también pasa sin cambios.

---

## Adendo 2 — hallazgos reportados por el usuario (congelamiento de UI, `==` roto, guardado silencioso)

### 12. La vista de Cortes de Gomory podía congelar la interfaz — sin límite de tablas renderizadas

**Archivo:** `ui/programacion_lineal_entera/vista_cortes_gomory.py`

**Descripción:** `_renderizar_paneles_resultados` construía, en una sola pasada síncrona, un `ft.DataTable` completo por cada `IteracionTabular` de `resultado.iteraciones` — sin límite. Cada corte de Gomory vuelve a resolver el LP creciente desde cero (hasta 300 iteraciones de pivoteo en Dos Fases), y pueden ejecutarse hasta `MAX_CORTES=50` cortes: una corrida real puede generar cientos de tablas completas en un único render, saturando tanto la construcción en Python como el árbol de controles enviado al cliente Flet — exactamente la causa del congelamiento reportado.

**Estado: ✅ Corregido con paginación por corte** (confirmado con el usuario). Se agregó el campo `iteraciones_por_corte: List[int]` a `RespuestaPlanoCorte` (`respuesta.py`) para que `planos_corte.py` reporte cuántas iteraciones aporta cada corte. La vista ahora pagina: cada página = un corte completo (o la relajación inicial), con controles Anterior/Siguiente/Primero/Último, y solo construye las tablas de la página actualmente visible — nunca las de todas las páginas a la vez. Como red de seguridad adicional, si un solo corte tuviera un número patológico de pasos (>30), esa página también trunca mostrando los primeros y últimos 15 con una nota, en vez de construir todos. Verificado con un run real de múltiples cortes (2 páginas) y con una página sintética de 75 pasos (se construyen 31 controles en vez de 75).

### 13. `==` en restricciones algebraicas/CSV de PLE se interpretaba siempre como el operador lógico EQUIVALENCIA

**Archivo:** `src/utils/programacion_lineal_entera/parser_sintactico.py:272-297` (antes: rama 8 de `_parse_tokens`)

**Descripción:** Esta es la causa raíz de "el `==` no funciona en programación entera". El tokenizador identifica `==` como un token independiente, y `_parse_tokens` lo interceptaba SIEMPRE como el operador lógico `EQUIVALENCIA` (pensado únicamente para `x1 == x2` entre dos variables binarias sueltas, per manual de sintaxis, Sección 2) — antes de llegar siquiera a intentar `_parse_algebraic_constraint`. Esto rompía cualquier restricción algebraica de igualdad ordinaria:
- `x1 + x2 == 10` → intenta interpretar `"x1 + x2"` como una variable suelta, falla, y lanza una excepción confusa (`No se pudo parsear la expresión: x1 + x2`) sin indicar la causa real.
- `x1 == 10` (una sola variable) → **sin lanzar ningún error**, interpreta el token `"10"` como si fuera la variable **`x10`** (por la regla CSV de índices directos, reutilizada indebidamente aquí), generando una relación lógica sin sentido entre `x1` y una variable fantasma `x10` fuera de rango. Esto coincide exactamente con "da algún resultado sin sentido" reportado.

Se confirmó que esto **no ocurre en Programación Lineal básica** porque ese módulo usa un parser completamente distinto y más simple (`src/utils/programacion_lineal_basica/parser.py`), sin esta sobrecarga de operadores.

**Estado: ✅ Corregido.** `==` solo se interpreta como `EQUIVALENCIA` lógica cuando ambos lados son exactamente una referencia de variable suelta (`xN`, o un índice CSV plano); cualquier otro caso (coeficientes, `+`/`-`, una constante numérica del lado derecho) se trata como restricción algebraica de igualdad ordinaria. Se añadió `_es_token_variable_suelta` para esta detección. Verificado: `x1 + x2 == 10` y `x1 == 5` ahora compilan y resuelven correctamente de extremo a extremo (parser → compilador → Branch and Bound), mientras que `x1 == x2` (la equivalencia lógica real) se sigue reconociendo sin cambios.

### 14. Restricciones CSV planas (sin paréntesis) con coeficientes posicionales se ignoraban en silencio

**Archivo:** `src/utils/programacion_lineal_entera/parser_sintactico.py` (fallback final de `_parse_tokens`)

**Descripción:** Descubierto al corregir el hallazgo #13. El manual de sintaxis CSV y la propia UI (`vista_ingreso_pi.py`, texto de ejemplo del campo de restricciones) muestran `2, 1, <=, 10` como formato válido de nivel superior (sin envolver en paréntesis). Pero `_parse_csv_constraint` — el único código capaz de interpretar coeficientes CSV posicionales — solo se invocaba para el caso de un único token entre paréntesis; una línea CSV plana se tokenizaba en varios tokens (`["2","1","<=","10"]`) y cae en el mismo camino genérico que el modo algebraico, cuyo parser de respaldo busca patrones `"xN"` — que nunca aparecen en CSV. Resultado: la restricción se "parseaba" sin error pero con **todos los coeficientes en cero** (`[0, 0] <= 10`), una restricción vacía que no hace nada, sin ninguna advertencia.

**Estado: ✅ Corregido.** Se extrajo la lógica de `_parse_csv_constraint` a un nuevo método `_construir_restriccion_csv` que opera sobre una lista de tokens ya separados (no solo sobre un string entre paréntesis), y el fallback final de `_parse_tokens` ahora lo usa cuando `is_csv=True` en vez de intentar el parser algebraico basado en regex `xN`. Verificado: `2, 1, <=, 10` ahora produce correctamente `[2, 1] <= 10` en vez de `[0, 0] <= 10`.

### 15. Errores de sintaxis en restricciones PLE no indicaban en qué línea ocurrían

**Archivo:** `src/utils/programacion_lineal_entera/parser_sintactico.py:106-142` (`parse_restricciones`)

**Descripción:** Contribuye a "el botón guardar no da una alerta indicando dónde está el error de sintaxis". El manejador de guardado en la UI (`vista_ingreso_pi.py:manejador_guardar_problema`) sí captura cualquier excepción y la muestra en un snackbar rojo — pero el mensaje de la excepción original no incluía nunca el número de línea ni el texto exacto de la línea que falló (especialmente para errores internos tipo `IndexError`/`KeyError`, que no traen ese contexto por sí solos). Con modelos de varias líneas de restricciones, esto hacía prácticamente imposible ubicar el error.

**Estado: ✅ Corregido.** Cada línea de `texto_res` ahora se parsea dentro de un `try/except` individual en `parse_restricciones`; cualquier excepción se re-lanza envuelta con el número de línea y su contenido exacto (`Error de sintaxis en la línea N ("..."): <causa original>`). Aplica automáticamente tanto al modo algebraico como al CSV, ya que ambos comparten esta misma función. Verificado con una línea deliberadamente malformada.

### 16. *(hallazgo colateral, no reportado por el usuario pero descubierto verificando #8)* Cortes de Gomory nunca aplicaba la cota superior de variables BINARIA

**Archivo:** `src/models/metodos/programacion_lineal_entera/planos_corte.py`

**Descripción:** Al verificar la pregunta del usuario sobre `SELECCION_K_DE_N` ("¿puede cumplir menos de K?"), se comparó Branch and Bound (correcto) contra Cortes de Gomory con el mismo modelo, y se encontró que **Planos de Corte nunca inyecta la restricción `X_j <= 1` para variables BINARIA** (a diferencia de B&B, que sí la aplica vía *variable shifting*). Como la detección de "variable fraccionaria" de este solver solo dispara sobre valores no enteros, un valor entero pero fuera de rango (ej. `X_j = 3` para una variable declarada binaria) pasa completamente inadvertido como "óptimo entero" válido. Contraejemplo mínimo verificado: `MAX x1`, `x1 <= 5`, `x1` BINARIA → Cortes de Gomory devolvía `x1 = 5` en vez de `x1 = 1`. Esto explica la confusión del usuario con `SELECCION_K_DE_N`: el K-of-N en sí está bien implementado (verificado también con Branch and Bound), pero al resolverlo vía Cortes de Gomory, variables "binarias" podían tomar valores muy por fuera de {0,1}, produciendo resultados que parecían violar la regla de K.

**Estado: ✅ Corregido.** `SolucionadorPlanosCorte.resolver` ahora inyecta explícitamente `X_j <= 1` para cada variable `BINARIA` antes de iniciar el ciclo de cortes. Verificado: el contraejemplo mínimo ahora da `x1=1, Z=1`, y el modelo de `SELECCION_K_DE_N` que antes daba una solución no-binaria ahora coincide exactamente con el resultado (correcto) de Branch and Bound.
