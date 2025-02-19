from com import *
from com.variables import *
from com.json_io_custom_columns import *
from tkinter.scrolledtext import ScrolledText
from com.utilities import *


# Class for custom columns tab
class CustomColumns(object):
    def __init__(self, master_notebook):
        """
        Constructor
        """
        self.notebook = master_notebook

        # Create custom columns tab
        self.custom_columns_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.custom_columns_tab, text="  Custom Columns  ")

        # Method to create custom columns tab GUI components
        self.create_custom_columns_tab()

    # Method to create GUI for custom columns tab
    def create_custom_columns_tab(self):
        # Get frame for button to add custom columns
        custom_column_button_frame = ttk.Frame(self.custom_columns_tab, padding=10)
        custom_column_button_frame.pack(pady=10)

        # Initialize button to add custom column
        add_custom_column_button = ttk.Button(
            custom_column_button_frame,
            text="Add Custom Columns",
            command=lambda: self.add_custom_column(add_custom_column_button),
        )

        # Place add custom column button
        add_custom_column_button.grid(row=0, column=0, padx=10, pady=10)

        # Initialize button to delte custom column
        delete_custom_column_button = ttk.Button(
            custom_column_button_frame,
            text="Delete Custom Columns",
            command=lambda: self.delete_selected_custom_columns(),
        )

        # Place delete custom column button
        delete_custom_column_button.grid(row=0, column=1, padx=10, pady=10)

        # Place in center
        custom_column_button_frame.place(relx=0.5, anchor=tk.CENTER)
        custom_column_button_frame.place(y=30)

        # Create Treeview Frame for custom columns
        custom_columns_table_frame = ttk.Frame(self.custom_columns_tab, padding=10)
        custom_columns_table_frame.pack(pady=10)

        # Place in center
        custom_columns_table_frame.place(relx=0.5, anchor=tk.CENTER)
        custom_columns_table_frame.place(y=415)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(custom_columns_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview Table
        self.custom_columns_table = ttk.Treeview(
            custom_columns_table_frame,
            yscrollcommand=tree_scroll.set,
            height=27,
            selectmode="extended",
        )

        # Pack to the screen
        self.custom_columns_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.custom_columns_table.yview)

        # Get columns for custom columns table
        custom_columns_table_columns = copy.deepcopy(
            variables.custom_columns_table_columns
        )

        # Set columns for custom columns table
        self.custom_columns_table["columns"] = custom_columns_table_columns

        # Creating Column
        self.custom_columns_table.column("#0", width=0, stretch="no")

        # Creating columns for custom columns table
        for column_name in custom_columns_table_columns:
            # For "Column No" column set width to 100
            if column_name == "Column ID":
                self.custom_columns_table.column(
                    column_name, anchor="center", width=100
                )

            # For "Column Name" column set width to 200
            elif column_name == "Column Name":
                self.custom_columns_table.column(
                    column_name, anchor="center", width=200
                )

            # For "Column Expression" and "Column Description" column set width to 626
            else:
                self.custom_columns_table.column(
                    column_name, anchor="center", width=626
                )

        # Create Heading
        self.custom_columns_table.heading("#0", text="", anchor="w")

        # Create headings for custom columns table
        for column_heading in custom_columns_table_columns:
            self.custom_columns_table.heading(
                column_heading, text=column_heading, anchor="center"
            )

        # Back ground for rows in table
        self.custom_columns_table.tag_configure("oddrow", background="white")
        self.custom_columns_table.tag_configure("evenrow", background="lightblue")

    # Method to get selected custom columns and delete them
    def delete_selected_custom_columns(self):
        # Get values of selected rows
        selected_items = self.custom_columns_table.selection()

        # Iterate every selected column id
        for column_id in selected_items:
            try:
                # Delete custom column
                self.delete_custom_column(column_id)

            except Exception as e:
                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"For column ID: {column_id}, Exception occures while deleting custom column, Exp: {e}"
                    )

    # Method to delete custom columns
    def delete_custom_column(self, column_id):
        # Delete custom column
        delete_custom_column_from_json(column_id)

        # Update the table
        self.update_custom_column_table()

        # Update secondary columns dictionary
        update_secondary_columns()

        # Update CAS table
        variables.screen.screen_cas_obj.update_cas_tale_gui()

    # Method to adde custom column
    def add_custom_column(self, add_custom_column_button):
        # Disabled button
        # add_custom_column_button.config(state="Disabled")

        self.get_add_custom_column_popup()

    # Create pop up to add custom column
    def get_add_custom_column_popup(self):
        # title for pop up
        title_string = f"Add Custom Column"

        # Create a popup window with the table
        popup = tk.Toplevel()
        popup.title(title_string)

        # Setting pop up height and width
        popup.geometry("355x250")

        # Create a frame for the input fields
        input_frame = ttk.Frame(popup, padding=20)
        input_frame.pack(fill="both", expand=True)

        ttk.Label(
            input_frame,
            text="Column Name",
            width=19,
            anchor="w",
        ).grid(column=0, row=0, padx=5, pady=5)

        # Input textbox for column name
        column_name_entry = ttk.Entry(
            input_frame,
            width=30,
        )
        column_name_entry.grid(column=1, row=0, padx=5, pady=5)

        ttk.Label(
            input_frame,
            text="Column Description",
            width=19,
            anchor="w",
        ).grid(column=0, row=1, padx=5, pady=5)

        # Input textbox for column name
        column_description_entry = tk.Text(
            input_frame,
            width=23,
            height=8,
        )
        column_description_entry.grid(column=1, row=1, padx=5, pady=5)

        # Get frame for button to add custom columns
        custom_column_button_frame = ttk.Frame(input_frame, padding=10)
        # custom_column_button_frame.pack(pady=10)

        def get_input_from_popup():
            # Column attribute's values dict
            column_data_dict = {}

            # Get column name input
            column_data_dict["Column Name"] = column_name_entry.get().strip()

            # Get column Description
            column_data_dict["Column Description"] = column_description_entry.get(
                1.0, tk.END
            ).strip()

            # check if column name in niput is valid
            is_column_name_unique = check_new_column_name(
                column_data_dict["Column Name"]
            )

            # If column name is valid
            if is_column_name_unique:
                # destroy pop up
                popup.destroy()

                # Create enter condition popup
                variables.screen.screen_cas_obj.display_enter_condition_popup(
                    None,
                    None,
                    None,
                    None,
                    None,
                    custom_column_data_dict=column_data_dict,
                )

            else:
                error_title = error_string = (
                    "Column name matches with already available columns in CAS table"
                )

                variables.screen.display_error_popup(error_title, error_string)

        # Initialize button to add custom column
        add_custom_column_button = ttk.Button(
            custom_column_button_frame,
            text="Add Custom Column",
            command=lambda: get_input_from_popup(),
        )

        # Place add custom column button
        add_custom_column_button.pack()

        # Place in center
        custom_column_button_frame.grid(
            column=0, row=2, padx=5, pady=5, columnspan=2
        )  # .place(relx=0.5, anchor=tk.CENTER)

        """variables.screen.screen_cas_obj.display_enter_condition_popup(original_unique_id, buy_sell_action, 
                                                  combo_identified, reference_price, reference_position, order_type, combo_quantity,
                                                limit_price, trigger_price, trail_value, trading_combination_unique_id )"""

    # Method to update table of custom columns
    def update_custom_column_table(self):
        # Get updated custom columns from json
        get_all_custom_columns_from_json()

        # Get local dataframe for custom columns dataframe
        local_custom_columns_table_dataframe = variables.custom_columns_table_dataframe

        # Get all item IDs in the Treeview
        item_ids = self.custom_columns_table.get_children()

        # Delete each item from the Treeview
        for item_id in item_ids:
            self.custom_columns_table.delete(item_id)

        # Update the rows
        for i, row_val in local_custom_columns_table_dataframe.iterrows():
            # Column Id of row val
            column_id = int(float(row_val["Column ID"]))

            # Tuple of vals
            row_val = tuple(row_val)

            # Insert it in the table
            self.custom_columns_table.insert(
                "",
                "end",
                iid=column_id,
                text="",
                values=row_val,
                tags=("oddrow",),
            )

        # All the rows in column Table
        all_column_id_in_scale_trade_table = self.custom_columns_table.get_children()

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in local_custom_columns_table_dataframe.iterrows():
            # Ladder Id of row val
            column_id = str(row["Column ID"])

            # If unique_id in table
            if column_id in all_column_id_in_scale_trade_table:
                self.custom_columns_table.move(column_id, "", counter_row)

                if counter_row % 2 == 0:
                    self.custom_columns_table.item(column_id, tags="evenrow")
                else:
                    self.custom_columns_table.item(column_id, tags="oddrow")

                # Increase row count
                counter_row += 1


