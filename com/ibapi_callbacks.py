"""
Created on 14-Mar-2023

@author: Karan
"""


from com import *
from com.variables import *
from com.mysql_io import *
from com.screen_accounts_tab import *
from com.account_tab_helper import *
from ibapi.client import *
from ibapi.wrapper import *


class IBapi(
    EWrapper,
    EClient,
):
    def __init__(
        self,
    ):
        EClient.__init__(self, self)
        self.nextorderId = None

    # This callback is invoked when first connecting to TWS. Subsequently it will be invoked whenever variables.reqIds(-1) is requested.
    def nextValidId(self, orderId: int):

        super().nextValidId(orderId)
        variables.nextorderId = orderId

        # For CAS order Id we will use this
        self.nextorderId = orderId

        # Print to console
        if True or variables.flag_debug_mode:
            print("The next valid order id is: ", variables.nextorderId)

    # Callback method to receive error
    def error(
        self,
        reqId: TickerId,
        errorCode: int,
        errorString: str,
        advancedOrderRejectJson="",
    ):

        # When we get a make some request like cancelling of subscription and it get excecuted
        # we receive "Error returned by TWS: reqId: -1  Error Code: 2100  Msg: API client has been unsubscribed from account data."
        # When reqId = -1 and flag_debug_mode is off we will not print this for user.
        if (reqId == -1) and (not variables.flag_debug_mode):
            return

        # Error Code: 200 No security definition has been found OR The contract description specified for <Symbol> is ambiguous
        # Error Code: 300 Can't find EId with ticker Id:
        # Error Code: 162 Historical Market Data Service error message:HMDS query returned no data:
        if (errorCode == 200) or (errorCode == 300) or (errorCode == 162):
            variables.req_error[reqId] = True

            # Print to console in case of error in debug mode
            if variables.flag_debug_mode:  # or (errorCode == 162):
                print(
                    "Error returned by TWS: reqId:",
                    reqId,
                    " Error Code:",
                    errorCode,
                    " Msg:",
                    errorString,
                    " AdvancedOrderRejectJson:",
                    advancedOrderRejectJson,
                )

        else:
            # We have added this to handle all errors, known and unknown
            variables.req_error[reqId] = True

            if variables.flag_debug_mode:

                print(
                    "Error returned by TWS: reqId:",
                    reqId,
                    " Error Code:",
                    errorCode,
                    " Msg:",
                    errorString,
                    " AdvancedOrderRejectJson:",
                    advancedOrderRejectJson,
                )

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

        if variables.flag_debug_mode:
            print(
                "SecurityDefinitionOptionParameter.",
                "ReqId:",
                reqId,
                "Exchange:",
                exchange,
                "Underlying conId:",
                intMaxString(underlyingConId),
                "TradingClass:",
                tradingClass,
                "Multiplier:",
                multiplier,
                "Expirations:",
                expirations,
                "Strikes:",
                str(strikes),
            )

        # Appending the trading class to the list.
        variables.map_reqid_to_all_trading_class[reqId].append(tradingClass)

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

        # Print to console
        if variables.flag_debug_mode:
            print("securityDefinitionOptionParameterEnd : reqId = ", reqId)

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

        # Print to console
        if variables.flag_debug_mode:
            print(
                "In contractDetails:  reqId=",
                reqId,
                "Trading Class=",
                contractDetails.contract.tradingClass,
                "Contract Details=",
                contractDetails,
            )

        # code to get tick size
        rule_id = contractDetails.marketRuleIds

        # get con id
        con_id = contractDetails.contract.conId

        # get all rule ids
        list_of_all_rules = [int(rule_id) for rule_id in rule_id.split(",")]

        # remove duplicates
        list_of_all_rules = set(list_of_all_rules)

        # get market rules for each rule id
        for rule_ids in list_of_all_rules:

            variables.map_con_id_to_rule_id[con_id] = rule_ids

            self.reqMarketRule(rule_ids)

    # Method to to get price increments for market
    def marketRule(self, marketRuleId: int, priceIncrements: ListOfPriceIncrements):

        super().marketRule(marketRuleId, priceIncrements)

        # map rule id to price increments
        variables.map_rule_id_to_increments[marketRuleId] = priceIncrements

    # Callback for reqContractDetails
    def contractDetailsEnd(self, reqId: int):

        super().contractDetailsEnd(reqId)

        # Indicates that the reqContractDetails response has ended
        variables.contract_details_end[reqId] = True

        # Print to console
        if variables.flag_debug_mode:
            print("contractDetailsEnd. ReqId:", reqId)

    # Callback for trading account
    def managedAccounts(self, accountsList: str):
        """Receives a comma-separated string with the managed account ids."""

        if accountsList.count(",") > 0:
            # Get account in current session
            variables.current_session_accounts = sorted(
                list(set(accountsList[:-1].split(",")))
            )

            #variables.current_session_accounts = [variables.current_session_accounts[0]]
        else:
            variables.current_session_accounts = [accountsList]

        # add row for each account in df
        add_accounts_in_df()

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
        if variables.flag_debug_mode:
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

        # Setting delta value for reqId, (tickType = 13 -> Model Delta)
        if (delta is not None) and (tickType == 13):
            # print(
            #     "TickOptionComputation. TickerId:",
            #     reqId,
            #     "TickType:",
            #     tickType,
            #     "TickAttrib:",
            #     str(tickAttrib),
            #     "ImpliedVolatility:",
            #     str(impliedVol),
            #     "Delta:",
            #     str(delta),
            #     "OptionPrice:",
            #     str(optPrice),
            #     "pvDividend:",
            #     str(pvDividend),
            #     "Gamma: ",
            #     str(gamma),
            #     "Vega:",
            #     str(vega),
            #     "Theta:",
            #     str(theta),
            #     "UnderlyingPrice:",
            #     str(undPrice),
            # )
            # print(['Delta received', delta])
            variables.options_delta[reqId] = delta
            variables.options_gamma[reqId] = gamma
            variables.options_theta[reqId] = theta
            variables.options_vega[reqId] = vega



        # Print to console
        if (
            variables.flag_debug_mode
            and tickType == 13
            and reqId in variables.options_delta
        ):
            print(
                f"Option delta is set for reqId : {reqId} delta_value : {variables.options_delta[reqId]}"
            )


        if tickType == 10:

            variables.options_iv_bid[reqId] = impliedVol


        elif tickType == 11:

            variables.options_iv_ask[reqId] = impliedVol
        
        elif tickType == 12:
            
            variables.options_iv_last[reqId] = impliedVol

    # Callback for reqMktData
    def tickSnapshotEnd(self, reqId: int):

        # Indicates that the reqMktData response has ended
        variables.req_mkt_data_end[reqId] = True

        # Print to console
        if variables.flag_debug_mode:
            print("tickSnapshotEnd. ReqId:", reqId)

    # Callback for reqHistoricalData
    def historicalData(self, reqId, bar):

        # Print to console
        if variables.flag_debug_mode:
            print("HistoricalData. ReqId:", reqId, "BarData.", bar)

        # Get bar data
        bar_date = bar.date
        bar_open = bar.open
        bar_high = bar.high
        bar_low = bar.low
        bar_close = bar.close
        bar_volume = bar.volume

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
            # print(f"Exception in bar data : {bar}")
            # print(f"Exception : {e}")
            bar_date = datetime.datetime.strptime(bar_date, "%Y%m%d")
            # tws_date_str = bar_date
            # 2023-04-04

        # create another row to append
        row = pd.DataFrame(
            {
                "Time": bar_date,
                "Open": bar_open,
                "Close": bar_close,
                "Volume": bar_volume,
            },
            index=[0],
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

        # Print to console
        if variables.flag_debug_mode:
            print("HistoricalDataEnd. ReqId:", reqId)

    #########################################################################
    #    VERSION 1
    #########################################################################

    # Callback for ticksize
    def tickSize(self, reqId: TickerId, tickType: TickType, size: float):

        super().tickSize(reqId, tickType, size)

        size = float(size)
        
        # print(f"ReqID: {reqId} tickType {tickType}: {size}")
        # Updating ask price, if price is not -1
        if (tickType == TickTypeEnum.BID_SIZE) and (size != -1):

            variables.bid_size[reqId] = size

        # Updating ask price, if price is not -1
        if (tickType == TickTypeEnum.ASK_SIZE) and (size != -1):

            variables.ask_size[reqId] = size

        # Updating ask price, if price is not -1
        if (tickType == TickTypeEnum.VOLUME) and (size != -1):

            variables.volume[reqId] = size
        
        if (tickType == TickTypeEnum.OPTION_CALL_OPEN_INTEREST):
            # print(f"ReqID: {reqId} Call OI: {size}")
            variables.call_option_open_interest[reqId] = size

        if (tickType == TickTypeEnum.OPTION_PUT_OPEN_INTEREST):
            
            # print(f"ReqID: {reqId} Put OI: {size}")
            variables.put_option_open_interest[reqId] = size
        


    # Callback for reqMktData (BID, ASK)
    def tickPrice(
        self, reqId: TickerId, tickType: TickType, price: float, attrib: TickAttrib
    ):
        super().tickPrice(reqId, tickType, price, attrib)

        if variables.flag_debug_mode:
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

        # Trying update order status in DB if orderId is present in order_status DB
        try:

            # Last update time current time with timezone info
            last_update_time = datetime.datetime.now(variables.target_timezone_obj)

            # Query
            query_update_filled_qty = text(
                f"UPDATE `{variables.sql_table_order_status}` SET `Current Fill`= '{str(filled)}', \
                            `Avg Fill Price`= '{str(avgFillPrice)}', `Last Update Time`= '{str(last_update_time)}', `Status`= '{str(status)}' \
                             WHERE `Order ID` = '{str(orderId)}' "
            )

            # Executing query for active combo DB
            result_update_filled_qty = variables.active_sqlalchemy_connection.execute(
                query_update_filled_qty
            )

            # Sleeping
            time.sleep(variables.sleep_time_db)

        except:

            # Print to console
            print(
                f"Unable to update the Order Status in order_status table, Order ID: {orderId}"
            )

        # Print to console
        if variables.flag_debug_mode:
            print(
                "Inside orderStatus: Order Id:",
                orderId,
                "Status:",
                status,
                "Filled:",
                filled,
                "Remaining:",
                remaining,
                "LastFillPrice:",
                lastFillPrice,
                "\n",
            )

    # Callback for placeOrder
    def openOrder(self, orderId, contract, order, orderState):

        # Print to console
        if variables.flag_debug_mode:
            print(
                "Inside openOrder: OrderId:",
                orderId,
                "Symbol:",
                contract.symbol,
                "SecType:",
                contract.secType,
                "Exchange:",
                contract.exchange,
                "Action:",
                order.action,
                "OrderType:",
                order.orderType,
                "TotalQty:",
                order.totalQuantity,
                "CashQty:",
                order.cashQty,
                "LmtPrice:",
                order.lmtPrice,
                "AuxPrice:",
                order.auxPrice,
                "Status:",
                orderState.status,
                "\n",
            )

    # Callback for reqExecutions
    def execDetails(self, reqId: int, contract: Contract, execution: Execution):

        try:

            super().execDetails(reqId, contract, execution)

            # Current Time
            last_update_time = datetime.datetime.now(variables.target_timezone_obj)

            if variables.flag_debug_mode:
                print(
                    "ExecDetails. ReqId:",
                    reqId,
                    "Symbol:",
                    contract.symbol,
                    "SecType:",
                    contract.secType,
                    "Currency:",
                    "Order Id:",
                    execution.orderId,
                    contract.currency,
                    execution,
                )

            if execution.orderId in order_id_database():

                # Getting Target fill and Current Fill for order id from database
                query_target_fill = text(
                    f"SELECT `Target Fill`, `Current Fill` FROM `{variables.sql_table_order_status}` WHERE `Order ID` = '{execution.orderId}'"
                )
                result_target_fill = variables.active_sqlalchemy_connection.execute(
                    query_target_fill
                )

                results = result_target_fill.fetchone()

                # Getting Current fill for order id from database
                target_fill = int(results[0])
                current_fill = int(results[1])

                #  Update Current Fill IF Cum Qty > Current Fill
                if execution.cumQty > current_fill:

                    query_ins_target_fill = text(
                        "UPDATE `"
                        + str(variables.sql_table_order_status)
                        + "` SET `Current Fill`= "
                        + str(execution.cumQty)
                        + " WHERE `Order ID` = "
                        + str(execution.orderId)
                    )
                    variables.active_sqlalchemy_connection.execute(
                        query_ins_target_fill
                    )

                # Update if open position is filled
                if execution.cumQty == target_fill:

                    # Update total quantity filled, average fill price to database
                    query_ins_target_fill = text(
                        "UPDATE `"
                        + str(variables.sql_table_order_status)
                        + "` SET `Current Fill`= "
                        + str(target_fill)
                        + ",`Avg Fill Price`= "
                        + str(execution.avgPrice)
                        + ",`Status`= '"
                        + str("Filled")
                        + "',`Last Update Time`= '"
                        + str(last_update_time)
                        + "' WHERE `Order ID` = "
                        + str(execution.orderId)
                    )
                    variables.active_sqlalchemy_connection.execute(
                        query_ins_target_fill
                    )

                # Throw an Error when Cum Qty > Target Qty ->>>>>> "ERROR"
                if execution.cumQty > target_fill:
                    sys.exit("ERROR: Filled order qty > Target qty, exiting")

        except Exception as e:

            if variables.flag_debug_mode:
                print("Exception in execDetails")
                print(e)

    # Callback for reqExecutions
    def execDetailsEnd(self, reqId: int):
        super().execDetailsEnd(reqId)

        if variables.flag_debug_mode:
            print("Inside execDetailsEnd")

        variables.bool_execution_details = True

    # Tkinter
    def pressed_yes(self):
        variables.recovery_mode_input_tk = True
        self.window.destroy()

    def pressed_no(self):
        variables.recovery_mode_input_tk = False
        self.window.destroy()

    ############ Remove these  ##################

    # Callback for reqAccountUpdates
    def updateAccountValue(self, key, val, currency, accountName):

        # Print to console
        if variables.flag_debug_mode:
            print("Inside updateAccountValue: ", key, val, currency, accountName)

        # If key is NetLiquidationByCurrency
        if (
            key == "NetLiquidationByCurrency"
            and currency == variables.standard_currency_for_account_value
        ):

            try:

                # converting val to float
                val = float(val)

                # Update column value in df
                variables.accounts_table_dataframe.loc[
                    variables.accounts_table_dataframe["Account ID"] == accountName,
                    "Net Liquidity Value",
                ] = val

            except Exception as e:

                # Update column value in df
                variables.accounts_table_dataframe.loc[
                    variables.accounts_table_dataframe["Account ID"] == accountName,
                    "Net Liquidity Value",
                ] = "None"

        # If key is SMA
        if key == "SMA" and currency == variables.standard_currency_for_account_value:

            try:

                # converting val to float
                val = float(val)

                # Update column value in df
                variables.accounts_table_dataframe.loc[
                    variables.accounts_table_dataframe["Account ID"] == accountName,
                    "Special Memorandum Account",
                ] = round(val, 4)

            except Exception as e:

                # Update column value in df
                variables.accounts_table_dataframe.loc[
                    variables.accounts_table_dataframe["Account ID"] == accountName,
                    "Special Memorandum Account",
                ] = "None"

        # If key is FullExcessLiquidity
        if (
            key == "FullExcessLiquidity"
            and currency == variables.standard_currency_for_account_value
        ):

            try:

                # converting val to float
                val = float(val)

                # Update column value in df
                variables.accounts_table_dataframe.loc[
                    variables.accounts_table_dataframe["Account ID"] == accountName,
                    "Current Excess Liquidity",
                ] = round(val, 4)

            except Exception as e:

                # Update column value in df
                variables.accounts_table_dataframe.loc[
                    variables.accounts_table_dataframe["Account ID"] == accountName,
                    "Current Excess Liquidity",
                ] = "None"

        # If key is MaintMarginReq
        if (
            key == "MaintMarginReq"
            and currency == variables.standard_currency_for_account_value
        ):

            try:

                # converting val to float
                val = float(val)

                # Update column value in df
                variables.accounts_table_dataframe.loc[
                    variables.accounts_table_dataframe["Account ID"] == accountName,
                    "Utilised Margin",
                ] = round(val, 4)

            except Exception as e:

                # Update column value in df
                variables.accounts_table_dataframe.loc[
                    variables.accounts_table_dataframe["Account ID"] == accountName,
                    "Utilised Margin",
                ] = "None"

    # Callback for reqAccountUpdates, Indicates the end
    def accountDownloadEnd(self, accountName: str):

        # Print to console
        if variables.flag_debug_mode:
            print(f"AccountDownloadEnd. Account: {accountName}")

        # Cancel subscription
        # variables.app.reqAccountUpdates(False, accountName)

        # Set flag to true
        variables.flag_account_update_ended[accountName] = True

    # Callback for PNL
    def pnl(
        self, reqId: int, dailyPnL: float, unrealizedPnL: float, realizedPnL: float
    ):

        super().pnl(reqId, dailyPnL, unrealizedPnL, realizedPnL)
        # print("Daily PnL. ReqId:", reqId, "DailyPnL:", floatMaxString(dailyPnL), "UnrealizedPnL:", floatMaxString(unrealizedPnL), "RealizedPnL:", floatMaxString(realizedPnL))

        # Get account name
        account_name = variables.map_req_id_to_account_id[reqId]

        try:

            # Update column value in df
            variables.accounts_table_dataframe.loc[
                variables.accounts_table_dataframe["Account ID"] == account_name,
                "Day Profit and Loss",
            ] = round(dailyPnL, 4)

        except Exception as e:

            # Update column value in df
            variables.accounts_table_dataframe.loc[
                variables.accounts_table_dataframe["Account ID"] == account_name,
                "Day Profit and Loss",
            ] = "None"

        # check if reqid is in list
        if reqId in variables.pnl_single_req_ids:

            variables.pnl_single_req_ids.remove(reqId)

            # cancel subscription
            self.cancelPnL(reqId)

    # Callback for single PNL
    def pnlSingle(
        self,
        reqId: int,
        pos: float,
        dailyPnL: float,
        unrealizedPnL: float,
        realizedPnL: float,
        value: float,
    ):

        super().pnlSingle(reqId, pos, dailyPnL, unrealizedPnL, realizedPnL, value)

        # Get account id and con id
        account_id = variables.map_req_id_to_account_id_and_cond_id[reqId]["Account ID"]
        con_id = variables.map_req_id_to_account_id_and_cond_id[reqId]["Con ID"]

        # Init keys in dictionary if already not apresent in dict
        if account_id not in variables.map_account_id_and_con_id_to_pnl:

            variables.map_account_id_and_con_id_to_pnl[account_id] = {}

        if reqId in variables.pnl_single_req_ids:

            variables.pnl_single_req_ids.remove(reqId)

            # cancel subscription
            variables.app.cancelPnLSingle(reqId)

        # set value of pnl in dict mapped to account and conid
        variables.map_account_id_and_con_id_to_pnl[account_id][con_id] = floatMaxString(
            dailyPnL
        )

        # print(variables.map_account_id_and_con_id_to_pnl)

        # print(variables.map_account_id_and_con_id_to_pnl)

        # print("Daily PnL Single. ReqId:", reqId, "Position:", decimalMaxString(pos),"DailyPnL:", floatMaxString(dailyPnL), "UnrealizedPnL:", floatMaxString(unrealizedPnL),"RealizedPnL:", floatMaxString(realizedPnL), "Value:", floatMaxString(value), variables.map_req_id_to_account_id_and_cond_id[reqId])

    # Callback for position
    def position(
        self, account: str, contract: Contract, position: float, avgCost: float
    ):

        super().position(account, contract, position, avgCost)

        # Get reqID
        req_id = variables.nextorderId
        variables.nextorderId += 1

        # map req id to account id
        variables.map_req_id_to_account_id_and_cond_id[req_id] = {
            "Account ID": account,
            "Con ID": contract.conId,
        }

        if variables.flag_pnl_single:

            variables.pnl_single_req_ids.append(req_id)

            # Request PNL for con id mapped to account
            variables.app.reqPnLSingle(req_id, account, "", contract.conId)

        """print("Position.", "Account:", account, "Symbol:", contract.symbol, "SecType:",

        contract.secType, "Currency:", contract.currency,

        "Position:", decimalMaxString(position), "Avg cost:", floatMaxString(avgCost))"""

    # Callback for position end
    def positionEnd(self):
        variables.flag_pnl_single = False

        super().positionEnd()
        self.cancelPositions()
