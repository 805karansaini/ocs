import copy
import heapq
import time
import traceback

from option_combo_scanner.indicators_calculator.helper_indicator import IndicatorHelper
from option_combo_scanner.indicators_calculator.historical_volatility import HistoricalVolatility
from option_combo_scanner.indicators_calculator.implied_volatility import ImpliedVolatility
from option_combo_scanner.indicators_calculator.put_call_vol import PutCallVol
from option_combo_scanner.strategy.min_heap import MinHeap
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

        # Create a secondary heap for Indicator
        secondary_min_heap_indicator: MinHeap = copy.deepcopy(StrategyVariables.primary_min_heap_indicators)

        # Run while heap is not empty
        while secondary_min_heap_indicator:
            # Get the indicator id from the heap
            current_item = secondary_min_heap_indicator.pop()
            _, indicator_id = current_item

            # if indicator id is not present, continue
            if indicator_id not in StrategyVariables.map_indicator_id_to_indicator_object:
                # print(f"Inside calculate_realtime_market_data_based_indicators could not find indicator id: {indicator_id}")
                continue

            # Get the unix time
            current_time_in_unix = int(time.time())

            # Updating the Primary Heap, for the current item, with new time
            new_item = (current_time_in_unix, indicator_id)
            StrategyVariables.primary_min_heap_indicators.update(current_item, new_item)

            # Get the indicator object
            indicator_object = copy.deepcopy(StrategyVariables.map_indicator_id_to_indicator_object[int(indicator_id)])
            instrument_id = indicator_object.instrument_id

            # Get all the strikes, so that we can create the FOP OPT contract, for which the below data is required(Strike, Delta, IV )
            if instrument_id not in StrategyVariables.map_instrument_id_to_instrument_object:
                # print(f"Inside calculate_realtime_market_data function could not find instrument id: {instrument_id}")
                continue

            # Local copy of the instrument object
            local_instrument_obj = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object[instrument_id])
            
            # CRITICAL CHANGE IND SUPPORT - START
            symbol = indicator_object.symbol
            expiry = indicator_object.expiry
            sec_type = local_instrument_obj.sec_type

            # Underlying SecType
            if sec_type.upper() == "OPT":
                underlying_sec_type = "STK"
            elif sec_type.upper() == "FOP":
                underlying_sec_type = "FUT"
            elif sec_type.upper() == "IND":
                underlying_sec_type = "IND"
            else:
                continue

            underlying_sec_type = underlying_sec_type 
            exchange = local_instrument_obj.exchange
            currency = local_instrument_obj.currency
            multiplier = local_instrument_obj.multiplier
            trading_class = local_instrument_obj.trading_class
            # CRITICAL CHANGE IND SUPPORT - END

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
            
            if StrategyVariables.flag_test_print:
                print(f"Underlying Contract: {underlying_contract}")
                print(f"All Strikes: {all_strikes}")
            
            # Can not compute the values for this indcator row continue  
            if underlying_contract is None or all_strikes is None:
                # print(f"Inside calculate_realtime_market_data_based_indicators getting for Underlying Contract: {underlying_contract}")
                continue

            try:
                if flag_realtime_indicators:
                    
                    # Calculate RealTime Market Data Based Indicators, and return call and put strikes for selected delta
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

                    if StrategyVariables.flag_put_call_indicator_based_on_selected_deltas_only == True and (
                        list_of_call_strike is None or list_of_put_strikes is None
                    ):
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
