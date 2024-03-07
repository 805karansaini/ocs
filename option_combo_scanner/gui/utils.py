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
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import StrategyVariables

logger = CustomLogger.logger

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
        error_string = "\n".join(
            [
                error_string[i : i + char_count]
                for i in range(0, len(error_string), char_count)
            ]
        )
        # Add labels and entry fields for each column in the table
        error_label = ttk.Label(
            message_frame, text=error_string, width=80, anchor="center"
        )
        error_label.place(relx=0.5, rely=0.5, anchor="center")

    # Display table/treeview popup
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

        custom_width = (
            80 * len(list_of_row_tuple[0]) + 60
        )  # 60 = 20 * 2(padding) + 20(scrollbar)
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
        if val in ["N/A",  "inf", "-inf"]:
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
        values = sorted(
            values, key=lambda row: Utils.custom_sort(row[col_index]), reverse=reverse
        )

        return values


    @staticmethod
    def clear_scanner_combination_table():
        
        list_of_combo_ids = Utils.scanner_combination_tab_object.scanner_combination_table.get_children()

        # Remove rows from scanned combo table
        Utils.scanner_combination_tab_object.remove_row_from_scanner_combination_table(list_of_combo_ids)

    @staticmethod
    def remove_row_from_scanner_combination_table(list_of_combo_ids=None, instrument_id=None, ):
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
                row_value = Utils.scanner_combination_tab_object.scanner_combination_table.item(combo_id , "values")

                row_instrume_id = row_value[1]
                if int(row_instrume_id) == int(instrument_id):
                    list_of_combo_ids.append(str(combo_id))

            # Remove rows from scanned combo table
            Utils.scanner_combination_tab_object.remove_row_from_scanner_combination_table(list_of_combo_ids)

    @staticmethod
    def remove_row_from_indicator_table(list_of_indicator_ids=None, instrument_id=None,):      
        # Remove all the indicator based on the list_of_indicator_ids
        if list_of_indicator_ids is not None:
            # Remove rows from indicator table
            Utils.scanner_indicator_tab_object.remove_row_from_indicator_table(list_of_indicator_ids)

        if instrument_id is not None:
            list_of_indicator_ids = []
            list_of_all_indicator_ids_in_table = Utils.scanner_indicator_tab_object.option_indicator_table.get_children()
            
            for indicator_id in list_of_all_indicator_ids_in_table:
                row_value = Utils.scanner_indicator_tab_object.option_indicator_table.item(indicator_id , "values")

                row_instrume_id = row_value[1]
                if int(row_instrume_id) == int(instrument_id):
                    list_of_indicator_ids.append(str(indicator_id))

    #         # Remove rows from indicator table
            Utils.scanner_indicator_tab_object.remove_row_from_indicator_table(list_of_indicator_ids)

    
    @staticmethod
    def get_implied_volatility(S, r1, r2, t, X, market_premium, opt_type):
        
        max_iters = 50
        max_iv = 8.0
            
        '''
        # Print diagnostics
        print("S=" + str(S))
        print("r1=" + str(r1))
        print("r2=" + str(r2))
        print("t=" + str(t))
        print("X=" + str(X))
        print("market_premium=" + str(market_premium))
        print("opt_type=" + str(opt_type))    
        '''
        
        # Inits
        tolerance = 0.0001
        guess_mid = float("NaN")
        theoretical_premium = float("NaN")
        cur_iter = 0
        
        # Set guess range
        guess_lower = 0.0001
        guess_upper = 0.50
        while(Utils.get_theoretical_premium(S, r1, r2, t, X, guess_upper, opt_type) < market_premium):    
            
            # Update upper bound
            guess_upper = guess_upper * 2.0

            # Exit if upper bound exceed max_iv
            if(guess_upper >= max_iv):
                return guess_upper
            
        # Run iteration
        while(pd.isnull(guess_mid) or (abs(market_premium - theoretical_premium) / market_premium > tolerance)):

            # Calculate mid
            guess_mid = (guess_upper + guess_lower) / 2.0

            # Get theoretical premium
            theoretical_premium = Utils.get_theoretical_premium(S, r1, r2, t, X, guess_mid, opt_type)        

            '''
            # Print diagnostics
            print(str(guess_lower) + " - " + str(guess_upper) + " : " + str(guess_mid) + " = " + str(theoretical_premium))
            '''
            
            # Update guess range
            if(theoretical_premium == market_premium):
                break
            elif(theoretical_premium > market_premium):
                guess_upper = guess_mid
            else:
                guess_lower = guess_mid
            
            # Break condition
            cur_iter = cur_iter + 1
            if(cur_iter >= max_iters):
                break
                
        return guess_mid
    
    @staticmethod
    def get_theoretical_premium(S, r1, r2, t, X, sigma, opt_type):
        
        sigma_t = sigma * math.sqrt(t)
        d1 = (math.log(S/X) + ((r1 + math.pow(sigma,2) / 2) * t)) / sigma_t
        d2 = d1 - sigma_t
        
        if(opt_type == "CALL"):
            return (S * math.exp((r1 - r2) * t) * norm.cdf(d1) - X * math.exp(-r2 * t) * norm.cdf(d2))
        elif(opt_type == "PUT"):
            return (X * math.exp(-r2 * t) * norm.cdf(-d2) - S * math.exp((r1 - r2) * t) * norm.cdf(-d1))
        else:
            sys.exit("Unknown opt_type = " + opt_type)

    @staticmethod
    def get_delta(S, r1, r2, t, X, market_premium, opt_type):
        """
        current_price,
        StrategyVariables.riskfree_rate1,
        0,
        time_to_expiration,
        float(contract.strike),
        market_premium,
        right,
        """
        sigma = Utils.get_implied_volatility(S, r1, r2, t, X, market_premium, opt_type)
        
        if(sigma is float("NaN")):        
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
        
    """

    # Method to update cas table rows in GUI table
    @staticmethod
    def filter_and_update_table_view(self, filtered_table_dataframe, table_name=""):
        # scanner_combination_table
        # indicator_table
        if table_name == "":
            return
        
        # All theIDs in the dataframe
        if table_name == 'scanner_combination_table':
            # TODO
            Utils.clear_scanner_combination_table()
            all_ids = filtered_table_dataframe["Combo ID"].tolist()
        elif table_name == 'indicator_table':
            # TODO
            all_ids = filtered_table_dataframe["Indicator ID"].tolist()
        else:
            print("invalid Tbale Name")

        for x in all_ids:
            pass insert_combination_in_scanner_combination_table_gui



        # All the rows in CAS Table
        all_unique_ids_in_watchlist = all_unique_id_in_cas_table = [
            int(_x) for _x in self.cas_table.get_children()
        ]

        # If we want to update the table as watchlist changed
        if variables.flag_update_tables_watchlist_changed:
            try:
                # Get all the
                if variables.selected_watchlist == "ALL":
                    all_unique_ids_in_watchlist = all_unique_ids_in_system
                else:
                    all_unique_ids_in_watchlist = copy.deepcopy(
                        variables.unique_id_list_of_selected_watchlist
                    )
                    all_unique_ids_in_watchlist = (
                        list(map(int, all_unique_ids_in_watchlist.split(",")))
                        if all_unique_ids_in_watchlist.strip() not in ["", None, "None"]
                        else []
                    )

                # convert list to set
                set_all_unique_ids_in_watchlist = set(all_unique_ids_in_watchlist)
                set_unique_ids_list_of_passed_condition = set(
                    variables.unique_ids_list_of_passed_condition
                )

                # get intersection of set and convert result to list
                all_unique_ids_in_watchlist = list(
                    set_all_unique_ids_in_watchlist.intersection(
                        set_unique_ids_list_of_passed_condition
                    )
                )

            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside updating cas table, {e}")

            # Setting it to False
            variables.flag_update_tables_watchlist_changed = False

        # Update the rows
        for i, row_val in cas_table_update_values_df.iterrows():

            # Unique ID of row val
            unique_id = row_val["Unique ID"]

            if unique_id in all_unique_ids_in_watchlist:

                # Tuple of vals
                row_val = tuple(cas_table_update_values_df.iloc[i])

                if unique_id in all_unique_id_in_cas_table:
                    # Update the row at once.
                    self.cas_table.item(unique_id, values=row_val)
                else:
                    # Insert it in the table
                    self.cas_table.insert(
                        "",
                        "end",
                        iid=unique_id,
                        text="",
                        values=row_val,
                        tags=("oddrow",),
                    )
            else:
                # If this unique_id in CAS Table but not in watchlist delete it
                if unique_id in all_unique_id_in_cas_table:
                    try:
                        self.cas_table.delete(unique_id)
                    except Exception as e:
                        pass

        try:
            # Filter out the dataframe such that the dataframe only consists of all the unique ids that are present in the watchlist, so sorting will be in correct order.
            cas_table_update_values_df = cas_table_update_values_df[
                cas_table_update_values_df["Unique ID"].isin(
                    all_unique_ids_in_watchlist
                )
            ]
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Error inside updating cas table values, is {e}")

        # All the rows in CAS Table
        all_unique_id_in_cas_table = self.cas_table.get_children()

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in cas_table_update_values_df.iterrows():

            # Unique_id
            unique_id = str(row["Unique ID"])

            # If unique_id in table
            if unique_id in all_unique_id_in_cas_table:
                self.cas_table.move(unique_id, "", counter_row)

                if counter_row % 2 == 0:
                    self.cas_table.item(unique_id, tags="evenrow")
                else:
                    self.cas_table.item(unique_id, tags="oddrow")

                # Increase row count
                counter_row += 1


    """









































    ###############################
    ### DEP
    ###############################
    # Calculates the prices of all the combos, and returns them in a dict {unique_id : {BUY: , SELL, total_spread:}
    @staticmethod
    def get_prices_for_order_presets():
        # Making a local copy of unique_id_to_order_preset_obj
        local_unique_id_to_order_preset_obj = copy.deepcopy(
            variables.map_unique_id_to_order_preset
        )

        # Contains all the unique_id and prices, {unique_id : {BUY: , SELL, total_spread:}
        prices_dict = {}

        # Process each order_preset_obj one by one.
        for unique_id, order_preset_obj in local_unique_id_to_order_preset_obj.items():
            con_id = order_preset_obj.conid
            try:
                req_id = variables.map_conid_to_subscripiton_req_id[con_id]
                bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]

                if bid == None:
                    bid = 0
                else:
                    bid = float(bid)

                if ask == None:
                    ask = 0
                else:
                    ask = float(ask)
            except Exception as e:
                logger.error(
                    f"Exception in get_prices_for_order_presets {e} Unique ID: {unique_id} Con ID: {con_id} Req ID: {req_id} Bid: {variables.bid_price[req_id]} Ask: {variables.ask_price[req_id]}"
                )
                continue

            prices_dict[unique_id] = {"Bid": bid, "Ask": ask}

        # Make it available in variables
        variables.unique_id_to_prices_dict = prices_dict

        # print(prices_dict)
        return prices_dict

    @staticmethod
    def create_latest_order_preset_values_dataframe(prices_unique_id):
        # List of update values
        order_preset_table_latest_values = []

        # Making a local copy of unique_id_to_order_preset_obj
        local_unique_id_to_order_preset_obj = copy.deepcopy(
            variables.map_unique_id_to_order_preset
        )

        for unique_id, order_preset_obj in local_unique_id_to_order_preset_obj.items():
            try:
                bid, ask = (
                    prices_unique_id[unique_id]["Bid"],
                    prices_unique_id[unique_id]["Ask"],
                )
            except Exception as e:
                bid, ask = None, None
                logger.error(
                    f"Exception in create latest order preset {e} UID: {unique_id} Bid: {bid} Ask: {ask}"
                )

            row_value = Utils.get_tuple_values_for_order_preset_row(
                order_preset_obj, bid, ask
            )

            order_preset_table_latest_values.append(row_value)

        # Create dataframe
        order_preset_table_latest_values_dataframe = pd.DataFrame(
            order_preset_table_latest_values, columns=ORDER_PRESET_COLUMNS
        )

        return order_preset_table_latest_values_dataframe

    @staticmethod
    def update_setting_in_system(
        number_of_trades_allowed: int,
        max_ba_spread: float,
        price_gap_threshold: float,
        stoploss_threshold: float,
        number_of_iterations: int,
        sleep_time_between_iterations: float,
        trade_start_time: str,
        trade_end_time: str,
        max_nlv_exposure_per_trade: float,
    ):
        # Set the values for attributes
        setattr(StrategyVariables, "number_of_trades_allowed", number_of_trades_allowed)
        setattr(StrategyVariables, "max_ba_spread", max_ba_spread)
        setattr(StrategyVariables, "price_gap_threshold", price_gap_threshold)
        setattr(StrategyVariables, "stoploss_threshold", stoploss_threshold)
        setattr(StrategyVariables, "number_of_iterations", number_of_iterations)
        setattr(
            StrategyVariables,
            "sleep_time_between_iterations",
            sleep_time_between_iterations,
        )
        setattr(StrategyVariables, "trade_start_time", trade_start_time)
        setattr(StrategyVariables, "trade_end_time", trade_end_time)
        setattr(
            StrategyVariables, "max_nlv_exposure_per_trade", max_nlv_exposure_per_trade
        )

    @staticmethod
    def update_settings_in_config_file(
        number_of_trades_allowed,
        max_ba_spread,
        price_gap_threshold,
        stoploss_threshold,
        number_of_iterations,
        sleep_time_between_iterations,
        trade_start_time,
        trade_end_time,
        max_nlv_exposure_per_trade,
    ):
        # Read the config file
        config = configparser.ConfigParser()
        config.read("config.ini")

        # Update the values
        config["ExecutionEngine"]["number_of_trades_allowed"] = str(
            number_of_trades_allowed
        )
        config["ExecutionEngine"]["max_ba_spread"] = str(max_ba_spread)
        config["ExecutionEngine"]["price_gap_threshold"] = str(price_gap_threshold)
        config["ExecutionEngine"]["stoploss_threshold"] = str(stoploss_threshold)
        config["ExecutionEngine"]["number_of_iterations"] = str(number_of_iterations)
        config["ExecutionEngine"]["sleep_time_between_iterations"] = str(
            sleep_time_between_iterations
        )
        config["ExecutionEngine"]["trade_start_time"] = str(trade_start_time)
        config["ExecutionEngine"]["trade_end_time"] = str(trade_end_time)
        config["ExecutionEngine"]["max_nlv_exposure_per_trade"] = str(
            max_nlv_exposure_per_trade
        )

        # Write the config file
        with open("config.ini", "w") as configfile:
            config.write(configfile)

    @staticmethod
    def get_tuple_values_for_order_preset_row(order_preset_obj, bid=None, ask=None):
        unique_id = order_preset_obj.unique_id
        ticker = order_preset_obj.ticker
        risk_percentage = order_preset_obj.risk_percentage
        risk_dollar = order_preset_obj.risk_dollar
        net_liquidation_value = order_preset_obj.net_liquidation_value
        entry_price = order_preset_obj.entry_price
        tp1_price = order_preset_obj.tp1_price
        tp2_price = order_preset_obj.tp2_price
        sl1_price = order_preset_obj.sl1_price
        sl2_price = order_preset_obj.sl2_price
        entry_quantity = order_preset_obj.entry_quantity
        status = order_preset_obj.status
        entry_quantity_filled = order_preset_obj.entry_quantity_filled
        average_entry_price = order_preset_obj.average_entry_price
        exit_quantity_filled = order_preset_obj.exit_quantity_filled
        average_exit_price = order_preset_obj.average_exit_price
        pnl = order_preset_obj.pnl
        failure_reason = order_preset_obj.failure_reason

        try:
            realised_pnl = (
                average_exit_price - average_entry_price
            ) * exit_quantity_filled
        except Exception as e:
            realised_pnl = None

        try:
            ba_mid = (bid + ask) / 2
            unrealised_pnl = (ba_mid - average_entry_price) * (
                entry_quantity_filled - exit_quantity_filled
            )
        except Exception as e:
            unrealised_pnl = None

        # Format the values here
        try:
            risk_percentage = f"{float(risk_percentage):,.2f}"
        except Exception as e:
            pass

        try:
            risk_dollar = f"{float(risk_dollar):,.2f}"
        except Exception as e:
            pass

        try:
            net_liquidation_value = f"{float(net_liquidation_value):,.2f}"
        except Exception as e:
            pass

        try:
            entry_price = f"{float(entry_price):,.2f}"
        except Exception as e:
            pass

        try:
            tp1_price = f"{float(tp1_price):,.2f}"
        except Exception as e:
            pass

        try:
            tp2_price = f"{float(tp2_price):,.2f}"
        except Exception as e:
            pass

        try:
            sl1_price = f"{float(sl1_price):,.2f}"
        except Exception as e:
            pass

        try:
            sl2_price = f"{float(sl2_price):,.2f}"
        except Exception as e:
            pass

        try:
            entry_quantity = f"{float(entry_quantity):,.2f}"
        except Exception as e:
            pass

        try:
            bid = f"{float(bid):,.2f}"
        except Exception as e:
            pass

        try:
            ask = f"{float(ask):,.2f}"
        except Exception as e:
            pass

        try:
            entry_quantity_filled = f"{float(entry_quantity_filled):,}"
        except Exception as e:
            pass

        try:
            average_entry_price = f"{float(average_entry_price):,.2f}"
        except Exception as e:
            pass

        try:
            exit_quantity_filled = f"{float(exit_quantity_filled):,}"
        except Exception as e:
            pass

        try:
            average_exit_price = f"{float(average_exit_price):,.2f}"
        except Exception as e:
            pass

        try:
            if (unrealised_pnl is not None) and (realised_pnl is not None):
                pnl = f"{float(unrealised_pnl + realised_pnl):,.2f}"
        except Exception as e:
            pass

        return (
            unique_id,
            ticker,
            risk_percentage,
            risk_dollar,
            net_liquidation_value,
            entry_price,
            tp1_price,
            tp2_price,
            sl1_price,
            sl2_price,
            entry_quantity,
            status,
            bid,
            ask,
            entry_quantity_filled,
            average_entry_price,
            exit_quantity_filled,
            average_exit_price,
            pnl,
            failure_reason,
        )

    