# Method to calculate values of secondary columns
def get_dataframe_for_seconday_columns_in_cas_table(cas_table_values):
    # Get copy of cas tble values
    cas_table_update_values = copy.deepcopy(cas_table_values)

    # create dataframe
    cas_table_update_values_df = pd.DataFrame(
        cas_table_update_values, columns=variables.cas_table_columns
    )

    # Get secondary columns mapped to expression dictionary
    local_map_secondary_columns_to_expression_in_cas_table = copy.deepcopy(
        variables.map_secondary_columns_to_expression_in_cas_table
    )

    # Init secondary column values
    secondary_columns_values = []

    try:
        # Iterate each row in dataframe
        for index, cas_row in cas_table_update_values_df.iterrows():
            # Initialize a tuple
            values_for_row = ()

            # Iterate each custom column
            for column_name in local_map_secondary_columns_to_expression_in_cas_table:
                try:
                    # Get Expression and flag for valid results to eval further
                    _, expression = evaluate_condition(
                        variables.cas_table_fields_for_expression,
                        cas_row,
                        local_map_secondary_columns_to_expression_in_cas_table[
                            column_name
                        ],
                        None,
                        None,
                    )

                    # Evaluate value of expression
                    expression_value = eval(str(expression))

                    # Add value in tuple
                    # values_for_row += (str(expression_value),)
                    if isinstance(expression_value, bool):
                        values_for_row += (str(expression_value),)

                    else:
                        values_for_row += (f"{(expression_value):,.2f}",)

                except Exception as e:
                    values_for_row += ("N/A",)

                    # Print  to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception while calculating values of secondary columns, Exp: {e}"
                        )

            # appending secondary column values to primary column vlaues
            cas_table_update_values[index] += values_for_row

        # returning merged list of vlaues for both primary and secondary columns
        return cas_table_update_values

    except Exception as e:
        # In case of exception ad all N/A values
        # getting copy of primary column values
        cas_table_update_values = copy.deepcopy(cas_table_values)

        # Iterate each row in dataframe
        for index, cas_row in cas_table_update_values_df.iterrows():
            # Initialize a tuple and add 'N/A'
            values_for_row = ("N/A",) * len(
                local_map_secondary_columns_to_expression_in_cas_table
            )

            cas_table_update_values[index] += values_for_row

        # Print  to console
        if variables.flag_debug_mode:
            print(f"Exception while adding values of secondary columns, Exp: {e}")

        # returning merged list of vlaues for both primary and secondary columns
        return cas_table_update_values
