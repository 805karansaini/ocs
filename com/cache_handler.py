from com.variables import *
from com.mysql_io import update_cas_table_combination_data_to_cache_table_db


# update values cache DB table
def update_cache_data_in_db(cas_table_update_values):
    # Getting columns of cache data table
    local_cache_data_table_columns = copy.deepcopy(variables.cache_data_table_columns)

    # Iterating values
    for values_for_cas_table in cas_table_update_values:
        # Create dictionary of columns and values to be updated in the cache table in DB
        dict_of_col_name_and_values_to_be_updated_in_cache_table = {}

        # Unique ID
        unique_id = int(values_for_cas_table[0])

        # Iterating over cache column and value of column from CAS table
        for col_name_for_cache, cas_table_value in zip(
            local_cache_data_table_columns, values_for_cas_table
        ):
            try:
                # check if values are valid
                if cas_table_value not in ["N/A", None, "None"]:
                    dict_of_col_name_and_values_to_be_updated_in_cache_table[
                        col_name_for_cache
                    ] = cas_table_value
                else:
                    pass
                    # do not update this value in cache table
            except Exception as e:
                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Inside update_cache_data_in_db, Uniqude ID: {unique_id}, Exception Happend, Exp: {e}"
                    )

        # Update the Cache in DB
        if len(dict_of_col_name_and_values_to_be_updated_in_cache_table) > 0:
            # Run query and update the value in cache_table
            update_cas_table_combination_data_to_cache_table_db(
                unique_id, dict_of_col_name_and_values_to_be_updated_in_cache_table
            )
        else:
            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Inside update_cache_data_in_db, Uniqude ID: {unique_id}, No New Values for updation"
                )

            pass


# Replace cached data values for values which are not available
def process_the_latest_cas_indicator_values_fetched_from_cache_table_db(
    cache_table_values_in_tuples,
):
    # List of tuple of final values to display in CAS table
    values_to_be_displayed_in_cas_table = []

    try:
        # Current time in the target time zone
        current_time_in_target_time_zone = datetime.datetime.now(
            variables.target_timezone_obj
        )

        # Formatting current time in target timezone without milliseconds and convert it in string format
        current_time_in_target_time_zone = current_time_in_target_time_zone.strftime(
            "%Y-%m-%d %H:%M:%S %z"
        )

        # Convert current time in target timezone to datetime object
        current_time_in_target_time_zone = datetime.datetime.strptime(
            current_time_in_target_time_zone, "%Y-%m-%d %H:%M:%S %z"
        )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception Inside process_the_latest_cas_indicator_values_fetched_from_cache_table_db getting current time , Exp: {e}"
            )

        return None

    try:
        # Get row of all values for each unique id from cache DB table
        for cache_table_row in cache_table_values_in_tuples:
            # Define tuple for values to be displayed in cas table row
            row_of_values_to_be_added_in_cas_table_values = [cache_table_row[0]]

            # Get value for each column from cache table row (started iterating from index 1)
            for cache_table_column_value in cache_table_row[1:]:
                if cache_table_column_value not in ["N/A", None, "None"]:
                    # Get list of value and timestamp of cache column
                    cache_column_value_and_timestamp = cache_table_column_value.split(
                        "|"
                    )

                    # Get value of cache column
                    cache_column_value = cache_column_value_and_timestamp[0]

                    # Get timestamp of update time of cache column
                    last_update_time_of_column_value = cache_column_value_and_timestamp[
                        1
                    ]

                    # Format date and time of update of cache columns values into date time object
                    last_update_time_of_column_value_obj = datetime.datetime.strptime(
                        last_update_time_of_column_value, "%Y-%m-%d %H:%M:%S %z"
                    )

                    # Calculate the time difference between current time and update time of cache column value
                    difference_between_current_and_lut_time_for_column = (
                        current_time_in_target_time_zone
                        - last_update_time_of_column_value_obj
                    )

                    # Get time difference in term of minutes
                    difference_between_current_and_lut_for_column_in_minutes = (
                        difference_between_current_and_lut_time_for_column.total_seconds()
                        / 60
                    )

                    # Check if time difference is less than or equal to allowed lookback period for cache value
                    if (
                        difference_between_current_and_lut_for_column_in_minutes
                        <= variables.lookback_period_for_cache
                    ):
                        # Add cache column data to be displayed
                        row_of_values_to_be_added_in_cas_table_values.append(
                            cache_column_value
                        )

                    else:
                        # Add 'N/A' value to be displayed
                        row_of_values_to_be_added_in_cas_table_values.append("N/A")

                else:
                    # Add 'CAS column value to be displayed
                    row_of_values_to_be_added_in_cas_table_values.append("N/A")

            # Append row of values for each row in CAS table
            values_to_be_displayed_in_cas_table.append(
                tuple(row_of_values_to_be_added_in_cas_table_values)
            )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception Inside replacing invalid values in CAS table by cache table value, Exp: {e}"
            )

        return None

    # Return list of tuples of CAS table updated values
    return values_to_be_displayed_in_cas_table


