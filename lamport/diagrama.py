"""Gera o diagrama espaco-tempo do cenario executado, em SVG puro.

Sem dependencias externas: o SVG e montado como texto. O eixo horizontal e o
TEMPO LOGICO (valor de L), nao o tempo fisico -- por isso toda seta de mensagem
aponta para a direita, que e a leitura visual do teorema a -> b => L(a) < L(b).
"""

from __future__ import annotations

import math
from typing import Dict, List, Sequence

from .evento import RECEIVE, SEND, Evento, indice_do_processo

CORES = {
    "EXEC": "#6b7280",
    "SEND": "#2563eb",
    "RECEIVE": "#059669",
}


def _escapar(texto: str) -> str:
    return (texto.replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))


def _largura_texto(texto: str, tamanho: float, negrito: bool = False) -> float:
    """Estimativa da largura de um texto, em px.

    Nao da para medir uma fonte sem renderiza-la, entao usamos a largura media
    de caractere da DejaVu Sans. Superestimar so deixa o SVG um pouco mais
    largo; subestimar corta o texto -- que e exatamente o defeito que isto
    corrige.
    """
    return len(texto) * tamanho * (0.62 if negrito else 0.56)


def _parear_mensagens(eventos: Sequence[Evento]) -> List[tuple]:
    """Casa cada SEND com o RECEIVE correspondente, em FIFO por (origem, destino).

    Usa a mesma regra de pareamento do canal, entao o desenho reflete exatamente
    o que aconteceu na execucao.
    """
    envios: Dict[tuple, List[Evento]] = {}
    for e in sorted(eventos, key=lambda x: (indice_do_processo(x.processo), x.ordem_local)):
        if e.tipo == SEND:
            envios.setdefault((e.processo, e.peer), []).append(e)

    pares = []
    for e in sorted(eventos, key=lambda x: x.chave_ordem_total):
        if e.tipo == RECEIVE:
            fila = envios.get((e.peer, e.processo), [])
            if fila:
                pares.append((fila.pop(0), e))
    return pares


