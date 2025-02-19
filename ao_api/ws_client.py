import asyncio
import json
import queue

import websockets

from ao_api.custom_logger import CustomLogger

FLAG_LOG_REQUEST_RESPONSES = True


class WebSocketClient:
    """
    Simple WebSocket client
    """

    def __init__(self, endpoint, queue: queue.Queue):
        self.endpoint = endpoint
        self.websocket = None
        self.queue = queue
        self.loop = None
        self.custom_logger = CustomLogger("server_response")

    async def connect(self):
        """
        Connects to the server
        """
        try:
            # Connect via WS
            self.websocket = await websockets.connect(
                self.endpoint, max_size=None, ping_timeout=None, close_timeout=None
            )

            self.loop = asyncio.get_event_loop()
        except Exception as e:
            print("Error while connecting: ", e)

    async def disconnect(self):
        """
        Disconnect to the server
        """
        try:
            if self.websocket is not None:
                self.custom_logger.info("disconnecting")
                await self.websocket.close()
                self.websocket = None
                self.custom_logger.info("disconnected")
        except Exception as e:
            pass

    async def close(self):
        """
        Closes the connection
        """
        try:
            if self.websocket:
                await self.websocket.close()

                # Once the websocket is close set as None
                self.websocket = None
        except Exception as e:
            pass

    def is_connected(self):
        return self.websocket is not None

    async def receive_response(self):
        """
        Receives the response from the server
        """
        while True:
            try:
                # Get Response
                response = await self.websocket.recv()
                json_response = json.loads(response)

                # Insert the response in the Queue
                self.queue.put(json_response)

                # Logging
                if FLAG_LOG_REQUEST_RESPONSES:
                    request_id = json_response.get("request_id", None)
                    response_type = json_response.get("response_type", None)
                    self.custom_logger.logger.info(
                        f"Received response for reqId: {request_id} responseType: {response_type} Response Size: {len(json_response.get('result', []))}"
                    )
                    # self.custom_logger.logger.info(json_response)

            except websockets.exceptions.ConnectionClosed as e:
                self.websocket = None
                self.custom_logger.logger.info(f"WebSocket connection closed: {e}")
                break
            except Exception as e:
                self.custom_logger.logger.error(f"Exception: {e}")

    def run_async(self, coro):
        """
        Helper method to run coroutine synchronously
        """
        loop = self.loop

        # print(f"WS Loop: {loop}")
        print(f"WS loop {loop}, loop id: {id(loop)}")

        return loop.run_until_complete(coro)
        # return asyncio.get_event_loop().run_until_complete(coro)

    def send_request(self, request):
        try:

            async def async_send_request():
                await self.websocket.send(request)

            self.run_async(async_send_request())
        except Exception as e:
            print(f"Exception: {e}")

    async def async_send_request(self, request):
        await self.websocket.send(request)

        if FLAG_LOG_REQUEST_RESPONSES:
            # Logging
            self.custom_logger.logger.info(f"Sent request: {request}")
