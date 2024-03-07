import asyncio
import time

import pandas as pd

from com.variables import variables as variables
from option_combo_scanner.custom_logger.logger import CustomLogger

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
