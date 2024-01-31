from com.variables import *
from sqlalchemy.orm import sessionmaker
from com.mysql_io_account_group import get_all_account_groups_from_db
from com.mysql_io_account_group import get_accounts_in_account_group_from_db
from com.mysql_io import (
    do_cas_condition_exists_for_unique_id_in_db,
    do_cas_condition_series_exists_for_unique_id_in_db,
)

# Method to get most recent series id from DB
def get_series_id_db():

    # Initializing max ladder id variable
    max_series_id = 0

    try:

        # get max ladder id SQL query
        query = text(
            f"SELECT MAX(`Series ID`) FROM {variables.sql_table_conditional_series}"
        )

        # Executing query to get max ladder id SQL query
        result = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        # Extracting results from output of SQL query
        result = result.fetchone()[0]

        if result != None:

            result = int(result)
        else:

            result = 0

        max_series_id = max(max_series_id, result)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Successfuly got the max present series ID from {variables.sql_table_conditional_series}"
            )

    except Exception as e:
        # print(e)
        max_series_id = None

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unable to get the max present series ID from {variables.sql_table_conditional_series}"
            )

    return max_series_id


# Method to get most recent sequence id from DB
def get_sequence_id_db():

    # Initializing max ladder id variable
    max_sequence_id = 0

    try:

        # get max ladder id SQL query
        query = text(
            f"SELECT MAX(`Sequence ID`) FROM {variables.sql_table_conditional_series_sequence}"
        )

        # Executing query to get max ladder id SQL query
        result = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        # Extracting results from output of SQL query
        result = result.fetchone()[0]

        if result != None:

            result = int(result)
        else:

            result = 0

        max_sequence_id = max(max_sequence_id, result)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Successfuly got the max present sequence ID from {variables.sql_table_conditional_series_sequence}"
            )

    except Exception as e:

        max_sequence_id = None

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unable to get the max present sequence ID from {variables.sql_table_conditional_series_sequence}"
            )
    # print(f"{max_sequence_id=}")
    return max_sequence_id

# Method to execute insert queries for conditional series
def execute_all_insert_queries(
    series_query, position_query_list, cas_legs_query_list, sequence_query_list
):
    # Create a session factory
    Session = sessionmaker(bind=variables.active_sqlalchemy_connection)

    # Create a session
    session = Session()

    try:
        # Start a transaction
        with session.begin() as transaction:

            result = session.execute(series_query)

            for query_list in position_query_list:

                for query in query_list:

                    session.execute(query)

            for query_list in cas_legs_query_list:

                for query in query_list:
                    session.execute(query)

            for query in sequence_query_list:
                session.execute(query)

    except Exception as e:
        # Roll back the transaction if an exception occurs
        session.rollback()

        if variables.flag_debug_mode:

            print(f"Transaction failed: {e}")

    finally:
        # Close the session
        session.close()


# Method to insert values ofconditional series in db tbale
def insert_conditional_series_instance_values_to_conditional_series_table(
    values_dict, return_only=False
):
    try:

        # Get unique id for which conditional series is being created
        unique_id = values_dict["Unique ID"]

        # Create query to insert conditional series values in conditional series tble
        query = f"INSERT INTO {variables.sql_table_conditional_series} ("

        # Get column names from dictionary
        for column_name in values_dict:
            # Append column name in query
            query += f"`{column_name}`,"

        # Removing ',' at last index and adding closing bracket for columns field, value keyword and opening bracket for start of values to insert
        query = query[:-1] + " ) VALUES ("

        # Get value of columns that need to be inserted
        for column_name in values_dict:
            # Append column value in query
            query += f"'{values_dict[column_name]}',"

        # Removing ',' at last index and adding closing bracket
        query = query[:-1] + " );"

        # print(query)

        if return_only:
            return query

        # Run query to insert ladder instance values in ladder_table
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:

            print(
                f"Unique ID= {unique_id}, Query successfully executed for inserting new series values ",
                query,
            )

        # If query executed successfully then return true and 'no error' message
        return True, "No Error", "No Error"
    except Exception as e:

        # Show an error popup unable to insert a scale trader.
        error_title = (
            error_string
        ) = "Error, Query failed for inserting new conditional series values"

        variables.screen.display_error_popup(error_title, error_string)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, Query failed for inserting new conditional series values",
                query,
                e,
            )

        # If query execution failed then return false and 'query failed' message
        return False, "Query failed", f"Unique ID= {unique_id}, Query failed "


