"""Orquestrador da simulacao: cria as threads, espera o fim e coleta o log."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .canal import Rede
from .cenario import Cenario
from .evento import Evento
from .processo import Processo
from .registrador import Registrador


@dataclass
class Resultado:
    cenario: Cenario
    eventos_em_tempo_real: List[Evento]   
    ordem_total: List[Evento]             
    estados_finais: List[Dict[str, object]]

    @property
    def ids(self) -> List[str]:
        return self.cenario.ids


class FalhaNaSimulacao(RuntimeError):
    pass


def simular(
    cenario: Cenario,
    jitter: float = 0.0,
    semente: Optional[int] = None,
    timeout: float = 10.0,
    ecoar: bool = True,
    saida=None,
) -> Resultado:
    rede = Rede(cenario.ids)
    registrador = Registrador(ecoar=ecoar, saida=saida)

    processos = [
        Processo(
            pid=pid,
            roteiro=cenario.roteiros[pid],
            rede=rede,
            registrador=registrador,
            timeout=timeout,
            jitter=jitter,
            semente=None if semente is None else semente + i,
        )
        for i, pid in enumerate(cenario.ids)
    ]

    for p in processos:
        p.start()

    for p in processos:
        p.join(timeout=timeout + 5.0)

    vivos = [p.pid for p in processos if p.is_alive()]
    if vivos:
        raise FalhaNaSimulacao(f"Processos que nao terminaram: {', '.join(vivos)}")

    for p in processos:
        if p.erro is not None:
            raise FalhaNaSimulacao(f"Falha em {p.pid}: {p.erro}") from p.erro

    sobras = rede.mensagens_nao_consumidas()
    if sobras:
        descr = ", ".join(f"{m.origem}->{m.destino}:'{m.conteudo}'" for m in sobras)
        raise FalhaNaSimulacao(f"Mensagens enviadas e nunca recebidas: {descr}")

    return Resultado(
        cenario=cenario,
        eventos_em_tempo_real=registrador.eventos,
        ordem_total=registrador.ordem_total(),
        estados_finais=[p.estado() for p in processos],
    )
