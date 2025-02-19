import pandas as pd
from tkinter import filedialog
from com.variables import *


# Metthod to save combination in CSV file from app
def download_combo_from_app_to_csv(
    combination_dataframe_grouped_on_unique_id,
    combo_dataframe_columns,
    download_combo_button,
):
    # Create an empty DataFrame with columns
    combo_dataframe_to_csv = pd.DataFrame(columns=combo_dataframe_columns)

    # Creating list for empty values
    palce_holder_list = [""] * (len(combo_dataframe_columns) - 1)

    # create list for start of combination row
    data_list = [["#SOC"] + palce_holder_list]
    start_combo_row_values_dataframe = pd.DataFrame(
        data_list, columns=combo_dataframe_columns
    )

    # create list for end of combination row
    data_list = [["#EOC"] + palce_holder_list]
    end_combo_row_values_dataframe = pd.DataFrame(
        data_list, columns=combo_dataframe_columns
    )

    # Getting unique ids in current watchlist
    local_unique_id_list_of_selected_watchlist = copy.deepcopy(
        variables.unique_id_list_of_selected_watchlist
    )

    # Emptry listt for unique ids in watchlist
    local_unique_id_list_of_selected_watchlist_list = []

    try:
        # Checking if unique ids list in watchlist is empty
        if local_unique_id_list_of_selected_watchlist == "None":
            # Error Message
            error_title = error_string = (
                f"Error - No Unique IDs in Watchlist to Download Combinations"
            )
            variables.screen.display_error_popup(error_title, error_string)

            # Enabled download combo button
            download_combo_button.config(state="enabled")

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

            except Exception as e:
                # Print to console
                if variables.flag_debug_mode:
                    print(e)
                # Error Message
                error_title = error_string = (
                    f"Error - Filtering Download Combinations Dataframe Failed"
                )
                variables.screen.display_error_popup(error_title, error_string)

                # Enabled download order button
                download_combo_button.config(state="enabled")

                return

        # Check if watchlist is ALL
        elif local_unique_id_list_of_selected_watchlist == "ALL":
            # Get combo object using unique ids
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )

            # Get all unique ids in system
            local_unique_id_list_of_selected_watchlist_list = (
                local_unique_id_to_combo_obj.keys()
            )

    except Exception as e:
        # Error Message
        error_title = error_string = f"Error - In Getting Unique IDs from Watchlist"
        variables.screen.display_error_popup(error_title, error_string)

        # Enabled download order button
        download_combo_button.config(state="enabled")

        return

    # Iterate over the groups
    for combo_df_for_unique_id_tuple in combination_dataframe_grouped_on_unique_id:
        # Get combo dataframe specific for unique id
        combo_df_for_unique_id = combo_df_for_unique_id_tuple[1]

        # Get unique id
        unique_id = combo_df_for_unique_id_tuple[0]

        # Filter based on unique ids present in watchlist
        if unique_id not in local_unique_id_list_of_selected_watchlist_list:
            continue

        # Drop Unique ID column from dataframe
        combo_df_for_unique_id = combo_df_for_unique_id.drop(["Unique ID"], axis=1)

        # Add "#SOC" row to dataframe for combo
        combo_dataframe_to_csv = pd.concat(
            [combo_dataframe_to_csv, start_combo_row_values_dataframe],
            ignore_index=True,
        )

        # Add a new column 'Leg' with incrementing values
        combo_df_for_unique_id.insert(
            0, "Type", ["#LEG" for i in range(len(combo_df_for_unique_id))]
        )

        # Add all leg rows to dataframe
        combo_dataframe_to_csv = pd.concat(
            [combo_dataframe_to_csv, combo_df_for_unique_id], ignore_index=True
        )

        # Add "#EOC" row to dataframe for combo
        combo_dataframe_to_csv = pd.concat(
            [combo_dataframe_to_csv, end_combo_row_values_dataframe], ignore_index=True
        )

    # Open a file dialog to choose the save location and filename
    file_path = filedialog.asksaveasfilename(defaultextension=".csv")

    # Check if a file path was selected
    if file_path:
        # Save the DataFrame as a CSV file
        combo_dataframe_to_csv.to_csv(file_path, index=False)

    # Enabled download combo button
    download_combo_button.config(state="enabled")
