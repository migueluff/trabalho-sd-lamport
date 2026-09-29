#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

pausa() { echo; read -rp "  [ENTER para continuar] "; clear; }

clear
echo "### 1. Cenario principal: cadeia causal P1 -> P2 -> P3 -> P1"
echo "###    Note o salto do relogio em cada RECEIVE: max(L, ts) + 1"
echo
python3 -m lamport cenarios/cenario1_basico.json --ascii
pausa

echo "### 2. Determinismo: a ordem REAL das threads muda entre execucoes,"
echo "###    mas a ordem total de Lamport e sempre a mesma."
echo
for s in 1 2 3; do
  echo -n "  execucao $s | ordem real das threads: "
  python3 -m lamport cenarios/cenario1_basico.json --jitter 0.03 --semente "$s" \
    | grep '^\[Processo' | awk '{print $2}' | tr -d ']' | tr '\n' ' '
  echo
done
echo
for s in 1 2 3; do
  echo -n "  execucao $s | hash da ordem total de Lamport: "
  python3 -m lamport cenarios/cenario1_basico.json --jitter 0.03 --semente "$s" --silencioso \
    | sed -n '/ORDEM TOTAL/,/RELOGIOS/p' | md5sum | cut -c1-16
done
pausa

echo "### 3. Empates de timestamp: desempate por ID (P1 < P2 < P3)"
echo
python3 -m lamport cenarios/cenario4_cruzado.json 
pausa

echo "### 4. A limitacao do relogio de Lamport: L(a) < L(b) sem a -> b"
echo
python3 -m lamport cenarios/cenario3.json --saida /tmp/lamport_demo.txt
echo
if [ -f ../analise_log.py ]; then
  python3 ../analise_log.py /tmp/lamport_demo.txt
else
  echo "  (a analise vive em ../analise_log.py, fora deste diretorio)"
fi
pausa

echo "### 5. Diagrama espaco-tempo do cenario principal (SVG)"
echo
python3 -m lamport cenarios/cenario1_basico.json --silencioso \
  --diagrama saida/diagrama_cenario1_basico.svg | tail -3
echo
echo "  Abra o arquivo gerado em saida/ para projetar o diagrama."
