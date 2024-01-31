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

class TradingRulesTab:
    def __init__(self, trading_rules_tab):
        self.last_update_settings_mssg_time = None
        self.trading_rules_tab = trading_rules_tab
        self.create_trading_rules_tab()

    def create_trading_rules_tab(self):
        # Create Treeview Frame for active combo table
        add_instrument_frame = ttk.Frame(self.trading_rules_tab, padding=20)
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


        instrument_table_frame = ttk.Frame(self.trading_rules_tab, padding=20)
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
        self.instrument_table.heading("#0", text="\n", anchor="w")

        for col_name, col_width, col_heading in instruments_table_columns_width:
            self.instrument_table.column(col_name, anchor="center", width=col_width)
            self.instrument_table.heading(col_name, text=col_heading, anchor="center")

        # Back ground
        self.instrument_table.tag_configure("oddrow", background="white")
        self.instrument_table.tag_configure("evenrow", background="lightblue")
        ttk.Label(input_frame, text="SecType", width=12, anchor="center").grid(
            column=0, row=0, padx=5, pady=5
        )

        # # Label for Config box
        # ttk.Label(instrument_table_frame, text="Config").grid(
        #     row=4, column=0, padx=10, pady=5, sticky="w"
        # )

        # # Description box for config
        # self.config_description = ttk.Treeview(
        #     instrument_table_frame,
        #     columns=("ConfigID", "Legs", "DTE"),
        #     show="headings",
        #     height=8,
        # )
        # self.config_description.grid(
        #     row=5, column=0, padx=(10, 50), pady=(5, 20), rowspan=2, sticky="ew"
        # )

        # # Set column headings and styles for config table
        # self.config_description.heading("ConfigID", text="Config ID")
        # self.config_description.heading("Legs", text="Legs")
        # self.config_description.heading("DTE", text="DTE")

        # self.config_description.column("ConfigID", width=300)
        # self.config_description.column("Legs", width=300)
        # self.config_description.column("DTE", width=300)
        # style.configure(
        #     "Config.Treeview",
        #     background="#D3D3D3",
        #     foreground="black",
        #     rowheight=25,
        #     fieldbackground="#D3D3D3",
        # )


    def add_instrument(
        self, 
        sectype,
        ticker,
        multiplier,
        exchange,
        trading_class,
        currency,
        con_id,
        primary_exchange,
    ):
        # Validate inputs
        # if not self.validate_input(ticker, "Ticker"):
        #     return
        # if not self.validate_input(ticker, "Right"):
        #     return
        # if not self.validate_input(trading_class, "Trading Class"):
        #     return
        # if not sectype:
        #     messagebox.showerror("Validation Error", "SecType cannot be empty")
        #     return

        # Add instrument details to the instrument tree
        instrument_id = 1

        # Add instrument details to the instrument tree
        row_values = (
                instrument_id,
                ticker,
                sectype,
                currency,
                multiplier,
                exchange,
                trading_class,
                "coni ",
                "Pri Exh",
            )

        # Get the current number of items in the treeview
        num_items = len(self.instrument_table.get_children())

        if num_items % 2 == 1:
            self.instrument_table.insert(
                "",
                "end",
                iid=instrument_id,
                text=num_items + 1,
                values=row_values,
                tags=("oddrow",),
            )
        else:
            self.instrument_table.insert(
                "",
                "end",
                iid=instrument_id,
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

            con_id_entry = ttk.Entry(input_frame, width=12)
            con_id_entry.grid(column=6, row=row_loc, padx=5, pady=5)

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
                    con_id = input_frame.grid_slaves(row=row_loc, column=6)[0].get()
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
                        con_id,
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
                con_id = input_frame.grid_slaves(row=row_loc, column=6)[0].get()
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
                        con_id,
                        primary_exchange,
                    )
                )

            print("Combo Values: ", combo_values)

            self.add_instrument(*combo_values[0])

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


























