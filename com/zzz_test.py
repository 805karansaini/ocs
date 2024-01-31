import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog


class YourApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Rules")

        self.trading_rules_tab = ttk.Frame(root)
        self.trading_rules_tab.pack(fill='both', expand=True)

        self.create_trading_rules_tab()

    def create_trading_rules_tab(self):
        # Create Frame for the description boxes
        description_frame = ttk.Frame(self.trading_rules_tab, padding=20)
        description_frame.pack(pady=20)

        # Description box for instrument
        self.instrument_description = tk.Text(description_frame, width=50, height=10, state='disabled')
        self.instrument_description.grid(row=0, column=0, padx=10, pady=5, rowspan=2)

        # Description box for config
        self.config_description = tk.Text(description_frame, width=50, height=10, state='disabled')
        self.config_description.grid(row=2, column=0, padx=10, pady=5, rowspan=2)

        # Create "Add" button
        add_button = ttk.Button(description_frame, text="Add", command=self.open_popup)
        add_button.grid(row=0, column=1, padx=5, pady=5, sticky='n')

    def open_popup(self):
        # Open a popup dialog for user input
        popup = tk.Toplevel(self.root)
        popup.title("Add Instrument")

        # Input fields
        tk.Label(popup, text="Ticker:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        tk.Label(popup, text="Sectype:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        tk.Label(popup, text="Currency:").grid(row=2, column=0, padx=5, pady=5, sticky='e')

        ticker_entry = ttk.Entry(popup)
        ticker_entry.grid(row=0, column=1, padx=5, pady=5)

        sectype_entry = ttk.Entry(popup)
        sectype_entry.grid(row=1, column=1, padx=5, pady=5)

        currency_entry = ttk.Entry(popup)
        currency_entry.grid(row=2, column=1, padx=5, pady=5)

        # Submit button
        submit_button = ttk.Button(popup, text="Add",
                                   command=lambda: self.add_instrument(ticker_entry.get(), sectype_entry.get(),
                                                                       currency_entry.get()))
        submit_button.grid(row=3, columnspan=2, pady=10)

    def add_instrument(self, ticker, sectype, currency):
        # Add instrument details to the instrument description box
        instrument_info = f"Ticker: {ticker}\nSectype: {sectype}\nCurrency: {currency}\n\n"
        self.instrument_description.config(state='normal')
        self.instrument_description.insert('end', instrument_info)
        self.instrument_description.config(state='disabled')


# Usage
root = tk.Tk()
app = YourApp(root)
root.mainloop()
