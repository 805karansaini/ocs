"""
Created on 25-Mar-2023

@author: Karan
"""

from com import *
from com.variables import *
from com.ibapi_callbacks import *
from com.contracts import *
from com.prices import *
from com.greeks import *

# Compares the 'target date(expiry)' with all expiries and returns the closest available expiry from them.
def get_closest_exp_from_expiries_given_target_date(
    symbol, target_date_str, expiry_dates_ticker, today_str, low_range_date_str, high_range_date_str,
):

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Getting Closest Expiry from list of Expiries, {symbol=} {target_date_str=}"
        )

    # Making dict, so the user can visualize the result in DataFrame(tabular form)
    col1 = variables.df_expiry_summary_header_col1  # Expiry Dates
    col2 = variables.df_expiry_summary_header_col2  # Difference
    col3 = variables.df_expiry_summary_header_col3  # Expiry DTE

    expiry_dates_summary = {col1: [], col3: [], col2: []}

    # Making the date object, for getting the closest_expiry date, Init Variables
    target_date_obj = variables.target_timezone_obj.localize(
        datetime.datetime.strptime(target_date_str, "%Y%m%d")
    )

    low_range_date_obj = variables.target_timezone_obj.localize(
        datetime.datetime.strptime(low_range_date_str, "%Y%m%d")
    )

    high_range_date_obj = variables.target_timezone_obj.localize(
        datetime.datetime.strptime(high_range_date_str, "%Y%m%d")
    )
    min_diff = None
    closest_expiry = None
    selected_row = None
    expiries_in_range = []

    # For each date in expiry_dates_ticker' checking the difference and updating the closest_expiry(date)
    
    for row, d in enumerate(expiry_dates_ticker):
        expiry_date_obj = variables.target_timezone_obj.localize(datetime.datetime.strptime(d, "%Y%m%d"))
        
        # print(low_range_date_obj, high_range_date_obj, expiry_date_obj)
        # Difference between the dates
        if low_range_date_obj <= expiry_date_obj <= high_range_date_obj:
            expiries_in_range.append(d)
        diff = abs(
            (
                variables.target_timezone_obj.localize(
                    datetime.datetime.strptime(d, "%Y%m%d")
                )
                - target_date_obj
            ).days
        )

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Date : {target_date_obj} date we are checking : {d} difference => {diff}"
            )
            print(
                "Expiry DTE: ",
                (
                    variables.target_timezone_obj.localize(
                        datetime.datetime.strptime(str(d), "%Y%m%d")
                    )
                    - variables.target_timezone_obj.localize(
                        datetime.datetime.strptime(str(today_str), "%Y%m%d")
                    )
                ),
            )
        # Updating closest_expiry(date), min_diff, selected_row
        if (min_diff is None) or (diff < min_diff):
            min_diff = diff
            closest_expiry = d
            selected_row = row

        # Adding the value to columns
        expiry_dates_summary[col1].append(d)
        expiry_dates_summary[col2].append(str(diff))
        expiry_dates_summary[col3].append(
            (
                variables.target_timezone_obj.localize(
                    datetime.datetime.strptime(str(d), "%Y%m%d")
                ).date()
                - variables.target_timezone_obj.localize(
                    datetime.datetime.strptime(str(today_str), "%Y%m%d")
                ).date()
            ).days
        )

    # Making pandas 'expiry_dates_summary_df' and adding the * on the selected value
    expiry_dates_summary_df = pd.DataFrame(expiry_dates_summary)

    expiry_dates_summary_df.loc[[selected_row], col2] = f"{min_diff} *"

    # Print to console in tabular form
    if variables.flag_identification_print:
        print(f"Closet Expiry for {symbol}")
        print(
            tabulate(
                expiry_dates_summary_df,
                headers="keys",
                tablefmt="psql",
                showindex=False,
            )
        )

    # Print to console
    if variables.flag_debug_mode:
        print(f"Got Closest Expiry = {closest_expiry},  {symbol=} {target_date_str=}")

    return closest_expiry, expiries_in_range


