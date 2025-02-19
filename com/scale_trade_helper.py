from com import *
from com.variables import *
from com.combination_helper import is_integer
from com.upload_combo_to_application import make_multiline_mssg_for_gui_popup
from com.mysql_io_scale_trader import *
from com.ladder import *
from com.mysql_io import *
from com.sequence import *
from com.order_execution import *


# Method to check if value is float or not
def is_float(value):
    try:
        # Check if the value can be converted to a float
        float_value = float(value)

        # Return true if no exception occured
        return True

    except Exception as e:
        # Return false if value cannot be converted to float
        return False


# Fill scale trade table in GUI at start of app
def insert_all_scale_trades_in_scale_trader_table():
    try:
        # Get all ladder rows from DB
        variables.scale_trade_table_dataframe = get_primary_vars_db(
            variables.sql_table_ladder
        )

        # check if dataframe is empty
        if variables.scale_trade_table_dataframe.empty:
            # Return if dataframe is empty
            return

        # Get values in tuple format
        all_row_values = variables.scale_trade_table_dataframe.to_records(index=False)

        # Fill scale trade GUI table in scale trade tab
        for row_values in all_row_values:
            # Add row in scale trade table
            variables.screen.screen_scale_trader_obj.insert_scale_trade_in_scale_trader_table(
                row_values
            )

    except Exception as e:
        # Print to Console
        if variables.flag_debug_mode:
            print(f"Could not filled scale trader GUI table")


# Method to get ladder objects from DB -
def get_ladder_id_ladder_obj_dict(ladder_id_to_sequence_obj_dict):
    try:
        # Get dataframe from ladder table
        ladder_table_dataframe = get_primary_vars_db(variables.sql_table_ladder)

        # Get all rows of the DataFrame as a list of lists
        ladder_table_rows_list = ladder_table_dataframe.values.tolist()

        # Iterating all rows in ladder table as list
        for ladder_table_row in ladder_table_rows_list:
            # Getting values for ladder id and unique id
            ladder_id = int(float(ladder_table_row[0]))
            unique_id = int(float(ladder_table_row[1]))

            # Check if the key unique id exists in the dictionary
            if not unique_id in variables.map_unique_id_to_ladder_ids_list:
                variables.map_unique_id_to_ladder_ids_list[unique_id] = []

            # Map unique id to ladder
            variables.map_unique_id_to_ladder_ids_list[unique_id].append(ladder_id)

            # Creating list to store sequence objects
            sequence_obj_list = ladder_id_to_sequence_obj_dict[ladder_id]

            # Append sequence object list to ladder table row list to add sequences in ladder obj
            ladder_table_row.append(sequence_obj_list)

            # Create ladder object
            ladder_obj = Ladder(*ladder_table_row)

            # Map ladder id to ladder object
            variables.map_ladder_id_to_ladder_obj[ladder_id] = ladder_obj

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Exception inside 'get_ladder_id_ladder_obj_dict', Exp: {e}")


# Method to get sequence objects from DB
def get_sequence_obj_dict():
    try:
        # Get dataframe from sequence table
        sequence_table_dataframe = get_primary_vars_db(variables.sql_table_sequence)

        # Get all rows of the DataFrame as a list of lists
        sequence_table_rows_list = sequence_table_dataframe.values.tolist()

        # Dict for sequence objects
        sequence_obj_dict = {}

        # Iterating all rows in sequence table as list
        for sequence_table_row in sequence_table_rows_list:
            # Getting values for ladder id, sequence id and sequence type
            ladder_id = int(float(sequence_table_row[2]))
            sequence_id = int(float(sequence_table_row[0]))
            sequence_type = sequence_table_row[1]

            # Check if ladder id is not in dictionary
            if ladder_id not in sequence_obj_dict:
                # Put ladder id in dict as key
                sequence_obj_dict[ladder_id] = []

            # Create sequence object
            sequence_obj = Sequence(*sequence_table_row)

            # Appending sequence objects in list
            sequence_obj_dict[ladder_id].append(sequence_obj)

        return sequence_obj_dict

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Exception inside 'get_sequence_obj_dict', Exp: {e}")


