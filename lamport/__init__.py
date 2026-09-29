"""
Simulacao dos Relogios Logicos de Lamport - Abordagem B

Trabalho Pratico -- Sistemas Distribuidos.
"""

__version__ = "1.0.0"

from .cenario import Cenario, CenarioInvalido
from .evento import EXEC, RECEIVE, SEND, Evento, Mensagem, ordenar_total
from .relogio import RelogioLamport
from .simulador import Resultado, simular

__all__ = [
    "Cenario", "CenarioInvalido", "Evento", "Mensagem", "Resultado",
    "RelogioLamport", "EXEC", "SEND", "RECEIVE",
    "simular", "ordenar_total",
]
