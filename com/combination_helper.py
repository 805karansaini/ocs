"""
Created on 15-Mar-2023

@author: Karan
"""
import time

from com.leg import *
from com.combination import *
from com.contracts import *
from com.variables import *
from com.prices import *
from com.mysql_io import *
from com.leg_identifier import *


# To check if values if int or not
def is_integer(num):

    try:

        # check if reminder is zero or not
        if float(num) % 1 != 0:
            return False
        else:
            return True
    except Exception as e:

        return False


# Create combination: When we get legs from user/DB resolve the legs and make combination object, and inserts the high level detail of combo in the combo creator tab
def create_combination(
    user_combination_input, input_from_db=False, input_from_cas_tab=False
):

    # Print to console
    if variables.flag_debug_mode:
        print("\nCreating Combination: ")

    # Column names, for each leg
    leg_columns = variables.leg_columns

    # Create DataFrame, with columns
    all_rows_df = pd.DataFrame(user_combination_input, columns=leg_columns)

    # Init order_specs_dict, keeps on changing for every iteration of row
    leg_specs_dict = {}

    # List of legs in df
    legs_dict_list = []

    #### Start: This Part Deals with cleaning data, and checking basic info of leg is in correct format #####

    # First check all the legs, if the sufficient info not given throw error, Then try resolving the legs (get conid etc)
    for leg_no, row in all_rows_df.iterrows():

        # If we have conid we will not throw any error
        is_con_id_available_for_leg = False

        # Read user inputs
        unique_id = int(row["Unique ID"])

        if unique_id not in leg_specs_dict:
            leg_specs_dict[unique_id] = dict()

        # Strip all the values
        leg_specs_dict[unique_id]["Action"] = str(row["Action"]).strip().upper()
        leg_specs_dict[unique_id]["SecType"] = str(row["SecType"]).strip().upper()
        leg_specs_dict[unique_id]["Symbol"] = str(row["Symbol"]).strip().upper()
        leg_specs_dict[unique_id]["DTE"] = str(row["DTE"]).strip()
        leg_specs_dict[unique_id]["Delta"] = str(row["Delta"]).strip()
        leg_specs_dict[unique_id]["Right"] = str(row["Right"]).strip().upper()
        leg_specs_dict[unique_id]["#Lots"] = str(row["#Lots"]).strip()
        leg_specs_dict[unique_id]["Lot Size"] = str(
            row["Lot Size"]
        ).strip()  # Lot Size is Lot Size
        leg_specs_dict[unique_id]["Exchange"] = str(row["Exchange"]).strip().upper()
        leg_specs_dict[unique_id]["Trading Class"] = (
            str(row["Trading Class"]).strip().upper()
        )
        leg_specs_dict[unique_id]["Currency"] = str(row["Currency"]).strip().upper()
        leg_specs_dict[unique_id]["ConID"] = str(row["ConID"]).strip()
        leg_specs_dict[unique_id]["Primary Exchange"] = (
            str(row["Primary Exchange"]).strip().upper()
        )
        leg_specs_dict[unique_id]["Strike"] = str(row["Strike"]).strip()
        leg_specs_dict[unique_id]["Expiry"] = str(row["Expiry"]).strip()

        # Action is necessary, so as the #Lots, the way input is taken we will always have the Action,
        # Now make sure other fields, are available are in correct format

        # Action value can either be 'BUY' or 'SELL'
        try:
            if (
                leg_specs_dict[unique_id]["Action"] != "BUY"
                and leg_specs_dict[unique_id]["Action"] != "SELL"
            ):
                raise Exception(
                    f"Combo Leg:{leg_no + 1}, Action must be either 'BUY' or 'SELL'."
                )
        except Exception as e:
            return (
                True,
                "Action must be either 'BUY' or 'SELL'.",
                f"Combo Leg:{leg_no + 1}, Action must be either 'BUY' or 'SELL'.",
                None,
            )

        # SecType value can either be 'STK' or 'FUT' or 'OPT' or 'FOP'
        try:
            if (
                leg_specs_dict[unique_id]["SecType"] != "STK"
                and leg_specs_dict[unique_id]["SecType"] != "FUT"
                and leg_specs_dict[unique_id]["SecType"] != "OPT"
                and leg_specs_dict[unique_id]["SecType"] != "FOP"
            ):
                raise Exception(
                    f"Combo Leg:{leg_no + 1}, SecType must be either 'STK' or 'OPT' or 'FUT' or 'FOP'."
                )
        except Exception as e:
            return (
                True,
                "SecType must be either 'STK' or 'OPT' or 'FUT' or 'FOP'",
                f"Combo Leg:{leg_no + 1}, SecType must be either 'STK' or 'OPT' or 'FUT' or 'FOP'.",
                None,
            )

        # #Lots/Quantity must be an integer value
        if not is_integer(leg_specs_dict[unique_id]["#Lots"]):
            return (
                True,
                "#Lots must be an integer.",
                f"Combo Leg:{leg_no + 1}, #Lots must be an integer.",
                None,
            )

        # Converting #Lots(leg quantity) to integer value
        leg_specs_dict[unique_id]["#Lots"] = int(
            float(leg_specs_dict[unique_id]["#Lots"])
        )

        # If we have conid it will be the primary identifier, to get contract and we will put all the details in the db(from contract details)
        if (leg_specs_dict[unique_id]["ConID"] == "") or (
            leg_specs_dict[unique_id]["ConID"] == "None"
        ):
            leg_specs_dict[unique_id]["ConID"] = None
        else:
            # Check if conid is integer value
            if not is_integer(leg_specs_dict[unique_id]["ConID"]):
                return (
                    True,
                    "ConID must be an integer.",
                    f"Combo Leg:{leg_no + 1}, ConID must be an integer.",
                    None,
                )

            # Now we have a con_id for leg so by pass error throwing
            is_con_id_available_for_leg = True
            leg_specs_dict[unique_id]["ConID"] = int(float(row["ConID"]))

        # If Values are blank set these to 'None'
        for column_name in leg_columns:

            if (column_name != "Unique ID") and (
                (leg_specs_dict[unique_id][column_name] == "")
                or (leg_specs_dict[unique_id][column_name] == "None")
            ):
                leg_specs_dict[unique_id][column_name] = None

        # If we have ConId we will not throw any error and will take every field from the contract that will be fetched using ContractDetails()
        if is_con_id_available_for_leg:
            pass
        else:
            # Since con_id was not provided check for the missing field and incomplete information

            # If SecType is not selected
            if leg_specs_dict[unique_id]["Symbol"] == None:
                return (
                    True,
                    "Missing Symbol",
                    f"Combo Leg:{leg_no + 1}, Symbol is missing.",
                    None,
                )

            # If SecType is not selected
            if leg_specs_dict[unique_id]["SecType"] == None:
                return (
                    True,
                    "Missing SecType",
                    f"Combo Leg:{leg_no + 1}, SecType is missing.",
                    None,
                )

            # If Exchange is not given
            if leg_specs_dict[unique_id]["Exchange"] == None:
                return (
                    True,
                    "Missing Exchange",
                    f"Combo Leg:{leg_no + 1}, Exchange is missing.",
                    None,
                )

            # If DTE is negative or non integer value
            if leg_specs_dict[unique_id]["DTE"] != None:
                try:

                    # validate vlaue is integer or not
                    if not is_integer(leg_specs_dict[unique_id]["DTE"]):
                        raise Exception(f"Combo Leg:{leg_no + 1}, DTE must be numeric.")

                    # assign value in dict
                    leg_specs_dict[unique_id]["DTE"] = int(
                        float(leg_specs_dict[unique_id]["DTE"])
                    )

                    # validate DTE value
                    if leg_specs_dict[unique_id]["DTE"] < 0:
                        raise Exception(f"Combo Leg:{leg_no + 1}, DTE must be numeric.")

                except Exception as e:
                    return (
                        True,
                        "DTE must be numeric.",
                        f"Combo Leg:{leg_no + 1}, DTE must be numeric.",
                        None,
                    )

            # If Delta is not in range 0 to 1. For Put Change delta to -delta
            if leg_specs_dict[unique_id]["Delta"] != None:
                try:
                    leg_specs_dict[unique_id]["Delta"] = float(
                        leg_specs_dict[unique_id]["Delta"]
                    )

                    if (leg_specs_dict[unique_id]["Delta"] < 0) or (
                        leg_specs_dict[unique_id]["Delta"] > 1
                    ):
                        raise Exception("Delta should be Between 0 to 1.")

                    if leg_specs_dict[unique_id]["Right"] == "PUT":
                        leg_specs_dict[unique_id]["Delta"] = (
                            -1 * leg_specs_dict[unique_id]["Delta"]
                        )

                except Exception as e:
                    return (
                        True,
                        "Delta must be numeric.",
                        f"Combo Leg:{leg_no + 1}, Delta should be Between 0 to 1.",
                        None,
                    )

            # If Strike is negative or numeric value.
            if leg_specs_dict[unique_id]["Strike"] != None:
                try:
                    leg_specs_dict[unique_id]["Strike"] = float(
                        leg_specs_dict[unique_id]["Strike"]
                    )
                    if leg_specs_dict[unique_id]["Strike"] < 0:
                        raise Exception("Negative Strike given.")

                    # Convert Strike back to Str for ibkr contract
                    # leg_specs_dict[unique_id]["Strike"] = float(leg_specs_dict[unique_id]["Strike"])
                except Exception as e:
                    return (
                        True,
                        f"Strike must be numeric.",
                        f"Combo Leg:{leg_no + 1}, Strike must be +ve numeric value.",
                        None,
                    )

            # If Expiry is not integer.
            if leg_specs_dict[unique_id]["Expiry"] != None:
                try:
                    leg_specs_dict[unique_id]["Expiry"] = str(
                        int(leg_specs_dict[unique_id]["Expiry"])
                    )
                except Exception as e:
                    return (
                        True,
                        "Invalid Expiry",
                        f"Combo Leg:{leg_no + 1}, Allowed Expiry format YYYYMMDD or YYYYMM.",
                        None,
                    )

            #### For (STK, FUT, OPT and FOP) --> Lot Size is required #####
            if leg_specs_dict[unique_id]["Lot Size"] == None:

                return (
                    True,
                    f"Missing Multiplier",
                    f"Combo Leg:{leg_no + 1}, Multiplier required for {leg_specs_dict[unique_id]['SecType']}.",
                    None,
                )

            else:

                try:
                    if not is_integer(leg_specs_dict[unique_id]["Lot Size"]):
                        raise Exception(
                            f"Combo Leg:{leg_no + 1}, Multiplier must be an integer value."
                        )
                    leg_specs_dict[unique_id]["Lot Size"] = str(
                        int(float(leg_specs_dict[unique_id]["Lot Size"]))
                    )
                except Exception as e:
                    return (
                        True,
                        "Invalid Multiplier",
                        f"Combo Leg:{leg_no + 1}, Multiplier must be an integer value.",
                        None,
                    )

                # If secType is STK and multiplier is not 1 Throw error
                if (leg_specs_dict[unique_id]["SecType"] == "STK") and (
                    leg_specs_dict[unique_id]["Lot Size"] != "1"
                ):
                    return (
                        True,
                        "Invalid Multiplier",
                        f"Combo Leg:{leg_no + 1}, Multiplier must be '1' for Stocks.",
                        None,
                    )

            #### For (FUT, OPT and FOP) --> DTE or Expiry is required #####
            if leg_specs_dict[unique_id]["SecType"] in ["FUT", "OPT", "FOP"]:

                # We must have DTE or Expiry
                if (
                    leg_specs_dict[unique_id]["DTE"] == None
                    and leg_specs_dict[unique_id]["Expiry"] == None
                ):
                    return (
                        True,
                        f"Expiry or DTE required for {leg_specs_dict[unique_id]['SecType']}",
                        f"Combo Leg:{leg_no + 1}, Expiry or DTE required for {leg_specs_dict[unique_id]['SecType']}.",
                        None,
                    )

            #### For (OPT and FOP) --> [Strike or Delta] and  [DTE (OPT) or Expiry (OPT)] is required #####
            if leg_specs_dict[unique_id]["SecType"] in ["OPT", "FOP"]:

                # Right is required
                if leg_specs_dict[unique_id]["Right"] == None or (
                    leg_specs_dict[unique_id]["Right"]
                    not in [
                        "C",
                        "P",
                        "CALL",
                        "PUT",
                    ]
                ):
                    return (
                        True,
                        f"Right required for {leg_specs_dict[unique_id]['SecType']}.",
                        f"Combo Leg:{leg_no + 1}, Right required for {leg_specs_dict[unique_id]['SecType']}.",
                        None,
                    )

                # Strike or Delta is required
                if (
                    leg_specs_dict[unique_id]["Strike"] == None
                    and leg_specs_dict[unique_id]["Delta"] == None
                ):
                    return (
                        True,
                        f"Strike or Delta required for {leg_specs_dict[unique_id]['SecType']}",
                        f"Combo Leg:{leg_no + 1}, Strike or Delta required for {leg_specs_dict[unique_id]['SecType']}.",
                        None,
                    )

            #### For FOP --> Trading Class is required #####
            if leg_specs_dict[unique_id]["SecType"] == "FOP":

                if leg_specs_dict[unique_id]["Trading Class"] == None:
                    return (
                        True,
                        f"Trading Class required for FOP",
                        f"Combo Leg:{leg_no + 1}, Trading Class required for FOP.",
                        None,
                    )

        # Make a deep, as we later append it to list, the content should not change in next iteration
        leg_dict = copy.deepcopy(leg_specs_dict[unique_id])

        # Append leg dict to list
        legs_dict_list.append(leg_dict)

    #### End: This Part Deals with cleaning data, and checking basic info of leg is in correct format #####

    # Print to console
    if variables.flag_debug_mode:
        for leg_no, leg_dict in enumerate(legs_dict_list):
            print(f"Leg No : {leg_no + 1}", leg_dict)

    ###### Start : This Part Deals with resolving STK legs / Complete info legs.         #####
    ######         So that when we resolve we are sure user provided legs are correct.   #####

    # Contains leg_objs
    leg_obj_list = []

    # legs which need to resolved, (Non-STK, missing info)
    legs_needs_to_be_solved = []

    # Processing individual leg_dict, to get conid.
    for leg_no, leg_dict in enumerate(legs_dict_list):

        # Init Variables
        action = leg_dict["Action"]
        symbol = leg_dict["Symbol"]
        sec_type = leg_dict["SecType"]
        exchange = leg_dict["Exchange"]
        currency = leg_dict["Currency"]
        quantity = leg_dict["#Lots"]
        expiry_date = leg_dict["Expiry"]
        strike_price = leg_dict["Strike"]
        right = leg_dict["Right"]
        multiplier = leg_dict["Lot Size"]
        con_id = leg_dict["ConID"]
        primary_exchange = leg_dict["Primary Exchange"]
        trading_class = leg_dict["Trading Class"]
        dte = leg_dict["DTE"]
        delta = leg_dict["Delta"]

        # by design we want to make sure if for user provided(strike and expiry) we are not able to get any contract/conID.
        # he should know that, before we search for legs expiry an strike.(basically resolve legs after making sure user provided legs are correct.)

        # we need to resolve this FUT which is without expiry_date and con_id
        if (sec_type == "FUT") and (expiry_date == None) and (con_id == None):

            # Adding leg which needs to be resolved
            legs_needs_to_be_solved.append(
                (
                    leg_no,
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
                        dte,
                        delta,
                    ),
                )
            )
            continue

        # we need to resolve this OPT/FOP which is without expiry_date, strike_price and con_id
        elif (
            (sec_type in ["OPT", "FOP"])
            and (con_id == None)
            and (expiry_date == None or strike_price == None)
        ):

            # Adding leg which needs to be resolved
            legs_needs_to_be_solved.append(
                (
                    leg_no,
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
                        dte,
                        delta,
                    ),
                )
            )
            continue

        # Resolve these legs, STK/Full info legs
        else:

            # Create contract for adding to leg_obj,
            contract = get_contract(
                symbol,
                sec_type,
                exchange,
                currency,
                expiry_date,
                strike_price,
                right,
                multiplier,
                con_id,
                primary_exchange,
                trading_class,
            )

            # if leg have con_id or complete info resolve them right_away(for STK always do it)
            # Contracts from DB or the contracts with conid
            contract_details = get_contract_details(contract)

            # Throw error pop can not get contract id
            if contract_details == None:

                # Give error not able to find Contract ID
                return (
                    True,
                    "Unable to fetch Contract ID.",
                    f"Please check ComboLeg:{leg_no + 1} or insert more fields.",
                    None,
                )

            else:

                # Contract
                contract = contract_details.contract

                # Init Variables : True values for resolved legs.
                symbol = contract.symbol
                sec_type = contract.secType
                exchange = contract.exchange
                currency = contract.currency

                # Set Expiry Value
                expiry_date = (
                    None
                    if contract.lastTradeDateOrContractMonth == ""
                    else contract.lastTradeDateOrContractMonth
                )

                strike_price = None if float(contract.strike) == 0 else contract.strike
                right = None if contract.right == "" else contract.right
                multiplier = 1 if contract.multiplier == "" else contract.multiplier
                con_id = int(contract.conId)
                primary_exchange = contract.primaryExchange
                trading_class = contract.tradingClass

                # All supported orders for the contract
                all_supported_order_types = contract_details.orderTypes

                # Map If conid supports the IB Algo Order
                if all_supported_order_types.find(",ALGO,") != -1:
                    variables.map_con_id_to_flag_supports_ib_algo_order[con_id] = True
                else:
                    variables.map_con_id_to_flag_supports_ib_algo_order[con_id] = False

            # Create leg object
            leg_obj = Leg(
                action,
                symbol,
                sec_type,
                dte,
                delta,
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
                contract,
            )

            # Add Leg Object to list
            leg_obj_list.append(leg_obj)

    ###### End : This Part Deals with resolving STK legs / Complete info legs.           #####
    ######         So that when we resolve we are sure user provided legs are correct.   #####

    ###### Start : This Part Deals with resolving complex legs. i.e OPT, FUT, FOP legs.   #####
    ######         If we dont have conId or full info for legs, find relevant info        #####
    ######         and resolve the legs.                                                  #####

    if len(legs_needs_to_be_solved) > 0:
        # Process the results here
        start = time.perf_counter()

        # Call the async function to start the event loop
        contracts_details = asyncio.run(run_tasks(legs_needs_to_be_solved))

        # get end time
        end = time.perf_counter()

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Time took to resolve {len(legs_needs_to_be_solved)} legs :{end-start}"
            )
            print(f"Contract Details : {contracts_details}")

        for leg_info, contract_details in zip(
            legs_needs_to_be_solved, contracts_details
        ):

            # unpack user prodived info for leg object,
            leg_no, (
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
                dte,
                delta,
            ) = leg_info

            # Throw error pop can not get contract id
            if contract_details == None:
                return (
                    True,
                    "Unable to fetch ConID.",
                    f"Please check ComboLeg:{leg_no + 1} or insert more fields.",
                    None,
                )

            # Contract from contract Details
            contract = contract_details.contract

            # Init Variables : True values for resolved legs.
            symbol = contract.symbol
            sec_type = contract.secType
            # KARAN - 20231027 CRITICAL
            # KARAN ADDED THS PART - if the SYMBOL is SPX and SecType is OPT we want exchange as SMART
            if (symbol in ["SPX", "spx", "NDX", "ndx"]) and sec_type == "OPT":
                contract.exchange = "SMART"

            exchange = contract.exchange
            currency = contract.currency

            # Set Expiry Value
            expiry_date = (
                None
                if contract.lastTradeDateOrContractMonth == ""
                else contract.lastTradeDateOrContractMonth
            )

            # Init
            strike_price = None if float(contract.strike) == 0 else contract.strike
            right = None if contract.right == "" else contract.right
            multiplier = 1 if contract.multiplier == "" else contract.multiplier
            con_id = int(contract.conId)
            primary_exchange = contract.primaryExchange
            trading_class = contract.tradingClass

            # All supported orders for the contract
            all_supported_order_types = contract_details.orderTypes

            # Map If conid supports the IB Algo Order
            if all_supported_order_types.find(",ALGO,") != -1:
                variables.map_con_id_to_flag_supports_ib_algo_order[con_id] = True
            else:
                variables.map_con_id_to_flag_supports_ib_algo_order[con_id] = False

            # Create leg object
            leg_obj = Leg(
                action,
                symbol,
                sec_type,
                dte,
                delta,
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
                contract,
            )

            # Add Leg Object to list
            leg_obj_list.append(leg_obj)

    ###### End : This Part Deals with resolving complex legs. i.e OPT, FUT, FOP legs.     #####
    ######         If we dont have conId or full info for legs, find relevant info        #####
    ######         and resolve the legs.                                                  #####

    # Print to console
    if variables.flag_debug_mode:
        for leg_obj_print in leg_obj_list:
            print(leg_obj_print)

    # If CAS
    if input_from_cas_tab == True:

        # Create combination object
        combination_obj = Combination(unique_id, leg_obj_list)

        # # Checking Combo type, and map con_id to contract
        for leg_obj_ in combination_obj.buy_legs + combination_obj.sell_legs:

            if leg_obj_.sec_type in ["OPT", "FOP"]:
                only_stk_fut = False

            # Mapping con_id to contract
            variables.map_con_id_to_contract[leg_obj_.con_id] = leg_obj_.contract

        # if from db, only return the combination
        if input_from_db:

            return combination_obj
        else:

            return False, "no error", "no error", combination_obj

    # Init Variables for Treeview - Combination table
    num_stk, num_fut, num_opt, num_fop = 0, 0, 0, 0

    # Counting sec_type of legs
    for leg_obj in leg_obj_list:

        sec_type = leg_obj.sec_type

        # Keeping count, of sec_type to insert in active combo GUI table
        if sec_type == "STK":
            num_stk += 1
        elif sec_type == "OPT":
            num_opt += 1
        elif sec_type == "FUT":
            num_fut += 1
        elif sec_type == "FOP":
            num_fop += 1

    if variables.flag_debug_mode:
        print(f"Unique ID = {unique_id}, Creating combination object")

    # Create combination object
    combination_obj = Combination(unique_id, leg_obj_list)

    # Add combo_obj to dict so it is available via class variables
    variables.unique_id_to_combo_obj[unique_id] = combination_obj

    # Informative ticker string for tables, Combo description
    tickers_string = make_informative_combo_string(combination_obj)

    # Buy and Sell legs for the active combo table in GUI
    num_buy_legs = len(combination_obj.buy_legs)
    num_sell_legs = len(combination_obj.sell_legs)

    # Unique ID, No. of legs, Tickers_str,  Buys, Sells, STK, FUT, OPT, FOP
    combo_table_data = (
        unique_id,
        num_buy_legs + num_sell_legs,
        tickers_string,
        num_buy_legs,
        num_sell_legs,
        num_stk,
        num_fut,
        num_opt,
        num_fop,
    )

    # Creating dataframe for row data
    combo_row_df = pd.DataFrame(
        [combo_table_data], columns=variables.combo_table_columns
    )

    # Get all the combination orders from db
    all_combination_order = get_all_combinaiton_orders_from_db()

    # check if df is empty
    if all_combination_order.empty:

        # Init
        all_account_ids_in_order_book = []

    else:

        # all account ids in order book
        all_account_ids_in_order_book = all_combination_order["Account ID"].to_list()

    # make list of account ids in system
    all_account_ids_in_system = sorted(
        list(set(variables.current_session_accounts + all_account_ids_in_order_book))
    )

    # Merge row with combo details dataframe
    variables.combo_table_df = pd.concat([variables.combo_table_df, combo_row_df])

    if variables.unique_id_list_of_selected_watchlist == "ALL":
        # Add values to combo table
        variables.screen.add_high_level_combo_details_to_combo_creator_tab(
            [combo_table_data]
        )

    # iterate accounts in current session
    for account_id in all_account_ids_in_system:

        # Row Value in combination position tab in GUI (unique_id. #Legs, Tickers, Positions)
        value_of_row_in_positions_table = (
            unique_id,
            num_buy_legs + num_sell_legs,
            tickers_string,
            0,
            account_id,
            f"{unique_id}_{account_id}",
        )

        # Creating dataframe for positions table row data
        positions_row_dataframe = pd.DataFrame(
            [value_of_row_in_positions_table], columns=variables.positions_table_columns
        )

        # Merge row with positions details dataframe
        variables.positions_table_dataframe = pd.concat(
            [variables.positions_table_dataframe, positions_row_dataframe]
        )

        # check watchlist value
        if variables.unique_id_list_of_selected_watchlist == "ALL":

            # Add row to the Positions table
            variables.screen.screen_position_obj.insert_positions_in_positions_table(
                value_of_row_in_positions_table
            )

    try:
        # Values to Insert in CAS Table, Default to "N/A" for indicators
        value_of_row_in_cas_table = [
            unique_id,
            tickers_string,
        ] + ["N/A" for _ in range(46)]

        # Only insert the newly created combonation in the GUI if watchlist selected is default WL. (ALL)
        if variables.unique_id_list_of_selected_watchlist == "ALL":
            # Add row to the CAS Table
            variables.screen.screen_cas_obj.insert_cas_row_in_cas_table(
                value_of_row_in_cas_table
            )

    except Exception as e:

        # Print to Console
        print(f"Error occured while inserting cas table row, is {e}")

    # what data do we need for the combo 1Day or 1H for CAS(N-Day) Longterm Values
    only_stk_fut = False

    # # Checking Combo type, and map con_id to contract
    for leg_obj_ in combination_obj.buy_legs + combination_obj.sell_legs:

        if leg_obj_.sec_type in ["OPT", "FOP"]:
            only_stk_fut = False

        # Mapping con_id to contract
        variables.map_con_id_to_contract[leg_obj_.con_id] = leg_obj_.contract

    # Update the values of 'cas_map_con_id_to_action_type_and_combo_type' used while getting HighLowCAS prices
    for leg_obj_ in combination_obj.buy_legs + combination_obj.sell_legs:
        # Coind for leg
        conid = leg_obj_.con_id
        action = leg_obj_.action

        if conid not in variables.cas_map_con_id_to_action_type_and_combo_type:
            variables.cas_map_con_id_to_action_type_and_combo_type[conid] = {
                "BUY": {"1H": 0, "1D": 0},
                "SELL": {"1H": 0, "1D": 0},
            }

        # Count which data is required how many times for CAS
        if only_stk_fut:
            variables.cas_map_con_id_to_action_type_and_combo_type[conid][action][
                "1D"
            ] += 1
        else:
            variables.cas_map_con_id_to_action_type_and_combo_type[conid][action][
                "1H"
            ] += 1

    # Insert row with Unique ID in cache table
    if input_from_db == False:
        # insert new for newly created unique id
        insert_combination_unique_id_to_cache_table_db(unique_id)

    # If this input is from the Database then return the combination_obj, else from return values to screen_gui
    if input_from_db == True:
        return combination_obj
    else:
        return False, "no error", "no error", combination_obj


