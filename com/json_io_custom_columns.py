import json
import os
from com.variables import *

# Method to check if json file exists
def check_if_json_file_exists():

    try:
        # Folder path
        folder_path = variables.custom_columns_json_csv_file_path

        # Check if the folder already exists
        if not os.path.exists(folder_path):

            # Create the folder
            os.makedirs(folder_path)

        # Specify the path to the JSON file
        file_path = folder_path + "/" + "custom_columns.json"

        # Check if the file already exists
        if not os.path.exists(file_path):

            # Create an empty dictionary to store data
            data = {}

            # Create key for custom columns
            data["Custom Columns"] = {}

            # Write the data to the JSON file
            with open(file_path, "w") as file:
                json.dump(data, file, indent=2)

        return True

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"JSON file for custom columns was not found, Exp: {e}")

        return False


# Method get max column ID from JSON file
def get_custom_column_id_from_json():

    try:
        # Folder path
        folder_path = variables.custom_columns_json_csv_file_path

        # Specify the path to the JSON file
        file_path = folder_path + "/" + "custom_columns.json"

        with open(file_path, "r") as file:
            data = json.load(file)

        # Initialize a variable to keep track of the maximum age
        max_id = 0

        # Iterate through each custom column object to find the maximum id present
        for custom_column in data["Custom Columns"]:

            max_id = max(max_id, int(float(custom_column)))

        variables.custom_column_id = max_id + 1

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Could not get custom column ID from JSON file, Exp: {e}")

        sys.exit(
            f"Could not get custom column ID from JSON file: {variables.custom_columns_json_csv_file_path}"
        )


# Method to add custom column in json file
def add_custom_column_in_json(column_name, column_expression, column_description):

    try:
        # Folder path
        folder_path = variables.custom_columns_json_csv_file_path

        # Specify the path to the JSON file
        file_path = folder_path + "/" + "custom_columns.json"

        # Open json file and load data from it
        with open(file_path, "r") as file:
            data = json.load(file)

        # Get custom column ID
        custom_column_id = variables.custom_column_id

        # Increment custom column id
        variables.custom_column_id += 1

        # Add the new custom column object
        new_custom_column = {
            "Column ID": custom_column_id,
            "Column Name": column_name,
            "Column Expression": column_expression,
            "Column Description": column_description,
        }

        data["Custom Columns"][custom_column_id] = new_custom_column

        # Write the updated data back to the JSON file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=2)

        # Update secondary columns dictionary
        update_secondary_columns()

        # Update CAS table
        variables.screen.screen_cas_obj.update_cas_tale_gui()

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Could not add custom column to JSON file, Exp: {e}")


# Method to delete custom column from JSON
def delete_custom_column_from_json(custom_column_id):

    # format column id to string
    custom_column_id = str(custom_column_id)

    try:
        # Folder path
        folder_path = variables.custom_columns_json_csv_file_path

        # Specify the path to the JSON file
        file_path = folder_path + "/" + "custom_columns.json"

        # Open json file and load data from it
        with open(file_path, "r") as file:
            data = json.load(file)

        del data["Custom Columns"][custom_column_id]

        # Write the updated data back to the JSON file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=2)

        # Update secondary columns dictionary
        update_secondary_columns()

        # Update CAS table
        variables.screen.screen_cas_obj.update_cas_tale_gui()

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Could not delete custom column from JSON file, Exp: {e}")


# Method to get all custom column from json file
def get_all_custom_columns_from_json():

    try:
        # Folder path
        folder_path = variables.custom_columns_json_csv_file_path

        # Specify the path to the JSON file
        file_path = folder_path + "/" + "custom_columns.json"

        # Open json file and load data from it
        with open(file_path, "r") as file:
            data = json.load(file)

        # Convert the dictionary to a dataframe
        custom_columns_df = pd.DataFrame.from_dict(
            data["Custom Columns"], orient="index"
        )

        # update datafrmae of custom column table
        variables.custom_columns_table_dataframe = custom_columns_df

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Could not get custom columns data from JSON file, Exp: {e}")


# Method to check if column name is not repeated
def check_new_column_name(column_name):

    try:
        # Folder path
        folder_path = variables.custom_columns_json_csv_file_path

        # Specify the path to the JSON file
        file_path = folder_path + "/" + "custom_columns.json"

        # Open json file and load data from it
        with open(file_path, "r") as file:
            data = json.load(file)

        # Convert the dictionary to a dataframe
        custom_columns_df = pd.DataFrame.from_dict(
            data["Custom Columns"], orient="index"
        )

        # check if dataframe is empty
        if custom_columns_df.empty:

            return True

        # get available column names from custom column table
        available_columns_cas_table = (
            custom_columns_df["Column Name"].to_list() + variables.cas_table_columns
        )

        # convert all columns names present in CAS table to upper case
        available_columns_cas_table = [
            column_name.upper() for column_name in available_columns_cas_table
        ]

        # check if new column to be added has duplicate name and if yes return true
        if column_name.upper() in available_columns_cas_table:

            return False

        else:

            return True

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Could not determine if column name is unique or not, Exp: {e}")

        return False


# Update secondary columns lists in CAS table
def update_secondary_columns():

    try:
        # Folder path
        folder_path = variables.custom_columns_json_csv_file_path

        # Specify the path to the JSON file
        file_path = folder_path + "/" + "custom_columns.json"

        # Open json file and load data from it
        with open(file_path, "r") as file:
            data = json.load(file)

        # Convert the dictionary to a dataframe
        custom_columns_df = pd.DataFrame.from_dict(
            data["Custom Columns"], orient="index"
        )

        # check if dataframe is empty
        if custom_columns_df.empty:

            return

        # Create a dictionary from the DataFrame columns
        variables.map_secondary_columns_to_expression_in_cas_table = {
            key: value
            for key, value in zip(
                custom_columns_df["Column Name"], custom_columns_df["Column Expression"]
            )
        }

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Could not determine if column name is unique or not, Exp: {e}")

        return
