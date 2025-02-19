from com.variables import *
from com.order_execution import *
from com.prices import *
from com.combination_helper import *
from com.trade_rm_check_result_module import *


# Method to validate if value is float
def is_float_upload_order(value):
    try:
        # Check if the value can be converted to a float
        float_value = float(value)

        # Return true if no exception occured
        return True

    except Exception as e:
        # Return false if value cannot be converted to float
        return False


# Check validaity of values in csv file
def check_validity_of_dataframe(orders_dataframe_to_be_checked):
    # Getting list of valid columns
    columns_for_orders_csv = copy.deepcopy(variables.columns_for_download_orders_to_csv)

    # Getting columns of dataframe to-be-checked
    order_dataframe_columns = orders_dataframe_to_be_checked.columns

    # check if number of columns in csv file is correct
    if len(columns_for_orders_csv) != len(order_dataframe_columns):
        error_title = f"Error columns are not matching"
        error_string = f"Columns are not matching in file, Number of columns is wrong"

        return False, error_title, error_string

    # Check if columns in order dataframe for upload orders are valid
    for allowed_columns_name, user_input_col_name in zip(
        columns_for_orders_csv, order_dataframe_columns
    ):
        if allowed_columns_name != user_input_col_name:
            error_title = f"Error columns are not matching"
            error_string = f"Columns are not matching in file, Invalid column: '{user_input_col_name}'"

            return False, error_title, error_string

    # Define the valid values
    valid_values_in_action = {"BUY", "SELL"}

    # Valid values for column order type
    valid_values_in_order_type = set(
        [
            "MARKET",
            "LIMIT",
            "STOP LOSS",
            "TRAILING STOP LOSS",
            "IB ALGO MARKET",
            "STOP LOSS PREMIUM",
            "TAKE PROFIT PREMIUM",
            "TRAILING SL PREMIUM",
            "STOP LOSS CANDLE",
            "TAKE PROFIT CANDLE",
        ]
    )

    # Convert all values in column 'Action' to upper case
    orders_dataframe_to_be_checked["Action"] = orders_dataframe_to_be_checked[
        "Action"
    ].str.upper()

    # Convert all values in column 'Order type' to upper case
    orders_dataframe_to_be_checked["Order Type"] = orders_dataframe_to_be_checked[
        "Order Type"
    ].str.upper()

    # Get latest combo prices
    prices_unique_id = copy.deepcopy(variables.unique_id_to_prices_dict)

    local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

    # Mapped upper values to standard values of order type
    order_type_values_upper_to_standard_dict = {
        "MARKET": "Market",
        "LIMIT": "Limit",
        "STOP LOSS": "Stop Loss",
        "TRAILING STOP LOSS": "Trailing Stop Loss",
        "IB ALGO MARKET": "IB Algo Market",
    }

    # To check values are valid or not
    for indx, row in orders_dataframe_to_be_checked.iterrows():
        # Get values from row to validate
        unique_id = str(row["Unique ID"]).strip()
        buy_sell_action = str(row["Action"]).strip()
        order_type = str(row["Order Type"]).strip()
        quantity = str(row["#Lots"]).strip()
        limit_price = str(row["Limit Price"]).strip()
        trigger_price = str(row["Trigger Price"]).strip()
        trail_value = str(row["Trail Value"]).strip()
        atr_multiple = str(row["ATR Multiple"]).strip()
        account_id = str(row["Account ID"]).strip()
        bypass_rm_check = str(row["Bypass RM Check"]).strip()

        error_in_column_unique_id_action_order_type_quantity = ""
        flag_is_error_inside_unique_id_action_order_type_quantity = False

        # Checking if unique id is non - integer
        if not is_integer(unique_id):
            error_in_column_unique_id_action_order_type_quantity += "Unique Id, "

            flag_is_error_inside_unique_id_action_order_type_quantity = True

        else:
            unique_id = int(unique_id)

        # Checking if account id is present in current session accounts
        if account_id not in variables.current_session_accounts:
            error_title = f"Error Row no - {indx + 2}, Account Id Not Available"
            error_string = f"Row no - {indx + 2}, Provided Account Id is Not Available in Current Session"

            return False, error_title, error_string

        # Checking if Action value none of 'BUY' or 'SELL'
        if buy_sell_action not in valid_values_in_action:
            error_in_column_unique_id_action_order_type_quantity += "Action, "

            flag_is_error_inside_unique_id_action_order_type_quantity = True

        # Checking if Order Type value is invalid
        if order_type not in valid_values_in_order_type:
            error_in_column_unique_id_action_order_type_quantity += "Order Type, "

            flag_is_error_inside_unique_id_action_order_type_quantity = True

        # Checking if quantity is non integer
        if not is_integer(quantity):
            error_in_column_unique_id_action_order_type_quantity += "Quantity, "

            flag_is_error_inside_unique_id_action_order_type_quantity = True

        # Creating error string for error in unique id, action, order type, quantity
        if flag_is_error_inside_unique_id_action_order_type_quantity:
            error_title = f"Error Row no - {indx + 2}, Invalid values"
            error_string = make_multiline_mssg_for_gui_popup(
                f"Row no - {indx + 2}, Please provide a valid values for {error_in_column_unique_id_action_order_type_quantity[:-2]} columns."
            )

            return False, error_title, error_string

        # Check if unique id is valid
        if not unique_id in local_unique_id_to_combo_obj:
            error_title = f"Error Row no - {indx + 2}, Invalid Unique Id"
            error_string = (
                f"Row no - {indx + 2}, Please provide a valid Unique Id for Order"
            )

            return False, error_title, error_string

        # Check if bypass rm check has valid value
        if bypass_rm_check not in ["True", "False"]:
            error_title = f"Error Row no - {indx + 2}, Invalid Bypass RM Check"
            error_string = (
                f"Row no - {indx + 2}, Please provide a valid Bypass RM Check for Order"
            )

            return False, error_title, error_string

            # Get buy and sell price for unique id
        try:
            current_buy_price, current_sell_price = (
                prices_unique_id[unique_id]["BUY"],
                prices_unique_id[unique_id]["SELL"],
            )
        except Exception as e:
            error_title = f"Error Row no - {indx + 2}, Invalid Unique Id"
            error_string = (
                f"Row no - {indx + 2}, Please provide a valid Unique Id for Order"
            )

            return False, error_title, error_string

        # Validating we have prices for the combo
        if buy_sell_action == "BUY" and current_buy_price == None:
            error_title = f"Error Row no - {indx + 2}, Buy Price is unavailable."
            error_string = f"Row no - {indx + 2}, Can not buy combo because buy price is unavailable"

            return error_title, error_string
        elif buy_sell_action == "SELL" and current_sell_price == None:
            error_title = f"Error Row no - {indx + 2}, Sell Price is unavailable."
            error_string = f"Row no - {indx + 2}, Can not sell combo because sell price is unavailable"

            return error_title, error_string

        else:
            try:
                current_buy_price = (
                    float(current_buy_price) if current_buy_price != None else None
                )
                current_sell_price = (
                    float(current_sell_price) if current_sell_price != None else None
                )
            except Exception as e:
                print("Exception Inside Trade Combo, {e}")

                error_title = f"Error Row no - {indx + 2}, Price is unavailable."
                error_string = f"Row no - {indx + 2}, Can not {buy_sell_action} combo because price is unavailable"

                return error_title, error_string

        if order_type in [
            "STOP LOSS PREMIUM",
            "TAKE PROFIT PREMIUM",
            "TRAILING SL PREMIUM",
        ]:
            # get combo object
            # Get combo object using unique ids
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )

            combo_obj = local_unique_id_to_combo_obj[unique_id]

            # init
            flag_premium = False

            # get all legs
            all_legs = combo_obj.buy_legs + combo_obj.sell_legs

            # check if any leg is OPT or FOP
            for leg_obj in all_legs:
                if leg_obj.sec_type in ["OPT", "FOP"]:
                    # set value to True
                    flag_premium = True

            # if flag is true
            if not flag_premium:
                error_title = f"Error Row no - {indx + 2}, No OPT or FOP available for premium order"
                error_string = f"Row no - {indx + 2}, Unique-Id - {unique_id}, No OPT or FOP available for premium order"

                return False, error_title, error_string

            premium_dict = variables.screen.get_premium_for_orders(all_legs)

            if premium_dict == None:
                error_title = f"Error Row no - {indx + 2}, Could not get premium for premium order"
                error_string = f"Row no - {indx + 2}, Unique-Id - {unique_id}, Could not get premium for premium order"

                return False, error_title, error_string

            try:
                # dict for combo prices
                local_unique_id_to_prices_dict = copy.deepcopy(
                    variables.unique_id_to_prices_dict
                )

                current_buy_price, current_sell_price = (
                    local_unique_id_to_prices_dict[unique_id]["BUY"],
                    local_unique_id_to_prices_dict[unique_id]["SELL"],
                )

                current_price = (current_buy_price + current_sell_price) / 2

            except Exception as e:
                if variables.flag_debug_mode:
                    print(
                        f"Exception inside getting current price for stop loss premium, Exp: {e}"
                    )

                current_price = "N/A"

                error_title = f"Error Row no - {indx + 2}, Could not get current price for premium order"
                error_string = f"Row no - {indx + 2}, Unique-Id - {unique_id}, Could not get current price for premium order"

                return False, error_title, error_string

            # set order type based on premium order type provided
            if order_type == "STOP LOSS PREMIUM":
                order_type = "STOP LOSS"

                # getting value of trigger price to refill
                if premium_dict != None and is_float_upload_order(current_price):
                    net_premium = premium_dict["Stop Loss Premium"]

                    # check if it is float
                    if is_float_upload_order(net_premium):
                        # get trigger price
                        if buy_sell_action.upper() == "BUY":
                            value_to_prefill = current_price + abs(net_premium)

                        else:
                            value_to_prefill = current_price - abs(net_premium)

                        value_to_prefill = round(value_to_prefill, 2)

                    else:
                        value_to_prefill = "N/A"

                else:
                    value_to_prefill = "N/A"

                # overwrite values
                trigger_price = value_to_prefill

                atr_multiple = "None"

                # Make change in df
                orders_dataframe_to_be_checked.at[indx, "Order Type"] = order_type

                orders_dataframe_to_be_checked.at[indx, "Trigger Price"] = trigger_price

                orders_dataframe_to_be_checked.at[indx, "ATR Multiple"] = "None"

            elif order_type == "TAKE PROFIT PREMIUM":
                order_type = "LIMIT"

                # getting value of trigger price to refill
                if premium_dict != None and is_float_upload_order(current_price):
                    net_premium = premium_dict["Take Profit Premium"]

                    # check if it is float
                    if is_float_upload_order(net_premium):
                        # get trigger price
                        if buy_sell_action.upper() == "BUY":
                            value_to_prefill = current_price - abs(net_premium)

                        else:
                            value_to_prefill = current_price + abs(net_premium)

                        value_to_prefill = round(value_to_prefill, 2)

                    else:
                        value_to_prefill = "N/A"

                else:
                    value_to_prefill = "N/A"

                # overwrite values
                limit_price = value_to_prefill

                atr_multiple = "None"

                # Make change in df
                orders_dataframe_to_be_checked.at[indx, "Order Type"] = order_type

                orders_dataframe_to_be_checked.at[indx, "Limit Price"] = limit_price

                orders_dataframe_to_be_checked.at[indx, "ATR Multiple"] = "None"

            elif order_type == "TRAILING SL PREMIUM":
                order_type = "TRAILING STOP LOSS"

                # getting value of trigger price to refill
                if premium_dict != None and is_float_upload_order(current_price):
                    net_premium = premium_dict["Trailing Stop Loss Premium"]

                    # check if it is float
                    if is_float_upload_order(net_premium):
                        value_to_prefill = abs(net_premium)

                        value_to_prefill = round(value_to_prefill, 2)

                    else:
                        value_to_prefill = "N/A"

                else:
                    value_to_prefill = "N/A"

                # overwrite values
                trail_value = value_to_prefill
                atr_multiple = "None"

                # Make change in df
                orders_dataframe_to_be_checked.at[indx, "Order Type"] = order_type

                orders_dataframe_to_be_checked.at[indx, "Trail Value"] = trail_value

                orders_dataframe_to_be_checked.at[indx, "ATR Multiple"] = "None"

        if order_type in ["STOP LOSS CANDLE", "TAKE PROFIT CANDLE"]:
            # set order type based on premium order type provided
            if order_type == "STOP LOSS CANDLE":
                order_type = "STOP LOSS"

                # Init
                value_to_prefill = "N/A"

                # get last candle high or low price
                try:
                    # check if action is sell
                    if buy_sell_action.upper() == "BUY":
                        value_to_prefill = (
                            variables.map_unique_id_to_candle_for_order_values[
                                unique_id
                            ]["High Candle Value"]
                        )

                    # check if action is buy
                    else:
                        value_to_prefill = (
                            variables.map_unique_id_to_candle_for_order_values[
                                unique_id
                            ]["Low Candle Value"]
                        )

                except Exception as e:
                    # print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception inside getting current price for stop loss premium, Exp: {e}"
                        )

                    # set value to N/A
                    value_to_prefill = "N/A"

                # overwrite values
                trigger_price = value_to_prefill

                atr_multiple = "None"

                # Make change in df
                orders_dataframe_to_be_checked.at[indx, "Order Type"] = order_type

                orders_dataframe_to_be_checked.at[indx, "Trigger Price"] = trigger_price

                orders_dataframe_to_be_checked.at[indx, "ATR Multiple"] = "None"

            elif order_type == "TAKE PROFIT CANDLE":
                order_type = "LIMIT"

                # Init
                value_to_prefill = "N/A"

                # get last candle high or low price
                try:
                    # check if action is sell
                    if buy_sell_action.upper() == "SELL":
                        value_to_prefill = (
                            variables.map_unique_id_to_candle_for_order_values[
                                unique_id
                            ]["High Candle Value"]
                        )

                    # check if action is buy
                    else:
                        value_to_prefill = (
                            variables.map_unique_id_to_candle_for_order_values[
                                unique_id
                            ]["Low Candle Value"]
                        )

                except Exception as e:
                    # print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception inside getting current price for stop loss premium, Exp: {e}"
                        )

                    # set value to N/A
                    value_to_prefill = "N/A"

                # overwrite values
                limit_price = value_to_prefill

                atr_multiple = "None"

                # Make change in df
                orders_dataframe_to_be_checked.at[indx, "Order Type"] = order_type

                orders_dataframe_to_be_checked.at[indx, "Limit Price"] = limit_price

                orders_dataframe_to_be_checked.at[indx, "ATR Multiple"] = "None"

        # Limit Orders
        if order_type == "LIMIT":
            order_type = "LIMIT"
            try:
                limit_price = float(limit_price)

                # Check if limit price is NaN
                if math.isnan(limit_price):
                    raise Exception(f"Error Row no - {indx + 2}, Limit Price is NULL")

            except Exception as e:
                error_title = f"Error Row no - {indx + 2}, Missing Limit Price"
                error_string = f"Row no - {indx + 2}, Unique-Id - {unique_id}, Please provide a Limit Price for Limit Order"

                return False, error_title, error_string

            if (order_type == "LIMIT") and (
                buy_sell_action == "BUY" and current_buy_price < limit_price
            ):
                error_title = f"Error Row no - {indx + 2}, Invalid Limit Price."
                error_string = make_multiline_mssg_for_gui_popup(
                    f"Row no - {indx + 2}, Unique-Id - {unique_id}, Limit Price for Buy Order must be less than current Buy Price"
                )

                return False, error_title, error_string

            elif (order_type == "LIMIT") and (
                buy_sell_action == "SELL" and current_sell_price > limit_price
            ):
                error_title = f"Error Row no - {indx + 2}, Invalid Limit Price"
                error_string = make_multiline_mssg_for_gui_popup(
                    f"Row no - {indx + 2}, Unique-Id - {unique_id}, Limit Price for Sell Order must be greater than current Sell Price"
                )

                return False, error_title, error_string

        # Stop Loss Orders
        elif order_type == "STOP LOSS":
            print(atr_multiple)

            # Check if both trigger price and atr multiple is empty
            if trigger_price == "None" and atr_multiple == "None":
                error_title = (
                    f"Error, Row no - {indx + 2}, Invalid combination of values"
                )
                error_string = make_multiline_mssg_for_gui_popup(
                    f"Error, Row no - {indx + 2}, Values for both Trigger Price and ATR Multiple must not be empty."
                )

                return False, error_title, error_string

            # Check if trigger price is valid
            elif trigger_price != "None" and atr_multiple == "None":
                try:
                    trigger_price = float(trigger_price)

                    # Check if trigger price is NaN
                    if math.isnan(trigger_price):
                        raise Exception(
                            f"Error Row no - {indx + 2}, Trigger Price is NULL"
                        )

                except Exception as e:
                    error_title = f"Error Row no - {indx + 2}, Missing Trigger Price"
                    error_string = make_multiline_mssg_for_gui_popup(
                        f"Row no - {indx + 2}, Unique-Id - {unique_id}, Please provide a Trigger Price for Stop Loss Order"
                    )

                    return False, error_title, error_string

            # Check if atr multiple is valid and have valid trigger price value
            elif (trigger_price == "None" and atr_multiple != "None") or (
                trigger_price != "None" and atr_multiple != "None"
            ):
                # Get ATR value
                atr = get_atr_value_for_unique_id(unique_id)

                # If atr is N/A return error
                if atr == "N/A":
                    error_title = f"Error, Row no - {indx + 2}, For Unique ID: {unique_id}, Unable to get ATR"
                    error_string = f"Error, Row no - {indx + 2}, For Unique ID: {unique_id}, Unable to get ATR"

                    return False, error_title, error_string

                # checking if atr multiple value is valid
                try:
                    atr_multiple = float(atr_multiple)

                    # Make trigger price None
                    trigger_price = "None"

                    # check if atrr multiple is less than or equal to zero
                    if atr_multiple <= 0:
                        raise Exception("Invalid ATR Multiple")

                except Exception as e:
                    error_title = f"Error, Row no - {indx + 2}, Invalid ATR Multiple"
                    error_string = f"Error, Row no - {indx + 2}, Please provide a valid ATR Multiple for Stop Loss Order."

                    return False, error_title, error_string

                # checking if trigger price calculations are valid
                trigger_price = get_trigger_price_for_stop_loss(
                    unique_id, buy_sell_action, atr_multiple, atr
                )

                if trigger_price == "N/A":
                    error_title = f"Error, Row no - {indx + 2},Invalid Trigger Price"
                    error_string = f"Error, Row no - {indx + 2},Unable to get valid Trigger Price based on ATR Multiple: {atr_multiple}, \nATR: {atr}"

                    return False, error_title, error_string

            if (order_type == "STOP LOSS") and (
                buy_sell_action == "BUY" and current_buy_price > trigger_price
            ):
                error_title = f"Error Row no - {indx + 2}, Invalid Trigger Price"
                error_string = make_multiline_mssg_for_gui_popup(
                    f"Row no - {indx + 2}, Unique-Id - {unique_id}, Trigger Price for Buy Order must be greater than current Buy Price"
                )

                return False, error_title, error_string

            elif (order_type == "STOP LOSS") and (
                buy_sell_action == "SELL" and current_sell_price < trigger_price
            ):
                error_title = f"Error Row no - {indx + 2}, Invalid Trigger Price"
                error_string = make_multiline_mssg_for_gui_popup(
                    f"Row no - {indx + 2}, Unique-Id - {unique_id}, Trigger Price for Sell Order must be lower than current Sell Price"
                )

                return False, error_title, error_string

        # Trailing Stop Loss Orders
        elif order_type == "TRAILING STOP LOSS":
            # Check if both trail value and atr multiple is empty
            if trail_value == "None" and atr_multiple == "None":
                error_title = (
                    f"Error, Row no - {indx + 2}, Invalid combination of values"
                )
                error_string = f"Error, Row no - {indx + 2}, Values for both Trail Value and ATR Multiple must not be empty."

                return False, error_title, error_string

            # Check if trail value is valid
            elif trail_value != "None" and atr_multiple == "None":
                try:
                    trail_value = float(trail_value)

                    # Make ATR value empty in case of not using ATR multiplier in trailing stop loss order
                    atr = ""
                except Exception as e:
                    error_title = f"Error, Row no - {indx + 2},Invalid Trail Value"
                    error_string = f"Error, Row no - {indx + 2},Please provide a valid Trail Value for Stop Loss Order."

                    return False, error_title, error_string

            # Check if atr multiple is valid and get valid trail value
            elif (trail_value == "None" and atr_multiple != "None") or (
                trail_value != "None" and atr_multiple != "None"
            ):
                # Get ATR value
                atr = get_atr_value_for_unique_id(unique_id)

                # If atr is N/A return error
                if atr == "N/A":
                    error_title = f"Error, Row no - {indx + 2},For Unique ID: {unique_id}, Unable to get ATR"
                    error_string = f"Error, Row no - {indx + 2},For Unique ID: {unique_id}, Unable to get ATR"

                    return False, error_title, error_string

                # checking if atr multiple value is valid
                try:
                    atr_multiple = float(atr_multiple)

                    # Make trail value None
                    trail_value = "None"

                    # check if atr multiple is less than or equal to zero
                    if atr_multiple <= 0:
                        raise Exception("Invalid ATR Multiple")

                except Exception as e:
                    error_title = f"Error, Row no - {indx + 2},Invalid ATR Multiple"
                    error_string = f"Error, Row no - {indx + 2},Please provide a valid ATR Multiple for Stop Loss Order."

                    return False, error_title, error_string

                # checking if trail value calcualtions are valid
                trail_value = get_trail_value_for_trailing_stop_loss(atr_multiple, atr)

                if trail_value == "N/A":
                    error_title = f"Error, Row no - {indx + 2},Invalid Trigger Price"
                    error_string = f"Error, Row no - {indx + 2},Unable to get valid Trail Value based on ATR Multiple: {atr_multiple} and ATR: {atr}"

                    return False, error_title, error_string

    # Getting standard order type values mapped to upper case order type values
    orders_dataframe_to_be_checked["Order Type"] = orders_dataframe_to_be_checked[
        "Order Type"
    ].map(order_type_values_upper_to_standard_dict)

    return True, "No Error", "No Error"


