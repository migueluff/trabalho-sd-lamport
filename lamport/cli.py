"""Interface de linha de comando.

Uso tipico:
    python -m lamport cenarios/cenario1_basico.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .cenario import Cenario, CenarioInvalido
from .diagrama import gerar_ascii, salvar_svg
from .simulador import FalhaNaSimulacao, simular


def formatar_ordem_total(eventos: Sequence[Evento]) -> str:
    linhas = []
    add = linhas.append
    add("=" * 78)
    add("ORDEM TOTAL DE EVENTOS")
    add("=" * 78)
    add(f"{'#':>3}  {'L':>3}  {'Processo':<9} {'Tipo':<8} Detalhes")
    add("-" * 78)
    for i, e in enumerate(sorted(eventos, key=lambda x: x.chave_ordem_total), 1):
        add(f"{i:>3}  {e.relogio:>3}  {e.processo:<9} {e.tipo:<8} {e.detalhes}")
    add("")
    return "\n".join(linhas)


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m lamport",
        description="Simulador dos Relógios Lógicos de Lamport.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Exemplos:\n"
            "  python -m lamport cenarios/cenario1_basico.json\n"
            "  python -m lamport cenarios/cenario1_basico.json --jitter 0.05 "
            "--semente 7 --diagrama saida/diagrama.svg\n"
        ),
    )
    p.add_argument("cenario", type=Path, help="arquivo JSON com o cenario")
    p.add_argument("--diagrama", type=Path, metavar="ARQ.svg",
                   help="gera o diagrama espaco-tempo em SVG")
    p.add_argument("--ascii", action="store_true",
                   help="imprime uma versao textual do diagrama no terminal")
    p.add_argument("--saida", type=Path, metavar="ARQ.txt",
                   help="alem de imprimir, salva o relatorio completo em arquivo")
    p.add_argument("--jitter", type=float, default=0.0, metavar="SEG",
                   help="atraso aleatorio maximo entre eventos de um processo, "
                        "para embaralhar o interleaving das threads (padrao: 0)")
    p.add_argument("--semente", type=int, default=None,
                   help="semente do gerador aleatorio, para reproduzir um jitter")
    p.add_argument("--timeout", type=float, default=10.0, metavar="SEG",
                   help="tempo maximo que um RECEIVE espera por uma mensagem")
    p.add_argument("--silencioso", action="store_true",
                   help="omite o log em tempo real; mostra so o resultado final")
    return p


def main(argv=None) -> int:
    args = construir_parser().parse_args(argv)

    try:
        cenario = Cenario.de_arquivo(args.cenario)
    except (CenarioInvalido, OSError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2

    partes = []

    cabecalho = (
        "=" * 78 + "\n"
        f"CENÁRIO: {cenario.nome}\n"
        + (f"{cenario.descricao}\n" if cenario.descricao else "")
        + f"Processos: {', '.join(cenario.ids)} | "
          f"Eventos programados: {cenario.total_de_eventos}\n"
        + "=" * 78 + "\n"
    )
    print(cabecalho)
    partes.append(cabecalho)

    if not args.silencioso:
        titulo = "LOG\n" + "-" * 78
        print(titulo)
        partes.append(titulo)

    try:
        resultado = simular(
            cenario,
            jitter=args.jitter,
            semente=args.semente,
            timeout=args.timeout,
            ecoar=not args.silencioso,
        )
    except FalhaNaSimulacao as exc:
        print(f"\nerro: {exc}", file=sys.stderr)
        return 1

    if not args.silencioso:
        for e in resultado.eventos_em_tempo_real:
            partes.append(e.formatar())
        partes.append("")
        print()

    ordem = formatar_ordem_total(resultado.ordem_total)
    print(ordem)
    partes.append(ordem)

    estados = ["RELÓGIOS FINAIS: " + " | ".join(
        f"{s['processo']}: L={s['relogio_final']}" for s in resultado.estados_finais), ""]
    print("\n".join(estados))
    partes.extend(estados)

    if args.ascii:
        txt = gerar_ascii(resultado.ordem_total, resultado.ids)
        print(txt)
        partes.append(txt)


    if args.diagrama:
        caminho = salvar_svg(
            args.diagrama, resultado.ordem_total, resultado.ids,
            titulo=f"Diagrama espaço-tempo — {cenario.nome}",
        )
        print(f"Diagrama salvo em: {caminho}\n")

    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text("\n".join(partes) + "\n", encoding="utf-8")
        print(f"Relatório salvo em: {args.saida}")

    return 0
