import asyncio
import configparser
import threading
import tkinter as tk
from tkinter import Scrollbar, messagebox, ttk

from option_combo_scanner.database.set_up_db import SetupDatabase
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.house_keeping import HouseKeepingGUI
from option_combo_scanner.gui.order_presets_tab_helper import OrderPresetHelper
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.contracts import (
    get_contract,
    get_contract_details_async,
)
from option_combo_scanner.strategy.order_preset import OrderPreset
from option_combo_scanner.strategy.utilities import StrategyUtils

# Read the config file
config = configparser.ConfigParser()
config.read("config.ini")

tws_config = config["TWS"]
ACCOUNT_ID = tws_config["account"]

# Name, Width, Heading
order_presets_table_columns_width = [
    ("Unique ID", 75, "Unique ID"),
    ("Ticker", 75, "Ticker"),
    ("Risk (%)", 75, "Risk (%)"),
    ("Risk (USD)", 75, "Risk (USD)"),
    ("NLV", 75, "NLV"),
    ("Entry Price", 75, "Entry Price"),
    ("TP1 Price", 75, "TP1 Price"),
    ("TP2 Price", 75, "TP2 Price"),
    ("SL1 Price", 75, "SL1 Price"),
    ("SL2 Price", 75, "SL2 Price"),
    ("Entry Qty", 75, "Entry Qty"),
    ("Status", 75, "Status"),
    ("Bid", 75, "Bid"),
    ("Ask", 75, "Ask"),
    ("Filled Entry Qty", 75, "  Filled \nEntry Qty"),
    ("Avg. Entry Price", 75, "  Average \nEntry Price"),
    ("Filled Exit Qty", 75, " Filled \nExit Qty"),
    ("Avg. Exit Price", 75, " Average \nExit Price"),
    ("PNL", 75, "PNL"),
    ("Failure Reason", 300, "Failure Reason"),
]


