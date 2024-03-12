import threading
import time
import os

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.execution import ExecutionFilter
from ibapi.contract import *
from ibapi.order import *
from ibapi.common import *
from ibapi.ticktype import *

class IBapi(
    EWrapper,
    EClient,
):
    def __init__(
        self,
    ):
        EClient.__init__(self, self)
        self.nextorderId = None

        self.contract = None
        self.disconnected = False
        self.flag = False

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
        if errorCode == 502:
            self.disconnected = True
        # Print to console
        print(
            f"Error returned by TWS: reqId: {reqId} Error Code: {errorCode} Msg: {errorString} AdvancedOrderRejectJson: {advancedOrderRejectJson}"
        )

    # Callback for reqExecutions
    def execDetails(self, reqId, contract, execution):
        # Print to console
        print(
            f"Inside Execution Details => reqId: {reqId}, execution: {execution}"
        )

    # Callback for reqExecutions
    def execDetailsEnd(self, reqId):
        # Print to console
        print(f"Inside execDetailsEnd reqId: {reqId}")

    def openOrder(self, orderId, contract, order, orderState):

        if True:
            print("\n")
            print("OpenOrder. PermId:", order.permId, "ClientId:", order.clientId, "orderId", order.orderId,
                  "Account:", order.account, "Symbol:", contract.symbol, "SecType:", contract.secType,
                  "Exchange:", contract.exchange, "Action:", order.action, "OrderType:", order.orderType,
                  "TotalQty:", order.totalQuantity, "CashQty:", order.cashQty,
                  "LmtPrice:", order.lmtPrice, "AuxPrice:", order.auxPrice, "Status:", orderState.status,
                  "MinTradeQty:", order.minTradeQty, "MinCompeteSize:", order.minCompeteSize,
                  "competeAgainstBestOffset:", (
                      "UpToMid" if order.competeAgainstBestOffset == COMPETE_AGAINST_BEST_OFFSET_UP_TO_MID else order.competeAgainstBestOffset),
                  "MidOffsetAtWhole:", order.midOffsetAtWhole, "MidOffsetAtHalf:", order.midOffsetAtHalf)

    def orderStatus(self, orderId, status, filled,
                    remaining, avgFillPrice, permId,
                    parentId, lastFillPrice, clientId,
                    whyHeld, mktCapPrice):

        if True:
            # Print to Console
            print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", filled,
                  "Remaining:", remaining, "AvgFillPrice:", avgFillPrice,
                  "PermId:", permId, "ParentId:", parentId, "LastFillPrice:",
                  lastFillPrice, "ClientId:", clientId, "WhyHeld:",
                  whyHeld, "MktCapPrice:", mktCapPrice)

    def contractDetails(self, reqId: int, contractDetails: ContractDetails):

        self.contract = contractDetails.contract
        print(contractDetails.contract)

        # contractDetails.contract.conId
        # print(
        #     datetime.now().strftime("%H:%M:%S.%f")[:-3],
        #     "contractDetails.",
        #     f"reqId:{reqId}",
        #     "\n",
        #     "\n".join(f"{name}: {value}" for name, value in attrs.items()),
        #     contractDetails.contract.conId
        # )
        # print(contractDetails.contract)
        print(contractDetails.contract.lastTradeDateOrContractMonth)
        # print(contractDetails.contract.right)
        print(contractDetails.contract.multiplier)
        print(contractDetails.underSymbol, contractDetails.underConId, contractDetails.underSecType)

        # print("All valid exchanges: ",contractDetails.validExchanges)
        # # print(contractDetails.contract.tradingClass)
        # # print(contractDetails.marketRuleIds)
        # rule_id = contractDetails.marketRuleIds
        # self.contract_for_price = contractDetails.contract
        # list_of_all_rules = [int(rule_id) for rule_id in rule_id.split(",")]
        # print("All rule-ids: ", list_of_all_rules)
        # list_of_all_rules = set(list_of_all_rules)
        # for rule_ids in list_of_all_rules:
        #     self.reqMarketRule(rule_ids)

    def securityDefinitionOptionParameter(self, reqId: int, exchange: str,
                                              underlyingConId: int, tradingClass: str, multiplier: str,
                                              expirations: SetOfString, strikes: SetOfFloat):
        super().securityDefinitionOptionParameter(reqId, exchange,
                                                    underlyingConId, tradingClass, multiplier, expirations, strikes)
        print("SecurityDefinitionOptionParameter.",
                "ReqId:", reqId, "Exchange:", exchange, "Underlying conId:", intMaxString(underlyingConId), "TradingClass:", tradingClass, "Multiplier:", multiplier,
                "Expirations:", expirations, "Strikes:", str(strikes))
        # print(type(expirations))

        # for expiration in expirations:
        #     self.expiry.add(expiration)

        # print(self.expiry)

    # Callback for reqMktData (BID, ASK)
    def tickPrice(
                self, reqId, tickType, price, attrib
      ):
        '''
        A callback to get the tickprice for a contract
        :param reqId: The request if for the request
        :param tickType: The type of the request (bid or ask)
        :param price: The price data
        :param attrib: The attribute
        '''
        super().tickPrice(reqId, tickType, price, attrib)

        print(
            "TickPrice. TickerId:",
            reqId,
            "tickType:",
            tickType,
            "Price:",
            floatMaxString(price),
            "CanAutoExecute:",
            attrib.canAutoExecute,
            "PastLimit:",
            attrib.pastLimit,
            "PreOpen:",
            attrib.preOpen,
            
        )

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

    def managedAccounts(self, accountsList: str):
        '''
        Saves the account ids that are active in the current connection of the TWS instance
        :param accountsList: The list of accounts as a comma separated string
        :return: None
        '''
        super().managedAccounts(accountsList)

        for acc_id in accountsList.split(","):
            print(accountsList)

    # Callback for reqHistoricalData
    def historicalData(self, reqId, bar):
        '''
        A callback method that is called when the historical data is fetched

        :param reqId: The request id for the request which have eneded
        :param bar: The bar object
        '''

        # Print to Console
        if True:
            print("HistoricalData. ReqId:", reqId, "BarData.", bar)

        # Get bar data
        bar_date = bar.date
        bar_open = bar.open
        bar_high = bar.high
        bar_low = bar.low
        bar_close = bar.close
        bar_volume = bar.volume




