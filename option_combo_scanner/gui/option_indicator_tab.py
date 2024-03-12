import asyncio
import configparser
import copy
import threading
import tkinter as tk
from tkinter import Scrollbar, messagebox, ttk

from option_combo_scanner.database.set_up_db import SetupDatabase
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.house_keeping import HouseKeepingGUI
from option_combo_scanner.gui.order_presets_tab_helper import OrderPresetHelper
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.contracts import (
    get_contract, get_contract_details_async)
from option_combo_scanner.indicators_calculator.historical_volatility import \
    HistoricalVolatility
from option_combo_scanner.indicators_calculator.implied_volatility import \
    ImpliedVolatility
from option_combo_scanner.indicators_calculator.put_call_vol import PutCallVol
from option_combo_scanner.strategy.indicator import Indicator
from option_combo_scanner.strategy.order_preset import OrderPreset
from option_combo_scanner.strategy.scanner import Scanner
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
from option_combo_scanner.strategy.utilities import StrategyUtils

# Read the config file
config = configparser.ConfigParser()
config.read("config.ini")

tws_config = config["TWS"]
ACCOUNT_ID = tws_config["account"]

# Name, Width, Heading

option_indicator_table_columns_width = [
    ("indicator_id", 165, "Indicator ID"),
    ("instrument_id", 165, "Instrument ID"),
    ("symbol", 165, "Symbol"),
    ("sec_type", 165, "Sec Type"),
    ("expiry", 165, "Expiry"),

    ("current_underlying_hv_value", 165, "HV"),
    ("average_underlying_hv_over_n_days", 165, "HV(14D)-Avg(14D)"),
    ("absoulte_change_in_underlying_over_n_days", 165, "Abs Chg Under-(N)"),
    ("percentage_change_in_underlying_over_n_days", 165, "%Chg Under-(N)"),
    ("current_hv_minus_iv", 165, "HV - IV"),
    ("current_iv_d1", 165, "IV(D1)"),
    ("current_iv_d2", 165, "IV(D2)"),
    ("current_avg_iv", 165, "Avg(IV)"),
    ("absolute_change_in_avg_iv_since_yesterday", 165, "Abs Chg Avg(IV)(1D)"),
    ("percentage_change_in_avg_iv_since_yesterday", 165, "%Chg Avg(IV)(1D)"),
    
    ("avg_iv_over_n_days", 165, "Avg IV-Avg(14D)"),
    ("current_rr_d1", 165, "RR(D1)"),
    ("current_rr_d2", 165, "RR(D2)"),
    ("percentage_change_in_rr_since_yesterday_d1", 165, "RR(D1)-Chg(1D)"),
    ("percentage_change_in_rr_since_yesterday_d2", 165, "RR(D2)-Chg(1D)"),
    ("percentage_change_in_rr_since_14_day_d1", 165, "RR(D1)-Chg(14D)"),
    ("percentage_change_in_rr_since_14_day_d2", 165, "RR(D2)-Chg(14D)"),
    ("max_pain_strike", 165, "Max Pain"),
    ("min_pain_strike", 165, "Min Pain"),
    ("oi_support_strike", 165, "OI Support"),
    ("oi_resistance_strike", 165, "OI Resistance"),
    
    ("put_call_volume_ratio_current_day", 165, "PC Ratio Current"),
    ("put_call_volume_ratio_average_over_n_days", 165, "PC Ratio-Avg-(14D)"),
    ("absolute_pc_change_since_yesterday", 165, "Abs PC Change(1D)"),
    
    ("pc_change_iv_change", 165, "PC Change/I.V.Change"),

    ("chg_in_underl_call_opt_price_since_yesterday_d1", 165, "C-D1 Chg Und/OPT Price-(1D)"),
    ("chg_in_underl_call_opt_price_since_yesterday_d2", 165, "C-D2 Chg Und/OPT Price-(1D)"),
    ("chg_in_underl_put_opt_price_since_yesterday_d1", 165, "P-D1 Chg Und/OPT Price-(1D)"),
    ("chg_in_underl_put_opt_price_since_yesterday_d2", 165, "P-D2 Chg Und/OPT Price-(1D)"),

    ("chg_in_underl_call_opt_price_since_nth_day_d1", 165, "C-D1 Chg Und/OPT Price-(N)"),
    ("chg_in_underl_call_opt_price_since_nth_day_d2", 165, "C-D2 Chg Und/OPT Price-(N)"),
    ("chg_in_underl_put_opt_price_since_nth_day_d1", 165, "P-D1 Chg Und/OPT Price-(N)"),
    ("chg_in_underl_put_opt_price_since_nth_day_d2", 165, "P-D2 Chg Und/OPT Price-(N)"),
    
]


