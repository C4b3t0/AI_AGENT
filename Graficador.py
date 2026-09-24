"""Graficador de funciones en un plano cartesiano.

Este archivo contiene un programa sencillo para introducir una función
matemática de una variable, evaluarla en muchos puntos y dibujarla usando
la biblioteca Matplotlib.

La mayor parte de los comentarios de este archivo es intencionalmente
extensa: sirven como explicación didáctica de cada paso del programa.
"""

# ``ast`` permite analizar una expresión matemática sin ejecutarla
# directamente como código Python. Esto nos ayuda a controlar qué partes
# de la expresión introducida por el usuario están permitidas.
import ast

# ``operator`` contiene funciones que representan operaciones matemáticas,
# como suma, resta, multiplicación y potencia.
import operator

# Matplotlib se encarga de crear la ventana y dibujar la gráfica.
import matplotlib.pyplot as plt

# NumPy permite trabajar con miles de valores de x simultáneamente y ofrece
# funciones matemáticas que funcionan con arreglos completos.
import numpy as np


# ---------------------------------------------------------------------------
# OPERADORES PERMITIDOS
# ---------------------------------------------------------------------------
#
# Cuando el usuario escribe, por ejemplo, ``x**2 + 3``, Python puede
# representarlo como un árbol sintáctico. Cada tipo de operación del árbol
# tiene una clase dentro del módulo ``ast``.
#
# Este diccionario relaciona cada clase de operación con la función que la
# ejecuta. Al usar una lista explícita, evitamos aceptar instrucciones que no
# sean operaciones matemáticas.
_OPERADORES = {
    # Suma: a + b.
    ast.Add: operator.add,

    # Resta: a - b.
    ast.Sub: operator.sub,

    # Multiplicación: a * b.
    ast.Mult: operator.mul,

    # División: a / b.
    ast.Div: operator.truediv,

    # Potencia: a ** b.
    ast.Pow: operator.pow,

    # Signo negativo: -a.
    ast.USub: operator.neg,

    # Signo positivo: +a.
    ast.UAdd: operator.pos,
}


# ---------------------------------------------------------------------------
# FUNCIONES MATEMÁTICAS DISPONIBLES
# ---------------------------------------------------------------------------
#
# La clave es el nombre que el usuario escribirá. El valor es la función
# NumPy que realmente se utilizará para calcular los resultados.
#
# Por ejemplo, si el usuario escribe ``sin(x)``, el programa buscará ``sin``
# en este diccionario y utilizará ``np.sin``.
_FUNCIONES = {
    # Funciones trigonométricas.
    "sin": np.sin,
    "cos": np.cos,
    "tan": np.tan,

    # Funciones trigonométricas inversas.
    "arcsin": np.arcsin,
    "arccos": np.arccos,
    "arctan": np.arctan,

    # Otras funciones matemáticas comunes.
    "sqrt": np.sqrt,
    "abs": np.abs,
    "exp": np.exp,
    "log": np.log,
    "log10": np.log10,
}


# ---------------------------------------------------------------------------
# EVALUACIÓN CONTROLADA DE LA EXPRESIÓN
# ---------------------------------------------------------------------------
def _evaluar_nodo(nodo, x):
    """Evalúa recursivamente un nodo del árbol de la expresión.

    ``nodo`` es una parte de la expresión matemática y ``x`` puede ser un
    número individual o un arreglo de NumPy. La función recorre el árbol,
    reconoce únicamente elementos permitidos y devuelve el resultado.

    No se utiliza ``eval``. Esto es importante porque ``eval`` podría
    ejecutar instrucciones arbitrarias introducidas por el usuario.
    """

    # ``ast.Expression`` es el nodo inicial creado al analizar una expresión
    # completa con ``ast.parse(..., mode="eval")``. Su contenido real está
    # guardado en ``body``, por lo que continuamos evaluando ese contenido.
    if isinstance(nodo, ast.Expression):
        return _evaluar_nodo(nodo.body, x)

    # Las constantes numéricas pueden ser enteros o números decimales.
    # Cualquier otro tipo de constante se rechaza.
    if isinstance(nodo, ast.Constant) and isinstance(nodo.value, (int, float)):
        return nodo.value

    # Un nodo ``Name`` representa un nombre, como x, pi o e.
    if isinstance(nodo, ast.Name):
        # ``x`` es la variable independiente de la función.
        if nodo.id == "x":
            return x

        # También permitimos las constantes matemáticas pi y e.
        if nodo.id == "pi":
            return np.pi
        if nodo.id == "e":
            return np.e

        # Cualquier otro nombre no está autorizado.
        raise ValueError(f"Nombre no permitido: {nodo.id}")

    # Un ``UnaryOp`` representa una operación con un solo operando, por
    # ejemplo -x o +x. Primero confirmamos que el operador sea permitido.
    if isinstance(nodo, ast.UnaryOp) and type(nodo.op) in _OPERADORES:
        # Evaluamos el valor sobre el que se aplica el signo y luego usamos
        # la operación correspondiente del diccionario.
        valor = _evaluar_nodo(nodo.operand, x)
        return _OPERADORES[type(nodo.op)](valor)

    # Un ``BinOp`` representa operaciones con dos valores, por ejemplo
    # x + 2, x * x o x**2.
    if isinstance(nodo, ast.BinOp) and type(nodo.op) in _OPERADORES:
        # Evaluamos primero la parte izquierda de la operación.
        izquierda = _evaluar_nodo(nodo.left, x)

        # Después evaluamos la parte derecha de la operación.
        derecha = _evaluar_nodo(nodo.right, x)

        # Finalmente aplicamos el operador correspondiente.
        return _OPERADORES[type(nodo.op)](izquierda, derecha)

    # Un ``Call`` representa una llamada a una función, como sin(x).
    if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
        # Solo aceptamos funciones incluidas en nuestro diccionario, con un
        # único argumento posicional y sin argumentos nombrados.
        if nodo.func.id not in _FUNCIONES or len(nodo.args) != 1 or nodo.keywords:
            raise ValueError("Función no permitida o argumentos inválidos")

        # Evaluamos el argumento de la función y luego llamamos a la función
        # matemática autorizada.
        argumento = _evaluar_nodo(nodo.args[0], x)
        return _FUNCIONES[nodo.func.id](argumento)

    # Si el nodo no coincidió con ninguna opción anterior, significa que la
    # expresión contiene una estructura no contemplada por el graficador.
    raise ValueError("La expresión contiene elementos no permitidos")