# We want all the strikes for given user expriy_date and Trading class for FOP,
# So first get all the future expiry (upto 7months + given user expriy_date)
# Note: To get FOP strike we need FUT(coind), reqDefSec
# Then get all the strikes such that for given FUTs such that user_given Trading Class exists in FOP.
def get_all_strikes_for_fop_given_expiry_date(
    symbol,
    expiry_date,
    underlying_sec_type,
    exchange,
    currency,
    multiplier,
    trading_class,
):

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Getting all the strikes for FOP for Given Expiry Date: {symbol=} {expiry_date=} {underlying_sec_type=} {exchange=} {multiplier=} {trading_class=}"
        )

    # Making Specified target date so we can get all the expiry for upto this date.
    try:
        # Str to Time object
        expiry_date = datetime.datetime.strptime(expiry_date, "%Y%m%d")
        specific_target_date = (expiry_date + datetime.timedelta(days=210)).strftime(
            "%Y%m%d"
        )
    except Exception as e:
        print("Exception Inside get_all_strikes_for_fop_given_expiry_date", e)
        return None

    # Init
    days_to_expiry = 1

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Getting all the FUT expiries for {symbol=} upto {specific_target_date=} {underlying_sec_type=} {exchange=} {multiplier=} {trading_class=}"
        )

    # All Fut Expiries upto the
    all_fut_expiries = find_nearest_expiry_for_future_given_fut_dte(
        symbol,
        days_to_expiry,
        underlying_sec_type,
        exchange,
        currency,
        multiplier,
        trading_class,
        only_want_all_expiries=True,
        specific_target_date=specific_target_date,
    )

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Got all FUT Expiries: {all_fut_expiries}, {symbol=} upto {specific_target_date=} {underlying_sec_type=} {exchange=} {multiplier=} {trading_class=}"
        )

    # Handling None
    if all_fut_expiries == None:
        return None

    # Set of all the strike
    all_strikes = set()

    # futFopExchange for FUT
    futFopExchange = exchange

    # Processing all FUT expiry, want to get all expiries for FUT such that the Trading class is same as user provided
    for expiry_date_ith in all_fut_expiries:

        # Getting Conid for Underlying FUT
        contract = get_contract(
            symbol,
            underlying_sec_type,
            exchange,
            currency,
            expiry_date_ith,
            multiplier=multiplier,
        )
        contract_details = get_contract_details(contract)

        # Handling None Value of contract_details
        if contract_details == None:
            continue
        else:
            conid = contract_details.contract.conId

        # Getting all the expiries for fop such trading class is same as user provided one.
        all_expiry, all_strike_ith = get_list_of_strikes_and_expiries(
            symbol, conid, futFopExchange, underlying_sec_type, trading_class
        )

        # if all_expiry is not non
        if all_strike_ith != None:
            for x in all_strike_ith[1:-1].split(","):
                all_strikes.add(float(x))

    # Converting to sorted list
    all_strikes = sorted(all_strikes)

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Got all Strikes for FOP: {symbol=} {exchange=} {multiplier=} {trading_class=}"
        )
        print(f"{all_strikes=}")

    # Return None if Zero strikes found(i.e wrong user input)
    if len(all_strikes) == 0:
        return None

    return all_strikes


# Find the nearest expiry for FUTURE given FUT DTE
def find_nearest_expiry_for_future_given_fut_dte(
    ticker,
    days_to_expiry,
    sec_type,
    exchange,
    currency,
    multiplier,
    trading_class,
    only_want_all_expiries=False,
    specific_target_date=False,
):

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Finding nearest expiry for FUT: {ticker=} {days_to_expiry=} {sec_type=} {exchange=} {trading_class=} {only_want_all_expiries=} {specific_target_date=}"
        )

    # Creating a date for which we need to check the closest expiry date in expiry_dates_ticker (today_str + dte)
    today_obj = datetime.datetime.now(variables.target_timezone_obj)
    today_str = today_obj.strftime("%Y%m%d")
    target_date_str = (today_obj + datetime.timedelta(days=days_to_expiry)).strftime(
        "%Y%m%d"
    )
    if only_want_all_expiries:
        target_date = today_obj + relativedelta(days=days_to_expiry, months=7)
        target_date_str = target_date.strftime("%Y%m%d")

        # Used when expiry is given but not strike, so to get all the strikes we will need it.
        if specific_target_date != False:
            target_date_str = specific_target_date

    # Print to console
    if variables.flag_debug_mode:
        print(f"Finding the nearest expiry date near {target_date_str} for {ticker}")

    # Creating the contract, this contract will be used to get the conId using contractDetails for the underlying so we can use that conId to fetch option chain using reqSecDef
    contract = get_contract(
        ticker,
        sec_type,
        exchange,
        currency,
        multiplier=multiplier,
    )
    # primary_exchange=exchange, trading_class=trading_class)

    # Get reqId
    reqId = variables.nextorderId
    variables.nextorderId += 1

    # Getting Contract details so we have conId of respective ticker
    contract_details = get_contract_details(contract, reqId)

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Contract to fetch all the expiries and strikes {contract} and Contract Details: {contract_details}"
        )

    # Contract details not found
    if contract_details is None:
        return None

    # These variables are inside get_contract_details
    # variables.map_expiry_to_conid[reqId]
    # variables.all_conid_from_con_details[reqId]

    # Convert all the expiry dates set to list
    all_expiry_dates_ticker = sorted(variables.map_expiry_to_conid[reqId].keys())

    # Handling no Values
    if all_expiry_dates_ticker is None:
        return None

    # Print to console
    if variables.flag_debug_mode:
        print(f"Expiry Dates: {all_expiry_dates_ticker}")

    # When only needs all the Expiries for FOP
    if only_want_all_expiries == True:

        # Trim expiry to right
        right_index = bisect.bisect_right(all_expiry_dates_ticker, target_date_str)
        all_expiry_dates_ticker = all_expiry_dates_ticker[:right_index]

        return all_expiry_dates_ticker

    # if flag_return_all_filter_epxpiries:
    #     get_all_filter_expires()
    # else:
    #     pass
    # Get Closest Expiry to 'target_date_str'
    closest_expiry_date = str(
        get_closest_exp_from_expiries_given_target_date(
            ticker, target_date_str, all_expiry_dates_ticker, today_str
        )
    )

    return closest_expiry_date


