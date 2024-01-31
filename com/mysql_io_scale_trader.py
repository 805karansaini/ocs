from com.variables import *
from com.mysql_io import *


# Method to get most recent ladder id from DB
def get_ladder_id_db():

    # Initializing max ladder id variable
    max_ladder_id = 0

    # Get the max present ladder id from ladder table
    for sql_database_name in variables.all_sql_databases:

        # Init active_sqlalchemy_connection for active and archive DB
        active_sqlalchemy_connection = (
            variables.active_sqlalchemy_connection
            if sql_database_name == variables.active_sql_db_name
            else variables.archive_sqlalchemy_connection
        )

        try:

            # get max ladder id SQL query
            get_max_ladder_id_query = text(
                f"SELECT MAX(`Ladder ID`) FROM {variables.sql_table_ladder}"
            )

            # Executing query to get max ladder id SQL query
            result = active_sqlalchemy_connection.execute(get_max_ladder_id_query)
            time.sleep(variables.sleep_time_db)

            # Extracting results from output of SQL query
            result = int(result.fetchone()[0])
            max_ladder_id = max(max_ladder_id, result)

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Successfuly got the max present ladder ID from {sql_database_name}.{variables.sql_table_ladder}"
                )

        except:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Unable to get the max present ladder ID from {sql_database_name}.{variables.sql_table_ladder}"
                )

    return max_ladder_id


# Method to insert values of scale trade in DB ladder table
def insert_ladder_instance_values_to_ladder_table(ladder_values_dict):

    try:
        # Get unique id for which scale trade is being created
        unique_id = ladder_values_dict["Unique ID"]

        # Create query to insert ladder values in ladder_table
        query_insert_ladder_values = f"INSERT INTO {variables.sql_table_ladder} ("

        # Get column names from dictionary
        for column_name in ladder_values_dict:

            # Append column name in query
            query_insert_ladder_values += f"`{column_name}`,"

        # Removing ',' at last index and adding closing bracket for columns field, value keyword and opening bracket for start of values to insert
        query_insert_ladder_values = query_insert_ladder_values[:-1] + " ) VALUES ("

        # Get value of columns that need to be inserted
        for column_name in ladder_values_dict:

            # Append column value in query
            query_insert_ladder_values += f"'{ladder_values_dict[column_name]}',"

        # Removing ',' at last index and adding closing bracket
        query_insert_ladder_values = query_insert_ladder_values[:-1] + " );"

        # Run query to insert ladder instance values in ladder_table
        result = variables.active_sqlalchemy_connection.execute(
            query_insert_ladder_values
        )

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, Query successfully executed for inserting new ladder values ",
                query_insert_ladder_values,
            )

        # If query executed successfully then return true and 'no error' message
        return True, "No Error", "No Error"
    except Exception as e:

        # Show an error popup unable to insert a scale trader.
        (
            error_title,
            error_string,
        ) = "Error, Query failed for inserting new ladder values"

        variables.screen.display_error_popup(error_title, error_string)

        # Print to console
        if variables.flag_debug_mode:

            print(
                f"Unique ID= {unique_id}, Query failed for inserting new ladder values",
                query_insert_ladder_values,
                e,
            )

        # If query execution failed then return false and 'query failed' message
        return False, "Query failed", f"Unique ID= {unique_id}, Query failed "


# Method to get most recent sequence id from DB
def get_sequence_id_db():

    # Initializing max sequence id variable
    max_sequence_id = 0

    # Get the max present sequence id from sequence table
    for sql_database_name in variables.all_sql_databases:

        # Init active_sqlalchemy_connection for active and archive DB
        active_sqlalchemy_connection = (
            variables.active_sqlalchemy_connection
            if sql_database_name == variables.active_sql_db_name
            else variables.archive_sqlalchemy_connection
        )

        try:

            # get max sequence id SQL query
            get_max_sequence_id_query = text(
                f"SELECT MAX(`Sequence ID`) FROM {variables.sql_table_sequence}"
            )

            # Executing query to get max sequence id SQL query
            result = active_sqlalchemy_connection.execute(get_max_sequence_id_query)
            time.sleep(variables.sleep_time_db)

            # Extracting results from output of SQL query
            result = int(result.fetchone()[0])
            max_sequence_id = max(max_sequence_id, result)

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Successfully got the max present sequence ID from {sql_database_name}.{variables.sql_table_sequence}"
                )

        except:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Unable to get the max present sequence ID from {sql_database_name}.{variables.sql_table_sequence}"
                )

    return max_sequence_id


