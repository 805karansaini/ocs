"""
Created on 20-Apr-2023

@author: Karan
"""

from com.mysql_io import *
from com.order_execution import *
import re

from com.trade_rm_check_result_module import *
from com.positions import update_combo_positions_in_positions_tab


# Using local Import for (create_combination), to avoid circular imports:(combo_helper -> price -> utilities -> combo_helper)
# Using local Import for (calculate_combo_prices), to avoid circular imports:(order execution -> screen_accounts_tab -> utilities -> execution)
# importing Function in process_cas_add_condition_for_combo, process_cas_switch_condition_for_combo
# from com.combination_helper import create_combination, subscribe_mktdata_combo_obj, insert_combination_db


# Method to sort string numeric values
def custom_sort(val):
    # Replace 'N/A' with a large value
    if val == "N/A":
        return 10**15

    elif type(val) == str and (val[0].isnumeric() or val[0] == "-"):
        # Replace "," with ""
        val = val.replace(",", "")
        val = val.replace(":", "")

        # Remove %
        if val[-1] == "%":
            return float(val[:-1])

        return float(val)
    else:
        return val


# Method to sort cas rows
def sort_cas_row_values_by_column(values):
    # Sort Values Based on the User selected column
    key, reverse = list(variables.cas_table_sort_by_column.items())[0]

    # Col_index
    col_index = variables.map_cas_column_name_to_index[key]

    # Sort Values
    values = sorted(
        values, key=lambda row: custom_sort(row[col_index]), reverse=reverse
    )

    return values


# Method to check if format of brackets in string is correct
def check_valid_brackets(condition_string):
    stack = []
    for ch in condition_string:
        if ch == "(":
            stack.append("(")
        elif ch == ")":
            if stack:
                stack.pop()
            else:
                return False
        else:
            continue

    if stack:
        return False

    return True


# Method to check if condition is in right format or not
def check_basic_condition(
    condition_string,
    unique_id,
    refer_price,
    refer_position,
    flag_check_expression=False,
):
    # local copy of allowed tokens
    set_allowed_tokens = copy.deepcopy(variables.set_allowed_tokens)

    if len(variables.current_session_accounts) > 1:
        set_allowed_tokens.remove("Price Adverse Chg By")
        set_allowed_tokens.remove("Price Favorable Chg By")

    # local copy of allowed condition
    condition_string_copy = copy.deepcopy(condition_string)

    # Checking for valid brackets
    if not check_valid_brackets(condition_string_copy):
        error_string = "Invalid brackets, Please check the condition."
        return False, error_string

    # Replacing opening and closing brackets
    condition_string_copy = condition_string_copy.replace("(", " ")
    condition_string_copy = condition_string_copy.replace(")", " ")

    # Find all the date_time and times in condition, replace them by empty spaces
    date_times_list = re.findall(variables.date_time_regex, condition_string_copy)

    # replace date-times with empty spaces
    for _date_time_ in date_times_list:
        condition_string_copy = condition_string_copy.replace(_date_time_, " ")

    # Extract the times from the condition string
    times_list = re.findall(variables.time_regex, condition_string_copy)

    # replace times with spaces empty spaces
    for _time_ in times_list:
        condition_string_copy = condition_string_copy.replace(_time_, " ")

    # All Allowed Tokens
    set_allowed_tokens = sorted(list(set_allowed_tokens), key=lambda word: -len(word))

    # Checking for Tokens
    for token in set_allowed_tokens:
        condition_string_copy = condition_string_copy.replace(token, " ")

    # Checking Floats
    for num_val in condition_string_copy.split(" "):
        num_val = num_val.strip()

        if num_val != "":
            try:
                float(num_val)
            except:
                error_string = "Invalid Values, Please check the condition."
                return False, error_string

    # Check if expression is being checked
    if flag_check_expression:
        # Get list of column for expression
        user_input_fields = copy.deepcopy(variables.cas_table_fields_for_expression)

    else:
        # Get list of columns for condition
        user_input_fields = copy.deepcopy(variables.cas_table_fields_for_condition)

        if len(variables.current_session_accounts) > 1:
            user_input_fields.remove("Price Adverse Chg By")
            user_input_fields.remove("Price Favorable Chg By")

    # Sorted 'user_input_fields' longest word first, local copy
    user_input_fields = sorted(user_input_fields, key=lambda word: -len(word))

    # Prices of combination
    unique_id_to_prices_dict = copy.deepcopy(
        variables.unique_id_to_prices_dict,
    )

    # Cas Table Dataframe
    cas_table_data_frame = copy.deepcopy(variables.cas_table_values_df)

    # filter the DataFrame to get the row where "Unique ID" is equal to unique_id
    filtered_df = cas_table_data_frame[cas_table_data_frame["Unique ID"] == unique_id]

    # Check if expression is being checked
    if flag_check_expression:
        # Get the column names of the DataFrame
        columns = cas_table_data_frame.columns

        # Create a dictionary with 'N/A' for each column
        na_values = {column: "N/A" for column in columns}

        # Create the row with 'N/A'
        cas_row = na_values

    else:
        if filtered_df.empty:
            # Get the column names of the DataFrame
            columns = cas_table_data_frame.columns

            # Create a dictionary with 'N/A' for each column
            na_values = {column: "N/A" for column in columns}

            # Create the row with 'N/A'
            cas_row = na_values
        else:
            # get the first row of the filtered DataFrame using .iloc
            cas_row = filtered_df.iloc[0]

    return evaluate_condition(
        user_input_fields,
        cas_row,
        condition_string,
        refer_price,
        refer_position,
        first_time_checking=True,
    )


# Method to validate account condition is in right format or not
def check_account_condition(condition_string):
    # local copy of allowed tokens
    set_allowed_tokens = set(
        [
            x
            for x in variables.accounts_table_columns[1:-1]
            + ["Tickers PNL"]
            + variables.cas_table_operators_for_condition[1:]
        ]
    )

    # local copy of allowed condition
    condition_string_copy = copy.deepcopy(condition_string)

    # Checking for valid brackets
    if not check_valid_brackets(condition_string_copy):
        error_string = "Invalid brackets, Please check the condition."
        return False, error_string

    # Replacing opening and closing brackets
    condition_string_copy = condition_string_copy.replace("(", " ")
    condition_string_copy = condition_string_copy.replace(")", " ")

    # Find all the date_time and times in condition, replace them by empty spaces
    date_times_list = re.findall(variables.date_time_regex, condition_string_copy)

    # replace date-times with empty spaces
    for _date_time_ in date_times_list:
        condition_string_copy = condition_string_copy.replace(_date_time_, " ")

    # Extract the times from the condition string
    times_list = re.findall(variables.time_regex, condition_string_copy)

    # replace times with spaces empty spaces
    for _time_ in times_list:
        condition_string_copy = condition_string_copy.replace(_time_, " ")

    # All Allowed Tokens
    set_allowed_tokens = sorted(list(set_allowed_tokens), key=lambda word: -len(word))

    # Checking for Tokens
    for token in set_allowed_tokens:
        condition_string_copy = condition_string_copy.replace(token, " ")

    # Checking Floats
    for num_val in condition_string_copy.split(" "):
        num_val = num_val.strip()

        if num_val != "":
            try:
                # Check if term has % in it
                if num_val.count("%") == 1:
                    num_val = num_val.replace("%", "")

                    float(num_val)

                else:
                    float(num_val)
            except:
                error_string = "Invalid Values, Please check the condition."
                return False, error_string

    # Get list of column for condition
    user_input_fields = copy.deepcopy(
        variables.accounts_table_columns[1:-1] + ["Tickers PNL"]
    )

    # Sorted 'user_input_fields' longest word first, local copy
    user_input_fields = sorted(user_input_fields, key=lambda word: -len(word))

    # Get the column names of the DataFrame
    columns = copy.deepcopy(variables.accounts_table_columns[1:-1] + ["Tickers PNL"])

    # Create a dictionary with 'N/A' for each column
    na_values = {column: "N/A" for column in columns}

    # Create the row with 'N/A'
    df_row = na_values

    # Replacing %
    condition_string = condition_string.replace("%", "")

    return evaluate_condition(
        user_input_fields,
        df_row,
        condition_string,
        None,
        None,
        first_time_checking=True,
    )


