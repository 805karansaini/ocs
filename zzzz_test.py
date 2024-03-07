import threading
import time
from decimal import Decimal

from com.variables import variables
from ibapi.client import EClient
from ibapi.common import TickAttrib, TickerId
from ibapi.contract import *
from ibapi.execution import ExecutionFilter
from ibapi.order import *
from ibapi.ticktype import TickType, TickTypeEnum
from ibapi.utils import Decimal
from ibapi.wrapper import EWrapper


class IBapi(
    EWrapper,
    EClient,
):
    def __init__(
        self,
    ):
        EClient.__init__(self, self)
        self.nextorderId = None
        self.start = None

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
    def historicalData(self, reqId, bar):
        super().historicalData(reqId, bar)
        print(f"{bar.date} - {bar.open} - {bar.high} - {bar.low} - {bar.close} - {bar.volume}")

     # Callback for reqMktData (Delta)
    def tickOptionComputation(
        self,
        reqId: TickerId,
        tickType: TickType,
        tickAttrib: int,
        impliedVol: float,
        delta: float,
        optPrice: float,
        pvDividend: float,
        gamma: float,
        vega: float,
        theta: float,
        undPrice: float,
    ):

        super().tickOptionComputation(
            reqId,
            tickType,
            tickAttrib,
            impliedVol,
            delta,
            optPrice,
            pvDividend,
            gamma,
            vega,
            theta,
            undPrice,
        )

        # Print to console
        print(
                "TickOptionComputation. TickerId:",
                reqId,
                "TickType:",
                tickType,
                "TickAttrib:",
                str(tickAttrib),
                "ImpliedVolatility:",
                str(impliedVol),
                "Delta:",
                str(delta),
                "OptionPrice:",
                str(optPrice),
                "pvDividend:",
                str(pvDividend),
                "Gamma: ",
                str(gamma),
                "Vega:",
                str(vega),
                "Theta:",
                str(theta),
                "UnderlyingPrice:",
                str(undPrice),
            )

    # Callback for reqMktData
    def tickSnapshotEnd(self, reqId: int):

        # Print to console
        print("tickSnapshotEnd. ReqId:", reqId)

    

    # def tickSize(self, reqId: TickerId, tickType: TickerId, size: Decimal):
    #     super().tickSize(reqId, tickType, size)
    #     # print(size)
    #     if (tickType == TickTypeEnum.OPTION_CALL_OPEN_INTEREST) and (size != -1):
    #         print("Call OI:", size, time.perf_counter() - self.start)
            

    #     # Updating ask price, if price is not -1
    #     if (tickType == TickTypeEnum.OPTION_PUT_OPEN_INTEREST) and (size != -1):
    #         print("PUT OI:", size)

# Run the IBAPI APP
def run_app():
    app.run()


if __name__ == "__main__":
    # IBKR TWS params
    ibkr_tws_host = "25.51.188.153"
    ibkr_tws_host = "25.29.181.59" 
    ibkr_tws_host = "localhost" 

    ibkr_tws_port = 7497
    ibkr_tws_connection_id = 12123
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
    contract.symbol = "CRM"
    contract.secType = "OPT"
    contract.exchange = "SMART"
    contract.currency = "USD"
    contract.multiplier = 100
    contract.strike = 310
    contract.lastTradeDateOrContractMonth = "20240315"
    contract.right = "PUT"

    # reqId = app.nextorderId
    # app.nextorderId += 1

    # app.reqContractDetails(reqId, contract)

    reqId = app.nextorderId
    app.nextorderId += 1

    genericTickList = ""
    snapshot = False
    regulatory = False 

    print(f"Contract: {contract}")
    app.reqMktData(reqId, contract, genericTickList,
            snapshot,
            regulatory,
            [],)

    while True:
        time.sleep(12)
    # Creating a string for the generic tick list
    
    end_date_time = ""
    duration_string = "14 D"
    duration_string = "14 D"
    bar_size_setting = "2 hours"
    what_to_show = "TRADES"
    use_rth = variables.flag_use_rth
    format_date = 1
    keep_up_to_date = False

    app.start = time.perf_counter()
    # Requesting the marketdata for all generic ticks
    app.reqHistoricalData(
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

    while True:
        time.sleep(20)