# Gets the list of all the available strikes and expiries from TWS, uses reqSecDefOptParams
def get_list_of_strikes_and_expiries(
    ticker, conid, futFopExchange, underlying_sec_type, fop_trading_class, reqId=None
):

    # Get reqId
    if reqId == None:
        reqId = variables.nextorderId
        variables.nextorderId += 1
    else:
        reqId = reqId

    # Init
    variables.expiry_dates[reqId] = None
    variables.strike_prices[reqId] = None
    variables.map_reqid_to_trading_class_sec_def[reqId] = fop_trading_class
    variables.req_sec_def_end[reqId] = None
    variables.req_error[reqId] = False

    variables.map_reqid_to_all_trading_class[reqId] = []

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Fetching all available Strike Prices and Expiry Dates from TWS for {ticker} reqI: {reqId}"
        )

    # Map reqId to exchange so we can select value based on set, futFopExchange, if futFopExchange is blank we will pick 'SMART' Values
    variables.map_req_id_to_fut_fop_exchange[reqId] = (
        futFopExchange if futFopExchange != "" else "SMART"
    )

    # print(reqId, ticker, futFopExchange, underlying_sec_type, conid)
    # Fetching all the expiry and strikes for the ticker
    variables.app.reqSecDefOptParams(
        reqId, ticker, futFopExchange, underlying_sec_type, conid
    )

    # Timeout
    counter = 0

    # Wait for response from TWS
    while True:

        # Received Response, or request ended
        if (
            (
                (variables.expiry_dates[reqId] is not None)
                and (variables.strike_prices[reqId] is not None)
            )
            or (variables.req_sec_def_end[reqId] == True)
            or (variables.req_error[reqId] == True)
        ):

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Successfully fetched all the Strike Price and Expiry Dates from TWS for {ticker} reqI: {reqId}"
                )

            # Answer received successfully
            return (variables.expiry_dates[reqId], variables.strike_prices[reqId])

        else:

            # Timeout of 11 secs
            if counter >= int(11 / variables.sleep_time_waiting_for_tws_response):

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Could not fetch all the Strike Price and Expiry Dates from TWS for {ticker} reqI: {reqId}"
                    )

                # Returning None
                return (variables.expiry_dates[reqId], variables.strike_prices[reqId])

            if variables.flag_debug_mode and (counter % 20 == 0):
                print(
                    f"Waiting for the Strike Price and Expiry Dates response from TWS for {ticker} reqI: {reqId}"
                )

            # Waiting for response
            time.sleep(variables.sleep_time_waiting_for_tws_response)

            # Increasing counter
            counter += 1


# Async code for getting strikes and expiries used when identifying the trading class for legs
async def get_list_of_strikes_and_expiries_async(
    ticker, conid, futFopExchange, underlying_sec_type, fop_trading_class, reqId=None
):

    # Get reqId
    if reqId == None:
        reqId = variables.nextorderId
        variables.nextorderId += 1
    else:
        reqId = reqId

    # Init
    variables.expiry_dates[reqId] = None
    variables.strike_prices[reqId] = None
    variables.map_reqid_to_trading_class_sec_def[reqId] = fop_trading_class
    variables.req_sec_def_end[reqId] = None
    variables.req_error[reqId] = False

    variables.map_reqid_to_all_trading_class[reqId] = []

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Fetching all available Strike Prices and Expiry Dates from TWS for {ticker} reqI: {reqId}"
        )

    # Map reqId to exchange so we can select value based on set, futFopExchange, if futFopExchange is blank we will pick 'SMART' Values
    variables.map_req_id_to_fut_fop_exchange[reqId] = (
        futFopExchange if futFopExchange != "" else "SMART"
    )

    # Fetching all the expiry and strikes for the ticker
    variables.app.reqSecDefOptParams(
        reqId, ticker, futFopExchange, underlying_sec_type, conid
    )

    # Timeout
    counter = 0

    # Wait for response from TWS
    while True:

        # Received Response, or request ended
        if (
            (
                (variables.expiry_dates[reqId] is not None)
                and (variables.strike_prices[reqId] is not None)
            )
            or (variables.req_sec_def_end[reqId] == True)
            or (variables.req_error[reqId] == True)
        ):

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Successfully fetched all the Strike Price and Expiry Dates from TWS for {ticker} reqI: {reqId}"
                )

            # Answer received successfully
            return (variables.expiry_dates[reqId], variables.strike_prices[reqId])

        else:

            # Timeout of 11 secs
            if counter >= int(11 / variables.sleep_time_waiting_for_tws_response):

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Could not fetch all the Strike Price and Expiry Dates from TWS for {ticker} reqI: {reqId}"
                    )

                # Returning None
                return (variables.expiry_dates[reqId], variables.strike_prices[reqId])

            if variables.flag_debug_mode and (counter % 20 == 0):
                print(
                    f"Waiting for the Strike Price and Expiry Dates response from TWS for {ticker} reqI: {reqId}"
                )

            # Waiting for response
            await asyncio.sleep(variables.sleep_time_waiting_for_tws_response)

            # Increasing counter
            counter += 1


