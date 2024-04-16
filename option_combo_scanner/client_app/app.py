# import nest_asyncio
# nest_asyncio.apply()

import asyncio
import datetime
import time

import pandas as pd
import pytz

from ao_api.client import EClient
from ao_api.wrapper import EWrapper
from com.variables import variables
import warnings

# VENDOR = "-polygon"
# BASE_FOLDER_PATH = rf"tests\results"
# EXP_NO = "exp4"


class AlgoOneAPI(EClient, EWrapper):

    def __init__(self, data_server_host, data_server_port, data_server_client_id, loop):
        EClient.__init__(self, self, loop=loop)
        self.loop = loop

        (
            self.data_server_host,
            self.data_server_port,
            self.data_server_client_id,
        ) = (data_server_host, data_server_port, data_server_client_id)

        self.req_id = None
        self.map_req_id_to_error = {}
        self.map_req_id_to_historical_data = {}
        self.map_req_id_to_historical_data_ended = {}

    async def setup_api_connection(self):
        try:

            await self.connect(self.data_server_host, self.data_server_port, self.data_server_client_id)

            print("Connecting to Data Server...")

            # Check if the API is connected via order id
            while True:
                if self.is_connected():
                    print("Connected to Data Server.")

                    # Set the req_id
                    self.req_id = 1

                    # Start the receiver coroutine
                    asyncio.create_task(self.conn.receive_response())

                    break
                else:
                    print("Waiting for connection with Data Server...")
                    await asyncio.sleep(1)

        except Exception as exp:
            # TODO we should log it and not show it to the user.
            print(f"Unable to connect to data server, Exception: {exp}")

    def historical_data(self, request_id: str, historical_bars: dict):
        # print(f"Historical Data: reqId: {request_id} Bar: {historical_bars}")
        request_id = int(request_id)
        
        # # Formatting bar_date and converting to users target_timezone
        # try:
        #     # Time, and timezone string
        #     tws_date_str, tws_tz_str = bar_date.rsplit(" ", 1)
        #     # Parsing time
        #     tws_date_obj = datetime.datetime.strptime(tws_date_str, "%Y%m%d %H:%M:%S")
        #     # Parsing tws_dt with tws_tz
        #     tws_tz = pytz.timezone(tws_tz_str)
        #     tws_received_date_obj = tws_tz.localize(tws_date_obj)
        #     # convert localized datetime to target timezone
        #     bar_date = tws_received_date_obj.astimezone(variables.target_timezone_obj)

        # except Exception as e:
        #     # print(f"Exception in bar data : {bar}")
        #     # print(f"Exception : {e}")
        #     bar_date = datetime.datetime.strptime(bar_date, "%Y%m%d")

        # def convert_utc_to_timezone(utc_time, target_timezone):
        # Define timezone objects
        # utc_timezone = pytz.utc
        # target_timezone_obj = pytz.timezone(target_timezone)

        # # Parse UTC time string to datetime object
        # utc_datetime = datetime.strptime(utc_time, '%Y-%m-%d %H%M%S')

        # # Convert UTC time to target time zone
        # target_datetime = utc_timezone.localize(utc_datetime).astimezone(target_timezone_obj)

        # return target_datetime.strftime('%Y-%m-%d %H:%M:%S %Z')def convert_utc_to_timezone(utc_time, target_timezone):

        bar_date = historical_bars['datetime']
        bar_open = historical_bars['open']
        bar_high = historical_bars['high']
        bar_low = historical_bars['low']
        bar_close = historical_bars['close']
        bar_volume = historical_bars['volume']

        try:
                
            # Formatting bar_date and converting to users target_timezone
            utc_timezone = pytz.utc

            # Parse bar date string to datetime object
            utc_datetime_dt_obj = datetime.datetime.strptime(bar_date, '%Y%m%d %H%M%S')

            # Convert UTC time to target time zone
            bar_target_datetime = utc_timezone.localize(utc_datetime_dt_obj).astimezone(variables.target_timezone_obj)

            # bar_target_datetime = bar_target_datetime.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(e)

        # Add Row to dataframe (concat)
        warnings.filterwarnings("ignore", category=FutureWarning,)


        # create another row to append
        row = pd.DataFrame(
            {
                "Time": bar_target_datetime,
                "Open": bar_open,
                "Close": bar_close,
                "Volume": bar_volume,
            },
            index=[0],
        )

        # While Using Price Chart Making a dataframe
        if request_id in variables.map_req_id_to_historical_data_dataframe:

            # Add Row to dataframe (concat)
            variables.map_req_id_to_historical_data_dataframe[request_id] = pd.concat(
                [variables.map_req_id_to_historical_data_dataframe[request_id], row],
                ignore_index=True,
            )
        # self.map_req_id_to_historical_data[request_id].append(historical_bars)

    def historical_data_end(self, request_id: str):
        print(f"Historical data end, Request id: {request_id}")
        
        request_id = int(request_id)
        variables.req_mkt_data_end[request_id] = True

        # self.map_req_id_to_historical_data_ended[request_id] = True

    def error(
        self,
        request_id: str,
        error_code: int,
        error_msg: str,
        advance_order_reject_json="",
    ):
        request_id = int(request_id)
        print(f"Error: request_id={request_id}, {error_code=} msg={error_msg} {advance_order_reject_json=}")
        
        variables.req_mkt_data_end[request_id] = True

    async def _start_setup(self):
        """
        Wrapper to setup conn and keeps running the event loop
        """
        # Connect to Data Server via WS
        await self.setup_api_connection()

        while self.is_connected():
            await asyncio.sleep(5)

    def start(self):
        try:
            print(self.loop)
            asyncio.run_coroutine_threadsafe(self._start_setup(), self.loop)
            # asyncio.run(self._start_setup())
        except Exception as e:
            print("Inside Start: ", e)
        # TODO - Handle Reconnection