# Subscribes the market data for combination, all legs if not already subscribed, and insert the (nones) in market watch for first time
def subscribe_mktdata_combo_obj(combination_obj):

    # Print to console
    if variables.flag_debug_mode:
        print(f"Subscribing the market data for {combination_obj}")

    # Unique Id
    unique_id = combination_obj.unique_id

    # All legs of combination
    buy_legs, sell_legs = combination_obj.buy_legs, combination_obj.sell_legs
    all_leg_objs = buy_legs + sell_legs

    # When Snapshot is False we will get market data on ongoing basis
    snapshot = False

    # Subscribing Bid-Ask for all the legs
    for leg_obj in all_leg_objs:

        # Contract to subscribe the data, ConId to make sure we are subscribing only once.
        contract = leg_obj.contract
        con_id = contract.conId

        # Subscribing if not already subscribed
        if con_id in variables.conid_mktdata_subscription_dict:
            variables.conid_mktdata_subscription_dict[con_id] += 1
        else:
            # Set conid subscription to 1
            variables.conid_mktdata_subscription_dict[con_id] = 1

            # Subscribe mkt data for contract, snapshot = False
            bid, ask = get_market_data_for_contract(unique_id, contract, snapshot)

    # Print to console
    if variables.flag_debug_mode:
        print(f"Done Subscribing the market data for {combination_obj}")

    # Informative ticker string for market watch table, Combo description
    tickers_string = make_informative_combo_string(combination_obj)

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Inserting Prices(nones) in market watch tab for first time for {combination_obj}"
        )

    # Insert Prices in Market Watch table, (Unique ID, No. Legs., Tickers, Buy Price, Sell Prices, Spread,)
    values = (unique_id, len(all_leg_objs), tickers_string, "None", "None", "None")

    # We want to concat these values in a gloabl df here for watchlist.
    # Creating dataframe for row data
    market_watchlist_row_df = pd.DataFrame(
        [values], columns=variables.market_watch_table_columns
    )

    # Concat row with market_watch_table_dataframe
    variables.market_watch_table_dataframe = pd.concat(
        [variables.market_watch_table_dataframe, market_watchlist_row_df]
    )

    # Check value of watchlist is ALL
    if variables.unique_id_list_of_selected_watchlist == "ALL":
        variables.screen.insert_prices_market_watch(values)


