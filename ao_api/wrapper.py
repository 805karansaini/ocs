import logging

logger = logging.getLogger(__name__)


class EWrapper:
    def __init__(self):
        pass

    def error(
        self,
        request_id: str,
        error_code: int,
        error_msg: str,
        advance_order_reject_json="",
    ):
        """This event is called when error response is received."""
        pass

    def historical_data(self, request_id: str, historical_bars: dict):
        """Returns the requested historical bars."""
        pass

    def historical_data_end(self, request_id: str):
        """Marks the ending of the historical bars reception."""
        pass
