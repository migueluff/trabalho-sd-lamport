
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Dict, List

from .evento import Mensagem


class ErroDeEntrega(RuntimeError):
    """Cenario mal formado: um RECEIVE que nunca encontra o SEND correspondente."""


class CaixaDeEntrada:
    def __init__(self, dono: str) -> None:
        self.dono = dono
        self._filas: Dict[str, deque] = defaultdict(deque)
        self._cond = threading.Condition()

    def entregar(self, msg: Mensagem) -> None:
        with self._cond:
            self._filas[msg.origem].append(msg)
            self._cond.notify_all()

    def retirar(self, origem: str, timeout: float) -> Mensagem:
        limite = time.monotonic() + timeout
        with self._cond:
            while not self._filas[origem]:
                restante = limite - time.monotonic()
                if restante <= 0:
                    raise ErroDeEntrega(
                        f"{self.dono} esperou {timeout:.1f}s por uma mensagem de "
                        f"{origem} e nada chegou. Verifique se o cenario tem um "
                        f"SEND de {origem} para {self.dono} correspondente a este "
                        f"RECEIVE."
                    )
                self._cond.wait(restante)
            return self._filas[origem].popleft()

    def pendentes(self) -> List[Mensagem]:
        with self._cond:
            return [m for fila in self._filas.values() for m in fila]


class Rede:

    def __init__(self, ids) -> None:
        self.caixas = {pid: CaixaDeEntrada(pid) for pid in ids}

    def enviar(self, msg: Mensagem) -> None:
        if msg.destino not in self.caixas:
            raise ErroDeEntrega(f"Destino desconhecido: {msg.destino}")
        self.caixas[msg.destino].entregar(msg)

    def caixa(self, pid: str) -> CaixaDeEntrada:
        return self.caixas[pid]

    def mensagens_nao_consumidas(self) -> List[Mensagem]:
        return [m for c in self.caixas.values() for m in c.pendentes()]
