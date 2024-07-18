# import nest_asyncio
# nest_asyncio.apply()

import asyncio
import datetime
import time
import warnings

import pandas as pd
import pytz

from ao_api.client import EClient as AlgoEclient
from ao_api.contract import AOContractDetails
from ao_api.wrapper import EWrapper as AlgoEWrapper
from com.variables import variables

# VENDOR = "-polygon"
# BASE_FOLDER_PATH = rf"tests\results"
# EXP_NO = "exp4"


class AlgoOneAPI(AlgoEclient, AlgoEWrapper):

    def __init__(
        self,
        data_server_host,
        data_server_port,
        data_server_client_id,
        loop,
        access_token,
    ):
        AlgoEclient.__init__(self, self, loop=loop)
        self.loop = loop

        (
            self.data_server_host,
            self.data_server_port,
            self.data_server_client_id,
        ) = (data_server_host, data_server_port, data_server_client_id)

        self.access_token = access_token
        self.nextorderId = None

        self.req_id = None
        self.map_req_id_to_error = {}
        self.map_req_id_to_historical_data = {}
        self.map_req_id_to_historical_data_ended = {}

    async def setup_api_connection(self):
        try:

            await self.connect(
                self.data_server_host,
                self.data_server_port,
                self.data_server_client_id,
                self.access_token,
            )

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
            # we should log it and not show it to the user.
            print(f"Unable to connect to data server, Exception: {exp}")

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
            asyncio.run_coroutine_threadsafe(self._start_setup(), self.loop)
            # asyncio.run(self._start_setup())
        except Exception as e:
            print("Inside Start: ", e)

    def next_valid_request_id(self, next_request_id: int):
        self.req_id = next_request_id
        self.nextorderId = self.req_id
        print("Next valid request id:", self.req_id)
        variables.nextorderId = next_request_id

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

        bar_date = historical_bars["datetime"]
        bar_open = historical_bars["open"]
        bar_high = historical_bars["high"]
        bar_low = historical_bars["low"]
        bar_close = historical_bars["close"]
        bar_volume = historical_bars["volume"]

        try:

            # Formatting bar_date and converting to users target_timezone
            utc_timezone = pytz.utc

            # Parse bar date string to datetime object
            utc_datetime_dt_obj = datetime.datetime.strptime(bar_date, "%Y%m%d %H%M%S")

            # Convert UTC time to target time zone
            bar_target_datetime = utc_timezone.localize(utc_datetime_dt_obj).astimezone(
                variables.target_timezone_obj
            )

            # bar_target_datetime = bar_target_datetime.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(e)

        # Add Row to dataframe (concat)
        warnings.filterwarnings(
            "ignore",
            category=FutureWarning,
        )

        # # Fill NaN
        # row = row.fillna(-1)

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
        # print(f"Error: request_id={request_id}, {error_code=} msg={error_msg} {advance_order_reject_json=}")

        variables.req_mkt_data_end[request_id] = True
        variables.req_error[request_id] = True

    # Callback for req_market_snapshot
    def tick_price(self, request_id: int, tick_type: str, price: float):

        if variables.flag_debug_mode:
            print(
                "TickPrice. TickerId:",
                request_id,
                "tickType:",
                tick_type,
                "Price:",
                price,
            )

        # Updating bid price, if price is not -1
        if (tick_type == "BID") and (price != -1):
            variables.bid_price[request_id] = price

        # Updating ask price, if price is not -1
        if (tick_type == "ASK") and (price != -1):
            variables.ask_price[request_id] = price

        # Updating ask price, if price is not -1
        if (tick_type == "LAST") and (price != -1):
            variables.last_price[request_id] = price

    # Callback for req_market_snapshot
    def tick_size(self, request_id: int, tick_type: str, size: float):

        if variables.flag_debug_mode:
            print(
                "TickSize. TickerId:",
                request_id,
                "tickType:",
                tick_type,
                "Price:",
                size,
            )

        # Updating ask price, if price is not -1
        if (tick_type == "BID_SIZE") and (size != -1):
            variables.bid_size[request_id] = size

        # Updating ask price, if price is not -1
        if (tick_type == "ASK_SIZE") and (size != -1):
            variables.ask_size[request_id] = size

        # Updating ask price, if price is not -1
        if (tick_type == "VOLUME") and (size != -1):
            variables.volume[request_id] = size

        if (tick_type == "OPTION_CALL_OPEN_INTEREST") and (size is not None):
            variables.call_option_open_interest[request_id] = size

        if (tick_type == "OPTION_PUT_OPEN_INTEREST") and (size is not None):
            variables.put_option_open_interest[request_id] = size

    # Callback for req_market_snapshot
    def tick_option_computation(
        self,
        request_id: int,
        tick_type: str,
        delta: float,
        gamma: float,
        vega: float,
        theta: float,
        iv: float,
        underlying_price: float,
        option_price: float,
        pvDividend: float,
    ):
        if variables.flag_debug_mode:
            print(
                "TickOptionComputation. TickerId:",
                request_id,
                "TickType:",
                tick_type,
                "ImpliedVolatility:",
                iv,
                "Delta:",
                delta,
                "Gamma: ",
                gamma,
                "Vega:",
                vega,
                "Theta:",
                theta,
            )

        # Setting delta value for reqId, (tickType = 13 -> Model Delta)
        if tick_type == "OPTION_MODEL":
            if delta is not None:
                variables.options_delta[request_id] = delta

            if gamma is not None:
                variables.options_gamma[request_id] = gamma

            if theta is not None:
                variables.options_theta[request_id] = theta

            if vega is not None:
                variables.options_vega[request_id] = vega

            if underlying_price is not None:
                variables.und_price[request_id] = underlying_price
                # print("Underlying Price: ", underlying_price)

        if tick_type == "OPTION_BID":
            variables.options_iv_bid[request_id] = iv

        elif tick_type == "OPTION_ASK":
            variables.options_iv_ask[request_id] = iv

        elif tick_type == "OPTION_LAST":
            variables.options_iv_last[request_id] = iv

    # Callback for req_market_snapshot
    def market_snapshot_end(self, request_id: int):

        # Indicates that the market_snapshot response has ended
        variables.req_mkt_data_end[request_id] = True

        # Print to console
        if variables.flag_debug_mode:
            print("market_snapshot_end. ReqId:", request_id)

    # Callback for req_option_contracts
    def option_contracts_data(
        self,
        request_id: int,
        underlyingConId: int,
        exchange: str,
        trading_class: str,
        multiplier: int,
        expirations: set,
        strikes: set,
    ):

        if variables.flag_debug_mode:
            print(
                "SecurityDefinitionOptionParameter.",
                "ReqId:",
                request_id,
                "Underlying conId:",
                underlyingConId,
                "Exchange:",
                exchange,
                "TradingClass:",
                trading_class,
                "Multiplier:",
                multiplier,
                "Expirations:",
                expirations,
                "Strikes:",
                str(strikes),
            )

        # Appending the trading class to the list.
        variables.map_reqid_to_all_trading_class[request_id].append(trading_class)

        # TODO Karan: strikes and expirtions are list check if it is working
        # Store details only for the target exchange
        if exchange == variables.map_req_id_to_fut_fop_exchange[request_id]:
            if (
                trading_class
                == variables.map_reqid_to_trading_class_sec_def[request_id]
            ):
                variables.expiry_dates[request_id] = expirations
                variables.strike_prices[request_id] = str(strikes)
            elif variables.map_reqid_to_trading_class_sec_def[request_id] == "":
                variables.expiry_dates[request_id] = expirations
                variables.strike_prices[request_id] = str(strikes)

    # Callback for req_option_contracts
    def option_contracts_data_end(self, request_id: int):
        variables.req_sec_def_end[request_id] = True

        # Print to console
        if variables.flag_debug_mode:
            print("option_contracts_data_end : reqId = ", request_id)

    # Callback for req_contract_details
    def contract_details(self, request_id: int, contract_details: AOContractDetails):

        # Record in class variable
        variables.contract_details[request_id] = contract_details

        # Append all the contract for request_id in class variable
        variables.all_conid_from_con_details[request_id].append(
            contract_details.contract.conId
        )
        variables.map_expiry_to_conid[request_id][
            contract_details.contract.expiry
        ] = contract_details.contract.conId

        # Print to console
        if variables.flag_debug_mode:
            print(
                "In contract_details:  request_id=",
                request_id,
                "Trading Class=",
                contract_details.contract.trading_class,
                "Contract Details=",
                contract_details,
            )

        # code to get tick size
        rule_id = contract_details.marketRuleIds

        # get con id
        con_id = contract_details.contract.conId

        # get all rule ids
        list_of_all_rules = [int(rule_id) for rule_id in rule_id.split(",")]

        # remove duplicates
        list_of_all_rules = set(list_of_all_rules)

        # get market rules for each rule id
        for rule_ids in list_of_all_rules:

            # This is only used for API bridge
            request_id = variables.nextorderId
            variables.nextorderId += 1

            variables.map_con_id_to_rule_id[con_id] = rule_ids

            # self.req_market_rule(rule_ids)
            if variables.use_api_bridge:
                self.req_market_rule(request_id, rule_ids, priority=1)
            else:
                variables.app.reqMarketRule(rule_ids)

    # Callback for req_contract_details
    def contract_details_end(self, request_id: int):

        # Indicates that the req_contract_details response has ended
        variables.contract_details_end[request_id] = True

        # Print to console
        if variables.flag_debug_mode:
            print("contract_details_end. request_id:", request_id)

    def market_rule(self, request_id: int, market_rule_id: int, price_increments: list):

        if variables.flag_debug_mode:
            print(
                "Market Rule. ReqId:",
                request_id,
                "Market Rule ID:",
                market_rule_id,
                "Price Increments:",
                price_increments,
            )

        # map rule id to price increments
        variables.map_rule_id_to_increments[market_rule_id] = price_increments