# Method to cancel all scale trader - sequence orders after app restart - Deprecated
def cancel_all_orders_from_scale_trade_after_restart():
    # TODO -  Ashish
    # At the start -> run a simple query on db.
    # Mark all Pending orders cancelled that are related to sequence or ladder

    try:
        # Get all orders dataframe
        local_orders_book_table_dataframe = get_primary_vars_db(
            variables.sql_table_combination_status
        )

        # If dataframe is empty
        if local_orders_book_table_dataframe.empty:
            # Then initialize with columns
            local_orders_book_table_dataframe = pd.DataFrame(
                columns=variables.order_book_table_columns
            )

        # Filter the rows where 'ladder id' is not None and get the value of 'order time' column
        order_row_values = local_orders_book_table_dataframe.loc[
            local_orders_book_table_dataframe["Ladder ID"] != "None",
            ["Order Time", "Status", "Ladder ID", "Sequence ID"],
        ].values

        # Iterate order row values
        for [order_time, status, ladder_id, sequence_id] in order_row_values:
            # check if status is pending
            if status == "Pending":
                # Cancel order
                variables.screen.cancel_order(order_time)

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception inside 'cancel_all_orders_from_scale_trade_after_restart', Exp: {e}"
            )


# Method to cancel orders based on ladder id
def cancel_orders_of_ladder_id_or_sequence_id(ladder_id=None, sequence_id=None):
    try:
        # Get all orders dataframe
        local_orders_book_table_dataframe = get_primary_vars_db(
            variables.sql_table_combination_status
        )

        # If dataframe is empty
        if local_orders_book_table_dataframe.empty:
            # Then initialize with columns
            local_orders_book_table_dataframe = pd.DataFrame(
                columns=variables.order_book_table_columns
            )

        # Check if ladder id is not none
        if ladder_id != None:
            # convert ladder id column to string format
            local_orders_book_table_dataframe["Ladder ID"] = (
                local_orders_book_table_dataframe["Ladder ID"].astype(str)
            )

            # Filter the rows for 'ladder id' and get the value of 'order time' column
            order_time_status_values = local_orders_book_table_dataframe.loc[
                local_orders_book_table_dataframe["Ladder ID"] == ladder_id,
                ["Order Time", "Status"],
            ].values

        # Check if sequence id is not none
        if sequence_id != None:
            # convert ladder id column to string format
            local_orders_book_table_dataframe["Sequence ID"] = (
                local_orders_book_table_dataframe["Sequence ID"].astype(str)
            )

            # Filter the rows for 'ladder id' and get the value of 'order time' column
            order_time_status_values = local_orders_book_table_dataframe.loc[
                local_orders_book_table_dataframe["Sequence ID"] == sequence_id,
                ["Order Time", "Status"],
            ].values

        # Iterate order time and status values
        for order_time_and_status in order_time_status_values:
            # Get order time and status
            order_time = order_time_and_status[0]
            status = order_time_and_status[1]

            # check if status is pending
            if status == "Pending":
                # Cancel order
                variables.screen.cancel_order(order_time)

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Exception inside 'cancel_orders_of_ladder_id', Exp: {e}")


# Pause all active ladders after app restart - Deprecated
def pause_all_active_ladders_after_restart():
    # TODO - write a ACTUIVE K LIYE
    # Change in DB
    # Get dictionary in which all ladder ids are present
    local_map_ladder_id_to_ladder_obj = copy.deepcopy(
        variables.map_ladder_id_to_ladder_obj
    )

    # Get all ladder id in system
    all_ladder_ids_in_system = local_map_ladder_id_to_ladder_obj.keys()

    # Iterate each ladder id
    for ladder_id in all_ladder_ids_in_system:
        # Get ladder obj
        ladder_obj = local_map_ladder_id_to_ladder_obj[ladder_id]

        # Check if ladder pbject's status is active
        if ladder_obj.status == "Active":
            # Update status of ladder
            variables.screen.screen_scale_trader_obj.update_ladder_status(
                ladder_id, "Paused"
            )


