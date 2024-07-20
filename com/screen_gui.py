"""
Created on 16-Mar-2023

@author: Karan
"""
import time
import tkinter

from com import *
from com.variables import *
from com.combination_helper import *
from com.mysql_io import *
from com.order_execution import *
from com.screen_price_chart import PriceChart
from com.screen_positions import ScreenPositions
from com.screen_custom_columns import *
from com.screen_cas import ScreenCAS
from com.screen_watchlist_manager import ScreenWatchList
from com.screen_scale_trader_manager import ScreenScaleTrader
from com.upload_combo_to_application import *
from com.download_combinations_from_app import *
from com.upload_orders_from_csv import *
from tkinter import filedialog
from com.mysql_io_watchlist import *
from com.scale_trade_helper import *
from com.identify_trading_class_for_fop import *
import asyncio
from com.upload_orders_from_csv import update_values_based_on_order_type
from com.screen_accounts_tab import ScreenAccounts
from com.screen_conditional_series import ScreenConditionalSeries
from com.screen_accounts_tab import rm_check_for_order
from com.mysql_io_account_group import *
from tkinter import *
from com.trade_rm_check_result_module import *
from com.single_combo_value_calculations import single_combo_values
from com.screen_filter_tab import ScreenFilter
from com.screen_user_inputs_manager import ScreenUserInputs
from com.screen_portflio_tab import ScreenPortfolio

