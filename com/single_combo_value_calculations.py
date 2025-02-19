import threading
from com.variables import *
from com.high_low_price_calculator import HighLowCalculator
from com.volume_and_change_related_columns import VolumeRelated
from com.high_low_cal_helper import update_price_based_relative_indicators_values


# Method to calculate all indicator values for single combo
def single_combo_values(combination_obj, unique_id):
    try:
        # reset counter
        variables.counter_filter_condition = 0

        high_low_price_obj = HighLowCalculator()
        volumne_related_values_obj = VolumeRelated()

        # Buy legs and Sell legs
        buy_legs = combination_obj.buy_legs
        sell_legs = combination_obj.sell_legs
        all_legs = buy_legs + sell_legs

        con_id_list = [leg_obj.con_id for leg_obj in all_legs]

        high_low_price_obj.update_long_term_values(
            conid_list=con_id_list, unique_id_added=unique_id
        )

        high_low_price_obj.update_intraday_values(
            conid_list=con_id_list, unique_id_added=unique_id
        )

        high_low_price_obj.calculate_hv_related_columns(
            conid_list=con_id_list, unique_id_added=unique_id
        )

        volumne_related_values_obj.update_volume_related_fields(
            conid_list=con_id_list, unique_id_added=unique_id
        )

        volumne_related_values_obj.get_volume_magnet_tiestamps(
            conid_list=con_id_list, unique_id_added=unique_id
        )

        update_price_based_relative_indicators_values(
            conid_list=con_id_list, unique_id_added=unique_id
        )

        high_low_price_obj.calculate_atr_for_order(
            conid_list=con_id_list, unique_id_added=unique_id
        )

        high_low_price_obj.get_last_candle_for_order(
            conid_list=con_id_list, unique_id_added=unique_id
        )

        # reset counter
        variables.counter_filter_condition = 10**10

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Exception inside 'single_combo_values', Exp: {e} ")
