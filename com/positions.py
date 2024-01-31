"""
Created on 14-Apr-2023

@author: Karan
"""

from com import *
from com.variables import *
from com.mysql_io import *
from com.combination import *

# Method to calculate combo positions
def calculation_combinations_positions():

    # local copy of 'unique_id_to_combo_obj'
    local_unique_id_to_combo_obj = variables.unique_id_to_combo_obj

    # Get all the combination orders from db
    all_combination_order = get_all_combinaiton_orders_from_db()

    # Check if datafrmae is empty
    if all_combination_order.empty:

        all_account_ids_in_order_book = []

    else:

        # all account ids in order book
        all_account_ids_in_order_book = all_combination_order["Account ID"].to_list()

    # make list of account ids in system
    all_account_ids_in_system = sorted(
        list(set(variables.current_session_accounts + all_account_ids_in_order_book))
    )

    # Positions dict
    positions_dict = {
        unique_id: {account_id: 0 for account_id in all_account_ids_in_system}
        for unique_id, _ in local_unique_id_to_combo_obj.items()
    }

    if all_combination_order.empty:
        return positions_dict

    # filter rows where status is not 'Pending'
    all_combination_order = all_combination_order[
        all_combination_order["Status"] != "Pending"
    ]

    # Calculate positions row wise
    for i, row in all_combination_order.iterrows():

        status = row["Status"]

        # If status is cancelled continue
        if status in ["Cancelled", "Sent", "Failed"]:
            continue

        unique_id = int(row["Unique ID"])
        action = row["Action"]
        combo_qty = int(row["#Lots"])
        account_id = row["Account ID"]

        # The reason for this try block is when a combo is delete at that time it might happen that cas_legs are available and cas_condition was deleted Or viceaversa
        try:
            if "BUY" in action:

                positions_dict[unique_id][account_id] += combo_qty
            else:

                positions_dict[unique_id][account_id] -= combo_qty

        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:

                print(e)
                print(
                    f"positions_dict ; {positions_dict} dont have account id : {account_id}"
                )

    return positions_dict

# Method to insert positions in GUI table
def insert_combo_positions_in_positions_tab():

    # Get calcutaed position
    position_dict = calculation_combinations_positions()

    # Update positions to class variable
    variables.map_unique_id_to_positions = position_dict

    # All comobs
    unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

    for unique_id, combo_object in unique_id_to_combo_obj.items():

        informative_string = make_informative_combo_string(combo_object)
        total_legs = len(combo_object.buy_legs) + len(combo_object.sell_legs)
        position = position_dict[unique_id] if (unique_id in position_dict) else 0

        if position < 0:
            position = f"{position}"
        elif position > 0:
            position = f"+{position}"

        value_of_row_in_positions_table = (
            unique_id,
            total_legs,
            informative_string,
            position,
        )
        variables.screen.screen_position_obj.insert_positions_in_positions_table(
            value_of_row_in_positions_table
        )

# Method to keep updaing positions in GUI table
def update_combo_positions_in_positions_tab():

    # Get calcutaed position
    position_dict = calculation_combinations_positions()

    # Update the 'position_dict' to class variables.
    variables.map_unique_id_to_positions = position_dict

    # All comobs
    unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

    for unique_id, combo_object in unique_id_to_combo_obj.items():

        # Iterate account ids
        for account_id in position_dict[unique_id]:

            position = (
                position_dict[unique_id][account_id]
                if (
                    unique_id in position_dict
                    and account_id in position_dict[unique_id]
                )
                else 0
            )

            if position < 0:
                position = f"{position}"
            elif position > 0:
                position = f"+{position}"

            variables.screen.screen_position_obj.update_positions_in_positions_table(
                f"{unique_id}_{account_id}", position
            )