class ScreenGUI(threading.Thread):
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Option Combo Scanner")
        self.window.geometry("1600x800")  # Set the window size

        # Create the notebook widget with three tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill="both")

        # Create the Multi-Leg Combo Creator tab
        self.combo_creator_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.combo_creator_tab, text="Combo Creator")
        self.create_combo_creator_tab()

        # Create the Market Watch and Order Placement tab
        self.market_watch_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.market_watch_tab, text=" Market Watch")
        self.create_market_watch_tab()

        # Create the Order Book tab
        self.order_book_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.order_book_tab, text=" Order Book  ")
        self.create_order_book_tab()

        # Create Positions Tab
        self.screen_position_obj = ScreenPositions(self.notebook)

        # Create CAS Tab
        self.screen_cas_obj = ScreenCAS(self.notebook)

        # Create Watchlist Tab
        self.screen_watchlist_obj = ScreenWatchList(self.notebook)

        # Create Scale trader Tab
        self.screen_scale_trader_obj = ScreenScaleTrader(self.notebook)

        # Create custom column tab
        self.screen_custom_columns_obj = CustomColumns(self.notebook)

        # Create accounts tab
        self.screen_accounts_obj = ScreenAccounts(self.notebook)

        # Create filter tab
        self.screen_filter_obj = ScreenFilter(self.notebook)

        # cereate conditional series tab
        self.screen_conditional_series_tab = ScreenConditionalSeries(self.notebook)

        # create user input tab
        self.screen_user_inputs_tab = ScreenUserInputs(self.notebook)

        # create portfolio tab
        self.screen_portfolio_tab = ScreenPortfolio(self.notebook)


    # Method to dispaly error pop up
    def display_error_popup(self, error_title, error_string):

        # Create a error popup window
        error_popup = tk.Toplevel()
        error_popup.title(error_title)

        error_popup.geometry("400x100")

        # Create a frame for the input fields
        error_frame = ttk.Frame(error_popup, padding=20)
        error_frame.pack(fill="both", expand=True)

        # Add labels and entry fields for each column in the table
        error_label = ttk.Label(
            error_frame, text=error_string, width=80, anchor="center"
        )
        error_label.place(relx=0.5, rely=0.5, anchor="center")

    # Meyhod to run main screen
    def run(self):
        # Create and configure your GUI here...
        self.window.mainloop()



    # Method to design combo creation tab
    def create_combo_creator_tab(self):
        # Create a frame for the user input fields
        input_frame = ttk.Frame(self.combo_creator_tab, padding=20)
        input_frame.pack(fill="both", expand=True)

        # Add a label and entry field for the user to enter an integer
        ttk.Label(input_frame, text="Enter number of legs:").grid(
            column=0, row=0, padx=(535, 5), pady=5
        )
        rows_entry = ttk.Entry(input_frame)
        rows_entry.grid(column=1, row=0, padx=5, pady=5)

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

        # Create Treeview Frame for active combo table
        active_combo_table_frame = ttk.Frame(self.combo_creator_tab, padding=20)
        active_combo_table_frame.pack(pady=20)
        active_combo_table_frame.pack(fill="both", expand=True)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(active_combo_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.combination_table = ttk.Treeview(
            active_combo_table_frame,
            yscrollcommand=tree_scroll.set,
            height=27,
            selectmode="extended",
        )
        # Pack to the screen
        self.combination_table.pack(fill="both", expand=True)

        # Configure the scrollbar
        tree_scroll.config(command=self.combination_table.yview)

        # Place table fram in center
        active_combo_table_frame.place(relx=0.5, anchor=tk.CENTER)
        active_combo_table_frame.place(y=415)

        # Define Our Columns
        self.combination_table["columns"] = (
            "Unique ID",
            "#Legs",
            "Tickers",
            "#Buys",
            "#Sells",
            "#STK",
            "#FUT",
            "#OPT",
            "#FOP",
        )

        # Formate Our Columns
        self.combination_table.column("#0", width=0, stretch="no")
        self.combination_table.column("Unique ID", anchor="center", width=130)
        self.combination_table.column("#Legs", anchor="center", width=130)
        self.combination_table.column("Tickers", anchor="center", width=500)
        self.combination_table.column("#Buys", anchor="center", width=130)
        self.combination_table.column("#Sells", anchor="center", width=130)
        self.combination_table.column("#STK", anchor="center", width=130)
        self.combination_table.column("#FUT", anchor="center", width=130)
        self.combination_table.column("#OPT", anchor="center", width=130)
        self.combination_table.column("#FOP", anchor="center", width=130)

        # Create Headings
        self.combination_table.heading("#0", text="", anchor="w")
        self.combination_table.heading("Unique ID", text="Unique ID", anchor="center")
        self.combination_table.heading("#Legs", text="#Legs", anchor="center")
        self.combination_table.heading("Tickers", text="Tickers", anchor="center")
        self.combination_table.heading("#Buys", text="#Buys", anchor="center")
        self.combination_table.heading(
            "#Sells",
            text="#Sells",
            anchor="center",
        )
        self.combination_table.heading(
            "#STK",
            text="#STK",
            anchor="center",
        )
        self.combination_table.heading(
            "#FUT",
            text="#FUT",
            anchor="center",
        )
        self.combination_table.heading(
            "#OPT",
            text="#OPT",
            anchor="center",
        )
        self.combination_table.heading("#FOP", text="#FOP", anchor="center")

        self.combination_table.tag_configure("oddrow", background="white")
        self.combination_table.tag_configure("evenrow", background="lightblue")

        def treeview_right_click(event):
            # get the Treeview row that was clicked
            row = self.combination_table.identify_row(event.y)
            if row:
                # select the row
                self.combination_table.selection_set(row)

                # create a context menu
                menu = tk.Menu(self.combination_table, tearoff=0)
                menu.add_command(label="Delete", command=lambda: self.delete_row())
                menu.add_command(
                    label="View Details",
                    command=lambda: self.display_combination_details("combo_creator"),
                )
                menu.add_command(
                    label="Edit Combination",
                    command=lambda: self.display_edit_combination_popup(),
                )

                # display the context menu at the location of the mouse cursor
                menu.post(event.x_root, event.y_root)

        self.combination_table.bind("<Button-3>", treeview_right_click)

        # Add a button to create the combo
        create_button = ttk.Button(
            input_frame,
            text="Create Combo",
            command=lambda: self.create_combination_popup(rows_entry, "Combo"),
        )
        create_button.grid(column=2, row=0, padx=(5, 265), pady=5)

        # Add a button to delete multiple combinations
        delete_combinations_button = ttk.Button(
            input_frame,
            text="Delete Combinations",
            command=lambda: self.delete_all_selected_combinations_start_thread(
                delete_combinations_button
            ),
        )
        delete_combinations_button.grid(column=3, row=0, padx=5, pady=5)

        # Add a button to upload the combo to application
        upload_combo_button = ttk.Button(
            input_frame,
            text="Upload Combinations",
            command=lambda: self.upload_combination_csv_file_to_app(
                upload_combo_button
            ),
        )
        upload_combo_button.grid(column=4, row=0, padx=5, pady=5)
        # upload_combo_button.place(x=300,y=5)

        # Add a button to download the combo to csv file
        download_combo_button = ttk.Button(
            input_frame,
            text="Download Combinations",
            command=lambda: self.download_combination_csv_file_from_app(
                download_combo_button
            ),
        )
        download_combo_button.grid(column=5, row=0, padx=5, pady=5)
        # download_combo_button.place(x=450,y=5)

        # Place in center
        input_frame.place(relx=0.5, anchor=tk.CENTER)

        input_frame.place(y=30)

        # Update combo table based on watchlist
        self.update_combo_details_table()

    # Delete multiple combinations
    def delete_all_selected_combinations_start_thread(self, delete_combinations_button):
        delete_combo_thread = threading.Thread(
            target=self.delete_all_selected_combinations,
            args=(delete_combinations_button,),
        )
        delete_combo_thread.start()

    # Delete multiple combinations
    def delete_all_selected_combinations(self, delete_combinations_button):

        # Get values of selected rows
        selected_items = self.combination_table.selection()

        # Disable the button
        delete_combinations_button.config(state="disabled")

        # Delete all selected combinations

        for unique_id in selected_items:
            try:

                # Delete combination function for each combination to be deleted
                self.delete_row(int(float(unique_id)))

            except Exception as e:
                # Print to console
                if variables.flag_debug_mode:
                    print(f"Error in deleting multiple combinations: {e}")

        delete_combinations_button.config(state="normal")

    # Download combinations
    def download_combination_csv_file_from_app(self, download_combo_button):

        # Disabled download combination button
        download_combo_button.config(state="disabled")

        # Place combinations based on values in CSV
        download_combo_thread = threading.Thread(
            target=self.download_combination_csv_file_from_app_from_thread,
            args=(download_combo_button,),
        )
        download_combo_thread.start()

    # Download combinations from thread
    def download_combination_csv_file_from_app_from_thread(self, download_combo_button):

        # Get all combination from database
        all_active_combination_dataframe = get_primary_vars_db(
            variables.sql_table_combination
        )

        # Checking if dataframe is empty
        if all_active_combination_dataframe.empty:
            # Error Message
            error_title = error_string = f"Error - No Combinations found"
            variables.screen.display_error_popup(error_title, error_string)

            # Enabled download combo button
            download_combo_button.config(state="enabled")

            return

        # Rename a column
        all_active_combination_dataframe.rename(
            columns={"Lot Size": "Multiplier"}, inplace=True
        )

        combo_dataframe_columns = copy.deepcopy(
            variables.columns_for_download_combo_to_csv
        )

        # Re-arranging and ordering columns in dataframe as it should be in download CSV file (unique id used to create combo with leg)
        all_active_combination_dataframe = all_active_combination_dataframe.loc[
            :, combo_dataframe_columns[1:] + ["Unique ID"]
        ]

        try:
            # Group dataframe based on unique-id
            all_active_combination_dataframe = all_active_combination_dataframe.groupby(
                "Unique ID"
            )

            # Order values based on format and save csv file
            download_combo_from_app_to_csv(
                all_active_combination_dataframe,
                combo_dataframe_columns,
                download_combo_button,
            )
        except Exception as e:

            # Enabled download combo button
            download_combo_button.config(state="enabled")

            print(f"Inside downloading combination to CSV file, error is {e}")

    # Upload combinations
    def upload_combination_csv_file_to_app(self, upload_combo_button):

        # Disabled upload combinations button
        upload_combo_button.config(state="disabled")

        # Pop up to select file
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:

            # Place combinations based on values in CSV
            upload_combo_thread = threading.Thread(
                target=upload_combo_from_csv_to_app,
                args=(
                    file_path,
                    upload_combo_button,
                ),
            )
            upload_combo_thread.start()

        # Enabled upload combinations button
        upload_combo_button.config(state="enabled")

    # Method to update watchlist after combination deleted
    def update_watchlists_after_delete_combination(self, unique_id):

        # Get all the watchlist from the db
        all_watchlist_dataframe = get_all_watchlists_from_db()

        all_watchlist_dataframe = all_watchlist_dataframe.iloc[1:]

        try:
            # All watchlist names and watchlist ids
            all_watchlist_name = all_watchlist_dataframe["Watchlist Name"].to_list()
            all_watchlist_id = all_watchlist_dataframe["Watchlist ID"].to_list()

            for watchlist_name, watchlist_id in zip(
                all_watchlist_name, all_watchlist_id
            ):

                # Get all unique ids for watchlists
                unique_ids_in_watchlist = get_unique_id_in_watchlists_from_db(
                    watchlist_name
                )

                if unique_ids_in_watchlist == "None":
                    unique_ids_in_watchlist = ""

                # Convert string of unique ids to list
                unique_ids_in_watchlist = [
                    int(float(unique_id))
                    for unique_id in unique_ids_in_watchlist.split(",")
                    if len(unique_ids_in_watchlist) > 0
                ]

                # Check if deleted unique id is in watchlist and if yes then remove it from watchlist
                if unique_id in unique_ids_in_watchlist:

                    unique_ids_in_watchlist.remove(unique_id)

                # Create string of unique ids from updated list of unique ids
                unique_ids_string = ",".join(map(str, unique_ids_in_watchlist))

                # Update the database table for wathlist being updated
                update_watchlist_in_db(watchlist_id, unique_ids_string)

                # Reflect updated values in GUI watchlist tab
                variables.screen.screen_watchlist_obj.update_watchlist_in_watchlist_table(
                    watchlist_id, unique_ids_string
                )

        except Exception as e:

            if variables.flag_debug_mode:

                print(f"Error inside updating watchlist unique ids string, is {e}")

    # Method to delete all rows in position tab for particular unique id
    def delete_all_rows_in_position_tab_for_unique_id(self, unique_id):

        all_rows = self.screen_position_obj.positions_table.get_children()

        for row in all_rows:

            if row.split("_")[0] == str(unique_id):

                # Remove combination from the positions table
                self.screen_position_obj.positions_table.delete(row)

    # Method to delete all rows in cas condition tab for particular unique id
    def delete_all_rows_in_cas_condition_tab_for_unique_id(self, unique_id):

        all_rows = self.screen_cas_obj.cas_condition_table.get_children()

        for row in all_rows:
            values = self.screen_cas_obj.cas_condition_table.item(row, "values")

            if row.split("_")[0] == str(unique_id) and values[9] != "Failed":

                # Remove combination from the positions table
                self.screen_cas_obj.cas_condition_table.delete(row)

    # Method to delete combination
    def delete_row(self, unique_id=None):

        if unique_id == None:
            # Delete the active combo
            selected_item = self.combination_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.combination_table.item(
                selected_item, "values"
            )  # get the values of the selected row
            unique_id = int(values[0])
        else:
            selected_item = unique_id

        # terminate series
        terminate_series(unique_id)

        # failed cas condition having eval unique id same as unique id to delte
        # Update values in column 'Evaluation Unique ID' where 'Evaluation Unique ID' is equal to unique id
        variables.cas_condition_table_dataframe.loc[
            variables.cas_condition_table_dataframe["Evaluation Unique ID"]
            == str(unique_id),
            "Status",
        ] = "Failed"

        # Update values in column 'Evaluation Unique ID' where 'Evaluation Unique ID' is equal to unique id
        variables.cas_condition_table_dataframe.loc[
            variables.cas_condition_table_dataframe["Trading Combo Unique ID"].isin(
                [unique_id, str(unique_id)]
            ),
            "Status",
        ] = "Failed"

        # Update values in column 'Evaluation Unique ID' where 'Evaluation Unique ID' is equal to unique id
        variables.cas_condition_table_dataframe.loc[
            variables.cas_condition_table_dataframe["Evaluation Unique ID"]
            == str(unique_id),
            "Reason For Failed",
        ] = "Evaluation Unique ID Deleted"

        # Update values in column 'Evaluation Unique ID' where 'Evaluation Unique ID' is equal to unique id
        variables.cas_condition_table_dataframe.loc[
            variables.cas_condition_table_dataframe["Trading Combo Unique ID"].isin(
                [unique_id, str(unique_id)]
            ),
            "Reason For Failed",
        ] = "Trading Unique ID Deleted"

        # print(variables.cas_condition_table_dataframe.to_string())
        # print(variables.cas_condition_table_dataframe.to_string())
        # Update GUI table
        variables.flag_cas_condition_table_watchlist_changed = True
        variables.screen.screen_cas_obj.update_cas_condition_table_watchlist_change()

        # update evaluation ids
        failed_eval_unique_id_cas_condition_db(unique_id)

        # fail conditional series if unique id present in as trading or evaluation unique id
        variables.screen.screen_conditional_series_tab.make_series_failed(unique_id)

        # Remove combination from the table
        self.combination_table.delete(selected_item)

        # Cancel subscription
        # removed the orders from screen already
        delete_combination(unique_id)

        # Update scale trade after combo delte
        variables.screen.screen_scale_trader_obj.terminate_all_scale_trade_for_unique_id(
            unique_id
        )

        # Remove combination from the market watch table
        self.market_watch_table.delete(unique_id)

        # Get all account ids
        """for account_id in variables.current_session_accounts:
        
            # Remove combination from the positions table
            self.screen_position_obj.positions_table.delete(f"{unique_id}_{account_id}")"""
        self.delete_all_rows_in_position_tab_for_unique_id(unique_id)

        # Remove combination from the cas_table table
        self.screen_cas_obj.cas_table.delete(unique_id)

        # Getting all the unique ids in cas_condition table
        all_table_id_in_cas_condition = (
            self.screen_cas_obj.cas_condition_table.get_children()
        )

        self.update_watchlists_after_delete_combination(unique_id)

        # Get all account ids
        self.delete_all_rows_in_cas_condition_tab_for_unique_id(unique_id)

        variables.screen.screen_conditional_series_tab.update_conditional_series_table()

        variables.screen.screen_portfolio_tab.update_portfolio_combo_table(flag_delete=True)

        variables.screen.screen_portfolio_tab.update_portfolio_legs_table(flag_delete=True)
        """for account_id in variables.current_session_accounts:
        
            table_id = f"{unique_id}_{account_id}"
        
            # Remove unique id from the cas_condition_table if exists
            if table_id in all_table_id_in_cas_condition:
                
                self.screen_cas_obj.cas_condition_table.delete(table_id)
                
            else:
                # Print to console
                if variables.flag_debug_mode:
                    print(f"Screen 239, Cas condition was not present, {table_id} , {all_table_id_in_cas_condition}")"""

        # update tables after the combo is deleted, (color scheme)
        self.update_tables_after_combo_deleted()

    # Method to create combination
    def create_combination_popup(
        self,
        rows_entry,
        combo_tab_or_cas_tab,
        title_string="Add Combo",
        cas_row_input_popup=None,
        unique_id=None,
        refer_price=None,
        refer_position=None,
        num_rows=None,
        combo_obj=None,
        flag_edit_combo=False,
        target_positions_dict=None,
        flag_add_legs_conditional_add_switch=False,
        bypass_rm_account_check=None,
        evalaution_unique_id=None,
        flag_conditional_series=False,
        modify_seq_data=None,
        index=None,
    ):

        # num_rows, combo_obj, flag_edit_combo are currently being used when we are editing the combo,

        # Get the number of rows entered by the user
        if (
            num_rows != None
            and flag_edit_combo
            and combo_obj != None
            and unique_id != None
        ):
            try:
                num_rows = int(num_rows)
                old_combo_unique_id = unique_id
            except:
                self.display_error_popup(
                    "Error", "Number of Legs for edit combo is required."
                )
                return
        else:
            try:
                num_rows = int(rows_entry.get())

            except Exception as e:

                self.display_error_popup("Error", "Please Enter Valid Number of Legs.")
                return

            # Check if target position is not None
            """if target_position_entry != None:
                
                try:
                    target_position = int(target_position_entry.get())
                    
                    
    
    
                except:
                    self.display_error_popup("Error", "Please Enter Target Position")
                    return"""
            # Check if flag for adding legs from combo is True
            if flag_add_legs_conditional_add_switch:

                # Buy legs and Sell legs
                buy_legs = combo_obj.buy_legs
                sell_legs = combo_obj.sell_legs
                all_legs = buy_legs + sell_legs

                # if number of legs entered is less than number of legs of combo
                if num_rows < len(all_legs):

                    num_rows = len(all_legs)

        # Destroy the cas number of legs input popup
        if combo_tab_or_cas_tab in ["ADD", "SWITCH"]:
            cas_row_input_popup.destroy()

        # Create a popup window with the table
        popup = tk.Toplevel()
        popup.title(title_string)
        custom_height = min(max((num_rows * 40) + 100, 150), 750)

        popup.geometry("1335x" + str(custom_height))

        # Create a frame for the input fields
        input_frame = ttk.Frame(popup, padding=20)
        input_frame.pack(fill="both", expand=True)

        # Add labels and entry fields for each column in the table
        ttk.Label(
            input_frame,
            text="Action",
            width=12,
            anchor="center",
        ).grid(column=0, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="SecType",
            width=12,
            anchor="center",
        ).grid(column=1, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Symbol",
            width=12,
            anchor="center",
        ).grid(column=2, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="#Lots",
            width=12,
            anchor="center",
        ).grid(column=3, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="DTE",
            width=12,
            anchor="center",
        ).grid(column=4, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Delta",
            width=12,
            anchor="center",
        ).grid(column=5, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Right",
            width=12,
            anchor="center",
        ).grid(column=6, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Multiplier",
            width=12,
            anchor="center",
        ).grid(column=7, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Exchange",
            width=12,
            anchor="center",
        ).grid(column=8, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Trading Class",
            width=12,
            anchor="center",
        ).grid(column=9, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Currency",
            width=12,
            anchor="center",
        ).grid(column=10, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="ConId",
            width=12,
            anchor="center",
        ).grid(column=11, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Primary Exch.",
            width=12,
            anchor="center",
        ).grid(column=12, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Strike",
            width=12,
            anchor="center",
        ).grid(column=13, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Expiry",
            width=12,
            anchor="center",
        ).grid(column=14, row=0, padx=5, pady=5)

        # Create a list of options
        action_type_options = ["BUY", "SELL"]
        sec_type_options = ["", "STK", "FUT", "OPT", "FOP"]
        right_type_options = ["", "CALL", "PUT"]

        drop_down_items_dict = {}

        def select_buy(event, combo_new):
            combo_new.current(0)

        def select_sell(event, combo_new):
            combo_new.current(1)

        def select_call(event, combo_new):
            combo_new.current(1)

        def select_put(event, combo_new):
            combo_new.current(2)

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
            action_combo_box = f"action_combo_box_{row_loc}"
            sec_type_combo_box = f"sec_type_combo_box_{row_loc}"
            right_combo_box = f"right_combo_box_{row_loc}"

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

            drop_down_items_dict[row_loc][action_combo_box] = ttk.Combobox(
                input_frame,
                width=10,
                values=action_type_options,
                state="readonly",
                style="Custom.TCombobox",
            )
            drop_down_items_dict[row_loc][action_combo_box].current(0)
            drop_down_items_dict[row_loc][action_combo_box].grid(
                column=0, row=row_loc, padx=5, pady=5
            )

            drop_down_items_dict[row_loc][action_combo_box].bind(
                "s",
                lambda event, combo_new=drop_down_items_dict[row_loc][
                    action_combo_box
                ]: select_sell(event, combo_new),
            )
            drop_down_items_dict[row_loc][action_combo_box].bind(
                "b",
                lambda event, combo_new=drop_down_items_dict[row_loc][
                    action_combo_box
                ]: select_buy(event, combo_new),
            )
            drop_down_items_dict[row_loc][action_combo_box].bind(
                "S",
                lambda event, combo_new=drop_down_items_dict[row_loc][
                    action_combo_box
                ]: select_sell(event, combo_new),
            )
            drop_down_items_dict[row_loc][action_combo_box].bind(
                "B",
                lambda event, combo_new=drop_down_items_dict[row_loc][
                    action_combo_box
                ]: select_buy(event, combo_new),
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
                column=1, row=row_loc, padx=5, pady=5
            )

            symbol_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            symbol_entry.grid(column=2, row=row_loc, padx=5, pady=5)

            quantity_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            quantity_entry.grid(column=3, row=row_loc, padx=5, pady=5)

            dte_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            dte_entry.grid(column=4, row=row_loc, padx=5, pady=5)

            delta_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            delta_entry.grid(column=5, row=row_loc, padx=5, pady=5)

            drop_down_items_dict[row_loc][right_combo_box] = ttk.Combobox(
                input_frame,
                width=10,
                values=right_type_options,
                state="readonly",
                style="Custom.TCombobox",
            )
            drop_down_items_dict[row_loc][right_combo_box].current(0)
            drop_down_items_dict[row_loc][right_combo_box].grid(
                column=6, row=row_loc, padx=5, pady=5
            )

            drop_down_items_dict[row_loc][right_combo_box].bind(
                "c",
                lambda event, combo_new=drop_down_items_dict[row_loc][
                    right_combo_box
                ]: select_call(event, combo_new),
            )
            drop_down_items_dict[row_loc][right_combo_box].bind(
                "p",
                lambda event, combo_new=drop_down_items_dict[row_loc][
                    right_combo_box
                ]: select_put(event, combo_new),
            )
            drop_down_items_dict[row_loc][right_combo_box].bind(
                "C",
                lambda event, combo_new=drop_down_items_dict[row_loc][
                    right_combo_box
                ]: select_call(event, combo_new),
            )
            drop_down_items_dict[row_loc][right_combo_box].bind(
                "P",
                lambda event, combo_new=drop_down_items_dict[row_loc][
                    right_combo_box
                ]: select_put(event, combo_new),
            )

            lot_size_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            lot_size_entry.grid(column=7, row=row_loc, padx=5, pady=5)

            exchange_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            exchange_entry.grid(column=8, row=row_loc, padx=5, pady=5)

            trading_class_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            trading_class_entry.grid(column=9, row=row_loc, padx=5, pady=5)

            currency_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            currency_entry.grid(column=10, row=row_loc, padx=5, pady=5)

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

            con_id_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            con_id_entry.grid(column=11, row=row_loc, padx=5, pady=5)

            primary_exchange_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            primary_exchange_entry.grid(column=12, row=row_loc, padx=5, pady=5)

            strike_entry = ttk.Entry(
                input_frame,
                width=12,
            )

            strike_entry.grid(column=13, row=row_loc, padx=5, pady=5)

            expiry_date_entry = ttk.Entry(
                input_frame,
                width=12,
            )
            expiry_date_entry.grid(column=14, row=row_loc, padx=5, pady=5)

        # Inserting the value in GUI fields for Edit combo
        def set_legs_values_for_edit_combo(combo_obj):

            # Buy legs and Sell legs
            buy_legs = combo_obj.buy_legs
            sell_legs = combo_obj.sell_legs
            all_legs = buy_legs + sell_legs

            if num_rows < len(all_legs):

                all_legs = all_legs[0:num_rows]

            # Iterate GUI compoenets for legs
            for leg_indx, leg_obj in enumerate(all_legs):

                # Getting all the leg related fields to insert them in GUI
                action = leg_obj.action
                sectype = leg_obj.sec_type
                symbol = leg_obj.symbol
                dte = (
                    leg_obj.dte
                    if leg_obj.dte
                    not in [
                        None,
                        "None",
                    ]
                    else ""
                )
                delta = (
                    abs(float(leg_obj.delta))
                    if leg_obj.delta
                    not in [
                        None,
                        "None",
                    ]
                    else ""
                )
                right = (
                    leg_obj.right
                    if leg_obj.right
                    not in [
                        None,
                        "None",
                    ]
                    else ""
                )
                quantity = leg_obj.quantity
                multiplier = leg_obj.multiplier
                exchange = leg_obj.exchange
                trading_class = (
                    leg_obj.trading_class
                    if leg_obj.trading_class
                    not in [
                        None,
                        "None",
                    ]
                    else ""
                )
                currency = leg_obj.currency
                conid = leg_obj.con_id
                primary_exchange = (
                    leg_obj.primary_exchange
                    if leg_obj.primary_exchange
                    not in [
                        None,
                        "None",
                    ]
                    else ""
                )
                strike = (
                    leg_obj.strike_price
                    if leg_obj.strike_price
                    not in [
                        None,
                        "None",
                    ]
                    else ""
                )
                expiry = (
                    leg_obj.expiry_date
                    if leg_obj.expiry_date
                    not in [
                        None,
                        "None",
                    ]
                    else ""
                )

                # Make "right" field value either "CALL" or "PUT"
                if right == "C":
                    right = "CALL"
                elif right == "P":
                    right = "PUT"
                else:
                    pass

                # Row Location for the GUI rows (starts from 1)
                row_loc = leg_indx + 1

                # Dict Name for combobox
                action_combo_box = f"action_combo_box_{row_loc}"
                sec_type_combo_box = f"sec_type_combo_box_{row_loc}"
                right_combo_box = f"right_combo_box_{row_loc}"

                # Set the values of the input fields
                drop_down_items_dict[row_loc][action_combo_box].set(action)
                drop_down_items_dict[row_loc][sec_type_combo_box].set(sectype)
                input_frame.grid_slaves(row=row_loc, column=2)[0].insert(0, symbol)
                input_frame.grid_slaves(row=row_loc, column=3)[0].insert(0, quantity)
                input_frame.grid_slaves(row=row_loc, column=4)[0].insert(0, dte)
                input_frame.grid_slaves(row=row_loc, column=5)[0].insert(0, delta)
                drop_down_items_dict[row_loc][right_combo_box].set(right)
                input_frame.grid_slaves(row=row_loc, column=7)[0].insert(0, multiplier)
                input_frame.grid_slaves(row=row_loc, column=8)[0].insert(0, exchange)
                input_frame.grid_slaves(row=row_loc, column=9)[0].insert(
                    0, trading_class
                )
                input_frame.grid_slaves(row=row_loc, column=10)[0].insert(0, currency)
                input_frame.grid_slaves(row=row_loc, column=11)[0].insert(0, conid)
                input_frame.grid_slaves(row=row_loc, column=12)[0].insert(
                    0, primary_exchange
                )
                input_frame.grid_slaves(row=row_loc, column=13)[0].insert(0, strike)
                input_frame.grid_slaves(row=row_loc, column=14)[0].insert(0, expiry)

        if modify_seq_data != None:

            combo_obj_modify = modify_seq_data["Combo Obj"]

            if combo_obj == None:

                set_legs_values_for_edit_combo(combo_obj_modify)

        # if Editing combo insert the value in GUI
        if flag_edit_combo:
            # Writing the value for each leg in popup
            set_legs_values_for_edit_combo(combo_obj)

        # If flag to prefill values of legs for conditional add or switch
        if flag_add_legs_conditional_add_switch:

            # Writing the value for each leg in popup
            set_legs_values_for_edit_combo(combo_obj)

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

                        # Check if result
                        if trading_classes != []:

                            # Get the grid slave of the input frame for FOP trading class textbox
                            slave = input_frame.grid_slaves(row=row_indx, column=9)[0]

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
                            ].grid(row=row_indx, column=9)

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

                    action_combo_box = f"action_combo_box_{row_loc}"
                    sec_type_combo_box = f"sec_type_combo_box_{row_loc}"
                    right_combo_box = f"right_combo_box_{row_loc}"

                    sec_type = (
                        drop_down_items_dict[row_loc][sec_type_combo_box].get().strip()
                    )

                    symbol = input_frame.grid_slaves(row=row_loc, column=2)[0].get()

                    exchange = (
                        input_frame.grid_slaves(row=row_loc, column=8)[0].get().strip()
                    )

                    action = drop_down_items_dict[row_loc][action_combo_box].get()
                    sec_type = (
                        drop_down_items_dict[row_loc][sec_type_combo_box].get().strip()
                    )

                    quantity = input_frame.grid_slaves(row=row_loc, column=3)[0].get()
                    dte = input_frame.grid_slaves(row=row_loc, column=4)[0].get()
                    delta = input_frame.grid_slaves(row=row_loc, column=5)[0].get()
                    right = drop_down_items_dict[row_loc][right_combo_box].get()
                    lot_size = input_frame.grid_slaves(row=row_loc, column=7)[0].get()
                    trading_class = input_frame.grid_slaves(row=row_loc, column=9)[
                        0
                    ].get()
                    currency = (
                        input_frame.grid_slaves(row=row_loc, column=10)[0].get().strip()
                    )
                    con_id = input_frame.grid_slaves(row=row_loc, column=11)[0].get()
                    primary_exchange = input_frame.grid_slaves(row=row_loc, column=12)[
                        0
                    ].get()
                    strike = input_frame.grid_slaves(row=row_loc, column=13)[0].get()
                    expiry_date = input_frame.grid_slaves(row=row_loc, column=14)[
                        0
                    ].get()

                    row_of_values_for_leg = [
                        action,
                        sec_type,
                        symbol,
                        dte,
                        delta,
                        right,
                        quantity,
                        lot_size,
                        exchange,
                        trading_class,
                        currency,
                        con_id,
                        primary_exchange,
                        strike,
                        expiry_date,
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
            unique_id=unique_id,
            refer_price=refer_price,
            refer_position=refer_position,
        ):
            add_combo_button.config(state="disabled")
            add_combo_thread = threading.Thread(
                target=add_combo, args=(popup, add_combo_button)
            )
            add_combo_thread.start()

        def add_combo(
            popup,
            add_combo_button,
            unique_id=unique_id,
            refer_price=refer_price,
            refer_position=refer_position,
        ):

            # KARAN CAS combo_tab_or_cas_tab
            if not combo_tab_or_cas_tab in ["ADD", "SWITCH"]:

                # Getting the unique_id
                unique_id = variables.unique_id

                # Increase the unique_id got successful combination,
                variables.unique_id += 1

            combo_values = []
            for i in range(num_rows):
                row_loc = i + 1

                action_combo_box = f"action_combo_box_{row_loc}"
                sec_type_combo_box = f"sec_type_combo_box_{row_loc}"
                right_combo_box = f"right_combo_box_{row_loc}"

                action = drop_down_items_dict[row_loc][action_combo_box].get()
                sec_type = (
                    drop_down_items_dict[row_loc][sec_type_combo_box].get().strip()
                )
                symbol = input_frame.grid_slaves(row=row_loc, column=2)[0].get()
                quantity = input_frame.grid_slaves(row=row_loc, column=3)[0].get()
                dte = input_frame.grid_slaves(row=row_loc, column=4)[0].get()
                delta = input_frame.grid_slaves(row=row_loc, column=5)[0].get()
                right = drop_down_items_dict[row_loc][right_combo_box].get()
                lot_size = input_frame.grid_slaves(row=row_loc, column=7)[0].get()
                exchange = (
                    input_frame.grid_slaves(row=row_loc, column=8)[0].get().strip()
                )
                trading_class = input_frame.grid_slaves(row=row_loc, column=9)[0].get()

                currency = (
                    input_frame.grid_slaves(row=row_loc, column=10)[0].get().strip()
                )
                con_id = input_frame.grid_slaves(row=row_loc, column=11)[0].get()
                primary_exchange = input_frame.grid_slaves(row=row_loc, column=12)[
                    0
                ].get()
                strike = input_frame.grid_slaves(row=row_loc, column=13)[0].get()
                expiry_date = input_frame.grid_slaves(row=row_loc, column=14)[0].get()

                combo_values.append(
                    (
                        unique_id,
                        action,
                        sec_type,
                        symbol,
                        dte,
                        delta,
                        right,
                        quantity,
                        lot_size,
                        exchange,
                        trading_class,
                        currency,
                        con_id,
                        primary_exchange,
                        strike,
                        expiry_date,
                    )
                )

            # Is CAS
            input_from_cas_tab = (
                True if combo_tab_or_cas_tab in ["ADD", "SWITCH"] else False
            )

            (
                show_error_popup,
                error_title,
                error_string,
                combination_obj,
            ) = create_combination(
                combo_values,
                input_from_cas_tab=input_from_cas_tab,
            )

            # Enabling the Button again
            add_combo_button.config(state="normal")

            # If We are editing the combo return these things
            if flag_edit_combo:

                # Call edit combo
                self.edit_combination(
                    popup,
                    show_error_popup,
                    error_title,
                    error_string,
                    combination_obj,
                    old_combo_unique_id,
                    unique_id,
                )

                return

            # error Occurs show that to user
            if show_error_popup == True:

                self.display_error_popup(error_title, error_string)

            else:

                # Close the popup
                popup.destroy()

                # if cas conditional leg
                if combo_tab_or_cas_tab in ["ADD", "SWITCH"]:

                    # process the cas legs
                    variables.screen.screen_cas_obj.display_enter_condition_popup(
                        unique_id,
                        combo_tab_or_cas_tab,
                        combination_obj,
                        refer_price,
                        refer_position,
                        target_position=target_positions_dict,
                        bypass_rm_check=bypass_rm_account_check,
                        evalaution_unique_id=evalaution_unique_id,
                        flag_conditional_series=flag_conditional_series,
                        modify_seq_data=modify_seq_data,
                        index=index,
                    )

                else:
                    # Subscribe the MktData and Inser Combination in the db
                    subscribe_mktdata_combo_obj(combination_obj)
                    insert_combination_db(True, combination_obj)

                    # Create a thread and pass the result_queue as an argument
                    single_combo_values_thread = threading.Thread(
                        target=single_combo_values,
                        args=(
                            combination_obj,
                            unique_id,
                        ),
                    )

                    # Start the thread
                    single_combo_values_thread.start()

                    # reset counter
                    variables.counter_trade_rm_checks = 10**10

                    # Set counter to big number so the cas values can be updated
                    """variables.flag_update_long_term_value = True
                    variables.flag_update_intra_day_value = True
                    variables.flag_update_hv_related_value = True
                    variables.flag_update_volume_related_value = True
                    variables.flag_update_support_resistance_and_relative_fields = True
                    variables.flag_update_atr_for_order = True"""

        # Create a frame for the "Add Combo" button
        button_frame = ttk.Frame(popup)
        button_frame.place(
            relx=0.5, anchor=tk.CENTER
        )  # x=530, y=custom_height-50,width=100, height=30,  )
        button_frame.place(y=custom_height - 50)

        # Text we want to show for the button
        edit_add_combo_button_text = "Edit Combo" if flag_edit_combo else "Add Combo"

        # Create the "Add Combo" button
        add_combo_button = ttk.Button(
            button_frame,
            text=edit_add_combo_button_text,
            command=lambda: on_add_combo_button_click(
                add_combo_button,
                popup,
                unique_id=unique_id,
                refer_price=refer_price,
                refer_position=refer_position,
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

    # Display table/treeview - combo details combination details
    def display_treeview_popup(self, title, columns_name_list, rows_data_list):

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

        # Create a popup window with the table
        treeview_popup = tk.Toplevel()
        treeview_popup.title(title)
        custom_height = min(max((num_rows * 20) + 100, 150), 210)

        custom_width = (
            80 * len(rows_data_list[0]) + 60
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

    # Method to display combination details
    def display_combination_details(self, table_type):

        if table_type == "market_watch":
            selected_item = self.market_watch_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.market_watch_table.item(
                selected_item, "values"
            )  # get the values of the selected row
        elif table_type == "combo_creator":
            selected_item = self.combination_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.combination_table.item(
                selected_item, "values"
            )  # get the values of the selected row
        elif table_type == "order_book":
            selected_item = self.order_book_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.order_book_table.item(
                selected_item, "values"
            )  # get the values of the selected row
        elif table_type == "positions":
            selected_item = self.screen_position_obj.positions_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.screen_position_obj.positions_table.item(
                selected_item, "values"
            )  # get the values of the selected row
        elif table_type == "cas":
            selected_item = self.screen_cas_obj.cas_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.screen_cas_obj.cas_table.item(
                selected_item, "values"
            )  # get the values of the selected row
        elif table_type == "cas_condition":
            selected_item = self.screen_cas_obj.cas_condition_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.screen_cas_obj.cas_condition_table.item(
                selected_item, "values"
            )  # get the values of the selected row

        unique_id = int(values[0])

        # Title and (cas_condition or not)
        if table_type == "cas_condition":
            title = f"Incremental Legs, Unique ID : {unique_id}"
            cas_condition = True
        else:
            title = f"Combination Details, Unique ID : {unique_id}"
            cas_condition = False

        (
            columns,
            row_data_list,
        ) = get_combination_details_list_for_combination_tab_gui(
            unique_id, cas_condition
        )

        if (columns == None) and (row_data_list == None):
            return

        # DISPLAY DETAILS of combo
        self.display_treeview_popup(title, columns, row_data_list)

    # Method to edit combination
    def display_edit_combination_popup(self):

        try:

            selected_item = self.combination_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.combination_table.item(
                selected_item, "values"
            )  # get the values of the selected row

            unique_id = int(values[0])

            # Print to console
            if variables.flag_debug_mode:
                print(f"Got Unique ID :{unique_id} to Edit Combination")

            # Get combination
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )

            # Combination Obj
            combination_obj = local_unique_id_to_combo_obj[unique_id]

            # Buy legs and Sell legs
            buy_legs = combination_obj.buy_legs
            sell_legs = combination_obj.sell_legs
            all_legs = buy_legs + sell_legs

            # Print to console
            if variables.flag_debug_mode:
                print(f"Edit Combination, Got Combination Object: {combination_obj}")

        except Exception as e:
            print("Exception Found display_edit_combination_popup", e)

            error_title = "Error, Could not get combination values"
            error_string = "Error happened while getting combination values"

            self.display_error_popup(error_title, error_string)
            return

        # Init
        num_rows = len(all_legs)
        flag_edit_combo = True

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Edit Combination, Creating Edit Combination pop up for Unique ID : {unique_id}"
            )

        # Display the Edit combo popup
        self.create_combination_popup(
            rows_entry=None,
            combo_tab_or_cas_tab="Combo",
            title_string="Edit Combo",
            cas_row_input_popup=None,
            unique_id=unique_id,
            refer_price=None,
            refer_position=None,
            num_rows=num_rows,
            combo_obj=combination_obj,
            flag_edit_combo=flag_edit_combo,
        )

    # Method to edit combination
    def edit_combination(
        self,
        popup,
        show_error_popup,
        error_title,
        error_string,
        combination_obj,
        old_combo_unique_id,
        new_unique_id,
    ):

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Edit Combination: Old Unique ID: {old_combo_unique_id}, New Combo : {combination_obj}"
            )

        # Error Occurs show that to user
        if show_error_popup == True:
            self.display_error_popup(error_title, error_string)
            return

        # Close the popup
        popup.destroy()

        try:
            # Getting dictionary of mapped unique id to position
            local_map_unique_id_to_positions = copy.deepcopy(
                variables.map_unique_id_to_positions
            )

            # Get position for unique id
            current_position = local_map_unique_id_to_positions[old_combo_unique_id]
        except Exception as e:
            print(
                f"Unique ID not found in Edit combination Exception: {e}",
            )

            error_title = "Error, Unique ID not found "
            error_string = "Error, Unique ID not found in Edit combination"

            self.display_error_popup(error_title, error_string)
            return

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Edit Combination: New Combo : {combination_obj} Subscribe the MktData and Insert Combo in DB"
            )

        # Subscribe the MktData and Insert Combination in the db
        subscribe_mktdata_combo_obj(combination_obj)
        insert_combination_db(True, combination_obj)

        # Create a thread and pass the result_queue as an argument
        single_combo_values_thread = threading.Thread(
            target=single_combo_values,
            args=(
                combination_obj,
                new_unique_id,
            ),
        )

        # Start the thread
        single_combo_values_thread.start()

        # reset counter
        variables.counter_trade_rm_checks = 10**10

        # Set counter to big number so the cas values can be updated
        """variables.flag_update_long_term_value = True
        variables.flag_update_intra_day_value = True
        variables.flag_update_hv_related_value = True
        variables.flag_update_volume_related_value = True
        variables.flag_update_support_resistance_and_relative_fields = True
        variables.flag_update_atr_for_order = True"""

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Edit Combination: New Combo UID : {combination_obj.unique_id} Getting all the pending order "
            )

        # Get All pending order
        all_pending_order = get_pending_orders()

        # Record module start time
        last_update_time = datetime.datetime.now(variables.target_timezone_obj)

        # Mark the orders cancelled
        for _, pending_order_row in all_pending_order.iterrows():

            # Init value
            r_unique_id = int(pending_order_row["Unique ID"])
            order_time = pending_order_row["Order Time"]
            status = pending_order_row["Status"]

            # Cancel order if unique Id matches
            if r_unique_id == old_combo_unique_id:

                # Update the Status in Order Book
                self.update_combo_order_status_in_order_book(
                    order_time,
                    last_update_time,
                    entry_price="None",
                    reference_price="None",
                    status="Cancelled",
                    flag_only_update_status=True,
                )

                mark_pending_combo_order_cancelled(
                    old_combo_unique_id, order_time, status, last_update_time
                )

        try:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Edit Combination: New Combo UID : {combination_obj.unique_id}, Old Unique ID: {old_combo_unique_id} Current Position: {current_position} Sending Exit order"
                )

            for account_id in variables.current_session_accounts:

                # Get position for unique id
                current_position = local_map_unique_id_to_positions[
                    old_combo_unique_id
                ][account_id]

                # Check if current position is not zero for exiting position

                if current_position != 0:

                    # Action for the order
                    if current_position > 0:
                        buy_sell_action = "SELL"
                    else:
                        buy_sell_action = "BUY"

                    # Init values
                    action = buy_sell_action
                    combo_quantity = abs(current_position)
                    order_type = variables.edit_combo_exit_position_order_type
                    limit_price = ""
                    trigger_price = ""
                    trail_value = ""
                    bypass_rm_check = "True"
                    flag_execution_engine = False

                    # Send order in a separate thread
                    send_order_thread = threading.Thread(
                        target=send_order,
                        args=(
                            old_combo_unique_id,
                            action,
                            order_type,
                            combo_quantity,
                            limit_price,
                            trigger_price,
                            trail_value,
                        ),
                        kwargs={
                            "account_id": account_id,
                            "bypass_rm_check": bypass_rm_check,
                            "execution_engine": flag_execution_engine,
                        },
                    )
                    send_order_thread.start()

                    # Joining the thread(wait till thread ends)
                    time.sleep(3)  # send_order_thread.join()

            # Delete the old combination
            self.delete_row(old_combo_unique_id)

        except Exception as e:
            # Print to console
            print("Error in Edit combination, while sending error", e)

            error_title = "Error, Exit position had error"
            error_string = "Error, Exit position for edit combo was not successful"

            self.display_error_popup(error_title, error_string)
            return

    # Update GUI tables after combo deleted
    def update_tables_after_combo_deleted(self):

        list_of_tables = [
            self.combination_table,
            self.market_watch_table,
            self.order_book_table,
            self.screen_position_obj.positions_table,
            self.screen_cas_obj.cas_table,
            self.screen_cas_obj.cas_condition_table,
        ]

        for table in list_of_tables:

            count = 0
            for row in table.get_children():
                if count % 2 == 0:
                    table.item(row, tags="evenrow")
                else:
                    table.item(row, tags="oddrow")

                count += 1

    # Update the combo details table according to selected watchlist
    def update_combo_details_table(
        self,
    ):

        # Get combo details dataframe
        local_combo_details_df = copy.deepcopy(variables.combo_table_df)

        # All the Unique IDs in the System
        all_unique_ids_in_system = local_combo_details_df["Unique ID"].tolist()

        # All the rows in combo Table
        all_unique_id_in_combo_table = [
            int(_x) for _x in self.combination_table.get_children()
        ]

        # If we want to update the table as watchlist changed
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
                print(f"Error inside updating combo table, {e}")

        # Update the rows
        for i, row_val in local_combo_details_df.iterrows():

            # Unique ID of row val
            unique_id = row_val["Unique ID"]

            if unique_id in all_unique_ids_in_watchlist:

                # Tuple of vals
                row_val = tuple(row_val)

                if unique_id in all_unique_id_in_combo_table:
                    # Update the row at once.
                    self.combination_table.item(unique_id, values=row_val)

                else:
                    # Insert it in the table
                    self.combination_table.insert(
                        "",
                        "end",
                        iid=unique_id,
                        text="",
                        values=row_val,
                        tags=("oddrow",),
                    )
            else:
                # If this unique_id in CAS Table but not in watchlist delete it
                if unique_id in all_unique_id_in_combo_table:
                    try:
                        self.combination_table.delete(unique_id)
                    except Exception as e:
                        if variables.flag_debug_mode:
                            print(f"Error in updating combo table, is {e}")

        try:
            # Filter out the dataframe such that the dataframe only consists of all the unique ids that are present in the watchlist, so sorting will be in correct order.
            local_combo_details_df = local_combo_details_df[
                local_combo_details_df["Unique ID"].isin(all_unique_ids_in_watchlist)
            ]
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Error inside updating combo table values, is {e}")

        # All the rows in combo Table
        all_unique_id_in_combo_table = self.combination_table.get_children()

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in local_combo_details_df.iterrows():

            # Unique_id
            unique_id = str(row["Unique ID"])

            # If unique_id in table
            if unique_id in all_unique_id_in_combo_table:
                self.combination_table.move(unique_id, "", counter_row)

                if counter_row % 2 == 0:
                    self.combination_table.item(unique_id, tags="evenrow")
                else:
                    self.combination_table.item(unique_id, tags="oddrow")

                # Increase row count
                counter_row += 1

    # Method to inserrt rows in combo table
    def add_high_level_combo_details_to_combo_creator_tab(self, values):
        # Get the current number of items in the treeview
        num_items = len(self.combination_table.get_children())

        # Add the values to the treeview
        for i, value in enumerate(values):

            unique_id = value[0]
            if (num_items + i + 1) % 2 == 0:
                self.combination_table.insert(
                    "",
                    "end",
                    iid=unique_id,
                    text=num_items + i + 1,
                    values=value,
                    tags=("oddrow",),
                )
            else:
                self.combination_table.insert(
                    "",
                    "end",
                    iid=unique_id,
                    text=num_items + i + 1,
                    values=value,
                    tags=("evenrow",),
                )

    # Method to create market watch table
    def create_market_watch_tab(self):

        # Add widgets to the Market Watch tab here

        # Create Treeview Frame for active combo table
        market_watch_table_frame = ttk.Frame(self.market_watch_tab, padding=20)
        market_watch_table_frame.pack(pady=20)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(market_watch_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.market_watch_table = ttk.Treeview(
            market_watch_table_frame,
            yscrollcommand=tree_scroll.set,
            height=29,
            selectmode="extended",
        )

        # Pack to the screen
        self.market_watch_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.market_watch_table.yview)

        # Place in center
        market_watch_table_frame.place(relx=0.5, anchor=tk.CENTER)
        market_watch_table_frame.place(y=390)

        # Define Our Columns
        self.market_watch_table["columns"] = variables.market_watch_table_columns

        # Formate Our Columns
        self.market_watch_table.column("#0", width=0, stretch="no")
        self.market_watch_table.column("Unique ID", anchor="center", width=210)
        self.market_watch_table.column("#Legs", anchor="center", width=210)
        self.market_watch_table.column("Tickers", anchor="center", width=490)
        self.market_watch_table.column("Sell Price", anchor="center", width=210)
        self.market_watch_table.column("Buy Price", anchor="center", width=210)
        self.market_watch_table.column("Bid - Ask Spread", anchor="center", width=210)

        # Create Headings
        self.market_watch_table.heading("#0", text="", anchor="w")
        self.market_watch_table.heading("Unique ID", text="Unique ID", anchor="center")
        self.market_watch_table.heading("#Legs", text="#Legs", anchor="center")
        self.market_watch_table.heading("Tickers", text="Tickers", anchor="center")
        self.market_watch_table.heading(
            "Sell Price",
            text="Sell Price",
            anchor="center",
        )
        self.market_watch_table.heading("Buy Price", text="Buy Price", anchor="center")
        self.market_watch_table.heading(
            "Bid - Ask Spread",
            text="Bid - Ask Spread",
            anchor="center",
        )

        # Create striped row tags
        self.market_watch_table.tag_configure("oddrow", background="white")
        self.market_watch_table.tag_configure("evenrow", background="lightblue")

        # Method to add ranage schedule order
        def add_range_schedule(flag_multi=False):

            # Unique ID the active combo
            selected_item = self.market_watch_table.selection()[
                0
            ]  # get the item ID of the selected row

            values = self.market_watch_table.item(
                selected_item, "values"
            )  # get the values of the selected row

            # Get unique id for selecte row
            unique_id = int(values[0])

            # Start the web socket in a thread
            thread = threading.Thread(target=variables.screen.screen_scale_trader_obj.get_percentage_qnty_pair,
                                      args=(unique_id,),kwargs={'flag_multi':flag_multi},
                                       daemon=True)
            thread.start()

        # Method to add range order
        def add_range_order(flag_multi=False,):

            # Unique ID the active combo
            selected_item = self.market_watch_table.selection()[
                0
            ]  # get the item ID of the selected row

            values = self.market_watch_table.item(
                selected_item, "values"
            )  # get the values of the selected row

            # Get unique id for selecte row
            unique_id = int(values[0])

            # Start the web socket in a thread
            thread = threading.Thread(target=variables.screen.screen_scale_trader_obj.get_range_order_prior_input,
                                      args=(unique_id,),
                                      kwargs={'flag_multi': flag_multi,}, daemon=True)
            thread.start()

        # Method to add scale trade
        def add_scale_trade(flag_multi=False, flag_range=False):

            # Unique ID the active combo
            selected_item = self.market_watch_table.selection()[
                0
            ]  # get the item ID of the selected row

            values = self.market_watch_table.item(
                selected_item, "values"
            )  # get the values of the selected row

            # Get unique id for selecte row
            unique_id = int(values[0])


            # Start the web socket in a thread
            thread = threading.Thread(target=variables.screen.screen_scale_trader_obj.add_scale_trade_instance_pop_up,args=(unique_id,) ,
                                      kwargs={'flag_multi':flag_multi,'flag_range': flag_range}, daemon=True)
            thread.start()

            # Call method to add scale trade instance
            '''variables.screen.screen_scale_trader_obj.add_scale_trade_instance_pop_up(
                unique_id, flag_multi=flag_multi, flag_range=flag_range
            )'''

        # Method to buy combination by placing order
        def buy_combo(flag_multi_account=False):

            # Unique ID the active combo
            selected_item = self.market_watch_table.selection()[
                0
            ]  # get the item ID of the selected row

            values = self.market_watch_table.item(
                selected_item, "values"
            )  # get the values of the selected row

            unique_id = int(values[0])
            buy_sell_action = "BUY"

            # Define title for create trade pop up
            create_trade_popup = f"{buy_sell_action.capitalize()} Combination, Combination Unique ID : {unique_id}"

            # If flag is true
            if flag_multi_account:

                # Define title for create trade pop up
                create_trade_popup = f"{buy_sell_action.capitalize()} Combination For Multiple Accounts, Combination Unique ID : {unique_id}"

            self.create_trade_popup(
                buy_sell_action,
                unique_id,
                popup_title=create_trade_popup,
                flag_multi_account=flag_multi_account,
            )


        # Method to place sell combo order
        def sell_combo(flag_multi_account=False):

            # Unique ID the active combo
            selected_item = self.market_watch_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.market_watch_table.item(
                selected_item, "values"
            )  # get the values of the selected row
            unique_id = int(values[0])

            buy_sell_action = "SELL"

            # Define title for create trade pop up
            create_trade_popup = f"{buy_sell_action.capitalize()} Combination, Combination Unique ID : {unique_id}"

            # If flag is true
            if flag_multi_account:

                # Define title for create trade pop up
                create_trade_popup = f"{buy_sell_action.capitalize()} Combination For Multiple Accounts, Combination Unique ID : {unique_id}"

            self.create_trade_popup(
                buy_sell_action,
                unique_id,
                popup_title=create_trade_popup,
                flag_multi_account=flag_multi_account,
            )

        # Method create price chart
        def create_price_chart_screen():

            # Unique ID the active combo
            selected_item = self.market_watch_table.selection()[
                0
            ]  # get the item ID of the selected row
            values = self.market_watch_table.item(
                selected_item, "values"
            )  # get the values of the selected row
            unique_id = int(values[0])

            # Create Price Chart Object
            PriceChart(unique_id)

        # Method to define price table right click options
        def price_table_right_click(event):
            # get the Treeview row that was clicked
            row = self.market_watch_table.identify_row(event.y)

            if row:
                # select the row
                self.market_watch_table.selection_set(row)

                # create a context menu
                menu = tk.Menu(self.market_watch_table, tearoff=0)

                # Create submenus
                submenu1 = tk.Menu(menu, tearoff=0)
                submenu2 = tk.Menu(menu, tearoff=0)
                submenu3 = tk.Menu(menu, tearoff=0)
                submenu4 = tk.Menu(menu, tearoff=0)
                submenu5 = tk.Menu(menu, tearoff=0)
                submenu6 = tk.Menu(menu, tearoff=0)


                submenu1.add_command(label="Buy Combo", command=buy_combo)
                submenu1.add_command(label="Sell Combo", command=sell_combo)

                submenu1.add_command(
                    label="Buy Combo Multi",
                    command=lambda: buy_combo(flag_multi_account=True),
                )
                submenu1.add_command(
                    label="Sell Combo Multi",
                    command=lambda: sell_combo(flag_multi_account=True),
                )

                submenu2.add_command(label="Add Scale Trade", command=add_scale_trade)
                submenu2.add_command(
                    label="Add Scale Trade Multi",
                    command=lambda: add_scale_trade(flag_multi=True),
                )
                submenu2.add_command(
                    label="Range Orders",
                    command=lambda: add_range_order(),
                )
                submenu2.add_command(
                    label="Range Orders Multi",
                    command=lambda: add_range_order(flag_multi=True),
                )
                submenu2.add_command(
                    label="Range Schedule Orders",
                    command=lambda: add_range_schedule(),
                )
                submenu2.add_command(
                    label="Range Schedule Orders Multi",
                    command=lambda: add_range_schedule(flag_multi=True),
                )
                submenu5.add_command(
                    label="Volatility Order",
                    command=lambda: self.add_volatility_orders(),
                )

                submenu5.add_command(
                    label="Volatility Order Multi",
                    command=lambda: self.add_volatility_orders(flag_multi=True),
                )



                # Add submenus to the main menu
                menu.add_cascade(label="Buy / Sell Combo", menu=submenu1)
                menu.add_cascade(label="Scale Trade", menu=submenu2)

                menu.add_cascade(label="Volatility Order", menu=submenu5)


                menu.add_command(label="Price Chart", command=create_price_chart_screen)
                menu.add_command(
                    label="View Details",
                    command=lambda: self.display_combination_details("market_watch"),
                )
                menu.add_command(
                    label="Edit Position",
                    command=lambda: self.edit_position(),
                )

                # display the context menu at the location of the mouse cursor
                menu.post(event.x_root, event.y_root)

        self.market_watch_table.bind("<Button-3>", price_table_right_click)

    # Method to add volatility order
    def add_volatility_orders(self, flag_multi=False):

        # Unique ID the active combo
        selected_item = self.market_watch_table.selection()[
            0
        ]  # get the item ID of the selected row

        values = self.market_watch_table.item(
            selected_item, "values"
        )  # get the values of the selected row

        # Get unique id for selecte row
        unique_id = int(values[0])

        # local copy of 'unique_id_to_combo_obj'
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

        # get combo object
        combo_obj = local_unique_id_to_combo_obj[unique_id]

        # get all legs
        all_legs = combo_obj.buy_legs + combo_obj.sell_legs

        # init
        req_id_list = []

        # iterate legs
        for leg_obj in all_legs:

            # append req ids list
            req_id_list.append(variables.con_id_to_req_id_dict[leg_obj.con_id])

            # check if any leg is stk or fut and if yes then show error pop up
            if leg_obj.sec_type in ['STK','FUT']:
                # Error Message
                error_title = error_string = f"Error - Not allowed for STK and FUT"
                variables.screen.display_error_popup(error_title, error_string)

                return

        # init
        buy_iv = 0

        sell_iv = 0

        try:

            # iterate request ids and legs
            for req_id, leg_obj in zip(req_id_list, all_legs):


                print([leg_obj.strike_price, variables.options_iv_bid[req_id], variables.options_iv_ask[req_id]])

                # calculate buy implied volatilitty and sell implied volatility
                buy_iv += (variables.options_iv_bid[req_id] if leg_obj.action.upper() == 'BUY' else variables.options_iv_ask[req_id]) * leg_obj.quantity * leg_obj.multiplier * (1 if leg_obj.action.upper() == 'BUY' else -1)

                sell_iv += (variables.options_iv_bid[req_id] if leg_obj.action.upper() == 'SELL' else variables.options_iv_ask[req_id]) * leg_obj.quantity * leg_obj.multiplier * (1 if leg_obj.action.upper() == 'BUY' else -1)

            buy_iv *= 100

            sell_iv *= 100

        except Exception as e:

            if variables.flag_debug_mode:

                print(f"Exception for getting implied volatility, Exp: {e}")

            # Error pop up
            error_title = f"Could not get implied volatility"
            error_string = f"Could not get implied volatility"

            self.display_error_popup(
                error_title, error_string
            )

            return



        # display pop up for volatility order

        self.display_volatility_order_pop_up(unique_id, buy_iv, sell_iv, flag_multi=flag_multi)

    # Method to display volatility order
    def display_volatility_order_pop_up(self, unique_id, buy_iv, sell_iv, flag_multi=False):

        # Create popup window
        volatility_order_popup = tk.Toplevel()

        # set title
        volatility_order_popup.title(
            f"Volatility Order, Unique ID: {unique_id}"
        )

        # init
        custom_height = 150

        # set dimensions
        volatility_order_popup.geometry("1030x" + str(custom_height))

        # check flag for multi account
        if flag_multi:

            custom_height = 270

            # set dimensions
            volatility_order_popup.geometry("1060x" + str(custom_height))

        # Create main frame
        volatility_order_popup_frame = ttk.Frame(
            volatility_order_popup, padding=20
        )
        volatility_order_popup_frame.pack(fill="both", expand=True)

        # Add labels and entry fields for each column in the table
        ttk.Label(
            volatility_order_popup_frame,
            text="Action",
            width=16,
            anchor="center",
        ).grid(column=0, row=0, padx=5, pady=5)

        # Add labels for each column in the table
        ttk.Label(
            volatility_order_popup_frame,
            text="Order Type",
            width=16,
            anchor="center", justify='center'
        ).grid(column=1, row=0, padx=5, pady=5)

        if not flag_multi:

            # Add labels for each column in the table
            ttk.Label(
                volatility_order_popup_frame,
                text="Combo Quantity\n(#Lots)",
                width=16,
                anchor="center", justify='center'
            ).grid(column=2, row=0, padx=5, pady=5)

        else:

            # Add labels for each column in the table
            ttk.Label(
                volatility_order_popup_frame,
                text=f"Combo Quantity\n(x% * {variables.account_parameter_for_order_quantity}) / Price",
                width=16,
                anchor="center", justify='center'
            ).grid(column=2, row=0, padx=5, pady=5)

        # Add labels for each column in the table
        ttk.Label(
            volatility_order_popup_frame,
            text="Limit IV (%)",
            width=16,
            anchor="center",
        ).grid(column=3, row=0, padx=5, pady=5)

        # Add labels for each column in the table
        ttk.Label(
            volatility_order_popup_frame,
            text="Trigger IV (%)",
            width=16,
            anchor="center",
        ).grid(column=4, row=0, padx=5, pady=5)

        # Add labels for each column in the table
        ttk.Label(
            volatility_order_popup_frame,
            text="Current IV (%)",
            width=16,
            anchor="center",
        ).grid(column=5, row=0, padx=5, pady=5)

        # Add labels for each column in the table
        ttk.Label(
            volatility_order_popup_frame,
            text="Trading Account",
            width=16,
            anchor="center",
        ).grid(column=6, row=0, padx=5, pady=5)

        # Add labels for each column in the table
        ttk.Label(
            volatility_order_popup_frame,
            text="Bypass RM Check",
            width=16,
            anchor="center",
        ).grid(column=7, row=0, padx=5, pady=5)

        # Add labels for each column in the table
        ttk.Label(
            volatility_order_popup_frame,
            text="Execution Engine",
            width=16,
            anchor="center",
        ).grid(column=8, row=0, padx=5, pady=5)

        # Input textbox for column
        lots_entry = ttk.Entry(
            volatility_order_popup_frame,
            width=16,
        )
        lots_entry.grid(column=2, row=1, padx=5, pady=5)

        # Input textbox for column
        limit_iv_entry = ttk.Entry(
            volatility_order_popup_frame,
            width=16,
        )
        limit_iv_entry.grid(column=3, row=1, padx=5, pady=5)

        # Input textbox for column
        trigger_iv_entry = ttk.Entry(
            volatility_order_popup_frame,
            width=16,
        )
        trigger_iv_entry.grid(column=4, row=1, padx=5, pady=5)

        trigger_iv_entry.config(state='disabled')

        # Input textbox for column
        iv_entry = ttk.Entry(
            volatility_order_popup_frame,
            width=16,
        )
        iv_entry.grid(column=5, row=1, padx=5, pady=5)

        try:

            # initialize iv entry textbox
            iv_entry.insert(0, str(round(buy_iv,2)))
            iv_entry.config(state='readonly')

        except Exception as e:

            # print to console
            if variables.flag_debug_mode:

                print(f"Exception while initializing implied volatility text box, Exp: {e}")


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

        # on click method for add volatility order button
        def on_select_action(event):

            try:

                # get selected option
                selected_option = action_combo_box.get()

                # make it enabled
                iv_entry.config(state='normal')

                # delete previous content
                iv_entry.delete(0,tk.END)

                # check if action is 'BUY'
                if selected_option == 'BUY':

                    # insert value in iv entry textbox
                    iv_entry.insert(0, str(round(buy_iv,2)))

                else:

                    # insert value in iv entry textbox
                    iv_entry.insert(0, str(round(sell_iv,2)))

                # make iv entry field disabled
                iv_entry.config(state='readonly')

            except Exception as e:

                # print to console
                if variables.flag_debug_mode:
                    print(f"Exception while adjusting implied volatility text box, Exp: {e}")

        # method to invoke when select order type
        def on_select_order(event):

            # get selected option
            selected_option = order_combo_box.get()

            # if user selects limit volatility then adjust fields
            if selected_option == 'Limit Vol.':

                trigger_iv_entry.config(state='normal')

                trigger_iv_entry.delete(0, tk.END)

                trigger_iv_entry.config(state='disabled')

                limit_iv_entry.config(state='normal')

            # if user selects stop loss volatility then adjust fields
            else:

                limit_iv_entry.config(state='normal')

                limit_iv_entry.delete(0, tk.END)

                limit_iv_entry.config(state='disabled')

                trigger_iv_entry.config(state='normal')

        # add action drop down for buy sell action
        actions_list = ['BUY', 'SELL']

        action_combo_box = ttk.Combobox(
            volatility_order_popup_frame, width=14, values=actions_list, state="readonly", style="Custom.TCombobox",
        )
        action_combo_box.current(0)
        action_combo_box.grid(column=0, row=1, padx=5, pady=5)

        # on select method for dropdown
        action_combo_box.bind("<<ComboboxSelected>>", on_select_action)

        # add order type drop down for order type
        order_list = ['Limit Vol.', 'Stop Loss Vol.']

        order_combo_box = ttk.Combobox(
            volatility_order_popup_frame, width=14, values=order_list, state="readonly", style="Custom.TCombobox",
        )
        order_combo_box.current(0)
        order_combo_box.grid(column=1, row=1, padx=5, pady=5)

        # on select method for dropdown
        order_combo_box.bind("<<ComboboxSelected>>", on_select_order)

        # add bypass rm check drop down for bypass rm check value
        bypass_rm_check_list = ['True', 'False']

        rm_check_combo_box = ttk.Combobox(
            volatility_order_popup_frame, width=14, values=bypass_rm_check_list, state="readonly", style="Custom.TCombobox",
        )
        rm_check_combo_box.current(0)
        rm_check_combo_box.grid(column=7, row=1, padx=5, pady=5)

        # add execution engine drop down for execution engine
        execution_engine_list = [True, False]

        execution_engine_combo_box = ttk.Combobox(
            volatility_order_popup_frame, width=14, values=execution_engine_list, state="readonly", style="Custom.TCombobox",
        )
        execution_engine_combo_box.current(execution_engine_list.index(variables.flag_use_execution_engine))
        execution_engine_combo_box.grid(column=8, row=1, padx=5, pady=5)

        # check for flag for multi account
        if flag_multi:

            # Create a frame for the input fields
            trade_input_frame_acc = ttk.Frame(volatility_order_popup_frame, padding=0)
            trade_input_frame_acc.grid(column=6, row=1, padx=5, pady=15, rowspan=4)

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

            # insert account groups
            for indx, account_id in enumerate(
                    account_group_df["Group Name"].to_list(), start=1
            ):
                listbox.insert(listbox_index + indx, "Group: " + account_id)

            listbox.pack()

        else:

            # add account drop down for accounts
            accounts_list = variables.current_session_accounts

            accounts_combo_box = ttk.Combobox(
                volatility_order_popup_frame, width=14, values=accounts_list, state="readonly", style="Custom.TCombobox",
            )
            accounts_combo_box.current(0)
            accounts_combo_box.grid(column=6, row=1, padx=5, pady=5)

        def proceed():

            # get user input values in pop up
            map_account_to_quanity_dict = {}

            action = action_combo_box.get().strip()

            order_type = order_combo_box.get().strip()

            lots = lots_entry.get().strip()

            limit_iv = limit_iv_entry.get().strip()

            trigger_iv = trigger_iv_entry.get().strip()

            iv_value =iv_entry.get().strip()

            bypass_rm_check = rm_check_combo_box.get().strip()

            execution_engine = execution_engine_combo_box.get().strip()


            if bypass_rm_check == 'True':

                bypass_rm_check = True

            else:

                bypass_rm_check = False

            if execution_engine == 'True':

                execution_engine = True

            else:

                execution_engine = False


            # init
            account_val = None

            # check if lots value is numeric for single account
            if not flag_multi and not lots.isnumeric():
                # Error pop up
                error_title = f"Lots must be integer"
                error_string = f"Lots must be integer"

                self.display_error_popup(
                    error_title, error_string
                )

                return

            # check if lots value if decimal for multi accounts
            elif flag_multi and not is_float(lots):
                # Error pop up
                error_title = f"Lots percentage must be integer"
                error_string = f"Lots percentage must be integer"

                self.display_error_popup(
                    error_title, error_string
                )

                return

            # check limit iv is available for limit volatility order.
            elif not is_float(limit_iv) and order_type == 'Limit Vol.':

                # Error pop up
                error_title = f"Limit implied volatility percentage must be decimal"
                error_string = f"Limit implied volatility percentage must be decimal"

                self.display_error_popup(
                    error_title, error_string
                )

                return

            # check trigger iv is available for stop loss volatility order.
            elif not is_float(trigger_iv) and order_type == 'Stop Loss Vol.':

                # Error pop up
                error_title = f"Trigger implied volatility percentage must be decimal"
                error_string = f"Trigger implied volatility percentage must be decimal"

                self.display_error_popup(
                    error_title, error_string
                )

                return

            # check flag for multi account.
            if not flag_multi:

                # get account value
                account_val = accounts_combo_box.get().strip()

            else:

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
                account_val = sorted(list(set(account_id_list)))

                # check if account list is empty
                if account_val == []:
                    # Error pop up
                    error_title = f"Please select atleast one account"
                    error_string = f"Please select atleast one account"

                    self.display_error_popup(
                        error_title, error_string
                    )

                    return



                try:

                    # Getting initial trigger price
                    price = variables.unique_id_to_prices_dict[unique_id][
                        action
                    ]

                    # Iterating account ids
                    for account in account_id_list:

                        # Getting value of account parameter
                        if variables.account_parameter_for_order_quantity == "NLV":

                            value_of_account_parameter = (
                                variables.accounts_table_dataframe.loc[
                                    variables.accounts_table_dataframe["Account ID"]
                                    == account,
                                    variables.accounts_table_columns[1],
                                ].iloc[0]
                            )
                        # Getting value of account parameter
                        elif variables.account_parameter_for_order_quantity == "SMA":

                            value_of_account_parameter = (
                                variables.accounts_table_dataframe.loc[
                                    variables.accounts_table_dataframe["Account ID"]
                                    == account,
                                    variables.accounts_table_columns[2],
                                ].iloc[0]
                            )

                        # Getting value of account parameter
                        elif variables.account_parameter_for_order_quantity == "CEL":

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

                            self.display_error_popup(error_title, error_string)
                            return

                        # Calculate combo qunaity for account id
                        if float(price) != 0:

                            combo_quantity = float(lots)

                            combo_quantity_for_account = round(
                                (
                                        (combo_quantity / 100)
                                        * float(value_of_account_parameter)
                                )
                                / abs(float(price))
                            )

                        else:

                            combo_quantity_for_account = 0

                        if combo_quantity_for_account != 0:

                            # add it to dictionary
                            map_account_to_quanity_dict[
                                account
                            ] = combo_quantity_for_account



                except Exception as e:

                    # show error pop up
                    error_title = f"For Unique ID: {unique_id}, Could not get quantity for accounts"
                    error_string = f"For Unique ID: {unique_id}, Could not get quantity for accounts"

                    self.display_error_popup(error_title, error_string)
                    return

            if order_type == 'Limit Vol.':

                order_type = 'Limit Volatility'

                limit_price = 'None'
                trigger_price = 'None'
                trail_value = 'None'

                trigger_iv = 'None'

                if action.upper() == 'BUY':

                    limit_iv = float(limit_iv)

                else:

                    limit_iv = float(limit_iv)

                limit_iv = round(limit_iv, 2)

            else:

                order_type = 'Stop Loss Volatility'

                limit_price = 'None'
                trigger_price = 'None'
                trail_value = 'None'

                limit_iv = 'None'

                if action.upper() == 'BUY':

                    trigger_iv = float(trigger_iv)

                else:

                    trigger_iv = float(trigger_iv)

                trigger_iv = round(trigger_iv, 2)

            if not flag_multi:

                # Send order in a separate thread
                send_order_thread = threading.Thread(
                    target=send_order,
                    args=(
                        unique_id,
                        action,
                        order_type,
                        lots,
                        limit_price,
                        trigger_price,
                        trail_value,
                    ),
                    kwargs={
                        "account_id": account_val,
                        "bypass_rm_check": bypass_rm_check,
                        "execution_engine": execution_engine,
                        "limit_iv": limit_iv,
                        "trigger_iv": trigger_iv,
                    },
                )
                send_order_thread.start()

            else:

                for account in map_account_to_quanity_dict:
                    # Send order in a separate thread
                    send_order_thread = threading.Thread(
                        target=send_order,
                        args=(
                            unique_id,
                            action,
                            order_type,
                            map_account_to_quanity_dict[account],
                            limit_price,
                            trigger_price,
                            trail_value,
                        ),
                        kwargs={
                            "account_id": account,
                            "bypass_rm_check": bypass_rm_check,
                            "execution_engine": execution_engine,
                            "limit_iv": limit_iv,
                            "trigger_iv": trigger_iv,
                        },
                    )
                    send_order_thread.start()

                    time.sleep(0.5)

            volatility_order_popup.destroy()

        # Initialize button to add volatility order instances
        add_volatility_order_instances_button = ttk.Button(
            volatility_order_popup_frame,
            text="Add Volatility Order",
            command=lambda: proceed()
            )

        add_volatility_order_instances_button.grid(column=0, row=6, padx=5, pady=(15,5), columnspan=10)



    # method for edit position
    def edit_position(self):

        # Unique ID the active combo
        selected_item = self.market_watch_table.selection()[
            0
        ]  # get the item ID of the selected row

        values = self.market_watch_table.item(
            selected_item, "values"
        )  # get the values of the selected row

        # Get unique id for selecte row
        unique_id = int(values[0])

        variables.screen.screen_position_obj.edit_postion_pop_up(unique_id)

    # Method to insert prices in mrket watch
    def insert_prices_market_watch(self, value):

        unique_id = value[0]
        # my_tree.insert(parent='', index='end', iid=count, text="", values=(name_box.get(), id_box.get(), topping_box.get()), tags=('evenrow',))

        # Get the current number of items in the treeview
        num_items = len(self.market_watch_table.get_children())

        if num_items % 2 == 1:
            self.market_watch_table.insert(
                "",
                "end",
                iid=unique_id,
                text=num_items + 1,
                values=value,
                tags=("oddrow",),
            )
        else:
            self.market_watch_table.insert(
                "",
                "end",
                iid=unique_id,
                text=num_items + 1,
                values=value,
                tags=("evenrow",),
            )

    # Method to keep updating market watch prices
    def update_prices_market_watch(self, prices_unique_id):
        # print("Update Prices: ", self.market_watch_table.get_children())

        unique_id_in_market_watch_table = self.market_watch_table.get_children()

        for unique_id, prices in prices_unique_id.items():

            if str(unique_id) in unique_id_in_market_watch_table:
                # update the value of the 'Sell Price' column of 'Unique ID' to SELL price
                sell_price = (
                    "None" if prices["SELL"] == None else f"{prices['SELL']:,.2f}"
                )
                self.market_watch_table.set(unique_id, 3, sell_price)

                # update the value of the 'Buy Price' column of 'Unique ID' to BUY price
                buy_price = "None" if prices["BUY"] == None else f"{prices['BUY']:,.2f}"
                self.market_watch_table.set(unique_id, 4, buy_price)

                # update the value of the 'Buy Price' column of 'Unique ID' to Spread price
                spread_price = (
                    "None" if prices["Spread"] == None else f"{prices['Spread']:,.2f}"
                )
                self.market_watch_table.set(unique_id, 5, spread_price)

    # Method to market watch table after watchlist changed
    def update_market_watch_table_watchlist_changed(self):

        # All the Unique IDs in the System
        # Get combo details dataframe
        local_market_watch_details_df = copy.deepcopy(
            variables.market_watch_table_dataframe
        )

        # All the Unique IDs in the System
        all_unique_ids_in_system = local_market_watch_details_df["Unique ID"].tolist()

        # All the rows in market watch Table
        all_unique_ids_in_watchlist = all_unique_id_in_market_watch_table = [
            int(_x) for _x in self.market_watch_table.get_children()
        ]

        # If we want to update the table as watchlist changed
        if variables.flag_market_watch_tables_watchlist_changed:
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
                    print(f"Error inside updating market watch table, {e}")

            # Setting it to False
            variables.flag_market_watch_tables_watchlist_changed = False

        # Update the rows
        for i, row_val in local_market_watch_details_df.iterrows():

            # Unique ID of row val
            unique_id = row_val["Unique ID"]

            if unique_id in all_unique_ids_in_watchlist:

                # Tuple of vals
                row_val = tuple(row_val)

                if unique_id in all_unique_id_in_market_watch_table:
                    # Update the row at once.
                    self.market_watch_table.item(unique_id, values=row_val)
                else:
                    # Insert it in the table
                    self.market_watch_table.insert(
                        "",
                        "end",
                        iid=unique_id,
                        text="",
                        values=row_val,
                        tags=("oddrow",),
                    )
            else:
                # If this unique_id in market watch Table but not in watchlist delete it
                if unique_id in all_unique_id_in_market_watch_table:
                    try:
                        self.market_watch_table.delete(unique_id)
                    except Exception as e:
                        pass

        try:
            # Filter out the dataframe such that the dataframe only consists of all the unique ids that are present in the watchlist, so sorting will be in correct order.
            local_market_watch_details_df = local_market_watch_details_df[
                local_market_watch_details_df["Unique ID"].isin(
                    all_unique_ids_in_watchlist
                )
            ]
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Error inside updating market watch table values, is {e}")

        # All the rows in market watch Table
        all_unique_id_in_market_watch_table = self.market_watch_table.get_children()

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in local_market_watch_details_df.iterrows():

            # Unique_id
            unique_id = str(row["Unique ID"])

            # If unique_id in table
            if unique_id in all_unique_id_in_market_watch_table:
                self.market_watch_table.move(unique_id, "", counter_row)

                if counter_row % 2 == 0:
                    self.market_watch_table.item(unique_id, tags="evenrow")
                else:
                    self.market_watch_table.item(unique_id, tags="oddrow")

                # Increase row count
                counter_row += 1

    # Method to get premium for order
    def get_premium_for_orders(self, all_legs):

        # init
        net_premium_stop_loss = 0

        net_premium_take_profit = 0

        net_premium_trailing_stop_loss = 0

        count_opt_fop = 0

        # iterate all legs
        for leg_obj in all_legs:

            # init
            quantity = int(leg_obj.quantity)
            con_id = leg_obj.con_id

            # check if leg is OPT or FOP
            if leg_obj.sec_type not in ['OPT', 'FOP']:
                continue

            # Multiplier/Lot size
            if leg_obj.multiplier is None:
                multiplier = 1
            else:
                multiplier = int(leg_obj.multiplier)

            try:
                # get bid ask values for leg
                req_id = variables.con_id_to_req_id_dict[con_id]
                bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]

                # check if values are available
                if bid in ['None', None, 'N/A'] or ask in ['None', None, 'N/A']:

                    return None

                # get premium value
                premium_value = (bid + ask) / 2

                premium_value *= multiplier * leg_obj.quantity * (-1 if leg_obj.action.upper() == 'SELL' else 1)

                # assign it differently for three orders
                premium_stop_loss = premium_value

                premium_take_profit = premium_value

                premium_trailing_stop_loss = premium_value

                # Check for flag and valid value
                if variables.flag_stop_loss_premium == 'Positive Only' and premium_value < 0:

                    premium_stop_loss = 0

                # Check for flag and valid value
                elif variables.flag_stop_loss_premium == 'Negative Only' and premium_value > 0:

                    premium_stop_loss = 0

                # Check for flag and valid value
                if variables.flag_take_profit_premium == 'Positive Only' and premium_value < 0:

                    premium_take_profit = 0

                # Check for flag and valid value
                elif variables.flag_take_profit_premium == 'Negative Only' and premium_value > 0:

                    premium_take_profit = 0


                # Check for flag and valid value
                if variables.flag_trailing_stop_loss_premium == 'Positive Only' and premium_value < 0:

                    premium_trailing_stop_loss = 0

                # Check for flag and valid value
                elif variables.flag_trailing_stop_loss_premium == 'Negative Only' and premium_value > 0:

                    premium_trailing_stop_loss = 0

                # keep calcualting net premium vlaues
                net_premium_stop_loss += premium_stop_loss

                net_premium_take_profit += premium_take_profit

                net_premium_trailing_stop_loss += premium_trailing_stop_loss

            except Exception as e:

                if variables.flag_debug_mode:
                    print(f"Exception in getting premium, Exp: {e}")

                return None

        # store values in dict
        premium_dict = {'Stop Loss Premium': net_premium_stop_loss, 'Take Profit Premium': net_premium_take_profit, 'Trailing Stop Loss Premium': net_premium_trailing_stop_loss}

        return premium_dict

    # Method to get order details
    def create_trade_popup(
        self,
        buy_sell_action,
        unique_id,
        popup_title=None,
        flag_cas_order=False,
        reference_price=None,
        reference_position=None,
        trading_combination_unique_id=None,
        action_from_order_book=None,
        values_from_order_book_row=None,
        flag_multi_account=False,
        flag_conditional_series=False,
        account_id_series=None,
        bypass_rm_check_series=None,
        flag_execution_engine=None,
        modify_seq_data=None,
        index=None,
    ):

        # Create a popup window with the table
        trade_popup = tk.Toplevel()

        if popup_title == None:
            trade_popup.title(
                f"{buy_sell_action.capitalize()} Combination, Conditional Unique ID : {unique_id}"
            )
        else:
            trade_popup.title(popup_title)

        # Geometry
        trade_popup.geometry("1300x150")

        # Check if flag for multi account is True
        if flag_multi_account:

            # Geometry
            trade_popup.geometry("1330x230")

        # Create a frame for the input fields
        trade_input_frame = ttk.Frame(trade_popup, padding=20)
        trade_input_frame.pack(fill="both", expand=True)

        # Add labels and entry fields for each column in the table
        ttk.Label(
            trade_input_frame,
            text="Order Type",
            width=18,
            anchor="center",
        ).grid(column=0, row=0, padx=5, pady=5)

        # Check if flag for multi account is True
        if flag_multi_account:

            combo_quantity_label_text = f"Combo Quantity\n( x% * {variables.account_parameter_for_order_quantity} ) / Price"

        else:

            combo_quantity_label_text = "Combo Quantity\n(#Lots)"

        ttk.Label(
            trade_input_frame,
            text=combo_quantity_label_text,
            width=18,
            anchor="center",
            justify="center",
        ).grid(column=1, row=0, padx=5, pady=5)
        ttk.Label(
            trade_input_frame,
            text="Limit Price",
            width=18,
            anchor="center",
        ).grid(column=2, row=0, padx=5, pady=5)
        ttk.Label(
            trade_input_frame,
            text="Trigger Price",
            width=18,
            anchor="center",
        ).grid(column=3, row=0, padx=5, pady=5)
        ttk.Label(
            trade_input_frame,
            text="Trail Value",
            width=18,
            anchor="center",
        ).grid(column=4, row=0, padx=5, pady=5)
        ttk.Label(
            trade_input_frame,
            text="ATR Multiple",
            width=18,
            anchor="center",
        ).grid(column=5, row=0, padx=5, pady=5)
        ttk.Label(
            trade_input_frame,
            text="ATR",
            width=18,
            anchor="center",
        ).grid(column=6, row=0, padx=5, pady=5)

        ttk.Label(
            trade_input_frame,
            text="Trading Account",
            width=18,
            anchor="center",
        ).grid(column=7, row=0, padx=5, pady=5)

        ttk.Label(
            trade_input_frame,
            text="Bypass RM Checks",
            width=18,
            anchor="center",
        ).grid(column=8, row=0, padx=5, pady=5)

        ttk.Label(
            trade_input_frame,
            text="Execution Engine",
            width=18,
            anchor="center",
        ).grid(column=9, row=0, padx=5, pady=5)

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
            "Limit",
            "Stop Loss",
            "Trailing Stop Loss",
            "IB Algo Market",
            "Stop Loss Candle",
            "Take Profit Candle"
        ]

        # get combo object
        # Get combo object using unique ids
        local_unique_id_to_combo_obj = copy.deepcopy(
            variables.unique_id_to_combo_obj
        )

        combo_obj = local_unique_id_to_combo_obj[unique_id]

        #init
        flag_premium = False

        # get all legs
        all_legs = combo_obj.buy_legs + combo_obj.sell_legs


        # check if any leg is OPT or FOP
        for leg_obj in all_legs:

            if leg_obj.sec_type in ['OPT', 'FOP']:

                # set value to True
                flag_premium = True

        # if flag is true
        if flag_premium:

            order_type_options.append('Stop Loss Premium')
            order_type_options.append('Take Profit Premium')
            order_type_options.append('Trailing SL Premium')

            premium_dict = self.get_premium_for_orders(all_legs)




        # Create a Tkinter variable
        selected_order_type_option = tk.StringVar(trade_input_frame)
        selected_order_type_option.set(order_type_options[0])  # set the default option

        # Create the combo box
        order_type_options_combo_box = ttk.Combobox(
            trade_input_frame,
            textvariable=selected_order_type_option,
            width=18,
            values=order_type_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        order_type_options_combo_box.grid(column=0, row=1, padx=5, pady=5)

        # check if series input is available
        if bypass_rm_check_series == None:

            # Create a list of options
            bypass_rm_account_checks_options = ["False", "True"]

        else:

            # Create a list of options
            bypass_rm_account_checks_options = [bypass_rm_check_series]

        # Create the combo box
        bypass_rm_account_checks_options_combo_box = ttk.Combobox(
            trade_input_frame,
            width=18,
            values=bypass_rm_account_checks_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        bypass_rm_account_checks_options_combo_box.current(0)
        bypass_rm_account_checks_options_combo_box.grid(column=8, row=1, padx=5, pady=5)

        flag_execution_engine_options = [True, False]

        if flag_execution_engine != None:

            flag_execution_engine_options = [flag_execution_engine]

        # create combo box
        flag_execution_engine_combo_box = ttk.Combobox(
            trade_input_frame,
            width=18,
            values=flag_execution_engine_options,
            state="readonly",
            style="Custom.TCombobox",
        )

        if flag_execution_engine == None:

            flag_execution_engine_combo_box.current(
                flag_execution_engine_options.index(variables.flag_use_execution_engine)
            )

        else:

            flag_execution_engine_combo_box.current(0)
        flag_execution_engine_combo_box.grid(column=9, row=1, padx=5, pady=5)

        if not flag_multi_account:

            # check if series input is available
            if account_id_series == None:

                # Create a list of options
                current_session_accounts_options = copy.deepcopy(
                    variables.current_session_accounts
                )

            else:

                current_session_accounts_options = [account_id_series]

            # Create the combo box
            accounts_options_combo_box = ttk.Combobox(
                trade_input_frame,
                # textvariable=selected_account_option,
                width=18,
                values=current_session_accounts_options,
                state="readonly",
                style="Custom.TCombobox",
            )
            accounts_options_combo_box.current(0)
            accounts_options_combo_box.grid(column=7, row=1, padx=5, pady=5)

        else:

            # Create a frame for the input fields
            trade_input_frame_acc = ttk.Frame(trade_input_frame, padding=0)
            trade_input_frame_acc.grid(column=7, row=1, padx=5, pady=15, rowspan=4)

            # Create a listbox
            listbox = Listbox(
                trade_input_frame_acc,
                width=20,
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

            # check if series input is available
            if account_id_series == None:

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

            else:

                # Inserting the listbox items
                # Get all account ids
                for indx, account_id in enumerate(account_id_series, start=1):
                    listbox.insert(indx, account_id)

                for i in range(listbox.size()):
                    listbox.select_set(i)

                listbox.config(state="disabled")

            listbox.pack()

        combo_quantity_entry = ttk.Entry(
            trade_input_frame,
            width=18,
        )
        combo_quantity_entry.grid(column=1, row=1, padx=5, pady=5)

        limit_price_entry = ttk.Entry(
            trade_input_frame,
            width=18,
        )

        limit_price_entry.grid(column=2, row=1, padx=5, pady=5)

        trigger_price_entry = ttk.Entry(
            trade_input_frame,
            width=18,
        )
        trigger_price_entry.grid(column=3, row=1, padx=5, pady=5)

        trailing_sl_entry = ttk.Entry(
            trade_input_frame,
            width=18,
        )
        trailing_sl_entry.grid(column=4, row=1, padx=5, pady=5)

        atr_multiple_entry = ttk.Entry(
            trade_input_frame,
            width=18,
        )
        atr_multiple_entry.grid(column=5, row=1, padx=5, pady=5)

        atr_entry = ttk.Entry(
            trade_input_frame,
            width=18,
        )
        atr_entry.grid(column=6, row=1, padx=5, pady=5)

        # Create a frame for the "Trade" button
        button_frame = ttk.Frame(trade_popup)
        button_frame.place(
            relx=0.5, anchor=tk.CENTER
        )  # x=530, y=custom_height-50,width=100, height=30,  )
        if not flag_multi_account:

            button_frame.place(y=120)

        else:

            button_frame.place(y=205)

        # Create the "Trade" button
        trade_button = ttk.Button(
            button_frame,
            text="Trade",
            command=lambda: trade_combo(
                trade_popup, buy_sell_action, unique_id, trading_combination_unique_id
            ),
        )
        trade_button.pack(side="right")

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
        trade_input_frame.grid_slaves(row=1, column=6)[0].insert(0, atr)

        # Make entry widget readonly
        trade_input_frame.grid_slaves(row=1, column=6)[0].config(state="readonly")

        if modify_seq_data != None:
            # Convert 'None' to empty string in the dictionary values
            modify_seq_data = {
                key: "" if value in ["None", None] else value
                for key, value in modify_seq_data.items()
            }

            # Set the values of the input fields
            selected_order_type_option.set(modify_seq_data["Order Type"])

            combo_quantity_entry.insert(0, modify_seq_data["#Lots"])

            limit_price_entry.insert(0, modify_seq_data["Limit Price"])
            trigger_price_entry.insert(0, modify_seq_data["Trigger Price"])
            trailing_sl_entry.insert(0, modify_seq_data["Trail Value"])
            atr_multiple_entry.insert(0, modify_seq_data["ATR Multiple"])

        def on_order_type_combobox_selected(event=None):

            order_type = selected_order_type_option.get()

            # [row=1, column=2] => Limit price field
            # [row=1, column=3] => Trigger price field
            # [row=1, column=4] => Trail value field
            # [row=1, column=5] => ATR multiple field
            # For order type "Market"
            if order_type == "Market":

                # Delete values from fields
                trade_input_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=4)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=5)[0].delete(0, "end")

                # Set fields to empty values
                trade_input_frame.grid_slaves(row=1, column=2)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=3)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=4)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=5)[0].insert(0, "")

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="disabled"
                )

            # [row=1, column=2] => Limit price field
            # [row=1, column=3] => Trigger price field
            # [row=1, column=4] => Trail value field
            # [row=1, column=5] => ATR multiple field
            # For order type "Limit"
            elif order_type == "Limit":

                # Make entry widget selectively available
                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="normal"
                )

                # Make entry widget selectively available
                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="normal"
                )

                # Make entry widget selectively available
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="normal"
                )

                # Delete values from fields
                trade_input_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=4)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=5)[0].delete(0, "end")

                # Set fields to empty values
                trade_input_frame.grid_slaves(row=1, column=3)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=4)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=5)[0].insert(0, "")

                # Make entry widget selectively available
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(state="normal")
                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="disabled"
                )

                if not is_float(trade_input_frame.grid_slaves(row=1, column=2)[0].get().strip()):
                    trade_input_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")

            # [row=1, column=2] => Limit price field
            # [row=1, column=3] => Trigger price field
            # [row=1, column=4] => Trail value field
            # [row=1, column=5] => ATR multiple field
            # For order type "Stop loss"
            elif order_type == "Stop Loss":

                # Make entry widget selectively available
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="normal"
                )

                # Delete values from fields
                trade_input_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=4)[0].delete(0, "end")

                # Set fields to empty values
                trade_input_frame.grid_slaves(row=1, column=2)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=4)[0].insert(0, "")

                # Make entry widget selectively available
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=3)[0].config(state="normal")
                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(state="normal")

                if not is_float(trade_input_frame.grid_slaves(row=1, column=3)[0].get().strip()):
                    trade_input_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")

            # [row=1, column=2] => Limit price field
            # [row=1, column=3] => Trigger price field
            # [row=1, column=4] => Trail value field
            # [row=1, column=5] => ATR multiple field
            # For order type "Trailing Stop Loss"
            elif order_type == "Trailing Stop Loss":

                # Make entry widget selectively available
                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="normal"
                )

                # Make entry widget selectively available
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="normal"
                )



                # Delete values from fields
                trade_input_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")

                # Set fields to empty values
                trade_input_frame.grid_slaves(row=1, column=2)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=3)[0].insert(0, "")

                # Make entry widget selectively available
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=4)[0].config(state="normal")
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(state="normal")

                if not is_float(trade_input_frame.grid_slaves(row=1, column=4)[0].get().strip()):
                    trade_input_frame.grid_slaves(row=1, column=4)[0].delete(0, "end")

            # [row=1, column=2] => Limit price field
            # [row=1, column=3] => Trigger price field
            # [row=1, column=4] => Trail value field
            # [row=1, column=5] => ATR multiple field
            # For order type "IB Algo Market"
            elif order_type == "IB Algo Market":

                # Delete values from fields
                trade_input_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=4)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=5)[0].delete(0, "end")

                # Set fields to empty values
                trade_input_frame.grid_slaves(row=1, column=2)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=3)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=4)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=5)[0].insert(0, "")

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="disabled"
                )

            elif order_type == 'Stop Loss Premium':


                try:

                    # dict for combo prices
                    local_unique_id_to_prices_dict = copy.deepcopy(variables.unique_id_to_prices_dict)

                    current_buy_price, current_sell_price = (
                        local_unique_id_to_prices_dict[unique_id]["BUY"],
                        local_unique_id_to_prices_dict[unique_id]["SELL"],
                    )

                    current_price = (current_buy_price + current_sell_price) / 2

                except Exception as e:

                    if variables.flag_debug_mode:

                        print(f"Exception inside getting current price for stop loss premium, Exp: {e}")

                    current_price = 'N/A'

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="normal"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="normal"
                )

                # enabling entry object
                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="normal"
                )

                # Init
                value_to_prefill = 'None'

                net_premium = 'None'

                # getting value of trigger price to refill
                if premium_dict != None and 'Stop Loss Premium' in premium_dict and is_float(current_price):

                    net_premium = premium_dict['Stop Loss Premium']

                    # check if it is float
                    if is_float(net_premium):

                        # get trigger price
                        if buy_sell_action.upper() == 'BUY':
                            value_to_prefill = current_price + abs(net_premium)

                        else:

                            value_to_prefill = current_price - abs(net_premium)

                        value_to_prefill = round(value_to_prefill, 2)

                    else:

                        value_to_prefill = 'N/A'

                else:

                    value_to_prefill = 'N/A'

                # Delete values from fields
                trade_input_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=4)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=5)[0].delete(0, "end")

                # Set fields to empty values
                trade_input_frame.grid_slaves(row=1, column=2)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=3)[0].insert(0, value_to_prefill)
                trade_input_frame.grid_slaves(row=1, column=4)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=5)[0].insert(0, "")

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )


                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="readonly"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="disabled"
                )

            elif order_type == 'Take Profit Premium':

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="normal"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="normal"
                )

                try:

                    # dict for combo prices
                    local_unique_id_to_prices_dict = copy.deepcopy(variables.unique_id_to_prices_dict)

                    current_buy_price, current_sell_price = (
                        local_unique_id_to_prices_dict[unique_id]["BUY"],
                        local_unique_id_to_prices_dict[unique_id]["SELL"],
                    )

                    current_price = (current_buy_price + current_sell_price) / 2

                except Exception as e:

                    if variables.flag_debug_mode:
                        print(f"Exception inside getting current price for stop loss premium, Exp: {e}")

                    current_price = 'N/A'


                # Init
                value_to_prefill = 'None'

                net_premium = 'None'


                # getting value of trigger price to refill
                if premium_dict != None and 'Take Profit Premium' in premium_dict and is_float(current_price):

                    net_premium = premium_dict['Take Profit Premium']

                    if is_float(net_premium):

                        net_premium = round(net_premium, 2)

                        # get trigger price
                        if buy_sell_action.upper() == 'BUY':
                            value_to_prefill = current_price - abs(net_premium)

                        else:

                            value_to_prefill = current_price + abs(net_premium)

                        value_to_prefill = round(value_to_prefill, 2)

                    else:

                        value_to_prefill = 'N/A'

                else:

                    value_to_prefill = 'N/A'

                # Delete values from fields
                trade_input_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=4)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=5)[0].delete(0, "end")

                # Set fields to empty values
                trade_input_frame.grid_slaves(row=1, column=2)[0].insert(0, value_to_prefill)
                trade_input_frame.grid_slaves(row=1, column=3)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=4)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=5)[0].insert(0, "")

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="readonly"
                )


                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="disabled"
                )

            elif order_type == 'Trailing SL Premium':

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="normal"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="normal"
                )

                # Init
                value_to_prefill = 'None'

                # getting value of trigger price to refill
                if premium_dict != None and 'Trailing Stop Loss Premium' in premium_dict:

                    value_to_prefill = premium_dict['Trailing Stop Loss Premium']

                    if is_float(value_to_prefill):

                        value_to_prefill = abs(round(value_to_prefill, 2))

                    else:

                        value_to_prefill = 'N/A'

                else:

                    value_to_prefill = 'N/A'

                # Delete values from fields
                trade_input_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=4)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=5)[0].delete(0, "end")

                # Set fields to empty values
                trade_input_frame.grid_slaves(row=1, column=2)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=3)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=4)[0].insert(0, value_to_prefill)
                trade_input_frame.grid_slaves(row=1, column=5)[0].insert(0, "")

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )


                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="readonly"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="disabled"
                )

            elif order_type == 'Stop Loss Candle':

                # Init
                value_to_prefill = 'N/A'

                # get last candle high or low price
                try:

                    # check if action is buy
                    if buy_sell_action.upper() == 'BUY':

                        value_to_prefill = variables.map_unique_id_to_candle_for_order_values[unique_id]['High Candle Value']

                    # if action is sell
                    else:

                        value_to_prefill = variables.map_unique_id_to_candle_for_order_values[unique_id]['Low Candle Value']

                except Exception as e:

                    # Print to console
                    if variables.flag_debug_mode:

                        print(f"Exception inside getting current price for stop loss premium, Exp: {e}")

                    # set value to N/A
                    value_to_prefill = 'N/A'


                # Make entry widget normal
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="normal"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="normal"
                )

                # enabling entry object
                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="normal"
                )



                # Delete values from fields
                trade_input_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=4)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=5)[0].delete(0, "end")

                # Set fields to empty values
                trade_input_frame.grid_slaves(row=1, column=2)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=3)[0].insert(0, value_to_prefill)
                trade_input_frame.grid_slaves(row=1, column=4)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=5)[0].insert(0, "")

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="disabled"
                )


                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="readonly"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="disabled"
                )

            elif order_type == 'Take Profit Candle':

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="normal"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="normal"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="normal"
                )

                # Init
                value_to_prefill = 'N/A'

                # get last candle high or low price
                try:

                    # check if action is sell
                    if buy_sell_action.upper() == 'SELL':

                        value_to_prefill = variables.map_unique_id_to_candle_for_order_values[unique_id][
                            'High Candle Value']

                    # check if action is buy
                    else:

                        value_to_prefill = variables.map_unique_id_to_candle_for_order_values[unique_id][
                            'Low Candle Value']

                except Exception as e:

                    # print to console
                    if variables.flag_debug_mode:
                        print(f"Exception inside getting current price for stop loss premium, Exp: {e}")

                    # set value to N/A
                    value_to_prefill = 'N/A'



                # Delete values from fields
                trade_input_frame.grid_slaves(row=1, column=2)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=3)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=4)[0].delete(0, "end")
                trade_input_frame.grid_slaves(row=1, column=5)[0].delete(0, "end")

                # Set fields to empty values
                trade_input_frame.grid_slaves(row=1, column=2)[0].insert(0, value_to_prefill)
                trade_input_frame.grid_slaves(row=1, column=3)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=4)[0].insert(0, "")
                trade_input_frame.grid_slaves(row=1, column=5)[0].insert(0, "")

                # Make entry widget disabled
                trade_input_frame.grid_slaves(row=1, column=2)[0].config(
                    state="readonly"
                )


                trade_input_frame.grid_slaves(row=1, column=3)[0].config(
                    state="disabled"
                )

                trade_input_frame.grid_slaves(row=1, column=4)[0].config(
                    state="disabled"
                )
                trade_input_frame.grid_slaves(row=1, column=5)[0].config(
                    state="disabled"
                )

        # Bind the function to the ComboBoxSelected event
        order_type_options_combo_box.bind(
            "<<ComboboxSelected>>", on_order_type_combobox_selected
        )

        def set_values_in_trade_popup():

            # Get values of order selected and strip it, replace ",", "None" with empty string
            order_type = values_from_order_book_row[5].strip()
            combo_quantity = values_from_order_book_row[4].strip().replace(",", "")
            limit_price = (
                values_from_order_book_row[9]
                .strip()
                .replace(",", "")
                .replace("None", "")
            )
            trigger_price = (
                values_from_order_book_row[10]
                .strip()
                .replace(",", "")
                .replace("None", "")
            )
            trail_value = (
                values_from_order_book_row[12]
                .strip()
                .replace(",", "")
                .replace("None", "")
            )
            atr_multiple = (
                values_from_order_book_row[16]
                .strip()
                .replace(",", "")
                .replace("None", "")
            )
            atr = (
                values_from_order_book_row[17]
                .strip()
                .replace(",", "")
                .replace("None", "")
            )
            account_id = values_from_order_book_row[1].strip()
            bypass_rm_check = values_from_order_book_row[19].strip()

            # Get updated values based on order type
            [
                limit_price,
                trigger_price,
                trail_value,
                atr_multiple,
                atr,
            ] = update_values_based_on_order_type(
                order_type, limit_price, trigger_price, trail_value, atr_multiple, atr
            )

            # In case of trailing stop loss ATR order trail vaue will be empty
            if trail_value != "" and atr_multiple != "":

                trail_value = ""

            # In case of stop loss ATR order trigger price will be empty
            if trigger_price != "" and atr_multiple != "":

                trigger_price = ""

            # Make quantity double for flip order
            if action_from_order_book == "Flip":

                combo_quantity = int(float(combo_quantity)) * 2

            # Set the values of the input fields
            selected_order_type_option.set(order_type)
            accounts_options_combo_box.set(account_id)
            bypass_rm_account_checks_options_combo_box.set(bypass_rm_check)
            flag_execution_engine_combo_box.set(values_from_order_book_row[20])

            trade_input_frame.grid_slaves(row=1, column=1)[0].insert(0, combo_quantity)
            trade_input_frame.grid_slaves(row=1, column=2)[0].insert(0, limit_price)
            trade_input_frame.grid_slaves(row=1, column=3)[0].insert(0, trigger_price)
            trade_input_frame.grid_slaves(row=1, column=4)[0].insert(0, trail_value)
            trade_input_frame.grid_slaves(row=1, column=5)[0].insert(0, atr_multiple)
            trade_input_frame.grid_slaves(row=1, column=6)[0].insert(0, atr)

        # check if action to be taken for order selected is availabel
        if action_from_order_book != None:

            # Set values in trade pop up
            set_values_in_trade_popup()

        # Disabled fields based on order type
        on_order_type_combobox_selected()

        def trade_combo(
            trade_popup, buy_sell_action, unique_id, trading_combination_unique_id=None
        ):

            # Get values for each field
            order_type = (
                selected_order_type_option.get()
            )  # trade_input_frame.grid_slaves(row=1, column=0)[0].get().strip()

            bypass_rm_check = bypass_rm_account_checks_options_combo_box.get()

            # get vlaue for execution engine
            flag_execution_engine = flag_execution_engine_combo_box.get()

            # get boolean value for execution engine
            if flag_execution_engine == "True":

                flag_execution_engine = True

            else:

                flag_execution_engine = False

            if not flag_multi_account:

                account_id = accounts_options_combo_box.get().strip()

            else:

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

                                    self.display_error_popup(error_title, error_string)

                                    return

                                account_id_list.append(account)

                # Get unique account ids and sort them
                account_id_list = sorted(list(set(account_id_list)))

            combo_quantity = (
                trade_input_frame.grid_slaves(row=1, column=1)[0].get().strip()
            )
            limit_price = (
                trade_input_frame.grid_slaves(row=1, column=2)[0].get().strip()
            )
            trigger_price = (
                trade_input_frame.grid_slaves(row=1, column=3)[0].get().strip()
            )
            trail_value = (
                trade_input_frame.grid_slaves(row=1, column=4)[0].get().strip()
            )
            atr_multiple = (
                trade_input_frame.grid_slaves(row=1, column=5)[0].get().strip()
            )
            atr = trade_input_frame.grid_slaves(row=1, column=6)[0].get().strip()

            # Get updated values based on order type
            [
                limit_price,
                trigger_price,
                trail_value,
                atr_multiple,
                atr,
            ] = update_values_based_on_order_type(
                order_type, limit_price, trigger_price, trail_value, atr_multiple, atr
            )

            # When we have conditional buy and sell order, where the trading UID is d/f from the cond. combo UID.
            # we want to validate the order on the trading combo. but we want the condition on the original unique_id
            original_unique_id = copy.deepcopy(unique_id)

            # For conditional buy and sell order where user can give different combo for trading.
            # it is done so we can validate the order on the correct unique id if the limit, trigger price is correct.
            if trading_combination_unique_id is not None:
                unique_id = trading_combination_unique_id

            current_price_unique_id = variables.unique_id_to_prices_dict[unique_id]

            current_buy_price, current_sell_price = (
                current_price_unique_id["BUY"],
                current_price_unique_id["SELL"],
            )

            if variables.flag_debug_mode:
                print(current_price_unique_id)
                print(
                    "Order Type: ",
                    order_type,
                    "Combo: ",
                    combo_quantity,
                    "Limit: ",
                    limit_price,
                    "Trigger: ",
                    trigger_price,
                    "Trail: ",
                    trail_value,
                    "Order Type type: ",
                    type(order_type),
                    "ATR Multiple: ",
                    atr_multiple,
                    "ATR: ",
                    atr,
                )

            # Check if account id is empty
            if not flag_multi_account and account_id == "":

                # Error pop up
                error_title = "Account ID is unavailable."
                error_string = "Can not trade combo because Account ID is unavailable."

                self.display_error_popup(error_title, error_string)
                return

            # check if unique id is in current session accounts
            if (
                not flag_multi_account
                and account_id not in variables.current_session_accounts
            ):

                # Error pop up
                error_title = "Account ID is unavailable in current session."
                error_string = "Can not trade combo because Account ID \nis unavailable in current session."

                self.display_error_popup(error_title, error_string)

                return
            # Check if multiple account selection is empty
            if flag_multi_account and account_id_list == []:

                # Error pop up
                error_title = "List of Account ID is Unavailable."
                error_string = (
                    "Can not trade combo because list of Account ID is unavailable."
                )

                self.display_error_popup(error_title, error_string)
                return

            # Validating we have prices for the combo
            if buy_sell_action == "BUY" and current_buy_price == None:
                error_title = "Buy Price is unavailable."
                error_string = "Can not buy combo because buy price is unavailable."

                self.display_error_popup(error_title, error_string)
                return
            elif buy_sell_action == "SELL" and current_sell_price == None:
                error_title = "Sell Price is unavailable."
                error_string = "Can not sell combo because sell price is unavailable."

                self.display_error_popup(error_title, error_string)
                return
            else:
                try:
                    current_buy_price = (
                        float(current_buy_price) if current_buy_price != None else None
                    )
                    current_sell_price = (
                        float(current_sell_price)
                        if current_sell_price != None
                        else None
                    )
                except Exception as e:
                    print("Exception Inside Trade Combo, {e}")

            # User have provided correct comboquantity
            if not flag_multi_account and (
                (combo_quantity == "")
                or (combo_quantity.isnumeric() == False)
                or (int(float(combo_quantity)) <= 0)
            ):

                error_title = "Invalid Combo Quantity"
                error_string = "Combo Quantity must be an integer value."

                self.display_error_popup(error_title, error_string)
                return

            # User have provided correct comboquantity
            if flag_multi_account and not is_float(combo_quantity):

                error_title = "Invalid Combo Quantity"
                error_string = "Combo Quantity must be an decimal value ."

                self.display_error_popup(error_title, error_string)
                return

            # User have provided correct comboquantity
            if flag_multi_account and float(combo_quantity) <= 0:
                error_title = "Invalid Combo Quantity"
                error_string = "Combo Quantity must be greater than 0 ."

                self.display_error_popup(error_title, error_string)
                return

            # check if order type is premium based order
            if order_type in ['Stop Loss Premium', 'Take Profit Premium', 'Trailing SL Premium']:


                # set order type Stop Loss based on Stop Loss premium order type provided
                if order_type == 'Stop Loss Premium':

                    order_type = 'Stop Loss'


                # set order type Limit based on Take Profit premium order type provided
                elif order_type == 'Take Profit Premium':

                    order_type = 'Limit'


                # set order type Trailing Stop Loss based on Trailing Stop Loss premium order type provided
                else:

                    order_type = 'Trailing Stop Loss'

            # check if order type is candle based order
            if order_type in ['Stop Loss Candle', 'Take Profit Candle']:


                # set order type Stop Loss based on Stop Loss premium order type provided
                if order_type == 'Stop Loss Candle':

                    order_type = 'Stop Loss'


                # set order type Limit based on Take Profit premium order type provided
                elif order_type == 'Take Profit Candle':

                    order_type = 'Limit'




            # Limit Orders
            if order_type == "Limit":

                try:
                    limit_price = float(limit_price)
                except Exception as e:
                    error_title = "Missing Limit Price"
                    error_string = "Please provide a valid Limit Price for Limit Order."

                    self.display_error_popup(error_title, error_string)
                    return

                if (order_type == "Limit") and (
                    buy_sell_action == "BUY" and current_buy_price < limit_price
                ):
                    error_title = "Invalid Limit Price."
                    error_string = (
                        "Limit Price for Buy Order must be less than current Buy Price."
                    )

                    self.display_error_popup(error_title, error_string)
                    return

                elif (order_type == "Limit") and (
                    buy_sell_action == "SELL" and current_sell_price > limit_price
                ):
                    error_title = "Invalid Limit Price"
                    error_string = "Limit Price for Sell Order must be greater than current Sell Price."

                    self.display_error_popup(error_title, error_string)
                    return

            # Stop Loss Orders
            elif order_type == "Stop Loss":

                # Check if both trigger price and atr multiple is filled
                if trigger_price != "" and atr_multiple != "":

                    error_title = "Invalid combination of values"
                    error_string = "Values for both Trigger Price and ATR Multiple must not be filled."

                    self.display_error_popup(error_title, error_string)
                    return

                # Check if both trigger price and atr multiple is empty
                elif trigger_price == "" and atr_multiple == "":

                    error_title = "Invalid combination of values"
                    error_string = "Values for both Trigger Price and ATR Multiple must not be empty."

                    self.display_error_popup(error_title, error_string)
                    return

                # Check if trigger price is valid
                elif trigger_price != "" and atr_multiple == "":
                    try:
                        trigger_price = float(trigger_price)

                        # Make ATR value empty in case of not using ATR multiplier in stop loss order
                        atr = ""
                    except Exception as e:
                        error_title = "Invalid Trigger Price"
                        error_string = (
                            "Please provide a valid Trigger Price for Stop Loss Order."
                        )

                        self.display_error_popup(error_title, error_string)
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

                        self.display_error_popup(error_title, error_string)
                        return

                    # checking if atr value is valid
                    try:
                        atr = float(atr)

                    except Exception as e:
                        error_title = "Invalid ATR"
                        error_string = "Unable to get valid ATR for Stop Loss Order."

                        self.display_error_popup(error_title, error_string)
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
                        if variables.flag_debug_mode:

                            print(e)
                        error_title = "Invalid Trigger Price"
                        error_string = f"Unable to get valid Trigger Price based on ATR Multiple: {atr_multiple}, \nATR: {atr} and Avg Price for Combo: {avg_price_combo} "

                        self.display_error_popup(error_title, error_string)
                        return

                if (order_type == "Stop Loss") and (
                    buy_sell_action == "BUY" and current_buy_price > trigger_price
                ):
                    error_title = "Invalid Trigger Price"
                    error_string = "Trigger Price for Buy Order must be greater than current Buy Price."

                    self.display_error_popup(error_title, error_string)
                    return

                elif (order_type == "Stop Loss") and (
                    buy_sell_action == "SELL" and current_sell_price < trigger_price
                ):
                    error_title = "Invalid Trigger Price"
                    error_string = "Trigger Price for Sell Order must be lower than current Sell Price."

                    self.display_error_popup(error_title, error_string)
                    return

            # Trailing Stop Loss Orders
            elif order_type == "Trailing Stop Loss":

                # check if both trail value and atr multiple is filled
                if trail_value != "" and atr_multiple != "":

                    error_title = "Invalid combination of values"
                    error_string = "Values for both Trail Value and ATR Multiple must not be filled."

                    self.display_error_popup(error_title, error_string)
                    return

                # Check if both trail value and atr multiple is empty
                elif trail_value == "" and atr_multiple == "":

                    error_title = "Invalid combination of values"
                    error_string = "Values for both Trail Value and ATR Multiple must not be empty."

                    self.display_error_popup(error_title, error_string)
                    return

                # Check if trail value is valid
                elif trail_value != "" and atr_multiple == "":
                    try:
                        trail_value = float(trail_value)

                        # Make ATR value empty in case of not using ATR multiplier in trailing stop loss order
                        atr = ""
                    except Exception as e:
                        error_title = "Invalid Trail Value"
                        error_string = (
                            "Please provide a valid Trail Value for Stop Loss Order."
                        )

                        self.display_error_popup(error_title, error_string)
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

                        self.display_error_popup(error_title, error_string)
                        return

                    # checking if atr value is valid
                    try:
                        atr = float(atr)

                    except Exception as e:
                        error_title = "Invalid ATR"
                        error_string = (
                            "Unable to get valid ATR for Trailing Stop Loss Order."
                        )

                        self.display_error_popup(error_title, error_string)
                        return

                    # checking if trail value calcualtions are valid
                    try:

                        # Get trigger price
                        trail_value = atr_multiple * atr

                    except Exception as e:
                        error_title = "Invalid Trigger Price"
                        error_string = f"Unable to get valid Trail Value based on ATR Multiple: {atr_multiple} and ATR: {atr}"

                        self.display_error_popup(error_title, error_string)
                        return







            temp_uid = None

            if flag_multi_account:

                if trading_combination_unique_id != None:

                    temp_uid = int(trading_combination_unique_id)

                else:

                    temp_uid = unique_id

                try:
                    # Check order type is market or ib algo market
                    if order_type in ["Market", "IB Algo Market"]:
                        # add trading_combination_unique_id
                        price = (
                            variables.unique_id_to_prices_dict[temp_uid]["BUY"]
                            + variables.unique_id_to_prices_dict[temp_uid]["SELL"]
                        ) / 2

                    # Check order type is limit order
                    elif order_type == "Limit":

                        price = float(limit_price)

                    # Check order type is stop loss order
                    elif order_type == "Stop Loss":

                        price = float(trigger_price)

                    # Check order type is trailing stop loss
                    elif order_type == "Trailing Stop Loss":

                        # Getting initial trigger price
                        avg_combo_price = variables.unique_id_to_prices_dict[temp_uid][
                            buy_sell_action
                        ]

                        init_trigger_price = avg_combo_price + (
                            trail_value * ((-1) if buy_sell_action == "SELL" else (1))
                        )

                        price = float(init_trigger_price)
                except Exception as e:

                    error_title = f"For Unique ID: {unique_id}, Could not get price of combination"
                    error_string = f"For Unique ID: {unique_id}, Could not get price of combination"

                    self.display_error_popup(error_title, error_string)
                    return

                # Init
                map_account_to_quanity_dict = {}

                try:

                    # Iterating account ids
                    for account in account_id_list:

                        # Getting value of account parameter
                        if variables.account_parameter_for_order_quantity == "NLV":

                            value_of_account_parameter = (
                                variables.accounts_table_dataframe.loc[
                                    variables.accounts_table_dataframe["Account ID"]
                                    == account,
                                    variables.accounts_table_columns[1],
                                ].iloc[0]
                            )

                        elif variables.account_parameter_for_order_quantity == "SMA":

                            value_of_account_parameter = (
                                variables.accounts_table_dataframe.loc[
                                    variables.accounts_table_dataframe["Account ID"]
                                    == account,
                                    variables.accounts_table_columns[2],
                                ].iloc[0]
                            )

                        elif variables.account_parameter_for_order_quantity == "CEL":

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

                            self.display_error_popup(error_title, error_string)
                            return

                        # Calculate combo qunaity for account id
                        if float(price) != 0:

                            combo_quantity = float(combo_quantity)

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
                        map_account_to_quanity_dict[
                            account
                        ] = combo_quantity_for_account

                except Exception as e:

                    error_title = f"For Unique ID: {unique_id}, Could not get quantity for accounts"
                    error_string = f"For Unique ID: {unique_id}, Could not get quantity for accounts"

                    self.display_error_popup(error_title, error_string)
                    return

            # Adjusting values
            limit_price = "None" if limit_price == "" else limit_price
            trigger_price = "None" if trigger_price == "" else trigger_price
            trail_value = "None" if trail_value == "" else trail_value
            atr_multiple = "None" if atr_multiple == "" else atr_multiple
            atr = "None" if atr in ["N/A", ""] else atr

            # If order is Conditional Order
            if flag_cas_order:

                # Reached end means no error were found place order
                # Close the popup
                trade_popup.destroy()

                # Init None Values
                combo_identified = None
                if not flag_multi_account:

                    # Display Popup for user to enter condition
                    # Display Popup for user to enter condition
                    variables.screen.screen_cas_obj.display_enter_condition_popup(
                        original_unique_id,
                        buy_sell_action,
                        combo_identified,
                        reference_price,
                        reference_position[account_id],
                        order_type,
                        combo_quantity,
                        limit_price,
                        trigger_price,
                        trail_value,
                        trading_combination_unique_id,
                        atr_multiple=atr_multiple,
                        atr=atr,
                        account_id=account_id,
                        bypass_rm_check=bypass_rm_check,
                        flag_conditional_series=flag_conditional_series,
                        flag_execution_engine=flag_execution_engine,
                        modify_seq_data=modify_seq_data,
                        index=index,
                    )

                else:

                    # Display Popup for user to enter condition
                    # Display Popup for user to enter condition
                    variables.screen.screen_cas_obj.display_enter_condition_popup(
                        original_unique_id,
                        buy_sell_action,
                        combo_identified,
                        reference_price,
                        reference_position,
                        order_type,
                        map_account_to_quanity_dict,
                        limit_price,
                        trigger_price,
                        trail_value,
                        trading_combination_unique_id,
                        atr_multiple=atr_multiple,
                        atr=atr,
                        account_id=None,
                        flag_multi_account=True,
                        bypass_rm_check=bypass_rm_check,
                        flag_conditional_series=flag_conditional_series,
                        flag_execution_engine=flag_execution_engine,
                        modify_seq_data=modify_seq_data,
                        index=index,
                        combo_quantity_prcnt=combo_quantity,
                    )

            else:

                # If for single account
                if not flag_multi_account:

                    def single_account_order():

                        flag_send_order = True

                        # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
                        if (
                            bypass_rm_check == "False"
                            and variables.flag_enable_rm_account_rules
                            and variables.flag_account_liquidation_mode[account_id]
                        ):

                            time.sleep(variables.rm_checks_interval_if_failed)

                            # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
                            if (
                                bypass_rm_check == "False"
                                and variables.flag_enable_rm_account_rules
                                and variables.flag_account_liquidation_mode[account_id]
                            ):

                                # Error pop up
                                error_title = f"For Account ID: {account_id}, Order cannot be placed, \naccount is in liquidation mode"
                                error_string = f"For Account ID: {account_id}, Order cannot be placed, \naccount is in liquidation mode"

                                self.display_error_popup(error_title, error_string)

                                flag_send_order = False

                        if (
                            not trade_level_rm_check_result(
                                bypass_rm_check, original_unique_id
                            )
                            and flag_send_order
                        ):

                            time.sleep(variables.rm_checks_interval_if_failed)

                            if not trade_level_rm_check_result(
                                bypass_rm_check, original_unique_id
                            ):

                                # get details of which check in trade rm check failed
                                failed_trade_checks_details = (
                                    get_failed_checks_string_for_trade_rm_check(
                                        original_unique_id
                                    )
                                )

                                # Error pop up
                                error_title = f"For Account ID: {account_id}, Order cannot be placed, \nTrade level RM check failed"
                                error_string = f"For Account ID: {account_id}, Order cannot be placed, \nTrade level RM check failed :\n{failed_trade_checks_details}"

                                self.display_error_popup(error_title, error_string)
                                flag_send_order = False

                        if flag_send_order:

                            # Reached end means no error were found place order
                            # Close the popup
                            trade_popup.destroy()

                            # Send order in a separate thread
                            send_order_thread = threading.Thread(
                                target=send_order,
                                args=(
                                    original_unique_id,
                                    buy_sell_action,
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
                                    "execution_engine": flag_execution_engine,
                                },
                            )
                            send_order_thread.start()
                        else:
                            trade_button.config(state="normal")

                    # Send order in a separate thread
                    rm_check_thread = threading.Thread(
                        target=single_account_order,
                        args=(),
                    )
                    rm_check_thread.start()
                    trade_button.config(state="disabled")

                # For multi accounts
                else:

                    def multi_account_order():

                        # Init
                        rejected_account_liquidation_string = ""
                        rejected_account_trade_rm_failed_string = ""
                        flag_trade_pop_up_keep = False

                        # Iterate accounts
                        for account in map_account_to_quanity_dict:

                            # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
                            if (
                                bypass_rm_check == "False"
                                and variables.flag_enable_rm_account_rules
                                and variables.flag_account_liquidation_mode[account]
                            ):

                                time.sleep(variables.rm_checks_interval_if_failed)

                                # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
                                if (
                                    bypass_rm_check == "False"
                                    and variables.flag_enable_rm_account_rules
                                    and variables.flag_account_liquidation_mode[account]
                                ):

                                    rejected_account_liquidation_string += account + ","

                                    # set value to false
                                    flag_trade_pop_up_keep = True
                                    continue

                            # trade level RM check
                            elif not trade_level_rm_check_result(
                                bypass_rm_check, original_unique_id
                            ):

                                time.sleep(variables.rm_checks_interval_if_failed)

                                if not trade_level_rm_check_result(
                                    bypass_rm_check, original_unique_id
                                ):

                                    rejected_account_trade_rm_failed_string += (
                                        account + ","
                                    )

                                    # set value to false
                                    flag_trade_pop_up_keep = True
                                    continue

                            # Get value of combo quantity for account
                            combo_quantity_for_count = map_account_to_quanity_dict[
                                account
                            ]

                            # Check if quantity is greater than 0
                            if combo_quantity_for_count > 0:

                                # Send order in a separate thread
                                send_order_thread = threading.Thread(
                                    target=send_order,
                                    args=(
                                        original_unique_id,
                                        buy_sell_action,
                                        order_type,
                                        combo_quantity_for_count,
                                        limit_price,
                                        trigger_price,
                                        trail_value,
                                    ),
                                    kwargs={
                                        "atr_multiple": atr_multiple,
                                        "atr": atr,
                                        "account_id": account,
                                        "bypass_rm_check": bypass_rm_check,
                                        "execution_engine": flag_execution_engine,
                                    },
                                )
                                send_order_thread.start()

                                # sleep
                                time.sleep(0.5)

                        # Error msg
                        error_msg = ""

                        # Error message for account liquidaton errors
                        if len(rejected_account_liquidation_string) != 0:

                            rejected_account_liquidation_string = (
                                make_multiline_mssg_for_gui_popup(
                                    "Accounts in liquidation mode: "
                                    + rejected_account_liquidation_string[:-1]
                                )
                            )
                            error_msg += rejected_account_liquidation_string

                        # Error message for trade rm check errors
                        if len(rejected_account_trade_rm_failed_string) != 0:

                            # get details of which check in trade rm check failed
                            failed_trade_checks_details = (
                                get_failed_checks_string_for_trade_rm_check(
                                    original_unique_id
                                )
                            )

                            # create error msg
                            rejected_account_trade_rm_failed_string = (
                                make_multiline_mssg_for_gui_popup(
                                    "Trade RM check failed for accounts : "
                                    + failed_trade_checks_details
                                )
                            )

                            if error_msg != "":
                                error_msg += (
                                    "\n" + rejected_account_trade_rm_failed_string
                                )

                            else:

                                error_msg += rejected_account_trade_rm_failed_string

                            # error_msg += f'\n{failed_trade_checks_details}'

                        # display error msg
                        if error_msg != "":

                            self.display_error_popup("Rejected Accounts", error_msg)

                        # chck if pop up is not destroyed
                        if flag_trade_pop_up_keep:

                            trade_button.config(state="enabled")

                        else:

                            # Reached end means no error were found place order
                            # Close the popup
                            trade_popup.destroy()

                    # Send order in a separate thread
                    rm_check_thread = threading.Thread(
                        target=multi_account_order,
                        args=(),
                    )
                    rm_check_thread.start()

                    trade_button.config(state="disabled")

    # Method to create order book table
    def create_order_book_tab(self):
        # Add widgets to the Order Book tab here

        # Create Treeview Frame for active combo table
        order_book_clean_table_frame = ttk.Frame(self.order_book_tab, padding=20)
        order_book_clean_table_frame.pack(pady=20)

        # Create the "Clear Table" button
        clean_table_button = ttk.Button(
            order_book_clean_table_frame,
            text="Clear Table",
            command=lambda: self.clear_order_book_table(),
        )

        clean_table_button.grid(column=1, row=0, padx=(705, 470), pady=5)

        # Create the "Delete Multiple Orders" button
        delete_multiple_orders_button = ttk.Button(
            order_book_clean_table_frame,
            text="Cancel Orders",
            command=lambda: self.cancel_selected_orders(delete_multiple_orders_button),
        )

        delete_multiple_orders_button.grid(column=2, row=0, padx=5, pady=5)

        # Create the "Upload Orders from CSV" button
        upload_order_from_csv_button = ttk.Button(
            order_book_clean_table_frame,
            text="Upload Orders",
            command=lambda: self.upload_order_from_csv(upload_order_from_csv_button),
        )

        upload_order_from_csv_button.grid(column=3, row=0, padx=5, pady=5)

        # Create the "download Orders to CSV" button
        download_order_to_csv_button = ttk.Button(
            order_book_clean_table_frame,
            text="Download Orders",
            command=lambda: self.download_order_to_csv(download_order_to_csv_button),
        )

        download_order_to_csv_button.grid(column=5, row=0, padx=5, pady=5)

        # Place in center
        order_book_clean_table_frame.place(relx=0.5, anchor=tk.CENTER)
        order_book_clean_table_frame.place(y=30)

        # Create Treeview Frame for active combo table
        order_book_table_frame = ttk.Frame(self.order_book_tab, padding=20)
        order_book_table_frame.pack(pady=20)
        order_book_table_frame.pack(fill="both", expand=True)

        # Place in center
        order_book_table_frame.place(relx=0.5, anchor=tk.CENTER)
        order_book_table_frame.place(y=415, width=1600)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(order_book_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Treeview Scrollbar
        tree_scroll_x = Scrollbar(order_book_table_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        # Create Treeview
        self.order_book_table = ttk.Treeview(
            order_book_table_frame,
            xscrollcommand=tree_scroll_x.set,
            yscrollcommand=tree_scroll.set,
            height=26,
            selectmode="extended",
        )
        # Pack to the screen
        self.order_book_table.pack(expand=True, fill="both")

        # Configure the scrollbar
        tree_scroll.config(command=self.order_book_table.yview)

        # Configure the scrollbar
        tree_scroll_x.config(command=self.order_book_table.xview)

        local_order_book_table_columns = copy.deepcopy(
            variables.order_book_table_columns
        )

        # Column in order book table
        self.order_book_table["columns"] = local_order_book_table_columns

        # Creating Columns
        self.order_book_table.column("#0", width=0, stretch="no")
        self.order_book_table.column("Unique ID", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Account ID", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Tickers", anchor="center", width=212, stretch="no")
        self.order_book_table.column("Action", anchor="center", width=82, stretch="no")
        self.order_book_table.column("#Lots", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Order Type", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Order Time", anchor="center", width=150, stretch="no")
        self.order_book_table.column("Last Update Time", anchor="center", width=150, stretch="no")
        self.order_book_table.column("Entry Price", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Limit Price", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Trigger Price", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Reference Price", anchor="center", width=102, stretch="no")
        self.order_book_table.column("Trail Value", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Status", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Reason For Failed", anchor="center", width=282, stretch="no")
        self.order_book_table.column("Ladder ID", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Sequence ID", anchor="center", width=82, stretch="no")
        self.order_book_table.column("ATR Multiple", anchor="center", width=82, stretch="no")
        self.order_book_table.column("ATR", anchor="center", width=82, stretch="no")
        self.order_book_table.column("Bypass RM Check", anchor="center", width=112, stretch="no")
        self.order_book_table.column("Execution Engine", anchor="center", width=112, stretch="no")
        self.order_book_table.column("Limit IV", anchor="center", width=112, stretch="no")
        self.order_book_table.column("Trigger IV", anchor="center", width=112, stretch="no")
        self.order_book_table.column("Actual Entry Price", anchor="center", width=112, stretch="no")

        # Create Headings
        self.order_book_table.heading("#0", text="", anchor="w")
        self.order_book_table.heading("Unique ID", text="Unique ID", anchor="center")
        self.order_book_table.heading(
            "Account ID",
            text="Account ID",
            anchor="center",
        )
        self.order_book_table.heading("Tickers", text="Tickers", anchor="center")
        self.order_book_table.heading("Action", text="Action", anchor="center")
        self.order_book_table.heading("#Lots", text="#Lots", anchor="center")
        self.order_book_table.heading(
            "Order Type",
            text="Order Type",
            anchor="center",
        )
        self.order_book_table.heading(
            "Order Time",
            text="Order Time",
            anchor="center",
        )
        self.order_book_table.heading(
            "Last Update Time",
            text="Last Update Time",
            anchor="center",
        )
        self.order_book_table.heading(
            "Entry Price",
            text="Entry Price",
            anchor="center",
        )
        self.order_book_table.heading(
            "Limit Price",
            text="Limit Price",
            anchor="center",
        )
        self.order_book_table.heading(
            "Trigger Price",
            text="Trigger Price",
            anchor="center",
        )
        self.order_book_table.heading(
            "Reference Price",
            text="Reference Price",
            anchor="center",
        )
        self.order_book_table.heading(
            "Trail Value",
            text="Trail Value",
            anchor="center",
        )
        self.order_book_table.heading(
            "Status",
            text="Status",
            anchor="center",
        )
        self.order_book_table.heading(
            "Ladder ID",
            text="Ladder ID",
            anchor="center",
        )
        self.order_book_table.heading(
            "Sequence ID",
            text="Sequence ID",
            anchor="center",
        )
        self.order_book_table.heading(
            "ATR Multiple",
            text="ATR Multiple",
            anchor="center",
        )
        self.order_book_table.heading(
            "ATR",
            text="ATR",
            anchor="center",
        )
        self.order_book_table.heading(
            "Reason For Failed",
            text="Failure Reason",
            anchor="center",
        )

        self.order_book_table.heading(
            "Bypass RM Check",
            text="Bypass RM Check",
            anchor="center",
        )

        self.order_book_table.heading(
            "Execution Engine",
            text="Execution Engine",
            anchor="center",
        )

        self.order_book_table.heading(
            "Limit IV",
            text="Limit IV",
            anchor="center",
        )

        self.order_book_table.heading(
            "Trigger IV",
            text="Trigger IV",
            anchor="center",
        )

        self.order_book_table.heading(
            "Actual Entry Price",
            text="Actual Entry Price",
            anchor="center",
        )

        # Back ground
        self.order_book_table.tag_configure("oddrow", background="white")
        self.order_book_table.tag_configure("evenrow", background="lightblue")

        self.order_book_table.bind("<Button-3>", self.order_book_table_right_click)

    # Method to cancel selected order
    def cancel_selected_orders(self, delete_multiple_orders_button):
        # Get values of selected rows
        selected_items = self.order_book_table.selection()

        # Disable the button
        delete_multiple_orders_button.config(state="disabled")

        # Delete all selected combinations
        for selected_item in selected_items:
            try:
                self.cancel_order(
                    selected_item=selected_item, flag_cancel_from_order_table=True
                )
            except Exception as e:
                # Print to console
                if variables.flag_debug_mode:
                    print(f"Error in deleting multiple orders: {e}")

        delete_multiple_orders_button.config(state="normal")

    # Upload orders
    def upload_order_from_csv(self, upload_order_from_csv_button):

        # Disabled upload orders button
        upload_order_from_csv_button.config(state="disabled")

        # Get window to choose file from storage
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])

        if file_path:

            # Place orders based on values in CSV
            upload_order_thread = threading.Thread(
                target=upload_orders_from_csv_to_app,
                args=(
                    file_path,
                    upload_order_from_csv_button,
                ),
            )
            upload_order_thread.start()

        # Enabled upload orders button
        upload_order_from_csv_button.config(state="enabled")

    # Download orders
    def download_order_to_csv(self, download_orders_button):

        # Disabled download order button
        download_orders_button.config(state="disabled")

        download_order_thread = threading.Thread(
            target=self.download_order_to_csv_thread,
            args=(download_orders_button,),
        )

        download_order_thread.start()

    # Download orders using thread
    def download_order_to_csv_thread(self, download_orders_button):

        # Order Book Cleaned Time
        order_book_last_cleaned_time = get_order_book_cleaned_time()

        # Getting all the order from the active db.
        orders_dataframe = get_all_combinaiton_orders_from_db(
            order_book_last_cleaned_time
        )

        # Checking if dataframe is empty
        if orders_dataframe.empty:
            # Error Message

            error_title = error_string = f"Error - Orders dataframe is empty"
            variables.screen.display_error_popup(error_title, error_string)

            # Enabled download order button
            download_orders_button.config(state="enabled")

            return

        orders_dataframe_columns = copy.deepcopy(
            variables.columns_for_download_orders_to_csv
        )

        # Re- arranging columns in dataframe
        orders_dataframe = orders_dataframe.loc[:, orders_dataframe_columns]

        # Getting unique ids in current watchlist
        local_unique_id_list_of_selected_watchlist = copy.deepcopy(
            variables.unique_id_list_of_selected_watchlist
        )

        # Empty listt for unique ids in watchlist
        local_unique_id_list_of_selected_watchlist_list = []

        # Checking if unique ids list in watchlist is empty
        if local_unique_id_list_of_selected_watchlist == "None":

            # Error Message
            error_title = (
                error_string
            ) = f"Error - No Unique IDs in Watchlist to Download Orders"
            variables.screen.display_error_popup(error_title, error_string)

            # Enabled download order button
            download_orders_button.config(state="enabled")

            return

        # Checking if watchlist is not ALL watchlist
        elif local_unique_id_list_of_selected_watchlist != "ALL":
            try:
                # Convert string of unique id to list of unique id
                local_unique_id_list_of_selected_watchlist_list = [
                    int(float(unique_id))
                    for unique_id in local_unique_id_list_of_selected_watchlist.split(
                        ","
                    )
                ]

                # Filter dataframe based on unique ids present in watchlist
                orders_dataframe = orders_dataframe[
                    orders_dataframe["Unique ID"].isin(
                        local_unique_id_list_of_selected_watchlist_list
                    )
                ]

            except Exception as e:
                if variables.flag_debug_mode:

                    print(e)
                # Error Message
                error_title = (
                    error_string
                ) = f"Error - Filtering Orders Dataframe to Download Orders Failed"
                variables.screen.display_error_popup(error_title, error_string)

                # Enabled download order button
                download_orders_button.config(state="enabled")

                return


        elif local_unique_id_list_of_selected_watchlist == "ALL":

            # Get all unique ids in order dataframe
            local_unique_id_list_of_selected_watchlist_list = orders_dataframe[
                "Unique ID"
            ].to_list()

        all_unique_ids_in_system = orders_dataframe["Unique ID"].to_list()

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

        # Filter dataframe based on unique ids present in watchlist
        orders_dataframe = orders_dataframe[
            orders_dataframe["Account ID"].isin(all_account_ids_in_account_group)
        ]

        # Getting dictionary of combo objs
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

        # Dictionary for mapping unique id to ticker string
        local_unique_id_to_ticker_string = {}

        # Get ticker string for unique ids
        for unique_id in local_unique_id_list_of_selected_watchlist_list:

            # Combo_object
            combination_obj = local_unique_id_to_combo_obj[unique_id]

            # Getting Ticker string
            local_unique_id_to_ticker_string[unique_id] = make_informative_combo_string(
                combination_obj
            )

        # TODO - tickers while downloading the order - On Hold
        # Getting values for ticker column
        # tickers_column_values = [local_unique_id_to_ticker_string[unique_id] for unique_id in orders_dataframe['Unique ID'].to_list()]

        # Insert the new column at index 2
        # orders_dataframe.insert(1, 'Tickers', tickers_column_values)

        # Open a file dialog to choose the save location and filename
        file_path = filedialog.asksaveasfilename(defaultextension=".csv")

        # Check if a file path was selected
        if file_path:

            # Save the DataFrame as a CSV file
            orders_dataframe.to_csv(file_path, index=False)

        # Enabled download order button
        download_orders_button.config(state="enabled")

    # Method to clear order book table
    def clear_order_book_table(self):
        # Remove all the entries
        # Move From DB to archive DB

        # Get all combo order Flled, remove combo from table based on ordertime,
        all_cancelled_or_filled_combo_order = get_all_cancelled_or_filled_combo_order()

        # update the theme of table,
        if len(all_cancelled_or_filled_combo_order) > 0:

            # Removing cleared orders from watchlist orders book dataframe
            variables.orders_book_table_dataframe = (
                variables.orders_book_table_dataframe.loc[
                    ~variables.orders_book_table_dataframe["Order Time"].isin(
                        all_cancelled_or_filled_combo_order
                    )
                ]
            )

            # Remove these orders from the order book
            self.remove_row_from_order_book(all_cancelled_or_filled_combo_order)

            # update the view
            self.update_tables_after_combo_deleted()

        # Update the `Order Book Cleaned Time` in metadata table
        current_time_order_book_cleaned = datetime.datetime.now(
            variables.target_timezone_obj
        )

        # Update the `Order Book Cleaned Time`
        update_order_book_cleaned_time(current_time_order_book_cleaned)

    # Method to define order book rgiht click options
    def order_book_table_right_click(self, event):
        # get the Treeview row that was clicked
        row = self.order_book_table.identify_row(event.y)

        if row:
            # select the row
            self.order_book_table.selection_set(row)



            # create a context menu
            menu = tk.Menu(self.order_book_table, tearoff=0)



            menu.add_command(
                label="Cancel Order",
                command=lambda: self.cancel_order(flag_cancel_from_order_table=True),
            )
            menu.add_command(
                label="View Details",
                command=lambda: self.display_combination_details("order_book"),
            )
            menu.add_command(
                label="Duplicate Order",
                command=lambda: self.duplicate_close_flip_order(
                    action_from_order_book="Duplicate"
                ),
            )
            menu.add_command(
                label="Close Order",
                command=lambda: self.duplicate_close_flip_order(
                    action_from_order_book="Close"
                ),
            )
            menu.add_command(
                label="Flip Order",
                command=lambda: self.duplicate_close_flip_order(
                    action_from_order_book="Flip"
                ),
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)


    # Method to duplicate order
    def duplicate_close_flip_order(self, action_from_order_book=None):

        # get Order time of selected row
        selected_item = self.order_book_table.selection()[
            0
        ]  # get the item ID of the selected row

        # Get values of slected order
        values = self.order_book_table.item(
            selected_item, "values"
        )  # get the values of the selected row

        # Get unique id
        unique_id = int(float(values[0]))
        # Get action
        buy_sell_action = values[3]

        order_type = values[5]

        if 'Volatility' in order_type:
            # Error Message
            error_title = "Error, Volatility orders cannot be duplicated, closed, flipped"
            error_string = (
                "Error, Volatility orders cannot be duplicated, closed, flipped"
            )

            error_string = make_multiline_mssg_for_gui_popup(error_string)

            variables.screen.display_error_popup(error_title, error_string)

            return

        # For close and flip order, reverse action of selected order
        if action_from_order_book in ["Close", "Flip"]:

            # If action of selected order is BUY
            if buy_sell_action == "BUY":

                buy_sell_action = "Sell"

            # If action of selected order is SELL
            else:

                buy_sell_action = "Buy"

        # Define title for op up window
        pop_up_title = f"{buy_sell_action} combination, {action_from_order_book} Order, Combination Unique ID: {unique_id}"

        # Make action in upper case
        buy_sell_action = buy_sell_action.upper()

        # Create pop up with pre filled values
        self.create_trade_popup(
            buy_sell_action,
            unique_id,
            popup_title=pop_up_title,
            action_from_order_book=action_from_order_book,
            values_from_order_book_row=values,
        )

    # Cancel the Selected Order if Possible Else Throw eror
    def cancel_order(
        self,
        selected_item=None,
        flag_cancel_from_order_table=False,
        updated_status=None,
        reason_for_failed=None,
    ):

        if selected_item == None:
            selected_item = self.order_book_table.selection()[
                0
            ]  # get the item ID of the selected row

        values = self.order_book_table.item(
            selected_item, "values"
        )  # get the values of the selected row

        unique_id = values[0]
        status = values[13]
        account_id = values[1]

        try:
            # Get ladder id
            ladder_id = values[15]

            # Check if ladder id is not None
            if ladder_id != "None":

                ladder_id = int(float(ladder_id))

            # Check if flag of cancel from order table is true and ladder id is not none
            if (
                flag_cancel_from_order_table
                and ladder_id != "None"
                and status == "Pending"
            ):

                # Pause ladder for which order has been cancelled
                variables.screen.screen_scale_trader_obj.pause_scale_trade(
                    selected_item=ladder_id
                )
        except Exception as e:

            if variables.flag_debug_mode:

                print(
                    f"For Unique ID: {unique_id},Exception happened inside cancel order, Exp: {e}"
                )

        order_time = values[6]
        entry_price = values[8]
        reference_price = values[11]

        last_update_time = datetime.datetime.now(variables.target_timezone_obj)

        # Checking if account id is present in current session accounts
        if (
            account_id not in variables.current_session_accounts
            and updated_status != "Failed"
        ):

            # error pop up
            error_title, error_string = (
                "Can't Cancel Order",
                "Only the order of account ID present in current session can be Cancelled.",
            )
            self.display_error_popup(error_title, error_string)

            return

        # If order Status is not pending Throw error window
        if status != "Pending":
            error_title, error_string = (
                "Can't Cancel Order",
                "Only the pending orders can be Cancelled.",
            )
            self.display_error_popup(error_title, error_string)
        else:

            # Check if updated status is none
            if updated_status == None:

                updated_status = "Cancelled"

            # Update the Status in Order Book
            self.update_combo_order_status_in_order_book(
                order_time,
                last_update_time,
                entry_price,
                reference_price,
                updated_status,
                reason_for_failed=reason_for_failed,
            )

            # Mark this order cancelled
            mark_pending_combo_order_cancelled(
                unique_id,
                order_time,
                status,
                last_update_time,
                updated_status,
                reason_for_failed=reason_for_failed,
            )

    # Method to insert order status in order book table
    def insert_combo_order_status_order_book(self, value):

        # Order Time
        order_time = value[6]

        # Get the current number of items in the treeview
        num_items = len(self.order_book_table.get_children())

        if num_items % 2 == 1:
            self.order_book_table.insert(
                "",
                "end",
                iid=order_time,
                text=num_items + 1,
                values=value,
                tags=("oddrow",),
            )
        else:
            self.order_book_table.insert(
                "",
                "end",
                iid=order_time,
                text=num_items + 1,
                values=value,
                tags=("evenrow",),
            )

    # Method to update order book datafrmae
    def update_order_book_dataframe_as_order_book_table_updates(
        self,
        order_time,
        last_update_time,
        entry_price,
        reference_price,
        status,
        lots=None,
        exit_type=None,
        trigger_price=None,
        flag_only_update_status=False,
        reason_for_failed=None,
            actual_entry_price=None
    ):

        # 2023-06-28 06:27:11.413006-04:00 2023-06-28 06:27:14.023308-04:00 220637.5 None Filled None None None      False
        # If we update dataframe we will only need to do it here and we can ignore every single thing

        # Converting Order Time to str
        variables.orders_book_table_dataframe[
            "Order Time"
        ] = variables.orders_book_table_dataframe["Order Time"].astype(str)

        # Formatting Price
        if entry_price not in ["None", ""]:
            if isinstance(entry_price, str):
                entry_price = entry_price.replace(",", "")
            entry_price = f"{float(entry_price):,.2f}"
        else:
            print(
                "Updating Entry Price values in oder book dataframe for watchlist changed",
                entry_price,
            )

        if reference_price not in ["None", ""]:
            if isinstance(reference_price, str):
                reference_price = reference_price.replace(",", "")
            reference_price = f"{float(reference_price):,.2f}"
        else:
            if variables.flag_debug_mode:
                print(
                    "Updating Reference Price values in oder book dataframe for watchlist changed",
                    reference_price,
                )

        order_time_in_table = [
            str(_) for _ in variables.orders_book_table_dataframe["Order Time"].tolist()
        ]

        if str(order_time) in order_time_in_table:

            if flag_only_update_status:
                # Update the value of status where the value of order time is valid
                variables.orders_book_table_dataframe.loc[
                    variables.orders_book_table_dataframe["Order Time"] == order_time,
                    "Status",
                ] = status


                return

            # only used for the Exit Orders
            if exit_type != None:
                # Update the value of action where the value of order time is valid
                variables.orders_book_table_dataframe.loc[
                    variables.orders_book_table_dataframe["Order Time"] == order_time,
                    "Action",
                ] = exit_type

            if lots != None:
                # Update the value of #Lots where the value of order time is valid
                variables.orders_book_table_dataframe.loc[
                    variables.orders_book_table_dataframe["Order Time"] == order_time,
                    "#Lots",
                ] = lots

            if trigger_price != None:
                # Update the value of trigger price where the value of order time is valid
                variables.orders_book_table_dataframe.loc[
                    variables.orders_book_table_dataframe["Order Time"] == order_time,
                    "Trigger Price",
                ] = f"{(trigger_price):,.2f}"

            if actual_entry_price != None:
                # Update the value of trigger price where the value of order time is valid
                variables.orders_book_table_dataframe.loc[
                    variables.orders_book_table_dataframe["Order Time"] == order_time,
                    "Actual Entry Price",
                ] = f"{(actual_entry_price):,.2f}"

            if reason_for_failed != None:

                # Update the value of trigger price where the value of order time is valid
                variables.orders_book_table_dataframe.loc[
                    variables.orders_book_table_dataframe["Order Time"] == order_time,
                    "Reason For Failed",
                ] = reason_for_failed

            variables.orders_book_table_dataframe.loc[
                variables.orders_book_table_dataframe["Order Time"] == order_time,
                ["Last Update Time", "Entry Price", "Reference Price", "Status"],
            ] = [last_update_time, entry_price, reference_price, status]

    # Method to update order status in order book table
    def update_combo_order_status_in_order_book(
        self,
        order_time,
        last_update_time,
        entry_price,
        reference_price,
        status,
        lots=None,
        exit_type=None,
        trigger_price=None,
        flag_only_update_status=False,
        reason_for_failed=None,
            actual_entry_price=None
    ):

        try:
            # If we update dataframe we will only need to do it here and we can ignore every single thing
            self.update_order_book_dataframe_as_order_book_table_updates(
                order_time,
                last_update_time,
                entry_price,
                reference_price,
                status,
                lots,
                exit_type,
                trigger_price,
                flag_only_update_status,
                reason_for_failed=reason_for_failed,
                actual_entry_price=actual_entry_price
            )
        except Exception as e:
            print(
                f"Error in updating order book for watchlist changed dataframe, is {e}"
            )

        # Formatting Price
        if entry_price not in ["None", ""]:
            if isinstance(entry_price, str):
                entry_price = entry_price.replace(",", "")
            entry_price = f"{float(entry_price):,.2f}"
        else:
            if variables.flag_debug_mode:
                print(
                    "Updating Combo Order Status In Order Book Entry Price", entry_price
                )

        if reference_price not in ["None", ""]:
            if isinstance(reference_price, str):
                reference_price = reference_price.replace(",", "")
            reference_price = f"{float(reference_price):,.2f}"
        else:
            if variables.flag_debug_mode:
                print(
                    "Updating Combo Order Status In Order Book Reference Price",
                    reference_price,
                )

        order_time_in_table = self.order_book_table.get_children()

        if str(order_time) in order_time_in_table:

            if flag_only_update_status:
                self.order_book_table.set(order_time, 13, status)
                return

            # only used for the Exit Orders
            if exit_type != None:
                pass  # self.order_book_table.set(order_time, 2, exit_type)
            if lots != None:
                self.order_book_table.set(order_time, 4, lots)
            if trigger_price != None:
                self.order_book_table.set(
                    order_time,
                    10,
                    f"{(trigger_price):,.2f}",
                )
            if reason_for_failed != None:

                self.order_book_table.set(order_time, 14, reason_for_failed)

            if actual_entry_price != None:
                self.order_book_table.set(order_time, 23, actual_entry_price)

            self.order_book_table.set(order_time, 7, last_update_time)
            self.order_book_table.set(order_time, 8, entry_price)
            self.order_book_table.set(order_time, 11, reference_price)
            self.order_book_table.set(order_time, 13, status)

    # Method to update order book table after watchlist changed
    def update_orders_book_table_watchlist_changed(self):

        # All the Unique IDs in the System
        # Get combo details dataframe

        # TODO
        local_orders_book_table_dataframe = copy.deepcopy(
            variables.orders_book_table_dataframe
        )

        # All the Unique IDs in the System
        all_unique_ids_in_system = local_orders_book_table_dataframe[
            "Unique ID"
        ].tolist()

        # all account ids in table
        all_account_ids_in_account_group = all_account_id_in_orders_book_table = [
            (self.order_book_table.item(_x)["values"][1])
            for _x in self.order_book_table.get_children()
        ]

        # All the rows in orders book Table
        all_unique_ids_in_watchlist = all_unique_id_in_orders_book_table = [
            int(self.order_book_table.item(_x)["values"][0])
            for _x in self.order_book_table.get_children()
        ]

        # If we want to update the table as watchlist changed
        if variables.flag_orders_book_table_watchlist_changed:
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
                    print(f"Error inside updating orders book table, {e}")

            try:
                # Get all the
                if variables.selected_account_group == "ALL":
                    all_account_ids_in_account_group = (
                        variables.current_session_accounts
                        + local_orders_book_table_dataframe["Account ID"].to_list()
                    )
                else:
                    all_account_ids_in_account_group = copy.deepcopy(
                        variables.account_ids_list_of_selected_acount_group
                    )

            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Error inside updating orders book table, {e}")

            # Setting it to False
            variables.flag_orders_book_table_watchlist_changed = False

        # Update the rows
        for i, row_val in local_orders_book_table_dataframe.iterrows():
            # Unique ID of row val
            unique_id = row_val["Unique ID"]
            order_time = row_val["Order Time"]
            order_quantity = row_val["#Lots"]
            order_action = row_val["Action"]
            account_id = row_val["Account ID"]

            # if unique id and account id is in selected groups
            if (
                unique_id in all_unique_ids_in_watchlist
                and account_id in all_account_ids_in_account_group
            ):

                # Convert row values to list
                row_val = list(row_val)

                # Convert row of values to tuple
                row_val = tuple(row_val)

                # If unique id and account id present in table
                if order_time in self.order_book_table.get_children():
                    # Update the row at once.
                    self.order_book_table.item(order_time, values=row_val)

                elif isinstance(order_time, str):

                    # Insert it in the table
                    self.order_book_table.insert(
                        "",
                        "end",
                        iid=order_time,
                        text="",
                        values=row_val,
                        tags=("oddrow",),
                    )
            else:
                # If this unique_id in orders book Table but not in watchlist delete it
                if order_time in self.order_book_table.get_children():
                    try:

                        self.order_book_table.delete(order_time)
                    except Exception as e:
                        pass

        try:
            # Filter out the dataframe such that the dataframe only consists of all the unique ids that are present in the watchlist, so sorting will be in correct order.
            local_orders_book_table_dataframe = local_orders_book_table_dataframe[
                local_orders_book_table_dataframe["Unique ID"].isin(
                    all_unique_ids_in_watchlist
                )
            ]
        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Error inside updating orders book table values, is {e}")

        # All the rows in orders book Table
        all_unique_id_in_orders_book_table = [
            int(self.order_book_table.item(_x)["values"][0])
            for _x in self.order_book_table.get_children()
        ]

        # all account ids in table
        all_account_id_in_orders_book_table = [
            (self.order_book_table.item(_x)["values"][1])
            for _x in self.order_book_table.get_children()
        ]

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in local_orders_book_table_dataframe.iterrows():

            # Unique_id
            unique_id = row["Unique ID"]
            order_time = row["Order Time"]
            account_id = row["Account ID"]

            # If unique_id in table and account id in table
            if order_time in self.order_book_table.get_children():

                self.order_book_table.move(order_time, "", counter_row)

                if counter_row % 2 == 0:

                    self.order_book_table.item(order_time, tags="evenrow")
                else:

                    self.order_book_table.item(order_time, tags="oddrow")

                # Increase row count
                counter_row += 1

    # Method to remove row from order book table
    def remove_row_from_order_book(self, values):

        order_times_in_order_book_table = self.order_book_table.get_children()

        for order_time in values:

            if order_time in order_times_in_order_book_table:

                self.order_book_table.delete(order_time)


if __name__ == "__main__":
    screen_gui_app = ScreenGUI()
    screen_gui_app.window.mainloop()
