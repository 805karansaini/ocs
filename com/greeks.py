"""
Created on 25-Mar-2023

@author: Karan
"""

from com import *
from com.variables import *
from com.contracts import *
import asyncio


# Gets option delta from TWS, Using reqMktData, Changed Time from 11Sec to 14Sec
# Note: On TWS the reqMktData time is 11sec, but while looking for more than 8 legs(11 legs), most of the time(always)-we were
# not able to get the deltas for last 3 legs, therefore karan changed the wait from 11secs to 14secs(and it started workig, resolving all 11 legs)
async def get_opt_delta(contract_opt, flag_market_open):
    # print("Contract : ", contract_opt)
    # Get reqID
    reqId = variables.nextorderId
    variables.nextorderId += 1

    # Init response
    variables.options_delta[reqId] = None

    variables.req_error[reqId] = False
    variables.req_mkt_data_end[reqId] = False

    # Set request type depending on whether the market is live or not
    if flag_market_open:
        variables.app.reqMarketDataType(1)  # real time
    else:
        variables.app.reqMarketDataType(2)  # frozen

    # Set remaining params
    genericTickList = ""
    regulatory = False

    # Print to console
    if variables.flag_debug_mode:
        print("Fetching delta for option contract = ", contract_opt, "reqId = ", reqId)

    # Send request
    variables.app.reqMktData(
        reqId,
        contract_opt,
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
            or (counter >= int(20 / variables.sleep_time_waiting_for_tws_response))
            or (variables.req_mkt_data_end[reqId])
            or (variables.options_delta[reqId] is not None)
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
            return variables.options_delta[reqId]

        # Response not yet ended
        else:
            # Print to console
            if (variables.flag_debug_mode) and (counter % 20 == 0):
                print("Waiting for delta for reqId = ", reqId)

            # Wait for response
            await asyncio.sleep(variables.sleep_time_waiting_for_tws_response)
            counter += 1


# # Making/Wrapping 'get_opt_delta' to be async
# async def get_opt_delta_async(contract_opt, flag_market_open):
#     return await asyncio.to_thread(get_opt_delta, contract_opt,flag_market_open)


# Using list comprehension to get Delta and gather the results with await
async def async_get_deltas(contracts_list, flag_market_open):
    result = await asyncio.gather(
        *[get_opt_delta(contract, flag_market_open) for contract in contracts_list]
    )
    return result


#########################################################################
#    VERSION 1
#########################################################################