class OrderPresetTab:
    def __init__(self, tab) -> None:
        self.order_presets_tab = tab
        self.create_order_presets_tab()
        self.order_preset_helper: OrderPresetHelper = OrderPresetHelper(
            self.order_presets_table
        )

        # # Insert the preset orders in the preset order tab[table]
        # HouseKeepingGUI.dump_all_preset_order_in_preset_order_tab(
        #     self.order_preset_helper
        # )

    def create_order_presets_tab(self):
        # Create a frame for the user input fields
        input_frame = ttk.Frame(self.order_presets_tab, padding=20)
        input_frame.pack(fill="both", expand=True)

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

        # Create Treeview Frame for Order Presets
        order_presets_table_frame = ttk.Frame(self.order_presets_tab, padding=20)
        order_presets_table_frame.pack(pady=20)
        order_presets_table_frame.pack(fill="both", expand=True)

        # Place table fram in center
        order_presets_table_frame.place(relx=0.5, anchor=tk.CENTER)
        order_presets_table_frame.place(y=342, width=1484)

        # Treeview Scrollbar
        tree_scroll_y = Scrollbar(order_presets_table_frame)
        tree_scroll_y.pack(side="right", fill="y")

        # Treeview Scrollbar
        tree_scroll_x = Scrollbar(order_presets_table_frame, orient="horizontal")
        tree_scroll_x.pack(side="bottom", fill="x")

        # Create Treeview
        self.order_presets_table = ttk.Treeview(
            order_presets_table_frame,
            xscrollcommand=tree_scroll_x.set,
            yscrollcommand=tree_scroll_y.set,
            height=20,
            selectmode="extended",
        )
        # Pack to the screen
        self.order_presets_table.pack(expand=True, fill="both")

        # Configure the scrollbar
        tree_scroll_y.config(command=self.order_presets_table.yview)

        # Configure the scrollbar
        tree_scroll_x.config(command=self.order_presets_table.xview)

        # Define Columns
        self.order_presets_table["columns"] = [
            _[0] for _ in order_presets_table_columns_width
        ]

        # Format Column
        self.order_presets_table.column("#0", width=0, stretch="no")

        # Create Heading
        self.order_presets_table.heading("#0", text="\n", anchor="w")

        # Formate Columns and Create Heading for Columns
        for col_name, col_width, col_heading in order_presets_table_columns_width:
            self.order_presets_table.column(col_name, anchor="center", width=col_width)
            self.order_presets_table.heading(
                col_name, text=col_heading, anchor="center"
            )

        self.order_presets_table.tag_configure("oddrow", background="white")
        self.order_presets_table.tag_configure("evenrow", background="lightblue")

        self.order_presets_table.bind(
            "<Button-3>", self.order_presets_table_right_click_menu
        )

        # Add a button to create New Preset Order
        create_order_preset_button = ttk.Button(
            input_frame,
            text="  Create Preset Order  ",
            command=lambda: self.create_order_preset_popup(),
        )
        create_order_preset_button.grid(column=0, row=0, padx=5, pady=5)

        # Add a button to Cancel all Preset Order
        cancel_all_preset_orders_button = ttk.Button(
            input_frame,
            text="Cancel All Preset Order",
            command=lambda: threading.Thread(
                target=StrategyUtils.cancel_all_pending_preset_orders
            ).start(),
        )
        cancel_all_preset_orders_button.grid(column=1, row=0, padx=(5, 50), pady=5)

        # Place in center
        input_frame.place(relx=0.5, anchor=tk.CENTER)
        input_frame.place(y=30)

    def create_order_preset_popup(
        self,
    ):
        # Create a popup window with the table
        popup = tk.Toplevel()
        popup.title("Create Preset Order")
        custom_width = 450
        popup.geometry("350x" + str(custom_width))

        # Create a frame for the input fields
        input_frame = ttk.Frame(popup, padding=20)
        input_frame.pack(fill="both", expand=True)

        # Ticker Label
        ttk.Label(input_frame, text="Ticker", width=16, anchor="center").grid(
            column=0, row=0, padx=15, pady=5
        )

        ticker_entry = ttk.Entry(input_frame)
        ticker_entry.grid(column=0, row=1, padx=15, pady=5)

        # NLV Label
        ttk.Label(input_frame, text="NLV", width=16, anchor="center").grid(
            column=1, row=0, padx=15, pady=5
        )

        nlv_entry = ttk.Entry(input_frame)
        try:
            account_nlv = StrategyUtils.get_account_nlv()
            account_nlv = f"{account_nlv:,}"
        except Exception as exp:
            account_nlv = "N/A"
        nlv_entry.insert(0, f"{account_nlv}")
        nlv_entry.config(state="disabled", foreground="black")
        nlv_entry.grid(column=1, row=1, padx=15, pady=5)

        # Entry Price Label
        ttk.Label(input_frame, text="Entry Price", width=16, anchor="center").grid(
            column=0, row=3, padx=15, pady=5
        )

        entry_price_entry = ttk.Entry(input_frame)
        entry_price_entry.grid(column=0, row=4, padx=15, pady=5)

        # % Risk Label
        ttk.Label(input_frame, text="% Risk", width=16, anchor="center").grid(
            column=1, row=3, padx=15, pady=5
        )

        risk_percent_entry = ttk.Entry(input_frame)
        risk_percent_entry.grid(column=1, row=4, padx=15, pady=5)

        # TP1 Price Label
        ttk.Label(input_frame, text="TP1 Price", width=16, anchor="center").grid(
            column=0, row=5, padx=15, pady=5
        )

        tp1_price_entry = ttk.Entry(input_frame)
        tp1_price_entry.grid(column=0, row=6, padx=15, pady=5)

        # SL1 Price Label
        ttk.Label(input_frame, text="SL1 Price", width=16, anchor="center").grid(
            column=1, row=5, padx=15, pady=5
        )

        sl1_price_entry = ttk.Entry(input_frame)
        sl1_price_entry.grid(column=1, row=6, padx=15, pady=5)

        # TP2 Price Label
        ttk.Label(input_frame, text="TP2 Price", width=16, anchor="center").grid(
            column=0, row=7, padx=15, pady=5
        )

        tp2_price_entry = ttk.Entry(input_frame)
        tp2_price_entry.grid(column=0, row=8, padx=15, pady=5)

        # SL2 Price Label
        ttk.Label(input_frame, text="SL2 Price", width=16, anchor="center").grid(
            column=1, row=7, padx=15, pady=5
        )

        sl2_price_entry = ttk.Entry(input_frame)
        sl2_price_entry.grid(column=1, row=8, padx=15, pady=5)

        # Risk USD Label
        ttk.Label(input_frame, text="Risk (USD)", width=16, anchor="center").grid(
            column=0, row=10, padx=15, pady=5
        )

        risk_usd_entry = ttk.Entry(input_frame)
        risk_usd_entry.grid(column=0, row=11, padx=15, pady=5)
        risk_usd_entry.config(state="disabled", foreground="black")

        # Entry Qty Label
        ttk.Label(input_frame, text="Entry Qty", width=16, anchor="center").grid(
            column=1, row=10, padx=15, pady=5
        )

        entry_qty_entry = ttk.Entry(input_frame)
        entry_qty_entry.grid(column=1, row=11, padx=15, pady=5)
        entry_qty_entry.config(state="disabled", foreground="black")

        # Create the "Compute Risk and Entry Qty" button
        compute_risk_and_entry_qty_button = ttk.Button(
            input_frame,
            text="Compute Risk",
            command=lambda: self.compute_risk_and_entry_qty_button_clicked(
                risk_percent_entry,
                entry_price_entry,
                sl1_price_entry,
                risk_usd_entry,
                entry_qty_entry,
            ),
        ).grid(column=1, row=9, padx=15, pady=(20, 20))

        # Create a frame for the "Add Preset Order" button
        button_frame = ttk.Frame(popup)
        button_frame.place(relx=0.5, anchor=tk.CENTER)
        button_frame.place(y=custom_width - 50)

        # Create the "Add Presets Order" button
        add_preset_order_button = ttk.Button(
            button_frame,
            text="Add Preset Order",
            command=lambda: threading.Thread(
                target=self.validate_and_add_preset_order_button_clicked,
                args=(
                    add_preset_order_button,
                    popup,
                    ticker_entry,
                    nlv_entry,
                    entry_price_entry,
                    risk_percent_entry,
                    tp1_price_entry,
                    sl1_price_entry,
                    tp2_price_entry,
                    sl2_price_entry,
                ),
            ).start(),
        )
        add_preset_order_button.pack(side="right")

    def compute_risk_and_entry_qty_button_clicked(
        self,
        risk_percent_entry,
        entry_price_entry,
        sl1_price_entry,
        risk_usd_entry,
        entry_qty_entry,
    ):
        try:
            # Get the values from option_combo_scanner.the entry fields
            entry_price = float(entry_price_entry.get().strip())
            risk_percent = float(risk_percent_entry.get().strip())
            sl1_price = float(sl1_price_entry.get().strip())

            (
                apprx_entry_qty,
                apprx_risk_usd,
            ) = StrategyUtils.calculate_entry_qty_and_risk_dollar(
                risk_percent, entry_price, sl1_price
            )
            formatted_risk_usd = f"{apprx_risk_usd:,}"
            formatted_entry_qty = f"{apprx_entry_qty:,}"

            # Enable Entry Qty and Risk USD
            risk_usd_entry.config(state="normal", foreground="black")
            entry_qty_entry.config(state="normal", foreground="black")

            # Clear the entry fields and insert the values
            risk_usd_entry.delete(0, tk.END)
            risk_usd_entry.insert(0, formatted_risk_usd)
            entry_qty_entry.delete(0, tk.END)
            entry_qty_entry.insert(0, formatted_entry_qty)

            # Disable Entry Qty and Risk USD
            risk_usd_entry.config(state="disabled", foreground="black")
            entry_qty_entry.config(state="disabled", foreground="black")

        except Exception as exp:
            Utils.display_message_popup(
                "Error",
                "Could not compute Risk USD and Entry Qty. Please check the values entered.",
            )
            return

    def validate_and_add_preset_order_button_clicked(
        self,
        add_preset_order_button,
        popup,
        ticker_entry,
        nlv_entry,
        entry_price_entry,
        risk_percent_entry,
        tp1_price_entry,
        sl1_price_entry,
        tp2_price_entry,
        sl2_price_entry,
    ):
        # Disable the button
        add_preset_order_button.config(state="disabled")

        # Get the values from option_combo_scanner.the entry fields
        ticker = ticker_entry.get().strip().upper()
        nlv = nlv_entry.get().strip().upper().replace(",", "")
        entry_price = entry_price_entry.get().strip().upper()
        risk_percent = risk_percent_entry.get().strip().upper()
        tp1_price = tp1_price_entry.get().strip().upper()
        sl1_price = sl1_price_entry.get().strip().upper()
        tp2_price = tp2_price_entry.get().strip().upper()
        sl2_price = sl2_price_entry.get().strip().upper()

        # If input valid: True else: False
        is_inputs_valid = self.order_preset_helper.validate_preset_order_inputs(
            ticker,
            nlv,
            entry_price,
            risk_percent,
            tp1_price,
            sl1_price,
            tp2_price,
            sl2_price,
        )

        # If not valid, enable the button and return
        if not is_inputs_valid:
            # Enable the button
            add_preset_order_button.config(state="enabled")
            return

        # Validate if the ticker is valid
        stk_contract = get_contract(
            symbol=ticker, sec_type="STK", currency="USD", exchange="SMART"
        )
        contract_details = asyncio.run(get_contract_details_async(stk_contract))

        if contract_details is None:
            # Show popup tell user contract can not be found please check the ticker
            Utils.display_message_popup(
                "Error",
                "Contract not found, please check the ticker",
            )

            # Enable the button
            add_preset_order_button.config(state="enabled")
            return
        else:
            contract = contract_details.contract
            conid = contract.conId

        # Values Dict
        values_dict = {}
        values_dict["AccountID"] = ACCOUNT_ID
        values_dict["Ticker"] = ticker
        values_dict["SecType"] = "STK"
        values_dict["Currency"] = "USD"
        values_dict["Exchange"] = "SMART"
        values_dict["Conid"] = conid
        values_dict["RiskPercentage"] = risk_percent
        values_dict["NetLiquidationValue"] = nlv
        values_dict["EntryPrice"] = entry_price
        values_dict["TP1Price"] = tp1_price
        values_dict["SL1Price"] = sl1_price
        values_dict["TP2Price"] = tp2_price
        values_dict["SL2Price"] = sl2_price
        values_dict["Status"] = "Pending"
        values_dict["EntryQuantityFilled"] = 0
        values_dict["AverageEntryPrice"] = 0
        values_dict["ExitQuantityFilled"] = 0
        values_dict["AverageExitPrice"] = 0
        values_dict["PNL"] = 0
        values_dict["EntryOrderID"] = None
        values_dict["FlagEntryOrderSent"] = False
        values_dict["FlagExitOrderSent"] = False
        values_dict["FailureReason"] = ""

        # Get the values from option_combo_scanner.the entry fields
        entry_price = float(entry_price_entry.get().strip())
        risk_percent = float(risk_percent_entry.get().strip())
        sl1_price = float(sl1_price_entry.get().strip())

        (
            apprx_entry_qty,
            apprx_risk_usd,
        ) = StrategyUtils.calculate_entry_qty_and_risk_dollar(
            risk_percent, entry_price, sl1_price
        )
        values_dict["EntryQuantity"] = apprx_entry_qty
        values_dict["RiskDollar"] = apprx_risk_usd

        # Insert the order preset in the DB.
        result, unique_id = SqlQueries.insert_order_preset(values_dict=values_dict)

        if result:
            unique_id = int(unique_id)
            values_dict["UniqueID"] = unique_id

            # Add the row to the table.
            self.order_preset_helper.add_order_preset_to_table(values_dict)

            # Create OrderPreset Object and Manage Conid, contract, Subscription
            OrderPreset(values_dict, contract)

            # Destory the popup
            popup.destroy()

    def order_presets_table_right_click_menu(self, event):
        # get the Treeview row that was clicked
        row = self.order_presets_table.identify_row(event.y)
        if row:
            # select the row
            self.order_presets_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.order_presets_table, tearoff=0)
            menu.add_command(
                label="Cancel Preset Order",
                command=lambda: self.cancel_selected_preset_order(),
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    def update_order_preset_table(self, order_preset_table_values_df):
        # Update the row in the table.
        self.order_preset_helper.update_order_preset_table(order_preset_table_values_df)

    def cancel_selected_preset_order(
        self,
    ):
        # Unique ID
        unique_id = self.order_presets_table.selection()[
            0
        ]  # get the item ID of the selected row

        values = self.order_presets_table.item(
            unique_id, "values"
        )  # get the values of the selected row

        unique_id = int(unique_id)

        # Cancel only if the order is pending
        if values[11] == "Pending":
            StrategyUtils.cancel_pending_preset_order(unique_id)

        else:
            Utils.display_message_popup(
                "Error",
                "Only pending orders can be cancelled",
            )