# Finds the nearest expiry date given 'ticker' and 'days_to_expiry'
def find_nearest_expiry_and_all_strikes_for_stk_given_dte(
    ticker,
    days_to_expiry,
    underlying_sec_type,
    exchange,
    currency,
    multiplier,
    fop_trading_class,
    low_range_date_str,
    high_range_date_str,
):

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Finding Nearest Expiry and All Strikes for STK(OPT): {ticker=} {days_to_expiry=}"
        )

    # Creating a date for which we need to check the closest expiry date in expiry_dates_ticker (today_str + dte)
    today_obj = datetime.datetime.now(variables.target_timezone_obj)
    today_str = today_obj.strftime("%Y%m%d")
    target_date_str = (today_obj + datetime.timedelta(days=days_to_expiry)).strftime(
        "%Y%m%d"
    )

    # Print to console
    if variables.flag_debug_mode:
        print(f"Finding the Closest expiry date near {target_date_str} for {ticker}")

    # Making a contract
    contract = get_contract(
        ticker,
        underlying_sec_type,
        exchange,
        currency,
    )

    # Get reqId
    reqId = variables.nextorderId
    variables.nextorderId += 1

    # Getting Contract details so we have conId of respective ticker
    contract_details = get_contract_details(contract)

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Contract to fetch all the expiries and strikes {contract} and Contract Details: {contract_details}"
        )

    # Contract details not found
    if contract_details is None:
        return None, None, None, None, None

    # The exchange on which the returned options are trading. Can be set to the empty string "" for all exchanges
    # (for STK we are using "" and the callback of reqsecdef is handles such we get the 'SMART' values or The futFopExchange values).
    futFopExchange = ""
    conid = contract_details.contract.conId
    underlying_conid  = int(conid)
    
    # Getting Expiry dates and Strike prices for a ticker
    all_expiry_dates_ticker, strike_prices_ticker = get_list_of_strikes_and_expiries(
        ticker, conid, futFopExchange, underlying_sec_type, fop_trading_class
    )

    # Handling no Values
    if (all_expiry_dates_ticker is None) or len(all_expiry_dates_ticker) == 0:
        return None, None, None, None, None

    # Sorting Expiries
    all_expiry_dates_ticker = sorted(all_expiry_dates_ticker)

    # Print to console
    if variables.flag_debug_mode:
        print(f"Expiry Dates: {all_expiry_dates_ticker}")

    # Finding Closest Expiry to 'target_date_str'
    # Return multiexpiries from here # TODO Point 2
    closest_expiry_date, expiry_date_in_range = (
        get_closest_exp_from_expiries_given_target_date(
            ticker, target_date_str, all_expiry_dates_ticker, today_str, low_range_date_str, high_range_date_str,
        )
    )

    # Print to console
    if variables.flag_debug_mode:
        print(f"Expiry Dates: {all_expiry_dates_ticker}")
        print(f"Available Strike Prices: {strike_prices_ticker}")

    return all_expiry_dates_ticker, strike_prices_ticker, closest_expiry_date, underlying_conid, expiry_date_in_range


