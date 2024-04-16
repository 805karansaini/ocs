import copy
import time

import pandas as pd
import tabulate

from com.variables import variables
from option_combo_scanner.cache.data_store import DataStore
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.indicators_calculator.historical_data_fetcher import \
    HistoricalDataFetcher
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
from option_combo_scanner.strategy.utilities import StrategyUtils


class BinarySearchDeltaIV:
    def __init__(self) -> None:
        pass

    """
    current_date = datetime.datetime.today().strftime("%Y%m%d")
    current_date_obj = datetime.datetime.strptime(current_date, "%Y%m%d")

    expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")
    time_to_expiration = abs(current_date_obj - expiry_date_obj).days

    time_to_expiration = (time_to_expiration + i) / 365
    """

    # @staticmethod
    # def find_the_strike_delta_iv_tuple(
    #     current_underlying_price,
    #     right: str,
    #     time_to_expiration: float,
    #     dataframe_with_current_mkt_data: pd.DataFrame,  # Righ C / P only
    #     list_of_target_deltas: list,
    # ):
    #     """
    #     DF must have Bid and Ask (menaing no nan value)
    #     BS for the Strike, its Delta and IV  given the list of target delta and time_to_expiration
    #     return [ tuple(Strike, Delta, IV)]
    #     list_of_target_deltas should sorted
    #     """
    #     if right == "Put":
    #         list_of_target_deltas = [-1 * _ for _ in list_of_target_deltas]

    #     list_of_all_strikes = list(dataframe_with_current_mkt_data["Strike"])
    #     temp = (dataframe_with_current_mkt_data["Bid"] + dataframe_with_current_mkt_data["Ask"]) / 2
    #     list_of_all_strike_premium = list(temp)

    #     N = len(list_of_all_strikes)
    #     list_of_calculated_delta = [None] * N
    #     list_of_calculated_iv = [None] * N

    #     for target_delta in list_of_target_deltas:
    #         (
    #             list_of_calculated_delta,
    #             list_of_calculated_iv,
    #         ) = BinarySearchDeltaIV.custom_binary_search(
    #             current_underlying_price,
    #             right,
    #             time_to_expiration,
    #             list_of_all_strikes,
    #             list_of_all_strike_premium,
    #             list_of_calculated_delta,
    #             list_of_calculated_iv,
    #             target_delta,
    #         )

    #         '''
    #         Karan Supressed prints
    #         print(f"Target Delta: {target_delta}")
    #         # Create a pandas DataFrame
    #         df_temp = pd.DataFrame(
    #             {f"Strikes: ": list_of_all_strikes, f"{right} Delta": list_of_calculated_delta, f"{right} IV": list_of_calculated_iv}
    #         )

    #         # Print the DataFrame using tabulate
    #         print(tabulate.tabulate(df_temp, headers="keys", tablefmt="psql"))
    #         '''

    #     # Cal Delta, Indx computed delta, iv
    #     list_of_strike_delta_iv_tuple = [(None, None, None) for _ in list_of_target_deltas]

    #     for indx, (strike, delta, iv) in enumerate(zip(list_of_all_strikes, list_of_calculated_delta, list_of_calculated_iv)):
    #         if delta is not None and iv is not None:
    #             for i, target_delta in enumerate(list_of_target_deltas):
    #                 if list_of_strike_delta_iv_tuple[i] == (None, None, None):
    #                     list_of_strike_delta_iv_tuple[i] = (strike, delta, iv)
    #                 else:
    #                     old_strike, old_delta, old_iv = list_of_strike_delta_iv_tuple[i]

    #                     if abs(target_delta - old_delta) > abs(target_delta - delta):
    #                         list_of_strike_delta_iv_tuple[i] = (strike, delta, iv)

    #     return list_of_strike_delta_iv_tuple

    # @staticmethod
    # def custom_binary_search(
    #     current_underlying_price,
    #     option_right,
    #     time_to_expiration,
    #     list_of_all_strikes,
    #     list_of_all_strike_premium,
    #     list_of_calculated_delta,
    #     list_of_calculated_iv,
    #     target_delta,
    # ):
    #     """
    #     Delta is always decreasing
    #     """

    #     left = 0
    #     right = len(list_of_all_strikes) - 1

    #     while left <= right:
    #         mid = (left + right) // 2
    #         strike = list_of_all_strikes[mid]
    #         market_premium = list_of_all_strike_premium[mid]

    #         # if value of delta already exists for the given strike, do binary search
    #         if list_of_calculated_delta[mid] is not None and list_of_calculated_delta[mid] == target_delta:
    #             return mid
    #         # Move current delta is greater than target delta, we need to decrease the delta
    #         # Delta is always decreasing, move to right handside
    #         elif list_of_calculated_delta[mid] is not None and list_of_calculated_delta[mid] > target_delta:
    #             left = mid + 1
    #         # Move current delta is lower than target delta, we need to increase the delta
    #         # Delta is always decreasing, move to left handside
    #         elif list_of_calculated_delta[mid] is not None and list_of_calculated_delta[mid] < target_delta:
    #             right = mid - 1
    #         elif list_of_calculated_delta[mid] == float("NaN"):
    #             right = mid - 1
    #         else:
    #             # Get Option Price Here

    #             # Mid Delta, IV is not computed so compte it
    #             calucalted_delta, calucalted_iv = Utils.get_delta(
    #                 current_underlying_price,
    #                 StrategyVariables.riskfree_rate1,
    #                 0,
    #                 time_to_expiration,
    #                 float(strike),
    #                 market_premium,
    #                 option_right,
    #             )
    #             # Store in Array
    #             list_of_calculated_delta[mid] = calucalted_delta
    #             list_of_calculated_iv[mid] = calucalted_iv

    #     return list_of_calculated_delta, list_of_calculated_iv

    @staticmethod
    def find_the_strike_delta_iv_tuple(
        underlying_price,
        right: str,
        time_to_expiration: float,
        list_of_all_contracts: list,  # Righ C / P only
        list_of_target_deltas: list,
        target_date, # pd.dt.date
    ):
        """
        BS for the Strike, its Delta and IV  given the list of target delta and time_to_expiration
        return [ tuple(Strike, Delta, IV)]
        list_of_target_deltas should sorted
        """
        if right == "Put":
            list_of_target_deltas = [-1 * _ for _ in list_of_target_deltas]

        # Cal Delta, Indx computed delta, iv
        list_of_strike_delta_iv_tuple = [(None, None, None) for _ in list_of_target_deltas]

        for i, target_delta in enumerate(list_of_target_deltas):
            (
                list_of_new_contracts,
                map_strike_to_calculated_delta,
                map_strike_to_calculated_iv,
            ) = BinarySearchDeltaIV.custom_binary_search(
                underlying_price,
                right,
                time_to_expiration,
                list_of_all_contracts,
                target_delta,
                target_date,
            )

            """
            Karan Supressed prints
            print(f"Target Delta: {target_delta}")
            # Create a pandas DataFrame
            df_temp = pd.DataFrame(
                {f"Strikes: ": list_of_all_strikes, f"{right} Delta": list_of_calculated_delta, f"{right} IV": list_of_calculated_iv}
            )

            # Print the DataFrame using tabulate
            print(tabulate.tabulate(df_temp, headers="keys", tablefmt="psql"))
            """

            temp_list_of_strike = [float(contract.strike) for contract in list_of_new_contracts]
            # print(f"TargetDate: {target_date} Right: {right} Target Delta: {target_delta}")
            # print(f"List of Strikes: {temp_list_of_strike}")
            # print(f"Map Strike to Calculated Delta: {map_strike_to_calculated_delta}")
            # print(f"Map Strike to Calculated IV: {map_strike_to_calculated_iv}")

            for strike in temp_list_of_strike:
                if strike in map_strike_to_calculated_delta and map_strike_to_calculated_delta[strike] is not None and map_strike_to_calculated_iv[strike] is not None:
                    delta = map_strike_to_calculated_delta[strike]
                    iv = map_strike_to_calculated_iv[strike]

                    if list_of_strike_delta_iv_tuple[i] == (None, None, None):
                        list_of_strike_delta_iv_tuple[i] = (strike, delta, iv)
                    else:
                        old_strike, old_delta, old_iv = list_of_strike_delta_iv_tuple[i]

                        if abs(target_delta - old_delta) > abs(target_delta - delta):
                            list_of_strike_delta_iv_tuple[i] = (strike, delta, iv)

        return list_of_strike_delta_iv_tuple

    @staticmethod
    def custom_binary_search(
        underlying_price,
        option_right,
        time_to_expiration,
        list_of_all_contracts,
        target_delta,
        target_date,
    ):
        """
        Delta is always decreasing
        """
        list_of_all_contracts = copy.deepcopy(list_of_all_contracts)
        map_strike_to_calculated_delta = {}
        map_strike_to_calculated_iv = {}

        left = 0
        right = len(list_of_all_contracts) - 1

        while left <= right:
            # Mid index
            mid = (left + right) // 2

            # Strike
            contract = list_of_all_contracts[mid]
            strike = float(contract.strike)

            # if value of delta already exists for the given strike, do binary search
            if strike in map_strike_to_calculated_delta and map_strike_to_calculated_delta[strike] == target_delta:
                break
            # Move current delta is greater than target delta, we need to decrease the delta
            # Delta is always decreasing, move to right handside
            elif strike in map_strike_to_calculated_delta and map_strike_to_calculated_delta[strike] > target_delta:
                left = mid + 1
            # Move current delta is lower than target delta, we need to increase the delta
            # Delta is always decreasing, move to left handside
            elif strike in map_strike_to_calculated_delta and map_strike_to_calculated_delta[strike] < target_delta:
                right = mid - 1
            elif strike in map_strike_to_calculated_delta and map_strike_to_calculated_delta[strike] == float("NaN"):
                # Delete the index from the list:
                del list_of_all_contracts[mid]

                # Reset the left and right
                left = 0
                right = len(list_of_all_contracts) - 1
            else:
                # Key for DataStore, get the data
                key = BinarySearchDeltaIV.get_key_from_contract(contract)
                data_frame = DataStore.get_data(key)

                # Get Option Price Here
                opt_premium = BinarySearchDeltaIV.get_historical_data_for_opt(target_date, contract, data_frame)
                # print(f"Date: {target_date} {key}: {opt_premium}")

                if opt_premium is None:
                    # Delete the index from the list, Reset the left and right
                    del list_of_all_contracts[mid]
                    left = 0
                    right = len(list_of_all_contracts) - 1
                    continue
                
                # print(f"         Date: {target_date} UnderlyingPrice: {underlying_price} TTE: {time_to_expiration} {option_right} {strike} Premium: {opt_premium}")
                # Mid Delta, IV is not computed so compte it
                calucalted_delta, calucalted_iv = Utils.get_delta(
                    underlying_price,
                    StrategyVariables.riskfree_rate1,
                    0,
                    time_to_expiration,
                    float(strike),
                    opt_premium,
                    option_right,
                )

                # Store in Array
                map_strike_to_calculated_delta[strike] = calucalted_delta
                map_strike_to_calculated_iv[strike] = calucalted_iv

                # print(f"Date: {target_date} Strike: {strike} Delta: {calucalted_delta} IV: {calucalted_iv} Indx: {mid}")
        
        return list_of_all_contracts, map_strike_to_calculated_delta, map_strike_to_calculated_iv

    @staticmethod
    def get_historical_data_for_opt(target_date, contract, data_frame=None):

        # Get the historical data for the contract and the target date
        if data_frame is not None:
            temp_data_frame = data_frame.copy()
            temp_data_frame["Date"] = pd.to_datetime(temp_data_frame["Time"]).dt.date

            if target_date in temp_data_frame["Date"].unique():
                target_df = temp_data_frame[temp_data_frame["Date"] == target_date]
                take_last_close = target_df["Close"].iloc[-1] if not target_df.empty else None
            else:
                take_last_close = None
            return take_last_close

        # If the data is not present in the data store, fetch the data from the IBKR
        what_to_show_price = "BID"
        bar_size_price = StrategyVariables.historical_price_data_bar_size
        duration_size_price = f"{StrategyVariables.avg_iv_lookback_days} D"

        contract_reqid_price = HistoricalDataFetcher.fetch_historical_data_for_list_of_contracts(
            [contract], bar_size_price, [duration_size_price], what_to_show_price
        )

        req_id = contract_reqid_price[0]
        contract_df = variables.map_req_id_to_historical_data_dataframe[req_id]

        key = BinarySearchDeltaIV.get_key_from_contract(contract)
        
        # If flag is True store CSV Files
        if StrategyVariables.flag_store_csv_files:
            folder_name = f"DeltaIV\{contract.symbol}_{contract.right}_{contract.tradingClass}"
            file_name = rf"{key}"
            StrategyUtils.save_option_combo_scanner_csv_file(contract_df, folder_name, file_name)

        DataStore.store_data(key, contract_df)

        contract_df["Date"] = pd.to_datetime(contract_df["Time"]).dt.date

        if target_date in contract_df["Date"].unique():
            target_df = contract_df[contract_df["Date"] == target_date]
            take_last_close = target_df["Close"].iloc[-1] if not target_df.empty else None
        else:
            take_last_close = None
        return take_last_close

    @staticmethod
    def get_key_from_contract(contract):
        right = contract.right.lower()
        key_string = f"{contract.symbol}_{contract.lastTradeDateOrContractMonth}_{contract.strike}_{contract.secType}_{right}_{contract.multiplier}_{contract.tradingClass}".lower()

        return key_string

    @staticmethod
    def get_historical_data_for_list_of_contracts_and_store_in_data_store(list_of_contracts,):

        N = len(list_of_contracts)

        # If the data is not present in the data store, fetch the data from the IBKR
        what_to_show_price = "BID"
        bar_size_price = StrategyVariables.historical_price_data_bar_size
        duration_size_price = f"{StrategyVariables.avg_iv_lookback_days} D"
        list_of_duration_size = [duration_size_price] * N

        list_of_req_id_for_historical_data = HistoricalDataFetcher.fetch_historical_data_for_list_of_contracts(
            list_of_contracts, bar_size_price, list_of_duration_size, what_to_show_price
        )

        for req_id, contract in zip(list_of_req_id_for_historical_data, list_of_contracts):
            contract_df = variables.map_req_id_to_historical_data_dataframe[req_id]
            key = BinarySearchDeltaIV.get_key_from_contract(contract)
        
            # If flag is True store CSV Files
            if StrategyVariables.flag_store_csv_files:
                folder_name = f"DeltaIV\{contract.symbol}_{contract.right}_{contract.tradingClass}"
                file_name = rf"{key}"
                StrategyUtils.save_option_combo_scanner_csv_file(contract_df, folder_name, file_name)

            DataStore.store_data(key, contract_df)
