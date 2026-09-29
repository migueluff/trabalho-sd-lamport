"""Registrador de log compartilhado pelas threads."""

from __future__ import annotations

import sys
import threading
from typing import List

from .evento import Evento, ordenar_total


class Registrador:


    def __init__(self, ecoar: bool = True, saida=None) -> None:
        self._eventos: List[Evento] = []
        self._lock = threading.Lock()
        self._ecoar = ecoar
        self._saida = saida or sys.stdout

    def registrar(self, evento: Evento) -> None:
        with self._lock:
            self._eventos.append(evento)
            if self._ecoar:
                print(evento.formatar(), file=self._saida, flush=True)

    @property
    def eventos(self) -> List[Evento]:
        with self._lock:
            return list(self._eventos)

    def ordem_total(self) -> List[Evento]:

        return ordenar_total(self.eventos)