# Deletes combination, unsubscribe mkt data, moves data from active DB to Archive DB, (also removes all the Orders from the OrderBook -- order_time is iid in table)
def delete_combination(unique_id):

    # Print to console
    if variables.flag_debug_mode:
        print(f"Unique ID={unique_id}, Deleting combination")

    # Init Active ComboObj
    combination_obj = variables.unique_id_to_combo_obj[unique_id]

    # Legs in ComboObj
    buy_legs = combination_obj.buy_legs
    sell_legs = combination_obj.sell_legs

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Unique ID={unique_id}, Deleting combination, buy legs : {buy_legs}, sell Legs: {sell_legs}"
        )

    # All Legs in ComboObj
    all_leg_objs = buy_legs + sell_legs

    # what data do we need for the combo 1Day or 1H for CAS(N-Day) Longterm Values
    only_stk_fut = False

    # Checking Combo type, and map con_id to contract
    for leg_obj_ in all_leg_objs:

        if leg_obj_.sec_type in ["OPT", "FOP"]:
            only_stk_fut = False

    # Processing all legs and canceling sub if required
    for leg_obj in all_leg_objs:

        # ConId of leg
        con_id = leg_obj.contract.conId

        # Action of leg
        action = leg_obj.action

        # Decrease the conid_mktdata_sub
        variables.conid_mktdata_subscription_dict[con_id] -= 1
        con_id_times_subs = variables.conid_mktdata_subscription_dict[con_id]

        # Decrease the Count which data is required how many times for CAS
        if only_stk_fut:

            variables.cas_map_con_id_to_action_type_and_combo_type[con_id][action][
                "1D"
            ] -= 1

        else:

            variables.cas_map_con_id_to_action_type_and_combo_type[con_id][action][
                "1H"
            ] -= 1

        # Check and Cancel the subscription
        if con_id_times_subs <= 0:
            req_id = variables.con_id_to_req_id_dict[con_id]
            variables.app.cancelMktData(req_id)

            # Print to console
            if variables.flag_debug_mode:
                print(
                    "Cancelling Marktet data Request reqId: {req_id} for Leg: {leg_obj}"
                )

    # Delete the combo from the class variable
    del variables.unique_id_to_combo_obj[unique_id]

    # Delete CAS COMBO if exists
    if unique_id in variables.cas_unique_id_to_combo_obj:
        # Init CAS ComboObj
        combination_obj = variables.cas_unique_id_to_combo_obj[unique_id]

        # Legs in ComboObj
        buy_legs = combination_obj.buy_legs
        sell_legs = combination_obj.sell_legs

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID={unique_id}, Deleting CAS combination, buy legs : {buy_legs}, sell Legs: {sell_legs}"
            )

        # All Legs in ComboObj
        all_leg_objs = buy_legs + sell_legs

        # what data do we need for the combo 1Day or 1H for CAS(N-Day) Longterm Values
        only_stk_fut = False

        # Checking Combo type, and map con_id to contract
        for leg_obj_ in all_leg_objs:

            if leg_obj_.sec_type in ["OPT", "FOP"]:
                only_stk_fut = False

        # Processing all legs and canceling sub if required
        for leg_obj in all_leg_objs:

            # ConId of leg
            con_id = leg_obj.contract.conId

            # Action of leg
            action = leg_obj.action

            # Decrease the Count which data is required how many times for CAS
            if only_stk_fut:

                variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type[
                    con_id
                ][action]["1D"] -= 1
            else:

                variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type[
                    con_id
                ][action]["1H"] -= 1

        # Delete the CAS combo from the class variable
        del variables.cas_unique_id_to_combo_obj[unique_id]

    # Getting list of order times from DB. Used to remove order from order book.
    order_time_list = get_order_times_for_combination(unique_id)
    # print(order_time_list)
    # Remove if orders are present in order book
    if len(order_time_list):

        variables.screen.remove_row_from_order_book(order_time_list)

    # Move all the data from active table to archive database
    move_active_data_to_archive_db(unique_id)

    # Delete the combo from the dataframe ( MIGHT MOVE TO DELTE COMBO METHOD
    variables.combo_table_df = variables.combo_table_df[
        variables.combo_table_df["Unique ID"] != unique_id
    ]
    variables.market_watch_table_dataframe = variables.market_watch_table_dataframe[
        variables.market_watch_table_dataframe["Unique ID"] != unique_id
    ]
    variables.positions_table_dataframe = variables.positions_table_dataframe[
        variables.positions_table_dataframe["Unique ID"] != unique_id
    ]

    variables.orders_book_table_dataframe = variables.orders_book_table_dataframe[
        variables.orders_book_table_dataframe["Unique ID"] != unique_id
    ]

    # variables.cas_condition_table_dataframe   = variables.cas_condition_table_dataframe[variables.cas_condition_table_dataframe['Unique ID'] != unique_id]
    variables.cas_condition_table_dataframe = variables.cas_condition_table_dataframe[
        (variables.cas_condition_table_dataframe["Unique ID"] != unique_id)
        | (
            (variables.cas_condition_table_dataframe["Unique ID"] == unique_id)
            & (variables.cas_condition_table_dataframe["Status"] != "Pending")
        )
    ]


