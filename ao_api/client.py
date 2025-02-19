import asyncio
import json
import logging
import queue
import socket
from typing import Optional

from ao_api import decoder, msg_reader
from ao_api.brokers import Broker
from ao_api.contract import Contract, contract_to_json
from ao_api.enums import BarType, BarUnit, DurationUnit
from ao_api.execution import ExecutionFilter, execution_filter_to_json
from ao_api.message import OUT
from ao_api.order import Order, order_to_json
from ao_api.ws_client import WebSocketClient

logger = logging.getLogger(__name__)


class EClient(object):
    def __init__(self, wrapper, loop):
        self.msg_queue = queue.Queue()
        self.wrapper = wrapper
        self.loop = loop
        self.decoder = None
        self.endpoint = None
        self.conn = None
        self.reader = None
        self.decoder = None
        self.reset()

    def reset(self):
        self.msg_queue = queue.Queue()
        self.decoder = None
        self.endpoint = None
        self.conn = None
        self.reader = None
        self.decoder = None
        self.loop = None
        # self.connState = None

    def sendMsg(self, msg):
        # Ensure you're calling this inside a function where the loop is running
        # self.conn.send_request(msg)

        asyncio.run_coroutine_threadsafe(self.conn.async_send_request(msg), self.loop)

    async def connect(self, host=None, port=None, client_id=None, access_token=None):
        if access_token is None:
            endpoint = f"ws://{host}:{port}/ws/{client_id}"
        else:
            # Endpoint
            endpoint = f"ws://{host}:{port}/ws/{client_id}?access_token={access_token}"
        self.endpoint = endpoint

        print("Connecting to endpoint: ", self.endpoint)

        try:
            # Create WS connection
            self.conn: WebSocketClient = WebSocketClient(self.endpoint, self.msg_queue)
            await self.conn.connect()

            # Create Decoder Obj
            self.decoder = decoder.Decoder(self.wrapper)

            # Run Decoder in Separate thread
            self.reader = msg_reader.MsgReader(self.conn, self.msg_queue, self.decoder)
            self.reader.start()  # start thread

            # TODO - we should send a message saying got connected, or disconnect if the conn. fails
        except socket.error:
            # TODO Test later
            # if self.wrapper:
            #     self.wrapper.error(-1, -1, "Unable to connect with Data Server")
            logger.info("could not connect")
            self.disconnect()

    def disconnect(self):
        """Call this function to terminate the connections with TWS.
        Calling this function does not cancel orders that have already been
        sent."""

        if self.conn is not None:
            logger.info("disconnecting")
            asyncio.run(self.conn.disconnect())
            self.reset()

    def is_connected(self):
        """Call this function to check if there is a connection with TWS"""

        if self.conn is not None:
            return self.conn.is_connected()
        else:
            return False

    #########################################################################
    ################## Historical Data
    #########################################################################

    def get_historical_bars(
        self,
        request_id: int,
        contract: Contract,
        end_datetime: Optional[str] = None,
        start_datetime: Optional[str] = None,
        duration: Optional[int] = None,
        duration_unit: Optional[DurationUnit] = None,
        bar_size: Optional[int] = None,
        bar_unit: Optional[BarUnit] = None,
        bar_type: Optional[BarType] = None,
        flag_rth_only: Optional[bool] = None,
        priority: int = 1,
    ) -> None:
        """
        required params:
            request_id: str,
            contract: Contract

        Optional params:
            end_datetime: str,
            start_datetime: str,
            duration: int,
            duration_unit: DurationUnit,
            bar_size: int,
            bar_unit: BarUnit,
            bar_type: BarType,
            flag_rth_only: bool
        """

        try:
            # Request
            request: dict = {}
            request["request_id"] = request_id
            request["request_type"] = "get_historical_bars"
            request["priority"] = priority

            # Create a params dict
            params: dict = dict()

            # Define request parameters
            params["contract"] = contract_to_json(contract)

            if end_datetime is not None:
                params["end_datetime"] = end_datetime
            if start_datetime is not None:
                params["start_datetime"] = start_datetime
            if duration is not None:
                params["duration"] = duration
            if duration_unit is not None:
                params["duration_unit"] = duration_unit
            if bar_size is not None:
                params["bar_size"] = bar_size
            if bar_unit is not None:
                params["bar_unit"] = bar_unit
            if bar_type is not None:
                params["bar_type"] = bar_type
            if flag_rth_only is not None:
                params["flag_rth_only"] = flag_rth_only

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request_json = json.dumps(request)

        except Exception as ex:
            print(f"Error fetching historical data: {ex}")
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request_json)

    #########################################################################
    ################## Real time quotes
    #########################################################################

    def subscribe_real_time_quotes(
        self, request_id: int, contract: Contract, priority: int = 1
    ):
        """
        required params:
            request_id: str,
            contract: Contract
        """

        try:
            # Request
            request: dict = {}
            request["request_id"] = request_id
            request["request_type"] = "subscribe_real_time_quotes"
            request["priority"] = priority

            # Create a params dict
            params: dict = dict()

            # Define request parameters
            params["contract"] = contract_to_json(contract)

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request_json = json.dumps(request)

        except Exception as ex:
            print(f"Error subscribing real time quotes: {ex}")
            return

        self.sendMsg(request_json)

    def unsubscribe_real_time_quotes(self, request_id: int, priority: int = 1):
        """
        required params:
            request_id: int
        """

        try:
            # Request
            request: dict = {}
            request["request_id"] = request_id
            request["request_type"] = "unsubscribe_real_time_quotes"
            request["priority"] = priority

            # Create a params dict
            params: dict = dict()

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request_json = json.dumps(request)

        except Exception as ex:
            print(f"Error unsubscribing real time quotes: {ex}")
            return

        self.sendMsg(request_json)

    def req_market_snapshot(
        self,
        request_id: int,
        contract: Contract,
        genericTickList: str = "",
        flag_tws_only: bool = False,
        priority: int = 1,
    ):
        """
        required params:
            request_id: str,
            contract: Contract,
            genericTickList: str = "",
            flag_tws_only: bool = False,
            priority: int = 1
        """

        try:
            # Request
            request: dict = {}
            request["request_id"] = request_id
            request["request_type"] = "req_market_snapshot"
            request["priority"] = priority

            # Create a params dict
            params: dict = dict()

            # Define request parameters
            params["contract"] = contract_to_json(contract)

            params["genericTickList"] = genericTickList
            params["flag_tws_only"] = flag_tws_only

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request_json = json.dumps(request)

        except Exception as ex:
            print(f"Error fetching option greeks iv: {ex}")
            return

        self.sendMsg(request_json)

    def req_option_contracts(
        self,
        request_id: int,
        ticker: str,
        underlying_sec_type: str,
        futFopExchange: str = "",
        conid: int = -1,
        as_of_date: str = "",
        flag_use_tws_only: bool = False,
        priority: int = 1,
    ) -> None:
        """
        required params:
            request_id: str,
            ticker: str,
            underlying_sec_type: str,
            futFopExchange: str,
            conid: int,
            as_of_date: str,
            flag_use_tws_only: bool
            priority: int = 1,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_option_contracts"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["ticker"] = ticker
            params["underlying_sec_type"] = underlying_sec_type
            params["futFopExchange"] = futFopExchange
            params["conid"] = conid
            params["as_of_date"] = as_of_date
            params["flag_use_tws_only"] = flag_use_tws_only

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error sending historical data request for option contracts: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def req_contract_details(
        self,
        request_id: int,
        contract: Contract,
        priority: int = 1,
    ) -> None:
        """
        required params:
            request_id: str,
            contract: Contract,

        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_contract_details"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["contract"] = contract_to_json(contract)

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error sending contract details request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def place_order(
        self,
        request_id: int,
        contract: Contract,
        broker: Broker,
        account: str,
        order: Order,
        priority: int = 10,
    ) -> None:
        """
        required params:
            request_id: str,
            contract: Contract,
            broker: Broker,
            account: str,
            order: Order,
            priority: int = 10,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "place_order"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["contract"] = contract_to_json(contract)
            params["broker"] = broker.value
            params["account"] = account
            params["order"] = order_to_json(order)

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error sending contract details request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def cancel_order(
        self,
        request_id: int,
        order_request_id: int,
        priority: int = 10,
    ) -> None:
        """
        required params:
            request_id: str,
            contract: Contract,
            order_request_id: int,
            priority: int = 10,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "cancel_order"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["order_request_id"] = order_request_id

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error sending contract details request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def modify_order(
        self,
        request_id: int,
        order_request_id: int,
        contract: Contract,
        order: Order,
        priority: int = 10,
    ) -> None:
        """
        required params:
            request_id: str,
            order_request_id: int,
            contract: Contract,
            order: Order,
            priority: int = 10,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "modify_order"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["order_request_id"] = order_request_id
            params["contract"] = contract_to_json(contract)
            params["order"] = order_to_json(order)

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error modify order request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def req_open_orders(
        self,
        request_id: int,
        broker: Broker,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_open_orders"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["broker"] = broker.value

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error req_open_orders request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def req_executions(
        self,
        request_id: int,
        broker: Broker,
        execution_filter: ExecutionFilter,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker,
            execution_filter: ExecutionFilter,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_executions"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["broker"] = broker.value
            params["execution_filter"] = execution_filter_to_json(execution_filter)

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error req_executions request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def req_next_request_id(
        self,
        request_id: int,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_next_request_id"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error req_next_request_id request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def req_positions(
        self,
        request_id: int,
        broker: Broker,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_positions"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["broker"] = broker.value

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error req_positions request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def req_account_updates(
        self,
        request_id: int,
        broker: Broker,
        account: str,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker,
            account: str,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_account_updates"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["broker"] = broker.value
            params["account"] = account

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error req_account_updates request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def req_pnl(
        self,
        request_id: int,
        broker: Broker,
        account: str,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker,
            account: str,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_pnl"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["broker"] = broker.value
            params["account"] = account

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error req_pnl request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def req_pnl_single(
        self,
        request_id: int,
        broker: Broker,
        account: str,
        contract: Contract,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker,
            account: str,
            contract: Contract,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_pnl_single"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["broker"] = broker.value
            params["account"] = account
            params["contract"] = contract_to_json(contract)

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error req_pnl_single request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def cancel_positions(
        self,
        request_id: int,
        broker: Broker = Broker.TWS,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "cancel_positions"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # # Define request parameters
            params["broker"] = broker.value

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error cancel_positions request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def cancel_account_updates(
        self,
        request_id: int,
        account: str,
        broker: Broker = Broker.TWS,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker,
            account: str,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "cancel_account_updates"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["broker"] = broker.value
            params["account"] = account

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error cancel_account_updates request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def cancel_pnl(
        self,
        request_id: int,
        broker: Broker = Broker.TWS,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker,
            account: str,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "cancel_pnl"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["broker"] = broker.value
            # params["account"] = account

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error cancel_pnl request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def cancel_pnl_single(
        self,
        request_id: int,
        broker: Broker = Broker.TWS,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker,
            account: str,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "cancel_pnl_single"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["broker"] = broker.value
            # params["account"] = account

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error cancel_pnl_single request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def req_market_rule(
        self,
        request_id: int,
        market_rule_id: int,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            market_rule_id: int,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_market_rule"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["market_rule_id"] = market_rule_id
            # params["account"] = account

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error req_market_rule request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    """
    def managedAccounts(self, accountsList: str):
        Acc, Read, Write
        self.logAnswer(current_fn_name(), vars())
    """

    def req_managed_accounts(
        self,
        request_id: int,
        broker: Broker = Broker.TWS,
        priority: int = 1,
    ):
        """
        required params:
            request_id: int,
            broker: Broker = Broker.TWS,
            priority: int,
        """
        try:
            # Request
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "req_managed_accounts"
            request["priority"] = priority

            # Create a params dict
            params = dict()

            # Define request parameters
            params["broker"] = broker.value

            # Add params dict to request
            request["params"] = params

            # Convert request to json format to send to server
            request = json.dumps(request)

        except Exception as ex:
            print("Error req_managed_accounts request: ", ex)
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def reqMarketDataType(self, marketDataType: int):
        """Not Using it"""
        pass
