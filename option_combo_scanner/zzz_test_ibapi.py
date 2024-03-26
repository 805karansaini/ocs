import threading
import time
from ibapi.client import EClient
from ibapi.common import TickAttrib, TickerId
from ibapi.ticktype import TickType, TickTypeEnum
from ibapi.wrapper import EWrapper
from ibapi.execution import ExecutionFilter
from ibapi.contract import *
from ibapi.order import *


class IBapi(
    EWrapper,
    EClient,
):
    def __init__(
        self,
    ):
        EClient.__init__(self, self)
        self.nextorderId = None

    # This callback is invoked when first connecting to TWS.
    def nextValidId(self, orderId):
        self.nextorderId = orderId

        # Print to console
        print("The next valid req id is: ", orderId)

    def error(
        self,
        reqId,
        errorCode,
        errorString,
        advancedOrderRejectJson="",
    ):
        # Print to console
        print(
            f"Error returned by TWS: reqId: {reqId} Error Code: {errorCode} Msg: {errorString} AdvancedOrderRejectJson: {advancedOrderRejectJson}"
        )

    
        # Callback for reqMktData (BID, ASK)
    def tickPrice(
        self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib
    ):
        super().tickPrice(reqId, tickType, price, attrib)

        # Updating bid price, if price is not -1
        if (tickType == TickTypeEnum.BID) and (price != -1):
            print("Bid Price", price)

        # Updating ask price, if price is not -1
        if (tickType == TickTypeEnum.ASK) and (price != -1):
            print("Ask Price", price)

    # Callback for reqContractDetails
    def contractDetails(self, reqId: int, contractDetails):
        print(contractDetails)

# Run the IBAPI APP
def run_app():
    app.run()


if __name__ == "__main__":
    # IBKR TWS params
    ibkr_tws_host = "25.51.188.153"
    ibkr_tws_port = 7497  # Value: Live A/C -> 7496, Paper A/C -> 7497
    ibkr_tws_connection_id = 59
    nextorderId = None

    # Connect to IBKR TWS
    app = IBapi()
    app.connect(
        ibkr_tws_host,
        ibkr_tws_port,
        ibkr_tws_connection_id,
    )

    # Start the web socket in a thread
    api_thread = threading.Thread(target=run_app, daemon=True)
    api_thread.start()

    # Check if the API is connected via order id
    while True:
        if isinstance(app.nextorderId, int):
            print("Connected")
            break
        else:
            print("waiting for connection")
            time.sleep(1)


    contract = Contract()
    contract.symbol = "AAPL"
    contract.secType = "STK"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.multiplier = 1

    reqId = app.nextorderId
    app.nextorderId += 1

    app.reqContractDetails(reqId, contract)

    reqId = app.nextorderId
    app.nextorderId += 1

    # Creating a string for the generic tick list
    generic_tick_list = ""
    snapshot = True  # A true value will return a one=time snapshot, while a false value will provide streaming data.
    regulatory = False

    # Requesting the marketdata for all generic ticks
    app.reqMktData(
        reqId, contract, generic_tick_list, snapshot, regulatory, []
    )

    while True:
        time.sleep(20)
        








