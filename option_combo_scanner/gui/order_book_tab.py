import datetime
import pprint
import tkinter as tk
from tkinter import Scrollbar, messagebox, ttk

import pandas as pd

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.sql_queries import SqlQueries

logger = CustomLogger.logger

# Name, Width, Heading
order_book_table_columns_width = [
    ("OrderID", 119, "Order ID"),
    ("UniqueID", 119, "Unique ID"),
    ("Ticker", 119, "Ticker"),
    ("Action", 119, "Action"),
    ("OrderQuantity", 119, "Quantity"),
    ("OrderType", 119, "Order Type"),
    ("OrderTime", 119, "Order Time"),
    ("LastUpdateTime", 119, "Last Update Time"),
    ("OrderPrice", 119, "Order Price"),
    ("FilledQuantity", 118, "Filled Quantity"),
    ("AverageFillPrice", 118, "Average Fill Price"),
    ("OrderStatus", 118, "Status"),
]


class OrderBookTab:
    def __init__(self, order_book_tab):
        self.order_book_tab = order_book_tab
        self.create_order_book_tab()

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

        clean_table_button.grid(column=1, row=0, padx=5, pady=5)

        # Place in center
        order_book_clean_table_frame.place(relx=0.5, anchor=tk.CENTER)
        order_book_clean_table_frame.place(y=30)

        # Create Treeview Frame for active combo table
        order_book_table_frame = ttk.Frame(self.order_book_tab, padding=20)
        order_book_table_frame.pack(pady=20)

        # Place in center
        order_book_table_frame.place(relx=0.5, anchor=tk.CENTER)
        order_book_table_frame.place(y=335)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(order_book_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview
        self.order_book_table = ttk.Treeview(
            order_book_table_frame,
            yscrollcommand=tree_scroll.set,
            height=20,
            selectmode="extended",
        )
        # Pack to the screen
        self.order_book_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.order_book_table.yview)

        # Column in order book table
        self.order_book_table["columns"] = [
            _[0] for _ in order_book_table_columns_width
        ]

        # Creating Columns
        self.order_book_table.column("#0", width=0, stretch="no")
        # Create Headings
        self.order_book_table.heading("#0", text="\n", anchor="w")

        for col_name, col_width, col_heading in order_book_table_columns_width:
            self.order_book_table.column(col_name, anchor="center", width=col_width)
            self.order_book_table.heading(col_name, text=col_heading, anchor="center")

        # Back ground
        self.order_book_table.tag_configure("oddrow", background="white")
        self.order_book_table.tag_configure("evenrow", background="lightblue")

    def clear_order_book_table(self):
        # Set FlagPurged = 1 for all Filled or Cancelled orders
        data = {"FlagPurged": 1}
        where_clause = "WHERE OrderStatus = 'Filled' OR OrderStatus = 'Cancelled' OR OrderStatus = 'Inactive'"
        SqlQueries.update_orders(data, where_clause=where_clause)

    def insert_order_preset_status_order_book(self, value_dict):
        # OrderID
        order_id = value_dict.get("OrderID", "N/A")
        row_values = (
            value_dict.get("OrderID", "N/A"),
            value_dict.get("UniqueID", "N/A"),
            value_dict.get("Ticker", "N/A"),
            value_dict.get("Action", "N/A"),
            value_dict.get("Quantity", "N/A"),
            value_dict.get("OrderType", "N/A"),
            value_dict.get("OrderTime", "N/A"),
            value_dict.get("LastUpdateTime", "N/A"),
            value_dict.get("OrderPrice", "N/A"),
            value_dict.get("FilledQuantity", "N/A"),
            value_dict.get("AverageFillPrice", "N/A"),
            value_dict.get("Status", "N/A"),
        )

        # Get the current number of items in the treeview
        num_items = len(self.order_book_table.get_children())

        if num_items % 2 == 1:
            self.order_book_table.insert(
                "",
                "end",
                iid=order_id,
                text=num_items + 1,
                values=row_values,
                tags=("oddrow",),
            )
        else:
            self.order_book_table.insert(
                "",
                "end",
                iid=order_id,
                text=num_items + 1,
                values=row_values,
                tags=("evenrow",),
            )

    def update_order_book_table(
        self,
    ):
        where_clause = " WHERE FlagPurged = 0"
        # Get all the orders from option_combo_scanner.database.
        all_orders_dict = SqlQueries.get_orders(columns="*", where_clause=where_clause)

        # Columns Header
        columns_header = [x[0] for x in order_book_table_columns_width]

        # Format OrderQuantity, OrderPrice, FilledQuantity, AverageFillPrice with commas and 2 decimal places
        for i, order in enumerate(all_orders_dict):
            try:
                order_qty = float(all_orders_dict[i]["OrderQuantity"])
                all_orders_dict[i]["OrderQuantity"] = f"{order_qty:,}"
            except Exception as e:
                logger.error(f"Exception in formatting OrderQuantity: {order_qty} {e}")

            try:
                order_price = float(all_orders_dict[i]["OrderPrice"])
                all_orders_dict[i]["OrderPrice"] = f"{order_price:,.2f}"
            except Exception as e:
                logger.error(f"Exception in formatting OrderPrice: {order_price}  {e}")

            try:
                filled_qty = int(float(all_orders_dict[i]["FilledQuantity"]))
                all_orders_dict[i]["FilledQuantity"] = f"{filled_qty:,}"
            except Exception as e:
                logger.error(
                    f"Exception in formatting FilledQuantity: {filled_qty} {e}"
                )

            try:
                avg_price = float(all_orders_dict[i]["AverageFillPrice"])
                all_orders_dict[i]["AverageFillPrice"] = f"{avg_price:,.2f}"
            except Exception as e:
                logger.error(
                    f"Exception in formatting AverageFillPrice: {avg_price} {e}"
                )

        # create dataframe from option_combo_scanner.the orders
        all_orders_df = pd.DataFrame(all_orders_dict, columns=columns_header)

        # All the rows in Order Preset Table
        order_id_in_order_preset_table = self.order_book_table.get_children()

        # All order id from option_combo_scanner.database
        set_of_all_order_ids_from_db = set()

        # Update the rows
        for i, row_val in all_orders_df.iterrows():
            # Unique ID of row val
            order_id = row_val["OrderID"]

            # Add to list
            set_of_all_order_ids_from_db.add(str(order_id))

            # Tuple of vals
            row_val = tuple(all_orders_df.iloc[i])

            # If this order_id in Table update the values
            if str(order_id) in order_id_in_order_preset_table:
                # Update the row at once.
                self.order_book_table.item(order_id, values=row_val)
            else:
                # Row Values
                values_dict = all_orders_dict[i]
                try:
                    # Insert the row
                    self.insert_order_preset_status_order_book(values_dict)
                except Exception as e:
                    logger.error(
                        f"Exception in inserting dict value in the order book: {e}  Values: {values_dict}"
                    )

        # Remove the rows which are not in database
        values_to_remove = (
            set(order_id_in_order_preset_table) - set_of_all_order_ids_from_db
        )

        # Remove the rows
        self.remove_row_from_order_book(values_to_remove)

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in all_orders_df.iterrows():
            # OrderId
            order_id = str(row["OrderID"])

            # If order_id in table
            if order_id in order_id_in_order_preset_table:
                self.order_book_table.move(order_id, "", counter_row)

                if counter_row % 2 == 0:
                    self.order_book_table.item(order_id, tags="evenrow")
                else:
                    self.order_book_table.item(order_id, tags="oddrow")

                # Increase row count
                counter_row += 1

    def remove_row_from_order_book(self, values):
        order_times_in_order_book_table = self.order_book_table.get_children()

        for order_id in values:
            if order_id in order_times_in_order_book_table:
                self.order_book_table.delete(order_id)
