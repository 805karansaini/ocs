import asyncio
import configparser
import threading
import time
import tkinter as tk
from tkinter import Scrollbar, messagebox, ttk
from com.identify_trading_class_for_fop import identify_the_trading_class_for_all_the_fop_leg_in_combination_async
from option_combo_scanner.gui.house_keeping import HouseKeepingGUI

from option_combo_scanner.gui.utils import Utils
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
    ("LegNo", 382, "Leg No"),
    ("Action", 382, "Action"),
    ("MinDelta", 382, "MinDelta"),
    ("MaxDelta", 382, "MaxDelta"),
    ]

class ScannerInputsTab:
    def __init__(self, scanner_inputs_tab):
        self.last_update_settings_mssg_time = None
        self.scanner_inputs_tab = scanner_inputs_tab
        self.create_scanner_inputs_tab()

    def create_scanner_inputs_tab(self):
        self.create_instrument_table()
        self.create_configuration_inputs_and_table()

        HouseKeepingGUI.dump_all_instruments_in_instrument_tab(
            self
        )
    def create_instrument_table(self, ):
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

        
        self.instrument_table.bind(
            "<Button-3>", self.instrument_table_right_click_menu
        )

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

    def delete_selected_instrument(
        self,
    ):
        # Instrument ID
        instrument_id = self.instrument_table.selection()[0]  # get the item ID of the selected row
        instrument_id = int(instrument_id)

        self.remove_instruments([int(instrument_id)])

    def remove_instruments(self, list_of_instrument_ids: list):
        for instrument_id in list_of_instrument_ids:
            where_clause = f"WHERE instrument_id = {instrument_id}"
            # Database Remove
            is_deleted = SqlQueries.delete_from_db_table(table_name="instrument_table", where_clause=where_clause)
            
            if not is_deleted:
                Utils.display_message_popup(
                    "Error",
                    f"Unable to delete the Instrument, Instrument ID: {instrument_id}",
                )
            
            # Remove GUI
            self.remove_row_from_instrument_table([instrument_id])
            
            # Remove from system
            instrument_obj = strategy_variables.map_instrument_id_to_instrument_object[int(instrument_id)]
            instrument_obj.remove_from_system()

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
            'symbol': symbol,
            'sec_type': sec_type,
            'currency': currency,
            'multiplier': multiplier,
            'exchange': exchange,
            'trading_class': trading_class,
            'conid': conid,
            'primary_exchange': primary_exchange,
        }
        
        # TODO Validaitons

        # Insert in the database
        res, instrument_id = SqlQueries.insert_into_db_table(table_name="instrument_table", values_dict=values_dict)

        # if not inserted
        if not res:
            # show error TODO
            return
        
        values_dict['instrument_id']  = instrument_id
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
        sec_type_options = ["", "STK", "FUT", "OPT", "FOP"]

        drop_down_items_dict = {}

        def update_textbox(
            event, currency_entry, exchange_entry, lot_size_entry, combo_new
        ):
            selected_value = combo_new.get()

            if selected_value in ["STK", "OPT", "FOP", "FUT"]:
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

        def select_stk(
            event, currency_entry, exchange_entry, lot_size_entry, combo_new
        ):
            combo_new.current(1)

            selected_value = "STK"
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

        def select_fut(
            event, currency_entry, exchange_entry, lot_size_entry, combo_new
        ):
            combo_new.current(2)

            selected_value = "FUT"
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
                "s",
                lambda event, currency_entry=currency_entry, exchange_entry=exchange_entry, lot_size_entry=lot_size_entry, combo_new=drop_down_items_dict[
                    row_loc
                ][
                    sec_type_combo_box
                ]: select_stk(
                    event, currency_entry, exchange_entry, lot_size_entry, combo_new
                ),
            )
            drop_down_items_dict[row_loc][sec_type_combo_box].bind(
                "f",
                lambda event, currency_entry=currency_entry, exchange_entry=exchange_entry, lot_size_entry=lot_size_entry, combo_new=drop_down_items_dict[
                    row_loc
                ][
                    sec_type_combo_box
                ]: select_fut(
                    event, currency_entry, exchange_entry, lot_size_entry, combo_new
                ),
            )
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
                "S",
                lambda event, currency_entry=currency_entry, exchange_entry=exchange_entry, lot_size_entry=lot_size_entry, combo_new=drop_down_items_dict[
                    row_loc
                ][
                    sec_type_combo_box
                ]: select_stk(
                    event, currency_entry, exchange_entry, lot_size_entry, combo_new
                ),
            )
            drop_down_items_dict[row_loc][sec_type_combo_box].bind(
                "F",
                lambda event, currency_entry=currency_entry, exchange_entry=exchange_entry, lot_size_entry=lot_size_entry, combo_new=drop_down_items_dict[
                    row_loc
                ][
                    sec_type_combo_box
                ]: select_fut(
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

            # Get trading classes and put those trading classes in new dropdown
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
                        print(f"Trading class: {list_of_trading_classes}" )
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
                        "", # action
                        sec_type,
                        symbol,
                        "", # dte
                        "", # delta
                        "", # right
                        "", # qty
                        lot_size,
                        exchange,
                        trading_class,
                        currency,
                        conid,
                        primary_exchange,
                        "", # Strike
                        "", # expiry

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

        def on_add_combo_button_click(
            add_combo_button,
            popup,
        ):
            add_combo_button.config(state="disabled")
            add_combo_thread = threading.Thread(
                target=add_combo, args=(popup, add_combo_button)
            )
            add_combo_thread.start()

        def add_combo(
            popup,
            add_combo_button,
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

            print("Combo Values: ", combo_values)

            # TODO - get result
            res = self.add_instrument(*combo_values[0])

            # if res
            popup.destroy()
            # Enabling the Button again
            add_combo_button.config(state="normal")

        # Create a frame for the "Add Combo" button
        button_frame = ttk.Frame(popup)
        button_frame.place(
            relx=0.5, anchor=tk.CENTER
        )  # x=530, y=custom_height-50,width=100, height=30,  )
        button_frame.place(y=custom_height - 50)

        # Text we want to show for the button
        edit_add_combo_button_text = "Add Instrument"

        # Create the "Add Combo" button
        add_combo_button = ttk.Button(
            button_frame,
            text=edit_add_combo_button_text,
            command=lambda: on_add_combo_button_click(
                add_combo_button,
                popup,
            ),
        )
        add_combo_button.grid(row=0, column=0, padx=10)

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
    
    def create_configuration_inputs_and_table(self,):

        # Create a frame for input fields
        input_fields_frame = ttk.Frame(self.scanner_inputs_tab, padding=20)
        input_fields_frame.pack()

        # Place the input fields frame just below the instrument table
        input_fields_frame.place(relx=0.5, anchor=tk.CENTER, rely=0.2, y=250)

        # Labels
        right_label = ttk.Label(input_fields_frame, text="Right", anchor="center", width=12)
        right_label.grid(column=0, row=0, padx=5, pady=(0, 5), sticky="n")
        
        dte_leg_label = ttk.Label(input_fields_frame, text="List of DTE", anchor="center", width=12)
        dte_leg_label.grid(column=1, row=0, padx=5, pady=(0, 5), sticky="n")
        
        leg_label = ttk.Label(input_fields_frame, text="#Legs", anchor="center", width=12)
        leg_label.grid(column=2, row=0, padx=5, pady=(0, 5), sticky="n")
        
        # Entry and Combo box Inputs 
        right_var = tk.StringVar()
        right_dropdown = ttk.Combobox(input_fields_frame, textvariable=right_var, values=["Call", "Put"], state="readonly")
        right_dropdown.grid(column=0, row=1, padx=5, pady=5)

        # Add Entry for "dte leg" with label above
        dte_leg_entry = ttk.Entry(input_fields_frame)
        dte_leg_entry.grid(column=1, row=1, padx=5, pady=5)
        
        leg_entry = ttk.Entry(input_fields_frame)
        leg_entry.grid(column=2, row=1, padx=5, pady=5)

        update_leg_config_button = ttk.Button(input_fields_frame, text="Update Legs Config")
        update_leg_config_button.grid(column=5, row=1, padx=5, pady=5)

        # Add Save button
        save_config_button = ttk.Button(input_fields_frame, text="Save Config")
        save_config_button.grid(column=6, row=1, padx=5, pady=5)

        self.create_leg_config_editable_table()

    def create_leg_config_editable_table(self):
        # Table, 
        # Editable
        # Header: ["LegNo", "Action", "MinDelta",, "MaxDelta"] 
        
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
            height=10,
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

        # Create an Entry widget
        self.entry = tk.Entry(leg_config_table_frame)
        # Create combo box
        self.combo_box = ttk.Combobox(leg_config_table_frame, state="readonly",
            style="Custom.TCombobox",)
        
        for _ in range(3):
            
            # Entry and Combo box Inputs 
            desc = f"Leg {_+1}"
            action_value = "Buy"
            delta_min_value = 0.4 + (_/10) 
            delta_max_value = 0.5+ (_/10)

            row_values = (desc, action_value, delta_min_value, delta_max_value)
            if _ % 2 == 1:
                self.leg_config_table.insert(
                    "",
                    "end",
                    iid=_,
                    text=_ + 1,
                    values=row_values,
                    tags=("oddrow",),
                )
            else:
                self.leg_config_table.insert(
                    "",
                    "end",
                    iid=_,
                    text=_ + 1,
                    values=row_values,
                    tags=("evenrow",),
                )

        


        #######################
        #######################
        #######################

        # Bind the <Configure> event of the scrollbar to on_scroll function
        self.leg_config_table.bind('<Configure>', self.on_scroll)

        # Bind the mouse wheel event to the Treeview
        self.leg_config_table.bind("<MouseWheel>", self.on_scroll)

        # Bind on click methods
        self.entry.bind('<Return>', lambda e: self.on_entry_validate)
        self.combo_box.bind('<Return>', lambda e: self.on_entry_validate)

        # Bind the double-click event to the Treeview widget
        self.leg_config_table.bind('<Double-1>', self.on_double_click)

        # update filter table
        # self.update_uer_inputs_table()

    def on_scroll(self, event):

        # Your action upon scrolling goes here
        self.entry.place_forget()
        self.combo_box.place_forget()


    def on_double_click(self, event):

        self.entry.place_forget()
        self.combo_box.place_forget()

        # Get the item selected
        item = self.leg_config_table.identify('item', event.x, event.y)

        column = self.leg_config_table.identify_column(event.x)


        print(f"item {item} column: {column}")

        column_index = int(column.replace("#", ""))
        # action, min, max delta
        if column_index not in [2, 3, 4]:
            return

        # Position the entry widget over the cell
        x, y, width, height = self.leg_config_table.bbox(item, column)

        print(column, column_index )
        if column in ["#3", "#4"]:

            self.entry.place(x=x, y=y, width=width, height=height)

            # Set the entry widget's text to the cell's value
            self.entry.delete(0, tk.END)
            value_at_this_cell = self.leg_config_table.item(item, 'values')[column_index - 1]
            self.entry.insert(0, value_at_this_cell)

            # Focus on the entry widget
            self.entry.focus()

        else:

            self.combo_box.place(x=x, y=y, width=width, height=height)

            self.combo_box['values'] = ["Buy", "Sell"] 
            values_list = ["Buy", "Sell"]

            # get the values of the selected row
            all_values = self.leg_config_table.item(item, "values")
            selected_option = all_values[column_index - 1]

            try:

                # set initial option
                self.combo_box.current(values_list.index(selected_option))

            except Exception as e:

                self.combo_box.current(0)
                print(f"Exception inside combo box option setting, Exp: {e}")

            # Focus on the entry widget
            self.combo_box.focus()

    def on_entry_validate(self, ):
        print(f"on_entry_validate")
        # Remove input fields
        self.entry.place_forget()
        self.combo_box.place_forget()
        return
        # Update user input table
        self.update_uer_inputs_table()

        # Remove input fields
        entry.place_forget()
        combo_box.place_forget()


    # Method to define user inputs tab right click options
    def user_inputs_table_right_click(self, event):
        print(f"user_inputs_table_right_click")
        return

