import datetime
from pprint import pprint

import pandas as pd

from com.contracts import get_contract
from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import \
    StrategyVariables as strategy_variables

logger = CustomLogger.logger


class Indicator:
    def __init__(self, data):
        self.indicator_id = data.get("indicator_id", None)
        self.instrument_id = data.get("instrument_id", None)
        self.underlying_conid = data.get("underlying_conid", None)
        self.symbol = data.get("symbol", None)
        self.sec_type = data.get("sec_type", None)
        self.expiry = data.get("expiry", None)
        self.multiplier = data.get("multiplier", None)
        self.exchange = data.get("exchange", None)
        self.trading_class = data.get("trading_class", None)

        self.current_underlying_hv_value = data.get("current_underlying_hv_value", None)
        self.average_underlying_hv_over_n_days = data.get("average_underlying_hv_over_n_days", None)
        self.absoulte_change_in_underlying_over_n_days = data.get("absoulte_change_in_underlying_over_n_days", None)
        self.absoulte_change_in_underlying_over_one_day = data.get("absoulte_change_in_underlying_over_one_day", None)
        self.percentage_change_in_underlying_over_n_days = data.get("percentage_change_in_underlying_over_n_days", None)

        self.current_iv_d1 = data.get("current_iv_d1", None)
        self.current_iv_d2 = data.get("current_iv_d2", None)
        self.current_avg_iv = data.get("current_avg_iv", None)
        self.absolute_change_in_avg_iv_since_yesterday = data.get("absolute_change_in_avg_iv_since_yesterday", None)
        self.percentage_change_in_avg_iv_since_yesterday = data.get("percentage_change_in_avg_iv_since_yesterday", None)
        self.avg_iv_over_n_days = data.get("avg_iv_over_n_days", None)

        self.current_rr_d1 = data.get("current_rr_d1", None)
        self.current_rr_d2 = data.get("current_rr_d2", None)
        self.percentage_change_in_rr_since_yesterday_d1 = data.get("percentage_change_in_rr_since_yesterday_d1", None)
        self.percentage_change_in_rr_since_yesterday_d2 = data.get("percentage_change_in_rr_since_yesterday_d2", None)
        self.percentage_change_in_rr_since_14_day_d1 = data.get("percentage_change_in_rr_since_14_day_d1", None)
        self.percentage_change_in_rr_since_14_day_d2 = data.get("percentage_change_in_rr_since_14_day_d2", None)

        self.max_pain_strike = data.get("max_pain_strike", None)
        self.min_pain_strike = data.get("min_pain_strike", None)
        self.oi_support_strike = data.get("oi_support_strike", None)
        self.oi_resistance_strike = data.get("oi_resistance_strike", None)

        self.chg_in_call_opt_price_since_yesterday_d1 = data.get("chg_in_call_opt_price_since_yesterday_d1", None)
        self.chg_in_call_opt_price_since_yesterday_d2 = data.get("chg_in_call_opt_price_since_yesterday_d2", None)
        self.chg_in_put_opt_price_since_yesterday_d1 = data.get("chg_in_put_opt_price_since_yesterday_d1", None)
        self.chg_in_put_opt_price_since_yesterday_d2 = data.get("chg_in_put_opt_price_since_yesterday_d2", None)

        self.chg_in_call_opt_price_since_nth_day_d1 = data.get("chg_in_call_opt_price_since_nth_day_d1", None)
        self.chg_in_call_opt_price_since_nth_day_d2 = data.get("chg_in_call_opt_price_since_nth_day_d2", None)
        self.chg_in_put_opt_price_since_nth_day_d1 = data.get("chg_in_put_opt_price_since_nth_day_d1", None)
        self.chg_in_put_opt_price_since_nth_day_d2 = data.get("chg_in_put_opt_price_since_nth_day_d2", None)

        self.put_call_volume_ratio_current_day = data.get("put_call_volume_ratio_current_day", None)
        self.put_call_volume_ratio_average_over_n_days = data.get("put_call_volume_ratio_average_over_n_days", None)
        self.absolute_pc_change_since_yesterday = data.get("absolute_pc_change_since_yesterday", None)

        self.currency = "USD"
        self.indicator_id = int(self.indicator_id)
        self.instrument_id = int(self.instrument_id)
        self.underlying_conid = int(self.underlying_conid)
        self.map_indicator_id_to_indicator_object()

    def __str__(self) -> str:
        attributes_str = ", ".join([f"{key}={value}" for key, value in vars(self).items()])
        return f"Indicator: {attributes_str}"

    def update_attr_value(self, values_dict):
        """
        Change value of an attribute of this class
        """
        for key, value in values_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                # TODO - ARYAN
                logger.error(
                    f"Inside Indicator Object : {self.indicator_id} '{key}' is not an attribute of this class. new value: {value}"
                )

    def remove_indicator_from_system(self):

        # Drop rows where "Indicator ID" matches self.indicator_id
        # strategy_variables.scanner_indicator_table_df = strategy_variables.scanner_indicator_table_df.drop(
        #     strategy_variables.scanner_indicator_table_df[
        #         strategy_variables.scanner_indicator_table_df["Indicator ID"] == self.indicator_id
        #     ].index
        # )

        # Reset index if needed
        # strategy_variables.scanner_indicator_table_df.reset_index(drop=True, inplace=True)

        del strategy_variables.map_indicator_id_to_indicator_object[self.indicator_id]

    def map_indicator_id_to_indicator_object(self):

        # Assigning the current object to the 'indicator_object' variable within the 'strategy_variables'
        strategy_variables.map_indicator_id_to_indicator_object[self.indicator_id] = self
        
        # Used by the Impact Calculation
        strategy_variables.map_instrument_to_indicator_id[self.instrument_id] = self.indicator_id

        # # Create DataFrame
        # row = pd.DataFrame([self.get_tuple()], columns=strategy_variables.indicator_columns, index=[0],)

        # # Add Row to dataframe (concat)
        # strategy_variables.scanner_indicator_table_df = pd.concat(
        #     [strategy_variables.scanner_indicator_table_df, row],
        #     ignore_index=True,
        # )

        # TODO - Comment

        # Check if the underlying contract ID is not already present in the map
        if self.underlying_conid not in strategy_variables.map_con_id_to_contract:
            # Underlying SecType
            underlying_sec_type = "FUT" if self.sec_type == "FOP" else "STK"

            # Create an underlying contract
            underlying_contract = get_contract(
                self.symbol,
                underlying_sec_type,
                "SMART" if underlying_sec_type == "STK" else self.exchange,
                self.currency,
                multiplier=self.multiplier,
                con_id=self.underlying_conid,
            )
            
            #  Add the underlying contract to the map with its contract ID as the key

            strategy_variables.map_con_id_to_contract[self.underlying_conid] = underlying_contract

    def get_tuple(self):
        
        # LastAllowedTime: CurrentTime - CacheTime, Permissible time for the indicator cache        
        indicator_cache_time_in_seconds: int = strategy_variables.indicator_cache_time_in_seconds
        current_time = datetime.datetime.now(variables.target_timezone_obj)
        last_allowed_time =  current_time - datetime.timedelta(seconds=indicator_cache_time_in_seconds)

        # Decode the values
        current_underlying_hv_value = self.decode_value(self.current_underlying_hv_value, last_allowed_time)
        current_avg_iv = self.decode_value(self.current_avg_iv, last_allowed_time)

        # Computation H.V-I.V
        if current_underlying_hv_value and current_avg_iv:
            current_hv_minus_iv = round(current_underlying_hv_value - current_avg_iv, 2)
        else:
            current_hv_minus_iv = None

        # Decode the values
        absolute_pc_change_since_yesterday = self.decode_value(self.absolute_pc_change_since_yesterday, last_allowed_time)
        absolute_change_in_avg_iv_since_yesterday = self.decode_value(self.absolute_change_in_avg_iv_since_yesterday, last_allowed_time)

        # Calclute PC Change/IV Change
        if (
            absolute_pc_change_since_yesterday
            and absolute_change_in_avg_iv_since_yesterday
            and absolute_change_in_avg_iv_since_yesterday != 0
        ):
            pc_change_iv_change = round(absolute_pc_change_since_yesterday / absolute_change_in_avg_iv_since_yesterday, 2)
        else:
            pc_change_iv_change = None
        
        absoulte_change_in_underlying_over_n_days = self.decode_value(self.absoulte_change_in_underlying_over_n_days, last_allowed_time)
        absoulte_change_in_underlying_over_one_day = self.decode_value(self.absoulte_change_in_underlying_over_one_day, last_allowed_time)
        # Calculate Chg Underlying/Chg Option Price
        res = []

        for val_ in [
            self.decode_value(self.chg_in_call_opt_price_since_yesterday_d1, last_allowed_time),
            self.decode_value(self.chg_in_call_opt_price_since_yesterday_d2, last_allowed_time),
            self.decode_value(self.chg_in_put_opt_price_since_yesterday_d1, last_allowed_time),
            self.decode_value(self.chg_in_put_opt_price_since_yesterday_d2, last_allowed_time),
        ]:

            if val_ and val_ != 0 and absoulte_change_in_underlying_over_one_day:
                res.append(round(absoulte_change_in_underlying_over_one_day / val_, 2))
            else:
                res.append(None)


        for val_ in [
            self.decode_value(self.chg_in_call_opt_price_since_nth_day_d1, last_allowed_time),
            self.decode_value(self.chg_in_call_opt_price_since_nth_day_d2, last_allowed_time),
            self.decode_value(self.chg_in_put_opt_price_since_nth_day_d1, last_allowed_time),
            self.decode_value(self.chg_in_put_opt_price_since_nth_day_d2, last_allowed_time),
        ]:

            if val_ and val_ != 0 and absoulte_change_in_underlying_over_n_days:
                res.append(round(absoulte_change_in_underlying_over_n_days / val_, 2))
            else:
                res.append(None)
        if strategy_variables.flag_test_print:
            print(f"Indicator ID: {self.indicator_id}, Chg Underlying/Chg Opt Price: {res}")

        tup = [
            self.indicator_id,
            self.instrument_id,
            self.symbol,
            self.sec_type,
            self.expiry,
            
            # Decode Values
            current_underlying_hv_value,
            self.decode_value(self.average_underlying_hv_over_n_days, last_allowed_time),
            self.decode_value(self.absoulte_change_in_underlying_over_n_days, last_allowed_time),
            self.decode_value(self.percentage_change_in_underlying_over_n_days, last_allowed_time),
            current_hv_minus_iv,

            self.decode_value(self.current_iv_d1, last_allowed_time),
            self.decode_value(self.current_iv_d2, last_allowed_time),
            current_avg_iv,
            self.decode_value(self.absolute_change_in_avg_iv_since_yesterday, last_allowed_time),
            self.decode_value(self.percentage_change_in_avg_iv_since_yesterday, last_allowed_time),
            
            self.decode_value(self.avg_iv_over_n_days, last_allowed_time),
            self.decode_value(self.current_rr_d1, last_allowed_time),
            self.decode_value(self.current_rr_d2, last_allowed_time),
            self.decode_value(self.percentage_change_in_rr_since_yesterday_d1, last_allowed_time),
            self.decode_value(self.percentage_change_in_rr_since_yesterday_d2, last_allowed_time),
            self.decode_value(self.percentage_change_in_rr_since_14_day_d1, last_allowed_time),
            self.decode_value(self.percentage_change_in_rr_since_14_day_d2, last_allowed_time),
            self.decode_value(self.max_pain_strike, last_allowed_time),
            self.decode_value(self.min_pain_strike, last_allowed_time),
            self.decode_value(self.oi_support_strike, last_allowed_time),
            self.decode_value(self.oi_resistance_strike, last_allowed_time),
            
            self.decode_value(self.put_call_volume_ratio_current_day, last_allowed_time),
            self.decode_value(self.put_call_volume_ratio_average_over_n_days, last_allowed_time),
            absolute_pc_change_since_yesterday,
            # Computed
            
            pc_change_iv_change,
        ]

        tup.extend(res)
        
        tup = ["N/A" if _ is None else _ for _ in tup]

        return tuple(tup)

    def decode_value(self, value, last_allowed_time):
        
        if value is None:
            return None
        # if not isinstance(value, str):
        #     value = str(value)
        
        # value = 62.58434308994543|2024-03-08 23:30:38.481088+02:00
        try:
            value, time_stamp = value.split("|")

            if value.strip() == "":
                return None
            else:
                if time_stamp:
                    time_stamp = datetime.datetime.strptime(time_stamp, "%Y-%m-%d %H:%M:%S.%f%z")
                    if time_stamp < last_allowed_time:
                        return None    
                return float(value)
        except Exception as e:
            print(f"Value: {value}, {e}")