# Update values based on order type selected
def update_values_based_on_order_type(
    order_type, limit_price, trigger_price, trail_value, atr_multiple, atr
):
    order_type = order_type.upper()

    # For order type "Market"
    if order_type == "MARKET":
        limit_price = trigger_price = trail_value = atr_multiple = atr = ""

    # For order type "Limit"
    elif order_type == "LIMIT":
        trigger_price = trail_value = atr_multiple = atr = ""

    # For order type "Stop loss"
    elif order_type == "STOP LOSS":
        limit_price = trail_value = ""

    # For order type "Trailing Stop Loss"
    elif order_type == "TRAILING STOP LOSS":
        limit_price = trigger_price = ""

    # For order type "IB Algo Market"
    elif order_type == "IB ALGO MARKET":
        limit_price = trigger_price = trail_value = atr_multiple = atr = ""

    # Return updated values
    return [limit_price, trigger_price, trail_value, atr_multiple, atr]


# Method to get trail value for atr multiple and atr
def get_trail_value_for_trailing_stop_loss(atr_multiple, atr):
    try:
        # Get trigger price
        trail_value = atr_multiple * atr

    except Exception as e:
        # Init
        trail_value = "N/A"

    return trail_value


# Method to get trigger price for atr multiple and atr
def get_trigger_price_for_stop_loss(unique_id, buy_sell_action, atr_multiple, atr):
    # checking if trigger price calculations are valid
    try:
        # Init
        trigger_price = "N/A"

        avg_price_combo = "N/A"

        # Make it available in variables
        avg_price_combo = (
            variables.unique_id_to_prices_dict[unique_id]["BUY"]
            + variables.unique_id_to_prices_dict[unique_id]["SELL"]
        ) / 2

        # When action is BUY
        if buy_sell_action == "BUY":
            # Get trigger price
            trigger_price = avg_price_combo + atr_multiple * atr

        # When action is SELL
        elif buy_sell_action == "SELL":
            # Get trigger price
            trigger_price = avg_price_combo - atr_multiple * atr

    except Exception as e:
        trigger_price = "N/A"

    return trigger_price