# def update_settings(self):
    #     # Get the field values
    #     number_of_trades_allowed = self.field_values[0].get().strip()
    #     max_ba_spread = self.field_values[1].get().strip()
    #     price_gap_threshold = self.field_values[2].get().strip()
    #     stoploss_threshold = self.field_values[3].get().strip()
    #     number_of_iterations = self.field_values[4].get().strip()
    #     sleep_time_between_iterations = self.field_values[5].get().strip()
    #     trade_start_time = self.field_values[6].get().strip()
    #     trade_end_time = self.field_values[7].get().strip()
    #     max_nlv_exposure_per_trade = self.field_values[8].get().strip()
    #
    #     flag_valid_settings = self.validate_settings_values(
    #         number_of_trades_allowed,
    #         max_ba_spread,
    #         price_gap_threshold,
    #         stoploss_threshold,
    #         number_of_iterations,
    #         sleep_time_between_iterations,
    #         trade_start_time,
    #         trade_end_time,
    #         max_nlv_exposure_per_trade,
    #     )
    #
    #     # Invalid setttings
    #     if not flag_valid_settings:
    #         time.sleep(MESSAGE_TIME_IN_SECONDS)
    #
    #         # Clear the message label
    #         self.clear_message_label()
    #
    #         return
    #
    #     # Convert to int and floats
    #     number_of_trades_allowed = int(number_of_trades_allowed)
    #     max_ba_spread = float(max_ba_spread)
    #     price_gap_threshold = float(price_gap_threshold)
    #     stoploss_threshold = float(stoploss_threshold)
    #     number_of_iterations = int(number_of_iterations)
    #     sleep_time_between_iterations = float(sleep_time_between_iterations)
    #     trade_start_time = trade_start_time
    #     trade_end_time = trade_end_time
    #     max_nlv_exposure_per_trade = float(max_nlv_exposure_per_trade)
    #
    #     Utils.update_setting_in_system(
    #         number_of_trades_allowed,
    #         max_ba_spread,
    #         price_gap_threshold,
    #         stoploss_threshold,
    #         number_of_iterations,
    #         sleep_time_between_iterations,
    #         trade_start_time,
    #         trade_end_time,
    #         max_nlv_exposure_per_trade,
    #     )
    #
    #     # Update the settings
    #     Utils.update_settings_in_config_file(
    #         number_of_trades_allowed,
    #         max_ba_spread,
    #         price_gap_threshold,
    #         stoploss_threshold,
    #         number_of_iterations,
    #         sleep_time_between_iterations,
    #         trade_start_time,
    #         trade_end_time,
    #         max_nlv_exposure_per_trade,
    #     )
    #
    #     message = "Settings Updated Successfully."
    #     # Clear the message label
    #     self.update_message_label.config(text=message)
    #     self.last_update_settings_mssg_time = time.time()
    #     time.sleep(MESSAGE_TIME_IN_SECONDS)
    #
    #     # Clear the message label
    #     self.clear_message_label()
    #
    # def clear_message_label(self):
    #     current_time = time.time()
    #     time_difference = current_time - self.last_update_settings_mssg_time
    #
    #     difference_in_seconds = int(time_difference)
    #     if difference_in_seconds >= MESSAGE_TIME_IN_SECONDS - 0.5:
    #         # Clear the message label
    #         self.update_message_label.config(text="")
    #
    # def validate_settings_values(
    #     self,
    #     number_of_trades_allowed,
    #     max_ba_spread,
    #     price_gap_threshold,
    #     stoploss_threshold,
    #     number_of_iterations,
    #     sleep_time_between_iterations,
    #     trade_start_time,
    #     trade_end_time,
    #     max_nlv_exposure_per_trade,
    # ):
    #     result_flag = True
    #
    #     # Validate is Float
    #     if not Utils.is_non_negative_integer(number_of_trades_allowed):
    #         message = "Please enter valid values for '# of Trades'.\nThe value should be an non-negative integer."
    #         result_flag = False
    #
    #     elif not Utils.is_non_negative_number(max_ba_spread):
    #         message = "Please enter valid values for '% Spread'.\nThe value should be an non-negative number."
    #         result_flag = False
    #     elif not Utils.is_non_negative_number(price_gap_threshold):
    #         message = "Please enter valid values for '% Above Entry Price'.\nThe value should be an non-negative number."
    #         result_flag = False
    #     elif not Utils.is_non_negative_number(stoploss_threshold):
    #         message = "Please enter valid values for 'Max Stoploss % Below Entry'.\nThe value should be an non-negative number."
    #         result_flag = False
    #     elif not Utils.is_non_negative_integer(number_of_iterations):
    #         message = "Please enter valid values for '# of Iterations'.\nThe value should be an non-negative integer."
    #         result_flag = False
    #     elif not Utils.is_non_negative_number(sleep_time_between_iterations):
    #         message = "Please enter valid values for 'Wait Time Between Iterations'.\nThe value should be an non-negative number."
    #         result_flag = False
    #     elif not Utils.is_time(trade_start_time):
    #         message = "Please enter valid values for 'Trade Start Time'.\nThe value should be a time in the format HH:MM:SS."
    #         result_flag = False
    #     elif not Utils.is_time(trade_end_time):
    #         message = "Please enter valid values for 'Trade End Time'.\nThe value should be a time in the format HH:MM:SS."
    #         result_flag = False
    #     elif not Utils.is_non_negative_number(max_nlv_exposure_per_trade):
    #         message = "Please enter valid values for 'Max N.L.V. Exposure per Trade'.\nThe value should be an non-negative number."
    #         result_flag = False
    #     else:
    #         pass
    #
    #     # if error
    #     if not result_flag:
    #         self.last_update_settings_mssg_time = time.time()
    #
    #         # Display Error Message, in the bottom label
    #         self.update_message_label.config(text=message)
    #
    #     return result_flag
    #
    # def update_trading_rules(self, event):
    #     # Get the current settings from option_combo_scanner.StrategyVariable
    #     self.field_values[0].set(strategy_variables.number_of_trades_allowed)
    #     self.field_values[1].set(strategy_variables.max_ba_spread)
    #     self.field_values[2].set(strategy_variables.price_gap_threshold)
    #     self.field_values[3].set(strategy_variables.stoploss_threshold)
    #     self.field_values[4].set(strategy_variables.number_of_iterations)
    #     self.field_values[5].set(strategy_variables.sleep_time_between_iterations)
    #     self.field_values[6].set(strategy_variables.trade_start_time)
    #     self.field_values[7].set(strategy_variables.trade_end_time)