# Method to evaluate condition
def evaluate_condition(
    user_input_fields,
    cas_row,
    condition_string,
    refer_price,
    refer_position,
    first_time_checking=False,
):
    # define the global and local namespaces for eval
    globals_dict = {}
    locals_dict = {}
    dates_counter = 1
    flag_date_time_present = False
    flag_time_present = False

    # Find all the date_time and times in condition, replace them by some thing dates1, dates2, etc..
    # Extract the date_times from the condition string
    date_times_list = re.findall(variables.date_time_regex, condition_string)

    # Replace date_times with variables and add that to globals dict
    for date_time in date_times_list:
        # Mark flag to True
        flag_date_time_present = True

        # add to globals_dict (time object)
        globals_dict[f"dates{dates_counter}"] = variables.target_timezone_obj.localize(
            datetime.datetime.strptime(date_time, "%Y%m%d %H:%M:%S")
        )
        condition_string = condition_string.replace(
            date_time, f" dates{dates_counter} "
        )
        dates_counter += 1

    # Extract the times from the condition string
    times_list = re.findall(variables.time_regex, condition_string)

    # replace times with variables and add that to globals dict
    for _time_ in times_list:
        # Mark flag to True
        flag_time_present = True

        # add to globals_dict (time object)
        globals_dict[f"dates{dates_counter}"] = variables.target_timezone_obj.localize(
            datetime.datetime.strptime(_time_, "%H:%M:%S")
        )
        condition_string = condition_string.replace(_time_, f" dates{dates_counter} ")
        dates_counter += 1

    # user_input_fields contains all the different tokens that user can give
    # Replace Token with Value
    for token in user_input_fields:
        # check if this token in condition string
        is_token_present = condition_string.find(token)

        # Token is not present
        if is_token_present == -1:
            continue

        if token in [
            "Price Adverse Chg By",
            "Price Favorable Chg By",
        ]:
            """if refer_position == 0:

                error_string = f"Can not use '{token}' as current position is 0."
                return False, error_string

            else:"""
            try:
                # Get current price buy and sell price of combo from cas
                combo_buy_price = cas_row["Buy Price"]
                combo_sell_price = cas_row["Sell Price"]

                # Remove , from the strings.
                combo_buy_price = combo_buy_price.replace(",", "")
                combo_sell_price = combo_sell_price.replace(",", "")

                # Calculating Current Price
                current_price = (float(combo_buy_price) + float(combo_sell_price)) / 2

                # Calculating Price Change
                if (refer_position > 0 and token == "Price Favorable Chg By") or (
                    refer_position < 0 and token == "Price Adverse Chg By"
                ):
                    price_change = current_price - refer_price
                else:
                    price_change = refer_price - current_price

            except Exception as e:
                # Print to console
                if variables.flag_debug_mode:
                    print("error,", e)
                # If the price are not available use these value only to test the condition when it is added by the user
                if first_time_checking:
                    # If Price were not available when user wanted to insert condition, we are giving default price so we can insert condition
                    current_price = 10000
                    price_change = 1000

                else:
                    return False, False

            # Price Adv and Fav
            token_val = f" {price_change} >= "

            # Replace Value in the string and continue
            condition_string = condition_string.replace(f"{token}", f"{token_val}")
            continue

        elif token in ["Price Increase By", "Price Decrease By"]:
            try:
                # Get current price buy and sell price of combo from cas
                combo_buy_price = cas_row["Buy Price"]
                combo_sell_price = cas_row["Sell Price"]

                # Remove , from the strings.
                combo_buy_price = combo_buy_price.replace(",", "")
                combo_sell_price = combo_sell_price.replace(",", "")

                current_price = (float(combo_buy_price) + float(combo_sell_price)) / 2
            except Exception as e:
                # If the price are not available use these value only to test the condition when it is added by the user
                if first_time_checking:
                    current_price = 10000
                else:
                    return False, False

            if token == "Price Increase By":
                token_val = f" {current_price}  >= {refer_price} + "
            elif token == "Price Decrease By":
                token_val = f" {current_price} <= {refer_price} - "

            # Replace Value in the string and continue
            condition_string = condition_string.replace(f"{token}", f"{token_val}")
            continue

        elif token in ["Intraday Low Time", "Intraday High Time"]:
            # Token Value
            token_val = cas_row[f"{token}"]

            if first_time_checking and (token_val == "N/A"):
                current_time = datetime.datetime.now(variables.target_timezone_obj)
                token_val = current_time.strftime("%H:%M:%S")

            if not first_time_checking and (token_val == "N/A"):
                return False, False

            # Add to globals_dict (time object)
            globals_dict[f"dates{dates_counter}"] = (
                variables.target_timezone_obj.localize(
                    datetime.datetime.strptime(token_val, "%H:%M:%S")
                )
            )
            condition_string = condition_string.replace(
                token, f" dates{dates_counter} "
            )
            dates_counter += 1

            continue

        # Normal Tokens
        else:
            token_val = str(cas_row[f"{token}"]).replace(",", "")

        # If the field is not available use this value only to test the condition when it is added by the user
        if first_time_checking:
            if token_val == "N/A":
                token_val = "1000"
        else:
            if token_val == "N/A":
                return False, False

        # Remove (% and ,) from value
        token_val = token_val.replace(",", "")
        token_val = token_val.replace("%", "")
        token_val = float(token_val)

        # Replace Value in the string.
        condition_string = condition_string.replace(f"{token}", f"{token_val}")

    try:
        result_of_condition_eval = eval(condition_string, globals_dict, locals_dict)

        # If we are able to evaluate the condition when it is added by the user(but eval resulted in False, still returning True)
        if first_time_checking:
            return True, None

        # when checking condition for triggering the CAS
        return result_of_condition_eval, condition_string

    except Exception as e:
        # If we are able to evaluate the condition when it is added by the user
        if first_time_checking:
            error_string = "Unable to evaluate condition, Please check the condition."
            return False, error_string

        # if not able to evaluate (maybe value is  "N/A" return False)
        return False, False