# Method to insert values ofconditional series sequence in db tbale
def insert_conditional_series_sequence_instance_values_to_conditional_series_sequence_table(
    values_dict, return_only=False
):
    try:
        # Get unique id for which conditional series is being created
        unique_id = values_dict["Unique ID"]

        # Create query to insert conditional series values in conditional series tble
        query = f"INSERT INTO {variables.sql_table_conditional_series_sequence} ("

        # Get column names from dictionary
        for column_name in values_dict:
            # Append column name in query
            query += f"`{column_name}`,"

        # Removing ',' at last index and adding closing bracket for columns field, value keyword and opening bracket for start of values to insert
        query = query[:-1] + " ) VALUES ("

        # Get value of columns that need to be inserted
        for column_name in values_dict:
            # Append column value in query
            query += f"'{values_dict[column_name]}',"

        # Removing ',' at last index and adding closing bracket
        query = query[:-1] + " );"

        if return_only:
            return query

        # Run query to insert ladder instance values in ladder_table
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, Query successfully executed for inserting new series sequence values ",
                query,
            )

        # If query executed successfully then return true and 'no error' message
        return True, "No Error", "No Error"
    except Exception as e:

        # Show an error popup unable to insert a scale trader.
        error_title = (
            error_string
        ) = "Error, Query failed for inserting new conditional series sequence values"

        variables.screen.display_error_popup(error_title, error_string)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, Query failed for inserting new conditional series sequence values",
                query,
                e,
            )

        # If query execution failed then return false and 'query failed' message
        return False, "Query failed", f"Unique ID= {unique_id}, Query failed "


# insert cas legs into db table
def insert_cas_legs_for_series_db(
    combination_obj, sequence_id, series_id, unique_id, return_only=False
):
    # Init
    # unique_id = combination_obj.unique_id
    buy_legs = combination_obj.buy_legs
    sell_legs = combination_obj.sell_legs
    current_time = datetime.datetime.now(variables.target_timezone_obj)

    sql_database_name = variables.active_sql_db_name
    active_sqlalchemy_connection = variables.active_sqlalchemy_connection

    insert_in_table = variables.sql_table_series_cas_legs

    query_list = []

    # Loop over leg object and insert it into the database
    for leg_obj in buy_legs + sell_legs:

        action = leg_obj.action
        symbol = leg_obj.symbol
        sec_type = leg_obj.sec_type
        exchange = leg_obj.exchange
        currency = leg_obj.currency
        quantity = leg_obj.quantity
        expiry_date = leg_obj.expiry_date
        strike_price = leg_obj.strike_price
        right = leg_obj.right
        multiplier = leg_obj.multiplier
        con_id = leg_obj.con_id
        primary_exchange = leg_obj.primary_exchange
        trading_class = leg_obj.trading_class
        dte = leg_obj.dte
        delta = leg_obj.delta

        insr_query = text(
            f"INSERT INTO `{sql_database_name}`.`{insert_in_table}` \
                        ( `Sequence ID`, `Series ID`, `Unique ID`,`Action`,`Symbol`, `SecType`,`Exchange`, `Currency`, `#Lots`,`Strike`, `Expiry`,`Lot Size`,`Right`, `Trading Class`,`ConId`, `Primary Exchange`, `Time`, `DTE`, `Delta`) \
                        VALUES ('{str(sequence_id)}','{str(series_id)}', '{unique_id}','{action}','{str(symbol)}','{str(sec_type)}','{str(exchange)}','{str(currency)}','{str(quantity)}','{str(strike_price)}',\
                        '{str(expiry_date)}','{str(multiplier)}', '{str(right)}', '{str(trading_class)}', '{str(con_id)}','{str(primary_exchange)}', '{str(current_time)}', '{str(dte)}', '{str(delta)}' )"
        )

        if return_only:
            query_list.append(insr_query)

            continue

        try:
            result = active_sqlalchemy_connection.execute(insr_query)
            time.sleep(variables.sleep_time_db)

        except Exception as e:

            if variables.flag_debug_mode:
                print(
                    f"Unable to insert the identified cas legs for series in to database, Unique ID: {unique_id}"
                )

    return query_list


