import asyncio
import configparser
import copy
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog
import uuid
from tkinter import Scrollbar, messagebox, ttk

import pandas as pd
from com.identify_trading_class_for_fop import (
    identify_the_trading_class_for_all_the_fop_leg_in_combination_async,
)
from option_combo_scanner.gui.house_keeping import HouseKeepingGUI

from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.strategy.scanner_config import Config
from option_combo_scanner.strategy.scanner_config_leg import ConfigLeg
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)
from com.variables import variables
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.strategy.instrument import Instrument

MESSAGE_TIME_IN_SECONDS = 6  # in seconds

# Name, Width, Heading
instruments_table_columns_width = [
    ("InstrumentID", 170, "Instrument ID"),
    ("Symbol", 170, "Symbol"),
    ("SecType", 170, "SecType"),
    ("Multiplier", 170, "Multiplier"),
    ("Exchange", 170, "Exchange"),
    ("TradingClass", 170, "Trading Class"),
    ("Currency", 170, "Currency"),
    ("Conid", 170, "Conid"),
    ("PrimaryExchange", 170, "Primary Exchange"),
]

leg_config_table_columns_width = [
    ("LegNo", 190, "Leg No"),
    ("InstrumentID", 191, "Instrument ID"),
    ("Action", 190, "Action"),
    ("Right", 190, "Right"),
    ("MinDelta", 190, "MinDelta"),
    ("MaxDelta", 190, "MaxDelta"),
    ("MinDTE", 190, "MinDTE"),
    ("MaxDTE", 190, "MaxDTE"),

]


