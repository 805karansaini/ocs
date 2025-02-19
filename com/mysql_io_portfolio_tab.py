from com.variables import *


# Method to get filled order of combo
def get_orders_for_combo(unique_id, account_id):
    # check if status is none
    query = f"SELECT * FROM `{variables.sql_table_combination_status}` WHERE `Unique ID`='{unique_id}' AND `Account ID`='{account_id}' AND `Status`='Filled';"

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


# Method to fetch all filled order of leg
def get_orders_for_legs(con_id, account_id):
    # check if status is none
    query = f"SELECT * FROM `{variables.sql_table_order_status}` WHERE SUBSTRING_INDEX(`Ticker`, ',', -1) = '{con_id}' AND `Account ID`='{account_id}' AND `Status`='Filled';"

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
        if True or variables.flag_debug_mode:
            print(
                f"Could not get all the filter conditions, Query Failed: {query}, Exception {e}"
            )

        return pd.DataFrame()