# Find closest expiry for FOP, with user provided DTE, trading class
def find_closest_expiry_for_fop_given_fut_expiries_and_trading_class(
    symbol,
    dte,
    underlying_sec_type,
    exchange,
    currency,
    multiplier,
    trading_class,
    all_fut_expiries,
    low_range_date_str,
    high_range_date_str,
):

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Finding closest expiry for FOP {symbol=} given {dte} {trading_class} {all_fut_expiries=}"
        )

    # Creating a date for which we need to check the closest expiry date in expiry_dates_ticker (today_str + dte)
    today_obj = datetime.datetime.now(variables.target_timezone_obj)
    today_str = today_obj.strftime("%Y%m%d")
    target_date_str = (today_obj + datetime.timedelta(days=dte)).strftime("%Y%m%d")

    # Print to console
    if variables.flag_debug_mode:
        print(f"Finding the Closest expiry date near {target_date_str} for {symbol}")

    # Map expiry to all_strikes for FOP
    map_expiry_to_all_strikes = {}

    # if expiry found for trading class, save it.
    futFopExchange = exchange

    # Creating a set, it will contains all the expiry such trading class is same as user provided
    all_expiries_with_user_provided_trading_class = set()

    # Map the fop expiry to fut conid TODO ARYAN
    map_fop_expiry_to_fut_conid = {}   

    # Processing all FUT expiry, want to get all expiries for FUT such that the Trading class is same as user provided
    for expiry_date_ith in all_fut_expiries:

        # Getting Conid for Underlying FUT
        contract = get_contract(
            symbol,
            underlying_sec_type,
            exchange,
            currency,
            expiry_date_ith,
            multiplier=multiplier,
        )
        contract_details = get_contract_details(contract)

        # Handling None Value of contract_details
        if contract_details == None:
            continue
        else:
            conid = contract_details.contract.conId

        # Getting all the expiries for fop such trading class is same as user provided one.
        all_expiry, all_strike = get_list_of_strikes_and_expiries(
            symbol, conid, futFopExchange, underlying_sec_type, trading_class
        )

        # if all_expiry is not none
        if all_expiry != None:
            for __expiry_date in all_expiry:
                all_expiries_with_user_provided_trading_class.add(__expiry_date)

                # TODO - ARYAN Map FOP expiry to FUT conid
                map_fop_expiry_to_fut_conid[int(__expiry_date)] = int(conid)

                # if all_expiry is not none
                if all_strike != None:

                    # Creating a list, if not already
                    if __expiry_date in map_expiry_to_all_strikes:
                        pass
                    else:
                        map_expiry_to_all_strikes[__expiry_date] = []

                    for __strike in all_strike[1:-1].split(","):
                        map_expiry_to_all_strikes[__expiry_date].append(float(__strike))
                        
    # Creating sorted list
    all_expiries_with_user_provided_trading_class = sorted(
        list(all_expiries_with_user_provided_trading_class)
    )

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Got all the expiries for FOP {symbol=} given {dte=} {trading_class=} {all_expiries_with_user_provided_trading_class=}"
        )

    # If length of 'all_expiries_with_user_provided_trading_class' is Zero. Return None
    if len(all_expiries_with_user_provided_trading_class) < 1:
        return None, None, None

    # Getting Closest Expiry for FOP if length 'all_expiries_with_user_provided_trading_class' > 0
    closest_expiry_date, expiry_date_in_range = get_closest_exp_from_expiries_given_target_date(
        symbol,
        target_date_str,
        all_expiries_with_user_provided_trading_class,
        today_str,
        low_range_date_str,
        high_range_date_str,
    )
    
    
    # Creating 'closest_expiry_date' str again
    closest_expiry_date = str(closest_expiry_date)

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Got the closest expiry for FOP {symbol=} given {dte=} {trading_class=} {closest_expiry_date=}"
        )

    # Look up the 
    underlying_conid = map_fop_expiry_to_fut_conid[int(closest_expiry_date)]

    # Creating sorted list of strike with unique values
    all_strike_prices = sorted(set(map_expiry_to_all_strikes[closest_expiry_date]))

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"All The strikes for FOP {symbol=} given {dte=} {trading_class=} {all_strike_prices=}"
        )

    return all_strike_prices, closest_expiry_date, underlying_conid, expiry_date_in_range

