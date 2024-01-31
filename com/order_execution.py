"""
Created on 14-Mar-2023

@author: Karan
"""

from com.mysql_io import *
from com.contracts import *
from com.combination import *
from enum import unique
from com.screen_accounts_tab import *
from com.variables import *
from com.trade_rm_check_result_module import *
from com.mysql_io_scale_trader import *



# Creates the base_order, Adaptive IB Algo order
def make_order_adaptive_ib_algo(unique_id, base_order, priority):

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Unique ID = {unique_id}: Making Order as IB Algo Adaptive Order, Priority: {priority}"
        )

    # Adding IB algoStrategy, algoParams to base_order
    base_order.algoStrategy = "Adaptive"
    base_order.algoParams = []
    base_order.algoParams.append(TagValue("adaptivePriority", priority))

    return base_order

# Method to get tick size for market
def get_tick_size(bid, ask, con_id):

    try:
        # get market rule id
        market_rule_id = variables.map_con_id_to_rule_id[con_id]

        # get price increments
        price_incr = variables.map_rule_id_to_increments[market_rule_id]

        # get mid
        mid = (bid + ask) / 2

        # init
        tick_size = -1

        # iterate price increment
        for increment in price_incr:

            # check if mid is greater than lowedge
            if mid > increment.lowEdge:

                if tick_size < increment.increment:

                    # get value fot ticksize
                    tick_size = increment.increment

        return tick_size

    except Exception as e:

        if variables.flag_debug_mode:

            print(f"Exception inside 'get_tick_size', Exp: {e}")

        return "N/A"


# Places the MKT IB Algo Order, uses (make_order_adaptive_ib_algo)
def place_market_order(
    unique_id,
    combo_contract,
    order_id,
    order_action,
    order_total_quantity,
    account_id,
    transmit,
    entry_exit_order,
    order_type_des,
    order_time,
    ib_algo_mkt=False,
    limit_order=False,
):

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Unique ID = {unique_id}: Placing Market Order Order ID: {order_id}, Action: {order_action} Quantity: {order_total_quantity} for Contract: {combo_contract}"
        )

    # Temp
    parent_order_id = "NA"

    # Creating Order
    order = Order()
    order.action = order_action
    order.orderType = variables.order_type  # MKT
    order.totalQuantity = order_total_quantity
    order.orderId = order_id
    order.account = account_id
    order.transmit = transmit
    # order.whatIf = True

    # status
    status = str("Order Placed")

    if limit_order:
        order.orderType = "LMT"  # Specify that it's a limit order

        # Get con id
        con_id = combo_contract.conId

        # get req id
        req_id = variables.con_id_to_req_id_dict[con_id]

        # Get bid price and ask price
        bid_price, ask_price = variables.bid_price[req_id], variables.ask_price[req_id]

        # ConId of contract
        con_id = combo_contract.conId

        # get tick size
        tick_size = get_tick_size(bid_price, ask_price, con_id)

        if variables.limit_price_selection_for_execution_engine == "Limit_Bid":

            # Make it available in variables
            avg_price_combo = bid_price

        elif variables.limit_price_selection_for_execution_engine == "Limit_Ask":

            # Make it available in variables
            avg_price_combo = ask_price

        elif variables.limit_price_selection_for_execution_engine == "Limit_Mid":

            # Make it available in variables
            avg_price_combo = (bid_price + ask_price) / 2

            avg_price_combo = round(avg_price_combo / tick_size) * tick_size

        elif variables.limit_price_selection_for_execution_engine == "Pegged_Market":

            # send pegged to market only for stocks
            if combo_contract.secType == "STK":
                order.orderType = "PEG BEST"

            if order_action == "BUY":

                # Make it available in variables
                avg_price_combo = (bid_price + ask_price) / 2

                offset = variables.offset_value_execution_engine

            else:

                # Make it available in variables
                avg_price_combo = (bid_price + ask_price) / 2

                offset = variables.offset_value_execution_engine

            # round of to tick size
            avg_price_combo = round(avg_price_combo / tick_size) * tick_size

            offset = round(offset / tick_size) * tick_size

            order.auxPrice = offset

        elif variables.limit_price_selection_for_execution_engine == "Pegged_Midpoint":

            # send pegged to midpoint only for stocks
            if combo_contract.secType == "STK":

                order.orderType = "PEG MID"

            # Make it available in variables
            avg_price_combo = (bid_price + ask_price) / 2

            offset = 0

            if order_action == "BUY":

                # Make it available in variables
                avg_price_combo = avg_price_combo

            else:

                # Make it available in variables
                avg_price_combo = avg_price_combo

            order.auxPrice = offset

            # round of to tick size
            avg_price_combo = round(avg_price_combo / tick_size) * tick_size

        avg_price_combo = round(avg_price_combo, 2)

        # set limit price
        order.lmtPrice = avg_price_combo

    # Current Time => Order Sent Time & Last Upd.Time
    current_time = datetime.datetime.now(variables.target_timezone_obj)

    # Get con id
    con_id = combo_contract.conId

    # Making the order -> Adaptive ib algo order with MKT and priority(if possible)
    if (
        (ib_algo_mkt)
        and not limit_order
        and (variables.map_con_id_to_flag_supports_ib_algo_order[con_id])
    ):

        # Create IB ALGO order
        order = make_order_adaptive_ib_algo(
            unique_id, order, variables.ib_algo_priority
        )

    # Placing Order
    variables.app.placeOrder(order_id, combo_contract, order)

    # ticker string
    ticker_str = (
        combo_contract.symbol
        + ","
        + str(order_total_quantity)
        + ","
        + str(combo_contract.conId)
    )

    # Query to insert the order into Order Status Table in DB
    insr_query = text(
        f"INSERT INTO `{variables.active_sql_db_name}`.`{variables.sql_table_order_status}` \
                ( `Account ID`, `Unique ID`, `Order ID`, `Parent Order ID`, `Order Action`, `Target Fill`, `Current Fill`, `Avg Fill Price`,  `Order Time`,`Order Sent Time`, `Last Update time`, `Order Type`, `Status`, `Ticker`) \
                VALUES ('{account_id}', '{unique_id}','{order_id}','{parent_order_id}','{order_action}','{order_total_quantity}','{0}','{-1}','{str(order_time)}','{str(current_time)}','{str(current_time)}','{str(entry_exit_order + ' ' + order_type_des)}', '{status}', '{ticker_str}' )"
    )

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Unique ID = {unique_id}: Insert Order Query for Order Status table: {insr_query}"
        )

    # Trying to insert row in DB
    try:
        result = variables.active_sqlalchemy_connection.execute(insr_query)
        time.sleep(variables.sleep_time_db)
    except:

        # Print to console
        print(
            f"Unique ID = {unique_id}: Unable to insert the identified butterfly in to database, Unique ID: {unique_id}"
        )

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Unique ID = {unique_id}: {order_action.capitalize()} {order_type_des}, Qty: '{order_total_quantity}', {entry_exit_order} order placed, order_id= {order_id}"
        )
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

