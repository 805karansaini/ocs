"""
Created on 21-Jun-2023

@author: Karan
"""

from com import *
from com.variables import *


# Method to fetch unique ids in watchlist
def get_unique_id_in_watchlists_from_db(watchlist_name):
    query = f"SELECT `Unique IDs` FROM `{variables.sql_table_watchlist}` WHERE `Watchlist Name` = '{watchlist_name}';"

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got unique id list for the watchlist, Query successfully executed: {query}"
            )

        return str(all_rows[0][0])

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not unique id list for the watchlist, Query Failed: {query}, Exception {e}"
            )

        return "N/A"


# Method to fetch all watchlist from db table
def get_all_watchlists_from_db():
    query = f"SELECT * FROM `{variables.sql_table_watchlist}`;"

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Got all the watchlist, Query successfully executed: {query}")

        return all_rows_df
    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get all the watchlist, Query Failed: {query}, Exception {e}"
            )

        return pd.DataFrame()


# Method to insert in watchlist db table
def insert_watchlist_in_db(watchlist_name):
    query = f"INSERT INTO `{variables.sql_table_watchlist}` ( `Watchlist Name`) \
         VALUES ( '{watchlist_name}');"

    try:
        variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Inserted Name: {watchlist_name} in DB , Query successfully executed: {query}"
            )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not insert Name: {watchlist_name} in DB , Query successfully executed: {query}, Exception {e}"
            )


# Method to delete watchlist from db table
def delete_watchlist_in_db(watchlist_id):
    query = f"DELETE FROM `{variables.sql_table_watchlist}`  WHERE `Watchlist ID` = '{watchlist_id}';"

    try:
        variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Deleted Watchlist ID: {watchlist_id} in DB , Query successfully executed: {query}"
            )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not delete Watchlist ID: {watchlist_id} in DB , Query successfully executed: {query}, \nException {e}"
            )


# Method to update account ids in watchlist db table
def update_watchlist_in_db(watchlist_id, unique_ids_string):
    query = f"UPDATE `{variables.sql_table_watchlist}` SET `Unique IDs` = '{unique_ids_string}' WHERE `Watchlist ID`='{watchlist_id}';"

    try:
        variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Updated Watchlist ID: {watchlist_id}, Unique IDs: {unique_ids_string} in DB, Query successfully executed: {query}"
            )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not Update Watchlist ID: {watchlist_id}, Unique IDs: {unique_ids_string} in DB, Query Failed : {query}, Exception {e}"
            )
