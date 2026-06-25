# src/models/metodos/programacion_no_lineal/historial_de_problemas.py

from __future__ import annotations
from typing import List, Optional

from src.models.entity.programacion_no_lineal.problema import ProblemaNoLineal


class HistorialProblemasNL:
    """Gestor en memoria de los problemas no lineales guardados en la sesión."""

    def __init__(self) -> None:
        self._problemas: List[ProblemaNoLineal] = []

    def guardar(self, problema: ProblemaNoLineal) -> None:
        self._problemas.append(problema)

    def obtener_todos(self) -> List[ProblemaNoLineal]:
        return list(self._problemas)

    def obtener_por_indice(self, indice: int) -> Optional[ProblemaNoLineal]:
        if 0 <= indice < len(self._problemas):
            return self._problemas[indice]
        return None

    def eliminar_por_indice(self, indice: int) -> None:
        if 0 <= indice < len(self._problemas):
            self._problemas.pop(indice)

    def esta_vacio(self) -> bool:
        return len(self._problemas) == 0
