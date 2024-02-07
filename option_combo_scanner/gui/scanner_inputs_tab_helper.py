import asyncio
import configparser
import threading
import time
import tkinter as tk
from tkinter import Scrollbar, messagebox, ttk
from com.identify_trading_class_for_fop import identify_the_trading_class_for_all_the_fop_leg_in_combination_async

from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)
from com.variables import variables


class ScannerInputsTab:
    def __init__(self):
        pass

    @staticmethod
    def delete_instrument(scanner_inputs_tab_obj):
        
        scanner_inputs_tab_obj.instrument_table
    


