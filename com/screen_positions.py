"""
Created on 13-Apr-2023

@author: Karan
"""

from com import *
from com.variables import *
from com.combination_helper import *
from com.upload_orders_from_csv import (
    make_multiline_mssg_for_gui_popup,
    is_float_upload_order,
)


class ScreenPositions(object):
    def __init__(self, master_notebook):
        """
        Constructor
        """
        self.notebook = master_notebook

        self.positions_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.positions_tab, text="  Positions  ")
        self.create_positions_tab()

    # Method to create position table
    def create_positions_tab(self):
        # Add widgets to the Order Book tab here

        # Create Treeview Frame for active combo table
        positions_table_frame = ttk.Frame(self.positions_tab, padding=20)
        positions_table_frame.pack(pady=20)

        # Place in center
        positions_table_frame.place(relx=0.5, anchor=tk.CENTER)
        positions_table_frame.place(y=390)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(positions_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.positions_table = ttk.Treeview(
            positions_table_frame,
            yscrollcommand=tree_scroll.set,
            height=29,
            selectmode="extended",
        )

        # Pack to the screen
        self.positions_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.positions_table.yview)

        """positions_table_columns = (
            "Unique ID",
            "#Legs",
            "Tickers",
            "#Net Position",
        )"""

        # Column in order book table
        self.positions_table["columns"] = variables.positions_table_columns

        # Creating Columns
        self.positions_table.column("#0", width=0, stretch="no")
        self.positions_table.column("Unique ID", anchor="center", width=213)
        self.positions_table.column("#Legs", anchor="center", width=213)
        self.positions_table.column("Tickers", anchor="center", width=685)
        self.positions_table.column("#Net Position", anchor="center", width=213)
        self.positions_table.column("Account ID", anchor="center", width=213)
        self.positions_table.column(
            "Account ID Unique ID Combo", anchor="center", width=0, stretch="no"
        )

        # Create Headings
        self.positions_table.heading("#0", text="", anchor="w")
        self.positions_table.heading("Unique ID", text="Unique ID", anchor="center")
        self.positions_table.heading("#Legs", text="#Legs", anchor="center")
        self.positions_table.heading("Tickers", text="Tickers", anchor="center")
        self.positions_table.heading(
            "#Net Position",
            text="#Net Position",
            anchor="center",
        )
        self.positions_table.heading(
            "Account ID",
            text="Account ID",
            anchor="center",
        )
        self.positions_table.heading(
            "Account ID Unique ID Combo",
            text="Account ID Unique ID Combo",
            anchor="center",
        )

        # Back ground
        self.positions_table.tag_configure("oddrow", background="white")
        self.positions_table.tag_configure("evenrow", background="lightblue")

        self.positions_table.bind("<Button-3>", self.positions_table_right_click)

    # Method to define position table right click option
    def positions_table_right_click(self, event):
        # get the Treeview row that was clicked
        row = self.positions_table.identify_row(event.y)

        if row:
            # select the row
            self.positions_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.positions_table, tearoff=0)
            menu.add_command(
                label="View Details",
                command=lambda: variables.screen.display_combination_details(
                    "positions"
                ),
            )
            menu.add_command(label="Quick Exit", command=lambda: self.quick_exit())
            menu.add_command(
                label="Quick Exit All", command=lambda: self.quick_exit_all()
            )
            menu.add_command(label="Edit Position", command=lambda: self.edit_postion())
            menu.add_command(
                label="Flip Order", command=lambda: self.quick_exit(flag_flip=True)
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    # Method to close position across all accounts
    def quick_exit_all(self):
        unique_id_account_id_combined = self.positions_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.positions_table.item(
            unique_id_account_id_combined, "values"
        )  # get the values of the selected row

        unique_id = int(values[0])

        self.display_quick_exit_order_specs(unique_id, None, flag_all=True)

    # Method to close position of combo for account ID
    def quick_exit(self, flag_flip=False):
        unique_id_account_id_combined = self.positions_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.positions_table.item(
            unique_id_account_id_combined, "values"
        )  # get the values of the selected row

        unique_id = int(values[0])

        # Get account id
        account_id = values[4]

        self.display_quick_exit_order_specs(unique_id, account_id, flag_flip=flag_flip)

    # Method to edit position
    def edit_postion(self):
        unique_id_account_id_combined = self.positions_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.positions_table.item(
            unique_id_account_id_combined, "values"
        )  # get the values of the selected row

        unique_id = int(values[0])

        # Get account id
        account_id = values[4]

        # existing position
        existing_position = int(values[3])

        # create pop up
        self.edit_postion_pop_up(unique_id, account_id, existing_position)

    # Method to create pop up for edit position
    def edit_postion_pop_up(self, unique_id, account_id=None, existing_position=None):
        try:
            # Get Ticker String
            # Get combo obj
            local_stored_copy_of_combo_object = variables.unique_id_to_combo_obj[
                unique_id
            ]

            # Ticker String
            ticker_string = make_informative_combo_string(
                local_stored_copy_of_combo_object
            )

        except Exception as e:
            # Error pop up
            error_title = f"Could Not get ticker string for unique ID"
            error_string = f"Could Not get ticker string for unique ID "

            variables.screen.display_error_popup(error_title, error_string)

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Exception inside getting ticker string inside conditional switch, Exp: {e}"
                )

        try:
            current_price_unique_id = variables.unique_id_to_prices_dict[unique_id]

            current_buy_price, current_sell_price = (
                current_price_unique_id["BUY"],
                current_price_unique_id["SELL"],
            )

            current_price = (current_buy_price + current_sell_price) / 2

        except Exception as e:
            # Error pop up
            error_title = f"Could Not get current price for unique ID"
            error_string = f"Could Not get current price for unique ID"

            variables.screen.display_error_popup(error_title, error_string)

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Exception inside getting current price inside conditional switch, Exp: {e}"
                )

            return

        # Create a enter unique id popup window
        enter_target_position_popup = tk.Toplevel()

        title = f"Edit Position, Unique ID: {unique_id}, Account ID: {account_id}"
        enter_target_position_popup.title(title)

        enter_target_position_popup.geometry("600x120")

        # Create main frame
        enter_target_position_popup_frame = ttk.Frame(
            enter_target_position_popup, padding=20
        )
        enter_target_position_popup_frame.pack(fill="both", expand=True)

        # Create a frame for the input fields
        enter_target_position_frame = ttk.Frame(
            enter_target_position_popup_frame, padding=20
        )
        enter_target_position_frame.pack(fill="both", expand=True)

        # Add a label and entry field for the user to enter an integer
        ttk.Label(enter_target_position_frame, text="Enter Target Position:").grid(
            column=0, row=3, padx=5, pady=5
        )

        # Adding the entry for user to insert the target position
        target_position_entry = ttk.Entry(enter_target_position_frame)
        target_position_entry.grid(column=1, row=3, padx=5, pady=5)

        # Add a label and entry field for the user to enter an integer
        ttk.Label(enter_target_position_frame, text="Select Account:").grid(
            column=2, row=3, padx=5, pady=5
        )

        current_session_accounts_options = variables.current_session_accounts

        if account_id != None:
            current_session_accounts_options = [account_id]

        # Create the combo box
        account_id_combo_box = ttk.Combobox(
            enter_target_position_frame,
            # textvariable=selected_account_option,
            width=18,
            values=current_session_accounts_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        account_id_combo_box.current(0)
        account_id_combo_box.grid(column=3, row=3, padx=5, pady=5)

        def on_click_proceed_button(existing_position):
            # Getting unique id use entered
            target_position = target_position_entry.get()

            # get account id
            account_id = account_id_combo_box.get().strip()

            # Check if user entered value is valid integer
            if not is_integer(target_position):
                # Showing error pop up
                error_title = f"Invalid Target Position Entered"
                error_string = f"Please Enter Valid Target Position "

                variables.screen.display_error_popup(error_title, error_string)

                return

            else:
                # Convert valid value to int
                target_position = int(target_position)

            if existing_position == None:
                existing_position = variables.map_unique_id_to_positions[
                    int(unique_id)
                ][account_id]

            # Checking if format of unique id entered is valid and available in system
            if target_position != existing_position:
                # Get number of lots to trade
                positions_to_dummy_trade = target_position - existing_position

                # Place dummy order
                insert_order_when_conditional_add_switch_fails(
                    account_id,
                    unique_id,
                    positions_to_dummy_trade,
                    ticker_string,
                    entry_price=current_price,
                )

                # Destroy pop up
                enter_target_position_popup.destroy()

            elif target_position == existing_position:
                # Show error pop up
                error_title = f"Target position Must not be equal to existing position"
                error_string = f"Target position Must not be equal to existing position"

                variables.screen.display_error_popup(error_title, error_string)
                return

        # Add a button to edit position
        proceed_button = ttk.Button(
            enter_target_position_frame,
            text="Proceed",
            command=lambda: on_click_proceed_button(existing_position),
        )

        proceed_button.grid(column=4, row=3, padx=5, pady=5)

        # Place in center
        enter_target_position_frame.place(relx=0.5, anchor=tk.CENTER)
        enter_target_position_frame.place(y=30)

    # Method to fill details for quick exit order
    def display_quick_exit_order_specs(
        self, unique_id, account_id, flag_all=False, flag_flip=False
    ):
        # check if unique id is in current session accounts
        if account_id not in variables.current_session_accounts and not flag_all:
            # Error pop up
            error_title = "Account ID is unavailable in current session."
            error_string = f"Can not trade combo because Account ID: {account_id} \nis unavailable in current session."

            variables.screen.display_error_popup(error_title, error_string)

            return

        current_position = 0
        multi_account_to_position_dict = {}

        if not flag_all:
            try:
                current_position = variables.map_unique_id_to_positions[unique_id][
                    account_id
                ]

                if flag_flip:
                    current_position *= 2

            except Exception as e:
                current_position = 0
                print(f"Exception in quick exit, {unique_id}")

            # Position is Zero can not place quick exit
            if current_position == 0:
                error_title = f"Unique ID: {unique_id}, zero positions"
                error_string = f"Unique ID: {unique_id}, Can not place a quick exit order for zero positions."

                variables.screen.display_error_popup(error_title, error_string)
                return

        else:
            # Get all account ids
            for account_id in variables.current_session_accounts:
                try:
                    current_position_multi = variables.map_unique_id_to_positions[
                        unique_id
                    ][account_id]

                    if flag_flip:
                        current_position_multi *= 2

                except Exception as e:
                    current_position_multi = 0

                    print(f"Exception in quick exit, {unique_id}")

                # Position is Zero can not place quick exit
                if current_position_multi != 0:
                    multi_account_to_position_dict[account_id] = current_position_multi

            try:
                # getting list of account in system and all accounts with positions
                accounts_in_session_with_positions = list(
                    multi_account_to_position_dict.keys()
                )
                accounts_with_positions = list(
                    variables.map_unique_id_to_positions[unique_id].keys()
                )

                # Get accounts not in current session and have positions
                accounts_not_in_system_with_positions = set(
                    accounts_with_positions
                ) - set(accounts_in_session_with_positions)

                # Init string
                accounts_not_in_system_string = ""

                # Get list of account not in sytem and have non zero positions
                for account_not_in_system in accounts_not_in_system_with_positions:
                    # Check if position is non-zero
                    if (
                        variables.map_unique_id_to_positions[unique_id][
                            account_not_in_system
                        ]
                        != 0
                    ):
                        # Concatenate account id in string
                        accounts_not_in_system_string += account_not_in_system + ","

            except Exception as e:
                if variables.flag_debug_mode:
                    print(
                        f'Inside finding accounts not in system for "quick exit all", Exp: {e}'
                    )

        # Create a popup window with the table
        quick_exit_spec_popup = tk.Toplevel()

        # Title
        quick_exit_spec_popup.title(f"Quick Exit, Unique ID: {unique_id}")

        # Geometry
        quick_exit_spec_popup.geometry("690x150")

        # Create a main frame
        quick_exit_popup_frame = ttk.Frame(quick_exit_spec_popup, padding=10)
        quick_exit_popup_frame.pack(fill="both", expand=True)

        # Create a frame for the input fields
        quick_exit_frame = ttk.Frame(quick_exit_popup_frame, padding=10)
        quick_exit_frame.pack(fill="both", expand=True)

        # Add labels and entry fields for each column in the table
        ttk.Label(
            quick_exit_frame,
            text="Order Type",
            width=15,
            anchor="center",
        ).grid(column=0, row=0, padx=10, pady=10)

        ttk.Label(
            quick_exit_frame,
            text="Trigger Price",
            width=15,
            anchor="center",
        ).grid(column=1, row=0, padx=10, pady=10)

        ttk.Label(
            quick_exit_frame,
            text="Trail Value",
            width=15,
            anchor="center",
        ).grid(column=2, row=0, padx=10, pady=10)

        ttk.Label(
            quick_exit_frame,
            text="ATR Multiple",
            width=15,
            anchor="center",
        ).grid(column=3, row=0, padx=5, pady=5)

        ttk.Label(
            quick_exit_frame,
            text="ATR",
            width=15,
            anchor="center",
        ).grid(column=4, row=0, padx=5, pady=5)

        ttk.Label(
            quick_exit_frame,
            text="Execution Engine",
            width=15,
            anchor="center",
        ).grid(column=5, row=0, padx=5, pady=5)

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

        # Create a list of options
        order_type_options = [
            "Market",
            "IB Algo Market",
            "Stop Loss",
            "Trailing Stop Loss",
            "Stop Loss Candle",
        ]

        # get combo object
        # Get combo object using unique ids
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

        combo_obj = local_unique_id_to_combo_obj[unique_id]

        # init
        flag_premium = False

        # get all legs
        all_legs = combo_obj.buy_legs + combo_obj.sell_legs

        # check if any leg is OPT or FOP
        for leg_obj in all_legs:
            if leg_obj.sec_type in ["OPT", "FOP"]:
                # set value to True
                flag_premium = True

        # if flag is true
        if flag_premium:
            order_type_options.append("Stop Loss Premium")

            order_type_options.append("Trailing SL Premium")

            premium_dict = variables.screen.get_premium_for_orders(all_legs)

        # Create a Tkinter variable
        selected_order_type_option = tk.StringVar(quick_exit_frame)
        selected_order_type_option.set(order_type_options[0])  # set the default option

        # Create the combo box
        order_type_options_combo_box = ttk.Combobox(
            quick_exit_frame,
            textvariable=selected_order_type_option,
            width=16,
            values=order_type_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        order_type_options_combo_box.current(0)
        order_type_options_combo_box.grid(column=0, row=1, padx=10, pady=10)

        execution_engine_options = [True, False]

        # Create the combo box
        flag_execution_engine_combo_box = ttk.Combobox(
            quick_exit_frame,
            width=15,
            values=execution_engine_options,
            state="readonly",
            style="Custom.TCombobox",
        )

        flag_execution_engine_combo_box.current(
            execution_engine_options.index(variables.flag_use_execution_engine)
        )
        flag_execution_engine_combo_box.grid(column=5, row=1, padx=10, pady=10)

        # Trigger Price Entry
        trigger_price_entry = ttk.Entry(
            quick_exit_frame,
            width=15,
        )
        trigger_price_entry.grid(column=1, row=1, padx=10, pady=10)

        # Trail Value Entry
        trail_value_entry = ttk.Entry(
            quick_exit_frame,
            width=15,
        )
        trail_value_entry.grid(column=2, row=1, padx=10, pady=10)

        atr_multiple_entry = ttk.Entry(
            quick_exit_frame,
            width=15,
        )
        atr_multiple_entry.grid(column=3, row=1, padx=5, pady=5)

        atr_entry = ttk.Entry(
            quick_exit_frame,
            width=15,
        )
        atr_entry.grid(column=4, row=1, padx=5, pady=5)

        # HV Related Column
        order_atr_values = copy.deepcopy(
            variables.map_unique_id_to_atr_for_order_values
        )

        # Get atr value
        try:
            # Get ATR value
            atr = (
                "N/A"
                if order_atr_values[unique_id] == "N/A"
                else order_atr_values[unique_id]
            )

        except Exception as e:
            # In case of exception set it to N/A
            atr = "N/A"

            # Print to console
            if variables.flag_debug_mode:
                print(f"For Unique ID: {unique_id}, Unable to get ATR")

        # Insert ATR in entry widget for ATR
        quick_exit_frame.grid_slaves(row=1, column=4)[0].insert(0, atr)

        # Make entry widget readonly
        quick_exit_frame.grid_slaves(row=1, column=4)[0].config(state="readonly")

        # Place in center
        quick_exit_frame.place(relx=0.5, anchor=tk.CENTER)
        quick_exit_frame.place(y=35)

        # Create a frame for the "Add Combo" button
        button_frame = ttk.Frame(quick_exit_popup_frame)
        button_frame.place(relx=0.5, anchor=tk.CENTER)
        button_frame.place(y=110)

        # Create the "Add Combo" button
        ttk.Button(
            button_frame,
            text="Exit",
            command=lambda: on_click_exit_button(),
        ).pack(side="right")

        def on_click_exit_button():
            if not flag_all:
                self.add_quick_exit_order(
                    unique_id,
                    quick_exit_spec_popup,
                    selected_order_type_option,
                    quick_exit_frame,
                    current_position,
                    account_id,
                )

            else:
                # if string is non empty
                if accounts_not_in_system_string != "":
                    error_msg = (
                        "Failed to exit positions for account IDs not present in current session: "
                        + accounts_not_in_system_string[:-1]
                    )

                    # show error pop up
                    variables.screen.display_error_popup(
                        "For Quick Exit ALL, Account IDs not in current session",
                        make_multiline_mssg_for_gui_popup(error_msg),
                    )

                for account in multi_account_to_position_dict:
                    current_position_multi = multi_account_to_position_dict[account]

                    self.add_quick_exit_order(
                        unique_id,
                        quick_exit_spec_popup,
                        selected_order_type_option,
                        quick_exit_frame,
                        current_position_multi,
                        account,
                    )

            # Reached end means no error were found place order
            # Close the popup
            quick_exit_spec_popup.destroy()

        def on_order_type_combobox_selected(event=None):
            order_type = selected_order_type_option.get()

            # [row=1, column=1] => Trigger price field
            # [row=1, column=2] => Trail value field
            # [row=1, column=3] => ATR multiple field
            # For order type "Market"
            if order_type == "Market":
                # Make entry widget disabled
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(state="normal")

                # Delete values from fields
                quick_exit_frame.grid_slaves(row=1, column=1)[0].delete(0, "end")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")

                # Set fields to empty values
                quick_exit_frame.grid_slaves(row=1, column=1)[0].insert(0, "")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].insert(0, "")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].insert(0, "")

                # Make entry widget disabled
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(
                    state="disabled"
                )
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )

            # [row=1, column=1] => Trigger price field
            # [row=1, column=2] => Trail value field
            # [row=1, column=3] => ATR multiple field
            # For order type "Stop loss"
            elif order_type == "Stop Loss":
                # Make entry widget disabled
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(state="normal")

                # Delete values from fields
                quick_exit_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")

                # Set fields to empty values
                quick_exit_frame.grid_slaves(row=1, column=2)[0].insert(0, "")

                # Make entry widget selectively available
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(state="normal")

            # [row=1, column=1] => Trigger price field
            # [row=1, column=2] => Trail value field
            # [row=1, column=3] => ATR multiple field
            # For order type "Trailing Stop Loss"
            elif order_type == "Trailing Stop Loss":
                # Make entry widget disabled
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(state="normal")

                # Delete values from fields
                quick_exit_frame.grid_slaves(row=1, column=1)[0].delete(0, "end")

                # Set fields to empty values
                quick_exit_frame.grid_slaves(row=1, column=1)[0].insert(0, "")

                # Make entry widget selectively available
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(
                    state="disabled"
                )
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(state="normal")

            # [row=1, column=1] => Trigger price field
            # [row=1, column=2] => Trail value field
            # [row=1, column=3] => ATR multiple field
            # For order type "IB Algo Market"
            elif order_type == "IB Algo Market":
                # Make entry widget disabled
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(state="normal")

                # Delete values from fields
                quick_exit_frame.grid_slaves(row=1, column=1)[0].delete(0, "end")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")

                # Set fields to empty values
                quick_exit_frame.grid_slaves(row=1, column=1)[0].insert(0, "")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].insert(0, "")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].insert(0, "")

                # Make entry widget disabled
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(
                    state="disabled"
                )
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )

            elif order_type == "Stop Loss Premium":
                if current_position > 0:
                    buy_sell_action = "SELL"
                else:
                    buy_sell_action = "BUY"

                try:
                    # dict for combo prices
                    local_unique_id_to_prices_dict = copy.deepcopy(
                        variables.unique_id_to_prices_dict
                    )

                    current_buy_price, current_sell_price = (
                        local_unique_id_to_prices_dict[unique_id]["BUY"],
                        local_unique_id_to_prices_dict[unique_id]["SELL"],
                    )

                    current_price = (current_buy_price + current_sell_price) / 2

                except Exception as e:
                    if variables.flag_debug_mode:
                        print(
                            f"Exception inside getting current price for stop loss premium, Exp: {e}"
                        )

                    current_price = "N/A"

                # Init
                value_to_prefill = "None"

                net_premium = "None"

                # getting value of trigger price to refill
                if (
                    premium_dict != None
                    and "Stop Loss Premium" in premium_dict
                    and is_float_upload_order(current_price)
                ):
                    net_premium = premium_dict["Stop Loss Premium"]

                    # check if it is float
                    if is_float_upload_order(net_premium):
                        # get trigger price
                        if buy_sell_action.upper() == "BUY":
                            value_to_prefill = current_price + abs(net_premium)

                        else:
                            value_to_prefill = current_price - abs(net_premium)

                        value_to_prefill = round(value_to_prefill, 2)

                    else:
                        value_to_prefill = "N/A"

                else:
                    value_to_prefill = "N/A"

                # Make entry widget disabled
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(state="normal")

                # Delete values from fields
                quick_exit_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                quick_exit_frame.grid_slaves(row=1, column=1)[0].delete(0, "end")

                # Set fields to empty values
                quick_exit_frame.grid_slaves(row=1, column=2)[0].insert(0, "")

                quick_exit_frame.grid_slaves(row=1, column=1)[0].insert(
                    0, value_to_prefill
                )

                # Make entry widget selectively available
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(
                    state="readonly"
                )
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )

            elif order_type == "Trailing SL Premium":
                if current_position > 0:
                    buy_sell_action = "SELL"
                else:
                    buy_sell_action = "BUY"

                try:
                    # dict for combo prices
                    local_unique_id_to_prices_dict = copy.deepcopy(
                        variables.unique_id_to_prices_dict
                    )

                    current_buy_price, current_sell_price = (
                        local_unique_id_to_prices_dict[unique_id]["BUY"],
                        local_unique_id_to_prices_dict[unique_id]["SELL"],
                    )

                    current_price = (current_buy_price + current_sell_price) / 2

                except Exception as e:
                    if variables.flag_debug_mode:
                        print(
                            f"Exception inside getting current price for stop loss premium, Exp: {e}"
                        )

                    current_price = "N/A"

                # Init
                value_to_prefill = "None"

                net_premium = "None"

                # getting value of trigger price to refill
                if (
                    premium_dict != None
                    and "Stop Loss Premium" in premium_dict
                    and is_float_upload_order(current_price)
                ):
                    net_premium = premium_dict["Stop Loss Premium"]

                    # check if it is float
                    if is_float_upload_order(net_premium):
                        value_to_prefill = abs(net_premium)

                        value_to_prefill = round(value_to_prefill, 2)

                    else:
                        value_to_prefill = "N/A"

                else:
                    value_to_prefill = "N/A"

                # Make entry widget disabled
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(state="normal")

                # Delete values from fields
                quick_exit_frame.grid_slaves(row=1, column=1)[0].delete(0, "end")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                # Set fields to empty values
                quick_exit_frame.grid_slaves(row=1, column=2)[0].insert(
                    0, value_to_prefill
                )

                quick_exit_frame.grid_slaves(row=1, column=1)[0].insert(0, "")

                # Make entry widget selectively available
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(
                    state="disabled"
                )
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(
                    state="readonly"
                )
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )

            elif order_type == "Stop Loss Candle":
                if current_position > 0:
                    buy_sell_action = "SELL"
                else:
                    buy_sell_action = "BUY"

                # Init
                value_to_prefill = "N/A"

                # get last candle high or low price
                try:
                    # check if action is buy
                    if buy_sell_action.upper() == "BUY":
                        value_to_prefill = (
                            variables.map_unique_id_to_candle_for_order_values[
                                unique_id
                            ]["High Candle Value"]
                        )

                    # if action is sell
                    else:
                        value_to_prefill = (
                            variables.map_unique_id_to_candle_for_order_values[
                                unique_id
                            ]["Low Candle Value"]
                        )

                except Exception as e:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception inside getting current price for stop loss premium, Exp: {e}"
                        )

                    # set value to N/A
                    value_to_prefill = "N/A"

                # Make entry widget disabled
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(state="normal")
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(state="normal")

                # Delete values from fields
                quick_exit_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                quick_exit_frame.grid_slaves(row=1, column=1)[0].delete(0, "end")
                # Set fields to empty values
                quick_exit_frame.grid_slaves(row=1, column=2)[0].insert(0, "")

                quick_exit_frame.grid_slaves(row=1, column=1)[0].insert(
                    0, value_to_prefill
                )

                # Make entry widget selectively available
                quick_exit_frame.grid_slaves(row=1, column=1)[0].config(
                    state="readonly"
                )
                quick_exit_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )
                quick_exit_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )

        # Bind the function to the ComboBoxSelected event
        order_type_options_combo_box.bind(
            "<<ComboboxSelected>>", on_order_type_combobox_selected
        )

        # Adjust fields at start
        on_order_type_combobox_selected()

    # Method to add quick exit order
    def add_quick_exit_order(
        self,
        unique_id,
        quick_exit_spec_popup,
        selected_order_type_option,
        quick_exit_frame,
        current_position,
        account_id,
    ):
        # Getting the value out
        order_type = selected_order_type_option.get()
        trigger_price = quick_exit_frame.grid_slaves(row=1, column=1)[0].get().strip()
        trail_value = quick_exit_frame.grid_slaves(row=1, column=2)[0].get().strip()
        atr_multiple = quick_exit_frame.grid_slaves(row=1, column=3)[0].get().strip()
        atr = quick_exit_frame.grid_slaves(row=1, column=4)[0].get().strip()
        execution_engine = (
            quick_exit_frame.grid_slaves(row=1, column=5)[0].get().strip()
        )

        # get boolean value for execution engine flag
        if execution_engine == "True":
            execution_engine = True

        else:
            execution_engine = False

        if current_position > 0:
            buy_sell_action = "SELL"
        else:
            buy_sell_action = "BUY"

        if order_type == "Stop Loss Premium":
            order_type = "Stop Loss"

        elif order_type == "Trailing SL Premium":
            order_type = "Trailing Stop Loss"

        elif order_type == "Stop Loss Candle":
            order_type = "Stop Loss"

        # Getting Current buy, sell price for the combo
        current_price_unique_id = variables.unique_id_to_prices_dict[unique_id]
        current_buy_price, current_sell_price = (
            current_price_unique_id["BUY"],
            current_price_unique_id["SELL"],
        )

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Order Type: {order_type}, Trigger: {trigger_price}, Trail: {trail_value}, Current Position: {current_position}"
            )

        # Validating we have prices for the combo
        if (
            order_type in ["Trailing Stop Loss", "Stop Loss"]
            and buy_sell_action == "BUY"
            and current_buy_price == None
        ):
            error_title = "Unique ID: {unique_id}, Buy Price is unavailable."
            error_string = f"Can not Place {order_type}, [Exit(Sell)] order as buy price is unavailable for combo."

            variables.screen.display_error_popup(error_title, error_string)
            return
        elif (
            order_type in ["Trailing Stop Loss", "Stop Loss"]
            and buy_sell_action == "SELL"
            and current_sell_price == None
        ):
            error_title = "Unique ID: {unique_id}, Sell Price is unavailable."
            error_string = f"Can not Place {order_type}, [Exit(Sell)] order as sell price is unavailable for combo."

            variables.screen.display_error_popup(error_title, error_string)
            return
        else:
            try:
                current_buy_price = (
                    float(current_buy_price) if current_buy_price != None else None
                )
            except Exception as e:
                print("Exception Inside Qucik Exit, {e}")

            try:
                current_sell_price = (
                    float(current_sell_price) if current_sell_price != None else None
                )
            except Exception as e:
                print("Exception Inside Quick Exit, {e}")

        # Stop Loss Orders
        if order_type == "Stop Loss":
            """try:
                trigger_price = float(trigger_price)
            except Exception as e:
                error_title = "Missing Trigger Price"
                error_string = "Please provide a Trigger Price for Stop Loss Order."

                variables.screen.display_error_popup(error_title, error_string)
                return"""

            # Check if both trigger price and atr multiple is filled
            if trigger_price != "" and atr_multiple != "":
                error_title = "Invalid combination of values"
                error_string = (
                    "Values for both Trigger Price and ATR Multiple must not be filled."
                )

                variables.screen.display_error_popup(error_title, error_string)
                return

            # Check if both trigger price and atr multiple is empty
            elif trigger_price == "" and atr_multiple == "":
                error_title = "Invalid combination of values"
                error_string = (
                    "Values for both Trigger Price and ATR Multiple must not be empty."
                )

                variables.screen.display_error_popup(error_title, error_string)
                return

            # Check if trigger price is valid
            elif trigger_price != "" and atr_multiple == "":
                try:
                    trigger_price = float(trigger_price)

                    # Setting values of atr and atr multiple None
                    atr_multiple = "None"
                    atr = "None"

                except Exception as e:
                    error_title = "Invalid Trigger Price"
                    error_string = (
                        "Please provide a valid Trigger Price for Stop Loss Order."
                    )

                    variables.screen.display_error_popup(error_title, error_string)
                    return

            # Check if atr multiple is valid and have valid trigger price value
            elif trigger_price == "" and atr_multiple != "":
                # checking if atr multiple value is valid
                try:
                    atr_multiple = float(atr_multiple)

                    # check if atrr multiple is less than or equal to zero
                    if atr_multiple <= 0:
                        raise Exception("Invalid ATR Multiple")

                except Exception as e:
                    error_title = "Invalid ATR Multiple"
                    error_string = (
                        "Please provide a valid ATR Multiple for Stop Loss Order."
                    )

                    variables.screen.display_error_popup(error_title, error_string)
                    return

                # checking if atr value is valid
                try:
                    atr = float(atr)

                except Exception as e:
                    error_title = "Invalid ATR"
                    error_string = "Unable to get valid ATR for Stop Loss Order."

                    variables.screen.display_error_popup(error_title, error_string)
                    return

                # checking if trigger price calculations are valid
                try:
                    avg_price_combo = "N/A"

                    # Make it available in variables
                    avg_price_combo = (
                        variables.unique_id_to_prices_dict[unique_id]["BUY"]
                        + variables.unique_id_to_prices_dict[unique_id]["SELL"]
                    ) / 2

                    # When action is BUY
                    if buy_sell_action == "BUY":
                        # Get trigger price
                        trigger_price = avg_price_combo + atr_multiple * atr

                    # When action is SELL
                    elif buy_sell_action == "SELL":
                        # Get trigger price
                        trigger_price = avg_price_combo - atr_multiple * atr

                except Exception as e:
                    error_title = "Invalid Trigger Price"
                    error_string = f"Unable to get valid Trigger Price based on ATR Multiple: {atr_multiple}, \nATR: {atr} and Avg Price for Combo: {avg_price_combo} "

                    variables.screen.display_error_popup(error_title, error_string)
                    return

            if (order_type == "Stop Loss") and (
                buy_sell_action == "BUY" and current_buy_price > trigger_price
            ):
                error_title = "Invalid Trigger Price"
                error_string = "Trigger Price for [Exit(Buy)] Order must be greater than current Buy Price."

                variables.screen.display_error_popup(error_title, error_string)
                return

            elif (order_type == "Stop Loss") and (
                buy_sell_action == "SELL" and current_sell_price < trigger_price
            ):
                error_title = "Invalid Trigger Price"
                error_string = "Trigger Price for [Exit(Sell)] Order must be lower than current Sell Price."

                variables.screen.display_error_popup(error_title, error_string)
                return

        # Trailing Stop Loss Orders
        elif order_type == "Trailing Stop Loss":
            # check if both trail value and atr multiple is filled
            if trail_value != "" and atr_multiple != "":
                error_title = "Invalid combination of values"
                error_string = (
                    "Values for both Trail Value and ATR Multiple must not be filled."
                )

                variables.screen.display_error_popup(error_title, error_string)
                return

            # Check if both trail value and atr multiple is empty
            elif trail_value == "" and atr_multiple == "":
                error_title = "Invalid combination of values"
                error_string = (
                    "Values for both Trail Value and ATR Multiple must not be empty."
                )

                variables.screen.display_error_popup(error_title, error_string)
                return

            # Check if trail value is valid
            elif trail_value != "" and atr_multiple == "":
                try:
                    trail_value = float(trail_value)

                    # Setting values of atr and atr multiple None
                    atr_multiple = "None"
                    atr = "None"

                except Exception as e:
                    error_title = "Invalid Trail Value"
                    error_string = (
                        "Please provide a valid Trail Value for Stop Loss Order."
                    )

                    variables.screen.display_error_popup(error_title, error_string)
                    return

            # Check if atr multiple is valid and get valid trail value
            elif trail_value == "" and atr_multiple != "":
                # checking if atr multiple value is valid
                try:
                    atr_multiple = float(atr_multiple)

                    # check if atr multiple is less than or equal to zero
                    if atr_multiple <= 0:
                        raise Exception("Invalid ATR Multiple")

                except Exception as e:
                    error_title = "Invalid ATR Multiple"
                    error_string = (
                        "Please provide a valid ATR Multiple for Stop Loss Order."
                    )

                    variables.screen.display_error_popup(error_title, error_string)
                    return

                # checking if atr value is valid
                try:
                    atr = float(atr)

                except Exception as e:
                    error_title = "Invalid ATR"
                    error_string = (
                        "Unable to get valid ATR for Trailing Stop Loss Order."
                    )

                    variables.screen.display_error_popup(error_title, error_string)
                    return

                # checking if trail value calcualtions are valid
                try:
                    # Get trigger price
                    trail_value = atr_multiple * atr

                except Exception as e:
                    error_title = "Invalid Trigger Price"
                    error_string = f"Unable to get valid Trail Value based on ATR Multiple: {atr_multiple} and ATR: {atr}"

                    variables.screen.display_error_popup(error_title, error_string)
                    return
            """try:
                trail_value = float(trail_value)
            except Exception as e:
                error_title = "Missing/Invalid Trail Value"
                error_string = "Please provide a Trailing Value for Trailing Stop Loss Order."

                variables.screen.display_error_popup(error_title, error_string)
                return"""

        else:
            # Market orders
            # Setting values of atr and atr multiple None
            atr_multiple = "None"
            atr = "None"
            pass

        # Init
        action = buy_sell_action
        combo_quantity = abs(current_position)
        limit_price = ""
        bypass_rm_check = "True"

        # Send order in a separate thread
        send_order_thread = threading.Thread(
            target=send_order,
            args=(
                unique_id,
                action,
                order_type,
                combo_quantity,
                limit_price,
                trigger_price,
                trail_value,
            ),
            kwargs={
                "atr_multiple": atr_multiple,
                "atr": atr,
                "account_id": account_id,
                "bypass_rm_check": bypass_rm_check,
                "execution_engine": execution_engine,
            },
        )
        send_order_thread.start()
        time.sleep(0.5)

    # Method to insert rows in positions table
    def insert_positions_in_positions_table(self, value):
        # unique_id
        unique_id = value[0]

        # account id
        account_id_uid_combo = value[5]

        # net position
        net_position = value[3]

        # check if net position is zero
        if net_position == 0:
            return

        # Get the current number of items in the treeview
        num_items = len(self.positions_table.get_children())

        if num_items % 2 == 1:
            self.positions_table.insert(
                "",
                "end",
                iid=account_id_uid_combo,
                text=num_items + 1,
                values=value,
                tags=("oddrow",),
            )
        else:
            self.positions_table.insert(
                "",
                "end",
                iid=account_id_uid_combo,
                text=num_items + 1,
                values=value,
                tags=("evenrow",),
            )

    # Method to update positions in GUI table
    def update_positions_in_positions_table(
        self, unique_id_account_id_combined, positions
    ):
        # Set the value to 1 where id column is 4
        variables.positions_table_dataframe.loc[
            variables.positions_table_dataframe["Account ID Unique ID Combo"]
            == unique_id_account_id_combined,
            "#Net Position",
        ] = positions

        # Get the row as a tuple where id column is 4
        row_tuple = tuple(
            variables.positions_table_dataframe[
                variables.positions_table_dataframe["Account ID Unique ID Combo"]
                == unique_id_account_id_combined
            ].values[0]
        )

        # GEt uniqueid and account id
        unique_id = row_tuple[0]
        account_id = row_tuple[4]

        # get table id column
        unique_id_account_id_combined_in_table = self.positions_table.get_children()

        # Get combo details dataframe
        local_positions_details_df = copy.deepcopy(variables.positions_table_dataframe)

        # All the Unique IDs in the System
        all_unique_ids_in_system = local_positions_details_df["Unique ID"].tolist()

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
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Error inside updating positions table, {e}")
        try:
            # Get all the
            if variables.selected_account_group == "ALL":
                all_account_ids_in_account_group = (
                    variables.current_session_accounts
                    + list(variables.map_unique_id_to_positions[unique_id])
                )
            else:
                all_account_ids_in_account_group = copy.deepcopy(
                    variables.account_ids_list_of_selected_acount_group
                )

        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Error inside updating orders book table, {e}")

        # Check if row is present in table and position is non zero
        if (
            str(unique_id_account_id_combined) in unique_id_account_id_combined_in_table
            and positions != 0
        ):
            self.positions_table.set(unique_id_account_id_combined, 3, positions)

        # Check if row is present in table and position is zero
        elif (
            str(unique_id_account_id_combined) in unique_id_account_id_combined_in_table
            and positions == 0
        ):
            self.positions_table.delete(unique_id_account_id_combined)

        # Check if row is not present in table and position is non zero
        elif (
            unique_id in all_unique_ids_in_watchlist
            and account_id in all_account_ids_in_account_group
            and positions != 0
        ):
            self.insert_positions_in_positions_table(row_tuple)

    # Method to update position table
    def update_positions_table_watchlist_changed(self):
        # All the Unique IDs in the System
        # Get combo details dataframe
        local_positions_details_df = copy.deepcopy(variables.positions_table_dataframe)

        # All the Unique IDs in the System
        all_unique_ids_in_system = local_positions_details_df["Unique ID"].tolist()

        # All the rows in positions Table
        all_unique_ids_in_watchlist = all_unique_id_in_positions_table = [
            int(self.positions_table.item(_x)["values"][0])
            for _x in self.positions_table.get_children()
        ]

        # All the rows in positions Table
        all_account_ids_in_account_group = all_account_id_in_positions_table = [
            self.positions_table.item(_x)["values"][4]
            for _x in self.positions_table.get_children()
        ]

        # If we want to update the table as watchlist changed
        if variables.flag_positions_tables_watchlist_changed:
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
            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside updating positions table, {e}")
            try:
                # Get all the
                if variables.selected_account_group == "ALL":
                    all_account_ids_in_account_group = (
                        variables.current_session_accounts
                        + list(
                            variables.map_unique_id_to_positions[
                                next(iter(all_unique_ids_in_system))
                            ]
                        )
                    )
                else:
                    all_account_ids_in_account_group = copy.deepcopy(
                        variables.account_ids_list_of_selected_acount_group
                    )

            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside updating orders book table, {e}")

            # Setting it to False
            variables.flag_positions_tables_watchlist_changed = False
        # print(all_account_ids_in_account_group)
        # Update the rows
        for i, row_val in local_positions_details_df.iterrows():
            # Unique ID of row val
            unique_id = row_val["Unique ID"]

            # Get combo of account id and unique id
            account_id_unique_id_combo = row_val["Account ID Unique ID Combo"]

            # account id
            account_id = row_val["Account ID"]

            # Net positions
            net_position = row_val["#Net Position"]

            if (
                unique_id in all_unique_ids_in_watchlist
                and account_id in all_account_ids_in_account_group
                and net_position != 0
            ):
                # Tuple of vals
                row_val = tuple(row_val)

                if account_id_unique_id_combo in self.positions_table.get_children():
                    # Update the row at once.
                    self.positions_table.item(
                        account_id_unique_id_combo, values=row_val
                    )
                else:
                    # Insert it in the table
                    self.positions_table.insert(
                        "",
                        "end",
                        iid=account_id_unique_id_combo,
                        text="",
                        values=row_val,
                        tags=("oddrow",),
                    )
            else:
                # If this unique_id in positions Table but not in watchlist delete it
                if account_id_unique_id_combo in self.positions_table.get_children():
                    try:
                        self.positions_table.delete(account_id_unique_id_combo)
                    except Exception as e:
                        pass

        try:
            # Filter out the dataframe such that the dataframe only consists of all the unique ids that are present in the watchlist, so sorting will be in correct order.
            local_positions_details_df = local_positions_details_df[
                local_positions_details_df["Unique ID"].isin(
                    all_unique_ids_in_watchlist
                )
            ]
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Error inside updating positions table values, is {e}")

        # All the rows in positions Table
        all_unique_id_in_positions_table = [
            str(self.positions_table.item(_x)["values"][0])
            for _x in self.positions_table.get_children()
        ]  # self.positions_table.get_children()

        # All the rows in positions Table
        all_account_id_in_positions_table = [
            (self.positions_table.item(_x)["values"][4])
            for _x in self.positions_table.get_children()
        ]

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in local_positions_details_df.iterrows():
            # Unique_id
            unique_id = str(row["Unique ID"])

            # account id
            account_id = str(row["Account ID"])

            # Get combo of account id and unique id
            account_id_unique_id_combo = row["Account ID Unique ID Combo"]

            # If unique_id in table
            if account_id_unique_id_combo in self.positions_table.get_children():
                self.positions_table.move(account_id_unique_id_combo, "", counter_row)

                if counter_row % 2 == 0:
                    self.positions_table.item(
                        account_id_unique_id_combo, tags="evenrow"
                    )
                else:
                    self.positions_table.item(account_id_unique_id_combo, tags="oddrow")

                # Increase row count
                counter_row += 1
