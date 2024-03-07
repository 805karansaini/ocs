from pprint import pprint

import pandas as pd

from com.contracts import get_contract

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.manage_mkt_data_sub import ManageMktDataSubscription
from option_combo_scanner.strategy.monitor_order_preset import MonitorOrderPreset
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)

logger = CustomLogger.logger


class Indicator:
    def __init__(
        self,
        values_dict,
    ):
        [setattr(self, key, value) for key, value in values_dict.items()]

        self.indicator_id = int(self.indicator_id)
        self.underlying_conid = int(self.underlying_conid)
        self.currency = 'USD'  # TODO ARYAN
        self.map_indicator_id_to_indicator_object()

    def map_indicator_id_to_indicator_object(self):

        underlying_sec_type = "FUT" if self.sec_type == "FOP" else "STK"

        # Create an underlying contract
        underlying_contract = get_contract(
            self.symbol,
            underlying_sec_type,
            "SMART" if underlying_sec_type == 'STK' else 'CME', # TODO ARYAN
            self.currency,
            multiplier=self.multiplier,
            con_id=self.underlying_conid,
        )
        strategy_variables.map_con_id_to_contract[self.underlying_conid] = underlying_contract
        
        # Assigning the current object to the 'indicator_object' variable within the 'strategy_variables'
        strategy_variables.map_indicator_id_to_indicator_object[self.indicator_id] = self
        row = pd.DataFrame(
            {
                "Indicator ID": self.indicator_id,
                "Instrument ID": self.instrument_id,
                "Symbol": self.symbol,
                "sec_type": underlying_sec_type,
                "expiry": self.expiry,
                "hv": None,
                "iv_d1": None,
                "iv_d2": None,
                "avg_iv": None,
                "rr_d1": None,
                "rr_d2": None,
                "avg_iv_avg_14d": None,
                "change_rr_d1_1D": None,
                "change_rr_d2_1D": None,
                "change_rr_d1_14D": None,
                "change_rr_d2_14D": None,
                "hv_14d_avg_14d": None,
                'hv_14d_avg_iv': None,
                'open_interest_support': None,
                'open_interest_resistance': None,
                "pc_change": None,
                'pc_change_iv_change': None,
                "put_call_ratio_avg": None,
                "put_call_ratio_current": None,
                'Change_underlying_options_price_today':None,
                'chg_uderlying_opt_price_14d': None,
                'max_pain': None,
                'min_pain': None,
            
                
            },
            index=[0],
        )


        # Add Row to dataframe (concat)
        strategy_variables.scanner_indicator_table_df = pd.concat(
            [strategy_variables.scanner_indicator_table_df, row],
            ignore_index=True,
        )


    def __str__(self) -> str:

        return f"Indicator:\n{pprint(vars(self))}"

    def remove_indicator_from_system(self):

        # Remove row from dataframe
        # TODO Check
        strategy_variables.scanner_indicator_table_df = (
            strategy_variables.scanner_indicator_table_df.drop(
                strategy_variables.scanner_indicator_table_df[
                    strategy_variables.scanner_indicator_table_df["Indicator ID"]
                    == self.indicator_id
                ].index
            )
        )

        del strategy_variables.map_indicator_id_to_indicator_object[self.indicator_id]
    
    # TODO: Change RR IV names as per df
    def get_indicator_tuple_for_gui(
        self,
    ):
        # Create a tuple with object attributes in the specified order
        indicator_tuple = (
            self.indicator_id,
            self.symbol,
            self.expiry,
            # self.expiry, TODO UnderLying Conid
            self.hv,
            self.iv,
            self.hv_iv,
            self.rr_25,
            self.rr_50,
            self.rr_25_50,
            self.rr_change_last_close,
            self.max_pain,
            self.min_pain,
            self.avg_iv,
            self.avg_hv,
            self.open_interest_support,
            self.open_interest_resistance,
            self.put_volume,
            self.call_volume,
            self.put_call_volume_ratio,
            self.put_call_volume_average,
            self.change_underlying_option_price,
            self.change_underlying_option_price_14_days,
            self.pc_change,
            self.iv_change,
            self.pc_change_iv_change,
        )

        return indicator_tuple