# Method to find nearest strike prices
async def find_nearest_strike_delta_diff_min_async(
    ticker,
    expiry_date,
    otype,
    delta,
    strike_prices_ticker,
    sec_type,
    exchange,
    currency,
    multiplier,
    trading_class,
):
    # For th NDX which is IND we have to give 'NASDAQ' to get the underlying contracts and the list of strikes and expiry.
    # And to recieve the OPT Delta we will put in the exchange == 'SMART'
    if ticker in ["NDX", "ndx"]:
        exchange = "SMART"

    # Empty list of strikes
    if len(strike_prices_ticker) < 1:
        return None

    # Making a dict, so we can make the DataFrame and visualize the results
    col1 = variables.df_strike_summary_header_col1
    col2 = variables.df_strike_summary_header_col2
    col3 = variables.df_strike_summary_header_col3
    data_frame = {col1: [], col2: [], col3: []}

    # Set the nearest strike, min_diff, selected_row to None, And valid_strike to empty list so we can have all the strike for which we have received the delta
    nearest_strike = None
    min_delta_difference = None
    selected_row = None

    # TODO - performance measure
    start = time.perf_counter()

    # We will check for delta for buckets_size = 10, if no delta is found then check for delta in buxket size of 20, if still not found check all strikes
    while True:

        # Checking 10 strikes

        ### This is the part of algorithm in which we are concerned with getting the range of strike where given delta is present ####
        number_buckets = 20
        modulo_value = max(int(len(strike_prices_ticker) / number_buckets), 1)

        # Taking odd number
        if modulo_value % 2 == 0:
            modulo_value = modulo_value - 1

        strikes_level_1 = strike_prices_ticker[
            ::modulo_value
        ]  # [x for x in strike_prices_ticker if x % modulo_value == 0]

        # Making a list of all the contracts, So we can fetch the delta for each contract
        contracts_level_1 = [
            get_contract(
                ticker,
                sec_type,
                exchange,
                currency,
                expiry_date,
                strikeprice,
                otype,
                multiplier,
                trading_class=trading_class,
            )
            for strikeprice in strikes_level_1
        ]

        # Fetching option delta for each contract in the contracts_list
        opt_deltas_level_1 = await asyncio.gather(
            *[
                get_opt_delta(contract, variables.flag_market_open)
                for contract in contracts_level_1
            ]
        )

        if variables.flag_debug_mode:
            print("Strike Level 1a : ")
            print(strikes_level_1)
            print(opt_deltas_level_1)

        # Count the number of occurrences of each result
        counter = Counter(opt_deltas_level_1)

        # If all deltas are None
        if (None in counter) and (counter[None] == len(opt_deltas_level_1)):

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"All strikes in Level 1 (10 Strikes Checked) returned delta = None for ticker: {ticker} Expiry {expiry_date}"
                )

        else:
            break

        # Check for 20 strikes
        ### This is the part of algorithm in which we are concerned with getting the range of strike where given delta is present ####
        number_buckets = 20
        modulo_value = max(int(len(strike_prices_ticker) / number_buckets), 1)

        # Taking odd number
        if modulo_value % 2 == 0:
            modulo_value = modulo_value - 1

        strikes_level_1 = strike_prices_ticker[
            ::modulo_value
        ]  # [x for x in strike_prices_ticker if x % modulo_value == 0]

        # Making a list of all the contracts, So we can fetch the delta for each contract
        contracts_level_1 = [
            get_contract(
                ticker,
                sec_type,
                exchange,
                currency,
                expiry_date,
                strikeprice,
                otype,
                multiplier,
                trading_class=trading_class,
            )
            for strikeprice in strikes_level_1
        ]

        # Fetching option delta for each contract in the contracts_list
        opt_deltas_level_1 = await asyncio.gather(
            *[
                get_opt_delta(contract, variables.flag_market_open)
                for contract in contracts_level_1
            ]
        )

        if variables.flag_debug_mode:
            print("Strike Level 1b : ")
            print(strikes_level_1)
            print(opt_deltas_level_1)

        # Count the number of occurrences of each result
        counter = Counter(opt_deltas_level_1)

        # If all deltas are None
        if (None in counter) and (counter[None] == len(opt_deltas_level_1)):

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"All strikes in Level 1 (20 Strikes Checked) returned delta = None for ticker: {ticker} Expiry {expiry_date}"
                )
                print("Checking all Strikes")

        break

    # Init, variable will store the strike prices such that the (strike_price_such_that_delta_lower_than_target_delta) low_delta < given delta(user input) < high_delta(strike_price_such_that_delta_higher_than_target_delta)
    strike_price_such_that_delta_higher_than_target_delta = strikes_level_1[0]
    strike_price_such_that_delta_lower_than_target_delta = strikes_level_1[-1]

    # Note:- call: 1 to 0, Put 0 to -1, delta is always decreasing for both PUT and CALL

    # Higher Delta
    for strike_val, delta_val in zip(strikes_level_1, opt_deltas_level_1):

        # if delta is None: Continue
        if delta_val is None:
            continue

        # if delta <= given delta break
        if delta_val <= delta:
            break

        # Keep the strike such that delta value is greater
        strike_price_such_that_delta_higher_than_target_delta = strike_val

    # Lower Delta
    for strike_val, delta_val in zip(strikes_level_1, opt_deltas_level_1):

        # if delta is None Continue
        if delta_val is None:
            continue

        # if delta < given delta break
        if delta_val < delta:

            # Keep the strike such that delta value is greater
            strike_price_such_that_delta_lower_than_target_delta = strike_val
            break

    range_of_strikes_level_2 = [
        strike_price_such_that_delta_higher_than_target_delta,
        strike_price_such_that_delta_lower_than_target_delta,
    ]

    if variables.flag_debug_mode:
        print("Range Level :", range_of_strikes_level_2)

    if variables.flag_debug_mode:
        print(
            f"Range of strikes identified for Level 2, before buffer: {range_of_strikes_level_2}"
        )

    # Additional number of strikes to consider on either side
    buffer_strike = 5

    # Get left and right indices for the range of strikes for Level 2, with buffer added on either side
    index_left = max(
        bisect.bisect_left(strike_prices_ticker, range_of_strikes_level_2[0])
        - buffer_strike,
        0,
    )
    index_right = min(
        bisect.bisect_right(strike_prices_ticker, range_of_strikes_level_2[1])
        + buffer_strike,
        len(strike_prices_ticker),
    )

    # Print to console
    if variables.flag_identification_print:
        print(
            f"{ticker}: Searching in range: {strike_prices_ticker[index_left]} to {strike_prices_ticker[index_right - 1]}"
        )

    ### This is the part of algorithm in which we are actually getting the strike which have the minimum delta ####

    # Making a list of all the contracts, all_available_strike_prices[index_left : index_right] So we can fetch the delta for each contract in it.
    contracts_level_2 = [
        get_contract(
            ticker,
            sec_type,
            exchange,
            currency,
            expiry_date,
            strikeprice,
            otype,
            multiplier,
            trading_class=trading_class,
        )
        for strikeprice in strike_prices_ticker[index_left:index_right]
    ]

    # Fetching option delta for each contract in the contracts_list
    opt_deltas_level_2 = await asyncio.gather(
        *[
            get_opt_delta(contract, variables.flag_market_open)
            for contract in contracts_level_2
        ]
    )

    # End time of performance counter
    end = time.perf_counter()

    # Print to console
    if variables.flag_debug_mode:
        print(f"Time took for fetching delta: {end - start}")

    ### Selecting the row which has the lowest diff between deltas (given delta and opt_delta @ strike)
    # To keep track of the selected row
    row = 0

    # Making the contract with all the different strike price, Then fetching the delta for that contract
    for strike_price, delta_opt in zip(
        strike_prices_ticker[index_left:index_right], opt_deltas_level_2
    ):

        # if value of delta_opt is 'None'
        if delta_opt is None:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Couldnot find the option delta for {ticker} {strike_price} {expiry_date} {otype}"
                )
            continue

        # Updating the 'nearest_strike' if (it is None) OR (a closer delta has been identified)
        if (nearest_strike is None) or (abs(delta - delta_opt) < min_delta_difference):

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Difference between delta given Userinput :{delta} and delta at strike {strike_price} : {abs(delta - delta_opt)}"
                )

            # Updating the variables, so we can keep info regarding our best strike
            min_delta_difference = abs(delta - delta_opt)

            nearest_strike = strike_price
            selected_row = row

        # Adding valid values to data_frame
        data_frame[col1].append(strike_price)
        data_frame[col2].append(f"{delta_opt:.4f}")
        data_frame[col3].append(f"{abs(delta - delta_opt):.4f}")

        row += 1

    # Could not find nearest strike
    if nearest_strike is None:

        return None

    # Converting dict to pandas df and adding the * to selected row
    df = pd.DataFrame(data_frame)
    df.loc[[selected_row], col3] = f"{min_delta_difference:.4f} *"

    # Printing in tabular form
    df = df.sort_values(col1)

    if variables.flag_identification_print:
        print(f"Delta for {ticker}")
        print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))

    return nearest_strike


