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
from com.mysql_io_accounts import *
from tkinter import *
from com.mysql_io_account_group import *
import re
from com.utilities import *


# Class for accounts tab
class ScreenAccounts(object):
    def __init__(self, master_notebook):
        """
        Constructor
        """
        self.notebook = master_notebook

        # Create account tab
        self.accounts_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.accounts_tab, text="  Accounts  ")

        # Method to create account tab GUI components
        self.create_accounts_tab()

    # Method to create GUI for account tab
    def create_accounts_tab(self):
        # Create Treeview Frame for accounts instances
        accounts_table_frame = ttk.Frame(self.accounts_tab, padding=10)
        accounts_table_frame.pack(pady=10)

        # Place in center
        accounts_table_frame.place(relx=0.5, anchor=tk.CENTER)
        accounts_table_frame.place(y=175)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(accounts_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview Table
        self.accounts_table = ttk.Treeview(
            accounts_table_frame,
            yscrollcommand=tree_scroll.set,
            height=12,
            selectmode="extended",
        )

        # Pack to the screen
        self.accounts_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.accounts_table.yview)

        # Get columns for accounts table
        accounts_table_columns = copy.deepcopy(variables.accounts_table_columns)

        # Set columns for accounts table
        self.accounts_table["columns"] = accounts_table_columns

        # Creating Column
        self.accounts_table.column("#0", width=0, stretch="no")

        # Creating columns for scale trader table
        for column_name in accounts_table_columns:
            self.accounts_table.column(column_name, anchor="center", width=222)

        # Create Heading
        self.accounts_table.heading("#0", text="", anchor="w")

        # Create headings for accounts table
        for column_name in accounts_table_columns:
            self.accounts_table.heading(column_name, text=column_name, anchor="center")

        # Back ground for rows in table
        self.accounts_table.tag_configure("oddrow", background="white")
        self.accounts_table.tag_configure("evenrow", background="lightblue")

        self.create_account_conditions_table()

    # Method to create account  condition table
    def create_account_conditions_table(self):
        # Get frame for button to add custom columns
        account_condition_button_frame = ttk.Frame(self.accounts_tab, padding=10)
        account_condition_button_frame.pack(pady=10)

        # Initialize button to add custom column
        add_account_condition_button = ttk.Button(
            account_condition_button_frame,
            text="Add Account Condition",
            command=lambda: variables.screen.screen_cas_obj.display_enter_condition_popup(
                flag_account_condition=True
            ),
        )

        # Place add custom column button
        add_account_condition_button.grid(row=0, column=0, padx=10, pady=10)

        # Initialize button to delte custom column
        delete_account_condition_button = ttk.Button(
            account_condition_button_frame,
            text="Delete Account Condition",
            command=lambda: self.delete_selected_condition(),
        )

        # Place delete custom column button
        delete_account_condition_button.grid(row=0, column=1, padx=10, pady=10)

        # Place in center
        account_condition_button_frame.place(relx=0.5, anchor=tk.CENTER)
        account_condition_button_frame.place(y=370)

        # Create Treeview Frame for accounts condition instances
        accounts_condition_table_frame = ttk.Frame(self.accounts_tab, padding=10)
        accounts_condition_table_frame.pack(pady=10)

        # Place in center
        accounts_condition_table_frame.place(relx=0.5, anchor=tk.CENTER)
        accounts_condition_table_frame.place(y=580)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(accounts_condition_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview Table
        self.accounts_conditions_table = ttk.Treeview(
            accounts_condition_table_frame,
            yscrollcommand=tree_scroll.set,
            height=14,
            selectmode="extended",
        )

        # Pack to the screen
        self.accounts_conditions_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.accounts_table.yview)

        # Get columns for accounts table
        accounts_conditions_table_columns = copy.deepcopy(
            variables.account_conditions_table_columns
        )

        # Set columns for accounts table
        self.accounts_conditions_table["columns"] = accounts_conditions_table_columns

        # Creating Column
        self.accounts_conditions_table.column("#0", width=0, stretch="no")

        # Creating columns for scale trader table
        for column_name in accounts_conditions_table_columns:
            if column_name == "Table ID":
                self.accounts_conditions_table.column(
                    column_name, anchor="center", width=0, stretch="no"
                )

            elif column_name == "Account ID":
                self.accounts_conditions_table.column(
                    column_name, anchor="center", width=258
                )

            else:
                self.accounts_conditions_table.column(
                    column_name, anchor="center", width=1290
                )

        # Create Heading
        self.accounts_conditions_table.heading("#0", text="", anchor="w")

        # Create headings for accounts table
        for column_name in accounts_conditions_table_columns:
            self.accounts_conditions_table.heading(
                column_name, text=column_name, anchor="center"
            )

        # Back ground for rows in table
        self.accounts_conditions_table.tag_configure("oddrow", background="white")
        self.accounts_conditions_table.tag_configure("evenrow", background="lightblue")

    # Method to delete account conditions
    def delete_selected_condition(self):
        # Get selected row
        condition_account_id_combined_selected = (
            self.accounts_conditions_table.selection()
        )

        # Iterate slected rows
        for condition_account_id_combined in condition_account_id_combined_selected:
            # get values of selected row
            values = self.accounts_conditions_table.item(
                condition_account_id_combined, "values"
            )  # get the values of the selected row

            # Get values
            account_id = values[0]

            # Get condition
            condition = values[1]

            # delte from db table
            delete_account_condition_in_db(account_id, condition)

            # set value high so account liquidation check will be updated
            variables.counter_accounts_value = 10**10

            # Get table id from accoutn id and condition
            table_id = account_id + "_" + condition

            # Delete from table
            self.accounts_conditions_table.delete(table_id)

            # Update table
            self.update_account_conditions_table()

    # Method to update account condition table
    def update_account_conditions_table(self):
        # Get df fof all values
        account_condition_table_df = get_all_conditions_from_db()

        table_ids_in_table = self.accounts_conditions_table.get_children()

        # Iterate rows of df
        for indx, row in account_condition_table_df.iterrows():
            # Get combination of account and condition
            account_condition_combined = row["Account ID"] + "_" + row["Condition"]

            # Convert to list
            row = list(row)

            # Append combination of account and condition
            row.append(account_condition_combined)

            # convert to tuple
            row = tuple(row)

            # Check if it is already in table
            if account_condition_combined in table_ids_in_table:
                # Update the row at once.
                self.accounts_conditions_table.item(
                    account_condition_combined, values=row
                )

            else:
                # Insert it in the table
                self.accounts_conditions_table.insert(
                    "",
                    "end",
                    iid=account_condition_combined,
                    text="",
                    values=row,
                    tags=("oddrow",),
                )

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in account_condition_table_df.iterrows():
            account_condition_combined = row["Account ID"] + "_" + row["Condition"]

            # If table id in table
            if (
                account_condition_combined
                in self.accounts_conditions_table.get_children()
            ):
                self.accounts_conditions_table.move(
                    account_condition_combined, "", counter_row
                )

                if counter_row % 2 == 0:
                    self.accounts_conditions_table.item(
                        account_condition_combined, tags="evenrow"
                    )
                else:
                    self.accounts_conditions_table.item(
                        account_condition_combined, tags="oddrow"
                    )

                # Increase row count
                counter_row += 1

    # Method to update table
    def update_accounts_table(self):
        # Get local copy of account table df
        local_accounts_table_dataframe = copy.deepcopy(
            variables.accounts_table_dataframe
        )

        # account ids in GUI table
        account_ids_in_table = self.accounts_table.get_children()

        # Iterate rows in df
        for indx, row in local_accounts_table_dataframe.iterrows():
            # Get account id
            account_id = row["Account ID"]

            # Get values and format values
            nlv_value = (
                "None"
                if row["Net Liquidity Value"] in ["None", None, "N/A"]
                else f"{row['Net Liquidity Value']:,.2f}"
            )
            sma_value = (
                "None"
                if row["Special Memorandum Account"] in ["None", None, "N/A"]
                else f"{row['Special Memorandum Account']:,.2f}"
            )
            pnl_value = (
                "None"
                if row["Day Profit and Loss"] in ["None", None, "N/A"]
                else f"{row['Day Profit and Loss']:,.2f}"
            )
            cel_value = (
                "None"
                if row["Current Excess Liquidity"] in ["None", None, "N/A"]
                else f"{row['Current Excess Liquidity']:,.2f}"
            )
            utilized_margin_value = (
                "None"
                if row["Utilised Margin"] in ["None", None, "N/A"]
                else f"{row['Utilised Margin']:,.2f}"
            )
            liquidation_mode = str(variables.flag_account_liquidation_mode[account_id])

            # Update row
            row = (
                account_id,
                nlv_value,
                sma_value,
                pnl_value,
                cel_value,
                utilized_margin_value,
                liquidation_mode,
            )

            # Check account id present in table
            if account_id in account_ids_in_table:
                # Update the row at once.
                self.accounts_table.item(account_id, values=tuple(row))

            else:
                # Insert it in the table
                self.accounts_table.insert(
                    "",
                    "end",
                    iid=account_id,
                    text="",
                    values=tuple(row),
                    tags=("oddrow",),
                )

        # account ids in GUI table
        account_ids_in_table = self.accounts_table.get_children()

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in local_accounts_table_dataframe.iterrows():
            # account id
            account_id = str(row["Account ID"])

            # If unique_id in table
            if account_id in account_ids_in_table:
                self.accounts_table.move(account_id, "", counter_row)

                if counter_row % 2 == 0:
                    self.accounts_table.item(account_id, tags="evenrow")
                else:
                    self.accounts_table.item(account_id, tags="oddrow")

                # Increase row count
                counter_row += 1

    # Method to select accounts
    def get_accounts_for_condition(self, user_entered_condition):
        # Create a enter unique id popup window
        enter_account_id_popup = tk.Toplevel()

        title = f"Enter Accounts"
        enter_account_id_popup.title(title)

        enter_account_id_popup.geometry("200x220")

        # Create a frame for the input fields
        trade_input_frame_acc = ttk.Frame(enter_account_id_popup, padding=0)
        trade_input_frame_acc.pack(side=TOP, fill=BOTH)

        ttk.Label(
            trade_input_frame_acc,
            text="Select Account IDs",
            width=18,
            anchor="center",
            justify="center",
        ).grid(column=1, row=0, padx=5, pady=10)

        # Create the "Add Accounts Ids" button
        ttk.Button(
            trade_input_frame_acc,
            text="Add Account Ids",
            command=lambda: add_account_ids(),
        ).grid(column=1, row=6, padx=5, pady=10)

        # Create a frame for the input fields
        listbox_input_frame_acc = ttk.Frame(trade_input_frame_acc, padding=0)
        listbox_input_frame_acc.grid(column=1, row=1, padx=30, pady=10, rowspan=4)

        # Create a listbox
        listbox = Listbox(
            listbox_input_frame_acc,
            width=20,
            height=7,
            selectmode=MULTIPLE,
            exportselection=False,
        )
        scrollbar = Scrollbar(listbox_input_frame_acc)

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
        for indx, account_id in enumerate(variables.current_session_accounts, start=1):
            listbox.insert(indx, "Account: " + account_id)

            listbox_index = indx

        account_group_df = get_all_account_groups_from_db()

        for indx, account_id in enumerate(
            account_group_df["Group Name"].to_list(), start=1
        ):
            listbox.insert(listbox_index + indx, "Group: " + account_id)

        listbox.pack()

        # On click method for button
        def add_account_ids():
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
                            if account not in variables.current_session_accounts:
                                # Error pop up
                                error_title = f"For Account ID: {account}, Account ID is unavailable in current session."
                                error_string = f"For Account ID: {account}, Can not trade combo\nbecause Account ID is unavailable in current session."

                                variables.screen.display_error_popup(
                                    error_title, error_string
                                )

                                return

                            account_id_list.append(account)

            # Get unique account ids and sort them
            account_id_list = sorted(list(set(account_id_list)))

            # check if list is empty
            if account_id_list == []:
                # Error pop up
                error_title = f"No Account IDs Selected."
                error_string = f"No Account IDs Selected."

                variables.screen.display_error_popup(error_title, error_string)

                return

            # Get table ids in account conditions table
            table_ids_in_table = self.accounts_conditions_table.get_children()

            # Iterate every account user selected
            for account in account_id_list:
                # Table ID
                table_id = account + "_" + user_entered_condition

                if table_id not in table_ids_in_table:
                    # Insert in db
                    insert_account_condition_in_db(account, user_entered_condition)

                    # set value high so account liquidation check will be updated
                    variables.counter_accounts_value = 10**10

                    # Update table
                    self.update_account_conditions_table()

            # Destroy pop up
            enter_account_id_popup.destroy()