# Places Order for Single leg, get option contract then places order,
def send_order_singe_leg(
    unique_id,
    contract,
    order_qty,
    order_action,
    entry_exit_order,
    order_type_des,
    order_time,
    ib_algo_mkt=False,
    account_id=None,
    limit_order=False,
):

    # Print to console
    if variables.flag_debug_mode:
        print(f"Unique ID = {unique_id}: Sending Single Leg Order")

    # Get reqId
    order_id = variables.nextorderId
    variables.nextorderId += 1
    transmit = True

    # Create IB ALGO order, Place the order
    place_market_order(
        unique_id,
        contract,
        order_id,
        order_action,
        order_qty,
        account_id,
        transmit,
        entry_exit_order,
        order_type_des,
        order_time,
        ib_algo_mkt,
        limit_order,
    )

# Method to send order
def send_order(
    unique_id,
    action,
    order_type,
    combo_quantity,
    limit_price,
    trigger_price,
    trail_value,
    order_from_db=False,
    original_order_time=None,
    entry_price=None,
    order_description=None,
    lock_hash_for_db_order=None,
    reference_price=None,
    exit_type=None,
    ladder_id=None,
    sequence_id=None,
    atr_multiple=None,
    atr=None,
    incremental_combo=None,
    account_id=None,
    bypass_rm_check=None,
    execution_engine=False,
    limit_iv=None,
    trigger_iv=None,
):
    actual_entry_price = None



    # Combo _object for order placement, When CAS condition is triggered (for "ADD" we needed to take position in cas legs, with new unique ID)
    # (later the combo was updated to Existing combo + Incremental Combo), to avoid the issue where the order was waiting for locks to be freed on the tickers and
    # during that wait time the incremental combo was updated that is cas_legs combo was replaced by (existing combo + cas_legs_combo). to avoid this error storing the combo here
    # check if flag for incremental combo is false
    if incremental_combo == None:

        # Get combo obj
        local_stored_copy_of_combo_object = variables.unique_id_to_combo_obj[unique_id]

        # Ticker String
        ticker_string = make_informative_combo_string(local_stored_copy_of_combo_object)

    else:

        # Get incremental combo obj
        local_stored_copy_of_combo_object = (
            incremental_combo  # Get CAS Legs Combo Object
        )

        # Get final combo obj
        local_stored_copy_of_combo_object_final = variables.unique_id_to_combo_obj[
            unique_id
        ]

        # Ticker String
        ticker_string = make_informative_combo_string(
            local_stored_copy_of_combo_object_final
        )

    # Adjusting values
    limit_price = "None" if limit_price == "" else limit_price
    trigger_price = "None" if trigger_price == "" else trigger_price
    trail_value = "None" if trail_value == "" else trail_value

    # Selecting value of execution price to "None"
    reason_for_failed = None

    # Changing order type from 'Market' to 'MKT' for IBKR
    if order_type == "Market":
        order_type = "MKT"
        limit_price = "None"
        trigger_price = "None"
        trail_value = "None"

    # Entry_price
    if entry_price == None:

        entry_price = variables.unique_id_to_prices_dict[unique_id][action]



    # reference_price
    if order_type == "Trailing Stop Loss":
        reference_price = variables.unique_id_to_prices_dict[unique_id][action]
    else:
        reference_price = "None" if reference_price == None else reference_price

    # Current time when order is created
    last_update_time = order_time = datetime.datetime.now(variables.target_timezone_obj)

    if order_type in [
        "Limit",
        "Stop Loss",
        "Trailing Stop Loss", "Limit Volatility", "Stop Loss Volatility"
    ]:

        # save order in DB
        entry_price = -1
        status = "Pending"
        insert_combination_order_in_combo_status_db(
            unique_id,
            action,
            combo_quantity,
            order_type,
            entry_price,
            limit_price,
            trigger_price,
            reference_price,
            trail_value,
            status,
            order_time,
            ladder_id,
            sequence_id,
            atr_multiple,
            atr,
            reason_for_failed,
            account_id,
            ticker_string=ticker_string,
            bypass_rm_check=bypass_rm_check,
            execution_engine=execution_engine,
            limit_iv=limit_iv,
            trigger_iv=trigger_iv,
            actual_entry_price=actual_entry_price,
        )

        # Check if sequence id is not None
        if sequence_id != None:

            # Creatinf dict of values to update in sequence table
            sequence_table_values_dict = {
                "Order Time": order_time,
                "Last Update Time": order_time,
            }

            # Update order time and last update time in sequence table
            update_sequence_table_values(sequence_id, sequence_table_values_dict)

        # Check if sequence id is not None
        if sequence_id != None:

            # Get order details for sequence obj order
            variables.map_sequence_id_to_order_details[sequence_id] = [
                unique_id,
                action,
                combo_quantity,
                order_type,
                entry_price,
                limit_price,
                trigger_price,
                reference_price,
                trail_value,
                status,
                order_time,
                ladder_id,
                sequence_id,
            ]

        # Formatting Values
        try:
            entry_price = f"{float(entry_price):,.2f}"
        except Exception as e:
            pass
        try:
            limit_price = f"{float(limit_price):,.2f}"
        except Exception as e:
            pass
        try:
            trigger_price = f"{float(trigger_price):,.2f}"
        except Exception as e:
            pass
        try:
            reference_price = f"{float(reference_price):,.2f}"
        except Exception as e:
            pass
        try:
            trail_value = f"{float(trail_value):,.2f}"
        except Exception as e:
            pass

        # creating tuple of values to put in dataframe
        order_book_row_values = (
            unique_id,
            account_id,
            ticker_string,
            action,
            combo_quantity,
            order_type,
            order_time,
            last_update_time,
            entry_price,
            limit_price,
            trigger_price,
            reference_price,
            trail_value,
            status,
            reason_for_failed,
            ladder_id,
            sequence_id,
            atr_multiple,
            atr,
            bypass_rm_check,
            str(execution_engine),
            limit_iv,
            trigger_iv,
            actual_entry_price
        )

        # Creating dataframe for row data
        orders_book_row_df = pd.DataFrame(
            [order_book_row_values], columns=variables.order_book_table_df_columns
        )

        # Merge row with combo details dataframe
        variables.orders_book_table_dataframe = pd.concat(
            [variables.orders_book_table_dataframe, orders_book_row_df]
        )

        local_unique_id_list_of_selected_watchlist = copy.deepcopy(
            variables.unique_id_list_of_selected_watchlist
        )

        if (
            str(unique_id) in local_unique_id_list_of_selected_watchlist.split(",")
            or local_unique_id_list_of_selected_watchlist == "ALL"
        ):
            variables.screen.insert_combo_order_status_order_book(
                (
                    unique_id,
                    account_id,
                    ticker_string,
                    action,
                    combo_quantity,
                    order_type,
                    order_time,
                    last_update_time,
                    entry_price,
                    limit_price,
                    trigger_price,
                    reference_price,
                    trail_value,
                    status,
                    reason_for_failed,
                    ladder_id,
                    sequence_id,
                    atr_multiple,
                    atr,
                    bypass_rm_check,
                    str(execution_engine),
                    limit_iv,
                    trigger_iv,
                    actual_entry_price
                )
            )

        # Update order book
        variables.flag_orders_book_table_watchlist_changed = True
        variables.screen.update_orders_book_table_watchlist_changed()

    elif order_type in ["MKT", "IB Algo Market"]:

        # save copy of original order time
        original_order_time_stored = original_order_time

        # if original order time is none
        if original_order_time == None:

            # assign value of order time for market and ib algo market orders
            original_order_time = order_time

        flag_send_order = True

        # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
        if (
            bypass_rm_check == "False"
            and variables.flag_enable_rm_account_rules
            and variables.flag_account_liquidation_mode[account_id]
        ):

            time.sleep(variables.rm_checks_interval_if_failed)

            # if bypass rm checks value is false, flag_enable_rm_account_rules value is True and account is in liquidation mode
            if (
                bypass_rm_check == "False"
                and variables.flag_enable_rm_account_rules
                and variables.flag_account_liquidation_mode[account_id]
            ):

                # set flag to false
                flag_send_order = False

                if (
                    original_order_time
                    in variables.screen.order_book_table.get_children()
                ):
                    # converting value to string
                    original_order_time = str(original_order_time)

                    variables.screen.cancel_order(
                        selected_item=original_order_time,
                        updated_status="Failed",
                        reason_for_failed="Account Is In Liquidation Mode",
                    )

                    if ladder_id not in [None, "None", "N/A"]:

                        variables.screen.screen_scale_trader_obj.pause_scale_trade(
                            selected_item=ladder_id
                        )

                # if original order time is none then add failed order row in order table
                if original_order_time_stored == None:
                    # Init values
                    status = "Failed"
                    reason_for_failed = "Account Is In Liquidation Mode"
                    order_type = "Market" if order_type == "MKT" else "IB Algo Market"

                    # Add order row in gui
                    add_failed_mkt_order(
                        unique_id,
                        action,
                        combo_quantity,
                        order_type,
                        entry_price,
                        limit_price,
                        trigger_price,
                        reference_price,
                        trail_value,
                        status,
                        order_time,
                        ladder_id,
                        sequence_id,
                        atr_multiple,
                        atr,
                        reason_for_failed,
                        account_id,
                        ticker_string=ticker_string,
                        bypass_rm_check=bypass_rm_check,
                        limit_iv=limit_iv,
                        trigger_iv=trigger_iv,
                        actual_entry_price=actual_entry_price,
                    )

                # Error pop up
                error_title = f"For Account ID: {account_id}, Order cannot be triggered, \naccount is in liquidation mode"
                error_string = f"For Account ID: {account_id}, Order cannot be triggered, \naccount is in liquidation mode"

                variables.screen.display_error_popup(error_title, error_string)

        if (
            not trade_level_rm_check_result(bypass_rm_check, unique_id)
            and flag_send_order
        ):

            time.sleep(variables.rm_checks_interval_if_failed)

            if not trade_level_rm_check_result(bypass_rm_check, unique_id):

                # set flag to false
                flag_send_order = False

                if (
                    original_order_time
                    in variables.screen.order_book_table.get_children()
                ):
                    # converting value to string
                    original_order_time = str(original_order_time)

                    variables.screen.cancel_order(
                        selected_item=original_order_time,
                        updated_status="Failed",
                        reason_for_failed="Trade level RM check failed",
                    )

                    if ladder_id not in [None, "None", "N/A"]:
                        variables.screen.screen_scale_trader_obj.pause_scale_trade(
                            selected_item=ladder_id
                        )

                # if original order time is none then add failed order row in order table
                if original_order_time_stored == None:
                    # Init values
                    status = "Failed"
                    reason_for_failed = "Trade level RM check failed"
                    order_type = "Market" if order_type == "MKT" else "IB Algo Market"

                    # Add order row in gui
                    add_failed_mkt_order(
                        unique_id,
                        action,
                        combo_quantity,
                        order_type,
                        entry_price,
                        limit_price,
                        trigger_price,
                        reference_price,
                        trail_value,
                        status,
                        order_time,
                        ladder_id,
                        sequence_id,
                        atr_multiple,
                        atr,
                        reason_for_failed,
                        account_id,
                        ticker_string=ticker_string,
                        bypass_rm_check=bypass_rm_check,
                        limit_iv=limit_iv,
                        trigger_iv=trigger_iv,
                        actual_entry_price=actual_entry_price,

                    )

                # get details of which check in trade rm check failed
                failed_trade_checks_details = (
                    get_failed_checks_string_for_trade_rm_check(unique_id)
                )

                # Error pop up
                error_title = f"For Account ID: {account_id}, Order cannot be triggered, \nTrade level RM check failed"
                error_string = f"For Account ID: {account_id}, Order cannot be triggered, \nTrade level RM check failed :\n{failed_trade_checks_details}"

                variables.screen.display_error_popup(error_title, error_string)

        if flag_send_order:

            # Send order now
            # Combo _object for order placement
            combination_object = local_stored_copy_of_combo_object
            # Buy and Sell legs
            buy_legs = combination_object.buy_legs
            sell_legs = combination_object.sell_legs

            # All legs for sending orders.
            all_legs = buy_legs + sell_legs

            # Is it IB Algo Order?
            ib_algo_mkt = True if "IB Algo Market" in order_type else False

            # Checking if ib algo order is supported or not.
            if ib_algo_mkt:

                legs_does_not_support_algo = []

                for leg_obj in all_legs:
                    # Contract
                    contract = leg_obj.contract
                    temp_con_id = contract.conId

                    if (
                        variables.map_con_id_to_flag_supports_ib_algo_order[temp_con_id]
                    ) == False:
                        legs_does_not_support_algo.append(leg_obj)

                if len(legs_does_not_support_algo) > 0:
                    legs_info_string = make_informative_combo_string(
                        legs_does_not_support_algo, need_legs_desc=True
                    )
                    # Values
                    error_title = f"Unique ID: {unique_id}, IB Algo Order not supported"
                    error_string = f"Unique ID={unique_id} Following Legs: {legs_info_string}, does not support IB Algo Mkt Order. Regular Market order are sent for following legs."

                    # Split in to line
                    words = error_string.split()
                    new_string = ""
                    line_len = 0
                    for word in words:
                        if line_len + len(word) + 1 > 55:
                            new_string += "\n"
                            line_len = 0
                        if line_len > 0:
                            new_string += " "
                            line_len += 1
                        new_string += word
                        line_len += len(word)

                    # Display the popup
                    variables.screen.display_error_popup(error_title, new_string)

            # Init
            flag_tick_size = True

            if not execution_engine:

                ##### ACQUIRING LOCKS -- When Sending Market Orders ################
                # Acquire lock on order sending
                variables.order_sending_lock.acquire()
                ##### ACQUIRING LOCKS -- When Sending Market Orders ################
                try:
                    # Acquire lock on coninds
                    for leg_obj_for_order_lock in all_legs:

                        hash_for_lock = f"{leg_obj_for_order_lock.con_id}{account_id}"

                        if hash_for_lock in variables.order_lock:
                            pass
                        else:
                            variables.order_lock[hash_for_lock] = Lock()

                        variables.order_lock[hash_for_lock].acquire()

                    # Print to console
                    if variables.flag_debug_mode:
                        print(f"Unique ID: {unique_id}, Sending Orders Locks Acquired")
                except Exception as e:

                    # Print to console
                    if variables.flag_debug_mode:
                        print(f"Error in Acquiring order sending lock")

                # Release lock on order sending
                variables.order_sending_lock.release()

                # Sending order for each leg one by one
                for leg_obj in all_legs:

                    # Contract
                    contract = leg_obj.contract

                    # Order Quantity, Leg Quantity * Combo Quantity
                    order_qty = int(leg_obj.quantity) * int(combo_quantity)

                    # If action(user-input) is buy pass, else change buy to sell & sell to buy
                    order_action = leg_obj.action

                    # Change order action according to user input
                    if action == "BUY":
                        pass
                    elif action == "SELL":
                        # change leg_action (selling)
                        order_action = "BUY" if order_action == "SELL" else "SELL"

                    if order_from_db == False:
                        # Temp, Descriptions
                        entry_exit_order = "Market"
                        order_type_des = str(order_action)
                    else:
                        entry_exit_order = f"{order_description}"
                        order_type_des = str(order_action)

                    # print([entry_exit_order, order_action, ib_algo_mkt])

                    # When its a MKT Order(from GUI)
                    if order_from_db == False:
                        # Send Order Now
                        send_order_singe_leg(
                            unique_id,
                            contract,
                            order_qty,
                            order_action,
                            entry_exit_order,
                            order_type_des,
                            order_time,
                            ib_algo_mkt,
                            account_id,
                        )
                    else:
                        send_order_singe_leg(
                            unique_id,
                            contract,
                            order_qty,
                            order_action,
                            entry_exit_order,
                            order_type_des,
                            original_order_time,
                            ib_algo_mkt,
                            account_id,
                        )

            else:

                leg_to_bid_ask_spread_dict = {}

                # Sending order for each leg one by one
                for leg_obj in all_legs:

                    # Get con id
                    con_id = leg_obj.con_id

                    # get req id
                    req_id = variables.con_id_to_req_id_dict[con_id]

                    # Get bid price and ask price
                    bid_price, ask_price = (
                        variables.bid_price[req_id],
                        variables.ask_price[req_id],
                    )

                    # get tick size
                    tick_size = get_tick_size(bid_price, ask_price, con_id)

                    # check if execution engine method is limit mid
                    if variables.limit_price_selection_for_execution_engine in [
                        "Limit_Mid",
                        "Pegged_Market",
                        "Pegged_Midpoint",
                    ]:

                        # check if tick price is invalid
                        if tick_size == -1 or tick_size == "N/A":

                            flag_tick_size = False

                            break

                    # calcualte spread %
                    spread = ask_price - bid_price

                    leg_to_bid_ask_spread_dict[leg_obj] = spread

                if flag_tick_size:

                    # Find the key-value pair with the maximum value
                    max_pair = max(
                        leg_to_bid_ask_spread_dict.items(), key=lambda x: x[1]
                    )

                    all_legs = [max_pair[0]]

                    ##### ACQUIRING LOCKS -- When Sending Market Orders ################
                    # Acquire lock on order sending
                    variables.order_sending_lock.acquire()
                    ##### ACQUIRING LOCKS -- When Sending Market Orders ################

                    try:
                        # Acquire lock on coninds
                        for leg_obj_for_order_lock in all_legs:

                            hash_for_lock = (
                                f"{leg_obj_for_order_lock.con_id}{account_id}"
                            )

                            if hash_for_lock in variables.order_lock:
                                pass
                            else:
                                variables.order_lock[hash_for_lock] = Lock()

                            variables.order_lock[hash_for_lock].acquire()

                        # Print to console
                        if variables.flag_debug_mode:
                            print(
                                f"Unique ID: {unique_id}, Sending Orders Locks Acquired"
                            )
                    except Exception as e:

                        # Print to console
                        if variables.flag_debug_mode:
                            print(f"Error in Acquiring order sending lock")

                    # Release lock on order sending
                    variables.order_sending_lock.release()

                    # Sending order for each leg one by one
                    for leg_obj in all_legs:

                        limit_order = True

                        # Contract
                        contract = leg_obj.contract

                        # Order Quantity, Leg Quantity * Combo Quantity
                        order_qty = int(leg_obj.quantity) * int(combo_quantity)

                        # If action(user-input) is buy pass, else change buy to sell & sell to buy
                        order_action = leg_obj.action

                        # Change order action according to user input
                        if action == "BUY":
                            pass
                        elif action == "SELL":
                            # change leg_action (selling)
                            order_action = "BUY" if order_action == "SELL" else "SELL"

                        if order_from_db == False:
                            # Temp, Descriptions
                            entry_exit_order = "Market"
                            order_type_des = str(order_action)
                        else:
                            entry_exit_order = f"{order_description}"
                            order_type_des = str(order_action)

                        # When its a MKT Order(from GUI)
                        if order_from_db == False:
                            # Send Order Now
                            send_order_singe_leg(
                                unique_id,
                                contract,
                                order_qty,
                                order_action,
                                entry_exit_order,
                                order_type_des,
                                order_time,
                                ib_algo_mkt,
                                account_id,
                                limit_order,
                            )
                        else:

                            send_order_singe_leg(
                                unique_id,
                                contract,
                                order_qty,
                                order_action,
                                entry_exit_order,
                                order_type_des,
                                original_order_time,
                                ib_algo_mkt,
                                account_id,
                                limit_order,
                            )

            status = "Sent"

            # if tick size is invlaid
            if not flag_tick_size:

                status = "Failed"

                reason_for_failed = "Tick size not available"

            if order_from_db == False:

                # Change orderType from MKT to Market, for Viewing
                order_type = "IB Algo Market" if ib_algo_mkt else "Market"
                insert_combination_order_in_combo_status_db(
                    unique_id,
                    action,
                    combo_quantity,
                    order_type,
                    entry_price,
                    limit_price,
                    trigger_price,
                    reference_price,
                    trail_value,
                    status,
                    order_time,
                    ladder_id,
                    sequence_id,
                    atr_multiple,
                    atr,
                    reason_for_failed,
                    account_id,
                    ticker_string=ticker_string,
                    bypass_rm_check=bypass_rm_check,
                    execution_engine=execution_engine,
                    limit_iv=limit_iv,
                    trigger_iv=trigger_iv,
                    actual_entry_price=actual_entry_price
                )

                # Formatting Values
                try:
                    entry_price = f"{float(entry_price):,.2f}"
                except Exception as e:
                    pass
                try:
                    limit_price = f"{float(limit_price):,.2f}"
                except Exception as e:
                    pass
                try:
                    trigger_price = f"{float(trigger_price):,.2f}"
                except Exception as e:
                    pass
                try:
                    reference_price = f"{float(reference_price):,.2f}"
                except Exception as e:
                    pass
                try:
                    trail_value = f"{float(trail_value):,.2f}"
                except Exception as e:
                    pass

                # creating tuple of value to put in dataframe
                order_book_row_values = (
                    unique_id,
                    account_id,
                    ticker_string,
                    action,
                    combo_quantity,
                    order_type,
                    order_time,
                    last_update_time,
                    entry_price,
                    limit_price,
                    trigger_price,
                    reference_price,
                    trail_value,
                    status,
                    reason_for_failed,
                    ladder_id,
                    sequence_id,
                    atr_multiple,
                    atr,
                    bypass_rm_check,
                    str(execution_engine),
                    limit_iv,
                    trigger_iv,
                    actual_entry_price
                )

                # Creating dataframe for row data
                orders_book_row_df = pd.DataFrame(
                    [order_book_row_values],
                    columns=variables.order_book_table_df_columns,
                )

                # TODO KARAN CHECK THIS CODE STACK  - todo
                # Merge row with combo details dataframe
                variables.orders_book_table_dataframe = pd.concat(
                    [variables.orders_book_table_dataframe, orders_book_row_df]
                )

                # Getting all the unique id in the watchlist
                local_unique_id_list_of_selected_watchlist = copy.deepcopy(
                    variables.unique_id_list_of_selected_watchlist
                )

                # Insert the order in table if the UID is present in the watchlist or default WL(ALL) is selected.
                if (
                    str(unique_id)
                    in local_unique_id_list_of_selected_watchlist.split(",")
                    or local_unique_id_list_of_selected_watchlist == "ALL"
                ):
                    variables.screen.insert_combo_order_status_order_book(
                        (
                            unique_id,
                            account_id,
                            ticker_string,
                            action,
                            combo_quantity,
                            order_type,
                            order_time,
                            last_update_time,
                            entry_price,
                            limit_price,
                            trigger_price,
                            reference_price,
                            trail_value,
                            status,
                            reason_for_failed,
                            ladder_id,
                            sequence_id,
                            atr_multiple,
                            atr,
                            bypass_rm_check,
                            str(execution_engine),
                            limit_iv,
                            trigger_iv,
                            actual_entry_price
                        )
                    )

                # Update order book
                variables.flag_orders_book_table_watchlist_changed = True
                variables.screen.update_orders_book_table_watchlist_changed()

                # update/put order ID's in the combination table.
                insert_order_ids_in_combo_status(unique_id, order_time)
            else:
                # update status,
                # update the DB for combination. change status to sent, and changeorder time, change entry_price also
                # original_order_time unique_id, original_order_time, last_update_time,entry_price, status
                update_combination_order_status_in_db(
                    unique_id,
                    original_order_time,
                    order_time,
                    entry_price,
                    status,
                    combo_quantity,
                    exit_type,
                    actual_entry_price=actual_entry_price
                )

                # Update Combination order status in order_book_table
                variables.screen.update_combo_order_status_in_order_book(
                    original_order_time,
                    order_time,
                    entry_price,
                    reference_price,
                    status,
                    combo_quantity,
                    exit_type,
                    actual_entry_price=actual_entry_price
                )

                # update/put order ID's in the combination table.
                insert_order_ids_in_combo_status(unique_id, original_order_time)

                # Order Time, will be used to free locks
                order_time = original_order_time

            ####### RELEASE LOCKS -- When Sending Market Orders  ##########
            # Init counter
            counter = 0

            # Wait for max_time_order_fill seconds then free the locks
            while counter <= int(
                variables.max_time_order_fill / variables.sleep_order_status_update
            ):

                # If orders are not filled or cancelled wait
                if check_all_orders_filled(unique_id, order_time) > 0:
                    time.sleep(variables.sleep_order_status_update)

                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Waiting for locks to be freed, Unique ID: {unique_id} {counter}"
                        )
                    counter += 1

                # if all order for Unique ID is filled or cancelled, break and free locks
                else:
                    break

            # Release lock on coninds
            for leg_obj_for_order_lock in all_legs:

                hash_for_lock = f"{leg_obj_for_order_lock.con_id}{account_id}"

                if hash_for_lock in variables.order_lock:

                    variables.order_lock[hash_for_lock].release()

            # Print to console
            if variables.flag_debug_mode:
                print(f"Unique ID: {unique_id}, Sending Orders Locks Released")
            ####### RELEASE LOCKS -- When Sending Market Orders  ##########

    else:
        print(f"Unique ID = {unique_id}: wrong order type received = {order_type=}")

    # Release Lock on the order DB
    if lock_hash_for_db_order != None:
        variables.order_lock[lock_hash_for_db_order].release()