# insert positions for sequences
def insert_positions_for_series(
    reference_positions,
    target_positions,
    sequence_id,
    series_id,
    unique_id,
    return_only=False,
):

    # print([reference_positions, target_positions])

    query_list = []

    for account in target_positions:

        ref_position = reference_positions[account]

        target_pos = target_positions[account]

        sql_database_name = variables.active_sql_db_name
        active_sqlalchemy_connection = variables.active_sqlalchemy_connection

        insert_in_table = variables.sql_table_series_positions

        insr_query = text(
            f"INSERT INTO `{sql_database_name}`.`{insert_in_table}` \
                                ( `Sequence ID`, `Series ID`, `Unique ID`, `Account ID`,`Reference Position`, `Target Position`) \
                                VALUES ('{str(sequence_id)}', '{str(series_id)}', '{unique_id}','{account}','{str(ref_position)}','{str(target_pos)}')"
        )

        if return_only:
            query_list.append(insr_query)

            continue

        try:
            result = active_sqlalchemy_connection.execute(insr_query)
            time.sleep(variables.sleep_time_db)

        except Exception as e:

            if variables.flag_debug_mode:
                print(
                    f"Unable to insert the positions for series in to database, Sequence ID: {sequence_id}"
                )

    return query_list

# Method to update data in series db table to relaunch
def relaunch_series_db(old_unique_id, new_unique_id, series_id):

    try:

        # update conditional series table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series}` SET `Unique ID` = '{new_unique_id}' WHERE `Unique ID` = '{old_unique_id}' AND `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series}` SET `Sequences Completed` = '0' WHERE `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series}` SET `Is Started Once` = 'No' WHERE `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series}` SET `Status` = 'Inactive' WHERE `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series}` SET `Evaluation Unique ID` = '{new_unique_id}' WHERE `Evaluation Unique ID` = '{old_unique_id}' AND `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series sequence table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series_sequence}` SET `Unique ID` = '{new_unique_id}' WHERE `Unique ID` = '{old_unique_id}' AND `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series sequence table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series_sequence}` SET `Evaluation Unique ID` = '{new_unique_id}' WHERE `Evaluation Unique ID` = '{old_unique_id}' AND `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series sequence table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series_sequence}` SET `Trading Unique ID` = '{new_unique_id}' WHERE `Trading Unique ID` = '{old_unique_id}' AND `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series sequence table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series_sequence}` SET `Status` = 'Active' WHERE `Series ID`='{series_id}' LIMIT 1"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series sequence table
        query = text(
            f"UPDATE `{variables.sql}` SET `Status` = 'Queued' WHERE `Series ID`='{series_id}' AND `Status`='Completed'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series positions table
        query = text(
            f"UPDATE `{variables.sql_table_series_positions}` SET `Unique ID` = '{new_unique_id}' WHERE `Unique ID` = '{old_unique_id}' AND `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # update conditional series cas legs table
        query = text(
            f"UPDATE `{variables.sql_table_series_cas_legs}` SET `Unique ID` = '{new_unique_id}' WHERE `Unique ID` = '{old_unique_id}' AND `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

    except Exception as e:

        if variables.flag_debug_mode:

            print(f"Exception inside 'relaunch_series_db', Exp: {e}")

# Method to get conditional seres table in dataframe
def get_conditional_series_df(flag_inactive=False):

    if flag_inactive:
        # Query to get all rows from the DB
        query_get_all_rows = text(
            f"SELECT * FROM `{variables.sql_table_conditional_series}` WHERE `Status`='Inactive' AND `Is Started Once`='No'"
        )

    else:
        # Query to get all rows from the DB
        query_get_all_rows = text(
            f"SELECT * FROM `{variables.sql_table_conditional_series}`"
        )

    try:
        result = variables.active_sqlalchemy_connection.execute(query_get_all_rows)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the conditional series, Query successfully executed: {query_get_all_rows}"
            )

        return all_rows_df
    except Exception as e:
        # print(e)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get conditional series, Query Failed: {query_get_all_rows}"
            )

        return pd.DataFrame()

# Method to fetch all sequences of series
def get_all_sequences_of_series(series_id, flag_active=False):

    # Query to get all rows from the DB
    query_get_all_rows = text(
        f"SELECT * FROM `{variables.sql_table_conditional_series_sequence}` WHERE `Series ID`={series_id}"
    )

    # check flag value
    if flag_active:
        # Query to get all rows from the DB
        query_get_all_rows = text(
            f"SELECT * FROM `{variables.sql_table_conditional_series_sequence}` WHERE `Series ID`={series_id} AND `Status`='Active'"
        )

    try:
        result = variables.active_sqlalchemy_connection.execute(query_get_all_rows)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the conditional series sequence, Query successfully executed: {query_get_all_rows}"
            )

        return all_rows_df
    except Exception as e:
        # print(e)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get conditional series sequence, Query Failed: {query_get_all_rows}"
            )

        return pd.DataFrame()

