import asyncio
import time

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.ibapi.contract import *
from option_combo_scanner.ibapi_ao.variables import Variables as variables

logger = CustomLogger.logger


# Generates the contract and returns it
def get_contract(
    symbol=None,
    sec_type=None,
    exchange=None,
    currency=None,
    expiry_date=None,
    strike_price=None,
    right=None,
    multiplier=None,
    con_id=None,
    primary_exchange=None,
    trading_class=None,
):
    # Creating contract
    contract = Contract()

    # Setting Values in contract
    if symbol is not None:
        contract.symbol = symbol
    if sec_type is not None:
        contract.secType = sec_type
    if exchange is not None:
        contract.exchange = exchange
    if currency is not None:
        contract.currency = currency
    if expiry_date is not None:
        contract.lastTradeDateOrContractMonth = expiry_date
    if strike_price is not None:
        contract.strike = float(strike_price)
    if right is not None:
        contract.right = right
    if multiplier is not None:
        contract.multiplier = multiplier
    if con_id is not None:
        contract.conId = con_id
    if trading_class is not None:
        contract.tradingClass = trading_class
    if primary_exchange is not None:
        contract.primaryExchange = primary_exchange

    return contract


# Function to request Contract Details from IBKR
def get_contract_details(contract, req_id=None):
    # Handle Case where TWS is not available
    if variables.app.nextorderId is None:
        return

    if req_id is None:
        # Get reqId
        reqId = variables.app.nextorderId
        variables.app.nextorderId += 1
    else:
        # Get reqId
        reqId = req_id

    # Init response
    variables.contract_details[reqId] = None
    variables.all_conid_from_con_details[reqId] = []
    variables.map_expiry_to_conid[reqId] = {}
    variables.contract_details_end[reqId] = False
    variables.req_error[reqId] = False

    # Log
    logger.debug(
        f"Fetching contract details from TWS for reqId = {reqId} contract = {contract}"
    )

    # Request contract details
    variables.app.reqContractDetails(reqId, contract)

    counter = 0
    # Wait for response from TWS
    while True:
        # (Error received for the request) OR (Timeout of 11 secs) OR (Response end indicated by API)
        if (
            (variables.req_error[reqId] == True)
            or (counter >= int(11 / variables.sleep_time_waiting_for_tws_response))
            or (variables.contract_details_end[reqId] == True)
        ):
            # Log
            logger.debug(
                f"Successfully fetched contract details from TWS for reqId = {reqId} -> contract_details = {variables.contract_details[reqId]}"
            )

            # Return contract_details
            return variables.contract_details[reqId]

        # Response not yet ended
        else:
            # Wait for response
            time.sleep(variables.sleep_time_waiting_for_tws_response)
            counter += 1


# Function to request Contract Details Async from IBKR,
# To Avoid much change to present this async function was created.
# While resolving legs. 8 or more, we were getting error, because the wait time is only 11 sec in 'get_contract_details' and that function was synchronous in nature so the task was waiting for it to be finised.
# To avoid wait time (for user) and Increase the contract_details wait time to 30sec (from 11sec) this function was created.
# Used in Resolve Leg(leg_identifier)
async def get_contract_details_async(contract, req_id=None):
    # Handle Case where TWS is not available
    if variables.app.nextorderId is None:
        logger.error("Inside get_contract_details_async, TWS is not available")
        return

    if req_id is None:
        # Get reqId
        reqId = variables.app.nextorderId
        variables.app.nextorderId += 1
    else:
        # Get reqId
        reqId = req_id

    # Init response
    variables.contract_details[reqId] = None
    variables.all_conid_from_con_details[reqId] = []
    variables.map_expiry_to_conid[reqId] = {}
    variables.contract_details_end[reqId] = False
    variables.req_error[reqId] = False

    # Log
    logger.debug(
        f"Fetching contract details async from TWS for reqId = {reqId} contract = {contract}"
    )

    # Request contract details
    variables.app.reqContractDetails(reqId, contract)

    # Print to console
    if variables.flag_debug_mode:
        print(f"Inside Async Contract Details: {reqId=} {contract=}")

    counter = 0
    # Wait for response from TWS
    while True:
        # (Error received for the request) OR (Timeout of 30 secs) OR (Response end indicated by API)
        if (
            (variables.req_error[reqId] == True)
            or (counter >= int(30 / variables.sleep_time_waiting_for_tws_response))
            or (variables.contract_details_end[reqId] == True)
        ):
            # Log
            logger.debug(
                f"Successfully fetched contract details from TWS for reqId = {reqId} -> contract_details = {variables.contract_details[reqId]}"
            )

            # Return contract_details
            return variables.contract_details[reqId]

        # Response not yet ended
        else:
            # Wait for response
            await asyncio.sleep(variables.sleep_time_waiting_for_tws_response)
            counter += 1


async def get_contract_details_for_contracts_list_async(
    contracts_list,
):
    """
    Returns the details of a group of contract objects

    :param contracts_list: A list of all contracts

    :return: The details of the contract as a list
    """
    # contract_details_list = await asyncio.gather(*[get_contract_details_async(contract,) for contract in contracts_list if contract is not None else None])

    # result = [contract_details.contract if contract_details is not None else None for contract_details in
    #              contract_details_list]

    contract_details_list = await asyncio.gather(
        *[get_contract_details_async(contract) for contract in contracts_list]
    )

    result = [
        contract_details.contract if contract_details is not None else None
        for contract_details in contract_details_list
    ]

    # Returning the result
    return result


# Create Combination contract
def create_combo_contract(
    symbol, legs_exchange_list, combo_exchange, currency, conid_list, qty_list
):
    # Add underlying details
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "BAG"
    contract.currency = currency
    contract.exchange = combo_exchange

    # Add legs
    contract.comboLegs = []
    combo_leg_dictionary = {}

    # For each leg
    for number, (conid_num, leg_exchange, qty_num) in enumerate(
        zip(conid_list, legs_exchange_list, qty_list)
    ):
        combo_leg_dictionary[f"leg{number}"] = ComboLeg()
        combo_leg_dictionary[f"leg{number}"].conId = int(conid_num)
        combo_leg_dictionary[f"leg{number}"].ratio = abs(int(qty_num))
        combo_leg_dictionary[f"leg{number}"].action = (
            "SELL" if int(qty_num) < 0 else "BUY"
        )
        combo_leg_dictionary[f"leg{number}"].exchange = leg_exchange

        # Add leg
        contract.comboLegs.append(combo_leg_dictionary[f"leg{number}"])

    # Return the combo contract
    return contract
