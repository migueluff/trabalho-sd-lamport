from __future__ import annotations

import random
import threading
from typing import Dict, List, Optional

from .canal import Rede
from .evento import EXEC, RECEIVE, SEND, Evento, Mensagem
from .registrador import Registrador
from .relogio import RelogioLamport


class Processo(threading.Thread):
    def __init__(
        self,
        pid: str,
        roteiro: List[dict],
        rede: Rede,
        registrador: Registrador,
        timeout: float = 10.0,
        jitter: float = 0.03,
        semente: Optional[int] = None,
    ) -> None:
        super().__init__(name=pid, daemon=True)
        self.pid = pid
        self.roteiro = roteiro
        self.rede = rede
        self.registrador = registrador
        self.relogio = RelogioLamport()
        self.timeout = timeout
        self.jitter = jitter
        self._rng = random.Random(semente)
        self._ordem_local = 0
        self.erro: Optional[BaseException] = None

    #

    def _proxima_ordem(self) -> int:
        self._ordem_local += 1
        return self._ordem_local

    def _esperar_um_pouco(self) -> None:
        if self.jitter > 0:
            threading.Event().wait(self._rng.uniform(0, self.jitter))

    

    def executar_interno(self, descricao: str) -> Evento:
        l = self.relogio.tick()
        evento = Evento(
            processo=self.pid,
            tipo=EXEC,
            relogio=l,
            detalhes=descricao,
            ordem_local=self._proxima_ordem(),
            conteudo=descricao,
        )
        self.registrador.registrar(evento)
        return evento

    def enviar(self, destino: str, conteudo: str) -> Evento:
        l = self.relogio.tick()
        msg = Mensagem(
            origem=self.pid, destino=destino, conteudo=conteudo,
            timestamp=l,
        )
        evento = Evento(
            processo=self.pid,
            tipo=SEND,
            relogio=l,
            detalhes=f"Enviou para {destino} -> '{conteudo}' (timestamp={l})",
            ordem_local=self._proxima_ordem(),
            peer=destino,
            conteudo=conteudo,
        )
        self.registrador.registrar(evento)
        self.rede.enviar(msg)
        return evento

    def receber(self, origem: str, conteudo_esperado: Optional[str] = None) -> Evento:
        """RECEIVE -- regra 3: L_i = max(L_i, timestamp) + 1."""
        msg = self.rede.caixa(self.pid).retirar(origem, timeout=self.timeout)
        if conteudo_esperado is not None and msg.conteudo != conteudo_esperado:
            raise AssertionError(
                f"{self.pid} esperava receber '{conteudo_esperado}' de {origem}, "
                f"mas chegou '{msg.conteudo}'"
            )
        anterior = self.relogio.valor
        l = self.relogio.receber(msg.timestamp)
        evento = Evento(
            processo=self.pid,
            tipo=RECEIVE,
            relogio=l,
            detalhes=(
                f"Recebeu de {origem} -> '{msg.conteudo}' | "
                f"max(L={anterior}, ts={msg.timestamp}) + 1 = {l}"
            ),
            ordem_local=self._proxima_ordem(),
            peer=origem,
            conteudo=msg.conteudo,
            timestamp_recebido=msg.timestamp,
        )
        self.registrador.registrar(evento)
        return evento


    def run(self) -> None:
        try:
            for passo in self.roteiro:
                self._esperar_um_pouco()
                tipo = passo["tipo"]
                if tipo == EXEC:
                    self.executar_interno(passo.get("conteudo", "evento interno"))
                elif tipo == SEND:
                    self.enviar(passo["destino"], passo.get("conteudo", ""))
                elif tipo == RECEIVE:
                    self.receber(passo["origem"], passo.get("conteudo"))
                else: 
                    raise ValueError(f"Tipo de evento desconhecido: {tipo}")
        except BaseException as exc:
            self.erro = exc

    def estado(self) -> Dict[str, object]:
        return {"processo": self.pid, "relogio_final": self.relogio.valor}