# Making/Wrapping 'get_opt_delta' to be async
async def resolve_leg(
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
):

    # Init
    all_strike_prices = None
    # The way reqSecurityDefinitionOptionParameter works its important to have string in this form.
    if trading_class == None:
        trading_class = ""

    # For Futures get the nearest 'fut_expiry_date' date given 'DTE (FUT)'
    if (sec_type in ["FUT"]) and (expiry_date == None):

        # cheange under asset sec type for rty
        if symbol in ["RTY", "rty"]:

            underlying_sec_type = "IND"

        # Get closest fut_expiry_date
        expiry_date = find_nearest_expiry_for_future_given_fut_dte(
            symbol, dte, sec_type, exchange, currency, multiplier, trading_class=""
        )

        # Return None if fut_expiry_date not found, it will throw error
        if expiry_date == None:
            return None

    if (sec_type == "OPT") and (expiry_date == None):

        # Underlying SecType for FUT & OPT
        underlying_sec_type = "STK"

        if symbol in ["SPX", "spx"]:

            underlying_sec_type = "IND"

        if symbol in ["NDX", "ndx"]:
            underlying_sec_type = "IND"

            """if symbol in ['SPX', 'spx']:
                exchange = 'CBOE"""

        # Get the closest expiry date given the 'symbol' and 'dte'
        (
            all_expiries,
            all_strike_prices,
            expiry_date,
        ) = find_nearest_expiry_and_all_strikes_for_stk_given_dte(
            symbol,
            dte,
            underlying_sec_type,
            exchange,
            currency,
            multiplier,
            trading_class,
        )

        # Can not get opt expiry throw error
        if expiry_date == None:
            return None

        # Sort and convert to list of floats
        if all_strike_prices != None:
            # Converting strike in float and Sort the strike
            all_strike_prices = sorted(
                [float(x) for x in all_strike_prices[1:-1].split(",")]
            )

    elif (sec_type == "FOP") and (expiry_date == None):

        # Get all the future expiries
        underlying_sec_type = "FUT"
        all_fut_expiries = find_nearest_expiry_for_future_given_fut_dte(
            symbol,
            dte,
            underlying_sec_type,
            exchange,
            currency,
            multiplier,
            trading_class="",
            only_want_all_expiries=True,
        )

        # Handling None
        if all_fut_expiries == None:
            return None

        # get closest FOP Expiry for given Trading class
        (
            all_strike_prices,
            expiry_date,
        ) = find_closest_expiry_for_fop_given_fut_expiries_and_trading_class(
            symbol,
            dte,
            underlying_sec_type,
            exchange,
            currency,
            multiplier,
            trading_class,
            all_fut_expiries,
        )

        if expiry_date == None:
            return None

    # Now we have Expiry. if we dont have strike and all the strike for FOP/OPT is also None. Get all the strikes to search the strike
    if sec_type in ["OPT", "FOP"] and (
        strike_price == None and all_strike_prices == None
    ):

        # Init
        underlying_sec_type = "STK" if sec_type == "OPT" else "FUT"
        futFopExchange = "" if exchange == "SMART" else exchange

        if sec_type == "OPT":

            # Underlying contract to get conid
            contract = get_contract(
                symbol,
                underlying_sec_type,
                exchange,
                currency,
                expiry_date,
                multiplier,
                primary_exchange,
                trading_class,
            )
            contract_details = get_contract_details(contract)
            if contract_details == None:

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Could Not contract details, {symbol=} {sec_type=} {exchange=} {currency=} {expiry_date=} {strike_price=} {right=} {multiplier=} {primary_exchange=} {trading_class=}"
                    )

                return None
            else:
                con_id = contract_details.contract.conId

            # Getting option chain, all the strikes and expiry
            _, all_strike_prices = get_list_of_strikes_and_expiries(
                symbol, con_id, futFopExchange, underlying_sec_type, trading_class
            )

            # Converting strike in float and Sort the strike
            all_strike_prices = sorted(
                [float(x) for x in all_strike_prices[1:-1].split(",")]
            )

        else:
            all_strike_prices = get_all_strikes_for_fop_given_expiry_date(
                symbol,
                expiry_date,
                underlying_sec_type,
                exchange,
                currency,
                multiplier,
                trading_class,
            )

    # Now we have OPT/FOP Expiry, search for strike if not provided by user
    # For OPT and FOP, find nearest 'strike', given 'delta'
    if (sec_type in ["OPT", "FOP"]) and (strike_price == None):

        # if we dont have strike return error, can not search for strikes, given delta
        if all_strike_prices == None:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Could Not Find All Strike , {symbol=} {sec_type=} {exchange=} {currency=} {expiry_date=} {strike_price=} {right=} {multiplier=} {primary_exchange=} {trading_class=}"
                )

            return None

        # Finding strike delta difference minimum
        strike_price = await find_nearest_strike_delta_diff_min_async(
            symbol,
            expiry_date,
            right,
            delta,
            all_strike_prices,
            sec_type,
            exchange,
            currency,
            multiplier,
            trading_class,
        )
        # print(strike_price)
        # Return None if strike not found, it will throw error
        if strike_price == None:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Could Not Find Strike {strike_price}, {symbol=} {sec_type=} {exchange=} {currency=} {expiry_date=} {strike_price=} {right=} {multiplier=} {primary_exchange=} {trading_class=}"
                )
            return None

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Inside Resolve Legs:  {symbol=} {sec_type=} {exchange=} {currency=} {expiry_date=} {strike_price=} {right=} {multiplier=} {primary_exchange=} {trading_class=}"
        )

    # Now we have everything now get the conid for the leg
    contract = get_contract(
        symbol,
        sec_type,
        exchange,
        currency,
        expiry_date,
        strike_price,
        right,
        multiplier,
        primary_exchange=primary_exchange,
        trading_class=trading_class,
    )

    # Get Contract Details for the identified contract
    contract_details = await get_contract_details_async(contract)

    # Print to console
    if variables.flag_debug_mode:
        print(f"Resolve Leg: {contract_details}")

    return contract_details


