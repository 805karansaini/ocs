"""
Created on 14-Mar-2023

@author: Karan
"""


from com import *
from com.variables import *

# Function to fetch Account Value, and return the NLV amount using reqAccountUpdates
def get_account_value_v2():

    # Get reqID
    reqId = variables.nextorderId
    variables.nextorderId += 1

    # Response is already initialised to None in constructor for account value

    # Print to console
    if variables.flag_debug_mode:
        print("Fetching account summary, reqId = ", reqId)

    # Send request
    variables.app.reqAccountUpdates(True, variables.ibkr_account_number)

    # Wait for response from TWS
    while True:
        # Response ended
        if variables.bool_account_summary_end:

            # Account value found
            if variables.bool_account_value_available:

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Successfully fetched account value for reqId = {reqId}  -> account_value = {variables.account_value} "
                    )

                # Return account value
                return float(variables.account_value)

            # Account value not found
            else:

                # Print to console
                if variables.flag_debug_mode:
                    print("Account value not found for reqId = ", reqId)

                # Return None
                return None

        # Response not yet ended
        else:

            # Print to console
            if variables.flag_debug_mode:
                print("Waiting for account value for reqId = ", reqId)

            # Wait for response
            time.sleep(variables.sleep_time_waiting_for_tws_response)


# Function to fetch Account Value, and return the NLV amount using reqAccountSummary
def get_account_value():

    # Get reqID
    reqId = variables.nextorderId
    variables.nextorderId += 1

    # Response is already initialised to None in constructor

    # Print to console
    if variables.flag_debug_mode:
        print("Fetching account summary, reqId = ", reqId)

    # Send request
    variables.app.reqAccountSummary(reqId, "All", "$LEDGER:ALL")

    # Wait for response from TWS
    while True:

        # Response ended
        if variables.bool_account_summary_end:

            # Account value found
            if variables.bool_account_value_available:

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        "Successfully fetched account value for reqId = ",
                        reqId,
                        " -> account_value = ",
                        variables.account_value,
                    )

                # Return account value
                return variables.account_value

            # Account value not found
            else:

                # Print to console
                if variables.flag_debug_mode:
                    print("Account value not found for reqId = ", reqId)

                # Return None
                return None

        # Response not yet ended
        else:

            # Print to console
            if variables.flag_debug_mode:
                print("Waiting for account value for reqId = ", reqId)

            # Wait for response
            time.sleep(variables.sleep_time_waiting_for_tws_response)
