import tkinter.ttk

import pandas as pd

from com.variables import *
import configparser
from com.scale_trade_helper import is_float
from com.upload_orders_from_csv import make_multiline_mssg_for_gui_popup
from com.variables import variables
from com.user_inputs import UserInputs


class ScreenUserInputs(object):
    def __init__(self, master_notebook):
        """
        Constructor
        """
        self.notebook = master_notebook

        # Create user inputs tab
        self.user_inputs_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.user_inputs_tab, text="  User Inputs  ")

        # Method to create user inputs tab GUI components
        self.create_user_inputs_tab()

    # Method to create GUI for user inputs tab
    def create_user_inputs_tab(self):
        # Create Treeview Frame for user_inputs instances
        user_inputs_table_frame = ttk.Frame(self.user_inputs_tab, padding=10)
        user_inputs_table_frame.pack(pady=10)

        # Place in center
        user_inputs_table_frame.place(relx=0.5, anchor=tk.N)
        user_inputs_table_frame.place(y=10)

        # Create Treeview Frame for filter instances
        """buttons_frame = ttk.Frame(self.user_inputs_tab, padding=0)
        buttons_frame.pack(pady=0)

        # Initialize button to add filter
        add_user_inputs_button = ttk.Button(
            buttons_frame,
            text="Add Condition",
            command=lambda: self.add_user_inputs_condition(),
        )

        # Place add custom column button
        add_user_inputs_button.grid(row=0, column=0, padx=10, pady=10)"""

        # Initialize button to delte custom column
        """self.activate_deactivate_button = ttk.Button(
            buttons_frame,
            text="Activate Filter",
            command=lambda: self.activate_deactivated_filter_condition(),
        )

        # Place delete custom column button
        self.activate_deactivate_button.grid(row=0, column=1, padx=10, pady=10)

        # Place in center
        buttons_frame.place(relx=0.5, anchor=tk.N)
        buttons_frame.place(y=10)"""

        # Treeview Scrollbar
        tree_scroll = Scrollbar(user_inputs_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview Table
        self.user_inputs_table = ttk.Treeview(
            user_inputs_table_frame,
            yscrollcommand=tree_scroll.set,
            height=29,
            selectmode="extended",
        )

        # Pack to the screen
        self.user_inputs_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.user_inputs_table.yview)

        # Get columns for user_inputs table
        user_inputs_table_columns = [
            "User Input Name",
            "Value",
            "User Input Desciption",
            "Table ID",
        ]

        # Set columns for filter table
        self.user_inputs_table["columns"] = user_inputs_table_columns

        # Creating Column
        self.user_inputs_table.column("#0", width=0, stretch="no")

        # Creating columns for user_inputs table
        for column_name in user_inputs_table_columns:
            width = 330

            if column_name in ["User Input Desciption"]:
                width = 900

            if column_name in ["Table ID"]:
                width = 0

            self.user_inputs_table.column(
                column_name, anchor=tk.W, width=width, stretch="no"
            )

        # Create Heading
        self.user_inputs_table.heading("#0", text="", anchor="w")

        # Create headings for filter table
        for column_name in user_inputs_table_columns:
            self.user_inputs_table.heading(
                column_name, text=column_name, anchor="center"
            )

        # Back ground for rows in table
        self.user_inputs_table.tag_configure("oddrow", background="white")
        self.user_inputs_table.tag_configure("evenrow", background="lightblue")

        self.user_inputs_table.bind("<Button-3>", self.user_inputs_table_right_click)

        # Create an Entry widget
        entry = tk.Entry(user_inputs_table_frame)

        # Create a custom style for the Combobox widget
        custom_style = ttk.Style()
        custom_style.map(
            "Custom.TCombobox",
            fieldbackground=[
                ("readonly", "white"),
                ("!disabled", "white"),
                ("disabled", "lightgray"),
            ],
        )

        # create combo box
        combo_box = tkinter.ttk.Combobox(
            user_inputs_table_frame,
            state="readonly",
            style="Custom.TCombobox",
        )

        def on_scroll(event):
            self.selected_row = None

            # Your action upon scrolling goes here
            entry.place_forget()
            combo_box.place_forget()

        # Bind the <Configure> event of the scrollbar to on_scroll function
        self.user_inputs_table.bind("<Configure>", on_scroll)
        # Bind the mouse wheel event to the Treeview

        self.user_inputs_table.bind("<MouseWheel>", on_scroll)

        dropdown_list = [
            "flag_recovery_mode",
            "flag_enable_hv_annualized",
            "flag_identification_print",
            "flag_simulate_prices",
            "flag_debug_mode",
            "flag_store_cas_tab_csv_files",
            "flag_hv_daily",
            "flag_since_start_of_day_candles_for_relative_fields",
            "flag_enable_rm_account_rules",
            "flag_enable_trade_level_rm",
            "flag_use_execution_engine",
            "target_timezone",
            "account_parameter_for_order_quantity",
            "flag_series_condition",
            "limit_price_selection_for_execution_engine",
            "ib_algo_priority",
            "flag_relative_atr_in_range",
            "hv_method",
            "hv_candle_size",
            "volume_related_fileds_candle_size",
            "volume_magnet_candle_size",
            "support_resistance_and_relative_fields_candle_size",
            "index_select_for_beta_column",
            "last_n_minutes_fields_candle_size",
            "order_parameter_atr_candle_size",
            "flag_rm_checks_trade_volume_and_or",
            "order_parameter_candle_candle_size",
            "flag_range_order",
            "flag_stop_loss_premium",
            "flag_take_profit_premium",
            "flag_trailing_stop_loss_premium",
        ]

        entry_list = [
            "ibkr_tws_host",
            "ibkr_tws_port",
            "ibkr_tws_connection_id",
            "ibkr_tws_connection_id_for_cas",
            "ibkr_account_number",
            "offset_value_execution_engine",
            "lookback_period_for_cache",
            "time_frame_for_price_comparison_in_intraday",
            "time_frame_for_price_range_ratio_in_intraday",
            "max_wait_time_for_order_fill",
            "cas_number_of_days",
            "atr_number_of_days",
            "relative_atr_in_range_number_of_buckets",
            "hv_look_back_days",
            "volume_related_fileds_look_back_days",
            "relative_volume_derivation_lookback_mins",
            "relative_atr_derivation_lookback_mins",
            "volume_magnet_max_lookback_days",
            "support_resistance_and_relative_fields_look_back_days",
            "last_n_minutes_fields_lookback_days",
            "order_parameter_atr_lookback_days",
            "support_resistance_range_percent",
            "cas_long_term_fields_update_interval",
            "cas_intraday_fields_update_interval",
            "hv_related_fields_update_interval_time",
            "volume_related_fields_update_interval_time",
            "support_resistance_and_relative_fields_update_interval_time",
            "atr_for_order_interval",
            "account_table_update_interval",
            "rm_checks_interval_if_failed",
            "trade_rm_check_update_interval",
            "filter_conditions_update_interval",
            "candle_for_order_interval",
            "trade_level_rm_check_volume_lookback_mins",
            "volume_threshold_trade_rm_check",
            "bid_ask_spread_threshold_trade_rm_check",
            "bid_ask_qty_threshold_trade_rm_check",
            "cas_tab_csv_file_path",
            "custom_columns_json_csv_file_path",
            "buy_sell_csv",
            "stk_currency",
            "opt_currency",
            "fut_currency",
            "fop_currency",
            "stk_exchange",
            "opt_exchange",
            "fut_exchange",
            "fop_exchange",
            "opt_lot_size",
            "fut_lot_size",
            "fop_lot_size",
        ]

        int_valid_list = [
            "ibkr_tws_port",
            "ibkr_tws_connection_id",
            "ibkr_tws_connection_id_for_cas",
            "lookback_period_for_cache",
            "time_frame_for_price_comparison_in_intraday",
            "time_frame_for_price_range_ratio_in_intraday",
            "max_wait_time_for_order_fill",
            "cas_number_of_days",
            "atr_number_of_days",
            "relative_atr_in_range_number_of_buckets",
            "hv_look_back_days",
            "volume_related_fileds_look_back_days",
            "relative_volume_derivation_lookback_mins",
            "relative_atr_derivation_lookback_mins",
            "volume_magnet_max_lookback_days",
            "support_resistance_and_relative_fields_look_back_days",
            "last_n_minutes_fields_lookback_days",
            "order_parameter_atr_lookback_days",
            "cas_long_term_fields_update_interval",
            "cas_intraday_fields_update_interval",
            "hv_related_fields_update_interval_time",
            "volume_related_fields_update_interval_time",
            "support_resistance_and_relative_fields_update_interval_time",
            "atr_for_order_interval",
            "account_table_update_interval",
            "rm_checks_interval_if_failed",
            "trade_rm_check_update_interval",
            "filter_conditions_update_interval",
            "candle_for_order_interval",
            "trade_level_rm_check_volume_lookback_mins",
            "opt_lot_size",
            "fut_lot_size",
            "fop_lot_size",
        ]

        float_valid_list = [
            "offset_value_execution_engine",
            "support_resistance_range_percent",
            "volume_threshold_trade_rm_check",
            "bid_ask_spread_threshold_trade_rm_check",
            "bid_ask_qty_threshold_trade_rm_check",
        ]

        true_or_false_inputs = [
            "flag_recovery_mode",
            "flag_enable_hv_annualized",
            "flag_identification_print",
            "flag_simulate_prices",
            "flag_debug_mode",
            "flag_store_cas_tab_csv_files",
            "flag_hv_daily",
            "flag_since_start_of_day_candles_for_relative_fields",
            "flag_enable_rm_account_rules",
            "flag_enable_trade_level_rm",
            "flag_use_execution_engine",
            "flag_cache_data",
        ]

        true_false_list = ["True", "False"]

        time_zone_list = ["US/Eastern", "Israel"]

        account_parameters_list = ["SMA", "NLV", "CEL"]

        and_or_list = ["AND", "OR"]

        and_or_parameters = [
            "flag_rm_checks_trade_volume_and_or",
            "flag_series_condition",
        ]

        limit_price_for_execution_engine_parameter = [
            "limit_price_selection_for_execution_engine"
        ]

        limit_price_for_execution_engine_parameter_list = [
            "Limit_Bid",
            "Limit_Ask",
            "Limit_Mid",
            "Pegged_Midpoint",
        ]

        ib_algo_priority_list = ["Urgent", "Normal", "Patient"]

        flag_relative_atr_in_range_list = [
            "Open In Range",
            "Close In Range",
            "Open Or Close In Range",
        ]

        hv_methods_list = [
            "STANDARD_DEVIATION",
            "PARKINSON_WITH_GAP",
            "PARKINSON_WITHOUT_GAP",
            "NATR",
        ]

        candle_size_list = [
            "ONE_MIN",
            "TWO_MIN",
            "THREE_MIN",
            "FIVE_MIN",
            "TEN_MIN",
            "FIFTEEN_MIN",
            "TWENTY_MIN",
            "THIRTY_MIN",
            "ONE_HOUR",
            "TWO_HOUR",
            "THREE_HOUR",
            "FOUR_HOUR",
        ]

        candle_input_parameters = [
            "volume_related_fileds_candle_size",
            "volume_magnet_candle_size",
            "support_resistance_and_relative_fields_candle_size",
            "last_n_minutes_fields_candle_size",
            "order_parameter_atr_candle_size",
            "order_parameter_candle_candle_size",
            "hv_candle_size",
        ]

        flag_range_order_values_list = ["Intraday", "Week", "Month"]

        premium_order_parameter_list = [
            "flag_stop_loss_premium",
            "flag_take_profit_premium",
            "flag_trailing_stop_loss_premium",
        ]

        premium_order_flag_values_list = ["Positive Only", "Negative Only", "Both"]

        index_values_list = ["SPY", "QQQ"]

        default_values_for_sec_type_parameters = [
            "stk_currency",
            "opt_lot_size",
            "stk_exchange",
            "opt_currency",
            "opt_exchange",
            "fut_currency",
            "fut_exchange",
            "fut_lot_size",
            "fop_currency",
            "fop_exchange",
            "fop_lot_size",
        ]

        self.selected_row = None

        def on_double_click(event):
            entry.place_forget()
            combo_box.place_forget()

            # Get the item selected
            item = self.user_inputs_table.identify("item", event.x, event.y)

            column = self.user_inputs_table.identify_column(event.x)

            self.selected_row = item

            user_input_name = item.split("|")[0]

            if column not in ["#2"]:
                return

            # Position the entry widget over the cell
            x, y, width, height = self.user_inputs_table.bbox(item, column)

            if user_input_name in entry_list:
                entry.place(x=x, y=y, width=width, height=height)

                # Set the entry widget's text to the cell's value
                entry.delete(0, tk.END)
                entry.insert(
                    0, self.user_inputs_table.item(item, "values")[int(column[1:]) - 1]
                )

                # Focus on the entry widget
                entry.focus()

            else:
                combo_box.place(x=x, y=y, width=width, height=height)

                values_list = []

                if user_input_name in true_or_false_inputs:
                    # Clear the current options and set new ones
                    combo_box["values"] = true_false_list

                elif user_input_name == "target_timezone":
                    # Clear the current options and set new ones
                    combo_box["values"] = time_zone_list

                elif user_input_name == "account_parameter_for_order_quantity":
                    # Clear the current options and set new ones
                    combo_box["values"] = account_parameters_list

                elif user_input_name in and_or_parameters:
                    # Clear the current options and set new ones
                    combo_box["values"] = and_or_list

                elif user_input_name in limit_price_for_execution_engine_parameter:
                    # Clear the current options and set new ones
                    combo_box["values"] = (
                        limit_price_for_execution_engine_parameter_list
                    )

                elif user_input_name == "ib_algo_priority":
                    # Clear the current options and set new ones
                    combo_box["values"] = ib_algo_priority_list

                elif user_input_name == "flag_relative_atr_in_range":
                    # Clear the current options and set new ones
                    combo_box["values"] = flag_relative_atr_in_range_list

                elif user_input_name == "hv_method":
                    # Clear the current options and set new ones
                    combo_box["values"] = hv_methods_list

                elif user_input_name in candle_input_parameters:
                    # Clear the current options and set new ones
                    combo_box["values"] = candle_size_list

                elif user_input_name == "flag_range_order":
                    # Clear the current options and set new ones
                    combo_box["values"] = flag_range_order_values_list

                elif user_input_name in premium_order_parameter_list:
                    # Clear the current options and set new ones
                    combo_box["values"] = premium_order_flag_values_list

                elif user_input_name == "index_select_for_beta_column":
                    # Clear the current options and set new ones
                    combo_box["values"] = index_values_list

                # get the values of the selected row
                values = self.user_inputs_table.item(item, "values")

                # get selcted option
                selected_option = values[1]

                # get list values
                list_values = combo_box["values"]

                try:
                    # set initial option
                    combo_box.current(list_values.index(selected_option))

                except Exception as e:
                    combo_box.current(0)

                    if variables.flag_debug_mode:
                        print(f"Exception inside combo box option setting, Exp: {e}")

                # Focus on the entry widget
                combo_box.focus()

        def on_entry_validate():
            # Save the edited value to the table and hide the entry widg
            selected_item = self.selected_row

            user_input_name_to_validate = self.selected_row.split("|")[0]

            # parse ini file
            configur = configparser.ConfigParser()
            configur.read("user_inputs.ini")

            self.selected_row = None

            # Check if new value is from textbox
            if user_input_name_to_validate in entry_list:
                new_value = entry.get().strip()

                # Check if user input require integer input or not
                if user_input_name_to_validate in int_valid_list:
                    if not new_value.isnumeric():
                        # Error Message
                        error_title = error_string = (
                            f"Error - Value for {user_input_name_to_validate} must be numeric"
                        )

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                # Check if user input require float input or not
                elif user_input_name_to_validate in float_valid_list:
                    if not is_float(new_value):
                        # Error Message
                        error_title = error_string = (
                            f"Error - Value for {user_input_name_to_validate} must be decimal"
                        )

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

            else:
                new_value = combo_box.get().strip()

            # print([user_input_name_to_validate, new_value])

            configur.set("USER INPUTS", user_input_name_to_validate, new_value)

            # Check if type of value and convert new value based on type
            if new_value in ["True", "False"]:
                if new_value == "True":
                    new_value = True

                else:
                    new_value = False

            elif new_value.isnumeric():
                new_value = int(new_value)

            elif is_float(new_value):
                new_value = float(new_value)

            elif new_value in candle_size_list:
                new_value = get_candle_size(new_value)

            elif new_value in hv_methods_list:
                new_value = get_hv_method(new_value)

            # Set new value to user input
            setattr(variables, user_input_name_to_validate, new_value)
            setattr(UserInputs, user_input_name_to_validate, new_value)

            # Special case of timezone variable
            if user_input_name_to_validate == "target_timezone":
                variables.target_timezone_obj = pytz.timezone(variables.target_timezone)

            # Writing our configuration file to 'example.ini'
            with open("user_inputs.ini", "w") as configfile:
                configur.write(configfile)

            if user_input_name_to_validate in default_values_for_sec_type_parameters:
                # Change value of combo creation default values

                variables.defaults = {
                    "STK": [
                        UserInputs.stk_currency,
                        UserInputs.stk_exchange,
                        variables.stk_lot_size,
                    ],
                    "OPT": [
                        UserInputs.opt_currency,
                        UserInputs.opt_exchange,
                        UserInputs.opt_lot_size,
                    ],
                    "FUT": [
                        UserInputs.fut_currency,
                        UserInputs.fut_exchange,
                        UserInputs.fut_lot_size,
                    ],
                    "FOP": [
                        UserInputs.fop_currency,
                        UserInputs.fop_exchange,
                        UserInputs.fop_lot_size,
                    ],
                }

            # Update user input table
            self.update_uer_inputs_table()

            # Remove input fields
            entry.place_forget()
            combo_box.place_forget()

        # Bind on click methods
        entry.bind("<Return>", lambda e: on_entry_validate())

        combo_box.bind("<Return>", lambda e: on_entry_validate())

        # Bind the double-click event to the Treeview widget
        self.user_inputs_table.bind("<Double-1>", on_double_click)

        # update filter table
        self.update_uer_inputs_table()

    # Method to define user inputs tab right click options
    def user_inputs_table_right_click(self, event):
        # get the Treeview row that was clicked
        row = self.user_inputs_table.identify_row(event.y)

        if row:
            # select the row
            self.user_inputs_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.user_inputs_table, tearoff=0)
            menu.add_command(
                label="Update User Input",
                # command=lambda: self.activate_filter_condition(),
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    # Method to update user input table rows
    def update_uer_inputs_table(self):
        # parse ini file
        parser = configparser.ConfigParser()
        parser.read("user_inputs.ini")

        # get table id
        table_ids_list = self.user_inputs_table.get_children()

        # delete existing rows
        for table_id_item in table_ids_list:
            self.user_inputs_table.delete(table_id_item)

        # init
        user_inputs_name_list = []
        user_inputs_value_list = []
        user_inputs_description_list = [
            "IPv4 address for connecting TWS.",
            "Network port for connecting TWS.",
            "It is a unique identifier that represents a connection to the TWS trading platform.",
            "It is a unique identifier that represents a connection to the TWS trading platform for CAS app.",
            "IBKR account number",
            "When set to True the Program will run in recovery mode.",
            "When set to True Historical Volatility will be Annualized else non-Annualized.",
            "When Set to True Identification steps will be printed in console.",
            "When set to True prices will be read from CSV file.",
            "When set to True extra detailed prints will printed in console",
            "When Set to True for combination all the CSV(data files) using which the values are calculated will be stored. ",
            "When Set to True for NULL values in CAS table will be replaced by updated values in cache DB table",
            "When set to true historic volatility will be calculated on daily candles.",
            "When set to True it will consider candles since start of day for relative fields else it will consider only current candle.",
            "When flag set to True Account level RM checks will be performed.",
            "When flag set to True trade level RM checks will be performed.",
            "Flag will set default value for execution engine input field.",
            "Specify time zone for application. Value for this input needs to be valid time-zone string.",
            "Select account parameter for calculating combo quantity for multi-order creation. Value of given account parameter will be used for calculating combo quantity for orders. ",
            "It decides whether to use ‘and’ or ‘or’ between series combination condition and  series ID condition.",
            "It decides which type of order to send in execution engine for leg with highest bid ask spread.",
            "Offset value to add in limit price for pegged orders.",
            "Time lookback in minutes upto which the cache data will be used in the execution system.",
            "This value is used in comparing intraday values of two separate time frames.",
            "This value is used in calculating ratio of price ranges in different time frames.",
            "This input specify priority for IB Algo Market Order.",
            "Maximum time before locks are released on the ticker.",
            "Lookback days of historic data for long term values. This input takes value in terms of days.",
            "Lock back days of historic data for ATR. This input takes value in terms of days.",
            "Number of buckets for relative atr in range indicator.",
            "Indicates which price among ‘Open’ and ‘Close’ prices to consider for relative at in range CAS indicator calculations.",
            "Methods to use to calculate historic volatility(HV).",
            "Lookback days of historic data for historic volatility values.",
            "Candle size of historic data for historic volatility values.",
            "Lookback days of historic data for volume related values.",
            "Candle size of historic data for volume related values.",
            "Lookback mins for relative volume derivative.",
            "Lookback mins for relative atr derivative.",
            "Candle size for volume magnet indicator.",
            "Maximum lookback days for volume magnet.",
            "Lookback days of historic data for support, resistance and relative field columns values.",
            "Candle size of historic data for support, resistance and relative field columns values.",
            "Specify index instrument to calculate beta value. Possible values are ‘SPY’ and ‘QQQ’",
            "Candle size of historic data for last N minutes field values.",
            "Lookback days of historic data for last N minute column values.",
            "Lookback days of historic data for ATR for order placement value.",
            "Candle size of historic data for ATR for order placement values.",
            "Percentage value to decide range of price in which support and resistance are calculated.",
            "Interval time to update long term values.",
            "Interval time to update intraday values.",
            "Interval time to update HV related values.",
            "Interval time to update volume related values.",
            "Interval time to update relative field values.",
            "Interval time to update ATR for order values.",
            "Interval time to update account parameters.",
            "Interval time to wait before performing RM check again.",
            "Interval time to update trade level RM check flags.",
            "Interval time to update filter conditions for CAS table filter feature.",
            "Interval time to update candle values for candle orders.",
            "Lookback days of historic data for trade level RM check.",
            "Decides use ‘AND’ condition or ‘OR’ condition for trade level RM check.",
            "Threshold for volume value in trade level RM check.",
            "Threshold for bid-ask spread value in trade level RM check.",
            "Threshold for bid size and ask size value in trade level RM check.",
            "Candle size for historical data for stop loss candle and take profit candle orders.",
            "To specify duration size of historical data for range orders and range schedule orders.",
            "To specify whether to consider only positive or negative premium or both for stop loss premium order.",
            "To specify whether to consider only positive or negative premium or both for take profit premium order.",
            "To specify whether to consider only positive or negative premium or both for trailing stop loss premium order.",
            "Folder path for saving historic and execution data for CAS columns.",
            "Folder path for managing custom columns.The value should valid string to indicate path available in system.",
            "Exact file path to simulate buy/ sell price for combination. ",
            "Defaults currency value for combination creation for stocks. ",
            "Defaults currency value for combination creation for options.",
            "Defaults currency value for combination creation for futures. ",
            "Defaults currency value for combination creation for future options. ",
            "Defaults exchange value for combination creation for stocks.",
            "Defaults exchange value for combination creation for options.",
            "Defaults exchange value for combination creation for futures.",
            "Defaults exchange value for combination creation for future options.",
            "Defaults lot size for combination creation for options.",
            "Defaults lot size for combination creation for futures.",
            "Defaults lot size for combination creation for future options.",
        ]

        # get value in ini section by sction
        for sect in parser.sections():
            # get name and value from ini file for section
            for name, value in parser.items(sect):
                # append it in list
                user_inputs_name_list.append(name)

                user_inputs_value_list.append(value)

        # create df
        user_inputs_df = pd.DataFrame(
            columns=["User Input Name", "User Input Value", "User Input Description"]
        )

        # map user input to its description
        map_user_input_to_description = dict(
            zip(user_inputs_name_list, user_inputs_description_list)
        )

        map_user_input_to_value = dict(
            zip(user_inputs_name_list, user_inputs_value_list)
        )

        # User input grouping dictionary
        user_input_grouping_map_dict = {
            "IBKR Inputs": {
                "System Flags": [
                    "ibkr_tws_host",
                    "ibkr_tws_port",
                    "ibkr_tws_connection_id",
                    "ibkr_tws_connection_id_for_cas",
                    "ibkr_account_number",
                ],
                "Order Placement Related Flags": ["ib_algo_priority"],
            },
            "Flag Inputs": {
                "System Flags": [
                    "flag_recovery_mode",
                    "flag_identification_print",
                    "flag_simulate_prices",
                    "flag_debug_mode",
                    "flag_store_cas_tab_csv_files",
                    "flag_series_condition",
                ],
                "Risk Management Flags": [
                    "flag_enable_rm_account_rules",
                    "flag_enable_trade_level_rm",
                    "flag_use_execution_engine",
                    "flag_rm_checks_trade_volume_and_or",
                ],
                "Indicator Related Flags": [
                    "flag_enable_hv_annualized",
                    "flag_cache_data",
                    "flag_hv_daily",
                    "flag_since_start_of_day_candles_for_relative_fields",
                    "flag_relative_atr_in_range",
                ],
                "Order Placement Related Flags": [
                    "flag_range_order",
                    "flag_stop_loss_premium",
                    "flag_take_profit_premium",
                    "flag_trailing_stop_loss_premium",
                ],
            },
            "Timezone Inputs": ["target_timezone"],
            "Parameter Inputs": {
                "Risk Management Flags": [
                    "limit_price_selection_for_execution_engine",
                    "offset_value_execution_engine",
                    "trade_level_rm_check_volume_lookback_mins",
                    "volume_threshold_trade_rm_check",
                    "bid_ask_spread_threshold_trade_rm_check",
                    "bid_ask_qty_threshold_trade_rm_check",
                ],
                "Indicator Related Flags": [
                    "time_frame_for_price_comparison_in_intraday",
                    "time_frame_for_price_range_ratio_in_intraday",
                    "relative_atr_in_range_number_of_buckets",
                    "hv_method",
                    "index_select_for_beta_column",
                    "support_resistance_range_percent",
                ],
                "Order Placement Related Flags": [
                    "account_parameter_for_order_quantity",
                    "max_wait_time_for_order_fill",
                ],
            },
            "Candle Size Selection": {
                "Indicator Related Flags": [
                    "hv_candle_size",
                    "volume_related_fileds_candle_size",
                    "volume_magnet_candle_size",
                    "support_resistance_and_relative_fields_candle_size",
                    "last_n_minutes_fields_candle_size",
                ],
                "Order Placement Related Flags": [
                    "order_parameter_atr_candle_size",
                    "order_parameter_candle_candle_size",
                ],
            },
            "Lookback Duratioon Inputs": {
                "Indicator Related Flags": [
                    "cas_number_of_days",
                    "hv_look_back_days",
                    "volume_related_fileds_look_back_days",
                    "relative_volume_derivation_lookback_mins",
                    "relative_atr_derivation_lookback_mins",
                    "volume_magnet_max_lookback_days",
                    "support_resistance_and_relative_fields_look_back_days",
                    "last_n_minutes_fields_lookback_days",
                ],
                "Order Placement Related Flags": [
                    "order_parameter_atr_lookback_days",
                    "atr_number_of_days",
                ],
            },
            "Interval Inputs": {
                "Indicator Related Flags": [
                    "cas_long_term_fields_update_interval",
                    "cas_intraday_fields_update_interval",
                    "hv_related_fields_update_interval_time",
                    "volume_related_fields_update_interval_time",
                    "support_resistance_and_relative_fields_update_interval_time",
                    "filter_conditions_update_interval",
                ],
                "Risk Managmenet Flags": [
                    "account_table_update_interval",
                    "rm_checks_interval_if_failed",
                    "trade_rm_check_update_interval",
                ],
                "Order Placement Related Flags": [
                    "atr_for_order_interval",
                    "candle_for_order_interval",
                ],
            },
            "Combination Creation Default Values Inputs": [
                "stk_currency",
                "opt_currency",
                "fut_currency",
                "fop_currency",
                "stk_exchange",
                "opt_exchange",
                "fut_exchange",
                "fop_exchange",
                "opt_lot_size",
                "fut_lot_size",
                "fop_lot_size",
            ],
            "File Path Inputs": [
                "cas_tab_csv_file_path",
                "custom_columns_json_csv_file_path",
                "buy_sell_csv",
            ],
        }

        # Get grouped user input names, values, and descriptions
        user_inputs_name_list, user_inputs_value_list, user_inputs_description_list = (
            self.group_user_inputs(
                user_input_grouping_map_dict,
                map_user_input_to_description,
                map_user_input_to_value,
            )
        )

        # set values for df columns
        user_inputs_df["User Input Name"] = user_inputs_name_list

        user_inputs_df["User Input Value"] = user_inputs_value_list

        user_inputs_df["User Input Description"] = user_inputs_description_list

        # init
        counter = 0

        tag_name = f"bold"
        self.user_inputs_table.tag_configure(
            tag_name, font=("TkDefaultFont", 10, "bold")
        )

        # iterate rows of dataframe
        for indx, row in user_inputs_df.iterrows():
            # get table id vaue
            table_id = row["User Input Name"] + "|" + str(counter)

            user_input_name = row["User Input Name"]

            user_input_value = row["User Input Value"]

            # convert row to tuple
            row = tuple(row) + (table_id,)

            # insert row in table
            if counter % 2 == 1:
                self.user_inputs_table.insert(
                    "",
                    "end",
                    iid=table_id,
                    values=row,
                    tags=("oddrow",),
                )

                # Make group name bold
                if user_input_value in [""]:
                    self.user_inputs_table.item(table_id, tags=(tag_name, "oddrow"))

            # insert row in table
            else:
                self.user_inputs_table.insert(
                    "",
                    "end",
                    iid=table_id,
                    values=row,
                    tags=("evenrow",),
                )

                # Make group name bold
                if user_input_value in [""]:
                    self.user_inputs_table.item(table_id, tags=(tag_name, "evenrow"))

            # Keep space between two groups
            if user_input_name in [""]:
                self.user_inputs_table.item(table_id, tags=(tag_name,))

            counter += 1

    # Method to group user inputs
    def group_user_inputs(
        self,
        user_input_grouping_map_dict,
        map_user_input_to_description,
        map_user_input_to_value,
    ):
        # Init
        user_input_list = []

        user_input_value_list = []

        user_input_desciption_list = []

        flag_first_group = True

        # Iterate every group
        for group, subgroup in user_input_grouping_map_dict.items():
            # Check flag for first group
            if not flag_first_group:
                # Append empty values
                user_input_list.append("")

                user_input_value_list.append("")

                user_input_desciption_list.append("")

            # Append group to table
            user_input_list.append(group)

            user_input_value_list.append("")

            user_input_desciption_list.append("")

            # Make flag false after first group
            flag_first_group = False

            # Check if subgroup is dictionary
            if isinstance(subgroup, dict):
                # Iterate items in subgroup
                for sub_group, user_inputs_list in subgroup.items():
                    # Append subgroup to table values
                    user_input_list.append(sub_group)

                    user_input_value_list.append("")

                    user_input_desciption_list.append("")

                    # Iterate user input names in subgroup
                    for user_input_item in user_inputs_list:
                        # Append values to table values
                        user_input_list.append(user_input_item)

                        user_input_value_list.append(
                            map_user_input_to_value[user_input_item]
                        )

                        user_input_desciption_list.append(
                            map_user_input_to_description[user_input_item]
                        )

            else:
                # Iterate user inputs in group
                for user_input_item_in_subgroup in subgroup:
                    # Append values to table values
                    user_input_list.append(user_input_item_in_subgroup)

                    user_input_value_list.append(
                        map_user_input_to_value[user_input_item_in_subgroup]
                    )

                    user_input_desciption_list.append(
                        map_user_input_to_description[user_input_item_in_subgroup]
                    )

        return user_input_list, user_input_value_list, user_input_desciption_list