# Method to insert values of scale trade sequences in DB sequnce table
def insert_sequence_instance_values_to_sequence_table(sequence_values_dict):

    try:
        # Get ladder id for which sequences is being inserted
        ladder_id = sequence_values_dict["Ladder ID"]

        # Create query to insert seuence values in sequence_table
        query_insert_sequence_values = f"INSERT INTO {variables.sql_table_sequence} ("

        # Get column names from dictionary
        for column_name in sequence_values_dict:

            # Append column name in query
            query_insert_sequence_values += f"`{column_name}`,"

        # Removing ',' at last index and adding closing bracket for columns field, value keyword and opening bracket for start of values to insert
        query_insert_sequence_values = query_insert_sequence_values[:-1] + " ) VALUES ("

        # Get value of columns that need to be inserted
        for column_name in sequence_values_dict:

            # Append column value in query
            query_insert_sequence_values += f"'{sequence_values_dict[column_name]}',"

        # Removing ',' at last index and adding closing bracket
        query_insert_sequence_values = query_insert_sequence_values[:-1] + " );"

        # Run query to insert sequence values in sequence table
        result = variables.active_sqlalchemy_connection.execute(
            query_insert_sequence_values
        )

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Ladder ID= {ladder_id}, Query successfully executed for inserting new sequence values ",
                query_insert_sequence_values,
            )

        # If query executed successfully then return true and 'no error' message
        return True, "No Error", "No Error"
    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(
                f"Ladder ID= {ladder_id}, Query failed for inserting new sequence values",
                query_insert_sequence_values,
                e,
            )

        # If query execution failed then return false and 'query failed' message
        return False, "Query failed", f"Ladder ID= {ladder_id}, Query failed"


# Update sequence status for sequence id
def update_sequence_table_values(sequence_id, sequence_values_dict):

    query_update_sequence_vaues = f"UPDATE `{variables.sql_table_sequence}` SET"

    # Get columns and its values from dictionary
    for column_name in sequence_values_dict:

        # Add columns to update and its updated values
        query_update_sequence_vaues += (
            f" `{column_name}` = '{sequence_values_dict[column_name]}',"
        )

    query_update_sequence_vaues = (
        query_update_sequence_vaues[:-1] + f" WHERE `Sequence ID` = '{sequence_id}'"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(
            query_update_sequence_vaues
        )

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Sequence ID= {sequence_id}, updated the Sequence values, Query successfully executed: {query_update_sequence_vaues}"
            )

    except Exception as e:

        if variables.flag_debug_mode:
            print(
                f"Unable to Execute the query to UPDATE the Sequence values for Sequence ID: {sequence_id}, Query : {query_update_sequence_vaues}, Exp: {e}"
            )


# Update ladder status for ladder id -
def update_ladder_table_values(ladder_id, ladder_values_to_update_dict):

    query_update_ladder_values = f"UPDATE `{variables.sql_table_ladder}` SET"

    # Get columns and its values from dictionary
    for column_name in ladder_values_to_update_dict:

        # Add columns to update and its updated values
        query_update_ladder_values += (
            f" `{column_name}` = '{ladder_values_to_update_dict[column_name]}',"
        )

    query_update_ladder_values = (
        query_update_ladder_values[:-1] + f" WHERE `Ladder ID` = '{ladder_id}'"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(
            query_update_ladder_values
        )

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Ladder ID= {ladder_id}, updated the Ladder values, Query successfully executed: {query_update_ladder_values}"
            )

    except Exception as e:

        if variables.flag_debug_mode:
            print(
                f"Unable to Execute the query to UPDATE the Ladder values for Ladder ID: {ladder_id}, Query : {query_update_ladder_values}, Exp: {e}"
            )


# Move data of deleted ladder and sequence to archive
def move_deleted_ladder_and_sequence_to_archive(ladder_id):

    try:
        # Query to get ladder data
        query_get_ladder_data = text(
            f"SELECT * FROM `{variables.sql_table_ladder}` WHERE `Ladder ID` = '{ladder_id}'"
        )

        # Get data from ladder table for ladder id
        result = variables.active_sqlalchemy_connection.execute(query_get_ladder_data)

        # Fetching all the results. (list of tuples)
        all_rows_ladder_table = result.fetchall()

        # Making DataFrame
        all_rows_ladder_table_df = pd.DataFrame(all_rows_ladder_table)

        # Query to get sequence data
        query_get_sequence_data = text(
            f"SELECT * FROM `{variables.sql_table_sequence}` WHERE `Ladder ID` = '{ladder_id}'"
        )

        # Get data from sequence table for ladder id
        result = variables.active_sqlalchemy_connection.execute(query_get_sequence_data)

        # Fetching all the results. (list of tuples)
        all_rows_sequence_table = result.fetchall()

        # Making DataFrame
        all_rows_sequence_table_df = pd.DataFrame(all_rows_sequence_table)

        # Move data
        all_rows_ladder_table_df.to_sql(
            variables.sql_table_ladder,
            con=variables.archive_sqlalchemy_connection,
            if_exists="append",
            index=False,
        )

        # Move data
        all_rows_sequence_table_df.to_sql(
            variables.sql_table_sequence,
            con=variables.archive_sqlalchemy_connection,
            if_exists="append",
            index=False,
        )

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(f"Ladder ID = {ladder_id}, Could not move data to archive")


