# modes.py
from enum import Enum

class Mode(Enum):
    LIVE = 'live'
    PAPER = 'paper'
    BACKTEST = 'backtest'