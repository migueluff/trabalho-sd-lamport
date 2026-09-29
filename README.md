# Relógios Lógicos de Lamport — Simulação

Trabalho Prático de Sistemas Distribuídos. Simula um ambiente distribuído com
três ou mais processos concorrentes que se comunicam por troca de mensagens e
mantêm, cada um, um relógio lógico de Lamport.

**Abordagem adotada: B — simulação dirigida por arquivo de configuração.** Um
programa principal lê um cenário em JSON que descreve a sequência de eventos de
cada processo e produz o log final logicamente ordenado.

---

## 1. Requisitos de ambiente

| Item | Versão |
|---|---|
| Python | 3.9 ou superior (desenvolvido em 3.12) |
| Dependências externas | **nenhuma** apenas a biblioteca padrão |

---

## 2. Como executar

A partir da raiz do projeto (`trabalho-lamport/`):

```bash
python3 -m lamport cenarios/cenario1_basico.json
```

> A flag `-m` carrega `lamport/` como **pacote**. Sem ela, `python3 lamport ...`
> apontaria o Python para o diretório, que seria executado como script solto e
> sem pacote pai. O arquivo `lamport/__main__.py` detecta e corrige esse caso,
> então as duas formas funcionam — mas `-m` é a canônica.

### Exemplo completo 

```bash
python3 -m lamport cenarios/cenario1_basico.json \
    --diagrama saida/diagrama_cenario1.svg \
    --saida saida/log_cenario1.txt
```

Isso imprime, em ordem:

1. o **log em tempo real**, na ordem em que as threads executaram;
2. a **ordem total** dos eventos por timestamp de Lamport, com desempate por ID do processo;
3. os relógios finais de cada processo;
4. o diagrama espaço-tempo em SVG.

### Opções

| Opção | Efeito |
|---|---|
| `--diagrama ARQ.svg` | gera o diagrama espaço-tempo do que foi executado |
| `--ascii` | desenha o diagrama em texto, direto no terminal |
| `--saida ARQ.txt` | salva todo o relatório em arquivo |
| `--jitter SEG` | atraso aleatório entre eventos, para embaralhar o escalonamento das threads |
| `--semente N` | torna o `--jitter` reproduzível |
| `--silencioso` | omite o log em tempo real, mostrando apenas o resultado final |
| `--timeout SEG` | tempo máximo que um `RECEIVE` espera por uma mensagem (padrão: 10 s) |

---

## 3. Cenários incluídos

| Arquivo | O que demonstra |
|---|---|
| `cenario1_basico.json` | cadeia causal `P1 → P2 → P3 → P1`. **Cenário principal da apresentação.** |
| `cenario2_empates.json` | vários eventos com o mesmo `L` em processos diferentes: exercita o desempate por ID |
| `cenario3_limitacao.json` | `P3` trabalha isolado enquanto `P1`/`P2` conversam: expõe `L(a) < L(b)` sem `a → b` |
| `cenario4_cruzado.json` | envios cruzados simultâneos; os dois `SEND` recebem o mesmo timestamp |

### Formato do arquivo de cenário

```json
{
  "nome": "Meu cenário",
  "descricao": "texto livre, opcional",
  "processos": {
    "P1": [
      {"tipo": "EXEC",    "conteudo": "o que o processo está fazendo"},
      {"tipo": "SEND",    "destino": "P2", "conteudo": "m1"},
      {"tipo": "RECEIVE", "origem":  "P3", "conteudo": "m3"}
    ],
    "P2": [ ... ],
    "P3": [ ... ]
  }
}
```

- Em um `RECEIVE`, `conteudo` é **opcional**: quando presente, funciona como
  asserção — a simulação falha se chegar outra mensagem.
- O cenário é validado antes de executar. Um `SEND` sem o `RECEIVE`
  correspondente é rejeitado com mensagem explícita, em vez de travar a
  simulação até o timeout.

---

## 4. Estrutura do projeto

```
trabalho-lamport/
├── lamport/
│   ├── relogio.py      as três regras de Lamport
│   ├── evento.py       evento, mensagem, formato do log e ordem total
│   ├── canal.py        caixas de entrada com bloqueio (motor de comunicação)
│   ├── processo.py     um processo = uma thread executando seu roteiro
│   ├── registrador.py  coleta thread-safe do log de eventos
│   ├── cenario.py      leitura e validação do arquivo JSON
│   ├── simulador.py    orquestra as threads e coleta o log
│   ├── diagrama.py     diagrama espaço-tempo em SVG e em texto
│   └── cli.py          interface de linha de comando
├── cenarios/           cenários de teste
├── saida/              diagramas SVG e logs gerados pela execução
├── demo.sh            
└── requirements.txt
```

---

## 5. Resumo das regras implementadas

Todas em `lamport/relogio.py`, para auditoria em um único lugar:

| Regra | Quando | Efeito |
|---|---|---|
| 1 | antes de um evento interno (`EXEC`) | `L_i = L_i + 1` |
| 2 | antes de um `SEND` | `L_i = L_i + 1` e a mensagem leva `timestamp = L_i` |
| 3 | ao processar um `RECEIVE` com timestamp `t` | `L_i = max(L_i, t) + 1` |