# Method to get order details for sequence id
def get_order_details_for_sequence_id(sequence_id):

    query = text(
        f"SELECT * FROM `{variables.sql_table_combination_status}` WHERE `Sequence ID` = '{sequence_id}'"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        order_details = result.fetchall()

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Sequence ID: {sequence_id}, Successfully executed query: {query}, to get_order_details_for_sequence_id."
            )
    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            pass
        print(
            f"Sequence ID: {sequence_id}, Inside 'get_order_details_for_sequence_id' unable to execute the query: {query}, Exception : {e}"
        )

    try:
        # Making DataFrame
        order_details_df = pd.DataFrame(order_details)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Sequence ID= {sequence_id}, Got order details: {order_details}")

        return order_details_df

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Sequence ID: {sequence_id}, Inside 'get_order_details_for_sequence_id' No orders were found. Exception : {e} "
            )

        return pd.DataFrame()


# Delete row for ladder id
def delete_row_from_ladder_or_sequence_table_db_for_ladder_id(
    ladder_id, flag_delete_sequences=False
):

    # Check flag_delete_sequences is false
    if not flag_delete_sequences:

        # Query to delete ladder from ladder table
        query = text(
            f"DELETE FROM `{variables.sql_table_ladder}` WHERE `Ladder ID` = '{ladder_id}' "
        )

    # Check flag_delete_sequences is True
    elif flag_delete_sequences:

        # Query to delete sequnce from sequence table
        query = text(
            f"DELETE FROM `{variables.sql_table_sequence}` WHERE `Ladder ID` = '{ladder_id}' "
        )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"for Ladder ID: {ladder_id}, Removed row from DB. Query successfully executed: {query}"
            )

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(
                f"Unable to Execute the query to DELETE the row from Table for Ladder ID: {ladder_id}, Query : {query}, Exp: {e}"
            )

# Method to get all sequences from db table
def get_all_sequence_from_db(status=None):

    if status is None:
        query = f"""SELECT * FROM `{variables.sql_table_sequence}`"""
    else:
        query = f"""SELECT * FROM `{variables.sql_table_sequence}` WHERE STATUS = '{status}' """

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"For getting sequence from DB table, Query successfully executed: {query}"
            )

        all_active_sequence = pd.DataFrame(result.fetchall())

        return all_active_sequence

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(
                f"Unable to Execute the query to -For getting sequence from DB table -  Query : {query}, Exp: {e}"
            )

        return pd.DataFrame()

# Method to find order originated from sequence
def get_all_order_from_db_where(sequence_id_string=None):

    if sequence_id_string is None:
        pass
    else:
        query = f"""SELECT * FROM {variables.sql_table_combination_status} WHERE `Sequence ID` IN ({sequence_id_string})"""

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"For getting order of sequence ID, Query successfully executed: {query}"
            )

        all_order_with_sequence_id = pd.DataFrame(result.fetchall())

        return all_order_with_sequence_id

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(
                f"Unable to Execute the query to -For getting order of sequence ID -  Query : {query}, Exp: {e}"
            )

        return pd.DataFrame()


# Method to get ladder status from db
def get_ladder_or_sequence_column_value_from_db(
    ladder_id=None, column_name_as_in_db=None, sequence_id=None
):

    # When ladder id is not none
    if ladder_id != None:

        query = f"""SELECT `{column_name_as_in_db}` FROM `{variables.sql_table_ladder}` WHERE `Ladder ID` = '{ladder_id}' """

    # When sequence id is not none
    elif sequence_id != None:

        query = f"""SELECT `{column_name_as_in_db}` FROM `{variables.sql_table_sequence}` WHERE `Sequence ID` = '{sequence_id}' """

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Getting ladder {column_name_as_in_db} from DB table, Query successfully executed: {query}"
            )

        column_value = str(result.fetchall()[0][0])

        return column_value

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(
                f"Unable to Execute the query to -For getting ladder {column_name_as_in_db} from DB table -  Query : {query}, Exp: {e}"
            )

        return "None"


# Method to pause all scale trade after restart
def pause_all_active_ladders_after_restart_db():

    query = text(
        f"UPDATE `{variables.sql_table_ladder}` SET `Status`='Paused' WHERE `Status` = 'Active';"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Inside MySql IO Scale Trade pause_all_active_ladders_after_restart_db Exception : {e} "
            )


# Method to cancel all pending order originatd in scale trade after restart
def cancel_all_orders_from_scale_trade_after_restart_db():

    query = text(
        f"UPDATE `{variables.sql_table_combination_status}` SET `Status`='Cancelled' WHERE `Status` = 'Pending' AND `Ladder ID` <> 'None';"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Inside MySql IO Scale Trade cancel_all_orders_from_scale_trade_after_restart_db Exception : {e} "
            )

# Method to get entry sequences from aldder
def get_sequences_for_ladder(ladder_id):

    query = f"SELECT * FROM `{variables.sql_table_sequence}` WHERE `Ladder ID` = '{ladder_id}' AND `Sequence Type`='Entry'"



    try:
        result = variables.active_sqlalchemy_connection.execute(query)



        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Getting sequences from DB table for ladder, Query successfully executed: {query}"
            )

        sequences_df = pd.DataFrame(result.fetchall())

        return sequences_df

    except Exception as e:

        # Print to console
        if True or variables.flag_debug_mode:
            print(
                f"Unable to Execute the query to Getting sequences from DB table for ladder, from DB table -  Query : {query}, Exp: {e}"
            )

        return "None"