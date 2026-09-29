"""Representacao de eventos e mensagens, e a ordem total exigida no requisito 3."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Optional

EXEC = "EXEC"
SEND = "SEND"
RECEIVE = "RECEIVE"
TIPOS_VALIDOS = (EXEC, SEND, RECEIVE)


def indice_do_processo(pid: str) -> tuple:
    m = re.search(r"\d+", pid)
    if m:
        return (0, int(m.group()), pid)
    return (1, 0, pid)


@dataclass(frozen=True)
class Mensagem:

    origem: str
    destino: str
    conteudo: str
    timestamp: int


@dataclass
class Evento:
    """Um evento registrado no log de um processo.

    `relogio` e o valor de L_i JA atualizado, ou seja, o valor com que o evento
    e carimbado -- e nao o valor anterior a ele.
    """

    processo: str
    tipo: str
    relogio: int
    detalhes: str
    ordem_local: int                      
    peer: Optional[str] = None             # destino (SEND) ou origem (RECEIVE)
    conteudo: Optional[str] = None
    timestamp_recebido: Optional[int] = None   

    def formatar(self) -> str:
        return (
            f"[Processo {self.processo}] Evento: {self.tipo} | "
            f"Relógio Lógico: {self.relogio} | Detalhes: {self.detalhes}"
        )

    @property
    def chave_ordem_total(self) -> tuple:
        return (self.relogio, indice_do_processo(self.processo), self.ordem_local)

    @property
    def rotulo(self) -> str:
        """Identificador curto do evento, usado no diagrama e no log."""
        return f"{self.processo}.e{self.ordem_local}"


def ordenar_total(eventos) -> list:
    """Requisito 3: lista unificada ordenada por (L, ID do processo)."""
    return sorted(eventos, key=lambda e: e.chave_ordem_total)
