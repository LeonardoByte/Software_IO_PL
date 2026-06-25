"""
Implementa el Patrón Fachada para orquestar los distintos
sub-controladores matemáticos del ecosistema
"""

from src.controller.controlador_lineal import ControladorLineal
from src.controller.controlador_entera import ControladorEntera
from src.controller.controlador_no_lineal import ControladorNoLineal

class ControladorPrincipal:
    """
    Punto de entrada único para la gestión del dominio.
    Instancia y expone los sub-controladores especializados.
    """
    def __init__(self) -> None:
        self.lineal:     ControladorLineal    = ControladorLineal()
        self.entera:     ControladorEntera    = ControladorEntera()
        self.no_lineal:  ControladorNoLineal  = ControladorNoLineal()