# Method to monitor and manage conditional orders
def monitor_and_trigger_cas_condition():
    try:
        # Get all cas conditions in the DB.
        cas_conditions_df = get_all_cas_conditions_from_db(only_pending=True)

        # Sorted 'user_input_fields' longest word first, local copy
        user_input_fields = copy.deepcopy(variables.cas_table_fields_for_condition)
        user_input_fields = sorted(user_input_fields, key=lambda word: -len(word))

        # Cas Table Dataframe
        cas_table_data_frame = copy.deepcopy(variables.cas_table_values_df)

        # For each condition evaluate the condition
        for indx, cas_condition_row in cas_conditions_df.iterrows():
            unique_id = cas_condition_row["Unique ID"]
            trading_combination_unique_id = cas_condition_row[
                "Trading Combination Unique ID"
            ]
            eval_unqiue_id = int(cas_condition_row["Evaluation Unique ID"])

            condition = cas_condition_row["Condition"]
            cas_condition_type = cas_condition_row["CAS Condition Type"]
            reference_price = float(cas_condition_row["Condition Reference Price"])
            reference_position = int(cas_condition_row["Reference Position"])
            condition_trigger_price = cas_condition_row["Condition Trigger Price"]
            order_type = cas_condition_row["Order Type"].strip()
            combo_quantity = cas_condition_row["#Lots"].strip()
            limit_price = cas_condition_row["Limit Price"].strip()
            order_trigger_price = cas_condition_row["Order Trigger Price"].strip()
            trail_value = cas_condition_row["Trail Value"].strip()
            atr_multiple = cas_condition_row["ATR Multiple"].strip()
            atr = cas_condition_row["ATR"].strip()
            status = cas_condition_row["Status"]
            target_position = cas_condition_row["Target Position"]
            account_id = cas_condition_row["Account ID"]
            bypass_rm_check = cas_condition_row["Bypass RM Check"]
            series_id = cas_condition_row["Series ID"]
            flag_use_execution_engine = cas_condition_row["Execution Engine"]

            # set boolan value of execution engine
            if flag_use_execution_engine == "True":
                flag_use_execution_engine = True

            else:
                flag_use_execution_engine = False

            # If status is not pending continue
            if status != "Pending":
                continue

            # filter the DataFrame to get the row where "Unique ID" is equal to unique_id
            filtered_df = cas_table_data_frame[
                cas_table_data_frame["Unique ID"] == eval_unqiue_id
            ]

            try:
                # get the first row of the filtered DataFrame using .iloc
                cas_row = filtered_df.iloc[0]
            except Exception as e:
                # Print to console
                if variables.flag_debug_mode:
                    print(f"\nUnique ID: {unique_id}")
                    print(f"Cas Table Main Df", cas_table_data_frame.to_string())
                    print(f"Filtered Df", filtered_df.to_string())

                    print(f"Error in Utilities {e}")
                continue

            """local_unique_id_to_positions_dict = copy.deepcopy(
                variables.map_unique_id_to_positions
            )

            try:

                eval_position = local_unique_id_to_positions_dict[int(eval_unqiue_id)][account_id]

            except Exception as e:

                eval_position = None"""

            # Eval Result (condition passed or not), solved_conditon_string(will have values and equation) or False incase eval is False
            eval_result, solved_condition_string = evaluate_condition(
                user_input_fields,
                cas_row,
                condition,
                reference_price,
                reference_position,
            )

            if eval_result and variables.flag_account_checks_completed_first_time:
                # It will be show in popup that happend when codition is triggered (CAS)
                solved_condition_string = (
                    f"{condition.strip()} \n{solved_condition_string.strip()}"
                )

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"{condition.strip()}, Unique ID: {unique_id}, Trading Combination Unique ID: {trading_combination_unique_id} = {eval_result}  "
                    )

                # Unique Id of combo for which the condition is triggered
                trading_combination_unique_id = int(trading_combination_unique_id)

                # If we have conditional order to place(BUY, SELL)
                if cas_condition_type in ["BUY", "SELL"]:
                    if account_id not in variables.current_session_accounts:
                        # update value
                        variables.cas_condition_table_dataframe.loc[
                            variables.cas_condition_table_dataframe["Table ID Column"]
                            == f"{unique_id}_{account_id}",
                            "Status",
                        ] = "Failed"

                        # update value
                        variables.cas_condition_table_dataframe.loc[
                            variables.cas_condition_table_dataframe["Table ID Column"]
                            == f"{unique_id}_{account_id}",
                            "Reason For Failed",
                        ] = "Account ID not present in current session"

                        # Update in GUI table
                        variables.screen.screen_cas_obj.cas_condition_table.set(
                            f"{unique_id}_{account_id}", 10, "Failed"
                        )
                        variables.screen.screen_cas_obj.cas_condition_table.set(
                            f"{unique_id}_{account_id}",
                            11,
                            "Account ID not present in current session",
                        )

                        # Update in db
                        update_cas_condition_status(unique_id, "Failed", account_id)
                        update_cas_condition_reason_for_failed(
                            unique_id,
                            "Account ID not present in current session",
                            account_id,
                        )

                        # check if order was originated from conditional series
                        if series_id not in ["None", "N/A", None]:
                            if series_id not in [None, "None"]:
                                terminate_series(unique_id, series_id)

                            """variables.screen.screen_conditional_series_tab.stop_series(
                                series_id, unique_id
                            )"""

                        continue

                    combo_quantity = int(combo_quantity)

                    # Local copy of the all the unique ids in the system
                    all_the_unique_ids_in_the_system = copy.deepcopy(
                        variables.unique_id_to_combo_obj
                    )

                    if (
                        int(trading_combination_unique_id)
                        in all_the_unique_ids_in_the_system
                    ):
                        rm_checks_result = True

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
                                # variables.screen.cancel_order(selected_item=order_time, updated_status='Failed')
                                # update value

                                # print(variables.cas_condition_table_dataframe.to_string())

                                # Update values in column 'Stauts' where 'table id is for failed order' is equal to unique id
                                variables.cas_condition_table_dataframe.loc[
                                    variables.cas_condition_table_dataframe[
                                        "Table ID Column"
                                    ]
                                    == f"{unique_id}_{account_id}",
                                    "Status",
                                ] = "Failed"

                                # update value
                                variables.cas_condition_table_dataframe.loc[
                                    variables.cas_condition_table_dataframe[
                                        "Table ID Column"
                                    ]
                                    == f"{unique_id}_{account_id}",
                                    "Reason For Failed",
                                ] = "Account is in liquidation mode"

                                # print(variables.cas_condition_table_dataframe.to_string())

                                # iables.cas_condition_table_dataframe.to_string())
                                # Update in GUI table
                                variables.screen.screen_cas_obj.cas_condition_table.set(
                                    f"{unique_id}_{account_id}", 10, "Failed"
                                )
                                variables.screen.screen_cas_obj.cas_condition_table.set(
                                    f"{unique_id}_{account_id}",
                                    11,
                                    "Account is in liquidation mode",
                                )

                                # Update in db
                                update_cas_condition_status(
                                    unique_id, "Failed", account_id
                                )
                                update_cas_condition_reason_for_failed(
                                    unique_id,
                                    "Account is in liquidation mode",
                                    account_id,
                                )

                                # check if order was originated from conditional series
                                if series_id not in ["None", "N/A", None]:
                                    if series_id not in [None, "None"]:
                                        terminate_series(unique_id, series_id)

                                    """variables.screen.screen_conditional_series_tab.stop_series(
                                        series_id, unique_id
                                    )"""

                                continue

                        if not trade_level_rm_check_result(
                            bypass_rm_check, trading_combination_unique_id
                        ):
                            time.sleep(variables.rm_checks_interval_if_failed)

                            if not trade_level_rm_check_result(
                                bypass_rm_check, trading_combination_unique_id
                            ):
                                # variables.screen.cancel_order(selected_item=order_time, updated_status='Failed')
                                # update value
                                variables.cas_condition_table_dataframe.loc[
                                    variables.cas_condition_table_dataframe[
                                        "Table ID Column"
                                    ]
                                    == f"{unique_id}_{account_id}",
                                    "Status",
                                ] = "Failed"

                                # update value
                                variables.cas_condition_table_dataframe.loc[
                                    variables.cas_condition_table_dataframe[
                                        "Table ID Column"
                                    ]
                                    == f"{unique_id}_{account_id}",
                                    "Reason For Failed",
                                ] = "Trade Level RM Check Failed"

                                # Update in GUI table
                                variables.screen.screen_cas_obj.cas_condition_table.set(
                                    f"{unique_id}_{account_id}", 10, "Failed"
                                )
                                variables.screen.screen_cas_obj.cas_condition_table.set(
                                    f"{unique_id}_{account_id}",
                                    11,
                                    "Trade Level RM Check Failed",
                                )

                                # Update in db
                                update_cas_condition_status(
                                    unique_id, "Failed", account_id
                                )
                                update_cas_condition_reason_for_failed(
                                    unique_id, "Trade Level RM Check Failed", account_id
                                )

                                # check if order was originated from conditional series
                                if series_id not in ["None", "N/A", None]:
                                    if series_id not in [None, "None"]:
                                        terminate_series(unique_id, series_id)

                                    """variables.screen.screen_conditional_series_tab.stop_series(
                                        series_id, unique_id
                                    )"""

                                continue

                        # Send order in a separate thread
                        send_order_thread = threading.Thread(
                            target=send_order,
                            args=(
                                trading_combination_unique_id,
                                cas_condition_type,
                                order_type,
                                combo_quantity,
                                limit_price,
                                order_trigger_price,
                                trail_value,
                            ),
                            kwargs={
                                "atr_multiple": atr_multiple,
                                "atr": atr,
                                "account_id": account_id,
                                "bypass_rm_check": bypass_rm_check,
                                "execution_engine": flag_use_execution_engine,
                            },
                        )
                        send_order_thread.start()

                        # sleep
                        time.sleep(0.5)

                        # update value
                        variables.cas_condition_table_dataframe.loc[
                            variables.cas_condition_table_dataframe["Table ID Column"]
                            == f"{unique_id}_{account_id}",
                            "Status",
                        ] = "Completed"

                        # Removing failed cas condition from  cas condition dataframe
                        variables.cas_condition_table_dataframe = (
                            variables.cas_condition_table_dataframe[
                                variables.cas_condition_table_dataframe["Status"]
                                != "Completed"
                            ]
                        )

                        # Update the status to Completed in db
                        update_cas_condition_status(
                            unique_id, status="Completed", account_id=account_id
                        )

                        # Move this row from the table to archive table.
                        move_active_data_to_archive_db(
                            unique_id,
                            flag_move_cas_condition_table_row=True,
                            account_id=account_id,
                        )

                        pending_count = do_cas_condition_exists_for_unique_id_in_db(
                            unique_id, condition_type=cas_condition_type
                        )

                        if pending_count == 0:
                            # Show informative popup that the order is completed - xxxx
                            variables.screen.screen_cas_obj.display_condition_order_triggered_informative_popup(
                                unique_id,
                                trading_combination_unique_id,
                                cas_condition_type,
                                solved_condition_string,
                                reference_price,
                                reference_position,
                                order_type,
                                combo_quantity,
                                limit_price,
                                order_trigger_price,
                                trail_value,
                                series_id=series_id,
                            )

                        # Remove condition from the table
                        variables.screen.screen_cas_obj.cas_condition_table.delete(
                            f"{unique_id}_{account_id}"
                        )

                        # update the table
                        variables.screen.screen_cas_obj.update_cas_condition_after_cas_condition_deleted()

                        if pending_count == 0:
                            # check if order was originated from conditional series
                            if series_id not in ["None", "N/A", None]:
                                # variables.screen.screen_cas_obj.delete_cas_condition(unique_id)

                                variables.screen.screen_conditional_series_tab.update_conditional_order_after_order_completed(
                                    series_id
                                )

                    else:
                        # Move this row from the table to archive table.
                        move_active_data_to_archive_db(
                            unique_id,
                            flag_move_cas_condition_table_row=True,
                            account_id=account_id,
                        )

                        # Please display a error/notification here.
                        error_title = f"Conditional {cas_condition_type.strip()} order can not be completed"
                        error_string = f"Conditional {cas_condition_type.strip()} order can not be completed, \nTrading Combo Unique ID: {trading_combination_unique_id} is not present in system"
                        variables.screen.display_error_popup(error_title, error_string)

                        # Remove condition from the table
                        variables.screen.screen_cas_obj.cas_condition_table.delete(
                            f"{unique_id}_{account_id}"
                        )

                        # update the table
                        variables.screen.screen_cas_obj.update_cas_condition_after_cas_condition_deleted()

                    return

                else:
                    pass
                    # If conditional Add or Switch do that.

                # Get All pending order
                all_pending_order = get_pending_orders()

                # Record module start time
                last_update_time = datetime.datetime.now(variables.target_timezone_obj)

                # Mark the orders cancelled
                for i, pending_order_row in all_pending_order.iterrows():
                    # Init value
                    r_unique_id = int(pending_order_row["Unique ID"])
                    order_time = pending_order_row["Order Time"]
                    status = pending_order_row["Status"]

                    # Cancel order if unique Id matches
                    if r_unique_id == unique_id:
                        try:
                            mark_pending_combo_order_cancelled(
                                unique_id,
                                order_time,
                                status,
                                last_update_time,
                                updated_status="Cancelled",
                                reason_for_failed="None",
                            )
                        except Exception as e:
                            if variables.flag_debug_mode:
                                print(e)

                # Positions Add or Switch.
                if cas_condition_type == "ADD":
                    process_cas_add_condition_for_combo(
                        unique_id,
                        solved_condition_string,
                        reference_price,
                        reference_position,
                        target_position,
                        cas_conditions_df,
                        series_id=series_id,
                    )
                elif cas_condition_type == "SWITCH":
                    process_cas_switch_condition_for_combo(
                        unique_id,
                        solved_condition_string,
                        reference_price,
                        reference_position,
                        target_position,
                        cas_conditions_df,
                    )

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Exception inside 'monitor_and_trigger_cas_condition', Exp: {e}")


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


