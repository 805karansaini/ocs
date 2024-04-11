import logging
import queue
from threading import Thread

from ao_api.decoder import Decoder
from ao_api.ws_client import WebSocketClient

logger = logging.getLogger(__name__)


class MsgReader(Thread):
    def __init__(self, conn: WebSocketClient, msg_queue: queue.Queue, decoder: Decoder):
        super().__init__()
        self.conn = conn
        self.msg_queue = msg_queue
        self.decoder = decoder

    def run(self):
        try:
            # To check the is_connected Method
            while self.conn.is_connected() or not self.msg_queue.empty():
                try:
                    try:
                        # TODO Check these settings
                        response_mssg = self.msg_queue.get(block=True, timeout=1)
                    except queue.Empty:
                        logger.debug("queue.get: empty")
                        # self.msgLoopTmo()
                    else:
                        self.decoder.interpret(response_mssg)
                except (KeyboardInterrupt, SystemExit):
                    logger.info("detected KeyboardInterrupt, SystemExit")
        finally:
            pass
