from com.variables import *

# Method to fetch all filter conditions
def get_all_filter_conditions(active=None):

    # check if status is none
    if active == None:

        query = f"SELECT * FROM `{variables.sql_table_filter_table}`;"

    else:

        query = f"SELECT * FROM `{variables.sql_table_filter_table}` WHERE `Active`='{active}';"

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the filter conditions, Query successfully executed: {query}"
            )

        return all_rows_df
    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get all the filter conditions, Query Failed: {query}, Exception {e}"
            )

        return pd.DataFrame()

    # Method to insert new account group

# Method to insert condition in db table
def insert_filter_condition_in_db(conditiona_name, condition, active):

    # replace %
    condition = condition.replace("%", "%%")

    query = f"INSERT INTO `{variables.sql_table_filter_table}` ( `Condition Name`, `Condition Expression`, `Active`) \
         VALUES ( '{conditiona_name}', '{condition}', '{active}');"

    try:
        variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Inserted Condition Name: {conditiona_name} in DB , Query successfully executed: {query}"
            )

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not insert Condition Name: {conditiona_name} in DB , Query Failed: {query}, Exception {e}"
            )


# Method to delete filter condition
def delete_filter_condition_in_db(condition_name):

    query = f"DELETE FROM `{variables.sql_table_filter_table}`  WHERE `Condition Name` = '{condition_name}';"

    try:
        variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Deleted Condition Name: {condition_name} in DB , Query successfully executed: {query}"
            )

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not deleteCondition Name: {condition_name} in DB , Query Failed: {query}, \nException {e}"
            )


# Update filter condition in DB table
def update_filter_condition_table_db(condition_name, column_to_value_dict):

    query = f"UPDATE `{variables.sql_table_filter_table}` SET"

    # Get columns and its values from dictionary
    for column_name in column_to_value_dict:
        # Add columns to update and its updated values
        query += f" `{column_name}` = '{column_to_value_dict[column_name]}',"

    query = query[:-1] + f" WHERE `Condition Name` = '{condition_name}'"

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Condition name= {condition_name}, updated the Filter Condition values, Query successfully executed: {query}"
            )

    except Exception as e:

        if variables.flag_debug_mode:
            print(
                f"Unable to Execute the query to UPDATE the filter condition values for Condition name: {condition_name}, Query : {query}, Exp: {e}"
            )
