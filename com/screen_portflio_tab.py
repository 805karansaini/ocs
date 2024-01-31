import copy

import numpy as np
import pandas as pd

from com.variables import *
from com.mysql_io_portfolio_tab import *
from com.upload_combo_to_application import create_combo_wrapper
from com.utilities import get_values_for_new_combo


# Method to check if value is float or not
def is_float(value):
    try:
        # Check if the value can be converted to a float
        float_value = float(value)

        # Return true if no exception occured
        return True

    except Exception as e:

        # Return false if value cannot be converted to float
        return False

# Class for accounts tab
class ScreenPortfolio(object):
    def __init__(self, master_notebook):
        """
        Constructor
        """
        self.notebook = master_notebook

        # Create portfolio tab
        self.portfolio_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.portfolio_tab, text="  Portfolio  ")

        # Method to create portfolio tab GUI components
        self.create_portfolio_tab()

    # Method to get updated lots and entry price
    def get_temp_lots_entry_price_list(self, temp_lots, temp_entry_price_list, temp_lots_list, current_lots):

        # Init
        current_lots = abs(current_lots)

        new_entry_price_list = []

        new_lots_list = []



        index = 0

        # Based on new order update old lots and entry price list
        while current_lots > 0:

            if temp_lots > temp_lots_list[index]:

                lots = temp_lots_list[index]

            else:

                lots = temp_lots

            new_entry_price_list.append(temp_entry_price_list[index])

            new_lots_list.append(lots)

            current_lots -= temp_lots_list[index]

            index += 1

        return new_entry_price_list, new_lots_list

    # Method to update lots and entry price list
    def update_temp_lots_entry_price_list(self, temp_lots, temp_entry_price_list, temp_lots_list):


        # Init
        temp_lots = abs(temp_lots)

        new_entry_price_list = []

        new_lots_list = []

        temp_entry_price_list = temp_entry_price_list[::-1]

        temp_lots_list = temp_lots_list[::-1]

        index = 0

        # Blcok to calculate updated lots and entry prices
        while temp_lots > 0:

            if temp_lots > temp_lots_list[index]:

                lots = temp_lots_list[index]

            else:

                lots = temp_lots

            new_entry_price_list.append(temp_entry_price_list[index])

            new_lots_list.append(lots)

            temp_lots -= temp_lots_list[index]

            index += 1

        return  new_entry_price_list, new_lots_list

    # Method to create GUI for portfolio tab
    def create_portfolio_tab(self):

        # Create Treeview Frame for portfolio instances
        portfolio_table_frame = ttk.Frame(self.portfolio_tab, padding=10)
        portfolio_table_frame.pack(pady=10)

        # Create Treeview Frame for portfolio instances
        portfolio_table_legs_frame = ttk.Frame(self.portfolio_tab, padding=10)
        portfolio_table_legs_frame.pack(pady=10)

        portfolio_table_legs_frame.place_forget()
        portfolio_table_legs_frame.pack_forget()

        # Place in center
        portfolio_table_frame.place(relx=0.5, anchor=tk.N)
        portfolio_table_frame.place(y=50)

        # Create Treeview Frame for portfolio instances
        buttons_frame = ttk.Frame(self.portfolio_tab, padding=0)
        buttons_frame.pack(pady=0)

        # Add labels for each column in the table
        ttk.Label(
            buttons_frame,
            text="Select Table :",
            width=16,
            anchor="center",
        ).grid(column=0, row=0, padx=5, pady=5)

        # add table name
        table_list = ['Combination Table', 'Legs Table']

        table_combo_box = ttk.Combobox(
            buttons_frame, width=18, values=table_list, state="readonly", style="Custom.TCombobox",
        )
        table_combo_box.current(0)


        # Place add custom column button
        table_combo_box.grid(row=0, column=1, padx=5, pady=5)



        # Initialize button to add portfolio combo
        portfolio_combo_button = ttk.Button(
            buttons_frame,
            text="Add Portfolio Combo",
            command=lambda: self.display_portfolio_combo_gui_pop_up(),
        )

        # Place delete custom column button
        portfolio_combo_button.grid(row=0, column=3, padx=(10,10), pady=10)

        ttk.Separator(buttons_frame, orient=tk.VERTICAL).grid(
            column=2, row=0, rowspan=1, sticky="ns", padx=30
        )

        # Add labels for each column in the table
        ttk.Label(
            buttons_frame,
            text="Show Zero Position :",
            width=18,
            anchor="center",
        ).grid(column=5, row=0, padx=5, pady=5)

        # add table name
        zero_position_options_list = ['Yes', 'No']

        def on_combobox_select(event):
            selected_item = self.zero_position_options_combo_box.get()  # Get the selected item

            self.update_portfolio_combo_table(flag_delete=True)

            self.update_portfolio_legs_table(flag_delete=True)

        self.zero_position_options_combo_box = ttk.Combobox(
            buttons_frame, width=18, values=zero_position_options_list, state="readonly", style="Custom.TCombobox",
        )
        self.zero_position_options_combo_box.current(0)

        # Place add custom column button
        self.zero_position_options_combo_box.grid(row=0, column=6, padx=5, pady=5)

        # Bind the function to the <<ComboboxSelected>> event
        self.zero_position_options_combo_box.bind("<<ComboboxSelected>>", on_combobox_select)

        ttk.Separator(buttons_frame, orient=tk.VERTICAL).grid(
            column=4, row=0, rowspan=1, sticky="ns", padx=30
        )

        # Place in center
        buttons_frame.place(relx=0.5, anchor=tk.N)
        buttons_frame.place(y=10)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(portfolio_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview Table
        self.portfolio_table = ttk.Treeview(
            portfolio_table_frame,
            yscrollcommand=tree_scroll.set,
            height=27,
            selectmode="extended",
        )

        # Pack to the screen
        self.portfolio_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.portfolio_table.yview)

        # Get columns for portfolio table
        portfolio_table_columns = copy.deepcopy(variables.portfolio_table_combo_columns)

        # Set columns for portfolio table
        self.portfolio_table["columns"] = portfolio_table_columns

        # Creating Column
        self.portfolio_table.column("#0", width=0, stretch="no")

        # Creating columns for portfolio table
        for column_name in portfolio_table_columns:
            self.portfolio_table.column(column_name, anchor="center", width=195)

        # Create Heading
        self.portfolio_table.heading("#0", text="", anchor="w")

        # Create headings for portfolio table
        for column_name in portfolio_table_columns:
            self.portfolio_table.heading(column_name, text=column_name, anchor="center")

        # Back ground for rows in table
        self.portfolio_table.tag_configure("oddrow", background="white")
        self.portfolio_table.tag_configure("evenrow", background="lightblue")

        # Treeview Scrollbar
        tree_scroll = Scrollbar(portfolio_table_legs_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview Table
        self.portfolio_legs_table = ttk.Treeview(
            portfolio_table_legs_frame,
            yscrollcommand=tree_scroll.set,
            height=27,
            selectmode="extended",
        )

        # Pack to the screen
        self.portfolio_legs_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.portfolio_legs_table.yview)

        # Get columns for portfolio table
        portfolio_table_columns = copy.deepcopy(variables.portfolio_table_legs_columns)

        # Set columns for portfolio table
        self.portfolio_legs_table["columns"] = portfolio_table_columns + ['Table ID']

        # Creating Column
        self.portfolio_legs_table.column("#0", width=0, stretch="no")

        # Creating columns for portfolio table
        for column_name in portfolio_table_columns:
            self.portfolio_legs_table.column(column_name, anchor="center", width=260)

        self.portfolio_legs_table.column('Table ID',width=0, stretch="no")

        # Create Heading
        self.portfolio_legs_table.heading("#0", text="", anchor="w")

        # Create headings for portfolio table
        for column_name in portfolio_table_columns:
            self.portfolio_legs_table.heading(column_name, text=column_name, anchor="center")

        self.portfolio_legs_table.heading('Table ID', text='Table ID', anchor="center")

        # Back ground for rows in table
        self.portfolio_legs_table.tag_configure("oddrow", background="white")
        self.portfolio_legs_table.tag_configure("evenrow", background="lightblue")


        def toggle_table_method(event):


            if table_combo_box.get().strip() == 'Combination Table':
                # Place in center
                portfolio_table_frame.place(relx=0.5, anchor=tk.N)
                portfolio_table_frame.place(y=50)

                portfolio_table_legs_frame.pack_forget()
                portfolio_table_legs_frame.place_forget()


            else:

                # Place in center
                portfolio_table_legs_frame.place(relx=0.5, anchor=tk.N)
                portfolio_table_legs_frame.place(y=50)

                portfolio_table_frame.pack_forget()
                portfolio_table_frame.place_forget()

        # on select method for dropdown
        table_combo_box.bind("<<ComboboxSelected>>", toggle_table_method)

        #self.portfolio_table.bind("<Button-3>", self.portfolio_table_right_click)

        # update portfolio table
        self.update_portfolio_combo_table()

    # Method to add portfolio combo
    def display_portfolio_combo_gui_pop_up(self):

        # Create a add portfolio combo popup window
        portfolio_combo_popup = tk.Toplevel()
        portfolio_combo_popup.title('Add Portfolio Combo')



        portfolio_combo_popup.geometry("360x120")

        # enter_legs_popup.geometry("450x520")

        # Create main frame
        portfolio_combo_popup_frame = ttk.Frame(portfolio_combo_popup, padding=5)
        portfolio_combo_popup_frame.pack(fill="both", expand=True)

        # Create a frame for the input fields
        portfolio_combo_popup_frame = ttk.Frame(portfolio_combo_popup_frame, padding=0)
        portfolio_combo_popup_frame.pack(side=tk.TOP, pady=5)



        # Add a label
        ttk.Label(portfolio_combo_popup_frame, text="Select Account ID :").grid(
            column=0, row=0, padx=15, pady=15
        )

        account_id_values = variables.current_session_accounts

        # Create the combo box
        account_id_combo_box = ttk.Combobox(
            portfolio_combo_popup_frame,
            width=18,
            values=account_id_values,
            state="readonly",
            style="Custom.TCombobox",
        )
        account_id_combo_box.current(0)
        account_id_combo_box.grid(column=1, row=0, padx=15, pady=15)

        def add_portfolio_combo():

            # Init
            account_id = account_id_combo_box.get().strip()

            local_legs_df = self.legs_df.copy()

            list_of_tuple_of_values = []

            local_map_con_id_to_contract = copy.deepcopy(variables.map_con_id_to_contract)

            # Get all legs
            for indx, row in local_legs_df.iterrows():

                account_id_in_row = row['Account ID']

                quantity = row['#Net Position']


                # Check if position is zero
                if float(quantity) == 0:

                    continue

                # check if account is right
                if account_id != account_id_in_row:

                    continue

                con_id = row['ConId']

                leg_obj = local_map_con_id_to_contract[con_id]


                # Decide leg action
                action = 'BUY'

                if float(quantity) < 0:

                    action = 'SELL'

                quantity = abs(float(quantity))

                # GEt leg's values
                leg_values_list = [variables.unique_id, action, leg_obj.secType, leg_obj.symbol, 'None', 'None', leg_obj.right, quantity, leg_obj.multiplier, leg_obj.exchange,
                                   leg_obj.tradingClass, leg_obj.currency, leg_obj.conId, leg_obj.primaryExchange, leg_obj.strike, leg_obj.lastTradeDateOrContractMonth]

                list_of_tuple_of_values.append(tuple(leg_values_list))

            # Create combo obj
            combo_obj, unique_id_added = create_combo_wrapper(list_of_tuple_of_values, 0,
                False,
                False,
            )

            # Create a thread and pass the result_queue as an argument
            new_combo_values_thread = threading.Thread(
                target=get_values_for_new_combo,
                args=(
                    [combo_obj],
                    [unique_id_added],
                ),
            )

            # Start the thread
            new_combo_values_thread.start()

            portfolio_combo_popup.destroy()

        # Initialize button to add portfolio combo
        portfolio_combo_button = ttk.Button(
            portfolio_combo_popup_frame,
            text="Add Portfolio Combo",
            command=lambda: add_portfolio_combo(),
        )

        # Place delete custom column button
        portfolio_combo_button.grid(row=1, column=0, padx=15, pady=15, columnspan=3)

    # Method to calcualte pnl and entry price for combo
    def calculate_pnl_entry_price(self, local_position_table):

        try:

            # init
            final_entry_price_list = []

            unrealized_pnl_list = []

            realized_pnl_list = []

            # iterate rows in table
            for indx, row in local_position_table.iterrows():


                # get values from row
                unique_id = row['Unique ID']

                account_id = row['Account ID']


                # get orders from db
                df = get_orders_for_combo(unique_id, account_id)


                # check if df is empty
                if df.empty:

                    # append 0 in all resultant lists
                    final_entry_price_list.append(0)

                    unrealized_pnl_list.append(0)

                    realized_pnl_list.append(0)

                    continue


                # get net position
                net_position = row['#Net Position']


                # get list of values of orders
                entry_price_list = df['Actual Entry Price'].to_list()

                lots_list = df['#Lots'].to_list()

                action_list = df['Action'].to_list()

                # Init
                lots_process_list = []

                entry_price_process_list = []

                action_process_list = []


                # check if net position is greater than 0
                if float(net_position) > 0:

                    # save lots and entry prices for getting entry price for combination
                    for entry_price, lots, action in zip(entry_price_list, lots_list, action_list):

                        if action == 'BUY' and lots.isnumeric() and is_float(entry_price):
                            action_process_list.append('BUY')
                            lots_process_list.append(lots)
                            entry_price_process_list.append(entry_price)


                # check if net position is less than 0
                elif float(net_position) < 0:

                    # save lots and entry prices for getting entry price for combination
                    for entry_price, lots, action in zip(entry_price_list, lots_list, action_list):

                        if action == 'SELL' and lots.isnumeric() and is_float(entry_price):
                            action_process_list.append('SELL')
                            lots_process_list.append(lots)
                            entry_price_process_list.append(entry_price)
                else:

                    # append 0 in all resultant lists
                    '''final_entry_price_list.append(0)

                    unrealized_pnl_list.append(0)

                    realized_pnl_list.append(0)

                    continue'''

                    # save lots and entry prices for getting entry price for combination
                    for entry_price, lots, action in zip(entry_price_list, lots_list, action_list):

                        if lots.isnumeric() and is_float(entry_price):
                            action_process_list.append(action)
                            lots_process_list.append(lots)
                            entry_price_process_list.append(entry_price)

                # Init
                temp_lots = 0

                temp_price = 0

                realized_pnl = 0

                temp_entry_price_list = []

                temp_lots_list = []

                flag_first = True

                # code to calculate relaized PNL
                for entry_price, lots, action in zip(entry_price_list, lots_list, action_list):

                    # convert to int and float
                    lots = int(lots)

                    entry_price = float(entry_price)

                    # for first iteration
                    if flag_first:

                        temp_lots += (int(lots) * (1 if action == 'BUY' else -1))

                        temp_price = float(entry_price)

                        temp_entry_price_list.append(float(entry_price))

                        temp_lots_list.append(abs(lots))

                        flag_first = False

                    else:

                        if temp_entry_price_list != []:
                            #temp_price = sum(temp_entry_price_list) / len(temp_entry_price_list)



                            # Calculating weighted average
                            temp_price = np.sum(np.array(temp_entry_price_list) * np.array(temp_lots_list)) / np.sum(np.array(temp_lots_list))


                            '''if int(unique_id) == 2:
                                print('weighted average calcualtion - ')
                                print([temp_entry_price_list, temp_lots_list, temp_price])'''






                        # get lots with sign (+/-)
                        lots = (int(lots) * (1 if action == 'BUY' else -1))

                        # in case of + accumulated lots and sell order lots
                        if temp_lots > 0 and lots < 0 and abs(temp_lots) > abs(lots):

                            temp_lots += lots

                            new_temp_price_list, new_lots_list = self.get_temp_lots_entry_price_list(temp_lots, temp_entry_price_list, temp_lots_list, lots)

                            #print([new_temp_price_list, new_lots_list])

                            # Calculating weighted average
                            temp_price = np.sum(np.array(new_temp_price_list) * np.array(new_lots_list)) / np.sum(
                                np.array(new_lots_list))

                            realized_pnl += abs(lots) * (float(entry_price) - temp_price)



                            '''if int(unique_id) == 2:


                                print([temp_price, entry_price, realized_pnl])'''

                            temp_entry_price_list, temp_lots_list = self.update_temp_lots_entry_price_list(temp_lots, temp_entry_price_list, temp_lots_list)

                            # realized_pnl += lots * (float(entry_price) - temp_price)

                        # in case of + accumulated lots and sell order lots
                        elif temp_lots > 0 and lots < 0 and abs(temp_lots) <= abs(lots):

                            #print([temp_entry_price_list, temp_lots_list])

                            realized_pnl += abs(temp_lots) * ((float(entry_price) - temp_price))

                            '''if int(unique_id) == 2:
                                print([temp_price, entry_price, realized_pnl])'''

                            temp_lots += lots

                            temp_price = float(entry_price)

                            temp_entry_price_list = []

                            temp_entry_price_list.append(float(entry_price))

                            temp_lots_list = []

                            temp_lots_list.append(abs(lots))

                        # in case of - accumulated lots and buy order lots
                        elif temp_lots < 0 and lots > 0 and abs(temp_lots) > abs(lots):

                            temp_lots += lots

                            new_temp_price_list, new_lots_list = self.get_temp_lots_entry_price_list(temp_lots,
                                                                                                     temp_entry_price_list,
                                                                                                     temp_lots_list,
                                                                                                     lots)

                            #print([new_temp_price_list, new_lots_list])

                            # Calculating weighted average
                            temp_price = np.sum(np.array(new_temp_price_list) * np.array(new_lots_list)) / np.sum(
                                np.array(new_lots_list))

                            realized_pnl += abs(lots) * (temp_price - float(entry_price))

                            temp_entry_price_list, temp_lots_list = self.update_temp_lots_entry_price_list(temp_lots,
                                                                                                           temp_entry_price_list,
                                                                                                           temp_lots_list)

                        # in case of - accumulated lots and buy order lots
                        elif temp_lots < 0 and lots > 0 and abs(temp_lots) <= abs(lots):

                            #print([temp_entry_price_list, temp_lots_list])

                            realized_pnl += abs(temp_lots) * (temp_price - float(entry_price))

                            temp_lots += lots

                            temp_price = float(entry_price)

                            temp_entry_price_list = []

                            temp_entry_price_list.append(float(entry_price))

                            temp_lots_list = []

                            temp_lots_list.append(abs(lots))

                        else:

                            temp_lots += lots

                            temp_entry_price_list.append(float(entry_price))

                            temp_lots_list.append(abs(lots))


                # round up realized pnl value
                realized_pnl = round(realized_pnl, 2)

                # append it to list
                realized_pnl_list.append(realized_pnl)


                # Init
                entry_price_list = []

                lots_list = []

                unrealized_pnl = 0


                # get current price
                try:
                    current_price_unique_id = variables.unique_id_to_prices_dict[unique_id]

                    current_buy_price, current_sell_price = (
                        current_price_unique_id["BUY"],
                        current_price_unique_id["SELL"],
                    )

                    current_price = (current_buy_price + current_sell_price) / 2

                except Exception as e:

                    current_price = None


                # calcualte entry price for combo
                if entry_price_process_list != []:

                    # get net position
                    position_counter = abs(int(net_position))

                    # set index
                    index = len(entry_price_process_list) - 1


                    # check if counter is greater than 0
                    while position_counter > 0:

                        # entry price append
                        entry_price_list.append(entry_price_process_list[index])

                        # lots append
                        if position_counter >= int(lots_process_list[index]):

                            lots_list.append(lots_process_list[index])

                        else:

                            lots_list.append(position_counter)

                        # if current price is none
                        if current_price == None:

                            unrealized_pnl += 0

                        # if current price is not none
                        else:

                            if action_process_list[index] in 'BUY':

                                '''if int(unique_id) == 6:

                                    print([current_price, entry_price_list[-1]])'''

                                #if current_price > 0 and float(entry_price_list[-1]) > 0:

                                unrealized_pnl += float(lots_list[-1]) * (
                                            current_price - float(entry_price_list[-1]))


                                '''elif current_price < 0 and float(entry_price_list[-1]) < 0:

                                    unrealized_pnl += float(lots_list[-1]) * (
                                            float(entry_price_list[-1]) - current_price)

                                elif current_price < 0 and float(entry_price_list[-1]) > 0:
                                    unrealized_pnl += float(lots_list[-1]) * (
                                            float(entry_price_list[-1]) - current_price)


                                else:


                                    unrealized_pnl += float(lots_list[-1]) * (current_price - float(
                                        entry_price_list[-1]))'''


                            else:

                                '''if int(unique_id) == 4:

                                    print([current_price, entry_price_list[-1]])'''

                                #if current_price > 0 and float(entry_price_list[-1]) > 0:


                                unrealized_pnl += float(lots_list[-1]) * ( float(entry_price_list[-1]) - current_price )

                                '''elif current_price < 0 and float(entry_price_list[-1]) < 0:



                                    unrealized_pnl += float(lots_list[-1]) * (
                                                float(entry_price_list[-1]) - current_price)

                                elif current_price < 0 and float(entry_price_list[-1]) > 0:

                                    unrealized_pnl += float(lots_list[-1]) * (current_price - float(
                                        entry_price_list[-1]))

                                else:

                                    unrealized_pnl += float(lots_list[-1]) * (
                                                float(entry_price_list[-1]) - current_price)'''

                        # update counter
                        position_counter -= int(lots_process_list[index])

                        # update index
                        index -= 1




                    # update unrealized pnl
                    unrealized_pnl_list.append(round(unrealized_pnl, 2))

                    # calculate entry price
                    if entry_price_list != []:

                        # Convert the entire list to float values
                        entry_price_list = [float(value) for value in entry_price_list]

                        lots_list = [float(value) for value in lots_list]

                        #print([entry_price_list,lots_list])

                        # Calculating weighted average
                        weighted_average = round(np.sum(np.array(entry_price_list) * np.array(lots_list)) / np.sum(np.array(lots_list)), 2)

                        # append entry price
                        final_entry_price_list.append(weighted_average)

                    else:



                        final_entry_price_list.append(0)



            return final_entry_price_list, unrealized_pnl_list, realized_pnl_list

        except Exception as e:
            print('here 2')
            print(e)

    # Method to calculate pnl and entry prices
    def calculate_pnl_entry_price_for_legs_table(self, local_legs_table):

        try:

            # init
            final_entry_price_list = []

            unrealized_pnl_list = []

            realized_pnl_list = []

            # iterate rows in table
            for indx, row in local_legs_table.iterrows():


                con_id = row['ConId']

                account_id = row['Account ID']

                # get orders from db
                df = get_orders_for_legs(con_id, account_id)

                # check if df is empty
                if df.empty:
                    # append 0 in all resultant lists
                    final_entry_price_list.append(0)

                    unrealized_pnl_list.append(0)

                    realized_pnl_list.append(0)

                    continue

                # get net position
                net_position = row['#Net Position']

                # get list of values of orders
                entry_price_list = df['Avg Fill Price'].to_list()

                lots_list = df['Target Fill'].to_list()

                action_list = df['Order Action'].to_list()



                # Init
                lots_process_list = []

                entry_price_process_list = []

                action_process_list = []

                # check if net position is greater than 0
                if float(net_position) > 0:

                    # save lots and entry prices for getting entry price for combination
                    for entry_price, lots, action in zip(entry_price_list, lots_list, action_list):

                        if action == 'BUY' and lots.isnumeric() and is_float(entry_price):
                            action_process_list.append('BUY')
                            lots_process_list.append(lots)
                            entry_price_process_list.append(entry_price)


                # check if net position is less than 0
                elif float(net_position) < 0:

                    # save lots and entry prices for getting entry price for combination
                    for entry_price, lots, action in zip(entry_price_list, lots_list, action_list):

                        if action == 'SELL' and lots.isnumeric() and is_float(entry_price):
                            action_process_list.append('SELL')
                            lots_process_list.append(lots)
                            entry_price_process_list.append(entry_price)
                else:

                    # append 0 in all resultant lists
                    '''final_entry_price_list.append(0)

                    unrealized_pnl_list.append(0)

                    realized_pnl_list.append(0)

                    continue'''
                    # save lots and entry prices for getting entry price for combination
                    for entry_price, lots, action in zip(entry_price_list, lots_list, action_list):

                        if lots.isnumeric() and is_float(entry_price):
                            action_process_list.append(action)
                            lots_process_list.append(lots)
                            entry_price_process_list.append(entry_price)




                # Init
                temp_lots = 0

                temp_price = 0

                realized_pnl = 0

                temp_entry_price_list = []

                temp_lots_list = []

                flag_first = True

                # code to calculate relaized PNL
                for entry_price, lots, action in zip(entry_price_list, lots_list, action_list):

                    # convert to int and float
                    lots = int(lots)

                    entry_price = float(entry_price)

                    # for first iteration
                    if flag_first:

                        temp_lots += (int(lots) * (1 if action == 'BUY' else -1))

                        temp_price = float(entry_price)

                        temp_entry_price_list.append(float(entry_price))

                        temp_lots_list.append(abs(lots))
                        flag_first = False

                    else:

                        if temp_entry_price_list != []:
                            # temp_price = sum(temp_entry_price_list) / len(temp_entry_price_list)

                            # Calculating weighted average
                            temp_price = round(
                                np.sum(np.array(temp_entry_price_list) * np.array(temp_entry_price_list)) / np.sum(
                                    np.array(temp_entry_price_list)),
                                2)

                        # get lots with sign (+/-)
                        lots = (int(lots) * (1 if action == 'BUY' else -1))

                        # in case of + accumulated lots and sell order lots
                        if temp_lots > 0 and lots < 0 and abs(temp_lots) > abs(lots):

                            temp_lots += lots

                            new_temp_price_list, new_lots_list = self.get_temp_lots_entry_price_list(temp_lots,
                                                                                                     temp_entry_price_list,
                                                                                                     temp_lots_list,
                                                                                                     lots)

                            # Calculating weighted average
                            temp_price = np.sum(np.array(new_temp_price_list) * np.array(new_lots_list)) / np.sum(
                                np.array(new_lots_list))

                            realized_pnl += abs(lots) * (float(entry_price) - temp_price)



                            temp_entry_price_list, temp_lots_list = self.update_temp_lots_entry_price_list(temp_lots,
                                                                                                           temp_entry_price_list,
                                                                                                           temp_lots_list)

                            # realized_pnl += lots * (float(entry_price) - temp_price)

                        # in case of + accumulated lots and sell order lots
                        elif temp_lots > 0 and lots < 0 and abs(temp_lots) <= abs(lots):

                            realized_pnl += abs(temp_lots) * ((float(entry_price) - temp_price))



                            temp_lots += lots

                            temp_price = float(entry_price)

                            temp_entry_price_list = []

                            temp_entry_price_list.append(float(entry_price))

                            temp_lots_list = []

                            temp_lots_list.append(abs(lots))

                        # in case of - accumulated lots and buy order lots
                        elif temp_lots < 0 and lots > 0 and abs(temp_lots) > abs(lots):

                            temp_lots += lots

                            new_temp_price_list, new_lots_list = self.get_temp_lots_entry_price_list(temp_lots,
                                                                                                     temp_entry_price_list,
                                                                                                     temp_lots_list,
                                                                                                     lots)

                            # Calculating weighted average
                            temp_price = np.sum(np.array(new_temp_price_list) * np.array(new_lots_list)) / np.sum(
                                np.array(new_lots_list))

                            realized_pnl += abs(lots) * (temp_price - float(entry_price))

                            temp_entry_price_list, temp_lots_list = self.update_temp_lots_entry_price_list(temp_lots,
                                                                                                           temp_entry_price_list,
                                                                                                           temp_lots_list)

                        # in case of - accumulated lots and buy order lots
                        elif temp_lots < 0 and lots > 0 and abs(temp_lots) <= abs(lots):

                            realized_pnl += abs(temp_lots) * (temp_price - float(entry_price))

                            temp_lots += lots

                            temp_price = float(entry_price)

                            temp_entry_price_list = []

                            temp_entry_price_list.append(float(entry_price))

                            temp_lots_list = []

                            temp_lots_list.append(abs(lots))

                        else:

                            temp_lots += lots

                            temp_entry_price_list.append(float(entry_price))

                            temp_lots_list.append(abs(lots))




                #print('*************************')
                # round up realized pnl value
                realized_pnl = round(realized_pnl, 2)



                # append it to list
                realized_pnl_list.append(realized_pnl)

                # Init
                entry_price_list = []

                lots_list = []

                unrealized_pnl = 0

                # get current price
                try:
                    req_id = variables.con_id_to_req_id_dict[con_id]
                    bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]
                    current_price = (ask + bid) / 2



                except Exception as e:

                    current_price = None



                # calcualte entry price for combo
                if entry_price_process_list != []:

                    # get net position
                    position_counter = abs(int(net_position))

                    # set index
                    index = len(entry_price_process_list) - 1

                    # check if counter is greater than 0
                    while position_counter > 0:

                        if index < 0:

                            break

                        # entry price append
                        entry_price_list.append(entry_price_process_list[index])

                        # lots append
                        if position_counter >= int(lots_process_list[index]):

                            lots_list.append(lots_process_list[index])

                        else:

                            lots_list.append(position_counter)



                        # if current price is none
                        if current_price == None:

                            unrealized_pnl += 0

                        # if current price is not none
                        else:



                            if action_process_list[index] in 'BUY':

                                unrealized_pnl += float(lots_list[-1]) * (current_price - float(entry_price_list[-1]))




                            else:

                                unrealized_pnl += float(lots_list[-1]) * (float(entry_price_list[-1]) - current_price)


                        # update counter
                        position_counter -= int(lots_process_list[index])

                        # update index
                        index -= 1



                    # update unrealized pnl
                    unrealized_pnl_list.append(round(unrealized_pnl, 2))

                    # calculate entry price
                    if entry_price_list != []:

                        # Convert the entire list to float values
                        entry_price_list = [float(value) for value in entry_price_list]

                        lots_list = [float(value) for value in lots_list]

                        # print([entry_price_list,lots_list])

                        # Calculating weighted average
                        weighted_average = round(
                            np.sum(np.array(entry_price_list) * np.array(lots_list)) / np.sum(np.array(lots_list)), 2)

                        # append entry price
                        final_entry_price_list.append(weighted_average)

                    else:



                        final_entry_price_list.append(0)



            return final_entry_price_list, unrealized_pnl_list, realized_pnl_list

        except Exception as e:

            print(e)

    # Method to update portfolio combo
    def update_portfolio_combo_table(self, flag_delete = False):

        # get table ids
        table_ids = self.portfolio_table.get_children()


        if flag_delete:

            for table_id in table_ids:

                self.portfolio_table.delete(table_id)



        # get position tab dataframe
        local_position_table = copy.deepcopy(variables.positions_table_dataframe)

        # Init
        local_position_table['Unrealized PNL'] = 'None'

        local_position_table['Realized PNL'] = 'None'

        local_position_table['Entry Price'] = 'None'



        # Concatenating 'unique id' and 'account id' using the + operator
        local_position_table['Table ID'] = local_position_table['Unique ID'].astype(str) + '_' + local_position_table['Account ID']

        local_position_table = local_position_table[variables.portfolio_table_combo_columns + ['Table ID']]

        # get entry price, realized pn and unrealized pnl
        list_entry_price, unreal_pnl_list, realized_pnl_list = self.calculate_pnl_entry_price(local_position_table)


        # set value for columns
        local_position_table['Entry Price'] = list_entry_price

        local_position_table['Unrealized PNL'] = unreal_pnl_list

        local_position_table['Realized PNL'] = realized_pnl_list

        counter = 0



        try:

            local_position_table['#Net Position'] = local_position_table['#Net Position'].astype(int)

            local_position_table['Realized PNL'] = local_position_table['Realized PNL'].astype(float)

            local_position_table['Unrealized PNL'] = local_position_table['Unrealized PNL'].astype(float)

            local_position_table['Entry Price'] = local_position_table['Entry Price'].astype(float)


            # New row as a list
            new_row = ['None', 'None', 'Total', local_position_table['#Net Position'].sum(),local_position_table['Realized PNL'].sum(),
                       local_position_table['Unrealized PNL'].sum(), 'None', local_position_table['Entry Price'].sum(), '-1']

            # Convert the list to a DataFrame
            new_row_df = pd.DataFrame([new_row], columns=local_position_table.columns)


            # Concatenate the new row DataFrame with the existing DataFrame
            local_position_table = pd.concat([local_position_table, new_row_df], ignore_index=True)

            zero_position_flag = self.zero_position_options_combo_box.get()

            # Formatting the value with thousand separator and upto  2 precision points
            local_position_table['Realized PNL'] = local_position_table['Realized PNL'].map(lambda x: f"{x:,.2f}")
            local_position_table['Unrealized PNL'] = local_position_table['Unrealized PNL'].map(lambda x: f"{x:,.2f}")
            local_position_table['Entry Price'] = local_position_table['Entry Price'].map(lambda x: f"{x:,.2f}")

            # iterate rows
            for indx, row in local_position_table.iterrows():

                # get table id
                table_id = row['Table ID']

                account_id = row['Account ID']

                net_position = int(row['#Net Position']
                                   )
                # get row in tuple
                row = tuple(row)

                if table_id in ['-1'] and table_id in table_ids:


                    # else:
                    self.portfolio_table.item(table_id, values=row)

                    self.portfolio_table.move('-1', '', 'end')

                    continue

                elif table_id in ['-1'] and table_id not in table_ids:

                    # insert in table
                    if counter % 2 == 0:
                        # Insert it in the table
                        self.portfolio_table.insert(
                            "",
                            "end",
                            iid=table_id,
                            text="",
                            values=row,
                            tags=("evenrow",),
                        )

                    else:

                        # Insert it in the table
                        self.portfolio_table.insert(
                            "",
                            "end",
                            iid=table_id,
                            text="",
                            values=row,
                            tags=("oddrow",),
                        )

                    continue



                # if already present then update row
                if table_id in table_ids:

                    if zero_position_flag in ['No'] and net_position == 0:
                        self.portfolio_table.delete(table_id)

                        continue

                    '''if 'ALL' not in variables.account_ids_list_of_selected_acount_group and account_id not in variables.account_ids_list_of_selected_acount_group:
                        self.portfolio_table.delete(table_id)'''
                    #else:
                    self.portfolio_table.item(table_id, values=row)

                    continue

                if 'ALL' in variables.account_ids_list_of_selected_acount_group or account_id in variables.account_ids_list_of_selected_acount_group:

                    if zero_position_flag in ['No'] and net_position == 0:

                        continue

                    # insert in table
                    if counter % 2 == 0:
                        # Insert it in the table
                        self.portfolio_table.insert(
                            "",
                            "end",
                            iid=table_id,
                            text="",
                            values=row,
                            tags=("evenrow",),
                        )

                    else:

                        # Insert it in the table
                        self.portfolio_table.insert(
                            "",
                            "end",
                            iid=table_id,
                            text="",
                            values=row,
                            tags=("oddrow",),
                        )

                    counter += 1

            # All the rows in Table
            table_ids = self.portfolio_table.get_children()

            # Row counter
            counter_row = 0

            for table_id in table_ids:

                if counter_row % 2 == 0:
                    self.portfolio_table.item(table_id, tags="evenrow")
                else:
                    self.portfolio_table.item(table_id, tags="oddrow")

                # Increase row count
                counter_row += 1

        except Exception as e:

            if variables.flag_debug_mode:

                print(f"Expection inside updating portfolio tab combo table, Exp: {e}")

    # Make ticker string for legs table
    def make_informative_leg_string(self, leg_obj):

        # Ticker 1 (Sec Type 1: Expiry 1 C/P Strike 1) +/- Qty 1,
        # Tickers Informative string
        combo_desc_string = ""


        all_leg_objs = [leg_obj]  # (it will be a list of legs)

        # Processing Leg Obj and appending to combo_desc_string
        for leg_no, leg_obj in enumerate(all_leg_objs):

            # Symbol and SecType
            combo_desc_string += f"{leg_obj.symbol} ({leg_obj.sec_type}"

            # Expiry Date, Right, Strike
            if leg_obj.sec_type in ["FOP", "OPT"]:
                combo_desc_string += (
                    f" {leg_obj.expiry_date} {leg_obj.right[0]} {leg_obj.strike_price}"
                )
            elif leg_obj.sec_type == "FUT":
                combo_desc_string += f" {leg_obj.expiry_date}"

            # Buy/Sell +1 or -1
            if leg_obj.action == "BUY":
                if leg_no == len(all_leg_objs) - 1:
                    combo_desc_string += f")"
                else:
                    combo_desc_string += f") "
            else:
                if leg_no == len(all_leg_objs) - 1:
                    combo_desc_string += f")"
                else:
                    combo_desc_string += f") "

        return combo_desc_string

    # Method to calculate legs position
    def calculate_legs_position(self, con_id, account_id):

        # get all legs orders
        legs_df = get_orders_for_legs(con_id, account_id)

        # Init
        position = 0


        # Iterate all orders
        for indx, row in legs_df.iterrows():



            # Check i forder action is buy
            if row['Order Action'] in 'BUY':

                # add lots in position value
                position += int(row['Target Fill'])

            else:

                # subtract lots in position value
                position -= int(row['Target Fill'])

        return position

    # Method to update portfolio legs table
    def update_portfolio_legs_table(self, flag_delete=False):

        # Get combo object using unique ids
        local_unique_id_to_combo_obj = copy.deepcopy(
            variables.unique_id_to_combo_obj
        )

        # Update the 'position_dict' to class variables.
        local_position_dict = variables.map_unique_id_to_positions

        # Init
        legs_decription_dict = {}

        legs_positions_dict = {}

        legs_decription_list = []

        legs_positions_list = []

        legs_account_list = []

        table_id_list = []

        cond_id_list = []

        # check legs combo by combo
        for unique_id in local_unique_id_to_combo_obj:

            # get combo obj and its legs
            combo_obj = local_unique_id_to_combo_obj[unique_id]

            all_legs = combo_obj.buy_legs + combo_obj.sell_legs

            # iterate all legs for combo
            for leg_obj in all_legs:

                # if leg is not already present
                if leg_obj.con_id not in legs_decription_dict:

                    # add legs details
                    legs_decription_dict[leg_obj.con_id] = {key: self.make_informative_leg_string(leg_obj) for key, value in local_position_dict[int(unique_id)].items()}

                    legs_decription_list += [self.make_informative_leg_string(leg_obj) for key, value in local_position_dict[int(unique_id)].items()]

                    legs_positions_dict[leg_obj.con_id] = {key: self.calculate_legs_position(leg_obj.con_id, key) for key, value in local_position_dict[int(unique_id)].items()}

                    legs_positions_list += [value * int(leg_obj.quantity) for key, value in local_position_dict[int(unique_id)].items()]

                    legs_account_list += [key for key, value in local_position_dict[int(unique_id)].items()]

                    table_id_list += [key + '_' + str(leg_obj.con_id) for key, value in local_position_dict[int(unique_id)].items()]

                    cond_id_list += [leg_obj.con_id for key, value in local_position_dict[int(unique_id)].items()]






        # create dataframe
        self.legs_df = pd.DataFrame(columns=['Leg Description', '#Net Position', 'Account ID', 'Realized PNL' ,'Unrealized PNL','Entry Price', 'Table ID', 'ConId'])

        # Extract values from nested dictionaries and flatten them into a list
        legs_positions_list = [value for inner_dict in legs_positions_dict.values() for value in inner_dict.values()]

        # assign value for dataframe columns
        self.legs_df['Leg Description'] = legs_decription_list

        self.legs_df['#Net Position'] = legs_positions_list

        self.legs_df['Account ID'] = legs_account_list

        self.legs_df['Realized PNL'] = 'None'

        self.legs_df['Unrealized PNL'] = 'None'

        self.legs_df['Entry Price'] = 'None'

        self.legs_df['Table ID'] = table_id_list

        self.legs_df['ConId'] = cond_id_list

        entry_list, unrealize_pnl, realize_pnl = self.calculate_pnl_entry_price_for_legs_table(self.legs_df)

        self.legs_df['Realized PNL'] = realize_pnl

        self.legs_df['Unrealized PNL'] = unrealize_pnl

        self.legs_df['Entry Price'] = entry_list

        # Init
        counter = 0

        # get table ids
        table_ids = self.portfolio_legs_table.get_children()



        try:

            self.legs_df['#Net Position'] = self.legs_df['#Net Position'].astype(int)

            self.legs_df['Realized PNL'] = self.legs_df['Realized PNL'].astype(float)

            self.legs_df['Unrealized PNL'] = self.legs_df['Unrealized PNL'].astype(float)

            self.legs_df['Entry Price'] = self.legs_df['Entry Price'].astype(float)

            # New row as a list
            new_row = ['Total', self.legs_df['#Net Position'].sum(),
                       'None',
                       round(self.legs_df['Realized PNL'].sum(), 2),
                       round(self.legs_df['Unrealized PNL'].sum(), 2), round(self.legs_df['Entry Price'].sum(), 2),
                       '-1', 'None']

            # Convert the list to a DataFrame
            new_row_df = pd.DataFrame([new_row], columns=self.legs_df.columns)

            # Concatenate the new row DataFrame with the existing DataFrame
            self.legs_df = pd.concat([self.legs_df, new_row_df], ignore_index=True)

            # Formatting values
            # self.legs_df['#Net Position'] = self.legs_df['#Net Position'].map(lambda x: f"{x:,.2f}")
            self.legs_df['Realized PNL'] = self.legs_df['Realized PNL'].map(lambda x: f"{x:,.2f}")
            self.legs_df['Unrealized PNL'] = self.legs_df['Unrealized PNL'].map(lambda x: f"{x:,.2f}")
            self.legs_df['Entry Price'] = self.legs_df['Entry Price'].map(lambda x: f"{x:,.2f}")

            zero_position_flag = self.zero_position_options_combo_box.get()

            if flag_delete:

                for table_id in table_ids:
                    self.portfolio_legs_table.delete(table_id)

            for indx, row in self.legs_df.iterrows():

                # get table id values
                table_id = row['Table ID']

                account_id = row['Account ID']

                net_position = int(row['#Net Position'])

                # get row in tuple
                row = tuple(row)

                if table_id in ['-1'] and table_id in table_ids:


                    # else:
                    self.portfolio_legs_table.item(table_id, values=row)

                    self.portfolio_legs_table.move('-1', '', 'end')

                    continue

                elif table_id in ['-1'] and table_id not in table_ids:

                    # insert in table
                    if counter % 2 == 0:
                        # Insert it in the table
                        self.portfolio_legs_table.insert(
                            "",
                            "end",
                            iid=table_id,
                            text="",
                            values=row,
                            tags=("evenrow",),
                        )

                    else:

                        # Insert it in the table
                        self.portfolio_legs_table.insert(
                            "",
                            "end",
                            iid=table_id,
                            text="",
                            values=row,
                            tags=("oddrow",),
                        )

                    continue


                # if already present then update row
                if table_id in table_ids:

                    if zero_position_flag in ['No'] and net_position == 0:
                        self.portfolio_legs_table.delete(table_id)

                        continue

                    self.portfolio_legs_table.item(table_id, values=row)

                    continue

                if 'ALL' in variables.account_ids_list_of_selected_acount_group or account_id in variables.account_ids_list_of_selected_acount_group:

                    if zero_position_flag in ['No'] and net_position == 0:

                        continue

                    # insert row in table
                    if counter % 2 == 0:
                        # Insert it in the table
                        self.portfolio_legs_table.insert(
                            "",
                            "end",
                            iid=table_id,
                            text="",
                            values=row,
                            tags=("evenrow",),
                        )

                    else:

                        # Insert it in the table
                        self.portfolio_legs_table.insert(
                            "",
                            "end",
                            iid=table_id,
                            text="",
                            values=row,
                            tags=("oddrow",),
                        )




                    counter += 1

            # All the rows in Table
            table_ids = self.portfolio_legs_table.get_children()

            # Row counter
            counter_row = 0

            for table_id in table_ids:

                if counter_row % 2 == 0:
                    self.portfolio_legs_table.item(table_id, tags="evenrow")
                else:
                    self.portfolio_legs_table.item(table_id, tags="oddrow")

                # Increase row count
                counter_row += 1

        except Exception as e:

            if variables.flag_debug_mode:
                print(f"Expection inside updating portfolio tab legs table, Exp: {e}")