import pprint

from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.order_presets_tab_helper import OrderPresetHelper
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.contracts import get_contract
from option_combo_scanner.strategy.instrument import Instrument
from option_combo_scanner.strategy.order_preset import OrderPreset


class HouseKeepingGUI:
    def __init__(self) -> None:
        pass
    
    
    @staticmethod
    def dump_all_instruments_in_instrument_tab(
        scanner_inputs_tab_obj,
    ):
        # TODO Get the preset orders from option_combo_scanner.the database
        all_instruments = SqlQueries.select_from_db_table(table_name="instrument_table", columns="*")
        
        # Insert the preset orders in the preset order tab[table]
        for values_dict in all_instruments:
            intrument_obj = Instrument(values_dict)  # Mapping

            ### Add in the preset order table ###
            scanner_inputs_tab_obj.insert_into_instrument_table(intrument_obj)
    
    @staticmethod
    def dump_all_preset_order_in_preset_order_tab(
        order_preset_helper_obj: OrderPresetHelper,
    ):
        # Get the preset orders from option_combo_scanner.the database
        preset_orders = SqlQueries.get_preset_orders(columns="*")

        # Insert the preset orders in the preset order tab[table]
        for preset_order_value in preset_orders:
            ### Add in the preset order table ###
            order_preset_helper_obj.add_order_preset_to_table(preset_order_value)

            #### Manage Conid, contract, Subscription ####
            # Contract
            contract = get_contract(
                symbol=preset_order_value["Ticker"],
                sec_type=preset_order_value["SecType"],
                exchange=preset_order_value["Exchange"],
                currency=preset_order_value["Currency"],
                con_id=int(preset_order_value["Conid"]),
            )

            # Create OrderPreset Object and Manage Conid, contract, Subscription
            OrderPreset(preset_order_value, contract)

    def insert_order_status_in_order_book_tab(self):
        pass
