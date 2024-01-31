import datetime
import threading
import time
from pprint import pprint

import pandas as pd
import pytz

from com.variables import variables as com_variables
from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.ibapi.client import EClient
from option_combo_scanner.ibapi.common import TickAttrib, TickerId
from option_combo_scanner.ibapi.contract import Contract
from option_combo_scanner.ibapi.execution import Execution
from option_combo_scanner.ibapi.ticktype import TickType, TickTypeEnum
from option_combo_scanner.ibapi.utils import floatMaxString, intMaxString
from option_combo_scanner.ibapi.wrapper import EWrapper
from option_combo_scanner.ibapi_ao.executions import get_execution_details
from option_combo_scanner.ibapi_ao.reconnection_handler import ReconnectionHandler
from option_combo_scanner.ibapi_ao.recovery_mode import RecoveryMode
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.utilities import StrategyUtils

logger = CustomLogger.logger


class IBapi(
    EWrapper,
    EClient,
):
    def __init__(
        self,
    ):
        EClient.__init__(self, self)

        # Initialize instance variables
        self.nextorderId = None
        self.reconnector = None

        # Setup the API connection
        self.setup_api_connection()

    def setup_api_connection(
        self,
    ):
        print("Trying to connect to TWS")
        logger.info("Trying to connect to TWS")

        self.connect(
            variables.tws_host,
            variables.tws_port,
            variables.tws_client_id,
        )

        # Start the socket in a thread
        self.run_loop()

        # Check if the API is connected via order id
        while True:
            if isinstance(self.nextorderId, int):
                print("Connected to TWS")
                logger.info("Connected to TWS")
                break
            else:
                print("Waiting for connection with TWS...")
                logger.info("Waiting for connection with TWS...")
                time.sleep(0.5)

        self.reqManagedAccts()

        # self.reconnector = ReconnectionHandler(self)
        # self.reconnector.run()

    def close_api_connection(
        self,
    ):
        # self.reconnector.stop()
        self.disconnect()

    def run_loop(
        self,
    ):
        # Start the web socket in a thread
        api_thread = threading.Thread(target=self.run, daemon=True)
        api_thread.start()

    # This callback is invoked when first connecting to TWS. Subsequently it will be invoked whenever variables.reqIds(-1) is requested.
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)

        # For CAS order Id we will use this
        self.nextorderId = orderId
        com_variables.nextorderId = orderId

        if variables.flag_debug_mode:
            print(f"The next valid order id is: {self.nextorderId}")

    def error(
        self,
        reqId: TickerId,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson="",
    ):
        # Log
        logger.debug(
            f"Error returned by TWS: reqId: {reqId} Error Code: {errorCode} Msg: {errorString} AdvancedOrderRejectJson: {advancedOrderRejectJson}"
        )

        # When we get a make some request like cancelling of subscription and it get excecuted
        # we receive "Error returned by TWS: reqId: -1  Error Code: 2100  Msg: API client has been unsubscribed from option_combo_scanner.account data."
        # When reqId = -1 and flag_debug_mode is off we will not print this for user.
        if (reqId == -1) and (not variables.flag_debug_mode):
            return

        # Error Code: 200 No security definition has been found OR The contract description specified for <Symbol> is ambiguous
        # Error Code: 300 Can't find EId with ticker Id:
        # Error Code: 162 Historical Market Data Service error message:HMDS query returned no data:
        if (errorCode == 200) or (errorCode == 300) or (errorCode == 162):
            variables.req_error[reqId] = True

        else:
            # We have added this to handle all errors, known and unknown
            variables.req_error[reqId] = True

    # Callback for reqSecDefOptParams
    def securityDefinitionOptionParameter(
        self,
        reqId,
        exchange,
        underlyingConId,
        tradingClass,
        multiplier,
        expirations,
        strikes,
    ):
        super().securityDefinitionOptionParameter(
            reqId,
            exchange,
            underlyingConId,
            tradingClass,
            multiplier,
            expirations,
            strikes,
        )

        # Log
        logger.debug(
            f"SecurityDefinitionOptionParameter. ReqId: {reqId} exchange: {exchange} underlyingConId: {underlyingConId} tradingClass: {tradingClass} multiplier: {multiplier} expirations: {expirations} strikes: {strikes}"
        )

        # Store details only for the target exchange
        if exchange == variables.map_req_id_to_fut_fop_exchange[reqId]:
            if tradingClass == variables.map_reqid_to_trading_class_sec_def[reqId]:
                variables.expiry_dates[reqId] = expirations
                variables.strike_prices[reqId] = str(strikes)
            elif variables.map_reqid_to_trading_class_sec_def[reqId] == "":
                variables.expiry_dates[reqId] = expirations
                variables.strike_prices[reqId] = str(strikes)

    # Callback for reqSecDefOptParams
    def securityDefinitionOptionParameterEnd(self, reqId):
        variables.req_sec_def_end[reqId] = True

        # Log
        logger.debug(f"securityDefinitionOptionParameterEnd : reqId {reqId}")

    # Callback for reqContractDetails
    def contractDetails(self, reqId: int, contractDetails):
        # Record in class variable
        variables.contract_details[reqId] = contractDetails

        # Append all the contract for reqId in class variable
        variables.all_conid_from_con_details[reqId].append(
            contractDetails.contract.conId
        )
        variables.map_expiry_to_conid[reqId][
            contractDetails.contract.lastTradeDateOrContractMonth
        ] = contractDetails.contract.conId

        # Log
        logger.debug(
            f"In contractDetails:  reqId={reqId} Trading Class={contractDetails.contract.tradingClass} Contract Details={contractDetails}"
        )

    # Callback for reqContractDetails
    def contractDetailsEnd(self, reqId: int):
        super().contractDetailsEnd(reqId)

        # Indicates that the reqContractDetails response has ended
        variables.contract_details_end[reqId] = True

        # Log
        logger.debug(f"contractDetailsEnd. ReqId: {reqId}")

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

        # Setting delta value for reqId, (tickType = 13 -> Model Delta)
        if (delta is not None) and (tickType == 13):
            variables.options_delta[reqId] = delta

            # Log
            logger.debug(
                f"tickOptionComputation. ReqId: {reqId} TickType: {tickType} TickAttrib: {str(tickAttrib)} ImpliedVolatility: {str(impliedVol)} Delta: {str(delta)} OptionPrice: {str(optPrice)} pvDividend: {str(pvDividend)} Gamma: {str(gamma)} Vega: {str(vega)} Theta: {str(theta)} UnderlyingPrice: {str(undPrice)}"
            )

    def tickGeneric(self, reqId, tickType, value):
        if tickType == 24 and reqId in variables.implied_volatility:
            variables.implied_volatility[reqId] = value

            # Log
            logger.debug(
                f"tickGeneric. ReqId: {reqId} TickType: {tickType} Value: {str(value)}"
            )

    # Callback for reqMktData
    def tickSnapshotEnd(self, reqId: int):
        # Indicates that the reqMktData response has ended
        variables.req_mkt_data_end[reqId] = True

        # Log
        logger.debug(f"tickSnapshotEnd. ReqId: {reqId}")

    # Callback for reqHistoricalData
    def historicalData(self, reqId, bar):
        # Log
        logger.debug(f"historicalData. ReqId: {reqId} BarData: {bar}")

        # Get bar data
        bar_date = bar.date
        bar_open = bar.open
        bar_high = bar.high
        bar_low = bar.low
        bar_close = bar.close

        # Formatting bar_date and converting to users target_timezone
        try:
            # Time, and timezone string
            tws_date_str, tws_tz_str = bar_date.rsplit(" ", 1)

            # Parsing time
            tws_date_obj = datetime.datetime.strptime(tws_date_str, "%Y%m%d %H:%M:%S")

            # Parsing tws_dt with tws_tz
            tws_tz = pytz.timezone(tws_tz_str)
            tws_received_date_obj = tws_tz.localize(tws_date_obj)

            # convert localized datetime to target timezone
            bar_date = tws_received_date_obj.astimezone(variables.target_timezone_obj)

        except Exception as e:
            bar_date = datetime.datetime.strptime(bar_date, "%Y%m%d")

        # create another row to append
        row = pd.DataFrame(
            {"Time": bar_date, "Open": bar_open, "Close": bar_close}, index=[0]
        )

        # While Using Price Chart Making a dataframe
        if reqId in variables.map_req_id_to_historical_data_dataframe:
            # Add Row to dataframe (concat)
            variables.map_req_id_to_historical_data_dataframe[reqId] = pd.concat(
                [variables.map_req_id_to_historical_data_dataframe[reqId], row],
                ignore_index=True,
            )

        else:
            # Update close only if fresher data is available
            if (
                variables.price_data_update_time[reqId] is None
                or bar_date >= variables.price_data_update_time[reqId]
            ):
                variables.close_price[reqId] = bar_close
                variables.price_data_update_time[reqId] = bar_date

            # Update high only if variables.high_price is None or bar_high >= variables.high_price[reqId]
            if (
                variables.high_price[reqId] is None
                or bar_high > variables.high_price[reqId]
            ):
                variables.high_price[reqId] = bar_high

            # Update low only if variables.low_price is None or bar_low <= variables.low_price[reqId]
            if (
                variables.low_price[reqId] is None
                or bar_low < variables.low_price[reqId]
            ):
                variables.low_price[reqId] = bar_low

    # Callback for reqHistoricalData
    def historicalDataEnd(self, reqId: int, start: str, end: str):
        super().historicalDataEnd(reqId, start, end)

        # Indicates that the reqHistoricalData response has ended
        variables.req_mkt_data_end[reqId] = True

        # Log
        logger.debug(
            f"historicalDataEnd. ReqId: {reqId} from option_combo_scanner.{start} to {end} Historical Data Ended"
        )

    #########################################################################
    #    VERSION 1
    #########################################################################

    # Callback for reqMktData (BID, ASK)
    def tickPrice(
        self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib
    ):
        super().tickPrice(reqId, tickType, price, attrib)

        # Log
        logger.debug(
            f"TickPrice. TickerId: {reqId} tickType: {tickType} Price: {floatMaxString(price)} CanAutoExecute: {attrib.canAutoExecute} PastLimit: {attrib.pastLimit} PreOpen: {attrib.preOpen}"
        )

        # Updating bid price, if price is not -1
        if (tickType == TickTypeEnum.BID) and (price != -1):
            variables.bid_price[reqId] = price

        # Updating ask price, if price is not -1
        if (tickType == TickTypeEnum.ASK) and (price != -1):
            variables.ask_price[reqId] = price

    # Callback for placeOrder
    def orderStatus(
        self,
        orderId,
        status,
        filled,
        remaining,
        avgFillPrice,
        permId,
        parentId,
        lastFillPrice,
        clientId,
        whyHeld,
        mktCapPrice,
    ):
        try:
            orderId = int(orderId)
        except Exception as exp:
            pass

        if remaining == 0 or status in ["Filled", "Cancelled", "Inactive"]:
            data = {}
            # data["AccountID"] = variables.user_trading_account
            # data["OrderID"] = orderId
            data["AverageFillPrice"] = avgFillPrice
            data["OrderStatus"] = status  # if status != "Inactive" else "Rejected"
            data["LastUpdateTime"] = datetime.datetime.now(
                variables.target_timezone_obj
            )

            try:
                SqlQueries.update_orders(data, where_clause=f"WHERE OrderID={orderId}")
                StrategyUtils.update_the_values_for_order_preset_table()
            except Exception as e:
                logger.error(f"Exception in updating order status: {e}")

            logger.info(
                f"Order status updated for order id: {orderId} status: {status} avgFillPrice: {avgFillPrice}"
            )

        # Log debug
        logger.debug(
            f"Inside orderStatus: Order Id: {orderId} Status: {status} Filled: {filled} Remaining: {remaining} LastFillPrice: {lastFillPrice}"
        )

    # Callback for placeOrder
    def openOrder(self, orderId, contract, order, orderState):
        data = {}
        data["LastUpdateTime"] = datetime.datetime.now(variables.target_timezone_obj)

        try:
            SqlQueries.update_orders(data, where_clause=f"WHERE OrderID={orderId}")
        except Exception as e:
            logger.error(f"Exception in openOrder, updating LUT: {e}")

        # Log
        logger.debug(
            f"Inside openOrder: OrderId: {orderId} Symbol: {contract.symbol} SecType: {contract.secType} Exchange: {contract.exchange} Action: {order.action} OrderType: {order.orderType} TotalQty: {order.totalQuantity} CashQty: {order.cashQty} LmtPrice: {order.lmtPrice} AuxPrice: {order.auxPrice} Status: {orderState.status}"
        )

    # Callback for reqExecutions
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):
        super().execDetails(reqId, contract, execution)

        # Execution Time
        execution_time = execution.time

        # Split the input string into date, time, and timezone parts
        date_str, time_str, tz_str = execution_time.split()

        # Parse the string into a datetime object
        local_time = datetime.datetime.strptime(
            f"{date_str} {time_str}", "%Y%m%d %H:%M:%S"
        )

        # Define time zones
        received_timezone = pytz.timezone(tz_str)
        eastern_timezone = pytz.timezone("US/Eastern")

        # Localize the time to Asia/Calcutta timezone
        localized_time = received_timezone.localize(local_time)

        # Convert the time to Eastern Time Zone
        eastern_time = localized_time.astimezone(eastern_timezone)

        data = {}
        data["ExecutionID"] = execution.execId
        data["OrderID"] = execution.orderId
        data["ExecutionPrice"] = execution.price
        data["ExecutionQuantity"] = execution.shares
        data["ExecutionTime"] = eastern_time
        data["PermID"] = execution.permId
        data["CumExecutionQuantity"] = execution.cumQty
        data["AverageExecutionPrice"] = execution.avgPrice
        data["AccountID"] = execution.acctNumber

        SqlQueries.insert_into_executions(data)

        # Log
        logger.debug(
            f"ExecDetails. ReqId: {reqId} Symbol: {contract.symbol} SecType: {contract.secType} Currency: {contract.currency} Order Id: {execution.orderId} Execution: {execution}"
        )

    # Callback for reqExecutions
    def execDetailsEnd(self, reqId: int):
        super().execDetailsEnd(reqId)

        variables.bool_execution_details = True

        # Log
        logger.debug(f"ExecDetailsEnd. ReqId: {reqId}")

    # Callback for reqAccountUpdates
    def updateAccountValue(self, key, val, currency, accountName):
        # When the required data is available, Set the value in dataframe.
        if (key == "NetLiquidationByCurrency") and (
            currency == variables.standard_currency_for_account_value
        ):
            variables.map_account_id_to_nlv[accountName] = float(val)

        if (key == "MaintMarginReq") and (
            currency == variables.standard_currency_for_account_value
        ):
            variables.map_account_id_to_maint_margin[accountName] = float(val)

    # Callback for reqAccountUpdates, Indicates the end
    def accountDownloadEnd(self, accountName: str):
        """
        Callback method to check if the account details fetching is completed

        :param accountName: The name of the account (account-id)
        :return: None
        """

        #  Setting Flag as True to indicate the request ended.
        variables.flag_account_update_ended[accountName] = True

        # Log
        logger.debug(f"Account download finished: {accountName}")

    # Get all the acive managed accounts
    def managedAccounts(self, accountsList: str):
        super().managedAccounts(accountsList)

        # print("Active Managed Accounts: ", accountsList)
        for account_id in accountsList.split(","):
            if account_id == "":
                continue
            variables.all_active_trading_accounts.add(account_id)
