import asyncio
import time

from ao_api.ibkr_ao_adapter import IBkrAlgoOneAdapter
from com.variables import variables
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)


class MarketDataFetcher:
    @staticmethod
    async def get_option_delta_and_implied_volatility(
        contract,
        flag_market_open=True,
        generic_tick_list="",
        snapshot=True,
        max_wait_time=None,
    ):
        # Handle Case where TWS is not available
        if variables.app.nextorderId is None:
            return (None, None, None, None, None, None, None, None, None, None, None)

        # Get reqID
        reqId = variables.app.nextorderId
        variables.app.nextorderId += 1

        # Init response
        variables.req_error[reqId] = False
        variables.req_mkt_data_end[reqId] = False

        variables.options_iv_ask[reqId] = None
        variables.options_iv_bid[reqId] = None
        variables.options_iv_last[reqId] = None
        variables.options_delta[reqId] = None
        variables.ask_price[reqId] = None
        variables.bid_price[reqId] = None
        variables.call_option_open_interest[reqId] = None
        variables.put_option_open_interest[reqId] = None
        variables.options_vega[reqId] = None
        variables.options_theta[reqId] = None
        variables.options_gamma[reqId] = None
        variables.und_price[reqId] = None
        variables.last_price[reqId] = None

        # Set request type depending on whether the market is live or not
        if flag_market_open:
            variables.app.reqMarketDataType(1)  # real time
        else:
            variables.app.reqMarketDataType(2)  # frozen

        # Set remaining params
        generic_tick_list = generic_tick_list
        regulatory = False
        snapshot = snapshot  # A true value will return a one=time snapshot, while a false value will provide streaming data.

        # Print to console
        if variables.flag_debug_mode:
            print(f"Fetching MKt Data contract = {contract} reqId = ", reqId)

        # Use API Bridge
        if variables.use_api_bridge:
            # Convert the ibapi contract to the api bridge contract
            contract = IBkrAlgoOneAdapter.convert_ibapi_to_ao_contract(contract)

            if snapshot or generic_tick_list:
                variables.ds_client.req_market_snapshot(
                    reqId, contract, generic_tick_list, priority=1
                )
            else:
                # if snapshot is False then subscribe to real time quotes
                variables.ds_client.subscribe_real_time_quotes(
                    reqId, contract, priority=1
                )

        else:
            # Send request
            variables.app.reqMktData(
                reqId,
                contract,
                generic_tick_list,
                snapshot,
                regulatory,
                [],
            )

        # Wait for response from TWS
        max_wait_time_for_mkt_data = variables.max_wait_time_for_mkt_data

        # If max_wait_time is not None, then set max_wait_time_for_mkt_data to max_wait_time
        if max_wait_time is not None:
            max_wait_time_for_mkt_data = max_wait_time

        # Wait for response from TWS
        counter = 0
        while True:
            # (Error received for the request) OR (Timeout of 14 secs) OR (Response end indicated by API) OR (delta value is available)
            if (
                (variables.req_error[reqId] == True)
                or (
                    counter
                    >= int(
                        max_wait_time_for_mkt_data
                        / variables.sleep_time_waiting_for_tws_response
                    )
                )
                or (variables.req_mkt_data_end[reqId])
                or (
                    variables.options_delta[reqId] is not None
                    and variables.options_iv_ask[reqId] is not None
                    and variables.options_iv_bid[reqId] is not None
                    and variables.options_iv_last[reqId] is not None
                    and variables.bid_price[reqId] is not None
                    and variables.ask_price[reqId] is not None
                    and variables.call_option_open_interest[reqId] is not None
                    and variables.put_option_open_interest[reqId] is not None
                    and variables.options_vega[reqId] is not None
                    and variables.options_theta[reqId] is not None
                    and variables.options_gamma[reqId] is not None
                    and variables.und_price[reqId] is not None
                    and variables.last_price[reqId] is not None
                )
            ):
                # Unsubscribe market data
                if variables.use_api_bridge:
                    variables.ds_client.unsubscribe_real_time_quotes(reqId, priority=1)
                else:
                    variables.app.cancelMktData(reqId)

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Inside MarketDataFetcher: Successfully fetched Option Delta & Implied Volatility for reqId = {reqId}"
                    )

                # Return Implied Volatility
                return (
                    variables.options_delta[reqId],
                    variables.options_iv_ask[reqId],
                    variables.options_iv_bid[reqId],
                    variables.options_iv_last[reqId],
                    variables.bid_price[reqId],
                    variables.ask_price[reqId],
                    variables.call_option_open_interest[reqId],
                    variables.put_option_open_interest[reqId],
                    variables.options_vega[reqId],
                    variables.options_theta[reqId],
                    variables.options_gamma[reqId],
                    variables.und_price[reqId],
                    variables.last_price[reqId],
                )

            # Response not yet ended
            else:
                # If in debug mode and the counter is divisible by 20, print a debug message
                if (variables.flag_debug_mode) and (counter % 20 == 0):
                    print("Waiting for option_delta_and_iv for reqId = ", reqId)

                # Wait for response
                await asyncio.sleep(variables.sleep_time_waiting_for_tws_response)
                counter += 1

    # Using list comprehension to get Delta and gather the results with await
    # retrieves delta and implied volatility for a list of option contracts asynchronously.

    @staticmethod
    async def get_option_delta_and_implied_volatility_for_contracts_list_async(
        contracts_list,
        flag_market_open=True,
        generic_tick_list="",
        snapshot=True,
        max_wait_time=None,
    ):
        """
        # Use Batch Size of 80
        result = await asyncio.gather(
            *[
                MarketDataFetcher.get_option_delta_and_implied_volatility(
                    contract, flag_market_open, generic_tick_list
                )
                for contract in contracts_list
            ]
        )
        return result
        """
        # Gettting batch size from variables
        batch_size = strategy_variables.batch_size

        # Splitting the contracts into batches
        contract_batches = [
            contracts_list[i : i + batch_size]
            for i in range(0, len(contracts_list), batch_size)
        ]

        result = []

        for indx, batch in enumerate(contract_batches):
            result += await asyncio.gather(
                *[
                    MarketDataFetcher.get_option_delta_and_implied_volatility(
                        contract,
                        flag_market_open,
                        generic_tick_list,
                        snapshot,
                        max_wait_time,
                    )
                    for contract in batch
                ]
            )

        return result

    # Get bid and ask for contract, snapshot = False, Uses reqMktData
    @staticmethod
    async def get_current_price_for_contract(contract, snapshot=True):
        """
        Only return the (Bid, Ask) Price for the contract
        """
        # Handle Case where TWS is not available
        if variables.app.nextorderId is None:
            return (None, None)

        # Get reqID
        reqId = variables.app.nextorderId
        variables.app.nextorderId += 1

        # Init response
        variables.req_error[reqId] = False
        variables.req_mkt_data_end[reqId] = False

        variables.ask_price[reqId] = None
        variables.bid_price[reqId] = None
        variables.last_price[reqId] = None

        # Print to console
        if variables.flag_debug_mode:
            # Getting req_id
            print(
                f"Req ID = {reqId}: Requesting Market Data for (snapshot: {snapshot}) Contract: {contract}"
            )

        # Set request type depending on whether the market is live or not
        if variables.flag_market_open:
            variables.app.reqMarketDataType(1)  # real time
        else:
            variables.app.reqMarketDataType(2)  # frozen

        generic_tick_list = ""
        snapshot = snapshot  # A true value will return a one=time snapshot, while a false value will provide streaming data.
        regulatory = False

        # Use API Bridge
        if variables.use_api_bridge:
            # Convert the ibapi contract to the api bridge contract
            contract = IBkrAlgoOneAdapter.convert_ibapi_to_ao_contract(contract)

            if snapshot or generic_tick_list:
                variables.ds_client.req_market_snapshot(
                    reqId, contract, generic_tick_list, priority=1
                )
            else:
                # if snapshot is False then subscribe to real time quotes
                variables.ds_client.subscribe_real_time_quotes(
                    reqId, contract, priority=1
                )

        else:
            # Send the request
            variables.app.reqMktData(
                reqId,
                contract,
                generic_tick_list,
                snapshot,
                regulatory,
                [],
            )

        # Wait for response from TWS
        counter = 0
        while True:
            # (Error received for the request) OR (Timeout of 14 secs) OR (Response end indicated by API) OR (bid and ask value is available)
            if (
                (variables.req_error[reqId] == True)
                or (
                    counter
                    >= int(
                        variables.max_wait_time_for_mkt_data
                        / variables.sleep_time_waiting_for_tws_response
                    )
                )
                or (variables.req_mkt_data_end[reqId])
                or (
                    variables.bid_price[reqId] is not None
                    and variables.ask_price[reqId] is not None
                    and variables.last_price[reqId] is not None
                )
            ):
                # Unsubscribe market data
                if variables.use_api_bridge:
                    variables.ds_client.unsubscribe_real_time_quotes(reqId, priority=1)
                else:
                    variables.app.cancelMktData(reqId)

                # Return Bid And Ask
                return (
                    variables.bid_price[reqId],
                    variables.ask_price[reqId],
                    variables.last_price[reqId],
                )

            # Response not yet ended
            else:
                # Print to console
                if (variables.flag_debug_mode) and (counter % 20 == 0):
                    print("Waiting for current price of contract for reqId = ", reqId)

                # Wait for response
                await asyncio.sleep(variables.sleep_time_waiting_for_tws_response)
                counter += 1

    @staticmethod
    async def get_current_price_for_list_of_contracts_async(
        contracts_list,
        snapshot=True,
    ):
        """
        Return [(Bid, Ask)..]
        """

        # Getting Bar Size
        batch_size = strategy_variables.batch_size

        # Splitting the contracts into batches
        contract_batches = [
            contracts_list[i : i + batch_size]
            for i in range(0, len(contracts_list), batch_size)
        ]

        result = []

        for indx, batch in enumerate(contract_batches):
            # print(f"Fetching data for batch: {indx + 1}")

            result += await asyncio.gather(
                *[
                    MarketDataFetcher.get_current_price_for_contract(contract, snapshot)
                    for contract in batch
                ]
            )

        return result