# Gets all the combination order from DB, then Inserts combo_order_status inside order_book_tab - screen gui
def insert_combo_order_status_in_order_book(order_book_last_cleaned_time=None):

    # Get all the orders from the DB.
    combo_order_status_dataframe = get_all_combinaiton_orders_from_db(
        order_book_last_cleaned_time
    )

    # Insert each order from DB to Screen GUI
    for _, row in combo_order_status_dataframe.iterrows():

        # Init
        unique_id = row["Unique ID"]
        action = row["Action"]
        combo_quantity = row["#Lots"]
        order_type = row["Order Type"]
        order_time = row["Order Time"]
        last_update_time = row["Last Update Time"]
        tickers = row["Tickers"]
        entry_price = row["Entry Price"]
        limit_price = row["Limit Price"].strip()
        trigger_price = row["Trigger Price"].strip()
        reference_price = row["Reference Price"]
        trail_value = row["Trail Value"].strip()
        status = row["Status"].strip()
        ladder_id = row["Ladder ID"].strip()
        sequence_id = row["Sequence ID"].strip()
        atr_multiple = row["ATR Multiple"].strip()
        atr = row["ATR"].strip()
        reason_for_failed = row["Reason For Failed"].strip()
        account_id = row["Account ID"].strip()
        bypass_rm_check = row["Bypass RM Check"].strip()
        execution_engine = str(row["Execution Engine"].strip())

        limit_iv = row["Limit IV"].strip()
        trigger_iv = row["Trigger IV"].strip()
        actual_entry_price = row['Actual Entry Price'].strip()

        # Formatting Values
        if entry_price != "None":
            entry_price = f"{float(entry_price):,.2f}"
        if limit_price not in ["None", ""]:
            limit_price = f"{float(limit_price):,.2f}"
        if trigger_price not in ["None", ""]:
            trigger_price = f"{float(trigger_price):,.2f}"
        if reference_price not in ["None", ""]:
            reference_price = f"{float(reference_price):,.2f}"
        if trail_value not in ["None", ""]:
            trail_value = f"{float(trail_value):,.2f}"
        if atr_multiple not in ["None", ""]:
            atr_multiple = f"{float(atr_multiple):,.2f}"
        if atr not in ["None", "", "N/A"]:
            atr = f"{float(atr):,.2f}"

        # group values in tuple
        order_book_row_values = (
            unique_id,
            account_id,
            tickers,
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
            execution_engine,
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

        # All the unique ids in the currently selected watchlist
        local_unique_id_list_of_selected_watchlist = copy.deepcopy(
            variables.unique_id_list_of_selected_watchlist
        )

        # If watchlist have this unique_id we want to insert it in table else not
        if (local_unique_id_list_of_selected_watchlist == "ALL") or (
            int(unique_id)
            in [int(_) for _ in local_unique_id_list_of_selected_watchlist.split(",")]
        ):

            # Insert the value value inside of combo_order_status_order_book
            variables.screen.insert_combo_order_status_order_book(
                (
                    unique_id,
                    account_id,
                    tickers,
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
                    execution_engine,
                    limit_iv,
                    trigger_iv,
                    actual_entry_price
                )
            )

        # Update order book
        variables.flag_orders_book_table_watchlist_changed = True
        variables.screen.update_orders_book_table_watchlist_changed()


# Method to update execution orders
def update_execution_engine_orders():

    # Print to console
    if variables.flag_debug_mode:
        print("Checking and Trying to update execution engine orders.")

    try:
        # Print to console
        if variables.flag_debug_mode:
            print("Getting all the combination order where status is 'Sent'.")

        # get all the combo orders where order status is sent.
        all_combo_orders_status_sent = get_sent_combo_orders()

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Fetched combination order where status is 'Sent' are: {all_combo_orders_status_sent}."
            )

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Getting all the (Individual Leg Orders) order ids where status is not 'Filled'."
            )

        # Getting all the order_ids from db where status is not Filled. (individaul leg orders)
        all_order_ids = get_all_order_ids_status_not_equal_filled()

        # Creating order IDs set to match order
        all_order_ids_set = set([int(order_id) for order_id in all_order_ids])

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Fetched all the (Individual Leg Orders) order ids where status is not 'Filled': {all_order_ids_set}"
            )

        # Check if Sent order is filled.
        for _, row in all_combo_orders_status_sent.iterrows():

            # Strip all the values
            order_ids_of_pending_combo = row["Order IDs"].strip()

            # If currently the order id is set to pass in combo_order_status continue
            if order_ids_of_pending_combo == "pass":
                continue
            else:
                pass
                # Since now we have order ids of combos order check if status is filled or not

            # Init Variables for updating
            unique_id = row["Unique ID"]

            execution_engine = row["Execution Engine"]
            status = row["Status"]
            combo_quantity = row["#Lots"]
            action = row["Action"]
            original_order_time = row["Order Time"]
            order_type_of_original_order = row["Order Type"]
            account_id = row["Account ID"]
            ib_algo_mkt = False
            ladder_id = row["Ladder ID"]

            # Get combo obj
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )

            # Get Combo object
            combo_obj = local_unique_id_to_combo_obj[int(float(unique_id))]

            # Buy legs and Sell legs
            buy_legs = combo_obj.buy_legs
            sell_legs = combo_obj.sell_legs
            all_legs = buy_legs + sell_legs

            # If order ids are present for every leg
            if (
                len(order_ids_of_pending_combo.split(",")) == 1
                and len(all_legs) > 1
                and execution_engine == "True"
            ):

                # If any order id is in not filled state, do not update status to filled.
                for leg_order_id in order_ids_of_pending_combo.split(","):

                    # Get stripped value
                    leg_order_id = leg_order_id.strip()

                    # check order ids
                    if int(leg_order_id) in all_order_ids_set:
                        break

                    else:

                        # get quantity
                        symbol_quantity = get_ticker_order_status_db(leg_order_id)

                        # Init flag
                        flag_matched = False

                        # Sending order for each leg one by one
                        for leg_obj in all_legs:

                            # Contract
                            contract = leg_obj.contract

                            # Order Quantity, Leg Quantity * Combo Quantity
                            order_qty = int(leg_obj.quantity) * int(combo_quantity)

                            # ticker string
                            ticker_str = (
                                leg_obj.symbol
                                +","
                                +str(order_qty)
                                +","
                                +str(contract.conId)
                            )

                            # skip leg with highest spread
                            if not flag_matched and ticker_str == symbol_quantity:

                                # Toggle flag
                                flag_matched = True

                                continue

                            # If action(user-input) is buy pass, else change buy to sell & sell to buy
                            order_action = leg_obj.action

                            # Change order action according to user input
                            if action == "BUY":
                                pass
                            elif action == "SELL":
                                # change leg_action (selling)
                                order_action = (
                                    "BUY" if order_action == "SELL" else "SELL"
                                )

                            try:

                                # Getting the Order Type if order is for the sequence of a ladder.
                                if ladder_id not in [None, "None"]:
                                    order_type_scale_trade = (
                                        get_ladder_or_sequence_column_value_from_db(
                                            ladder_id=ladder_id,
                                            column_name_as_in_db="Order Type",
                                        )
                                    )

                            except Exception as e:

                                # Print to console
                                if variables.flag_debug_mode:
                                    print(
                                        f"For Ladder ID: {ladder_id}, Query for getting ladder order type failed"
                                    )

                            # if ladder id is present
                            if ladder_id != "None":

                                # Temp, Descriptions
                                entry_exit_order = "Limit"
                                order_type_des = str(order_action)

                                # if order is ib algo market
                                if order_type_scale_trade == "IB Algo Market":

                                    ib_algo_mkt = True

                            else:

                                # if order is ib algo market
                                if order_type_of_original_order == "IB Algo Market":

                                    ib_algo_mkt = True

                                # Temp, Descriptions
                                entry_exit_order = "Market"
                                order_type_des = str(order_action)

                            try:
                                # send order
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

                                # update/put order ID's in the combination table.
                                insert_order_ids_in_combo_status(
                                    unique_id, original_order_time
                                )

                                # Sleep
                                time.sleep(variables.sleep_time_db)

                            except Exception as e:

                                # Print to console
                                if variables.flag_debug_mode:

                                    print(
                                        f"Exception inside sending order afetr limit order of execution engine: Exp {e}"
                                    )

            else:
                pass

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Exception inside updating execution engine orders, Exp: {e}")