def gerar_svg(eventos: Sequence[Evento], ids: Sequence[str], titulo: str = "") -> str:
    eventos = list(eventos)
    if not eventos:
        raise ValueError("Nao ha eventos para desenhar.")

    max_l = max(e.relogio for e in eventos)
    margem_esq, margem_dir = 120, 60
    margem_base = 78
    passo_x = 78
    passo_y = 110

    # Cabecalho: titulo (opcional) + legenda em duas linhas. Sao duas linhas,
    # e nao uma, para que o texto nao force um SVG largo em cenarios curtos.
    subtitulo = (
        "Eixo horizontal: tempo lógico (valor do relógio de Lamport).",
        "Toda seta aponta para a direita: a → b implica L(a) < L(b).",
    )
    y_titulo = 34
    y_legenda = [(y_titulo + 24 if titulo else 26) + 15 * i
                 for i in range(len(subtitulo))]
    # A regua de L comeca abaixo da ultima linha do cabecalho, com folga.
    margem_topo = y_legenda[-1] + 50

    # A largura precisa caber a linha do tempo E o cabecalho. Em cenarios
    # curtos quem manda e o texto; sem isso, o titulo sai cortado.
    larguras_de_texto = [_largura_texto(linha, 11) for linha in subtitulo]
    if titulo:
        larguras_de_texto.append(_largura_texto(titulo, 16, negrito=True))
    largura = math.ceil(max(
        margem_esq + max_l * passo_x + margem_dir,
        margem_esq + max(larguras_de_texto) + margem_dir,
    ))
    altura = margem_topo + (len(ids) - 1) * passo_y + margem_base

    def x(l: int) -> float:
        return margem_esq + l * passo_x

    def y(pid: str) -> float:
        return margem_topo + list(ids).index(pid) * passo_y

    s: List[str] = []
    add = s.append
    add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{largura}" '
        f'height="{altura}" viewBox="0 0 {largura} {altura}" '
        f'font-family="DejaVu Sans, Helvetica, Arial, sans-serif">')
    add('<defs>'
        '<marker id="seta" viewBox="0 0 10 10" refX="9" refY="5" '
        'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#b45309"/></marker></defs>')
    add(f'<rect width="{largura}" height="{altura}" fill="#ffffff"/>')

    if titulo:
        add(f'<text x="{margem_esq}" y="{y_titulo}" font-size="16" '
            f'font-weight="600" fill="#111827">{_escapar(titulo)}</text>')
    for linha, yy in zip(subtitulo, y_legenda):
        add(f'<text x="{margem_esq}" y="{yy}" font-size="11" fill="#6b7280">'
            f'{_escapar(linha)}</text>')

    # Grade vertical com os valores de L
    for l in range(1, max_l + 1):
        add(f'<line x1="{x(l)}" y1="{margem_topo - 26}" x2="{x(l)}" '
            f'y2="{altura - margem_base + 34}" stroke="#e5e7eb" stroke-width="1"/>')
        add(f'<text x="{x(l)}" y="{margem_topo - 34}" font-size="11" '
            f'fill="#9ca3af" text-anchor="middle">L={l}</text>')

    # Linha de vida de cada processo
    for pid in ids:
        yy = y(pid)
        add(f'<line x1="{margem_esq - 40}" y1="{yy}" x2="{largura - margem_dir + 20}" '
            f'y2="{yy}" stroke="#374151" stroke-width="2"/>')
        add(f'<text x="{margem_esq - 52}" y="{yy + 5}" font-size="14" '
            f'font-weight="600" fill="#111827" text-anchor="end">{_escapar(pid)}</text>')

    # Setas de mensagem (desenhadas antes dos pontos, para ficarem atras)
    for envio, recebimento in _parear_mensagens(eventos):
        x1, y1 = x(envio.relogio), y(envio.processo)
        x2, y2 = x(recebimento.relogio), y(recebimento.processo)
        add(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#b45309" '
            f'stroke-width="1.8" marker-end="url(#seta)"/>')
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        rotulo = _escapar(envio.conteudo or "")
        add(f'<rect x="{mx - 22}" y="{my - 9}" width="44" height="17" rx="4" '
            f'fill="#fffbeb" stroke="#fcd34d" stroke-width="0.8"/>')
        add(f'<text x="{mx}" y="{my + 3}" font-size="10" fill="#92400e" '
            f'text-anchor="middle">{rotulo}</text>')

    # Pontos dos eventos
    for e in eventos:
        cx, cy = x(e.relogio), y(e.processo)
        cor = CORES.get(e.tipo, "#111827")
        add(f'<circle cx="{cx}" cy="{cy}" r="7" fill="{cor}" stroke="#ffffff" '
            f'stroke-width="2"/>')
        add(f'<text x="{cx}" y="{cy - 14}" font-size="11" font-weight="600" '
            f'fill="{cor}" text-anchor="middle">{e.relogio}</text>')
        add(f'<text x="{cx}" y="{cy + 24}" font-size="9" fill="#6b7280" '
            f'text-anchor="middle">{_escapar(e.rotulo)}</text>')

    # Legenda
    ly = altura - 24
    lx = margem_esq
    for tipo, cor in CORES.items():
        add(f'<circle cx="{lx}" cy="{ly - 4}" r="6" fill="{cor}"/>')
        add(f'<text x="{lx + 12}" y="{ly}" font-size="11" fill="#374151">{tipo}</text>')
        lx += 100
    add(f'<line x1="{lx}" y1="{ly - 4}" x2="{lx + 26}" y2="{ly - 4}" '
        f'stroke="#b45309" stroke-width="1.8" marker-end="url(#seta)"/>')
    add(f'<text x="{lx + 34}" y="{ly}" font-size="11" fill="#374151">mensagem</text>')

    add('</svg>')
    return "\n".join(s)


def salvar_svg(caminho, eventos, ids, titulo: str = "") -> str:
    from pathlib import Path

    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(gerar_svg(eventos, ids, titulo), encoding="utf-8")
    return str(caminho)


def gerar_ascii(eventos: Sequence[Evento], ids: Sequence[str]) -> str:
    """Versao em texto do diagrama, util quando so se tem o terminal."""
    max_l = max(e.relogio for e in eventos)
    largura = 6
    linhas = ["", "DIAGRAMA ESPAÇO-TEMPO (horizontal = tempo lógico)", ""]
    cabecalho = " " * 6 + "".join(f"{l:^{largura}}" for l in range(1, max_l + 1))
    linhas.append(cabecalho)
    simbolos = {"EXEC": "[E]", "SEND": "[S]", "RECEIVE": "[R]"}
    for pid in ids:
        celulas = ["-" * largura for _ in range(max_l)]
        for e in eventos:
            if e.processo == pid:
                celulas[e.relogio - 1] = simbolos[e.tipo].center(largura, "-")
        linhas.append(f"{pid:<5} " + "".join(celulas))
    linhas.append("")
    linhas.append("  [E] evento interno   [S] envio   [R] recebimento")
    linhas.append("")
    return "\n".join(linhas)