# Method to place dummy order
def insert_order_when_conditional_add_switch_fails(
    account_id,
    new_unique_id,
    positions_to_trade,
    ticker_string=None,
    execution_engine=False,
    entry_price=None,
):
    try:
        try:
            # Get combo object using unique ids
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )

            combo_obj = local_unique_id_to_combo_obj[int(new_unique_id)]

            # get all legs
            all_legs = combo_obj.buy_legs + combo_obj.sell_legs

            for leg_obj in all_legs:
                # get current price
                try:
                    req_id = variables.con_id_to_req_id_dict[leg_obj.con_id]
                    bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]
                    current_price = (ask + bid) / 2

                except Exception as e:
                    if variables.flag_debug_mode:
                        print(f"Exception inside getting leg's bid-ask price, Exp: {e}")

                    return

        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Exception inside adding dummy order status, Exp: {e}")

            return

        positions_to_trade = int(positions_to_trade)

        # Action
        buy_sell_action = "BUY" if positions_to_trade > 0 else "SELL"

        # calculate actual entry price
        try:
            actual_entry_price = variables.unique_id_to_actual_prices_dict[
                int(new_unique_id)
            ][buy_sell_action]

            if not is_float(actual_entry_price):
                return

        except Exception as e:
            return

        # Position
        combo_quantity = abs(positions_to_trade)

        # Cehck if combo quanity is 0 ####################################################################
        if combo_quantity == 0:
            return

        # Init value
        order_type = "Market"
        limit_price, trigger_price, trail_value = "None", "None", "None"

        if entry_price != None:
            entry_price = str(entry_price)
        else:
            return

        status = "Filled"

        order_time = datetime.datetime.now(variables.target_timezone_obj)

        ladder_id = None
        sequence_id = None
        atr_multiple = None
        atr = None

        reference_price = None
        bypass_rm_check = "False"
        reason_for_failed = "None"
        limit_iv = "None"
        trigger_iv = "None"

        insert_combination_order_in_combo_status_db(
            new_unique_id,
            buy_sell_action,
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
            execution_engine="False",
            actual_entry_price=actual_entry_price,
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

        last_update_time = order_time

        # creating tuple of value to put in dataframe
        order_book_row_values = (
            new_unique_id,
            account_id,
            ticker_string,
            buy_sell_action,
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
            ladder_id,
            sequence_id,
            atr_multiple,
            atr,
            reason_for_failed,
            bypass_rm_check,
            str(execution_engine),
            limit_iv,
            trigger_iv,
            actual_entry_price,
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
            str(new_unique_id) in local_unique_id_list_of_selected_watchlist.split(",")
            or local_unique_id_list_of_selected_watchlist == "ALL"
        ):
            variables.screen.insert_combo_order_status_order_book(
                (
                    new_unique_id,
                    account_id,
                    ticker_string,
                    buy_sell_action,
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
                    ladder_id,
                    sequence_id,
                    atr_multiple,
                    atr,
                    reason_for_failed,
                    bypass_rm_check,
                    str(execution_engine),
                    limit_iv,
                    trigger_iv,
                    actual_entry_price,
                )
            )

        try:
            # Get combo object using unique ids
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )

            combo_obj = local_unique_id_to_combo_obj[int(new_unique_id)]

            # get all legs
            all_legs = combo_obj.buy_legs + combo_obj.sell_legs

            action_for_leg = buy_sell_action

            for leg_obj in all_legs:
                # get current price
                try:
                    req_id = variables.con_id_to_req_id_dict[leg_obj.con_id]
                    bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]
                    current_price = (ask + bid) / 2

                except Exception as e:
                    current_price = None

                if buy_sell_action in "BUY":
                    action_for_leg = leg_obj.action

                else:
                    if leg_obj.action in "BUY":
                        action_for_leg = "SELL"

                    else:
                        action_for_leg = "BUY"

                legs_quantity = combo_quantity * leg_obj.quantity

                insert_dummy_order_in_order_status(
                    new_unique_id,
                    leg_obj,
                    action_for_leg,
                    legs_quantity,
                    account_id,
                    order_time,
                    current_price,
                )

        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Exception inside adding dummy order status, Exp: {e}")

    except Exception as e:
        if variables.flag_debug_mode:
            print(e)