# run Rm check twice for order placements
def rm_check_for_order(account_id):
    # Run RM checks
    rm_check_result = run_risk_management_checks(account_id)

    # If RM check failed
    if not rm_check_result:
        # sleep
        time.sleep(variables.rm_checks_interval_if_failed)

        # Run RM checks again
        rm_check_result = run_risk_management_checks(account_id)

        # If RM checks failed again
        if not rm_check_result:
            # Error pop up
            """error_title = f"For Account ID: {account_id}, RM checks failed"
            error_string = f"For Account ID: {account_id}, RM checks failed"

            variables.screen.display_error_popup(error_title, error_string)"""
            return False

        else:
            return True

    else:
        return True


# Method to run Rm checks
def run_risk_management_checks(account_id, flag_liquidation_check=False):
    # Get value dataframe for account id
    conditions_df = get_account_conditions_from_db(account_id)

    # check if df is empty
    if conditions_df.empty:
        # If flag for liquidation check is true
        if flag_liquidation_check:
            # set value to false
            variables.flag_account_liquidation_mode[account_id] = False

        return True

    # Get list of conditions
    conditions_list = conditions_df["Condition"].to_list()

    # Iterate conditions
    for condition in conditions_list:
        # Relace % term by value / 100
        def replace_percent(match):
            number = int(match.group(1)) / 100
            return "{:.2f}".format(number)

        pattern = r"(\d+)\s*%"

        condition = re.sub(pattern, replace_percent, condition)

        # check if tickers PNL is in condition
        if "Tickers PNL" in condition:
            value_for_row = True

            for con_id in variables.map_account_id_and_con_id_to_pnl[account_id]:
                try:
                    # Get row for account id
                    account_row = variables.accounts_table_dataframe.loc[
                        variables.accounts_table_dataframe["Account ID"] == account_id
                    ]

                    # Get the first row
                    account_row = account_row.iloc[0]

                    # Add an extra column 'New Column' with a value
                    account_row["Tickers PNL"] = (
                        variables.map_account_id_and_con_id_to_pnl[account_id][con_id]
                    )

                    # Get Expression and flag for valid results to eval further
                    _, condition = evaluate_condition(
                        variables.accounts_table_columns[1:-1] + ["Tickers PNL"],
                        account_row,
                        condition,
                        None,
                        None,
                    )

                    # Evaluate value of expression
                    expression_value = eval(str(condition))

                    # Get value in boolean
                    value_for_row = bool(expression_value)

                except Exception as e:
                    # Set value to true
                    value_for_row = False

                    # Print  to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception while calculating values of account conditions, Exp: {e}"
                        )

                # check if value is false
                if not value_for_row:
                    # If flag for liquidation check is true
                    if flag_liquidation_check:
                        # set value to True
                        variables.flag_account_liquidation_mode[account_id] = True

                    return False

                    break

        else:
            try:
                # Get row for account id
                account_row = variables.accounts_table_dataframe.loc[
                    variables.accounts_table_dataframe["Account ID"] == account_id
                ]

                # Get the first row
                account_row = account_row.iloc[0]

                # Add an extra column 'New Column' with a value
                account_row["Tickers PNL"] = None

                # Get Expression and flag for valid results to eval further
                _, condition = evaluate_condition(
                    variables.accounts_table_columns[1:-1] + ["Tickers PNL"],
                    account_row,
                    condition,
                    None,
                    None,
                )

                # Evaluate value of expression
                expression_value = eval(str(condition))

                # Get value in boolean
                value_for_row = bool(expression_value)

            except Exception as e:
                # Set value to true
                value_for_row = False

                # Print  to console
                if variables.flag_debug_mode:
                    print(
                        f"Exception while calculating values of account conditions, Exp: {e}"
                    )

        # check if value is false
        if not value_for_row:
            # If flag for liquidation check is true
            if flag_liquidation_check:
                # set value to True
                variables.flag_account_liquidation_mode[account_id] = True

            return False

            break

    # If flag for liquidation check is true
    if flag_liquidation_check:
        # set value to True
        variables.flag_account_liquidation_mode[account_id] = False

    return True