# Replace null values in cas indicator by cached values
def replace_null_values_in_cas_table_from_cache_table(
    cas_table_update_values, cache_table_values_in_tuples
):
    # List of tuple of final values to display in CAS table
    values_to_be_displayed_in_cas_table = []

    try:
        # Current time in the target time zone
        current_time_in_target_time_zone = datetime.datetime.now(
            variables.target_timezone_obj
        )

        # Formatting current time in target timezone without milliseconds and convert it in string format
        current_time_in_target_time_zone = current_time_in_target_time_zone.strftime(
            "%Y-%m-%d %H:%M:%S %z"
        )

        # Convert current time in target timezone to datetime object
        current_time_in_target_time_zone = datetime.datetime.strptime(
            current_time_in_target_time_zone, "%Y-%m-%d %H:%M:%S %z"
        )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception Inside getting current time in target timezone to update CAS table using cache table value, Exp: {e}"
            )

        return cas_table_update_values

    try:
        # Get row of all values for each unique id from cas table and cache DB table
        for cas_table_row, cache_table_row in zip(
            cas_table_update_values, cache_table_values_in_tuples
        ):
            # Define tuple for values to be displayed in cas table row
            row_of_values_to_be_added_in_cas_table_values = [cas_table_row[0]]

            # Get value for each column from CAS table row and cache table row (started iterating from index 1)
            for cas_table_column_value, cache_table_column_value in zip(
                cas_table_row[1:], cache_table_row[1:]
            ):
                # Get value for CAS table column
                cas_column_value = cas_table_column_value

                # Check if CAS column has valid value or not
                if cas_column_value in [
                    "N/A",
                    None,
                    "None",
                ] and cache_table_column_value not in ["N/A", None, "None"]:
                    # Get list of value and timestamp of cache column
                    cache_column_value_and_timestamp = cache_table_column_value.split(
                        "|"
                    )

                    # Get value of cache column
                    cache_column_value = cache_column_value_and_timestamp[0]

                    # Get timestamp of update time of cache column
                    time_of_update_for_cache_column_value = (
                        cache_column_value_and_timestamp[1]
                    )

                    # Format date and time of update of cache columns values into date time object
                    time_of_update_for_cache_column_value = datetime.datetime.strptime(
                        time_of_update_for_cache_column_value, "%Y-%m-%d %H:%M:%S %z"
                    )

                    # Calculate the time difference between current time and update time of cache column value
                    difference_between_current_timestamp_and_timestamp_of_update_for_cache_column = (
                        current_time_in_target_time_zone
                        - time_of_update_for_cache_column_value
                    )

                    # Get time difference in term of minutes
                    difference_between_current_timestamp_and_timestamp_of_update_for_cache_column_in_minutes = (
                        difference_between_current_timestamp_and_timestamp_of_update_for_cache_column.total_seconds()
                        / 60
                    )

                    # Check if time difference is less than or equal to allowed lookback period for cache value
                    if (
                        difference_between_current_timestamp_and_timestamp_of_update_for_cache_column_in_minutes
                        <= variables.lookback_period_for_cache
                    ):
                        # Add cache column data to be displayed
                        row_of_values_to_be_added_in_cas_table_values += (
                            cache_column_value,
                        )

                    else:
                        # Add 'N/A' value to be displayed
                        row_of_values_to_be_added_in_cas_table_values.append("N/A")
                else:
                    # Add 'CAS column value to be displayed
                    row_of_values_to_be_added_in_cas_table_values.append(
                        cas_column_value
                    )

            # Append row of values for each row in CAS table
            values_to_be_displayed_in_cas_table.append(
                tuple(row_of_values_to_be_added_in_cas_table_values)
            )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception Inside replacing values in CAS table by cache table value, Exp: {e}"
            )

        return cas_table_update_values

    # Return list of tuples
    return values_to_be_displayed_in_cas_table