# Method to process cas add order after trigger
def process_cas_add_condition_for_combo(
    unique_id,
    solved_condition_string,
    reference_price,
    reference_position,
    target_position,
    cas_conditions_df,
    series_id="None",
):
    # Filter df for unique id
    cas_conditions_df = cas_conditions_df.loc[
        cas_conditions_df["Unique ID"] == unique_id
    ]

    # New Unique Id for new combo
    new_unique_id = variables.unique_id

    # Increasing it so we can use it.
    variables.unique_id += 1

    # New Unique Id for old combo
    new_unique_id_for_old_combo = variables.unique_id

    # Increasing it so we can use it.
    variables.unique_id += 1

    # Local unique_id_to_combo_obj
    local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

    # Local cas_unique_id_to_combo_obj
    local_cas_unique_id_to_combo_obj = copy.deepcopy(
        variables.cas_unique_id_to_combo_obj
    )

    # Local Position
    local_map_unique_id_to_positions = copy.deepcopy(
        variables.map_unique_id_to_positions
    )

    # Existing Combo
    existing_combo = local_unique_id_to_combo_obj[unique_id]

    # series id
    # series_id = "None"

    try:
        # Get Ticker String
        # Get combo obj
        local_stored_copy_of_combo_object = variables.unique_id_to_combo_obj[unique_id]

        # Ticker String
        ticker_string = make_informative_combo_string(local_stored_copy_of_combo_object)

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception inside getting ticker string inside conditional add, Exp: {e}"
            )

    # Get account id list which were present when condition add was placed but not in current session
    try:
        # account ids when not present when condition add was placed but in current session
        account_id_not_in_df = [
            account_id_item
            for account_id_item in variables.current_session_accounts
            if account_id_item not in cas_conditions_df["Account ID"].to_list()
        ]

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception inside getting account id list in conditional add, Exp: {e}"
            )

    dummy_orders_list = []

    # Iterate account ids
    for account_id in account_id_not_in_df:
        try:
            # Current Position of existing combo
            existing_position = local_map_unique_id_to_positions[unique_id][account_id]

        except Exception as e:
            # set value to zero
            existing_position = 0

        dummy_orders_list.append(
            [account_id, new_unique_id_for_old_combo, existing_position, ticker_string]
        )

        # Insert order without placing on TWS
        """insert_order_when_conditional_add_switch_fails(
            account_id,
            new_unique_id_for_old_combo,
            existing_position,
            ticker_string=ticker_string,
        )"""

    # Display
    variables.screen.screen_cas_obj.display_condition_triggered_informative_popup(
        unique_id,
        new_unique_id,
        "Add",
        solved_condition_string,
        reference_price,
        reference_position,
        new_unique_id_for_old_combo,
        series_id=series_id,
    )

    # Create a combo with cas legs (new unique ID) and take equal position in it
    cas_combo_object_with_new_unique_id = local_cas_unique_id_to_combo_obj[unique_id]
    cas_combo_object_with_new_unique_id.unique_id = new_unique_id

    # Make it available to class variables Add this combo to unique ID
    variables.unique_id_to_combo_obj[new_unique_id] = (
        cas_combo_object_with_new_unique_id
    )

    # Account_id list
    account_id_list = []

    # bypass rm check values list
    bypass_rm_check_list = []

    # target position list
    target_position_list = []

    existing_position_list = []

    # Iterate rows
    for indx, row in cas_conditions_df.iterrows():
        # Check status
        status = row["Status"]

        # Get account id and target positions
        account_id = row["Account ID"]
        target_position = row["Target Position"]

        # get bypass rm checks value
        bypass_rm_check = row["Bypass RM Check"]

        # series_id
        series_id = row["Series ID"]

        # switching off rm checks
        bypass_rm_check = "True"

        # print([bypass_rm_check, variables.flag_enable_rm_account_rules,variables.flag_account_liquidation_mode[account_id],account_id])
        # Check if status is failed
        if status == "Failed":
            continue

        try:
            # Current Position of existing combo
            existing_position = local_map_unique_id_to_positions[unique_id][account_id]

        except Exception as e:
            # Set value to 0
            existing_position = 0

        # Get target postion
        target_position = int(float(target_position))

        # Check if exsting position is not zero
        if existing_position != 0:
            positions_to_trade_for_old_combo = target_position - existing_position

        # Check if existing poition is zero
        elif existing_position == 0:
            positions_to_trade_for_old_combo = target_position

        else:
            pass

        try:
            # print([bypass_rm_check ,variables.flag_enable_rm_account_rules, variables.flag_account_liquidation_mode[account_id], account_id])

            if account_id not in variables.current_session_accounts:
                dummy_orders_list.append(
                    [
                        account_id,
                        new_unique_id_for_old_combo,
                        existing_position,
                        ticker_string,
                    ]
                )

                """insert_order_when_conditional_add_switch_fails(
                    account_id,
                    new_unique_id_for_old_combo,
                    existing_position,
                    ticker_string=ticker_string,
                )"""

                try:
                    # variables.screen.cancel_order(selected_item=order_time, updated_status='Failed')
                    # update value
                    variables.cas_condition_table_dataframe.loc[
                        variables.cas_condition_table_dataframe["Table ID Column"]
                        == f"{unique_id}_{account_id}",
                        "Status",
                    ] = "Failed"

                    # update value
                    variables.cas_condition_table_dataframe.loc[
                        variables.cas_condition_table_dataframe["Table ID Column"]
                        == f"{unique_id}_{account_id}",
                        "Reason For Failed",
                    ] = "Account not present in current session"

                    # Update in GUI table
                    variables.screen.screen_cas_obj.cas_condition_table.set(
                        f"{unique_id}_{account_id}", 10, "Failed"
                    )
                    variables.screen.screen_cas_obj.cas_condition_table.set(
                        f"{unique_id}_{account_id}",
                        11,
                        "Account not present in current session",
                    )

                    # Update in db
                    update_cas_condition_status(unique_id, "Failed", account_id)
                    update_cas_condition_reason_for_failed(
                        unique_id, "Account not present in current session", account_id
                    )

                    # Error pop up
                    """error_title = f"For Account ID: {account_id}, Order cannot be placed, \n'Account not present in current session'"
                    error_string = f"For Account ID: {account_id}, Order cannot be placed, \n'Account not present in current session'"
    
                    variables.screen.display_error_popup(error_title, error_string)"""

                    if series_id not in [None, "None"]:
                        terminate_series(unique_id, series_id)

                    """variables.screen.screen_conditional_series_tab.stop_series(
                        series_id, unique_id
                    )"""

                except Exception as e:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception inside adding failed row for conditional add, Exp: {e}"
                        )

                continue

            elif (
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
                    insert_order_when_conditional_add_switch_fails(
                        account_id,
                        new_unique_id_for_old_combo,
                        existing_position,
                        ticker_string=ticker_string,
                    )

                    try:
                        # variables.screen.cancel_order(selected_item=order_time, updated_status='Failed')
                        # update value
                        variables.cas_condition_table_dataframe.loc[
                            variables.cas_condition_table_dataframe["Table ID Column"]
                            == f"{unique_id}_{account_id}",
                            "Status",
                        ] = "Failed"

                        # update value
                        variables.cas_condition_table_dataframe.loc[
                            variables.cas_condition_table_dataframe["Table ID Column"]
                            == f"{unique_id}_{account_id}",
                            "Reason For Failed",
                        ] = "Account is in liquidation mode"

                        # Update in GUI table
                        variables.screen.screen_cas_obj.cas_condition_table.set(
                            f"{unique_id}_{account_id}", 10, "Failed"
                        )
                        variables.screen.screen_cas_obj.cas_condition_table.set(
                            f"{unique_id}_{account_id}",
                            11,
                            "Account is in liquidation mode",
                        )

                        # Update in db
                        update_cas_condition_status(unique_id, "Failed", account_id)
                        update_cas_condition_reason_for_failed(
                            unique_id, "Account is in liquidation mode", account_id
                        )

                        # Error pop up
                        """error_title = f"For Account ID: {account_id}, Order cannot be placed, \naccount is in liquidation mode"
                        error_string = f"For Account ID: {account_id}, Order cannot be placed, \naccount is in liquidation mode"
                        
                        variables.screen.display_error_popup(error_title, error_string)"""

                        if series_id not in [None, "None"]:
                            terminate_series(unique_id, series_id)

                        """variables.screen.screen_conditional_series_tab.stop_series(
                            series_id, unique_id
                        )"""

                    except Exception as e:
                        # Print to console
                        if variables.flag_debug_mode:
                            print(
                                f"Exception inside adding failed row for conditional add, Exp: {e}"
                            )

                    continue

            elif not trade_level_rm_check_result(bypass_rm_check, unique_id):
                time.sleep(variables.rm_checks_interval_if_failed)

                if not trade_level_rm_check_result(bypass_rm_check, unique_id):
                    insert_order_when_conditional_add_switch_fails(
                        account_id,
                        new_unique_id_for_old_combo,
                        existing_position,
                        ticker_string=ticker_string,
                    )

                    try:
                        # variables.screen.cancel_order(selected_item=order_time, updated_status='Failed')
                        # update value
                        variables.cas_condition_table_dataframe.loc[
                            variables.cas_condition_table_dataframe["Table ID Column"]
                            == f"{unique_id}_{account_id}",
                            "Status",
                        ] = "Failed"

                        # update value
                        variables.cas_condition_table_dataframe.loc[
                            variables.cas_condition_table_dataframe["Table ID Column"]
                            == f"{unique_id}_{account_id}",
                            "Reason For Failed",
                        ] = "Trade Level RM check Failed"

                        # Update in GUI table
                        variables.screen.screen_cas_obj.cas_condition_table.set(
                            f"{unique_id}_{account_id}", 10, "Failed"
                        )
                        variables.screen.screen_cas_obj.cas_condition_table.set(
                            f"{unique_id}_{account_id}",
                            11,
                            "Trade Level RM check Failed",
                        )

                        # Update in db
                        update_cas_condition_status(unique_id, "Failed", account_id)
                        update_cas_condition_reason_for_failed(
                            unique_id, "Trade Level RM check Failed", account_id
                        )

                        if series_id not in [None, "None"]:
                            terminate_series(unique_id, series_id)

                        """variables.screen.screen_conditional_series_tab.stop_series(
                            series_id, unique_id
                        )"""

                    except Exception as e:
                        # Print to console
                        if variables.flag_debug_mode:
                            print(
                                f"Exception inside adding failed trade level rm check for conditional add, Exp: {e}"
                            )

                    continue

        except Exception as e:
            if variables.flag_debug_mode:
                print(f"Checking if ")

        # append values
        account_id_list.append(account_id)
        bypass_rm_check_list.append(bypass_rm_check)
        target_position_list.append(target_position)
        existing_position_list.append(existing_position)

        # Check comment inside the 'send_order' at the starting of function refering to 'local_stored_copy_of_combo_object'
        # Position to trade is not 'zero' for old combo
        if positions_to_trade_for_old_combo != 0:
            # Action
            buy_sell_action = "BUY" if positions_to_trade_for_old_combo > 0 else "SELL"

            # Position
            combo_quantity = abs(positions_to_trade_for_old_combo)

            # Init value
            order_type = "Market"
            limit_price, trigger_price, trail_value = "", "", ""

            # Show User a Poup that the order is triggered
            # variables.screen.display_error_popup("Unique ID : {unique_id}", "Conditional Add.")

            rm_checks_result = True

            # Place order for old combo
            # Take position: Send order in a separate thread
            take_position_thread = threading.Thread(
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
                kwargs={"account_id": account_id, "bypass_rm_check": bypass_rm_check},
            )
            take_position_thread.start()
            time.sleep(0.5)

    # Update the status to Triggered
    update_cas_condition_status(unique_id, status="Completed")

    # Create Target New combo (Existing + Cas Combo)
    local_existing_combo = local_unique_id_to_combo_obj[unique_id]
    local_cas_combo = local_cas_unique_id_to_combo_obj[unique_id]

    # All legs of existing and cas combo
    all_legs = (
        local_existing_combo.buy_legs
        + local_cas_combo.buy_legs
        + local_existing_combo.sell_legs
        + local_cas_combo.sell_legs
    )

    # All legs for existing combo (for Retaining old Combo)
    all_legs_existing_combo = (
        local_existing_combo.buy_legs + local_existing_combo.sell_legs
    )

    # New Combo Value
    new_combo_values = get_list_of_leg_values_for_combo_creation(
        new_unique_id, all_legs
    )

    # Existing Combo Value (for Retaining old Combo)
    existing_combo_values = get_list_of_leg_values_for_combo_creation(
        new_unique_id_for_old_combo, all_legs_existing_combo
    )

    incremental_combo_for_order = variables.cas_unique_id_to_combo_obj[unique_id]

    # Importing Function
    from com.combination_helper import (
        create_combination,
        subscribe_mktdata_combo_obj,
        insert_combination_db,
    )

    combo_values_list = [new_combo_values, existing_combo_values]
    new_unique_id_list = [new_unique_id, new_unique_id_for_old_combo]

    new_combo_unique_id = new_unique_id

    combo_obj_list = []

    for indx, (new_unique_id, combo_values) in enumerate(
        zip(new_unique_id_list, combo_values_list)
    ):
        # Create new incremental combo now, it also make the combo available in class, but redoing in below again
        (
            show_error_popup,
            error_title,
            error_string,
            new_incremental_combo,
        ) = create_combination(
            combo_values,
        )

        if indx == 1:
            # Display Error Popup
            if show_error_popup == True:
                # It should never happen technically
                variables.screen.display_error_popup(error_title, error_string)
                return
            else:
                pass

        # Make it available to class variables Add this combo to unique ID
        variables.unique_id_to_combo_obj[new_unique_id] = new_incremental_combo

        # Subscribe the mkt data
        subscribe_mktdata_combo_obj(new_incremental_combo)

        # Insert combo in DB
        insert_combination_db(True, new_incremental_combo)

        combo_obj_list.append(new_incremental_combo)

        # reset counter
        variables.counter_trade_rm_checks = 10**10

        # set value to false
        variables.flag_account_checks_completed_wait = False

        # Init
        counter_time = 0

        # wait for it to become true
        while (
            counter_time < 10 and variables.flag_account_checks_completed_wait == False
        ):
            counter_time += 0.5
            time.sleep(0.5)

        # Set counter to big number so the cas values can be updated
        """variables.flag_update_long_term_value = True
        variables.flag_update_intra_day_value = True
        variables.flag_update_hv_related_value = True
        variables.flag_update_volume_related_value = True
        variables.flag_update_support_resistance_and_relative_fields = True
        variables.flag_update_atr_for_order = True"""

        # Print to console
        if variables.flag_debug_mode:
            print("ADD condition Incremental Combo and Retain Old Combo")
            print(new_incremental_combo)

    # Removing deleted cas condition from watchlist cas condition dataframe
    variables.cas_condition_table_dataframe = variables.cas_condition_table_dataframe[
        (variables.cas_condition_table_dataframe["Unique ID"] != unique_id)
        | (
            (variables.cas_condition_table_dataframe["Unique ID"] == unique_id)
            & (variables.cas_condition_table_dataframe["Status"] != "Pending")
        )
    ]

    # update evaluation unique id in db
    replace_eval_unique_id_cas_condition_db(
        unique_id, new_unique_id_for_old_combo, variables.sql_table_cas_status
    )

    # Update values in column 'Evaluation Unique ID' where 'Evaluation Unique ID' is equal to unique id
    variables.cas_condition_table_dataframe.loc[
        variables.cas_condition_table_dataframe["Evaluation Unique ID"]
        == str(unique_id),
        "Evaluation Unique ID",
    ] = str(new_unique_id_for_old_combo)

    # Update values in column 'trading Unique ID' where 'trading Unique ID' is equal to unique id
    variables.cas_condition_table_dataframe.loc[
        variables.cas_condition_table_dataframe["Trading Combo Unique ID"].isin(
            [unique_id, str(unique_id)]
        ),
        "Trading Combo Unique ID",
    ] = new_unique_id_for_old_combo

    # Update GUI table
    variables.flag_cas_condition_table_watchlist_changed = True
    variables.screen.screen_cas_obj.update_cas_condition_table_watchlist_change()

    from com.prices import calculate_combo_prices

    calculate_combo_prices()

    # update_combo_positions_in_positions_tab()

    # check series id
    if series_id not in ["None", "N/A", None]:
        variables.screen.screen_conditional_series_tab.update_unique_id_series(
            new_combo_unique_id,
            unique_id,
            new_unique_id_for_old_combo,
            flag_series=True,
            series_id=series_id,
        )

    else:
        variables.screen.screen_conditional_series_tab.update_unique_id_series(
            new_combo_unique_id, unique_id, new_unique_id_for_old_combo
        )

    # check if order was originated from conditional series
    if series_id not in ["None", "N/A", None]:
        # variables.screen.screen_cas_obj.delete_cas_condition(unique_id)

        variables.screen.screen_conditional_series_tab.update_conditional_order_after_order_completed(
            series_id, new_combo_unique_id, unique_id, new_unique_id_for_old_combo
        )

    try:
        # Delete the existing combo
        variables.screen.delete_row(unique_id)

    except Exception as e:
        if variables.flag_debug_mode:
            print(f"Exception for delteing combo in cas add trigger function, Exp: {e}")

    for account_id, bypass_rm_check, target_position, existing_position in zip(
        account_id_list,
        bypass_rm_check_list,
        target_position_list,
        existing_position_list,
    ):
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
                continue

        elif not trade_level_rm_check_result(bypass_rm_check, new_unique_id):
            time.sleep(variables.rm_checks_interval_if_failed)

            if not trade_level_rm_check_result(bypass_rm_check, unique_id):
                continue

        target_position = int(float(target_position))

        # target position is not 'zero'
        if target_position != 0:
            # Action
            buy_sell_action = "BUY" if target_position > 0 else "SELL"

            # Position
            combo_quantity = abs(target_position)

            # Init value
            order_type = "Market"
            limit_price, trigger_price, trail_value = "", "", ""

            # Place order for incremental combo
            # Take position: Send order in a separate thread
            take_position_thread = threading.Thread(
                target=send_order,
                args=(
                    new_combo_unique_id,
                    buy_sell_action,
                    order_type,
                    combo_quantity,
                    limit_price,
                    trigger_price,
                    trail_value,
                ),
                kwargs={
                    "incremental_combo": incremental_combo_for_order,
                    "account_id": account_id,
                    "bypass_rm_check": bypass_rm_check,
                },
            )
            take_position_thread.start()
            time.sleep(0.5)

    # check if order was originated from conditional series
    """'if series_id not in ["None", "N/A", None]:
        # variables.screen.screen_cas_obj.delete_cas_condition(unique_id)

        variables.screen.screen_conditional_series_tab.update_conditional_order_after_order_completed(
            series_id, new_combo_unique_id, unique_id, new_unique_id_for_old_combo
        )

    # Delete the existing combo
    variables.screen.delete_row(unique_id)"""

    try:
        current_price_unique_id = variables.unique_id_to_prices_dict[unique_id]

        current_buy_price, current_sell_price = (
            current_price_unique_id["BUY"],
            current_price_unique_id["SELL"],
        )

        current_price = (current_buy_price + current_sell_price) / 2

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception inside getting current price inside conditional add, Exp: {e}"
            )

        current_price = None

    for row in dummy_orders_list:
        insert_order_when_conditional_add_switch_fails(
            row[0], row[1], row[2], ticker_string=row[3], entry_price=current_price
        )

    # Create a thread and pass the result_queue as an argument
    new_combo_values_thread = threading.Thread(
        target=get_values_for_new_combo,
        args=(
            combo_obj_list,
            new_unique_id_list,
        ),
    )

    # Start the thread
    new_combo_values_thread.start()


