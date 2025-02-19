"""
Created on 18-Apr-2023

@author: Karan
"""

import copy
import time
import tkinter

from com import *
from com.variables import *
from com.combination_helper import *
from com.utilities import *
from com.mysql_io import *
from com.json_io_custom_columns import *
from com.mysql_io_filter_tab import *
from tkinter import *
from com.scale_trade_helper import is_float
from com.json_io_leg_to_combo_columns import *


class ScreenCAS(object):
    def __init__(self, master_notebook):
        """
        Constructor
        """
        self.notebook = master_notebook

        self.cas_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.cas_tab, text="   C. A. S.    ")
        self.create_cas_table()

        self.create_cas_condition_status_table()

    # Method to create CAS table
    def create_cas_table(self):
        # Create Treeview Frame for active combo table
        cas_table_frame = ttk.Frame(self.cas_tab, padding=10)
        cas_table_frame.pack(pady=10)
        cas_table_frame.pack(fill="both", expand=True)

        # Place in center
        cas_table_frame.place(relx=0.5, anchor=tk.N)
        cas_table_frame.place(y=10, width=1600)

        # Treeview Scrollbar
        tree_scroll_y = Scrollbar(cas_table_frame)
        tree_scroll_y.pack(side="right", fill="y")

        # Treeview Scrollbar
        tree_scroll_x = Scrollbar(cas_table_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        # Create Treeview
        self.cas_table = ttk.Treeview(
            cas_table_frame,
            yscrollcommand=tree_scroll_y.set,
            xscrollcommand=tree_scroll_x.set,
            height=12,
            selectmode="extended",
        )

        # Pack to the screen
        self.cas_table.pack(expand=True, fill="both")

        # Configure the scrollbar
        tree_scroll_y.config(command=self.cas_table.yview)

        # Configure the scrollbar
        tree_scroll_x.config(command=self.cas_table.xview)

        # CAS LongTerm Days
        cas_n_days = variables.cas_number_of_days

        # ATR Days
        n_day_atr = variables.atr_number_of_days

        # Get secondary columns mapped to expression dictionary
        local_map_secondary_columns_to_expression_in_cas_table = copy.deepcopy(
            variables.map_secondary_columns_to_expression_in_cas_table
        )

        # Get secondary columns
        secondary_columns_in_cas_table = list(
            local_map_secondary_columns_to_expression_in_cas_table.keys()
        )

        # Column in order book table
        self.cas_table["columns"] = (
            variables.cas_table_columns + secondary_columns_in_cas_table
        )

        # Creating Columns
        self.cas_table.column("#0", width=0, stretch="no")

        for column_name, column_heading in variables.cas_table_columns_name_heading:
            if column_name == "Tickers":
                self.cas_table.column(
                    column_name, anchor="center", width=125, minwidth=125
                )
            else:
                self.cas_table.column(
                    column_name, anchor="center", width=85, minwidth=85
                )

        # Iterate secondary columns
        for column_name in secondary_columns_in_cas_table:
            # Adding column to table
            self.cas_table.column(column_name, anchor="center", width=85, minwidth=85)

        # Create Headings
        self.cas_table.heading("#0", text="\n", anchor="center")

        for column_name, column_heading in variables.cas_table_columns_name_heading:
            self.cas_table.heading(column_name, text=column_heading, anchor="center")

        # Iterate secondary columns
        for column_heading in secondary_columns_in_cas_table:
            # Adding column to table
            self.cas_table.heading(column_heading, text=column_heading, anchor="center")

        # Back ground
        self.cas_table.tag_configure("oddrow", background="white")
        self.cas_table.tag_configure("evenrow", background="lightblue")

        # Right Click bind
        self.cas_table.bind("<Button-3>", self.cas_table_right_click)

        # Bind the sort_treeview function to the TreeviewColumnHeader event for each column
        for column in self.cas_table["columns"]:
            self.cas_table.heading(
                column, command=lambda c=column: self.sort_cas_table(c, False)
            )

    # Method to update cas table for secondary column
    def update_cas_tale_gui(self):
        # Get secondary columns mapped to expression dictionary
        local_map_secondary_columns_to_expression_in_cas_table = copy.deepcopy(
            variables.map_secondary_columns_to_expression_in_cas_table
        )

        # Get secondary columns
        secondary_columns_in_cas_table = list(
            local_map_secondary_columns_to_expression_in_cas_table.keys()
        )

        # Column in order book table
        self.cas_table["columns"] = (
            variables.cas_table_columns + secondary_columns_in_cas_table
        )

        # Creating Columns
        self.cas_table.column("#0", width=0, stretch="no")

        for column_name, column_heading in variables.cas_table_columns_name_heading:
            if column_name == "Tickers":
                self.cas_table.column(
                    column_name, anchor="center", width=125, minwidth=125
                )
            else:
                self.cas_table.column(
                    column_name, anchor="center", width=85, minwidth=85
                )

        # Iterate secondary columns
        for column_name in secondary_columns_in_cas_table:
            # Adding column to table
            self.cas_table.column(column_name, anchor="center", width=85, minwidth=85)

        # Create Headings
        self.cas_table.heading("#0", text="\n", anchor="center")

        for column_name, column_heading in variables.cas_table_columns_name_heading:
            self.cas_table.heading(column_name, text=column_heading, anchor="center")

        # Iterate secondary columns
        for column_heading in secondary_columns_in_cas_table:
            # Adding column to table
            self.cas_table.heading(column_heading, text=column_heading, anchor="center")

    # Method to cas condition table
    def create_cas_condition_status_table(
        self,
    ):
        # Create Treeview Frame for active combo table
        cas_condition_table_frame = ttk.Frame(self.cas_tab, padding=10)
        cas_condition_table_frame.pack(pady=10)
        cas_condition_table_frame.pack(fill="both", expand=True)

        # Place in center
        cas_condition_table_frame.place(relx=0.5, anchor=tk.N)
        cas_condition_table_frame.place(y=370, width=1600)  # KARAN CHANGE 260
        # cas_condition_table_frame.pack(fill="both", expand=True)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(cas_condition_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Treeview Scrollbar
        tree_scroll_x = Scrollbar(cas_condition_table_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        # Create Treeview
        self.cas_condition_table = ttk.Treeview(
            cas_condition_table_frame,
            yscrollcommand=tree_scroll.set,
            xscrollcommand=tree_scroll_x.set,
            height=11,  # KARAN CHANGE 19
            selectmode="extended",
        )

        # Pack to the screen
        # self.cas_condition_table.pack()
        self.cas_condition_table.pack(fill="both", expand=True)

        # Configure the scrollbar
        tree_scroll.config(command=self.cas_condition_table.yview)

        # Configure the scrollbar
        tree_scroll_x.config(command=self.cas_condition_table.xview)

        # CAS LongTerm Days
        cas_n_days = variables.cas_number_of_days

        # Column in order book table
        self.cas_condition_table["columns"] = variables.cas_condition_table_columns

        # Creating Columns
        self.cas_condition_table.column("#0", width=0, stretch="no")
        self.cas_condition_table.column(
            "Unique ID",
            anchor="center",
            width=108,
        )
        self.cas_condition_table.column(
            "Trading Combo Unique ID",
            anchor="center",
            width=108,
        )
        self.cas_condition_table.column(
            "Evaluation Unique ID",
            anchor="center",
            width=108,
        )
        self.cas_condition_table.column("Add/Switch", anchor="center", width=108)
        self.cas_condition_table.column(
            "Incremental Tickers", anchor="center", width=312
        )
        self.cas_condition_table.column("Condition", anchor="center", width=108)
        self.cas_condition_table.column("Reference Price", anchor="center", width=108)
        self.cas_condition_table.column(
            "Reference Position", anchor="center", width=108
        )
        self.cas_condition_table.column("Target Position", anchor="center", width=108)
        self.cas_condition_table.column("Trigger Price", anchor="center", width=108)
        self.cas_condition_table.column(f"Status", anchor="center", width=108)
        self.cas_condition_table.column(
            f"Reason For Failed", anchor="center", width=200
        )
        self.cas_condition_table.column(f"Correlation", anchor="center", width=108)
        self.cas_condition_table.column(f"Account ID", anchor="center", width=108)
        self.cas_condition_table.column(f"Execution Engine", anchor="center", width=108)
        self.cas_condition_table.column(f"Series ID", anchor="center", width=108)
        self.cas_condition_table.column(
            f"Table ID Column", anchor="center", width=0, stretch="no"
        )

        # Create Headings
        self.cas_condition_table.heading("#0", text="\n", anchor="w")
        self.cas_condition_table.heading("Unique ID", text="Unique ID", anchor="center")
        self.cas_condition_table.heading(
            "Trading Combo Unique ID",
            text="Trading Combo\n     Unique ID",
            anchor="center",
        )
        self.cas_condition_table.heading(
            "Evaluation Unique ID", text="Evaluation\nUnique ID", anchor="center"
        )
        self.cas_condition_table.heading(
            "Add/Switch", text="Add/Switch", anchor="center"
        )
        self.cas_condition_table.heading(
            "Incremental Tickers", text="Incremental Tickers", anchor="center"
        )
        self.cas_condition_table.heading(
            "Condition",
            text="Condition",
            anchor="center",
        )
        self.cas_condition_table.heading(
            "Reference Price",
            text="Reference Price",
            anchor="center",
        )
        self.cas_condition_table.heading(
            "Reference Position",
            text="Reference Position",
            anchor="center",
        )
        self.cas_condition_table.heading(
            "Target Position",
            text="Target Position",
            anchor="center",
        )
        self.cas_condition_table.heading(
            "Trigger Price",
            text="Trigger Price",
            anchor="center",
        )
        self.cas_condition_table.heading(f"Status", text=f"Status", anchor="center")
        self.cas_condition_table.heading(
            f"Reason For Failed", text=f"Failure Reason", anchor="center"
        )
        self.cas_condition_table.heading(
            f"Correlation", text=f"Correlation", anchor="center"
        )
        self.cas_condition_table.heading(
            f"Account ID", text=f"Account ID", anchor="center"
        )
        self.cas_condition_table.heading(
            f"Execution Engine", text=f"Execution Engine", anchor="center"
        )
        self.cas_condition_table.heading(
            f"Series ID", text=f"Series ID", anchor="center"
        )
        self.cas_condition_table.heading(
            f"Table ID Column", text=f"Table ID Column", anchor="center"
        )

        # Back ground
        self.cas_condition_table.tag_configure("oddrow", background="white")
        self.cas_condition_table.tag_configure("evenrow", background="lightblue")

        # Right Click bind
        self.cas_condition_table.bind(
            "<Button-3>", self.cas_condition_table_right_click
        )

        # create purge button
        purge_cas_conditions_button = ttk.Button(
            self.cas_tab,
            text="Purge Cas Conditions",
            command=lambda: self.purge_cas_conditions(),
        )
        purge_cas_conditions_button.pack()
        purge_cas_conditions_button.place(relx=0.5, anchor=tk.N)
        purge_cas_conditions_button.place(y=730)

        # create purge button
        edit_leg_to_combo_columns_button = ttk.Button(
            self.cas_tab,
            text="Edit Leg-to-Combo Columns",
            command=lambda: self.edit_leg_to_combo_columns(),
        )
        edit_leg_to_combo_columns_button.pack()
        edit_leg_to_combo_columns_button.place(relx=0.06, anchor=tk.N)
        edit_leg_to_combo_columns_button.place(y=730)

    # Method to organize leg-to-combo table columns
    def edit_leg_to_combo_columns(self):
        # Get current session accounts
        local_current_session_columns = copy.deepcopy(
            variables.cas_table_columns_name_heading
        )

        local_current_session_columns = [
            column_name
            for (column_name, column_heading) in local_current_session_columns
        ]

        try:
            all_columns_in_system = (
                local_current_session_columns  # list of all columns in System
            )

            if len(local_current_session_columns) < 1:
                raise Exception("No Account ID")

        except Exception as e:
            error_title = f"Error, No column Found"
            error_string = f"Please try after adding an column."

            variables.screen.display_error_popup(error_title, error_string)
            return

        # get columns present in json file
        local_columns_selected = get_all_custom_ltc_columns_from_json()

        # Create a popup window
        edit_popup_frame = tk.Toplevel()

        # Title for pop up
        edit_popup_frame_title = f"Edit Columns"

        edit_popup_frame.title(edit_popup_frame_title)

        width_of_pop_up = 850  # Minimum width for pop up
        height_of_pop_up = 400

        # Geometry
        edit_popup_frame.geometry(
            f"{width_of_pop_up}x{height_of_pop_up}"
        )  # Make the size dynamic (Number UID in system, Row in a single row) min() dynamic

        # frame table for the columns not in crrent time
        pop_up_frame = ttk.Frame(edit_popup_frame, padding=0)
        pop_up_frame.pack(fill="both", expand=True)

        # frame table for the columns not in current file
        table_of_non_selected_columns_frame = ttk.Frame(pop_up_frame, padding=0)
        table_of_non_selected_columns_frame.grid(
            column=1, row=1, rowspan=3, padx=25, pady=5
        )

        # frame table for the buttons to move combo through tables
        table_of_buttons_frame = ttk.Frame(pop_up_frame, padding=0)
        table_of_buttons_frame.grid(column=2, row=1, padx=5, pady=5)

        # frame table for columns in json file
        table_of_selected_columns_frame = ttk.Frame(pop_up_frame, padding=0)
        table_of_selected_columns_frame.grid(
            column=3, row=1, rowspan=3, padx=25, pady=5
        )

        # frame table for columns in json file
        labels_of_non_selected_table_frame = ttk.Frame(pop_up_frame, padding=0)
        labels_of_non_selected_table_frame.grid(column=1, row=0, padx=5, pady=[25, 0])

        # frame table for columns in json file
        labels_of_selected_table_frame = ttk.Frame(pop_up_frame, padding=0)
        labels_of_selected_table_frame.grid(column=3, row=0, padx=5, pady=[25, 0])

        # Treeview Scrollbar
        tree_scroll = Scrollbar(table_of_non_selected_columns_frame)
        tree_scroll.pack(side="right", fill="y")

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            labels_of_non_selected_table_frame,
            text="Non Selected Columns",
            font=("Arial", 12),
        ).grid(column=1, row=0, padx=5, pady=[5, 5])

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            labels_of_selected_table_frame,
            text="Selected Columns",
            font=("Arial", 12),
        ).grid(column=2, row=0, padx=[0, 0], pady=[5, 5])

        # Create Treeview
        self.treeview_non_selected_columns = ttk.Treeview(
            table_of_non_selected_columns_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
        )

        # Pack to the screen
        self.treeview_non_selected_columns.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.treeview_non_selected_columns.yview)

        columns_in_non_selected_columns_table = ("Account ID",)

        # Define Our Columns
        self.treeview_non_selected_columns["columns"] = (
            columns_in_non_selected_columns_table
        )

        # First Column hiding it
        self.treeview_non_selected_columns.column("#0", width=0, stretch="no")
        self.treeview_non_selected_columns.column(
            "Account ID", anchor="center", width=320
        )

        # Defining headings for table
        self.treeview_non_selected_columns.heading("#0", text="", anchor="center")
        self.treeview_non_selected_columns.heading(
            "Account ID", text="Account ID", anchor="center"
        )

        self.treeview_non_selected_columns.tag_configure("oddrow", background="white")
        self.treeview_non_selected_columns.tag_configure(
            "evenrow", background="lightblue"
        )

        # Method to transfer selcted column to selcted table
        def on_click_transfer_column_to_selected():
            try:
                # Get columns for selected row
                selected_item = (
                    self.treeview_non_selected_columns.selection()
                )  # get the item ID of the selected row

                # Transfer selected columns from non selected table to selected table
                for item in selected_item:
                    local_columns_selected.append(item)

                # Update tables
                fill_non_selected_columns_table(
                    local_current_session_columns, local_columns_selected
                )
                fill_selected_columns_table(
                    local_current_session_columns, local_columns_selected
                )

            except Exception as e:
                if variables.flag_debug_mode:
                    print(
                        f"Error inside transferring Account id to selected Account ids table, is {e}"
                    )

        # Method to transefer selected column to non selected tabel
        def on_click_transfer_column_to_non_selected():
            try:
                # Get unique ids for selected row
                selected_item = (
                    self.treeview_selected_columns.selection()
                )  # get the item ID of the selected row

                # Transfer selected unique ids from selected table to non selected table
                for item in selected_item:
                    local_columns_selected.remove(item)

                # Update tables
                fill_non_selected_columns_table(
                    local_current_session_columns, local_columns_selected
                )
                fill_selected_columns_table(
                    local_current_session_columns, local_columns_selected
                )
            except Exception as e:
                if variables.flag_debug_mode:
                    print(
                        f"Error inside transferring Account id to non selected Account ids table, is {e}"
                    )

        # Method to edit list of columns
        def edit_list_of_column_for_watchlist():
            # Get all selected column which is present in selected table
            all_selected_columns = local_columns_selected

            if len(all_selected_columns) == 0:
                error_title = f"Error, Can not save empty columns list"
                error_string = f"Error, Can not save empty columns list"

                variables.screen.display_error_popup(error_title, error_string)
                return

            # Convert the list to a comma-separated string
            result_string = ",".join(all_selected_columns)

            add_custom_ltc_column_in_json(result_string)

            edit_popup_frame.destroy()

            return

        # Button to move selected columns to selected
        transfer_column_to_select = ttk.Button(
            table_of_buttons_frame,
            text=">>",
            command=lambda: on_click_transfer_column_to_selected(),
        )
        transfer_column_to_select.grid(row=1, column=1, pady=35)

        # Button to move selected columns to non-selected
        transfer_column_to_non_selected = ttk.Button(
            table_of_buttons_frame,
            text="<<",
            command=lambda: on_click_transfer_column_to_non_selected(),
        )
        transfer_column_to_non_selected.grid(row=2, column=1, pady=35)

        # Button to save selected columns to json file
        edit_account_group_button = ttk.Button(
            table_of_buttons_frame,
            text="Save",
            command=lambda: edit_list_of_column_for_watchlist(),
        )
        edit_account_group_button.grid(row=3, column=1, pady=35)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(table_of_selected_columns_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.treeview_selected_columns = ttk.Treeview(
            table_of_selected_columns_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
        )

        # Pack to the screen
        self.treeview_selected_columns.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.treeview_selected_columns.yview)

        columns_in_selected_columns_table = ("Account ID",)

        # Define Our Columns
        self.treeview_selected_columns["columns"] = columns_in_selected_columns_table

        # First Column hiding it
        self.treeview_selected_columns.column("#0", width=0, stretch="no")
        self.treeview_selected_columns.column("Account ID", anchor="center", width=320)

        self.treeview_selected_columns.heading("#0", text="", anchor="center")
        self.treeview_selected_columns.heading(
            "Account ID", text="Account ID", anchor="center"
        )

        self.treeview_selected_columns.tag_configure("oddrow", background="white")
        self.treeview_selected_columns.tag_configure("evenrow", background="lightblue")

        # Method to fill non slected table
        def fill_non_selected_columns_table(
            local_current_session_columns, local_columns_selected
        ):
            try:
                # Get all item IDs in the Treeview
                item_ids = self.treeview_non_selected_columns.get_children()

                # Delete each item from the Treeview
                for item_id in item_ids:
                    self.treeview_non_selected_columns.delete(item_id)

                # Getting columns which are not in json file
                columns_not_in_selected = [
                    column
                    for column in local_current_session_columns
                    if column not in local_columns_selected
                ]

                # Get the current number of items in the treeview
                num_items = len(columns_not_in_selected)

                # Iterate through selected columns
                for column in columns_not_in_selected:
                    values = (column,)

                    if num_items % 2 == 1:
                        self.treeview_non_selected_columns.insert(
                            "",
                            "end",
                            iid=column,
                            text=num_items + 1,
                            values=values,
                            tags=("oddrow",),
                        )

                    else:
                        self.treeview_non_selected_columns.insert(
                            "",
                            "end",
                            iid=column,
                            text=num_items + 1,
                            values=values,
                            tags=("evenrow",),
                        )

                    num_items += 1
            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside fillling non selected tables data, is {e}")

        # Method to fill selecteed table
        def fill_selected_columns_table(
            local_current_session_columns, local_columns_selected
        ):
            try:
                # Get all item IDs in the Treeview
                item_ids = self.treeview_selected_columns.get_children()

                # Delete each item from the Treeview
                for item_id in item_ids:
                    self.treeview_selected_columns.delete(item_id)

                # Getting columns which are in json file
                columns_in_selected = [
                    column
                    for column in local_current_session_columns
                    if column in local_columns_selected
                ]

                # Get the current number of items in the treeview
                num_items = len(columns_in_selected)

                # Iterate through selected columns
                for column in columns_in_selected:
                    values = (column,)

                    if num_items % 2 == 1:
                        self.treeview_selected_columns.insert(
                            "",
                            "end",
                            iid=column,
                            text=num_items + 1,
                            values=values,
                            tags=("oddrow",),
                        )

                    else:
                        self.treeview_selected_columns.insert(
                            "",
                            "end",
                            iid=column,
                            text=num_items + 1,
                            values=values,
                            tags=("evenrow",),
                        )

                    num_items += 1
            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside fillling selected table's data, is {e}")

        fill_non_selected_columns_table(
            local_current_session_columns, local_columns_selected
        )
        fill_selected_columns_table(
            local_current_session_columns, local_columns_selected
        )

    # Method to delete account group
    def delete_account_group(self):
        group_id = self.accounts_group_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.accounts_group_table.item(
            group_id, "values"
        )  # get the values of the selected row

        # Get group id of selected row
        group_id = values[0]
        group_name = values[1]

        # check if selected group is Default group
        if group_id == "1" and group_name == "ALL":
            error_title = f"Error, Can not delete the default Account Group"
            error_string = f"The default Account Group can not be deleted."

            variables.screen.display_error_popup(error_title, error_string)
            return

        # Delete selected row
        delete_account_group_in_db(group_id)

        # Update table
        self.update_account_group_table()

        try:
            # Get all account groups
            account_group_df = get_all_account_groups_from_db()

            # Get account groups in list
            all_account_groups = account_group_df["Group Name"].to_list()

            # Remove "All" group
            all_account_groups.remove("ALL")

            # Sort account groups
            all_account_groups = sorted(all_account_groups)

            # Add "ALL" group at zero index
            all_account_groups = ["ALL"] + all_account_groups

            # Update account groups drop down
            self.account_group_drop_down["values"] = all_account_groups

            # Update account group drop down
            self.account_group_drop_down.set("ALL")

            # Get selected account group
            variables.selected_account_group = "ALL"

            # get account ids in account group
            variables.account_ids_list_of_selected_acount_group = ["ALL"]

            # Update order book
            variables.flag_orders_book_table_watchlist_changed = True
            variables.flag_positions_tables_watchlist_changed = True

            variables.screen.screen_position_obj.update_positions_table_watchlist_changed()
            variables.screen.update_orders_book_table_watchlist_changed()

        except Exception as e:
            all_account_groups = ["ALL"]

    # Method to remove all failed cas conditional orders
    def purge_cas_conditions(self):
        # Removing failed cas condition from  cas condition dataframe
        local_cas_condition_table_dataframe = variables.cas_condition_table_dataframe[
            variables.cas_condition_table_dataframe["Status"] == "Failed"
        ].copy()

        # Removing failed cas condition from  cas condition dataframe
        variables.cas_condition_table_dataframe = (
            variables.cas_condition_table_dataframe[
                variables.cas_condition_table_dataframe["Status"] == "Pending"
            ]
        )

        table_id_list_all = self.cas_condition_table.get_children()

        table_id_list = []

        for table_id in table_id_list_all:
            # get the item ID of the selected row
            values = self.cas_condition_table.item(table_id, "values")

            if values[10] == "Failed":
                table_id_list.append(table_id)

        for table_id in table_id_list:
            self.cas_condition_table.delete(table_id)

        purge_cas_conditions()

        # Removing failed cas condition from  cas condition dataframe
        variables.cas_condition_table_dataframe = (
            variables.cas_condition_table_dataframe[
                variables.cas_condition_table_dataframe["Status"] == "Pending"
            ]
        )

        self.update_cas_condition_table_watchlist_change()

        # print(variables.cas_condition_table_dataframe)

    # Method to insert cas row in GUI table
    def insert_cas_row_in_cas_table(self, value):
        # unique_id
        unique_id = value[0]

        # Get the current number of items in the treeview
        num_items = len(self.cas_table.get_children())

        if num_items % 2 == 1:
            self.cas_table.insert(
                "",
                "end",
                iid=unique_id,
                text=num_items + 1,
                values=value,
                tags=("oddrow",),
            )
        else:
            self.cas_table.insert(
                "",
                "end",
                iid=unique_id,
                text=num_items + 1,
                values=value,
                tags=("evenrow",),
            )

    # Method to insert row to cas condition table
    def insert_cas_condition_row_in_cas_condition_table(self, value):
        # unique_id
        unique_id = value[0]

        # table id column
        table_id = value[-1]

        # Get the current number of items in the treeview
        num_items = len(self.cas_condition_table.get_children())

        if num_items % 2 == 1:
            self.cas_condition_table.insert(
                "",
                "end",
                iid=table_id,
                text=num_items + 1,
                values=value,
                tags=("oddrow",),
            )
        else:
            self.cas_condition_table.insert(
                "",
                "end",
                iid=table_id,
                text=num_items + 1,
                values=value,
                tags=("evenrow",),
            )

    # Method to update cas condition row in cas condition table
    def update_cas_condition_row_in_cas_condition_table(self, table_id, value):
        self.cas_condition_table.item(table_id, value)

    # function to sort the cas_table
    def sort_cas_table(self, column, reverse):
        data = [
            (self.cas_table.set(child, column), child)
            for child in self.cas_table.get_children("")
        ]
        data = sorted(data, key=lambda val: custom_sort(val[0]), reverse=reverse)

        for counter_row, (_, unique_id) in enumerate(data):
            self.cas_table.move(unique_id, "", counter_row)

            if counter_row % 2 == 0:
                self.cas_table.item(unique_id, tags="evenrow")
            else:
                self.cas_table.item(unique_id, tags="oddrow")

        # Change the reverse flag
        self.cas_table.heading(
            column, command=lambda: self.sort_cas_table(column, not reverse)
        )

        # Change the Reverse Flag in variables Dict
        variables.cas_table_sort_by_column = {column: reverse}

    # Method to dispaly leg-to-combo comparison table
    def display_leg_to_combo_comparison_popup(self):
        # Unique ID
        selected_item = self.cas_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.cas_table.item(
            selected_item, "values"
        )  # get the values of the selected row
        unique_id = int(values[0])

        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

        # Making a local copy of the variable.map_unique_id_to_leg_combo_comparision_val
        local_unique_id_to_leg_combo_comparision_val = copy.deepcopy(
            variables.map_unique_id_to_leg_combo_comparision_val
        )

        # Initialize a empty tuple to store values for table
        leg_to_combo_values = list()

        # Show Error popup
        if unique_id not in local_unique_id_to_combo_obj:
            # Error Message
            error_title = error_string = (
                f"Error - UID: {unique_id} unable to find combination"
            )
            variables.screen.display_error_popup(error_title, error_string)
            return

        # Getting combo object for unique Id
        combo_obj = local_unique_id_to_combo_obj[unique_id]

        # Buy legs and Sell legs
        buy_legs = combo_obj.buy_legs
        sell_legs = combo_obj.sell_legs
        all_legs = buy_legs + sell_legs

        # Adding leg information in addition with leg-to-combo values
        for indx, leg_obj in enumerate(all_legs):
            row_value_list = [
                leg_obj.action,
                leg_obj.symbol,
                leg_obj.quantity,
                leg_obj.multiplier,
            ]

            try:
                # If we have value for unique id get the value for wach leg and append to the sub list
                if unique_id in local_unique_id_to_leg_combo_comparision_val:
                    hv_leg_to_combo = local_unique_id_to_leg_combo_comparision_val[
                        unique_id
                    ][f"Leg {indx + 1}"]["HV for leg to Combo Comparison"]
                    high_price_leg_to_combo = (
                        local_unique_id_to_leg_combo_comparision_val[unique_id][
                            f"Leg {indx + 1}"
                        ]["Highest price for leg to Combo Comparison"]
                    )
                    change_in_price_leg_to_combo = (
                        local_unique_id_to_leg_combo_comparision_val[unique_id][
                            f"Leg {indx + 1}"
                        ]["Change in Price for leg to Combo Comparison"]
                    )

                    # Appending the calculated value to the sub list
                    row_value_list.extend(
                        [
                            hv_leg_to_combo,
                            high_price_leg_to_combo,
                            change_in_price_leg_to_combo,
                        ]
                    )
                else:
                    # Append "N/A" if no data is present for the unique id
                    row_value_list.extend(
                        [
                            "N/A",
                            "N/A",
                            "N/A",
                        ]
                    )

            except Exception as e:
                # Append "N/A" if no data is present for the unique id
                row_value_list.extend(
                    [
                        "N/A",
                        "N/A",
                        "N/A",
                    ]
                )

            if variables.flag_debug_mode:
                print()

            # Adding leg information to leg to combo values
            leg_to_combo_values.append(row_value_list)

        # Columns to be added
        columns_for_leg_to_combo_comparision = (
            variables.columns_for_leg_to_combo_comparision
        )

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

        # Create a popup window with the table
        treeview_popup = tk.Toplevel()
        treeview_popup.title(f"Leg-to-Combo Comparison Details, Unique ID: {unique_id}")
        custom_height = min(max((1 * 20) + 100, 150), 210)

        # 25 row high,  20 * 2(padding)
        custom_width = (
            150 * len(columns_for_leg_to_combo_comparision) + 60
        )  # 60 = 20 * 2(padding) + 20(scrollbar)
        treeview_popup.geometry(f"{custom_width}x{custom_height}")

        # Create a frame for the input fields
        treeview_table_frame = ttk.Frame(treeview_popup, padding=20)
        treeview_table_frame.pack(fill="both", expand=True)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(treeview_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.treeview_table = ttk.Treeview(
            treeview_table_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
        )

        # Pack to the screen
        self.treeview_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.treeview_table.yview)

        # Define Our Columns
        self.treeview_table["columns"] = columns_for_leg_to_combo_comparision

        # First Column hiding it
        self.treeview_table.column("#0", width=0, stretch="no")
        self.treeview_table.heading("#0", text="", anchor="w")

        # Table Columns and Heading
        for indx, column_name in enumerate(columns_for_leg_to_combo_comparision):
            # Width for 1st 4 column 120 then 190
            width = 120 if indx < 4 else 190
            self.treeview_table.column(
                column_name, anchor="center", width=width, minwidth=width
            )
            self.treeview_table.heading(column_name, text=column_name, anchor="center")

        # Create striped row tags
        self.treeview_table.tag_configure("oddrow", background="white")
        self.treeview_table.tag_configure("evenrow", background="lightblue")

        # To use alternate style for row
        flag_for_row_style = True

        for row_value in leg_to_combo_values:
            # Combine the values into a tuple
            combined_tuple = tuple(row_value)
            if flag_for_row_style:
                # Inserting in the table
                self.treeview_table.insert(
                    parent="",
                    index="end",
                    text="",
                    values=combined_tuple,
                    tags=("evenrow",),
                )
                flag_for_row_style = False
            else:
                # Inserting in the table
                self.treeview_table.insert(
                    parent="",
                    index="end",
                    text="",
                    values=combined_tuple,
                    tags=("oddrow",),
                )
                flag_for_row_style = True

    # Method to define CAS table right click options
    def cas_table_right_click(self, event):
        # get the Treeview row that was clicked
        row = self.cas_table.identify_row(event.y)

        if row:
            # select the row
            self.cas_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.cas_table, tearoff=0)
            menu.add_command(
                label="View Details",
                command=lambda: variables.screen.display_combination_details("cas"),
            )
            menu.add_command(
                label="View Leg-Combo Comparison",
                command=lambda: self.display_leg_to_combo_comparison_popup(),
            )
            menu.add_command(
                label="Conditional Add",
                command=lambda: self.conditional_add_switch_legs("ADD"),
            )
            menu.add_command(
                label="Conditional Switch",
                command=lambda: self.conditional_add_switch_legs("SWITCH"),
            )
            menu.add_command(
                label="Conditional Buy",
                command=lambda: self.conditional_add_switch_legs("BUY"),
            )
            menu.add_command(
                label="Conditional Sell",
                command=lambda: self.conditional_add_switch_legs("SELL"),
            )
            menu.add_command(
                label="Conditional Buy Multi",
                command=lambda: self.conditional_add_switch_legs(
                    "BUY", flag_multi_account=True
                ),
            )
            menu.add_command(
                label="Conditional Sell Multi",
                command=lambda: self.conditional_add_switch_legs(
                    "SELL", flag_multi_account=True
                ),
            )
            menu.add_command(
                label="Conditional Series",
                command=lambda: self.create_conditional_series(),
            )

            menu.add_command(
                label="Conditional Series Multi",
                command=lambda: self.create_conditional_series(flag_multi=True),
            )

            menu.add_command(
                label="Custom Leg-to-Combo Table",
                command=lambda: self.create_custom_leg_to_combo_table(),
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    # Method to display leg-to-combo table
    def create_custom_leg_to_combo_table(self):
        # Unique ID
        selected_item = self.cas_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.cas_table.item(
            selected_item, "values"
        )  # get the values of the selected row
        unique_id = int(values[0])

        # N days High And Low
        long_term_high_low = copy.deepcopy(
            variables.map_unique_id_to_long_term_high_low
        )

        # HV Related Column
        hv_related_values = copy.deepcopy(variables.map_unique_id_to_hv_related_values)

        # Days Open, High Low
        intraday_open_high_low = copy.deepcopy(
            variables.map_unique_id_to_intraday_high_low
        )

        # Volume Related columns
        volume_related_column_values = copy.deepcopy(
            variables.map_unique_id_to_volume_related_fields
        )

        # Both Price and Volume Related columns
        support_resistance_and_relative_fields_values = copy.deepcopy(
            variables.map_unique_id_to_support_resistance_and_relative_fields
        )

        legs_uid_list = copy.deepcopy(
            variables.map_unique_id_to_legs_unique_id[unique_id]["Leg Unique Ids"]
        )

        combo_list = copy.deepcopy(
            variables.map_unique_id_to_legs_unique_id[unique_id]["Combo Obj List"]
        )

        legs_uid_list.append(unique_id)

        # Get combo obj
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)
        combo_obj = local_unique_id_to_combo_obj[int(float(unique_id))]

        combo_list.append(combo_obj)

        list_of_value_rows = []

        # Get current session accounts
        local_current_session_columns = copy.deepcopy(
            variables.cas_table_columns_name_heading
        )

        try:
            # get cas table columns
            local_current_session_columns = [
                column_name
                for (column_name, column_heading) in local_current_session_columns
            ]

            # get columns present in json file
            local_columns_selected = get_all_custom_ltc_columns_from_json()

            # If column returned are None then set default columns
            if local_columns_selected in [None]:
                local_columns_selected = ["Unique ID", "Tickers"]

            # Sort the second list based on the order in the first list
            local_columns_selected = sorted(
                local_columns_selected,
                key=lambda x: local_current_session_columns.index(x),
            )

        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Exception inside getting columns for leg to column table, Exp {e}"
                )

            local_columns_selected = ["Unique ID", "Tickers"]

        leg_no = 1

        try:
            for legs_uid, combo_obj in zip(legs_uid_list, combo_list):
                try:
                    # N-Day High Low
                    if legs_uid in long_term_high_low:
                        n_day_high = (
                            None
                            if long_term_high_low[legs_uid]["N-Day High"] == "N/A"
                            else long_term_high_low[legs_uid]["N-Day High"]
                        )
                        n_day_low = (
                            None
                            if long_term_high_low[legs_uid]["N-Day Low"] == "N/A"
                            else long_term_high_low[legs_uid]["N-Day Low"]
                        )
                        atr = (
                            None
                            if long_term_high_low[legs_uid]["ATR"] == "N/A"
                            else long_term_high_low[legs_uid]["ATR"]
                        )
                        last_close_price = (
                            None
                            if long_term_high_low[legs_uid]["Close Price"] == "N/A"
                            else long_term_high_low[legs_uid]["Close Price"]
                        )
                        correlation = (
                            None
                            if long_term_high_low[legs_uid]["Correlation"] == "N/A"
                            else long_term_high_low[legs_uid]["Correlation"]
                        )
                        last_day_close_price_for_leg_list = (
                            "N/A"
                            if long_term_high_low[legs_uid][
                                "Last Day Close Price For Legs"
                            ]
                            == "N/A"
                            else long_term_high_low[legs_uid][
                                "Last Day Close Price For Legs"
                            ]
                        )
                        beta_value = (
                            "N/A"
                            if long_term_high_low[legs_uid]["Beta"] == "N/A"
                            else f"{(long_term_high_low[legs_uid]['Beta']):,.4f}"
                        )
                        avg_chg_in_price_for_n_days = (
                            None
                            if long_term_high_low[legs_uid][
                                "Avg chg In Price For Last N days"
                            ]
                            == "N/A"
                            else long_term_high_low[legs_uid][
                                "Avg chg In Price For Last N days"
                            ]
                        )
                    else:
                        (
                            n_day_high,
                            n_day_low,
                            atr,
                            last_close_price,
                            correlation,
                            last_day_close_price_for_leg_list,
                            beta_value,
                        ) = (None, None, None, None, None, "N/A", "N/A")
                        avg_chg_in_price_for_n_days = None

                except Exception as e:
                    if variables.flag_debug_mode:
                        print(f"Exception in getting long term values, Exp: {e}")

                    (
                        n_day_high,
                        n_day_low,
                        atr,
                        last_close_price,
                        correlation,
                        last_day_close_price_for_leg_list,
                        beta_value,
                    ) = (None, None, None, None, None, "N/A", "N/A")
                    avg_chg_in_price_for_n_days = None

                try:
                    # Current Day Open High Low
                    if legs_uid in intraday_open_high_low:
                        day_open = (
                            None
                            if intraday_open_high_low[legs_uid]["1-Day Open"] == "N/A"
                            else intraday_open_high_low[legs_uid]["1-Day Open"]
                        )
                        day_high = (
                            None
                            if intraday_open_high_low[legs_uid]["1-Day High"] == "N/A"
                            else intraday_open_high_low[legs_uid]["1-Day High"]
                        )
                        day_low = (
                            None
                            if intraday_open_high_low[legs_uid]["1-Day Low"] == "N/A"
                            else intraday_open_high_low[legs_uid]["1-Day Low"]
                        )
                        low_timestamp = intraday_open_high_low[legs_uid][
                            "Lowest Value TimeStamp"
                        ]
                        high_timestamp = intraday_open_high_low[legs_uid][
                            "Highest Value TimeStamp"
                        ]
                        intraday_support = (
                            "N/A"
                            if intraday_open_high_low[legs_uid]["Intraday Support"]
                            == "N/A"
                            else f"{intraday_open_high_low[legs_uid]['Intraday Support']:,.2f}"
                        )
                        intraday_resistance = (
                            "N/A"
                            if intraday_open_high_low[legs_uid]["Intraday Resistance"]
                            == "N/A"
                            else f"{intraday_open_high_low[legs_uid]['Intraday Resistance']:,.2f}"
                        )
                        intraday_support_count = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Intraday Support Count"
                            ]
                            == "N/A"
                            else f"{intraday_open_high_low[legs_uid]['Intraday Support Count']:,}"
                        )
                        intraday_resistance_count = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Intraday Resistance Count"
                            ]
                            == "N/A"
                            else f"{intraday_open_high_low[legs_uid]['Intraday Resistance Count']:,}"
                        )
                        current_day_open_for_legs_list = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Current Day Open Price For Legs"
                            ]
                            == "N/A"
                            else intraday_open_high_low[legs_uid][
                                "Current Day Open Price For Legs"
                            ]
                        )
                        highest_price_comparison_intraday = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Highest Price Comparison"
                            ]
                            == "N/A"
                            else str(
                                intraday_open_high_low[legs_uid][
                                    "Highest Price Comparison"
                                ]
                            )
                        )
                        lowest_price_comparison_intraday = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Lowest Price Comparison"
                            ]
                            == "N/A"
                            else str(
                                intraday_open_high_low[legs_uid][
                                    "Lowest Price Comparison"
                                ]
                            )
                        )
                        intraday_price_range_ratio = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Intraday Price Range Ratio"
                            ]
                            == "N/A"
                            else f"{intraday_open_high_low[legs_uid]['Intraday Price Range Ratio']:,.2f}"
                        )
                        price_at_highest_combo_price_time_for_legs_list = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Current Day Highest Price For Legs"
                            ]
                            == "N/A"
                            else intraday_open_high_low[legs_uid][
                                "Current Day Highest Price For Legs"
                            ]
                        )
                        price_at_lowest_combo_price_time_for_legs_list = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Current Day Lowest Price For Legs"
                            ]
                            == "N/A"
                            else intraday_open_high_low[legs_uid][
                                "Current Day Lowest Price For Legs"
                            ]
                        )
                        values_to_calculate_change_from_open_value = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Current Day Current Candle For Legs"
                            ]
                            == "N/A"
                            else intraday_open_high_low[legs_uid][
                                "Current Day Current Candle For Legs"
                            ]
                        )
                        day_open_or_current_candle_price = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Day Open Or Current Candle"
                            ]
                            == "N/A"
                            else intraday_open_high_low[legs_uid][
                                "Day Open Or Current Candle"
                            ]
                        )
                        support_price_ration_in_range_intraday = (
                            "N/A"
                            if intraday_open_high_low[legs_uid]["Price Support Ratio"]
                            == "N/A"
                            else f"{intraday_open_high_low[legs_uid]['Price Support Ratio']:,.4f}"
                        )
                        resistance_price_ration_in_range_intraday = (
                            "N/A"
                            if intraday_open_high_low[legs_uid][
                                "Price Resistance Ratio"
                            ]
                            == "N/A"
                            else f"{intraday_open_high_low[legs_uid]['Price Resistance Ratio']:,.4f}"
                        )
                    else:
                        (
                            day_open,
                            day_high,
                            day_low,
                            low_timestamp,
                            high_timestamp,
                            price_at_highest_combo_price_time_for_legs_list,
                            price_at_lowest_combo_price_time_for_legs_list,
                        ) = (None, None, None, "N/A", "N/A", "N/A", "N/A")
                        (
                            intraday_support,
                            intraday_resistance,
                            intraday_support_count,
                            intraday_resistance_count,
                            current_day_open_for_legs_list,
                        ) = ("N/A", "N/A", "N/A", "N/A", "N/A")
                        (
                            highest_price_comparison_intraday,
                            lowest_price_comparison_intraday,
                            intraday_price_range_ratio,
                            values_to_calculate_change_from_open_value,
                        ) = ("N/A", "N/A", "N/A", "N/A")
                        (
                            day_open_or_current_candle_price,
                            support_price_ration_in_range_intraday,
                            resistance_price_ration_in_range_intraday,
                        ) = ("N/A", "N/A", "N/A")
                except Exception as e:
                    if variables.flag_debug_mode:
                        print(f"Exception in getting long term values, Exp: {e}")

                    (
                        day_open,
                        day_high,
                        day_low,
                        low_timestamp,
                        high_timestamp,
                        price_at_highest_combo_price_time_for_legs_list,
                        price_at_lowest_combo_price_time_for_legs_list,
                    ) = (None, None, None, "N/A", "N/A", "N/A", "N/A")
                    (
                        intraday_support,
                        intraday_resistance,
                        intraday_support_count,
                        intraday_resistance_count,
                        current_day_open_for_legs_list,
                    ) = ("N/A", "N/A", "N/A", "N/A", "N/A")
                    (
                        highest_price_comparison_intraday,
                        lowest_price_comparison_intraday,
                        intraday_price_range_ratio,
                        values_to_calculate_change_from_open_value,
                    ) = ("N/A", "N/A", "N/A", "N/A")
                    (
                        day_open_or_current_candle_price,
                        support_price_ration_in_range_intraday,
                        resistance_price_ration_in_range_intraday,
                    ) = ("N/A", "N/A", "N/A")

                try:
                    # HV Related Coulmns
                    if legs_uid in hv_related_values:
                        # HV Val for the unique ID
                        data = hv_related_values[legs_uid]
                        hv_value = (
                            "N/A"
                            if data["H. V."] == "N/A"
                            else f"{data['H. V.']:,.2f}%"
                        )
                        hv_value_without_annualized = (
                            "N/A"
                            if data["H.V. Without Annualized"] == "N/A"
                            else data["H.V. Without Annualized"]
                        )
                        candle_volatility_val = (
                            "N/A"
                            if data["Candle Volatility"] == "N/A"
                            else data["Candle Volatility"]
                        )

                    else:
                        (
                            hv_value,
                            candle_volatility_val,
                            hv_value_without_annualized,
                        ) = (
                            "N/A",
                            "N/A",
                            "N/A",
                        )
                except Exception as e:
                    (hv_value, candle_volatility_val, hv_value_without_annualized) = (
                        "N/A",
                        "N/A",
                        "N/A",
                    )

                    if variables.flag_debug_mode:
                        print(e)

                try:
                    # Volume Related Coulmns
                    if legs_uid in volume_related_column_values:
                        # Volume Related Values for the unique ID
                        data = volume_related_column_values[legs_uid]

                        mean_of_net_volume = (
                            "N/A"
                            if data["Mean of Net Volume"] == "N/A"
                            else f"{data['Mean of Net Volume']:,.2f}"
                        )
                        std_plus_1 = (
                            "N/A"
                            if data["STD +1"] == "N/A"
                            else f"{data['STD +1']:,.2f}"
                        )
                        std_negative_1 = (
                            "N/A"
                            if data["STD -1"] == "N/A"
                            else f"{data['STD -1']:,.2f}"
                        )
                        std_plus_2 = (
                            "N/A"
                            if data["STD +2"] == "N/A"
                            else f"{data['STD +2']:,.2f}"
                        )
                        std_negative_2 = (
                            "N/A"
                            if data["STD -2"] == "N/A"
                            else f"{data['STD -2']:,.2f}"
                        )
                        std_plus_3 = (
                            "N/A"
                            if data["STD +3"] == "N/A"
                            else f"{data['STD +3']:,.2f}"
                        )
                        std_negative_3 = (
                            "N/A"
                            if data["STD -3"] == "N/A"
                            else f"{data['STD -3']:,.2f}"
                        )
                    else:
                        (
                            mean_of_net_volume,
                            std_plus_1,
                            std_negative_1,
                            std_plus_2,
                            std_negative_2,
                            std_plus_3,
                            std_negative_3,
                        ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")
                except Exception as e:
                    (
                        mean_of_net_volume,
                        std_plus_1,
                        std_negative_1,
                        std_plus_2,
                        std_negative_2,
                        std_plus_3,
                        std_negative_3,
                    ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

                try:
                    # Both price and Volume Related Coulmns
                    if legs_uid in support_resistance_and_relative_fields_values:
                        # Both price and Volume Related value for the unique ID
                        data = support_resistance_and_relative_fields_values[legs_uid]

                        resistance = (
                            "N/A"
                            if data["Resistance"] == "N/A"
                            else f"{data['Resistance']:,.2f}"
                        )
                        support = (
                            "N/A"
                            if data["Support"] == "N/A"
                            else f"{data['Support']:,.2f}"
                        )
                        resitance_count = (
                            "N/A"
                            if data["Resistance Count"] == "N/A"
                            else f"{data['Resistance Count']:,}"
                        )
                        support_count = (
                            "N/A"
                            if data["Support Count"] == "N/A"
                            else f"{data['Support Count']:,}"
                        )
                        avg_of_abs_changes_in_prices_for_lookback = (
                            "N/A"
                            if data["Avg of Abs Changes in Prices"] == "N/A"
                            else data["Avg of Abs Changes in Prices"]
                        )
                        relative_atr_derivative = (
                            "N/A"
                            if data["Relative ATR Derivative"] == "N/A"
                            else f"{data['Relative ATR Derivative']:,.2f}"
                        )
                        avg_bid_ask_spread = (
                            None
                            if data["Average Bid Ask"] == "N/A"
                            else data["Average Bid Ask"]
                        )
                        relative_atr_on_positive_candles = (
                            "N/A"
                            if data["Relative ATR on Positive Candles"] == "N/A"
                            else f"{data['Relative ATR on Positive Candles']:,.2f}"
                        )
                        relative_atr_on_negative_candles = (
                            "N/A"
                            if data["Relative ATR on Negative Candles"] == "N/A"
                            else f"{data['Relative ATR on Negative Candles']:,.2f}"
                        )
                        relative_volume_derivative = (
                            "N/A"
                            if data["Relative Volume Derivative"] == "N/A"
                            else f"{data['Relative Volume Derivative']:,.2f}"
                        )
                        relative_volume_on_positive_candles = (
                            "N/A"
                            if data["Relative Volume on Positive Candles"] == "N/A"
                            else f"{data['Relative Volume on Positive Candles']:,.2f}"
                        )
                        relative_volume_on_negative_candles = (
                            "N/A"
                            if data["Relative Volume on Negative Candles"] == "N/A"
                            else f"{data['Relative Volume on Negative Candles']:,.2f}"
                        )
                        relative_atr = (
                            "N/A"
                            if data["Relative ATR"] == "N/A"
                            else data["Relative ATR"]
                        )
                        relative_volume = (
                            "N/A"
                            if data["Relative Volume"] == "N/A"
                            else data["Relative Volume"]
                        )
                        relative_volume_last_n_minutes = (
                            "N/A"
                            if data["Relative Volume Last N Minutes"] == "N/A"
                            else data["Relative Volume Last N Minutes"]
                        )
                        relative_change_last_n_minutes = (
                            "N/A"
                            if data["Relative Change Last N Minutes"] == "N/A"
                            else data["Relative Change Last N Minutes"]
                        )
                        support_price_ration_in_range = (
                            "N/A"
                            if data["Price Support Ratio"] == "N/A"
                            else f"{data['Price Support Ratio']:,.4f}"
                        )
                        resistance_price_ration_in_range = (
                            "N/A"
                            if data["Price Resistance Ratio"] == "N/A"
                            else f"{data['Price Resistance Ratio']:,.4f}"
                        )
                        volume_magnet = (
                            "N/A"
                            if data["Volume Magnet"] == "N/A"
                            else f"{data['Volume Magnet']:,.2f}"
                        )
                        relative_atr_lower = (
                            "N/A"
                            if data["Relative ATR Lower"] == "N/A"
                            else f"{data['Relative ATR Lower']:,.2f}"
                        )
                        relative_atr_higher = (
                            "N/A"
                            if data["Relative ATR Higher"] == "N/A"
                            else data["Relative ATR Higher"]
                        )
                        relative_volume_lower = (
                            "N/A"
                            if data["Relative Volume on Lower Range"] == "N/A"
                            else data["Relative Volume on Lower Range"]
                        )
                        relative_volume_higher = (
                            "N/A"
                            if data["Relative Volume on Higher Range"] == "N/A"
                            else data["Relative Volume on Higher Range"]
                        )

                    else:
                        (
                            resistance,
                            support,
                            resitance_count,
                            support_count,
                            avg_of_abs_changes_in_prices_for_lookback,
                            relative_atr,
                            relative_volume,
                            relative_volume_last_n_minutes,
                            relative_change_last_n_minutes,
                        ) = (
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                        )

                        (
                            relative_atr_derivative,
                            relative_atr_on_positive_candles,
                            relative_atr_on_negative_candles,
                            relative_volume_derivative,
                            relative_volume_on_positive_candles,
                            relative_volume_on_negative_candles,
                            avg_bid_ask_spread,
                            support_price_ration_in_range,
                            resistance_price_ration_in_range,
                            volume_magnet,
                        ) = (
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                        )

                        (
                            relative_atr_lower,
                            relative_atr_higher,
                            relative_volume_lower,
                            relative_volume_higher,
                        ) = ("N/A", "N/A", "N/A", "N/A")

                except Exception as e:
                    if variables.flag_debug_mode:
                        print(e)

                    (
                        resistance,
                        support,
                        resitance_count,
                        support_count,
                        avg_of_abs_changes_in_prices_for_lookback,
                        relative_atr,
                        relative_volume,
                        relative_volume_last_n_minutes,
                        relative_change_last_n_minutes,
                    ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

                    (
                        relative_atr_derivative,
                        relative_atr_on_positive_candles,
                        relative_atr_on_negative_candles,
                        relative_volume_derivative,
                        relative_volume_on_positive_candles,
                        relative_volume_on_negative_candles,
                        avg_bid_ask_spread,
                        support_price_ration_in_range,
                        resistance_price_ration_in_range,
                        volume_magnet,
                    ) = (
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                    )

                    (
                        relative_atr_lower,
                        relative_atr_higher,
                        relative_volume_lower,
                        relative_volume_higher,
                    ) = ("N/A", "N/A", "N/A", "N/A")

                local_map_unique_id_to_legs_unique_id = copy.deepcopy(
                    variables.map_unique_id_to_legs_unique_id
                )

                all_legs = combo_obj.buy_legs + combo_obj.sell_legs

                try:
                    if legs_uid < 0:
                        for leg_obj in all_legs:
                            req_id = variables.con_id_to_req_id_dict[leg_obj.con_id]
                            bid, ask = (
                                variables.bid_price[req_id],
                                variables.ask_price[req_id],
                            )

                            ask = (
                                ask
                                * leg_obj.quantity
                                * leg_obj.multiplier
                                * (1 if leg_obj.action in "BUY" else -1)
                            )

                            bid = (
                                bid
                                * leg_obj.quantity
                                * leg_obj.multiplier
                                * (1 if leg_obj.action in "BUY" else -1)
                            )

                            buy_price, sell_price = ask, bid

                    else:
                        # dict for combo prices
                        local_unique_id_to_prices_dict = copy.deepcopy(
                            variables.unique_id_to_prices_dict
                        )

                        buy_price, sell_price = (
                            local_unique_id_to_prices_dict[unique_id]["BUY"],
                            local_unique_id_to_prices_dict[unique_id]["SELL"],
                        )

                    # update the value of the 'Total Absolute Cost' column of 'Unique ID' to total_abs_cost_value
                    total_abs_cost_value = abs(buy_price + sell_price) / 2

                except Exception as e:
                    buy_price, sell_price = "N/A", "N/A"
                    total_abs_cost_value = "N/A"

                try:
                    # Calculate average price of combo
                    avg_price_combo = (buy_price + sell_price) / 2

                    # Calculate bid ask spread
                    bid_ask_spread = bid - ask
                except Exception as e:
                    # set value to none
                    avg_price_combo = None
                    bid_ask_spread = None

                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Inside CAS Price Update: {sell_price=} {buy_price=}, Exception: {e} "
                        )

                # Calcualte bid ask related columns
                try:
                    # check if values are valid
                    if avg_chg_in_price_for_n_days not in [
                        0,
                        None,
                        "N/A",
                    ] and avg_bid_ask_spread not in [None, "N/A"]:
                        avg_bid_ask_div_by_avg_chg = (
                            avg_bid_ask_spread / avg_chg_in_price_for_n_days
                        )

                        # check if value is valid and if yes then format it
                        if avg_bid_ask_div_by_avg_chg not in [None, "N/A", "None"]:
                            avg_bid_ask_div_by_avg_chg = (
                                f"{avg_bid_ask_div_by_avg_chg:,.2f}"
                            )

                    else:
                        # Set value to N/A
                        avg_bid_ask_div_by_avg_chg = "N/A"

                    # check if values are valid
                    if avg_chg_in_price_for_n_days not in [
                        0,
                        None,
                        "N/A",
                    ] and bid_ask_spread not in [None, "N/A"]:
                        bid_ask_div_by_avg_chg = (
                            bid_ask_spread / avg_chg_in_price_for_n_days
                        )

                        # check if value is valid and if yes then format it
                        if bid_ask_div_by_avg_chg not in [None, "N/A", "None"]:
                            bid_ask_div_by_avg_chg = f"{bid_ask_div_by_avg_chg:,.2f}"

                    else:
                        # Set value to N/A
                        bid_ask_div_by_avg_chg = "N/A"

                except Exception as e:
                    # Set value to N/A
                    avg_bid_ask_div_by_avg_chg = "N/A"
                    bid_ask_div_by_avg_chg = "N/A"

                # Calculate change open dollar value
                if day_open not in ["N/A", None, "None"] and avg_price_combo not in [
                    "N/A",
                    None,
                    "None",
                ]:
                    # Calcualtion for change open dollar value
                    chg_open = avg_price_combo - day_open

                    # check value is valid
                    if chg_open not in ["N/A", None, "None"]:
                        chg_open = f"{chg_open:,.2f}"

                else:
                    chg_open = "N/A"

                # Calculate change close dollar value
                if last_close_price not in [
                    "N/A",
                    None,
                    "None",
                ] and avg_price_combo not in ["N/A", None, "None"]:
                    # Calcualtion for change close dollar value
                    chg_close = avg_price_combo - last_close_price

                    # check value is valid
                    if chg_close not in ["N/A", None, "None"]:
                        chg_close = f"{chg_close:,.2f}"

                else:
                    chg_close = "N/A"

                # Calculate Relative volume div by relative cange for last n minutes in lookback days
                if (
                    relative_volume_last_n_minutes != "N/A"
                    and relative_change_last_n_minutes not in ["N/A", 0]
                ):
                    # Relative volume div by relative cange for last n minutes in lookback days
                    rel_volume_div_by_rel_chg_last_n_minutes = (
                        relative_volume_last_n_minutes / relative_change_last_n_minutes
                    )

                    # Format value of change from lowest price percent
                    rel_volume_div_by_rel_chg_last_n_minutes = (
                        f"{rel_volume_div_by_rel_chg_last_n_minutes:,.2f}"
                    )

                else:
                    # set value to N/A
                    rel_volume_div_by_rel_chg_last_n_minutes = "N/A"

                # Init
                change_from_open_percent = "N/A"
                change_from_high_percent = "N/A"
                change_from_low_percent = "N/A"
                change_from_open_for_rel_chg = "N/A"

                # Getting combo objects mapped to unique ids
                local_unique_id_to_combo_obj = copy.deepcopy(
                    variables.unique_id_to_combo_obj
                )

                # Update From Open if the flag_weighted_change_in_price is False
                if (
                    (avg_price_combo != None)
                    and (day_open != None)
                    and not variables.flag_weighted_change_in_price
                ):
                    # Change from open percent
                    change_from_open_percent = math.log(
                        abs(avg_price_combo) + 1
                    ) * math.copysign(1, avg_price_combo) - math.log(
                        abs(day_open) + 1
                    ) * math.copysign(1, day_open)

                # Update From Open if the flag_weighted_change_in_price is True
                if (
                    current_day_open_for_legs_list != "N/A"
                    and variables.flag_weighted_change_in_price
                ):
                    # print(f"Unique ID: {unique_id} Change From Open")
                    change_from_open_percent = calc_weighted_change_legs_based(
                        combo_obj,
                        current_day_open_for_legs_list,
                    )

                # Update From Open if the flag_weighted_change_in_price is False
                if (
                    (avg_price_combo != None)
                    and (day_open != None)
                    and not variables.flag_weighted_change_in_price
                ):
                    # Change from open percent
                    change_from_open_for_rel_chg = math.log(
                        abs(avg_price_combo) + 1
                    ) * math.copysign(1, avg_price_combo) - math.log(
                        abs(day_open_or_current_candle_price) + 1
                    ) * math.copysign(1, day_open_or_current_candle_price)

                # Update From Open if the flag_weighted_change_in_price is True
                if (
                    current_day_open_for_legs_list not in ["N/A", "None", None]
                    and variables.flag_weighted_change_in_price
                ):
                    # print(f"Unique ID: {unique_id} Change From Open")
                    change_from_open_for_rel_chg = calc_weighted_change_legs_based(
                        combo_obj,
                        values_to_calculate_change_from_open_value,
                    )  # func name ask karan

                # Calculate change from high
                if price_at_highest_combo_price_time_for_legs_list not in [
                    "N/A",
                    "None",
                    None,
                ]:
                    # Get value of change from high percent
                    change_from_high_percent = calc_weighted_change_legs_based(
                        combo_obj,
                        price_at_highest_combo_price_time_for_legs_list,
                        unique_id=unique_id,
                    )

                    if change_from_high_percent not in ["N/A", "None", None]:
                        # Format value of change from highest price percent
                        change_from_high_percent = (
                            f"{change_from_high_percent * 100:,.2f}%"
                        )

                # Calculate change from low
                if price_at_lowest_combo_price_time_for_legs_list not in [
                    "N/A",
                    "None",
                    None,
                ]:
                    # Get value of change from low percent
                    change_from_low_percent = calc_weighted_change_legs_based(
                        combo_obj,
                        price_at_lowest_combo_price_time_for_legs_list,
                        unique_id=unique_id,
                    )

                    if change_from_low_percent not in ["N/A", "None", None]:
                        # Format value of change from lowest price percent
                        change_from_low_percent = (
                            f"{change_from_low_percent * 100:,.2f}%"
                        )

                # Net change since market opened divided by historical volatility value
                try:
                    if (
                        hv_value_without_annualized != 0
                        and hv_value_without_annualized not in ["N/A", "None", None]
                        and change_from_open_percent not in ["N/A", "None", None]
                    ):
                        net_change_from_open_by_hv = round(
                            change_from_open_percent / hv_value_without_annualized, 4
                        )
                    else:
                        net_change_from_open_by_hv = "N/A"
                except Exception as e:
                    net_change_from_open_by_hv = "N/A"

                    # Print to console:
                    if variables.flag_debug_mode:
                        print(
                            f"Inside net_change_since_market_opened_divided_by_hv_value, Exception : {e}"
                        )

                # Candle volatility divided by net change since market opened
                try:
                    if (
                        change_from_open_percent != 0
                        and change_from_open_percent not in ["N/A"]
                        and candle_volatility_val not in ["N/A"]
                    ):
                        cv_by_net_chng_from_open = (
                            candle_volatility_val / change_from_open_percent
                        )
                        cv_by_net_chng_from_open = round(cv_by_net_chng_from_open, 4)
                    else:
                        cv_by_net_chng_from_open = "N/A"
                except Exception as e:
                    cv_by_net_chng_from_open = "N/A"

                    # Print to console:
                    if variables.flag_debug_mode:
                        print(
                            f"Inside candle_volatility_div_by_net_change_since_open_value, Exception : {e}"
                        )

                try:
                    # print(f"{avg_of_abs_changes_in_prices_for_lookback=}{change_from_open_percent=}")
                    if avg_of_abs_changes_in_prices_for_lookback not in [
                        0,
                        "N/A",
                        None,
                    ] and change_from_open_for_rel_chg not in ["N/A", None]:
                        # Calculating Relative Change
                        relative_change_in_price = (
                            abs(change_from_open_for_rel_chg)
                            / avg_of_abs_changes_in_prices_for_lookback
                        )  # change_from_open_percent been in use for many things

                    else:
                        relative_change_in_price = "N/A"

                except Exception as e:
                    print(
                        f" Inside calculating final values for relative_change_value, error is {e}"
                    )
                    relative_change_in_price = "N/A"
                try:
                    if relative_atr not in [
                        0,
                        "N/A",
                        None,
                    ] and relative_change_in_price not in ["N/A", None]:
                        # Calculate relative chnage in price divided by relative ATR
                        relative_change_div_by_relative_atr = (
                            relative_change_in_price / relative_atr
                        )
                    else:
                        relative_change_div_by_relative_atr = "N/A"
                except Exception as e:
                    print(
                        f" Inside calculating final values for relative_change_div_by_relative_atr, error is {e}"
                    )
                    relative_change_div_by_relative_atr = "N/A"

                # Calculate Relative change in price divided by Relative volume
                if (
                    (relative_change_in_price != "N/A")
                    and (relative_volume != "N/A")
                    and (relative_volume != 0)
                ):
                    relative_change_in_price_div_by_relative_volume = (
                        relative_change_in_price / relative_volume
                    )

                    relative_change_in_price_div_by_relative_volume = (
                        f"{(relative_change_in_price_div_by_relative_volume):,.2f}"
                    )
                else:
                    relative_change_in_price_div_by_relative_volume = "N/A"

                # Calculate [ATR/Total absolute cost] / points from lowest price (intraday prices)
                if (
                    (total_abs_cost_value != "N/A")
                    and (atr != "N/A")
                    and (avg_price_combo != None)
                    and (day_low != None)
                ):
                    try:
                        atr_div_by_total_abs_cost_div_by_point_from_lowest_price = (
                            atr / total_abs_cost_value
                        ) / (avg_price_combo - day_low)

                        atr_div_by_total_abs_cost_div_by_point_from_lowest_price = f"{float(atr_div_by_total_abs_cost_div_by_point_from_lowest_price):,.2f}"
                    except Exception as e:
                        atr_div_by_total_abs_cost_div_by_point_from_lowest_price = "N/A"

                        # Print to console
                        if variables.flag_debug_mode:
                            print(
                                f"Inside calculating 'atr_div_by_total_abs_cost_div_by_point_from_lowest_price', error is {e} "
                            )
                else:
                    atr_div_by_total_abs_cost_div_by_point_from_lowest_price = "N/A"

                # Calculate Relative volume / Relative ATR
                if (
                    (relative_volume != "N/A")
                    and (relative_atr != "N/A")
                    and (relative_atr != 0)
                ):
                    relative_volume_div_by_relative_atr = relative_volume / relative_atr

                    relative_volume_div_by_relative_atr = (
                        f"{(relative_volume_div_by_relative_atr):,.2f}"
                    )
                else:
                    relative_volume_div_by_relative_atr = "N/A"

                # Calculate [ATR/Total absolute cost] / points from highest price (intraday prices)
                if (
                    (total_abs_cost_value != "N/A")
                    and (atr != "N/A")
                    and (avg_price_combo != None)
                    and (day_high != None)
                ):
                    try:
                        atr_div_by_total_abs_cost_div_by_point_from_highest_price = (
                            atr / total_abs_cost_value
                        ) / (avg_price_combo - day_high)

                        atr_div_by_total_abs_cost_div_by_point_from_highest_price = f"{(atr_div_by_total_abs_cost_div_by_point_from_highest_price):,.2f}"
                    except Exception as e:
                        atr_div_by_total_abs_cost_div_by_point_from_highest_price = (
                            "N/A"
                        )

                        # Print to console
                        if variables.flag_debug_mode:
                            print(
                                f"Inside calculating 'atr_div_by_total_abs_cost_div_by_point_from_highest_price', error is {e} "
                            )

                else:
                    atr_div_by_total_abs_cost_div_by_point_from_highest_price = "N/A"

                rel_vol_div_by_opening_gap = "N/A"

                # Calculate Size of Opening Gap as a %
                if (
                    day_open != None
                    and last_close_price != None
                    and not variables.flag_weighted_change_in_price
                ):
                    size_of_opening_gap_value = math.log(
                        abs(day_open) + 1
                    ) * math.copysign(1, day_open) - math.log(
                        abs(last_close_price) + 1
                    ) * math.copysign(1, last_close_price)

                    if size_of_opening_gap_value not in ["N/A", "None", None]:
                        size_of_opening_gap_value = (
                            f"{(size_of_opening_gap_value * 100):,.2f}%"
                        )

                    else:
                        size_of_opening_gap_value = "N/A"

                elif variables.flag_weighted_change_in_price:
                    size_of_opening_gap_value = calc_weighted_change_legs_based(
                        combo_obj,
                        last_day_close_price_for_leg_list,
                        current_day_open_for_legs_list,
                    )

                    if size_of_opening_gap_value not in ["N/A", "None", None]:
                        # check if values are vlaid
                        if size_of_opening_gap_value not in [
                            0,
                            "N/A",
                            "None",
                            None,
                        ] and relative_volume not in ["N/A", "None", None]:
                            # calculate indicator value
                            rel_vol_div_by_opening_gap = (
                                relative_volume / size_of_opening_gap_value
                            )

                            # check if values are valid
                            if rel_vol_div_by_opening_gap not in ["N/A", "None", None]:
                                # Format value
                                rel_vol_div_by_opening_gap = (
                                    f"{(rel_vol_div_by_opening_gap):,.2f}"
                                )

                            else:
                                # set value to N/A
                                rel_vol_div_by_opening_gap = "N/A"

                        else:
                            # set value to N/A
                            rel_vol_div_by_opening_gap = "N/A"

                        size_of_opening_gap_value = (
                            f"{(size_of_opening_gap_value * 100):,.2f}%"
                        )
                else:
                    size_of_opening_gap_value = "N/A"

                # Formatting relative_change_in_price
                if relative_change_in_price != "N/A":
                    relative_change_in_price = (
                        f"{(float(relative_change_in_price)):,.2f}"
                    )
                else:
                    relative_change_in_price = "N/A"

                # Formatting relative_volume
                if relative_volume != "N/A":
                    relative_volume = f"{(float(relative_volume)):,.2f}"
                else:
                    relative_volume = "N/A"

                # Formatting relative_atr
                if relative_atr != "N/A":
                    relative_atr = f"{(relative_atr):,.2f}"
                else:
                    relative_atr = "N/A"

                # Formatting total_abs_cost_value
                if total_abs_cost_value != "N/A":
                    total_abs_cost_value = f"{(float(total_abs_cost_value)):,.2f}"
                else:
                    total_abs_cost_value = "N/A"

                # Update High- Low Range N %, and Update High - Low Abs N-Days
                if (
                    (avg_price_combo != None)
                    and (n_day_low != None)
                    and (n_day_high != None)
                ):
                    # To Avoid by Zero error
                    try:
                        # HL range N-Days
                        hl_range_n_day_percent = (avg_price_combo - n_day_low) / (
                            n_day_high - n_day_low
                        )
                        hl_range_n_day_percent = (
                            f"{(hl_range_n_day_percent * 100):,.2f}%"
                        )
                    except Exception as e:
                        # Print to console
                        if variables.flag_debug_mode:
                            print(
                                f"Unique ID: {unique_id} Got Error for N Day HL Range Percent: {e}"
                            )

                        # Setting as N/A
                        hl_range_n_day_percent = "N/A"

                    # ABS of N-day high low
                    abs_hl_n_day = int(abs(n_day_high - n_day_low) * 100) / 100

                    # Format the Value
                    n_day_high = f"{(int(n_day_high * 100) / 100):,.2f}"
                    n_day_low = f"{(int(n_day_low * 100) / 100):,.2f}"
                    abs_hl_n_day = f"{abs_hl_n_day:,.2f}"
                else:
                    n_day_low = "N/A"
                    n_day_high = "N/A"
                    hl_range_n_day_percent = "N/A"
                    abs_hl_n_day = "N/A"

                # ATR
                if atr != None:
                    atr = f"{(int(atr * 100) / 100):,.2f}"
                else:
                    atr = "N/A"

                # Init change from close% value
                change_from_close_percent = "N/A"

                # Update From Close if the flag_weighted_change_in_price is False
                if (
                    (avg_price_combo != None)
                    and (last_close_price != None)
                    and not variables.flag_weighted_change_in_price
                ):
                    change_from_close_percent = math.log(
                        abs(avg_price_combo) + 1
                    ) * math.copysign(1, avg_price_combo) - math.log(
                        abs(last_close_price) + 1
                    ) * math.copysign(1, last_close_price)

                    # Format the Value
                    if not isinstance(change_from_close_percent, str):
                        change_from_close_percent = (
                            f"{(change_from_close_percent * 100):,.2f}%"
                        )

                # Update From Open if the flag_weighted_change_in_price is True
                if (
                    last_day_close_price_for_leg_list != "N/A"
                ) and variables.flag_weighted_change_in_price:
                    # print(f"Unique ID: {unique_id} Change From Close")
                    change_from_close_percent = calc_weighted_change_legs_based(
                        combo_obj,
                        last_day_close_price_for_leg_list,
                    )

                    # Format the Value
                    if change_from_close_percent not in ["N/A"]:
                        change_from_close_percent = float(change_from_close_percent)
                        change_from_close_percent = (
                            f"{(change_from_close_percent * 100):,.2f}%"
                        )

                # Last Close Price
                if last_close_price != None:
                    last_close_price = f"{(int(last_close_price * 100) / 100):,.2f}"
                else:
                    last_close_price = "N/A"

                # Correlation
                if correlation != None:
                    correlation = f"{(int(correlation * 10000) / 10000):,.4f}"
                else:
                    correlation = "N/A"

                # Update High Low Range 1 %
                if (
                    (avg_price_combo != None)
                    and (day_low != None)
                    and (day_high != None)
                ):
                    # To Avoid by Zero error
                    try:
                        # HL range N-Days
                        hl_range_current_day_percent = (avg_price_combo - day_low) / (
                            day_high - day_low
                        )
                        hl_range_current_day_percent = (
                            f"{int(hl_range_current_day_percent * 100):,.2f}%"
                        )
                    except Exception as e:
                        # Print to console
                        if variables.flag_debug_mode:
                            print(
                                f"Unique ID: {unique_id} Got Error for Current Day HL Range Percent: {e}"
                            )

                        # Setting None
                        hl_range_current_day_percent = "N/A"

                    # ABS of 1-day high low
                    abs_hl_current_day = int(abs(day_high - day_low) * 100) / 100

                    # Format the Value
                    abs_hl_current_day = f"{(int(abs_hl_current_day * 100) / 100):,.2f}"
                    day_high = f"{(int(day_high * 100) / 100):,.2f}"
                    day_low = f"{(int(day_low * 100) / 100):,.2f}"
                else:
                    day_high = "N/A"
                    day_low = "N/A"
                    hl_range_current_day_percent = "N/A"
                    abs_hl_current_day = "N/A"

                # Last Close Price
                if change_from_open_percent not in ["N/A", None]:
                    change_from_open_percent = f"{change_from_open_percent * 100:,.2f}%"
                else:
                    change_from_open_percent = "N/A"

                if net_change_from_open_by_hv not in ["N/A", None]:
                    net_change_from_open_by_hv = f"{net_change_from_open_by_hv:,.4f}"
                else:
                    net_change_from_open_by_hv = "N/A"

                if candle_volatility_val not in ["N/A", None]:
                    candle_volatility_val = f"{candle_volatility_val:,.2f}%"
                else:
                    candle_volatility_val = "N/A"

                if cv_by_net_chng_from_open not in ["N/A", None]:
                    cv_by_net_chng_from_open = f"{cv_by_net_chng_from_open:,.4f}"
                else:
                    cv_by_net_chng_from_open = "N/A"

                if relative_change_div_by_relative_atr not in ["N/A", None]:
                    relative_change_div_by_relative_atr = (
                        f"{relative_change_div_by_relative_atr:,.2f}"
                    )
                else:
                    relative_change_div_by_relative_atr = "N/A"

                # Ticker String
                ticker_string = make_informative_combo_string(combo_obj)

                # If Cache is Enabled, set the primary indicators to the "N/A"
                if variables.flag_cache_data:
                    # Current Time
                    current_time = datetime.datetime.now(variables.target_timezone_obj)

                    if (
                        variables.lut_for_long_term_values is not None
                        and current_time
                        >= variables.lut_for_long_term_values
                        + datetime.timedelta(
                            minutes=variables.time_buffer_for_keep_updating_lut_time_for_fetched_values
                        )
                    ):
                        n_day_high, n_day_low, atr, last_close_price, beta_value = (
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                        )

                    if (
                        variables.lut_for_intraday_values is not None
                        and current_time
                        >= variables.lut_for_intraday_values
                        + datetime.timedelta(
                            minutes=variables.time_buffer_for_keep_updating_lut_time_for_fetched_values
                        )
                    ):
                        day_open, day_high, day_low, low_timestamp, high_timestamp = (
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                        )
                        (
                            intraday_support,
                            intraday_resistance,
                            intraday_support_count,
                            intraday_resistance_count,
                        ) = (
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                        )
                        (
                            highest_price_comparison_intraday,
                            lowest_price_comparison_intraday,
                            intraday_price_range_ratio,
                        ) = ("N/A", "N/A", "N/A")

                    if (
                        variables.lut_for_hv_related_columns is not None
                        and current_time
                        >= variables.lut_for_hv_related_columns
                        + datetime.timedelta(
                            minutes=variables.time_buffer_for_keep_updating_lut_time_for_fetched_values
                        )
                    ):
                        (
                            hv_value,
                            candle_volatility_val,
                        ) = (
                            "N/A",
                            "N/A",
                        )

                    if (
                        variables.lut_for_volume_related_fields is not None
                        and current_time
                        >= variables.lut_for_volume_related_fields
                        + datetime.timedelta(
                            minutes=variables.time_buffer_for_keep_updating_lut_time_for_fetched_values
                        )
                    ):
                        (
                            mean_of_net_volume,
                            std_plus_1,
                            std_negative_1,
                            std_plus_2,
                            std_negative_2,
                            std_plus_3,
                            std_negative_3,
                        ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

                    if (
                        variables.lut_for_price_based_relative_indicators_values
                        is not None
                        and current_time
                        >= variables.lut_for_price_based_relative_indicators_values
                        + datetime.timedelta(
                            minutes=variables.time_buffer_for_keep_updating_lut_time_for_fetched_values
                        )
                    ):
                        (
                            resistance,
                            support,
                            resitance_count,
                            support_count,
                            relative_atr,
                            relative_volume,
                            rel_volume_div_by_rel_chg_last_n_minutes,
                        ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

                        (
                            relative_atr_derivative,
                            relative_atr_on_positive_candles,
                            relative_atr_on_negative_candles,
                            relative_volume_derivative,
                            relative_volume_on_positive_candles,
                            relative_volume_on_negative_candles,
                            avg_bid_ask_spread,
                            support_price_ration_in_range,
                            resistance_price_ration_in_range,
                            volume_magnet,
                        ) = (
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                            "N/A",
                        )

                        (
                            relative_atr_lower,
                            relative_atr_higher,
                            relative_volume_lower,
                            relative_volume_higher,
                        ) = ("N/A", "N/A", "N/A", "N/A")

                # List of values to check if it is 'N/A'
                values_for_cas_table = [
                    leg_no,
                    ticker_string,
                    buy_price,
                    sell_price,
                    total_abs_cost_value,
                    day_high,
                    high_timestamp,
                    day_low,
                    low_timestamp,
                    abs_hl_current_day,
                    hl_range_current_day_percent,
                    last_close_price,
                    change_from_close_percent,
                    change_from_open_percent,
                    chg_close,
                    chg_open,
                    size_of_opening_gap_value,
                    n_day_high,
                    n_day_low,
                    abs_hl_n_day,
                    hl_range_n_day_percent,
                    atr,
                    hv_value,
                    candle_volatility_val,
                    net_change_from_open_by_hv,
                    cv_by_net_chng_from_open,
                    resistance,
                    support,
                    resitance_count,
                    support_count,
                    intraday_resistance,
                    intraday_support,
                    intraday_resistance_count,
                    intraday_support_count,
                    mean_of_net_volume,
                    std_plus_1,
                    std_negative_1,
                    std_plus_2,
                    std_negative_2,
                    std_plus_3,
                    std_negative_3,
                    relative_atr,
                    relative_change_in_price,
                    relative_volume,
                    relative_volume_div_by_relative_atr,
                    relative_change_in_price_div_by_relative_volume,
                    relative_change_div_by_relative_atr,
                    atr_div_by_total_abs_cost_div_by_point_from_lowest_price,
                    atr_div_by_total_abs_cost_div_by_point_from_highest_price,
                    beta_value,
                    change_from_high_percent,
                    change_from_low_percent,
                    highest_price_comparison_intraday,
                    lowest_price_comparison_intraday,
                    intraday_price_range_ratio,
                    rel_volume_div_by_rel_chg_last_n_minutes,
                    relative_volume_on_positive_candles,
                    relative_volume_on_negative_candles,
                    relative_atr_on_positive_candles,
                    relative_atr_on_negative_candles,
                    avg_bid_ask_div_by_avg_chg,
                    bid_ask_div_by_avg_chg,
                    relative_volume_derivative,
                    relative_atr_derivative,
                    support_price_ration_in_range,
                    resistance_price_ration_in_range,
                    support_price_ration_in_range_intraday,
                    resistance_price_ration_in_range_intraday,
                    rel_vol_div_by_opening_gap,
                    volume_magnet,
                    relative_atr_lower,
                    relative_atr_higher,
                    relative_volume_lower,
                    relative_volume_higher,
                ]

                leg_no += 1

                values_dict = dict(
                    zip(local_current_session_columns, values_for_cas_table)
                )

                values_for_cas_table = []

                for column_name in local_columns_selected:
                    try:
                        values_for_cas_table.append(values_dict[column_name])

                    except Exception as e:
                        values_for_cas_table.append("N/A")

                list_of_value_rows.append(values_for_cas_table)

        except:
            pass

        combo_values = list_of_value_rows[-1]

        leg_rows_list = []

        for row in list_of_value_rows[:-1]:  # Iterate up to the second-to-last item
            new_row = []

            for ind in range(0, len(row)):
                try:
                    if isinstance(row[ind], str):
                        # Remove ',' and '%' from the string
                        row[ind] = row[ind].replace(",", "").replace("%", "")

                    if isinstance(combo_values[ind], str):
                        # Remove ',' and '%' from the string
                        combo_values[ind] = (
                            combo_values[ind].replace(",", "").replace("%", "")
                        )

                    if (
                        is_float(row[ind])
                        and is_float(combo_values[ind])
                        and local_columns_selected[ind] not in ["Unique ID"]
                    ):
                        try:
                            temp_value = float(row[ind]) / float(combo_values[ind])

                            temp_value = round(temp_value, 2)

                            new_row.append(temp_value)

                        except Exception as e:
                            new_row.append("N/A")

                    elif row[ind] not in ["None", None, "N/A"]:
                        new_row.append(row[ind])
                    else:
                        new_row.append("N/A")

                except Exception as e:
                    new_row.append("N/A")

            leg_rows_list.append(new_row)

        # Create a popup window with the table
        treeview_popup = tk.Toplevel()
        treeview_popup.title(f"Leg-to-Combo Comparison Details, Unique ID: {unique_id}")
        custom_height = 400

        columns_for_leg_to_combo_comparision = local_columns_selected

        # 25 row high,  20 * 2(padding)
        custom_width = 1200  # 60 = 20 * 2(padding) + 20(scrollbar)
        treeview_popup.geometry(f"{custom_width}x{custom_height}")

        # Create a frame for the input fields
        treeview_table_frame = ttk.Frame(treeview_popup, padding=20)
        treeview_table_frame.pack(fill="both", expand=True)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(treeview_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Treeview Scrollbar
        tree_scroll_x = Scrollbar(treeview_table_frame, orient=tk.HORIZONTAL)
        tree_scroll_x.pack(side="bottom", fill="x")

        # Create Treeview
        self.treeview_table = ttk.Treeview(
            treeview_table_frame,
            yscrollcommand=tree_scroll.set,
            height=15,
            xscrollcommand=tree_scroll_x.set,
            selectmode="extended",
        )

        # Pack to the screen
        self.treeview_table.pack(fill="both", expand=True)

        # Configure the scrollbar
        tree_scroll.config(command=self.treeview_table.yview)

        tree_scroll_x.config(command=self.treeview_table.xview)

        # Define Our Columns
        self.treeview_table["columns"] = columns_for_leg_to_combo_comparision

        # First Column hiding it
        self.treeview_table.column("#0", width=0, stretch="no")

        # Table Columns and Heading
        for indx, column_name in enumerate(columns_for_leg_to_combo_comparision):
            # Width for 1st 4 column 120 then 190
            width = 200
            self.treeview_table.column(
                column_name,
                anchor="center",
                width=width,
                minwidth=width,
            )

        self.treeview_table.heading("#0", text="\n", anchor="center")

        # Table Columns and Heading
        for indx, column_name in enumerate(columns_for_leg_to_combo_comparision):
            self.treeview_table.heading(column_name, text=column_name, anchor="center")

        # Create striped row tags
        self.treeview_table.tag_configure("oddrow", background="white")
        self.treeview_table.tag_configure("evenrow", background="lightblue")

        counter = 0

        for row_value in leg_rows_list:
            # Combine the values into a tuple
            combined_tuple = tuple(row_value)
            if counter % 2 == 0:
                # Inserting in the table
                self.treeview_table.insert(
                    parent="",
                    index="end",
                    text="",
                    values=combined_tuple,
                    tags=("evenrow",),
                )

            else:
                # Inserting in the table
                self.treeview_table.insert(
                    parent="",
                    index="end",
                    text="",
                    values=combined_tuple,
                    tags=("oddrow",),
                )
            counter += 1

    # Method to define cas condition table right click options
    def cas_condition_table_right_click(self, event):
        # get the Treeview row that was clicked
        row = self.cas_condition_table.identify_row(event.y)

        if row:
            # select the row
            self.cas_condition_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.cas_condition_table, tearoff=0)
            menu.add_command(
                label="View Details",
                command=lambda: variables.screen.display_combination_details(
                    "cas_condition"
                ),
            )
            menu.add_command(
                label="View Condition", command=lambda: self.display_cas_condition()
            )
            menu.add_command(
                label="View Order Details", command=lambda: self.view_order_details()
            )
            menu.add_command(
                label="Delete", command=lambda: self.delete_cas_condition()
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    # Method to dispaly order details
    def view_order_details(self):
        # Unique ID
        selected_item = self.cas_condition_table.selection()[0]

        # get the item ID of the selected row
        values = self.cas_condition_table.item(
            selected_item, "values"
        )  # get the values of the selected row
        unique_id = int(values[0])

        # Type of CAS Condition
        cas_condition_type = values[1]

        # Can not display order info popup for add and switch
        if cas_condition_type in ["ADD", "SWITCH"]:
            # Display error popup and return
            variables.screen.display_error_popup(
                "Error Order Details",
                f"Can not view order details for conditional {cas_condition_type}.",
            )
            return

        try:
            # Get all the pending cas condition from db
            all_cas_condition_dataframe = get_all_cas_conditions_from_db(
                True
            )  # OnlyPending

            # Renaming and  Dropping Extra Columns
            all_cas_condition_dataframe = all_cas_condition_dataframe.rename(
                columns={"CAS Condition Type": "Action"}
            )
            all_cas_condition_dataframe = all_cas_condition_dataframe.drop(
                [
                    "Condition",
                    "Condition Reference Price",
                    "Reference Position",
                    "Condition Trigger Price",
                ],
                axis=1,
            )

            # Selecting the column with Unique ID
            all_cas_condition_dataframe = all_cas_condition_dataframe.loc[
                all_cas_condition_dataframe["Unique ID"] == unique_id
            ]

            # Getting Columns and Values of the row
            order_details_table_columns = tuple(
                all_cas_condition_dataframe.columns.tolist()
            )
            order_details_table_values = tuple(
                all_cas_condition_dataframe.values.tolist()[0]
            )
        except Exception as e:
            # Display error popup and return
            variables.screen.display_error_popup(
                "Error Order Details", f"Unable to get conditional order details."
            )
            return

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

        # Create a popup window with the table
        treeview_popup = tk.Toplevel()
        treeview_popup.title(f"Conditional {cas_condition_type} Order Details")
        custom_height = min(max((1 * 20) + 100, 150), 210)

        custom_width = (
            120 * len((order_details_table_values)) + 60
        )  # 60 = 20 * 2(padding) + 20(scrollbar)
        treeview_popup.geometry(f"{custom_width}x{custom_height}")

        # Create a frame for the input fields
        treeview_table_frame = ttk.Frame(treeview_popup, padding=20)
        treeview_table_frame.pack(fill="both", expand=True)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(treeview_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.treeview_table = ttk.Treeview(
            treeview_table_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
        )

        # Pack to the screen
        self.treeview_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.treeview_table.yview)

        # Define Our Columns
        self.treeview_table["columns"] = order_details_table_columns

        # First Column hiding it
        self.treeview_table.column("#0", width=0, stretch="no")
        self.treeview_table.heading("#0", text="", anchor="w")

        # Table Columns and Heading
        for column_name in order_details_table_columns:
            self.treeview_table.column(column_name, anchor="center", width=120)
            self.treeview_table.heading(column_name, text=column_name, anchor="center")

        # Create striped row tags
        self.treeview_table.tag_configure("oddrow", background="white")
        self.treeview_table.tag_configure("evenrow", background="lightblue")

        # Inserting in the table
        self.treeview_table.insert(
            parent="",
            index="end",
            text="",
            values=order_details_table_values,
            tags=("evenrow",),
        )

    # # Method to display cas condition for cas condition order
    def display_cas_condition(self):
        # Unique ID
        selected_item = self.cas_condition_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.cas_condition_table.item(
            selected_item, "values"
        )  # get the values of the selected row
        unique_id = int(values[0])

        # Get all cas condition from db
        all_cas_condition_dataframe = get_all_cas_conditions_from_db()

        # Get condition
        selected_condition = all_cas_condition_dataframe.loc[
            all_cas_condition_dataframe["Unique ID"] == unique_id, "Condition"
        ].to_list()

        self.display_text_box_popup(
            selected_condition[0], f"Unique ID: {unique_id}, CAS Condition"
        )

    # Method to display some text in pop up
    def display_text_box_popup(self, text_to_display, title_of_popup):
        # Create a enter_legs popup window
        text_box_poup = tk.Toplevel()
        text_box_poup.title(title_of_popup)

        # Geo Size
        text_box_poup.geometry("400x270")

        # Frame
        text_box_poup_frame = ttk.Frame(text_box_poup, padding=20)
        text_box_poup_frame.pack(fill="both", expand=True)

        # Display the text in textbox
        text_box = tk.Text(
            text_box_poup_frame,
            width=45,
            height=16,
        )
        text_box.insert(tk.END, text_to_display)
        text_box.configure(state="disabled")
        text_box.pack()

    # Method to remove cas condition from system
    def delete_cas_condition(self, unique_id=None, series_id=None):
        if unique_id == None:
            # Unique ID
            selected_item = self.cas_condition_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.cas_condition_table.item(
                selected_item, "values"
            )  # get the values of the selected row
            unique_id = int(values[0])
            series_id = values[15]

        if series_id not in ["None", None, "N/A"]:
            variables.screen.screen_conditional_series_tab.stop_series(series_id)

        # Delete Condition from cas_condition_table_dbs
        delete_cas_condition_from_db_for_unique_id(unique_id)

        # Delete all legs
        delete_cas_legs_from_db_for_unique_id(unique_id)

        table_ids = self.cas_condition_table.get_children()

        for table_id in table_ids:
            values = self.cas_condition_table.item(
                table_id, "values"
            )  # get the values of the selected row
            unique_id_to_check = int(values[0])

            if unique_id_to_check == unique_id:
                # Remove condition from the table
                self.cas_condition_table.delete(table_id)

        # update the table
        self.update_cas_condition_after_cas_condition_deleted()
        # Removing deleted cas condition from watchlist cas condition dataframe
        try:
            variables.cas_condition_table_dataframe = (
                variables.cas_condition_table_dataframe.loc[
                    variables.cas_condition_table_dataframe["Unique ID"] != unique_id
                ]
            )
        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print("Can not update cas conditon dataframe for watchlist change", e)

        try:
            # remove key from variables.
            del variables.cas_unique_id_to_combo_obj[unique_id]

            # Removing deleted cas condition from watchlist cas condition dataframe
            # variables.cas_condition_table_dataframe = variables.cas_condition_table_dataframe.loc[variables.cas_condition_table_dataframe["Unique ID"] != unique_id]

        except Exception as e:
            # Print to console TODO
            if variables.flag_debug_mode:
                print("Error, Can not delete cas combo: ", e)

    # Method to update cas conditon table after watchlist changed
    def update_cas_condition_table_watchlist_change(
        self,
    ):
        # All the Unique IDs in the System
        # Get combo details dataframe
        local_cas_condition_details_df = copy.deepcopy(
            variables.cas_condition_table_dataframe
        )

        # All the Unique IDs in the System
        all_unique_ids_in_system = local_cas_condition_details_df["Unique ID"].tolist()

        # all account ids in table
        all_account_ids_in_account_group = all_account_id_in_cas_condition_table = [
            (self.cas_condition_table.item(_x)["values"][13])
            for _x in self.cas_condition_table.get_children()
        ]

        # All the rows in orders book Table
        all_unique_ids_in_watchlist = all_unique_id_in_cas_condition_table = [
            int(self.cas_condition_table.item(_x)["values"][0])
            for _x in self.cas_condition_table.get_children()
        ]

        # If we want to update the table as watchlist changed
        if variables.flag_cas_condition_table_watchlist_changed:
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

            # Setting it to False
            variables.flag_cas_condition_table_watchlist_changed = False

        # Update the rows
        for i, row_val in local_cas_condition_details_df.iterrows():
            # Unique ID of row val
            unique_id = row_val["Unique ID"]

            # table id
            table_id = row_val["Table ID Column"]

            if unique_id in all_unique_ids_in_watchlist:
                # Tuple of vals
                row_val = tuple(row_val)

                if unique_id in all_unique_id_in_cas_condition_table:
                    # Update the row at once.
                    self.cas_condition_table.item(table_id, values=row_val)
                else:
                    # Insert it in the table
                    self.cas_condition_table.insert(
                        "",
                        "end",
                        iid=table_id,
                        text="",
                        values=row_val,
                        tags=("oddrow",),
                    )
            else:
                # If this unique_id in positions Table but not in watchlist delete it
                if unique_id in all_unique_id_in_cas_condition_table:
                    try:
                        self.cas_condition_table.delete(table_id)
                    except Exception as e:
                        pass

        try:
            # Filter out the dataframe such that the dataframe only consists of all the unique ids that are present in the watchlist, so sorting will be in correct order.
            local_cas_condition_details_df = local_cas_condition_details_df[
                local_cas_condition_details_df["Unique ID"].isin(
                    all_unique_ids_in_watchlist
                )
            ]
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Error inside updating positions table values, is {e}")

        # All the rows in positions Table
        all_unique_id_in_cas_condition_table = [
            (self.cas_condition_table.item(_x)["values"][0])
            for _x in self.cas_condition_table.get_children()
        ]

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in local_cas_condition_details_df.iterrows():
            # Unique_id
            unique_id = row["Unique ID"]

            # Table Id
            table_id = row["Table ID Column"]

            # If unique_id in table
            if unique_id in all_unique_id_in_cas_condition_table:
                self.cas_condition_table.move(table_id, "", counter_row)

                if counter_row % 2 == 0:
                    self.cas_condition_table.item(table_id, tags="evenrow")
                else:
                    self.cas_condition_table.item(table_id, tags="oddrow")

                # Increase row count
                counter_row += 1

    # Method to update cas condition row in GUI table
    def update_cas_condition_table_rows_value(self, cas_table_update_values, index):
        # All Unique Id in cas_condition table
        list_of_unique_id_in_cas_condtion_table = (
            self.cas_condition_table.get_children()
        )

        # Update Values in cas condition
        for unique_id, val in cas_table_update_values:
            for account_id in variables.current_session_accounts:
                table_id = f"{unique_id}_{account_id}"
                # Update if unique id is in cas condition table
                if str(table_id) in list_of_unique_id_in_cas_condtion_table:
                    self.cas_condition_table.set(table_id, index, val)

    # Method to update cas condition table after cas condition deleted
    def update_cas_condition_after_cas_condition_deleted(self):
        count = 0
        for combo_row in self.cas_condition_table.get_children():
            if count % 2 == 0:
                self.cas_condition_table.item(combo_row, tags="evenrow")
            else:
                self.cas_condition_table.item(combo_row, tags="oddrow")

            count += 1

    # Method to update cas table rows in GUI table
    def update_cas_table_rows_value(self, cas_table_update_values_df):
        # All the Unique IDs in the System
        all_unique_ids_in_system = cas_table_update_values_df["Unique ID"].tolist()

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

    # Method to create conditional series
    def create_conditional_series(self, flag_multi=False):
        # Unique ID
        selected_item = self.cas_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.cas_table.item(
            selected_item, "values"
        )  # get the values of the selected row
        unique_id = int(values[0])

        variables.screen.screen_conditional_series_tab.add_conditional_series(
            unique_id, flag_multi=flag_multi
        )

    # Method to initiate to take input for conditional add/switch order
    def conditional_add_switch_legs(self, cas_add_or_switch, flag_multi_account=False):
        # Unique ID
        selected_item = self.cas_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.cas_table.item(
            selected_item, "values"
        )  # get the values of the selected row
        unique_id = int(values[0])

        # Number of CAS Conditions that exists
        number_of_conditions = do_cas_condition_exists_for_unique_id_in_db(unique_id)

        number_of_conditions += do_cas_condition_series_exists_for_unique_id_in_db(
            unique_id
        )

        # If a condition already exists, display error popup
        if number_of_conditions > 0:
            # TODO
            # Throw Error Popup
            variables.screen.display_error_popup(
                f"Unique ID : {unique_id}, Conditional {cas_add_or_switch.capitalize()}",
                "A Condition already exists, can not add another.",
            )
            return

        # Trying to get the reference price
        try:
            local_combo_buy_sell_price_dict = copy.deepcopy(
                variables.unique_id_to_prices_dict[unique_id]
            )
            current_buy_price, current_sell_price = (
                local_combo_buy_sell_price_dict["BUY"],
                local_combo_buy_sell_price_dict["SELL"],
            )
            reference_price = (
                int(((current_buy_price + current_sell_price) / 2) * 100) / 100
            )

        except Exception as e:
            if variables.flag_debug_mode:
                print(e)
            # TODO
            variables.screen.display_error_popup(
                f"Unique ID : {unique_id}, Conditional {cas_add_or_switch.capitalize()}",
                "Unable to get the combination current price1.",
            )
            return

        # Trying to get the reference positions
        try:
            local_unique_id_to_positions_dict = copy.deepcopy(
                variables.map_unique_id_to_positions
            )
            reference_position = local_unique_id_to_positions_dict[unique_id]
        except Exception as e:
            if variables.flag_debug_mode:
                print(e)
            # TODO
            variables.screen.display_error_popup(
                f"Unique ID : {unique_id}, Conditional {cas_add_or_switch.capitalize()}",
                "Unable to get the combination current positions.",
            )

            return

        # If Condition ADD or Switch
        if cas_add_or_switch in ["ADD", "SWITCH"]:
            # Show Enter Leg popup
            self.display_enter_legs_popup(
                f"Unique ID : {unique_id}, Conditional {cas_add_or_switch.capitalize()}",
                cas_add_or_switch,
                unique_id,
                reference_price,
                reference_position,
            )
        else:
            popup_title = None
            flag_cas_order = True

            # Get Unique ID and show the trade popup
            self.get_unique_id_from_user_and_create_trade_popup(
                cas_add_or_switch,
                unique_id,
                popup_title,
                flag_cas_order,
                reference_price,
                reference_position,
                flag_multi_account=flag_multi_account,
            )

    # Method to create trad pop up based on existing unique ids values
    def get_unique_id_from_user_and_create_trade_popup(
        self,
        cas_add_or_switch,
        unique_id,
        popup_title,
        flag_cas_order,
        reference_price,
        reference_position,
        flag_multi_account=False,
        flag_conditional_series=False,
        account_id_series=None,
        bypass_rm_check_series=None,
        flag_execution_engine=None,
        modify_seq_data=None,
        index=None,
    ):
        # Create a enter unique id popup window
        enter_unique_id_popup = tk.Toplevel()

        title = f"Conditional {cas_add_or_switch.capitalize()}, Combination Unique ID: {unique_id}"
        enter_unique_id_popup.title(title)

        enter_unique_id_popup.geometry("500x120")

        # Create main frame
        enter_unique_id_popup_frame = ttk.Frame(enter_unique_id_popup, padding=20)
        enter_unique_id_popup_frame.pack(fill="both", expand=True)

        # Create a frame for the input fields
        enter_unique_id_frame = ttk.Frame(enter_unique_id_popup_frame, padding=20)
        enter_unique_id_frame.pack(fill="both", expand=True)

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            enter_unique_id_frame, text="Enter Unique ID for Combination to trade:"
        ).grid(column=0, row=3, padx=5, pady=5)

        # Adding the entry for user to insert the trading unique id
        unique_id_entry = ttk.Entry(enter_unique_id_frame)
        unique_id_entry.grid(column=1, row=3, padx=5, pady=5)

        # Inserting the default value
        unique_id_entry.insert(0, unique_id)

        if modify_seq_data != None:
            unique_id_entry.delete(0, tkinter.END)

            # Inserting the default value
            unique_id_entry.insert(0, unique_id)

        def on_click_proceed_button():
            # Getting unique ids for active combinations
            local_unique_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

            # Getting unique id use entered
            trading_combo_unique_id = unique_id_entry.get()

            # Checking if format of unique id entered is valid and available in system
            if (
                trading_combo_unique_id.isnumeric()
                and int(float(trading_combo_unique_id))
                in local_unique_to_combo_obj.keys()
            ):
                trading_combo_unique_id = int(float(trading_combo_unique_id))
                enter_unique_id_popup.destroy()

                trade_popup_title = f"Conditional {cas_add_or_switch.capitalize()} Order, Trading Combo UID: {trading_combo_unique_id}, Conditional Combo UID: {unique_id}"

                flag_cas_order = True
                # Insert the OrderType and Quantity etc
                variables.screen.create_trade_popup(
                    cas_add_or_switch,
                    unique_id,
                    trade_popup_title,
                    flag_cas_order,
                    reference_price,
                    reference_position,
                    trading_combo_unique_id,
                    flag_multi_account=flag_multi_account,
                    flag_conditional_series=flag_conditional_series,
                    account_id_series=account_id_series,
                    bypass_rm_check_series=bypass_rm_check_series,
                    flag_execution_engine=flag_execution_engine,
                    modify_seq_data=modify_seq_data,
                    index=index,
                )

            else:
                error_title = f"Invalid Unique ID Entered"
                error_string = (
                    f"Please Enter Valid Unique ID which is available in system"
                )

                variables.screen.display_error_popup(error_title, error_string)

        # Add a button to create the combo
        proceed_button = ttk.Button(
            enter_unique_id_frame, text="Proceed", command=on_click_proceed_button
        )

        proceed_button.grid(column=2, row=3, padx=5, pady=5)

        # Place in center
        enter_unique_id_frame.place(relx=0.5, anchor=tk.CENTER)
        enter_unique_id_frame.place(y=30)

    # Method to create GUI to enter legs input
    def display_enter_legs_popup(
        self,
        title,
        cas_add_or_switch,
        unique_id,
        refer_price,
        refer_position,
        flag_conditional_series=False,
        modify_seq_data=None,
        index=None,
    ):
        # Create a enter_legs popup window
        enter_legs_popup = tk.Toplevel()
        enter_legs_popup.title(title)

        custom_height = max(
            ((len(variables.current_session_accounts) + 3) * 28) + 130, 120
        )

        enter_legs_popup.geometry("660x" + str(custom_height))

        # enter_legs_popup.geometry("450x520")

        # Create main frame
        enter_legs_popup_frame = ttk.Frame(enter_legs_popup, padding=20)
        enter_legs_popup_frame.pack(fill="both", expand=True)

        # Create a frame for the input fields
        enter_legs_frame = ttk.Frame(enter_legs_popup_frame, padding=0)
        enter_legs_frame.pack(side=TOP, pady=10)

        # Create a frame for the positions input fields
        enter_positions_frame = ttk.Frame(enter_legs_popup_frame, padding=0)
        enter_positions_frame.pack(side=BOTTOM, pady=10)

        # Add a label
        ttk.Label(enter_legs_frame, text="Target").grid(
            column=0, row=0, padx=5, pady=5, columnspan=7
        )

        ttk.Separator(enter_legs_frame, orient=VERTICAL).grid(
            column=1, row=1, rowspan=3, sticky="ns", padx=15
        )

        # Add a label and entry field for the user to enter an integer
        ttk.Label(enter_legs_frame, text="Enter Number of Legs").grid(
            column=4, row=1, padx=5, pady=5
        )

        ttk.Separator(enter_legs_frame, orient=VERTICAL).grid(
            column=5, row=1, rowspan=3, sticky="ns", padx=15
        )

        # Add a label
        ttk.Label(enter_legs_frame, text="Bypass RM Check").grid(
            column=6, row=1, padx=5, pady=5
        )

        # Add a label and entry field for the user to enter an unique id
        ttk.Label(enter_legs_frame, text="Target Unique ID").grid(
            column=2, row=1, padx=5, pady=5
        )

        # Add a label and entry field for the user to enter an evalaution unique id
        ttk.Label(enter_legs_frame, text="Evaluation Unique ID").grid(
            column=0, row=1, padx=5, pady=5
        )

        # Entry to input number of legs
        rows_entry = ttk.Entry(enter_legs_frame)
        rows_entry.grid(column=4, row=2, padx=5, pady=5)

        # Add a label
        ttk.Label(enter_legs_frame, text="or").grid(column=3, row=2, padx=5, pady=5)

        # Input entry for target unique id
        unique_id_entry = ttk.Entry(enter_legs_frame)
        unique_id_entry.grid(column=2, row=2, padx=5, pady=5)

        # Input entry for evaluation unique id
        eval_unique_id_entry = ttk.Entry(enter_legs_frame)
        eval_unique_id_entry.grid(column=0, row=2, padx=5, pady=5)

        eval_unique_id_entry.insert(0, unique_id)

        # Create a list of options
        bypass_rm_account_checks_options = ["True"]  # , "False"]

        # Create the combo box
        bypass_rm_account_checks_options_combo_box = ttk.Combobox(
            enter_legs_frame,
            width=18,
            values=bypass_rm_account_checks_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        bypass_rm_account_checks_options_combo_box.current(0)
        bypass_rm_account_checks_options_combo_box.grid(column=6, row=2, padx=5, pady=5)

        # Add a label and entry field for the user to enter an integer
        ttk.Label(enter_positions_frame, text="Account ID").grid(
            column=0, row=3, padx=5, pady=5
        )

        # Add a label and entry field for the user to enter an target postion
        ttk.Label(enter_positions_frame, text="Current Position").grid(
            column=1, row=3, padx=5, pady=5
        )

        # Add a label and entry field for the user to enter an unique id
        ttk.Label(enter_positions_frame, text="Target Position").grid(
            column=2, row=3, padx=5, pady=5
        )

        # target position table input dict
        positions_input_fields_dict = {}

        target_position_insert = refer_position

        if modify_seq_data != None:
            eval_unique_id_entry.delete(0, tkinter.END)

            eval_unique_id_entry.insert(0, modify_seq_data["Evaluation Unique ID"])

            refer_position = refer_position

            target_position_insert = modify_seq_data["Target Position"]

        # create input fields for each tading account
        for indx, account_id in enumerate(variables.current_session_accounts):
            positions_input_fields_dict[account_id] = {}

            positions_input_fields_dict[account_id]["account_id"] = ttk.Entry(
                enter_positions_frame
            )
            positions_input_fields_dict[account_id]["account_id"].grid(
                column=0, row=4 + indx, padx=5, pady=5
            )
            positions_input_fields_dict[account_id]["account_id"].insert(0, account_id)
            positions_input_fields_dict[account_id]["account_id"].config(
                state="readonly"
            )

            positions_input_fields_dict[account_id]["current_positions"] = ttk.Entry(
                enter_positions_frame
            )
            positions_input_fields_dict[account_id]["current_positions"].grid(
                column=1, row=4 + indx, padx=5, pady=5
            )
            positions_input_fields_dict[account_id]["current_positions"].insert(
                0, refer_position[account_id]
            )
            positions_input_fields_dict[account_id]["current_positions"].config(
                state="readonly"
            )

            positions_input_fields_dict[account_id]["target_postions"] = ttk.Entry(
                enter_positions_frame
            )
            positions_input_fields_dict[account_id]["target_postions"].grid(
                column=2, row=4 + indx, padx=5, pady=5
            )
            positions_input_fields_dict[account_id]["target_postions"].insert(
                0, target_position_insert[account_id]
            )

        # Method to validate unique id and create combination pop up
        def on_click_create_button():
            # Get unique id
            unique_id_input = unique_id_entry.get().strip()

            # get eval unqiue id
            eval_unique_id = eval_unique_id_entry.get().strip()

            if eval_unique_id == "":
                error_string = error_title = (
                    "Error, Evaluation Unique ID field is empty"
                )

                variables.screen.display_error_popup(error_title, error_string)

                return

            # Check if eval unique id is non empty
            elif not eval_unique_id.isnumeric():
                error_string = error_title = (
                    "Error, Evaluation Unique ID must be numeric"
                )

                variables.screen.display_error_popup(error_title, error_string)

                return

            elif eval_unique_id != "" and is_integer(eval_unique_id):
                # Get combo object using unique ids
                local_unique_id_to_combo_obj = copy.deepcopy(
                    variables.unique_id_to_combo_obj
                )

                try:
                    all_unique_ids_in_system = (
                        local_unique_id_to_combo_obj.keys()
                    )  # list of all Unique IDs in System

                    if len(all_unique_ids_in_system) < 1:
                        raise Exception("No Unique ID")

                    if int(float(eval_unique_id)) not in all_unique_ids_in_system:
                        error_title = (
                            f"Error, Evaluation Unique ID not available in system"
                        )
                        error_string = (
                            f"Error, Evaluation Unique ID not available in system"
                        )

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                except Exception as e:
                    error_title = f"Error, Evaluation Unique IDs Not Found"
                    error_string = f"Error, Evaluation Unique IDs Not Found"

                    variables.screen.display_error_popup(error_title, error_string)

            else:
                eval_unique_id = int(eval_unique_id)

            # Trying to get the reference price
            try:
                local_combo_buy_sell_price_dict = copy.deepcopy(
                    variables.unique_id_to_prices_dict[int(eval_unique_id)]
                )
                current_buy_price, current_sell_price = (
                    local_combo_buy_sell_price_dict["BUY"],
                    local_combo_buy_sell_price_dict["SELL"],
                )
                refer_price = (
                    float(((current_buy_price + current_sell_price) / 2) * 100) / 100
                )

                local_unique_id_to_positions_dict = copy.deepcopy(
                    variables.map_unique_id_to_positions
                )
                # print(variables.series_sequence_table_df.to_string())
                """for account in refer_position:

                    if account in local_unique_id_to_positions_dict[int(eval_unique_id)]:
                        # print(account)
                        refer_position[account] = \
                        local_unique_id_to_positions_dict[int(eval_unique_id)][account]"""
                # print(variables.series_sequence_table_df.to_string())
            except Exception as e:
                if variables.flag_debug_mode:
                    print(e)

            # get number of legs entered
            num_of_legs = rows_entry.get().strip()

            target_positions_dict = {}

            # create input fields for each tading account
            for indx, account_id in enumerate(variables.current_session_accounts):
                target_position = (
                    positions_input_fields_dict[account_id]["target_postions"]
                    .get()
                    .strip()
                )

                target_positions_dict[account_id] = target_position

                # Get input for bypass rm check
                bypass_rm_account_check = (
                    bypass_rm_account_checks_options_combo_box.get().strip()
                )

                if target_position == "":
                    variables.screen.display_error_popup(
                        f"For Account ID: {account_id}, Total positions must be filled",
                        f"For Account ID: {account_id}, Total positions must be filled",
                    )
                    return

                if not is_integer(target_position):
                    variables.screen.display_error_popup(
                        f"For Account ID: {account_id}, Please Enter Valid Target Position",
                        f"For Account ID: {account_id}, Please Enter Valid Target Position",
                    )
                    return

            # Check if unique id is non empty
            if not is_integer(unique_id_input) and unique_id_input != "":
                error_string = error_title = "Error, Target Unique ID must be numeric"

                variables.screen.display_error_popup(error_title, error_string)

            elif unique_id_input != "" and is_integer(unique_id_input):
                # Get combo object using unique ids
                local_unique_id_to_combo_obj = copy.deepcopy(
                    variables.unique_id_to_combo_obj
                )

                try:
                    all_unique_ids_in_system = (
                        local_unique_id_to_combo_obj.keys()
                    )  # list of all Unique IDs in System

                    if len(all_unique_ids_in_system) < 1:
                        raise Exception("No Unique ID")

                    if int(float(unique_id_input)) not in all_unique_ids_in_system:
                        error_title = f"Error, Target Unique ID not available in system"
                        error_string = (
                            f"Error, Target Unique ID not available in system"
                        )

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    # Get Active Combo Object
                    combo_obj = variables.unique_id_to_combo_obj[
                        int(float(unique_id_input))
                    ]

                    # check if input is empty for number of legs entered
                    if num_of_legs == "":
                        # Buy legs and Sell legs
                        buy_legs = combo_obj.buy_legs
                        sell_legs = combo_obj.sell_legs
                        all_legs = buy_legs + sell_legs

                        # Overwrite value of number of legs entered
                        rows_entry.insert(0, str(len(all_legs)))

                        # Function to open create combo pop up
                        variables.screen.create_combination_popup(
                            rows_entry,
                            cas_add_or_switch,
                            title,
                            enter_legs_popup,
                            unique_id,
                            refer_price,
                            refer_position,
                            combo_obj=combo_obj,
                            target_positions_dict=target_positions_dict,
                            flag_add_legs_conditional_add_switch=True,
                            bypass_rm_account_check=bypass_rm_account_check,
                            evalaution_unique_id=eval_unique_id,
                            flag_conditional_series=flag_conditional_series,
                            modify_seq_data=modify_seq_data,
                            index=index,
                        )

                    else:
                        # Function to open create combo pop up
                        variables.screen.create_combination_popup(
                            rows_entry,
                            cas_add_or_switch,
                            title,
                            enter_legs_popup,
                            unique_id,
                            refer_price,
                            refer_position,
                            combo_obj=combo_obj,
                            target_positions_dict=target_positions_dict,
                            flag_add_legs_conditional_add_switch=True,
                            bypass_rm_account_check=bypass_rm_account_check,
                            evalaution_unique_id=eval_unique_id,
                            flag_conditional_series=flag_conditional_series,
                            modify_seq_data=modify_seq_data,
                            index=index,
                        )

                except Exception as e:
                    error_title = f"Error, Target Unique IDs Not Found"
                    error_string = f"Error,Target Unique IDs Not Found"

                    variables.screen.display_error_popup(error_title, error_string)

            elif unique_id_input == "":
                # Function to open create combo pop up
                variables.screen.create_combination_popup(
                    rows_entry,
                    cas_add_or_switch,
                    title,
                    enter_legs_popup,
                    unique_id,
                    refer_price,
                    refer_position,
                    target_positions_dict=target_positions_dict,
                    bypass_rm_account_check=bypass_rm_account_check,
                    evalaution_unique_id=eval_unique_id,
                    flag_conditional_series=flag_conditional_series,
                    modify_seq_data=modify_seq_data,
                    index=index,
                )

        # Add a button to create the combo
        create_button = ttk.Button(
            enter_positions_frame,
            text="Proceed",
            command=lambda: on_click_create_button(),
        )

        create_button.grid(column=0, row=10, padx=5, pady=5, columnspan=3)

        # Place in center
        enter_legs_frame.place(relx=0)
        enter_legs_frame.place(x=0, y=0)

    # Method to display pop up to entr condition
    def display_enter_condition_popup(
        self,
        unique_id=None,
        cas_add_or_switch=None,
        combo_identified=None,
        reference_price=None,
        reference_position=None,
        order_type=None,
        combo_quantity=None,
        limit_price=None,
        trigger_price=None,
        trail_value=None,
        trading_combination_unique_id=None,
        custom_column_data_dict=None,
        atr_multiple=None,
        atr=None,
        target_position=None,
        account_id=None,
        flag_multi_account=False,
        flag_account_condition=False,
        bypass_rm_check=None,
        evalaution_unique_id=None,
        flag_conditional_series=False,
        flag_execution_engine=False,
        series_pop_up=None,
        modify_seq_data=None,
        index=None,
        combo_quantity_prcnt=None,
    ):
        # Create a enter_condition popup window
        enter_condition_popup = tk.Toplevel()

        # If not for entering expression
        if custom_column_data_dict == None and not flag_account_condition:
            # Title for the popup
            if cas_add_or_switch in ["BUY", "SELL"]:
                title_string = f"Insert {cas_add_or_switch.capitalize()} Condition on Conditional Combo Unique ID: {unique_id}, and Trading Combo Unique ID: {trading_combination_unique_id}"
            else:
                title_string = f"Unique ID: {unique_id}, Insert {cas_add_or_switch.capitalize()} Condition"

            # set hight and width of pop winoow
            enter_condition_popup.geometry("1150x400")

        elif custom_column_data_dict != None and not flag_account_condition:
            title_string = f"Insert Expression For Custom Column"

            # set hight and width of pop winoow
            enter_condition_popup.geometry("900x400")

        elif custom_column_data_dict == None and flag_account_condition:
            title_string = f"Insert Account Condition"

            # set hight and width of pop winoow
            enter_condition_popup.geometry("900x400")

        enter_condition_popup.title(title_string)

        # Create main frame
        enter_condition_popup_frame = ttk.Frame(enter_condition_popup, padding=20)
        enter_condition_popup_frame.pack(fill="both", expand=True)

        # Create a frame for the condition input fields (textbox)
        enter_condition_frame = ttk.Frame(enter_condition_popup_frame, padding=20)
        enter_condition_frame.pack(side=tk.LEFT, fill="both", expand=True)

        # Condition Text Box
        condition_text_box = tk.Text(
            enter_condition_frame,
            width=45,
            height=16,
        )
        condition_text_box.pack(side=tk.LEFT, pady=20)

        if modify_seq_data != None:
            condition_text_box.insert("1.0", modify_seq_data["Condition"])

        #############################
        #### column_fileds_table ####
        #############################
        # Create a frame for the Columns fields table
        column_fileds_frame = ttk.Frame(enter_condition_popup_frame, padding=20)
        column_fileds_frame.pack(
            side=tk.LEFT,
        )

        # Columns fields table Scrollbar
        column_fields_scroll = Scrollbar(column_fileds_frame)
        column_fields_scroll.pack(side="right", fill="y")

        # Create Treeview columns table
        column_fileds_table = ttk.Treeview(
            column_fileds_frame,
            yscrollcommand=column_fields_scroll.set,
            height=10,
            selectmode="extended",
        )

        # Pack to the screen
        column_fileds_table.pack()

        # Configure the scrollbar
        column_fields_scroll.config(command=column_fileds_table.yview)

        # Columns in table
        column_fileds_table_columns = ("Values",)

        # Column in order book table
        column_fileds_table["columns"] = column_fileds_table_columns

        # Creating Columns
        column_fileds_table.column("#0", width=0, stretch="no")
        column_fileds_table.column("Values", anchor="center", width=175)

        # Create Headings
        column_fileds_table.heading("#0", text="", anchor="w")
        column_fileds_table.heading("Values", text="Values", anchor="center")

        # Back ground
        column_fileds_table.tag_configure("oddrow", background="white")
        column_fileds_table.tag_configure("evenrow", background="lightblue")

        #############################
        #### Quick access table ####
        #############################

        # If not for entering expression and account condition
        if custom_column_data_dict == None and not flag_account_condition:
            # Create a frame for the Columns table fields
            quick_access_table_frame = ttk.Frame(
                enter_condition_popup_frame, padding=20
            )
            quick_access_table_frame.pack(
                side=tk.LEFT,
            )  # fill="both", expand=False)

            # Columns fields table Scrollbar
            quick_access_scroll = Scrollbar(quick_access_table_frame)
            quick_access_scroll.pack(side="right", fill="y")

            # Create Treeview columns table
            quick_access_table = ttk.Treeview(
                quick_access_table_frame,
                yscrollcommand=quick_access_scroll.set,
                height=10,
                selectmode="extended",
            )

            # Pack to the screen
            quick_access_table.pack()

            # Configure the scrollbar
            quick_access_scroll.config(command=column_fileds_table.yview)

            # Columns in table
            quick_access_table_columns = ("Price Operators",)

            # Column in order book table
            quick_access_table["columns"] = quick_access_table_columns

            # Creating Columns
            quick_access_table.column("#0", width=0, stretch="no")
            quick_access_table.column("Price Operators", anchor="center", width=175)

            # Create Headings
            quick_access_table.heading("#0", text="", anchor="w")
            quick_access_table.heading(
                "Price Operators", text="Price Operators", anchor="center"
            )

            # Back ground
            quick_access_table.tag_configure("oddrow", background="white")
            quick_access_table.tag_configure("evenrow", background="lightblue")

        # operateors list
        operators_list = variables.cas_table_operators_for_condition

        # If not for entering expression and account condition
        if custom_column_data_dict == None and not flag_account_condition:
            rows_for_column_fileds_table = copy.deepcopy(
                variables.cas_table_fields_for_condition
            )

            if len(variables.current_session_accounts) < 2:
                rows_for_quick_access_table = [
                    "Price Increase By",
                    "Price Decrease By",
                    "Price Adverse Chg By",
                    "Price Favorable Chg By",
                ]

            else:
                rows_for_quick_access_table = [
                    "Price Increase By",
                    "Price Decrease By",
                ]

                rows_for_column_fileds_table.remove("Price Adverse Chg By")
                rows_for_column_fileds_table.remove("Price Favorable Chg By")

            # Insert rows in quick access tabl
            for i_num, val in enumerate(rows_for_quick_access_table):
                val = (val,)
                if i_num % 2 == 1:
                    quick_access_table.insert(
                        "",
                        "end",
                        iid=val,
                        text=val,
                        values=val,
                        tags=("oddrow",),
                    )
                else:
                    quick_access_table.insert(
                        "",
                        "end",
                        iid=val,
                        text=val,
                        values=val,
                        tags=("evenrow",),
                    )

        # If not for cas condition and account condition
        elif custom_column_data_dict != None and not flag_account_condition:
            rows_for_column_fileds_table = copy.deepcopy(
                variables.cas_table_fields_for_expression
            )

        # If not for cas condition and entering expression
        elif custom_column_data_dict == None and flag_account_condition:
            rows_for_column_fileds_table = copy.deepcopy(
                variables.accounts_table_columns[1:-1] + ["Tickers PNL"]
            )

            operators_list = ["%"] + operators_list

        # Inserting values in 'column_fileds_table'
        for i_num, val in enumerate(rows_for_column_fileds_table):
            val = (val,)
            if i_num % 2 == 1:
                column_fileds_table.insert(
                    "",
                    "end",
                    iid=val,
                    text=val,
                    values=val,
                    tags=("oddrow",),
                )
            else:
                column_fileds_table.insert(
                    "",
                    "end",
                    iid=val,
                    text=val,
                    values=val,
                    tags=("evenrow",),
                )

        #####################
        #### operators_table ####
        #####################
        # Create a frame for the Columns table fields
        operator_table_frame = ttk.Frame(enter_condition_popup_frame, padding=20)
        operator_table_frame.pack(
            side=tk.LEFT,
        )  #  fill="both", expand=False)

        # Operator Table Scrollbar
        operator_table_tree_scroll = Scrollbar(operator_table_frame)
        operator_table_tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        operator_table = ttk.Treeview(
            operator_table_frame,
            yscrollcommand=operator_table_tree_scroll.set,
            height=10,
            selectmode="extended",
        )

        # Pack to the screen
        operator_table.pack()

        # Configure the scrollbar
        operator_table_tree_scroll.config(command=operator_table.yview)

        # Column name
        operator_table_columns = ("Operators",)

        # Column in order book table
        operator_table["columns"] = operator_table_columns

        # Creating Columns
        operator_table.column("#0", width=0, stretch="no")
        operator_table.column("Operators", anchor="center", width=175)

        # Create Headings
        operator_table.heading("#0", text="", anchor="w")
        operator_table.heading("Operators", text="Operators", anchor="center")

        # Back ground
        operator_table.tag_configure("oddrow", background="white")
        operator_table.tag_configure("evenrow", background="lightblue")

        # Inserting Operators in 'operator_table'
        for i_num, val in enumerate(operators_list):
            val = (val,)
            if i_num % 2 == 1:
                operator_table.insert(
                    "",
                    "end",
                    iid=val,
                    text=val,
                    values=val,
                    tags=("oddrow",),
                )
            else:
                operator_table.insert(
                    "",
                    "end",
                    iid=val,
                    text=val,
                    values=val,
                    tags=("evenrow",),
                )

        # Function to handle clicking on a Treeview row/cell
        def handle_click(event):
            item = event.widget.focus()
            selected_field_row_value = event.widget.item(item)["values"]

            # If row header is selected return
            if selected_field_row_value == "":
                return
            else:
                value = selected_field_row_value[0]
                val = f" {value} "
                condition_text_box.insert("insert", val)

        # Bind the Treeview tables to the click handler function
        column_fileds_table.bind("<ButtonRelease-1>", handle_click)
        operator_table.bind("<ButtonRelease-1>", handle_click)

        # If not for entering expression and account condition
        if custom_column_data_dict == None and not flag_account_condition:
            # Bind the Treeview tables to the click handler function
            quick_access_table.bind("<ButtonRelease-1>", handle_click)

        # Add the Treeview tables to the window
        column_fileds_table.pack(side=tk.RIGHT)
        operator_table.pack(side=tk.RIGHT)

        # Method to get expression
        def get_input_of_expression_and_check_it():
            # User Entered expression
            user_entered_expression = condition_text_box.get(1.0, tk.END).strip()

            # Validate Condition Here
            flag_condition_passed, error_string = check_basic_condition(
                user_entered_expression, None, None, None, flag_check_expression=True
            )

            key = "Flag Filter"

            # if this is for filter condition
            if key in custom_column_data_dict:
                # If expression is valid
                if flag_condition_passed:
                    # check if enter condition pop up is non None
                    if enter_condition_popup != None:
                        # Destroy pop up
                        enter_condition_popup.destroy()

                    # Add condition in db file
                    insert_filter_condition_in_db(
                        custom_column_data_dict["Condition Name"],
                        user_entered_expression,
                        "Yes",
                    )

                    # sleep for few seconds
                    time.sleep(variables.sleep_time_db)

                    # Update custom column table
                    variables.screen.screen_filter_obj.update_filter_table()

                else:
                    # Show error pop up
                    error_title = error_string = "Filter condition is invalid."

                    variables.screen.display_error_popup(error_title, error_string)

            else:
                # If expression is valid
                if flag_condition_passed:
                    # check if enter condition pop up is non None
                    if enter_condition_popup != None:
                        # Destroy pop up
                        enter_condition_popup.destroy()

                    # Add column in json file
                    add_custom_column_in_json(
                        custom_column_data_dict["Column Name"],
                        user_entered_expression,
                        custom_column_data_dict["Column Description"],
                    )

                    # Update custom column table
                    variables.screen.screen_custom_columns_obj.update_custom_column_table()

                else:
                    # Show error pop up
                    error_title = error_string = "Custom column expression is invalid."

                    variables.screen.display_error_popup(error_title, error_string)

        # Method to get condition for account
        def get_input_of_account_condition_and_check_it():
            # User Entered expression
            user_entered_condition = condition_text_box.get(1.0, tk.END).strip()

            pattern = r"(\d+)\s*%|%"

            def replace_percent(match):
                return match.group(1) + "%"

            user_entered_condition = re.sub(
                pattern, replace_percent, user_entered_condition
            )

            # Validate Condition Here
            flag_condition_passed, error_string = check_account_condition(
                user_entered_condition
            )

            # If expression is valid
            if flag_condition_passed:
                # check if enter condition pop up is non None
                if enter_condition_popup != None:
                    # Destroy pop up
                    enter_condition_popup.destroy()

                # Method for input of conditions
                variables.screen.screen_accounts_obj.get_accounts_for_condition(
                    user_entered_condition
                )

            else:
                # Show error pop up
                error_title = error_string = "Account condition is invalid."

                variables.screen.display_error_popup(error_title, error_string)

        # If not for entering expression
        if custom_column_data_dict == None and not flag_account_condition:
            # Create a frame for the condition input fields
            add_condition_frame = ttk.Frame(enter_condition_popup_frame, padding=20)
            add_condition_frame.pack(
                side=tk.BOTTOM,
            )  #  fill="x", expand=True)

            def on_click_insert_condition_button():
                """if series_pop_up != None:


                series_pop_up.config(state='Normal')

                series_pop_up.insert(0, cond)

                return"""

                self.get_condition_text(
                    unique_id,
                    condition_text_box,
                    combo_identified,
                    cas_add_or_switch,
                    reference_price,
                    reference_position,
                    enter_condition_popup,
                    order_type,
                    combo_quantity,
                    limit_price,
                    trigger_price,
                    trail_value,
                    trading_combination_unique_id,
                    atr_multiple=atr_multiple,
                    atr=atr,
                    target_position=target_position,
                    account_id=account_id,
                    flag_multi_account=flag_multi_account,
                    bypass_rm_check=bypass_rm_check,
                    evalaution_unique_id=evalaution_unique_id,
                    flag_conditional_series=flag_conditional_series,
                    execution_engine=flag_execution_engine,
                    series_pop_up=series_pop_up,
                    modify_seq_data=modify_seq_data,
                    index=index,
                    combo_quantity_prcnt=combo_quantity_prcnt,
                )

            # XXXXXXXX
            # XXXXXXXX

            # "Insert Condition" Button
            insert_condition_button = tk.Button(
                add_condition_frame,
                text="Insert Condition",
                command=lambda: on_click_insert_condition_button(),
            )

            # Pack the button
            insert_condition_button.pack(side=tk.BOTTOM, padx=20)

            # Place in center
            add_condition_frame.place(relx=0.5, anchor=tk.CENTER)
            add_condition_frame.place(y=350)

        elif custom_column_data_dict != None and not flag_account_condition:
            # Create a frame for the condition input fields
            add_condition_frame = ttk.Frame(enter_condition_popup_frame, padding=20)
            add_condition_frame.pack(
                side=tk.BOTTOM,
            )  #  fill="x", expand=True)

            # "Insert Condition" Button
            insert_condition_button = tk.Button(
                add_condition_frame,
                text="Insert Condition",
                command=lambda: get_input_of_expression_and_check_it(),
            )

            # Pack the button
            insert_condition_button.pack(side=tk.BOTTOM, padx=20)

            # Place in center
            add_condition_frame.place(relx=0.5, anchor=tk.CENTER)
            add_condition_frame.place(y=350)

        elif custom_column_data_dict == None and flag_account_condition:
            # Create a frame for the condition input fields
            add_condition_frame = ttk.Frame(enter_condition_popup_frame, padding=20)
            add_condition_frame.pack(
                side=tk.BOTTOM,
            )  #  fill="x", expand=True)

            # "Insert Condition" Button
            insert_condition_button = tk.Button(
                add_condition_frame,
                text="Insert Condition",
                command=lambda: get_input_of_account_condition_and_check_it(),
            )

            # Pack the button
            insert_condition_button.pack(side=tk.BOTTOM, padx=20)

            # Place in center
            add_condition_frame.place(relx=0.5, anchor=tk.CENTER)
            add_condition_frame.place(y=350)

    # Method to check reference positions for specific token
    def check_ref_position_for_specific_tokens(
        self, reference_position, user_entered_condition
    ):
        # Init
        flag_condition_passed = {}

        # check if variable is dictionary
        if isinstance(reference_position, dict):
            # Iterate all accounts
            for account_id in reference_position:
                # Check if ref positions is not 0 and check if conditions 'price adverse by' and 'price favourable by' present
                if int(reference_position[account_id]) == 0 and (
                    "Price Adverse Chg By" in user_entered_condition
                    or "Price Favorable Chg By" in user_entered_condition
                ):
                    # Set value to false
                    flag_condition_passed[account_id] = False

                else:
                    # Set value to True
                    flag_condition_passed[account_id] = True

        else:
            # Check if ref positions is not 0 and check if conditions 'price adverse by' and 'price favourable by' present
            if reference_position == 0 and (
                "Price Adverse Chg By" in user_entered_condition
                or "Price Favorable Chg By" in user_entered_condition
            ):
                # Set value to false
                flag_condition_passed = False

            else:
                # Set value to True
                flag_condition_passed = True

        return flag_condition_passed

    # Grab the text from the text box, and process the condition and cas legs
    def get_condition_text(
        self,
        unique_id,
        condition_text_box,
        combo_identified,
        cas_type,
        reference_price,
        reference_position,
        enter_condition_popup,
        order_type,
        combo_quantity,
        order_limit_price,
        order_trigger_price,
        order_trail_value,
        trading_combination_unique_id=None,
        atr_multiple=None,
        atr=None,
        target_position=None,
        account_id=None,
        flag_multi_account=False,
        bypass_rm_check=None,
        evalaution_unique_id=None,
        flag_conditional_series=False,
        series_id=None,
        execution_engine=None,
        series_pop_up=None,
        modify_seq_data=None,
        index=None,
        combo_quantity_prcnt=None,
    ):
        # check if instance is str
        if isinstance(condition_text_box, str):
            user_entered_condition = condition_text_box

        else:
            # User Entered Condition
            user_entered_condition = condition_text_box.get(1.0, tk.END)

        # Validate Condition Here
        flag_condition_passed_res, error_string = check_basic_condition(
            user_entered_condition, unique_id, reference_price, reference_position
        )

        flag_condition_passed = self.check_ref_position_for_specific_tokens(
            reference_position, user_entered_condition
        )

        # get passed down value of execution engine
        if execution_engine != None:
            flag_execution_engine = execution_engine

        else:
            # get flag for execution engine
            flag_execution_engine = variables.flag_use_execution_engine

        # In case of cas add or switch we make flaf execution engine False
        if cas_type in ["ADD", "SWITCH"]:
            flag_execution_engine = False

        else:
            evalaution_unique_id = unique_id

        # If Condition passed
        if flag_condition_passed_res:
            # display condition in series pop up
            if series_pop_up != None:
                # Check if it's a Pandas DataFrame
                if not isinstance(
                    variables.series_sequence_table_df, pd.core.frame.DataFrame
                ):
                    # destroy pop up
                    enter_condition_popup.destroy()

                    return

                # making it normal
                series_pop_up.config(state="Normal")

                series_pop_up.delete(0, tk.END)

                # editing entry content
                series_pop_up.insert(0, user_entered_condition)
                # making it readonly
                series_pop_up.config(state="readonly")
                # destroy pop up
                enter_condition_popup.destroy()
                return

            # Try Evaluate it and also check the refer_pos, refer_price
            if variables.flag_debug_mode:
                print("Condition Passed")

            # check if enter condition pop up is non None
            if enter_condition_popup != None:
                # Destroy pop up
                enter_condition_popup.destroy()

            # if flag for condition series is true
            if flag_conditional_series:
                # Check if it's a Pandas DataFrame
                if not isinstance(
                    variables.series_sequence_table_df, pd.core.frame.DataFrame
                ):
                    return

                # replace %
                condition = user_entered_condition.strip().replace("%", "%%")

                # init
                status_seq = "Queued"

                # check if cas type is add or switch
                if cas_type in ["ADD", "SWITCH"]:
                    # Incremental combo info string
                    ticker_info_string = make_informative_combo_string(combo_identified)

                    # set vlaue of trading unique id
                    trading_combination_unique_id = "None"

                    combo_quantity = "None"

                else:
                    ticker_info_string = "N/A"

                    # se value of evaluation unique id
                    evalaution_unique_id = "None"

                # if dataframe is empty
                if variables.series_sequence_table_df.empty:
                    # table id init
                    table_id = 1

                    # init
                    status_seq = "Active"

                else:
                    # table id
                    """table_id = (
                        variables.series_sequence_table_df["Table ID"].iloc[-1] + 1
                    )"""

                    table_ids_list_line = variables.series_sequence_table_df[
                        "Table ID"
                    ].to_list()

                    table_id = max(table_ids_list_line) + 1

                    if index != None:
                        status_lst = variables.series_sequence_table_df[
                            "Status"
                        ].to_list()

                        if status_lst.count("Active") == 0:
                            status_seq = "Active"

                if modify_seq_data != None:
                    table_id = modify_seq_data["Table ID"]

                    status_seq = modify_seq_data["Status"]

                """if target_position != None and not variables.series_sequence_table_df.empty:

                    target_positions_lst = variables.series_sequence_table_df['Target Positions'].to_list()

                    for dict in target_positions_lst:

                        if dict not in [None, 'None']:

                            reference_position = dict"""

                if flag_multi_account and cas_type in ["BUY", "SELL"]:
                    target_position = combo_quantity

                    combo_quantity = combo_quantity_prcnt

                # print(variables.series_sequence_table_df.to_string())

                # Watchlist cas condition dataframe update
                cas_condition_row_values = (
                    unique_id,
                    trading_combination_unique_id,
                    evalaution_unique_id,
                    cas_type,
                    ticker_info_string,
                    condition,
                    status_seq,
                    order_type,
                    combo_quantity,
                    order_limit_price,
                    order_trigger_price,
                    order_trail_value,
                    atr_multiple,
                    table_id,
                    combo_identified,
                    reference_position,
                    target_position,
                )

                # Creating dataframe for row data
                cas_condition_row_df = pd.DataFrame(
                    [cas_condition_row_values],
                    columns=variables.series_sequence_tble_columns,
                )

                if modify_seq_data != None:
                    table_id_list = variables.series_sequence_table_df[
                        "Table ID"
                    ].to_list()

                    idex = table_id_list.index(int(table_id))

                    # print(variables.series_sequence_table_df.to_string())

                    variables.series_sequence_table_df.iloc[idex] = (
                        cas_condition_row_values
                    )

                    # print(variables.series_sequence_table_df.to_string())

                else:
                    if index == None:
                        # Merge row with combo details dataframe
                        variables.series_sequence_table_df = pd.concat(
                            [variables.series_sequence_table_df, cas_condition_row_df]
                        )

                        variables.series_sequence_table_df = (
                            variables.series_sequence_table_df.reset_index(drop=True)
                        )

                    # print(variables.series_sequence_table_df.to_string())

                    if index != None:
                        # Get the upper and lower parts of the DataFrame
                        upper_df = variables.series_sequence_table_df.iloc[
                            :index
                        ]  # Rows before the insertion index
                        lower_df = variables.series_sequence_table_df.iloc[
                            index:
                        ]  # Rows after the insertion index

                        # Concatenate the upper part, new row, and lower part
                        variables.series_sequence_table_df = pd.concat(
                            [upper_df, cas_condition_row_df, lower_df]
                        )

                        variables.series_sequence_table_df = (
                            variables.series_sequence_table_df.reset_index(drop=True)
                        )

                # Replace NaN values with 'None'
                variables.series_sequence_table_df = (
                    variables.series_sequence_table_df.fillna("None")
                )

                # update conditional series table
                variables.screen.screen_conditional_series_tab.update_create_series_pop_up_table()

                # print(variables.series_sequence_table_df.to_string())

                return

            # In case of cas add or switch we make unique id and trading combination unique id same
            if cas_type in ["ADD", "SWITCH"]:
                trading_combination_unique_id = unique_id

                for account_id_in_system in variables.current_session_accounts:
                    # Init
                    status = "Pending"
                    reason_for_failed = "None"

                    # check for account , condition is valid or not
                    if not flag_condition_passed[account_id_in_system]:
                        status = "Failed"
                        reason_for_failed = "Reference position is 0"

                        if series_id not in [None, "None"]:
                            terminate_series(unique_id, series_id)

                    # Get Trigger Price Value
                    trigger_price = self.get_trigger_price_for_condition(
                        unique_id,
                        cas_type,
                        user_entered_condition,
                        reference_price,
                        reference_position[account_id_in_system],
                    )

                    # Inserting condition in the DB
                    insert_cas_condition_in_db(
                        unique_id,
                        cas_type,
                        user_entered_condition,
                        reference_price,
                        reference_position[account_id_in_system],
                        trigger_price,
                        status,
                        order_type,
                        combo_quantity,
                        order_limit_price,
                        order_trigger_price,
                        order_trail_value,
                        trading_combination_unique_id,
                        atr_multiple=atr_multiple,
                        atr=atr,
                        target_position=target_position[account_id_in_system],
                        account_id=account_id_in_system,
                        reason_for_failed=reason_for_failed,
                        bypass_rm_check=bypass_rm_check,
                        flag_execution_engine=flag_execution_engine,
                        evalaution_unique_id=evalaution_unique_id,
                        series_id=series_id,
                    )

            else:
                # set value for evaluation uniuq id
                evalaution_unique_id = unique_id

                if not flag_multi_account:
                    # Init
                    status = "Pending"
                    reason_for_failed = "None"

                    # check for account , condition is valid or not
                    if not flag_condition_passed:
                        status = "Failed"
                        reason_for_failed = "Reference position is 0"

                        if series_id not in [None, "None"]:
                            terminate_series(unique_id, series_id)

                    # Get Trigger Price Value
                    trigger_price = self.get_trigger_price_for_condition(
                        unique_id,
                        cas_type,
                        user_entered_condition,
                        reference_price,
                        reference_position,
                    )

                    # Inserting condition in the DB
                    insert_cas_condition_in_db(
                        unique_id,
                        cas_type,
                        user_entered_condition,
                        reference_price,
                        reference_position,
                        trigger_price,
                        status,
                        order_type,
                        combo_quantity,
                        order_limit_price,
                        order_trigger_price,
                        order_trail_value,
                        trading_combination_unique_id,
                        atr_multiple=atr_multiple,
                        atr=atr,
                        target_position=target_position,
                        account_id=account_id,
                        reason_for_failed=reason_for_failed,
                        bypass_rm_check=bypass_rm_check,
                        flag_execution_engine=flag_execution_engine,
                        evalaution_unique_id=evalaution_unique_id,
                        series_id=series_id,
                    )

                else:
                    # Iterate keys of dictionaries
                    for account in combo_quantity:
                        # Get value of combo quantity for account
                        combo_quantity_for_count = combo_quantity[account]

                        # Init
                        status = "Pending"
                        reason_for_failed = "None"

                        # check for account , condition is valid or not
                        if not flag_condition_passed[account]:
                            status = "Failed"
                            reason_for_failed = "Reference position is 0"

                            if series_id not in [None, "None"]:
                                terminate_series(unique_id, series_id)

                        # Check if quantity is greater than 0
                        if combo_quantity_for_count > 0:
                            # Get Trigger Price Value
                            trigger_price = self.get_trigger_price_for_condition(
                                unique_id,
                                cas_type,
                                user_entered_condition,
                                reference_price,
                                reference_position[account],
                            )

                            # Inserting condition in the DB
                            insert_cas_condition_in_db(
                                unique_id,
                                cas_type,
                                user_entered_condition,
                                reference_price,
                                reference_position[account],
                                trigger_price,
                                status,
                                order_type,
                                combo_quantity[account],
                                order_limit_price,
                                order_trigger_price,
                                order_trail_value,
                                trading_combination_unique_id,
                                atr_multiple=atr_multiple,
                                atr=atr,
                                target_position=target_position,
                                account_id=account,
                                reason_for_failed=reason_for_failed,
                                bypass_rm_check=bypass_rm_check,
                                flag_execution_engine=flag_execution_engine,
                                evalaution_unique_id=evalaution_unique_id,
                                series_id=series_id,
                            )

            # Init
            ticker_info_string = "N/A"

            if cas_type in ["ADD", "SWITCH"]:
                # Insert Legs in Cas Table
                insert_combination_db(True, combo_identified, insert_in_cas_table=True)

                # Make combo available to class variables
                variables.cas_unique_id_to_combo_obj[unique_id] = combo_identified

                # Incremental combo info string
                ticker_info_string = make_informative_combo_string(combo_identified)

                # what data do we need for the combo 1Day or 1H for CAS Correlation(N-Day) Longterm Values
                only_stk_fut = False

                # # Checking Combo type, and map con_id to contract
                for leg_obj_ in combo_identified.buy_legs + combo_identified.sell_legs:
                    if leg_obj_.sec_type in ["OPT", "FOP"]:
                        only_stk_fut = False

                    # Mapping con_id to contract
                    variables.map_con_id_to_contract[leg_obj_.con_id] = (
                        leg_obj_.contract
                    )

                # Update the values of 'cas_conditional_legs_map_con_id_to_action_type_and_combo_type' used while getting HighLowCAS prices (for Correlation)
                for leg_obj_ in combo_identified.buy_legs + combo_identified.sell_legs:
                    # Coind for leg
                    conid = leg_obj_.con_id
                    action = leg_obj_.action

                    if (
                        conid
                        not in variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type
                    ):
                        variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type[
                            conid
                        ] = {
                            "BUY": {"1H": 0, "1D": 0},
                            "SELL": {"1H": 0, "1D": 0},
                        }

                    # Count which data is required how many times for CAS
                    if only_stk_fut:
                        variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type[
                            conid
                        ][action]["1D"] += 1
                    else:
                        variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type[
                            conid
                        ][action]["1H"] += 1

                for account_id_in_system in variables.current_session_accounts:
                    status = "Pending"
                    reason_for_failed = "None"

                    if not flag_condition_passed[account_id_in_system]:
                        status = "Failed"
                        reason_for_failed = "Reference position is 0"

                        if series_id not in [None, "None"]:
                            terminate_series(unique_id, series_id)

                    # Get Trigger Price Value
                    trigger_price = self.get_trigger_price_for_condition(
                        unique_id,
                        cas_type,
                        user_entered_condition,
                        reference_price,
                        reference_position[account_id_in_system],
                    )

                    # Insert the condition in cas_condition_table
                    values = (
                        unique_id,
                        trading_combination_unique_id,
                        evalaution_unique_id,
                        cas_type,
                        ticker_info_string,
                        user_entered_condition.strip(),
                        f"{float(reference_price):,.2f}",
                        reference_position[account_id_in_system],
                        target_position[account_id_in_system],
                        trigger_price,
                        status,
                        reason_for_failed,
                        "N/A",
                        account_id_in_system,
                        str(flag_execution_engine),
                        series_id,
                        f"{unique_id}_{account_id_in_system}",
                    )
                    self.insert_cas_condition_row_in_cas_condition_table(values)

                    # Watchlist cas condition dataframe update
                    cas_condition_row_values = (
                        unique_id,
                        trading_combination_unique_id,
                        evalaution_unique_id,
                        cas_type,
                        ticker_info_string,
                        user_entered_condition.strip(),
                        f"{float(reference_price):,.2f}",
                        reference_position[account_id_in_system],
                        target_position[account_id_in_system],
                        trigger_price,
                        status,
                        reason_for_failed,
                        "N/A",
                        account_id_in_system,
                        str(flag_execution_engine),
                        series_id,
                        f"{unique_id}_{account_id_in_system}",
                    )

                    # Creating dataframe for row data
                    cas_condition_row_df = pd.DataFrame(
                        [cas_condition_row_values],
                        columns=variables.cas_condition_table_columns,
                    )

                    # Merge row with combo details dataframe
                    variables.cas_condition_table_dataframe = pd.concat(
                        [variables.cas_condition_table_dataframe, cas_condition_row_df],
                        ignore_index=True,
                    )

            else:
                if not flag_multi_account:
                    # Init
                    status = "Pending"
                    reason_for_failed = "None"

                    # check for account , condition is valid or not
                    if not flag_condition_passed:
                        status = "Failed"
                        reason_for_failed = "Reference position is 0"

                        if series_id not in [None, "None"]:
                            terminate_series(unique_id, series_id)

                    # Insert the condition in cas_condition_table
                    values = (
                        unique_id,
                        trading_combination_unique_id,
                        evalaution_unique_id,
                        cas_type,
                        ticker_info_string,
                        user_entered_condition.strip(),
                        f"{float(reference_price):,.2f}",
                        reference_position,
                        target_position,
                        trigger_price,
                        status,
                        reason_for_failed,
                        "N/A",
                        account_id,
                        str(flag_execution_engine),
                        series_id,
                        f"{unique_id}_{account_id}",
                    )
                    self.insert_cas_condition_row_in_cas_condition_table(values)

                    # Watchlist cas condition dataframe update
                    cas_condition_row_values = (
                        unique_id,
                        trading_combination_unique_id,
                        evalaution_unique_id,
                        cas_type,
                        ticker_info_string,
                        user_entered_condition.strip(),
                        f"{float(reference_price):,.2f}",
                        reference_position,
                        target_position,
                        trigger_price,
                        status,
                        reason_for_failed,
                        "N/A",
                        account_id,
                        str(flag_execution_engine),
                        series_id,
                        f"{unique_id}_{account_id}",
                    )

                    # Creating dataframe for row data
                    cas_condition_row_df = pd.DataFrame(
                        [cas_condition_row_values],
                        columns=variables.cas_condition_table_columns,
                    )

                    # Merge row with combo details dataframe
                    variables.cas_condition_table_dataframe = pd.concat(
                        [variables.cas_condition_table_dataframe, cas_condition_row_df],
                        ignore_index=True,
                    )
                else:
                    for account in combo_quantity:
                        # Init
                        status = "Pending"
                        reason_for_failed = "None"

                        # check for account , condition is valid or not
                        if not flag_condition_passed[account]:
                            status = "Failed"
                            reason_for_failed = "Reference position is 0"

                            if series_id not in [None, "None"]:
                                terminate_series(unique_id, series_id)

                        # Get value of combo quantity for account
                        combo_quantity_for_count = combo_quantity[account]

                        # Check if quantity is greater than 0
                        if combo_quantity_for_count > 0:
                            # Insert the condition in cas_condition_table
                            values = (
                                unique_id,
                                trading_combination_unique_id,
                                evalaution_unique_id,
                                cas_type,
                                ticker_info_string,
                                user_entered_condition.strip(),
                                f"{float(reference_price):,.2f}",
                                reference_position[account],
                                target_position,
                                trigger_price,
                                status,
                                reason_for_failed,
                                "N/A",
                                account,
                                str(flag_execution_engine),
                                series_id,
                                f"{unique_id}_{account}",
                            )
                            self.insert_cas_condition_row_in_cas_condition_table(values)

                            # Watchlist cas condition dataframe update
                            cas_condition_row_values = (
                                unique_id,
                                trading_combination_unique_id,
                                evalaution_unique_id,
                                cas_type,
                                ticker_info_string,
                                user_entered_condition.strip(),
                                f"{float(reference_price):,.2f}",
                                reference_position[account],
                                target_position,
                                trigger_price,
                                status,
                                reason_for_failed,
                                "N/A",
                                account,
                                str(flag_execution_engine),
                                series_id,
                                f"{unique_id}_{account}",
                            )

                            # Creating dataframe for row data
                            cas_condition_row_df = pd.DataFrame(
                                [cas_condition_row_values],
                                columns=variables.cas_condition_table_columns,
                            )

                            # Merge row with combo details dataframe
                            variables.cas_condition_table_dataframe = pd.concat(
                                [
                                    variables.cas_condition_table_dataframe,
                                    cas_condition_row_df,
                                ],
                                ignore_index=True,
                            )

        else:
            # Print to console
            if variables.flag_debug_mode:
                print("Condition Failed")

            # Show popup
            variables.screen.display_error_popup(
                f"Unique ID : {unique_id}, Condition Error", error_string
            )

    # Method to display conditional order filled pop up
    def display_condition_triggered_informative_popup(
        self,
        existing_combo_unique_id,
        new_combo_unique_id,
        cas_add_or_switch,
        cas_condition,
        reference_price,
        reference_position,
        new_unique_id_for_old_combo,
        series_id=None,
    ):
        # Create a condition triggered_informative popup window
        condition_triggered_informative_popup = tk.Toplevel()
        condition_triggered_informative_popup.title(
            f"Unique ID: {existing_combo_unique_id}, Conditional {cas_add_or_switch.capitalize()} Triggered"
        )

        # Custom Width, Geometry
        custom_width = 80 * len(variables.leg_columns_combo_detail_gui) + 60
        condition_triggered_informative_popup.geometry(f"{custom_width}x750")

        # Create main frame
        condition_triggered_informative_popup_frame = ttk.Frame(
            condition_triggered_informative_popup, padding=20
        )
        condition_triggered_informative_popup_frame.pack(fill="both", expand=True)

        # Create Label frame for the "Existing Combination"
        existing_label_frame = ttk.Frame(
            condition_triggered_informative_popup_frame, padding=10
        )
        existing_label_frame.pack(fill="both", expand=True)

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            existing_label_frame,
            text="Existing Combination Details",
            font=("Arial", 12),
        ).pack(side=tk.TOP, fill="both", expand=True)

        # Place existing combination frame in center
        existing_label_frame.place(relx=0.5, anchor=tk.CENTER)
        existing_label_frame.place(y=10)

        # Create a frame for displaying the existing combo details
        existing_combo_details_frame = ttk.Frame(
            condition_triggered_informative_popup_frame,
        )
        existing_combo_details_frame.pack(side=tk.TOP, fill="both", expand=True)

        # Place in center
        existing_combo_details_frame.place(relx=0.5, anchor=tk.CENTER)
        existing_combo_details_frame.place(y=100)

        # Display the Existing Details combo details in table
        self.add_combination_detail_to_informative_popup(
            existing_combo_unique_id, existing_combo_details_frame, False
        )

        # Create Label frame for the CAS order type label
        cas_add_switch_label_frame = ttk.Frame(
            condition_triggered_informative_popup_frame, padding=10
        )
        cas_add_switch_label_frame.pack(fill="both", expand=True)

        if series_id not in [None, "None", "N/A"]:
            origin_of_order_txt = (
                f"Origin of Order : Conditional Series, Series ID : {series_id}"
            )

        else:
            origin_of_order_txt = (
                f"Origin of Order : Conditional {cas_add_or_switch.capitalize()}"
            )

        # Add a label "CAS order Type"
        ttk.Label(
            cas_add_switch_label_frame,
            text=f"Conditional {cas_add_or_switch.capitalize()} Order, Reference Price = {reference_price} and Reference Position = {reference_position}",
            font=("Arial", 12),
        ).pack(side=tk.TOP, fill="both", expand=True)
        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            cas_add_switch_label_frame, text=origin_of_order_txt, font=("Arial", 12)
        ).pack(side=tkinter.TOP, anchor=tk.CENTER)

        # Place in frmae in center
        cas_add_switch_label_frame.place(relx=0.5, anchor=tk.CENTER)
        cas_add_switch_label_frame.place(y=215)

        # Create Label frame for the "Incremental Combination"
        incremental_label_frame = ttk.Frame(
            condition_triggered_informative_popup_frame, padding=10
        )
        incremental_label_frame.pack(fill="both", expand=True)

        # Add a label for the "Incremental Combination"
        ttk.Label(
            incremental_label_frame,
            text="Incremental Combination Details",
            font=("Arial", 12),
        ).pack(side=tk.TOP, fill="both", expand=True)

        # Place the "Incremental Combination" frame center
        incremental_label_frame.place(relx=0.5, anchor=tk.CENTER)
        incremental_label_frame.place(y=260)

        # Create a frame for displaying the incremental combo details
        incremental_combo_details_frame = ttk.Frame(
            condition_triggered_informative_popup_frame,
        )
        incremental_combo_details_frame.pack(side=tk.BOTTOM, fill="both", expand=True)

        # Place in the "Incremental combo" details frame in center
        incremental_combo_details_frame.place(relx=0.5, anchor=tk.CENTER)
        incremental_combo_details_frame.place(y=350)

        # Display the "Incremental combo" details table
        self.add_combination_detail_to_informative_popup(
            existing_combo_unique_id, incremental_combo_details_frame, True
        )

        # Create Label frame for the "Incremental Combination"
        cas_condition_label_frame = ttk.Frame(
            condition_triggered_informative_popup_frame, padding=10
        )
        cas_condition_label_frame.pack(fill="both", expand=True)

        # Add a label for the "Incremental Combination"
        ttk.Label(cas_condition_label_frame, text="Condition", font=("Arial", 12)).pack(
            side=tk.TOP, fill="both", expand=True
        )

        # Place the "Incremental Combination" frame center
        cas_condition_label_frame.place(relx=0.5, anchor=tk.CENTER)
        cas_condition_label_frame.place(y=460)

        # Condition Text Box
        condition_text_box = tk.Text(
            condition_triggered_informative_popup_frame,
            width=117,
            height=8,
            font=("Helvetica", 12),
        )
        condition_text_box.pack(
            side=tk.LEFT,
        )

        # Insert condition in textbox and disable the text box so user can not change condition in the textbox
        condition_text_box.insert(tk.END, f"{cas_condition}")
        condition_text_box.configure(state="disabled")

        # Place in center
        condition_text_box.place(relx=0.5, anchor=tk.CENTER)
        condition_text_box.place(y=560)

        # Create Label frame for the displaying "Old Unique Id" and "New Unique Id"
        old_to_new_unique_id_label_frame = ttk.Frame(
            condition_triggered_informative_popup_frame, padding=10
        )
        old_to_new_unique_id_label_frame.pack(fill="both", expand=True)

        # Mssg for the label
        mssg_string = f"The existing combination with Unique ID: {existing_combo_unique_id} has been replaced by a new combination with Unique ID: {new_combo_unique_id}. \nThe existing combination with Unique ID: {existing_combo_unique_id} has been retained with Unique ID: {new_unique_id_for_old_combo}."

        # Add a label for the "Incremental Combination"
        ttk.Label(
            old_to_new_unique_id_label_frame, text=mssg_string, font=("Arial", 12)
        ).pack(side=tk.TOP, fill="both", expand=True)

        # Place the "Incremental Combination" frame center
        old_to_new_unique_id_label_frame.place(relx=0.5, anchor=tk.CENTER)
        old_to_new_unique_id_label_frame.place(y=670)

    # Method to add combo details to conditioanl order filled info pop up
    def add_combination_detail_to_informative_popup(
        self, unique_id, base_frame, is_cas_condition
    ):
        (
            columns_name_list,
            rows_data_list,
        ) = get_combination_details_list_for_combination_tab_gui(
            unique_id, is_cas_condition
        )

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
            num_rows = len(rows_data_list)
        except:
            self.display_error_popup("Error", "Unable to get the combination data.")
            return

        # Create a frame for the input fields
        treeview_table_frame = ttk.Frame(
            base_frame,
        )
        treeview_table_frame.pack(fill="both", expand=False)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(treeview_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.treeview_table = ttk.Treeview(
            treeview_table_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
            height=5,
        )

        # Pack to the screen
        self.treeview_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.treeview_table.yview)

        # Define Our Columns
        self.treeview_table["columns"] = columns_name_list

        # First Column hiding it
        self.treeview_table.column("#0", width=0, stretch="no")
        self.treeview_table.heading("#0", text="", anchor="w")

        for column_name in columns_name_list:
            self.treeview_table.column(column_name, anchor="center", width=80)
            self.treeview_table.heading(column_name, text=column_name, anchor="center")

        # Create striped row tags
        self.treeview_table.tag_configure("oddrow", background="white")
        self.treeview_table.tag_configure("evenrow", background="lightblue")

        count = 0

        for record in rows_data_list:
            if count % 2 == 0:
                self.treeview_table.insert(
                    parent="",
                    index="end",
                    iid=count,
                    text="",
                    values=record,
                    tags=("evenrow",),
                )
            else:
                self.treeview_table.insert(
                    parent="",
                    index="end",
                    iid=count,
                    text="",
                    values=record,
                    tags=("oddrow",),
                )

            count += 1

    # Get Trigger Price
    def get_trigger_price_for_condition(
        self,
        unique_id,
        cas_add_or_switch,
        original_condition_string,
        reference_price,
        reference_position,
    ):
        # Extract the times from the condition string
        date_time_list = re.findall(variables.time_regex, original_condition_string)

        # Extract the times from the condition string
        times_list = re.findall(variables.time_regex, original_condition_string)

        # Return if date time and time in len
        if (len(date_time_list) > 0) or (len(times_list) > 0):
            return "N/A"

        # Original Condition String copy
        condition_string = copy.deepcopy(original_condition_string)

        # Sorted 'user_input_fields' longest word first, local copy
        user_input_fields = copy.deepcopy(variables.cas_table_fields_for_condition)

        # Adding and and or
        user_input_fields = user_input_fields + ["and", "or"]

        # Sorting
        user_input_fields = sorted(user_input_fields, key=lambda word: -len(word))

        # did user gave the input fields as it
        flag_price_increase_decrease = False

        # Count of tokens in condition
        counter_tokens_in_condition = 0

        for token in user_input_fields:
            # check if this token in condition string
            is_token_present = condition_string.find(token)

            # Token is not present
            if is_token_present == -1:
                continue

            # If token is not in this list we can not find the trigger price
            if token not in [
                "Price Adverse Chg By",
                "Price Favorable Chg By",
                "Price Decrease By",
                "Price Increase By",
            ]:
                return "N/A"

            else:
                # if we have multiple tokens we can not get the trigger price
                counter_tokens_in_condition += 1

                # Replace token
                condition_string = condition_string.replace(token, " ")

                # Marking the flag
                if token in ["Price Decrease By", "Price Increase By"]:
                    flag_price_increase_decrease = True

                # Return "N/A" as condition have multiple user input fields
                if counter_tokens_in_condition > 1:
                    return "N/A"

        # If we have zero tokens i.e these ["Price Adverse Chg By", "Price Favorable Chg By", "Price Decrease By", "Price Increase By" ] are not present so we will not show user the trigger price
        if counter_tokens_in_condition == 0:
            return "N/A"

        # If error occurs return "N/A"
        try:
            # Cas Table Dataframe
            cas_table_data_frame = copy.deepcopy(variables.cas_table_values_df)

            # filter the DataFrame to get the row where "Unique ID" is equal to unique_id
            filtered_df = cas_table_data_frame[
                cas_table_data_frame["Unique ID"] == unique_id
            ]

            # get the first row of the filtered DataFrame using .iloc
            cas_row = filtered_df.iloc[0]

            # Eval Result (condition passed or not), solved_conditon_string(will have values and equation) or False incase eval is False
            eval_result, solved_condition_string = evaluate_condition(
                user_input_fields,
                cas_row,
                original_condition_string,
                reference_price,
                reference_position,
            )

            '''if not eval_result:

                return "N/A"'''

        except:
            return "N/A"

        # Print to console
        if variables.flag_debug_mode:
            print(f"Getting Trigger Price: {solved_condition_string}")

        # Trigger Price, default Value
        trigger_price = "N/A"

        # If Solved Condition string is not false, we can calculate the trigger price
        if solved_condition_string != False:
            # Sign we can have
            greater_equal, lessthan_equal = ">=", "<="

            # Splitting the condition string
            if greater_equal in solved_condition_string:
                splitted_condition = solved_condition_string.split(greater_equal)
            else:
                splitted_condition = solved_condition_string.split(lessthan_equal)

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Getting Trigger Price (splitted condition): {splitted_condition}"
                )

            # If Token is Price Increase or Price Decrease in condition
            if flag_price_increase_decrease:
                # Getting Later half,filtering
                sub_condition = splitted_condition[1]
                sub_condition = sub_condition.replace(",", "")
                sub_condition = sub_condition.replace(")", "")
                sub_condition = sub_condition.replace("(", "")

                # Stripping
                sub_condition = sub_condition.strip()

                # Eval sub_condition for Trigger price
                try:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Trying to eval the conditon for trigger price condition: {sub_condition}"
                        )

                    trigger_price = eval(sub_condition)

                    # Formatting value
                    trigger_price = f"{trigger_price:,.2f}"

                    # Print to console
                    if variables.flag_debug_mode:
                        print(f"Eval trigger price: {trigger_price}")
                except Exception as e:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(f"Unable to calculate the Trigger Price, Error : {e}")

                return trigger_price
            else:
                # Later Equation, filtering it (it is the value user gave)

                # print(splitted_condition)
                sub_condition = splitted_condition[1]
                sub_condition = sub_condition.replace(",", "")
                sub_condition = sub_condition.replace(")", "")
                sub_condition = sub_condition.replace("(", "")

                # Stripping
                sub_condition = sub_condition.strip()

                # Calculating Price Change
                if (
                    reference_position > 0
                    and (original_condition_string.find("Price Favorable Chg By") != -1)
                ) or (
                    reference_position < 0
                    and (original_condition_string.find("Price Adverse Chg By") != -1)
                ):
                    sub_condition = f" {reference_price} + {sub_condition} "
                else:
                    sub_condition = f" {reference_price} - {sub_condition} "

                # Stripping the condition
                sub_condition = sub_condition.strip()

                # Trying to eval trigger price
                try:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Trying to eval the conditon for trigger price condition: {sub_condition}"
                        )

                    trigger_price = eval(sub_condition)

                    # Formatting value
                    trigger_price = f"{trigger_price:,.2f}"

                    # Print to console
                    if variables.flag_debug_mode:
                        print(f"Eval trigger price: {trigger_price}")
                except Exception as e:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(f"Unable to calculate the Trigger Price, Error : {e}")

                return trigger_price

        return trigger_price

    # Method to display pop up to inform conditional order filled
    def display_condition_order_triggered_informative_popup(
        self,
        existing_combo_unique_id,
        trading_combination_unique_id,
        cas_type,
        cas_condition,
        reference_price,
        reference_position,
        order_type,
        combo_quantity,
        limit_price,
        order_trigger_price,
        trail_value,
        series_id=None,
    ):
        # Create a condition triggered_informative popup window
        condition_triggered_informative_popup = tk.Toplevel()
        condition_triggered_informative_popup.title(
            f"Conditional {cas_type.capitalize()} Order Triggered, Conditional Combo Unique ID: {existing_combo_unique_id}, Trading Combo Unique ID: {trading_combination_unique_id}"
        )

        # Custom Width, Geometry
        custom_width = 80 * len(variables.leg_columns_combo_detail_gui) + 60
        condition_triggered_informative_popup.geometry(f"{custom_width}x320")

        # Create main frame
        condition_triggered_informative_popup_frame = ttk.Frame(
            condition_triggered_informative_popup, padding=20
        )
        condition_triggered_informative_popup_frame.pack(fill="both", expand=True)

        # Create Label frame for the "Order Specs Label Frame"
        order_type_label_frame = ttk.Frame(
            condition_triggered_informative_popup_frame, padding=10
        )
        order_type_label_frame.pack(fill="both", expand=True)

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            order_type_label_frame,
            text=f"Conditional {cas_type.capitalize()} Order Completed",
            font=("Arial", 12),
        ).pack(side=tk.TOP, fill="both", expand=True)

        # Place existing combination frame in center
        order_type_label_frame.place(relx=0.5, anchor=tk.CENTER)
        order_type_label_frame.place(y=10)

        # Create a frame for displaying the order specs
        order_specs_label_frame = ttk.Frame(
            condition_triggered_informative_popup_frame,
        )
        order_specs_label_frame.pack(side=tk.TOP, fill="both", expand=True)

        # Order Type and the value of the field to display in the label
        if order_type in ["Market", "IB Algo Market"]:
            order_spec_label_text = (
                f"Order Type: {order_type}, Quantity: {combo_quantity}"
            )
        elif order_type == "Stop Loss":
            order_spec_label_text = f"Order Type: {order_type}, Quantity: {combo_quantity}, Trigger Price: {order_trigger_price}"
        elif order_type == "Trailing Stop Loss":
            order_spec_label_text = f"Order Type: {order_type}, Quantity: {combo_quantity}, Trail Value: {trail_value}"
        elif order_type == "Limit":
            order_spec_label_text = f"Order Type: {order_type}, Quantity: {combo_quantity}, Limit Price: {limit_price}"

        if series_id not in [None, "None", "N/A"]:
            origin_of_order_txt = (
                f"Origin of Order : Conditional Series, Series ID : {series_id}"
            )

        else:
            origin_of_order_txt = (
                f"Origin of Order : Conditional {cas_type.capitalize()}"
            )

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            order_specs_label_frame, text=order_spec_label_text, font=("Arial", 12)
        ).pack(side=tk.TOP, fill="both", expand=True, anchor=tk.CENTER, pady=3)

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            order_specs_label_frame, text=origin_of_order_txt, font=("Arial", 12)
        ).pack(side=tkinter.TOP, anchor=tk.CENTER, pady=3)

        # Place in center
        order_specs_label_frame.place(relx=0.5, anchor=tk.CENTER)
        order_specs_label_frame.place(y=50)

        # Condition Text Box
        condition_text_box = tk.Text(
            condition_triggered_informative_popup_frame,
            width=117,
            height=8,
            font=("Helvetica", 12),
        )
        condition_text_box.pack(
            side=tk.LEFT,
        )

        # Insert condition in textbox and disable the text box so user can not change condition in the textbox
        condition_text_box.insert(tk.END, f"{cas_condition}")
        condition_text_box.configure(state="disabled")

        # Place in center
        condition_text_box.place(relx=0.5, anchor=tk.CENTER)
        condition_text_box.place(y=155)

        # Create Label frame for the displaying "Small info Mssg that order Completed"
        small_info_mssg_order_completed = ttk.Frame(
            condition_triggered_informative_popup_frame, padding=10
        )
        small_info_mssg_order_completed.pack(fill="both", expand=True)

        # Add a label for the "Incremental Combination"
        order_info_mssg = f"Conditional {cas_type.capitalize()} Order Completed, for Conditional Combination Unique ID: {existing_combo_unique_id} and  Trading Combination Unique ID: {trading_combination_unique_id}"
        ttk.Label(
            small_info_mssg_order_completed, text=order_info_mssg, font=("Arial", 12)
        ).pack(side=tk.TOP, fill="both", expand=True)

        # Place the "Incremental Combination" frame center
        small_info_mssg_order_completed.place(relx=0.5, anchor=tk.CENTER)
        small_info_mssg_order_completed.place(y=270)

        # Checking if it is valid cas type order
        if cas_type in ["BUY", "SELL"]:
            # Removing deleted cas condition from watchlist cas condition dataframe
            variables.cas_condition_table_dataframe = (
                variables.cas_condition_table_dataframe.loc[
                    variables.cas_condition_table_dataframe["Unique ID"]
                    != existing_combo_unique_id
                ]
            )

    # def conditional_buy_sell_order(self, order_type):
    #     # order_type can be 'BUY', 'SELL'
    #
    #     # Unique ID
    #     selected_item = self.cas_table.selection()[0]  # get the item ID of the selected row
    #     values = self.cas_table.item(selected_item, "values")  # get the values of the selected row
    #     unique_id = int(values[0])
    #
    #     # Number of CAS Conditions that exists
    #     number_of_conditions = do_cas_condition_exists_for_unique_id_in_db(unique_id)
    #
    #     # If a condition already exists, display error popup
    #     if number_of_conditions > 0:
    #         # Throw Error Popup
    #         variables.screen.display_error_popup(f"Unique ID : {unique_id}, Conditional {order_type.capitalize()}", "A Condition already exists, can not add another.")
    #         return
    #
    #     # Trying to get the reference price
    #     try:
    #         local_combo_buy_sell_price_dict = copy.deepcopy(variables.unique_id_to_prices_dict[unique_id])
    #         current_buy_price, current_sell_price = local_combo_buy_sell_price_dict['BUY'], local_combo_buy_sell_price_dict['SELL']
    #         reference_price = int(((current_buy_price + current_sell_price) / 2) * 100) / 100
    #     except Exception as e:
    #         print(e)
    #         variables.screen.display_error_popup(f"Unique ID : {unique_id}, Conditional {cas_add_or_switch.capitalize()}", "Unable to get the combination current price.")
    #         return
    #
