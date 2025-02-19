from com.mysql_io_filter_tab import *
from com.utilities import evaluate_condition


# Method to calculate values of filter conditions
def update_filter_condition_values(cas_table_values):
    # Get active filter conditions
    filter_conditions_df = get_all_filter_conditions(active="Yes")

    # Get copy of cas tble values
    cas_table_update_values = copy.deepcopy(cas_table_values)

    # create dataframe
    cas_table_update_values_df = pd.DataFrame(
        cas_table_update_values, columns=variables.cas_table_columns
    )

    # check if cas table df is empty
    if cas_table_update_values_df.empty:
        # consider all unique id passed
        variables.unique_ids_list_of_passed_condition = []

        return

    # check if conditions df is empty
    if filter_conditions_df.empty:
        # consider all unique id passed
        variables.unique_ids_list_of_passed_condition = cas_table_update_values_df[
            "Unique ID"
        ].to_list()

        return

    # Get condition expression dictionary
    condition_expressions = filter_conditions_df["Condition Expression"].to_list()
    condition_names = filter_conditions_df["Condition Name"].to_list()

    # Init ddict to map unique id to filter conditions value
    condition_values = {}

    try:
        # Iterate each row in dataframe
        for index, cas_row in cas_table_update_values_df.iterrows():
            # get unique id
            unique_id = cas_row["Unique ID"]

            # Check if flag for filter condition is off
            if not variables.flag_enable_filter_condition:
                # set value for each unique id to true
                condition_values[unique_id] = True

                continue

            # Initialize a list
            values_for_row = []

            # Iterate each custom column
            for expression, condition_name in zip(
                condition_expressions, condition_names
            ):
                try:
                    # Get Expression and flag for valid results to eval further
                    _, expression = evaluate_condition(
                        variables.cas_table_fields_for_expression,
                        cas_row,
                        expression,
                        None,
                        None,
                    )

                    # Evaluate value of expression
                    expression_value = eval(str(expression))

                    # Apeend value to list
                    values_for_row.append(bool(expression_value))

                except Exception as e:
                    # Append value to list
                    values_for_row.append(bool(False))

                    # Print  to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception while calculating values of filter conditions, Exp: {e}"
                        )

            # If number of condition valid values is greater than 0
            if len(values_for_row) > 0:
                # Get final condition valid value from all condition valid values
                condition_values[unique_id] = all(values_for_row)

            else:
                # Set it to true in case of no conditions
                condition_values[unique_id] = True

        # get unique ids for which conditions passed
        unique_ids_passed = [key for key, value in condition_values.items() if value]

        # Make lsit of unique ids with passed conditions
        variables.unique_ids_list_of_passed_condition = unique_ids_passed

    except Exception as e:
        # get unique ids for which conditions passed
        variables.unique_ids_list_of_passed_condition = []

        # Print  to console
        if variables.flag_debug_mode:
            print(f"Exception while adding values of filter conditions, Exp: {e}")