# Method to update order status for scale trade
def update_order_status_for_scale_trade():
    # Get all the sequence Number which are Active.
    # Get all the orders from db table which corresponds to seqID

    # check status if filled then run the function.

    try:
        # Print to console
        if variables.flag_debug_mode:
            print("Getting all the sequence where status is 'Active'.")

        # Get all the sequence where status is Active
        all_sequnce_with_status_active = get_all_sequence_from_db(status="Active")

        # print(f"all_sequnce_with_status_active")
        # print(all_sequnce_with_status_active.to_string())

        if all_sequnce_with_status_active.empty:
            return

        sequence_ids = all_sequnce_with_status_active["Sequence ID"].tolist()

        sequence_ids_string = ",".join(map(str, sequence_ids))

        all_orders_for_active_sequence = get_all_order_from_db_where(
            sequence_id_string=sequence_ids_string
        )

        # print(f"all_orders_for_active_sequence")
        # print(all_orders_for_active_sequence.to_string())

        if all_orders_for_active_sequence.empty:
            return

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Fetched sequence where status is 'Active' are: {all_orders_for_active_sequence}."
            )

        # Check if Sent order is filled.
        for _, row in all_orders_for_active_sequence.iterrows():
            # print("Sequence ID", row['Sequence ID'] , row['Status'] )

            if row["Status"] == "Filled":
                # Get ladder id
                ladder_id = row["Ladder ID"]

                # Check if order is originated from scale trade
                if ladder_id != "None":
                    # Method to update scale trade after order filled for scale trade
                    # Send order in a separate thread
                    """rm_check_thread = threading.Thread(
                        target=variables.screen.screen_scale_trader_obj.update_scale_trade_after_order_filled,
                        args=(row),

                    )
                    rm_check_thread.start()"""
                    variables.screen.screen_scale_trader_obj.update_scale_trade_after_order_filled(
                        row
                    )

    except Exception as e:
        print(f"Exception in update_order_status_for_scale_trade {e}")


# Method to create ladder and sequences instances
def create_ladder_and_sequences(
    unique_id,
    action,
    order_type,
    total_quantity,
    initial_quantity,
    subsequent_quantity,
    number_of_buckets,
    initial_entry_price,
    delta_price,
    price_movement,
    take_profit_buffer,
    take_profit_behaviour,
    account_id,
    bypass_rm_check,
    flag_use_execution_engine=False,
    schedule_data=None,
):
    try:
        # Initializing dictionary to map all column names in DB to its values
        scale_trade_values_dict = {}

        # Get recent ladder id
        ladder_id = copy.deepcopy(variables.ladder_id)

        # Incrementing it so we can use it further
        variables.ladder_id += 1

        entry_order_qunatity_filled = exit_order_quantity_filled = 0
        ladder_status = "Paused"

        # Values of scale trade to store
        scale_trade_values_list = [
            ladder_id,
            unique_id,
            action,
            order_type,
            total_quantity,
            initial_quantity,
            subsequent_quantity,
            number_of_buckets,
            initial_entry_price,
            delta_price,
            price_movement,
            take_profit_buffer,
            take_profit_behaviour,
            entry_order_qunatity_filled,
            exit_order_quantity_filled,
            ladder_status,
            account_id,
            bypass_rm_check,
            flag_use_execution_engine,
        ]

        # Get columns for scale trader table
        scale_trader_table_columns = copy.deepcopy(variables.scale_trader_table_columns)

        # Put all values of scale trade columns in dictionary
        for column_name, column_value in zip(
            scale_trader_table_columns, scale_trade_values_list
        ):
            scale_trade_values_dict[column_name] = column_value

        # Add scale trade instance and values
        insert_ladder_instance_values_to_ladder_table(scale_trade_values_dict)

        # TODO - move to separate module
        # Get list of sequnces for scale trade
        list_of_sequences = create_entry_sequences_for_scale_trade(
            ladder_id,
            unique_id,
            action,
            order_type,
            total_quantity,
            initial_quantity,
            subsequent_quantity,
            number_of_buckets,
            initial_entry_price,
            delta_price,
            price_movement,
            schedule_data,
        )

        # Checking if list of sequences is None
        if list_of_sequences == None:
            # Show an error popup unable to create a scale trader.
            error_title, error_string = "Error, Could not get sequences"

            variables.screen.display_error_popup(error_title, error_string)

            raise Exception("Could not get sequences")

        # Inititalize list to map ladder id to list of its sequence ids
        variables.map_ladder_id_to_sequence_ids_list[ladder_id] = []

        # List for sequence objects
        sequence_objects_list = []

        # Get columns of sequence table
        local_sequence_table_columns = copy.deepcopy(variables.sequence_table_columns)

        # Inititalize list to store sequence values
        list_of_sequences_values_to_insert_in_db = []

        # Iterating sequences
        for sequence in list_of_sequences:
            # Create sequence object
            sequence_obj = Sequence(*sequence)

            # Add sequence objects to list
            sequence_objects_list.append(sequence_obj)

            # Get sequence id for sequence
            sequence_id = sequence[0]

            # Use zip() to combine the column names and column values element-wise and create a list of tuples
            sequence_table_column_value_pair = zip(
                local_sequence_table_columns, sequence
            )

            # Convert the list of tuples to a dictionary using the dict() constructor
            sequence_table_column_value_dict = dict(sequence_table_column_value_pair)

            # Fill sequence values in list
            # list_of_sequences_values_to_insert_in_db.append(sequence_table_column_value_dict)

            # adding values of sequence in DB
            insert_sequence_instance_values_to_sequence_table(
                sequence_table_column_value_dict
            )

        # Create ladder object
        ladder_obj = Ladder(
            ladder_id,
            unique_id,
            action,
            order_type,
            total_quantity,
            initial_quantity,
            subsequent_quantity,
            number_of_buckets,
            initial_entry_price,
            delta_price,
            price_movement,
            take_profit_buffer,
            take_profit_behaviour,
            0,
            0,
            "Paused",
            account_id,
            bypass_rm_check,
            flag_use_execution_engine,
            sequence_objects_list,
        )

        # Check if the key unique id exists in the dictionary
        if not unique_id in variables.map_unique_id_to_ladder_ids_list:
            variables.map_unique_id_to_ladder_ids_list[unique_id] = []

        # Map unique id to ladder
        variables.map_unique_id_to_ladder_ids_list[unique_id].append(ladder_id)

        # Map ladder id to ladder object
        variables.map_ladder_id_to_ladder_obj[ladder_id] = ladder_obj

        # Insert Prices in scale trade table,
        values = (
            ladder_id,
            unique_id,
            action,
            order_type,
            total_quantity,
            initial_quantity,
            subsequent_quantity,
            number_of_buckets,
            initial_entry_price,
            delta_price,
            price_movement,
            take_profit_buffer,
            take_profit_behaviour,
            0,
            0,
            "Paused",
            account_id,
            bypass_rm_check,
            flag_use_execution_engine,
        )

        # Creating dataframe for row data
        scale_trade_row_df = pd.DataFrame(
            [values], columns=variables.scale_trader_table_columns
        )

        # Concat row with scale trade table dataframe
        variables.scale_trade_table_dataframe = pd.concat(
            [variables.scale_trade_table_dataframe, scale_trade_row_df]
        )

    except Exception as e:
        if variables.flag_debug_mode:
            print(f"Exception inside 'create_ladder_and_sequences', Exp: {e}")

        return None