# Method to process cas switch order after trigger
def process_cas_switch_condition_for_combo(
    unique_id,
    solved_condition_string,
    reference_price,
    reference_position,
    target_position,
    cas_conditions_df,
):
    # New Unique Id for new combo
    new_unique_id = variables.unique_id

    # Increasing it so we can use it.
    variables.unique_id += 1

    # New Unique Id for old combo
    new_unique_id_for_old_combo = variables.unique_id

    # Increasing it so we can use it.
    variables.unique_id += 1

    # Local unique_id_to_combo_obj
    local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

    # Local cas_unique_id_to_combo_obj
    local_cas_unique_id_to_combo_obj = copy.deepcopy(
        variables.cas_unique_id_to_combo_obj
    )

    # Local Position
    local_map_unique_id_to_positions = copy.deepcopy(
        variables.map_unique_id_to_positions
    )

    # Existing Combo
    existing_combo = local_unique_id_to_combo_obj[unique_id]

    # Account_id list
    account_id_list = []

    # bypass rm check values list
    bypass_rm_check_list = []

    # target position list
    target_position_list = []

    dummy_orders_list = []

    # series id
    series_id = "None"

    try:
        # Get Ticker String
        # Get combo obj
        local_stored_copy_of_combo_object = variables.unique_id_to_combo_obj[unique_id]

        # Ticker String
        ticker_string = make_informative_combo_string(local_stored_copy_of_combo_object)

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception inside getting ticker string inside conditional switch, Exp: {e}"
            )

    try:
        # account ids when not present when condition add was placed but in current session
        account_id_not_in_df = [
            account_id_item
            for account_id_item in variables.current_session_accounts
            if account_id_item not in cas_conditions_df["Account ID"].to_list()
        ]

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception inside getting account id list inside conditional switch, Exp: {e}"
            )

    # Iterate account ids
    for account_id in account_id_not_in_df:
        try:
            # Current Position of existing combo
            existing_position = local_map_unique_id_to_positions[unique_id][account_id]

        except Exception as e:
            # Set value to 0
            existing_position = 0

        dummy_orders_list.append(
            [account_id, new_unique_id_for_old_combo, existing_position, ticker_string]
        )

        # Insert order without placing on TWS
        """insert_order_when_conditional_add_switch_fails(
            account_id,
            new_unique_id_for_old_combo,
            existing_position,
            ticker_string=ticker_string,
        )"""

    # Iterate rows
    for indx, row in cas_conditions_df.iterrows():
        # Get account id and target positions
        account_id = row["Account ID"]
        target_position = row["Target Position"]

        # Check status
        status = row["Status"]

        # get bypass rm checks value
        bypass_rm_check = row["Bypass RM Check"]

        # switching off rm checks
        bypass_rm_check = "True"

        # series id
        series_id = row["Series ID"]

        # Check if status is failed
        if status == "Failed":
            continue

        if account_id in variables.current_session_accounts:
            # Current Position of existing combo
            existing_position = local_map_unique_id_to_positions[unique_id][account_id]

            # Buy legs and Sell legs
            buy_legs = existing_combo.buy_legs
            sell_legs = existing_combo.sell_legs
            existing_all_legs = buy_legs + sell_legs

        if account_id not in variables.current_session_accounts:
            dummy_orders_list.append(
                [
                    account_id,
                    new_unique_id_for_old_combo,
                    target_position,
                    ticker_string,
                ]
            )

            """insert_order_when_conditional_add_switch_fails(
                account_id,
                new_unique_id_for_old_combo,
                existing_position,
                ticker_string,
            )"""

            try:
                # variables.screen.cancel_order(selected_item=order_time, updated_status='Failed')
                # update value
                variables.cas_condition_table_dataframe.loc[
                    variables.cas_condition_table_dataframe["Table ID Column"]
                    == f"{unique_id}_{account_id}",
                    "Status",
                ] = "Failed"

                # update value
                variables.cas_condition_table_dataframe.loc[
                    variables.cas_condition_table_dataframe["Table ID Column"]
                    == f"{unique_id}_{account_id}",
                    "Reason For Failed",
                ] = "Account not present in current session"

                # Update in GUI table
                variables.screen.screen_cas_obj.cas_condition_table.set(
                    f"{unique_id}_{account_id}", 10, "Failed"
                )
                variables.screen.screen_cas_obj.cas_condition_table.set(
                    f"{unique_id}_{account_id}",
                    11,
                    "Account not present in current session",
                )

                # Update in db
                update_cas_condition_status(unique_id, "Failed", account_id)
                update_cas_condition_reason_for_failed(
                    unique_id, "Account not present in current session", account_id
                )

                # Error pop up
                """error_title = f"For Account ID: {account_id}, Order cannot be placed, \n'Account not present in current session'"
                error_string = f"For Account ID: {account_id}, Order cannot be placed, \n'Account not present in current session'"

                variables.screen.display_error_popup(error_title, error_string)"""

                if series_id not in [None, "None"]:
                    terminate_series(unique_id, series_id)

                """variables.screen.screen_conditional_series_tab.stop_series(
                    series_id, unique_id
                )"""

            except Exception as e:
                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Exception inside adding failed row for conditional add, Exp: {e}"
                    )

            continue

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
                insert_order_when_conditional_add_switch_fails(
                    account_id,
                    new_unique_id_for_old_combo,
                    existing_position,
                    ticker_string,
                )

                try:
                    # variables.screen.cancel_order(selected_item=order_time, updated_status='Failed')
                    # update value
                    variables.cas_condition_table_dataframe.loc[
                        variables.cas_condition_table_dataframe["Table ID Column"]
                        == f"{unique_id}_{account_id}",
                        "Status",
                    ] = "Failed"

                    # update value
                    variables.cas_condition_table_dataframe.loc[
                        variables.cas_condition_table_dataframe["Table ID Column"]
                        == f"{unique_id}_{account_id}",
                        "Reason For Failed",
                    ] = "Account is in liquidation mode"

                    # Update in GUI table
                    variables.screen.screen_cas_obj.cas_condition_table.set(
                        f"{unique_id}_{account_id}", 10, "Failed"
                    )
                    variables.screen.screen_cas_obj.cas_condition_table.set(
                        f"{unique_id}_{account_id}",
                        11,
                        "Account is in liquidation mode",
                    )

                    # Update in db
                    update_cas_condition_status(unique_id, "Failed", account_id)
                    update_cas_condition_reason_for_failed(
                        unique_id, "Account is in liquidation mode", account_id
                    )

                    # Error pop up
                    """error_title = f"For Account ID: {account_id}, Order cannot be placed, \naccount is in liquidation mode"
                    error_string = f"For Account ID: {account_id}, Order cannot be placed, \naccount is in liquidation mode"
    
                    variables.screen.display_error_popup(error_title, error_string)"""

                    if series_id not in [None, "None"]:
                        terminate_series(unique_id, series_id)

                    """variables.screen.screen_conditional_series_tab.stop_series(
                        series_id, unique_id
                    )"""

                except Exception as e:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception inside adding failed row for conditional add, Exp: {e}"
                        )

                continue

        if not trade_level_rm_check_result(bypass_rm_check, unique_id):
            time.sleep(variables.rm_checks_interval_if_failed)

            if not trade_level_rm_check_result(bypass_rm_check, unique_id):
                insert_order_when_conditional_add_switch_fails(
                    account_id,
                    new_unique_id_for_old_combo,
                    existing_position,
                    ticker_string,
                )

                # variables.screen.cancel_order(selected_item=order_time, updated_status='Failed')
                # update value
                variables.cas_condition_table_dataframe.loc[
                    variables.cas_condition_table_dataframe["Table ID Column"]
                    == f"{unique_id}_{account_id}",
                    "Status",
                ] = "Failed"

                # update value
                variables.cas_condition_table_dataframe.loc[
                    variables.cas_condition_table_dataframe["Table ID Column"]
                    == f"{unique_id}_{account_id}",
                    "Reason For Failed",
                ] = "Trade Level RM check Failed"

                # Update in GUI table
                variables.screen.screen_cas_obj.cas_condition_table.set(
                    f"{unique_id}_{account_id}", 10, "Failed"
                )
                variables.screen.screen_cas_obj.cas_condition_table.set(
                    f"{unique_id}_{account_id}", 11, "Trade Level RM check Failed"
                )

                # Update in db
                update_cas_condition_status(unique_id, "Failed", account_id)
                update_cas_condition_reason_for_failed(
                    unique_id, "Trade Level RM check Failed", account_id
                )

                if series_id not in [None, "None"]:
                    terminate_series(unique_id, series_id)

                """variables.screen.screen_conditional_series_tab.stop_series(
                    series_id, unique_id
                )"""

                continue

        # append account id
        account_id_list.append(account_id)

        # append bypass rm check value
        bypass_rm_check_list.append(bypass_rm_check)

        # append target position
        target_position_list.append(target_position)

        # Close position if not 'zero'
        if existing_position != 0:
            # Action
            buy_sell_action = "SELL" if existing_position > 0 else "BUY"

            # Position
            combo_quantity = abs(existing_position)

            # Init value
            order_type = "Market"
            limit_price, trigger_price, trail_value = "", "", ""

            # Close position: Send order in a separate thread
            close_position_thread = threading.Thread(
                target=send_order,
                args=(
                    unique_id,
                    buy_sell_action,
                    "Market",
                    combo_quantity,
                    limit_price,
                    trigger_price,
                    trail_value,
                ),
                kwargs={"account_id": account_id, "bypass_rm_check": bypass_rm_check},
            )
            close_position_thread.start()
            time.sleep(0.5)

    # Update the status to Triggered
    update_cas_condition_status(unique_id, status="Completed")

    # Target New combo
    cas_combo = local_cas_unique_id_to_combo_obj[unique_id]
    all_legs = cas_combo.buy_legs + cas_combo.sell_legs

    # Combo Value
    new_combo_values = get_list_of_leg_values_for_combo_creation(
        new_unique_id, all_legs
    )

    # Existing Combo Value (To retain existing combo)
    existing_combo_values = get_list_of_leg_values_for_combo_creation(
        new_unique_id_for_old_combo, existing_all_legs
    )

    # Importing Function
    from com.combination_helper import (
        create_combination,
        subscribe_mktdata_combo_obj,
        insert_combination_db,
    )

    combo_values_list = [new_combo_values, existing_combo_values]
    new_unique_id_list = [new_unique_id, new_unique_id_for_old_combo]

    new_combo_unique_id = new_unique_id

    combo_obj_list = []

    for indx, (new_unique_id_, combo_values) in enumerate(
        zip(new_unique_id_list, combo_values_list)
    ):
        # Create new combo now
        (
            show_error_popup,
            error_title,
            error_string,
            new_incremental_combo,
        ) = create_combination(
            combo_values,
        )

        # Display Error Popup
        if show_error_popup == True and indx == 1:
            # It should never happen technically
            variables.screen.display_error_popup(error_title, error_string)
            return
        else:
            pass

        # Print to console
        if variables.flag_debug_mode:
            print("Switch condition Incremental Combo and Retain Old combo")
            print(new_incremental_combo)

        # Subscribe the mkt data
        subscribe_mktdata_combo_obj(new_incremental_combo)

        # Insert combo in DB
        insert_combination_db(True, new_incremental_combo)

        combo_obj_list.append(new_incremental_combo)

        # reset counter
        variables.counter_trade_rm_checks = 10**10

        # set value to false
        variables.flag_account_checks_completed_wait = False

        # Init
        counter_time = 0

        # wait for it to become true
        while (
            counter_time < 10 and variables.flag_account_checks_completed_wait == False
        ):
            counter_time += 0.5
            time.sleep(0.5)

        # Set counter to big number so the cas values can be updated
        """variables.flag_update_long_term_value = True
        variables.flag_update_intra_day_value = True
        variables.flag_update_hv_related_value = True
        variables.flag_update_volume_related_value = True
        variables.flag_update_support_resistance_and_relative_fields = True
        variables.flag_update_atr_for_order = True"""

    # Display
    variables.screen.screen_cas_obj.display_condition_triggered_informative_popup(
        unique_id,
        new_unique_id,
        "Switch",
        solved_condition_string,
        reference_price,
        reference_position,
        new_unique_id_for_old_combo,
        series_id=series_id,
    )

    try:
        unique_id = int(unique_id)
    except Exception as e:
        if variables.flag_debug_mode:
            print(e)

    # Removing deleted cas condition from watchlist cas condition dataframe
    variables.cas_condition_table_dataframe = variables.cas_condition_table_dataframe[
        (variables.cas_condition_table_dataframe["Unique ID"] != unique_id)
        | (
            (variables.cas_condition_table_dataframe["Unique ID"] == unique_id)
            & (variables.cas_condition_table_dataframe["Status"] != "Pending")
        )
    ]

    # update evaluation unique id in db
    replace_eval_unique_id_cas_condition_db(
        unique_id, new_unique_id_for_old_combo, variables.sql_table_cas_status
    )
    # print(variables.cas_condition_table_dataframe.to_string())
    # Update values in column 'Evaluation Unique ID' where 'Evaluation Unique ID' is equal to unique id
    variables.cas_condition_table_dataframe.loc[
        variables.cas_condition_table_dataframe["Evaluation Unique ID"]
        == str(unique_id),
        "Evaluation Unique ID",
    ] = str(new_unique_id_for_old_combo)

    # Update values in column 'trading Unique ID' where 'trading Unique ID' is equal to unique id
    variables.cas_condition_table_dataframe.loc[
        variables.cas_condition_table_dataframe["Trading Combo Unique ID"].isin(
            [unique_id, str(unique_id)]
        ),
        "Trading Combo Unique ID",
    ] = new_unique_id_for_old_combo

    # Update GUI table
    variables.flag_cas_condition_table_watchlist_changed = True
    variables.screen.screen_cas_obj.update_cas_condition_table_watchlist_change()

    # Create a thread and pass the result_queue as an argument
    new_combo_values_thread = threading.Thread(
        target=get_values_for_new_combo,
        args=(
            combo_obj_list,
            new_unique_id_list,
        ),
    )

    # Start the thread
    new_combo_values_thread.start()

    from com.prices import calculate_combo_prices

    calculate_combo_prices()

    # update_combo_positions_in_positions_tab()

    # check series id
    if series_id not in ["None", "N/A", None]:
        variables.screen.screen_conditional_series_tab.update_unique_id_series(
            new_combo_unique_id,
            unique_id,
            new_unique_id_for_old_combo,
            flag_series=True,
            series_id=series_id,
        )

    else:
        variables.screen.screen_conditional_series_tab.update_unique_id_series(
            new_combo_unique_id, unique_id, new_unique_id_for_old_combo
        )

    # check if order was originated from conditional series
    if series_id not in ["None", "N/A", None]:
        # variables.screen.screen_cas_obj.delete_cas_condition(unique_id)

        variables.screen.screen_conditional_series_tab.update_conditional_order_after_order_completed(
            series_id, new_combo_unique_id, unique_id, new_unique_id_for_old_combo
        )

    try:
        # Delete the existing combo
        variables.screen.delete_row(unique_id)

    except Exception as e:
        if variables.flag_debug_mode:
            print(
                f"Exception for delteing combo in cas switch triiger function, Exp: {e}"
            )

    for target_position, account_id, bypass_rm_check in zip(
        target_position_list, account_id_list, bypass_rm_check_list
    ):
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
                continue

        elif not trade_level_rm_check_result(bypass_rm_check, new_unique_id):
            time.sleep(variables.rm_checks_interval_if_failed)

            if not trade_level_rm_check_result(bypass_rm_check, unique_id):
                continue

        target_position = int(float(target_position))

        # Take Position in the new incremental combo
        # Close position if not 'zero'
        if target_position != 0:
            # Action
            buy_sell_action = "BUY" if target_position > 0 else "SELL"

            # Position
            combo_quantity = abs(target_position)

            # None value

            limit_price, trigger_price, trail_value = "", "", ""

            # Take new position in new combo: Send order in a separate thread
            take_new_position_thread = threading.Thread(
                target=send_order,
                args=(
                    new_unique_id,
                    buy_sell_action,
                    "Market",
                    combo_quantity,
                    limit_price,
                    trigger_price,
                    trail_value,
                ),
                kwargs={
                    "account_id": account_id,
                    "bypass_rm_check": bypass_rm_check,
                },
            )
            take_new_position_thread.start()
            time.sleep(0.5)

    try:
        current_price_unique_id = variables.unique_id_to_prices_dict[
            new_unique_id_for_old_combo
        ]

        current_buy_price, current_sell_price = (
            current_price_unique_id["BUY"],
            current_price_unique_id["SELL"],
        )

        current_price = (current_buy_price + current_sell_price) / 2

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception inside getting current price inside conditional switch, Exp: {e}"
            )

        current_price = None

    for row in dummy_orders_list:
        insert_order_when_conditional_add_switch_fails(
            row[0], row[1], row[2], ticker_string=row[3], entry_price=current_price
        )

    # check if order was originated from conditional series
    """if series_id not in ["None", "N/A", None]:
        # variables.screen.screen_cas_obj.delete_cas_condition(unique_id)

        variables.screen.screen_conditional_series_tab.update_conditional_order_after_order_completed(
            series_id, new_combo_unique_id, unique_id, new_unique_id_for_old_combo
        )

    # Delete the existing combo
    variables.screen.delete_row(unique_id)"""