# Updates combination order status inside the DB as well as order book - screen_gui (only updates the status from sent to filled)
# Explaination: When MKT orde is placed by user The status is set to 'Sent', When Lim, SL, TlSL, is placed status is set to 'pending'
#               once the Lim, SL, tlSL is triggered status is updated in db as well as in order book to 'Sent', so this function only updates from 'sent' to 'filled'
def update_combination_status_in_db_and_order_book(flag_update_scale_trade_order=False):

    # Print to console
    if variables.flag_debug_mode:
        print(
            "Checking and Trying to update combination status from sent to filled in DB and Order Book."
        )

    try:
        # Print to console
        if variables.flag_debug_mode:
            print("Getting all the combination order where status is 'Sent'.")

        # get all the combo orders where order status is sent.
        all_combo_orders_status_sent = get_sent_combo_orders()

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Fetched combination order where status is 'Sent' are: {all_combo_orders_status_sent}."
            )

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Getting all the (Individual Leg Orders) order ids where status is not 'Filled'."
            )

        # Getting all the order_ids from db where status is not Filled. (individaul leg orders)
        all_order_ids = get_all_order_ids_status_not_equal_filled()

        # Creating order IDs set to match order
        all_order_ids_set = set([int(order_id) for order_id in all_order_ids])

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Fetched all the (Individual Leg Orders) order ids where status is not 'Filled': {all_order_ids_set}"
            )

        # Check if Sent order is filled.
        for _, row in all_combo_orders_status_sent.iterrows():

            # Strip all the values
            order_ids_of_pending_combo = row["Order IDs"].strip()

            # If currently the order id is set to pass in combo_order_status continue
            if order_ids_of_pending_combo == "pass":
                continue
            else:
                pass
                # Since now we have order ids of combos order check if status is filled or not

            # Init Variables for updating
            unique_id = row["Unique ID"]

            # flag execution engine
            flag_execution_engine = row["Execution Engine"]

            # Get combo obj
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )

            # Get combo obj
            combo_obj = local_unique_id_to_combo_obj[int(float(unique_id))]

            # Buy legs and Sell legs
            buy_legs = combo_obj.buy_legs
            sell_legs = combo_obj.sell_legs
            all_legs = buy_legs + sell_legs

            # If order ids are present for every leg
            if (
                len(order_ids_of_pending_combo.split(",")) < len(all_legs)
                and flag_execution_engine == "True"
            ):

                continue
            else:

                pass

            # If any order id is in not filled state, do not update status to filled.
            for leg_order_id in order_ids_of_pending_combo.split(","):

                leg_order_id = leg_order_id.strip()

                if int(leg_order_id) in all_order_ids_set:

                    break
            else:

                # Init Variables for updating
                unique_id = row["Unique ID"]
                original_order_time = row["Order Time"]
                order_quantity = row["#Lots"].strip()
                combo_order_action = row["Action"].strip()
                entry_price = row["Entry Price"]
                reference_price = row["Reference Price"]
                order_ids = row["Order IDs"]
                status = "Filled"
                last_update_time = datetime.datetime.now(variables.target_timezone_obj)

                # Get order ids list
                order_ids_list = order_ids.split(",")

                # Get avg fill price for order ids
                avg_fill_prices = get_avg_fill_prices_for_order_ids_db(
                    original_order_time, "Avg Fill Price"
                )

                # Get order actions for order ids
                order_action = get_avg_fill_prices_for_order_ids_db(
                    original_order_time, "Order Action"
                )

                # Init
                actual_entry_price = 0

                # print([avg_fill_prices, order_action, all_legs])

                # Iterate fill prices, action and leg objects
                for price, action, leg_obj in zip(avg_fill_prices, order_action, all_legs):

                    # If action is buy
                    if action in ['BUY']:

                        # calculate actual entry price
                        actual_entry_price += float(price) * leg_obj.quantity * leg_obj.multiplier

                    else:

                        # Calculate entry price
                        actual_entry_price += float(price) * -1 * leg_obj.quantity * leg_obj.multiplier

                # if order action is SELL
                if combo_order_action in ['SELL']:

                    # make sign of actual entry price opposite
                    actual_entry_price *= -1

                # round off value
                actual_entry_price = round(actual_entry_price, 2)

                # Get combo obj
                """try:
                    # Get combo obj
                    local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)
                    combo_obj = local_unique_id_to_combo_obj[int(float(unique_id))]
                    
                    # Buy legs and Sell legs
                    buy_legs = combo_obj.buy_legs
                    sell_legs = combo_obj.sell_legs
                    all_legs = buy_legs + sell_legs
                    
                    # Init excution price
                    execution_price = 0
                    
                    # Iterate avg fill price, leg and action for order id
                    for avg_fill_price, leg_obj, action in zip(avg_fill_prices, all_legs, order_action):
                        
                        # If action is BUY
                        if action == 'BUY':
                            
                            # Calculate execuation price
                            execution_price += float(avg_fill_price) * int(float(order_quantity)) * leg_obj.quantity * leg_obj.multiplier * 1 * (1 if combo_order_action == 'BUY' else -1)
                            
                        # If action is SELL
                        else:
                            
                            # Calculate execuation price
                            execution_price += float(avg_fill_price) * int(float(order_quantity)) * leg_obj.quantity * leg_obj.multiplier * (-1) * (1 if combo_order_action == 'BUY' else -1)
                            
                except Exception as e:
                    
                    execution_price = 'None'
                    
                    # Print to console
                    if variables.flag_debug_mode:
                        print(f"Error inside 'update_combination_status_in_db_and_order_book', is {e}")"""

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Updating combination order status in Database for {unique_id=} {original_order_time=} {entry_price=}"
                    )

                # Update combination_order_status_in_db
                update_combination_order_status_in_db(
                    unique_id,
                    original_order_time,
                    last_update_time,
                    entry_price,
                    status,
                    actual_entry_price=actual_entry_price,
                )

                # Check if flag for updating scale trade orers is true
                if flag_update_scale_trade_order:

                    return

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Updating combination order status in Order Book for {unique_id=} {original_order_time=} {entry_price=}"
                    )

                # Update Combination order status in order_book_table
                variables.screen.update_combo_order_status_in_order_book(
                    original_order_time,
                    last_update_time,
                    entry_price,
                    reference_price,
                    status,
                    actual_entry_price=actual_entry_price,
                )

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Exception in update_combination_status_in_db_and_order_book {e}")

