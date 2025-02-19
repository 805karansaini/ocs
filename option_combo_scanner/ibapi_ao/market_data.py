import asyncio

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)

logger = CustomLogger.logger


class RequestMarketData:
    def __init__(
        self,
    ):
        pass

    @staticmethod
    async def get_market_data_for_contract_async(
        contract,
        snapshot=True,
        cancel_request=True,
        req_id=None,
        max_wait_time=None,
    ):
        """
        Fetches the market data for the contracts

        :param contract: The contract object
        :param flag_market_open: If the market is open or not
        :param snapshot: If a snapshot data is required or continuous feed
        :param req_id: The request id for the data

        :return: Bid and Ask price lists if available
        """

        # If req_id is not given getting req_id
        if req_id == None:
            # Getting req_id
            req_id = variables.app.nextorderId
            variables.app.nextorderId += 1

        # Handle Case where TWS is not available
        if variables.app.nextorderId is None:
            return (None, None)

        # Init variables
        variables.ask_price[req_id] = None
        variables.bid_price[req_id] = None
        variables.req_error[req_id] = False
        variables.req_mkt_data_end[req_id] = False

        # Set request type depending on whether the market is live or not
        if variables.flag_market_open:
            variables.app.reqMarketDataType(1)  # real time
        else:
            variables.app.reqMarketDataType(2)  # frozen

        # Creating a string for the generic tick list
        generic_tick_list = ""
        snapshot = snapshot  # A true value will return a one=time snapshot, while a false value will provide streaming data.
        regulatory = False

        # Requesting the marketdata for all generic ticks
        variables.app.reqMktData(
            req_id, contract, generic_tick_list, snapshot, regulatory, []
        )

        # When we are subscribing data just return from here, if we dont want to cancel_request return from here.
        if (snapshot == False) and (cancel_request == False):
            return

        # Init the counter and max wait time
        counter = 0
        max_wait_time_for_req = (
            max_wait_time
            if max_wait_time != None
            else variables.max_wait_time_for_req_mkt_data
        )

        # Error checking loop - breaks from loop once MktData is obtained
        # Wait for response from TWS
        while True:
            # (End indicated by API) OR (Error received for the request)
            if (
                (variables.req_mkt_data_end[req_id] == True)
                or (
                    counter
                    >= int(
                        max_wait_time_for_req
                        / variables.sleep_time_waiting_for_tws_response
                    )
                )
                or (variables.req_error[req_id] == True)
                or (
                    variables.ask_price[req_id] != None
                    and variables.bid_price[req_id] != None
                )
            ):
                # Cancel the request before returning
                if cancel_request:
                    variables.app.cancelMktData(req_id)

                # Return the price
                return (
                    variables.ask_price[req_id],
                    variables.bid_price[req_id],
                )
            else:
                await asyncio.sleep(variables.sleep_time_waiting_for_tws_response)
                counter += 1

    @staticmethod
    async def get_market_data_for_all_contracts_async(
        contracts_list,
        max_wait_time=None,
        snapshot=True,
        inorder_snapshot_list=None,
    ):
        """
        Gets the market data for a group of contracts

        :param contracts_list: The list of contracts
        :param flag_market_open: If the market is open or close {Bool}
        :return: The market data
        """

        try:
            result = []
            batch_size = strategy_variables.batch_size
            # Process the requests in batches (The User can modify the batch size from variables)
            for indx in range(0, len(contracts_list), batch_size):
                # Creating a batch for all requests and sending it to the TWS
                start, end = indx, indx + batch_size

                # Getting the results for the first batch first, then going for the next batches
                temp_res = await asyncio.gather(
                    *[
                        RequestMarketData.get_market_data_for_contract_async(
                            contract,
                        )
                        for contract in contracts_list[start:end]
                    ]
                )
                # Adding to the result
                result.extend(temp_res)
        except Exception as exp:
            # Log
            logger.error(
                f"Exception occurred in get_market_data_for_all_contracts_async: {exp}"
            )
        return result
