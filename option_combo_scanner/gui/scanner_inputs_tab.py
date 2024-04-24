import asyncio
import configparser
import copy
import os
import threading
import time
import tkinter as tk
import uuid
from tkinter import Scrollbar, filedialog, messagebox, ttk

import pandas as pd

from com.identify_trading_class_for_fop import identify_the_trading_class_for_all_the_fop_leg_in_combination_async
from com.variables import variables
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.house_keeping import HouseKeepingGUI
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.strategy.instrument import Instrument
from option_combo_scanner.strategy.scanner_config import Config
from option_combo_scanner.strategy.scanner_config_leg import ConfigLeg
from option_combo_scanner.strategy.strategy_variables import StrategyVariables as strategy_variables

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
    ("LegNo", 170, "Leg No"),
    ("InstrumentID", 170, "Instrument ID"),
    ("Action", 170, "Action"),
    ("Right", 170, "Right"),
    ("Quantity", 170, "Quantity"),
    ("MinDelta", 170, "MinDelta"),
    ("MaxDelta", 170, "MaxDelta"),
    ("MinDTE", 170, "MinDTE"),
    ("MaxDTE", 170, "MaxDTE"),
]

leg_config_manager_table_columns_width = [
    ("Config ID", 182, "ConfigID"),
    ("Name", 182, "ConfigName"),
    ("Description", 982, "Description"),
    ("Status", 182, "Status"),
]