##################################################
# Version 1
##################################################


# Method to map unique id to combo legs
def get_unique_id_combolegs_dict(dataframe_containing_legs):
    # Creating a dict
    unique_id_to_combolegs_dict = {}
    for _, row in dataframe_containing_legs.iterrows():
        # Init Variables
        unique_id = int(row["Unique ID"])
        action = row["Action"]
        sec_type = row["SecType"]
        symbol = row["Symbol"]
        dte = row["DTE"]
        delta = row["Delta"]
        exchange = row["Exchange"]
        currency = row["Currency"]
        quantity = row["#Lots"]
        strike = row["Strike"]
        expiry = row["Expiry"]
        lot_size = int(row["Lot Size"])
        right = row["Right"]
        trading_class = row["Trading Class"]
        con_id = row["ConID"]
        primary_exchange = row["Primary Exchange"]

        # check if unique ids is present in dict
        if unique_id in unique_id_to_combolegs_dict:

            # append values
            unique_id_to_combolegs_dict[unique_id].append(
                (
                    unique_id,
                    action,
                    sec_type,
                    symbol,
                    dte,
                    delta,
                    right,
                    quantity,
                    lot_size,
                    exchange,
                    trading_class,
                    currency,
                    con_id,
                    primary_exchange,
                    strike,
                    expiry,
                )
            )
        else:

            # Init
            unique_id_to_combolegs_dict[unique_id] = []

            # Append values
            unique_id_to_combolegs_dict[unique_id].append(
                (
                    unique_id,
                    action,
                    sec_type,
                    symbol,
                    dte,
                    delta,
                    right,
                    quantity,
                    lot_size,
                    exchange,
                    trading_class,
                    currency,
                    con_id,
                    primary_exchange,
                    strike,
                    expiry,
                )
            )

    return unique_id_to_combolegs_dict