# Method to get atr value
def get_atr_value_for_unique_id(unique_id):
    # atr for order dict
    order_atr_values = copy.deepcopy(variables.map_unique_id_to_atr_for_order_values)

    # Get atr value
    try:
        unique_id = int(unique_id)

        # Get ATR value
        atr = (
            "N/A"
            if order_atr_values[unique_id] == "N/A"
            else order_atr_values[unique_id]
        )

        # Check if atr is float
        if not is_float_upload_order(atr):
            # In case of exception set it to N/A
            atr = "N/A"

        else:
            return atr

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Exceptions in getting ATR, Exp: {e}")

        # In case of exception set it to N/A
        atr = "N/A"

    return atr


# Method to place order based on csv data
def upload_orders_from_csv_to_app(orders_dataframe_path, upload_order_from_csv_button):
    try:
        # get csv file from file path
        orders_dataframe = pd.read_csv(orders_dataframe_path)

        # Replace null values by None string
        orders_dataframe = orders_dataframe.fillna("None")

    except Exception as e:
        # Error Message pop-up
        error_title = "Error reading the Order CSV file"
        error_string = f"Unable to read the CSV file"
        variables.screen.display_error_popup(error_title, error_string)

        # Enabled upload orders button
        upload_order_from_csv_button.config(state="enabled")

        return

    # Checking if dataframe is empty
    if orders_dataframe.empty:
        # Error Message pop-up
        error_title = "Error Empty CSV file"
        error_string = f"CSV file was empty"
        variables.screen.display_error_popup(error_title, error_string)

        # Enabled upload orders button
        upload_order_from_csv_button.config(state="enabled")

        return

    # Check validaity of dataframe
    (
        is_orders_df_valid,
        error_title_validation,
        error_string_validation,
    ) = check_validity_of_dataframe(orders_dataframe)

    # Show pop in event of file format is not correct
    if not is_orders_df_valid:
        # Make error string multiline
        error_title_validation = make_multiline_mssg_for_gui_popup(
            error_title_validation
        )

        # Make error string multiline
        error_string_validation = make_multiline_mssg_for_gui_popup(
            error_string_validation
        )

        # Error Message
        variables.screen.display_error_popup(
            error_title_validation, error_string_validation
        )

        # Enabled upload orders button
        upload_order_from_csv_button.config(state="enabled")

        return

    try:
        # Iterate dataframe
        for indx, row in orders_dataframe.iterrows():
            # Get all value for order
            unique_id, buy_sell_action, order_type, combo_quantity = (
                int(float(row["Unique ID"])),
                row["Action"],
                row["Order Type"],
                row["#Lots"],
            )

            limit_price, trigger_price, trail_value, atr_multiple = (
                row["Limit Price"],
                row["Trigger Price"],
                row["Trail Value"],
                row["ATR Multiple"],
            )

            # get bypass rm check value
            bypass_rm_check = str(row["Bypass RM Check"]).strip()

            # Get account id
            account_id = row["Account ID"]

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
                    # Error pop up
                    """error_title = f"For Account ID: {account_id}, Order cannot be placed, \naccount is in liquidation mode"
                    error_string = f"For Account ID: {account_id}, Order cannot be placed, \naccount is in liquidation mode"

                    self.display_error_popup(error_title, error_string)"""
                    continue

            elif not trade_level_rm_check_result(bypass_rm_check, unique_id):
                time.sleep(variables.rm_checks_interval_if_failed)

                if not trade_level_rm_check_result(bypass_rm_check, unique_id):
                    continue

            # Get order type in upper case
            order_type_upper_case = order_type.upper()

            # Get value of atr
            atr = get_atr_value_for_unique_id(unique_id)

            # Get updated values based on order type
            [
                limit_price,
                trigger_price,
                trail_value,
                atr_multiple,
                atr,
            ] = update_values_based_on_order_type(
                order_type, limit_price, trigger_price, trail_value, atr_multiple, atr
            )

            # In case of trailing stop loss ATR order trail value will be empty
            if (
                atr_multiple not in ["", "None"]
                and order_type_upper_case == "TRAILING STOP LOSS"
            ):
                trail_value = get_trail_value_for_trailing_stop_loss(
                    float(atr_multiple), float(atr)
                )

            # Check if order is trailign stop loss and values is available for trail vallue but not atr multiple
            elif (
                trail_value not in ["", "None"]
                and atr_multiple in ["", "None"]
                and order_type_upper_case == "TRAILING STOP LOSS"
            ):
                atr = "None"

            # In case of stop loss ATR order trigger price will be empty
            if (
                atr_multiple not in ["", "None"]
                and order_type_upper_case == "STOP LOSS"
            ):
                trigger_price = get_trigger_price_for_stop_loss(
                    unique_id, buy_sell_action, float(atr_multiple), float(atr)
                )

            # Check if order is stop loss and values is available for trigger price but not atr multiple
            elif (
                trigger_price not in ["", "None"]
                and atr_multiple in ["", "None"]
                and order_type_upper_case == "STOP LOSS"
            ):
                atr = "None"

            # Make aTR multiple None if it is empty string
            if atr_multiple in ["", "None"]:
                atr_multiple = "None"

            # Make aTR None if it is empty string
            if atr in ["", "None"]:
                atr = "None"

            # Converting value to int
            unique_id = int(float(unique_id))

            # Converting value to str
            combo_quantity = str(int(float(combo_quantity)))

            # Send order in a separate thread
            send_order_thread = threading.Thread(
                target=send_order,
                args=(
                    unique_id,
                    buy_sell_action,
                    order_type,
                    combo_quantity,
                    limit_price,
                    trigger_price,
                    trail_value,
                ),
                kwargs={
                    "atr_multiple": atr_multiple,
                    "atr": atr,
                    "account_id": account_id,
                    "bypass_rm_check": bypass_rm_check,
                },
            )
            send_order_thread.start()

            # Update order book
            variables.flag_orders_book_table_watchlist_changed = True
            variables.screen.update_orders_book_table_watchlist_changed()

            # To keep interval of 1 second between 2 orders
            time.sleep(1)
    except Exception as e:
        print(f"Upload Orders Sending order Exception: {e}")
    time.sleep(2)

    # Update table
    variables.screen.update_tables_after_combo_deleted()

    # Enabled upload orders button
    upload_order_from_csv_button.config(state="enabled")


# Method to make message multiline
def make_multiline_mssg_for_gui_popup(error_string):
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

    return new_string