class ScannerInputsTab:
    # List of Templates Mapping to path
    dropdown_file_mapping = {
        "Bull Call Spread": "Bull Call Spread.csv",
        "Bear Call Spread": "Bear Call Spread.csv",
        "Bull Put Spread": "Bull Put Spread.csv",
        "Bear Put Spread": "Bear Put Spread.csv",
        "Calendar Call Spread": "Calendar Call Spread.csv",
        "Calendar Put Spread": "Calendar Put Spread.csv",
        "Iron Condor": "Iron Condor.csv",
        "Iron Fly": "Iron Fly.csv",
        "Straddle": "Straddle.csv",
        "Strangle": "Strangle.csv",
        # Add more mappings for other dropdown options
    }

    def __init__(self, scanner_inputs_tab):

        # Mapping the directory for Templates
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root_dir = os.path.abspath(os.path.join(script_dir, "..", ".."))
        self.templates_dir = os.path.join(project_root_dir, "Templates")

        # Update file paths in the mapping to point to the templates directory
        for key, filename in self.dropdown_file_mapping.items():
            full_path = os.path.join(self.templates_dir, filename)
            self.dropdown_file_mapping[key] = full_path

        self.flag_legs_config_table_in_readonly_state = True
        self.scanner_inputs_tab = scanner_inputs_tab
        self.last_edited_config_id = None
        self.last_edited_name = None
        self.last_edited_description = None
        self.last_edited_status = None

        self.flag_config_manager_pop_opened = False

        self.create_scanner_inputs_tab()

    def create_scanner_inputs_tab(self):
        self.create_instrument_table()
        self.create_configuration_inputs_and_table()

        HouseKeepingGUI.dump_all_instruments_in_instrument_tab(self)
        HouseKeepingGUI.dump_all_config_in_system(self)

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
        self.instrument_table["columns"] = [_[0] for _ in instruments_table_columns_width]

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
        instrument_id = self.instrument_table.selection()[0]  # get the item ID of the selected row
        instrument_id = int(instrument_id)

        # Start Remove Instrument Thread
        remove_instrument_thread = threading.Thread(
            target=self.remove_instruments,
            args=([int(instrument_id)],),
        )
        remove_instrument_thread.start()

        # TODO - REMOVE ARYAN
        # self.remove_instruments([int(instrument_id)])

    def remove_instruments(self, list_of_instrument_ids: list):
        # Start flow for instrument get deleted
        self.delete_instrument_flow(list_of_instrument_ids)

        for instrument_id in list_of_instrument_ids:
            where_clause = f"WHERE instrument_id = {instrument_id}"
            # Database Remove
            is_deleted = SqlQueries.delete_from_db_table(table_name="instrument_table", where_clause=where_clause)

            if not is_deleted:
                Utils.display_message_popup(
                    "Error",
                    f"Unable to delete the Instrument, Instrument ID: {instrument_id}",
                )
                continue

            # Remove GUI
            self.remove_row_from_instrument_table([instrument_id])

            # Remove from system
            instrument_obj = strategy_variables.map_instrument_id_to_instrument_object[int(instrument_id)]
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
        res, instrument_id = SqlQueries.insert_into_db_table(table_name="instrument_table", values_dict=values_dict)

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
        ttk.Label(input_frame, text="SecType", width=12, anchor="center").grid(column=0, row=0, padx=5, pady=5)

        ttk.Label(input_frame, text="Symbol", width=12, anchor="center").grid(column=1, row=0, padx=5, pady=5)

        ttk.Label(input_frame, text="Multiplier", width=12, anchor="center").grid(column=2, row=0, padx=5, pady=5)

        ttk.Label(input_frame, text="Exchange", width=12, anchor="center").grid(column=3, row=0, padx=5, pady=5)

        ttk.Label(input_frame, text="Trading Class", width=12, anchor="center").grid(column=4, row=0, padx=5, pady=5)

        ttk.Label(input_frame, text="Currency", width=12, anchor="center").grid(column=5, row=0, padx=5, pady=5)

        ttk.Label(input_frame, text="ConId", width=12, anchor="center").grid(column=6, row=0, padx=5, pady=5)

        ttk.Label(input_frame, text="Primary Exch.", width=12, anchor="center").grid(column=7, row=0, padx=5, pady=5)

        # Create a list of options
        sec_type_options = ["", "OPT", "FOP", "IND"]

        drop_down_items_dict = {}

        def update_textbox(event, currency_entry, exchange_entry, lot_size_entry, combo_new):
            selected_value = combo_new.get()

            if selected_value in ["OPT", "FOP", "IND"]:
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

        def select_opt(event, currency_entry, exchange_entry, lot_size_entry, combo_new):
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

        def select_fop(event, currency_entry, exchange_entry, lot_size_entry, combo_new):
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
            drop_down_items_dict[row_loc][sec_type_combo_box].grid(column=0, row=row_loc, padx=5, pady=5)

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
                    for row_indx, trading_classes in enumerate(list_of_trading_classes, start=1):

                        list_of_trading_classes = sorted(list_of_trading_classes)

                        print(f"Trading class: {list_of_trading_classes}")
                        # Check if result
                        if trading_classes != []:
                            # Get the grid slave of the input frame for FOP trading class textbox
                            slave = input_frame.grid_slaves(row=row_indx, column=4)[0]

                            # Index for trading class dropdown
                            trading_class_combo_box = f"trading_class_combo_box_{row_indx}"

                            # Initialize drop down in FOP row for trading class field
                            drop_down_items_dict[row_indx][trading_class_combo_box] = ttk.Combobox(
                                input_frame,
                                width=10,
                                values=trading_classes,
                                state="readonly",
                                style="Custom.TCombobox",
                            )
                            # Select first element in list off options by default
                            drop_down_items_dict[row_indx][trading_class_combo_box].current(0)

                            # Put drop down in place of textbox
                            drop_down_items_dict[row_indx][trading_class_combo_box].grid(row=row_indx, column=4)

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

                    sec_type = drop_down_items_dict[row_loc][sec_type_combo_box].get().strip()

                    symbol = input_frame.grid_slaves(row=row_loc, column=1)[0].get()

                    lot_size = input_frame.grid_slaves(row=row_loc, column=2)[0].get()
                    exchange = input_frame.grid_slaves(row=row_loc, column=3)[0].get().strip()
                    trading_class = input_frame.grid_slaves(row=row_loc, column=4)[0].get()
                    currency = input_frame.grid_slaves(row=row_loc, column=5)[0].get().strip()
                    conid = input_frame.grid_slaves(row=row_loc, column=6)[0].get()
                    primary_exchange = input_frame.grid_slaves(row=row_loc, column=7)[0].get()

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
            list_of_trading_classes = asyncio.run(identify_the_trading_class_for_all_the_fop_leg_in_combination_async(leg_row_values_list))

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
            add_instrument_thread = threading.Thread(target=add_instrument, args=(popup, add_instrument_button))
            add_instrument_thread.start()

        def add_instrument(
            popup,
            add_instrument_button,
        ):
            combo_values = []
            for i in range(num_rows):
                row_loc = i + 1

                sec_type_combo_box = f"sec_type_combo_box_{row_loc}"

                sec_type = drop_down_items_dict[row_loc][sec_type_combo_box].get().strip()
                symbol = input_frame.grid_slaves(row=row_loc, column=1)[0].get()
                lot_size = input_frame.grid_slaves(row=row_loc, column=2)[0].get()
                exchange = input_frame.grid_slaves(row=row_loc, column=3)[0].get().strip()
                trading_class = input_frame.grid_slaves(row=row_loc, column=4)[0].get()

                currency = input_frame.grid_slaves(row=row_loc, column=5)[0].get().strip()
                conid = input_frame.grid_slaves(row=row_loc, column=6)[0].get()
                primary_exchange = input_frame.grid_slaves(row=row_loc, column=7)[0].get()
                
                # Added Validation for FOP and IND that trading class must be given
                if sec_type in ["FOP", "IND"] and not trading_class:
                    Utils.display_message_popup(
                        "Error",
                        f"Trading Class should be present for FOP or IND",
                    )
                    add_instrument_button.config(state="normal")
                    return
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
        button_frame.place(relx=0.5, anchor=tk.CENTER)  # x=530, y=custom_height-50,width=100, height=30,  )
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
            command=lambda: on_search_trading_classes_for_fop_button_click(search_trading_classes_for_fop_button),
        )
        search_trading_classes_for_fop_button.grid(row=0, column=1, padx=10)

    def update_leg_config_button_clicked(self, popup):
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
            self.insert_row_in_config_table_gui((int(num_leg) - config_table_len), config_table_len)
        elif int(num_leg) < config_table_len:
            self.delete_row_in_config_table_gui((config_table_len - int(num_leg)))
        else:
            pass

        popup.destroy()

    def insert_row_in_config_table_gui(self, num_legs, current_row_number):

        for i in range(num_legs):

            # Entry and Combo box Inputs
            desc = current_row_number + i + 1
            instrument_id = ""
            action_value = "BUY"
            right_value = "CALL"
            quantity = "1"
            delta_min_value = "0.4"
            delta_max_value = "0.6"
            dte_min_value = "1"
            dte_max_value = "7"
            right_value = "CALL"

            row_values = (
                desc,
                instrument_id,
                action_value,
                right_value,
                quantity,
                delta_min_value,
                delta_max_value,
                dte_min_value,
                dte_max_value,
            )

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
            self.leg_config_table.delete(config_leg_id)

    def create_configuration_inputs_and_table(
        self,
    ):
        """
        Config Manager Button, Create New Config Button
        Leg Config Table
        Save Config, Save Config as Buttons
        """

        # Create a frame for input fields
        input_fields_frame = ttk.Frame(self.scanner_inputs_tab, padding=20)
        input_fields_frame.pack()

        # Place the input fields frame just below the instrument table
        input_fields_frame.place(relx=0.5, anchor=tk.CENTER, rely=0.2, y=250)

        # Create New Config Button
        create_new_config_button = ttk.Button(
            input_fields_frame,
            text="Create New Config",
            command=self.create_new_config_button_click,
        )
        create_new_config_button.grid(column=1, row=2, padx=5, pady=5)

        # Config Manager Button
        config_manager_button = ttk.Button(
            input_fields_frame,
            text="Config Manager",
            command=self.create_config_manager_popup,
        )
        config_manager_button.grid(column=0, row=2, padx=5, pady=5)

        # Save Config Button
        save_config_button = ttk.Button(
            self.scanner_inputs_tab,
            text="Save Config",
            # TODO - ARYAN Use THread
            command=lambda: threading.Thread(target=self.save_config_click).start(),
        )
        save_config_button.place(x=700, y=728, width=115, height=35)

        # Save Config As Button
        save_config_as_button = ttk.Button(
            self.scanner_inputs_tab, text="Save Config As", command=lambda: threading.Thread(target=self.save_config_as_popup).start()
        )
        save_config_as_button.place(x=840, y=728, width=115, height=35)

        # Create the Config Leg Table
        self.create_leg_config_editable_table()

    def create_new_config_button_click(self):
        # Create a popup for creating a new configuration
        popup = tk.Toplevel()
        popup.title("Create New Configuration")
        # popup.geometry("200 X 220")
        config_input_frame = ttk.Frame(popup, padding=20)
        config_input_frame.pack(fill="both", expand=True)

        # Add the Template Label
        dropdown_label = ttk.Label(config_input_frame, text="Template", anchor="center", width=12)
        dropdown_label.grid(column=0, row=0, padx=5, pady=(0, 5), sticky="n")

        # Templare dropdown
        dropdown = ttk.Combobox(config_input_frame, state="readonly")
        # getting the values for templates from map
        dropdown["values"] = tuple(self.dropdown_file_mapping.keys())
        dropdown.current(0)
        dropdown.grid(column=0, row=1, padx=5, pady=5)

        # Bind the template which is selected
        template_button = ttk.Button(
            config_input_frame, text="Import Template", command=lambda: self.upload_template_from_mapped_path(dropdown.get(), popup)
        )
        template_button.grid(column=0, row=2, padx=5, pady=5)

        # Create a separator between the dropdown/button and the "#Legs" label
        separator = ttk.Separator(config_input_frame, orient="vertical")
        separator.grid(column=1, row=0, rowspan=2, padx=5, pady=(0, 5), sticky="ns")

        # No of legs label and entry
        leg_label = ttk.Label(config_input_frame, text="#Legs", anchor="center", width=12)
        leg_label.grid(column=2, row=0, padx=5, pady=(0, 5), sticky="n")
        self.no_of_legs_entry = ttk.Entry(config_input_frame)
        self.no_of_legs_entry.grid(column=2, row=1, padx=5, pady=5)

        # Add Update Leg Config Button
        update_leg_config_button = ttk.Button(
            config_input_frame,
            text="Update Legs",
            command=lambda: self.update_leg_config_button_clicked(popup),
        )
        update_leg_config_button.grid(column=2, row=2, padx=5, pady=5)

    # Funtion for Upload Template for mapped path
    def upload_template_from_mapped_path(self, selected_option, popup):
        # extract the file path from mapp
        file_path = self.dropdown_file_mapping.get(selected_option)
        if file_path:
            # function to upload the csv in app
            self.upload_template_from_csv_to_app(file_path)
        popup.destroy()

    # Function for Template upload to app
    def upload_template_from_csv_to_app(self, template_dataframe_path):

        try:
            # get csv file from file path
            template_dataframe = pd.read_csv(template_dataframe_path)

            # Replace null values by None string
            template_dataframe = template_dataframe.fillna("")

        except Exception as e:
            # Error Message pop-up
            Utils.display_message_popup(
                "Error",
                f"Unable to read the CSV file",
            )
            return

        if template_dataframe.empty:
            # Error Message pop-up
            Utils.display_message_popup(
                "Error",
                f"CSV file was empty",
            )
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
        for allowed_columns_name, user_input_col_name in zip(columns_for_template_csv, template_dataframe_columns):
            if allowed_columns_name != user_input_col_name:
                Utils.display_message_popup(
                    "Error",
                    f"Columns are not matching in file, Invalid column: '{user_input_col_name}",
                )
                return False
        return True

    # Function for Save Config Button Click
    def save_config_button_click(
        self,
        popup=None,
        values_dict=None,
    ):
        # Get the no of legs from the table
        no_of_leg = int(len(self.leg_config_table.get_children()))

        # Validate if No of Legs is Zero
        if no_of_leg == 0:
            Utils.display_message_popup(
                "Error",
                f"No of legs is zero",
            )
            return
        
        # Name should be complusory to proceed
        if popup:
            name_value = self.name_entry.get().strip()
            if not name_value:
                Utils.display_message_popup(
                    "Error",
                    "Name field cannot be empty",
                )
                return

        # Create value dict from the GUI table to insert in the db
        if values_dict is None:
            values_dict = {
                "description": self.description_entry.get("1.0", tk.END).strip(),
                "status": self.status_combobox.get(),
                "config_name": self.name_entry.get(),
            }

        # Add No of legs to dict for insertion in db
        values_dict["no_of_leg"] = no_of_leg

        leg_data_list = []

        # Iteration over config leg object
        for i in range(int(len(self.leg_config_table.get_children()))):

            # Prepare leg-wise data
            item_values = self.leg_config_table.item(i + 1, "values")

            leg_data = {
                "leg_number": i + 1,
                "instrument_id": (item_values[1]),
                "action": item_values[2].upper(),
                "right": item_values[3].upper(),
                "quantity": item_values[4],
                "delta_range_min": item_values[5],
                "delta_range_max": item_values[6],
                "dte_range_min": item_values[7],
                "dte_range_max": item_values[8],
                # Add other leg-wise data as needed
            }

            # Validate Config Leg
            if self.config_legs_validation(i, leg_data=leg_data) == False:
                return

            leg_data_list.append(leg_data)

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

        # Destory Popup
        if popup:
            popup.destroy()

        # Change the legs config table state flag
        # self.flag_legs_config_table_in_readonly_state = True

        list_of_config_leg_object = [ConfigLeg(config_leg_dict) for config_leg_dict in leg_data_list]
        values_dict["config_id"] = config_id
        values_dict["list_of_config_leg_object"] = list_of_config_leg_object

        # Creation of Config Object  (Leg)
        config_obj = Config(values_dict)

        # Insert leg-wise data into the config_leg_table
        self.insert_into_config_leg_table(config_obj)

        # Clear all the rows from the scanner combination table
        # Utils.clear_scanner_combination_table()

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

        # Remove prexisting rows
        self.leg_config_table.delete(*self.leg_config_table.get_children())

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
        leg_config_table_frame.place(y=570)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(leg_config_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.leg_config_table = ttk.Treeview(
            leg_config_table_frame,
            yscrollcommand=tree_scroll.set,
            height=9,
            selectmode="extended",
        )
        # Pack to the screen
        self.leg_config_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.leg_config_table.yview)

        # Column in order book table
        self.leg_config_table["columns"] = [_[0] for _ in leg_config_table_columns_width]

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

    # Function to Create Config Manager Popup
    def create_config_manager_popup(self):

        if self.flag_config_manager_pop_opened:

            # Show error pop up
            error_title = f"Config Manager Popup"
            error_string = f"Config Manager Window Already Opened."
            Utils.display_message_popup(error_title, error_string)
            return

        self.flag_config_manager_pop_opened = True

        try:
            # Popup and Title
            popup = tk.Toplevel()
            popup.title("Config Manager")

            # Config Manager Frame
            config_manager_input_frame = ttk.Frame(popup, padding=20)
            config_manager_input_frame.pack(fill=tk.BOTH, expand=True)  # Fill and expand to fit the popup

            # Treeview Scrollbar
            tree_scroll = Scrollbar(config_manager_input_frame)
            tree_scroll.pack(side="right", fill="y")

            # Create Treeview
            self.leg_config_manager_table = ttk.Treeview(
                config_manager_input_frame,
                yscrollcommand=tree_scroll.set,
                height=8,
                selectmode="extended",
            )
            self.leg_config_manager_table.pack(fill=tk.BOTH, expand=True)  # Fill and expand to fit the frame

            # Configure the scrollbar
            tree_scroll.config(command=self.leg_config_manager_table.yview)

            # Columns
            self.leg_config_manager_table["columns"] = [col[0] for col in leg_config_manager_table_columns_width]

            # Creating Columns
            self.leg_config_manager_table.column("#0", width=0, stretch="no")
            for col_name, col_width, col_heading in leg_config_manager_table_columns_width:
                self.leg_config_manager_table.column(col_name, anchor="center", width=col_width)
                self.leg_config_manager_table.heading(col_name, text=col_heading, anchor="center")

            # Background
            self.leg_config_manager_table.tag_configure("oddrow", background="white")
            self.leg_config_manager_table.tag_configure("evenrow", background="lightblue")

            # Get All Config from the db to populate the Table
            configs = self.retrieve_configs_from_database()

            # Populate the Config Manager Table
            for index, config in enumerate(configs):
                tag = "oddrow" if index % 2 == 1 else "evenrow"
                config_id = config.get("config_id", "")
                config_values = [
                    config_id,
                    config.get("config_name", ""),
                    config.get("description", ""),
                    config.get("status", ""),
                ]

                self.leg_config_manager_table.insert(
                    "",
                    "end",
                    iid=config_id,
                    text=index + 1,
                    values=config_values,
                    tags=(tag,),
                )

            try:
                # Right Click menu for config manager table
                self.leg_config_manager_table.bind("<Button-3>", self.leg_config_manager_table_right_click_menu)
            except Exception as e:
                pass

            popup.protocol("WM_DELETE_WINDOW", lambda: self.config_manager_on_close(popup))

        except Exception as e:
            self.flag_config_manager_pop_opened = False
            print("error in config manager popup")

    def config_manager_on_close(self, popup):
        popup.destroy()
        self.flag_config_manager_pop_opened = False

    # Function for Right CLick in Config Manager
    def leg_config_manager_table_right_click_menu(self, event):
        # Get the Treeview row that was clicked
        row = self.leg_config_manager_table.identify_row(event.y)

        if row:
            # Select the row
            self.leg_config_manager_table.selection_set(row)

            # Get the status of the selected row
            config_id = self.leg_config_manager_table.item(row, "values")[0]
            status = self.leg_config_manager_table.item(row, "values")[3]  # Assuming the status is at index 2

            # Create a context menu based on the status
            menu = tk.Menu(self.leg_config_manager_table, tearoff=0)

            if status == "Inactive":
                new_status = "Active"
            else:
                new_status = "Inactive"

            menu.add_command(
                label=new_status, command=lambda: threading.Thread(target=self.update_config_status(config_id, status)).start()
            )
            menu.add_command(label="Edit Config", command=lambda: threading.Thread(target=self.edit_config).start())
            menu.add_command(label="Delete", command=lambda: threading.Thread(target=self.delete_config_details_from_manager).start())

            # Display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    # Retrieve all the configs to insert into the config manager GUI table
    def retrieve_configs_from_database(self):
        all_config = SqlQueries.select_from_db_table(table_name="config_table", columns="*")
        return all_config

    # Function to make status inactive from active vice versa
    def update_config_status(self, config_id, current_status):

        # if True:
        try:
            # Validation to check that config exits, put in try except block as well.
            if int(config_id) not in strategy_variables.map_config_id_to_config_object:
                print(f"Config id {config_id} doesn't exist")
                return

            # Retrieve the config_id from the selected item
            config_id = int(config_id)
            if current_status == "Active":
                new_status = "Inactive"
            elif current_status == "Inactive":
                new_status = "Active"

                config_obj = copy.deepcopy(strategy_variables.map_config_id_to_config_object[config_id])
                values_dict = {
                    "description": config_obj.description,
                    "status": config_obj.status,
                    "config_name": config_obj.config_name,
                    "no_of_leg": config_obj.no_of_leg,
                }

                for config_leg_object in config_obj.list_of_config_leg_object:
                    leg_number = config_leg_object.leg_number
                    leg_data = {
                        "leg_number": leg_number,
                        "instrument_id": config_leg_object.instrument_id,
                        "action": config_leg_object.action,
                        "right": config_leg_object.right,
                        "quantity": config_leg_object.quantity,
                        "delta_range_min": config_leg_object.delta_range_min,
                        "delta_range_max": config_leg_object.delta_range_max,
                        "dte_range_min": config_leg_object.dte_range_min,
                        "dte_range_max": config_leg_object.dte_range_max,
                        # Add other leg-wise data as needed
                    }

                    if self.config_legs_validation(leg_number, leg_data) == False:
                        return
            else:
                return  # Do nothing if status is neither "Active" nor "Inactive"

            # Update the db for that config id with the new status
            res = self.update_config_status_in_db(config_id, new_status)

            # Update if update in db was successful
            if res:

                # Change in the GUI to the new status
                updated_values = list(self.leg_config_manager_table.item(str(config_id), "values"))
                updated_values[3] = new_status  # Update status to the new status
                self.leg_config_manager_table.item(str(config_id), values=updated_values)

                # Update in Config Object
                strategy_variables.map_config_id_to_config_object[config_id].status = new_status

            # If config status is inactive remove indicator row, combination row
            if new_status == "Inactive":
                flag_only_status_update = True
                self.delete_config_details_from_manager(config_id=config_id, flag_only_status_update=flag_only_status_update)

        except Exception as e:
            print(f"An error occurred: {e}")

    # Function to update the config status in db
    def update_config_status_in_db(self, config_id, new_status):

        # Update the status for the specified config_id
        where_condition = f"WHERE `config_id` = {config_id};"
        values_dict_for_db = {"status": new_status}  # New values for update
        update_query = SqlQueries.create_update_query(
            table_name="config_table",
            values_dict=values_dict_for_db,
            where_clause=where_condition,
        )

        # Update values in rows
        res = SqlQueries.execute_update_query(update_query)
        if not res:
            print(f"Could not update the config status, config_id: {config_id}")

        return res

        # Function for Edit Config

    def edit_config(self):

        try:
            # Select the current selected item
            selected_item = self.leg_config_manager_table.selection()

            # Retrieve the config_id from the selected item
            if selected_item:
                config_id = self.leg_config_manager_table.item(selected_item, "values")[0]
                config_id = int(config_id)

                # Config Details
                self.last_edited_config_id = config_id
                self.last_edited_name = self.leg_config_manager_table.item(selected_item, "values")[1]
                self.last_edited_description = self.leg_config_manager_table.item(selected_item, "values")[2]
                self.last_edited_status = self.leg_config_manager_table.item(selected_item, "values")[3]

            else:
                # return if nothing is selected
                return
        except Exception as e:
            print(f"Could not get the config_id value: {e} ")
            return

        # Getting the config
        row_data_list = self.get_config_details_column_and_data_from_config_object(config_id)

        if row_data_list is None:
            return

        # print(row_data_list)
        config_df = pd.DataFrame(row_data_list)

        # Insert row data list into the leg config table
        self.insert_into_config_leg_table_through_template(config_df)

    def get_config_details_column_and_data_from_config_object(self, config_id):

        # Getting the config object
        try:
            config_obj = copy.deepcopy(strategy_variables.map_config_id_to_config_object[config_id])
        except Exception as e:
            # Show error pop up
            error_title = f"Error Config ID: {config_id}"
            error_string = f"Unable to find the Config ID."
            Utils.display_message_popup(error_title, error_string)
            return None

        list_of_config_leg_objects = config_obj.list_of_config_leg_object
        config_details_list = []

        # Getting the config leg object details
        for config_leg_obj in list_of_config_leg_objects:
            config_details = {
                "leg_number": config_leg_obj.leg_number,
                "instrument_id": config_leg_obj.instrument_id,
                "action": config_leg_obj.action,
                "right": config_leg_obj.right,
                "quantity": config_leg_obj.quantity,
                "delta_range_min": config_leg_obj.delta_range_min,
                "delta_range_max": config_leg_obj.delta_range_max,
                "dte_range_min": config_leg_obj.dte_range_min,
                "dte_range_max": config_leg_obj.dte_range_max,
            }

            # Append the details to the list
            config_details_list.append(config_details)

        return config_details_list

    # Delete the config details from the manager table and db
    def delete_config_details_from_manager(self, config_id=None, flag_only_status_update=False):

        # If Config is nto given, get from the config manager table
        if config_id is None:
            selected_item = self.leg_config_manager_table.selection()
            if selected_item:
                # Retrieve the config_id from the selected item
                config_id = self.leg_config_manager_table.item(selected_item, "values")[0]
                self.leg_config_manager_table.delete(selected_item)
        else:
            config_id = int(float(config_id))

        # Get list of combo id based on config id, from DB
        list_of_combo_ids = Utils.get_list_of_combo_ids_for_based_on_config_id(config_id)

        # Get all the rows from config_indicator_rela table, such that config_id is N.
        where_condition = f" WHERE `config_id` = {config_id};"
        select_query = SqlQueries.create_select_query(
            table_name="config_indicator_relation",
            columns="*",
            where_clause=where_condition,
        )

        # Getting the Count of rows
        all_config_existing_row = SqlQueries.execute_select_query(select_query)
        list_of_config_ids_relation = [(row["config_id"], row["instrument_id"], row["expiry"]) for row in all_config_existing_row]

        # Delete the config details from the database
        if flag_only_status_update == False:
            res = self.delete_config_from_database(config_id)

            if res:
                config_id = int(float(config_id))
                print(f"Delete Config: {config_id}")

                # Remove from the system
                strategy_variables.map_config_id_to_config_object[config_id].remove_from_system()
        else:
            # Get all the rows from config_indicator_rela table, such that config_id is N.
            where_condition = f" WHERE `config_id` = {config_id};"
            delete_query = SqlQueries.create_delete_query(
                table_name="config_indicator_relation",
                where_clause=where_condition,
            )

            # Delete the rows from config indicator relation
            delete_query = SqlQueries.execute_delete_query(query=delete_query)

            # Delete the rows from combination table db
            delete_query = SqlQueries.create_delete_query(
                table_name="combination_table",
                where_clause=where_condition,
            )

            delete_query = SqlQueries.execute_delete_query(query=delete_query)

        # Remove from combination and deletion from indicator relation
        Utils.remove_row_from_scanner_combination_table(list_of_combo_ids)
        Utils.deletion_indicator_rows_based_on_config_tuple_relation(list_of_config_ids_relation)

    # Function to delete config from the database
    def delete_config_from_database(self, config_id):
        where_condition = f" WHERE `config_id` = {config_id};"

        # Delete Query
        delete_query = SqlQueries.create_delete_query(table_name="config_table", where_clause=where_condition)
        res = SqlQueries.execute_delete_query(delete_query)
        if not res:
            print(f"Error: Deletion not succesful for config id: {config_id}")

        return res

    # Functionality for Save Config Button Click
    def save_config_click(self):
        # if last edited config is None just call save config as button function
        if not self.last_edited_config_id:
            self.save_config_as_popup()
            return
        else:
            # Remove the Config from the system and db
            self.delete_config_details_from_manager(self.last_edited_config_id)

            # self.save_config_as_popup()
            self.last_edited_config_id = None

            values_dict = {
                "description": self.last_edited_description,
                "status": self.last_edited_status,
                "config_name": self.last_edited_name,
            }
            # Call the Save config function with the updated config details on the last edited config name, desc, status
            self.save_config_button_click(
                values_dict=values_dict,
            )

    # Function for Save Config As Popup
    def save_config_as_popup(self):
        # Popup Window
        popup = tk.Toplevel()
        popup.geometry("400x300")
        popup.title("Save Config As")

        # Create a frame for the input fields
        input_frame = ttk.Frame(popup, padding=20)
        input_frame.pack(fill="both", expand=True)

        # Add labels and entry widgets row-wise with proper alignment and width
        ttk.Label(input_frame, text="Name:", width=15, anchor="e").grid(column=0, row=0, padx=5, pady=5)
        ttk.Label(input_frame, text="Status:", width=15, anchor="e").grid(column=0, row=1, padx=5, pady=5)
        ttk.Label(input_frame, text="Description:", width=15, anchor="e").grid(column=0, row=2, padx=5, pady=5)

        self.name_entry = ttk.Entry(input_frame, width=30)
        self.name_entry.grid(column=1, row=0, padx=5, pady=5)

        self.status_combobox = ttk.Combobox(input_frame, width=28, state="readonly")
        self.status_combobox["values"] = ["Active", "Inactive"]
        self.status_combobox.current(0)
        self.status_combobox.grid(column=1, row=1, padx=5, pady=5)

        # Binding the Status DropDown with a,A,i,I
        self.status_combobox.bind(
            "a",
            lambda event: self.select_active_inactive(event, True, self.status_combobox),
        )
        self.status_combobox.bind(
            "A",
            lambda event: self.select_active_inactive(event, True, self.status_combobox),
        )
        self.status_combobox.bind(
            "i",
            lambda event: self.select_active_inactive(event, False, self.status_combobox),
        )
        self.status_combobox.bind(
            "I",
            lambda event: self.select_active_inactive(event, False, self.status_combobox),
        )

        self.description_entry = tk.Text(input_frame, width=23, height=8)
        self.description_entry.grid(column=1, row=2, padx=5, pady=5)

        proceed_button = ttk.Button(
            input_frame,
            text="Proceed",
            command=lambda: self.save_config_button_click(popup),
        )
        proceed_button.grid(column=1, row=3, padx=5, pady=10)

    ###########################
    ###########################
    ###########################
    ###########################


    def delete_instrument_flow(self, list_of_instrument_ids):
        """
        # for config_id in Set: <5 Config IDs>
        #     Create a deepcopy of Config Obj:
        #     (save_config_click)Save Config Funtionality to be reused. <delete_config_details_from_manager(config_id)>

        #     Create a deepcopy of Config Obj:
        #         list_of_config_leg_object
        #     New but use almost same code: save_config_button_click w/ no validations
            
        """
        # Get all the configs that matches instrument_id
        for instrument_id in list_of_instrument_ids:
            # Query to get the config ids
            where_condition = f" WHERE `instrument_id` = {instrument_id};"
            select_query = SqlQueries.create_select_query(
                table_name="config_legs_table",
                columns="`config_id`",
                where_clause=where_condition,
            )

            # Get all the rows from config_legs_table
            all_the_existing_rows_form_db_table = SqlQueries.execute_select_query(select_query)
            # Get list of config ids

            list_of_config_ids = [row["config_id"] for row in all_the_existing_rows_form_db_table]
            for config_id in list_of_config_ids:
                if config_id not in strategy_variables.map_config_id_to_config_object:
                    continue
                config_obj = copy.deepcopy(strategy_variables.map_config_id_to_config_object[config_id])

                # Call the save click button functionality to first delete instrument id and then create new and save
                self.save_config_click_for_instrument_delete(instrument_id, config_id, config_obj)

    # Functionality for Save Config Button Click when Instrument get deleted
    def save_config_click_for_instrument_delete(self, instrument_id, config_id, config_obj):
        # Delete the config id from config
        self.delete_config_details_from_manager(config_id)

        # Addition of new config new inactive status
        values_dict = {
            "description": config_obj.description,
            "status": "Inactive",
            "config_name": config_obj.config_name,
        }
        # Call the Save config function with the updated config details when instrument deleted
        self.save_config_button_click_for_instrument_delete(instrument_id, values_dict=values_dict, config_obj=config_obj)

    # TODO - check karan arayan
    # Function for Save Config Button Click when instrument deleted
    def save_config_button_click_for_instrument_delete(
        self,
        instrument_id,
        config_obj,
        values_dict,
    ):
        # Get the no of legs from config object
        no_of_leg = int(config_obj.no_of_leg)

        # Validate if No of Legs is Zero
        if no_of_leg == 0:
            Utils.display_message_popup(
                "Error",
                f"No of legs is zero",
            )
            return

        # Add No of legs to dict for insertion in db
        values_dict["no_of_leg"] = no_of_leg

        leg_data_list = []

        # Get the list of config leg objects
        list_of_config_leg_objects = config_obj.list_of_config_leg_object

        # Iteration over config leg object
        for i, config_leg_object in enumerate(list_of_config_leg_objects):

            # Set instrument id as -1 if it is deleted
            instrument_id = -1 if config_leg_object.instrument_id == instrument_id else config_leg_object.instrument_id

            # print(item_values)
            leg_data = {
                "leg_number": i + 1,
                "instrument_id": instrument_id,
                "action": config_leg_object.action.upper(),
                "right": config_leg_object.right.upper(),
                "quantity": config_leg_object.quantity,
                "delta_range_min": config_leg_object.delta_range_min,
                "delta_range_max": config_leg_object.delta_range_max,
                "dte_range_min": config_leg_object.dte_range_min,
                "dte_range_max": config_leg_object.dte_range_max,
                # Add other leg-wise data as needed
            }
            leg_data_list.append(leg_data)

        # Run the transaction for the leg data
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

        list_of_config_leg_object = [ConfigLeg(config_leg_dict) for config_leg_dict in leg_data_list]
        values_dict["config_id"] = config_id
        values_dict["list_of_config_leg_object"] = list_of_config_leg_object

        # Creation of Config Object  (Leg)
        config_obj = Config(values_dict)

        # Insert leg-wise data into the config_leg_table
        self.insert_into_config_leg_table(config_obj)

    def select_active_inactive(self, event, flag_active, status_combo_box):
        # Update the value in dropdown
        status_combo_box.config(state="normal")
        status_combo_box.delete(0, tk.END)  # Clear any existing text
        if flag_active:
            status_combo_box.insert(0, "Active")
        else:
            status_combo_box.insert(0, "Inactive")
        status_combo_box.config(state="readonly")

    # Validate Config Legs
    def config_legs_validation(self, i, leg_data):

        # For First leg only range between 0 to 1
        local_map_instrument_id_instrument_obj = copy.deepcopy(strategy_variables.map_instrument_id_to_instrument_object)
        list_of_instrument_ids = local_map_instrument_id_instrument_obj.keys()
        if not str(leg_data["instrument_id"]).isdigit():
            Utils.display_message_popup(
                "Error",
                f"Instrument ID '{leg_data['instrument_id']}' is not a valid integer",
            )
            return False

        # Quantity should be INT
        if not str(leg_data["quantity"]).isdigit():
            Utils.display_message_popup(
                "Error",
                f"Quantity '{leg_data['quantity']}' is not a valid integer",
            )
            return False

        # DTE Should be INT or float
        try:
            dte_range_min = int(float(leg_data["dte_range_min"]))
            dte_range_max = int(float(leg_data["dte_range_max"]))
        except ValueError:
            Utils.display_message_popup(
                "Error",
                f"MinDTE or MaxDTE is not a valid integer",
            )
            return False

        # MinDTE can be greater than MaxDTE
        if dte_range_min > dte_range_max:
            Utils.display_message_popup(
                "Error",
                f"MinDTE value cannot be greater than MaxDTE value",
            )
            return False

        if int(leg_data["instrument_id"]) not in list_of_instrument_ids:
            Utils.display_message_popup(
                "Error",
                f"Instrument ID doesn't exist in Instrument Table",
            )
            return False

        if i == 0:
            if not Utils.is_between_zero_to_one((leg_data["delta_range_max"])):
                Utils.display_message_popup(
                    "Error",
                    f"Delta values for the first leg should be between 0 and 1",
                )
                return False

            if dte_range_min < 0:
                Utils.display_message_popup(
                    "Error",
                    f"MinDTE values for the first leg should be greater than or equal to 0",
                )
                return False

            if not Utils.is_between_zero_to_one((leg_data["delta_range_min"])):
                Utils.display_message_popup(
                    "Error",
                    f"Delta values for the first leg should be between 0 and 1",
                )
                return False

            if float(leg_data["delta_range_min"]) > float(leg_data["delta_range_max"]):
                Utils.display_message_popup(
                    "Error",
                    f"MinDelta value cannot be greater than MaxDelta value",
                )
                return False

        else:
            # For legs 1 onwards validation for -1 to 1 value
            # Validation

            if not Utils.is_between_minus_one_to_one((leg_data["delta_range_max"])):
                Utils.display_message_popup(
                    "Error",
                    f"Delta values should be in between -1 to 1",
                )
                return False

            if not Utils.is_between_minus_one_to_one((leg_data["delta_range_min"])):
                Utils.display_message_popup(
                    "Error",
                    f"Delta values should be in between -1 to 1",
                )
                return False

            if float(leg_data["delta_range_min"]) > float(leg_data["delta_range_max"]):
                Utils.display_message_popup(
                    "Error",
                    f"MinDelta value cannot be greater than MaxDelta value",
                )
                return False

        return True