class OptionIndicator:
    def __init__(self, option_indicator_tab) -> None:
        self.option_indicator_tab = option_indicator_tab
        self.create_option_indicator_tab()
        HouseKeepingGUI.dump_all_indicator_values_in_indicator_tab(self)

        Scanner.scanner_indicator_tab_obj = self
        PutCallVol.scanner_indicator_tab_pc_obj = self
        HistoricalVolatility.scanner_hv_indicator_tab_obj = self

        ImpliedVolatility.scanner_indicator_tab_iv_obj = self
        Utils.scanner_indicator_tab_object = self

        # self.order_preset_helper: OrderPresetHelper = OrderPresetHelper(
        #     self.order_presets_table
        # )

        # Dump the Indicator values in the GUI
        # HouseKeepingGUI.dump_all_indicator_values_in_indicator_tab(
        #     self
        # )

    # Creating Tab for Option Indicator

    def create_option_indicator_tab(self):

        # Create a frame for the user input fields
        input_frame = ttk.Frame(self.option_indicator_tab, padding=20)
        input_frame.pack(fill="both", expand=True)

        # Add some style
        style = ttk.Style()

        # Pick a theme
        style.theme_use("default")

        # Configure our treeview colors
        style.configure(
            "Treeview",
            background="#D3D3D3",
            foreground="black",
            rowheight=25,
            fieldbackground="#D3D3D3",
        )

        # Change selected color
        style.map("Treeview", background=[("selected", "blue")])

        # Create Treeview Frame for Option Indicator Tab
        option_indicator_table_frame = ttk.Frame(self.option_indicator_tab, padding=20)
        option_indicator_table_frame.pack(pady=20)
        option_indicator_table_frame.pack(fill="both", expand=True)

        # Place table fram in center
        option_indicator_table_frame.place(relx=0.5, anchor=tk.CENTER)
        option_indicator_table_frame.place(y=400, width=1590)

        # Treeview Scrollbar
        tree_scroll_y = Scrollbar(option_indicator_table_frame)
        tree_scroll_y.pack(side="right", fill="y")

        # Treeview Scrollbar
        tree_scroll_x = Scrollbar(option_indicator_table_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        # Create Treeview
        self.option_indicator_table = ttk.Treeview(
            option_indicator_table_frame,
            xscrollcommand=tree_scroll_x.set,
            yscrollcommand=tree_scroll_y.set,
            height=26,
            selectmode="extended",
        )
        # Pack to the screen
        self.option_indicator_table.pack(expand=True, fill="both")

        # Configure the scrollbar
        tree_scroll_y.config(command=self.option_indicator_table.yview)

        # Configure the scrollbar
        tree_scroll_x.config(command=self.option_indicator_table.xview)

        # Define Columns
        self.option_indicator_table["columns"] = [
            _[0] for _ in option_indicator_table_columns_width
        ]

        # Format Column
        self.option_indicator_table.column("#0", width=0, stretch="no")

        # Create Heading
        self.option_indicator_table.heading("#0", text="\n", anchor="w")

        # Formate Columns and Create Heading for Columns
        for col_name, col_width, col_heading in option_indicator_table_columns_width:
            self.option_indicator_table.column(
                col_name,
                anchor="center",
                width=col_width,
                minwidth=col_width,
                stretch=False,
            )
            self.option_indicator_table.heading(
                col_name, text=col_heading, anchor="center"
            )

        self.option_indicator_table.tag_configure("oddrow", background="white")
        self.option_indicator_table.tag_configure("evenrow", background="lightblue")

    # Add Indicator Data Values in DB
    def remove_row_from_indicator_table(self, list_of_indicator_ids):
        indicator_ids_in_indicator_table = self.option_indicator_table.get_children()

        for indicator_id in list_of_indicator_ids:
            # Remove the scanned combination from system
            if (
                int(indicator_id)
                in StrategyVariables.map_indicator_id_to_indicator_object
            ):
                StrategyVariables.map_indicator_id_to_indicator_object[
                    int(indicator_id)
                ].remove_indicator_from_system()

            indicator_id = str(indicator_id)
            if indicator_id in indicator_ids_in_indicator_table:
                self.option_indicator_table.delete(indicator_id)

    # Insertion of Indicator data in GUI
    def insert_into_indicator_table(self, scanner_indicator_object):
        indicator_id = scanner_indicator_object.indicator_id

        row_values = scanner_indicator_object.get_tuple()

        # Get the current number of items in the treeview
        num_items = len(self.option_indicator_table.get_children())

        if num_items % 2 == 1:
            self.option_indicator_table.insert(
                "",
                "end",
                iid=indicator_id,
                text=num_items + 1,
                values=row_values,
                tags=("oddrow",),
            )
        else:
            self.option_indicator_table.insert(
                "",
                "end",
                iid=indicator_id,
                text=num_items + 1,
                values=row_values,
                tags=("evenrow",),
            )

    def update_into_indicator_table(self, indicator_df):

        indicator_id_in_indicator_table = self.option_indicator_table.get_children()

        for index, rows in indicator_df.iterrows():
            indicator_id = str(rows["Indicator ID"])
            if indicator_id in indicator_id_in_indicator_table:
                hv = "None" if rows["hv"] == None else f"{rows['hv']:,.4f}"
                iv_d1 = "None" if rows["iv_d1"] == None else f"{rows['iv_d1']:,.4f}"
                iv_d2 = "None" if rows["iv_d2"] == None else f"{rows['iv_d2']:,.4f}"
                avg_iv = "None" if rows["avg_iv"] == None else f"{rows['avg_iv']:,.4f}"
                rr_d1 = "None" if rows["rr_d1"] == None else f"{rows['rr_d1']:,.4f}"
                rr_d2 = "None" if rows["rr_d2"] == None else f"{rows['rr_d2']:,.4f}"
                avg_iv_avg_14d = (
                    "None"
                    if rows["avg_iv_avg_14d"] == None
                    else f"{rows['avg_iv_avg_14d']:,.4f}"
                )
                change_rr_d1_1D = (
                    "None"
                    if rows["change_rr_d1_1D"] == None
                    else f"{rows['change_rr_d1_1D']:,.4f}"
                )
                change_rr_d2_1D = (
                    "None"
                    if rows["change_rr_d2_1D"] == None
                    else f"{rows['change_rr_d2_1D']:,.4f}"
                )
                change_rr_d1_14D = (
                    "None"
                    if rows["change_rr_d1_14D"] == None
                    else f"{rows['change_rr_d1_14D']:,.4f}"
                )
                change_rr_d2_14D = (
                    "None"
                    if rows["change_rr_d2_14D"] == None
                    else f"{rows['change_rr_d2_14D']:,.4f}"
                )
                hv_14d_avg_14d = (
                    "None"
                    if rows["hv_14d_avg_14d"] == None
                    else f"{rows['hv_14d_avg_14d']:,.4f}"
                )

                open_interest_support = (
                    "None"
                    if rows["open_interest_support"] == None
                    else f"{rows['open_interest_support']:,.4f}"
                )
                open_interest_resistance = (
                    "None"
                    if rows["open_interest_resistance"] == None
                    else f"{rows['open_interest_resistance']:,.4f}"
                )
                put_call_ratio_avg = (
                    "None"
                    if rows["put_call_ratio_avg"] == None
                    else f"{rows['put_call_ratio_avg']:,.4f}"
                )
                put_call_ratio_current = (
                    "None"
                    if rows["put_call_ratio_current"] == None
                    else f"{rows['put_call_ratio_current']:,.4f}"
                )

                Change_underlying_options_price_today = (
                    "None"
                    if rows["Change_underlying_options_price_today"] == None
                    else f"{rows['Change_underlying_options_price_today']:,.4f}"
                )
                chg_uderlying_opt_price_14d = (
                    "None"
                    if rows["chg_uderlying_opt_price_14d"] == None
                    else f"{rows['chg_uderlying_opt_price_14d']:,.4f}"
                )

                max_pain = (
                    "None" if rows["max_pain"] == None else f"{rows['max_pain']:,.4f}"
                )
                min_pain = (
                    "None" if rows["min_pain"] == None else f"{rows['min_pain']:,.4f}"
                )
                change_in_iv = (
                    "None"
                    if rows["change_in_iv"] == None
                    else f"{rows['change_in_iv']:,.4f}"
                )

                pc_change = rows["pc_change"]

                hv_14d_avg_14d = rows["hv_14d_avg_14d"]

                if pc_change and (change_in_iv != 0 or change_in_iv != "None"):
                    pc_change_iv_change = float(pc_change / float(change_in_iv))
                else:
                    pc_change_iv_change = "None"

                if avg_iv != "None" and hv != "None":
                    hv_14d_avg_iv = float(hv) - float((avg_iv)) * 100
                else:
                    hv_14d_avg_iv = "None"

                # HV(14D)-AvgIV

                # print(f"indicator_id: ", indicator_id, pc_change, put_call_ratio_avg)

                self.option_indicator_table.set(indicator_id, 5, hv)
                self.option_indicator_table.set(indicator_id, 6, iv_d1)
                self.option_indicator_table.set(indicator_id, 7, iv_d2)
                self.option_indicator_table.set(indicator_id, 8, avg_iv)
                self.option_indicator_table.set(indicator_id, 9, rr_d1)
                self.option_indicator_table.set(indicator_id, 10, rr_d2)
                self.option_indicator_table.set(indicator_id, 15, avg_iv_avg_14d)
                self.option_indicator_table.set(indicator_id, 13, change_rr_d1_1D)
                self.option_indicator_table.set(indicator_id, 14, change_rr_d2_1D)
                self.option_indicator_table.set(indicator_id, 11, change_rr_d1_14D)
                self.option_indicator_table.set(indicator_id, 12, change_rr_d2_14D)
                self.option_indicator_table.set(indicator_id, 16, hv_14d_avg_14d)
                self.option_indicator_table.set(indicator_id, 17, open_interest_support)
                self.option_indicator_table.set(
                    indicator_id, 18, open_interest_resistance
                )
                self.option_indicator_table.set(indicator_id, 19, hv_14d_avg_iv)
                self.option_indicator_table.set(
                    indicator_id, 20, put_call_ratio_current
                )
                self.option_indicator_table.set(indicator_id, 21, put_call_ratio_avg)
                # self.option_indicator_table.set(indicator_id, 22, pc_change)
                self.option_indicator_table.set(indicator_id, 22, pc_change_iv_change)
                self.option_indicator_table.set(
                    indicator_id, 23, Change_underlying_options_price_today
                )
                self.option_indicator_table.set(
                    indicator_id, 24, chg_uderlying_opt_price_14d
                )

                self.option_indicator_table.set(indicator_id, 25, max_pain)
                self.option_indicator_table.set(indicator_id, 26, min_pain)
                self.option_indicator_table.set(indicator_id, 27, change_in_iv)