# Function to monitior and send orders
def monitor_and_send_order():

    # print("Monitoring")
    # get all the open/pending order from the db Quantity, TIme, unique ID, Prices all 4

    pending_orders = get_pending_orders()

    if not variables.flag_account_checks_completed_first_time:

        return

    for _, row in pending_orders.iterrows():

        unique_id = row["Unique ID"]
        order_action = row["Action"]
        combo_quantity = row["#Lots"]
        order_type = row["Order Type"]

        limit_price = row["Limit Price"].strip()
        trigger_price = row["Trigger Price"].strip()
        reference_price = row["Reference Price"].strip()
        trail_value = row["Trail Value"].strip()

        ladder_id = str(row["Ladder ID"]).strip()
        sequence_id = str(row["Sequence ID"]).strip()
        account_id = str(row["Account ID"]).strip()
        bypass_rm_check = str(row["Bypass RM Check"]).strip()

        flag_use_execution_engine = row["Execution Engine"].strip()

        limit_iv = row["Limit IV"].strip()
        trigger_iv = row["Trigger IV"].strip()

        # set boolean value for flag for execution engine
        if flag_use_execution_engine == "True":

            flag_use_execution_engine = True

        else:

            flag_use_execution_engine = False

        if order_type == "Limit":
            limit_price = float(limit_price)
        elif order_type in ["Stop Loss", "STP Market", "STP IB Algo Market"]:
            trigger_price = float(trigger_price)
        elif order_type == "Trailing Stop Loss":
            reference_price = float(reference_price)
            trail_value = float(trail_value)

        order_from_db = True
        order_time = row["Order Time"]

        buy_price, sell_price = (
            variables.unique_id_to_prices_dict[unique_id]["BUY"],
            variables.unique_id_to_prices_dict[unique_id]["SELL"],
        )

        if buy_price == None or sell_price == None:
            continue
        else:
            buy_price, sell_price = float(buy_price), float(sell_price)

        ########## Testing: Start ################
        # KARAN(CHANGE) TESTING
        if variables.flag_simulate_prices:
            buy_sell_csv = pd.read_csv(variables.buy_sell_csv)

            for _, row in buy_sell_csv.iterrows():
                if unique_id == int(row["Unique ID"]):
                    buy_price = float(row["BUY"])
                    sell_price = float(row["SELL"])
        ########## Testing : End ################

        level_reached = False
        if order_type == "Limit":
            order_description = "Limit"
            if order_action == "BUY" and (buy_price <= limit_price):
                level_reached = True
                entry_price = buy_price

                # Print to console
                if variables.flag_debug_mode:
                    print("LIMIT BUY buy_price <= limit_price", buy_price, limit_price)

            if order_action == "SELL" and (sell_price >= limit_price):
                level_reached = True
                entry_price = sell_price

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        "LIMIT SELL sell_price >= limit_price", sell_price, limit_price
                    )

        elif order_type in ["Stop Loss", "STP Market", "STP IB Algo Market"]:

            order_description = f"{order_type}"

            if order_type in ["STP Market", "STP IB Algo Market"]:

                # Get Position,
                try:
                    position_for_unique_id = variables.map_unique_id_to_positions[
                        unique_id
                    ]

                    if position_for_unique_id < 0:
                        order_action = "BUY"
                    elif position_for_unique_id > 0:
                        order_action = "SELL"
                    else:
                        continue

                    combo_quantity = abs(position_for_unique_id)
                except:
                    pass

            if order_action == "BUY" and (buy_price >= trigger_price):
                level_reached = True
                entry_price = buy_price

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        "Stop Loss BUY buy_price >= trigger_price",
                        buy_price,
                        trigger_price,
                    )

            if order_action == "SELL" and (sell_price <= trigger_price):
                level_reached = True
                entry_price = sell_price

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        "Stop Loss SELL sell_price <= trigger_price",
                        sell_price,
                        trigger_price,
                    )

        elif order_type == "Trailing Stop Loss":

            order_description = "Trailing Stop Loss"

            if order_action == "BUY" and (buy_price >= reference_price + trail_value):
                level_reached = True
                entry_price = buy_price

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        "Trailing Stop Loss BUY buy_price >= reference_price + trail_value",
                        buy_price,
                        reference_price + trail_value,
                    )

            if order_action == "SELL" and (sell_price <= reference_price - trail_value):
                level_reached = True
                entry_price = sell_price

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        "Trailing Stop Loss SEll sell_price <= reference_price - trail_value",
                        buy_price,
                        reference_price - trail_value,
                    )

        elif order_type in ['Limit Volatility']:

            order_description = "Limit"

            # Get unique id for selecte row
            unique_id = int(unique_id)

            # local copy of 'unique_id_to_combo_obj'
            local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

            # get combo object
            combo_obj = local_unique_id_to_combo_obj[unique_id]

            # get all legs
            all_legs = combo_obj.buy_legs + combo_obj.sell_legs

            # init
            req_id_list = []

            for leg_obj_item in all_legs:
                req_id = variables.con_id_to_req_id_dict[leg_obj_item.con_id]

                req_id_list.append(req_id)



            # init
            current_iv = 0

            try:



                # iterate request ids and legs
                for req_id, leg_obj in zip(req_id_list, all_legs):



                    if order_action.upper() in 'BUY':

                        # calculate buy implied volatilitty and sell implied volatility
                        current_iv += (variables.options_iv_bid[req_id] if leg_obj.action.upper() in 'BUY' else
                                   variables.options_iv_ask[req_id]) * leg_obj.quantity * leg_obj.multiplier * (
                                      1 if leg_obj.action.upper() in 'BUY' else -1)

                    else:

                        current_iv += (variables.options_iv_bid[req_id] if leg_obj.action.upper() in 'SELL' else
                                    variables.options_iv_ask[req_id]) * leg_obj.quantity * leg_obj.multiplier * (
                                       1 if leg_obj.action.upper() in 'BUY' else -1)



            except Exception as e:

                current_iv = None

                if variables.flag_debug_mode:
                    print(f"Exception for getting implied volatility, Exp: {e}")

                continue

            #print([current_iv, limit_iv, order_action])



            if current_iv is None:

                continue

            current_iv *= 100

            if current_iv <= float(limit_iv) and order_action == 'BUY':

                level_reached = True
                entry_price = buy_price

            elif current_iv >= float(limit_iv) and order_action == 'SELL':

                level_reached = True
                entry_price = sell_price

        elif order_type in ['Stop Loss Volatility']:

            order_description = 'Stop Loss'

            # Get unique id for selecte row
            unique_id = int(unique_id)

            # local copy of 'unique_id_to_combo_obj'
            local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

            # get combo object
            combo_obj = local_unique_id_to_combo_obj[unique_id]

            # get all legs
            all_legs = combo_obj.buy_legs + combo_obj.sell_legs

            # init
            req_id_list = []

            for leg_obj_item in all_legs:
                req_id = variables.con_id_to_req_id_dict[leg_obj_item.con_id]

                req_id_list.append(req_id)

            # init
            current_iv = 0

            try:

                # iterate request ids and legs
                for req_id, leg_obj in zip(req_id_list, all_legs):

                    if order_action.upper() == 'BUY':

                        # calculate buy implied volatilitty and sell implied volatility
                        current_iv += (variables.options_iv_bid[req_id] if leg_obj.action.upper() == 'BUY' else
                                   variables.options_iv_ask[req_id]) * leg_obj.quantity * leg_obj.multiplier * (
                                      1 if leg_obj.action.upper() == 'BUY' else -1)

                    else:

                        current_iv += (variables.options_iv_bid[req_id] if leg_obj.action.upper() == 'SELL' else
                                    variables.options_iv_ask[req_id]) * leg_obj.quantity * leg_obj.multiplier * (
                                       1 if leg_obj.action.upper() == 'BUY' else -1)

            except Exception as e:

                if variables.flag_debug_mode:
                    print(f"Exception for getting implied volatility, Exp: {e}")

                continue

            current_iv *= 100

            if current_iv >= float(trigger_iv) and order_action == 'BUY':
                level_reached = True
                entry_price = buy_price

            elif current_iv <= float(trigger_iv) and order_action == 'SELL':
                level_reached = True
                entry_price = sell_price

        if level_reached:

            # Check if account is not available in current session
            if account_id not in variables.current_session_accounts:

                # check if order time is in tbale
                if order_time in variables.screen.order_book_table.get_children():
                    # converting value to string
                    order_time = str(order_time)

                    # mark order as failed
                    variables.screen.cancel_order(
                        selected_item=order_time,
                        updated_status="Failed",
                        reason_for_failed="Account ID not available in current session",
                    )
                    continue

            if order_type in ["STP Market", "STP IB Algo Market"]:
                exit_type = f"EXIT ({order_action})"
            else:
                exit_type = None

            order_type = "MKT"
            order_from_db = True
            flag_send_this_order = False

            try:

                # Getting the Order Type if order is for the sequence of a ladder.
                if ladder_id not in [None, "None"]:
                    order_type = get_ladder_or_sequence_column_value_from_db(
                        ladder_id=ladder_id, column_name_as_in_db="Order Type"
                    )

            except Exception as e:

                # Print to console
                if variables.flag_debug_mode:

                    print(
                        f"For Ladder ID: {ladder_id}, Query for getting ladder order type failed"
                    )

            # Only Send this order if the lock is not acquired.
            lock_hash_for_db_order = f"{order_time}{unique_id}{limit_price}{trigger_price}{trail_value}{account_id}"

            # Checking if we have this lock in order_lock dict
            if lock_hash_for_db_order in variables.order_lock:
                try:

                    if variables.order_lock[lock_hash_for_db_order].acquire():
                        pass
                    else:
                        flag_send_this_order = True

                except Exception as e:

                    if variables.flag_debug_mode:
                        print(f"Inside monitor order, Exp: {e}")

            else:

                # Make lock and send the order
                variables.order_lock[lock_hash_for_db_order] = Lock()
                variables.order_lock[lock_hash_for_db_order].acquire()
                flag_send_this_order = True

            if flag_send_this_order:

                # Send order in a separate thread
                send_order_thread = threading.Thread(
                    target=send_order,
                    args=(
                        unique_id,
                        order_action,
                        order_type,
                        combo_quantity,
                        limit_price,
                        trigger_price,
                        trail_value,
                        order_from_db,
                        order_time,
                        entry_price,
                        order_description,
                        lock_hash_for_db_order,
                        reference_price,
                        exit_type,
                    ),
                    kwargs={
                        "ladder_id": ladder_id,
                        "account_id": account_id,
                        "bypass_rm_check": bypass_rm_check,
                        "execution_engine": flag_use_execution_engine,
                    },
                )
                send_order_thread.start()

