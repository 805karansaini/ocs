import pandas as pd
import tabulate

from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


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

    @staticmethod
    def find_the_strike_delta_iv_tuple(
        current_underlying_price,
        right: str,
        time_to_expiration: float,
        dataframe_with_current_mkt_data: pd.DataFrame,  # Righ C / P only
        list_of_target_deltas: list,
    ):
        """
        DF must have Bid and Ask (menaing no nan value)
        BS for the Strike, its Delta and IV  given the list of target delta and time_to_expiration
        return [ tuple(Strike, Delta, IV)]
        list_of_target_deltas should sorted
        """
        if right == "Put":
            list_of_target_deltas = [-1 * _ for _ in list_of_target_deltas]

        list_of_all_strikes = list(dataframe_with_current_mkt_data["Strike"])
        temp = (dataframe_with_current_mkt_data["Bid"] + dataframe_with_current_mkt_data["Ask"]) / 2
        list_of_all_strike_premium = list(temp)

        N = len(list_of_all_strikes)
        list_of_calculated_delta = [None] * N
        list_of_calculated_iv = [None] * N

        for target_delta in list_of_target_deltas:
            (
                list_of_calculated_delta,
                list_of_calculated_iv,
            ) = BinarySearchDeltaIV.custom_binary_search(
                current_underlying_price,
                right,
                time_to_expiration,
                list_of_all_strikes,
                list_of_all_strike_premium,
                list_of_calculated_delta,
                list_of_calculated_iv,
                target_delta,
            )

            '''
            Karan Supressed prints
            print(f"Target Delta: {target_delta}")
            # Create a pandas DataFrame
            df_temp = pd.DataFrame(
                {f"Strikes: ": list_of_all_strikes, f"{right} Delta": list_of_calculated_delta, f"{right} IV": list_of_calculated_iv}
            )

            # Print the DataFrame using tabulate
            print(tabulate.tabulate(df_temp, headers="keys", tablefmt="psql"))
            '''

        # Cal Delta, Indx computed delta, iv
        list_of_strike_delta_iv_tuple = [(None, None, None) for _ in list_of_target_deltas]

        for indx, (strike, delta, iv) in enumerate(zip(list_of_all_strikes, list_of_calculated_delta, list_of_calculated_iv)):
            if delta is not None and iv is not None:
                for i, target_delta in enumerate(list_of_target_deltas):
                    if list_of_strike_delta_iv_tuple[i] == (None, None, None):
                        list_of_strike_delta_iv_tuple[i] = (strike, delta, iv)
                    else:
                        old_strike, old_delta, old_iv = list_of_strike_delta_iv_tuple[i]

                        if abs(target_delta - old_delta) > abs(target_delta - delta):
                            list_of_strike_delta_iv_tuple[i] = (strike, delta, iv)

        return list_of_strike_delta_iv_tuple

    @staticmethod
    def custom_binary_search(
        current_underlying_price,
        option_right,
        time_to_expiration,
        list_of_all_strikes,
        list_of_all_strike_premium,
        list_of_calculated_delta,
        list_of_calculated_iv,
        target_delta,
    ):
        """
        Delta is always decreasing
        """

        left = 0
        right = len(list_of_all_strikes) - 1

        while left <= right:
            mid = (left + right) // 2

            strike = list_of_all_strikes[mid]
            market_premium = list_of_all_strike_premium[mid]
            # if value of delta already exists for the given strike, do binary search
            if list_of_calculated_delta[mid] is not None and list_of_calculated_delta[mid] == target_delta:
                return mid
            # Move current delta is greater than target delta, we need to decrease the delta
            # Delta is always decreasing, move to right handside
            elif list_of_calculated_delta[mid] is not None and list_of_calculated_delta[mid] > target_delta:
                left = mid + 1
            # Move current delta is lower than target delta, we need to increase the delta
            # Delta is always decreasing, move to left handside
            elif list_of_calculated_delta[mid] is not None and list_of_calculated_delta[mid] < target_delta:
                right = mid - 1
            elif list_of_calculated_delta[mid] == float("NaN"):
                right = mid - 1
            else:
                # Mid Delta, IV is not computed so compte it
                calucalted_delta, calucalted_iv = Utils.get_delta(
                    current_underlying_price,
                    StrategyVariables.riskfree_rate1,
                    0,
                    time_to_expiration,
                    float(strike),
                    market_premium,
                    option_right,
                )
                # Store in Array
                list_of_calculated_delta[mid] = calucalted_delta
                list_of_calculated_iv[mid] = calucalted_iv

        return list_of_calculated_delta, list_of_calculated_iv
