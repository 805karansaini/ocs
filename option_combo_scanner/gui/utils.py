import configparser
import copy
import datetime
import math
import sys
import tkinter as tk
from tkinter import Scrollbar, ttk

import pandas as pd
import scipy
from scipy.stats import norm

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import StrategyVariables

logger = CustomLogger.logger
scanner_logger = CustomLogger.scanner_logger

ORDER_PRESET_COLUMNS = [
    "Unique ID",
    "Ticker",
    "Risk (%)",
    "Risk (USD)",
    "NLV",
    "Entry Price",
    "TP1 Price",
    "TP2 Price",
    "SL1 Price",
    "SL2 Price",
    "Entry Qty",
    "Status",
    "Bid",
    "Ask",
    "Filled Entry Qty",
    "Avg. Entry Price",
    "Filled Exit Qty",
    "Avg. Exit Price",
    "PNL",
    "Failure Reason",
]


class Utils:
    # Setted while the object is created in constructor
    scanner_combination_tab_object = None
    scanner_indicator_tab_object = None

    def __init__(self):
        pass

    @staticmethod
    def is_non_negative_number(string):
        try:
            _ = float(string)
            if _ >= 0:
                return True
            return False
        except ValueError:
            return False

    @staticmethod
    def is_non_negative_integer(string):
        try:
            _ = float(string)
            if _ >= 0 and _ % 1 == 0:
                return True
            return False
        except ValueError:
            return False

    @staticmethod
    def is_positive_greater_than_equal_one_integer(string):
        try:
            _ = float(string)
            if _ >= 1 and _ % 1 == 0:
                return True
            return False
        except ValueError:
            return False

    @staticmethod
    def is_between_zero_to_one(string):
        try:
            _ = float(string)
            if 0 <= _ <= 1:
                return True
            return False
        except ValueError:
            return False

    @staticmethod
    def is_between_minus_one_to_one(string):
        try:
            value = float(string)
            if -1 <= value <= 1:
                return True
            return False
        except ValueError:
            return False

    @staticmethod
    def is_time(string):
        """
        Should we in HH:MM:SS format
        """
        try:
            datetime.datetime.strptime(string, "%H:%M:%S")
            return True
        except ValueError:
            return False

    @staticmethod
    def display_message_popup(error_title, error_string):
        # Create a message popup window
        message_popup = tk.Toplevel()
        message_popup.title(error_title)

        # Set the geometry of the message popup window
        message_popup.geometry("400x100")

        # Create a frame for the input fields
        message_frame = ttk.Frame(message_popup, padding=20)
        message_frame.pack(fill="both", expand=True)

        char_count = 65
        # Add New Line after every 'char_count' characters
        error_string = "\n".join([error_string[i : i + char_count] for i in range(0, len(error_string), char_count)])
        # Add labels and entry fields for each column in the table
        error_label = ttk.Label(message_frame, text=error_string, width=80, anchor="center")
        error_label.place(relx=0.5, rely=0.5, anchor="center")

    @staticmethod
    def display_treeview_popup(title, list_of_columns_header, list_of_row_tuple):

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

        # Get the number of rows entered by the user
        try:
            num_rows = len(list_of_row_tuple)
        except:
            Utils.display_message_popup("Error", "Unable to get the combination data.")
            return

        # Create a popup window with the table
        treeview_popup = tk.Toplevel()
        treeview_popup.title(title)
        custom_height = min(max((num_rows * 20) + 100, 150), 210)

        custom_width = 80 * len(list_of_row_tuple[0]) + 60  # 60 = 20 * 2(padding) + 20(scrollbar)
        treeview_popup.geometry(f"{custom_width}x{custom_height}")

        # Create a frame for the input fields
        treeview_table_frame = ttk.Frame(treeview_popup, padding=20)
        treeview_table_frame.pack(fill="both", expand=True)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(treeview_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        treeview_table = ttk.Treeview(
            treeview_table_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
        )

        # Pack to the screen
        treeview_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=treeview_table.yview)

        # Define Our Columns
        treeview_table["columns"] = list_of_columns_header

        # First Column hiding it
        treeview_table.column("#0", width=0, stretch="no")
        treeview_table.heading("#0", text="", anchor="w")

        for column_name in list_of_columns_header:
            treeview_table.column(column_name, anchor="center", width=80)
            treeview_table.heading(column_name, text=column_name, anchor="center")

        # Create striped row tags
        treeview_table.tag_configure("oddrow", background="white")
        treeview_table.tag_configure("evenrow", background="lightblue")

        count = 0

        for record in list_of_row_tuple:
            if count % 2 == 0:
                treeview_table.insert(
                    parent="",
                    index="end",
                    iid=count,
                    text="",
                    values=record,
                    tags=("evenrow",),
                )
            else:
                treeview_table.insert(
                    parent="",
                    index="end",
                    iid=count,
                    text="",
                    values=record,
                    tags=("oddrow",),
                )

            count += 1

    # Method to sort string numeric values
    @staticmethod
    def custom_sort(val):

        # Replace 'N/A' with a large value
        if val in ["N/A", "inf", "-inf"]:
            return 10**15

        elif type(val) == str and (val[0].isnumeric() or val[0] == "-"):

            # Replace "," with ""
            val = val.replace(",", "")
            val = val.replace(":", "")

            # Remove %
            if val[-1] == "%":
                return float(val[:-1])

            return float(val)
        else:
            return val

    @staticmethod
    # Method to sort cas rows
    def sort_cas_row_values_by_column(values):

        # Sort Values Based on the User selected column
        key, reverse = list(variables.cas_table_sort_by_column.items())[0]

        # Col_index
        col_index = variables.map_cas_column_name_to_index[key]

        # Sort Values
        values = sorted(values, key=lambda row: Utils.custom_sort(row[col_index]), reverse=reverse)

        return values

    @staticmethod
    def clear_scanner_combination_table():

        list_of_combo_ids = Utils.scanner_combination_tab_object.scanner_combination_table.get_children()

        # Remove rows from scanned combo table
        Utils.scanner_combination_tab_object.remove_row_from_scanner_combination_table(list_of_combo_ids)

    @staticmethod
    def get_list_of_combo_ids_for_based_on_config_id(config_id):

        # Query to fetch Combo ID such that config is is same
        where_condition = f" WHERE `config_id` = '{config_id}';"
        select_query = SqlQueries.create_select_query(
            table_name="combination_table",
            columns="`combo_id`",
            where_clause=where_condition,
        )

        # Get all the combo ids for config_id
        list_of_results_dict = SqlQueries.execute_select_query(select_query)

        list_of_combo_ids = [int(float(_temp["combo_id"])) for _temp in list_of_results_dict]

        return list_of_combo_ids

    @staticmethod
    def remove_row_from_scanner_combination_table(
        list_of_combo_ids=None,
        instrument_id=None,
    ):
        """
        Remove all the scanned combinations on the give list of combo_ids
        Remove all the rows such that the instrument id is same
        """

        # Remove all the combinations based on the list_of_combo_ids
        if list_of_combo_ids is not None:
            # Remove rows from scanned combo table
            Utils.scanner_combination_tab_object.remove_row_from_scanner_combination_table(list_of_combo_ids)

        if instrument_id is not None:
            list_of_combo_ids = []
            list_of_all_combo_ids_in_table = Utils.scanner_combination_tab_object.scanner_combination_table.get_children()

            for combo_id in list_of_all_combo_ids_in_table:
                row_value = Utils.scanner_combination_tab_object.scanner_combination_table.item(combo_id, "values")

                row_instrume_id = row_value[0]
                if int(row_instrume_id) == int(instrument_id):
                    list_of_combo_ids.append(str(combo_id))

            # Remove rows from scanned combo table
            Utils.scanner_combination_tab_object.remove_row_from_scanner_combination_table(list_of_combo_ids)

        for index, row_id in enumerate(Utils.scanner_combination_tab_object.scanner_combination_table.get_children()):
            if index % 2 == 0:
                Utils.scanner_combination_tab_object.scanner_combination_table.item(row_id, tags=("evenrow",))
            else:
                Utils.scanner_combination_tab_object.scanner_combination_table.item(row_id, tags=("oddrow",))

    @staticmethod
    def remove_row_from_indicator_table(
        list_of_indicator_ids=None,
        instrument_id=None,
    ):
        # TODO - IMPORTANT Check KARAN ARYAN
        # Remove all the indicator based on the list_of_indicator_ids
        if list_of_indicator_ids is not None:
            # Remove rows from indicator table
            Utils.scanner_indicator_tab_object.remove_row_from_indicator_table(list_of_indicator_ids)

        if instrument_id is not None:
            list_of_indicator_ids = []
            list_of_all_indicator_ids_in_table = Utils.scanner_indicator_tab_object.option_indicator_table.get_children()

            for indicator_id in list_of_all_indicator_ids_in_table:
                row_value = Utils.scanner_indicator_tab_object.option_indicator_table.item(indicator_id, "values")

                row_instrume_id = row_value[1]
                if int(row_instrume_id) == int(instrument_id):
                    list_of_indicator_ids.append(str(indicator_id))

            # Remove rows from indicator table
            Utils.scanner_indicator_tab_object.remove_row_from_indicator_table(list_of_indicator_ids)

        for index, row_id in enumerate(Utils.scanner_indicator_tab_object.option_indicator_table.get_children()):
            if index % 2 == 0:
                Utils.scanner_indicator_tab_object.option_indicator_table.item(row_id, tags=("evenrow",))
            else:
                Utils.scanner_indicator_tab_object.option_indicator_table.item(row_id, tags=("oddrow",))

    @staticmethod
    def update_indicator_row_in_gui(indicator_id: int):
        indicator_id = int(indicator_id)
        # Update if exits
        if indicator_id in StrategyVariables.map_indicator_id_to_indicator_object:
            row_values = StrategyVariables.map_indicator_id_to_indicator_object[indicator_id].get_tuple()
            indicator_id = str(indicator_id)

            try:
                # Update the row at once.
                Utils.scanner_indicator_tab_object.option_indicator_table.item(indicator_id, values=row_values)
            except Exception as e:
                print(f"Execption {e}")

    @staticmethod
    def create_and_display_impact_popup():
        pass

    @staticmethod
    def get_implied_volatility(S, r1, r2, t, X, market_premium, opt_type):
        """
        calucalted_delta, calucalted_iv = Utils.get_delta(
                    underlying_price,
                    StrategyVariables.riskfree_rate1,
                    0,
                    time_to_expiration,
                    float(strike),
                    opt_premium,
                    option_right,
                )
        current_price,
        StrategyVariables.riskfree_rate1 =0.04,
        0,
        time_to_expiration,
        float(contract.strike),
        market_premium,
        right,
        """
        max_iters = 50
        max_iv = 8.0

        """
        # Print diagnostics
        print("S=" + str(S))
        print("r1=" + str(r1))
        print("r2=" + str(r2))
        print("t=" + str(t))
        print("X=" + str(X))
        print("market_premium=" + str(market_premium))
        print("opt_type=" + str(opt_type))    
        """
        # Handling the case if t is 0
        if t == 0:
            t = 1 / 365

        # Inits
        tolerance = 0.0001
        guess_mid = float("NaN")
        theoretical_premium = float("NaN")
        cur_iter = 0

        # Set guess range
        guess_lower = 0.0001
        guess_upper = 0.50
        while Utils.get_theoretical_premium(S, r1, r2, t, X, guess_upper, opt_type) < market_premium:

            # Update upper bound
            guess_upper = guess_upper * 2.0

            # Exit if upper bound exceed max_iv
            if guess_upper >= max_iv:
                return guess_upper

        # Run iteration
        while pd.isnull(guess_mid) or (abs(market_premium - theoretical_premium) / market_premium > tolerance):

            # Calculate mid
            guess_mid = (guess_upper + guess_lower) / 2.0

            # Get theoretical premium
            theoretical_premium = Utils.get_theoretical_premium(S, r1, r2, t, X, guess_mid, opt_type)

            """
            # Print diagnostics
            print(str(guess_lower) + " - " + str(guess_upper) + " : " + str(guess_mid) + " = " + str(theoretical_premium))
            """

            # Update guess range
            if theoretical_premium == market_premium:
                break
            elif theoretical_premium > market_premium:
                guess_upper = guess_mid
            else:
                guess_lower = guess_mid

            # Break condition
            cur_iter = cur_iter + 1
            if cur_iter >= max_iters:
                break

        return guess_mid

    @staticmethod
    def get_theoretical_premium(S, r1, r2, t, X, sigma, opt_type):
        if S == 0:
            S = 0.0001

        # Handling the case if t is 0
        if t == 0:
            t = 1 / 365

        sigma_t = sigma * math.sqrt(t)
        d1 = (math.log(S / X) + ((r1 + math.pow(sigma, 2) / 2) * t)) / sigma_t
        d2 = d1 - sigma_t

        if opt_type == "CALL":
            return S * math.exp((r1 - r2) * t) * norm.cdf(d1) - X * math.exp(-r2 * t) * norm.cdf(d2)
        elif opt_type == "PUT":
            return X * math.exp(-r2 * t) * norm.cdf(-d2) - S * math.exp((r1 - r2) * t) * norm.cdf(-d1)
        else:
            sys.exit("Unknown opt_type = " + opt_type)

    @staticmethod
    def get_delta(S, r1, r2, t, X, market_premium, opt_type):
        """
        calucalted_delta, calucalted_iv = Utils.get_delta(
                    underlying_price,
                    StrategyVariables.riskfree_rate1,
                    0,
                    time_to_expiration,
                    float(strike),
                    opt_premium,
                    option_right,
                )
        current_price of underlying,
        StrategyVariables.riskfree_rate1 =0.04,
        0,
        time_to_expiration,
        float(contract.strike),
        market_premium,
        right,
        """
        opt_type = opt_type.upper()

        # Handling the case if t is 0
        if t == 0:
            t = 1 / 365

        sigma = Utils.get_implied_volatility(S, r1, r2, t, X, market_premium, opt_type)

        if sigma is float("NaN"):
            return float("NaN"), float("NaN")

        try:

            sigma_t = sigma * math.sqrt(t)
            d1 = (math.log(S / X) + ((r1 + math.pow(sigma, 2) / 2) * t)) / sigma_t

            if opt_type == "CALL":

                return scipy.stats.norm.cdf(d1), sigma

            elif opt_type == "PUT":
                return (scipy.stats.norm.cdf(d1) - 1), sigma

        except Exception as e:
            return float("NaN"), float("NaN")

    @staticmethod
    def deletion_indicator_rows_based_on_config_tuple_relation(list_of_config_relation_tuple_for_deletion):

        for config_id, instrument_id, expiry in list_of_config_relation_tuple_for_deletion:

            # Query to get the rows count
            where_condition = f" WHERE `instrument_id` = {instrument_id} AND `expiry` = {expiry};"
            select_query = SqlQueries.create_select_query(
                table_name="config_indicator_relation",
                columns="Count(*)",
                where_clause=where_condition,
            )
            count_of_existing_row = SqlQueries.execute_select_query(select_query)
            count_row = count_of_existing_row[0]["Count(*)"]

            scanner_logger.info(
                f"      Config ID: --  Inside Utils.deletion_indicator_rows_based_on_config_tuple_relation, #Row Count: {count_row} for <{config_id, instrument_id, expiry}> "
            )

            if count_row == 0:
                select_query = SqlQueries.create_select_query(
                    table_name="indicator_table",
                    columns="indicator_id",
                    where_clause=where_condition,
                )
                dict_of_all_indicator_ids = SqlQueries.execute_select_query(select_query)
                list_of_indicator_ids = [row["indicator_id"] for row in dict_of_all_indicator_ids]

                scanner_logger.info(
                    f"      Config ID: --  Inside Utils.deletion_indicator_rows_based_on_config_tuple_relation, Delete Indicator IDs: {list_of_indicator_ids}> "
                )

                Utils.delete_indicator_row_from_db_gui_and_system(list_of_indicator_ids)

    @staticmethod
    def delete_indicator_row_from_db_gui_and_system(list_of_indicator_ids_deletion):
        for indicator_id in list_of_indicator_ids_deletion:
            where_condition = f"WHERE `indicator_id` = {indicator_id}"
            delete_query = SqlQueries.create_delete_query(table_name="indicator_table", where_clause=where_condition)
            res = SqlQueries.execute_delete_query(delete_query)

        # Remove from system
        if list_of_indicator_ids_deletion:
            Utils.remove_row_from_indicator_table(list_of_indicator_ids=list_of_indicator_ids_deletion)