# Method to get new values for new combo
def get_values_for_new_combo(combo_obj_list, new_unique_id_list):
    from com.single_combo_value_calculations import single_combo_values

    for combo_obj, unique_id_added in zip(combo_obj_list, new_unique_id_list):
        # Create a thread and pass the result_queue as an argument
        single_combo_values(combo_obj, unique_id_added)


# Method to get leg values to create combo
def get_list_of_leg_values_for_combo_creation(target_unique_id, all_legs):
    # This map will be use to eliminate the duplicate conid(as well as adjusting the net qty for buy/sell)
    map_con_id_to_leg_info = {}

    # Will contain all the info for legs which is required to make combo
    combo_values = []

    # Processing legs, to have info in desired format
    for leg_obj in all_legs:
        con_id = int(leg_obj.con_id)
        action = (leg_obj.action).strip()
        quantity = int(leg_obj.quantity)

        # If conid already exists update the qty and action
        if con_id in map_con_id_to_leg_info:
            # Already existing leg values
            old_qty = int(map_con_id_to_leg_info[con_id][7])
            old_action = map_con_id_to_leg_info[con_id][1].strip()

            # Adjusting the qty and the action
            if old_action == action:
                # Action is same, Add qty
                new_qty = old_qty + quantity

                # Update the quantity
                map_con_id_to_leg_info[con_id][7] = new_qty

            else:
                # Action is different, Adjust the qty and action

                # Same qty delete the leg
                if old_qty == quantity:
                    del map_con_id_to_leg_info[con_id]
                elif old_qty < quantity:
                    # New adjusted Qty
                    new_qty = abs(old_qty - quantity)

                    # Update the quantity
                    map_con_id_to_leg_info[con_id][7] = new_qty

                    # Update the action
                    map_con_id_to_leg_info[con_id][1] = action

                else:
                    # New adjusted Qty
                    new_qty = abs(old_qty - quantity)

                    # Update the quantity
                    map_con_id_to_leg_info[con_id][7] = new_qty

        else:
            # Add Individual Leg info to dict
            map_con_id_to_leg_info[con_id] = [
                target_unique_id,
                leg_obj.action,
                leg_obj.sec_type,
                leg_obj.symbol,
                leg_obj.dte,
                leg_obj.delta,
                leg_obj.right,
                leg_obj.quantity,
                leg_obj.multiplier,
                leg_obj.exchange,
                leg_obj.trading_class,
                leg_obj.currency,
                leg_obj.con_id,
                leg_obj.primary_exchange,
                leg_obj.strike_price,
                leg_obj.expiry_date,
            ]

    # Convert the legs value to strings
    for con_id, leg_info_list in map_con_id_to_leg_info.items():
        # Converting to String
        leg_info_list = [str(item) for item in leg_info_list]

        # Appending leg to the list
        combo_values.append(leg_info_list)

    return combo_values