# Method to ad cas condition in cas condition table after app starts
def insert_cas_conditions_in_cas_conditions_table_from_db(only_pending):

    # Get all the CAS Condition from DB, (DataFrame)
    all_cas_conditions = get_all_cas_conditions_from_db(only_pending)

    # Iterate cas condition rows
    for _, row in all_cas_conditions.iterrows():

        # Init
        unique_id = row["Unique ID"]
        trading_combination_unique_id = row["Trading Combination Unique ID"]
        cas_condition_type = row["CAS Condition Type"]
        cas_condition = row["Condition"].strip()
        reference_price = f"{float(row['Condition Reference Price']):,.2f}"
        reference_position = row["Reference Position"]
        target_position = row["Target Position"]
        trigger_price = (
            row["Condition Trigger Price"].strip()
            if (row["Condition Trigger Price"].strip() != "N/A")
            else "N/A"
        )
        status = row["Status"]
        reason_for_failed = row["Reason For Failed"]
        correlation = "N/A"
        account_id = row["Account ID"]
        eval_unique_id = row["Evaluation Unique ID"].strip()
        flag_execution_engine = row["Execution Engine"]
        series_id = row["Series ID"]

        # chekc if series id is not none
        if series_id not in ["None", "N/A", None]:

            # convert to int
            series_id = int(series_id)

        # check if cas order is add/switch
        if cas_condition_type in ["ADD", "SWITCH"]:

            # check if unique id is not present in dict
            if int(unique_id) not in variables.cas_unique_id_to_combo_obj:

                # Init
                cas_combo_for_unique_id = "None"

                incremental_combo_tickes_info_string = "None"

            else:
                # Get CAS combo
                cas_combo_for_unique_id = variables.cas_unique_id_to_combo_obj[
                    unique_id
                ]

                # Get Informative string
                incremental_combo_tickes_info_string = make_informative_combo_string(
                    cas_combo_for_unique_id
                )
        else:

            # Set to N/A
            incremental_combo_tickes_info_string = "N/A"

        # Row data for the CAS Condition row in the GUI table
        cas_condition_row_values = (
            unique_id,
            trading_combination_unique_id,
            eval_unique_id,
            cas_condition_type,
            incremental_combo_tickes_info_string,
            cas_condition,
            reference_price,
            reference_position,
            target_position,
            trigger_price,
            status,
            reason_for_failed,
            correlation,
            account_id,
            flag_execution_engine,
            series_id,
            f"{unique_id}_{account_id}",
        )

        # Creating dataframe for row data
        cas_condition_row_df = pd.DataFrame(
            [cas_condition_row_values], columns=variables.cas_condition_table_columns
        )

        # Merge row with combo details dataframe
        variables.cas_condition_table_dataframe = pd.concat(
            [variables.cas_condition_table_dataframe, cas_condition_row_df],
            ignore_index=True,
        )

        # Make local copy
        local_unique_id_list_of_selected_watchlist = copy.deepcopy(
            variables.unique_id_list_of_selected_watchlist
        )

        # Inserting the cas condition row in the GUI table if the Unique ID exists in the watchlist
        if (
            str(unique_id) in local_unique_id_list_of_selected_watchlist.split(",")
            or local_unique_id_list_of_selected_watchlist == "ALL"
        ):

            # Insert the row value inside of cas_conditional_tab
            variables.screen.screen_cas_obj.insert_cas_condition_row_in_cas_condition_table(
                (
                    unique_id,
                    trading_combination_unique_id,
                    eval_unique_id,
                    cas_condition_type,
                    incremental_combo_tickes_info_string,
                    cas_condition,
                    reference_price,
                    reference_position,
                    target_position,
                    trigger_price,
                    status,
                    reason_for_failed,
                    correlation,
                    account_id,
                    flag_execution_engine,
                    series_id,
                    f"{unique_id}_{account_id}",
                )
            )