# Method to fetch details of next sequence in series
def get_next_sequences_of_series(series_id):
    # Query to get all rows from the DB
    query_get_all_rows = text(
        f"SELECT * FROM `{variables.sql_table_conditional_series_sequence}` WHERE `Series ID`={series_id} AND `Status`='Queued' LIMIT 1"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query_get_all_rows)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the conditional series sequence, Query successfully executed: {query_get_all_rows}"
            )

        return all_rows_df
    except Exception as e:
        # print(e)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get conditional series sequence, Query Failed: {query_get_all_rows}"
            )

        return pd.DataFrame()

# Method to get cas legs for series
def get_series_cas_legs_df(sequence_id):
    # Query to get all rows from the DB
    query_get_all_rows = text(
        f"SELECT * FROM `{variables.sql_table_series_cas_legs}` WHERE `Sequence ID`= {sequence_id}"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query_get_all_rows)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the conditional series, Query successfully executed: {query_get_all_rows}"
            )

        return all_rows_df
    except Exception as e:
        # print(e)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get conditional series, Query Failed: {query_get_all_rows}"
            )

        return pd.DataFrame()

# Method to fetch positions from series db table
def get_positions_from_series_positions_table(sequence_id):
    # Query to get all rows from the DB
    query_get_all_rows = text(
        f"SELECT * FROM `{variables.sql_table_series_positions}` WHERE `Sequence ID`= {sequence_id}"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query_get_all_rows)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the conditional series positions, Query successfully executed: {query_get_all_rows}"
            )

        return all_rows_df
    except Exception as e:
        # print(e)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get conditional series positions, Query Failed: {query_get_all_rows}"
            )

        return pd.DataFrame()

# Method to fetch position for series
def get_positions_from_series_positions_table_for_series(series_id):
    # Query to get all rows from the DB
    query_get_all_rows = text(
        f"SELECT * FROM `{variables.sql_table_series_positions}` WHERE `Series ID`= {series_id}"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query_get_all_rows)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the conditional series positions, Query successfully executed: {query_get_all_rows}"
            )

        return all_rows_df
    except Exception as e:
        # print(e)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get conditional series positions, Query Failed: {query_get_all_rows}"
            )

        return pd.DataFrame()


