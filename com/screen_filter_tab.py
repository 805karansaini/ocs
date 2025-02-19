import time

from com.variables import *
from com.mysql_io_filter_tab import *


# Class for accounts tab
class ScreenFilter(object):
    def __init__(self, master_notebook):
        """
        Constructor
        """
        self.notebook = master_notebook

        # Create filter tab
        self.filter_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.filter_tab, text="  Filter  ")

        # Method to create filter tab GUI components
        self.create_filter_tab()

    # Method to create GUI for filter tab
    def create_filter_tab(self):
        # Create Treeview Frame for filter instances
        filter_table_frame = ttk.Frame(self.filter_tab, padding=10)
        filter_table_frame.pack(pady=10)

        # Place in center
        filter_table_frame.place(relx=0.5, anchor=tk.N)
        filter_table_frame.place(y=50)

        # Create Treeview Frame for filter instances
        buttons_frame = ttk.Frame(self.filter_tab, padding=0)
        buttons_frame.pack(pady=0)

        # Initialize button to add filter
        add_filter_button = ttk.Button(
            buttons_frame,
            text="Add Condition",
            command=lambda: self.add_filter_condition(),
        )

        # Place add custom column button
        add_filter_button.grid(row=0, column=0, padx=10, pady=10)

        # Initialize button to delte custom column
        self.activate_deactivate_button = ttk.Button(
            buttons_frame,
            text="Activate Filter",
            command=lambda: self.activate_deactivated_filter_condition(),
        )

        # Place delete custom column button
        self.activate_deactivate_button.grid(row=0, column=1, padx=10, pady=10)

        # Place in center
        buttons_frame.place(relx=0.5, anchor=tk.N)
        buttons_frame.place(y=10)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(filter_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview Table
        self.filter_table = ttk.Treeview(
            filter_table_frame,
            yscrollcommand=tree_scroll.set,
            height=27,
            selectmode="extended",
        )

        # Pack to the screen
        self.filter_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.filter_table.yview)

        # Get columns for filter table
        filter_table_columns = copy.deepcopy(variables.filter_table_columns)

        # Set columns for filter table
        self.filter_table["columns"] = filter_table_columns

        # Creating Column
        self.filter_table.column("#0", width=0, stretch="no")

        # Creating columns for filter table
        for column_name in filter_table_columns:
            self.filter_table.column(column_name, anchor="center", width=520)

        # Create Heading
        self.filter_table.heading("#0", text="", anchor="w")

        # Create headings for filter table
        for column_name in filter_table_columns:
            self.filter_table.heading(column_name, text=column_name, anchor="center")

        # Back ground for rows in table
        self.filter_table.tag_configure("oddrow", background="white")
        self.filter_table.tag_configure("evenrow", background="lightblue")

        self.filter_table.bind("<Button-3>", self.filter_table_right_click)

        # update filter table
        self.update_filter_table(flag_init=True)

    # Method to toggle state of filter condition
    def activate_deactivated_filter_condition(self):
        # Check if value is true
        if variables.flag_enable_filter_condition:
            # Set value to false
            variables.flag_enable_filter_condition = False

            self.activate_deactivate_button.config(text="Activate Filter")

        else:
            # Set value to True
            variables.flag_enable_filter_condition = True

            self.activate_deactivate_button.config(text="Deactivate Filter")

        # set very big value
        variables.counter_filter_condition = 10**10

    # Method to define filter table right click options
    def filter_table_right_click(self, event):
        # get the Treeview row that was clicked
        row = self.filter_table.identify_row(event.y)

        if row:
            # select the row
            self.filter_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.filter_table, tearoff=0)
            menu.add_command(
                label="Activate Condition",
                command=lambda: self.activate_filter_condition(),
            )
            menu.add_command(
                label="Deactivate Condition",
                command=lambda: self.deactivate_filter_condition(),
            )
            menu.add_command(
                label="Delete Condition", command=lambda: self.delete_filter_condition()
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    # Method to activate filter condition
    def activate_filter_condition(self):
        # get selected row
        selected_item = self.filter_table.selection()[
            0
        ]  # get the item ID of the selected row

        values = self.filter_table.item(
            selected_item, "values"
        )  # get the values of the selected row

        # Get value of condition name
        condition_name = values[0]

        # Get active value
        active_val = values[2]

        # check if filter is already active
        if active_val == "Yes":
            return

        # create dict to update values
        values_to_update_dict = {"Active": "Yes"}

        # update in db
        update_filter_condition_table_db(condition_name, values_to_update_dict)

        # sleep
        time.sleep(variables.sleep_time_db)

        # update filter table
        self.update_filter_table()

    # Method to deactivate filter condition
    def deactivate_filter_condition(self):
        # get selected row
        selected_item = self.filter_table.selection()[
            0
        ]  # get the item ID of the selected row

        values = self.filter_table.item(
            selected_item, "values"
        )  # get the values of the selected row

        # Get value of condition name
        condition_name = values[0]

        # Get active value
        active_val = values[2]

        # check if filter is already not active
        if active_val == "No":
            return

        # create dict to uppdate values
        values_to_update_dict = {"Active": "No"}

        # Update in DB table
        update_filter_condition_table_db(condition_name, values_to_update_dict)

        # sleep
        time.sleep(variables.sleep_time_db)

        # update filter table
        self.update_filter_table()

    # Method to delete filter condition
    def delete_filter_condition(self):
        # get selected row
        selected_item = self.filter_table.selection()[
            0
        ]  # get the item ID of the selected row

        values = self.filter_table.item(
            selected_item, "values"
        )  # get the values of the selected row

        # Get value of condition name
        condition_name = values[0]

        # Delete condition
        delete_filter_condition_in_db(condition_name)

        # sleep
        time.sleep(variables.sleep_time_db)

        # update filter table
        self.update_filter_table()

    # Method to update filter table
    def update_filter_table(self, flag_init=False):
        # Get all conditions in db table
        filter_table_df = get_all_filter_conditions()

        # Get all item IDs in the Treeview
        item_ids = self.filter_table.get_children()

        # Delete each item from the Treeview
        for item_id in item_ids:
            self.filter_table.delete(item_id)

        # Check if df is empty
        if filter_table_df.empty:
            return

        # Init
        counter = 0

        # Iterate rowws in df
        for indx, row in filter_table_df.iterrows():
            # get condition name
            condition_name = row["Condition Name"]

            # convert to tuple
            row = tuple(row)

            # add rows
            if counter % 2 == 1:
                self.filter_table.insert(
                    "",
                    "end",
                    iid=condition_name,
                    text="",
                    values=row,
                    tags=("oddrow",),
                )

            else:
                self.filter_table.insert(
                    "",
                    "end",
                    iid=condition_name,
                    text="",
                    values=row,
                    tags=("evenrow",),
                )

            counter += 1

        # check it is not at time of  initializing screen
        if not flag_init:
            # set very big value
            variables.counter_filter_condition = 10**10

    # Method to add filter condition
    def add_filter_condition(self):
        # title for pop up
        title_string = f"Add Filter Condition"

        # Create a popup window with the table
        popup = tk.Toplevel()
        popup.title(title_string)

        # Setting pop up height and width
        popup.geometry("355x100")

        # Create a frame for the input fields
        input_frame = ttk.Frame(popup, padding=20)
        input_frame.pack(fill="both", expand=True)

        # add label
        ttk.Label(
            input_frame,
            text="Condition Name",
            width=19,
            anchor="w",
        ).grid(column=0, row=0, padx=5, pady=5)

        # Input textbox for condition name
        condition_name_entry = ttk.Entry(
            input_frame,
            width=30,
        )
        condition_name_entry.grid(column=1, row=0, padx=5, pady=5)

        # Get frame for button to add custom columns
        filter_condition_button_frame = ttk.Frame(input_frame, padding=10)

        def get_input_from_popup():
            # condition attribute's values dict
            condition_data_dict = {}

            # Get column name input
            condition_name_input = condition_name_entry.get().strip().upper()

            # check if input is empty
            if condition_name_input == "":
                # show error pop up
                error_title = error_string = "Condition name is empty"

                variables.screen.display_error_popup(error_title, error_string)

                return

            # Get all conditions in db table
            filter_table_df = get_all_filter_conditions()

            # check if dataframe is empty
            if filter_table_df.empty:
                condition_names = []
            else:
                # get existing condition names
                condition_names = filter_table_df["Condition Name"].to_list()

            # convert to upper case
            condition_names = [word.upper() for word in condition_names]

            # check if condition anme is already present
            if condition_name_input in condition_names:
                # show error pop up
                error_title = error_string = "Condition name already present"

                variables.screen.display_error_popup(error_title, error_string)

                return

            # Get condition name name input
            condition_data_dict["Condition Name"] = condition_name_entry.get().strip()

            # flag to indicate we are getting condition for filter
            condition_data_dict["Flag Filter"] = True

            # destroy pop up
            popup.destroy()

            # Create enter condition popup
            variables.screen.screen_cas_obj.display_enter_condition_popup(
                None,
                None,
                None,
                None,
                None,
                custom_column_data_dict=condition_data_dict,
            )

        # Initialize button to add custom column
        add_filter_condition_button = ttk.Button(
            filter_condition_button_frame,
            text="Add Filter Condition",
            command=lambda: get_input_from_popup(),
        )

        # Place add custom column button
        add_filter_condition_button.pack()

        # Place in center
        filter_condition_button_frame.grid(
            column=0, row=2, padx=5, pady=5, columnspan=2
        )  # .place(relx=0.5, anchor=tk.CENTER)
