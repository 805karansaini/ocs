import time

import pandas as pd

from com import *
from com.variables import *
from com.combination_helper import is_integer
from com.upload_combo_to_application import make_multiline_mssg_for_gui_popup
from com.mysql_io_scale_trader import *
from com.ladder import *
from com.mysql_io import *
from com.sequence import *
from com.order_execution import *
from com.scale_trade_helper import *
from tkinter import *
from com.mysql_io_account_group import *
from com.trade_rm_check_result_module import *
from com.high_low_cal_helper import *


# Class for scale trader tab
class ScreenScaleTrader(object):
    def __init__(self, master_notebook):
        """
        Constructor
        """
        self.notebook = master_notebook

        # Create scale trader tab
        self.scale_trader_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.scale_trader_tab, text="  Scale Trader  ")

        # Method to create scale trader tab GUI components
        self.create_scale_trader_tab()

    # Method to create GUI for scale trader tab
    def create_scale_trader_tab(self):
        # Get frame for button to delete multiple scale trader instances
        delete_scale_trader_instances_button_frame = ttk.Frame(
            self.scale_trader_tab, padding=10
        )
        delete_scale_trader_instances_button_frame.pack(pady=10)

        # Initialize button to delete multiple scale trader instances
        delete_scale_trader_instances_button = ttk.Button(
            delete_scale_trader_instances_button_frame,
            text="Delete Scale Trades",
            command=lambda: self.delete_scale_trader_instances(
                delete_scale_trader_instances_button
            ),
        )

        # Place create scale trader button
        delete_scale_trader_instances_button.pack(side=TOP)

        # Place in center
        delete_scale_trader_instances_button_frame.place(relx=0.5, anchor=tk.N)
        delete_scale_trader_instances_button_frame.place(y=10)

        # Create Treeview Frame for scale trade instances
        scale_trader_table_frame = ttk.Frame(self.scale_trader_tab, padding=10)
        scale_trader_table_frame.pack(pady=10, side=BOTTOM)

        # Place in center
        scale_trader_table_frame.place(relx=0.5, anchor=tk.N, width=1600, y=50)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(scale_trader_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Treeview Scrollbar
        tree_scroll_x = Scrollbar(scale_trader_table_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        # Create Treeview Table
        self.scale_trader_table = ttk.Treeview(
            scale_trader_table_frame,
            yscrollcommand=tree_scroll.set,
            xscrollcommand=tree_scroll_x.set,
            height=26,
            selectmode="extended",
        )

        # Pack to the screen
        self.scale_trader_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.scale_trader_table.yview)

        # Configure the scrollbar
        tree_scroll_x.config(command=self.scale_trader_table.xview)

        # Get columns for scale trader table
        scale_trader_table_columns = copy.deepcopy(variables.scale_trader_table_columns)

        # Set columns for scale trader table
        self.scale_trader_table["columns"] = scale_trader_table_columns

        # Creating Column
        self.scale_trader_table.column("#0", width=0, stretch="no")

        # Creating columns for scale trader table
        for (
            column_name,
            column_heading,
        ) in variables.scale_trader_table_columns_name_heading:
            self.scale_trader_table.column(column_name, anchor="center", width=112)

        # Create Heading
        self.scale_trader_table.heading("#0", text="\n", anchor="w")

        # Create headings for scale trader table
        for (
            column_name,
            column_heading,
        ) in variables.scale_trader_table_columns_name_heading:
            self.scale_trader_table.heading(
                column_name, text=column_heading, anchor="center"
            )

        # Back ground for rows in table
        self.scale_trader_table.tag_configure("oddrow", background="white")
        self.scale_trader_table.tag_configure("evenrow", background="lightblue")

        # Set right click options for selected row in table
        self.scale_trader_table.bind("<Button-3>", self.scale_trader_table_right_click)

    # Method to set up right click option for table rows
    def scale_trader_table_right_click(self, event):
        try:
            # Get the treeview table row that was clicked
            row = self.scale_trader_table.identify_row(event.y)

            if row:
                # select the row
                self.scale_trader_table.selection_set(row)

                # create a context menu
                menu = tk.Menu(self.scale_trader_table, tearoff=0)
                menu.add_command(
                    label="Pause", command=lambda: self.pause_scale_trade()
                )
                menu.add_command(
                    label="Resume", command=lambda: self.resume_scale_trade()
                )
                menu.add_command(
                    label="Terminate", command=lambda: self.terminate_scale_trade()
                )

                # display the context menu at the location of the mouse cursor
                menu.post(event.x_root, event.y_root)
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Excpetion inside 'scale_trader_table_right_click', Exp: {e}")

    # Method to delete multiple scale trades
    def delete_scale_trader_instances(
        self, delete_scale_trader_instances_button, selected_items=None
    ):
        try:
            # Get values of selected rows
            selected_items = self.scale_trader_table.selection()

            # Disable the button
            delete_scale_trader_instances_button.config(state="disabled")

            # Delete all selected ladders
            for ladder_id in selected_items:
                try:
                    # Delete ladder function for each ladder to be deleted
                    self.delete_ladder(ladder_id)

                except Exception as e:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(f"Error in deleting multiple ladders: {e}")

            delete_scale_trader_instances_button.config(state="normal")
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Excpetion inside 'delete_scale_trader_instances', Exp: {e}")

    # Method to remove ladder id from system
    def delete_ladder(self, ladder_id):
        try:
            # get the values of the selected row
            values = self.scale_trader_table.item(ladder_id, "values")

            # Get value of status
            status = values[15]

            # Check if ladder is terminated
            if status in ["Terminated", "Completed"]:
                # move to be deleted ladders and sequence to archive
                move_deleted_ladder_and_sequence_to_archive(ladder_id)

                # Delete sequence db table rows
                delete_row_from_ladder_or_sequence_table_db_for_ladder_id(
                    ladder_id=ladder_id, flag_delete_sequences=True
                )

                # Delete ladder db table row
                delete_row_from_ladder_or_sequence_table_db_for_ladder_id(
                    ladder_id=ladder_id
                )

                # Remove rows where ladder id is located
                variables.scale_trade_table_dataframe = (
                    variables.scale_trade_table_dataframe[
                        variables.scale_trade_table_dataframe["Ladder ID"]
                        != int(float(ladder_id))
                    ]
                )

                # Update
                del variables.map_ladder_id_to_ladder_obj[int(float(ladder_id))]

                # Update scale trade GUI table
                self.update_scale_trader_table()

            else:
                # Show error pop up
                error_title = (
                    "Error, Only terminated and completed ladder can be deleted."
                )
                error_string = (
                    f"Error, Only terminated and completed ladder can be deleted"
                )
                variables.screen.display_error_popup(error_title, error_string)

        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Excpetion inside 'delete_ladder', Exp: {e}")

    # Terminate all scale trade for unique id
    def terminate_all_scale_trade_for_unique_id(self, unique_id):
        try:
            # Get all ladder ids for uniqque id
            ladder_ids_in_unique_id = variables.map_unique_id_to_ladder_ids_list[
                unique_id
            ]

            # For each ladder, terminate ladder and delete it
            for ladder_id in ladder_ids_in_unique_id:
                self.terminate_scale_trade(str(ladder_id))

                self.delete_ladder(ladder_id)
        except Exception as e:
            if variables.flag_debug_mode:
                print(
                    f"Excpetion inside 'terminate_all_scale_trade_for_unique_id', Exp: {e}"
                )

    # Method to make scale trade completed
    def mark_scale_trade_as_completed(self, selected_item=None):
        try:
            # Check if selected item is None
            if selected_item == None:
                # get Ladder ID of selected row
                selected_item = self.scale_trader_table.selection()[
                    0
                ]  # get the item ID of the selected row

            values = self.scale_trader_table.item(
                selected_item, "values"
            )  # get the values of the selected row

            # Get value of status
            status = values[15]

            # Get ladder id
            ladder_id = values[0]

            # Update ladder status
            self.update_ladder_status(ladder_id, "Completed")
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Excpetion inside 'mark_scale_trade_as_completed', Exp: {e}")

    # Method to pause scale trade
    def pause_scale_trade(self, selected_item=None):
        try:
            # Check if selected item is None
            if selected_item == None:
                # get Ladder ID of selected row
                selected_item = self.scale_trader_table.selection()[
                    0
                ]  # get the item ID of the selected row

            values = self.scale_trader_table.item(
                selected_item, "values"
            )  # get the values of the selected row

            # Get value of status
            status = values[15]

            # Check if ladder has active or terminated status
            if status in ["Paused", "Terminated", "Completed"]:
                return

            # Get ladder id
            ladder_id = values[0]

            # Cancel orders of ladder id
            cancel_orders_of_ladder_id_or_sequence_id(ladder_id=ladder_id)

            # Update ladder status
            self.update_ladder_status(ladder_id, "Paused")
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Excpetion inside 'pause_scale_trade', Exp: {e}")

    # Method to terminate scale trade
    def terminate_scale_trade(self, selected_item=None):
        try:
            # Check if selected item is None
            if selected_item == None:
                # get Ladder ID of selected row
                selected_item = self.scale_trader_table.selection()[
                    0
                ]  # get the item ID of the selected row

            values = self.scale_trader_table.item(
                selected_item, "values"
            )  # get the values of the selected row

            # Get value of status
            status = values[15]

            # Check if ladder has active or terminated status
            if status in ["Terminated", "Completed"]:
                return

            # Get ladder id
            ladder_id = values[0]

            # Cancel orders of ladder id
            cancel_orders_of_ladder_id_or_sequence_id(ladder_id=ladder_id)

            # Update ladder status
            self.update_ladder_status(ladder_id, "Terminated")
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Exception inside 'terminate_scale_trade', Exp: {e}")

    # Method to resume sclae trade instance
    def resume_scale_trade(self, selected_item=None):
        try:
            # Check if selected item is None
            if selected_item == None:
                # get Ladder ID of selected row
                selected_item = self.scale_trader_table.selection()[
                    0
                ]  # get the item ID of the selected row

            values = self.scale_trader_table.item(
                selected_item, "values"
            )  # get the values of the selected row

            # Get value of status
            status = values[15]

            # Check if ladder has active or terminated status
            if status in ["Active", "Terminated", "Completed"]:
                return

            # Get ladder id
            ladder_id = int(values[0])

            # Unique ID
            unique_id = int(values[1])

            # Get ladder obj
            ladder_obj = copy.deepcopy(variables.map_ladder_id_to_ladder_obj[ladder_id])

            # Get local copy for orders book table dataframe
            local_orders_book_table_dataframe = get_primary_vars_db(
                variables.sql_table_combination_status
            )

            # If dataframe is empty
            if local_orders_book_table_dataframe.empty:
                # Then initialize with columns
                local_orders_book_table_dataframe = pd.DataFrame(
                    columns=variables.order_book_table_columns
                )

            # Get active entry sequence
            index_of_active_entry_sequence = self.get_active_sequence(
                ladder_obj.entry_sequences
            )

            # Get account id for ladder
            ladder_account_id = get_ladder_or_sequence_column_value_from_db(
                ladder_id=ladder_id, column_name_as_in_db="Account ID"
            )

            # Get bypass rm check for ladder
            bypass_rm_check = get_ladder_or_sequence_column_value_from_db(
                ladder_id=ladder_id, column_name_as_in_db="Bypass RM Check"
            )

            # Get execution engine value for ladder
            flag_use_execution_engine = get_ladder_or_sequence_column_value_from_db(
                ladder_id=ladder_id, column_name_as_in_db="Execution Engine"
            )

            # set boolean value for flag for execution engine
            if flag_use_execution_engine == "True":
                flag_use_execution_engine = True

            else:
                flag_use_execution_engine = False

            # check if unique id is in current session accounts
            if ladder_account_id not in variables.current_session_accounts:
                # Error pop up
                error_title = "Account ID is unavailable in current session."
                error_string = "Can not trade combo because Account ID \nis unavailable in current session."

                variables.screen.display_error_popup(error_title, error_string)

                return

            def rm_check_resume_for_scale_trade():
                # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
                if (
                    bypass_rm_check == "False"
                    and variables.flag_enable_rm_account_rules
                    and variables.flag_account_liquidation_mode[ladder_account_id]
                ):
                    time.sleep(variables.rm_checks_interval_if_failed)

                    # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
                    if (
                        bypass_rm_check == "False"
                        and variables.flag_enable_rm_account_rules
                        and variables.flag_account_liquidation_mode[ladder_account_id]
                    ):
                        # Error pop up
                        error_title = f"For Account ID: {ladder_account_id}, Scale Trade cannot be active, \naccount is in liquidation mode"
                        error_string = f"For Account ID: {ladder_account_id}, Scale Trade cannot be active, \naccount is in liquidation mode"

                        variables.screen.display_error_popup(error_title, error_string)
                        return

                if not trade_level_rm_check_result(bypass_rm_check, unique_id):
                    time.sleep(variables.rm_checks_interval_if_failed)

                    if not trade_level_rm_check_result(bypass_rm_check, unique_id):
                        # get details of which check in trade rm check failed
                        failed_trade_checks_details = (
                            get_failed_checks_string_for_trade_rm_check(unique_id)
                        )

                        # Error pop up
                        error_title = f"For Account ID: {ladder_account_id}, Scale Trade cannot be active, \nTrade Level RM Check Failed"
                        error_string = f"For Account ID: {ladder_account_id}, Scale Trade cannot be active, \nTrade Level RM Check Failed :\n {failed_trade_checks_details}"

                        variables.screen.display_error_popup(error_title, error_string)
                        return

                # Sending Entry Sequence Order, with status as Active
                # Check if index of sequence to activate is not None
                if index_of_active_entry_sequence != None:
                    # Get object of active entry sequence
                    entry_sequence_object = ladder_obj.entry_sequences[
                        index_of_active_entry_sequence
                    ]

                    # Sequence id for sequence obj
                    entry_sequence_id = str(entry_sequence_object.sequence_id)

                    # Get status value
                    status_values = local_orders_book_table_dataframe.loc[
                        local_orders_book_table_dataframe["Sequence ID"]
                        == entry_sequence_id,
                        "Status",
                    ].values

                    # Check if sequence has sent or filled order
                    if not ("Sent" in status_values or "Filled" in status_values):
                        # Place order for active sequence
                        self.place_order_for_sequence(
                            entry_sequence_object,
                            "Entry",
                            ladder_obj,
                            ladder_id,
                            unique_id,
                            ladder_account_id,
                            bypass_rm_check,
                            flag_use_execution_engine,
                        )

                        # Provide time sleep
                        time.sleep(0.5)

                # Get exit sequence that must be activate
                index_of_exit_sequence_to_activate = self.get_active_sequence(
                    ladder_obj.exit_sequences
                )

                # Check if index of sequence to activate is not None
                if index_of_exit_sequence_to_activate != None:
                    # Get object of active exit sequence
                    exit_sequence_object = ladder_obj.exit_sequences[
                        index_of_exit_sequence_to_activate
                    ]

                    # Sequence id for sequence obj
                    exit_sequence_id = str(exit_sequence_object.sequence_id)

                    # Get status value
                    status_values = local_orders_book_table_dataframe.loc[
                        local_orders_book_table_dataframe["Sequence ID"]
                        == exit_sequence_id,
                        "Status",
                    ].values

                    # Check if sequence has sent or filled order
                    if (
                        not ("Sent" in status_values or "Filled" in status_values)
                        or local_orders_book_table_dataframe.empty
                    ):
                        # Place order for active sequence
                        self.place_order_for_sequence(
                            exit_sequence_object,
                            "Exit",
                            ladder_obj,
                            ladder_id,
                            unique_id,
                            ladder_account_id,
                            bypass_rm_check,
                            flag_use_execution_engine,
                        )

                        # Provide time sleep
                        time.sleep(0.5)

                # Update ladder status
                self.update_ladder_status(ladder_id, "Active")

            # Send order in a separate thread
            rm_check_thread = threading.Thread(
                target=rm_check_resume_for_scale_trade,
                args=(),
            )
            rm_check_thread.start()
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Exception inside 'resume_scale_trade', Exp: {e}")

    # Method to place order for scale trader
    def place_order_for_sequence(
        self,
        active_sequence_obj,
        sequence_type,
        ladder_obj,
        ladder_id,
        unique_id,
        account_id,
        bypass_rm_check,
        execution_engine=False,
    ):
        try:
            # Check if index of active sequence is not None
            if active_sequence_obj != None and sequence_type == "Entry":
                # Values of sequence to activate
                attribute_values_of_sequences_obj = (
                    active_sequence_obj.get_list_of_sequence_values()
                )

            # Check if index of active sequence is not None
            if active_sequence_obj != None and sequence_type == "Exit":
                # Values of sequence to activate
                attribute_values_of_sequences_obj = (
                    active_sequence_obj.get_list_of_sequence_values()
                )

            # Get values to place order
            [
                action,
                order_type,
                combo_quantity,
                limit_price,
            ] = attribute_values_of_sequences_obj[3:7]

            # Get sequence id
            sequence_id = attribute_values_of_sequences_obj[0]

            # Send order in a separate thread
            send_order_thread = threading.Thread(
                target=send_order,
                args=(
                    unique_id,
                    action,
                    "Limit",
                    combo_quantity,
                    limit_price,
                    "None",
                    "None",
                ),
                kwargs={
                    "ladder_id": ladder_id,
                    "sequence_id": sequence_id,
                    "account_id": account_id,
                    "bypass_rm_check": bypass_rm_check,
                    "execution_engine": execution_engine,
                },
            )
            send_order_thread.start()

        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Exception inside 'place_order_for_sequence', Exp: {e}")

    # Method to update status of ladder
    def update_ladder_status(self, ladder_id, status):
        try:
            # Get ladder id in intger format
            ladder_id = int(float(ladder_id))

            # change status of ladder obj to Active
            variables.map_ladder_id_to_ladder_obj[ladder_id].status = status

            # Dict of values to update in ladder db table
            ladder_values_to_update_dict = {"Status": status}

            # Update status of ladder instance in db
            update_ladder_table_values(ladder_id, ladder_values_to_update_dict)

            # Change the value of the 'status' column where 'ladder id' is selected to resume
            variables.scale_trade_table_dataframe.loc[
                variables.scale_trade_table_dataframe["Ladder ID"] == ladder_id,
                "Status",
            ] = status

            # Update GUI table
            self.update_scale_trader_table()

        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Exception inside 'update_ladder_status', Exp: {e}")

    # Method to choose sequence to activate
    def get_active_sequence(self, ladder_sequences):
        try:
            # Iterate sequence objects
            for indx, sequence in enumerate(ladder_sequences):
                # Get values for attributes of sequence object
                sequence_obj_values = sequence.get_list_of_sequence_values()

                # Get status of sequence
                status_of_sequence = sequence_obj_values[11]

                # Check which sequence is active and return it
                if status_of_sequence == "Active":
                    return indx
            else:
                # No entry sequence is active [indicating all must have filled]
                return None

        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Exception inside 'get_active_sequence', Exp: {e}")

            return None

    # Method to get highest and lowest price for range orders
    def get_range_order_data(self, unique_id, flag_range=False, flag_hide_pop_up=False):
        if not flag_hide_pop_up:
            # set text to display
            if flag_range:
                msg_text = "Range Orders is Waiting for Historical Data"

            else:
                msg_text = "Range Schedule Orders is Waiting for Historical Data"

            # Create a waiting popup window
            waiting_pop_up = tk.Toplevel()
            waiting_pop_up.title("Waiting For Historical Data")

            waiting_pop_up.geometry("400x100")

            # Create a frame for the input fields
            waiting_frame = ttk.Frame(waiting_pop_up, padding=20)
            waiting_frame.pack(fill="both", expand=True)

            # Add labels and entry fields for each column in the table
            waiting_label = ttk.Label(
                waiting_frame, text=msg_text, width=80, anchor="center"
            )
            waiting_label.place(relx=0.5, rely=0.5, anchor="center")

        lookback_days = 0
        candle_size = 0

        # check for lookback days flag
        if variables.flag_range_order == "Intraday":
            lookback_days = 1
            candle_size = CandleSize.ONE_MIN

        elif variables.flag_range_order == "Week":
            lookback_days = 5
            candle_size = CandleSize.ONE_HOUR

        else:
            lookback_days = 22
            candle_size = CandleSize.ONE_HOUR

        # local copy of 'unique_id_to_combo_obj'
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

        local_map_unique_id_to_price_and_volume_based_indicators = {}

        # Init
        duration_size = f"{lookback_days} D"
        bar_size = candle_size.value

        # Create a local copy of 'cas_map_con_id_to_action_type_and_combo_type'
        cas_coinds_for_fetching_historical_data = copy.deepcopy(
            variables.cas_map_con_id_to_action_type_and_combo_type
        )

        # get comob obj
        combination_obj = local_unique_id_to_combo_obj[unique_id]

        # Buy legs and Sell legs
        buy_legs = combination_obj.buy_legs
        sell_legs = combination_obj.sell_legs
        all_legs = buy_legs + sell_legs

        conid_list = [leg_obj.con_id for leg_obj in all_legs]

        if conid_list != None:
            # Create a filtered dictionary using a dictionary comprehension
            cas_coinds_for_fetching_historical_data = {
                key: cas_coinds_for_fetching_historical_data[key] for key in conid_list
            }

            # local copy of 'unique_id_to_combo_obj'
            local_unique_id_to_combo_obj = {
                unique_id: local_unique_id_to_combo_obj[unique_id]
            }

        # Requesting historical data and getting reqid  (ask, bid)
        map_conid_action_bar_size_to_req_id = (
            get_historical_data_for_price_based_relative_indicators(
                cas_coinds_for_fetching_historical_data, duration_size, bar_size
            )
        )

        # Computing all the price based relative indicators
        dict = calculate_prices_for_range_order(
            local_unique_id_to_combo_obj, map_conid_action_bar_size_to_req_id
        )

        try:
            # get price for UID
            range_prices_dict = dict[unique_id]

        except:
            range_prices_dict = "None"

        if not flag_hide_pop_up:
            # destroy pop up
            waiting_pop_up.destroy()

        return range_prices_dict

    # Method to get inputs for range order
    def get_range_order_prior_input(self, unique_id, flag_multi=False):
        # Init
        range_prices_dict = "None"

        # Start the web socket in a thread
        range_prices_dict = self.get_range_order_data(unique_id, flag_range=True)

        try:
            # get highest and lowest price
            highest_price_val = range_prices_dict["Highest Price"]
            lowest_price_val = range_prices_dict["Lowest Price"]

            # convert prices to float
            highest_price_val = round(float(highest_price_val), 2)

            lowest_price_val = round(float(lowest_price_val), 2)

        except:
            highest_price_val = "None"
            lowest_price_val = "None"

        # Create popup window
        percentage_qnty_pair_popup = tk.Toplevel()

        # set title
        percentage_qnty_pair_popup.title(f"Range Order, Unique ID: {unique_id}")

        if not flag_multi:
            custom_height = 250

        else:
            custom_height = 270

        # set dimensions
        percentage_qnty_pair_popup.geometry("330x" + str(custom_height))

        # enter_legs_popup.geometry("450x520")

        # Create main frame
        percentage_qnty_pair_popup_frame = ttk.Frame(
            percentage_qnty_pair_popup, padding=20
        )
        percentage_qnty_pair_popup_frame.pack(fill="both", expand=True)

        # Create a frame for the input fields
        percentage_qnty_pair_frame = ttk.Frame(
            percentage_qnty_pair_popup_frame, padding=0
        )
        percentage_qnty_pair_frame.pack(side=TOP)

        # Create a frame for the input fields
        percentage_qnty_pair_button_frame = ttk.Frame(
            percentage_qnty_pair_popup_frame, padding=0
        )
        percentage_qnty_pair_button_frame.pack(side=BOTTOM)

        # Create a frame for the input fields
        percentage_qnty_pair_table_frame = ttk.Frame(
            percentage_qnty_pair_popup_frame, padding=0
        )
        percentage_qnty_pair_table_frame.pack(side=TOP)

        # Create a frame for the input fields
        add_percentage_qnty_pair_button_frame = ttk.Frame(
            percentage_qnty_pair_button_frame, padding=0
        )
        add_percentage_qnty_pair_button_frame.pack(side=BOTTOM)

        # Add a label
        ttk.Label(percentage_qnty_pair_frame, text="Highest Price").grid(
            column=0, row=0, padx=5, pady=5
        )

        # Add a label
        ttk.Label(percentage_qnty_pair_frame, text="Lowest Price").grid(
            column=1, row=0, padx=5, pady=5
        )

        if not flag_multi:
            # Add a label
            ttk.Label(percentage_qnty_pair_frame, text="Total Quantity").grid(
                column=0, row=2, padx=5, pady=5
            )

        else:
            # Add a label
            ttk.Label(
                percentage_qnty_pair_frame,
                text=f"Total Quantity\n(x % * {variables.account_parameter_for_order_quantity}) / Price",
            ).grid(column=0, row=2, padx=5, pady=5)

        # Add a label
        ttk.Label(percentage_qnty_pair_frame, text="Number of Buckets").grid(
            column=1, row=2, padx=5, pady=5
        )

        # Add a label
        ttk.Label(percentage_qnty_pair_frame, text="Action").grid(
            column=0, row=4, padx=5, pady=5
        )

        # Add a label
        ttk.Label(percentage_qnty_pair_frame, text="Price Movement").grid(
            column=1, row=4, padx=5, pady=5
        )

        # Entry to unique id
        highest_price = ttk.Entry(percentage_qnty_pair_frame)
        highest_price.grid(column=0, row=1, padx=5, pady=5, sticky="n")
        highest_price.insert(0, highest_price_val)
        highest_price.config(state="readonly")

        # Entry to evaluation unique id
        lowest_price = ttk.Entry(percentage_qnty_pair_frame)
        lowest_price.grid(column=1, row=1, padx=5, pady=5)
        lowest_price.insert(0, lowest_price_val)
        lowest_price.config(state="readonly")

        # Entry to unique id
        percnt_entry = ttk.Entry(percentage_qnty_pair_frame)
        percnt_entry.grid(column=0, row=3, padx=5, pady=(5, 5), sticky="n")

        # Entry to evaluation unique id
        lots_entry = ttk.Entry(percentage_qnty_pair_frame)
        lots_entry.grid(column=1, row=3, padx=5, pady=(5, 5))

        # Values to be included in acton drop down
        action_type_options = ["BUY", "SELL"]

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

        # Intialize and place drop down for action input field
        action_combo_box = ttk.Combobox(
            percentage_qnty_pair_frame,
            width=18,
            values=action_type_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        action_combo_box.current(0)
        action_combo_box.grid(column=0, row=5, padx=5, pady=5)

        # Values to be included in price movement drop down
        price_movement_options = ["Better", "Worse"]

        # Intialize and place drop down for price movement input field
        price_movement_combo_box = ttk.Combobox(
            percentage_qnty_pair_frame,
            width=18,
            values=price_movement_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        price_movement_combo_box.current(0)
        price_movement_combo_box.grid(column=1, row=5, padx=5, pady=5)

        # Text we want to show for the button
        add_pair_button_text = "Proceed"

        # Create the "Add pair " button
        add_pair_button = ttk.Button(
            percentage_qnty_pair_frame,
            text=add_pair_button_text,
            command=lambda: proceed(),
        )
        add_pair_button.grid(row=6, column=0, pady=(15, 10), columnspan=2)

        # Create a custom style for the Combobox widget
        custom_style = ttk.Style()
        custom_style.map(
            "Custom.TCombobox",
            fieldbackground=[
                ("readonly", "white"),
                ("!disabled", "white"),
                ("disabled", "lightgray"),
            ],
            foreground=[("disabled", "black")],
        )

        def proceed():
            total_quantity = percnt_entry.get().strip()

            number_of_buckets = lots_entry.get().strip()

            # check if ap have valid highest price and lowest price values
            if not is_float(highest_price_val) or not is_float(lowest_price_val):
                variables.screen.display_error_popup(
                    "Highest or lowest price not available",
                    "Highest or lowest price not available",
                )
                return

            # check if ap have valid highest price and lowest price values
            if total_quantity in [""]:
                variables.screen.display_error_popup(
                    "Total quantity should be present",
                    "Total quantity should be present",
                )
                return

            # check if ap have valid highest price and lowest price values
            if number_of_buckets in [""]:
                variables.screen.display_error_popup(
                    "Number of buckets should be present",
                    "Number of buckets should be present",
                )
                return

            # check if ap have valid highest price and lowest price values
            if not flag_multi and not total_quantity.isnumeric():
                variables.screen.display_error_popup(
                    "Total quantity should be numeric number",
                    "Total quantity should be numeric number",
                )
                return

            # check if ap have valid highest price and lowest price values
            elif flag_multi and not is_float(total_quantity):
                variables.screen.display_error_popup(
                    "Total quantity should be decimal number",
                    "Total quantity should be decimal number",
                )
                return

            # check if ap have valid highest price and lowest price values
            if not number_of_buckets.isnumeric():
                variables.screen.display_error_popup(
                    "Number of buckets should be numeric number",
                    "Number of buckets should be numeric number",
                )
                return

            if not flag_multi and int(total_quantity) < 2:
                variables.screen.display_error_popup(
                    "Total quantity should be at least 2",
                    "Total quantity should be at least 2",
                )
                return
            elif flag_multi and float(total_quantity) <= 0:
                variables.screen.display_error_popup(
                    "Total quantity should be greater than 0",
                    "Total quantity should be reater than 0",
                )
                return

            if int(number_of_buckets) < 2:
                variables.screen.display_error_popup(
                    "Number of Buckets should be at least 2",
                    "Number of Buckets should be at least 2",
                )
                return

            action = action_combo_box.get().strip()

            price_movement = price_movement_combo_box.get().strip()

            # columns list

            schedule_data = {
                "Highest Price": highest_price_val,
                "Lowest Price": lowest_price_val,
                "Total Quantity": float(total_quantity),
                "Number of Buckets": int(number_of_buckets),
                "Action": action,
                "Price Movement": price_movement,
            }

            percentage_qnty_pair_popup.destroy()

            # open scale trade iput pop up
            self.add_scale_trade_instance_pop_up(
                unique_id,
                flag_multi=flag_multi,
                range_data=schedule_data,
                flag_range=True,
            )

    # Method to add range chedule order inputs
    def get_percentage_qnty_pair(self, unique_id, flag_multi=False):
        # Init
        range_prices_dict = "None"

        # Start the web socket in a thread
        range_prices_dict = self.get_range_order_data(
            unique_id,
        )

        try:
            # get highest and lowest price
            highest_price_val = range_prices_dict["Highest Price"]
            lowest_price_val = range_prices_dict["Lowest Price"]

            # convert prices to float
            highest_price_val = float(highest_price_val)

            lowest_price_val = float(lowest_price_val)

        except:
            highest_price_val = "None"
            lowest_price_val = "None"

        # Create popup window
        percentage_qnty_pair_popup = tk.Toplevel()

        # set title
        percentage_qnty_pair_popup.title(
            f"Percentage - Quantity Pair, Unique ID: {unique_id}"
        )

        custom_height = 550

        # set dimensions
        percentage_qnty_pair_popup.geometry("330x" + str(custom_height))

        # enter_legs_popup.geometry("450x520")

        # Create main frame
        percentage_qnty_pair_popup_frame = ttk.Frame(
            percentage_qnty_pair_popup, padding=20
        )
        percentage_qnty_pair_popup_frame.pack(fill="both", expand=True)

        # Create a frame for the input fields
        percentage_qnty_pair_frame = ttk.Frame(
            percentage_qnty_pair_popup_frame, padding=0
        )
        percentage_qnty_pair_frame.pack(side=TOP)

        # Create a frame for the input fields
        percentage_qnty_pair_button_frame = ttk.Frame(
            percentage_qnty_pair_popup_frame, padding=0
        )
        percentage_qnty_pair_button_frame.pack(side=BOTTOM)

        # Create a frame for the input fields
        percentage_qnty_pair_table_frame = ttk.Frame(
            percentage_qnty_pair_popup_frame, padding=0
        )
        percentage_qnty_pair_table_frame.pack(side=TOP)

        # Create a frame for the input fields
        add_percentage_qnty_pair_button_frame = ttk.Frame(
            percentage_qnty_pair_button_frame, padding=0
        )
        add_percentage_qnty_pair_button_frame.pack(side=BOTTOM)

        # Add a label
        ttk.Label(percentage_qnty_pair_frame, text="Highest Price").grid(
            column=0, row=0, padx=5, pady=5
        )

        # Add a label
        ttk.Label(percentage_qnty_pair_frame, text="Lowest Price").grid(
            column=1, row=0, padx=5, pady=5
        )

        # Add a label
        ttk.Label(percentage_qnty_pair_frame, text="Percentage(%)").grid(
            column=0, row=2, padx=5, pady=5
        )

        # Add a label
        ttk.Label(percentage_qnty_pair_frame, text="#Lots").grid(
            column=1, row=2, padx=5, pady=5
        )

        # Entry to unique id
        highest_price = ttk.Entry(percentage_qnty_pair_frame)
        highest_price.grid(column=0, row=1, padx=5, pady=5, sticky="n")
        highest_price.insert(0, highest_price_val)
        highest_price.config(state="readonly")

        # Entry to evaluation unique id
        lowest_price = ttk.Entry(percentage_qnty_pair_frame)
        lowest_price.grid(column=1, row=1, padx=5, pady=5)
        lowest_price.insert(0, lowest_price_val)
        lowest_price.config(state="readonly")

        # Entry to unique id
        percnt_entry = ttk.Entry(percentage_qnty_pair_frame)
        percnt_entry.grid(column=0, row=3, padx=5, pady=(5, 15), sticky="n")

        # Entry to evaluation unique id
        lots_entry = ttk.Entry(percentage_qnty_pair_frame)
        lots_entry.grid(column=1, row=3, padx=5, pady=(5, 15))

        # Text we want to show for the button
        add_pair_button_text = "Add Scale Trade"

        def add_pair():
            # get values of input
            prcnt_val = percnt_entry.get().strip()

            qnty_val = lots_entry.get().strip()

            table_ids = pair_table.get_children()

            table_ids = [float(item) for item in table_ids]

            # check if float price is valid
            if not is_float(prcnt_val):
                variables.screen.display_error_popup(
                    "Percent value should be decimal number",
                    "Percent value should be decimal number",
                )

                return

            # check if quanitity is valid
            if not qnty_val.isnumeric():
                variables.screen.display_error_popup(
                    "Quantity value should be numeric",
                    "Quantity value should be numeric",
                )

                return

            if int(qnty_val) < 1:
                variables.screen.display_error_popup(
                    "Quantity value should be at least 1",
                    "Quantity value should be at least 1",
                )

                return

            prcnt_val = round(float(prcnt_val), 2)

            if prcnt_val in table_ids:
                variables.screen.display_error_popup(
                    "Percent value already present in table",
                    "Percent value already present in table",
                )
                return

            # insert rows in table
            if len(table_ids) % 2 == 1:
                pair_table.insert(
                    "",
                    "end",
                    iid=prcnt_val,
                    values=(prcnt_val, qnty_val),
                    tags=("oddrow",),
                )
            else:
                pair_table.insert(
                    "",
                    "end",
                    iid=prcnt_val,
                    values=(prcnt_val, qnty_val),
                    tags=("evenrow",),
                )

        # Create the "Add pair " button
        add_pair_button = ttk.Button(
            percentage_qnty_pair_frame,
            text=add_pair_button_text,
            command=lambda: add_pair(),
        )
        add_pair_button.grid(row=4, column=0, pady=(0, 15), columnspan=2)

        # Create a custom style for the Combobox widget
        custom_style = ttk.Style()
        custom_style.map(
            "Custom.TCombobox",
            fieldbackground=[
                ("readonly", "white"),
                ("!disabled", "white"),
                ("disabled", "lightgray"),
            ],
            foreground=[("disabled", "black")],
        )

        # Treeview Scrollbar
        tree_scroll = Scrollbar(percentage_qnty_pair_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview Table
        pair_table = ttk.Treeview(
            percentage_qnty_pair_table_frame,
            yscrollcommand=tree_scroll.set,
            height=11,
            selectmode="extended",
        )

        # Pack to the screen
        pair_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=pair_table.yview)

        # Get columns for series sequence table
        pair_table_columns = ["Percentage(%)", "#Lots"]

        # Set columns for series sequence table
        pair_table["columns"] = pair_table_columns

        # Creating Column
        pair_table.column("#0", width=0, stretch="no")

        # Creating columns for filter table
        for column_name in pair_table_columns:
            pair_table.column(column_name, anchor="center", width=120)

        # Create Heading
        pair_table.heading("#0", text="", anchor="w")

        # Create headings for filter table
        for column_name in pair_table_columns:
            pair_table.heading(column_name, text=column_name, anchor="center")

        # Back ground for rows in table
        pair_table.tag_configure("oddrow", background="white")
        pair_table.tag_configure("evenrow", background="lightblue")

        def proceed():
            # get all talb eids in table
            table_ids = pair_table.get_children()

            # check if there are minimum two rows
            if len(table_ids) < 2:
                variables.screen.display_error_popup(
                    "Table should have minimum 2 rows",
                    "Table should have minimum 2 rows",
                )
                return

            # check if ap have valid highest price and lowest price values
            if not is_float(highest_price_val) or not is_float(lowest_price_val):
                variables.screen.display_error_popup(
                    "Highest or lowest price not available",
                    "Highest or lowest price not available",
                )
                return

            # columns list
            columns = ["Percentage", "#Lots"]
            data = []

            # making data for dataframe ready
            for row_id in pair_table.get_children():
                values = [
                    pair_table.item(row_id)["values"][col]
                    for col in range(len(columns))
                ]
                data.append(values)

            # Create a Pandas DataFrame
            df = pd.DataFrame(data, columns=columns)

            # convert column to int
            df["Percentage"] = df["Percentage"].astype(float)

            # conevert lots to integer
            df["#Lots"] = df["#Lots"].astype(int)

            # Calculate price based on percentage
            df["Price"] = lowest_price_val + (
                df["Percentage"] * (highest_price_val - lowest_price_val) / 100
            )

            # init
            schedule_data = {}

            # assign value to dictionary
            schedule_data["Highest Price"] = highest_price_val

            schedule_data["Lowest Price"] = lowest_price_val

            schedule_data["Percentage Lots Pair"] = df

            # destroy pop up
            percentage_qnty_pair_popup.destroy()
            print(df)

            # open scale trade iput pop up
            self.add_scale_trade_instance_pop_up(
                unique_id, flag_multi=flag_multi, schedule_data=schedule_data
            )

        # Create the "Add pair " button
        proceed_button = ttk.Button(
            percentage_qnty_pair_popup_frame,
            text="Proceed",
            command=lambda: proceed(),
        )
        proceed_button.pack(side=BOTTOM)

        # method to delte row in table
        def delete_row_pair_table():
            try:
                # get values from selected rows
                selected_item = pair_table.selection()[0]

            except Exception as e:
                return

            # delte from table
            pair_table.delete(selected_item)

            # get table ids
            table_ids = pair_table.get_children()

            counter = 0

            # reformat rows in table
            for table_id in table_ids:
                if counter % 2 == 0:
                    pair_table.item(table_id, tags="evenrow")

                else:
                    pair_table.item(table_id, tags="oddrow")

                counter += 1

        def pair_table_right_click(event):
            try:
                # Get the treeview table row that was clicked
                row = pair_table.identify_row(event.y)

                if row:
                    # select the row
                    pair_table.selection_set(row)

                    # create a context menu
                    menu = tk.Menu(pair_table, tearoff=0)
                    menu.add_command(
                        label="Delete", command=lambda: delete_row_pair_table()
                    )

                    # display the context menu at the location of the mouse cursor
                    menu.post(event.x_root, event.y_root)
            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Excpetion inside 'pair_table_right_click', Exp: {e}")

        # Set right click options for selected row in table
        pair_table.bind("<Button-3>", pair_table_right_click)

    # Pop up to add scale trader instance
    def add_scale_trade_instance_pop_up(
        self,
        unique_id,
        flag_multi=None,
        flag_range=False,
        schedule_data=None,
        range_data=None,
    ):
        range_prices_dict = "None"

        # fetch data for range orders
        if flag_range:
            # Start the web socket in a thread
            range_prices_dict = range_data

        # title for pop up
        title_string = f"Add Scale Trade, Combination Unique ID: {unique_id}"

        # Create a popup window with the table
        popup = tk.Toplevel()
        popup.title(title_string)

        # Setting pop up height and width
        popup.geometry("1850x150")

        # Check if flag for multi account is True
        if flag_multi:
            # Geometry
            popup.geometry("1850x230")

        if range_data != None:
            pad_y_val = 0

            # check flag for multi account
            if not flag_multi:
                # Geometry
                popup.geometry("1850x470")

                pad_y_val = 10

            else:
                # Geometry
                popup.geometry("1850x560")

                pad_y_val = 0

        # check if range schedule data is available
        if schedule_data != None:
            pad_y_val = 0

            # check flag for multi account
            if not flag_multi:
                # Geometry
                popup.geometry("1850x470")

                pad_y_val = 10

            else:
                # Geometry
                popup.geometry("1850x560")

                pad_y_val = 0

            # Create a frame inside the popup
            frame_parent = ttk.Frame(popup)
            frame_parent.pack(fill="both", expand=True, side=BOTTOM)

            # Create a frame inside the popup
            frame = ttk.Frame(frame_parent, width=500)
            frame.pack(side=TOP, pady=(pad_y_val, 0))

            # Treeview Scrollbar
            tree_scroll = Scrollbar(frame)
            tree_scroll.pack(side="right", fill="y")

            # Create a Treeview widget inside the frame
            tree = ttk.Treeview(
                frame,
                columns=("Percentage", "#Lots", "Price"),
                yscrollcommand=tree_scroll.set,
                height=11,
                selectmode="extended",
                show="headings",
            )

            # Configure the scrollbar
            tree_scroll.config(command=tree.yview)

            # add columns in table
            tree.column("Percentage", width=200, anchor=tk.CENTER)
            tree.column("#Lots", width=200, anchor=tk.CENTER)
            tree.column("Price", width=200, anchor=tk.CENTER)

            # Define column headings
            tree.heading("Percentage", text="Percentage (%)")
            tree.heading("#Lots", text="#Lots")
            tree.heading("Price", text="Price")

            # palce table
            tree.pack(fill="both", expand=True, side=TOP)

            # Back ground for rows in table
            tree.tag_configure("oddrow", background="white")
            tree.tag_configure("evenrow", background="lightblue")

            # get df for data
            pair_df = schedule_data["Percentage Lots Pair"]

            counter = 0

            # fill table of schedule data
            for indx, row in pair_df.iterrows():
                # get table id
                table_id = row["Percentage"]

                # get tuple of values
                row = tuple(row)

                # insert rows in table
                if counter % 2 == 0:
                    tree.insert(
                        "",
                        "end",
                        iid=table_id,
                        values=row,
                        tags=("evenrow",),
                    )

                else:
                    tree.insert(
                        "",
                        "end",
                        iid=table_id,
                        values=row,
                        tags=("oddrow",),
                    )

                counter += 1
        # Create a frame for the input fields
        input_frame = ttk.Frame(popup, padding=20)
        input_frame.pack(fill="both", expand=True, side=TOP)

        # Get columns for scale trader table
        scale_trader_table_columns = copy.deepcopy(variables.scale_trader_table_columns)

        # Add labels fields for input fields in the table except for unique id
        for indx, input_field_label in enumerate(
            scale_trader_table_columns[2:13]
            + scale_trader_table_columns[16:18]
            + ["Execution Engine"],
            start=1,
        ):
            # For label of quantity input
            if input_field_label == "Total Quantity":
                # If flag for multi account is true
                if flag_multi:
                    # Set value for label
                    input_field_label = f"{input_field_label}\n( x% * {variables.account_parameter_for_order_quantity} ) / Price"

                else:
                    # Set value for label
                    input_field_label = f"{input_field_label}\n(#Lots)"

            # For label of quantity input
            elif input_field_label in ["Initial Quantity", "Subsequent Quantity"]:
                # If flag for multi account is true
                if flag_multi:
                    # Set value for label
                    input_field_label = f"{input_field_label}\n( x% * Total Qty )"

                else:
                    # Set value for label
                    input_field_label = f"{input_field_label}\n(#Lots)"

            # For label of quantity input
            elif input_field_label in ["Bypass RM Check"]:
                input_field_label = "Bypass RM Checks"

            ttk.Label(
                input_frame,
                text=input_field_label,
                width=19,
                anchor="center",
                justify="center",
            ).grid(column=indx, row=0, padx=5, pady=5)

        # Dictionary to store drop down widgets
        drop_down_items_dict = {}

        # Width for drop down objects
        drop_down_field_width = 17

        # Width for entry widgets
        entry_field_width = 19

        # Dictionary index for action drop down
        action_combo_box = f"action_combo_box"

        if range_data != None:
            action_type_options = [range_data["Action"]]

        else:
            # Values to be included in acton drop down
            action_type_options = ["BUY", "SELL"]

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

        # Intialize and place drop down for action input field
        drop_down_items_dict[action_combo_box] = ttk.Combobox(
            input_frame,
            width=drop_down_field_width,
            values=action_type_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        drop_down_items_dict[action_combo_box].current(0)
        drop_down_items_dict[action_combo_box].grid(column=1, row=1, padx=5, pady=5)

        # Dictionary index for order type drop down
        order_type_combo_box = f"order_type_combo_box"

        # Values to be included in order type drop down
        order_type_options = ["Market", "IB Algo Market"]

        # Intialize and place drop down for order type input field
        drop_down_items_dict[order_type_combo_box] = ttk.Combobox(
            input_frame,
            width=drop_down_field_width,
            values=order_type_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        drop_down_items_dict[order_type_combo_box].current(0)
        drop_down_items_dict[order_type_combo_box].grid(column=2, row=1, padx=5, pady=5)

        # Dictionary index for price movement drop down
        price_movement_combo_box = f"price_movement_combo_box"

        if range_data != None:
            price_movement_options = [range_data["Price Movement"]]

        else:
            # Values to be included in price movement drop down
            price_movement_options = ["Better", "Worse"]

        # Intialize and place drop down for price movement input field
        drop_down_items_dict[price_movement_combo_box] = ttk.Combobox(
            input_frame,
            width=drop_down_field_width,
            values=price_movement_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        drop_down_items_dict[price_movement_combo_box].current(0)
        drop_down_items_dict[price_movement_combo_box].grid(
            column=9, row=1, padx=5, pady=5
        )

        # Dictionary index for take profit behaviour drop down
        take_profit_behaviour_combo_box = f"take_profit_behaviour_combo_box"

        # Values to be included in take profit behaviour drop down
        take_profit_behaviour_options = ["Continue", "Restart", "Terminate"]

        # Intialize and place drop down for take profit behaviour input field
        drop_down_items_dict[take_profit_behaviour_combo_box] = ttk.Combobox(
            input_frame,
            width=drop_down_field_width,
            values=take_profit_behaviour_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        drop_down_items_dict[take_profit_behaviour_combo_box].current(0)
        drop_down_items_dict[take_profit_behaviour_combo_box].grid(
            column=11, row=1, padx=5, pady=5
        )

        # Create a list of options
        bypass_rm_account_checks_options = ["True", "False"]

        # Create the combo box
        bypass_rm_account_checks_options_combo_box = ttk.Combobox(
            input_frame,
            width=18,
            values=bypass_rm_account_checks_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        bypass_rm_account_checks_options_combo_box.current(1)
        bypass_rm_account_checks_options_combo_box.grid(
            column=13, row=1, padx=5, pady=5
        )

        # Create a list of options
        flag_execution_engine_options = [True, False]

        # Create the combo box
        flag_execution_engine_options_combo_box = ttk.Combobox(
            input_frame,
            width=18,
            values=flag_execution_engine_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        flag_execution_engine_options_combo_box.current(
            flag_execution_engine_options.index(variables.flag_use_execution_engine)
        )
        flag_execution_engine_options_combo_box.grid(column=14, row=1, padx=5, pady=5)

        # Dictionary index for account id drop down
        account_id_combo_box = f"account_id_combo_box"

        # Create a list of options
        current_session_accounts_options = copy.deepcopy(
            variables.current_session_accounts
        )

        if flag_multi:
            # Create a frame for the input fields
            trade_input_frame_acc = ttk.Frame(input_frame, padding=0)
            trade_input_frame_acc.grid(column=12, row=1, padx=5, pady=15, rowspan=4)

            # Create a listbox
            listbox = Listbox(
                trade_input_frame_acc,
                width=19,
                height=7,
                selectmode=MULTIPLE,
                exportselection=False,
            )
            scrollbar = Scrollbar(trade_input_frame_acc)

            # Adding Scrollbar to the right
            # side of root window
            scrollbar.pack(side=RIGHT, fill=BOTH)
            # scroll we use yscrollcommand
            listbox.config(yscrollcommand=scrollbar.set)

            # setting scrollbar command parameter
            # to listbox.yview method its yview because
            # we need to have a vertical view
            scrollbar.config(command=listbox.yview)

            listbox_index = 0

            # Inserting the listbox items
            # Get all account ids
            for indx, account_id in enumerate(
                variables.current_session_accounts, start=1
            ):
                listbox.insert(indx, "Account: " + account_id)

                listbox_index = indx

            account_group_df = get_all_account_groups_from_db()

            for indx, account_id in enumerate(
                account_group_df["Group Name"].to_list(), start=1
            ):
                listbox.insert(listbox_index + indx, "Group: " + account_id)

            listbox.pack()

        else:
            # Create the combo box
            drop_down_items_dict[account_id_combo_box] = ttk.Combobox(
                input_frame,
                # textvariable=selected_account_option,
                width=18,
                values=current_session_accounts_options,
                state="readonly",
                style="Custom.TCombobox",
            )
            drop_down_items_dict[account_id_combo_box].current(0)
            drop_down_items_dict[account_id_combo_box].grid(
                column=12, row=1, padx=5, pady=5
            )

        # Input textbox for total quantity
        total_quantity_entry = ttk.Entry(
            input_frame,
            width=entry_field_width,
        )
        total_quantity_entry.grid(column=3, row=1, padx=5, pady=5)

        # Input textbox for initial quantity
        initial_quantity_entry = ttk.Entry(
            input_frame,
            width=entry_field_width,
        )
        initial_quantity_entry.grid(column=4, row=1, padx=5, pady=5)

        # Input textbox for subsequent quantity
        subsequent_quantity_entry = ttk.Entry(
            input_frame,
            width=entry_field_width,
        )
        subsequent_quantity_entry.grid(column=5, row=1, padx=5, pady=5)

        # Input textbox for number of buckets
        number_of_buckets_entry = ttk.Entry(
            input_frame,
            width=entry_field_width,
        )
        number_of_buckets_entry.grid(column=6, row=1, padx=5, pady=5)

        # Input textbox for initial entry price
        initial_entry_price_entry = ttk.Entry(
            input_frame,
            width=entry_field_width,
        )
        initial_entry_price_entry.grid(column=7, row=1, padx=5, pady=5)

        # Input textbox for delta price
        delta_price_entry = ttk.Entry(
            input_frame,
            width=entry_field_width,
        )
        delta_price_entry.grid(column=8, row=1, padx=5, pady=5)

        # Input textbox for take profit buffer
        take_profit_buffer_entry = ttk.Entry(
            input_frame,
            width=entry_field_width,
        )
        take_profit_buffer_entry.grid(column=10, row=1, padx=5, pady=5)

        # Create a frame for the "Add Scale Trade" button
        button_frame = ttk.Frame(popup)
        button_frame.place(relx=0.5, anchor=tk.CENTER)

        # atr for order dict
        order_atr_values = copy.deepcopy(
            variables.map_unique_id_to_atr_for_order_values
        )

        # check if flag for range is true
        if flag_range:
            total_quantity_entry.insert(0, str(range_data["Total Quantity"]))

            number_of_buckets_entry.insert(0, str(range_data["Number of Buckets"]))

            # disable entries
            subsequent_quantity_entry.config(state="disabled")
            total_quantity_entry.config(state="readonly")
            number_of_buckets_entry.config(state="readonly")
            initial_entry_price_entry.config(state="disabled")
            delta_price_entry.config(state="disabled")
            initial_quantity_entry.config(state="disabled")

            pad_y_val = 0

            # check flag for multi account
            if not flag_multi:
                # Geometry
                popup.geometry("1850x470")

                pad_y_val = 10

            else:
                # Geometry
                popup.geometry("1850x560")

                pad_y_val = 0

            # Create a frame inside the popup
            frame_parent = ttk.Frame(popup)
            frame_parent.pack(fill="both", expand=True, side=BOTTOM)

            # Create a frame inside the popup
            frame = ttk.Frame(frame_parent, width=500)
            frame.pack(side=TOP, pady=(pad_y_val, 0))

            # Treeview Scrollbar
            tree_scroll = Scrollbar(frame)
            tree_scroll.pack(side="right", fill="y")

            lots_extend = ""

            if flag_multi:
                lots_extend = "(%)"

            # Create a Treeview widget inside the frame
            tree = ttk.Treeview(
                frame,
                columns=("#Lots", "Price"),
                yscrollcommand=tree_scroll.set,
                height=11,
                selectmode="extended",
                show="headings",
            )

            # Configure the scrollbar
            tree_scroll.config(command=tree.yview)

            # add columns in table

            tree.column("#Lots", width=200, anchor=tk.CENTER)
            tree.column("Price", width=200, anchor=tk.CENTER)

            # Define column headings

            tree.heading("#Lots", text="#Lots" + lots_extend)
            tree.heading("Price", text="Price")

            # palce table
            tree.pack(fill="both", expand=True, side=TOP)

            # Back ground for rows in table
            tree.tag_configure("oddrow", background="white")
            tree.tag_configure("evenrow", background="lightblue")

            price_movement = range_data["Price Movement"]

            action = range_data["Action"]

            number_of_buckets = int(range_data["Number of Buckets"])

            # get entry price and delta price for range orders
            if action == "BUY" and price_movement == "Better":
                initial_entry_price = range_prices_dict["Highest Price"]
                delta_price = (
                    range_prices_dict["Highest Price"]
                    - range_prices_dict["Lowest Price"]
                ) / int(number_of_buckets)

            elif action == "BUY" and price_movement == "Worse":
                initial_entry_price = range_prices_dict["Lowest Price"]
                delta_price = (
                    range_prices_dict["Highest Price"]
                    - range_prices_dict["Lowest Price"]
                ) / int(number_of_buckets)

            elif action == "SELL" and price_movement == "Better":
                initial_entry_price = range_prices_dict["Lowest Price"]
                delta_price = (
                    range_prices_dict["Highest Price"]
                    - range_prices_dict["Lowest Price"]
                ) / int(number_of_buckets)

            elif action == "SELL" and price_movement == "Worse":
                initial_entry_price = range_prices_dict["Highest Price"]
                delta_price = (
                    range_prices_dict["Highest Price"]
                    - range_prices_dict["Lowest Price"]
                ) / int(number_of_buckets)

            # round up values
            initial_entry_price = round(initial_entry_price, 2)
            delta_price = round(delta_price, 2)

            # Check if price movement is better
            if price_movement == "Better":
                # Check if action is BUY
                if action == "BUY":
                    delta_price *= -1
                else:
                    delta_price = delta_price

            # Check if price movement is worse
            elif price_movement == "Worse" and delta_price not in ["None", None]:
                # Check if action is SELL
                if action == "SELL":
                    delta_price *= -1
                else:
                    delta_price = delta_price

            # get df for data
            pair_df = pd.DataFrame()

            if not flag_multi:
                total_quantity_remaining = int(range_data["Total Quantity"])

            else:
                total_quantity_remaining = float(range_data["Total Quantity"])

            number_of_buckets = int(range_data["Number of Buckets"])

            subsequent_quantitities_list = []

            # Get subsequent qauntity for each bucket
            for bucket_number in range(1, number_of_buckets + 1):
                if bucket_number != number_of_buckets:
                    if not flag_multi:
                        # Get round value of subsequent qauntity in case for number of buckets value is not None
                        round_subsequent_quantity_for_sequences = round(
                            total_quantity_remaining
                            / (number_of_buckets - (bucket_number - 1))
                        )

                    else:
                        # Get round value of subsequent qauntity in case for number of buckets value is not None
                        round_subsequent_quantity_for_sequences = round(
                            total_quantity_remaining
                            / (number_of_buckets - (bucket_number - 1)),
                            2,
                        )

                    # Getting subsequent quantities for sequences afetr initial sequence and before last sequence in case of number of buckets is not none
                    subsequent_quantitities_list.append(
                        round_subsequent_quantity_for_sequences
                    )

                    # Keep total quantity remaining to trade for next bucket
                    total_quantity_remaining -= round_subsequent_quantity_for_sequences

                elif total_quantity_remaining != 0:
                    # Sort list
                    subsequent_quantitities_list.sort(reverse=True)

                    if flag_multi:
                        total_quantity_remaining = round(total_quantity_remaining, 2)

                    # Getting subsequent quantities for last sequence in case of number of buckets is not none
                    subsequent_quantitities_list.append(total_quantity_remaining)

            price_list = []

            for indx, qnty in enumerate(subsequent_quantitities_list):
                price_list.append(round(initial_entry_price + (delta_price * indx), 2))

            counter = 0

            # fill table of schedule data
            for lots, price in zip(subsequent_quantitities_list, price_list):
                # get table id
                table_id = price

                # get tuple of values
                row = (lots, price)

                # insert rows in table
                if counter % 2 == 0:
                    tree.insert(
                        "",
                        "end",
                        iid=table_id,
                        values=row,
                        tags=("evenrow",),
                    )

                else:
                    tree.insert(
                        "",
                        "end",
                        iid=table_id,
                        values=row,
                        tags=("oddrow",),
                    )

                counter += 1

        # check for range schedule data
        if schedule_data != None:
            # disable entries
            subsequent_quantity_entry.config(state="disabled")
            initial_entry_price_entry.config(state="disabled")
            delta_price_entry.config(state="disabled")
            # disable entries
            total_quantity_entry.config(state="disabled")
            initial_quantity_entry.config(state="disabled")
            number_of_buckets_entry.config(state="disabled")

        # Get atr value
        try:
            # Get ATR value
            atr = (
                "N/A"
                if order_atr_values[unique_id] == "N/A"
                else order_atr_values[unique_id]
            )

            # Check if atr is float
            if is_float(atr):
                # pre-fill value at delta price textbox
                delta_price_entry.insert(0, atr)

            else:
                pass

        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print(f"Exceptions in getting ATR for scale trade pop up, Exp: {e}")

        # Check if flag for multi account is True
        if flag_multi:
            button_frame.place(y=210)

        else:
            button_frame.place(y=120)

        # Text we want to show for the button
        add_scale_trade_button_text = "Add Scale Trade"

        # Create the "Add Scale Trade" button
        add_scale_trade_button = ttk.Button(
            button_frame,
            text=add_scale_trade_button_text,
            command=lambda: on_add_scale_trade_button_click(
                add_scale_trade_button, popup
            ),
        )
        add_scale_trade_button.grid(row=0, column=0, padx=10, pady=(0, 0))

        # Validate all input values from add scale trade pop up
        def validate_values_of_input_fields_from_pop_up(
            unique_id,
            total_quantity,
            initial_quantity,
            subsequent_quantity,
            number_of_buckets,
            initial_entry_price,
            delta_price,
            take_profit_buffer,
            flag_multi=False,
            account_id_list=None,
        ):
            try:
                # Check if flag for multi account is false
                if not flag_multi:
                    # Check if user provided value for both subsequent quantity and number of buckets
                    if subsequent_quantity != "" and number_of_buckets != "":
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Both subsequent quantity and number of buckets fields must not be filled at same time",
                        )

                    # Check if total quantity fields are not filled
                    if total_quantity == "":
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Total quantity field must be filled",
                        )

                    # Check if initial quantity fields are not filled
                    '''if initial_quantity == '':
                
                        return False, f"Error, For Unique ID: {unique_id}, Initial quantity field must be filled"'''

                    # Check if either subsequent quantity or number of buckets field are not filled
                    if subsequent_quantity == "" and number_of_buckets == "":
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Either subsequent quantity or number of buckets fields must be filled",
                        )

                    # Check if initial entry price field are not filled
                    '''if initial_entry_price == '':
                
                        return False, f"Error, For Unique ID: {unique_id}, Initial entry price field must be filled"'''

                    # Check if take profit buffer fields are not filled
                    '''if take_profit_buffer == '':
                
                        return False, f"Error, For Unique ID: {unique_id}, Take profit buffer field must be filled"'''

                    # Check if total quantity input has non - integer value
                    if not is_integer(total_quantity):
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for total quantity must be numeric",
                        )

                    # Check if total quantity input has non - positive value
                    if int(float(total_quantity)) <= 1:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for total quantity must be greater than 1",
                        )

                    # Check if to initial quantity input has non - integer value
                    if initial_quantity != "" and not is_integer(initial_quantity):
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for initial quantity must be numeric",
                        )

                    # Check if initial quantity input has non - positive value
                    if initial_quantity != "" and int(float(initial_quantity)) < 1:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for initial quantity must be positive number",
                        )

                    # Check if to subsequent quantity input has non - integer value
                    if (
                        subsequent_quantity != "" and number_of_buckets == ""
                    ) and not is_integer(subsequent_quantity):
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for subsequent quantity must be numeric",
                        )

                    # Check if subsequent quantity input has non - positive value
                    if (subsequent_quantity != "" and number_of_buckets == "") and int(
                        float(subsequent_quantity)
                    ) < 1:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for subsequent quantity must be positive number",
                        )

                    # Check if to number of buckets input has non - integer value
                    if (
                        subsequent_quantity == "" and number_of_buckets != ""
                    ) and not is_integer(number_of_buckets):
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for number of buckets must be numeric",
                        )

                    # Check if number of buckets input has non - positive value
                    if (subsequent_quantity == "" and number_of_buckets != "") and int(
                        float(number_of_buckets)
                    ) < 2:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Number of buckets must be at least 2",
                        )

                    # check if initial qunatity is greater than total quantity
                    if initial_quantity != "" and int(float(total_quantity)) <= int(
                        float(initial_quantity)
                    ):
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for total quantity must be greater than initial quantity",
                        )

                    # check if number of buckets for subsequent orders is less than total quantity for subsequent orders
                    if (
                        subsequent_quantity == ""
                        and number_of_buckets != ""
                        and initial_quantity != ""
                    ) and (
                        int(float(total_quantity)) - (int(float(initial_quantity)))
                    ) // int(float(number_of_buckets) - 1) < 1:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Number of buckets for subsequent orders is greater than total quantity for subsequent orders",
                        )

                    # check if number of buckets for subsequent orders is less than total quantity for subsequent orders
                    if (
                        subsequent_quantity == ""
                        and number_of_buckets != ""
                        and initial_quantity == ""
                    ) and (int(float(total_quantity))) // int(
                        float(number_of_buckets)
                    ) < 1:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Number of buckets for subsequent orders is greater than total quantity for subsequent orders",
                        )

                    # check if subsequent quantity is greater than total quantity
                    if (subsequent_quantity != "" and number_of_buckets == "") and int(
                        float(total_quantity)
                    ) <= int(float(subsequent_quantity)):
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for total quantity must be greater than subsequent quantity",
                        )

                else:
                    # Check if user provided value for both subsequent quantity and number of buckets
                    if subsequent_quantity != "" and number_of_buckets != "":
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Both subsequent quantity and number of buckets fields must not be filled at same time",
                        )

                    # Check if total quantity fields are not filled
                    if total_quantity == "":
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Total quantity field must be filled",
                        )

                    # Check if initial quantity fields are not filled
                    '''if initial_quantity == '':
                
                        return False, f"Error, For Unique ID: {unique_id}, Initial quantity field must be filled"'''

                    # Check if either subsequent quantity or number of buckets field are not filled
                    if subsequent_quantity == "" and number_of_buckets == "":
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Either subsequent quantity or number of buckets fields must be filled",
                        )

                    # Check if total quantity input has non - integer value
                    if not is_float(total_quantity):
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for total quantity must be decimal",
                        )

                    # Check if total quantity input has non - positive value
                    if float(total_quantity) <= 0:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for total quantity must be greater than 0",
                        )

                    # Check if to initial quantity input has non - integer value
                    if initial_quantity != "" and not is_float(initial_quantity):
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for initial quantity must be decimal",
                        )

                    # Check if initial quantity input has non - positive value
                    if initial_quantity != "" and float(initial_quantity) <= 0:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for initial quantity must be greater than 0",
                        )

                    # Check if to subsequent quantity input has non - integer value
                    if (
                        subsequent_quantity != "" and number_of_buckets == ""
                    ) and not is_float(subsequent_quantity):
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for subsequent quantity must be decimal",
                        )

                    # Check if subsequent quantity input has non - positive value
                    if (
                        subsequent_quantity != "" and number_of_buckets == ""
                    ) and float(subsequent_quantity) <= 0:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for subsequent quantity must be greater than 0",
                        )

                    # Check if to number of buckets input has non - integer value
                    if (
                        subsequent_quantity == "" and number_of_buckets != ""
                    ) and not is_integer(number_of_buckets):
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for number of buckets must be decimal",
                        )

                    # Check if number of buckets input has non - positive value
                    if (subsequent_quantity == "" and number_of_buckets != "") and int(
                        float(number_of_buckets)
                    ) < 2:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Number of buckets must be at least 2",
                        )

                    # check if initial qunatity is greater than total quantity
                    if initial_quantity != "" and float(initial_quantity) >= 100:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for total quantity must be lesser than 100",
                        )

                    # check if number of buckets for subsequent orders is less than total quantity for subsequent orders
                    '''if (subsequent_quantity == '' and number_of_buckets != '' and initial_quantity != '') and (int(float(total_quantity)) - (int(float(initial_quantity)))) // int(float(number_of_buckets) - 1) < 1:
                        
                        return False, f"Error, For Unique ID: {unique_id}, Number of buckets for subsequent orders is greater than total quantity for subsequent orders"
                    
                    # check if number of buckets for subsequent orders is less than total quantity for subsequent orders
                    if (subsequent_quantity == '' and number_of_buckets != '' and initial_quantity == '') and (int(float(total_quantity))) // int(float(number_of_buckets)) < 1:
                        
                        return False, f"Error, For Unique ID: {unique_id}, Number of buckets for subsequent orders is greater than total quantity for subsequent orders"'''

                    # check if subsequent quantity is greater than total quantity
                    if (
                        subsequent_quantity != "" and number_of_buckets == ""
                    ) and float(subsequent_quantity) >= 100:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, Value for total quantity must be lesser than 100",
                        )

                    # Check if multiple account selection is empty
                    if flag_multi and account_id_list == []:
                        return (
                            False,
                            f"Error, For Unique ID: {unique_id}, List of Account ID is Unavailable.",
                        )

                # If intiial entry price is empty
                '''if initial_entry_price  == '':
                        
                    try:
                        
                        # Get current price of combo
                        initial_entry_price = (variables.unique_id_to_prices_dict[unique_id]['BUY'] + variables.unique_id_to_prices_dict[unique_id]['SELL']) / 2
                    
                    except Exception as e:
                        
                        return False, f"Error, For Unique ID: {unique_id}, Current price of combination for initial entry price is invalid"'''
                # Check if initial entry price is non float value
                if initial_entry_price != "" and not is_float(initial_entry_price):
                    return (
                        False,
                        f"Error, For Unique ID: {unique_id}, Value for initial entry price must be decimal number",
                    )

                # Check if delta price field are not filled
                if delta_price == "":
                    return (
                        False,
                        f"Error, For Unique ID: {unique_id}, Delta price field must be filled",
                    )

                # Check if delta price is non float value
                if not is_float(delta_price):
                    return (
                        False,
                        f"Error, For Unique ID: {unique_id}, Value for delta price must be decimal number",
                    )

                # Check if delta price input has negative or 0 value
                if float(delta_price) <= 0:
                    return (
                        False,
                        f"Error, For Unique ID: {unique_id}, Value for delta price must be positive decimal number",
                    )

                # Check if take profit buffer is non float value
                if take_profit_buffer != "" and not is_float(take_profit_buffer):
                    return (
                        False,
                        f"Error, For Unique ID: {unique_id}, Value for take profit buffer must be decimal number",
                    )

                # Check if take profit buffer input has negative or 0 value
                if take_profit_buffer != "" and float(take_profit_buffer) <= 0:
                    return (
                        False,
                        f"Error, For Unique ID: {unique_id}, Value for take profit buffer must be positive decimal number",
                    )

                # If no problem found then return true
                return True, "No Error"

            except Exception as e:
                # Returning false if any exception occurs
                return False, f"Error, For Unique ID: {unique_id}, Exp: {e}"

        # On click function for add scale trade button
        def on_add_scale_trade_button_click(add_scale_trade_button, popup):
            # Disabled add scale trade button
            add_scale_trade_button.config(state="disabled")

            # Thread to add new scale trade
            add_scale_trader_thread = threading.Thread(
                target=add_scale_trade,
                args=(add_scale_trade_button, popup),
            )
            add_scale_trader_thread.start()

            # Enabled add scale trade button
            add_scale_trade_button.config(state="normal")

        # Function for add scale trade button
        def add_scale_trade(add_scale_trade_button, popup):
            try:
                # Dictionary index for action drop down
                action_combo_box = f"action_combo_box"

                # Dictionary index for order type drop down
                order_type_combo_box = f"order_type_combo_box"

                # Dictionary index for price movement drop down
                price_movement_combo_box = f"price_movement_combo_box"

                # Dictionary index for take profit behaviour drop down
                take_profit_behaviour_combo_box = f"take_profit_behaviour_combo_box"

                # Dictionary index for take account id drop down
                account_id_combo_box = f"account_id_combo_box"

                # Getting inputs from add scale trade pop up drop downs
                action = drop_down_items_dict[action_combo_box].get().strip()

                order_type = drop_down_items_dict[order_type_combo_box].get().strip()

                price_movement = (
                    drop_down_items_dict[price_movement_combo_box].get().strip()
                )

                take_profit_behaviour = (
                    drop_down_items_dict[take_profit_behaviour_combo_box].get().strip()
                )

                bypass_rm_check = (
                    bypass_rm_account_checks_options_combo_box.get().strip()
                )

                flag_execution_engine = (
                    flag_execution_engine_options_combo_box.get().strip()
                )

                if flag_multi:
                    # Init
                    account_id_list = []

                    # Get list of selections
                    for i in listbox.curselection():
                        # Split item in listbox
                        accounts_type = listbox.get(i).split(":")[0]

                        # Check if its account
                        if accounts_type == "Account":
                            # Append account id in list
                            account_id_list.append(listbox.get(i)[8:].strip())

                        else:
                            # Get account ids in group
                            accounts_in_group = get_accounts_in_account_group_from_db(
                                listbox.get(i)[6:].strip()
                            )

                            # Check if account group is 'all'
                            if accounts_in_group == "ALL":
                                # Set value of list to list of all account in current session
                                account_id_list = variables.current_session_accounts
                                break

                            else:
                                # Append account in account group on by one
                                for account in accounts_in_group.split(","):
                                    # check if unique id is in current session accounts
                                    if (
                                        account
                                        not in variables.current_session_accounts
                                    ):
                                        # Error pop up
                                        error_title = f"For Account ID: {account}, Account ID is unavailable in current session."
                                        error_string = f"For Account ID: {account}, Can not trade combo\nbecause Account ID is unavailable in current session."

                                        self.display_error_popup(
                                            error_title, error_string
                                        )

                                        return

                                    account_id_list.append(account)

                    # Get unique account ids and sort them
                    account_id_list = sorted(list(set(account_id_list)))

                else:
                    account_id = (
                        drop_down_items_dict[account_id_combo_box].get().strip()
                    )

                # Getting input from add scale trade pop up textboxes
                total_quantity = (
                    input_frame.grid_slaves(row=1, column=3)[0].get().strip()
                )
                initial_quantity = (
                    input_frame.grid_slaves(row=1, column=4)[0].get().strip()
                )
                subsequent_quantity = (
                    input_frame.grid_slaves(row=1, column=5)[0].get().strip()
                )
                number_of_buckets = (
                    input_frame.grid_slaves(row=1, column=6)[0].get().strip()
                )
                initial_entry_price = (
                    input_frame.grid_slaves(row=1, column=7)[0].get().strip()
                )
                delta_price = input_frame.grid_slaves(row=1, column=8)[0].get().strip()
                take_profit_buffer = (
                    input_frame.grid_slaves(row=1, column=10)[0].get().strip()
                )

                # chck if schedule price is available
                if schedule_data != None:
                    # get df
                    pair_df = schedule_data["Percentage Lots Pair"]

                    # sorrt df based on action and price movement
                    if action == "BUY" and price_movement == "Better":
                        # Sorting the DataFrame based on column in reverse order
                        pair_df = pair_df.sort_values(by="Percentage", ascending=False)

                    elif action == "BUY" and price_movement == "Worse":
                        # Sorting the DataFrame based on column in reverse order
                        pair_df = pair_df.sort_values(by="Percentage", ascending=True)

                    elif action == "SELL" and price_movement == "Better":
                        # Sorting the DataFrame based on column in reverse order
                        pair_df = pair_df.sort_values(by="Percentage", ascending=True)

                    else:
                        # Sorting the DataFrame based on column in reverse order
                        pair_df = pair_df.sort_values(by="Percentage", ascending=False)

                    # convert column to int
                    pair_df["#Lots"] = pair_df["#Lots"].astype(int)

                    # get list of quantity
                    list_of_qnty = pair_df["#Lots"].to_list()

                    # get list of prices
                    list_of_price = pair_df["Price"].to_list()

                    # overwrite values
                    total_quantity = sum(list_of_qnty)
                    initial_quantity = list_of_qnty[0]
                    number_of_buckets = len(list_of_qnty)

                    initial_entry_price = list_of_price[0]

                    delta_price = 3

                # check for flag of rnage orders
                if flag_range and number_of_buckets.isnumeric():
                    if range_prices_dict in ["None", None]:
                        # Make error string multiline
                        error_title = error_string = make_multiline_mssg_for_gui_popup(
                            "Historical Data is not fetched yet"
                        )

                        # Error Message
                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    try:
                        # get entry price and delta price for range orders
                        if action == "BUY" and price_movement == "Better":
                            initial_entry_price = range_prices_dict["Highest Price"]
                            delta_price = (
                                range_prices_dict["Highest Price"]
                                - range_prices_dict["Lowest Price"]
                            ) / int(number_of_buckets)

                        elif action == "BUY" and price_movement == "Worse":
                            initial_entry_price = range_prices_dict["Lowest Price"]
                            delta_price = (
                                range_prices_dict["Highest Price"]
                                - range_prices_dict["Lowest Price"]
                            ) / int(number_of_buckets)

                        elif action == "SELL" and price_movement == "Better":
                            initial_entry_price = range_prices_dict["Lowest Price"]
                            delta_price = (
                                range_prices_dict["Highest Price"]
                                - range_prices_dict["Lowest Price"]
                            ) / int(number_of_buckets)

                        elif action == "SELL" and price_movement == "Worse":
                            initial_entry_price = range_prices_dict["Highest Price"]
                            delta_price = (
                                range_prices_dict["Highest Price"]
                                - range_prices_dict["Lowest Price"]
                            ) / int(number_of_buckets)

                        # round up values
                        initial_entry_price = round(initial_entry_price, 2)
                        delta_price = round(delta_price, 2)

                    except Exception as e:
                        # init
                        initial_entry_price = "None"
                        delta_price = "None"

                if flag_multi:
                    # Check input values in add scale trade pop up are valid
                    (
                        is_input_values_valid,
                        error_message,
                    ) = validate_values_of_input_fields_from_pop_up(
                        unique_id,
                        total_quantity,
                        initial_quantity,
                        subsequent_quantity,
                        number_of_buckets,
                        initial_entry_price,
                        delta_price,
                        take_profit_buffer,
                        flag_multi=flag_multi,
                        account_id_list=account_id_list,
                    )

                else:
                    # Check input values in add scale trade pop up are valid
                    (
                        is_input_values_valid,
                        error_message,
                    ) = validate_values_of_input_fields_from_pop_up(
                        unique_id,
                        total_quantity,
                        initial_quantity,
                        subsequent_quantity,
                        number_of_buckets,
                        initial_entry_price,
                        delta_price,
                        take_profit_buffer,
                    )

            except Exception as e:
                # If exception occurs
                is_input_values_valid, error_message = (
                    False,
                    f"Error, For Unique ID: {unique_id}, Exp: {e}",
                )

            # If there is error in input values then display error pop up
            if not is_input_values_valid:
                # Make error string multiline
                error_title = error_string = make_multiline_mssg_for_gui_popup(
                    error_message
                )

                # Error Message
                variables.screen.display_error_popup(error_title, error_string)

            # If all input values are valid
            else:
                # make delta price None for schedule orders
                if schedule_data != None:
                    delta_price = "None"

                if flag_multi:
                    try:
                        price = (
                            variables.unique_id_to_prices_dict[unique_id]["BUY"]
                            + variables.unique_id_to_prices_dict[unique_id]["SELL"]
                        ) / 2

                    except Exception as e:
                        error_title = f"For Unique ID: {unique_id}, Could not get price of combination"
                        error_string = f"For Unique ID: {unique_id}, Could not get price of combination"

                        self.display_error_popup(error_title, error_string)
                        return

                    # Init
                    map_account_to_quanity_dict = {}
                    map_account_to_initial_quanity_dict = {}
                    map_account_to_subsequent_quanity_dict = {}

                    try:
                        # Iterating account ids
                        for account in account_id_list:
                            # get total quanity, intital quantity and subsequence quanity for range schedule orders
                            if schedule_data != None:
                                map_account_to_quanity_dict[account] = total_quantity

                                map_account_to_initial_quanity_dict[account] = (
                                    initial_quantity
                                )

                                map_account_to_subsequent_quanity_dict = (
                                    total_quantity - initial_quantity
                                )

                                continue

                            # Getting value of account parameter
                            if variables.account_parameter_for_order_quantity == "NLV":
                                value_of_account_parameter = (
                                    variables.accounts_table_dataframe.loc[
                                        variables.accounts_table_dataframe["Account ID"]
                                        == account,
                                        variables.accounts_table_columns[1],
                                    ].iloc[0]
                                )

                            elif (
                                variables.account_parameter_for_order_quantity == "SMA"
                            ):
                                value_of_account_parameter = (
                                    variables.accounts_table_dataframe.loc[
                                        variables.accounts_table_dataframe["Account ID"]
                                        == account,
                                        variables.accounts_table_columns[2],
                                    ].iloc[0]
                                )

                            elif (
                                variables.account_parameter_for_order_quantity == "CEL"
                            ):
                                value_of_account_parameter = (
                                    variables.accounts_table_dataframe.loc[
                                        variables.accounts_table_dataframe["Account ID"]
                                        == account,
                                        variables.accounts_table_columns[4],
                                    ].iloc[0]
                                )

                            else:
                                error_title = "Invalid Account Parameter"
                                error_string = f"Please provide valid Account Parameter"

                                self.display_error_popup(error_title, error_string)
                                return

                            # Check if account parameter value is invalid
                            if not is_float(value_of_account_parameter):
                                error_title = "Invalid Account Parameter Value"
                                error_string = f"For Account ID: {account}, Value of account Parameter: {variables.account_parameter_for_order_quantity} is invalid"

                                variables.screen.display_error_popup(
                                    error_title, error_string
                                )
                                return

                            # Calculate combo qunaity for account id
                            if float(price) != 0:
                                combo_quantity = float(total_quantity)

                                combo_quantity_for_account = round(
                                    (
                                        (combo_quantity / 100)
                                        * float(value_of_account_parameter)
                                    )
                                    / abs(float(price))
                                )

                            else:
                                combo_quantity_for_account = 0

                            # add it to dictionary
                            map_account_to_quanity_dict[account] = (
                                combo_quantity_for_account
                            )

                            if initial_quantity != "":
                                map_account_to_initial_quanity_dict[account] = round(
                                    combo_quantity_for_account
                                    * (float(initial_quantity) / 100)
                                )

                            if subsequent_quantity != "":
                                map_account_to_subsequent_quanity_dict[account] = round(
                                    combo_quantity_for_account
                                    * (float(subsequent_quantity) / 100)
                                )

                    except Exception as e:
                        error_title = f"For Unique ID: {unique_id}, Could not get quantity for accounts"
                        error_string = f"For Unique ID: {unique_id}, Could not get quantity for accounts"

                        self.display_error_popup(error_title, error_string)
                        return

                try:
                    # If entry price is empty
                    if initial_entry_price == "":
                        try:
                            # get current combo price
                            initial_entry_price = (
                                variables.unique_id_to_prices_dict[unique_id]["BUY"]
                                + variables.unique_id_to_prices_dict[unique_id]["SELL"]
                            ) / 2

                            # check if value is valid
                            if initial_entry_price not in ["N/A", None]:
                                initial_entry_price = round(initial_entry_price, 2)

                        except Exception as e:
                            # Make error string multiline
                            error_title = error_string = (
                                make_multiline_mssg_for_gui_popup(
                                    f"Error, For Unique ID: {unique_id}, Current price of combination for initial entry price is invalid"
                                )
                            )

                            # Error Message
                            variables.screen.display_error_popup(
                                error_title, error_string
                            )

                            return

                    else:
                        # Convert user inputted value to float
                        initial_entry_price = float(initial_entry_price)

                        # check if value is valid
                        if initial_entry_price not in ["N/A", None]:
                            initial_entry_price = round(initial_entry_price, 2)

                    # Check if take profit buffer is empty
                    if take_profit_buffer == "":
                        take_profit_buffer = "None"

                    else:
                        take_profit_buffer = float(take_profit_buffer)

                    if is_float(delta_price):
                        # convert values to float
                        delta_price = float(delta_price)

                    if not flag_multi:
                        # Convert values to integer
                        total_quantity = int(float(total_quantity))

                        # If subsequent quantity is empty then make it None
                        if subsequent_quantity == "":
                            # Convert value to integer
                            number_of_buckets = int(float(number_of_buckets))

                            # Check if initial quanity is empty
                            if initial_quantity == "":
                                # Set value for initial quanity
                                initial_quantity = round(
                                    total_quantity / (number_of_buckets)
                                )
                            else:
                                # Format value for initial quanity
                                initial_quantity = int(float(initial_quantity))

                            subsequent_quantity = "None"

                        # If number of buckets is empty then make it None
                        elif number_of_buckets == "":
                            # Convert value to integer
                            subsequent_quantity = int(float(subsequent_quantity))

                            # Check if initial quanity is empty
                            if initial_quantity == "":
                                # Set value for initial quanity
                                initial_quantity = subsequent_quantity
                            else:
                                # Format value for initial quanity
                                initial_quantity = int(float(initial_quantity))

                            number_of_buckets = "None"

                        else:
                            pass

                        # Create ladder instance and sequences instances
                        create_ladder_and_sequences(
                            unique_id,
                            action,
                            order_type,
                            total_quantity,
                            initial_quantity,
                            subsequent_quantity,
                            number_of_buckets,
                            initial_entry_price,
                            delta_price,
                            price_movement,
                            take_profit_buffer,
                            take_profit_behaviour,
                            account_id,
                            bypass_rm_check,
                            flag_execution_engine,
                            schedule_data,
                        )

                        # Destroy pop up
                        popup.destroy()

                        # Update GUI screen
                        self.update_scale_trader_table()

                        return

                    else:
                        for account in map_account_to_quanity_dict:
                            # Convert values to integer
                            total_quantity_val = int(
                                float(map_account_to_quanity_dict[account])
                            )

                            # If subsequent quantity is empty then make it None
                            if subsequent_quantity == "":
                                # Convert value to integer
                                number_of_buckets_val = int(float(number_of_buckets))

                                # Check if initial quanity is empty
                                if initial_quantity == "":
                                    # Set value for initial quanity
                                    initial_quantity_val = round(
                                        total_quantity_val / (number_of_buckets_val)
                                    )
                                else:
                                    # Format value for initial quanity
                                    initial_quantity_val = int(
                                        float(
                                            map_account_to_initial_quanity_dict[account]
                                        )
                                    )

                                subsequent_quantity_val = "None"

                            # If number of buckets is empty then make it None
                            elif number_of_buckets == "":
                                # Convert value to integer
                                subsequent_quantity_val = int(
                                    float(
                                        map_account_to_subsequent_quanity_dict[account]
                                    )
                                )

                                # Check if initial quanity is empty
                                if initial_quantity == "":
                                    # Set value for initial quanity
                                    initial_quantity_val = (
                                        map_account_to_subsequent_quanity_dict[account]
                                    )
                                else:
                                    # Format value for initial quanity
                                    initial_quantity_val = int(
                                        float(
                                            map_account_to_initial_quanity_dict[account]
                                        )
                                    )

                                number_of_buckets_val = "None"

                            else:
                                pass

                            # if initial quantity is zero
                            if initial_quantity_val == 0:
                                initial_quantity_val = 1

                            # if subsequent quantity is zero
                            if subsequent_quantity_val == 0:
                                subsequent_quantity_val = 1

                            # Only create scale trade if total qty is greater than 0
                            if total_quantity_val > 0:
                                # Create ladder instance and sequences instances
                                create_ladder_and_sequences(
                                    unique_id,
                                    action,
                                    order_type,
                                    total_quantity_val,
                                    initial_quantity_val,
                                    subsequent_quantity_val,
                                    number_of_buckets_val,
                                    initial_entry_price,
                                    delta_price,
                                    price_movement,
                                    take_profit_buffer,
                                    take_profit_behaviour,
                                    account,
                                    bypass_rm_check,
                                    flag_execution_engine,
                                    schedule_data,
                                )

                        # Destroy pop up
                        popup.destroy()

                        # Update GUI screen
                        self.update_scale_trader_table()

                        return

                except Exception as e:
                    # Make error string multiline
                    error_title = error_string = make_multiline_mssg_for_gui_popup(
                        f"Error, For Unique ID: {unique_id}, Exp: {e}"
                    )

                    # Error Message
                    variables.screen.display_error_popup(error_title, error_string)

                    # Destroy pop up
                    popup.destroy()

                    return

    # Method to Insert scale trades in scale trade table at start of app
    def insert_scale_trade_in_scale_trader_table(self, row_value):
        # Convert row values to list
        value = [val for val in row_value]

        # Ladder id
        ladder_id = value[0]

        # Get the current number of items in the treeview
        num_items = len(self.scale_trader_table.get_children())

        if num_items % 2 == 1:
            self.scale_trader_table.insert(
                "",
                "end",
                iid=ladder_id,
                text=num_items + 1,
                values=value,
                tags=("oddrow",),
            )
        else:
            self.scale_trader_table.insert(
                "",
                "end",
                iid=ladder_id,
                text=num_items + 1,
                values=value,
                tags=("evenrow",),
            )

    # Method to update sclae trade after its order filled
    def update_scale_trade_after_order_filled(self, filled_order_details):
        try:
            # Get ladder id, sequence id and unique id of filled order of scale trade
            ladder_id = int(float(filled_order_details["Ladder ID"]))
            sequence_id = int(float(filled_order_details["Sequence ID"]))
            unique_id = int(float(filled_order_details["Unique ID"]))

            # Get action of filled order
            action = filled_order_details["Action"]

            # Get quantity of filled order
            quantity_of_filled_order = filled_order_details["#Lots"]

            # Get ladder id to ladder object mapped dictionary
            local_map_ladder_id_to_ladder_obj = copy.deepcopy(
                variables.map_ladder_id_to_ladder_obj
            )

            # Get ladder object
            ladder_obj = local_map_ladder_id_to_ladder_obj[ladder_id]

            # Get ladder status
            ladder_status = get_ladder_or_sequence_column_value_from_db(
                ladder_id=ladder_id, column_name_as_in_db="Status"
            )

            # Get account id for ladder
            ladder_account_id = get_ladder_or_sequence_column_value_from_db(
                ladder_id=ladder_id, column_name_as_in_db="Account ID"
            )

            # Get ladder take profit buffer
            ladder_take_profit_buffer = get_ladder_or_sequence_column_value_from_db(
                ladder_id=ladder_id, column_name_as_in_db="Take Profit Buffer"
            )

            # get bypass rm check of ladder
            bypass_rm_check = get_ladder_or_sequence_column_value_from_db(
                ladder_id=ladder_id, column_name_as_in_db="Bypass RM Check"
            )

            # Get execution engine value for ladder
            flag_use_execution_engine = get_ladder_or_sequence_column_value_from_db(
                ladder_id=ladder_id, column_name_as_in_db="Execution Engine"
            )

            # set boolean value for flag for execution engine
            if flag_use_execution_engine == "True":
                flag_use_execution_engine = True

            else:
                flag_use_execution_engine = False

            # Check if filled order is entry or exit
            if action == ladder_obj.action:
                # Get values of ladder in table for ladder id
                values = self.scale_trader_table.item(
                    ladder_id, "values"
                )  # get the values of the selected row

                # Get value of entry order filled
                entry_quantity_filled = ladder_obj.entry_quantity_filled

                # Calculate updated entry quantity filled
                updated_entry_quantity_filled = int(float(entry_quantity_filled)) + int(
                    float(quantity_of_filled_order)
                )

                # Dict of values to update in ladder db table
                update_ladder_values_dict = {
                    "Entry Quantity Filled": updated_entry_quantity_filled
                }

                # Update ladder db table values
                update_ladder_table_values(ladder_id, update_ladder_values_dict)

                # Update entry quantity filled in scale trade dataframe
                variables.scale_trade_table_dataframe.loc[
                    variables.scale_trade_table_dataframe["Ladder ID"] == ladder_id,
                    "Entry Quantity Filled",
                ] = updated_entry_quantity_filled

                # Update entry quantity filled attribute for local and global ladder obj
                ladder_obj.entry_quantity_filled = updated_entry_quantity_filled
                variables.map_ladder_id_to_ladder_obj[
                    ladder_id
                ].entry_quantity_filled = updated_entry_quantity_filled

                # Get entry sequence that must be correspondent to filled order
                index_of_active_entry_sequence = self.get_active_sequence(
                    ladder_obj.entry_sequences
                )

                # Get sequence object which is correspondent to filled order
                sequence_obj = ladder_obj.entry_sequences[
                    index_of_active_entry_sequence
                ]

                # Get entry price of sequence object which is correspondent to filled order
                last_entry_price = sequence_obj.price

                # Updating local sequence object which is present in ladder object
                sequence_obj.status = "Filled"
                sequence_obj.order_sent_time = filled_order_details["Last Update Time"]
                sequence_obj.last_update_time = filled_order_details["Last Update Time"]
                sequence_obj.filled_quantity = quantity_of_filled_order

                # Dict of values to update in sequence db table
                update_sequence_values_dict = {
                    "Order Sent Time": filled_order_details["Last Update Time"],
                    "Last Update Time": filled_order_details["Last Update Time"],
                    "Filled Quantity": quantity_of_filled_order,
                    "Status": "Filled",
                }

                # Update sequence db table values
                update_sequence_table_values(
                    str(sequence_id), update_sequence_values_dict
                )

                # Overwrite changes to global sequences obj
                variables.map_ladder_id_to_ladder_obj[ladder_id].entry_sequences[
                    index_of_active_entry_sequence
                ] = sequence_obj
                ##################

                # Code for cancelling current exit sequence and add new exit sequence sequence
                if ladder_take_profit_buffer != "None":
                    # Get current exit sequence
                    if len(ladder_obj.exit_sequences) > 0:
                        # Get active exit sequence
                        current_exit_sequence = ladder_obj.exit_sequences[-1]

                        # Get sequence id for previous sequnece obj
                        current_exit_sequence_id = current_exit_sequence.sequence_id

                        # Get current exit sequence
                        current_exit_sequence_status = (
                            get_ladder_or_sequence_column_value_from_db(
                                column_name_as_in_db="Status",
                                sequence_id=current_exit_sequence_id,
                            )
                        )

                        if current_exit_sequence_status not in ["Sent", "Filled"]:
                            # Cancel current exit order
                            cancel_orders_of_ladder_id_or_sequence_id(
                                sequence_id=str(current_exit_sequence_id)
                            )

                            # Current time in the target time zone
                            current_time_in_target_time_zone = datetime.datetime.now(
                                variables.target_timezone_obj
                            )

                            # Dict of values to update in sequence db table
                            update_sequence_values_dict = {
                                "Last Update Time": current_time_in_target_time_zone,
                                "Filled Quantity": "0",
                                "Status": "Cancelled",
                            }

                            # Update sequence db table values
                            update_sequence_table_values(
                                current_exit_sequence_id, update_sequence_values_dict
                            )

                            # Change status of exit sequence to cancel
                            current_exit_sequence.status = "Cancelled"

                            # Overwrite changes to global sequences obj
                            variables.map_ladder_id_to_ladder_obj[
                                ladder_id
                            ].exit_sequences[-1] = current_exit_sequence

                    # Get max sequence_id present
                    sequence_id = copy.deepcopy(variables.sequence_id)

                    # Increment it to use later
                    variables.sequence_id += 1

                    # Action for exit order, price for new exit sequence
                    if action == "BUY":
                        # Set Action for exit order 'SELL'
                        action_for_exit_sequence = "SELL"

                        # Get limit price for new exit order
                        price_for_new_exit_sequence = float(last_entry_price) + float(
                            ladder_obj.take_profit_buffer
                        )
                    else:
                        # Set Action for exit order 'BUY'
                        action_for_exit_sequence = "BUY"

                        # Get limit price for new exit order
                        price_for_new_exit_sequence = float(last_entry_price) - float(
                            ladder_obj.take_profit_buffer
                        )

                    # order type and  quantity
                    order_type = ladder_obj.order_type
                    quantity = int(float(ladder_obj.entry_quantity_filled)) - int(
                        float(ladder_obj.exit_quantity_filled)
                    )

                    # Append initial entry order to list
                    new_exit_sequence_values = [
                        sequence_id,
                        "Exit",
                        ladder_id,
                        action_for_exit_sequence,
                        order_type,
                        quantity,
                        price_for_new_exit_sequence,
                        "None",
                        "None",
                        "None",
                        0,
                        "Active",
                    ]

                    # Get columns of sequence table
                    local_sequence_table_columns = copy.deepcopy(
                        variables.sequence_table_columns
                    )

                    # Use zip() to combine the column names and column values element-wise and create a list of tuples
                    sequence_table_column_value_pair = zip(
                        local_sequence_table_columns, new_exit_sequence_values
                    )

                    # Convert the list of tuples to a dictionary using the dict() constructor
                    sequence_table_column_value_dict = dict(
                        sequence_table_column_value_pair
                    )

                    # Inserting values of sequence in DB
                    insert_sequence_instance_values_to_sequence_table(
                        sequence_table_column_value_dict
                    )

                    # Create new exit sequence
                    new_exit_sequence_obj = Sequence(*new_exit_sequence_values)

                    # Add new exit sequence to global ladder object
                    variables.map_ladder_id_to_ladder_obj[
                        ladder_id
                    ].exit_sequences.append(new_exit_sequence_obj)

                    # Get sequence id for sequence
                    new_exit_sequence_id = new_exit_sequence_values[0]

                    # Place order only if status is active
                    if ladder_status == "Active":
                        # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
                        if (
                            bypass_rm_check == "False"
                            and variables.flag_enable_rm_account_rules
                            and variables.flag_account_liquidation_mode[
                                ladder_account_id
                            ]
                        ):
                            time.sleep(variables.rm_checks_interval_if_failed)

                            # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
                            if (
                                bypass_rm_check == "False"
                                and variables.flag_enable_rm_account_rules
                                and variables.flag_account_liquidation_mode[
                                    ladder_account_id
                                ]
                            ):
                                # Pause ladder
                                self.pause_scale_trade(selected_item=ladder_id)

                            else:
                                # Place order for new exit sequence
                                self.place_order_for_sequence(
                                    new_exit_sequence_obj,
                                    "Exit",
                                    ladder_obj,
                                    ladder_id,
                                    unique_id,
                                    ladder_account_id,
                                    bypass_rm_check,
                                    flag_use_execution_engine,
                                )

                                # Provide time sleep
                                time.sleep(0.5)

                        elif not trade_level_rm_check_result(
                            bypass_rm_check, unique_id
                        ):
                            time.sleep(variables.rm_checks_interval_if_failed)

                            if not trade_level_rm_check_result(
                                bypass_rm_check, unique_id
                            ):
                                # Pause ladder
                                self.pause_scale_trade(selected_item=ladder_id)

                            else:
                                # Place order for new exit sequence
                                self.place_order_for_sequence(
                                    new_exit_sequence_obj,
                                    "Exit",
                                    ladder_obj,
                                    ladder_id,
                                    unique_id,
                                    ladder_account_id,
                                    bypass_rm_check,
                                    flag_use_execution_engine,
                                )

                                # Provide time sleep
                                time.sleep(0.5)

                        else:
                            # Place order for new exit sequence
                            self.place_order_for_sequence(
                                new_exit_sequence_obj,
                                "Exit",
                                ladder_obj,
                                ladder_id,
                                unique_id,
                                ladder_account_id,
                                bypass_rm_check,
                                flag_use_execution_engine,
                            )

                            # Provide time sleep
                            time.sleep(0.5)

                    # Dict of values to update in sequence db table
                    update_sequence_values_dict = {"Status": "Active"}

                    # Update sequence db table values
                    update_sequence_table_values(
                        new_exit_sequence_id, update_sequence_values_dict
                    )
                ######
                # Code for adding next entry sequence order
                # Index for next entry sequence to be active
                index_of_next_entry_sequence_to_activate = (
                    index_of_active_entry_sequence + 1
                )

                # Check if filled entry order was not last in sequence and place order for next entry sequence
                if index_of_next_entry_sequence_to_activate < len(
                    ladder_obj.entry_sequences
                ):
                    # Get next entry sequence obj to be activate
                    next_entry_sequence_object = ladder_obj.entry_sequences[
                        index_of_next_entry_sequence_to_activate
                    ]

                    # Get sequence Id for
                    sequence_id_for_next_active_entry_sequence = (
                        next_entry_sequence_object.sequence_id
                    )

                    # Dict to update ladder db table values
                    update_sequence_values_dict = {"Status": "Active"}

                    # Update sequence db table values
                    update_sequence_table_values(
                        sequence_id_for_next_active_entry_sequence,
                        update_sequence_values_dict,
                    )

                    # Place order only if status is active
                    if ladder_status == "Active":
                        # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
                        if (
                            bypass_rm_check == "False"
                            and variables.flag_enable_rm_account_rules
                            and variables.flag_account_liquidation_mode[
                                ladder_account_id
                            ]
                        ):
                            time.sleep(variables.rm_checks_interval_if_failed)

                            # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
                            if (
                                bypass_rm_check == "False"
                                and variables.flag_enable_rm_account_rules
                                and variables.flag_account_liquidation_mode[
                                    ladder_account_id
                                ]
                            ):
                                # Pause ladder
                                self.pause_scale_trade(selected_item=ladder_id)

                            else:
                                # Place order for active sequence
                                self.place_order_for_sequence(
                                    next_entry_sequence_object,
                                    "Entry",
                                    ladder_obj,
                                    ladder_id,
                                    unique_id,
                                    ladder_account_id,
                                    bypass_rm_check,
                                    flag_use_execution_engine,
                                )

                                # Provide time sleep
                                time.sleep(0.5)

                        elif not trade_level_rm_check_result(
                            bypass_rm_check, unique_id
                        ):
                            time.sleep(variables.rm_checks_interval_if_failed)

                            if not trade_level_rm_check_result(
                                bypass_rm_check, unique_id
                            ):
                                # Pause ladder
                                self.pause_scale_trade(selected_item=ladder_id)

                            else:
                                # Place order for active sequence
                                self.place_order_for_sequence(
                                    next_entry_sequence_object,
                                    "Entry",
                                    ladder_obj,
                                    ladder_id,
                                    unique_id,
                                    ladder_account_id,
                                    bypass_rm_check,
                                    flag_use_execution_engine,
                                )

                                # Provide time sleep
                                time.sleep(0.5)

                        else:
                            # Place order for active sequence
                            self.place_order_for_sequence(
                                next_entry_sequence_object,
                                "Entry",
                                ladder_obj,
                                ladder_id,
                                unique_id,
                                ladder_account_id,
                                bypass_rm_check,
                                flag_use_execution_engine,
                            )

                            # Provide time sleep
                            time.sleep(0.5)

                    # Updating sequence object which is present in ladder object
                    next_entry_sequence_object.status = "Active"

                    # Overwrite changes to sequences obj
                    variables.map_ladder_id_to_ladder_obj[ladder_id].entry_sequences[
                        index_of_next_entry_sequence_to_activate
                    ] = next_entry_sequence_object

                # Check if filled entry order was last in sequence and mark it as completed
                elif (
                    index_of_next_entry_sequence_to_activate
                    >= len(ladder_obj.entry_sequences)
                    and ladder_take_profit_buffer == "None"
                ):
                    try:
                        # Get ladder total quantity
                        ladder_total_quantity = float(
                            get_ladder_or_sequence_column_value_from_db(
                                ladder_id=ladder_id,
                                column_name_as_in_db="Total Quantity",
                            )
                        )
                        ladder_entry_quantity_filled = float(
                            get_ladder_or_sequence_column_value_from_db(
                                ladder_id=ladder_id,
                                column_name_as_in_db="Entry Quantity Filled",
                            )
                        )

                    except Exception as e:
                        # Print to console
                        if variables.flag_debug_mode:
                            print(
                                f"For Sequence ID: {sequence_id}, Could not convert value of total quantity and entry qauntity filled to float"
                            )

                    # check if total quantity is filled for both entry and exit orders
                    if ladder_total_quantity == ladder_entry_quantity_filled:
                        # Terminate ladder
                        self.mark_scale_trade_as_completed(selected_item=ladder_id)
            else:
                # Get values in table for ladder id
                values = self.scale_trader_table.item(
                    ladder_id, "values"
                )  # get the values of the selected row

                # Get qauntity of exit order filled
                exit_quantity_filled = ladder_obj.exit_quantity_filled

                # Calculate updted exit quanity filled
                updated_exit_quantity_filled = int(float(exit_quantity_filled)) + int(
                    float(quantity_of_filled_order)
                )

                # Dict to update ladder db table values
                update_ladder_values_dict = {
                    "Exit Quantity Filled": updated_exit_quantity_filled
                }

                # Update ladder db table values
                update_ladder_table_values(ladder_id, update_ladder_values_dict)

                # Update exit quanity filled in scale trade dataframe
                variables.scale_trade_table_dataframe.loc[
                    variables.scale_trade_table_dataframe["Ladder ID"] == ladder_id,
                    "Exit Quantity Filled",
                ] = updated_exit_quantity_filled

                # Update local and global ladder obj exit quanity filled attribute
                ladder_obj.exit_quantity_filled = updated_exit_quantity_filled
                variables.map_ladder_id_to_ladder_obj[
                    ladder_id
                ].exit_quantity_filled = updated_exit_quantity_filled

                # Get exit sequence that must be activate
                index_of_active_exit_sequence = self.get_active_sequence(
                    ladder_obj.exit_sequences
                )

                # Get sequence object
                sequence_obj = ladder_obj.exit_sequences[index_of_active_exit_sequence]

                # Dict to update ladder db table values
                update_sequence_values_dict = {
                    "Order Sent Time": filled_order_details["Last Update Time"],
                    "Last Update Time": filled_order_details["Last Update Time"],
                    "Filled Quantity": quantity_of_filled_order,
                    "Status": "Filled",
                }

                # Update sequence db table values
                update_sequence_table_values(
                    str(sequence_id), update_sequence_values_dict
                )

                # Updating sequence object which is present in ladder object
                sequence_obj.status = "Filled"
                sequence_obj.order_sent_time = filled_order_details["Last Update Time"]
                sequence_obj.last_update_time = filled_order_details["Last Update Time"]
                sequence_obj.filled_quantity = quantity_of_filled_order

                # Overwrite changes to sequences obj
                variables.map_ladder_id_to_ladder_obj[ladder_id].exit_sequences[
                    index_of_active_exit_sequence
                ] = sequence_obj

                try:
                    # Get ladder total quantity
                    ladder_total_quantity = float(
                        get_ladder_or_sequence_column_value_from_db(
                            ladder_id=ladder_id, column_name_as_in_db="Total Quantity"
                        )
                    )
                    ladder_entry_quantity_filled = float(
                        get_ladder_or_sequence_column_value_from_db(
                            ladder_id=ladder_id,
                            column_name_as_in_db="Entry Quantity Filled",
                        )
                    )

                except Exception as e:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"For Sequence ID: {sequence_id}, Could not convert value of total quantity and entry qauntity filled to float"
                        )

                # check if total quantity is filled for both entry and exit orders
                if (
                    ladder_total_quantity == ladder_entry_quantity_filled
                    and ladder_total_quantity == updated_exit_quantity_filled
                    and ladder_obj.take_profit_behaviour == "Continue"
                ):
                    # Terminate ladder
                    self.mark_scale_trade_as_completed(selected_item=ladder_id)
                    # self.terminate_scale_trade(selected_item=ladder_id)

                # check if take profit behavious is terminate
                if ladder_obj.take_profit_behaviour == "Terminate":
                    # Terminate ladder
                    self.terminate_scale_trade(selected_item=ladder_id)

                # check if take profit behavious is restart
                elif ladder_obj.take_profit_behaviour == "Restart":
                    flag_execution_engine = get_ladder_or_sequence_column_value_from_db(
                        ladder_id=ladder_id, column_name_as_in_db="Execution Engine"
                    )

                    # Terminate ladder
                    self.terminate_scale_trade(selected_item=ladder_id)

                    # get values of terminated ladder
                    unique_id = ladder_obj.unique_id
                    action = ladder_obj.action
                    order_type = ladder_obj.order_type
                    total_quantity = ladder_obj.total_quantity
                    initial_quantity = ladder_obj.initial_quantity
                    subsequent_quantity = ladder_obj.subsequent_quantity
                    number_of_buckets = ladder_obj.number_of_buckets
                    initial_entry_price = ladder_obj.initial_entry_price
                    delta_price = ladder_obj.delta_price
                    price_movement = ladder_obj.price_movement
                    take_profit_buffer = ladder_obj.take_profit_buffer
                    take_profit_behaviour = ladder_obj.take_profit_behaviour
                    account_id = ladder_obj.account_id
                    old_ladder_id = ladder_obj.ladder_id

                    # Get recent ladder id
                    ladder_id = copy.deepcopy(variables.ladder_id)

                    # get boolean value for execution engine flag
                    if flag_execution_engine == "True":
                        flag_execution_engine = True

                    else:
                        flag_execution_engine = False

                    if delta_price not in ["None", None]:
                        # replicate ladder and sequences
                        create_ladder_and_sequences(
                            unique_id,
                            action,
                            order_type,
                            total_quantity,
                            initial_quantity,
                            subsequent_quantity,
                            number_of_buckets,
                            initial_entry_price,
                            delta_price,
                            price_movement,
                            take_profit_buffer,
                            take_profit_behaviour,
                            account_id,
                            bypass_rm_check,
                            flag_execution_engine,
                        )

                    else:
                        try:
                            data_dict = self.get_range_order_data(
                                unique_id, flag_range=False, flag_hide_pop_up=True
                            )

                            # convert thighest and lowest values to float
                            highest_price_val = float(data_dict["Highest Price"])

                            lowest_price_val = float(data_dict["Lowest Price"])

                            # get seuqneces df
                            sequence_df = get_sequences_for_ladder(old_ladder_id)

                            # Renaming columns in the DataFrame
                            sequence_df = sequence_df.rename(
                                columns={"Quantity": "#Lots"}
                            )

                            sequence_df = sequence_df[["Percentage", "#Lots"]]

                            # convert column to int
                            sequence_df["Percentage"] = sequence_df[
                                "Percentage"
                            ].astype(float)

                            # conevert lots to integer
                            sequence_df["#Lots"] = sequence_df["#Lots"].astype(int)

                            # Calculate price based on percentage
                            sequence_df["Price"] = lowest_price_val + (
                                sequence_df["Percentage"]
                                * (highest_price_val - lowest_price_val)
                                / 100
                            )

                            # get initial entry price
                            initial_entry_price = sequence_df["Price"].to_list()[0]

                            # get schedule data
                            data_dict["Highest Price"] = highest_price_val

                            data_dict["Lowest Price"] = lowest_price_val

                            data_dict["Percentage Lots Pair"] = sequence_df

                            # replicate ladder and sequences
                            create_ladder_and_sequences(
                                unique_id,
                                action,
                                order_type,
                                total_quantity,
                                initial_quantity,
                                subsequent_quantity,
                                number_of_buckets,
                                initial_entry_price,
                                delta_price,
                                price_movement,
                                take_profit_buffer,
                                take_profit_behaviour,
                                account_id,
                                bypass_rm_check,
                                flag_execution_engine,
                                data_dict,
                            )

                        except Exception as e:
                            if True or variables.flag_debug_mode:
                                print(
                                    f"Exception while restarting range schedule orders, Exp: {e}"
                                )

                    # Update scale trade GUI table
                    self.update_scale_trader_table()

                    # Resume ladder
                    self.resume_scale_trade(selected_item=ladder_id)

            # Update scale trade GUI table
            self.update_scale_trader_table()
        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Exception inside 'update_scale_trade_after_order_filled', Exp :{e}"
                )

    # Update scale trader GUI table
    def update_scale_trader_table(self):
        # All the Unique IDs in the System
        # Get scale trade dataframe
        local_scale_trade_table_dataframe = copy.deepcopy(
            variables.scale_trade_table_dataframe
        )

        # Get all item IDs in the Treeview
        item_ids = self.scale_trader_table.get_children()

        # Delete each item from the Treeview
        for item_id in item_ids:
            self.scale_trader_table.delete(item_id)

        try:
            # All the Unique IDs in the System
            all_unique_ids_in_system = local_scale_trade_table_dataframe[
                "Unique ID"
            ].tolist()

            # Get uniques ids for watchlist
            try:
                # Get all the unique ids
                if variables.selected_watchlist == "ALL":
                    all_unique_ids_in_watchlist = all_unique_ids_in_system
                # Get unique ids permitted in watchlist
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

            # Update datafrmae based on unique id present in watchlist
            local_scale_trade_table_dataframe = local_scale_trade_table_dataframe[
                local_scale_trade_table_dataframe["Unique ID"].isin(
                    all_unique_ids_in_watchlist
                )
            ]

            # Update the rows
            for i, row_val in local_scale_trade_table_dataframe.iterrows():
                """# Unique ID of row val
                unique_id = int(float(row_val['Unique ID']))"""

                # Ladder Id of row val
                ladder_id = int(float(row_val["Ladder ID"]))

                # Tuple of vals
                row_val = tuple(row_val)

                # Insert it in the table
                self.scale_trader_table.insert(
                    "",
                    "end",
                    iid=ladder_id,
                    text="",
                    values=row_val,
                    tags=("oddrow",),
                )

            # All the rows in scale trade Table
            all_ladder_id_in_scale_trade_table = self.scale_trader_table.get_children()

            # Row counter
            counter_row = 0

            # Move According to data Color here, Change Color
            for i, row in local_scale_trade_table_dataframe.iterrows():
                # Ladder Id of row val
                ladder_id = str(row["Ladder ID"])

                # If unique_id in table
                if ladder_id in all_ladder_id_in_scale_trade_table:
                    self.scale_trader_table.move(ladder_id, "", counter_row)

                    if counter_row % 2 == 0:
                        self.scale_trader_table.item(ladder_id, tags="evenrow")
                    else:
                        self.scale_trader_table.item(ladder_id, tags="oddrow")

                    # Increase row count
                    counter_row += 1

        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print(f"Error Inside update_scale_trader_table, Exp: {e}")
