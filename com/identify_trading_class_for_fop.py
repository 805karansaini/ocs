import asyncio

from com.contracts import *
from com.leg_identifier import get_list_of_strikes_and_expiries_async
from com.variables import *


# Method to get trading class for FOP
async def identify_the_trading_class_for_fop(fop_row_of_values, leg_number=None):

    # Base return value, empty list for non-fops and for exceptions
    all_trading_class = []

    # For non FOP legs
    if fop_row_of_values == None:
        return all_trading_class

    try:
        # User Input for leg
        (
            action,
            sec_type,
            symbol,
            dte,
            delta,
            right,
            quantity,
            lot_size,
            exchange,
            trading_class,
            currency,
            con_id,
            primary_exchange,
            strike,
            expiry_date,
        ) = fop_row_of_values

        if sec_type == "IND":
            # Creating the IND contract to fetch the contract deatils for conids
            fut_contract = get_contract(
                symbol,
                "IND",
                exchange,
                currency="USD",
            )

        else:
            # Creating the FUT contract to fetch the contract deatils for conids
            fut_contract = get_contract(
                symbol,
                "FUT",
                exchange,
                currency="USD",
            )

        # ReqId for COntract Details
        reqId = variables.nextorderId
        variables.nextorderId += 1

        # Getting the contract details
        contract_details = await get_contract_details_async(fut_contract, reqId)

        # Getting the copy of the expiry to conid dict for the contract
        fut_expiry_to_conid_dict = copy.deepcopy(variables.map_expiry_to_conid[reqId])

    except Exception as e:
        fut_expiry_to_conid_dict = {}

        # Print to console
        if variables.flag_debug_mode:
            print(f"Leg No: {leg_number + 1}, Unable to get the FUT")

        # Title,  String
        error_title, error_string = (
            "Error, Getting Trading Classes",
            f"Leg No: {leg_number + 1}, Could not get Trading Class for FOP",
        )

        # Display Error Mssg popup and return
        variables.screen.display_error_popup(error_title, error_string)

        return all_trading_class

    # Validation for exchange and symbol values
    if len(fut_expiry_to_conid_dict) < 1:

        # Print to console
        if variables.flag_debug_mode:
            print("")

        # Title,  String
        error_title, error_string = (
            "Error, Getting Trading Classes",
            f"Leg No: {leg_number + 1}, Could not get Trading Class for FOPs",
        )

        # Display Error Mssg popup and return
        variables.screen.display_error_popup(error_title, error_string)

        return all_trading_class

    try:
        # Sorting the dict with date
        fut_expiry_to_conid_dict = dict(sorted(fut_expiry_to_conid_dict.items()))

        for date_number, (date_, fut_con_id) in enumerate(fut_expiry_to_conid_dict.items()):

            if date_number >= 3:
                break

            reqId = variables.nextorderId
            variables.nextorderId += 1
            # TODO
            if sec_type in ["IND"]:
                # print(symbol, fut_con_id, exchange, "IND", "", reqId)
                # ReqSecDef
                await get_list_of_strikes_and_expiries_async(symbol, fut_con_id, "", "IND", "", reqId)
            else:
                # ReqSecDef
                await get_list_of_strikes_and_expiries_async(symbol, fut_con_id, exchange, "FUT", "", reqId)

            all_trading_class.extend(variables.map_reqid_to_all_trading_class[reqId])

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print("")

        # Title,  String
        error_title, error_string = (
            "Error, Getting Trading Classes",
            f"Leg No: {leg_number + 1}, Could not get Trading Class for FOPs",
        )

        # Display Error Mssg popup and return
        variables.screen.display_error_popup(error_title, error_string)

    # Converting to a set and then list
    all_trading_class = list(set(all_trading_class))

    return all_trading_class


# Method to manage for searching trading class for FOP
async def identify_the_trading_class_for_all_the_fop_leg_in_combination_async(
    leg_row_values_list,
):
    """
    leg_row = [
        "",  # action
        sec_type,
        symbol,
        "",  # dte
        "",  # delta
        "",  # right
        "",  # qty
        lot_size,
        exchange,
        trading_class,
        currency,
        conid,
        primary_exchange,
        "",  # Strike
        "",  # expiry
    ]
    """

    # Contains leg_row values for FOP and None for anything else
    filtered_leg_rows_list_containing_fop_legs = []

    for leg_number, leg_row_values in enumerate(leg_row_values_list):

        # User Input for leg
        [
            action,
            sec_type,
            symbol,
            dte,
            delta,
            right,
            quantity,
            lot_size,
            exchange,
            trading_class,
            currency,
            con_id,
            primary_exchange,
            strike,
            expiry_date,
        ] = leg_row_values

        # If sec_type is FOP, symbol and exchange must be available and append the values to "filtered_leg_rows_list_containing_fop_legs"
        if sec_type in ["FOP", "IND"]:

            # Formatting values
            symbol = symbol.strip().upper()
            exchange = exchange.strip().upper()

            # Check if symbol and exchange are present
            if symbol == "" or exchange == "":
                # Title,  String
                error_title, error_string = (
                    "Error Searching Trading Class",
                    f"Leg No: {leg_number + 1}, Symbol and Exchange is required to search trading class.",
                )

                # Display Error Mssg popup and return
                variables.screen.display_error_popup(error_title, error_string)

                return None
            else:
                filtered_leg_rows_list_containing_fop_legs.append(
                    [
                        action,
                        sec_type,
                        symbol,
                        dte,
                        delta,
                        right,
                        quantity,
                        lot_size,
                        exchange,
                        trading_class,
                        currency,
                        con_id,
                        primary_exchange,
                        strike,
                        expiry_date,
                    ]
                )
        else:
            # In case if the sec_type is not FOP
            filtered_leg_rows_list_containing_fop_legs.append(None)

    # Async Tasks "identify_the_trading_class_for_fop"
    tasks = [
        identify_the_trading_class_for_fop(leg_fop, leg_number)
        for leg_number, leg_fop in enumerate(filtered_leg_rows_list_containing_fop_legs)
    ]

    # Await for resolve_leg to be completed(To get returned value we need to await)
    trading_classes_for_fop_values = await asyncio.gather(*tasks)

    return trading_classes_for_fop_values
