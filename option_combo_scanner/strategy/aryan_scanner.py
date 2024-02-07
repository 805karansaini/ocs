import copy
from datetime import time

from com.contracts import get_contract, get_contract_details

from ibapi.contract import Contract
from option_combo_scanner.strategy.strategy_variables import StrategyVariables

class Scanner:
    
    # def __init__(self):
    def __init__(
        self,
    ):
        pass
        

    """
    Instrument: AAPL, STK, SMART
    DTE: 7

    Get Instrument and, Config [strategy_variable]
    base/underlying:
        contrac deatils
        contract
    """
    @staticmethod
    def get_instrument_from_variables():
        local_map_instrument_id_to_instrument_object = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object)
        return local_map_instrument_id_to_instrument_object

    @staticmethod
    def get_config_from_variables():
        local_config_object =  copy.deepcopy(StrategyVariables.config_object)
        return local_config_object

    @staticmethod
    def get_list_of_strikes_and_expiries(
            ticker, conid, underlying_sec_type, fop_trading_class, reqId=None
    ):

        # Get reqId
        if reqId == None:
            reqId = StrategyVariables.nextorderId
            StrategyVariables.nextorderId += 1
        else:
            reqId = reqId

        # Init
        # StrategyVariables.expiry_dates[reqId] = None
        # StrategyVariables.strike_prices[reqId] = None
        # StrategyVariables.map_reqid_to_trading_class_sec_def[reqId] = fop_trading_class
        # StrategyVariables.req_sec_def_end[reqId] = None
        # StrategyVariables.req_error[reqId] = False
        #
        # StrategyVariables.map_reqid_to_all_trading_class[reqId] = []

        # print(reqId, ticker, futFopExchange, underlying_sec_type, conid)
        # Fetching all the expiry and strikes for the ticker
        StrategyVariables.app.reqSecDefOptParams(
            reqId, ticker, underlying_sec_type, conid
        )

        # Timeout
        counter = 0

        # Wait for response from TWS
        while True:

            # Received Response, or request ended
            if (
                    (
                            (StrategyVariables.expiry_dates[reqId] is not None)
                            and (StrategyVariables.strike_prices[reqId] is not None)
                    )
                    or (StrategyVariables.req_sec_def_end[reqId] == True)
                    or (StrategyVariables.req_error[reqId] == True)
            ):

                # Print to console
                if StrategyVariables.flag_debug_mode:
                    print(
                        f"Successfully fetched all the Strike Price and Expiry Dates from TWS for {ticker} reqI: {reqId}"
                    )

                # Answer received successfully
                return (StrategyVariables.expiry_dates[reqId], StrategyVariables.strike_prices[reqId])

            else:

                # Timeout of 11 secs
                if counter >= int(11 / StrategyVariables.sleep_time_waiting_for_tws_response):

                    # Print to console
                    if StrategyVariables.flag_debug_mode:
                        print(
                            f"Could not fetch all the Strike Price and Expiry Dates from TWS for {ticker} reqI: {reqId}"
                        )

                    # Returning None
                    return (StrategyVariables.expiry_dates[reqId], StrategyVariables.strike_prices[reqId])

                if StrategyVariables.flag_debug_mode and (counter % 20 == 0):
                    print(
                        f"Waiting for the Strike Price and Expiry Dates response from TWS for {ticker} reqI: {reqId}"
                    )

                # Waiting for response
                time.sleep(StrategyVariables.sleep_time_waiting_for_tws_response)

                # Increasing counter
                counter += 1

    @staticmethod
    def get_underlying_contract_details(contract, req_id=None):

        if req_id is None:
            # Get reqId
            reqId = StrategyVariables.nextorderId
            StrategyVariables.nextorderId += 1
        else:
            # Get reqId
            reqId = req_id


        # Request contract details
        StrategyVariables.app.reqContractDetails(reqId, contract)



    # @staticmethod
    # def get_contract_from_limited_info(symbol=None, sec_type=None, exchange=None, currency=None):
    #     contract = Contract()
    #
    #     # Setting Values in contract
    #     if symbol is not None:
    #         contract.symbol = symbol
    #     if sec_type is not None:
    #         contract.secType = sec_type
    #     if exchange is not None:
    #         contract.exchange = exchange
    #     if currency is not None:
    #         contract.currency = currency
    #
    #     return contract
    @staticmethod
    def get_underlying_contract(instrument_obj):
        contract = Contract()
        contract.symbol = instrument_obj.symbol
        contract.secType = instrument_obj.sec_type
        contract.exchange = instrument_obj.exchange
        contract.currency = instrument_obj.currency
        print(contract)
        contract_details = Scanner.get_underlying_contract_details(contract)
        return contract

    @staticmethod
    def start_scanner():
        local_map_instrument_id_to_instrument_object = Scanner.get_instrument_from_variables()
        local_config_object = Scanner.get_config_from_variables()

        for instrument_id, instrument_object in local_map_instrument_id_to_instrument_object.items():
            # print(instrument_id)
            underlying_contract = Scanner.get_underlying_contract(instrument_object)
            if underlying_contract == None: continue
            else:
                con_id = underlying_contract.conId
            all_expiry, all_strike_ith = Scanner.get_list_of_strikes_and_expiries(
                instrument_object.symbol, con_id, instrument_object.sec_type, instrument_object.trading_class
            )
            print(underlying_contract)