class ScannerInputsTab:
    # List of Templates Mapping to path
    dropdown_file_mapping = {
        'Bull Call Spread': 'Bull Call Spread.csv',
        'Bear Call Spread': 'Bear Call Spread.csv',
        'Bull Put Spread': 'Bull Put Spread.csv',
        'Bear Put Spread': 'Bear Put Spread.csv',
        'Calendar Call Spread': 'Calendar Call Spread.csv',
        'Calendar Put Spread': 'Calendar Put Spread.csv',
        'Iron Condor': 'Iron Condor.csv',
        'Iron Fly': 'Iron Fly.csv',
        'Straddle': 'Straddle.csv',
        'Strangle': 'Strangle.csv',
        # Add more mappings for other dropdown options
    }

    def __init__(self, scanner_inputs_tab):

        # Mapping the directory for Templates
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_dir = os.path.abspath(os.path.join(script_dir, '..', '..'))
        self.templates_dir = os.path.join(project_root_dir, 'Templates')

        # Update file paths in the mapping to point to the templates directory
        for key, filename in self.dropdown_file_mapping.items():
            full_path = os.path.join(self.templates_dir, filename)
            self.dropdown_file_mapping[key] = full_path


        self.flag_legs_config_table_in_readonly_state = True
        self.scanner_inputs_tab = scanner_inputs_tab

        self.create_scanner_inputs_tab()
        
    def create_scanner_inputs_tab(self):
        self.create_instrument_table()
        self.create_configuration_inputs_and_table()

        HouseKeepingGUI.dump_all_instruments_in_instrument_tab(self)
        HouseKeepingGUI.dump_config_in_gui(self)

    def create_instrument_table(
        self,
    ):
        # Create Treeview Frame for active combo table
        add_instrument_frame = ttk.Frame(self.scanner_inputs_tab, padding=20)
        add_instrument_frame.pack(pady=20)
        # Create the "Clear Table" button
        add_instrument_button = ttk.Button(
            add_instrument_frame,
            text="Add Instrument",
            command=lambda: self.create_instrument_popup(),
        )


        add_instrument_button.grid(column=1, row=0, padx=5, pady=5)

        # Force Start Scan Button
        force_start_scan_button = ttk.Button(
            add_instrument_frame,
            text="Force Start Scan",
            command=lambda: self.force_start_scan_button_click(),
        )

        force_start_scan_button.grid(column=3, row=0, padx=5, pady=5)

        # Place in center
        add_instrument_frame.place(relx=0.5, anchor=tk.CENTER)
        add_instrument_frame.place(y=30)

        instrument_table_frame = ttk.Frame(self.scanner_inputs_tab, padding=20)
        instrument_table_frame.pack(pady=20)

        # Place in center
        instrument_table_frame.place(relx=0.5, anchor=tk.CENTER)
        instrument_table_frame.place(y=210)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(instrument_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.instrument_table = ttk.Treeview(
            instrument_table_frame,
            yscrollcommand=tree_scroll.set,
            height=10,
            selectmode="extended",
        )
        # Pack to the screen
        self.instrument_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.instrument_table.yview)

        # Column in order book table
        self.instrument_table["columns"] = [
            _[0] for _ in instruments_table_columns_width
        ]

        # Creating Columns
        self.instrument_table.column("#0", width=0, stretch="no")
        # Create Headings
        self.instrument_table.heading("#0", text="", anchor="w")

        for col_name, col_width, col_heading in instruments_table_columns_width:
            self.instrument_table.column(col_name, anchor="center", width=col_width)
            self.instrument_table.heading(col_name, text=col_heading, anchor="center")

        # Back ground
        self.instrument_table.tag_configure("oddrow", background="white")
        self.instrument_table.tag_configure("evenrow", background="lightblue")

        self.instrument_table.bind("<Button-3>", self.instrument_table_right_click_menu)

    def force_start_scan_button_click(self):
        strategy_variables.flag_force_restart_scanner = True

    def instrument_table_right_click_menu(self, event):
        # get the Treeview row that was clicked
        row = self.instrument_table.identify_row(event.y)
        if row:
            # select the row
            self.instrument_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.instrument_table, tearoff=0)
            menu.add_command(
                label="Delete Instrument",
                command=lambda: self.delete_selected_instrument(),
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    def remove_row_from_instrument_table(self, list_of_instrument_ids: list):
        all_instrument_ids = self.instrument_table.get_children()

        for instrument_id in list_of_instrument_ids:
            if str(instrument_id) in all_instrument_ids:
                self.instrument_table.delete(instrument_id)

        for index, row_id in enumerate(self.instrument_table.get_children()):
            if index % 2 == 0:
                self.instrument_table.item(row_id, tags=("evenrow",))
            else:
                self.instrument_table.item(row_id, tags=("oddrow",))
                    

    def delete_selected_instrument(
        self,
    ):
        # Instrument ID
        instrument_id = self.instrument_table.selection()[
            0
        ]  # get the item ID of the selected row
        instrument_id = int(instrument_id)

        self.remove_instruments([int(instrument_id)])

    def remove_instruments(self, list_of_instrument_ids: list):
        for instrument_id in list_of_instrument_ids:
            where_clause = f"WHERE instrument_id = {instrument_id}"
            # Database Remove
            is_deleted = SqlQueries.delete_from_db_table(
                table_name="instrument_table", where_clause=where_clause
            )

            if not is_deleted:
                Utils.display_message_popup(
                    "Error",
                    f"Unable to delete the Instrument, Instrument ID: {instrument_id}",
                )

            # Remove GUI
            self.remove_row_from_instrument_table([instrument_id])

            # Remove from system
            instrument_obj = strategy_variables.map_instrument_id_to_instrument_object[
                int(instrument_id)
            ]
            instrument_obj.remove_from_system()

            # Remove all the rows from the scanner combination table
            Utils.remove_row_from_scanner_combination_table(instrument_id=instrument_id)
            Utils.remove_row_from_indicator_table(instrument_id=instrument_id)

    def add_instrument(
        self,
        sec_type,
        symbol,
        multiplier,
        exchange,
        trading_class,
        currency,
        conid,
        primary_exchange,
    ):
        values_dict = {
            "symbol": symbol.upper(),
            "sec_type": sec_type,
            "currency": currency,
            "multiplier": multiplier,
            "exchange": exchange,
            "trading_class": trading_class.upper(),
            "conid": conid,
            "primary_exchange": primary_exchange,
        }

        where_condition = f" WHERE `symbol` = '{symbol}' AND `sec_type` = '{sec_type}' AND `trading_class` = '{trading_class}';"

        select_query = SqlQueries.create_select_query(
            table_name="instrument_table",
            columns="`symbol`",
            where_clause=where_condition,
        )

        existing_instrument = SqlQueries.execute_select_query(select_query)

        if existing_instrument:
            Utils.display_message_popup(
                "Error",
                "Instrument already Exist",
            )
            return
        # Insert in the database
        res, instrument_id = SqlQueries.insert_into_db_table(
            table_name="instrument_table", values_dict=values_dict
        )

        # if not inserted
        if not res:
            print(f"Insertion Failed in INstrument table: {values_dict}")
            return

        values_dict["instrument_id"] = instrument_id
        instrument_obj = Instrument(values_dict)

        self.insert_into_instrument_table(instrument_obj)

    def insert_into_instrument_table(self, instrument_obj):

        # Add instrument details to the instrument tree
        row_values = instrument_obj.get_instrument_tuple_for_gui()

        # Get the current number of items in the treeview
        num_items = len(self.instrument_table.get_children())

        if num_items % 2 == 1:
            self.instrument_table.insert(
                "",
                "end",
                iid=row_values[0],
                text=num_items + 1,
                values=row_values,
                tags=("oddrow",),
            )
        else:
            self.instrument_table.insert(
                "",
                "end",
                iid=row_values[0],
                text=num_items + 1,
                values=row_values,
                tags=("evenrow",),
            )

    def create_instrument_popup(self):
        title_string = "Add Instrument"
        num_rows = 1

        # Create a popup window with the table
        popup = tk.Toplevel()
        popup.title(title_string)
        custom_height = min(max((num_rows * 40) + 100, 170), 750)

        popup.geometry("750x" + str(custom_height))

        # Create a frame for the input fields
        input_frame = ttk.Frame(popup, padding=20)
        input_frame.pack(fill="both", expand=True)

        # Add labels and entry fields for each column in the table
        ttk.Label(input_frame, text="SecType", width=12, anchor="center").grid(
            column=0, row=0, padx=5, pady=5
        )

        ttk.Label(input_frame, text="Symbol", width=12, anchor="center").grid(
            column=1, row=0, padx=5, pady=5
        )

        ttk.Label(input_frame, text="Multiplier", width=12, anchor="center").grid(
            column=2, row=0, padx=5, pady=5
        )

        ttk.Label(input_frame, text="Exchange", width=12, anchor="center").grid(
            column=3, row=0, padx=5, pady=5
        )

        ttk.Label(input_frame, text="Trading Class", width=12, anchor="center").grid(
            column=4, row=0, padx=5, pady=5
        )

        ttk.Label(input_frame, text="Currency", width=12, anchor="center").grid(
            column=5, row=0, padx=5, pady=5
        )

        ttk.Label(input_frame, text="ConId", width=12, anchor="center").grid(
            column=6, row=0, padx=5, pady=5
        )

        ttk.Label(input_frame, text="Primary Exch.", width=12, anchor="center").grid(
            column=7, row=0, padx=5, pady=5
        )

        # Create a list of options
        sec_type_options = ["", "OPT", "FOP"]

        drop_down_items_dict = {}

        def update_textbox(
            event, currency_entry, exchange_entry, lot_size_entry, combo_new
        ):
            selected_value = combo_new.get()

            if selected_value in ["OPT", "FOP"]:
                (
                    default_currency,
                    default_exchange,
                    default_lot_size,
                ) = variables.defaults[selected_value]
                currency_entry.delete(0, tk.END)  # Clear any existing text
                currency_entry.insert(0, default_currency)

                exchange_entry.delete(0, tk.END)  # Clear any existing text
                exchange_entry.insert(0, default_exchange)

                lot_size_entry.delete(0, tk.END)  # Clear any existing text
                lot_size_entry.insert(0, default_lot_size)

        def select_opt(
            event, currency_entry, exchange_entry, lot_size_entry, combo_new
        ):
            combo_new.current(3)

            selected_value = "OPT"
            (
                default_currency,
                default_exchange,
                default_lot_size,
            ) = variables.defaults[selected_value]
            currency_entry.delete(0, tk.END)  # Clear any existing text
            currency_entry.insert(0, default_currency)

            exchange_entry.delete(0, tk.END)  # Clear any existing text
            exchange_entry.insert(0, default_exchange)

            lot_size_entry.delete(0, tk.END)  # Clear any existing text
            lot_size_entry.insert(0, default_lot_size)

        def select_fop(
            event, currency_entry, exchange_entry, lot_size_entry, combo_new
        ):
            combo_new.current(4)

            selected_value = "FOP"
            (
                default_currency,
                default_exchange,
                default_lot_size,
            ) = variables.defaults[selected_value]
            currency_entry.delete(0, tk.END)  # Clear any existing text
            currency_entry.insert(0, default_currency)

            exchange_entry.delete(0, tk.END)  # Clear any existing text
            exchange_entry.insert(0, default_exchange)

            lot_size_entry.delete(0, tk.END)  # Clear any existing text
            lot_size_entry.insert(0, default_lot_size)

        for i in range(num_rows):
            row_loc = i + 1

            drop_down_items_dict[row_loc] = {}
            sec_type_combo_box = f"sec_type_combo_box_{row_loc}"

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

            drop_down_items_dict[row_loc][sec_type_combo_box] = ttk.Combobox(
                input_frame,
                width=10,
                values=sec_type_options,
                state="readonly",
                style="Custom.TCombobox",
            )
            drop_down_items_dict[row_loc][sec_type_combo_box].current(0)
            drop_down_items_dict[row_loc][sec_type_combo_box].grid(
                column=0, row=row_loc, padx=5, pady=5
            )

            # Entry (input fields)
            symbol_entry = ttk.Entry(input_frame, width=12)

            symbol_entry.grid(column=1, row=row_loc, padx=5, pady=5)

            lot_size_entry = ttk.Entry(input_frame, width=12)
            lot_size_entry.grid(column=2, row=row_loc, padx=5, pady=5)

            exchange_entry = ttk.Entry(input_frame, width=12)
            exchange_entry.grid(column=3, row=row_loc, padx=5, pady=5)

            trading_class_entry = ttk.Entry(input_frame, width=12)
            trading_class_entry.grid(column=4, row=row_loc, padx=5, pady=5)

            currency_entry = ttk.Entry(input_frame, width=12)
            currency_entry.grid(column=5, row=row_loc, padx=5, pady=5)

            drop_down_items_dict[row_loc][sec_type_combo_box].bind(
                "o",
                lambda event, currency_entry=currency_entry, exchange_entry=exchange_entry, lot_size_entry=lot_size_entry, combo_new=drop_down_items_dict[
                    row_loc
                ][
                    sec_type_combo_box
                ]: select_opt(
                    event, currency_entry, exchange_entry, lot_size_entry, combo_new
                ),
            )
            drop_down_items_dict[row_loc][sec_type_combo_box].bind(
                "fo",
                lambda event, currency_entry=currency_entry, exchange_entry=exchange_entry, lot_size_entry=lot_size_entry, combo_new=drop_down_items_dict[
                    row_loc
                ][
                    sec_type_combo_box
                ]: select_fop(
                    event, currency_entry, exchange_entry, lot_size_entry, combo_new
                ),
            )

            drop_down_items_dict[row_loc][sec_type_combo_box].bind(
                "O",
                lambda event, currency_entry=currency_entry, exchange_entry=exchange_entry, lot_size_entry=lot_size_entry, combo_new=drop_down_items_dict[
                    row_loc
                ][
                    sec_type_combo_box
                ]: select_opt(
                    event, currency_entry, exchange_entry, lot_size_entry, combo_new
                ),
            )
            drop_down_items_dict[row_loc][sec_type_combo_box].bind(
                "FO",
                lambda event, currency_entry=currency_entry, exchange_entry=exchange_entry, lot_size_entry=lot_size_entry, combo_new=drop_down_items_dict[
                    row_loc
                ][
                    sec_type_combo_box
                ]: select_fop(
                    event, currency_entry, exchange_entry, lot_size_entry, combo_new
                ),
            )

            drop_down_items_dict[row_loc][sec_type_combo_box].bind(
                "<<ComboboxSelected>>",
                lambda event, currency_entry=currency_entry, exchange_entry=exchange_entry, lot_size_entry=lot_size_entry, combo_new=drop_down_items_dict[
                    row_loc
                ][
                    sec_type_combo_box
                ]: update_textbox(
                    event, currency_entry, exchange_entry, lot_size_entry, combo_new
                ),
            )

            conid_entry = ttk.Entry(input_frame, width=12)
            conid_entry.grid(column=6, row=row_loc, padx=5, pady=5)

            primary_exchange_entry = ttk.Entry(input_frame, width=12)
            primary_exchange_entry.grid(column=7, row=row_loc, padx=5, pady=5)

        def on_search_trading_classes_for_fop_button_click(
            search_trading_classes_for_fop_button,
        ):
            search_trading_classes_for_fop_button.config(state="disabled")

            # Get trading classes and put those trading_butto classes in new dropdown
            search_trading_classes_thread = threading.Thread(
                target=search_trading_classes_for_fop,
                args=(search_trading_classes_for_fop_button,),
            )
            search_trading_classes_thread.start()

        def search_trading_classes_for_fop(search_trading_classes_for_fop_button):
            # List of leg row values list
            leg_row_values_list = []

            try:
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

                # Replace textbox for FOP trading class with dropdown with valid classes for FOP
                def replace_textbox_with_dropdown(list_of_trading_classes):
                    # Getting result of each individual leg separately
                    for row_indx, trading_classes in enumerate(
                        list_of_trading_classes, start=1
                    ):
                        print(f"Trading class: {list_of_trading_classes}")
                        # Check if result
                        if trading_classes != []:
                            # Get the grid slave of the input frame for FOP trading class textbox
                            slave = input_frame.grid_slaves(row=row_indx, column=4)[0]

                            # Index for trading class dropdown
                            trading_class_combo_box = (
                                f"trading_class_combo_box_{row_indx}"
                            )

                            # Initialize drop down in FOP row for trading class field
                            drop_down_items_dict[row_indx][
                                trading_class_combo_box
                            ] = ttk.Combobox(
                                input_frame,
                                width=10,
                                values=trading_classes,
                                state="readonly",
                                style="Custom.TCombobox",
                            )
                            # Select first element in list off options by default
                            drop_down_items_dict[row_indx][
                                trading_class_combo_box
                            ].current(0)

                            # Put drop down in place of textbox
                            drop_down_items_dict[row_indx][
                                trading_class_combo_box
                            ].grid(row=row_indx, column=4)

                            # Remove textbox
                            slave.grid_forget()

            except Exception as e:
                # Print to console
                if variables.flag_debug_mode:
                    print(f"Exception Inside replacing textbox with drop down, is {e}")

                # Pop up window for error
                error_title = error_string = "Error, Unable to Get Trading Classes"

                variables.screen.display_error_popup(error_title, error_string)

                return

            try:
                for i in range(num_rows):
                    row_loc = i + 1

                    sec_type_combo_box = f"sec_type_combo_box_{row_loc}"

                    sec_type = (
                        drop_down_items_dict[row_loc][sec_type_combo_box].get().strip()
                    )

                    symbol = input_frame.grid_slaves(row=row_loc, column=1)[0].get()

                    lot_size = input_frame.grid_slaves(row=row_loc, column=2)[0].get()
                    exchange = (
                        input_frame.grid_slaves(row=row_loc, column=3)[0].get().strip()
                    )
                    trading_class = input_frame.grid_slaves(row=row_loc, column=4)[
                        0
                    ].get()
                    currency = (
                        input_frame.grid_slaves(row=row_loc, column=5)[0].get().strip()
                    )
                    conid = input_frame.grid_slaves(row=row_loc, column=6)[0].get()
                    primary_exchange = input_frame.grid_slaves(row=row_loc, column=7)[
                        0
                    ].get()

                    row_of_values_for_leg = [
                        "",  # action
                        sec_type,
                        symbol,
                        "",  # dte
                        "",  # delta
                        "",  # right
                        "",  # qty
                        lot_size,
                        exchange,
                        trading_class,
                        currency,
                        conid,
                        primary_exchange,
                        "",  # Strike
                        "",  # expiry
                    ]

                    leg_row_values_list.append(row_of_values_for_leg)

            except Exception as e:
                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Inside search_trading_classes_for_fop Exception occured while creating the list of all the leg values, exp: {e}"
                    )

                error_title, error_string = (
                    "Error, Searching Trading Class",
                    "Unable to read user input for the legs.",
                )

                variables.screen.display_error_popup(error_title, error_string)

                # Enabling the button
                search_trading_classes_for_fop_button.config(state="normal")

                return

            # Get all the trading classes for all the fop legs in combination
            list_of_trading_classes = asyncio.run(
                identify_the_trading_class_for_all_the_fop_leg_in_combination_async(
                    leg_row_values_list
                )
            )

            # Enabling the button
            search_trading_classes_for_fop_button.config(state="normal")

            # Set value in trading class gui
            if list_of_trading_classes != None:
                replace_textbox_with_dropdown(list(list_of_trading_classes))

        def on_add_instrument_button_click(
            add_instrument_button,
            popup,
        ):
            add_instrument_button.config(state="disabled")
            add_instrument_thread = threading.Thread(
                target=add_instrument, args=(popup, add_instrument_button)
            )
            add_instrument_thread.start()

        def add_instrument(
            popup,
            add_instrument_button,
        ):
            combo_values = []
            for i in range(num_rows):
                row_loc = i + 1

                sec_type_combo_box = f"sec_type_combo_box_{row_loc}"

                sec_type = (
                    drop_down_items_dict[row_loc][sec_type_combo_box].get().strip()
                )
                symbol = input_frame.grid_slaves(row=row_loc, column=1)[0].get()
                lot_size = input_frame.grid_slaves(row=row_loc, column=2)[0].get()
                exchange = (
                    input_frame.grid_slaves(row=row_loc, column=3)[0].get().strip()
                )
                trading_class = input_frame.grid_slaves(row=row_loc, column=4)[0].get()

                currency = (
                    input_frame.grid_slaves(row=row_loc, column=5)[0].get().strip()
                )
                conid = input_frame.grid_slaves(row=row_loc, column=6)[0].get()
                primary_exchange = input_frame.grid_slaves(row=row_loc, column=7)[
                    0
                ].get()

                combo_values.append(
                    (
                        sec_type,
                        symbol,
                        lot_size,
                        exchange,
                        trading_class,
                        currency,
                        conid,
                        primary_exchange,
                    )
                )

            # print("Combo Values: ", combo_values)

            res = self.add_instrument(*combo_values[0])

            popup.destroy()

        # Create a frame for the "Add Combo" button
        button_frame = ttk.Frame(popup)
        button_frame.place(
            relx=0.5, anchor=tk.CENTER
        )  # x=530, y=custom_height-50,width=100, height=30,  )
        button_frame.place(y=custom_height - 50)

        # Text we want to show for the button
        edit_add_instrument_button_text = "Add Instrument"

        # Create the "Add Combo" button
        add_instrument_button = ttk.Button(
            button_frame,
            text=edit_add_instrument_button_text,
            command=lambda: on_add_instrument_button_click(
                add_instrument_button,
                popup,
            ),
        )
        add_instrument_button.grid(row=0, column=0, padx=10)

        # Text we want to show for the button
        search_trading_classes_for_fop_button_text = "Search Trading Class"

        # Create the "Search trading classes for FOP" button
        search_trading_classes_for_fop_button = ttk.Button(
            button_frame,
            text=search_trading_classes_for_fop_button_text,
            command=lambda: on_search_trading_classes_for_fop_button_click(
                search_trading_classes_for_fop_button
            ),
        )
        search_trading_classes_for_fop_button.grid(row=0, column=1, padx=10)

    def update_leg_config_button_clicked(self):
        num_leg = self.no_of_legs_entry.get()

        if not Utils.is_positive_greater_than_equal_one_integer(num_leg):
            Utils.display_message_popup(
                "Error",
                f"Number of legs must be positive integer and greater than zero",
            )
            return

        config_table_len = len(self.leg_config_table.get_children())

        # Adjustment of rows based on inputs
        if int(num_leg) > config_table_len:
            self.insert_row_in_config_table_gui(
                (int(num_leg) - config_table_len), config_table_len
            )
        elif int(num_leg) < config_table_len:
            self.delete_row_in_config_table_gui((config_table_len - int(num_leg)))
        else:
            pass

        # Change the State of Leg Config Table
        # self.flag_legs_config_table_in_readonly_state = False

    def insert_row_in_config_table_gui(self, num_legs, current_row_number):

        for i in range(num_legs):

            # Entry and Combo box Inputs
            desc = current_row_number + i + 1
            instrument_id = ""
            action_value = "BUY"
            right_value = "CALL"
            delta_min_value = "0.0"
            delta_max_value = "0.0"
            dte_min_value = "0.0"
            dte_max_value = "0.0"
            right_value = "CALL"
            row_values = (desc, instrument_id, action_value, right_value, delta_min_value, delta_max_value, dte_min_value, dte_max_value)
            if i % 2 == 1:
                self.leg_config_table.insert(
                    "",
                    "end",
                    iid=desc,
                    text=desc,
                    values=row_values,
                    tags=("oddrow",),
                )
            else:
                self.leg_config_table.insert(
                    "",
                    "end",
                    iid=desc,
                    text=desc,
                    values=row_values,
                    tags=("evenrow",),
                )

    def delete_row_in_config_table_gui(
        self,
        num_legs_to_remove,
    ):
        # All the comfig_leg id in the config table
        all_config_leg_id = self.leg_config_table.get_children()

        # Remove last 'num_legs_to_remove' rows from the config_leg_table
        for config_leg_id in all_config_leg_id[-num_legs_to_remove:]:
            print(config_leg_id)
            self.leg_config_table.delete(config_leg_id)

    def create_configuration_inputs_and_table(
        self,
    ):
        
        # Create a frame for input fields
        input_fields_frame = ttk.Frame(self.scanner_inputs_tab, padding=20)
        input_fields_frame.pack()

        # Place the input fields frame just below the instrument table
        input_fields_frame.place(relx=0.5, anchor=tk.CENTER, rely=0.2, y=250)

        # dropdown for templates
        dropdown_label = ttk.Label(
            input_fields_frame, text="Template", anchor="center", width=12
        )
        dropdown_label.grid(column=0, row=0, padx=5, pady=(0, 5), sticky="n")
        dropdown_var = tk.StringVar()
        dropdown = ttk.Combobox(input_fields_frame, textvariable=dropdown_var, state="readonly")
        # getting the values for templates from map
        dropdown['values'] = tuple(self.dropdown_file_mapping.keys())
        dropdown.grid(column=0, row=1, padx=5, pady=5)

        # Bind the template which is selected
        # dropdown.bind("<<ComboboxSelected>>", lambda event: self.upload_template_from_mapped_path(dropdown_var.get()))
        template_button = ttk.Button(input_fields_frame, text='Import Template', 
                                    command=lambda: self.upload_template_from_mapped_path(dropdown_var.get()))
        template_button.grid(column=0, row=2, padx=5, pady=5)

        # Create a separator between the dropdown/button and the "#Legs" label
        separator = ttk.Separator(input_fields_frame, orient='vertical')
        separator.grid(column=1, row=0, rowspan=2, padx=5, pady=(0, 5), sticky='ns')

        # No of legs label and entry
        leg_label = ttk.Label(
            input_fields_frame, text="#Legs", anchor="center", width=12
        )
        leg_label.grid(column=2, row=0, padx=5, pady=(0, 5), sticky="n")

        self.no_of_legs_entry = ttk.Entry(input_fields_frame)
        self.no_of_legs_entry.grid(column=2, row=1, padx=5, pady=5)

        # Add Update Leg Config Button
        update_leg_config_button = ttk.Button(
            input_fields_frame,
            text="Update Legs",
            command=lambda: self.update_leg_config_button_clicked(),
        )
        update_leg_config_button.grid(column=2, row=2, padx=5, pady=5)
        save_config_button = ttk.Button(
            self.scanner_inputs_tab,
            text="Save Config",
            command=self.save_config_button_click,
        )
        save_config_button.place(x=710, y=728, width=115, height=35)
        # Create the leg_
        self.create_leg_config_editable_table()

    # Funtion for Upload Template for mapped path
    def upload_template_from_mapped_path(self, selected_option):
        # extract the file path from mapp
        file_path = self.dropdown_file_mapping.get(selected_option)
        if file_path:
            # function to upload the csv in app
            self.upload_template_from_csv_to_app(file_path)

    # Function for Template upload to app
    def upload_template_from_csv_to_app(self, template_dataframe_path):

        try:
            # get csv file from file path
            template_dataframe = pd.read_csv(template_dataframe_path)

            # Replace null values by None string
            template_dataframe = template_dataframe.fillna("")
            # print(template_dataframe.to_string())

        except Exception as e:
            # Error Message pop-up
            Utils.display_message_popup(
                "Error",
                f"Unable to read the CSV file",
            )
            # Enabled template button
            # template_button.config(state="enabled")

            return
        
        if template_dataframe.empty:
            # Error Message pop-up
            Utils.display_message_popup(
                "Error",
                f"CSV file was empty",
            )

            # Enabled upload template button
            # template_button.config(state="enabled")

            return
        
        # Check validness for the template dataframe
        is_valid = self.check_validness_for_template_df(template_dataframe)
        if not is_valid:
            return
        # Insert the template into the config leg table 
        self.insert_into_config_leg_table_through_template(template_dataframe)

    # Function to check validness of the template df
    def check_validness_for_template_df(self, template_dataframe_to_be_checked):
        # Getting list of valid columns
        columns_for_template_csv = copy.deepcopy(strategy_variables.columns_for_templates_to_csv)

        # Getting columns of dataframe to-be-checked
        template_dataframe_columns = template_dataframe_to_be_checked.columns

        # check if number of columns in csv file is correct
        if len(columns_for_template_csv) != len(template_dataframe_columns):
            Utils.display_message_popup(
                "Error",
                f"Columns are not matching in file, Number of columns is wrong",
            )
            return False


        # Check if columns in template dataframe for upload templates are valid
        for allowed_columns_name, user_input_col_name in zip(
            columns_for_template_csv, template_dataframe_columns
        ):
            if allowed_columns_name != user_input_col_name:
                Utils.display_message_popup(
                "Error",
                f"Columns are not matching in file, Invalid column: '{user_input_col_name}",
                )
                return False
        return True
            
        
    def save_config_button_click(self):
        values_dict = {
            "no_of_leg": int(self.no_of_legs_entry.get()),
        }
        # Validation on no of legs if it is greater than zero
        if not Utils.is_positive_greater_than_equal_one_integer(
            values_dict["no_of_leg"]
        ):
            Utils.display_message_popup(
                "Error",
                f"Number of legs must be positive integer greater than zero",
            )
            return

        if values_dict["no_of_leg"] != len(self.leg_config_table.get_children()):
            Utils.display_message_popup(
                "Error",
                f"Number of legs should be equal to number of row in config table",
            )
            return
        
        leg_data_list = []

        for i in range(int(self.no_of_legs_entry.get())):

            # Prepare leg-wise data
            item_values = self.leg_config_table.item(i + 1, "values")

            leg_data = {
                "leg_number": i + 1,
                "instrument_id": (item_values[1]),
                "action": item_values[2].upper(),
                "right": item_values[3].upper(),
                "delta_range_min": item_values[4],
                "delta_range_max": item_values[5],
                "dte_range_min": item_values[6],
                "dte_range_max": item_values[7],
                # Add other leg-wise data as needed
            }
            # print(leg_data)
            # For First leg only range between 0 to 1
            local_map_instrument_id_instrument_obj = copy.deepcopy(strategy_variables.map_instrument_id_to_instrument_object)
            list_of_instrument_ids = local_map_instrument_id_instrument_obj.keys()
            if not leg_data["instrument_id"].isdigit():
                Utils.display_message_popup(
                    "Error",
                    f"Instrument ID '{leg_data['instrument_id']}' is not a valid integer",
                )
                return
            if int(leg_data["instrument_id"]) not in list_of_instrument_ids:
                Utils.display_message_popup(
                    "Error",
                    f"Instrument ID doesn't exist in Instrument Table",
                )
                return
            
            if i == 0:
                if not Utils.is_between_zero_to_one(float(leg_data["delta_range_max"])):
                    Utils.display_message_popup(
                        "Error",
                        f"Delta values for the first leg should be between 0 and 1",
                    )
                    return

                if not Utils.is_between_zero_to_one(float(leg_data["delta_range_min"])):
                    Utils.display_message_popup(
                        "Error",
                        f"Delta values for the first leg should be between 0 and 1",
                    )
                    return
    
                if (float(leg_data["delta_range_min"])) > (float(leg_data["delta_range_max"])):
                    Utils.display_message_popup(
                        "Error",
                        f"MinDelta value cannot be greater than MaxDelta value",
                    )
                    return
                
            else:
                # For legs 1 onwards validation for -1 to 1 value
                # Validation
                
                if not Utils.is_between_minus_one_to_one(float(leg_data["delta_range_max"])):
                    Utils.display_message_popup(
                        "Error",
                        f"Delta values should be in between -1 to 1",
                    )
                    return

                if not Utils.is_between_minus_one_to_one(float(leg_data["delta_range_min"])):
                    Utils.display_message_popup(
                        "Error",
                        f"Delta values should be in between -1 to 1",
                    )
                    return

                if (float(leg_data["delta_range_min"])) > (float(leg_data["delta_range_max"])):
                    Utils.display_message_popup(
                        "Error",
                        f"MinDelta value cannot be greater than MaxDelta value",
                    )
                    return
            

            leg_data_list.append(leg_data)

        local_config_object = copy.deepcopy(strategy_variables.config_object)

        if local_config_object:
            if self.is_current_and_new_config_same(
                local_config_object, values_dict, leg_data_list
            ):
                print(f"Both Current and New config are same")

                # Change the legs config table state flag
                # self.flag_legs_config_table_in_readonly_state = True

                return
            else:
                print(f"Both Current and New config are different")

        is_transaction_successful, config_id = SqlQueries.run_config_update_transaction(
            common_config_dict=values_dict,
            list_of_config_legs_dict=leg_data_list,
        )

        if not is_transaction_successful:
            Utils.display_message_popup(
                "Error",
                f"Could not insert Rows in table. Please retry again",
            )
            return

        # Change the legs config table state flag
        # self.flag_legs_config_table_in_readonly_state = True

        list_of_config_leg_object = [
            ConfigLeg(config_leg_dict) for config_leg_dict in leg_data_list
        ]
        values_dict["config_id"] = config_id
        values_dict["list_of_config_leg_object"] = list_of_config_leg_object

        # Creation of Config Object  (Leg)
        config_obj = Config(values_dict)

        # Insert leg-wise data into the config_leg_table
        self.insert_into_config_leg_table(config_obj)

        # Clear all the rows from the scanner combination table
        Utils.clear_scanner_combination_table()

    def is_current_and_new_config_same(
        self, current_config_object, new_common_config_dict, new_leg_data_list
    ):

        # Default return True if same
        flag_same = True

        # current_list_of_dte = [
        #     int(dte.strip()) for dte in current_config_object.list_of_dte.split(",")
        # ]
        # new_list_of_dte = [
        #     int(dte.strip()) for dte in new_common_config_dict["list_of_dte"].split(",")
        # ]

        # Right
        # if current_config_object.right != new_common_config_dict["right"]:
        #     return not flag_same
        # # No of Legs
        if current_config_object.no_of_leg != int(new_common_config_dict["no_of_leg"]):
            return not flag_same
        # List of DTE
        # if set(new_list_of_dte) != set(current_list_of_dte):
        #     return not flag_same
        # current_list_of_config_leg_objects
        current_list_of_config_leg_objects = (
            current_config_object.list_of_config_leg_object
        )


        # Number of legs must be equal
        if len(current_list_of_config_leg_objects) != len(new_leg_data_list):
            return not flag_same

        for prev_leg_object, new_leg_data_dict in zip(
            current_list_of_config_leg_objects, new_leg_data_list
        ):
            if prev_leg_object.instrument_id != new_leg_data_dict["instrument_id"]:
                return not flag_same
            

            if prev_leg_object.action != new_leg_data_dict["action"]:
                return not flag_same
            
            if prev_leg_object.right != new_leg_data_dict["right"]:
                return not flag_same
            
            if prev_leg_object.delta_range_max != float(
                new_leg_data_dict["delta_range_max"]
            ):
                return not flag_same
            # New right addition in different and same condition
            
            if prev_leg_object.delta_range_min != float(
                new_leg_data_dict["delta_range_min"]
            ):
                return not flag_same
            if prev_leg_object.dte_range_max != float(
                new_leg_data_dict["dte_range_max"]
            ):
                return not flag_same
            # New DTE addition in different and same condition
            
            if prev_leg_object.dte_range_min != float(
                new_leg_data_dict["dte_range_min"]
            ):
                return not flag_same

        return flag_same

    def insert_into_config_leg_table(self, config_leg_obj):
        self.leg_config_table.delete(*self.leg_config_table.get_children())
        list_of_config_leg_objects = config_leg_obj.get_config_tuple_for_gui()

        (
            _,
            leg_number,
            list_of_config_leg_object,
        ) = list_of_config_leg_objects
        for leg_obj in list_of_config_leg_object:
            self.insert_into_config_leg_table_helper(leg_obj)

    def insert_into_config_leg_table_through_template(self, dataframe):
        self.leg_config_table.delete(*self.leg_config_table.get_children())
        # self.no_of_legs_entry.delete(*self.no_of_legs_entry)
        self.no_of_legs_entry.delete(0, tk.END)
        self.no_of_legs_entry.insert(0, len(dataframe))


        # Iterate over rows of the DataFrame
        for index, row in dataframe.iterrows():
            row_values = tuple(row)
            # print(row_values)
            # Get the current number of items in the treeview
            num_items = len(self.leg_config_table.get_children())

            if num_items % 2 == 1:
                self.leg_config_table.insert(
                    "",
                    "end",
                    iid=row_values[0],
                    text=num_items + 1,
                    values=row_values,
                    tags=("oddrow",),
                )
            else:
                self.leg_config_table.insert(
                    "",
                    "end",
                    iid=row_values[0],
                    text=num_items + 1,
                    values=row_values,
                    tags=("evenrow",),
                )

    def insert_into_common_config_table_helper(self, config_obj):
        _, no_of_legs, _ = config_obj.get_config_tuple_for_gui()
        self.no_of_legs_entry.insert(0, no_of_legs)
        

    def insert_into_config_leg_table_helper(self, leg_obj):
        row_values = leg_obj.get_config_leg_tuple_for_gui()

        # Get the current number of items in the treeview
        num_items = len(self.leg_config_table.get_children())

        if num_items % 2 == 1:
            self.leg_config_table.insert(
                "",
                "end",
                iid=row_values[0],
                text=num_items + 1,
                values=row_values,
                tags=("oddrow",),
            )
        else:
            self.leg_config_table.insert(
                "",
                "end",
                iid=row_values[0],
                text=num_items + 1,
                values=row_values,
                tags=("evenrow",),
            )

    def create_leg_config_editable_table(self):

        leg_config_table_frame = ttk.Frame(self.scanner_inputs_tab, padding=20)
        leg_config_table_frame.pack(pady=20)

        # Place in center
        leg_config_table_frame.place(relx=0.5, anchor=tk.CENTER)
        leg_config_table_frame.place(y=600)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(leg_config_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.leg_config_table = ttk.Treeview(
            leg_config_table_frame,
            yscrollcommand=tree_scroll.set,
            height=8,
            selectmode="extended",
        )
        # Pack to the screen
        self.leg_config_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.leg_config_table.yview)

        # Column in order book table
        self.leg_config_table["columns"] = [
            _[0] for _ in leg_config_table_columns_width
        ]

        # Creating Columns
        self.leg_config_table.column("#0", width=0, stretch="no")
        # Create Headings
        self.leg_config_table.heading("#0", text="", anchor="w")

        for col_name, col_width, col_heading in leg_config_table_columns_width:
            self.leg_config_table.column(col_name, anchor="center", width=col_width)
            self.leg_config_table.heading(col_name, text=col_heading, anchor="center")

        # Back ground
        self.leg_config_table.tag_configure("oddrow", background="white")
        self.leg_config_table.tag_configure("evenrow", background="lightblue")
        
        # self.leg_config_table.window_create("", window=right_combobox)

        # Create an Entry widget
        self.entry = tk.Entry(leg_config_table_frame)
        # Create combo box
        self.combo_box_action = ttk.Combobox(
            leg_config_table_frame,
            state="readonly",
            style="Custom.TCombobox",
        )
        self.combo_box_right = ttk.Combobox(
            leg_config_table_frame,
            state="readonly",
            style="Custom.TCombobox",
        )
        
        
        # Bind the <Configure> event of the scrollbar to on_scroll function
        self.leg_config_table.bind("<Configure>", self.forget_entry_end_combo)

        # Bind the mouse wheel event to the Treeview
        self.leg_config_table.bind("<MouseWheel>", self.forget_entry_end_combo)
        self.leg_config_table.bind("<Double-1>", self.on_double_click)
        # # Bind on click methods
        # self.entry.bind('<Return>', lambda e: self.on_entry_validate)
        # self.combo_box.bind('<Return>', lambda e: self.on_entry_validate)

    def forget_entry_end_combo(self, event):

        # Your action upon scrolling goes here
        try:
            self.entry.place_forget()
        except Exception as e:
            pass
        try:
            self.combo_box.place_forget()
        except Exception as e:
            pass

    def on_double_click(self, event):
        self.forget_entry_end_combo(event)

        # Get the item and column clicked
        item = self.leg_config_table.identify("item", event.x, event.y)
        column = self.leg_config_table.identify_column(event.x)

        # Ensure that the double click is on a cell containing editable data
        if item and column:
            column_index = int(column.replace("#", ""))

            # Check if the column is editable (exclude the first column, which represents the LegNo)
            if column_index != 0:
                # Get the position and dimensions of the cell
                x, y, width, height = self.leg_config_table.bbox(item, column)

                # Determine the current value in the cell
                current_value = self.leg_config_table.item(item, "values")[column_index - 1]

                # Destroy any existing Combobox or Entry widget
                if hasattr(self, "combo_box"):
                    self.combo_box.destroy()
                if hasattr(self, "entry"):
                    self.entry.destroy()

                # Create Combobox for Action column
                if column_index == 1:
                    return
                if column_index == 3:  
                    self.combo_box_action = ttk.Combobox(self.leg_config_table, values=["BUY", "SELL"], state="readonly")
                    self.combo_box_action.set(current_value)
                    self.combo_box_action.place(x=x, y=y, width=width, height=height)
                    self.combo_box_action.bind("<Return>", lambda event: self.save_combobox_changes(item, column_index))
                    self.combo_box_action.bind("<FocusOut>", lambda event: self.combo_box_action.destroy())

                # Create Combobox for Right column
                elif column_index == 4:
                    self.combo_box_right = ttk.Combobox(self.leg_config_table, values=["CALL", "PUT"], state="readonly")
                    self.combo_box_right.set(current_value)
                    self.combo_box_right.place(x=x, y=y, width=width, height=height)
                    self.combo_box_right.bind("<Return>", lambda event: self.save_combobox_changes(item, column_index))
                    self.combo_box_right.bind("<FocusOut>", lambda event: self.combo_box_right.destroy())

                # Create Entry for other columns
                else:
                    self.entry = ttk.Entry(self.leg_config_table)
                    self.entry.insert(0, current_value)
                    self.entry.place(x=x, y=y, width=width, height=height)
                    self.entry.bind("<Return>", lambda event: self.save_entry_changes(item, column_index))
                    self.entry.bind("<FocusOut>", lambda event: self.entry.destroy())
                    self.entry.focus_set()

    def save_combobox_changes(self, item, column_index):
        if column_index == 3:
            new_value = self.combo_box_action.get()
            self.leg_config_table.set(item, "#3", new_value)  # Use "#3" instead of column_index
            self.combo_box_action.destroy()
            self.leg_config_table.focus_set()
        elif column_index == 4:
            new_value = self.combo_box_right.get()
            self.leg_config_table.set(item, "#4", new_value)  # Use "#4" instead of column_index
            self.combo_box_right.destroy()
            self.leg_config_table.focus_set()

    def save_entry_changes(self, item, column_index):
        new_value = self.entry.get()
        self.leg_config_table.set(item, "#{}".format(column_index), new_value)  # Use "#{}".format(column_index) instead of column_index
        self.entry.destroy()


        

    def on_entry_validate(
        self,
    ):
        print(f"on_entry_validate")
        # Remove input fields
        self.entry.place_forget()
        self.combo_box.place_forget()
        return
        # Update user input table
        # self.update_uer_inputs_table()

        # Remove input fields
        entry.place_forget()
        combo_box.place_forget()

    # Method to define user inputs tab right click options
    def user_inputs_table_right_click(self, event):
        print(f"user_inputs_table_right_click")
        return
