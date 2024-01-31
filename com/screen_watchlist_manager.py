"""
Created on 21-Jun-2023

@author: Karan
"""

from com import *
from com.variables import *
from com.combination_helper import *
from com.mysql_io_watchlist import *
from com.mysql_io_account_group import *


class ScreenWatchList(object):
    def __init__(self, master_notebook):
        """
        Constructor
        """
        self.notebook = master_notebook

        self.watchlist_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.watchlist_tab, text="  WAG  ")
        self.create_watchlist_tab()

        self.create_watchlist_dropdown()

    # Method to create watchlist dropdown
    def create_watchlist_dropdown(self):
        # Add labels and entry fields for each column in the table
        watchlist_label = ttk.Label(
            self.notebook, text="Watchlist: ", width=40, anchor="center"
        )
        watchlist_label.pack()
        watchlist_label.place(relx=0.86, y=10, anchor="center")

        # Add labels and entry fields for each column in the table
        account_group_label = ttk.Label(
            self.notebook, text="Account Group: ", width=40, anchor="center"
        )
        account_group_label.pack()
        account_group_label.place(relx=0.74, y=10, anchor="center")

        # Get all the watchlist from the db
        all_watchlist_dataframe = get_all_watchlists_from_db()

        try:
            # All watchlist names
            all_watchlist_name = all_watchlist_dataframe["Watchlist Name"].to_list()
            all_watchlist_name.remove("ALL")
            all_watchlist_name = sorted(all_watchlist_name)
            all_watchlist_name.insert(0, "ALL")
        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Execption occured while creating the watchlist drop down, inserting only 'All' watchlist: {e}"
                )
            all_watchlist_name = ["ALL"]

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

        self.watchlist_drop_down = ttk.Combobox(
            self.notebook,
            width=15,
            values=all_watchlist_name,
            state="readonly",
            style="Custom.TCombobox",
        )
        self.watchlist_drop_down.current(0)
        self.watchlist_drop_down.pack()
        self.watchlist_drop_down.place(relx=0.91, y=10, anchor="center")

        try:

            # Get all account groups
            account_group_df = get_all_account_groups_from_db()

            # Checking if dataframe is empty
            if account_group_df.empty:

                # Reset group id column
                reset_group_id()

                # insert acount group in DB table
                insert_account_group_in_db("ALL")

                # Define update value dict
                value_dict = {"Account IDs": "ALL"}

                # Update ALL group with ALL value
                update_account_group_table_db(1, value_dict)

                # Update table
                self.update_account_group_table()

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

        except Exception as e:

            all_account_groups = ["ALL"]

        # Drop down for account group
        self.account_group_drop_down = ttk.Combobox(
            self.notebook,
            width=15,
            values=all_account_groups,
            state="readonly",
            style="Custom.TCombobox",
        )
        self.account_group_drop_down.current(0)
        self.account_group_drop_down.pack()
        self.account_group_drop_down.place(relx=0.8, y=10, anchor="center")

        def on_select(event):

            # Get the current value of the Combobox
            selected_watchlist = self.watchlist_drop_down.get()
            self.display_selected_watchlist(selected_watchlist)

        # Bind the function to the Combobox
        self.watchlist_drop_down.bind("<<ComboboxSelected>>", on_select)

        def on_select_account_group(event):

            # Get the current value of the Combobox
            selected_account_group = self.account_group_drop_down.get()

            # Get selected account group
            variables.selected_account_group = selected_account_group

            # get account ids in account group
            variables.account_ids_list_of_selected_acount_group = (
                get_accounts_in_account_group_from_db(selected_account_group).split(",")
            )

            # Update order book and position table
            variables.flag_orders_book_table_watchlist_changed = True
            variables.flag_positions_tables_watchlist_changed = True

            variables.screen.update_orders_book_table_watchlist_changed()
            variables.screen.screen_position_obj.update_positions_table_watchlist_changed()

            variables.screen.screen_portfolio_tab.update_portfolio_combo_table(flag_delete=True)

            variables.screen.screen_portfolio_tab.update_portfolio_legs_table(flag_delete=True)

        # Bind the function to the Combobox
        self.account_group_drop_down.bind(
            "<<ComboboxSelected>>", on_select_account_group
        )

    # Method to display selected watchlist across app
    def display_selected_watchlist(self, watchlist_name):
        # Get selected watchlist name
        variables.selected_watchlist = watchlist_name

        # Get unique id for watchlist name
        unique_id_list_for_watchlist = get_unique_id_in_watchlists_from_db(
            watchlist_name
        )
        variables.unique_id_list_of_selected_watchlist = unique_id_list_for_watchlist
        variables.flag_update_tables_watchlist_changed = True
        variables.flag_update_combo_tables_watchlist_changed = True
        variables.flag_market_watch_tables_watchlist_changed = True
        variables.flag_positions_tables_watchlist_changed = True
        variables.flag_orders_book_table_watchlist_changed = True
        variables.flag_cas_condition_table_watchlist_changed = True
        variables.flag_scale_trade_tables_watchlist_changed = True

        variables.screen.update_combo_details_table()
        variables.screen.update_market_watch_table_watchlist_changed()
        variables.screen.screen_position_obj.update_positions_table_watchlist_changed()
        variables.screen.update_orders_book_table_watchlist_changed()
        variables.screen.screen_cas_obj.update_cas_condition_table_watchlist_change()
        variables.screen.screen_scale_trader_obj.update_scale_trader_table()

        # Destroy pop up present at moment
        # for pop_up in variables.screen.window.winfo_children():
        #     if pop_up.winfo_class() == "Toplevel":
        #         pop_up.destroy()

    # Method to create watchlist table
    def create_watchlist_tab(self):

        # Create Treeview Frame for active combo table
        create_watchlist_button_frame = ttk.Frame(self.watchlist_tab, padding=10)
        create_watchlist_button_frame.pack(pady=10)

        # Create the "Create Watchlist" button
        create_watchlist_button = ttk.Button(
            create_watchlist_button_frame,
            text="Create Watchlist",
            command=lambda: self.create_watchlist(),
        )

        create_watchlist_button.pack()

        # Place in center
        create_watchlist_button_frame.place(relx=0.5, anchor=tk.CENTER)
        create_watchlist_button_frame.place(y=30)

        # Create Treeview Frame for active combo table
        watchlist_table_frame = ttk.Frame(self.watchlist_tab, padding=10)
        watchlist_table_frame.pack(pady=10)

        # Place in center
        watchlist_table_frame.place(relx=0.5, anchor=tk.CENTER)
        watchlist_table_frame.place(y=215)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(watchlist_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.watchlist_table = ttk.Treeview(
            watchlist_table_frame,
            yscrollcommand=tree_scroll.set,
            height=12,
            selectmode="extended",
        )

        # Pack to the screen
        self.watchlist_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.watchlist_table.yview)

        watchlist_table_columns = (
            "Watchlist ID",
            "Watchlist Name",
            "Unique IDs",
        )

        # Column in order book table
        self.watchlist_table["columns"] = watchlist_table_columns

        # Creating Columns
        self.watchlist_table.column("#0", width=0, stretch="no")
        self.watchlist_table.column("Watchlist ID", anchor="center", width=380)
        self.watchlist_table.column("Watchlist Name", anchor="center", width=380)
        self.watchlist_table.column("Unique IDs", anchor="center", width=780)

        # Create Headings
        self.watchlist_table.heading("#0", text="", anchor="w")
        self.watchlist_table.heading(
            "Watchlist ID", text="Watchlist ID", anchor="center"
        )
        self.watchlist_table.heading(
            "Watchlist Name", text="Watchlist Name", anchor="center"
        )
        self.watchlist_table.heading("Unique IDs", text="Unique IDs", anchor="center")

        # Back ground
        self.watchlist_table.tag_configure("oddrow", background="white")
        self.watchlist_table.tag_configure("evenrow", background="lightblue")

        self.watchlist_table.bind("<Button-3>", self.watchlist_table_right_click)

        # Create account table in WAG tab
        self.create_accounts_group_table()

    # Method to create account group table
    def create_accounts_group_table(self):

        # Create Treeview Frame for active combo table
        create_accounts_group_button_frame = ttk.Frame(self.watchlist_tab, padding=10)
        create_accounts_group_button_frame.pack(pady=5)

        # Create the "Create Accounts Group" button
        create_accounts_group_button = ttk.Button(
            create_accounts_group_button_frame,
            text="Create Accounts Group",
            command=lambda: self.create_account_group_pop_up(),
        )

        create_accounts_group_button.pack()

        # Place in center
        create_accounts_group_button_frame.place(relx=0.5, anchor=tk.CENTER)
        create_accounts_group_button_frame.place(y=400)

        # Create Treeview Frame for active accounts group table
        accounts_group_table_frame = ttk.Frame(self.watchlist_tab, padding=10)
        accounts_group_table_frame.pack(pady=10)

        # Place in center
        accounts_group_table_frame.place(relx=0.5, anchor=tk.CENTER)
        accounts_group_table_frame.place(y=600)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(accounts_group_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.accounts_group_table = ttk.Treeview(
            accounts_group_table_frame,
            yscrollcommand=tree_scroll.set,
            height=13,
            selectmode="extended",
        )

        # Pack to the screen
        self.accounts_group_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.accounts_group_table.yview)

        # Column in order book table
        self.accounts_group_table["columns"] = variables.accounts_group_table_columns

        # Creating Columns
        self.accounts_group_table.column("#0", width=0, stretch="no")

        self.accounts_group_table.column("Group ID", anchor="center", width=380)
        self.accounts_group_table.column("Group Name", anchor="center", width=380)
        self.accounts_group_table.column("Account IDs", anchor="center", width=780)

        # Create Headings
        self.accounts_group_table.heading("#0", text="", anchor="w")
        self.accounts_group_table.heading("Group ID", text="Group ID", anchor="center")
        self.accounts_group_table.heading(
            "Group Name", text="Group Name", anchor="center"
        )
        self.accounts_group_table.heading(
            "Account IDs", text="Account IDs", anchor="center"
        )

        # Back ground
        self.accounts_group_table.tag_configure("oddrow", background="white")
        self.accounts_group_table.tag_configure("evenrow", background="lightblue")

        self.accounts_group_table.bind(
            "<Button-3>", self.account_group_table_right_click
        )

        # Update table at start
        self.update_account_group_table()

    # Method to define account group table right click options
    def account_group_table_right_click(self, event):
        # get the Treeview row that was clicked
        row = self.accounts_group_table.identify_row(event.y)

        if row:
            # select the row
            self.accounts_group_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.accounts_group_table, tearoff=0)
            menu.add_command(
                label="Edit Account Group", command=lambda: self.edit_account_group()
            )
            menu.add_command(
                label="Delete Account Group",
                command=lambda: self.delete_account_group(),
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    # Method to edit account group
    def edit_account_group(self):

        group_id = self.accounts_group_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.accounts_group_table.item(
            group_id, "values"
        )  # get the values of the selected row

        # Get group id of selected row
        group_id = values[0]
        group_name = values[1]
        account_ids = values[2]

        # check if selected group is Default group
        if group_id == "1" and group_name == "ALL":
            error_title = f"Error, Can not edit the default Account Group"
            error_string = f"The default Account Group can not be edited."

            variables.screen.display_error_popup(error_title, error_string)
            return

        self.display_popup_to_edit_account_ids_in_account_group(
            group_id, group_name, account_ids
        )

        # self.display_quick_exit_order_specs(unique_id, )

    # Method to manage pop up to edit accounts in account group
    def display_popup_to_edit_account_ids_in_account_group(
        self, group_id, group_name, account_ids
    ):

        # Get current session accounts
        local_current_session_accounts = copy.deepcopy(
            variables.current_session_accounts
        )

        try:
            all_account_ids_in_system = (
                local_current_session_accounts  # list of all Account IDs in System
            )

            if len(all_account_ids_in_system) < 1:
                raise Exception("No Account ID")

        except Exception as e:
            error_title = f"Error, No Account Found"
            error_string = f"Please try after adding an Account."

            variables.screen.display_error_popup(error_title, error_string)
            return

        # get Account ids present in account group
        local_account_id_list_for_account_group = (
            account_ids  # Get account ids for account group
        )

        # check Account ids present in Account group is empty
        if local_account_id_list_for_account_group in [None, "None", ""]:

            local_account_id_list_for_account_group = []

        else:

            # Split the string by comma and convert each element to an integer
            local_account_id_list_for_account_group = [
                account_id
                for account_id in local_account_id_list_for_account_group.split(",")
            ]

            # Filtering nique ids based on all unique ids present in system
            local_account_id_list_for_account_group = [
                account_id
                for account_id in local_account_id_list_for_account_group
                if account_id in all_account_ids_in_system
            ]

        # Sort Account ids
        all_account_ids_in_system = sorted(all_account_ids_in_system)

        local_map_account_id_to_indx = {
            indx: account_id
            for indx, account_id in enumerate(all_account_ids_in_system)
        }

        # Create a popup window
        edit_popup_frame = tk.Toplevel()

        # Title for pop up
        edit_popup_frame_title = f"Edit Account Group, Account Group Name: {group_name}"

        edit_popup_frame.title(edit_popup_frame_title)

        width_of_pop_up = 1100  # Minimum width for pop up
        height_of_pop_up = 400

        # Geometry
        edit_popup_frame.geometry(
            f"{width_of_pop_up}x{height_of_pop_up}"
        )  # Make the size dynamic (Number UID in system, Row in a single row) min() dynamic

        # Retrieve the default button background color

        # edit_popup_frame.configure(background="seashell3")'''

        # Two Frame
        # one for the Account ids not in Account group
        # one for the buttons to move combo through tables
        # one for Account ids in account group

        # frame table for the Account ids not in account group
        pop_up_frame = ttk.Frame(edit_popup_frame, padding=0)
        pop_up_frame.pack(fill="both", expand=True)

        # frame table for the account ids not in account group
        table_of_non_selected_account_ids_frame = ttk.Frame(pop_up_frame, padding=0)
        table_of_non_selected_account_ids_frame.grid(
            column=1, row=1, rowspan=3, padx=25, pady=5
        )

        # frame table for the buttons to move combo through tables
        table_of_buttons_frame = ttk.Frame(pop_up_frame, padding=0)
        table_of_buttons_frame.grid(column=2, row=1, padx=5, pady=5)

        # frame table for account ids in account group
        table_of_selected_account_ids_frame = ttk.Frame(pop_up_frame, padding=0)
        table_of_selected_account_ids_frame.grid(
            column=3, row=1, rowspan=3, padx=25, pady=5
        )

        # frame table for account ids in account group
        labels_of_non_selected_table_frame = ttk.Frame(pop_up_frame, padding=0)
        labels_of_non_selected_table_frame.grid(column=1, row=0, padx=5, pady=[25, 0])

        # frame table for account ids in account group
        labels_of_selected_table_frame = ttk.Frame(pop_up_frame, padding=0)
        labels_of_selected_table_frame.grid(column=3, row=0, padx=5, pady=[25, 0])

        # Treeview Scrollbar
        tree_scroll = Scrollbar(table_of_non_selected_account_ids_frame)
        tree_scroll.pack(side="right", fill="y")

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            labels_of_non_selected_table_frame,
            text="Non Selected Account IDs",
            font=("Arial", 12),
        ).grid(column=1, row=0, padx=5, pady=[5, 5])

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            labels_of_selected_table_frame,
            text="Selected Account IDs",
            font=("Arial", 12),
        ).grid(column=2, row=0, padx=[0, 0], pady=[5, 5])

        # Create Treeview
        self.treeview_non_selected_account_id_table = ttk.Treeview(
            table_of_non_selected_account_ids_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
        )

        # Pack to the screen
        self.treeview_non_selected_account_id_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.treeview_non_selected_account_id_table.yview)

        columns_in_non_selected_account_ids_table = ("Account ID",)

        # Define Our Columns
        self.treeview_non_selected_account_id_table[
            "columns"
        ] = columns_in_non_selected_account_ids_table

        # First Column hiding it
        self.treeview_non_selected_account_id_table.column("#0", width=0, stretch="no")
        self.treeview_non_selected_account_id_table.column(
            "Account ID", anchor="center", width=320
        )

        # Defining headings for table
        self.treeview_non_selected_account_id_table.heading(
            "#0", text="", anchor="center"
        )
        self.treeview_non_selected_account_id_table.heading(
            "Account ID", text="Account ID", anchor="center"
        )

        self.treeview_non_selected_account_id_table.tag_configure(
            "oddrow", background="white"
        )
        self.treeview_non_selected_account_id_table.tag_configure(
            "evenrow", background="lightblue"
        )

        def on_click_transfer_account_id_to_selected():

            try:

                # Get Account ids for selected row
                selected_item = (
                    self.treeview_non_selected_account_id_table.selection()
                )  # get the item ID of the selected row

                # Transfer selected Account ids from non selected table to selected table
                for item in selected_item:
                    local_account_id_list_for_account_group.append(item)

                # Update tables
                fill_non_selected_account_id_table(
                    all_account_ids_in_system, local_account_id_list_for_account_group
                )
                fill_selected_account_id_table(
                    all_account_ids_in_system, local_account_id_list_for_account_group
                )

            except Exception as e:
                if variables.flag_debug_mode:
                    print(
                        f"Error inside transferring Account id to selected Account ids table, is {e}"
                    )

        def on_click_transfer_account_id_to_non_selected():

            try:

                # Get unique ids for selected row
                selected_item = (
                    self.treeview_table_selected_account_ids.selection()
                )  # get the item ID of the selected row

                # Transfer selected unique ids from selected table to non selected table
                for item in selected_item:
                    local_account_id_list_for_account_group.remove(item)

                # Update tables
                fill_non_selected_account_id_table(
                    all_account_ids_in_system, local_account_id_list_for_account_group
                )
                fill_selected_account_id_table(
                    all_account_ids_in_system, local_account_id_list_for_account_group
                )
            except Exception as e:
                if variables.flag_debug_mode:
                    print(
                        f"Error inside transferring Account id to non selected Account ids table, is {e}"
                    )

        def edit_list_of_account_id_for_watchlist():

            # Get all selected Account id which is present in selected table
            all_selected_account_ids = local_account_id_list_for_account_group

            # Sort selected Account ids in ascending manner
            all_selected_account_ids = sorted(all_selected_account_ids)

            try:

                # Create string of selected Account ids
                account_ids_string = ",".join(map(str, all_selected_account_ids))

                values_to_update_dict = {"Account IDs": account_ids_string}

                # Update unique ids in db for account group
                update_account_group_table_db(group_id, values_to_update_dict)

                # Update GUI table
                self.update_account_group_table()

                # Destryoing pop up window
                edit_popup_frame.destroy()

                # get account ids in account group
                variables.account_ids_list_of_selected_acount_group = (
                    get_accounts_in_account_group_from_db(group_name).split(",")
                )

                # Update order book
                variables.flag_orders_book_table_watchlist_changed = True
                variables.flag_positions_tables_watchlist_changed = True

                variables.screen.screen_position_obj.update_positions_table_watchlist_changed()
                variables.screen.update_orders_book_table_watchlist_changed()

            except Exception as e:
                if variables.flag_debug_mode:
                    print(
                        f"Error inside editing list if Account ids for watchlist, {e}"
                    )
            return

        # Button to move selected Account ids to selected
        transfer_account_id_to_select = ttk.Button(
            table_of_buttons_frame,
            text=">>",
            command=lambda: on_click_transfer_account_id_to_selected(),
        )
        transfer_account_id_to_select.grid(row=1, column=1, pady=35)

        # Button to move selected Account ids to non-selected
        transfer_account_id_to_non_selected = ttk.Button(
            table_of_buttons_frame,
            text="<<",
            command=lambda: on_click_transfer_account_id_to_non_selected(),
        )
        transfer_account_id_to_non_selected.grid(row=2, column=1, pady=35)

        # Button to save selected Account ids to account group
        edit_account_group_button = ttk.Button(
            table_of_buttons_frame,
            text="Save",
            command=lambda: edit_list_of_account_id_for_watchlist(),
        )
        edit_account_group_button.grid(row=3, column=1, pady=35)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(table_of_selected_account_ids_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.treeview_table_selected_account_ids = ttk.Treeview(
            table_of_selected_account_ids_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
        )

        # Pack to the screen
        self.treeview_table_selected_account_ids.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.treeview_table_selected_account_ids.yview)

        columns_in_selected_account_ids_table = ("Account ID",)

        # Define Our Columns
        self.treeview_table_selected_account_ids[
            "columns"
        ] = columns_in_selected_account_ids_table

        # First Column hiding it
        self.treeview_table_selected_account_ids.column("#0", width=0, stretch="no")
        self.treeview_table_selected_account_ids.column(
            "Account ID", anchor="center", width=320
        )

        self.treeview_table_selected_account_ids.heading("#0", text="", anchor="center")
        self.treeview_table_selected_account_ids.heading(
            "Account ID", text="Account ID", anchor="center"
        )

        self.treeview_table_selected_account_ids.tag_configure(
            "oddrow", background="white"
        )
        self.treeview_table_selected_account_ids.tag_configure(
            "evenrow", background="lightblue"
        )

        def fill_non_selected_account_id_table(
            all_account_ids_in_system, local_account_id_list_for_account_group
        ):

            try:

                # Get all item IDs in the Treeview
                item_ids = self.treeview_non_selected_account_id_table.get_children()

                # Delete each item from the Treeview
                for item_id in item_ids:
                    self.treeview_non_selected_account_id_table.delete(item_id)

                # Getting Account ids which are not in account group
                account_ids_not_in_selected = [
                    account_id
                    for account_id in all_account_ids_in_system
                    if account_id not in local_account_id_list_for_account_group
                ]

                # Get the current number of items in the treeview
                num_items = len(account_ids_not_in_selected)

                # Iterate through selected Account ids
                for account_id in account_ids_not_in_selected:

                    values = (account_id,)

                    if num_items % 2 == 1:
                        self.treeview_non_selected_account_id_table.insert(
                            "",
                            "end",
                            iid=account_id,
                            text=num_items + 1,
                            values=values,
                            tags=("oddrow",),
                        )

                    else:
                        self.treeview_non_selected_account_id_table.insert(
                            "",
                            "end",
                            iid=account_id,
                            text=num_items + 1,
                            values=values,
                            tags=("evenrow",),
                        )

                    num_items += 1
            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside fillling non selected tables data, is {e}")

        def fill_selected_account_id_table(
            all_account_ids_in_system, local_account_id_list_for_account_group
        ):

            try:

                # Get all item IDs in the Treeview
                item_ids = self.treeview_table_selected_account_ids.get_children()

                # Delete each item from the Treeview
                for item_id in item_ids:
                    self.treeview_table_selected_account_ids.delete(item_id)

                # Getting Account ids which are in account group
                account_ids_in_selected = [
                    account_id
                    for account_id in all_account_ids_in_system
                    if account_id in local_account_id_list_for_account_group
                ]

                # Get the current number of items in the treeview
                num_items = len(account_ids_in_selected)

                # Iterate through selected Account ids
                for account_id in account_ids_in_selected:
                    values = (account_id,)

                    if num_items % 2 == 1:
                        self.treeview_table_selected_account_ids.insert(
                            "",
                            "end",
                            iid=account_id,
                            text=num_items + 1,
                            values=values,
                            tags=("oddrow",),
                        )

                    else:
                        self.treeview_table_selected_account_ids.insert(
                            "",
                            "end",
                            iid=account_id,
                            text=num_items + 1,
                            values=values,
                            tags=("evenrow",),
                        )

                    num_items += 1
            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside fillling selected table's data, is {e}")

        fill_non_selected_account_id_table(
            all_account_ids_in_system, local_account_id_list_for_account_group
        )
        fill_selected_account_id_table(
            all_account_ids_in_system, local_account_id_list_for_account_group
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

    # Method to create new account group
    def create_account_group_pop_up(self):

        # Display Popup Ask User Input
        create_account_group_pop_up = tk.Toplevel()
        create_account_group_pop_up.title("Create Account Group")

        create_account_group_pop_up.geometry("400x150")

        create_account_group_pop_up_frame = ttk.Frame(
            create_account_group_pop_up, padding=20
        )
        create_account_group_pop_up_frame.pack(fill="both", expand=True)

        # Create a frame for the input fields
        input_frame = ttk.Frame(create_account_group_pop_up_frame, padding=20)
        input_frame.place(relx=0.5, y=20, anchor=tk.CENTER)

        # Get the Name of WatchList
        ttk.Label(input_frame, text="Enter the name of Account Group:").grid(
            column=0, row=0, padx=5, pady=5
        )
        account_group_entry = ttk.Entry(input_frame, width=30)
        account_group_entry.grid(column=1, row=0, padx=5, pady=5)

        # Create a frame for the input fields
        create_button_frame = ttk.Frame(create_account_group_pop_up_frame)
        create_button_frame.place(relx=0.5, y=80, anchor=tk.CENTER)

        create_button = ttk.Button(
            create_button_frame,
            text="Add Account Group",
            command=lambda: self.add_account_group_to_system(
                create_account_group_pop_up, account_group_entry
            ),
        )
        create_button.pack()

    # Method to add account group
    def add_account_group_to_system(
        self, create_account_group_pop_up, account_group_entry
    ):

        # Get input from account group name field
        account_group_name = account_group_entry.get().strip().upper()

        # Check if account group name is non empty
        if account_group_name == "":

            # Show error and return
            error_title = "Error, Empty Account Group Name"
            error_string = "Account Group Name can not be empty"

            variables.screen.display_error_popup(error_title, error_string)
            return

        # Get all account groups
        account_group_df = get_all_account_groups_from_db()

        # Get all account group names
        all_account_groups = account_group_df["Group Name"].to_list()

        # Check if name is already present
        if account_group_name in all_account_groups:

            # Show error and return
            error_title = "Error, Account Group Name Already Exists"
            error_string = "Account Group Name Can Not Be Repeated"

            variables.screen.display_error_popup(error_title, error_string)
            return

        # insert acount group in DB table
        insert_account_group_in_db(account_group_name)

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

        except Exception as e:

            all_account_groups = ["ALL"]

        # Destroy pop up
        create_account_group_pop_up.destroy()

    # Method to update account group table
    def update_account_group_table(self):

        try:
            # All the Unique IDs in the System
            # Get account group dataframe
            local_account_group_table_dataframe = get_all_account_groups_from_db()

            # Get all item IDs in the Treeview
            item_ids = self.accounts_group_table.get_children()

            # Delete each item from the Treeview
            for item_id in item_ids:
                self.accounts_group_table.delete(item_id)

            # Update the rows
            for i, row_val in local_account_group_table_dataframe.iterrows():

                # Group Id of row val
                group_id = int(float(row_val["Group ID"]))

                # Tuple of vals
                row_val = tuple(row_val)

                # Insert it in the table
                self.accounts_group_table.insert(
                    "",
                    "end",
                    iid=group_id,
                    text="",
                    values=row_val,
                    tags=("oddrow",),
                )

            # All the rows in scale trade Table
            all_group_id_in_account_group_table = (
                self.accounts_group_table.get_children()
            )

            # Row counter
            counter_row = 0

            # Move According to data Color here, Change Color
            for i, row in local_account_group_table_dataframe.iterrows():

                # Group Id of row val
                group_id = row["Group ID"]

                self.accounts_group_table.move(group_id, "", counter_row)

                if counter_row % 2 == 0:
                    self.accounts_group_table.item(group_id, tags="evenrow")
                else:
                    self.accounts_group_table.item(group_id, tags="oddrow")

                # Increase row count
                counter_row += 1

        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:
                print(f"Error Inside update_account_group_table, Exp: {e}")

    # Method to define right click options for watchlist table
    def watchlist_table_right_click(self, event):
        # get the Treeview row that was clicked
        row = self.watchlist_table.identify_row(event.y)

        if row:
            # select the row
            self.watchlist_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.watchlist_table, tearoff=0)
            menu.add_command(
                label="Edit WatchList", command=lambda: self.edit_watchlist()
            )
            menu.add_command(
                label="Delete WatchList", command=lambda: self.delete_watchlist()
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    # Method to create watchlist
    def create_watchlist(self):

        # Display Popup Ask User Input
        create_watchlist_popup = tk.Toplevel()
        create_watchlist_popup.title("Create Watchlist")

        create_watchlist_popup.geometry("400x150")

        create_watchlist_popup_frame = ttk.Frame(create_watchlist_popup, padding=20)
        create_watchlist_popup_frame.pack(fill="both", expand=True)

        # Create a frame for the input fields
        input_frame = ttk.Frame(create_watchlist_popup_frame, padding=20)
        input_frame.place(relx=0.5, y=20, anchor=tk.CENTER)

        # Get the Name of WatchList
        ttk.Label(input_frame, text="Enter the name of Watchlist:").grid(
            column=0, row=0, padx=5, pady=5
        )
        watchlist_name_entry = ttk.Entry(input_frame, width=30)
        watchlist_name_entry.grid(column=1, row=0, padx=5, pady=5)

        # Create a frame for the input fields
        create_button_frame = ttk.Frame(create_watchlist_popup_frame)
        create_button_frame.place(relx=0.5, y=80, anchor=tk.CENTER)

        create_button = ttk.Button(
            create_button_frame,
            text="Add Watchlist",
            command=lambda: self.add_watchlist_to_system(
                create_watchlist_popup, watchlist_name_entry
            ),
        )
        create_button.pack()

    # Method to add watchlist to system
    def add_watchlist_to_system(self, create_watchlist_popup, watchlist_name_entry):

        watchlist_name = watchlist_name_entry.get().strip().upper()

        # If the name is empty show a error popup
        if watchlist_name == "":
            # Show error and return
            error_title = "Error, Empty Watchlist Name"
            error_string = "Watchlist Name can not be empty"

            variables.screen.display_error_popup(error_title, error_string)
            return

        # Get all the watchlist from the db
        all_watchlist_dataframe = get_all_watchlists_from_db()

        # All watclist names
        all_watchlist_name = all_watchlist_dataframe["Watchlist Name"].to_list()

        # Make sure it does not exist already
        if watchlist_name in all_watchlist_name:

            # if so show a popup that watchlist with name exist
            error_title = "Error, Watchlist Already Exists"
            error_string = (
                "Watchlist already exists, Please give a different watchlist name"
            )

            variables.screen.display_error_popup(error_title, error_string)
            return

        else:
            # Create Watchlist
            insert_watchlist_in_db(watchlist_name)

            # Get the specific watchlist from the db
            all_watchlist_dataframe = get_all_watchlists_from_db()

            # Filtered Dataframe with user Watchlist name (for ID Name and UIDs)
            filtered_dataframe = all_watchlist_dataframe.loc[
                all_watchlist_dataframe["Watchlist Name"] == f"{watchlist_name}"
            ]

            # Insert the Watchlist in the GUI
            if len(filtered_dataframe) == 1:
                values = filtered_dataframe.to_records(index=False)
                self.insert_watchlist_in_watchlist_table(values[0])

                # Adding the watchlist to drop down menu
                all_watchlist_name = list(self.watchlist_drop_down["values"]) + [
                    watchlist_name,
                ]
                all_watchlist_name.remove("ALL")
                all_watchlist_name = sorted(all_watchlist_name)
                all_watchlist_name.insert(0, "ALL")
                self.watchlist_drop_down["values"] = all_watchlist_name

            else:
                # Show error and return
                error_title = "Unexpected Error while adding the Watchlist"
                error_string = "Error happened while trying to add the watchlist"

                variables.screen.display_error_popup(error_title, error_string)
                return

        # Destroy the popup
        create_watchlist_popup.destroy()

    # Method to edit watchlist
    def edit_watchlist(
        self,
    ):

        watchlist_id = self.watchlist_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.watchlist_table.item(
            watchlist_id, "values"
        )  # get the values of the selected row
        watchlist_id, watchlist_name, unique_ids = values
        watchlist_id = int(watchlist_id)

        if watchlist_id == 1 and watchlist_name == "ALL":
            error_title = f"Error, Can not edit the default watchlist"
            error_string = f"The default watchlist can not be edited."

            variables.screen.display_error_popup(error_title, error_string)
            return

        self.display_popup_to_edit_unique_ids_in_watchlist(
            watchlist_id, watchlist_name, unique_ids
        )

        # self.display_quick_exit_order_specs(unique_id, )

    # Manage pop up to edit unique ids to watchlist
    def display_popup_to_edit_unique_ids_in_watchlist(
        self, watchlist_id, watchlist_name, unique_ids
    ):

        # Get combo object using unique ids
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

        try:
            all_unique_ids_in_system = (
                local_unique_id_to_combo_obj.keys()
            )  # list of all Unique IDs in System
            if len(all_unique_ids_in_system) < 1:
                raise Exception("No Unique ID")
        except Exception as e:
            error_title = f"Error, No Combinations Found"
            error_string = f"Please try after adding an Combination."

            variables.screen.display_error_popup(error_title, error_string)
            return

        # get unique ids present in watchlist
        local_unique_id_list_for_watchlist = get_unique_id_in_watchlists_from_db(
            watchlist_name
        )  # Get unique id for watchlist name

        # check unique ids present in watchlist is empty
        if local_unique_id_list_for_watchlist in [None, "None", ""]:
            local_unique_id_list_for_watchlist = []
        else:

            # Split the string by comma and convert each element to an integer
            local_unique_id_list_for_watchlist = [
                int(float(unique_id))
                for unique_id in local_unique_id_list_for_watchlist.split(",")
            ]

            # Filtering nique ids based on all unique ids present in system
            local_unique_id_list_for_watchlist = [
                unique_id
                for unique_id in local_unique_id_list_for_watchlist
                if unique_id in all_unique_ids_in_system
            ]

        # Sort unique ids
        all_unique_ids_in_system = sorted(all_unique_ids_in_system)

        local_map_unique_id_to_tickers = {
            unique_id: make_informative_combo_string(
                local_unique_id_to_combo_obj[int(float(unique_id))]
            )
            for unique_id in all_unique_ids_in_system
        }

        # Create a popup window
        edit_popup_frame = tk.Toplevel()

        # Title for pop up
        edit_popup_frame_title = f"Edit Watchlist, Watchlist Name: {watchlist_name}"

        edit_popup_frame.title(edit_popup_frame_title)

        width_of_pop_up = 1100  # Minimum width for pop up
        height_of_pop_up = 400

        # Geometry
        edit_popup_frame.geometry(
            f"{width_of_pop_up}x{height_of_pop_up}"
        )  # Make the size dynamic (Number UID in system, Row in a single row) min() dynamic

        # Retrieve the default button background color

        # edit_popup_frame.configure(background="seashell3")'''

        # Two Frame
        # one for the unique ids not in watchlist
        # one for the buttons to move combo through tables
        # one for unique ids in watchlist

        # frame table for the unique ids not in watchlist
        pop_up_frame = ttk.Frame(edit_popup_frame, padding=0)
        pop_up_frame.pack(fill="both", expand=True)

        # frame table for the unique ids not in watchlist
        table_of_non_selected_unique_ids_frame = ttk.Frame(pop_up_frame, padding=0)
        table_of_non_selected_unique_ids_frame.grid(
            column=1, row=1, rowspan=3, padx=25, pady=5
        )

        # frame table for the buttons to move combo through tables
        table_of_buttons_frame = ttk.Frame(pop_up_frame, padding=0)
        table_of_buttons_frame.grid(column=2, row=1, padx=5, pady=5)

        # frame table for unique ids in watchlist
        table_of_selected_unique_ids_frame = ttk.Frame(pop_up_frame, padding=0)
        table_of_selected_unique_ids_frame.grid(
            column=3, row=1, rowspan=3, padx=25, pady=5
        )

        # frame table for unique ids in watchlist
        labels_of_non_selected_table_frame = ttk.Frame(pop_up_frame, padding=0)
        labels_of_non_selected_table_frame.grid(column=1, row=0, padx=5, pady=[25, 0])

        # frame table for unique ids in watchlist
        labels_of_selected_table_frame = ttk.Frame(pop_up_frame, padding=0)
        labels_of_selected_table_frame.grid(column=3, row=0, padx=5, pady=[25, 0])

        # Treeview Scrollbar
        tree_scroll = Scrollbar(table_of_non_selected_unique_ids_frame)
        tree_scroll.pack(side="right", fill="y")

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            labels_of_non_selected_table_frame,
            text="Non Selected Unique IDs",
            font=("Arial", 12),
        ).grid(column=1, row=0, padx=5, pady=[5, 5])

        # Add a label and entry field for the user to enter an integer
        ttk.Label(
            labels_of_selected_table_frame,
            text="Selected Unique IDs",
            font=("Arial", 12),
        ).grid(column=2, row=0, padx=[0, 0], pady=[5, 5])

        # Create Treeview
        self.treeview_non_selected_unique_id_table = ttk.Treeview(
            table_of_non_selected_unique_ids_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
        )

        # Pack to the screen
        self.treeview_non_selected_unique_id_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.treeview_non_selected_unique_id_table.yview)

        columns_in_non_selected_unique_ids_table = ("Unique ID", "Tickers")

        # Define Our Columns
        self.treeview_non_selected_unique_id_table[
            "columns"
        ] = columns_in_non_selected_unique_ids_table

        # First Column hiding it
        self.treeview_non_selected_unique_id_table.column("#0", width=0, stretch="no")
        self.treeview_non_selected_unique_id_table.column(
            "Unique ID", anchor="center", width=120
        )
        self.treeview_non_selected_unique_id_table.column(
            "Tickers", anchor="center", width=300
        )

        # Defining headings for table
        self.treeview_non_selected_unique_id_table.heading(
            "#0", text="", anchor="center"
        )
        self.treeview_non_selected_unique_id_table.heading(
            "Unique ID", text="Unique ID", anchor="center"
        )
        self.treeview_non_selected_unique_id_table.heading(
            "Tickers", text="Tickers", anchor="center"
        )

        self.treeview_non_selected_unique_id_table.tag_configure(
            "oddrow", background="white"
        )
        self.treeview_non_selected_unique_id_table.tag_configure(
            "evenrow", background="lightblue"
        )

        def on_click_transfer_unique_id_to_selected():

            try:

                # Get unique ids for selected row
                selected_item = (
                    self.treeview_non_selected_unique_id_table.selection()
                )  # get the item ID of the selected row

                # Transfer selected unique ids from non selected table to selected table
                for item in selected_item:
                    local_unique_id_list_for_watchlist.append(int(float(item)))

                # Update tables
                fill_non_selected_unique_id_table(
                    local_map_unique_id_to_tickers,
                    all_unique_ids_in_system,
                    local_unique_id_list_for_watchlist,
                )
                fill_selected_unique_id_table(
                    local_map_unique_id_to_tickers,
                    all_unique_ids_in_system,
                    local_unique_id_list_for_watchlist,
                )

            except Exception as e:
                if variables.flag_debug_mode:
                    print(
                        f"Error inside transferring unique id to selected uniques ids table, is {e}"
                    )

        def on_click_transfer_unique_id_to_non_selected():

            try:

                # Get unique ids for selected row
                selected_item = (
                    self.treeview_table_selected_unique_ids.selection()
                )  # get the item ID of the selected row

                # Transfer selected unique ids from selected table to non selected table
                for item in selected_item:
                    local_unique_id_list_for_watchlist.remove(int(float(item)))

                # Update tables
                fill_non_selected_unique_id_table(
                    local_map_unique_id_to_tickers,
                    all_unique_ids_in_system,
                    local_unique_id_list_for_watchlist,
                )
                fill_selected_unique_id_table(
                    local_map_unique_id_to_tickers,
                    all_unique_ids_in_system,
                    local_unique_id_list_for_watchlist,
                )
            except Exception as e:
                if variables.flag_debug_mode:
                    print(
                        f"Error inside transferring unique id to non selected uniques ids table, is {e}"
                    )

        def edit_list_of_unique_id_for_watchlist():

            # Get all selected unique id which is present in selected table
            all_selected_unique_ids = local_unique_id_list_for_watchlist

            # Sort selected unique ids in ascending manner
            all_selected_unique_ids = sorted(all_selected_unique_ids)

            try:

                # Create string of selected unique ids
                unique_ids_string = ",".join(map(str, all_selected_unique_ids))

                # Update unique ids in db for watchlist
                update_watchlist_in_db(watchlist_id, unique_ids_string)

                # Reflect updated values in GUI watchlist tab
                self.update_watchlist_in_watchlist_table(
                    watchlist_id, unique_ids_string
                )

                # Destryoing pop up window
                edit_popup_frame.destroy()

                # Update details of watchlist
                if variables.selected_watchlist == watchlist_name:
                    variables.unique_id_list_of_selected_watchlist = unique_ids_string

                    variables.flag_update_tables_watchlist_changed = True
                    variables.flag_market_watch_tables_watchlist_changed = True
                    variables.flag_positions_tables_watchlist_changed = True
                    variables.flag_orders_book_table_watchlist_changed = True
                    variables.flag_cas_condition_table_watchlist_changed = True

                    variables.screen.update_combo_details_table()
                    variables.screen.update_market_watch_table_watchlist_changed()
                    variables.screen.screen_position_obj.update_positions_table_watchlist_changed()
                    variables.screen.update_orders_book_table_watchlist_changed()
                    variables.screen.screen_cas_obj.update_cas_condition_table_watchlist_change()

            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside editing list if unique ids for watchlist, {e}")
            return

        # Button to move selected unique ids to selected
        transfer_unique_id_to_selected = ttk.Button(
            table_of_buttons_frame,
            text=">>",
            command=lambda: on_click_transfer_unique_id_to_selected(),
        )
        transfer_unique_id_to_selected.grid(row=1, column=1, pady=35)

        # Button to move selected unique ids to non-selected
        transfer_unique_id_to_non_selected = ttk.Button(
            table_of_buttons_frame,
            text="<<",
            command=lambda: on_click_transfer_unique_id_to_non_selected(),
        )
        transfer_unique_id_to_non_selected.grid(row=2, column=1, pady=35)

        # Button to save selected unique ids to watchlist
        edit_watchlist_button = ttk.Button(
            table_of_buttons_frame,
            text="Save",
            command=lambda: edit_list_of_unique_id_for_watchlist(),
        )
        edit_watchlist_button.grid(row=3, column=1, pady=35)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(table_of_selected_unique_ids_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.treeview_table_selected_unique_ids = ttk.Treeview(
            table_of_selected_unique_ids_frame,
            yscrollcommand=tree_scroll.set,
            selectmode="extended",
        )

        # Pack to the screen
        self.treeview_table_selected_unique_ids.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.treeview_table_selected_unique_ids.yview)

        columns_in_selected_unique_ids_table = ("Unique ID", "Tickers")

        # Define Our Columns
        self.treeview_table_selected_unique_ids[
            "columns"
        ] = columns_in_non_selected_unique_ids_table

        # First Column hiding it
        self.treeview_table_selected_unique_ids.column("#0", width=0, stretch="no")
        self.treeview_table_selected_unique_ids.column(
            "Unique ID", anchor="center", width=120
        )
        self.treeview_table_selected_unique_ids.column(
            "Tickers", anchor="center", width=300
        )

        self.treeview_table_selected_unique_ids.heading("#0", text="", anchor="center")
        self.treeview_table_selected_unique_ids.heading(
            "Unique ID", text="Unique ID", anchor="center"
        )
        self.treeview_table_selected_unique_ids.heading(
            "Tickers", text="Tickers", anchor="center"
        )

        self.treeview_table_selected_unique_ids.tag_configure(
            "oddrow", background="white"
        )
        self.treeview_table_selected_unique_ids.tag_configure(
            "evenrow", background="lightblue"
        )

        def fill_non_selected_unique_id_table(
            local_map_unique_id_to_tickers,
            all_unique_ids_in_system,
            local_unique_id_list_of_selected_watchlist,
        ):

            try:

                # Get all item IDs in the Treeview
                item_ids = self.treeview_non_selected_unique_id_table.get_children()

                # Delete each item from the Treeview
                for item_id in item_ids:
                    self.treeview_non_selected_unique_id_table.delete(item_id)

                # Getting unique ids which are not in watchlist
                unique_ids_not_in_selected = [
                    unique_id
                    for unique_id in all_unique_ids_in_system
                    if unique_id not in local_unique_id_list_of_selected_watchlist
                ]

                # Get the current number of items in the treeview
                num_items = len(unique_ids_not_in_selected)

                # Iterate through selected unique ids
                for unique_id in unique_ids_not_in_selected:
                    values = (unique_id, local_map_unique_id_to_tickers[unique_id])

                    if num_items % 2 == 1:
                        self.treeview_non_selected_unique_id_table.insert(
                            "",
                            "end",
                            iid=unique_id,
                            text=num_items + 1,
                            values=values,
                            tags=("oddrow",),
                        )

                    else:
                        self.treeview_non_selected_unique_id_table.insert(
                            "",
                            "end",
                            iid=unique_id,
                            text=num_items + 1,
                            values=values,
                            tags=("evenrow",),
                        )

                    num_items += 1
            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside fillling non selected tables data, is {e}")

        def fill_selected_unique_id_table(
            local_map_unique_id_to_tickers,
            all_unique_ids_in_system,
            local_unique_id_list_of_selected_watchlist,
        ):

            try:

                # Get all item IDs in the Treeview
                item_ids = self.treeview_table_selected_unique_ids.get_children()

                # Delete each item from the Treeview
                for item_id in item_ids:
                    self.treeview_table_selected_unique_ids.delete(item_id)

                # Getting unique ids which are in watchlist
                unique_ids_in_selected = [
                    unique_id
                    for unique_id in all_unique_ids_in_system
                    if unique_id in local_unique_id_list_of_selected_watchlist
                ]

                # Get the current number of items in the treeview
                num_items = len(unique_ids_in_selected)

                # Iterate through selected unique ids
                for unique_id in unique_ids_in_selected:
                    values = (unique_id, local_map_unique_id_to_tickers[unique_id])

                    if num_items % 2 == 1:
                        self.treeview_table_selected_unique_ids.insert(
                            "",
                            "end",
                            iid=unique_id,
                            text=num_items + 1,
                            values=values,
                            tags=("oddrow",),
                        )

                    else:
                        self.treeview_table_selected_unique_ids.insert(
                            "",
                            "end",
                            iid=unique_id,
                            text=num_items + 1,
                            values=values,
                            tags=("evenrow",),
                        )

                    num_items += 1
            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside fillling selected table's data, is {e}")

        fill_non_selected_unique_id_table(
            local_map_unique_id_to_tickers,
            all_unique_ids_in_system,
            local_unique_id_list_for_watchlist,
        )
        fill_selected_unique_id_table(
            local_map_unique_id_to_tickers,
            all_unique_ids_in_system,
            local_unique_id_list_for_watchlist,
        )

    # Method to delete watchlist
    def delete_watchlist(
        self,
    ):

        watchlist_id = self.watchlist_table.selection()[
            0
        ]  # get the item ID of the selected row
        values = self.watchlist_table.item(
            watchlist_id, "values"
        )  # get the values of the selected row
        watchlist_id = int(watchlist_id)
        watchlist_name = str(values[1]).strip()

        if watchlist_id == 1 and watchlist_name == "ALL":
            error_title = f"Error, Can not delete the default watchlist"
            error_string = f"The default watchlist can not be deleted."

            variables.screen.display_error_popup(error_title, error_string)
            return

        # Remove Watchlist from GUI
        self.watchlist_table.delete(watchlist_id)

        # Redesign the view
        self.restyle_the_watchlist_after_deletion()

        # Remove watchlist from the db
        delete_watchlist_in_db(int(watchlist_id))

        try:
            # Removing watchlist from drop down options
            all_watchlist_name = list(self.watchlist_drop_down["values"])
            all_watchlist_name.remove("ALL")
            all_watchlist_name.remove(watchlist_name)
            all_watchlist_name = sorted(all_watchlist_name)
            all_watchlist_name.insert(0, "ALL")
            self.watchlist_drop_down["values"] = all_watchlist_name
            self.watchlist_drop_down.current(0)
        except Exception as e:
            print("Delete watchlist", e)

        # if currently choosen watchlist was deleted show default one
        if variables.selected_watchlist == watchlist_name:

            # Setting watchlist name to ALL
            variables.selected_watchlist = "ALL"
            variables.unique_id_list_of_selected_watchlist = "ALL"

            # Updating flags to update every table after deletion of watchlist
            variables.flag_update_tables_watchlist_changed = True
            variables.flag_update_combo_tables_watchlist_changed = True
            variables.flag_market_watch_tables_watchlist_changed = True
            variables.flag_positions_tables_watchlist_changed = True
            variables.flag_orders_book_table_watchlist_changed = True
            variables.flag_cas_condition_table_watchlist_changed = True
            variables.flag_scale_trade_tables_watchlist_changed = True

            variables.screen.update_combo_details_table()
            variables.screen.update_market_watch_table_watchlist_changed()
            variables.screen.screen_position_obj.update_positions_table_watchlist_changed()
            variables.screen.update_orders_book_table_watchlist_changed()
            variables.screen.screen_cas_obj.update_cas_condition_table_watchlist_change()
            variables.screen.screen_scale_trader_obj.update_scale_trader_table()

    # Method to reformat watchlist table
    def restyle_the_watchlist_after_deletion(self):

        count = 0
        for row in self.watchlist_table.get_children():
            if count % 2 == 0:
                self.watchlist_table.item(row, tags="evenrow")
            else:
                self.watchlist_table.item(row, tags="oddrow")

            count += 1

    # Method to insert rows in watchlist
    def insert_watchlist_in_watchlist_table(self, row_value):

        value = [val for val in row_value]
        if value[2] in [None, "None"]:
            value[2] = ""

        # Watchlist_id
        watchlist_id = value[0]

        # Get the current number of items in the treeview
        num_items = len(self.watchlist_table.get_children())

        if num_items % 2 == 1:
            self.watchlist_table.insert(
                "",
                "end",
                iid=watchlist_id,
                text=num_items + 1,
                values=value,
                tags=("oddrow",),
            )
        else:
            self.watchlist_table.insert(
                "",
                "end",
                iid=watchlist_id,
                text=num_items + 1,
                values=value,
                tags=("evenrow",),
            )

    # Method to update watchlist in table
    def update_watchlist_in_watchlist_table(
        self,
        watchlist_id,
        unique_ids_string,
    ):

        watchlist_id_in_table = self.watchlist_table.get_children()

        if str(watchlist_id) in watchlist_id_in_table:

            self.watchlist_table.set(str(watchlist_id), 2, unique_ids_string)

# Method to add all watchlist rows in table
def insert_all_watchlists_in_watchlists_table():

    # Get all the watchlist from the db
    all_watchlist_dataframe = get_all_watchlists_from_db()

    all_row_values = all_watchlist_dataframe.to_records(index=False)

    # Insert the Watchlist in the GUI
    for row_value in all_row_values:
        variables.screen.screen_watchlist_obj.insert_watchlist_in_watchlist_table(
            row_value
        )
