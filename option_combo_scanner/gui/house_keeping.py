import pprint

from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.contracts import get_contract
from option_combo_scanner.strategy.indicator import Indicator
from option_combo_scanner.strategy.instrument import Instrument
from option_combo_scanner.strategy.scanner_combination import ScannerCombination
from option_combo_scanner.strategy.scanner_config import Config
from option_combo_scanner.strategy.scanner_config_leg import ConfigLeg
from option_combo_scanner.strategy.scanner_leg import ScannerLeg


class HouseKeepingGUI:
    def __init__(self) -> None:
        pass

    @staticmethod
    def dump_all_instruments_in_instrument_tab(
        scanner_inputs_tab_obj,
    ):
        # Get the Instrument from instrument table
        all_instruments = SqlQueries.select_from_db_table(
            table_name="instrument_table", columns="*"
        )

        # Insert the preset orders in the preset order tab[table]
        for values_dict in all_instruments:
            intrument_obj = Instrument(values_dict)  # Mapping

            ### Add in the preset order table ###
            scanner_inputs_tab_obj.insert_into_instrument_table(intrument_obj)

    @staticmethod
    def dump_all_scanner_combinations_in_scanner_combination_tab(
        scanner_combination_tab_obj,
    ):
        # Get the Combintaion from combintation tabl
        all_combinations = SqlQueries.select_from_db_table(
            table_name="combination_table", columns="*"
        )

        # Get the Combintaion Leg from legs table
        all_legs = SqlQueries.select_from_db_table(table_name="legs_table", columns="*")

        # Dictionary for quick look up
        legs_look_up_dict = {}

        # Mapping leg in the above dict
        for leg in all_legs:
            combo_id = int(leg["combo_id"])
            leg_number = int(leg["leg_number"])

            if combo_id in legs_look_up_dict:
                pass
            else:
                legs_look_up_dict[combo_id] = {}
            legs_look_up_dict[combo_id][leg_number] = leg

        # Iterating over all the combinations
        for combination in all_combinations:
            try:
                combo_id = int(combination["combo_id"])
                legs = int(combination["number_of_legs"])
                # list of leg object
                list_of_all_leg_objects = []

                # Creating the Leg Objects
                for leg_number in range(1, legs + 1):
                    leg_values_dict = legs_look_up_dict[combo_id][leg_number]

                    list_of_all_leg_objects.append(ScannerLeg(leg_values_dict))

                # Added the list of leg object
                combination["list_of_all_leg_objects"] = list_of_all_leg_objects

                # Creating the Scanner Combination Object
                scanner_combination_object = ScannerCombination(combination)

                # Insert the Scanner combination in GUI
                scanner_combination_tab_obj.insert_combination_in_scanner_combination_table_gui(
                    scanner_combination_object
                )
            except Exception as e:
                print(e)

    @staticmethod
    def dump_all_indicator_values_in_indicator_tab(
        scanner_indicator_tab_obj,
    ):
        # Get the Indicators from Indicator table
        all_indicator = SqlQueries.select_from_db_table(
            table_name="indicator_table", columns="*"
        )

        for values_dict in all_indicator:
            indicator_obj = Indicator(values_dict)  # Mapping

            ### Add in the Indicator table
            scanner_indicator_tab_obj.insert_into_indicator_table(indicator_obj)

    @staticmethod
    def dump_all_config_in_system(
        scanner_inputs_tab_obj=None,
    ):
        # Get the config from Config Table
        all_config = SqlQueries.select_from_db_table(
            table_name="config_table", columns="*"
        )

        # Get the config leg wise from Config Legs table
        all_legs_config = SqlQueries.select_from_db_table(
            table_name="config_legs_table", columns="*"
        )

        for config_dict in all_config:
            list_of_config_leg_object = []
            # Insert the preset orders in the preset order tab[table]
            for config_leg_dict in all_legs_config:
                if config_leg_dict["config_id"] != config_dict["config_id"]:
                    continue

                config_leg_obj = ConfigLeg(config_leg_dict)  # Mapping
                list_of_config_leg_object.append(config_leg_obj)

            config_dict["list_of_config_leg_object"] = list_of_config_leg_object
            config_obj = Config(config_dict)
