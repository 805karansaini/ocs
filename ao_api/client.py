import asyncio
import json
import logging
import queue
import socket
from typing import Optional

from ao_api import decoder, msg_reader
from ao_api.message import OUT
from ao_api.ws_client import WebSocketClient
from ao_api.contract import Contract, contract_to_dict
from ao_api.enums import BarType, BarUnit, DurationUnit

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

    async def connect(self, host=None, port=None, client_id=None, endpoint=None):

        # Endpoint
        endpoint = f"ws://{host}:{port}/ws/{client_id}"
        self.endpoint = endpoint

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
            self.conn.disconnect()
            self.reset()

    #########################################################################
    ################## Historical Data
    #########################################################################

    def get_historical_bars(
        self,
        request_id: str,
        contract: Contract,
        end_datetime: Optional[str] = None,
        start_datetime: Optional[str] = None,
        duration: Optional[int] = None,
        duration_unit: Optional[DurationUnit] = None,
        bar_size: Optional[int] = None,
        bar_unit: Optional[BarUnit] = None,
        bar_type: Optional[BarType] = None,
        flag_rth_only: Optional[bool] = None,
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
            request = {}
            request["request_id"] = request_id
            request["request_type"] = "get_historical_bars"

            # Create a params dict
            params = dict()

            # Define request parameters
            params["contract"] = contract_to_dict(contract)

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
            request = json.dumps(request)

        except Exception as ex:
            pass
            # self.wrapper.error(request_id, ex.code, ex.msg + ex.text)
            return

        self.sendMsg(request)

    def is_connected(self):
        """Call this function to check if there is a connection with TWS"""

        if self.conn is not None:
            return self.conn.is_connected()
        else:
            return False
