from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.manage_mkt_data_sub import ManageMktDataSubscription
from option_combo_scanner.strategy.monitor_order_preset import MonitorOrderPreset
from option_combo_scanner.strategy.strategy_variables import StrategyVariables as strategy_variables

logger = CustomLogger.logger


class ScannerCombination:
    def __init__(self, values_dict,):
        [setattr(self, key, value) for key, value in values_dict.items()]

        # Cast to integers
        self.combo_id = int(self.combo_id)
        self.instrument_id = int(self.instrument_id)
        
        # Set the combination description
        self.description = self.get_combo_description()

        # Map combination_id to combination object
        self.map_combo_id_to_scanner_combination_object()

    def map_combo_id_to_scanner_combination_object(self):
        
        strategy_variables.map_combo_id_to_scanner_combination_object[self.combo_id] = self

    def __str__(self) -> str:
        
        return f"Scanner Combination Object: {pprint(vars(self))}"
    
    def get_combo_description(self, ):

        # Ticker 1 (Sec Type 1: Expiry 1 C/P Strike 1) +/- Qty 1,
        # Tickers Informative string
        combo_desc_string = ""

        # Processing Leg Obj and appending to combo_desc_string
        for leg_no, leg_obj in enumerate(self.list_of_all_leg_objects):

            # Symbol and SecType
            combo_desc_string += f"{self.symbol} ({self.sec_type}"

            # Expiry Date, Right, Strike
            combo_desc_string += (
                f" {self.expiry} {self.right} {leg_obj.strike}"
            )
        
            # Buy/Sell +1 or -1
            if leg_obj.action.upper() == "BUY":
                # check if it is last leg
                if leg_no == len(self.list_of_all_leg_objects) - 1:
                    combo_desc_string += f") +{leg_obj.qty}"
                else:
                    combo_desc_string += f") +{leg_obj.qty}, "
            else:
                # check if it is last leg
                if leg_no == len(self.list_of_all_leg_objects) - 1:
                    combo_desc_string += f") -{leg_obj.qty}"
                else:
                    combo_desc_string += f") -{leg_obj.qty}, "

        return combo_desc_string


    def get_scanner_combination_tuple_for_gui(self, ):
        # Create a tuple with object attributes in the specified order
        combination_tuple = (
            self.combo_id,
            self.instrument_id,
            self.number_of_legs,
            self.symbol,
            self.sec_type,
            self.expiry,
            self.right,
            self.multiplier,
            self.trading_class,
            self.currency,
            self.exchange,
            self.combo_net_delta,
            self.max_profit,
            self.max_loss,
            self.max_profit_max_loss_ratio,
            self.list_of_all_leg_objects
        )

        return combination_tuple

    
# It is used to show user the combination details in combination tab of screen GUI
def get_scanner_combination_details_column_and_data_from_combo_object(
    combo_id: int,
):
    try:
        # Scanner Combo Object
        combo_obj = strategy_variables.map_combo_id_to_scanner_combination_object[combo_id]

    except Exception as e:
        # Show error pop up
        error_title = f"Error Scanned Combo ID: {combo_id}"
        error_string = f"Unable to find the Scanned Combination."
        Utils.display_message_popup(
                error_title,
                error_string
            )
        return None

    # Column names, to show inside Combination details screen GUI
    leg_columns_for_combo_detail_gui = strategy_variables.leg_columns_combo_detail_gui

    # List of tuple (for each row in combination details)
    leg_data_tuple_list = []

    # All Legs in combination
    all_legs = combo_obj.list_of_all_leg_objects

    symbol = combo_obj.symbol
    sec_type = combo_obj.sec_type
    exchange = combo_obj.exchange
    currency = combo_obj.currency
    expiry_date = combo_obj.expiry
    right = combo_obj.right
    multiplier = combo_obj.multiplier
    primary_exchange = combo_obj.primary_exchange
    trading_class = combo_obj.trading_class

    # Processing legs and getting data for row.
    for leg_obj in all_legs:

        # Init
        action = leg_obj.action
        quantity = leg_obj.qty
        strike_price = leg_obj.strike
        con_id = leg_obj.con_id

        # append values to list
        leg_data_tuple_list.append(
            (
                action,
                symbol,
                sec_type,
                exchange,
                currency,
                quantity,
                expiry_date,
                strike_price,
                right,
                multiplier,
                con_id,
                primary_exchange,
                trading_class,
            )
        )

    return leg_columns_for_combo_detail_gui, leg_data_tuple_list
