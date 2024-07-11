import inspect
import logging
import traceback

from ao_api.common import price_increment_from_json
from ao_api.contract import get_contract_details_obj, get_contract_obj
from ao_api.execution import json_to_algo_execution
from ao_api.message import IN
from ao_api.order import json_to_order, json_to_order_state
from ao_api.wrapper import *  # ignore: import

logger = logging.getLogger(__name__)


class HandleInfo:
    def __init__(self, wrap=None, proc=None):
        self.wrapperMeth = wrap
        self.wrapperParams = None
        self.processMeth = proc
        if wrap is None and proc is None:
            raise ValueError("both wrap and proc can't be None")

    def __str__(self):
        s = "wrap:%s meth:%s prms:%s" % (
            self.wrapperMeth,
            self.processMeth,
            self.wrapperParams,
        )
        return s


class Decoder:
    def __init__(self, wrapper):
        self.wrapper: EWrapper = wrapper
        self.discoverParams()

    def discoverParams(self):
        meth2handleInfo = {}
        for handleInfo in self.msgId2handleInfo.values():
            meth2handleInfo[handleInfo.wrapperMeth] = handleInfo

        methods = inspect.getmembers(EWrapper, inspect.isfunction)
        for _, meth in methods:
            # logger.debug("meth %s", name)
            sig = inspect.signature(meth)
            handleInfo = meth2handleInfo.get(meth, None)
            if handleInfo is not None:
                handleInfo.wrapperParams = sig.parameters

    def interpret(self, response_mssg):

        # Get response type
        response_type = response_mssg["response_type"]

        handleInfo = self.msgId2handleInfo.get(response_type, None)

        if handleInfo is None:
            print("no handleInfo", "response_mssg", response_mssg)
            # logger.debug("%s: no handleInfo", response_mssg)
            return

        try:
            # Call Wrapper Method here
            if handleInfo.wrapperMeth is not None:
                pass

                # TODO no method currently routed to the Ewrapper
                # logger.debug("In interpret(), handleInfo: %s", handleInfo)
                # self.interpretWithSignature(response_mssg, handleInfo)

            # Call ProcessMethod/Decoder Method
            elif handleInfo.processMeth is not None:
                handleInfo.processMeth(self, response_mssg)

        except Exception as e:
            print(f"Decorder Interpret error: request_id: {response_mssg['request_id']}, error: {e}")
            # TODO - Check
            # theBadMsg = ",".join(response_mssg)
            # self.wrapper.error(
            #     NO_VALID_ID, BAD_MESSAGE.code(), BAD_MESSAGE.msg() + theBadMsg
            # )
            # raise

    def process_error_msg(self, response_mssg):

        reqId = response_mssg["request_id"]
        error_code = response_mssg.get("error_code", None)
        error_msg = response_mssg.get("error_msg", None)
        advance_order_reject_json = response_mssg.get("advance_order_reject_json", None)

        self.wrapper.error(reqId, error_code, error_msg, advance_order_reject_json)

    def process_warning_msg(self, response_mssg):

        reqId = response_mssg["request_id"]
        warning_msg = response_mssg.get("warning_msg", None)
        self.wrapper.warning(reqId, warning_msg)

    def process_historical_data_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            itemCount = response_mssg["result"]

            for bar in itemCount:
                self.wrapper.historical_data(reqId, bar)
        except Exception as e:
            print(f"Error in process_historical_data_msg: {e} Traceback: {traceback.format_exc()}")
            
    def process_historical_data_end_msg(self, response_mssg):

        try:
            reqId = response_mssg["request_id"]
            self.wrapper.historical_data_end(
                reqId,
            )
        except Exception as e:
            print("Error in process_historical_data_end_msg", e, traceback.format_exc())

    def process_option_contracts_data_msg(self, response_mssg):

        try:
            reqId = response_mssg["request_id"]
            itemCount = response_mssg["result"]

            for option_contract in itemCount:
                underlyingConId = option_contract["underlyingConId"]
                exchange = option_contract["exchange"]
                trading_class = option_contract["trading_class"]
                multiplier = option_contract["multiplier"]
                expirations = set(option_contract["expirations"])
                strikes = set(option_contract["strikes"])
                self.wrapper.option_contracts_data(reqId, underlyingConId, exchange, trading_class, multiplier, expirations, strikes)

        except Exception as e:
            print("Error in process_tick_price_msg", e)

    def process_option_contracts_data_end_msg(self, response_mssg):

        try:
            reqId = response_mssg["request_id"]
            self.wrapper.option_contracts_data_end(
                reqId,
            )
        except Exception as e:
            print(e)

    def process_tick_price_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for data in results:
                tick_type = data["tick_type"]
                price = data["price"]

                self.wrapper.tick_price(reqId, tick_type, price)
        except Exception as e:
            print("Error in process_tick_price_msg", e)

    def process_tick_size_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for data in results:
                tick_type = data["tick_type"]
                size = data["size"]

                self.wrapper.tick_size(reqId, tick_type, size)
        except Exception as e:
            print("Error in process_tick_size_msg", e)

    def process_tick_option_computation_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for data in results:
                tick_type = data["tick_type"]
                delta = data["delta"]
                gamma = data["gamma"]
                vega = data["vega"]
                theta = data["theta"]
                iv = data["iv"]

                self.wrapper.tick_option_computation(
                    reqId, tick_type, delta, gamma, vega, theta, iv
                )
        except Exception as e:
            print("Error in process_tick_option_computation_msg", e)

    def process_tick_generic_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for data in results:
                tick_type = data["tick_type"]
                value = data["value"]

                self.wrapper.tick_generic(reqId, tick_type, value)
        except Exception as e:
            print("Error in process_tick_generic_msg", e)

    def process_market_snapshot_end_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            self.wrapper.market_snapshot_end(reqId)
        except Exception as e:
            print("Error in process_market_snapshot_end_msg", e)

    def process_contract_details_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                contract_details = get_contract_details_obj(res)
                self.wrapper.contract_details(reqId, contract_details)
        except Exception as e:
            print("Error in process_contract_details_msg", e)

    def process_contract_details_end_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            self.wrapper.contract_details_end(reqId)
        except Exception as e:
            print(e)

    def process_order_status_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                status = res["status"]
                filled = res["filled"]
                remaining = res["remaining"]
                avg_fill_price = res["avg_fill_price"]
                last_fill_price = res["last_fill_price"]
                why_held = res["why_held"]
                mkt_cap_price = res["mkt_cap_price"]
                self.wrapper.order_status(reqId, status, filled, remaining, avg_fill_price, last_fill_price, why_held, mkt_cap_price)
        except Exception as e:
            print(e)

    def process_open_order_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                contract = get_contract_obj(res["contract"])
                order = json_to_order(res["order"])
                order_state = json_to_order_state(res["order_state"])
                self.wrapper.open_order(reqId, contract, order, order_state)
        except Exception as e:
            print(e)

    def process_executions_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                contract = get_contract_obj(res["contract"])
                execution = json_to_algo_execution(res["execution"])
                self.wrapper.executions(reqId, contract, execution)
        except Exception as e:
            print(e)

    def process_executions_end_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            self.wrapper.executions_end(reqId)
        except Exception as e:
            print(e)

    def process_positions_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                account = res["account"]
                contract = get_contract_obj(res["contract"])
                position = res["position"]
                avg_cost = res["avg_cost"]
                self.wrapper.positions(reqId, account, contract, position, avg_cost)
        except Exception as e:
            print(e)

    def process_positions_end_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            self.wrapper.positions_end(reqId)
        except Exception as e:
            print(e)

    def process_request_id_msg(self, response_mssg):
        try:
            # reqId = response_mssg["request_id"]
            results = response_mssg["result"]
            self.wrapper.next_valid_request_id(results[0]["request_id"])
        except Exception as e:
            print(f"Error in process_request_id_msg: {e}")

    def process_all_accounts_data_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                readAccountsList = res["readAccountsList"]
                writeAccountsList = res["writeAccountsList"]
                self.wrapper.all_accounts_data(
                    reqId, readAccountsList, writeAccountsList
                )
        except Exception as e:
            print(f"Error in process_all_account_data_msg: {e}")

    def process_managed_accounts_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                readAccountsList = res["readAccountsList"]
                writeAccountsList = res["writeAccountsList"]
                self.wrapper.managed_accounts(
                    reqId, readAccountsList, writeAccountsList
                )
        except Exception as e:
            print(f"Error in process_managed_accounts_msg: {e}")

    def process_account_updates_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                key = res["key"]
                val = res["val"]
                currency = res["currency"]
                account = res["account"]
                self.wrapper.account_updates(reqId, key, val, currency, account)
        except Exception as e:
            print(e)

    def process_account_updates_end_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                account = res["account"]
                self.wrapper.account_updates_end(reqId, account)
        except Exception as e:
            print(e)

    def process_pnl_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                daily_pnl = res["daily_pnl"]
                unrealized_pnl = res["unrealized_pnl"]
                realized_pnl = res["realized_pnl"]
                self.wrapper.pnl(reqId, daily_pnl, unrealized_pnl, realized_pnl)
        except Exception as e:
            print(e)

    def process_pnl_single_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                pos = res["pos"]
                daily_pnl = res["daily_pnl"]
                unrealized_pnl = res["unrealized_pnl"]
                realized_pnl = res["realized_pnl"]
                value = res["value"]
                self.wrapper.pnl_single(reqId, pos, daily_pnl, unrealized_pnl, realized_pnl, value)
        except Exception as e:
            print(e)

    def process_market_rule_msg(self, response_mssg):
        try:
            reqId = response_mssg["request_id"]
            results = response_mssg["result"]

            for res in results:
                market_rule_id = res["market_rule_id"]
                price_increments = []
                for price_increment in res["price_increments"]:
                    price_increments.append(price_increment_from_json(price_increment))
                self.wrapper.market_rule(reqId, market_rule_id, price_increments)
        except Exception as e:
            print(e)

    msgId2handleInfo = {
        IN.ERR_MSG: HandleInfo(proc=process_error_msg),
        IN.WARNING_MSG: HandleInfo(proc=process_warning_msg),
        IN.HISTORICAL_DATA: HandleInfo(proc=process_historical_data_msg),
        IN.HISTORICAL_DATA_END: HandleInfo(proc=process_historical_data_end_msg),
        IN.OPTION_CONTRACTS_DATA: HandleInfo(proc=process_option_contracts_data_msg),
        IN.OPTION_CONTRACTS_DATA_END: HandleInfo(
            proc=process_option_contracts_data_end_msg
        ),
        IN.TICK_OPTION_COMPUTATION: HandleInfo(
            proc=process_tick_option_computation_msg
        ),
        IN.TICK_PRICE: HandleInfo(proc=process_tick_price_msg),
        IN.TICK_SIZE: HandleInfo(proc=process_tick_size_msg),
        IN.MARKET_SNAPSHOT_END: HandleInfo(proc=process_market_snapshot_end_msg),
        IN.CONTRACT_DETAILS: HandleInfo(proc=process_contract_details_msg),
        IN.CONTRACT_DETAILS_END: HandleInfo(proc=process_contract_details_end_msg),
        IN.ORDER_STATUS: HandleInfo(proc=process_order_status_msg),
        IN.OPEN_ORDER: HandleInfo(proc=process_open_order_msg),
        IN.EXECUTIONS: HandleInfo(proc=process_executions_msg),
        IN.EXECUTIONS_END: HandleInfo(proc=process_executions_end_msg),
        IN.POSITIONS: HandleInfo(proc=process_positions_msg),
        IN.POSITIONS_END: HandleInfo(proc=process_positions_end_msg),
        IN.REQUEST_ID: HandleInfo(proc=process_request_id_msg),
        IN.ALL_ACCOUNTS_DATA: HandleInfo(proc=process_all_accounts_data_msg),
        IN.MANAGED_ACCOUNTS: HandleInfo(proc=process_managed_accounts_msg),
        IN.ACCOUNT_UPDATES: HandleInfo(proc=process_account_updates_msg),
        IN.ACCOUNT_UPDATES_END: HandleInfo(proc=process_account_updates_end_msg),
        IN.PNL: HandleInfo(proc=process_pnl_msg),
        IN.PNL_SINGLE: HandleInfo(proc=process_pnl_single_msg),
        IN.MARKET_RULE: HandleInfo(proc=process_market_rule_msg),
        IN.TICK_GENERIC: HandleInfo(proc=process_tick_generic_msg),
    }
