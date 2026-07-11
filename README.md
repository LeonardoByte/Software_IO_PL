# Optimizador Lineal - Investigación de Operaciones

Software interactivo desarrollado en Python para la resolución y análisis de problemas de Programación Lineal, Programación Lineal Entera/Mixta y Programación No Lineal. El proyecto está enfocado en proporcionar tanto la solución matemática óptima como el desglose procedimental de los algoritmos clásicos de optimización, diseñado específicamente como herramienta de apoyo para el estudio de Investigación de Operaciones.

## Características Principales

La aplicación cuenta con una interfaz gráfica (GUI) organizada en 3 grandes módulos, cada uno con varios sub-módulos:

### 1. Programación Lineal

1. **Solución Directa (Solver General):** Resolución rápida basada en SciPy que omite el paso a paso matricial y entrega el resultado final instantáneamente.
2. **Método Gráfico Interactivo:** Permite resolver problemas de 2 variables. Incluye un plano cartesiano donde la función objetivo y las restricciones son visibles.
3. **Método Simplex (Paso a Paso):** Resolución tabular con aritmética exacta (fracciones) que muestra cada iteración (tableau) hasta alcanzar la solución óptima, ideal para el seguimiento académico del algoritmo.
4. **Método de la M Grande:** Extensión del método tabular para problemas que requieren variables artificiales, mostrando el impacto de la penalización $M$ en cada matriz.
5. **Método de las Dos Fases:** Desglose del problema en la Fase I (minimización de variables artificiales) y Fase II (optimización de la función objetivo original), con sus respectivas tablas.

### 2. Programación Lineal Entera y Mixta (PLE / MILP)

1. **Branch and Bound:** Ramificación y acotamiento sobre relajaciones lineales continuas, con soporte para variables enteras, binarias y mixtas.
2. **Planos de Corte (Cortes de Gomory):** Refinamiento sucesivo de la región factible mediante cortes fraccionarios.
3. **Enumeración Implícita (Algoritmo de Balas):** Especializado en problemas de variables puramente binarias.
4. **Modelado Lógico:** Un compilador propio traduce reglas lógicas en lenguaje natural (NOT, Y, O, exclusión mutua, implicación, equivalencia) y restricciones tipo Big-M a un modelo `ProblemaPLE` estándar antes de resolverlo.

### 3. Programación No Lineal

1. **Método de la Sección Áurea:** Búsqueda unidimensional para optimización de funciones de una variable.
2. **Método de Newton:** Optimización basada en derivadas para funciones de una variable.
3. **Método del Gradiente:** Optimización multivariable mediante descenso/ascenso de gradiente.
4. **Condiciones KKT:** Análisis de puntos óptimos sujetos a restricciones mediante las condiciones de Karush-Kuhn-Tucker (apoyado en SciPy).

Cada familia de métodos conserva su propio historial de problemas resueltos dentro de la sesión.

## Arquitectura del Software

El proyecto está estructurado bajo el patrón de diseño **Modelo-Vista-Controlador (MVC)**, con un Controlador Principal que actúa como Fachada sobre tres sub-controladores especializados (uno por familia de algoritmos):

* **Modelos (`src/models/`):** Contiene la lógica pura de Python (sin dependencias de interfaz gráfica), separada en:
  * `entity/`: Entidades de dominio inmutables (problemas y respuestas) por familia de algoritmo.
  * `metodos/`: Los solucionadores matemáticos (pivoteos de matrices, ramificación, gradientes, etc.).
* **Utilidades (`src/utils/`):** Parsers de texto a modelos matemáticos, compilador de lógica booleana, graficador y herramientas de cálculo auxiliares.
* **Controladores (`src/controller/`):** `ControladorPrincipal` actúa como fachada, delegando en `ControladorLineal`, `ControladorEntera` y `ControladorNoLineal`. Capturan los datos ingresados por el usuario, los envían a los modelos matemáticos, y posteriormente devuelven los resultados numéricos a las vistas.
* **Vistas (`ui/`):** Desarrolladas íntegramente con Flet para garantizar facilidad de uso y resultados visuales modernos. Por su naturaleza multiplataforma, el mismo código permite ejecutar la aplicación de forma nativa en escritorio, navegadores web o dispositivos móviles. Cada familia de algoritmos tiene su propio navegador (enrutador) y conjunto de vistas.

## Tecnologías Utilizadas

* **Lenguaje:** Python 3.x
* **Interfaz Gráfica:** Flet 0.85.0
* **Gráficos:** Matplotlib
* **Cálculo Numérico y Solución Directa:** NumPy, SciPy

## Instalación y Ejecución

1. Clonar el repositorio.
```bash
   git clone https://github.com/LeonardoByte/Software_IO_PL
   cd Software_IO_PL
```

2. Se recomienda crear y activar un entorno virtual (`.venv`):
```bash
   python -m venv .venv
   # En Windows:
   .venv\Scripts\activate
   # En Linux/macOS:
   source .venv/bin/activate
   ```

3. Instalar dependencias: Con el entorno virtual activado, instale todos los paquetes necesarios definidos en el archivo requirements.txt:
```bash
   pip install -r requirements.txt
```
4. Ejecutar la aplicación: Inicie el programa ejecutando el archivo principal (asegúrese de estar en la raíz del proyecto):
```bash
   python main.py
```
