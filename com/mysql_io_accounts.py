from com import *
from com.variables import *
from com.mysql_io_scale_trader import *


# Update columns in DB table
def update_account_condition_table_db(account_id, column_to_value_dict):
    query_update_account_condition_values = (
        f"UPDATE `{variables.sql_table_account_conditions}` SET"
    )

    # Get columns and its values from dictionary
    for column_name in column_to_value_dict:
        # Add columns to update and its updated values
        query_update_account_condition_values += (
            f" `{column_name}` = '{column_to_value_dict[column_name]}',"
        )

    query_update_account_group_values = (
        query_update_account_condition_values[:-1]
        + f" WHERE `Account ID` = '{account_id}'"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(
            query_update_account_condition_values
        )

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Account ID= {account_id}, updated the Account Condition values, Query successfully executed: {query_update_account_condition_values}"
            )

    except Exception as e:
        if variables.flag_debug_mode:
            print(
                f"Unable to Execute the query to UPDATE the account condition values for Account ID: {account_id}, Query : {query_update_account_condition_values}, Exp: {e}"
            )


# Method to insert new account group
def insert_account_condition_in_db(account_id, condition):
    # replace %
    condition = condition.replace("%", "%%")

    query = (
        f"INSERT INTO `{variables.sql_table_account_conditions}` ( `Account ID`, `Condition`) \
         VALUES ( '{account_id}', '{condition}');"
    )

    try:
        variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Inserted Account ID: {account_id} in DB , Query successfully executed: {query}"
            )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not insert Account ID: {account_id} in DB , Query Failed: {query}, Exception {e}"
            )


# Method to delete account group
def delete_account_condition_in_db(account_id, condition):
    # replace %
    condition = condition.replace("%", "%%")

    query = f"DELETE FROM `{variables.sql_table_account_conditions}`  WHERE `Account ID` = '{account_id}' AND `Condition` = '{condition}';"

    try:
        variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Deleted Account ID: {account_id} in DB , Query successfully executed: {query}"
            )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not delete Account ID: {account_id} in DB , Query Failed: {query}, \nException {e}"
            )


# Method to get all account groups
def get_account_conditions_from_db(account_id):
    query = f"SELECT * FROM `{variables.sql_table_account_conditions}` WHERE `Account ID`='{account_id}';"

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the account conditions, Query successfully executed: {query}"
            )

        return all_rows_df
    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get all the account conditions, Query Failed: {query}, Exception {e}"
            )

        return pd.DataFrame()


# Method to get all account groups
def get_all_conditions_from_db():
    query = f"SELECT * FROM `{variables.sql_table_account_conditions}`;"

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the account conditions, Query successfully executed: {query}"
            )

        return all_rows_df
    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get all the account conditions, Query Failed: {query}, Exception {e}"
            )

        return pd.DataFrame()
