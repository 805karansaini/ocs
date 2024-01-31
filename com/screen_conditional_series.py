import copy
import time
from tkinter import *
from com.upload_orders_from_csv import get_atr_value_for_unique_id
import pandas as pd
from com.combination_helper import create_combination
from com.variables import *
from com.mysql_io_conditional_series import *
from com.utilities import evaluate_condition, check_basic_condition
from tkinter import filedialog
from com.scale_trade_helper import is_float
from com.upload_orders_from_csv import (
    make_multiline_mssg_for_gui_popup,
    get_trigger_price_for_stop_loss,
    get_trail_value_for_trailing_stop_loss,
)
from com.upload_combo_to_application import (
    create_combo_wrapper,
    make_multiline_mssg_for_gui_popup,
    make_informative_combo_string,
)

# Class for coditional series tab
class ScreenConditionalSeries(object):
    def __init__(self, master_notebook):
        """
        Constructor
        """
        self.notebook = master_notebook

        # Create filter tab
        self.conditional_series_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.conditional_series_tab, text="  Conditional Series  ")

        # Method to create conditional series tab GUI components
        self.create_conditional_series_tab()

    # Method to create GUI for filter tab
    def create_conditional_series_tab(self):

        # Create Treeview Frame for conditional_series instances
        conditional_series_table_frame = ttk.Frame(
            self.conditional_series_tab, padding=10
        )
        conditional_series_table_frame.pack(pady=10)
        conditional_series_table_frame.pack(fill="both", expand=True)

        # Place in top
        conditional_series_table_frame.place(relx=0.5, anchor=tk.N)
        conditional_series_table_frame.place(y=50, width=1600)

        # Add a button to create the combo
        import_button = ttk.Button(
            self.conditional_series_tab,
            text="Upload Series",
            command=lambda: self.import_series(import_button),
        )

        # Place in top
        import_button.place(relx=0.5, anchor=tk.N)
        import_button.place(y=20)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(conditional_series_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Treeview Scrollbar
        x_tree_scroll = Scrollbar(conditional_series_table_frame, orient="horizontal")
        x_tree_scroll.pack(side="bottom", fill="x")

        # Create Treeview Table
        self.conditional_series_table = ttk.Treeview(
            conditional_series_table_frame,
            yscrollcommand=tree_scroll.set,
            xscrollcommand=x_tree_scroll.set,
            height=27,
            selectmode="extended",
        )

        # Pack to the screen
        self.conditional_series_table.pack(fill="both", expand=True)

        # Configure the scrollbar
        tree_scroll.config(command=self.conditional_series_table.yview)

        # Configure the scrollbar
        x_tree_scroll.config(command=self.conditional_series_table.xview)

        # Get columns for conditional_series table
        conditional_series_table_columns = copy.deepcopy(
            variables.conditional_series_table_columns
        )

        # Set columns for filter table
        self.conditional_series_table["columns"] = conditional_series_table_columns

        # Creating Column
        self.conditional_series_table.column("#0", width=0, stretch="no")

        # Creating columns for conditional_series table
        for column_name in conditional_series_table_columns:
            self.conditional_series_table.column(
                column_name, anchor="center", width=195
            )

        # Create Heading
        self.conditional_series_table.heading("#0", text="", anchor="w")

        # Create headings for conditional_series table
        for column_name in conditional_series_table_columns:
            self.conditional_series_table.heading(
                column_name, text=column_name, anchor="center"
            )

        # Back ground for rows in table
        self.conditional_series_table.tag_configure("oddrow", background="white")
        self.conditional_series_table.tag_configure("evenrow", background="lightblue")

        # right click options
        self.conditional_series_table.bind(
            "<Button-3>", self.conditional_series_table_right_click
        )

        # Update table
        self.update_conditional_series_table()

    # Method to define conditional table right click options
    def conditional_series_table_right_click(self, event):

        # get the Treeview row that was clicked
        row = self.conditional_series_table.identify_row(event.y)

        if row:
            # select the row
            self.conditional_series_table.selection_set(row)

            # create a context menu
            menu = tk.Menu(self.conditional_series_table, tearoff=0)
            menu.add_command(
                label="View Details", command=lambda: self.view_series_details()
            )
            menu.add_command(label="Start Series", command=lambda: self.start_series())
            menu.add_command(label="Stop Series", command=lambda: self.stop_series())
            menu.add_command(label="Unpark Series", command=lambda: self.unpark_series())
            menu.add_command(label="Park Series", command=lambda: self.park_series())
            menu.add_command(
                label="Delete Series", command=lambda: self.delete_series()
            )
            menu.add_command(
                label="Relaunch Series", command=lambda: self.relaunch_series()
            )

            menu.add_command(label="Edit Series", command=lambda: self.edit_series())
            menu.add_command(
                label="Export Series", command=lambda: self.export_series()
            )

            # display the context menu at the location of the mouse cursor
            menu.post(event.x_root, event.y_root)

    # Method to update conditional order after order completed
    def update_conditional_order_after_order_completed(
        self,
        series_id,
        new_unique_id=None,
        old_unique_id=None,
        new_unique_id_for_old_combo=None,
    ):

        try:

            if new_unique_id != None:

                update_unique_id_series_db(
                    new_unique_id,
                    old_unique_id,
                    new_unique_id_for_old_combo,
                    flag_series=True,
                )

            # get active sequence for series
            active_sequence_item = get_all_sequences_of_series(
                series_id, flag_active=True
            )

            # get sequence id
            sequence_id = active_sequence_item.loc[0, "Sequence ID"]

            sequence_id_completed = sequence_id

            # values to be updated
            values_to_update_dict = {"Status": "Completed"}

            # update values in db table
            update_conditional_series_sequence_table_values(
                sequence_id, values_to_update_dict, flag_active=True
            )

            # get value of sequences from db
            sequences_completed = get_series_column_value_from_db(
                series_id=series_id, column_name_as_in_db="Sequences Completed"
            )

            # convert value to int
            sequences_completed = int(sequences_completed)

            # Imcrement value of sequences completed
            sequences_completed += 1

            # values to be updated
            values_to_update_dict = {"Sequences Completed": sequences_completed}

            # update values in db table
            update_conditional_series_table_values(series_id, values_to_update_dict)

            # get next active sequence
            row_df = get_next_sequences_of_series(series_id)

            # check if df is empty
            if row_df.empty:
                # values to be updated
                values_to_update_dict = {"Status": "Completed"}

                # update values in db table
                update_conditional_series_table_values(series_id, values_to_update_dict)

                # update gui table
                self.update_conditional_series_table()

                return

            # get new sequence id
            sequence_id = row_df.loc[0, "Sequence ID"]

            # values to be updated
            values_to_update_dict = {"Status": "Active"}

            # update values in db table
            update_conditional_series_sequence_table_values(
                sequence_id, values_to_update_dict
            )

            # update gui table
            self.update_conditional_series_table()

            # add new order
            self.start_series(selected_item=series_id)

        except Exception as e:
            if variables.flag_debug_mode:

                print(e)

    # Method to upload csv file to app to create series
    def upload_series_from_csv_to_app(self, file_path, upload_series_button):

        try:
            # get csv file from file path
            series_dataframe = pd.read_csv(file_path)

            # Replace null values by None string
            series_dataframe = series_dataframe.fillna("None")

            # print(series_dataframe.to_string())

            # Enabled upload combinations button
            upload_series_button.config(state="enabled")

            # Creating dataframe for row data
            sequence_df = pd.DataFrame(
                columns=variables.series_sequence_tble_columns,
            )

        except Exception as e:
            # Error Message
            error_title = f"Error reading the Series CSV file"
            error_string = f"Unable to read the Series CSV file"
            variables.screen.display_error_popup(error_title, error_string)

            # Enabled upload combinations button
            upload_series_button.config(state="enabled")

            return

        try:

            # get column names
            columns_list = series_dataframe.columns

            # check if start of series tag is in right position
            if columns_list[0] != "#StartOfSeries":
                # Error Message
                error_title = f"Error #StartOfSeries not available"
                error_string = "Error #StartOfSeries not available"
                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # get list of all tags
            tags_list = series_dataframe["#StartOfSeries"].to_list()

            # Rename columns
            new_column_names = ["#StartOfSeries"] + [
                f"Column {i}" for i in range(1, 16)
            ]

            try:

                # rename columns
                series_dataframe.columns = new_column_names

            except Exception as e:

                # Error Message
                error_title = f"Error, Columns are invalid, at line no: {1}"
                error_string = f"Error, Columns are invalid, at line no: {1}"
                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # print(series_dataframe.to_string())

            # check if end of series is in right place
            if tags_list[-1] != "#EndOfSeries":
                # Error Message
                error_title = "Error #EndOfSeries not available"
                error_string = f"Error #EndOfSeries not available"
                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # check count of end of series tag
            if tags_list.count("#EndOfSeries") != 1:
                # Error Message
                error_title = "Error #EndOfSeries should not be present multiple times"
                error_string = "Error #EndOfSeries should not be present multiple times"

                error_string = make_multiline_mssg_for_gui_popup(error_string)
                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # check count of end of series tag
            if tags_list.count("#StartOfSeries") != 0:
                # Error Message
                error_title = (
                    "Error #StartOfSeries should not be present multiple times"
                )
                error_string = (
                    "Error #StartOfSeries should not be present multiple times"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)
                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # check is start of series condition tag is in right place
            if tags_list[0] != "#StartOfSeriesCondition":
                # Error Message
                error_title = "Error #StartOfSeriesCondition not available"
                error_string = (
                    f"Error #StartOfSeriesCondition not available, at line no: {2}"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking count for start of series condition tag
            if tags_list.count("#StartOfSeriesCondition") != 1:
                # Error Message
                error_title = (
                    "Error #StartOfSeriesCondition should not be present multiple times"
                )
                error_string = (
                    "Error #StartOfSeriesCondition should not be present multiple times"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking position of series condition value tag
            if tags_list[1] != "#SeriesConditionValues":
                # Error Message
                error_title = "Error #SeriesConditionValues not available"
                error_string = (
                    f"Error #SeriesConditionValues not available, at line no: {3}"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking count of series condition values
            if tags_list.count("#SeriesConditionValues") != 1:
                # Error Message
                error_title = (
                    "Error #SeriesConditionValues should not be present multiple times"
                )
                error_string = (
                    "Error #SeriesConditionValues should not be present multiple times"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking position of end of series condition tag
            if tags_list[2] != "#EndOfSeriesCondition":
                # Error Message
                error_title = "Error #EndOfSeriesCondition not available"
                error_string = (
                    f"Error #EndOfSeriesCondition not available, at line no: {4}"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking count of end of series condition tag
            if tags_list.count("#EndOfSeriesCondition") != 1:
                # Error Message
                error_title = (
                    "Error #EndOfSeriesCondition should not be present multiple times"
                )
                error_string = (
                    "Error #EndOfSeriesCondition should not be present multiple times"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking position of end of StartOfSeriesValues tag
            if tags_list[3] != "#StartOfSeriesValues":
                # Error Message
                error_title = "Error #StartOfSeriesValues not available"
                error_string = (
                    f"Error #StartOfSeriesValues not available, at line no: {5}"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking count of end of StartOfSeriesValues tag
            if tags_list.count("#StartOfSeriesValues") != 1:
                # Error Message
                error_title = (
                    "Error #StartOfSeriesValues should not be present multiple times"
                )
                error_string = (
                    "Error #StartOfSeriesValues should not be present multiple times"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking position of end of series values tag
            if tags_list[4] != "#SeriesValues":
                # Error Message
                error_title = "Error #SeriesValues not available"
                error_string = "Error #SeriesValues not available, at line no: {6}"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking count of end of series values tag
            if tags_list.count("#SeriesValues") != 1:
                # Error Message
                error_title = "Error #SeriesValues should not be present multiple times"
                error_string = (
                    "Error #SeriesValues should not be present multiple times"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking position of end of end of series values tag
            if tags_list[5] != "#EndOfSeriesValues":
                # Error Message
                error_title = "Error #EndOfSeriesValues not available"
                error_string = "Error #EndOfSeriesValues not available, at line no: {7}"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking count of end of end of series values tag
            if tags_list.count("#EndOfSeriesValues") != 1:
                # Error Message
                error_title = (
                    "Error #EndOfSeriesValues should not be present multiple times"
                )
                error_string = (
                    "Error #EndOfSeriesValues should not be present multiple times"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking count of start of sequence and end of sequence tag
            if (
                tags_list.count("#StartOfSequence") != tags_list.count("#EndOfSequence")
                and tags_list.count("#StartOfSequence") > 0
            ):
                # Error Message
                error_title = (
                    "Error, count of #StartOfSequence and #EndOfSequence should be same"
                )
                error_string = (
                    "Error, count of #StartOfSequence and #EndOfSequence should be same"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking count of start of sequence values and end of sequence values tag
            if (
                tags_list.count("#StartOfSequenceValues")
                != tags_list.count("#EndOfSequenceValues")
                and tags_list.count("#StartOfSequence") > 0
            ):
                # Error Message
                error_title = "Error, count of #StartOfSequenceValues and #EndOfSequenceValues should be same"
                error_string = "Error, count of #StartOfSequenceValues and #EndOfSequenceValues should be same"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking count of start of sequence leg and end of sequence leg tag
            if tags_list.count("#StartOfSequenceLeg") != tags_list.count(
                "#EndOfSequenceLeg"
            ):
                # Error Message
                error_title = "Error, count of #StartOfSequenceLeg and #EndOfSequenceLeg should be same"
                error_string = "Error, count of #StartOfSequenceLeg and #EndOfSequenceLeg should be same"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # checking count of start of sequence position and end of sequence position tag
            if tags_list.count("#StartOfSequencePosition") != tags_list.count(
                "#EndOfSequencePosition"
            ):
                # Error Message
                error_title = "Error, count of #StartOfSequencePosition and #EndOfSequencePosition should be same"
                error_string = "Error, count of #StartOfSequencePosition and #EndOfSequencePosition should be same"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                # Enabled upload combinations button
                upload_series_button.config(state="enabled")

                return

            # Get combo details dataframe
            local_combo_details_df = copy.deepcopy(variables.combo_table_df)

            # All the Unique IDs in the System
            all_unique_ids_in_system = local_combo_details_df["Unique ID"].tolist()

            # get copy of data frame
            local_conditional_series_table = get_conditional_series_df()

            # check if df is empty
            if local_conditional_series_table.empty:

                all_series_ids_in_system = []

            else:
                # All the series IDs in the System
                all_series_ids_in_system = local_conditional_series_table[
                    "Series ID"
                ].tolist()

            # get values
            base_uid = series_dataframe.at[4, "Column 1"]
            account_id = series_dataframe.at[4, "Column 2"]
            bypass_rm_check = series_dataframe.at[4, "Column 3"].upper().strip()
            execution_engine = series_dataframe.at[4, "Column 4"].upper().strip()

            # check if base UID is numeric
            if not base_uid.isnumeric():
                # Error Message
                error_title = f"Error, Base unique id should be numeric"
                error_string = f"Error, Base unique id should be numeric, at line: {5}"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if base uid is in system
            if int(base_uid) not in all_unique_ids_in_system:
                # Error Message
                error_title = f"Error, Base unique id is not in system"
                error_string = (
                    f"Error, Base unique id is not in system, at line no: {5}"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return

            # Number of CAS Conditions that exists
            '''number_of_conditions = do_cas_condition_exists_for_unique_id_in_db(base_uid)

            number_of_conditions += do_cas_condition_series_exists_for_unique_id_in_db(
                base_uid
            )

            # If a condition already exists, display error popup
            if number_of_conditions > 0:
                # TODO
                # Throw Error Popup
                variables.screen.display_error_popup(
                    f"Unique ID : {base_uid}, Conditional order or series already exists",
                    "A Conditional order or series already exists, can not add another.",
                )
                return'''


            # check account ids provide are right or not
            if account_id.count("|") > 0:

                account_id = account_id.split("|")

                for account in account_id:

                    if account not in variables.current_session_accounts:
                        # Error Message
                        error_title = f"Error, Account ID is not in system"
                        error_string = (
                            f"Error, Account ID is not in system, at line no: {5}"
                        )

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return
            else:

                if account_id not in variables.current_session_accounts:
                    # Error Message
                    error_title = f"Error, Account ID is not in system"
                    error_string = (
                        f"Error, Account ID is not in system, at line no: {5}"
                    )

                    error_string = make_multiline_mssg_for_gui_popup(error_string)

                    variables.screen.display_error_popup(error_title, error_string)

                    return

            # check bypass rm check value
            if bypass_rm_check not in ["TRUE", "FALSE"]:
                # Error Message
                error_title = f"Error, Bypass RM Check value is invalid"
                error_string = (
                    f"Error, Bypass RM Check value is invalid, at line no: {5}"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return

            # check execution engine vlaue
            if execution_engine not in ["TRUE", "FALSE"]:
                # Error Message
                error_title = f"Error, Execution engine value is invalid"
                error_string = (
                    f"Error, Execution engine value is invalid, at line no: {5}"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return

            # method to get index for tags
            def get_indexes(lst, value):
                return [index for index, item in enumerate(lst) if item == value]

            # sequence start index list
            seq_start_index = get_indexes(tags_list, "#StartOfSequence")

            # sequence end index list
            seq_end_index = get_indexes(tags_list, "#EndOfSequence")

            # get account ids
            account_id = series_dataframe.at[4, "Column 2"]

            flag_multi = False

            # check if count is more than 0 for '|'
            if account_id.count("|") > 0:

                # set value to true
                flag_multi = True

            # iterate for every sequence available
            for ind_seq, (seq_start, seq_end) in enumerate(
                zip(seq_start_index, seq_end_index)
            ):

                # get values
                cas_type = series_dataframe.at[seq_start + 2, "Column 3"]

                cas_type = cas_type.upper()
                trading_uid_seq = series_dataframe.at[seq_start + 2, "Column 1"]
                eval_uid_seq_val = series_dataframe.at[seq_start + 2, "Column 2"]
                condition = series_dataframe.at[seq_start + 2, "Column 4"]
                order_type = series_dataframe.at[seq_start + 2, "Column 5"].upper()
                qnty_seq = series_dataframe.at[seq_start + 2, "Column 6"]
                limit_price = series_dataframe.at[seq_start + 2, "Column 7"]
                trigger_price = series_dataframe.at[seq_start + 2, "Column 8"]
                trail_value = series_dataframe.at[seq_start + 2, "Column 9"]
                atr_multiple = series_dataframe.at[seq_start + 2, "Column 10"]

                ticker_info_string = ""
                combination_obj = None

                # check condition of sequence
                if condition in ["None", ""]:
                    # Error Message
                    error_title = "Error, condition value is invalid"
                    error_string = (
                        f"Error, condition is invalid, at line no: {seq_start + 4}"
                    )

                    error_string = make_multiline_mssg_for_gui_popup(error_string)

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                else:

                    if cas_type in ["ADD", "SWITCH"]:

                        temp_uid = eval_uid_seq_val

                    else:

                        temp_uid = base_uid

                    try:

                        if (
                            isinstance(temp_uid, str) and temp_uid.isnumeric()
                        ) or isinstance(temp_uid, int):

                            reference_price_seq = (
                                variables.unique_id_to_prices_dict[int(temp_uid)]["BUY"]
                                + variables.unique_id_to_prices_dict[int(temp_uid)][
                                    "SELL"
                                ]
                            ) / 2

                        else:

                            reference_price_seq = None

                    except Exception as e:

                        reference_price_seq = None

                        if variables.flag_debug_mode:
                            print(f"Exception for getting price for combo, Exp: {e}")

                    # Trying to get the reference positions
                    try:
                        local_unique_id_to_positions_dict = copy.deepcopy(
                            variables.map_unique_id_to_positions
                        )

                        if (
                            (isinstance(temp_uid, str) and temp_uid.isnumeric())
                            or isinstance(temp_uid, int)
                            and len(variables.current_session_accounts) == 1
                        ):

                            reference_position_seq = local_unique_id_to_positions_dict[
                                int(temp_uid)
                            ][variables.current_session_accounts[0]]

                        else:

                            reference_position_seq = None
                    except Exception as e:

                        reference_position_seq = None

                        if variables.flag_debug_mode:
                            print(e)

                    # Validate Condition Here
                    flag_condition_passed, error_string = check_basic_condition(
                        condition, None, reference_price_seq, reference_position_seq
                    )

                    if not flag_condition_passed:
                        # Error Message
                        error_title = "Error, format of sequence condition is invalid"
                        error_string = f"Error, format of sequence condition is invalid, at line no: {seq_start + 4}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                # check if order type is valid
                if cas_type not in ["ADD", "SWITCH", "BUY", "SELL"]:

                    # Error Message
                    error_title = "Error, cas type value is invalid"
                    error_string = (
                        f"Error, cas type value is invalid, at line no: {seq_start + 4}"
                    )

                    error_string = make_multiline_mssg_for_gui_popup(error_string)

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                # check for cas type add or switch
                if cas_type in ["ADD", "SWITCH"]:

                    # check if evaluation uid is numeric
                    if not eval_uid_seq_val.isnumeric():
                        # Error Message
                        error_title = "Error, Evaluation unique id must be numeric for add or switch"
                        error_string = f"Error, Evaluation unique id must be numeric for add or switch, at line no: {seq_start + 4}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    if int(eval_uid_seq_val) not in all_unique_ids_in_system:
                        # Error Message
                        error_title = "Error, Evaluation unique id for sequence must be present in system for add or switch"
                        error_string = f"Error, Evaluation unique id for sequence must be present in system for add or switch, at line no: {seq_start + 4}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                else:

                    # checking if trading uid is numeric
                    if not trading_uid_seq.isnumeric():
                        # Error Message
                        error_title = (
                            "Error, Trading unique id must be numeric for buy or sell"
                        )
                        error_string = f"Error, Trading unique id must be numeric for buy or sell, at line no: {seq_start + 4}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    if int(trading_uid_seq) not in all_unique_ids_in_system:
                        # Error Message
                        error_title = "Error, Trading unique id for sequence must be present in system for buy or sell"
                        error_string = f"Error, Trading unique id for sequence must be present in system for buy or sell, at line no: {seq_start + 4}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    # checking if order type is correct
                    if order_type not in [
                        "MARKET",
                        "LIMIT",
                        "STOP LOSS",
                        "TRAILING STOP LOSS",
                        "IB ALGO MARKET",
                    ]:
                        # Error Message
                        error_title = "Error, Invalid order type"
                        error_string = (
                            f"Error, Invalid order type, at line no: {seq_start + 4}"
                        )

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    # checking fr flag multi
                    if flag_multi:

                        if not is_float(qnty_seq):
                            # Error Message
                            error_title = "Error, Quantity is invalid"
                            error_string = f"Error, Quantity is invalid, at line no: {seq_start + 4}"

                            error_string = make_multiline_mssg_for_gui_popup(
                                error_string
                            )

                            variables.screen.display_error_popup(
                                error_title, error_string
                            )

                            return

                    else:

                        # hecking if quanity is numeric
                        if not qnty_seq.isnumeric():
                            # Error Message
                            error_title = "Error, Quantity is invalid"
                            error_string = f"Error, Quantity is invalid, at line no: {seq_start + 4}"

                            error_string = make_multiline_mssg_for_gui_popup(
                                error_string
                            )

                            variables.screen.display_error_popup(
                                error_title, error_string
                            )

                            return

                    # check if order values are correct
                    res = self.order_value_check(
                        order_type,
                        limit_price,
                        trigger_price,
                        trail_value,
                        atr_multiple,
                        cas_type,
                        seq_start + 2,
                        int(base_uid),
                    )

                    flag_order, error_title, error_msg = res

                    # checking flags value
                    if not flag_order:
                        # Error Message
                        error_title = error_title
                        error_string = error_msg

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                # check position of start of sequence values
                if tags_list[seq_start + 1] != "#StartOfSequenceValues":
                    # Error Message
                    error_title = "Error, position of #StartOfSequenceValues is invalid"
                    error_string = f"Error, position of #StartOfSequenceValues is invalid, at line no: {seq_start + 1}"

                    error_string = make_multiline_mssg_for_gui_popup(error_string)

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                # check position of sequence values
                if tags_list[seq_start + 2] != "#SequenceValues":
                    # Error Message
                    error_title = "Error, position of #SequenceValues is invalid"
                    error_string = f"Error, position of #SequenceValues is invalid, at line no: {seq_start + 4}"

                    error_string = make_multiline_mssg_for_gui_popup(error_string)

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                # check value for end of sequence values
                if tags_list[seq_start + 3] != "#EndOfSequenceValues":
                    # Error Message
                    error_title = "Error, position of #EndOfSequenceValues is invalid"
                    error_string = f"Error, position of #EndOfSequenceValues is invalid, at line no: {seq_start + 3}"

                    error_string = make_multiline_mssg_for_gui_popup(error_string)

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                # checing difference of index for start and end of sequence
                if cas_type in ["BUY", "SELL"] and seq_end - seq_start > 4:
                    # Error Message
                    error_title = "Error, structure of buy or sell sequence is wrong"
                    error_string = f"Error, structure of buy or sell sequence is wrong, at line no: {seq_start}"

                    error_string = make_multiline_mssg_for_gui_popup(error_string)

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                # checking position of start of sequence leg
                if (
                    cas_type in ["ADD", "SWITCH"]
                    and tags_list[seq_start + 4] != "#StartOfSequenceLeg"
                ):
                    # Error Message
                    error_title = "Error, position of #StartOfSequenceLeg is invalid"
                    error_string = f"Error, position of #StartOfSequenceLeg is invalid, at line no: {seq_start + 4}"

                    error_string = make_multiline_mssg_for_gui_popup(error_string)

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                # checking position of end of sequence psotion
                if (
                    cas_type in ["ADD", "SWITCH"]
                    and tags_list[seq_end - 1] != "#EndOfSequencePosition"
                ):
                    # Error Message
                    error_title = "Error, position of #EndOfSequencePosition is invalid"
                    error_string = f"Error, position of #EndOfSequencePosition is invalid, at line no: {seq_end - 1}"

                    error_string = make_multiline_mssg_for_gui_popup(error_string)

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                indx_tag = seq_start + 5

                list_of_tuple_of_values = []

                # iterating till app find position of end of sequence leg
                while (
                    cas_type in ["ADD", "SWITCH"]
                    and tags_list[indx_tag] != "#EndOfSequenceLeg"
                ):

                    # check if tag is for sequence leg values
                    if tags_list[indx_tag] != "#SequenceLeg":
                        # Error Message
                        error_title = (
                            f"Error, position of {tags_list[indx_tag]} is invalid"
                        )
                        error_string = f"Error, position of {tags_list[indx_tag]} is invalid, at line no: {indx_tag + 2}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    # check if tag is for sequence leg values
                    if tags_list[indx_tag] == "#SequenceLeg":
                        # Get the values of the row at index
                        row_at_index = series_dataframe.iloc[indx_tag].values

                        row_at_index = list(row_at_index[1:])

                        # Remove 'None' values
                        row_at_index = [
                            "" if item in ["None", "NONE"] else item
                            for item in row_at_index
                        ]

                        # get tuple of leg values
                        row_at_index = (0,) + tuple(row_at_index)

                        # append tuple in list
                        list_of_tuple_of_values.append(row_at_index)

                    indx_tag += 1

                    # check if structure is mismatched
                    if indx_tag >= seq_end:
                        # Error Message
                        error_title = (
                            f"Error, structure of {tags_list[indx_tag - 1]} is invalid"
                        )
                        error_string = f"Error, structure of {tags_list[indx_tag - 1]} is invalid, , at line no: {seq_end + 2}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                # init
                combination_obj = None

                # if cas type is add or switch
                if cas_type in ["ADD", "SWITCH"]:

                    # Create combination one by one
                    combination_obj = create_combo_wrapper(
                        list_of_tuple_of_values,
                        indx_tag,
                        input_from_db=True,
                        input_from_cas_tab=True,
                        input_series=True,
                    )

                    # check if there is error msg in return object
                    if isinstance(combination_obj, tuple):
                        # Error Message
                        error_title = combination_obj[1]
                        error_string = combination_obj[2] + f", at line no: {indx_tag}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                # check position of start of sequence position
                if (
                    cas_type in ["ADD", "SWITCH"]
                    and tags_list[indx_tag + 1] != "#StartOfSequencePosition"
                ):
                    # Error Message
                    error_title = f"Error, #StartOfSequencePosition not present"
                    error_string = f"Error, #StartOfSequencePosition not present, at line no: {indx_tag + 1}"

                    error_string = make_multiline_mssg_for_gui_popup(error_string)

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                indx_tag += 2

                # init
                target_position_dict = {}
                ref_pos_dict = {}

                # iterate till app encounter end of sequence position tag
                while (
                    cas_type in ["ADD", "SWITCH"]
                    and tags_list[indx_tag] != "#EndOfSequencePosition"
                ):

                    if tags_list[indx_tag] != "#SequencePosition":
                        # Error Message
                        error_title = (
                            f"Error, position of {tags_list[indx_tag]} is invalid"
                        )
                        error_string = f"Error, position of {tags_list[indx_tag]} is invalid, at line no: {indx_tag + 2}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    # get values
                    account = series_dataframe.at[indx_tag, "Column 1"]
                    target_pos = series_dataframe.at[indx_tag, "Column 2"]

                    # check if account id is valid
                    if account not in variables.current_session_accounts:
                        # Error Message
                        error_title = (
                            f"Error, account ID for {tags_list[indx_tag]} is invalid"
                        )
                        error_string = f"Error, account ID for {tags_list[indx_tag]} is invalid, at line no: {indx_tag + 2}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    # check if target position is valid
                    if not target_pos.lstrip("-").isnumeric():
                        # Error Message
                        error_title = (
                            f"Error, position for {tags_list[indx_tag]} is invalid"
                        )
                        error_string = f"Error, position for {tags_list[indx_tag]} is invalid, at line no: {indx_tag + 2}"

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    # map account to position
                    target_position_dict[account] = target_pos

                    ref_pos_dict[account] = 0

                    indx_tag += 1

                    # check if structure is mismatched
                    if indx_tag >= seq_end:
                        # Error Message
                        error_title = (
                            f"Error, structure of {tags_list[indx_tag - 1]} is invalid"
                        )
                        error_string = (
                            f"Error, structure of {tags_list[indx_tag - 1]} is invalid"
                        )

                        error_string = make_multiline_mssg_for_gui_popup(error_string)

                        variables.screen.display_error_popup(error_title, error_string)

                        return

                    # chekc if combo obj is not none
                    if combination_obj != None:

                        ticker_info_string = make_informative_combo_string(
                            combination_obj
                        )

                if flag_multi and cas_type in ["BUY", "SELL"]:

                    # Init
                    map_account_to_quanity_dict = {}

                    try:

                        # Getting initial trigger price
                        price = (
                            variables.unique_id_to_prices_dict[int(trading_uid_seq)][
                                "BUY"
                            ]
                            + variables.unique_id_to_prices_dict[int(trading_uid_seq)][
                                "SELL"
                            ]
                        ) / 2

                        # Iterating account ids
                        for account in account_id.split("|"):

                            # Getting value of account parameter
                            if variables.account_parameter_for_order_quantity == "NLV":

                                value_of_account_parameter = (
                                    variables.accounts_table_dataframe.loc[
                                        variables.accounts_table_dataframe["Account ID"]
                                        == account,
                                        variables.accounts_table_columns[1],
                                    ].iloc[0]
                                )

                            elif (
                                variables.account_parameter_for_order_quantity == "SMA"
                            ):

                                value_of_account_parameter = (
                                    variables.accounts_table_dataframe.loc[
                                        variables.accounts_table_dataframe["Account ID"]
                                        == account,
                                        variables.accounts_table_columns[2],
                                    ].iloc[0]
                                )

                            elif (
                                variables.account_parameter_for_order_quantity == "CEL"
                            ):

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

                                variables.screen.display_error_popup(
                                    error_title, error_string
                                )
                                return

                            # Check if account parameter value is invalid
                            if not is_float(value_of_account_parameter):
                                error_title = "Invalid Account Parameter Value"
                                error_string = f"For Account ID: {account}, Value of account Parameter: {variables.account_parameter_for_order_quantity} is invalid"

                                variables.screen.display_error_popup(
                                    error_title, error_string
                                )
                                return

                            # Calculate combo qunaity for account id
                            if float(price) != 0:

                                # get quantity in percentage
                                combo_quantity = float(qnty_seq)

                                # get rounded value for quantity
                                combo_quantity_for_account = round(
                                    (
                                        (combo_quantity / 100)
                                        * float(value_of_account_parameter)
                                    )
                                    / abs(float(price))
                                )

                            else:

                                # set to zero
                                combo_quantity_for_account = 0

                            # add it to dictionary
                            target_position_dict[account] = combo_quantity_for_account

                            ref_pos_dict[account] = 0

                    except Exception as e:

                        # error message
                        error_title = f"For Unique ID: {base_uid}, Could not get quantity for accounts"
                        error_string = f"For Unique ID: {base_uid}, Could not get quantity for accounts"

                        variables.screen.display_error_popup(error_title, error_string)
                        return

                if len(target_position_dict) != len(
                    variables.current_session_accounts
                ) and cas_type in ["ADD", "SWITCH"]:
                    # error message
                    error_title = f"For Unique ID: {base_uid}, number of accounts are invalid for sequence positions"
                    error_string = f"For Unique ID: {base_uid}, number of accounts are invalid for sequence positions"

                    variables.screen.display_error_popup(error_title, error_string)
                    return

                # replace % by %%
                condition = condition.replace("%", "%%")

                # make '' to 'None'
                if ticker_info_string == "":
                    ticker_info_string = "None"

                # capitalize it
                order_type = order_type.title()

                # Watchlist cas condition dataframe update
                cas_condition_row_values = (
                    base_uid,
                    trading_uid_seq,
                    eval_uid_seq_val,
                    cas_type,
                    ticker_info_string,
                    condition,
                    "Queued",
                    order_type,
                    qnty_seq,
                    limit_price,
                    trigger_price,
                    trail_value,
                    atr_multiple,
                    ind_seq,
                    combination_obj,
                    ref_pos_dict,
                    target_position_dict,
                )

                # Creating dataframe for row data
                cas_condition_row_df = pd.DataFrame(
                    [cas_condition_row_values],
                    columns=variables.series_sequence_tble_columns,
                )

                # Merge row with combo details dataframe
                sequence_df = pd.concat([sequence_df, cas_condition_row_df])

            # ge vlaues
            eval_uid = series_dataframe.at[1, "Column 1"]
            condition_text = series_dataframe.at[1, "Column 2"]
            series_id_cond = series_dataframe.at[1, "Column 3"]

            # init
            flag_condition_passed = True

            try:

                if (isinstance(eval_uid, str) and eval_uid.isnumeric()) or isinstance(
                    eval_uid, int
                ):

                    reference_price = (
                        variables.unique_id_to_prices_dict[int(eval_uid)]["BUY"]
                        + variables.unique_id_to_prices_dict[int(eval_uid)]["SELL"]
                    ) / 2

                else:

                    reference_price = None

            except Exception as e:

                reference_price = None

                if variables.flag_debug_mode:

                    print(f"Exception for getting price for combo, Exp: {e}")

            if (
                "Price Increase By" in condition_text
                or "Price Decrease By" in condition_text
            ) and reference_price == None:
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Reference price not available for series condition"
                variables.screen.display_error_popup(error_title, error_string)

                return

            reference_position = None

            if len(variables.current_session_accounts) == 1:

                if (
                    "Price Adverse Chg By" in condition_text
                    or "Price Favorable Chg By" in condition_text
                ) and reference_price == None:
                    # Error Message
                    error_title = (
                        error_string
                    ) = f"Error, Reference price not available for series condition"
                    variables.screen.display_error_popup(error_title, error_string)

                    return

                # Trying to get the reference positions
                try:
                    local_unique_id_to_positions_dict = copy.deepcopy(
                        variables.map_unique_id_to_positions
                    )

                    if (
                        isinstance(eval_uid, str) and eval_uid.isnumeric()
                    ) or isinstance(eval_uid, int):

                        reference_position = local_unique_id_to_positions_dict[
                            int(eval_uid)
                        ][variables.current_session_accounts[0]]

                    else:
                        reference_position = None

                except Exception as e:

                    reference_position = None

                    if variables.flag_debug_mode:
                        print(e)

                if (
                    "Price Adverse Chg By" in condition_text
                    or "Price Favorable Chg By" in condition_text
                ) and reference_position in [None]:
                    # Error Message
                    error_title = (
                        error_string
                    ) = f"Error, Reference position not available for series condition"
                    variables.screen.display_error_popup(error_title, error_string)

                    return

                if (
                    "Price Adverse Chg By" in condition_text
                    or "Price Favorable Chg By" in condition_text
                ) and reference_position == 0:
                    # Error Message
                    error_title = (
                        error_string
                    ) = f"Error, Reference position should not be 0 for series condition"
                    variables.screen.display_error_popup(error_title, error_string)

                    return

            else:

                if (
                    "Price Adverse Chg By" in condition_text
                    or "Price Favorable Chg By" in condition_text
                ):
                    # Error Message
                    error_title = (
                        error_string
                    ) = f"Error, Price favourable/Adverse not allowed for multiple accounts\nin series condition"
                    variables.screen.display_error_popup(error_title, error_string)

                    return

                condition_list = sequence_df["Condition"].to_list()

                for condition_item in condition_list:

                    if (
                        "Price Adverse Chg By" in condition_item
                        or "Price Favorable Chg By" in condition_item
                    ):
                        # Error Message
                        error_title = (
                            error_string
                        ) = f"Error, Price favourable/Adverse not allowed for multiple accounts\nin sequence condition"
                        variables.screen.display_error_popup(error_title, error_string)

                        return

            # check if conition text is not none
            if condition_text != "None":

                # Validate Condition Here
                flag_condition_passed, error_string = check_basic_condition(
                    condition_text, None, reference_price, None
                )

            # check if both conditions are empty
            '''if condition_text == "None" and series_id_cond == "None":
                # Error Message
                error_title = (
                    f"Error, Both combination condition and series condition are empty"
                )
                error_string = f"Error, Both combination condition and series condition are empty, at line no: {3}"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return'''

            # check if eval uid is not present
            if condition_text != "None" and eval_uid == "None":
                # Error Message
                error_title = f"Error, Evalaution unique id should be present"
                error_string = f"Error, Evalaution unique id should be present, at line no: {3}"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if condition is valid
            if condition_text != "None" and not flag_condition_passed:
                # Error Message
                error_title = f"Error, Condition is invalid"
                error_string = (
                    f"Error, Condition is invalid, at line no: {3}"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return



            # check if eval uid is valid
            if condition_text != "None" and not eval_uid.isnumeric():
                # Error Message
                error_title = f"Error, Evaluation unique id should be numeric"
                error_string = f"Error, Evaluation unique id should be numeric, at line no: {3}"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if eval uid is valid
            if condition_text == "None" and eval_uid != 'None':
                # Error Message
                error_title = f"Error, For evaluation unique id condition text not available"
                error_string = f"Error, For evaluation unique id condition text not available, at line no: {3}"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if eval uid is in system
            if eval_uid.isnumeric() and int(eval_uid) not in all_unique_ids_in_system:
                # Error Message
                error_title = f"Error, Evalaution unique id is not in system"
                error_string = f"Error, Evalaution unique id is not in system, at line no: {3}"

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if series id is numeric
            if not series_id_cond.isnumeric() and series_id_cond != "None":
                # Error Message
                error_title = f"Error, Series id should be numeric"
                error_string = (
                    f"Error, Series id should be numeric, at line no: {3}"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if sries id is not in system
            if (
                series_id_cond != "None"
                and int(series_id_cond) not in all_series_ids_in_system
            ):
                # Error Message
                error_title = f"Error, Series id not in system"
                error_string = (
                    f"Error, Series id not in system, at line no: {3}"
                )

                error_string = make_multiline_mssg_for_gui_popup(error_string)

                variables.screen.display_error_popup(error_title, error_string)

                return

            # get series id
            series_id = get_series_id_db()

            # make empty fields None
            if eval_uid == "":
                eval_uid = "None"

            # make empty fields None
            if condition_text == "":
                condition_text = "None"

            # make empty fields None
            if series_id_cond == "":
                series_id_cond = "None"

            # increment series id
            series_id += 1

            # get max sequence id present
            sequence_id = get_sequence_id_db()

            # increment sequence id
            sequence_id += 1

            # get total sequences for series
            total_sequences = len(sequence_df)

            # init
            sequences_completed = sequence_df["Status"].to_list().count("Completed")

            # Init
            status = "Parked"

            bypass_rm_check = bypass_rm_check.title()

            # get boolean value for execution engine flag
            if execution_engine in ["TRUE", "True", "true"]:

                execution_engine = True

            else:

                execution_engine = False

            condition_text = condition_text.replace("%", "%%")

            account_id = account_id.replace("|", ",")

            # create list of values
            values_list = [
                series_id,
                base_uid,
                account_id,
                total_sequences,
                sequences_completed,
                status,
                bypass_rm_check,
                execution_engine,
                eval_uid,
                condition_text,
                series_id_cond,
                "No",
                flag_multi,
                reference_price,
                reference_position,
            ]

            # Create a dictionary from the list of values and columns
            values_dict = dict(
                zip(variables.conditional_series_table_columns, values_list)
            )

            # insert series in db
            series_query = (
                insert_conditional_series_instance_values_to_conditional_series_table(
                    values_dict, return_only=True
                )
            )

            # Create a new column with incremental values
            sequence_df["Sequence ID"] = [sequence_id] + list(
                range(
                    sequence_id + 1,
                    sequence_id + tags_list.count("#StartOfSequence"),
                )
            )

            sequence_df = sequence_df.reset_index(drop=True)

            # Change the value of 'Status' at index 0 to 'New Status'
            sequence_df.loc[0, "Status"] = "Active"

            # Create a new column with series id
            sequence_df["Series ID"] = series_id

            # get value of positions
            target_positions_list = sequence_df["Target Position"]
            reference_positions_list = sequence_df["Reference Position"]

            # get list of sequence ids list
            sequence_id_list = sequence_df["Sequence ID"]

            pos_query_list = []

            # insert sequences postions in db
            for target_position, reference_position, sequence_id in zip(
                target_positions_list, reference_positions_list, sequence_id_list
            ):

                if target_position not in ["None", None]:
                    pos_query = insert_positions_for_series(
                        reference_position,
                        target_position,
                        sequence_id,
                        series_id,
                        base_uid,
                        return_only=True,
                    )

                    pos_query_list.append(pos_query)

            # make position column none
            sequence_df["Reference Position"] = "None"

            # make position column none
            sequence_df["Target Position"] = "None"

            # get list of combo objests
            combo_obj_list = sequence_df["Combo Obj"]

            cas_legs_query_list = []

            # insert combo objects of sequences
            for combo_obj, sequence_id_combo in zip(combo_obj_list, sequence_id_list):

                if combo_obj not in ["None", None]:
                    cas_legs_query = insert_cas_legs_for_series_db(
                        combo_obj,
                        sequence_id_combo,
                        series_id,
                        base_uid,
                        return_only=True,
                    )

                    cas_legs_query_list.append(cas_legs_query)

            # print(variables.series_sequence_table_df.to_string())

            # get copy of df
            local_conditional_series_sequence_df = sequence_df[
                variables.conditional_series_sequence_table_columns
            ].copy()

            # Iterate over rows and create a dictionary for each row
            row_dicts = [
                row.to_dict()
                for _, row in local_conditional_series_sequence_df.iterrows()
            ]

            sequence_query_list = []

            # insert sequences
            for row_dict in row_dicts:
                sequence_query = insert_conditional_series_sequence_instance_values_to_conditional_series_sequence_table(
                    row_dict, return_only=True
                )

                sequence_query_list.append(sequence_query)

            execute_all_insert_queries(
                series_query, pos_query_list, cas_legs_query_list, sequence_query_list
            )

            # update GUI table
            self.update_conditional_series_table()

            # print('success')

        except Exception as e:

            print(f"Exception inside 'import series', Exp: {e}")

    # Method to upload series from app to csv file
    def import_series(self, upload_series_button):

        # Disabled upload combinations button
        upload_series_button.config(state="disabled")

        # Pop up to select file
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            # Place combinations based on values in CSV
            upload_combo_thread = threading.Thread(
                target=self.upload_series_from_csv_to_app,
                args=(
                    file_path,
                    upload_series_button,
                ),
            )
            upload_combo_thread.start()

        else:

            # enabled upload combinations button
            upload_series_button.config(state="normal")

    # Method to validate order value for upload series
    def order_value_check(
        self,
        order_type,
        limit_price,
        trigger_price,
        trail_value,
        atr_multiple,
        buy_sell_action,
        indx,
        unique_id,
    ):

        try:

            # Get latest combo prices
            prices_unique_id = copy.deepcopy(variables.unique_id_to_prices_dict)

            current_buy_price, current_sell_price = (
                prices_unique_id[unique_id]["BUY"],
                prices_unique_id[unique_id]["SELL"],
            )
        except Exception as e:
            error_title = f"Error Row no - {indx + 2}, Invalid Unique Id"
            error_string = (
                f"Row no - {indx + 2}, Please provide a valid Unique Id for Order"
            )

            return False, error_title, error_string

        # Limit Orders
        if order_type == "LIMIT":

            order_type = "LIMIT"
            try:
                limit_price = float(limit_price)

                # Check if limit price is NaN
                if math.isnan(limit_price):
                    raise Exception(f"Error, Limit Price is NULL")

            except Exception as e:
                error_title = f"Error , Missing Limit Price"
                error_string = f"Please provide a Limit Price for Limit Order"

                return False, error_title, error_string

            if (order_type == "LIMIT") and (
                buy_sell_action == "BUY" and current_buy_price < limit_price
            ):
                error_title = f"Error Row no - {indx + 2}, Invalid Limit Price."
                error_string = make_multiline_mssg_for_gui_popup(
                    f"Row no - {indx + 2}, Unique-Id - {unique_id}, Limit Price for Buy Order must be less than current Buy Price"
                )

                return False, error_title, error_string

            elif (order_type == "LIMIT") and (
                buy_sell_action == "SELL" and current_sell_price > limit_price
            ):
                error_title = f"Error Row no - {indx + 2}, Invalid Limit Price"
                error_string = make_multiline_mssg_for_gui_popup(
                    f"Row no - {indx + 2}, Unique-Id - {unique_id}, Limit Price for Sell Order must be greater than current Sell Price"
                )

                return False, error_title, error_string

        # Stop Loss Orders
        elif order_type == "STOP LOSS":

            # Check if both trigger price and atr multiple is empty
            if trigger_price == "None" and atr_multiple == "None":

                error_title = (
                    f"Error, Row no - {indx + 2}, Invalid combination of values"
                )
                error_string = make_multiline_mssg_for_gui_popup(
                    f"Error, Row no - {indx + 2}, Values for both Trigger Price and ATR Multiple must not be empty."
                )

                return False, error_title, error_string

            # Check if trigger price is valid
            elif trigger_price != "None" and atr_multiple == "None":
                try:
                    trigger_price = float(trigger_price)

                    # Check if trigger price is NaN
                    if math.isnan(trigger_price):
                        raise Exception(
                            f"Error Row no - {indx + 2}, Trigger Price is NULL"
                        )

                except Exception as e:
                    error_title = f"Error Row no - {indx + 2}, Missing Trigger Price"
                    error_string = make_multiline_mssg_for_gui_popup(
                        f"Row no - {indx + 2}, Unique-Id - {unique_id}, Please provide a Trigger Price for Stop Loss Order"
                    )

                    return False, error_title, error_string

            # Check if atr multiple is valid and have valid trigger price value
            elif (trigger_price == "None" and atr_multiple != "None") or (
                trigger_price != "None" and atr_multiple != "None"
            ):

                # Get ATR value
                atr = get_atr_value_for_unique_id(unique_id)

                # If atr is N/A return error
                if atr == "N/A":
                    error_title = f"Error, Row no - {indx + 2}, For Unique ID: {unique_id}, Unable to get ATR"
                    error_string = f"Error, Row no - {indx + 2}, For Unique ID: {unique_id}, Unable to get ATR"

                    return False, error_title, error_string

                # checking if atr multiple value is valid
                try:
                    atr_multiple = float(atr_multiple)

                    # Make trigger price None
                    trigger_price = "None"

                    # check if atrr multiple is less than or equal to zero
                    if atr_multiple <= 0:
                        raise Exception("Invalid ATR Multiple")

                except Exception as e:
                    error_title = f"Error, Row no - {indx + 2}, Invalid ATR Multiple"
                    error_string = f"Error, Row no - {indx + 2}, Please provide a valid ATR Multiple for Stop Loss Order."

                    return False, error_title, error_string

                # checking if trigger price calculations are valid
                trigger_price = get_trigger_price_for_stop_loss(
                    unique_id, buy_sell_action, atr_multiple, atr
                )

                if trigger_price == "N/A":
                    error_title = f"Error, Row no - {indx + 2},Invalid Trigger Price"
                    error_string = f"Error, Row no - {indx + 2},Unable to get valid Trigger Price based on ATR Multiple: {atr_multiple}, \nATR: {atr}"

                    return False, error_title, error_string

            if (order_type == "STOP LOSS") and (
                buy_sell_action == "BUY" and current_buy_price > trigger_price
            ):
                error_title = f"Error Row no - {indx + 2}, Invalid Trigger Price"
                error_string = make_multiline_mssg_for_gui_popup(
                    f"Row no - {indx + 2}, Unique-Id - {unique_id}, Trigger Price for Buy Order must be greater than current Buy Price"
                )

                return False, error_title, error_string

            elif (order_type == "STOP LOSS") and (
                buy_sell_action == "SELL" and current_sell_price < trigger_price
            ):
                error_title = f"Error Row no - {indx + 2}, Invalid Trigger Price"
                error_string = make_multiline_mssg_for_gui_popup(
                    f"Row no - {indx + 2}, Unique-Id - {unique_id}, Trigger Price for Sell Order must be lower than current Sell Price"
                )

                return False, error_title, error_string

        # Trailing Stop Loss Orders
        elif order_type == "TRAILING STOP LOSS":

            # Check if both trail value and atr multiple is empty
            if trail_value == "None" and atr_multiple == "None":

                error_title = (
                    f"Error, Row no - {indx + 2}, Invalid combination of values"
                )
                error_string = f"Error, Row no - {indx + 2}, Values for both Trail Value and ATR Multiple must not be empty."

                return False, error_title, error_string

            # Check if trail value is valid
            elif trail_value != "None" and atr_multiple == "None":
                try:
                    trail_value = float(trail_value)

                    # Make ATR value empty in case of not using ATR multiplier in trailing stop loss order
                    atr = ""
                except Exception as e:
                    error_title = f"Error, Row no - {indx + 2},Invalid Trail Value"
                    error_string = f"Error, Row no - {indx + 2},Please provide a valid Trail Value for Stop Loss Order."

                    return False, error_title, error_string

            # Check if atr multiple is valid and get valid trail value
            elif (trail_value == "None" and atr_multiple != "None") or (
                trail_value != "None" and atr_multiple != "None"
            ):

                # Get ATR value
                atr = get_atr_value_for_unique_id(unique_id)

                # If atr is N/A return error
                if atr == "N/A":
                    error_title = f"Error, Row no - {indx + 2},For Unique ID: {unique_id}, Unable to get ATR"
                    error_string = f"Error, Row no - {indx + 2},For Unique ID: {unique_id}, Unable to get ATR"

                    return False, error_title, error_string

                # checking if atr multiple value is valid
                try:
                    atr_multiple = float(atr_multiple)

                    # Make trail value None
                    trail_value = "None"

                    # check if atr multiple is less than or equal to zero
                    if atr_multiple <= 0:
                        raise Exception("Invalid ATR Multiple")

                except Exception as e:
                    error_title = f"Error, Row no - {indx + 2},Invalid ATR Multiple"
                    error_string = f"Error, Row no - {indx + 2},Please provide a valid ATR Multiple for Stop Loss Order."

                    return False, error_title, error_string

                # checking if trail value calcualtions are valid
                trail_value = get_trail_value_for_trailing_stop_loss(atr_multiple, atr)

                if trail_value == "N/A":
                    error_title = f"Error, Row no - {indx + 2},Invalid Trigger Price"
                    error_string = f"Error, Row no - {indx + 2},Unable to get valid Trail Value based on ATR Multiple: {atr_multiple} and ATR: {atr}"

                    return False, error_title, error_string

        return True, "No Error", "No Error"

    # Method to download series to csv file
    def export_series(self):

        try:

            try:

                # get values from selected rows
                selected_item = self.conditional_series_table.selection()[0]

            except Exception as e:

                return

            # get the item ID of the selected row
            values = self.conditional_series_table.item(selected_item, "values")

            # get values for selected series
            unique_id = int(values[1])
            user_condition = values[9]
            eval_uid = values[8]
            series_id_cond = values[10]
            account_id = values[2]
            bypass_rm_check = values[6]
            execution_engine = values[7]

            account_id = account_id.replace(",", "|")

            # Creating list for empty values
            palce_holder_list = [""] * (15)
            series_dataframe_columns = ["#StartOfSeries"] + [""] * 15

            series_dataframe_to_csv = pd.DataFrame(columns=series_dataframe_columns)

            # create list for start of combination row
            """data_list = [["#StartOfSeries"] + palce_holder_list]
            series_row_values_dataframe = pd.DataFrame(
                data_list, columns=series_dataframe_columns
            )
    
            series_dataframe_to_csv = pd.concat([series_dataframe_to_csv, series_row_values_dataframe], ignore_index=True)"""

            palce_holder_list = [""] * (12)

            # create list for start of combination row
            data_list = [
                [
                    "#StartOfSeriesCondition",
                    "Evaluation Unique ID",
                    "Combination Condition",
                    "Series ID Condition",
                ]
                + palce_holder_list
            ]
            series_row_values_dataframe = pd.DataFrame(
                data_list, columns=series_dataframe_columns
            )

            # create datafrae
            series_dataframe_to_csv = pd.concat(
                [series_dataframe_to_csv, series_row_values_dataframe],
                ignore_index=True,
            )

            # place holder list
            palce_holder_list = [""] * (12)

            # create list for start of combination row
            data_list = [
                ["#SeriesConditionValues", eval_uid, user_condition, series_id_cond]
                + palce_holder_list
            ]
            series_row_values_dataframe = pd.DataFrame(
                data_list, columns=series_dataframe_columns
            )

            # concat to df
            series_dataframe_to_csv = pd.concat(
                [series_dataframe_to_csv, series_row_values_dataframe],
                ignore_index=True,
            )

            # Creating list for empty values
            palce_holder_list = [""] * (15)

            # create list for start of combination row
            data_list = [["#EndOfSeriesCondition"] + palce_holder_list]
            series_row_values_dataframe = pd.DataFrame(
                data_list, columns=series_dataframe_columns
            )

            # conat to df
            series_dataframe_to_csv = pd.concat(
                [series_dataframe_to_csv, series_row_values_dataframe],
                ignore_index=True,
            )

            # place holder list
            palce_holder_list = [""] * (11)

            # create list for start of combination row
            data_list = [
                [
                    "#StartOfSeriesValues",
                    "Base Unique ID",
                    "Account ID",
                    "Bypass RM Check",
                    "Execution Engine",
                ]
                + palce_holder_list
            ]

            series_row_values_dataframe = pd.DataFrame(
                data_list, columns=series_dataframe_columns
            )

            # concat to df
            series_dataframe_to_csv = pd.concat(
                [series_dataframe_to_csv, series_row_values_dataframe],
                ignore_index=True,
            )

            # place holder list
            palce_holder_list = [""] * (11)

            # create list for start of combination row
            data_list = [
                [
                    "#SeriesValues",
                    unique_id,
                    account_id,
                    bypass_rm_check,
                    execution_engine,
                ]
                + palce_holder_list
            ]
            series_row_values_dataframe = pd.DataFrame(
                data_list, columns=series_dataframe_columns
            )

            series_dataframe_to_csv = pd.concat(
                [series_dataframe_to_csv, series_row_values_dataframe],
                ignore_index=True,
            )

            # Creating list for empty values
            palce_holder_list = [""] * (15)

            # create list for start of combination row
            data_list = [["#EndOfSeriesValues"] + palce_holder_list]
            series_row_values_dataframe = pd.DataFrame(
                data_list, columns=series_dataframe_columns
            )

            # concat to df
            series_dataframe_to_csv = pd.concat(
                [series_dataframe_to_csv, series_row_values_dataframe],
                ignore_index=True,
            )

            series_id = int(values[0])

            # get all sequences of selected series
            series_seq_df_db = get_all_sequences_of_series(series_id)

            # get list of sequence ids
            sequence_ids_list = series_seq_df_db["Sequence ID"].to_list()

            # get list of cas types
            cas_type_lst = series_seq_df_db["Add/Switch/Buy/Sell"].to_list()

            # # get list of quantities
            qnty_lst = series_seq_df_db["#Lots"].to_list()

            # inti
            combo_obj_lst = []
            ref_position_lst = []

            target_postions_lst = []

            # check sequence id, cas type and quanity for each row
            for (seq_id, cas_type_db, qnty) in zip(
                sequence_ids_list, cas_type_lst, qnty_lst
            ):

                # check if cas type is add or switch
                if cas_type_db in ["ADD", "SWITCH"]:

                    # Creates and return combolegs dict, for further process (combo_creation, inserting in cas condition table and viewing)
                    sequence_id_to_combolegs_df = get_series_cas_legs_df(seq_id)

                    # init
                    flag_multi_account = True

                    # legs columns
                    leg_columns = [
                        "Sequence ID",
                        "Series ID",
                        "Action",
                        "SecType",
                        "Symbol",
                        "DTE",
                        "Delta",
                        "Right",
                        "#Lots",
                        "Lot Size",
                        "Exchange",
                        "Trading Class",
                        "Currency",
                        "ConID",
                        "Primary Exchange",
                        "Strike",
                        "Expiry",
                    ]

                    # rearrange data frame
                    sequence_id_to_combolegs_df = sequence_id_to_combolegs_df[
                        leg_columns
                    ]

                    # convert fisrt row of df to tuple
                    """legs_tuple_list = [
                        (unique_id,) + tuple(sequence_id_to_combolegs_df.iloc[0, 2:])
                    ]"""

                    legs_tuple_list = []

                    for ind, row_df in sequence_id_to_combolegs_df.iterrows():
                        legs_tuple_list.append((unique_id,) + tuple(row_df[2:]))

                    # create combo object
                    cas_combo_object = create_combination(
                        legs_tuple_list, input_from_db=True, input_from_cas_tab=True
                    )

                    combo_obj_lst.append(cas_combo_object)

                    # get position for add or switch
                    positions_df = get_positions_from_series_positions_table(seq_id)

                    # Create a dictionary from the DataFrame
                    account_reference_positions_dict = dict(
                        zip(
                            positions_df["Account ID"],
                            positions_df["Reference Position"],
                        )
                    )

                    # Create a dictionary from the DataFrame
                    account_target_positions_dict = dict(
                        zip(positions_df["Account ID"], positions_df["Target Position"])
                    )

                    # get lsit of account ids
                    account_id = positions_df["Account ID"].to_list()

                    # append
                    ref_position_lst.append(account_reference_positions_dict)

                    target_postions_lst.append(account_target_positions_dict)

                else:

                    # check if quantity is none for buy or sell
                    if qnty in ["None"]:
                        # get position for add or switch
                        positions_df = get_positions_from_series_positions_table(seq_id)

                        # Create a dictionary from the DataFrame
                        combo_quantity = dict(
                            zip(
                                positions_df["Account ID"],
                                positions_df["Target Position"],
                            )
                        )

                        target_postions_lst.append(combo_quantity)

                        # Create a dictionary from the DataFrame
                        account_reference_positions_dict = dict(
                            zip(
                                positions_df["Account ID"],
                                positions_df["Reference Position"],
                            )
                        )

                        # append
                        combo_obj_lst.append("None")

                        ref_position_lst.append(account_reference_positions_dict)

                    else:

                        # append
                        combo_obj_lst.append("None")
                        ref_position_lst.append("None")
                        target_postions_lst.append("None")

            # add new columns in df
            series_seq_df_db["Combo Obj"] = combo_obj_lst

            series_seq_df_db["Reference Position"] = ref_position_lst

            series_seq_df_db["Target Position"] = target_postions_lst

            for ind, row in series_seq_df_db.iterrows():

                palce_holder_list = [""] * (15)

                # create list for start of combination row
                data_list = [["#StartOfSequence"] + palce_holder_list]
                series_row_values_dataframe = pd.DataFrame(
                    data_list, columns=series_dataframe_columns
                )

                series_dataframe_to_csv = pd.concat(
                    [series_dataframe_to_csv, series_row_values_dataframe],
                    ignore_index=True,
                )

                palce_holder_list = [""] * (5)

                # create list for start of combination row
                data_list = [
                    [
                        "#StartOfSequenceValues",
                        "Trading UID",
                        "Evaluation UID",
                        "Cas Type",
                        "Condition",
                        "Order Type",
                        "#Lots/(Qty)",
                        "Limit Price",
                        "Trigger Price",
                        "Trail Value",
                        "ATR Multiple",
                    ]
                    + palce_holder_list
                ]
                series_row_values_dataframe = pd.DataFrame(
                    data_list, columns=series_dataframe_columns
                )

                series_dataframe_to_csv = pd.concat(
                    [series_dataframe_to_csv, series_row_values_dataframe],
                    ignore_index=True,
                )

                # place holder list
                palce_holder_list = [""] * (5)

                # get values
                trading_uid = row["Trading Unique ID"]
                evaluation_uid = row["Evaluation Unique ID"]
                cas_type = row["Add/Switch/Buy/Sell"]
                condition = row["Condition"]
                order_type = row["Order Type"]
                qnty = row["#Lots"]
                limit_price = row["Limit Price"]
                trigger_price = row["Trigger Price"]
                trail_value = row["Trail Value"]
                atr_multiple = row["ATR Multiple"]

                # create list for start of combination row
                data_list = [
                    [
                        "#SequenceValues",
                        trading_uid,
                        evaluation_uid,
                        cas_type,
                        condition,
                        order_type,
                        qnty,
                        limit_price,
                        trigger_price,
                        trail_value,
                        atr_multiple,
                    ]
                    + palce_holder_list
                ]
                series_row_values_dataframe = pd.DataFrame(
                    data_list, columns=series_dataframe_columns
                )

                series_dataframe_to_csv = pd.concat(
                    [series_dataframe_to_csv, series_row_values_dataframe],
                    ignore_index=True,
                )

                palce_holder_list = [""] * (15)

                # create list for start of combination row
                data_list = [["#EndOfSequenceValues"] + palce_holder_list]
                series_row_values_dataframe = pd.DataFrame(
                    data_list, columns=series_dataframe_columns
                )

                series_dataframe_to_csv = pd.concat(
                    [series_dataframe_to_csv, series_row_values_dataframe],
                    ignore_index=True,
                )

                # in case of add or switch
                if cas_type in ["ADD", "SWITCH"]:

                    # create list for start of combination row
                    data_list = [
                        [
                            "#StartOfSequenceLeg",
                            "Action",
                            "SecType",
                            "Symbol",
                            "DTE",
                            "Delta",
                            "Right",
                            "#Lots",
                            "Multiplier",
                            "Exchange",
                            "Trading Class",
                            "Currency",
                            "ConID",
                            "Primary Exchange",
                            "Strike",
                            "Expiry",
                        ]
                    ]
                    series_row_values_dataframe = pd.DataFrame(
                        data_list, columns=series_dataframe_columns
                    )

                    series_dataframe_to_csv = pd.concat(
                        [series_dataframe_to_csv, series_row_values_dataframe],
                        ignore_index=True,
                    )

                    palce_holder_list = [""] * (5)

                    combo_obj = row["Combo Obj"]

                    # Buy legs and Sell legs
                    buy_legs = combo_obj.buy_legs
                    sell_legs = combo_obj.sell_legs
                    all_legs = buy_legs + sell_legs

                    for leg_obj in all_legs:

                        # create list for start of combination row
                        data_list = [
                            [
                                "#SequenceLeg",
                                leg_obj.action,
                                leg_obj.sec_type,
                                leg_obj.symbol,
                                leg_obj.dte,
                                leg_obj.delta,
                                leg_obj.right,
                                leg_obj.quantity,
                                leg_obj.multiplier,
                                leg_obj.exchange,
                                leg_obj.trading_class,
                                leg_obj.currency,
                                leg_obj.con_id,
                                leg_obj.primary_exchange,
                                leg_obj.strike_price,
                                leg_obj.expiry_date,
                            ]
                        ]
                        series_row_values_dataframe = pd.DataFrame(
                            data_list, columns=series_dataframe_columns
                        )

                        series_dataframe_to_csv = pd.concat(
                            [series_dataframe_to_csv, series_row_values_dataframe],
                            ignore_index=True,
                        )

                    palce_holder_list = [""] * (15)

                    # create list for start of combination row
                    data_list = [["#EndOfSequenceLeg"] + palce_holder_list]
                    series_row_values_dataframe = pd.DataFrame(
                        data_list, columns=series_dataframe_columns
                    )

                    series_dataframe_to_csv = pd.concat(
                        [series_dataframe_to_csv, series_row_values_dataframe],
                        ignore_index=True,
                    )

                    palce_holder_list = [""] * (13)

                    # create list for start of combination row
                    data_list = [
                        ["#StartOfSequencePosition", "Account ID", "Target Position"]
                        + palce_holder_list
                    ]
                    series_row_values_dataframe = pd.DataFrame(
                        data_list, columns=series_dataframe_columns
                    )

                    series_dataframe_to_csv = pd.concat(
                        [series_dataframe_to_csv, series_row_values_dataframe],
                        ignore_index=True,
                    )

                    palce_holder_list = [""] * (13)

                    target_postion_dict = row["Target Position"]

                    for targ_pos_row in target_postion_dict:
                        # create list for start of combination row
                        data_list = [
                            [
                                "#SequencePosition",
                                targ_pos_row,
                                target_postion_dict[targ_pos_row],
                            ]
                            + palce_holder_list
                        ]
                        series_row_values_dataframe = pd.DataFrame(
                            data_list, columns=series_dataframe_columns
                        )

                        series_dataframe_to_csv = pd.concat(
                            [series_dataframe_to_csv, series_row_values_dataframe],
                            ignore_index=True,
                        )

                    palce_holder_list = [""] * (15)

                    # create list for start of combination row
                    data_list = [["#EndOfSequencePosition"] + palce_holder_list]
                    series_row_values_dataframe = pd.DataFrame(
                        data_list, columns=series_dataframe_columns
                    )

                    series_dataframe_to_csv = pd.concat(
                        [series_dataframe_to_csv, series_row_values_dataframe],
                        ignore_index=True,
                    )

                palce_holder_list = [""] * (15)

                # create list for start of combination row
                data_list = [["#EndOfSequence"] + palce_holder_list]
                series_row_values_dataframe = pd.DataFrame(
                    data_list, columns=series_dataframe_columns
                )

                series_dataframe_to_csv = pd.concat(
                    [series_dataframe_to_csv, series_row_values_dataframe],
                    ignore_index=True,
                )

            palce_holder_list = [""] * (15)

            # create list for start of combination row
            data_list = [["#EndOfSeries"] + palce_holder_list]
            series_row_values_dataframe = pd.DataFrame(
                data_list, columns=series_dataframe_columns
            )

            series_dataframe_to_csv = pd.concat(
                [series_dataframe_to_csv, series_row_values_dataframe],
                ignore_index=True,
            )

            # Open a file dialog to choose the save location and filename
            file_path = filedialog.asksaveasfilename(defaultextension=".csv")

            # Check if a file path was selected
            if file_path:
                # Save the DataFrame as a CSV file
                series_dataframe_to_csv.to_csv(file_path, index=False)
        except Exception as e:

            print(f"Exception Inoside 'export_series Exp: {e}")




    # Method to edit series
    def edit_series(self):

        try:

            # get values from selected rows
            selected_item = self.conditional_series_table.selection()[0]

        except Exception as e:

            return

        # get the item ID of the selected row
        values = self.conditional_series_table.item(selected_item, "values")

        # get the values of the selected row
        status = values[5]
        series_id = int(values[0])

        # check if series is completed or not
        if status in ["Active"]:
            # Throw Error Popup
            variables.screen.display_error_popup(
                f"Sereis ID : {series_id}, Series is active",
                "A Conditional series is active, so can not be edited.",
            )
            return

        # check if series is completed or not
        if status in ["Completed"]:
            # Throw Error Popup
            variables.screen.display_error_popup(
                f"Sereis ID : {series_id}, Series is completed",
                "A Conditional series is completed, so can not be edited.",
            )
            return

        # check if series is completed or not
        if status in ["Terminated"]:
            # Throw Error Popup
            variables.screen.display_error_popup(
                f"Sereis ID : {series_id}, Series is terminated",
                "A Conditional series is terminated, so can not be edited.",
            )
            return

        # get values for selected series
        unique_id = int(values[1])
        user_condition = values[9]
        eval_uid = values[8]
        series_id_cond = values[10]
        account_id = values[2]
        bypass_rm_check = values[6]
        execution_engine = values[7]

        mulit_account = values[12]

        positions_df = get_positions_from_series_positions_table_for_series(series_id)

        # get account id list
        account_lst = account_id.split(",")

        if not positions_df.empty:

            account_lst = account_id.split(",") + positions_df["Account ID"].to_list()

            account_lst = list(set(account_lst))

        """if isinstance(account_lst,str) and account_lst.count(',') == 0:

            if account_lst not in variables.current_session_accounts:
                # Throw Error Popup
                variables.screen.display_error_popup(
                    f"Unique ID : {unique_id}, Account ID not present in current session",
                    f"Account ID: {account_lst} not present in current session",
                )

                return

        else:"""

        fail_account_lst = []

        for accnt_id in account_lst:

            if accnt_id not in variables.current_session_accounts:
                fail_account_lst.append(accnt_id)

        if fail_account_lst != []:

            error_string = make_multiline_mssg_for_gui_popup(
                f"Account ID: {account_lst} not present in current session"
            )
            # Throw Error Popup
            variables.screen.display_error_popup(
                f"Unique ID : {unique_id}, Account ID not present in current session",
                error_string,
            )

            return

        # Init
        flag_multi = False

        if mulit_account in ["True", True]:
            flag_multi = True

        # get all sequences for series
        series_seq_df_db = get_all_sequences_of_series(series_id)

        # get sequnces ids in list
        sequence_ids_list = series_seq_df_db["Sequence ID"].to_list()

        # get cas type for each rw in list
        cas_type_lst = series_seq_df_db["Add/Switch/Buy/Sell"].to_list()

        # get quantity fir each row in list
        qnty_lst = series_seq_df_db["#Lots"].to_list()

        # iterate sequence id, cas type and quanity for each row
        """for seq_id, cas_type_row, qnty in zip(sequence_ids_list, cas_type_lst, qnty_lst):

            # if cas type is buy or sell then we check if quantity is none
            if cas_type_row in ['BUY', 'SELL']:

                # if quantity is none then series is for multiple account ids
                if qnty in ['None', None]:
                    flag_multi = True

        # check if there is not buy and sell in series and series have multiple accounts
        if account_id.count(',') > 0 and cas_type_lst.count('BUY') == 0 and cas_type_lst.count('SELL') == 0:
            flag_multi = True"""

        # values to prefill in create series pop up
        values_relaunch = {
            "Series ID": series_id,
            "Eval UID": eval_uid,
            "User Condition": user_condition,
            "Series ID Condition": series_id_cond,
            "Account ID": account_id,
            "Bypass RM Check": bypass_rm_check,
            "Execution Engine": execution_engine,
        }

        # replaicng 'None' by ''
        values_relaunch = {
            key: ("" if value == "None" else value)
            for key, value in values_relaunch.items()
        }

        # running ad conditional series
        self.add_conditional_series(
            unique_id,
            flag_multi=flag_multi,
            values_relaunch=values_relaunch,
            flag_edit=True,
        )

    # Method to relaucn series
    def relaunch_series(self):

        try:

            # get values from selected rows
            selected_item = self.conditional_series_table.selection()[0]

        except Exception as e:

            return

        # get the item ID of the selected row
        values = self.conditional_series_table.item(selected_item, "values")

        # get the values of the selected row
        status = values[5]
        series_id = int(values[0])

        # check if series is completed or not
        if status not in ["Completed", "Terminated"]:
            # Throw Error Popup
            variables.screen.display_error_popup(
                f"Sereis ID : {series_id}, Series is not completed or terminated",
                "A Conditional series is not completed or terminated,\nso can not be relaunched.",
            )
            return


        # get values for selected series
        unique_id = int(values[1])
        user_condition = values[9]
        eval_uid = values[8]
        series_id_cond = values[10]
        account_id = values[2]
        bypass_rm_check = values[6]
        execution_engine = values[7]
        mulit_account = values[12]

        positions_df = get_positions_from_series_positions_table_for_series(series_id)

        # get account id list
        account_lst = account_id.split(",")

        if not positions_df.empty:
            account_lst = account_id.split(",") + positions_df["Account ID"].to_list()

            account_lst = list(set(account_lst))

        """if isinstance(account_lst,str) and account_lst.count(',') == 0:

            if account_lst not in variables.current_session_accounts:
                # Throw Error Popup
                variables.screen.display_error_popup(
                    f"Unique ID : {unique_id}, Account ID not present in current session",
                    f"Account ID: {account_lst} not present in current session",
                )

                return

        else:"""

        fail_account_lst = []

        for accnt_id in account_lst:

            if accnt_id not in variables.current_session_accounts:
                fail_account_lst.append(accnt_id)

        if fail_account_lst != []:
            error_string = make_multiline_mssg_for_gui_popup(
                f"Account ID: {account_lst} not present in current session"
            )
            # Throw Error Popup
            variables.screen.display_error_popup(
                f"Unique ID : {unique_id}, Account ID not present in current session",
                error_string,
            )

            return

        # Init
        flag_multi = False

        if mulit_account in ["True", True]:

            flag_multi = True

        # get all sequences for series
        series_seq_df_db = get_all_sequences_of_series(series_id)

        # get sequnces ids in list
        sequence_ids_list = series_seq_df_db["Sequence ID"].to_list()

        # get cas type for each rw in list
        cas_type_lst = series_seq_df_db["Add/Switch/Buy/Sell"].to_list()

        # get quantity fir each row in list
        qnty_lst = series_seq_df_db["#Lots"].to_list()

        # iterate sequence id, cas type and quanity for each row
        """for seq_id, cas_type_row, qnty in zip(sequence_ids_list, cas_type_lst, qnty_lst):

            # if cas type is buy or sell then we check if quantity is none
            if cas_type_row in ['BUY', 'SELL']:

                # if quantity is none then series is for multiple account ids
                if qnty in ['None', None]:

                    flag_multi = True

        # check if there is not buy and sell in series and series have multiple accounts
        if account_id.count(',') > 0 and cas_type_lst.count('BUY') == 0 and cas_type_lst.count('SELL') == 0:

            flag_multi = True"""

        # values to prefill in create series pop up
        values_relaunch = {
            "Series ID": series_id,
            "Eval UID": eval_uid,
            "User Condition": user_condition,
            "Series ID Condition": series_id_cond,
            "Account ID": account_id,
            "Bypass RM Check": bypass_rm_check,
            "Execution Engine": execution_engine,
        }

        # replaicng 'None' by ''
        values_relaunch = {
            key: ("" if value == "None" else value)
            for key, value in values_relaunch.items()
        }

        # running ad conditional series
        self.add_conditional_series(
            unique_id, flag_multi=flag_multi, values_relaunch=values_relaunch
        )

    # Method to update seies in db table
    def update_unique_id_series(
        self,
        new_combo_unique_id,
        unique_id,
        new_unique_id_for_old_combo,
        flag_series=False,
        series_id=None,
    ):

        update_unique_id_series_db(
            new_combo_unique_id,
            unique_id,
            new_unique_id_for_old_combo,
            flag_series=flag_series,
            series_id=series_id,
        )

    # Method to delete series
    def delete_series(self, selected_item=None):

        if selected_item == None:

            try:

                # get values from selected rows
                selected_item = self.conditional_series_table.selection()[0]

            except Exception as e:

                return

        values = self.conditional_series_table.item(
            selected_item, "values"
        )  # get the values of the selected row
        status = values[5]
        series_id = int(values[0])

        if status in ["Active", "active"]:
            # Throw Error Popup
            variables.screen.display_error_popup(
                f"Sereis ID : {series_id}, Series is active",
                "A Condition is active, can not be deleted.",
            )
            return

        # delete from db tables
        delete_series_db(series_id)

        # update gui table
        self.update_conditional_series_table()

    # Method to start series
    def start_series(self, selected_item=None):

        flag_place_nxt_order = True

        if selected_item == None:

            try:

                # get values from selected rows
                selected_item = self.conditional_series_table.selection()[0]

            except Exception as e:

                return
            # get the item ID of the selected row

            flag_place_nxt_order = False

        # get value of selected row
        values = self.conditional_series_table.item(
            selected_item, "values"
        )  # get the values of the selected row
        status = values[5]
        series_id = int(values[0])
        account_id = values[2]
        bypass_rm_check = values[6]
        execution_engine = values[7]
        unique_id = int(values[1])

        mulit_account = values[12]

        # Init
        flag_multi = False

        if mulit_account in ["True", True]:
            flag_multi = True

        if account_id.count(",") == 0:

            if account_id not in variables.current_session_accounts:
                # Throw Error Popup
                variables.screen.display_error_popup(
                    f"Unique ID : {unique_id}, Account ID not present in current session",
                    f"Account ID: {account_id} not present in current session",
                )
                return

        else:

            fail_account_lst = []

            for accnt_id in account_id.split(","):

                if accnt_id not in variables.current_session_accounts:
                    fail_account_lst.append(accnt_id)

            if fail_account_lst != []:
                # Throw Error Popup
                variables.screen.display_error_popup(
                    f"Unique ID : {unique_id}, Account ID not present in current session",
                    f"Account ID: {account_id} not present in current session",
                )
                return

        # values to be updated
        values_to_update_dict = {"Is Started Once": "Yes"}

        update_conditional_series_table_values(series_id, values_to_update_dict)

        # check if status is already active
        if (
            status in ["Active", "Completed", "Failed", "Terminated"]
            and not flag_place_nxt_order
        ):

            return

        # check if status is already active
        if status in ["Terminated"] and flag_place_nxt_order:

            return

        # check if status is already active
        if status in ["Parked"]:
            return

        # Number of CAS Conditions that exists
        '''number_of_conditions = do_cas_condition_exists_for_unique_id_in_db(unique_id)

        # If a condition already exists, display error popup
        if number_of_conditions > 0:
            # TODO
            # Throw Error Popup
            variables.screen.display_error_popup(
                f"Unique ID : {unique_id}, Condition already exists",
                "A Condition already exists, can not add another.",
            )
            return'''


        # get active sequence for series
        active_sequence_item = get_all_sequences_of_series(series_id, flag_active=True)

        sequence_id = active_sequence_item.loc[0, "Sequence ID"]
        unique_id = active_sequence_item.loc[0, "Unique ID"]
        cas_type = active_sequence_item.loc[0, "Add/Switch/Buy/Sell"]
        order_type = active_sequence_item.loc[0, "Order Type"]
        combo_quantity = active_sequence_item.loc[0, "#Lots"]
        limit_price = active_sequence_item.loc[0, "Limit Price"]
        trigger_price = active_sequence_item.loc[0, "Trigger Price"]
        trail_value = active_sequence_item.loc[0, "Trail Value"]
        trading_combination_unique_id = active_sequence_item.loc[0, "Trading Unique ID"]
        atr_multiple = active_sequence_item.loc[0, "ATR Multiple"]
        evalaution_unique_id = active_sequence_item.loc[0, "Evaluation Unique ID"]
        atr = get_atr_value_for_unique_id(unique_id)
        condition = active_sequence_item.loc[0, "Condition"]

        condition = condition.replace("%%", "%")

        # init
        cas_combo_object = None
        account_reference_positions_dict = 0
        account_target_positions_dict = None

        if cas_type in ["BUY", "SELL"]:
            evalaution_unique_id = unique_id

        # Trying to get the reference price
        try:

            local_combo_buy_sell_price_dict = copy.deepcopy(
                variables.unique_id_to_prices_dict[int(evalaution_unique_id)]
            )
            current_buy_price, current_sell_price = (
                local_combo_buy_sell_price_dict["BUY"],
                local_combo_buy_sell_price_dict["SELL"],
            )
            reference_price = (
                float(((current_buy_price + current_sell_price) / 2) * 100) / 100
            )
        except Exception as e:
            if variables.flag_debug_mode:

                print(e)
            # TODO
            variables.screen.display_error_popup(
                f"Unique ID : {unique_id}, Conditional {cas_type.capitalize()}",
                "Unable to get the combination current price2.",
            )

            self.stop_series(series_id=series_id)

            return

        local_unique_id_to_positions_dict = copy.deepcopy(
            variables.map_unique_id_to_positions
        )

        flag_multi_account = False

        if flag_multi and cas_type not in ["ADD", "SWITCH"]:

            # get position for add or switch
            positions_df = get_positions_from_series_positions_table(sequence_id)

            # Create a dictionary from the DataFrame
            combo_quantity = dict(
                zip(positions_df["Account ID"], positions_df["Target Position"])
            )

            # Assuming combo_quantity is the dictionary you want to modify
            combo_quantity = {k: int(v) for k, v in combo_quantity.items()}

            # Create a dictionary from the DataFrame
            account_reference_positions_dict = dict(
                zip(positions_df["Account ID"], positions_df["Reference Position"])
            )

            # getting current reference position
            try:

                for account in account_reference_positions_dict:

                    if (
                        int(evalaution_unique_id) in local_unique_id_to_positions_dict
                        and account
                        in local_unique_id_to_positions_dict[int(evalaution_unique_id)]
                    ):

                        account_reference_positions_dict[
                            account
                        ] = local_unique_id_to_positions_dict[
                            int(evalaution_unique_id)
                        ][
                            account
                        ]

            except Exception as e:

                if variables.flag_debug_mode:

                    print(
                        f"Exception inside getting current reference posisiton, Exp: {e}"
                    )

            flag_multi_account = True

        if not flag_multi and cas_type not in ["ADD", "SWITCH"]:
            # Trying to get the reference positions
            try:

                reference_position = local_unique_id_to_positions_dict[
                    int(evalaution_unique_id)
                ][account_id]

                account_reference_positions_dict = reference_position
            except Exception as e:

                reference_position = 0

                if variables.flag_debug_mode:
                    print(e)
                # TODO
                """variables.screen.display_error_popup(
                    f"Unique ID : {unique_id}, Conditional {cas_add_or_switch.capitalize()}",
                    "Unable to get the combination current positions.",
                )

                return"""

        # if cas type is add or switch
        if cas_type in ["ADD", "SWITCH"]:

            # Creates and return combolegs dict, for further process (combo_creation, inserting in cas condition table and viewing)
            sequence_id_to_combolegs_df = get_series_cas_legs_df(sequence_id)

            # init
            flag_multi_account = True

            # legs columns
            leg_columns = [
                "Sequence ID",
                "Series ID",
                "Action",
                "SecType",
                "Symbol",
                "DTE",
                "Delta",
                "Right",
                "#Lots",
                "Lot Size",
                "Exchange",
                "Trading Class",
                "Currency",
                "ConID",
                "Primary Exchange",
                "Strike",
                "Expiry",
            ]

            # rearrange data frame
            sequence_id_to_combolegs_df = sequence_id_to_combolegs_df[leg_columns]

            # convert fisrt row of df to tuple
            """legs_tuple_list = [
                (unique_id,) + tuple(sequence_id_to_combolegs_df.iloc[0, 2:])
            ]"""

            legs_tuple_list = []

            for ind, row_df in sequence_id_to_combolegs_df.iterrows():
                legs_tuple_list.append((unique_id,) + tuple(row_df[2:]))

            # create combo object
            cas_combo_object = create_combination(
                legs_tuple_list, input_from_db=True, input_from_cas_tab=True
            )

            # get position for add or switch
            positions_df = get_positions_from_series_positions_table(sequence_id)

            # Create a dictionary from the DataFrame
            account_reference_positions_dict = dict(
                zip(positions_df["Account ID"], positions_df["Reference Position"])
            )

            # get current positions for new sequence
            try:

                for account in account_reference_positions_dict:

                    if (
                        int(evalaution_unique_id) in local_unique_id_to_positions_dict
                        and account
                        in local_unique_id_to_positions_dict[int(evalaution_unique_id)]
                    ):

                        try:

                            account_reference_positions_dict[
                                account
                            ] = local_unique_id_to_positions_dict[
                                int(evalaution_unique_id)
                            ][
                                account
                            ]

                        except Exception as e:
                            if variables.flag_debug_mode:
                                print(
                                    f"Exception inside getting current reference position for add/switch , Exp: {e}"
                                )

            except Exception as e:

                if variables.flag_debug_mode:
                    print(
                        f"Exception inside getting current reference posisiton, Exp: {e}"
                    )
            # print(local_unique_id_to_positions_dict[int(evalaution_unique_id)])
            # print(account_reference_positions_dict)

            # Create a dictionary from the DataFrame
            account_target_positions_dict = dict(
                zip(positions_df["Account ID"], positions_df["Target Position"])
            )

            # get lsit of account ids
            account_id = positions_df["Account ID"].to_list()

        """flag_cond_passed = variables.screen.screen_cas_obj.check_ref_position_for_specific_tokens(account_reference_positions_dict, condition)
        
        if not flag_cond_passed:
            
            return"""

        # place conditional order
        variables.screen.screen_cas_obj.get_condition_text(
            unique_id,
            condition,
            cas_combo_object,
            cas_type,
            reference_price,
            account_reference_positions_dict,
            None,
            order_type,
            combo_quantity,
            limit_price,
            trigger_price,
            trail_value,
            trading_combination_unique_id,
            atr_multiple=atr_multiple,
            atr=atr,
            target_position=account_target_positions_dict,
            account_id=account_id,
            flag_multi_account=flag_multi_account,
            bypass_rm_check=bypass_rm_check,
            evalaution_unique_id=evalaution_unique_id,
            series_id=series_id,
            execution_engine=execution_engine,
        )

        # values to update
        values_dict = {"Status": "Active"}

        # update values in db
        update_conditional_series_table_values(series_id, values_dict)

        # update GUi table
        self.update_conditional_series_table()

    # Method to unpark series
    def unpark_series(self):

        try:

            # get values from selected rows
            selected_item = self.conditional_series_table.selection()[0]

        except Exception as e:

            return

        # get the item ID of the selected row
        values = self.conditional_series_table.item(
            selected_item, "values"
        )  # get the values of the selected row
        status = values[5]
        series_id = int(values[0])
        base_uid = int(values[1])





        # check if status is already active
        if status in ["Inactive", "Completed", "Failed", "Terminated", 'Active']:
            return

        # Number of CAS Conditions that exists
        number_of_conditions = do_cas_condition_exists_for_unique_id_in_db(base_uid)

        number_of_conditions += do_cas_condition_series_exists_for_unique_id_in_db(
            base_uid
        )

        # If a condition already exists, display error popup
        if number_of_conditions > 0:
            # TODO
            # Throw Error Popup
            variables.screen.display_error_popup(
                f"Unique ID : {base_uid}, Conditional order or series already exists",
                "A Conditional order or series already exists, can not add another.",
            )
            return



        # values to update
        values_dict = {"Status": "Inactive"}

        # update values in db
        update_conditional_series_table_values(series_id, values_dict)

        # update GUi table
        self.update_conditional_series_table()

    # Method to park series
    def park_series(self):


        try:

            # get values from selected rows
            selected_item = self.conditional_series_table.selection()[0]

        except Exception as e:

            return

        # get the item ID of the selected row
        values = self.conditional_series_table.item(
            selected_item, "values"
        )  # get the values of the selected row
        status = values[5]
        series_id = int(values[0])
        unique_id = int(values[1])

        # check if status is already active
        if status in ["Completed", "Failed", "Terminated", 'Parked']:
            return

        if status == 'Active':

            self.stop_series(series_id=series_id)


            self.cancel_conditional_orders(series_id, unique_id)




        # values to update
        values_dict = {"Status": "Parked"}

        # update values in db
        update_conditional_series_table_values(series_id, values_dict)

        # update GUi table
        self.update_conditional_series_table()

    # Method to stop series
    def stop_series(self, series_id=None, unique_id=None):

        status = "Active"

        if series_id == None:

            try:

                # get values from selected rows
                selected_item = self.conditional_series_table.selection()[0]

            except Exception as e:

                return

            # get the item ID of the selected row
            values = self.conditional_series_table.item(
                selected_item, "values"
            )  # get the values of the selected row
            status = values[5]
            series_id = int(values[0])
            unique_id = int(values[1])

            self.cancel_conditional_orders(series_id, unique_id)

        else:

            try:

                values = self.conditional_series_table.item(
                    int(series_id), "values"
                )  # get the values of the selected row
                status = values[5]



            except Exception as e:

                return

        # check if status is already active
        if status in ["Inactive", "Completed", "Failed", "Terminated"]:
            return

        # check if status is already active
        if status in ["Parked"]:
            return

        # values to update
        values_dict = {"Status": "Inactive"}

        # update values in db
        update_conditional_series_table_values(series_id, values_dict)

        # update GUi table
        self.update_conditional_series_table()

    # Method to cancel conditioonal order
    def cancel_conditional_orders(self, series_id, unique_id):

        try:
            # Get all orders dataframe
            local_orders_table_dataframe = get_table_db(variables.sql_table_cas_status)

            # If dataframe is empty
            if local_orders_table_dataframe.empty:

                return

            # convert ladder id column to string format
            local_orders_table_dataframe["Series ID"] = local_orders_table_dataframe[
                "Series ID"
            ].astype(str)

            # Filter the rows for 'ladder id' and get the value of 'order time' column
            unique_id_values = local_orders_table_dataframe.loc[
                local_orders_table_dataframe["Series ID"] == str(series_id),
                ["Unique ID"],
            ].values

            if len(unique_id_values) > 0:

                variables.screen.screen_cas_obj.delete_cas_condition(
                    unique_id=unique_id, series_id=series_id
                )

        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:
                print(f"Exception inside 'cancel_conditional_orders', Exp: {e}")

    # Method to view series details
    def view_series_details(self):

        try:

            try:

                # get values from selected rows
                selected_item = self.conditional_series_table.selection()[0]

            except Exception as e:

                return

            # get the item ID of the selected row
            values = self.conditional_series_table.item(
                selected_item, "values"
            )  # get the values of the selected row
            series_id = int(values[0])

            # Create a create conditional series popup window
            view_conditional_series_popup = tk.Toplevel()
            view_conditional_series_popup.title(
                f"View Conditional Series Details, Series ID: {series_id}"
            )

            # set height
            custom_height = 650

            # set dimensions
            view_conditional_series_popup.geometry("1600x" + str(custom_height))

            # enter_legs_popup.geometry("450x520")

            # Create main frame
            view_conditional_series_popup_frame = ttk.Frame(
                view_conditional_series_popup, padding=20
            )
            view_conditional_series_popup_frame.pack(fill="both", expand=True)

            # Create Treeview Frame for conditional_series instances
            conditional_series_table_frame = ttk.Frame(
                view_conditional_series_popup_frame, padding=10
            )
            conditional_series_table_frame.pack(fill="both", expand=True)

            # Place in top
            conditional_series_table_frame.place(relx=0.5, anchor=tk.N)
            conditional_series_table_frame.place(y=0)

            # Treeview Scrollbar
            tree_scroll = Scrollbar(conditional_series_table_frame)
            tree_scroll.pack(side="right", fill="y")

            # Treeview Scrollbar
            # tree_scroll_x = Scrollbar(conditional_series_table_frame)
            # tree_scroll_x.pack(side="bottom", fill="x")

            # Create Treeview Table
            self.conditional_series_details_table = ttk.Treeview(
                conditional_series_table_frame,
                yscrollcommand=tree_scroll.set,
                height=23,
                selectmode="extended",
            )

            # Pack to the screen
            self.conditional_series_details_table.pack(fill="both", expand=True)

            # Configure the scrollbar
            tree_scroll.config(command=self.conditional_series_details_table.yview)

            # tree_scroll_x.config(command=self.conditional_series_details_table.xview)

            # Get columns for conditional_series table
            conditional_series_table_columns = copy.deepcopy(
                variables.conditional_series_sequence_table_columns
            )

            conditional_series_table_columns = (
                conditional_series_table_columns[0:8]
                + conditional_series_table_columns[10:]
            )

            # Set columns for filter table
            self.conditional_series_details_table[
                "columns"
            ] = conditional_series_table_columns

            # Creating Column
            self.conditional_series_details_table.column("#0", width=0, stretch="no")

            # Creating columns for conditional_series table
            for column_name in conditional_series_table_columns:
                self.conditional_series_details_table.column(
                    column_name, anchor="center", width=104
                )

            # Create Heading
            self.conditional_series_details_table.heading("#0", text="", anchor="w")

            # Create headings for conditional_series table
            for column_name in conditional_series_table_columns:
                self.conditional_series_details_table.heading(
                    column_name, text=column_name, anchor="center"
                )

            # Back ground for rows in table
            self.conditional_series_details_table.tag_configure(
                "oddrow", background="white"
            )
            self.conditional_series_details_table.tag_configure(
                "evenrow", background="lightblue"
            )

            # get all sequences of series
            sequeces_df = get_all_sequences_of_series(series_id)

            # drop columns
            sequeces_df = sequeces_df.drop(
                columns=["Reference Position", "Target Position"]
            )

            # Init
            counter = 0

            # Itereate rows
            for indx, row in sequeces_df.iterrows():

                # get sequence id
                sequence_id = row["Sequence ID"]

                # convert row to tuple
                row = tuple(row)

                # add rows
                if counter % 2 == 1:

                    self.conditional_series_details_table.insert(
                        "",
                        "end",
                        iid=sequence_id,
                        text="",
                        values=row,
                        tags=("oddrow",),
                    )

                else:

                    self.conditional_series_details_table.insert(
                        "",
                        "end",
                        iid=sequence_id,
                        text="",
                        values=row,
                        tags=("evenrow",),
                    )

                counter += 1
        except Exception as e:

            if variables.flag_debug_mode:

                print(f"Exception inside 'view_series_details', Exp: {e}")

    # Method to add series
    def add_conditional_series(
        self, unique_id, flag_multi=False, values_relaunch=None, flag_edit=False
    ):

        # check if alreay conditional order is ening created
        if not isinstance(variables.series_sequence_table_df, list):
            # Error Message
            error_title = (
                error_string
            ) = f"Error, Conditional series pop up is already opened"
            variables.screen.display_error_popup(error_title, error_string)

            return

        if values_relaunch == None:

            # Number of CAS Conditions that exists
            '''number_of_conditions = do_cas_condition_exists_for_unique_id_in_db(
                unique_id
            )

            number_of_conditions += do_cas_condition_series_exists_for_unique_id_in_db(
                unique_id
            )

            # If a condition already exists, display error popup
            if number_of_conditions > 0:
                # TODO
                # Throw Error Popup
                variables.screen.display_error_popup(
                    f"Unique ID : {unique_id}, Condition already exists",
                    "A Condition already exists, can not add another.",
                )
                return'''
            pass

        # create series sequence table df
        variables.series_sequence_table_df = pd.DataFrame(
            columns=variables.series_sequence_tble_columns
        )

        # flag to add orders
        self.flag_add_conditional_order_confirm = False

        # Create a create conditional series popup window
        create_conditional_series_popup = tk.Toplevel()

        if values_relaunch != None and not flag_edit:
            create_conditional_series_popup.title(
                f"Relaunch Conditional Series, Unique ID: {unique_id}"
            )

        elif values_relaunch != None and flag_edit:

            create_conditional_series_popup.title(
                f"Edit Conditional Series, Unique ID: {unique_id}"
            )

        else:

            create_conditional_series_popup.title(
                f"Add Conditional Series, Unique ID: {unique_id}"
            )

        # check for flag multi account ids
        if not flag_multi:

            # set height
            custom_height = 780

        else:

            custom_height = 850

        # set dimensions
        create_conditional_series_popup.geometry("1600x" + str(custom_height))

        # enter_legs_popup.geometry("450x520")

        # Create main frame
        create_conditional_series_popup_frame = ttk.Frame(
            create_conditional_series_popup, padding=20
        )
        create_conditional_series_popup_frame.pack(fill="both", expand=True)

        # Create a frame for the input fields
        create_conditional_series_frame = ttk.Frame(
            create_conditional_series_popup_frame, padding=0
        )
        create_conditional_series_frame.pack(side=TOP)

        # Create a frame for the input fields
        create_conditional_series_table_button_frame = ttk.Frame(
            create_conditional_series_popup_frame, padding=0
        )
        create_conditional_series_table_button_frame.pack(side=BOTTOM)

        # Create a frame for the input fields
        create_conditional_series_table_frame = ttk.Frame(
            create_conditional_series_table_button_frame, padding=0
        )
        create_conditional_series_table_frame.pack(side=TOP)

        # Create a frame for the input fields
        create_conditional_series_button_frame = ttk.Frame(
            create_conditional_series_table_button_frame, padding=0
        )
        create_conditional_series_button_frame.pack(side=BOTTOM)

        # action to take after user close window
        def pop_up_close():

            # create series sequence table df
            variables.series_sequence_table_df = []

            create_conditional_series_popup.destroy()

        # Set the function to be called when the window is closed
        create_conditional_series_popup.protocol("WM_DELETE_WINDOW", pop_up_close)

        # Add a label
        ttk.Label(create_conditional_series_frame, text="Account ID").grid(
            column=0, row=0, padx=5, pady=5
        )

        # Add a label
        ttk.Label(create_conditional_series_frame, text="Base Unique ID").grid(
            column=1, row=0, padx=5, pady=5
        )

        # Add a label
        ttk.Label(create_conditional_series_frame, text="Bypass RM Check").grid(
            column=2, row=0, padx=5, pady=5
        )

        # Add a label
        ttk.Label(create_conditional_series_frame, text="Bypass RM Check").grid(
            column=2, row=0, padx=5, pady=5
        )

        # Add a label
        ttk.Label(create_conditional_series_frame, text="Conditional Order Type").grid(
            column=0, row=6, padx=5, pady=5
        )

        # Add a label
        ttk.Label(create_conditional_series_frame, text="Execution Engine").grid(
            column=3, row=0, padx=5, pady=5
        )

        # Add a label
        ttk.Label(
            create_conditional_series_frame,
            text="Evaluation Combination\n            Unique ID",
        ).grid(column=0, row=2, padx=5, pady=5, sticky="n")

        # Add a label
        ttk.Label(create_conditional_series_frame, text="Evaluation Series ID").grid(
            column=0, row=4, padx=5, pady=5
        )

        # Entry to unique id
        rows_entry = ttk.Entry(create_conditional_series_frame)
        rows_entry.grid(column=1, row=1, padx=5, pady=5, sticky="n")
        rows_entry.insert(0, unique_id)

        # Init
        unique_id_old = None

        # Init
        unique_id = unique_id

        # check if pop up is not for relauching series
        if values_relaunch == None:

            # make entry disabled
            rows_entry.config(state="readonly")

        # Entry to condition
        condition_entry = ttk.Entry(
            create_conditional_series_frame, width=60, justify="center"
        )
        condition_entry.grid(column=2, row=3, padx=5, pady=5, columnspan=3)

        condition_entry.config(state="readonly")

        # Entry to evaluation unique id
        evaluation_uid_entry = ttk.Entry(create_conditional_series_frame)
        evaluation_uid_entry.grid(column=0, row=3, padx=5, pady=5)

        # Entry to series id
        series_id_entry = ttk.Entry(create_conditional_series_frame)
        series_id_entry.grid(column=0, row=5, padx=5, pady=5)

        # Entry to condition extesnion
        series_condition_entry = ttk.Entry(
            create_conditional_series_frame, width=85, justify="center"
        )
        series_condition_entry.grid(column=1, row=5, padx=5, pady=5, columnspan=4)
        series_condition_entry.insert(0, "is completed")
        series_condition_entry.config(state="readonly")

        # Create a custom style for the Combobox widget
        custom_style = ttk.Style()
        custom_style.map(
            "Custom.TCombobox",
            fieldbackground=[
                ("readonly", "white"),
                ("!disabled", "white"),
                ("disabled", "lightgray"),
            ],
            foreground=[("disabled", "black")],
        )

        # Create a list of options
        bypass_rm_account_checks_options = ["True", "False"]

        # Create the combo box
        bypass_rm_account_checks_options_combo_box = ttk.Combobox(
            create_conditional_series_frame,
            width=18,
            values=bypass_rm_account_checks_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        bypass_rm_account_checks_options_combo_box.current(1)
        bypass_rm_account_checks_options_combo_box.grid(
            column=2, row=1, padx=5, pady=5, sticky="n"
        )

        execution_engine_options = ["True", "False"]

        # Create the combo box
        flag_execution_engine_combo_box = ttk.Combobox(
            create_conditional_series_frame,
            width=15,
            values=execution_engine_options,
            state="readonly",
            style="Custom.TCombobox",
        )

        flag_execution_engine_combo_box.current(
            execution_engine_options.index(str(variables.flag_use_execution_engine))
        )
        flag_execution_engine_combo_box.grid(
            column=3, row=1, padx=5, pady=5, sticky="n"
        )

        # check flag for multi account
        if not flag_multi:

            # Create a list of options
            account_id_options = variables.current_session_accounts

            # Create the combo box
            account_id_options_combo_box = ttk.Combobox(
                create_conditional_series_frame,
                width=18,
                values=account_id_options,
                state="readonly",
                style="Custom.TCombobox",
            )
            account_id_options_combo_box.current(0)
            account_id_options_combo_box.grid(
                column=0, row=1, padx=5, pady=5, sticky="n"
            )

        else:

            # Create a frame for the input fields
            trade_input_frame_acc = ttk.Frame(
                create_conditional_series_frame, padding=0
            )
            trade_input_frame_acc.grid(column=0, row=1, padx=5, pady=5, sticky="n")

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

            # for edit series and relaunch series
            if values_relaunch != None and flag_multi:

                # get account id list
                account_lst = values_relaunch["Account ID"]

                # get every account
                for account_lst_item in account_lst.split(","):

                    # select already available items
                    if account_lst_item in variables.current_session_accounts:

                        try:

                            listbox.select_set(
                                variables.current_session_accounts.index(
                                    account_lst_item
                                )
                            )

                        except Exception as e:

                            if variables.flag_debug_mode:

                                print(e)

            listbox.pack()

        # Create a list of options
        conditional_order_options = [
            "Conditional Add",
            "Conditional Switch",
            "Conditional Buy",
            "Conditional Sell",
        ]

        # Create the combo box
        conditional_order_options_combo_box = ttk.Combobox(
            create_conditional_series_frame,
            width=18,
            values=conditional_order_options,
            state="readonly",
            style="Custom.TCombobox",
        )
        conditional_order_options_combo_box.current(0)
        conditional_order_options_combo_box.grid(column=0, row=7, padx=5, pady=5)

        # Treeview Scrollbar
        tree_scroll = Scrollbar(create_conditional_series_table_frame)
        tree_scroll.pack(side="right", fill="y")

        # Create Treeview Table
        self.series_sequence_table = ttk.Treeview(
            create_conditional_series_table_frame,
            yscrollcommand=tree_scroll.set,
            height=15,
            selectmode="extended",
        )

        # Pack to the screen
        self.series_sequence_table.pack()

        # Configure the scrollbar
        tree_scroll.config(command=self.series_sequence_table.yview)

        # Get columns for series sequence table
        series_sequence_table_columns = copy.deepcopy(
            variables.series_sequence_tble_columns
        )

        # skip last 3 columns
        series_sequence_table_columns = series_sequence_table_columns[:-3]

        # Set columns for series sequence table
        self.series_sequence_table["columns"] = series_sequence_table_columns

        # skip last column in list
        series_sequence_table_columns = series_sequence_table_columns[:-1]

        # Creating Column
        self.series_sequence_table.column("#0", width=0, stretch="no")

        # Creating columns for filter table
        for column_name in series_sequence_table_columns:
            self.series_sequence_table.column(column_name, anchor="center", width=120)

        # add invisible column
        self.series_sequence_table.column("Table ID", anchor="center", width=0)

        # Create Heading
        self.series_sequence_table.heading("#0", text="", anchor="w")

        # Create headings for filter table
        for column_name in series_sequence_table_columns:

            self.series_sequence_table.heading(
                column_name, text=column_name, anchor="center"
            )

        # add invisible column
        self.series_sequence_table.heading("Table ID", text="Table ID", anchor="center")

        # Back ground for rows in table
        self.series_sequence_table.tag_configure("oddrow", background="white")
        self.series_sequence_table.tag_configure("evenrow", background="lightblue")

        # check if pop up is for relauching series
        if values_relaunch != None:

            # store old unique
            unique_id_old = unique_id

            # get series id
            series_id = values_relaunch["Series ID"]

            # get all sequences of selected series
            series_seq_df_db = get_all_sequences_of_series(series_id)

            # get list of sequence ids
            sequence_ids_list = series_seq_df_db["Sequence ID"].to_list()

            # get list of cas types
            cas_type_lst = series_seq_df_db["Add/Switch/Buy/Sell"].to_list()

            # # get list of quantities
            qnty_lst = series_seq_df_db["#Lots"].to_list()

            # inti
            combo_obj_lst = []
            ref_position_lst = []

            target_postions_lst = []

            # check sequence id, cas type and quanity for each row
            for (seq_id, cas_type_db, qnty) in zip(
                sequence_ids_list, cas_type_lst, qnty_lst
            ):

                # check if cas type is add or switch
                if cas_type_db in ["ADD", "SWITCH"]:

                    # Creates and return combolegs dict, for further process (combo_creation, inserting in cas condition table and viewing)
                    sequence_id_to_combolegs_df = get_series_cas_legs_df(seq_id)

                    # init
                    flag_multi_account = True

                    # legs columns
                    leg_columns = [
                        "Sequence ID",
                        "Series ID",
                        "Action",
                        "SecType",
                        "Symbol",
                        "DTE",
                        "Delta",
                        "Right",
                        "#Lots",
                        "Lot Size",
                        "Exchange",
                        "Trading Class",
                        "Currency",
                        "ConID",
                        "Primary Exchange",
                        "Strike",
                        "Expiry",
                    ]

                    # rearrange data frame
                    sequence_id_to_combolegs_df = sequence_id_to_combolegs_df[
                        leg_columns
                    ]

                    # convert fisrt row of df to tuple
                    """legs_tuple_list = [
                        (unique_id,) + tuple(sequence_id_to_combolegs_df.iloc[0, 2:])
                    ]"""

                    legs_tuple_list = []

                    for ind, row_df in sequence_id_to_combolegs_df.iterrows():
                        legs_tuple_list.append((unique_id,) + tuple(row_df[2:]))

                    # create combo object
                    cas_combo_object = create_combination(
                        legs_tuple_list, input_from_db=True, input_from_cas_tab=True
                    )

                    combo_obj_lst.append(cas_combo_object)

                    # get position for add or switch
                    positions_df = get_positions_from_series_positions_table(seq_id)

                    # Create a dictionary from the DataFrame
                    account_reference_positions_dict = dict(
                        zip(
                            positions_df["Account ID"],
                            positions_df["Reference Position"],
                        )
                    )

                    # Create a dictionary from the DataFrame
                    account_target_positions_dict = dict(
                        zip(positions_df["Account ID"], positions_df["Target Position"])
                    )

                    # get lsit of account ids
                    account_id = positions_df["Account ID"].to_list()

                    # append
                    ref_position_lst.append(account_reference_positions_dict)

                    target_postions_lst.append(account_target_positions_dict)

                else:

                    # check if quantity is none for buy or sell
                    if flag_multi:
                        # get position for add or switch
                        positions_df = get_positions_from_series_positions_table(seq_id)

                        # Create a dictionary from the DataFrame
                        combo_quantity = dict(
                            zip(
                                positions_df["Account ID"],
                                positions_df["Target Position"],
                            )
                        )

                        target_postions_lst.append(combo_quantity)

                        # Create a dictionary from the DataFrame
                        account_reference_positions_dict = dict(
                            zip(
                                positions_df["Account ID"],
                                positions_df["Reference Position"],
                            )
                        )

                        # append
                        combo_obj_lst.append("None")

                        ref_position_lst.append(account_reference_positions_dict)

                    else:

                        # append
                        combo_obj_lst.append("None")
                        ref_position_lst.append("None")
                        target_postions_lst.append("None")

            # add new columns in df
            series_seq_df_db["Combo Obj"] = combo_obj_lst

            series_seq_df_db["Reference Position"] = ref_position_lst

            series_seq_df_db["Target Position"] = target_postions_lst

            # Add a new column with sequential integers starting from 1
            series_seq_df_db["Table ID"] = range(1, len(series_seq_df_db) + 1)

            # rearrange df
            series_seq_df_db = series_seq_df_db[variables.series_sequence_tble_columns]

            # ake it available in global df
            variables.series_sequence_table_df = series_seq_df_db.copy()

            if not flag_edit:

                # Change the value of column 'A' to 100 where the value is 10
                variables.series_sequence_table_df["Status"] = "Queued"

                # Change the value of 'Status' at index 0 to 'New Status'
                variables.series_sequence_table_df.loc[0, "Status"] = "Active"

            # update table in series creation table
            self.update_create_series_pop_up_table()

            # prefill values in avaialable GUI components
            condition_entry.config(state="normal")

            condition_entry.insert(0, values_relaunch["User Condition"])

            condition_entry.config(state="readonly")

            series_id_entry.insert(0, values_relaunch["Series ID Condition"])

            evaluation_uid_entry.insert(0, values_relaunch["Eval UID"])

            bypass_rm_account_checks_options_combo_box.current(
                bypass_rm_account_checks_options.index(
                    values_relaunch["Bypass RM Check"]
                )
            )

            flag_execution_engine_combo_box.current(
                execution_engine_options.index(values_relaunch["Execution Engine"])
            )

            if not flag_multi:

                try:

                    account_id_options_combo_box.current(
                        account_id_options.index(values_relaunch["Account ID"])
                    )

                except Exception as e:

                    if variables.flag_debug_mode:

                        print(e)

        def modify_sequence():

            # get Ladder ID of selected row
            selected_item = self.series_sequence_table.selection()[0]

            # get value of row
            values = self.series_sequence_table.item(selected_item, "values")

            # table id
            table_id = int(values[13])

            # status value
            status_row = values[6]

            # get row of existing coditional order
            row_df = variables.series_sequence_table_df[
                variables.series_sequence_table_df["Table ID"] == table_id
            ].head(
                1
            )  # variables.series_sequence_table_df.iloc[table_id - 1]

            row_df = row_df.iloc[0]

            # Convert the row to a dictionary
            row_dict = row_df.to_dict()

            # check if stauts is completed
            if status_row == "Completed":
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Cannot edit completed conditional order"
                variables.screen.display_error_popup(error_title, error_string)

                return

            on_click_create_button(modify_seq_data=row_dict)

        def delete_sequence_item():

            # get Ladder ID of selected row
            selected_item = self.series_sequence_table.selection()[0]

            # get value of row
            values = self.series_sequence_table.item(selected_item, "values")

            # table id
            table_id = int(values[13])

            # status value
            status_row = values[6]

            # check if stauts is completed
            if status_row == "Completed":
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Cannot edit completed conditional order"
                variables.screen.display_error_popup(error_title, error_string)

                return

            # Filter rows where 'table id' is not equal to selected table id
            variables.series_sequence_table_df = variables.series_sequence_table_df[
                variables.series_sequence_table_df["Table ID"] != table_id
            ]

            variables.series_sequence_table_df = (
                variables.series_sequence_table_df.reset_index(drop=True)
            )

            try:

                if not variables.series_sequence_table_df.empty:

                    # Change the value of column 'status' to active for first row
                    variables.series_sequence_table_df.loc[0, "Status"] = "Active"

            except Exception as e:

                if variables.flag_debug_mode:

                    print(
                        f"Exception inside 'delete order from series pop up', Exp: {e}"
                    )

            # update series sequence table
            self.update_create_series_pop_up_table()

        def series_sequence_table_right_click(event):

            # get the Treeview row that was clicked
            row = self.series_sequence_table.identify_row(event.y)

            if values_relaunch != None and not flag_edit:

                return

            if row:
                # select the row
                self.series_sequence_table.selection_set(row)

                # create a context menu
                menu = tk.Menu(self.series_sequence_table, tearoff=0)
                menu.add_command(label="Delete", command=lambda: delete_sequence_item())

                if flag_edit:
                    menu.add_command(label="Modify", command=lambda: modify_sequence())

                # display the context menu at the location of the mouse cursor
                menu.post(event.x_root, event.y_root)

        # add right click optons in table
        self.series_sequence_table.bind("<Button-3>", series_sequence_table_right_click)

        # Method to validate unique id and create combination pop up
        def on_click_create_button(modify_seq_data=None, index=None):

            # check if flag is false for details confirmation
            if not self.flag_add_conditional_order_confirm:

                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Please confirm details before adding conditional order"
                variables.screen.display_error_popup(error_title, error_string)

                return

            unique_id = int(rows_entry.get().strip())

            if modify_seq_data == None:

                # get cas add or switch type
                cas_add_or_switch = conditional_order_options_combo_box.get().strip()
                cas_add_or_switch = cas_add_or_switch.split(" ")[1].upper()

            else:

                cas_add_or_switch = modify_seq_data["Add/Switch/Buy/Sell"]

            if not flag_multi:

                # account ID
                account_id = account_id_options_combo_box.get().strip()

            else:

                # Init
                account_id_list = []

                # Get list of selections
                for i in listbox.curselection():

                    # Split item in listbox
                    accounts_type = listbox.get(i).split(":")[0]

                    # Check if its account
                    # if accounts_type == "Account":

                    # Append account id in list
                    account_id_list.append(listbox.get(i))

                    """else:

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

                                account_id_list.append(account)"""

                # Get unique account ids and sort them
                account_id = account_id_list  # sorted(list(set(account_id_list)))

            # bypass RM check options
            bypass_rm_account_check_val = (
                bypass_rm_account_checks_options_combo_box.get().strip()
            )

            # flag executioon value
            flag_execution_engine = flag_execution_engine_combo_box.get().strip()

            # get boolean value for execution engine flag
            if flag_execution_engine == "True":

                flag_execution_engine = True

            else:

                flag_execution_engine = False

            # Trying to get the reference price
            try:

                local_combo_buy_sell_price_dict = copy.deepcopy(
                    variables.unique_id_to_prices_dict[unique_id]
                )
                current_buy_price, current_sell_price = (
                    local_combo_buy_sell_price_dict["BUY"],
                    local_combo_buy_sell_price_dict["SELL"],
                )
                reference_price = (
                    int(((current_buy_price + current_sell_price) / 2) * 100) / 100
                )

            except Exception as e:
                if variables.flag_debug_mode:

                    print(e)
                # TODO
                variables.screen.display_error_popup(
                    f"Unique ID : {unique_id}, Conditional {cas_add_or_switch.capitalize()}",
                    "Unable to get the combination current price3.",
                )
                return

            # Trying to get the reference positions
            try:
                local_unique_id_to_positions_dict = copy.deepcopy(
                    variables.map_unique_id_to_positions
                )
                reference_position = local_unique_id_to_positions_dict[unique_id]
            except Exception as e:

                reference_position = None

                if variables.flag_debug_mode:

                    print(e)
                # TODO
                variables.screen.display_error_popup(
                    f"Unique ID : {unique_id}, Conditional {cas_add_or_switch.capitalize()}",
                    "Unable to get the combination current positions.",
                )

                return

            # If Condition ADD or Switch
            if cas_add_or_switch in ["ADD", "SWITCH"]:

                # get previosu target positions
                if not variables.series_sequence_table_df.empty:

                    target_positions_lst = variables.series_sequence_table_df[
                        "Target Position"
                    ].to_list()

                    cas_type_lst = variables.series_sequence_table_df[
                        "Add/Switch/Buy/Sell"
                    ].to_list()

                    table_ids_list = variables.series_sequence_table_df[
                        "Table ID"
                    ].to_list()

                    for indx_df, (
                        dict_target,
                        cas_type_row,
                        table_id_item,
                    ) in enumerate(
                        zip(target_positions_lst, cas_type_lst, table_ids_list)
                    ):

                        try:

                            if modify_seq_data != None:

                                if modify_seq_data["Table ID"] == table_id_item:

                                    break

                        except Exception as e:

                            if variables.flag_debug_mode:

                                print(
                                    f"Error getting refer position for modify sequence, Exp: {e}"
                                )

                        if dict_target not in [None, "None"] and cas_type_row in [
                            "ADD",
                            "SWITCH",
                        ]:

                            reference_position = dict_target

                        if (
                            flag_edit
                            and isinstance(index, int)
                            and index - 1 == indx_df
                        ):

                            # modify_seq_data['Reference Position'] = dict_target

                            break

                # print(variables.series_sequence_table_df.to_string())

                # Show Enter Leg popup
                variables.screen.screen_cas_obj.display_enter_legs_popup(
                    f"Unique ID : {unique_id}, Conditional {cas_add_or_switch.capitalize()}",
                    cas_add_or_switch,
                    unique_id,
                    reference_price,
                    reference_position,
                    flag_conditional_series=True,
                    modify_seq_data=modify_seq_data,
                    index=index,
                )
            else:

                popup_title = None
                flag_cas_order = True

                # Get Unique ID and show the trade popup
                variables.screen.screen_cas_obj.get_unique_id_from_user_and_create_trade_popup(
                    cas_add_or_switch,
                    unique_id,
                    popup_title,
                    flag_cas_order,
                    reference_price,
                    reference_position,
                    flag_conditional_series=True,
                    flag_multi_account=flag_multi,
                    account_id_series=account_id,
                    bypass_rm_check_series=bypass_rm_account_check_val,
                    flag_execution_engine=flag_execution_engine,
                    modify_seq_data=modify_seq_data,
                    index=index,
                )

        def on_click_create_series_button():

            unique_id = int(rows_entry.get().strip())


            # get evaluation uid
            eval_uid = evaluation_uid_entry.get().strip()

            # get series id for condition
            series_id_condition = series_id_entry.get().strip()

            # get user entered condition
            series_condition_text = condition_entry.get().strip()

            # check if eval uid and series id for condition are both empty
            '''if series_id_condition == "" and series_condition_text == "":
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Please provide at least one condition"
                variables.screen.display_error_popup(error_title, error_string)

                return'''

            # check if eval uid and series id for condition are both empty
            if eval_uid == "" and series_condition_text != "":
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Please provide evaluation unique ID"
                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if eval uid and series id for condition are both empty
            if eval_uid != "" and series_condition_text == "":
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Please provide condition for evaluation unique ID"
                variables.screen.display_error_popup(error_title, error_string)

                return

            try:

                if (isinstance(eval_uid, str) and eval_uid.isnumeric()) or isinstance(
                    eval_uid, int
                ):

                    reference_price = (
                        variables.unique_id_to_prices_dict[int(eval_uid)]["BUY"]
                        + variables.unique_id_to_prices_dict[int(eval_uid)]["SELL"]
                    ) / 2

                else:

                    reference_price = None

            except Exception as e:

                reference_price = None

                if variables.flag_debug_mode:

                    print(f"Exception for getting price for combo, Exp: {e}")

            if (
                "Price Increase By" in series_condition_text
                or "Price Decrease By" in series_condition_text
            ) and reference_price == None:
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Reference price not available for series condition"
                variables.screen.display_error_popup(error_title, error_string)

                return

            reference_position = None

            if len(variables.current_session_accounts) == 1:

                if (
                    "Price Adverse Chg By" in series_condition_text
                    or "Price Favorable Chg By" in series_condition_text
                ) and reference_price == None:
                    # Error Message
                    error_title = (
                        error_string
                    ) = f"Error, Reference price not available for series condition"
                    variables.screen.display_error_popup(error_title, error_string)

                    return

                # Trying to get the reference positions
                try:
                    local_unique_id_to_positions_dict = copy.deepcopy(
                        variables.map_unique_id_to_positions
                    )

                    if (
                        isinstance(eval_uid, str) and eval_uid.isnumeric()
                    ) or isinstance(eval_uid, int):

                        reference_position = local_unique_id_to_positions_dict[
                            int(eval_uid)
                        ][variables.current_session_accounts[0]]

                    else:

                        reference_position = None
                except Exception as e:

                    reference_position = None

                    if variables.flag_debug_mode:
                        print(e)

                if (
                    "Price Adverse Chg By" in series_condition_text
                    or "Price Favorable Chg By" in series_condition_text
                ) and reference_position in [None]:
                    # Error Message
                    error_title = (
                        error_string
                    ) = f"Error, Reference position not available for series condition"
                    variables.screen.display_error_popup(error_title, error_string)

                    return

                if (
                    "Price Adverse Chg By" in series_condition_text
                    or "Price Favorable Chg By" in series_condition_text
                ) and reference_position == 0:
                    # Error Message
                    error_title = (
                        error_string
                    ) = f"Error, Reference position should not be 0 for series condition"
                    variables.screen.display_error_popup(error_title, error_string)

                    return

            else:

                if (
                    "Price Adverse Chg By" in series_condition_text
                    or "Price Favorable Chg By" in series_condition_text
                ):

                    # Error Message
                    error_title = (
                        error_string
                    ) = f"Error, Price favourable/Adverse not allowed for multiple accounts\nin series condition"
                    variables.screen.display_error_popup(error_title, error_string)

                    return

                condition_list = variables.series_sequence_table_df[
                    "Condition"
                ].to_list()

                for condition_item in condition_list:

                    if (
                        "Price Adverse Chg By" in condition_item
                        or "Price Favorable Chg By" in condition_item
                    ):
                        # Error Message
                        error_title = (
                            error_string
                        ) = f"Error, Price favourable/Adverse not allowed for multiple accounts\nin sequence condition"
                        variables.screen.display_error_popup(error_title, error_string)

                        return

            # Get combo details dataframe
            local_combo_details_df = copy.deepcopy(variables.combo_table_df)

            # All the Unique IDs in the System
            all_unique_ids_in_system = local_combo_details_df["Unique ID"].tolist()

            # get copy of data frame
            local_conditional_series_table = get_conditional_series_df()

            if local_conditional_series_table.empty:

                all_series_ids_in_system = []

            else:
                # All the series IDs in the System
                all_series_ids_in_system = local_conditional_series_table[
                    "Series ID"
                ].tolist()

            if int(unique_id) not in all_unique_ids_in_system:
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Base unique ID not present in system"
                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if eval uid is valid
            if not eval_uid.isnumeric() and eval_uid != "":
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Please provide numeric evalaution unique ID"
                variables.screen.display_error_popup(error_title, error_string)

                return

            if eval_uid != "" and int(eval_uid) not in all_unique_ids_in_system:
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Evalaution unique ID not present in system"
                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if series id for condition is valid
            if not series_id_condition.isnumeric() and series_id_condition != "":
                # Error Message
                error_title = error_string = f"Error, Please provide numeric series ID"
                variables.screen.display_error_popup(error_title, error_string)

                return

            if (
                series_id_condition != ""
                and int(series_id_condition) not in all_series_ids_in_system
            ):
                # Error Message
                error_title = error_string = f"Error, Series ID not present in system"
                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if flag is false for details confirmation
            if not self.flag_add_conditional_order_confirm:

                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Please confirm details before adding conditional series"
                variables.screen.display_error_popup(error_title, error_string)

                return

            # check if there are no codnitional orders inserted by user
            if variables.series_sequence_table_df.empty:
                # Error Message
                error_title = (
                    error_string
                ) = f"Error, Please add condtitional ordres before creating conditional series"
                variables.screen.display_error_popup(error_title, error_string)

                return

            # get series id
            series_id = get_series_id_db()

            # if series id is none
            if series_id == None:

                # Error Message
                error_title = error_string = f"Error, Series ID is none."
                variables.screen.display_error_popup(error_title, error_string)

                return

            else:

                # make empty fields None
                if eval_uid == "":

                    eval_uid = "None"

                # make empty fields None
                if series_id_condition == "":

                    series_id_condition = "None"

                # make empty fields None
                if series_condition_text == "":

                    series_condition_text = "None"

                # increment series id
                series_id += 1

                if flag_edit:

                    series_id = values_relaunch["Series ID"]

                    status = get_series_column_value_from_db(series_id=series_id, column_name_as_in_db='Status')



                    if status in ['Active','Completed', 'Terminated']:
                        # Error pop up
                        error_title = f"Active or completed or terminated series can not be edited."
                        error_string =  f"Active or completed or terminated series can not be edited."

                        variables.screen.display_error_popup(
                            error_title, error_string
                        )
                        return





                    self.delete_series(series_id)

                # get max sequence id present
                sequence_id = get_sequence_id_db()

                # increment sequence id
                sequence_id += 1

                # get total sequences for series
                total_sequences = len(variables.series_sequence_table_df)

                # init
                sequences_completed = (
                    variables.series_sequence_table_df["Status"]
                    .to_list()
                    .count("Completed")
                )

                # Init
                status = "Parked"

                # get value of bypass rm check
                bypass_rm_check = bypass_rm_account_checks_options_combo_box.get()

                # flag executioon value
                flag_execution_engine = flag_execution_engine_combo_box.get().strip()

                # get boolean value for execution engine flag
                if flag_execution_engine == "True":

                    flag_execution_engine = True

                else:

                    flag_execution_engine = False

                if not flag_multi:

                    # get account id
                    account_id = account_id_options_combo_box.get()

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
                    account_id = sorted(list(set(account_id_list)))

                    account_id = ",".join(account_id)

                series_condition_text = series_condition_text.replace("%", "%%")

                # is started once value
                if series_condition_text in ['None', None, ''] and series_id_condition in ['None', None, '']:

                    is_started_once = 'Yes'

                else:

                    is_started_once = 'No'

                # create list of values
                values_list = [
                    series_id,
                    unique_id,
                    account_id,
                    total_sequences,
                    sequences_completed,
                    status,
                    bypass_rm_check,
                    flag_execution_engine,
                    eval_uid,
                    series_condition_text,
                    series_id_condition,
                    is_started_once,
                    flag_multi,
                    reference_price,
                    reference_position,
                ]

                # Create a dictionary from the list of values and columns
                values_dict = dict(
                    zip(variables.conditional_series_table_columns, values_list)
                )

                # insert series in db
                series_query = insert_conditional_series_instance_values_to_conditional_series_table(
                    values_dict, return_only=True
                )

                # Create a new column with incremental values
                variables.series_sequence_table_df["Sequence ID"] = [
                    sequence_id
                ] + list(
                    range(
                        sequence_id + 1,
                        sequence_id + len(variables.series_sequence_table_df),
                    )
                )

                # Create a new column with series id
                variables.series_sequence_table_df["Series ID"] = series_id

                # get value of positions
                target_positions_list = variables.series_sequence_table_df[
                    "Target Position"
                ]

                reference_positions_list = variables.series_sequence_table_df[
                    "Reference Position"
                ]

                # get list of sequence ids list
                sequence_id_list = variables.series_sequence_table_df["Sequence ID"]

                # get list of cas type list
                cas_type_list = variables.series_sequence_table_df[
                    "Add/Switch/Buy/Sell"
                ]

                trading_uid_list = variables.series_sequence_table_df[
                    "Trading Unique ID"
                ]

                quantity_list = variables.series_sequence_table_df["#Lots"]

                pos_query_list = []

                # insert sequences postions in db
                for (
                    target_position,
                    reference_position,
                    sequence_id,
                    cas_type_item,
                    trading_uid_item,
                    qnty_seq,
                ) in zip(
                    target_positions_list,
                    reference_positions_list,
                    sequence_id_list,
                    cas_type_list,
                    trading_uid_list,
                    quantity_list,
                ):

                    if (
                        flag_multi
                        and cas_type_item in ["BUY", "SELL"]
                        and values_relaunch != None
                    ):

                        # Init
                        map_account_to_quanity_dict = {}

                        target_position = {}

                        reference_position = {}

                        try:

                            # Getting initial trigger price
                            price = (
                                variables.unique_id_to_prices_dict[
                                    int(trading_uid_item)
                                ]["BUY"]
                                + variables.unique_id_to_prices_dict[
                                    int(trading_uid_item)
                                ]["SELL"]
                            ) / 2

                            # Iterating account ids
                            for account in account_id.split(","):

                                # Getting value of account parameter
                                if (
                                    variables.account_parameter_for_order_quantity
                                    == "NLV"
                                ):

                                    value_of_account_parameter = (
                                        variables.accounts_table_dataframe.loc[
                                            variables.accounts_table_dataframe[
                                                "Account ID"
                                            ]
                                            == account,
                                            variables.accounts_table_columns[1],
                                        ].iloc[0]
                                    )

                                elif (
                                    variables.account_parameter_for_order_quantity
                                    == "SMA"
                                ):

                                    value_of_account_parameter = (
                                        variables.accounts_table_dataframe.loc[
                                            variables.accounts_table_dataframe[
                                                "Account ID"
                                            ]
                                            == account,
                                            variables.accounts_table_columns[2],
                                        ].iloc[0]
                                    )

                                elif (
                                    variables.account_parameter_for_order_quantity
                                    == "CEL"
                                ):

                                    value_of_account_parameter = (
                                        variables.accounts_table_dataframe.loc[
                                            variables.accounts_table_dataframe[
                                                "Account ID"
                                            ]
                                            == account,
                                            variables.accounts_table_columns[4],
                                        ].iloc[0]
                                    )

                                else:
                                    error_title = "Invalid Account Parameter"
                                    error_string = (
                                        f"Please provide valid Account Parameter"
                                    )

                                    variables.screen.display_error_popup(
                                        error_title, error_string
                                    )
                                    return

                                # Check if account parameter value is invalid
                                if not is_float(value_of_account_parameter):
                                    error_title = "Invalid Account Parameter Value"
                                    error_string = f"For Account ID: {account}, Value of account Parameter: {variables.account_parameter_for_order_quantity} is invalid"

                                    variables.screen.display_error_popup(
                                        error_title, error_string
                                    )
                                    return

                                # Calculate combo qunaity for account id
                                if float(price) != 0:

                                    # get quantity in percentage
                                    combo_quantity = float(qnty_seq)

                                    # get rounded value for quantity
                                    combo_quantity_for_account = round(
                                        (
                                            (combo_quantity / 100)
                                            * float(value_of_account_parameter)
                                        )
                                        / abs(float(price))
                                    )

                                else:

                                    # set to zero
                                    combo_quantity_for_account = 0

                                # add it to dictionary
                                target_position[account] = combo_quantity_for_account

                                local_unique_id_to_positions_dict = copy.deepcopy(
                                    variables.map_unique_id_to_positions
                                )

                                reference_position[
                                    account
                                ] = local_unique_id_to_positions_dict[
                                    int(trading_uid_item)
                                ][
                                    account
                                ]

                        except Exception as e:

                            # error message
                            error_title = f"For Unique ID: {trading_uid_item}, Could not get quantity for accounts"
                            error_string = f"For Unique ID: {trading_uid_item}, Could not get quantity for accounts"

                            variables.screen.display_error_popup(
                                error_title, error_string
                            )
                            return

                    if target_position not in ["None", None]:
                        pos_query = insert_positions_for_series(
                            reference_position,
                            target_position,
                            sequence_id,
                            series_id,
                            unique_id,
                            return_only=True,
                        )

                        pos_query_list.append(pos_query)

                # make position column none
                variables.series_sequence_table_df["Reference Position"] = "None"

                # make position column none
                variables.series_sequence_table_df["Target Position"] = "None"

                # get list of combo objests
                combo_obj_list = variables.series_sequence_table_df["Combo Obj"]

                cas_legs_query_list = []

                # insert combo objects of sequences
                for combo_obj, sequence_id_combo in zip(
                    combo_obj_list, sequence_id_list
                ):

                    if combo_obj not in ["None", None]:
                        cas_legs_query = insert_cas_legs_for_series_db(
                            combo_obj,
                            sequence_id_combo,
                            series_id,
                            unique_id,
                            return_only=True,
                        )

                        cas_legs_query_list.append(cas_legs_query)

                # print(variables.series_sequence_table_df.to_string())

                # get copy of df
                local_conditional_series_sequence_df = (
                    variables.series_sequence_table_df[
                        variables.conditional_series_sequence_table_columns
                    ].copy()
                )

                # Iterate over rows and create a dictionary for each row
                row_dicts = [
                    row.to_dict()
                    for _, row in local_conditional_series_sequence_df.iterrows()
                ]

                sequence_query_list = []

                # insert sequences
                for row_dict in row_dicts:

                    sequence_query = insert_conditional_series_sequence_instance_values_to_conditional_series_sequence_table(
                        row_dict, return_only=True
                    )

                    sequence_query_list.append(sequence_query)

                execute_all_insert_queries(
                    series_query,
                    pos_query_list,
                    cas_legs_query_list,
                    sequence_query_list,
                )

                # destroy pop up
                create_conditional_series_popup.destroy()

                # set df to empty list
                variables.series_sequence_table_df = []

                # create series sequence table df
                variables.series_sequence_table_df = []

                # update GUI table
                self.update_conditional_series_table()

        def on_click_confirm_details_button():

            # get updated unique id
            unique_id = rows_entry.get().strip()

            # check if pop up is for relauching
            if values_relaunch != None:

                if not unique_id.isnumeric():
                    # Error Message
                    error_title = (
                        error_string
                    ) = f"Error, Please provide valid base unique ID"
                    variables.screen.display_error_popup(error_title, error_string)

                    return

                # Get combo details dataframe
                local_combo_details_df = copy.deepcopy(variables.combo_table_df)

                # All the Unique IDs in the System
                all_unique_ids_in_system = local_combo_details_df["Unique ID"].tolist()

                # convert it to integer
                unique_id = int(unique_id)

                # check if unique id is not present system
                if unique_id not in all_unique_ids_in_system:
                    # Error Message
                    error_title = (
                        error_string
                    ) = f"Error, Base unique ID not present in system"
                    variables.screen.display_error_popup(error_title, error_string)

                    return

                if not flag_edit:

                    # Number of CAS Conditions that exists
                    '''number_of_conditions = do_cas_condition_exists_for_unique_id_in_db(
                        unique_id
                    )

                    number_of_conditions += (
                        do_cas_condition_series_exists_for_unique_id_in_db(unique_id)
                    )

                    # If a condition already exists, display error popup
                    if number_of_conditions > 0:
                        # TODO
                        # Throw Error Popup
                        variables.screen.display_error_popup(
                            f"Unique ID : {unique_id}, Condition already exists",
                            "A Condition already exists, can not add another.",
                        )
                        return'''
                    pass

                if flag_edit:

                    # Number of CAS Conditions that exists
                    '''number_of_conditions = do_cas_condition_exists_for_unique_id_in_db(
                        unique_id
                    )

                    number_of_conditions += (
                        do_cas_condition_series_exists_for_unique_id_in_db(unique_id)
                    )

                    # If a condition already exists, display error popup
                    if number_of_conditions > 1:
                        # TODO
                        # Throw Error Popup
                        variables.screen.display_error_popup(
                            f"Unique ID : {unique_id}, Condition already exists",
                            "A Condition already exists, can not add another.",
                        )
                        return'''
                    pass

                # set new value for column
                variables.series_sequence_table_df["Unique ID"] = unique_id

                # Change the value of column 'status' to queued
                # variables.series_sequence_table_df['Status'] = 'Queued'

                # Change the value of column 'status' to active for first row
                # variables.series_sequence_table_df.loc[0, 'Status'] = 'Active'

                # Change the value of column 'evaluation unique id' to new unique id where the value is old unique id
                variables.series_sequence_table_df.loc[
                    variables.series_sequence_table_df["Evaluation Unique ID"].isin(
                        [unique_id_old, str(unique_id_old)]
                    ),
                    "Evaluation Unique ID",
                ] = unique_id

                # Change the value of column 'trading unique id' to new unique id where the value is old unique id
                variables.series_sequence_table_df.loc[
                    variables.series_sequence_table_df["Trading Unique ID"].isin(
                        [unique_id_old, str(unique_id_old)]
                    ),
                    "Trading Unique ID",
                ] = unique_id

                # update table
                self.update_create_series_pop_up_table()

                # make it disabled
                rows_entry.config(state="readonly")

            # set flag of details confirmation to true
            self.flag_add_conditional_order_confirm = True

            if not flag_multi:

                # disabled dropdown
                account_id_options_combo_box.config(state="disabled")

            else:

                # init
                selected_items = []

                # Get list of selections
                for i in listbox.curselection():
                    # Split item in listbox
                    accounts_type = listbox.get(i)

                    selected_items.append(accounts_type)

                if selected_items == []:
                    # Error pop up
                    error_title = (
                        f"For Unique  ID: {unique_id}, Account ID list is unavailable."
                    )
                    error_string = (
                        f"For Unique ID: {unique_id}, Account ID list is unavailable."
                    )

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                # erase selection in listbox
                listbox.delete(0, tk.END)

                # insert only selcted items in listbox
                for ind, item in enumerate(selected_items):

                    listbox.insert(i, item)

                # make it selected
                for i in range(listbox.size()):

                    try:

                        listbox.select_set(i)

                    except Exception as e:

                        if variables.flag_debug_mode:
                            print(e)

                # disabled listbox
                listbox.config(state="disabled")

                # Get list of selections
                for i in listbox.curselection():
                    # Split item in listbox
                    accounts_type = listbox.get(i)

            # disabled dropdown
            bypass_rm_account_checks_options_combo_box.config(state="disabled")

            # make it disabled
            flag_execution_engine_combo_box.config(state="disabled")

        def on_click_combination_condition_button():

            try:

                reference_price = (
                    variables.unique_id_to_prices_dict[unique_id]["BUY"]
                    + variables.unique_id_to_prices_dict[unique_id]["SELL"]
                ) / 2

            except Exception as e:

                reference_price = None

                if variables.flag_debug_mode:

                    print(f"Exception for getting price for combo, Exp: {e}")

            # method to get condition
            variables.screen.screen_cas_obj.display_enter_condition_popup(
                unique_id=unique_id,
                cas_add_or_switch="Series",
                series_pop_up=condition_entry,
                reference_price=reference_price,
            )

        def create_index_popup():
            # Create a enter unique id popup window
            enter_index_entry_popup = tk.Toplevel()

            title = f"Add Index For Order, Series ID: {series_id}"
            enter_index_entry_popup.title(title)

            enter_index_entry_popup.geometry("500x120")

            # Create main frame
            enter_enter_index_entry_popup_popup_frame = ttk.Frame(
                enter_index_entry_popup, padding=20
            )
            enter_enter_index_entry_popup_popup_frame.pack(fill="both", expand=True)

            # Create a frame for the input fields
            enter_index_frame = ttk.Frame(
                enter_enter_index_entry_popup_popup_frame, padding=20
            )
            enter_index_frame.pack(fill="both", expand=True)

            # Add a label and entry field for the user to enter an integer
            ttk.Label(
                enter_index_frame, text="Enter Index for Conditional Order:"
            ).grid(column=0, row=3, padx=5, pady=5)

            # Adding the entry for user to insert the trading unique id
            index_entry = ttk.Entry(enter_index_frame)
            index_entry.grid(column=1, row=3, padx=5, pady=5)

            def on_click_proceed_button():

                index = index_entry.get().strip()

                if not index.isnumeric():
                    # Error pop up
                    error_title = (
                        f"For Series  ID: {series_id}, Index value is not valid."
                    )
                    error_string = (
                        f"For Series ID: {series_id}, Index value is not valid."
                    )

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                status_lst = variables.series_sequence_table_df["Status"].to_list()

                if status_lst.count("Active") > 0:

                    low_margin = status_lst.index("Active") + 1

                else:

                    low_margin = len(variables.series_sequence_table_df)

                if (
                    int(index) <= low_margin
                    or int(index) > len(variables.series_sequence_table_df) + 1
                ):
                    # Error pop up
                    error_title = (
                        f"For Series  ID: {series_id}, Index value is out-of-bound."
                    )
                    error_string = (
                        f"For Series ID: {series_id}, Index value is out-of-bound."
                    )

                    variables.screen.display_error_popup(error_title, error_string)

                    return

                index = int(index) - 1

                on_click_create_button(index=index)

                enter_index_entry_popup.destroy()

            # Add a button to create the combo
            proceed_button = ttk.Button(
                enter_index_frame, text="Proceed", command=on_click_proceed_button
            )

            proceed_button.grid(column=2, row=3, padx=5, pady=5)

            # Place in center
            enter_index_frame.place(relx=0.5, anchor=tk.CENTER)
            enter_index_frame.place(y=30)

        if flag_edit:

            # Add a button to create the conditional order
            create_button = ttk.Button(
                create_conditional_series_frame,
                text="Add Conditional Order",
                command=lambda: create_index_popup(),
            )

            create_button.grid(column=1, row=7, padx=0, pady=0)

        else:

            # Add a button to create the conditional order
            create_button = ttk.Button(
                create_conditional_series_frame,
                text="Add Conditional Order",
                command=lambda: on_click_create_button(),
            )

            create_button.grid(column=1, row=7, padx=0, pady=0)

        if values_relaunch != None and not flag_edit:

            create_button.config(state="disabled")

        # Add a button to confirm details
        confirm_details = ttk.Button(
            create_conditional_series_frame,
            text="Confirm Details",
            command=lambda: on_click_confirm_details_button(),
        )

        confirm_details.grid(column=4, row=1, padx=5, pady=5, sticky="n")

        # Add a button to add combo condition
        combo_condition_button = ttk.Button(
            create_conditional_series_frame,
            text="Combination Condition",
            command=lambda: on_click_combination_condition_button(),
        )

        combo_condition_button.grid(column=1, row=3, padx=5, pady=5)

        # Add a button to create the conditional series
        create_series_button = ttk.Button(
            create_conditional_series_button_frame,
            text="Create Conditional Series",
            command=lambda: on_click_create_series_button(),
        )

        create_series_button.pack(pady=15)

        # Place in center
        create_conditional_series_frame.place(relx=0)
        create_conditional_series_frame.place(x=0, y=0)

    # Update create series pop up table
    def update_create_series_pop_up_table(self):

        local_series_sequence_table = copy.deepcopy(variables.series_sequence_table_df)
        # print(local_series_sequence_table.to_string())

        # Get all item IDs in the Treeview
        item_ids = self.series_sequence_table.get_children()

        # Delete each item from the Treeview
        for item_id in item_ids:
            self.series_sequence_table.delete(item_id)

        # Check if df is empty
        if local_series_sequence_table.empty:
            return

        # Init
        counter = 0

        # Iterate rowws in df
        for indx, row in local_series_sequence_table.iterrows():

            # table id
            table_id = row["Table ID"]

            # convert to tuple
            row = tuple(row)

            # add rows
            if counter % 2 == 1:

                self.series_sequence_table.insert(
                    "",
                    "end",
                    iid=table_id,
                    text="",
                    values=row,
                    tags=("oddrow",),
                )

            else:

                self.series_sequence_table.insert(
                    "",
                    "end",
                    iid=table_id,
                    text="",
                    values=row,
                    tags=("evenrow",),
                )

            counter += 1

    # Method to make series failed
    def make_series_failed(self, unique_id):

        series_fail_for_deleted_unique_id(unique_id)

        self.update_conditional_series_table()

    # Method to update conditional series table
    def update_conditional_series_table(self):

        # get copy of data frame
        local_conditional_series_table = get_conditional_series_df()
        # print(local_series_sequence_table.to_string())

        # Get all item IDs in the Treeview
        item_ids = self.conditional_series_table.get_children()

        # Delete each item from the Treeview
        for item_id in item_ids:
            self.conditional_series_table.delete(item_id)

        # Check if df is empty
        if local_conditional_series_table.empty:
            return

        # Init
        counter = 0

        # Iterate rowws in df
        for indx, row in local_conditional_series_table.iterrows():

            # table id
            table_id = row["Series ID"]

            # convert to tuple
            row = tuple(row)

            # add rows
            if counter % 2 == 1:

                self.conditional_series_table.insert(
                    "",
                    "end",
                    iid=table_id,
                    text="",
                    values=row,
                    tags=("oddrow",),
                )

            else:

                self.conditional_series_table.insert(
                    "",
                    "end",
                    iid=table_id,
                    text="",
                    values=row,
                    tags=("evenrow",),
                )

            counter += 1

    # Method to monitor trigger condition of series
    def monitor_conditional_series(self):

        try:
            # get copy of data frame
            local_conditional_series_table = get_conditional_series_df(
                flag_inactive=True
            )

            # Sorted 'user_input_fields' longest word first, local copy
            user_input_fields = copy.deepcopy(variables.cas_table_fields_for_condition)
            user_input_fields = sorted(user_input_fields, key=lambda word: -len(word))

            # Cas Table Dataframe
            cas_table_data_frame = copy.deepcopy(variables.cas_table_values_df)

            # iterate rows
            for ind, row in local_conditional_series_table.iterrows():

                # get values of series
                user_condition = row["Combination Condition"]

                series_id = row["Series ID"]

                series_condition = row["Series ID Condition"]

                eval_uid = row["Evaluation Unique ID"]

                account_id = row["Account ID"]

                positions_df = get_positions_from_series_positions_table_for_series(
                    series_id
                )

                # get account id list
                account_lst = account_id.split(",")

                if not positions_df.empty:
                    account_lst = (
                        account_id.split(",") + positions_df["Account ID"].to_list()
                    )

                    account_lst = list(set(account_lst))

                """if isinstance(account_lst,str) and account_lst.count(',') == 0:

                    if account_lst not in variables.current_session_accounts:
                        # Throw Error Popup
                        variables.screen.display_error_popup(
                            f"Unique ID : {unique_id}, Account ID not present in current session",
                            f"Account ID: {account_lst} not present in current session",
                        )

                        return

                else:"""

                fail_account_lst = []

                for accnt_id in account_lst:

                    if accnt_id not in variables.current_session_accounts:
                        fail_account_lst.append(accnt_id)

                if fail_account_lst != []:

                    continue

                refer_price = row["Reference Price"]
                refer_position = row["Reference Position"]

                if refer_price not in ["None", "N/A", None]:
                    refer_price = float(refer_price)

                if refer_position.isnumeric():
                    refer_position = int(refer_position)

                unique_id = row["Unique ID"]

                # check if evaluation uniuqe id is present
                if eval_uid != "None":

                    # convert it to integer
                    eval_uid = int(eval_uid)

                    # Get combo details dataframe
                    local_combo_details_df = copy.deepcopy(variables.combo_table_df)

                    # All the Unique IDs in the System
                    all_unique_ids_in_system = local_combo_details_df[
                        "Unique ID"
                    ].tolist()

                    if eval_uid not in all_unique_ids_in_system:
                        # fail conditional series if unique id present in as trading or evaluation unique id
                        variables.screen.screen_conditional_series_tab.make_series_failed(
                            unique_id
                        )

                        self.update_conditional_series_table()

                        continue

                # initialize
                eval_result = False

                # check if condition is resent
                if user_condition != "None":

                    # filter the DataFrame to get the row where "Unique ID" is equal to unique_id
                    filtered_df = cas_table_data_frame[
                        cas_table_data_frame["Unique ID"] == eval_uid
                    ]

                    try:
                        # get the first row of the filtered DataFrame using .iloc
                        cas_row = filtered_df.iloc[0]
                    except Exception as e:

                        # Print to console
                        if variables.flag_debug_mode:
                            print(f"\nUnique ID: {unique_id}")
                            print(
                                f"Cas Table Main Df", cas_table_data_frame.to_string()
                            )
                            print(f"Filtered Df", filtered_df.to_string())

                            print(f"Error in Utilities {e}")
                        continue

                    # Eval Result (condition passed or not), solved_conditon_string(will have values and equation) or False incase eval is False
                    eval_result, solved_condition_string = evaluate_condition(
                        user_input_fields,
                        cas_row,
                        user_condition,
                        refer_price=refer_price,
                        refer_position=refer_position,
                    )

                    # get boolean value
                    eval_result = bool(eval_result)

                else:

                    if variables.flag_series_condition.upper() == "AND":

                        # set to true
                        eval_result = True

                    else:

                        # set to false
                        eval_result = False

                # get value of sequences from db
                series_id_cond = get_series_column_value_from_db(
                    series_id=series_id, column_name_as_in_db="Series ID Condition"
                )

                # Init
                series_id_cond_status = False

                all_series_ids_in_system = []

                # Check if series id condition is not none
                if series_id_cond not in ["None", None]:

                    # get copy of data frame
                    local_conditional_series_table = get_conditional_series_df()

                    if local_conditional_series_table.empty:

                        all_series_ids_in_system = []

                    else:
                        # All the series IDs in the System
                        all_series_ids_in_system = local_conditional_series_table[
                            "Series ID"
                        ].tolist()

                    if int(series_id_cond) not in all_series_ids_in_system:
                        # fail conditional series if unique id present in as trading or evaluation unique id
                        variables.screen.screen_conditional_series_tab.make_series_failed(
                            unique_id
                        )

                        self.update_conditional_series_table()

                        continue

                    # get value of sequences from db
                    series_id_cond_status = get_series_column_value_from_db(
                        series_id=series_id_cond, column_name_as_in_db="Status"
                    )

                    # check status of evaluation series id
                    if series_id_cond_status == "Completed":

                        series_id_cond_status = True

                    else:

                        series_id_cond_status = False

                else:

                    if variables.flag_series_condition.upper() == "AND":

                        # set to true
                        series_id_cond_status = True

                    else:

                        # set to false
                        series_id_cond_status = False

                    # set to true in case no condition available
                    # series_id_cond_status = True


                if variables.flag_series_condition.upper() == "AND":

                    # check and value of both conditions
                    if eval_result and series_id_cond_status:

                        self.start_series(selected_item=series_id)

                else:

                    # check and value of both conditions
                    if eval_result or series_id_cond_status:
                        self.start_series(selected_item=series_id)

        except Exception as e:

            if variables.flag_debug_mode:

                print(f"Exception inside 'monitor_conditional_series', Exp: {e}")