# Method to add dummy failed order
def add_failed_mkt_order(
    unique_id,
    action,
    combo_quantity,
    order_type,
    entry_price,
    limit_price,
    trigger_price,
    reference_price,
    trail_value,
    status,
    order_time,
    ladder_id,
    sequence_id,
    atr_multiple,
    atr,
    reason_for_failed,
    account_id,
    ticker_string=None,
    bypass_rm_check=None,
    execution_engine=False,
limit_iv=None,
        trigger_iv=None,
actual_entry_price=None
):

    if not is_float(actual_entry_price):

        return

    # Current time when order is created
    last_update_time = datetime.datetime.now(variables.target_timezone_obj)

    insert_combination_order_in_combo_status_db(
        unique_id,
        action,
        combo_quantity,
        order_type,
        entry_price,
        limit_price,
        trigger_price,
        reference_price,
        trail_value,
        status,
        order_time,
        ladder_id,
        sequence_id,
        atr_multiple,
        atr,
        reason_for_failed,
        account_id,
        ticker_string=ticker_string,
        bypass_rm_check=bypass_rm_check,
        execution_engine=False,
        limit_iv=limit_iv,
        trigger_iv=trigger_iv,
    )

    # Formatting Values
    try:
        entry_price = f"{float(entry_price):,.2f}"
    except Exception as e:
        pass
    try:
        limit_price = f"{float(limit_price):,.2f}"
    except Exception as e:
        pass
    try:
        trigger_price = f"{float(trigger_price):,.2f}"
    except Exception as e:
        pass
    try:
        reference_price = f"{float(reference_price):,.2f}"
    except Exception as e:
        pass
    try:
        trail_value = f"{float(trail_value):,.2f}"
    except Exception as e:
        pass

    # creating tuple of value to put in dataframe
    order_book_row_values = (
        unique_id,
        account_id,
        ticker_string,
        action,
        combo_quantity,
        order_type,
        order_time,
        last_update_time,
        entry_price,
        limit_price,
        trigger_price,
        reference_price,
        trail_value,
        status,
        reason_for_failed,
        ladder_id,
        sequence_id,
        atr_multiple,
        atr,
        bypass_rm_check,
        str(execution_engine),
    )

    # Creating dataframe for row data
    orders_book_row_df = pd.DataFrame(
        [order_book_row_values], columns=variables.order_book_table_df_columns
    )

    # TODO KARAN CHECK THIS CODE STACK  - todo
    # Merge row with combo details dataframe
    variables.orders_book_table_dataframe = pd.concat(
        [variables.orders_book_table_dataframe, orders_book_row_df]
    )

    # Getting all the unique id in the watchlist
    local_unique_id_list_of_selected_watchlist = copy.deepcopy(
        variables.unique_id_list_of_selected_watchlist
    )

    # Insert the order in table if the UID is present in the watchlist or default WL(ALL) is selected.
    if (
        str(unique_id) in local_unique_id_list_of_selected_watchlist.split(",")
        or local_unique_id_list_of_selected_watchlist == "ALL"
    ):
        variables.screen.insert_combo_order_status_order_book(
            (
                unique_id,
                account_id,
                ticker_string,
                action,
                combo_quantity,
                order_type,
                order_time,
                last_update_time,
                entry_price,
                limit_price,
                trigger_price,
                reference_price,
                trail_value,
                status,
                reason_for_failed,
                ladder_id,
                sequence_id,
                atr_multiple,
                atr,
                bypass_rm_check,
                str(execution_engine),
            )
        )

    # Update order book
    variables.flag_orders_book_table_watchlist_changed = True
    variables.screen.update_orders_book_table_watchlist_changed()

    # update/put order ID's in the combination table.
    insert_order_ids_in_combo_status(unique_id, order_time)

    time.sleep(0.5)