# Update series status for series id -
def update_conditional_series_table_values(series_id, values_to_update_dict):
    query = f"UPDATE `{variables.sql_table_conditional_series}` SET"

    # Get columns and its values from dictionary
    for column_name in values_to_update_dict:
        # Add columns to update and its updated values
        query += f" `{column_name}` = '{values_to_update_dict[column_name]}',"

    query = (
        query[:-1] + f" WHERE `Series ID` = '{series_id}' AND `Status`<>'Terminated'"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Series ID= {series_id}, updated the series values, Query successfully executed: {query}"
            )

    except Exception as e:

        if variables.flag_debug_mode:
            print(
                f"Unable to Execute the query to UPDATE the series values for Series ID: {series_id}, Query : {query}, Exp: {e}"
            )


# Update series status for series id -
def update_conditional_series_sequence_table_values(
    sequence_id, values_to_update_dict, flag_active=False
):
    query = f"UPDATE `{variables.sql_table_conditional_series_sequence}` SET"

    # Get columns and its values from dictionary
    for column_name in values_to_update_dict:
        # Add columns to update and its updated values
        query += f" `{column_name}` = '{values_to_update_dict[column_name]}',"

    # check flag
    if flag_active:
        query = (
            query[:-1] + f" WHERE `Sequence ID` = '{sequence_id}' AND `Status`='Active'"
        )

    else:
        query = query[:-1] + f" WHERE `Sequence ID` = '{sequence_id}'"

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Series ID= {sequence_id}, updated the series sequence values, Query successfully executed: {query}"
            )

    except Exception as e:

        if variables.flag_debug_mode:
            print(
                f"Unable to Execute the query to UPDATE the series sequence values for Series ID: {sequence_id}, Query : {query}, Exp: {e}"
            )

# Method to get db table in dataframe
def get_table_db(table_name):
    # Query to get all rows from the DB
    query_get_all_rows = text(f"SELECT * FROM `{table_name}`")

    try:
        result = variables.active_sqlalchemy_connection.execute(query_get_all_rows)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the rows, Query successfully executed: {query_get_all_rows}"
            )

        return all_rows_df
    except Exception as e:
        # print(e)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Could not get rows, Query Failed: {query_get_all_rows}")

        return pd.DataFrame()