# ---------------------------------------------------------------------------
# CONVERSIÓN DE TEXTO A FUNCIÓN
# ---------------------------------------------------------------------------
def crear_funcion(expresion):
    """Convierte texto matemático en una función que recibe valores de x.

    Un ejemplo de entrada sería ``x**2 + sin(x)``. También se acepta ``^``
    como símbolo de potencia para facilitar la escritura, convirtiéndolo
    internamente a ``**``, que es la sintaxis de Python.
    """

    # En algunos contextos se escribe x^2 para indicar una potencia. En
    # Python, la potencia se escribe x**2, así que hacemos esta conversión.
    expresion = expresion.replace("^", "**")

    # Convertimos el texto en un árbol sintáctico. Si hay un error de sintaxis
    # (por ejemplo, paréntesis incompletos), ast.parse generará una excepción.
    arbol = ast.parse(expresion, mode="eval")

    # Esta función interna conserva el árbol ya analizado. Cada vez que se
    # llame con un arreglo de x, evaluará la expresión completa.
    def funcion(x):
        return _evaluar_nodo(arbol, x)

    # Devolvemos la función lista para usarse en ``main``.
    return funcion


# ---------------------------------------------------------------------------
# FUNCIÓN PRINCIPAL DEL PROGRAMA
# ---------------------------------------------------------------------------
def main():
    """Permite graficar varias funciones en la misma ventana.

    La ventana se crea una sola vez y cada nueva expresión se añade al eje
    existente. Así el usuario puede reescribir la fórmula sin cerrar el
    programa ni perder las funciones ya dibujadas.
    """

    print("Graficador de funciones f(x)")
    print("Ejemplos: x**2, sin(x), 2*x + 5, sqrt(abs(x))")
    print("Escribe 'limpiar' para borrar las curvas o 'salir' para terminar.")

    x = np.linspace(-10, 10, 2001)
    figura, eje = plt.subplots(figsize=(11, 11))

    # Configuramos el plano una sola vez.
    eje.set_xlim(-10, 10)
    eje.set_ylim(-10, 10)
    eje.set_aspect("equal", adjustable="box")
    eje.set_xlabel("x")
    eje.set_ylabel("y")
    eje.set_title("Plano cartesiano — escala 1:10")
    eje.set_xticks(np.arange(-10, 11, 1))
    eje.set_yticks(np.arange(-10, 11, 1))
    eje.grid(True, which="major", alpha=0.18, linewidth=0.4)
    eje.axhline(0, color="black", linewidth=1)
    eje.axvline(0, color="black", linewidth=1)
    figura.tight_layout()

    # La ventana no bloquea el input: permanece abierta mientras se
    # introducen nuevas expresiones.
    plt.show(block=False)

    while plt.fignum_exists(figura.number):
        expresion = input("Introduce f(x) (o 'salir'): ").strip()

        if expresion.lower() in {"salir", "exit", "q"}:
            break

        if expresion.lower() in {"limpiar", "clear"}:
            # Conserva las dos líneas de los ejes y elimina las curvas.
            for linea in list(eje.lines)[2:]:
                linea.remove()
            if eje.legend_:
                eje.legend_.remove()
            figura.canvas.draw_idle()
            plt.pause(0.01)
            print("Gráfica limpiada.")
            continue

        if not expresion:
            print("Introduce una expresión.")
            continue

        try:
            funcion = crear_funcion(expresion)
            with np.errstate(all="ignore"):
                y = np.asarray(funcion(x), dtype=float)

            if y.ndim == 0:
                y = np.full_like(x, y, dtype=float)
            if y.shape != x.shape:
                raise ValueError("La función no produjo un valor para cada x")

            y = np.where(np.isfinite(y), y, np.nan)
            eje.plot(x, y, linewidth=1.2, label=f"f(x) = {expresion}")
            eje.legend()
            figura.canvas.draw_idle()
            plt.pause(0.01)
            print(f"Añadida: f(x) = {expresion}")

        except (SyntaxError, ValueError, TypeError, ZeroDivisionError) as error:
            print(f"Expresión inválida: {error}")

    plt.close(figura)
    print("Programa terminado.")


# Este condicional permite importar el archivo sin ejecutar inmediatamente la
# gráfica. ``main`` solo se ejecutará cuando este archivo se lance directamente
# con Python, por ejemplo: python Graficador.py.
if __name__ == "__main__":
    main()
