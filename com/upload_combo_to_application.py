import pandas as pd
from com.variables import *
from com.combination_helper import *
import numpy as np


# Check validilty of data in csv file
def check_validity_of_dataframe(combo_dataframe_to_be_checked):
    # Getting list of valid columns
    combination_dataframe_columns = copy.deepcopy(
        variables.columns_for_download_combo_to_csv
    )

    # Getting columns of dataframe to-be-checked
    combo_dataframe_to_be_checked_columns = combo_dataframe_to_be_checked.columns

    # Check if columns in combination dataframe for upload combination are valid
    for allowed_columns_name, user_input_col_name in zip(
        combination_dataframe_columns, combo_dataframe_to_be_checked_columns
    ):
        if allowed_columns_name != user_input_col_name:
            error_title = f"Error columns are not matching"
            error_string = f"Columns are not matching in file, Invalid column: '{user_input_col_name}'"

            error_string = make_multiline_mssg_for_gui_popup(error_string)

            return False, error_title, error_string

    # flag to check whether we are at start or end of combination
    flag_is_row_between_soc_and_eoc = False

    # Count number of legs
    num_of_legs = 0

    # To check format is valid or not
    for indx, row in combo_dataframe_to_be_checked.iterrows():
        # If row contain #SOC and no other combo is in started but not finished
        if row["Type"] == "#SOC" and not flag_is_row_between_soc_and_eoc:
            # Turning flag to true
            flag_is_row_between_soc_and_eoc = True

            # Count number of legs
            num_of_legs = 0

        # If row contain #SOC and other combo is in started but not finished
        elif row["Type"] == "#SOC" and flag_is_row_between_soc_and_eoc:
            error_title = f"Error Row no - {indx + 2}, previous #SOC not finished"
            error_string = (
                f"Row no - {indx + 2}, previous #SOC for combo is not finished"
            )
            return False, error_title, error_string

        # If row contain #EOC and #SOC was encountered for same combo and there were at least one #LEG between #SOC and #EOC
        elif (
            row["Type"] == "#EOC"
            and flag_is_row_between_soc_and_eoc
            and num_of_legs > 0
        ):
            # Turning flag to false
            flag_is_row_between_soc_and_eoc = False

        # If row contain #EOC and #SOC was encountered for same combo and there were no #LEG between #SOC and #EOC
        elif (
            row["Type"] == "#EOC"
            and flag_is_row_between_soc_and_eoc
            and num_of_legs == 0
        ):
            error_title = f"Error Row no - {indx + 2}, No #LEG between #SOC and #EOC"
            error_string = f"Row no - {indx + 2}, No #LEG between #SOC and #EOC"
            return False, error_title, error_string

        # If row contain #EOC and #SOC was not encountered for same combo
        elif row["Type"] == "#EOC" and not flag_is_row_between_soc_and_eoc:
            error_title = f"Error Row no - {indx + 2}, No prior #SOC found"
            error_string = f"Row no - {indx + 2}, No prior #SOC found for #EOC"
            return False, error_title, error_string

        # If row contain #LEG and #SOC was encountered for same combo
        elif row["Type"] == "#LEG" and flag_is_row_between_soc_and_eoc:
            # Count number of legs
            num_of_legs += 1

        # If row contain #EOC and #SOC was not encountered for same combo
        elif row["Type"] == "#LEG" and not flag_is_row_between_soc_and_eoc:
            error_title = f"Error Row no - {indx + 2}, No prior #SOC found"
            error_string = f"Row no - {indx + 2}, No prior #SOC found for #LEG"
            return False, error_title, error_string

        # If row contain neither #SOC, #LEG and #EOC
        elif row["Type"] != "#LEG" and row["Type"] != "#SOC" and row["Type"] != "#EOC":
            error_title = f"Error Row no - {indx + 2}, Invalid Type value"
            error_string = f"Row no - {indx + 2}, Invalid Type value"
            return False, error_title, error_string

    # To check if last line was #EOC or not
    if flag_is_row_between_soc_and_eoc:
        print(f"Inside check_validity_of_dataframe, #SOC and #EOC are not aligned")

        error_title = f"Error, Last row is not #EOC"
        error_string = f"Last row value is not #EOC"
        return False, error_title, error_string

    return True, "No Error", "No Error"


# Get numbers from error string
def extract_leg_number_from_error_string(sentence):
    leg_number = re.findall(r"\d+\.?\d*", sentence)

    return [float(num) for num in leg_number]