if __name__ == "__main__":
    # IBKR TWS params
    
    ibkr_tws_host = "25.51.188.153"
    # ibkr_tws_host = "127.0.0.1"
    ibkr_tws_port = 7497  # Value: Live A/C -> 7496, Paper A/C -> 7497
    ibkr_tws_connection_id = 5123
    nextorderId = None

    # Connect to IBKR TWS
    app = IBapi()
    app.connect(
        ibkr_tws_host,
        ibkr_tws_port,
        ibkr_tws_connection_id,
    )

    # Start the web socket in a thread
    api_thread = threading.Thread(target=app.run, daemon=True)
    api_thread.start()

    # The waiting time
    wait_time = 2

    print(ibapi.get_version_string())
    
    # Check if the API is connected via order id
    while (wait_time > 0):
        if app.disconnected:
            print("Disconnected")
            os._exit(-1)
        if isinstance(app.nextorderId, int):
            print("Connected")
            break
        else:
            print("waiting for connection")
            time.sleep(1)

    # contract = Contract()
    # contract.symbol = "NQ"
    # contract.exchange = "SMART"
    # contract.secType = "BAG"
    # contract.currency = "USD"
    # contract.right = "Call"
    # contract.multiplier = 50
    # contract.strike = "5700"
    # contract.lastTradeDateOrContractMonth = "20240307"
            
    contract = Contract()
    contract.symbol = "AAPL"
    contract.secType = "STK"
    contract.currency = "USD"
    contract.exchange = 'SMART' # Setting it to 'SMART' for better response from IBKR

    # # Add legs
    # contract.comboLegs = []
    # combo_leg_dictionary = {}

    # # For each leg
    # for number, (conid_num, leg_exchange, qty_num) in enumerate(zip([685241438,685241177], ['CME','CME'], [1,-1])):
    #     combo_leg_dictionary[f"leg{number}"] = ComboLeg()
    #     combo_leg_dictionary[f"leg{number}"].conId = int(conid_num)
    #     combo_leg_dictionary[f"leg{number}"].ratio = abs(int(qty_num))
    #     combo_leg_dictionary[f"leg{number}"].action = ("SELL" if int(qty_num) < 0 else "BUY")
    #     combo_leg_dictionary[f"leg{number}"].exchange = leg_exchange
    #     combo_leg_dictionary[f"leg{number}"].ExemptCode = 0

    #     # Add leg
    #     contract.comboLegs.append(combo_leg_dictionary[f"leg{number}"])

    nextorderId = app.nextorderId
    
    print(contract)

    # app.reqAllOpenOrders()
    # app.reqManagedAccts()
    # app.reqContractDetails(nextorderId, contract)

    app.reqMktData(
        nextorderId, contract, "", True, False, []
    )

    # # Static for reqHistoricalData
    # end_date_time = ""
    # duration_string = "60 S"
    # bar_size_setting = "1 min"
    # use_rth = 0
    # format_date = 1
    # keep_up_to_date = False

    # duration_size_for_historical_data = "60 S"
    # candle_size_for_historical_data = "1 min"
    # what_to_show_for_historical_data = 'BID_ASK'

    # app.reqHistoricalData(
    #     nextorderId,
    #     contract,
    #     end_date_time,
    #     duration_string,
    #     bar_size_setting,
    #     'BID_ASK',
    #     0,
    #     format_date,
    #     keep_up_to_date,
    #     [],
    # )

    
    while True:
        time.sleep(2)
    #     if app.contract:

    #         app.reqMktData(app.nextorderId, contract,"", False,"","")

    #         break


    # app.reqSecDefOptParams(nextorderId + 1, "EUR","IDEALPRO","CASH", 12087792)

    # app.reqSecDefOptParams(nextorderId + 1, "AAPL","","STK", 265598)
    
    # # contract.strike = 4350
    
    
    # contract.currency = "USD"
    # # contract.multiplier = 50
    # # contract.lastTradeDateOrContractMonth = '20231011'
    # order_id = app.nextorderId
    # app.nextorderId += 1

    # order = Order()
    # order.orderId = order_id

    # order.orderType = 'LMT'
    # order.action = "BUY"
    # order.tif = "DAY"
    # order.account = 'DU4214840'
    # order.totalQuantity = 1
    # order.lmtPrice = 0.2
    # order.transmit = True

    # # order.whatIf = True

    # # print(f"Origianl Order: ", order)

    # app.placeOrder(order.orderId, contract, order)

    # while True:
    #     # app.reqOpenOrders()
    #     time.sleep(20)










