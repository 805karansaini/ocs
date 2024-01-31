import asyncio

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.ibapi_ao import *
from option_combo_scanner.ibapi_ao.contracts import *
from option_combo_scanner.ibapi_ao.variables import variables

logger = CustomLogger.logger


# Gets option delta from TWS, Using reqMktData, Changed Time from 11Sec to 14Sec
# Note: On TWS the reqMktData time is 11sec, but while looking for more than 8 legs(11 legs), most of the time(always)-we were
# not able to get the deltas for last 3 legs, therefore karan changed the wait from 11secs to 14secs(and it started workig, resolving all 11 legs)
async def get_opt_delta(contract, flag_market_open, genericTickList=""):
    # Handle Case where TWS is not available
    if variables.app.nextorderId is None:
        return (None, None)

    # Get reqID
    reqId = variables.app.nextorderId
    variables.app.nextorderId += 1

    # Init response
    variables.options_delta[reqId] = None
    variables.req_error[reqId] = False
    variables.req_mkt_data_end[reqId] = False

    # Data - TODO added here
    variables.ask_price[reqId] = None
    variables.bid_price[reqId] = None

    # Set request type depending on whether the market is live or not
    if flag_market_open:
        variables.app.reqMarketDataType(1)  # real time
    else:
        variables.app.reqMarketDataType(2)  # frozen

    # Set remaining params
    genericTickList = genericTickList
    regulatory = False

    # Log
    logger.debug(f"Fetching delta for option contract = {contract} reqId = {reqId}")

    # Send request
    variables.app.reqMktData(
        reqId,
        contract,
        genericTickList,
        variables.flag_snapshot_req_mkt_data,
        regulatory,
        [],
    )

    # Wait for response from TWS
    counter = 0
    while True:
        # (Error received for the request) OR (Timeout of 14 secs) OR (Response end indicated by API) OR (delta value is available)
        if (
            (variables.req_error[reqId] == True)
            or (counter >= int(14 / variables.sleep_time_waiting_for_tws_response))
            or (variables.req_mkt_data_end[reqId])
            or (
                variables.options_delta[reqId] is not None
                and variables.ask_price[reqId] is not None
                and variables.bid_price[reqId] is not None
            )
        ):
            # Unsubscribe market data
            if not variables.flag_snapshot_req_mkt_data:
                variables.app.cancelMktData(reqId)

            # Print to console
            if variables.flag_debug_mode:
                print(
                    "Successfully fetched delta for reqId = ",
                    reqId,
                    " -> delta = ",
                    variables.options_delta[reqId],
                )

            # Return option delta
            return (
                variables.options_delta[reqId],
                variables.ask_price[reqId],
                variables.bid_price[reqId],
            )

        # Response not yet ended
        else:
            # Print to console
            if (variables.flag_debug_mode) and (counter % 20 == 0):
                print("Waiting for delta for reqId = ", reqId)

            # Wait for response
            await asyncio.sleep(variables.sleep_time_waiting_for_tws_response)
            counter += 1


async def get_underlying_implied_volatility_and_cmp(
    contract, flag_market_open, genericTickList=""
):
    # Handle Case where TWS is not available
    if variables.app.nextorderId is None:
        return (None, None)

    # Get reqID
    reqId = variables.app.nextorderId
    variables.app.nextorderId += 1

    # Init response
    variables.req_error[reqId] = False
    variables.req_mkt_data_end[reqId] = False
    variables.implied_volatility[reqId] = None

    variables.ask_price[reqId] = None
    variables.bid_price[reqId] = None

    # Set request type depending on whether the market is live or not
    if flag_market_open:
        variables.app.reqMarketDataType(1)  # real time
    else:
        variables.app.reqMarketDataType(2)  # frozen

    # Set remaining params
    genericTickList = genericTickList
    regulatory = False

    # Print to console
    if variables.flag_debug_mode:
        print("Fetching delta for option contract = ", contract, "reqId = ", reqId)

    # Send request
    variables.app.reqMktData(
        reqId,
        contract,
        genericTickList,
        variables.flag_snapshot_req_mkt_data,
        regulatory,
        [],
    )

    # Wait for response from TWS
    counter = 0
    while True:
        # (Error received for the request) OR (Timeout of 14 secs) OR (Response end indicated by API) OR (delta value is available)
        if (
            (variables.req_error[reqId] == True)
            or (counter >= int(14 / variables.sleep_time_waiting_for_tws_response))
            or (variables.req_mkt_data_end[reqId])
            or (
                variables.implied_volatility[reqId] is not None
                and variables.ask_price[reqId] is not None
                and variables.bid_price[reqId] is not None
            )
        ):
            # Unsubscribe market data
            if not variables.flag_snapshot_req_mkt_data:
                variables.app.cancelMktData(reqId)

            # Print to console
            if variables.flag_debug_mode:
                print(
                    "Successfully fetched Implied Volatility for reqId = ",
                    reqId,
                    " -> delta = ",
                    variables.implied_volatility[reqId],
                )

            # Return Implied Volatility
            return (
                variables.implied_volatility[reqId],
                variables.ask_price[reqId],
                variables.bid_price[reqId],
            )

        # Response not yet ended
        else:
            # Print to console
            if (variables.flag_debug_mode) and (counter % 20 == 0):
                print("Waiting for delta for reqId = ", reqId)

            # Wait for response
            await asyncio.sleep(variables.sleep_time_waiting_for_tws_response)
            counter += 1


# Using list comprehension to get Delta and gather the results with await
async def async_get_deltas(contracts_list, flag_market_open):
    result = await asyncio.gather(
        *[get_opt_delta(contract, flag_market_open) for contract in contracts_list]
    )
    return result
