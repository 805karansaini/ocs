from com.variables import *
import json

# Method to check if json file exists
def check_if_json_file_exists_for_lts_columns():

    try:
        # Folder path
        folder_path = variables.custom_columns_json_csv_file_path

        # Check if the folder already exists
        if not os.path.exists(folder_path):

            # Create the folder
            os.makedirs(folder_path)

        # Specify the path to the JSON file
        file_path = folder_path + "/" + "leg_to_combo_columns.json"

        # Check if the file already exists
        if not os.path.exists(file_path):

            # Create an empty dictionary to store data
            data = {}

            # Create key for custom columns
            data["Custom Leg to Combo Columns"] = ""

            # Write the data to the JSON file
            with open(file_path, "w") as file:
                json.dump(data, file, indent=2)

        return True

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"JSON file for leg-to-combo columns was not found, Exp: {e}")

        return False

# Get all leg-to-combo columns from JSON
def get_all_custom_ltc_columns_from_json():

    try:
        # Folder path
        folder_path = variables.custom_columns_json_csv_file_path

        # Specify the path to the JSON file
        file_path = folder_path + "/" + "leg_to_combo_columns.json"

        # Open json file and load data from it
        with open(file_path, "r") as file:
            data = json.load(file)


        return data["Custom Leg to Combo Columns"].split(',')


    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Could not get custom columns data from JSON file, Exp: {e}")

# Method to add columns in JSON
def add_custom_ltc_column_in_json(columns_string):

    try:
        # Folder path
        folder_path = variables.custom_columns_json_csv_file_path

        # Specify the path to the JSON file
        file_path = folder_path + "/" + "leg_to_combo_columns.json"

        # Open json file and load data from it
        with open(file_path, "r") as file:
            data = json.load(file)

        # Get custom column ID
        custom_column_id = variables.custom_column_id

        # Increment custom column id
        variables.custom_column_id += 1



        data["Custom Leg to Combo Columns"] = columns_string

        # Write the updated data back to the JSON file
        with open(file_path, "w") as file:
            json.dump(data, file, indent=2)

        # Update CAS table
        variables.screen.screen_cas_obj.update_cas_tale_gui()

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Could not add custom column to JSON file, Exp: {e}")