# Method to delete series from db tables
def delete_series_db(series_id):

    try:

        # delete from conditional series table
        query = text(
            f"DELETE FROM `{variables.sql_table_conditional_series}` WHERE `Series ID` = '{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # delete from conditional series sequence table
        query = text(
            f"DELETE FROM `{variables.sql_table_conditional_series_sequence}` WHERE `Series ID` = '{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # delete from conditional series cas legs table
        query = text(
            f"DELETE FROM `{variables.sql_table_series_cas_legs}` WHERE `Series ID` = '{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # delete from conditional series positions table
        query = text(
            f"DELETE FROM `{variables.sql_table_series_positions}` WHERE `Series ID` = '{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)
    except Exception as e:

        if variables.flag_debug_mode:

            print(f"Query failed inside 'series_id', Exp: {e} ")

# Method to update unique ids in db table for series
def update_unique_id_series_db(
    new_unique_id,
    old_unique_id,
    new_unique_id_for_old_combo,
    flag_series=False,
    series_id=None,
):
    try:

        if not flag_series:

            new_unique_id = new_unique_id_for_old_combo

        # delete from conditional series table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series}` SET `Unique ID` = '{new_unique_id}' WHERE `Unique ID` = '{old_unique_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # delete from conditional series table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series}` SET `Evaluation Unique ID` = '{new_unique_id}' WHERE `Evaluation Unique ID` = '{old_unique_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # delete from conditional series table
        """query = text(
            f"UPDATE `{variables.sql_table_conditional_series_sequence}` SET `Trading Unique ID` = '{new_unique_id}' WHERE `Trading Unique ID` = '{old_unique_id}' AND `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)"""

        # delete from conditional series table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series_sequence}` SET `Trading Unique ID` = '{new_unique_id}' WHERE `Trading Unique ID` = '{old_unique_id}'"
        )

        # delete from conditional series table
        """query = text(
            f"UPDATE `{variables.sql_table_conditional_series_sequence}` SET `Evaluation Unique ID` = '{new_unique_id}' WHERE `Evaluation Unique ID` = '{old_unique_id}'  AND `Series ID`='{series_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)"""

        result = variables.active_sqlalchemy_connection.execute(query)

        # delete from conditional series table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series_sequence}` SET `Evaluation Unique ID` = '{new_unique_id}' WHERE `Evaluation Unique ID` = '{old_unique_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # delete from conditional series sequence table
        query = text(
            f"UPDATE `{variables.sql_table_conditional_series_sequence}` SET `Unique ID` = '{new_unique_id}' WHERE `Unique ID` = '{old_unique_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # delete from conditional series cas legs table
        query = text(
            f"UPDATE `{variables.sql_table_series_cas_legs}` SET `Unique ID` = '{new_unique_id}' WHERE `Unique ID` = '{old_unique_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)

        # delete from conditional series positions table
        query = text(
            f"UPDATE `{variables.sql_table_series_positions}` SET `Unique ID` = '{new_unique_id}' WHERE `Unique ID` = '{old_unique_id}'"
        )

        result = variables.active_sqlalchemy_connection.execute(query)
    except Exception as e:

        if variables.flag_debug_mode:
            print(f"Query failed inside 'series_id', Exp: {e} ")

# Method to fetch series id for unique id
def get_series_id_for_deleted_unique_id(unique_id):
    # Query to get all rows from the DB
    query_get_all_rows = text(
        f"SELECT * FROM `{variables.sql_table_conditional_series_sequence}` WHERE (`Trading Unique ID` = '{unique_id}' OR `Evaluation Unique ID`='{unique_id}') AND `Status`<>'Completed' "
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query_get_all_rows)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        if all_rows_df.empty:

            return []

        series_id_list = all_rows_df["Series ID"].to_list()

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the rows, Query successfully executed: {query_get_all_rows}"
            )

        return series_id_list
    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(f"Could not get rows, Query Failed: {query_get_all_rows}")

        return []

# Method to make series fail for deleted unique id
def series_fail_for_deleted_unique_id(unique_id):

    try:

        series_id_list = get_series_id_for_deleted_unique_id(unique_id)

        series_id_list = list(set(series_id_list))

        if series_id_list == []:

            return

        # Convert the list elements to strings and join them with commas
        list_as_string = ", ".join(map(str, series_id_list))

        # Add parentheses around the resulting string
        result_string = f"({list_as_string})"

        # Construct the SQL query to update rows
        update_query = f"UPDATE `{variables.sql_table_conditional_series}` SET `Status` = 'Failed' WHERE `Status` IN ('Active', 'Inactive') AND `Series ID` IN {result_string}"
        # print(update_query)
        result = variables.active_sqlalchemy_connection.execute(update_query)

    except Exception as e:

        if variables.flag_debug_mode:
            print(f"Query failed inside 'series_id', Exp: {e} ")


# Method to get series value from db
def get_series_column_value_from_db(
    series_id=None, column_name_as_in_db=None, sequence_id=None
):
    # When series id is not none
    if series_id != None:

        query = f"""SELECT `{column_name_as_in_db}` FROM `{variables.sql_table_conditional_series}` WHERE `Series ID` = '{series_id}' """

    # When sequence id is not none
    elif sequence_id != None:

        query = f"""SELECT `{column_name_as_in_db}` FROM `{variables.sql_table_conditional_series_sequence}` WHERE `Sequence ID` = '{sequence_id}' """

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Getting series {column_name_as_in_db} from DB table, Query successfully executed: {query}"
            )



        column_value = str(result.fetchall()[0][0])



        return column_value

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unable to Execute the query to -For getting series {column_name_as_in_db} from DB table -  Query : {query}, Exp: {e}"
            )

        return "None"
