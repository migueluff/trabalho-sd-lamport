"""Leitura e validacao do arquivo de cenario (Abordagem B do enunciado).

Formato esperado (JSON):

{
  "nome": "...",
  "descricao": "...",
  "processos": {
    "P1": [
      {"tipo": "EXEC",    "conteudo": "calcula X"},
      {"tipo": "SEND",    "destino": "P2", "conteudo": "m1"},
      {"tipo": "RECEIVE", "origem":  "P3", "conteudo": "m4"}
    ],
    "P2": [...]
  }
}

O campo `conteudo` em um RECEIVE e opcional: quando presente, funciona como
assercao (o simulador falha se chegar outra mensagem), o que ajuda a escrever
cenarios corretos.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List

from .evento import EXEC, RECEIVE, SEND, TIPOS_VALIDOS, indice_do_processo


class CenarioInvalido(ValueError):
    pass


class Cenario:
    def __init__(self, dados: dict, origem: str = "<memoria>") -> None:
        self.origem = origem
        self.nome = dados.get("nome", "cenario sem nome")
        self.descricao = dados.get("descricao", "")
        processos = dados.get("processos")
        if not isinstance(processos, dict) or not processos:
            raise CenarioInvalido("O cenario precisa de um objeto 'processos' nao vazio.")
        self.ids: List[str] = sorted(processos, key=indice_do_processo)
        self.roteiros: Dict[str, List[dict]] = {
            pid: list(processos[pid]) for pid in self.ids
        }
        self._validar()

    

    @classmethod
    def de_arquivo(cls, caminho) -> "Cenario":
        caminho = Path(caminho)
        try:
            dados = json.loads(caminho.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CenarioInvalido(f"JSON invalido em {caminho}: {exc}") from exc
        return cls(dados, origem=str(caminho))


    def _validar(self) -> None:
        for pid, roteiro in self.roteiros.items():
            for i, passo in enumerate(roteiro, start=1):
                if not isinstance(passo, dict) or "tipo" not in passo:
                    raise CenarioInvalido(f"{pid}, passo {i}: falta o campo 'tipo'.")
                tipo = passo["tipo"]
                if tipo not in TIPOS_VALIDOS:
                    raise CenarioInvalido(
                        f"{pid}, passo {i}: tipo {tipo!r} invalido "
                        f"(use {', '.join(TIPOS_VALIDOS)})."
                    )
                if tipo == SEND:
                    self._exigir_campo(passo, "destino", pid, i)
                    if passo["destino"] == pid:
                        raise CenarioInvalido(f"{pid}, passo {i}: SEND para si mesmo.")
                if tipo == RECEIVE:
                    self._exigir_campo(passo, "origem", pid, i)
                    if passo["origem"] == pid:
                        raise CenarioInvalido(f"{pid}, passo {i}: RECEIVE de si mesmo.")
        self._validar_pareamento()

    def _exigir_campo(self, passo: dict, campo: str, pid: str, i: int) -> None:
        valor = passo.get(campo)
        if not valor:
            raise CenarioInvalido(f"{pid}, passo {i}: {passo['tipo']} exige '{campo}'.")
        if valor not in self.roteiros:
            raise CenarioInvalido(
                f"{pid}, passo {i}: processo {valor!r} nao existe no cenario."
            )

    def _validar_pareamento(self) -> None:
        enviados = Counter()
        recebidos = Counter()
        for pid, roteiro in self.roteiros.items():
            for passo in roteiro:
                if passo["tipo"] == SEND:
                    enviados[(pid, passo["destino"])] += 1
                elif passo["tipo"] == RECEIVE:
                    recebidos[(passo["origem"], pid)] += 1
        for par in set(enviados) | set(recebidos):
            origem, destino = par
            if enviados[par] != recebidos[par]:
                raise CenarioInvalido(
                    f"Desbalanceamento em {origem} -> {destino}: "
                    f"{enviados[par]} SEND(s) para {recebidos[par]} RECEIVE(s). "
                    f"Todo SEND precisa de um RECEIVE correspondente."
                )

    @property
    def total_de_eventos(self) -> int:
        return sum(len(r) for r in self.roteiros.values())

    def __repr__(self) -> str:  # pragma: no cover
        return f"Cenario({self.nome!r}, processos={self.ids})"