# Method to create entry sequences for scale trade
def create_entry_sequences_for_scale_trade(
    ladder_id,
    unique_id,
    action,
    order_type,
    total_quantity,
    initial_quantity,
    subsequent_quantity,
    number_of_buckets,
    initial_entry_price,
    delta_price,
    price_movement,
    schedule_data=None,
):
    # Create list of sequences
    sequences_for_scale_trade = []

    # Get max sequence_id present
    sequence_id = copy.deepcopy(variables.sequence_id)

    # Increment it to use later
    variables.sequence_id += 1

    # Sequence Type
    sequence_type = "Entry"

    # Init variables
    order_time = "None"
    order_sent_time = "None"
    last_update_time = "None"
    filled_quantity = 0
    sequence_status = "Active"

    percentage_list = ["None"]

    if schedule_data != None:
        # get df
        pair_df = schedule_data["Percentage Lots Pair"]

        # sorrt df based on action and price movement
        if action == "BUY" and price_movement == "Better":
            # Sorting the DataFrame based on column in reverse order
            pair_df = pair_df.sort_values(by="Percentage", ascending=False)

        elif action == "BUY" and price_movement == "Worse":
            # Sorting the DataFrame based on column in reverse order
            pair_df = pair_df.sort_values(by="Percentage", ascending=True)

        elif action == "SELL" and price_movement == "Better":
            # Sorting the DataFrame based on column in reverse order
            pair_df = pair_df.sort_values(by="Percentage", ascending=True)

        else:
            # Sorting the DataFrame based on column in reverse order
            pair_df = pair_df.sort_values(by="Percentage", ascending=False)

        percentage_list = pair_df["Percentage"].to_list()

    # Append initial entry order to list
    initial_entry_sequence = [
        sequence_id,
        sequence_type,
        ladder_id,
        action,
        order_type,
        initial_quantity,
        initial_entry_price,
        order_time,
        order_sent_time,
        last_update_time,
        filled_quantity,
        sequence_status,
        percentage_list[0],
    ]

    # Append to list
    sequences_for_scale_trade.append(initial_entry_sequence)

    try:
        # Get total quantity remained to trade
        total_quantity_remaining = total_quantity - initial_quantity

        # Initialize subsequent qauntities list
        subsequent_quantitities_list = []

        # If number of buckets is not none
        if number_of_buckets != "None":
            # Get subsequent qauntity for each bucket
            for bucket_number in range(2, number_of_buckets + 1):
                if bucket_number != number_of_buckets:
                    # Get round value of subsequent qauntity in case for number of buckets value is not None
                    round_subsequent_quantity_for_sequences = round(
                        total_quantity_remaining
                        / (number_of_buckets - (bucket_number - 1))
                    )

                    # Getting subsequent quantities for sequences afetr initial sequence and before last sequence in case of number of buckets is not none
                    subsequent_quantitities_list.append(
                        round_subsequent_quantity_for_sequences
                    )

                    # Keep total quantity remaining to trade for next bucket
                    total_quantity_remaining -= round_subsequent_quantity_for_sequences

                elif total_quantity_remaining != 0:
                    # Sort list
                    subsequent_quantitities_list.sort(reverse=True)

                    # Getting subsequent quantities for last sequence in case of number of buckets is not none
                    subsequent_quantitities_list.append(total_quantity_remaining)

        # If subsequent_quantity is not none
        elif subsequent_quantity != "None":
            # Getting subsequent quantities for sequences after initial sequence and before last sequence in case of number of buckets is not none
            subsequent_quantitities_list = [subsequent_quantity] * (
                total_quantity_remaining // (subsequent_quantity)
            )

            # If there is no remaining quantity to trade
            if total_quantity_remaining % subsequent_quantity != 0:
                # Getting subsequent quantity for last sequence in case of number of buckets is not none
                subsequent_quantitities_list.append(
                    (total_quantity_remaining % (subsequent_quantity))
                )

        # If None values for both subsequent quantity and number of buckets
        else:
            return None

        # Check if price movement is better
        if price_movement == "Better" and delta_price not in ["None", None]:
            # Check if action is BUY
            if action == "BUY":
                delta_price *= -1
            else:
                delta_price = delta_price

        # Check if price movement is worse
        elif price_movement == "Worse" and delta_price not in ["None", None]:
            # Check if action is SELL
            if action == "SELL":
                delta_price *= -1
            else:
                delta_price = delta_price

        # set sequence status to queued
        sequence_status = "Queued"

        # Init
        price_list = subsequent_quantitities_list

        percentage_list = ["None"] * len(subsequent_quantitities_list)

        if schedule_data != None:
            percentage_list = pair_df["Percentage"].to_list()[1:]

            # get lots for subsequent orders and prices
            subsequent_quantitities_list = pair_df["#Lots"].to_list()[1:]
            price_list = pair_df["Price"].to_list()[1:]

        # Get subsequent sequences obj for scale trade and Multiplier for delta price
        for multiplier_for_delta_price, (
            current_subsequent_quantity,
            price_for_seq,
            percentage,
        ) in enumerate(
            zip(subsequent_quantitities_list, price_list, percentage_list), start=1
        ):
            if current_subsequent_quantity == 0:
                continue

            # Get max sequence_id present
            sequence_id = copy.deepcopy(variables.sequence_id)

            # Increment it to use later
            variables.sequence_id += 1

            # insert sequence for other order than reange schedule orders
            if schedule_data == None:
                # Create subsequent sequences
                subsequent_entry_sequence = [
                    sequence_id,
                    "Entry",
                    ladder_id,
                    action,
                    order_type,
                    current_subsequent_quantity,
                    initial_entry_price + (multiplier_for_delta_price * delta_price),
                    order_time,
                    order_sent_time,
                    last_update_time,
                    filled_quantity,
                    sequence_status,
                    percentage,
                ]

            else:
                # Create subsequent sequences
                subsequent_entry_sequence = [
                    sequence_id,
                    "Entry",
                    ladder_id,
                    action,
                    order_type,
                    current_subsequent_quantity,
                    price_for_seq,
                    order_time,
                    order_sent_time,
                    last_update_time,
                    filled_quantity,
                    sequence_status,
                    percentage,
                ]

            # Append to list
            sequences_for_scale_trade.append(subsequent_entry_sequence)

        # Return list of sequences
        return sequences_for_scale_trade

    except Exception as e:
        # Return None id exception occurs
        return None
