import asyncio
import time

import pandas as pd

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
    def request_historical_data_for_contract(contract, bar_size, duration_size, what_to_show, req_id=None, cas_app=True):

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
        variables.map_req_id_to_historical_data_dataframe[reqId] = pd.DataFrame(columns=variables.historical_data_columns)

        # Static for reqHistoricalData
        end_date_time = ""
        duration_string = duration_size
        bar_size_setting = bar_size
        use_rth = variables.flag_use_rth
        format_date = 1
        keep_up_to_date = False

        # Error Received
        variables.req_error[reqId] = False

        # Which TWS API app to use?
        if cas_app:

            # Send request via CAS APP
            variables.cas_app.reqHistoricalData(
                reqId,
                contract,
                end_date_time,
                duration_string,
                bar_size_setting,
                what_to_show,
                use_rth,
                format_date,
                keep_up_to_date,
                [],
            )
        else:

            # Send request Via Main App
            variables.app.reqHistoricalData(
                reqId,
                contract,
                end_date_time,
                duration_string,
                bar_size_setting,
                what_to_show,
                use_rth,
                format_date,
                keep_up_to_date,
                [],
            )

    @staticmethod
    def fetch_historical_data_for_list_of_contracts(list_of_all_option_contracts, bar_size, list_of_duration_size, what_to_show):
        
        # Historical Data Batch Size
        batch_size = StrategyVariables.batch_size_historical_data

        # Splitting the contracts into batches
        contract_batches = [list_of_all_option_contracts[i : i + batch_size] for i in range(0, len(list_of_all_option_contracts), batch_size)]
        duration_batches = [list_of_duration_size[i : i + batch_size] for i in range(0, len(list_of_duration_size), batch_size)]
    
        # List of all request ids TODO
        list_of_req_id_for_historical_data = []

        for indx, (contract_batch, duration_batch) in enumerate(zip(contract_batches, duration_batches)):
            # TODO - REMOVE
            # print(f"Fetching Historical data for batch: {indx + 1}/{len(contract_batches)}")

            for indx, (contract, duration_size) in enumerate(zip(contract_batch, duration_batch)):

                # Getting req_id
                reqId = variables.cas_app.nextorderId
                variables.cas_app.nextorderId += 1

                # Send the request
                HistoricalDataFetcher.request_historical_data_for_contract(contract, bar_size, duration_size, what_to_show, reqId)

                # Append the reqId to list
                list_of_req_id_for_historical_data.append(reqId)

                counter = 0
                while variables.cas_wait_time_for_historical_data > (counter * variables.sleep_time_between_iters):

                    # Waitting for the request to end or give error
                    if all([variables.req_mkt_data_end[req_id] or variables.req_error[req_id] for req_id in list_of_req_id_for_historical_data]):
                        break

                    # Sleep for sleep_time_waiting_for_tws_response
                    time.sleep(variables.sleep_time_between_iters)

                    # Increase Counter
                    counter += 1

        return list_of_req_id_for_historical_data
