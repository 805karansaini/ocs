from com.variables import *


# Update columns in DB table
def update_account_group_table_db(group_id, column_to_value_dict):
    query_update_account_group_values = (
        f"UPDATE `{variables.sql_table_account_group}` SET"
    )

    # Get columns and its values from dictionary
    for column_name in column_to_value_dict:
        # Add columns to update and its updated values
        query_update_account_group_values += (
            f" `{column_name}` = '{column_to_value_dict[column_name]}',"
        )

    query_update_account_group_values = (
        query_update_account_group_values[:-1] + f" WHERE `Group ID` = '{group_id}'"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(
            query_update_account_group_values
        )

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Group ID= {group_id}, updated the Account Group values, Query successfully executed: {query_update_account_group_values}"
            )

    except Exception as e:
        if variables.flag_debug_mode:
            print(
                f"Unable to Execute the query to UPDATE the account group values for Group ID: {group_id}, Query : {query_update_account_group_values}, Exp: {e}"
            )


# Method to insert new account group
def insert_account_group_in_db(group_name):
    query = (
        f"INSERT INTO `{variables.sql_table_account_group}` ( `Group Name`, `Account IDs`) \
         VALUES ( '{group_name}', '');"
    )

    try:
        variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Inserted Name: {group_name} in DB , Query successfully executed: {query}"
            )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not insert Name: {group_name} in DB , Query successfully executed: {query}, Exception {e}"
            )


# Method to delete account group
def delete_account_group_in_db(group_id):
    query = f"DELETE FROM `{variables.sql_table_account_group}`  WHERE `Group ID` = '{group_id}';"

    try:
        variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Deleted Group ID: {group_id} in DB , Query successfully executed: {query}"
            )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not delete Group ID: {group_id} in DB , Query successfully executed: {query}, \nException {e}"
            )


# Method to get all account groups
def get_all_account_groups_from_db():
    query = f"SELECT * FROM `{variables.sql_table_account_group}`;"

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Got all the accounts, Query successfully executed: {query}")

        return all_rows_df
    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get all the accounts, Query Failed: {query}, Exception {e}"
            )

        return pd.DataFrame()


# Method to get accounts in group
def get_accounts_in_account_group_from_db(group_name):
    query = f"SELECT `Account IDs` FROM `{variables.sql_table_account_group}` WHERE `Group Name` = '{group_name}';"

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        return str(all_rows[0][0])

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got account id list for the account group, Query successfully executed: {query}"
            )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not account id list for the account group, Query Failed: {query}, Exception {e}"
            )

        return "N/A"


# Method to reset auto increment value
def reset_group_id():
    query = f"ALTER TABLE `{variables.sql_table_account_group}` AUTO_INCREMENT = 1;"

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Query successfully executed: {query}")

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Query Failed: {query}, Exception {e}")

        return "N/A"


# Method to get most recent group id from DB
"""def get_groupe_id_db():
    
    # Initializing max sequence id variable
    max_group_id = 0

    # Get the max present group id from group table
    for sql_database_name in variables.all_sql_databases:

        # Init active_sqlalchemy_connection for active and archive DB
        active_sqlalchemy_connection = (
            variables.active_sqlalchemy_connection
            if sql_database_name == variables.active_sql_db_name
            else variables.archive_sqlalchemy_connection
        )

        try:

            # get max group id SQL query
            get_max_group_id_query = text(
                f"SELECT MAX(`Group ID`) FROM {variables.sql_table_account_group}"
            )
            
            # Executing query to get max group id SQL query
            result = active_sqlalchemy_connection.execute(get_max_group_id_query)
            time.sleep(variables.sleep_time_db)

            # Extracting results from output of SQL query
            result = int(result.fetchone()[0])
            max_group_id = max(max_group_id, result)
            
            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Successfully got the max present group ID from {sql_database_name}.{variables.sql_table_account_group}"
                )

        except:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Unable to get the max present group ID from {sql_database_name}.{variables.sql_table_account_group}"
                )
    
    return max_group_id"""
