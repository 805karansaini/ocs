import asyncio
import copy
import datetime
import pprint
import time

import numpy as np
import pandas as pd
from tabulate import tabulate

from com.contracts import get_contract
from com.option_comobo_scanner_idetif import (
    find_closest_expiry_for_fop_given_fut_expiries_and_trading_class,
    find_nearest_expiry_and_all_strikes_for_stk_given_dte,
    find_nearest_expiry_for_future_given_fut_dte)
# from com import variables
from com.variables import variables
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.greeks import \
    get_underlying_implied_volatility_and_cmp
from option_combo_scanner.indicators_calculator.historical_data_fetcher import \
    HistoricalDataFetcher
from option_combo_scanner.indicators_calculator.historical_volatility import \
    HistoricalVolatility
from option_combo_scanner.indicators_calculator.market_data_fetcher import \
    MarketDataFetcher
from option_combo_scanner.indicators_calculator.put_call_vol import PutCallVol
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


class ChangeUnderlyingOptionsPrice :
    scanner_indicator_tab_chgopt_obj = None

    def __init__(self):
        pass

    @staticmethod
    def get_strike_and_closet_expiry_for_fop(
        symbol,
        dte,
        underlying_sec_type,
        exchange,
        currency,
        multiplier,
        trading_class,
    ):
        """
        Function used to get the
        list of all the available strikes
        and closest expiry for FOP sec_type

        """
        print(
            "IV: trying to get all_exp",
            symbol,
            dte,
            underlying_sec_type,
            exchange,
            currency,
            multiplier,
            trading_class,
        )

        # only call once (not for N-DTEs)
        all_fut_expiries = find_nearest_expiry_for_future_given_fut_dte(
            symbol,
            dte,
            underlying_sec_type,
            exchange,
            currency,
            multiplier,
            trading_class="",
            only_want_all_expiries=True,
        )

        # Handling None
        if all_fut_expiries == None:
            return None, None, None

        # get closest FOP Expiry for given Trading class
        (
            all_strikes,
            closest_expiry_date,
            underlying_conid,
        ) = find_closest_expiry_for_fop_given_fut_expiries_and_trading_class(
            symbol,
            dte,
            underlying_sec_type,
            exchange,
            currency,
            multiplier,
            trading_class,
            all_fut_expiries,
        )

        return all_strikes, closest_expiry_date, underlying_conid


    @staticmethod
    def get_strike_and_closet_expiry_for_opt(
        symbol,
        dte,
        underlying_sec_type,
        exchange,
        currency,
        multiplier,
        trading_class,
    ):
        """
        Function used to get the
        list of all the available strikes
        and closest expiry for OPT sec_type

        """
        (all_expiry_dates_ticker, all_strikes, closest_expiry_date, underlying_conid) = find_nearest_expiry_and_all_strikes_for_stk_given_dte(
            ticker=symbol,
            days_to_expiry=dte,
            underlying_sec_type=underlying_sec_type,
            exchange=exchange,
            currency=currency,
            multiplier=multiplier,
            fop_trading_class="",
        )

        if all_strikes is not None:

            # Removing  {  }
            all_strikes = [float(_) for _ in all_strikes[1:-1].split(",")]

            all_strikes = sorted(all_strikes)

        return all_strikes, closest_expiry_date

    @staticmethod
    def compute():
        
        # Map indicator id to indicator object
        local_map_indicator_id_to_indicator_object = copy.deepcopy(StrategyVariables.map_indicator_id_to_indicator_object)
        

        for (
            indicator_id,
            indicator_object,
        ) in local_map_indicator_id_to_indicator_object.items():

            # if the indictor was removed
            if indicator_id not in StrategyVariables.map_indicator_id_to_indicator_object:
                continue

            instrument_id = indicator_object.instrument_id

            # If instrument not present continue
            if instrument_id not in StrategyVariables.map_instrument_id_to_instrument_object:
                continue

            local_instrument_obj = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object[instrument_id])

            # get the indicator_object data 
            symbol = indicator_object.symbol
            expiry = indicator_object.expiry
            sec_type = local_instrument_obj.sec_type
            underlying_sec_type = "STK" if sec_type == "OPT" else "FUT"
            exchange = local_instrument_obj.exchange
            currency = local_instrument_obj.currency
            multiplier = local_instrument_obj.multiplier
            trading_class = local_instrument_obj.trading_class

            # Get the current date for calcluating dte
            current_date_for_dte = datetime.datetime.today().strftime("%Y%m%d")
            current_date_obj_for_dte = datetime.datetime.strptime(current_date_for_dte, "%Y%m%d")
            expiry_date_obj_for_dte = datetime.datetime.strptime(expiry, "%Y%m%d")
            
            dte = abs(current_date_obj_for_dte - expiry_date_obj_for_dte).days
        
            # Get the all strikes and closest expiry for the sec_type
            if underlying_sec_type == "FUT":
                all_strikes, closest_expiry_date, underlying_conid = ChangeUnderlyingOptionsPrice.get_strike_and_closet_expiry_for_fop(
                    indicator_object.symbol,
                    dte,
                    underlying_sec_type,
                    exchange,
                    currency,
                    int(multiplier),
                    trading_class,
                )

                
                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=exchange,
                    currency=currency,
                    multiplier=multiplier,
                    con_id=underlying_conid,
                )

            elif underlying_sec_type == "STK":
                all_strikes, closest_expiry_date = ChangeUnderlyingOptionsPrice.get_strike_and_closet_expiry_for_opt(
                    symbol,
                    dte,
                    underlying_sec_type,
                    exchange,
                    currency,
                    multiplier,
                    trading_class,
                )
                # print(all_strikes)
                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=exchange,
                    currency=currency,
                    multiplier=1,
                )
            else:
                continue
            
            
            # Calcluate the current price for today
            bid_ask_price_tuple = asyncio.run(MarketDataFetcher.get_current_price_for_contract(underlying_contract))

            if bid_ask_price_tuple[0] and bid_ask_price_tuple[1]:
                current_price_today = (bid_ask_price_tuple[0] + bid_ask_price_tuple[1]) / 2
            else:
                # TODO - ARYAN HANDLE ERRROR - Please give reason/try to understand this part 
                current_price_today = None

            

            # Fetch the historical Data for the underlyings
            list_of_req_ids_for_volume = ChangeUnderlyingOptionsPrice.fetch_historical_data(
                    [underlying_contract], StrategyVariables.bar_size_chg_underlying_price, StrategyVariables.lookback_days_chg_underlying_price
                )
            # Get the dataframe for the underlying and calculate the price today morning and 14 days ago

            for req_id in list_of_req_ids_for_volume:    
                df = variables.map_req_id_to_historical_data_dataframe[req_id]
                open_price_today_morning = None
                open_price_14_days_ago_morning = None
                if not df.empty:
                    # df.to_csv(f'Temp/{underlying_contract.symbol}_1.csv')
                    df['Time'] = pd.to_datetime(df['Time'])
                    df_sorted = df.sort_values(by='Time')
                    earliest_timestamps = {}

                    # Iterate through the DataFrame and select the earliest timestamp for each date
                    for index, row in df_sorted.iterrows():
                        date = row['Time'].date()
                        if date not in earliest_timestamps:
                            earliest_timestamps[date] = row['Time']

                    # Extract 'Open' data for the earliest timestamp of the current date
                    latest_date = df_sorted['Time'].dt.date.max()
                    
                    for date, timestamp in earliest_timestamps.items():
                        if date == latest_date:
                            open_price_today_morning = df_sorted.loc[df_sorted['Time'] == timestamp, 'Close'].iloc[0]
                            break

                    # Extract 'Open' data for the earliest timestamp of the date 14 days ago
                    date_14_days_ago = latest_date - datetime.timedelta(days=14)

                    for date, timestamp in earliest_timestamps.items():
                        if date == date_14_days_ago:
                            open_price_14_days_ago_morning = df_sorted.loc[df_sorted['Time'] == timestamp, 'Close'].iloc[0]
                            break
                else:
                    pass
                                    

            
            
            # Flow to calculte the filtered option strike create contracts based on D1 and D2
            
            list_of_rights = ["CALL", "PUT"]

            for right in list_of_rights:

                list_of_all_option_contracts = []
                
        
                for strike in all_strikes:

                    list_of_all_option_contracts.append(
                        get_contract(
                            symbol=symbol,
                            sec_type=sec_type,
                            multiplier=multiplier,
                            exchange=exchange,
                            currency=currency,
                            right=right,
                            strike_price=strike,
                            expiry_date=expiry,
                            trading_class=trading_class,
                        )
                    )

                
                generic_tick_list = ""
                snapshot = False
                # Fetch Data for all the  Contracts
                list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = asyncio.run(
                    MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                        list_of_all_option_contracts, True, generic_tick_list=generic_tick_list, snapshot=snapshot
                    )
                )

                data = []
                
                for contract, (delta, iv_ask, iv_bid, iv_last, bid_price, ask_price, call_oi, put_oi) in zip(
                    list_of_all_option_contracts, list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple
                ):
                    # print("calloi and put_oi", call_oi, put_oi)
                    
                    data.append(
                        {
                            "Strike": float(contract.strike),
                            "Delta": (delta),
                        }
                    )
                # print(data)

                target_deltas = [StrategyVariables.delta_d1_indicator_input, StrategyVariables.delta_d2_indicator_input]

                # Initialize variables to store the closest strikes and deltas
                closest_strikes = {target_delta: None for target_delta in target_deltas}


                # Iterate through the data and find strikes nearest to the desired deltas
                for item in data:
                    strike = item["Strike"]
                    delta = item["Delta"]
                    
                    if delta is not None:
                        for target_delta in target_deltas:
                            # If closest strike is not set or if current strike is closer to target delta
                            if closest_strikes[target_delta] is None or abs(delta - target_delta) < abs(closest_strikes[target_delta] - target_delta):
                                closest_strikes[target_delta] = strike
                    else:
                        pass
                        # print(f"Delta not available for strike {strike}. Skipping...")
                # Print the strikes nearest to desired deltas
                # print(closest_strikes)
            
            unique_strikes = set(closest_strikes.values())

            filtered_closest_strikes = list(unique_strikes)
            # list_of_rights = ["CALL", "PUT"]

            # Flow to get the filtered option contract
            for right in list_of_rights:
                list_of_filtered_option_contracts = []
                # print(filtered_closest_strikes)
                for filtered_strike in filtered_closest_strikes:

                    list_of_filtered_option_contracts.append(
                        get_contract(
                            symbol=symbol,
                            sec_type=sec_type,
                            multiplier=multiplier,
                            exchange=exchange,
                            currency=currency,
                            right=right,
                            strike_price=filtered_strike,
                            expiry_date=expiry,
                            trading_class=trading_class,
                        )
                    )
                
                
                
                bid_ask_tuple = asyncio.run(
                    MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                        list_of_filtered_option_contracts, True, generic_tick_list=generic_tick_list, snapshot=snapshot
                    )
                )
                for contract, (delta, iv_ask, iv_bid, iv_last, bid_price, ask_price, call_oi, put_oi) in zip(
                    list_of_filtered_option_contracts, bid_ask_tuple
                ):
                    
                    if ask_price and bid_price:
                        current_option_price = (ask_price + bid_price)/ 2
                    else:
                        current_option_price = None
                
                # NEW DF STRIKE DELTA IV SIR
                # GET STRIKE by filter on this new DF
                # NEW list_of_filtered_option_contracts
   
                # Fetch historical data for filtered contract
                list_of_req_ids_for_volume = ChangeUnderlyingOptionsPrice.fetch_historical_data(
                    list_of_filtered_option_contracts, StrategyVariables.bar_size_chg_underlying_price, StrategyVariables.lookback_days_chg_underlying_price
                )
                # Get the option price today morning from the datafrmae
                for req_id, contract in zip(list_of_req_ids_for_volume, list_of_filtered_option_contracts):
                        
                    df = variables.map_req_id_to_historical_data_dataframe[req_id]
                    # print(df.to_string())
                    open_option_price_today_morning = None
                    if not df.empty:
                        
                        df['Time'] = pd.to_datetime(df['Time'])
                        df_sorted = df.sort_values(by='Time')
                        earliest_timestamps = {}

                        # Iterate through the DataFrame and select the earliest timestamp for each date
                        for index, row in df_sorted.iterrows():
                            date = row['Time'].date()
                            if date not in earliest_timestamps:
                                earliest_timestamps[date] = row['Time']

                        # Extract 'Open' data for the earliest timestamp of the current date
                        latest_date = df_sorted['Time'].dt.date.max()
                        
                        for date, timestamp in earliest_timestamps.items():
                            if date == latest_date:
                                open_option_price_today_morning = df_sorted.loc[df_sorted['Time'] == timestamp, 'Close'].iloc[0]
                                break
                
                    else:
                        pass

            # Modified new sir code
            # Flow to ge the filtered strike based on D1 and D2 and use black scholes to get strike      
            for right in list_of_rights:

                list_of_all_option_contracts_14d=[]

                for strike in all_strikes:
                    # Here we are creating list of all option contract
                    list_of_all_option_contracts_14d.append(

                        get_contract(
                            symbol=symbol,
                            sec_type=sec_type,
                            multiplier=multiplier,
                            exchange=exchange,
                            currency=currency,
                            right=right,
                            strike_price=strike,
                            expiry_date=expiry,
                            trading_class=trading_class,
                        )
                    )

                
                generic_tick_list = ""
                snapshot = False
                
                # Fetch Data for all the  Contracts will only use bid ask for market prem.

                list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = asyncio.run(
                    MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                        list_of_all_option_contracts_14d, True, generic_tick_list=generic_tick_list, snapshot=snapshot
                    )
                )

            

                data_for_all_contract_to_get_nearest_strike = []
                for contract, (delta, iv_ask, iv_bid, iv_last, bid_price, ask_price, call_oi, put_oi) in zip(
                    list_of_all_option_contracts_14d, list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple
                ):
                    
                    data_for_all_contract_to_get_nearest_strike.append(
                        {
                            "Strike": float(contract.strike),
                            "Delta": None,
                        }
                    )

                    # print(data_for_all_contract_to_get_nearest_strike)
                    if all([ask_price, bid_price]):
                        
                        market_premium = (ask_price + bid_price)/ 2

                        current_date = datetime.datetime.today().strftime("%Y%m%d")
                        current_date_obj = datetime.datetime.strptime(current_date, "%Y%m%d")
                        
                        expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")
                        time_to_expiration = (abs(expiry_date_obj - current_date_obj).days + 14)/365

                        # getting the delta for the strike from black scholes
                        black_scholes_delta, black_scholes_iv = Utils.get_delta(
                                current_price_today,
                                StrategyVariables.riskfree_rate1,
                                0,
                                time_to_expiration,
                                float(contract.strike),
                                market_premium,
                                right,
                            )

                        # storing the delta and strike for all the option contract
                        data_for_all_contract_to_get_nearest_strike[-1]['Delta'] = black_scholes_delta
                        
                
                # print(f"list of all delta strike", data_for_all_contract_to_get_nearest_strike)
                target_deltas = [StrategyVariables.delta_d1_indicator_input, StrategyVariables.delta_d2_indicator_input]

                # Initialize variables to store the closest strikes
                closest_strikes_14d = {target_delta: None for target_delta in target_deltas}


                # Iterate through the data and find strikes nearest to the desired deltas
                for item in data_for_all_contract_to_get_nearest_strike:
                    strike = item["Strike"]
                    delta = item["Delta"]
                    
                    if delta is not None:
                        for target_delta in target_deltas:
                            # If closest strike is not set or if current strike is closer to target delta
                            if closest_strikes_14d[target_delta] is None or abs(delta - target_delta) < abs(closest_strikes_14d[target_delta] - target_delta):
                                closest_strikes_14d[target_delta] = strike
                    else:
                        pass
                        # print(f"Delta not available for strike {strike}. Skipping...")
                # Print the strikes nearest to desired deltas
            # print(closest_strikes_14d)
            unique_strikes = set(closest_strikes_14d.values())

            filtered_closest_strikes_14d = list(unique_strikes)
            # list_of_rights = ["CALL", "PUT"]

            # Create Option Contract for the filtered strikes (Black Scholes Model) and get the historical data
            for right in list_of_rights:
                list_of_filtered_option_contracts_14d = []
                # print(filtered_closest_strikes)
                for filtered_strike in filtered_closest_strikes_14d:

                    list_of_filtered_option_contracts_14d.append(
                        get_contract(
                            symbol=symbol,
                            sec_type=sec_type,
                            multiplier=multiplier,
                            exchange=exchange,
                            currency=currency,
                            right=right,
                            strike_price=filtered_strike,
                            expiry_date=expiry,
                            trading_class=trading_class,
                        )
                    )

                # Fetch the Historical Data
                list_of_req_ids_for_volume = ChangeUnderlyingOptionsPrice.fetch_historical_data(
                    list_of_filtered_option_contracts_14d, StrategyVariables.bar_size_chg_underlying_price, StrategyVariables.lookback_days_chg_underlying_price
                )

                for req_id, contract in zip(list_of_req_ids_for_volume, list_of_filtered_option_contracts_14d):
                        
                    df = variables.map_req_id_to_historical_data_dataframe[req_id]
                    # df.to_csv(f'Temp/{contract.symbol}_{contract.right}_3.csv')
                    close_option_price_14_days_ago_morning = None
                    if not df.empty:
                        
                        df['Time'] = pd.to_datetime(df['Time'])
                        df_sorted = df.sort_values(by='Time')
                        earliest_timestamps = {}

                        # Iterate through the DataFrame and select the earliest timestamp for each date
                        for index, row in df_sorted.iterrows():
                            date = row['Time'].date()
                            if date not in earliest_timestamps:
                                earliest_timestamps[date] = row['Time']

                        # Extract 'Open' data for the earliest timestamp of the date 14 days ago
                        latest_date = df_sorted['Time'].dt.date.max()
                        date_14_days_ago = latest_date - datetime.timedelta(days=14)
                        # print("dd", date_14_days_ago)
                        
                        for date, timestamp in earliest_timestamps.items():
                            if date == date_14_days_ago:
                                close_option_price_14_days_ago_morning = df_sorted.loc[df_sorted['Time'] == timestamp, 'Close'].iloc[0]
                                break
                
                    else:
                        pass

            if open_price_today_morning:
                print(open_price_today_morning)
            if current_price_today:
                print(current_price_today)
            if open_price_14_days_ago_morning:
                print(open_price_14_days_ago_morning)
            if current_option_price:
                print(current_option_price)
            if close_option_price_14_days_ago_morning:
                print(close_option_price_14_days_ago_morning)

            # print(open_price_today_morning, current_price_today, open_price_14_days_ago_morning, current_option_price, close_option_price_14_days_ago_morning)
            if open_price_today_morning and current_price_today:
                """Change in Underlying Today"""
                change_underlying_price = ((current_price_today - open_price_today_morning)/open_price_today_morning)*100
            if open_price_14_days_ago_morning and current_price_today:
                """Change in Underlying 14days"""
                change_underlying_price_14d = current_price_today - open_price_14_days_ago_morning

            """Change Option Price Today"""

            if current_option_price and open_option_price_today_morning:
                change_option_price = ((current_option_price - open_option_price_today_morning)/open_option_price_today_morning)*100
                if change_option_price != 0:
                    Change_underlying_options_price_today = change_underlying_price/change_option_price
                else:
                    Change_underlying_options_price_today = 0
            else:
                Change_underlying_options_price_today = None
            
            print("Indicator 1 Today", Change_underlying_options_price_today)

            if current_option_price and close_option_price_14_days_ago_morning and change_underlying_price_14d:
                change_option_price_14d = current_option_price - close_option_price_14_days_ago_morning
                if change_option_price_14d != 0:
                    chg_uderlying_opt_price_14d = change_underlying_price_14d/change_option_price_14d
                else:
                    chg_uderlying_opt_price_14d = None
            else:
                chg_uderlying_opt_price_14d = None

            print("Indicator 2 14d", chg_uderlying_opt_price_14d)
                    
            ChangeUnderlyingOptionsPrice.update_hv_calculation(indicator_id, Change_underlying_options_price_today, chg_uderlying_opt_price_14d)
                



                

                
    @staticmethod
    def update_hv_calculation(indicator_id, Change_underlying_options_price_today, chg_uderlying_opt_price_14d):
        
        values_dict = {'Change_underlying_options_price_today': Change_underlying_options_price_today,
                       'chg_uderlying_opt_price_14d': chg_uderlying_opt_price_14d,                       
                    }
        where_condition = f" WHERE `indicator_id` = {indicator_id};"

        select_query = SqlQueries.create_update_query(
            table_name="indicator_table",
            values_dict=values_dict,
            where_clause=where_condition,
        )
        # Get all the old rows from indicator table
        res = SqlQueries.execute_update_query(select_query)
        
        if not res:
            print(f'Change Underlying values not updated in DB', {indicator_id})
            # return

        if indicator_id in StrategyVariables.map_indicator_id_to_indicator_object:
            StrategyVariables.map_indicator_id_to_indicator_object[indicator_id].Change_underlying_options_price_today = Change_underlying_options_price_today
            StrategyVariables.map_indicator_id_to_indicator_object[indicator_id].chg_uderlying_opt_price_14d = chg_uderlying_opt_price_14d
            
            

            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"] == indicator_id,
                "Change_underlying_options_price_today",
            ] = Change_underlying_options_price_today
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"] == indicator_id,
                "chg_uderlying_opt_price_14d",
            ] = chg_uderlying_opt_price_14d
            

        else:
            print(f"Indicator object not found for indicator_id: {indicator_id}")

        # print(StrategyVariables.scanner_indicator_table_df.to_string())
        ChangeUnderlyingOptionsPrice.scanner_indicator_tab_chgopt_obj.update_into_indicator_table(StrategyVariables.scanner_indicator_table_df)

    @staticmethod
    def fetch_historical_data(list_of_all_option_contracts, bar_size, duration_size):

        # List of all request ids TODO 
        list_of_req_ids_for_volume = []
        
        for contract in list_of_all_option_contracts:
            
            # TODO 
            what_to_show = "BID"

            # Getting req_id
            reqId = variables.cas_app.nextorderId
            variables.cas_app.nextorderId += 1

            # Send the request
            HistoricalDataFetcher.request_historical_data_for_contract(
                contract, bar_size, duration_size, what_to_show, reqId
            )
            

            # Map TODO map list of reqid to volume
            list_of_req_ids_for_volume.append(reqId)
        
        counter = 0
        while variables.cas_wait_time_for_historical_data > (
            counter * variables.sleep_time_waiting_for_tws_response
        ):

            # KARAN CHANGED IT - TODO - 20231027
            if all(
                [
                    variables.req_mkt_data_end[req_id] or variables.req_error[req_id]
                    for req_id in list_of_req_ids_for_volume
                ]
            ):
                break

            # Sleep for sleep_time_waiting_for_tws_response
            time.sleep(variables.sleep_time_waiting_for_tws_response)

            # Increase Counter
            counter += 1
        
        return list_of_req_ids_for_volume
