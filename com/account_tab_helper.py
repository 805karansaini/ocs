from com.variables import *
from com.mysql_io_accounts import *
import re
from com.utilities import *

# add acoount rows in df design to keep track of account values
def add_accounts_in_df():

    # Check if df is empty
    if variables.accounts_table_dataframe.empty:

        # Get all account ids>
        for account_id in variables.current_session_accounts:

            # Values to add in df
            account_table_row_values = (
                account_id,
                "None",
                "None",
                "None",
                "None",
                "None",
                "None",
            )

            # Creating dataframe for row data
            account_table_row_df = pd.DataFrame(
                [account_table_row_values], columns=variables.accounts_table_columns
            )

            # Merge row with combo details dataframe
            variables.accounts_table_dataframe = pd.concat(
                [variables.accounts_table_dataframe, account_table_row_df]
            )

            # Init
            variables.flag_account_liquidation_mode[account_id] = False

            # Init
            variables.map_account_id_and_con_id_to_pnl[account_id] = {}
