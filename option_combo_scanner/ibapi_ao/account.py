import copy
import time

import pandas as pd

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.ibapi_ao.variables import Variables as variables

logger = CustomLogger.logger


class RequestAccountData:
    def __init__(self):
        pass

    # Function to fetch Account Value, and return the NLV amount using reqAccountUpdates
    @staticmethod
    def get_account_value_v2(acc_id):
        # Handle Case where TWS is not available
        if variables.app.nextorderId is None:
            return

        # Init
        variables.flag_account_update_ended[acc_id] = False

        # Log
        logger.debug(f"Fetching account summary, acc_id = {acc_id}")

        # Send request
        variables.app.reqAccountUpdates(True, acc_id)

        counter = 0
        # Wait for response from option_combo_scanner.TWS, max wait for 10 seconds
        while True:
            # Response ended
            if (variables.flag_account_update_ended[acc_id]) or (
                counter >= (10 / variables.sleep_time_waiting_for_tws_response)
            ):
                # Cancel Request
                variables.app.reqAccountUpdates(False, acc_id)

                # Return
                return

            # Response not yet ended
            else:
                # Wait for response
                time.sleep(variables.sleep_time_waiting_for_tws_response)
                counter += 1

    @staticmethod
    def get_account_value_for_all_active_trading_accounts():
        # Create an empty DataFrame to hold fetched account values
        variables.fetched_account_values_dataframe = pd.DataFrame(
            columns=variables.fetched_account_values_dataframe_columns
        )

        # Get the list of all active trading accounts
        list_of_all_active_trading_account = copy.deepcopy(
            variables.all_active_trading_accounts
        )
        logger.info(
            f"List of All Active Trading Accounts: {list_of_all_active_trading_account}"
        )

        for acc_id in list_of_all_active_trading_account:
            # Create a new DataFrame with 'AccountID'
            new_row = pd.DataFrame([[acc_id]], columns=["AccountID"])

            # Concatenate the new DataFrame with the existing DataFrame
            variables.fetched_account_values_dataframe = pd.concat(
                [variables.fetched_account_values_dataframe, new_row],
                ignore_index=True,
            )

            RequestAccountData.get_account_value_v2(acc_id)

        logger.debug(
            f"Final DataFrame with fetched account values: {variables.fetched_account_values_dataframe}"
        )

        return variables.fetched_account_values_dataframe
