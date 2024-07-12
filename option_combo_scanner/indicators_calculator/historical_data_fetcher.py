import asyncio
import time

import pandas as pd

from ao_api.enums import BarUnit
from ao_api.ibkr_ao_adapter import IBkrAlgoOneAdapter
from com.variables import variables as variables
from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.strategy.strategy_variables import StrategyVariables

logger = CustomLogger.logger


class HistoricalDataFetcher:
    def __init__(
        self,
    ):
        pass

    # Method to request historical data
    @staticmethod
    def request_historical_data_for_contract(
        contract, bar_size, duration_size, what_to_show, req_id=None, cas_app=True
    ):

        # print(f"IBKR: {contract}")
        # If req_id was not provided, getting request ID
        if req_id == None:
            # Getting req_id
            reqId = variables.nextorderId
            variables.nextorderId += 1
        else:
            reqId = req_id

        # Init
        variables.req_mkt_data_end[reqId] = False

        # Map req_id to dataframe containing historical_data
        variables.map_req_id_to_historical_data_dataframe[reqId] = pd.DataFrame(
            columns=variables.historical_data_columns
        )

        # Static for reqHistoricalData
        end_date_time = ""
        duration_string = duration_size
        bar_size = bar_size
        use_rth = variables.flag_use_rth
        format_date = 1
        keep_up_to_date = False

        # Error Received
        variables.req_error[reqId] = False

        # For IND we only have the Trades Data
        if contract.secType in ["IND"]:
            what_to_show = "TRADES"

        print(f"AO: {contract}")

        contract = IBkrAlgoOneAdapter.convert_ibapi_to_ao_contract(contract)
        duration, duration_unit = IBkrAlgoOneAdapter.duration(duration_string)
        bar_size, bar_unit = IBkrAlgoOneAdapter.bar_size(bar_size)
        flag_rth_only = IBkrAlgoOneAdapter.flag_rth_only(use_rth)
        bar_type = IBkrAlgoOneAdapter.bar_type(what_to_show)

        # print(f"AO: {contract}")

        # DS Client Requesting the Data
        variables.ds_client.get_historical_bars(
            request_id=reqId,
            contract=contract,  # Contract
            duration=duration,
            duration_unit=duration_unit,
            bar_unit=bar_unit,  # min
            bar_size=bar_size,  # 1
            flag_rth_only=flag_rth_only,
            bar_type=bar_type,  # What to Show
        )

        """
        bar_size_setting = "1 hour"
        ds_client.get_historical_bars(
            req_id,
            amzn_call_opt, # Contract
            duration=10,        # Days    
            bar_unit=bar_unit,  
            bar_size=3,         # inte
            flag_rth_only=True, 
        )
        """

        # Which TWS API app to use?
        # if cas_app:

        #     # Send request via CAS APP
        #     variables.cas_app.reqHistoricalData(
        #         reqId,
        #         contract,
        #         end_date_time,        ""
        #         duration_string,      "14 D", 1 D, 15 D
        #         bar_size_setting,      1 mins, 1 hour, 2 hours. bar size, bar unit
        #         what_to_show,
        #         use_rth,  False
        #         format_date,
        #         keep_up_to_d1ate,
        #         [],
        #     )
        # else:

        #     # Send request Via Main App
        #     variables.app.reqHistoricalData(
        #         reqId,
        #         contract,
        #         end_date_time,
        #         duration_string,
        #         bar_size_setting,
        #         what_to_show,
        #         use_rth,
        #         format_date,
        #         keep_up_to_date,
        #         [],
        #     )

    @staticmethod
    def fetch_historical_data_for_list_of_contracts(
        list_of_all_option_contracts, bar_size, list_of_duration_size, what_to_show
    ):

        # Historical Data Batch Size
        batch_size = StrategyVariables.batch_size_historical_data

        # Splitting the contracts into batches
        contract_batches = [
            list_of_all_option_contracts[i : i + batch_size]
            for i in range(0, len(list_of_all_option_contracts), batch_size)
        ]
        duration_batches = [
            list_of_duration_size[i : i + batch_size]
            for i in range(0, len(list_of_duration_size), batch_size)
        ]

        # List of all request ids
        list_of_req_id_for_historical_data = []

        for indx, (contract_batch, duration_batch) in enumerate(
            zip(contract_batches, duration_batches)
        ):
            # print(f"Fetching Historical data for batch: {indx + 1}/{len(contract_batches)}")

            for indx, (contract, duration_size) in enumerate(
                zip(contract_batch, duration_batch)
            ):

                # Getting req_id
                reqId = variables.cas_app.nextorderId
                variables.cas_app.nextorderId += 1

                # Send the request
                HistoricalDataFetcher.request_historical_data_for_contract(
                    contract, bar_size, duration_size, what_to_show, reqId
                )

                # Append the reqId to list
                list_of_req_id_for_historical_data.append(reqId)

            counter = 0
            while variables.cas_wait_time_for_historical_data > (
                counter * variables.sleep_time_between_iters
            ):

                # Waitting for the request to end or give error
                if all(
                    [
                        variables.req_mkt_data_end[req_id]
                        or variables.req_error[req_id]
                        for req_id in list_of_req_id_for_historical_data
                    ]
                ):
                    break

                # Sleep for sleep_time_waiting_for_tws_response
                time.sleep(variables.sleep_time_between_iters)

                # Increase Counter
                counter += 1

        return list_of_req_id_for_historical_data
