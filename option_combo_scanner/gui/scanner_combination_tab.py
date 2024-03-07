import copy
import datetime
import pprint
import tkinter as tk
from tkinter import Scrollbar, messagebox, ttk

import pandas as pd

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.house_keeping import HouseKeepingGUI
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.strategy.scanner import Scanner
from option_combo_scanner.strategy.scanner_combination import get_scanner_combination_details_column_and_data_from_combo_object
from option_combo_scanner.strategy.strategy_variables import StrategyVariables

logger = CustomLogger.logger

# Name, Width, Heading
scanner_combination_table_columns_width = [
    ("Combo ID", 220, "Combo ID"),
    ("Instrument ID", 220, "Instrument ID"),
    ("Description",220, "Description"),
    ("#Legs", 220, "#Legs"),
    ("Combo Net  Delta", 220, "Combo Net Delta"),    
    ("Max Profit", 220, "Max Profit"),
    ("Max Loss", 220, "Max Loss"),
    # ("Max Profit/Loss Ratio", 200, "Max Profit/Loss Ratio"),
]


class ScannerCombinationTab:
    def __init__(self, scanner_combination_tab_frame):
        self.scanner_combination_tab_frame = scanner_combination_tab_frame
        self.create_scanner_combination_tab()

        # Dumping all the combinations in the GUI and system
        HouseKeepingGUI.dump_all_scanner_combinations_in_scanner_combination_tab(self)
        
        # Set the scanner_combination_tab in the class variables
        Scanner.scanner_combination_tab_obj = self

        # Set the scanner_combination_tab in the gui/Utils class variables
        Utils.scanner_combination_tab_object = self

    def create_scanner_combination_tab(self):

        # Create Treeview Frame for active Filter DropDown
        scanner_filter_frame = ttk.Frame(self.scanner_combination_tab_frame, padding=20)
        scanner_filter_frame.pack(pady=20)

        # Label for filter used in max profit        
        filter_label_max_profit = ttk.Label(scanner_filter_frame, text="Filter Max Profit", anchor="center", width=14)
        filter_label_max_profit.grid(column=0, row=0, padx=5, pady=(0, 5), sticky="n")

        # Filter Dropdown for Max Profit 
        self.filter_max_profit_var = tk.StringVar()
        self.filter_dropdown_max_profit = ttk.Combobox(scanner_filter_frame, textvariable=self.filter_max_profit_var, values=["Limited", "Unlimited", "All"],
                                      state="readonly")
        self.filter_dropdown_max_profit.current(2)
        self.filter_dropdown_max_profit.grid(column=0, row=1, padx=5, pady=5)

        # Bind Filter function Based on MAx Profit
        self.filter_dropdown_max_profit.bind("<<ComboboxSelected>>", self.filter_combo_based_on_max_loss_and_max_profit)

        # Label for filter used in max loss        
        filter_label_max_loss = ttk.Label(scanner_filter_frame, text="Filter Max Loss", anchor="center", width=13)
        filter_label_max_loss.grid(column=1, row=0, padx=5, pady=(0, 5), sticky="n")

        # Filter Dropdown for Max Loss 
        self.filter_max_loss_var = tk.StringVar()
        self.filter_dropdown_max_loss = ttk.Combobox(scanner_filter_frame, textvariable=self.filter_max_loss_var, values=["Limited", "Unlimited", "All"],
                                      state="readonly")
        self.filter_dropdown_max_loss.current(2)
        self.filter_dropdown_max_loss.grid(column=1, row=1, padx=5, pady=5)

        # Bind Filter function Based on MAx Loss
        self.filter_dropdown_max_loss.bind("<<ComboboxSelected>>", self.filter_combo_based_on_max_loss_and_max_profit)

        # Place in center for filter frame
        scanner_filter_frame.place(relx=0.5, anchor=tk.CENTER)
        scanner_filter_frame.place(y=30)

        # Create Treeview Frame for active combo table
        scanner_combination_table_frame = ttk.Frame(self.scanner_combination_tab_frame, padding=20)
        scanner_combination_table_frame.pack(pady=20)

        # Place in center
        scanner_combination_table_frame.place(relx=0.5, anchor=tk.CENTER)
        scanner_combination_table_frame.place(y=425, width = 1590)

        # Treeview Scrollbar
        tree_scroll_y = Scrollbar(scanner_combination_table_frame)
        tree_scroll_y.pack(side="right", fill="y")

        tree_scroll_x = Scrollbar(scanner_combination_table_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        # Create Treeview
        self.scanner_combination_table = ttk.Treeview(
            scanner_combination_table_frame,
            xscrollcommand=tree_scroll_x.set,
            yscrollcommand=tree_scroll_y.set,
            height=25,
            selectmode="extended",
        )
        # Pack to the screen
        self.scanner_combination_table.pack(expand=True, fill="both")

        # Configure the scrollbar
        tree_scroll_y.config(command=self.scanner_combination_table.yview)
        tree_scroll_x.config(command=self.scanner_combination_table.xview)

        # Column in Combination table
        self.scanner_combination_table["columns"] = [
            _[0] for _ in scanner_combination_table_columns_width
        ]

        # Creating Columns
        self.scanner_combination_table.column("#0", width=0, stretch="no")
        # Create Headings
        self.scanner_combination_table.heading("#0", text="\n", anchor="w")

        for col_name, col_width, col_heading in scanner_combination_table_columns_width:
            self.scanner_combination_table.column(col_name, anchor="center", width=col_width, minwidth=col_width, stretch=False)
            self.scanner_combination_table.heading(col_name, text=col_heading, anchor="center")

        # Back ground
        self.scanner_combination_table.tag_configure("oddrow", background="white")
        self.scanner_combination_table.tag_configure("evenrow", background="lightblue")

        self.scanner_combination_table.bind(
            "<Button-3>", self.scanner_combination_table_right_click_menu
        )

        # Bind the sort_treeview function to the TreeviewColumnHeader event for each column
        for column in self.scanner_combination_table["columns"]:
            self.scanner_combination_table.heading(
                column, command=lambda c=column: self.sort_scanner_combination_table(c, False)
            )

    def filter_combo_based_on_max_loss_and_max_profit(self, event=None):
        # Get the selected value from the dropdown
        max_loss_selected_option = self.filter_max_loss_var.get().upper()
        
        # Get the selected value from the dropdown
        max_profit_selected_option = self.filter_max_profit_var.get().upper()

        local_scanner_combo_table_df = copy.deepcopy(StrategyVariables.scanner_combo_table_df)

        # print(f"\nRaw")
        # print(local_scanner_combo_table_df.to_string())
        # Filter dataframe here
        if max_profit_selected_option == "UNLIMITED":
            # Filter for cases where max loss is within the specified range
            local_scanner_combo_table_df = local_scanner_combo_table_df[
                local_scanner_combo_table_df['Max Profit'] == float('inf')
            ]
        elif max_profit_selected_option == "LIMITED":
            # Filter for cases where max loss is within the specified range
            local_scanner_combo_table_df = local_scanner_combo_table_df[
                local_scanner_combo_table_df['Max Profit'] != float('inf')
            ]
        else:
            pass
        # print(f"\nMax Profit")
        # print(local_scanner_combo_table_df.to_string())


        # Filter dataframe here
        if max_loss_selected_option == "UNLIMITED":
            # Filter for cases where max loss is within the specified range
            local_scanner_combo_table_df = local_scanner_combo_table_df[
                local_scanner_combo_table_df['Max Loss'] == float('-inf')
            ]
        elif max_loss_selected_option == "LIMITED":
            # Filter for cases where max loss is within the specified range
            local_scanner_combo_table_df = local_scanner_combo_table_df[
                local_scanner_combo_table_df['Max Loss'] != float('-inf')
            ]
        else:
            pass
        
        # print(f"\nMax Loss")
        # print(local_scanner_combo_table_df.to_string())

        # Clear table
        self.scanner_combination_table.delete(*self.scanner_combination_table.get_children())

        list_of_all_filtered_combo_ids =  local_scanner_combo_table_df["Combo ID"].to_list()

        # Sort the dataframe according to the header # TODO
        for combo_id in list_of_all_filtered_combo_ids:
            combo_id = int(combo_id)
            scanner_combination_object = StrategyVariables.map_combo_id_to_scanner_combination_object[combo_id]
            self.insert_combination_in_scanner_combination_table_gui(scanner_combination_object)


    # def clear_order_book_table(self):
    #     # Set FlagPurged = 1 for all Filled or Cancelled orders
    #     data = {"FlagPurged": 1}
    #     where_clause = "WHERE OrderStatus = 'Filled' OR OrderStatus = 'Cancelled' OR OrderStatus = 'Inactive'"
    #     SqlQueries.update_orders(data, where_clause=where_clause)
    
    def insert_combination_in_scanner_combination_table_gui(self, scanner_combination_object):
        """
        # Name, Width, Heading
        scanner_combination_table_columns_width = [
            ("Combo ID", 119, "Combo ID"),
            ("Instrument ID", 119, "Instrument ID"),
            ("Description", 119, "Description"),
            ("#Legs", 119, "#Legs"),
            ("Combo Net  Delta", 119, "Combo Net Delta"),    
        ]

        """
        combo_id = scanner_combination_object.combo_id
        
        row_values = (
            combo_id,
            scanner_combination_object.instrument_id,
            scanner_combination_object.description,
            scanner_combination_object.number_of_legs,
            scanner_combination_object.combo_net_delta,
            scanner_combination_object.max_profit,
            scanner_combination_object.max_loss,
            # scanner_combination_object.max_profit_max_loss_ratio
        )

        # Get the current number of items in the treeview
        num_items = len(self.scanner_combination_table.get_children())

        if num_items % 2 == 1:
            self.scanner_combination_table.insert(
                "",
                "end",
                iid=combo_id,
                text=num_items + 1,
                values=row_values,
                tags=("oddrow",),
            )
        else:
            self.scanner_combination_table.insert(
                "",
                "end",
                iid=combo_id,
                text=num_items + 1,
                values=row_values,
                tags=("evenrow",),
            )

    def remove_row_from_scanner_combination_table(self, list_of_combo_ids):
        combo_ids_in_scanner_combination_table = self.scanner_combination_table.get_children()

        for combo_id in list_of_combo_ids:
            # Remove the scanned combination from system 
            if int(combo_id) in StrategyVariables.map_combo_id_to_scanner_combination_object:
                StrategyVariables.map_combo_id_to_scanner_combination_object[int(combo_id)].remove_scanned_combo_from_system()

            combo_id = str(combo_id)
            if combo_id in combo_ids_in_scanner_combination_table:
                self.scanner_combination_table.delete(combo_id)
    
    # Right click menu, view details, show legs
    def scanner_combination_table_right_click_menu(self, event):
        # get the Treeview row that was clicked
        row = self.scanner_combination_table.identify_row(event.y)
        if row:
            # select the row
            self.scanner_combination_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.scanner_combination_table, tearoff=0)
            menu.add_command(
                label="View Details",
                command=lambda: self.display_scanner_combination_details(),
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    # Method to display scanner combination details
    def display_scanner_combination_details(self,):
        
        try:
                
            # Get the combo_id from table
            combo_id = self.scanner_combination_table.selection()[0]
            combo_id = int(combo_id)
        except Exception as e:
            print(f"Could not get the combo_id value: {combo_id} ")
            return
        
        # Title for the Scanned Combintation Details
        title = f"Scanned Combintation Details, Combo ID : {combo_id}"

        
        columns, row_data_list = get_scanner_combination_details_column_and_data_from_combo_object(combo_id)

        if (row_data_list is None or columns is None):
            return
    
        # DISPLAY DETAILS of combo
        Utils.display_treeview_popup(title, columns, row_data_list)

    # def refresh_scanner_combination_table(self):

    #     self.x 
        
    #     # Move According to data Color here, Change Color
    #     for i, row in scanner_combo_df.iterrows():

    #         # Unique_id
    #         unique_id = str(row["Unique ID"])

    #         # If unique_id in table
    #         if unique_id in all_unique_id_in_cas_table:
    #             self.cas_table.move(unique_id, "", counter_row)

    #             if counter_row % 2 == 0:
    #                 self.cas_table.item(unique_id, tags="evenrow")
    #             else:
    #                 self.cas_table.item(unique_id, tags="oddrow")

    #             # Increase row count
    #             counter_row += 1

    # function to sort the scanner combo table
        
    def sort_scanner_combination_table(self, column, reverse):

        data = [
            (self.scanner_combination_table.set(child, column), child)
            for child in self.scanner_combination_table.get_children("")
        ]
        data = sorted(data, key=lambda val: Utils.custom_sort(val[0]), reverse=reverse)

        for counter_row, (_, unique_id) in enumerate(data):
            self.scanner_combination_table.move(unique_id, "", counter_row)

            if counter_row % 2 == 0:
                self.scanner_combination_table.item(unique_id, tags="evenrow")
            else:
                self.scanner_combination_table.item(unique_id, tags="oddrow")

        # Change the reverse flag
        self.scanner_combination_table.heading(
            column, command=lambda: self.sort_scanner_combination_table(column, not reverse)
        )

        # Change the Reverse Flag in variables Dict
        StrategyVariables.scanner_combination_table_sort_by_column = {column: reverse}