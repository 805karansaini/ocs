import copy
import heapq
import traceback

from option_combo_scanner.indicators_calculator.helper_indicator import \
    IndicatorHelper
from option_combo_scanner.indicators_calculator.historical_volatility import \
    HistoricalVolatility
from option_combo_scanner.indicators_calculator.implied_volatility import \
    ImpliedVolatility
from option_combo_scanner.indicators_calculator.put_call_vol import PutCallVol
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


class IndicatorCalculation:
    def __init__(self):
        pass

    @staticmethod
    def calculate_realtime_market_data_based_indicators(flag_realtime_indicators):
        """
        Current: IVD1, IVD2, AvgIV,
        Current: RRD1, RRD2,
        RR(Chg-14D), RR(Chg-1D),
        AvgIV-Avg(14), AvgIV(Chg-1D),
        Current: Max & Min Pain
        Current: OI Support(Put) and OI Resistance(Call)
        Change Underlying/Options Price Today

        AvgIV is need for HV (minus) IV
        AvgIV(Chg-1D)<I.V. Change> is required for PC-Change/AvgIV(Chg-1D)
        """
        
        '''
        # All the indicator rows are unique data needs to be fethced for all, can not reduce the requests call
        local_map_indicator_id_to_indicator_object = copy.deepcopy(StrategyVariables.map_indicator_id_to_indicator_object)
        min_heap_for_indicator_cal = []
        current_time = datetime.datetime.now
        for indicator_id, indicator_object in local_map_indicator_id_to_indicator_object.items():
            min_heap_for_indicator_cal.append((-1, indicator_id))

        heapq.heapify(min_heap_for_indicator_cal)

        # Compute the value for each indicator id
        while min_heap_for_indicator_cal:
            _, indicator_id = min_heap_for_indicator_cal.heappop()
            push in some other heap which is in variable
            heapq.heappush(Orignal_heap, (-1, indicator_id))
            # Compute Indicator for indicator_id

        '''

        # All the indicator rows are unique data needs to be fethced for all, can not reduce the requests call
        local_map_indicator_id_to_indicator_object = copy.deepcopy(StrategyVariables.map_indicator_id_to_indicator_object)
            
        
        # Compute the value for each indicator id
        for (
            indicator_id,
            indicator_object,
        ) in local_map_indicator_id_to_indicator_object.items():

            # if the indictor was removed
            if indicator_id not in StrategyVariables.map_indicator_id_to_indicator_object:
                print(
                    f"Inside calculate_realtime_market_data_based_indicators could not find indicator id: {indicator_id}"
                )
                continue

            # Instrument ID
            instrument_id = indicator_object.instrument_id

            # Get all the strikes, so that we can create the FOP OPT contract, for which the below data is required(Strike, Delta, IV )
            if instrument_id not in StrategyVariables.map_instrument_id_to_instrument_object:
                print(f"Inside calculate_realtime_market_data function could not find instrument id: {instrument_id}")
                continue

            # Local copy of the instrument object
            local_instrument_obj = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object[instrument_id])

            symbol = indicator_object.symbol
            expiry = indicator_object.expiry
            sec_type = local_instrument_obj.sec_type
            underlying_sec_type = "STK" if sec_type.upper() == "OPT" else "FUT"
            exchange = local_instrument_obj.exchange
            currency = local_instrument_obj.currency
            multiplier = local_instrument_obj.multiplier
            trading_class = local_instrument_obj.trading_class

            underlying_contract, all_strikes = IndicatorHelper.get_underlying_contract_and_all_strikes(
                indicator_object,
                symbol,
                expiry,
                sec_type,
                underlying_sec_type,
                exchange,
                currency,
                multiplier,
                trading_class,
            )

            # Can not compute the values for this indcator row continue
            if underlying_contract is None or all_strikes is None:
                print(f"Inside calculate_realtime_market_data_based_indicators getting for Underlying Contract: {underlying_contract}")
                continue

            try:
                if flag_realtime_indicators:
                
                    list_of_call_strike, list_of_put_strikes = ImpliedVolatility.compute(
                        indicator_object,
                        symbol,
                        expiry,
                        sec_type,
                        underlying_sec_type,
                        exchange,
                        currency,
                        multiplier,
                        trading_class,
                        underlying_contract,
                        all_strikes,
                    )
                    if StrategyVariables.flag_put_call_indicator_based_on_selected_deltas_only == True and (list_of_call_strike is None or list_of_put_strikes is None):
                        print(
                            f"Inside calculate_realtime_market_data_based_indicators getting CallStrikes: {list_of_call_strike} PutStrikes {list_of_put_strikes}"
                        )
                        continue
                    else:
                        if StrategyVariables.flag_test_print:
                            print(f"Computing Put Call Volume based on (deltad1, deltad2, strikes) only")
                            print(f"List Of List of Call {list_of_call_strike} and Put {list_of_put_strikes}")

                    if StrategyVariables.flag_put_call_indicator_based_on_selected_deltas_only == True:
                        
                        PutCallVol.compute(
                            indicator_object,
                            symbol,
                            expiry,
                            sec_type,
                            underlying_sec_type,
                            exchange,
                            currency,
                            multiplier,
                            trading_class,
                            underlying_contract,
                            all_strikes,
                            True,
                            list_of_call_strike,
                            list_of_put_strikes,
                        )
                else:
                    # TODO- Remame
                    PutCallVol.compute(
                        indicator_object,
                        symbol,
                        expiry,
                        sec_type,
                        underlying_sec_type,
                        exchange,
                        currency,
                        multiplier,
                        trading_class,
                        underlying_contract,
                        all_strikes,
                    )
            except Exception as e:
                print()
                print(
                    f"Inside calculate_realtime_market_data_based_indicators: Failed to compute Indicator {e} \n Traceback: {traceback.print_exc()}"
                )

    @staticmethod
    def compute_indicators():

        # Historical Volatility, HV, HV(14-D)
        HistoricalVolatility.compute()

        # Current: IVD1, IVD2, AvgIV,
        # Current: RRD1, RRD2,
        # RR(Chg-14D), RR(Chg-1D),
        # AvgIV-Avg(14), AvgIV(Chg-1D),
        # Current: Max & Min Pain
        # Current: OI Support(Put) and OI Resistance(Call)
        # Change Underlying/Options Price Today

        # AvgIV is need for HV (minus) IV
        # AvgIV(Chg-1D)<I.V. Change> is required for PC-Change/AvgIV(Chg-1D)
        flag_realtime_indicators = True
        IndicatorCalculation.calculate_realtime_market_data_based_indicators(flag_realtime_indicators=flag_realtime_indicators)

        
        if not StrategyVariables.flag_put_call_indicator_based_on_selected_deltas_only:
            flag_realtime_indicators = False
            IndicatorCalculation.calculate_realtime_market_data_based_indicators(flag_realtime_indicators=flag_realtime_indicators)