# Create combination based on values in csv file
def create_combo_wrapper(
    list_of_tuple_of_values,
    indx,
    input_from_db=False,
    input_from_cas_tab=False,
    input_series=False,
):
    if not input_series:
        # Create combination and check if there is any error
        (
            show_error_popup,
            error_title,
            error_string,
            combination_obj,
        ) = create_combination(
            list_of_tuple_of_values,
            input_from_db=input_from_db,
            input_from_cas_tab=input_from_cas_tab,
        )

        # Show pop up in event of error
        if show_error_popup == True:
            # Get leg number in combo where error happened
            leg_number = extract_leg_number_from_error_string(error_string)

            # Check length of leg number is greater than zero
            if len(leg_number) > 0:
                error_string = f"Row no - {int(indx + leg_number[0])}, " + error_string
                error_string = make_multiline_mssg_for_gui_popup(error_string)
            else:
                error_string = f"Row no - {int(indx)}, " + error_string
                error_string = make_multiline_mssg_for_gui_popup(error_string)

            variables.screen.display_error_popup(error_title, error_string)

            return "N/A", "N/A"
        else:
            unique_id = copy.deepcopy(variables.unique_id)

            # Increasing it so we can use it.
            variables.unique_id += 1

            # Subscribe the MktData and Insert Combination in the db
            subscribe_mktdata_combo_obj(combination_obj)
            insert_combination_db(True, combination_obj)

            # single_combo_values(combination_obj)

            # reset counter
            variables.counter_trade_rm_checks = 10**10

            return combination_obj, unique_id

    else:
        # Create combination and check if there is any error
        combination_obj = create_combination(
            list_of_tuple_of_values, input_from_db=True, input_from_cas_tab=True
        )

        return combination_obj


# Function to get file path for csv file and upload combinations from csv file to application
def upload_combo_from_csv_to_app(csv_file_path, upload_combo_button):
    try:
        # get csv file from file path
        combo_dataframe = pd.read_csv(csv_file_path)

        # Replace null values by None string
        combo_dataframe = combo_dataframe.fillna("None")

    except Exception as e:
        # Error Message
        error_title = "Error reading the Order CSV file"
        error_string = f"Unable to read the CSV file"
        variables.screen.display_error_popup(error_title, error_string)

        # Enabled upload combinations button
        upload_combo_button.config(state="enabled")

        return

    # Check validaity of dataframe
    (
        is_combo_df_valid,
        error_title_from_validation,
        error_string_from_validation,
    ) = check_validity_of_dataframe(combo_dataframe)

    # Show pop in event of file format is not correct
    if not is_combo_df_valid:
        # Error Message
        error_title = error_title_from_validation
        error_string = error_string_from_validation

        # Make error string multiline
        error_string = make_multiline_mssg_for_gui_popup(error_string)

        variables.screen.display_error_popup(error_title, error_string)

        # Enabled upload combinations button
        upload_combo_button.config(state="enabled")

        return

    # flag to check whether we are at start or end of combination
    flag_is_row_between_soc_and_eoc = False

    # Defining list of tuples
    list_of_tuple_of_values = []

    # Get columns of dataframe
    combo_df_columns = combo_dataframe.columns

    # Keep track of row which is reason for error
    error_row_num = 0

    # Iniy list
    combo_obj_list = []
    unique_id_list = []

    for indx, row in combo_dataframe.iterrows():
        if row["Type"] == "#SOC" and not flag_is_row_between_soc_and_eoc:
            # Initializing list for every new combination
            list_of_tuple_of_values = []

            # Setting flag to true
            flag_is_row_between_soc_and_eoc = True

            # save row number for start of every combination
            error_row_num = indx + 2

        elif row["Type"] == "#EOC" and flag_is_row_between_soc_and_eoc:
            # Create combination one by one
            combination_obj, unique_id_added = create_combo_wrapper(
                list_of_tuple_of_values,
                error_row_num,
                False,
                False,
            )

            # check if combo obj and unique id is not N/A
            if combination_obj != "N/A" and unique_id_added != "N/A":
                # append
                combo_obj_list.append(combination_obj)
                unique_id_list.append(unique_id_added)

            # Setting flag to false
            flag_is_row_between_soc_and_eoc = False

        elif flag_is_row_between_soc_and_eoc:
            # Replace leg number with unique id
            row["Type"] = variables.unique_id

            # # Converting None to empty string values
            for column in combo_df_columns:
                if row[column] == "None":
                    row[column] = ""

            # Add row of values for combination
            list_of_tuple_of_values.append(tuple(row))

    # Create a thread and pass the result_queue as an argument
    new_combo_values_thread = threading.Thread(
        target=get_values_for_new_combo,
        args=(
            combo_obj_list,
            unique_id_list,
        ),
    )

    # Start the thread
    new_combo_values_thread.start()

    # Enabled upload combinations button
    upload_combo_button.config(state="enabled")

    # Set counter to big number so the cas values can be updated

    """variables.flag_update_long_term_value = True
    variables.flag_update_intra_day_value = True
    variables.flag_update_hv_related_value = True
    variables.flag_update_volume_related_value = True
    variables.flag_update_support_resistance_and_relative_fields = True
    variables.flag_update_atr_for_order = True"""


# Method to make multiline message
def make_multiline_mssg_for_gui_popup(error_string):
    # Split in to line
    words = error_string.split()
    new_string = ""
    line_len = 0
    for word in words:
        if line_len + len(word) + 1 > 55:
            new_string += "\n"
            line_len = 0
        if line_len > 0:
            new_string += " "
            line_len += 1
        new_string += word
        line_len += len(word)

    return new_string
