"""Relogios logicos.

Este modulo concentra as tres regras do algoritmo de Lamport. Nada mais no
projeto mexe no valor do relogio diretamente -- tudo passa por aqui, para que a
corretude da logica possa ser auditada num unico lugar.

A verificacao da relacao aconteceu-antes nao mora aqui: ela e feita por um
script separado, que le o log de saida e reconstroi a causalidade a partir dele.
"""

from __future__ import annotations

import threading


class RelogioLamport:
    """Contador inteiro L_i de um processo, com acesso protegido por lock.

    O lock e necessario porque cada processo roda em sua propria thread e o
    valor do relogio e lido pelo registrador de log.
    """

    def __init__(self, valor_inicial: int = 0) -> None:
        self._valor = valor_inicial
        self._lock = threading.Lock()

    @property
    def valor(self) -> int:
        with self._lock:
            return self._valor

    def tick(self) -> int:
  
        with self._lock:
            self._valor += 1
            return self._valor

    def receber(self, timestamp: int) -> int:
        with self._lock:
            self._valor = max(self._valor, timestamp) + 1
            return self._valor

    def __repr__(self) -> str:  # pragma: no cover - conveniencia de debug
        return f"RelogioLamport({self.valor})"