# Runs resolve_leg for all the legs that needed to be resolved.
async def run_tasks(legs_needs_to_be_solved):

    # Now resolve all the legs that needed to be resolved. (In separate threads for each leg)
    # tasks = [
    #     asyncio.to_thread(
    #         resolve_leg,
    #         action,
    #         symbol,
    #         sec_type,
    #         exchange,
    #         currency,
    #         quantity,
    #         expiry_date,
    #         strike_price,
    #         right,
    #         multiplier,
    #         con_id,
    #         primary_exchange,
    #         trading_class,
    #         dte,
    #         delta,
    #     )
    #     for leg_no, (
    #         action,
    #         symbol,
    #         sec_type,
    #         exchange,
    #         currency,
    #         quantity,
    #         expiry_date,
    #         strike_price,
    #         right,
    #         multiplier,
    #         con_id,
    #         primary_exchange,
    #         trading_class,
    #         dte,
    #         delta,
    #     ) in legs_needs_to_be_solved
    # ]
    #
    # # # Await for tasks/Threads to be completed   - When using thread use this line of code too
    # tasks_result = await asyncio.gather(*tasks)

    # Now resolve all the legs that needed to be resolved. single thread async code.
    tasks = [
        resolve_leg(
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
        )
        for leg_no, (
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
        ) in legs_needs_to_be_solved
    ]

    # Await for resolve_leg to be completed(To get returned value we need to await)
    results = await asyncio.gather(*tasks)

    # Print to console
    if variables.flag_debug_mode:
        for leg_no, res in enumerate(results):
            print(f"{leg_no=} {res=}")

    # contract_details or None
    return results
