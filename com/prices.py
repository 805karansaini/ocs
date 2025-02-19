"""
Created on 15-Mar-2023

@author: Karan
"""

import math

import numpy as np

from com.variables import *
from com.mysql_io import *
from com.combination import *
from com.utilities import *
from com.calc_weighted_change import *
from com.variables import *
from com.cache_handler import *
from com.screen_custom_columns import *
from com.screen_accounts_tab import *


# get tick size for contract
def get_tick_size_for_contract(all_leg_objs):
    for leg_obj in all_leg_objs:
        mycontract = Contract()

        mycontract = Contract()
        mycontract.conId = leg_obj.con_id
        con = variables.map_con_id_to_contract[mycontract.conId]

        mycontract.symbol = leg_obj.contract.symbol
        mycontract.secType = leg_obj.contract.secType
        mycontract.exchange = leg_obj.contract.exchange
        mycontract.currency = leg_obj.contract.currency

        # Get reqID
        req_id = variables.nextorderId
        variables.nextorderId += 1

        variables.app.reqContractDetails(reqId=req_id, contract=mycontract)

        rule_id = leg_obj.contract.marketRuleIds

        # print(rule_id)


# Get bid and ask for contract, snapshot = False, Uses reqMktData
def get_market_data_for_contract(unique_id, contract, snapshot=True):
    # Print to console
    if variables.flag_debug_mode:
        # Getting req_id
        print(
            f"Unique ID = {unique_id}: Requesting Market Data for (snapshot: {snapshot}) Contract: {contract}"
        )

    reqId = variables.nextorderId
    variables.nextorderId += 1

    if contract.conId in variables.con_id_to_req_id_dict:
        return

    # Init variables
    variables.ask_price[reqId] = None
    variables.bid_price[reqId] = None
    variables.con_id_to_req_id_dict[contract.conId] = reqId

    # set request type depending on whether the market is live or not
    if variables.flag_market_open:
        variables.app.reqMarketDataType(1)  # real time
    else:
        variables.app.reqMarketDataType(2)  # frozen

    generic_tick_list = ""
    snapshot = snapshot  # A true value will return a one=time snapshot, while a false value will provide streaming data.
    regulatory = False

    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Unique ID = {unique_id}: Fetching market data from TWS for option contract = {contract}, reqId = {reqId}"
        )

    variables.app.reqMktData(
        reqId, contract, generic_tick_list, snapshot, regulatory, []
    )

    # Error checking loop - breaks from loop once MktData is obtained
    for err_check in range(2):
        if variables.ask_price[reqId] == None or variables.bid_price[reqId] == None:
            time.sleep(variables.sleep_time_waiting_for_tws_response)
        else:
            if variables.flag_debug_mode:
                print(
                    "Successfully got answer for market data from TWS, ",
                    variables.ask_price[reqId],
                    variables.bid_price[reqId],
                )
            # variables.app.cancelMktData(reqId)
            return (variables.ask_price[reqId], variables.bid_price[reqId])

    # raise if error checking loop count maxed out (contract details not obtained)
    if err_check == 1:
        if variables.flag_debug_mode:
            print(
                f"Unable to found bid and ask for reqId {reqId}, Ask: {variables.ask_price[reqId]} and Bid: {variables.bid_price[reqId]}"
            )
        return (variables.ask_price[reqId], variables.bid_price[reqId])  # (None, None)


# Method to update prices in market watch
def update_prices_in_market_watch___reference_price_in_db_and_order_book__cas_table():
    # Get latest combo prices
    prices_unique_id = calculate_combo_prices()

    if variables.screen:
        try:
            variables.screen.update_prices_market_watch(prices_unique_id)
            # variables.screen.update_orders_book_table_watchlist_changed()

            update_reference_price_in_db_and_order_book(prices_unique_id)

            calculate_values_and_update_cas_table(prices_unique_id)

            # variables.screen.screen_cas_obj.update_cas_values_depends_on_current_price(prices_unique_id)

        except Exception as e:
            if variables.flag_debug_mode:
                print(e)
                print(
                    "Exception in update_prices_in_market_watch_and_reference_price_in_db"
                )


# Method to get updated account alues
def get_updated_account_values():
    # Get all account ids
    for account_id in variables.current_session_accounts:
        # Get reqID
        req_id = variables.nextorderId
        variables.nextorderId += 1

        # map req id to account id
        variables.map_req_id_to_account_id[req_id] = account_id

        # append
        variables.pnl_single_req_ids.append(req_id)

        # Request daily PNL data
        variables.app.reqPnL(req_id, account_id, "")

        # Get all conids from dict
        """for con_id in variables.map_con_id_to_contract:
            # Get reqID
            req_id = variables.nextorderId
            variables.nextorderId += 1

            # map req id to account id
            variables.map_req_id_to_account_id_and_cond_id[req_id] = {'Account ID': account_id, 'Con ID': con_id}

            # Request tickers PNL data
            variables.app.reqPnLSingle(req_id, account_id, "", con_id)"""

        # Request account update values
        variables.app.reqAccountUpdates(True, account_id)

        # Set value to false
        variables.flag_account_update_ended[account_id] = False

        # Init
        counter = 0

        # Wait while app get data
        while counter < 4 and variables.flag_account_update_ended[account_id] == False:
            # Sleep timer
            time.sleep(0.5)

            # Increment value of time counter
            counter += 0.5

        # Request account update values
        variables.app.reqAccountUpdates(False, account_id)

        # Update table
        variables.screen.screen_accounts_obj.update_accounts_table()

    # Get all account ids
    for account_id in variables.current_session_accounts:
        from com.screen_accounts_tab import run_risk_management_checks

        # run risk management checks
        run_risk_management_checks(account_id, flag_liquidation_check=True)


# Calculates the prices of all the combos, and returns them in a dict {unique_id : {BUY: , SELL, total_spread:}
def calculate_combo_prices():
    # conid_mktdata_subscription_dict = {}
    # con_id_to_req_id_dict = {}
    # unique_id_to_combo_obj = {}

    # Making a local copy of unique_id_to_combo_obj
    local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

    # Contains all the unique_id and prices, {unique_id : {BUY: , SELL, total_spread:}
    prices_dict = {}

    actual_prices_dict = {}

    # Process each combo_obj one by one.
    for unique_id, combo_obj in local_unique_id_to_combo_obj.items():
        # Buy legs and Sell legs
        buy_legs = combo_obj.buy_legs
        sell_legs = combo_obj.sell_legs

        # Setting current Price to 0
        price_of_buying, price_of_selling, ba_spread = 0, 0, 0

        # Initiliazing total abs cost variable
        total_abs_cost_value = 0
        # Is price for any leg None?, if so se bid ask spread for combo = None
        is_buy_price_none = False
        is_sell_price_none = False

        # Processing "Buy" Legs to calculate prices
        for leg_obj in buy_legs:
            quantity = int(leg_obj.quantity)
            con_id = leg_obj.con_id

            # Multiplier/Lot size
            if leg_obj.multiplier is None:
                multiplier = 1
            else:
                multiplier = int(leg_obj.multiplier)

            try:
                req_id = variables.con_id_to_req_id_dict[con_id]
                bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]

                if bid == None:
                    is_sell_price_none = True
                    bid = 0
                else:
                    bid = float(bid)

                if ask == None:
                    is_buy_price_none = True
                    ask = 0
                else:
                    ask = float(ask)

            except Exception as e:
                # Print to console:
                if variables.flag_debug_mode:
                    print(f"Exception in Price {e}")
                continue
            # BUy combo: buy combo price
            # leg buy aapl
            # appl buy ulti
            # ask,

            ba_spread += abs(ask - bid) * quantity * multiplier
            price_of_buying += ask * quantity * multiplier
            price_of_selling -= bid * quantity * multiplier

            # Summing price of leg * lots of leg * multiplier of leg
            total_abs_cost_value += abs(((ask + bid) / 2) * quantity * multiplier)

        # Processing "Sell" Legs to calculate prices
        for leg_obj in sell_legs:
            quantity = int(leg_obj.quantity)
            con_id = leg_obj.con_id

            # Multiplier/Lot size
            if leg_obj.multiplier is None:
                multiplier = 1
            else:
                multiplier = int(leg_obj.multiplier)

            try:
                req_id = variables.con_id_to_req_id_dict[con_id]

                bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]

                if bid == None:
                    is_buy_price_none = True
                    bid = 0
                else:
                    bid = float(bid)

                if ask == None:
                    is_sell_price_none = True
                    ask = 0
                else:
                    ask = float(ask)

            except Exception as e:
                # Print to console:
                if variables.flag_debug_mode:
                    print(f"Exception in Price {e}")
                continue

            ba_spread += abs(ask - bid) * quantity * multiplier
            price_of_buying -= bid * quantity * multiplier
            price_of_selling += ask * quantity * multiplier

            # Summing price of leg * lots of leg * multiplier of leg
            total_abs_cost_value += abs(((ask + bid) / 2) * quantity * multiplier)

        # Covert Price up to 2 decimals
        price_of_buying = int(price_of_buying * 100) / 100
        price_of_selling = int(price_of_selling * 100) / 100
        ba_spread = int(ba_spread * 100) / 100

        price_of_selling = -1 * price_of_selling

        # If any value was non for combo Show price as None
        if is_sell_price_none:
            price_of_selling = None
            ba_spread = None

        if is_buy_price_none:
            price_of_buying = None
            ba_spread = None

        actual_prices_dict[unique_id] = {
            "BUY": price_of_buying,
            "SELL": price_of_selling,
            "Spread": ba_spread,
            "Total Abs Cost": round(total_abs_cost_value, 2),
        }

        ########## Testing: Start ################
        # KARAN(CHANGE) TESTING
        if variables.flag_simulate_prices:
            buy_sell_csv = pd.read_csv(variables.buy_sell_csv)

            for _, row in buy_sell_csv.iterrows():
                try:
                    if unique_id == int(row["Unique ID"]):
                        price_of_buying = float(row["BUY"])
                        price_of_selling = float(row["SELL"])
                        ba_spread = abs(price_of_buying - price_of_selling)

                except Exception as e:
                    price_of_buying = None
                    price_of_selling = None
                    ba_spread = None

                    # Print to console:
                    if variables.flag_debug_mode:
                        print(f"Exception in Price, Exp: {e}")
                    continue

        ########## Testing : End ################

        prices_dict[unique_id] = {
            "BUY": price_of_buying,
            "SELL": price_of_selling,
            "Spread": ba_spread,
            "Total Abs Cost": round(total_abs_cost_value, 2),
        }

    # Make it available in variables
    variables.unique_id_to_prices_dict = prices_dict

    variables.unique_id_to_actual_prices_dict = actual_prices_dict

    # print(prices_dict)
    return prices_dict


# Method to request historical data
def request_historical_price_data_for_contract(
    contract, bar_size, duration_size, what_to_show, req_id=None, cas_app=False
):
    # If req_id was not provided, getting request ID
    if req_id == None:
        # Getting req_id
        reqId = variables.nextorderId
        variables.nextorderId += 1
    else:
        reqId = req_id

    # Init
    variables.req_mkt_data_end[reqId] = False

    # Map req_id to dataframe containing historical_data
    variables.map_req_id_to_historical_data_dataframe[reqId] = pd.DataFrame(
        columns=variables.historical_data_columns
    )

    # Static for reqHistoricalData
    end_date_time = ""
    duration_string = duration_size
    bar_size_setting = bar_size
    use_rth = variables.flag_use_rth
    format_date = 1
    keep_up_to_date = False

    # Error Received
    variables.req_error[reqId] = False

    # Which TWS API app to use?
    if cas_app:
        # Send request via CAS APP
        variables.cas_app.reqHistoricalData(
            reqId,
            contract,
            end_date_time,
            duration_string,
            bar_size_setting,
            what_to_show,
            use_rth,
            format_date,
            keep_up_to_date,
            [],
        )
    else:
        # Send request Via Main App
        variables.app.reqHistoricalData(
            reqId,
            contract,
            end_date_time,
            duration_string,
            bar_size_setting,
            what_to_show,
            use_rth,
            format_date,
            keep_up_to_date,
            [],
        )


# Method to request historical data for price chart
def request_historical_price_data_of_combination_for_chart(
    unique_id, bar_size, chart_size
):
    # Combination Object for unique ID
    conbination_object = variables.unique_id_to_combo_obj[unique_id]

    # Buy and sell Legs
    buy_legs = conbination_object.buy_legs
    sell_legs = conbination_object.sell_legs
    all_legs = buy_legs + sell_legs

    # Formatting Chart Duration, for TWS
    if chart_size == "12 Months":
        chart_size = "12 M"
    else:
        chart_size = chart_size[:3]

    req_id_list = []

    # Fetch ask for legs we're buying
    # Fetch bid for legs we're selling
    for leg_obj in all_legs:
        # Getting req_id
        reqId = variables.nextorderId
        variables.nextorderId += 1

        # Init
        contract = leg_obj.contract

        req_id_list.append(reqId)

        if leg_obj.action == "BUY":
            what_to_show = "ASK"
        else:
            what_to_show = "BID"

        request_historical_price_data_for_contract(
            contract, bar_size, chart_size, what_to_show, reqId
        )

    # To avoid Divide by Zero Error
    counter = 1
    while (
        int(
            variables.wait_time_for_historical_data
            / (counter * variables.sleep_time_waiting_for_tws_response)
        )
        >= 1
    ):
        # If reqHistorical Data ended for all the reqId
        if all([variables.req_mkt_data_end[req_id] for req_id in req_id_list]) or any(
            [variables.req_error[req_id] for req_id in req_id_list]
        ):
            break

        # Sleep for sleep_time_waiting_for_tws_response
        time.sleep(variables.sleep_time_waiting_for_tws_response)

        # Increase Counter
        counter += 1

    # Process Data,
    all_data_frames = [
        variables.map_req_id_to_historical_data_dataframe[req_id]
        for req_id in req_id_list
    ]

    # If data is not present
    for i, historical_dataframe in enumerate(all_data_frames):
        if (
            historical_dataframe is None
            or len(historical_dataframe.index) == 0
            or historical_dataframe.empty
        ):
            return None

    merged_df = all_data_frames[0]
    for i, df in enumerate(all_data_frames[1:]):
        merged_df = pd.merge(
            merged_df, df, on="Time", how="inner", suffixes=(f"", f" {i + 1}")
        )

        # file_name = f"0Merged {i}.csv"
        # merged_df.to_csv(f"Data/csv/{file_name}", index = False)

    # Dropping nan values
    merged_df = merged_df.dropna()

    # Creating Columns for new merged dataframe
    merged_df_columns = ["Time"]
    for i in range(len(all_data_frames)):
        merged_df_columns.append(f"Open {i + 1}")
        merged_df_columns.append(f"Close {i + 1}")
        merged_df_columns.append(f"Volume {i + 1}")

    # Setting columns in merged_df
    merged_df.columns = merged_df_columns

    # Multipling Factors to calculatr the historical price of combination
    factors = []

    for leg_obj in all_legs:
        quantity = int(leg_obj.quantity)
        multiplier = leg_obj.multiplier

        if (multiplier == None) or (multiplier == "None"):
            multiplier = 1
        else:
            multiplier = int(multiplier)

        if leg_obj.action == "BUY":
            factors.append(quantity * multiplier)
        else:
            factors.append(-1 * quantity * multiplier)

    merged_df["Combination Open"] = merged_df.apply(
        lambda row: formula_to_calculate_price_for_historical_data(
            row, "Open", all_data_frames, factors
        ),
        axis=1,
    )
    merged_df["Combination Close"] = merged_df.apply(
        lambda row: formula_to_calculate_price_for_historical_data(
            row, "Close", all_data_frames, factors
        ),
        axis=1,
    )

    # all_legs = buy_legs + sell_legs
    # counter = 1
    # for req_id, leg_obj in zip(req_id_list, all_legs):
    #     # print(f"Req_id : {req_id}  {leg_obj.action}, {leg_obj.symbol}, {leg_obj.sec_type}, {leg_obj.exchange}")
    #     # print(variables.map_req_id_to_historical_data_dataframe[req_id])
    #     # print("\n" * 2)
    #
    #     data_frame_csv = variables.map_req_id_to_historical_data_dataframe[req_id]
    #     if not os.path.exists("Data/csv"):
    #         os.makedirs("Data/csv")
    #     file_name = f"{current_time} Leg_{counter} {leg_obj.action} {leg_obj.symbol} {leg_obj.sec_type} {leg_obj.exchange}.csv"
    #     data_frame_csv.to_csv(f"Data/csv/{file_name}", index = False)
    #     counter += 1

    ##### Make data Frames with OHLC for Plotting #######

    # Create new DataFrame with desired columns
    ohlc_df = merged_df[["Time", "Combination Open", "Combination Close"]].copy()

    # Renaming Columns Name
    ohlc_df.columns = ["Time", "Open", "Close"]

    # Compute High and Low columns
    ohlc_df["High"] = ohlc_df[["Open", "Close"]].max(axis=1)
    ohlc_df["Low"] = ohlc_df[["Open", "Close"]].min(axis=1)

    # Reorder columns
    ohlc_df = ohlc_df[["Time", "Open", "High", "Low", "Close"]]

    # Convert 'Date' column to datetime
    ohlc_df["Time"] = pd.to_datetime(ohlc_df["Time"])

    # Sort Values by time
    ohlc_df = ohlc_df.sort_values(by="Time")

    # Set 'Date' column as index
    ohlc_df.set_index("Time", inplace=True)

    return ohlc_df


# Method to calculate combo prices
def formula_to_calculate_price_for_historical_data(
    row, open_or_close, all_data_frames, factors
):
    value = 0

    for leg_no in range(len(all_data_frames)):
        column_name = f"{open_or_close} {leg_no + 1}"

        value += float(row[column_name]) * factors[leg_no]
    return value


# Calulates latest Values and update the CAS table
def calculate_values_and_update_cas_table(prices_unique_id):
    # List of update values
    cas_table_update_values = []
    cas_condition_table_update_values = []

    # N days High And Low
    long_term_high_low = copy.deepcopy(variables.map_unique_id_to_long_term_high_low)

    # HV Related Column
    hv_related_values = copy.deepcopy(variables.map_unique_id_to_hv_related_values)

    # Days Open, High Low
    intraday_open_high_low = copy.deepcopy(variables.map_unique_id_to_intraday_high_low)

    # Volume Related columns
    volume_related_column_values = copy.deepcopy(
        variables.map_unique_id_to_volume_related_fields
    )

    # Both Price and Volume Related columns
    support_resistance_and_relative_fields_values = copy.deepcopy(
        variables.map_unique_id_to_support_resistance_and_relative_fields
    )

    """for ind in hv_related_values:

        print(long_term_high_low[ind])
    print('*'*100)"""

    if variables.flag_debug_mode:
        print(f"\n\nInside update cas table(Long Term): {long_term_high_low}")
        print(f"Inside update cas table(IntraTerm): {intraday_open_high_low}")
        print(f"Inside update cas table(HV Term): {hv_related_values}")
        print(
            f"Inside update cas table(Volume Related Columns): {volume_related_column_values}"
        )
        print(
            (
                f"Inside update cas table(Both Price and Volume Related Columns): {support_resistance_and_relative_fields_values}"
            )
        )

    try:
        for unique_id, prices in prices_unique_id.items():
            try:
                # N-Day High Low
                if unique_id in long_term_high_low:
                    n_day_high = (
                        None
                        if long_term_high_low[unique_id]["N-Day High"] == "N/A"
                        else long_term_high_low[unique_id]["N-Day High"]
                    )
                    n_day_low = (
                        None
                        if long_term_high_low[unique_id]["N-Day Low"] == "N/A"
                        else long_term_high_low[unique_id]["N-Day Low"]
                    )
                    atr = (
                        None
                        if long_term_high_low[unique_id]["ATR"] == "N/A"
                        else long_term_high_low[unique_id]["ATR"]
                    )
                    last_close_price = (
                        None
                        if long_term_high_low[unique_id]["Close Price"] == "N/A"
                        else long_term_high_low[unique_id]["Close Price"]
                    )
                    correlation = (
                        None
                        if long_term_high_low[unique_id]["Correlation"] == "N/A"
                        else long_term_high_low[unique_id]["Correlation"]
                    )
                    last_day_close_price_for_leg_list = (
                        "N/A"
                        if long_term_high_low[unique_id][
                            "Last Day Close Price For Legs"
                        ]
                        == "N/A"
                        else long_term_high_low[unique_id][
                            "Last Day Close Price For Legs"
                        ]
                    )
                    beta_value = (
                        "N/A"
                        if long_term_high_low[unique_id]["Beta"] == "N/A"
                        else f"{(long_term_high_low[unique_id]['Beta']):,.4f}"
                    )
                    avg_chg_in_price_for_n_days = (
                        None
                        if long_term_high_low[unique_id][
                            "Avg chg In Price For Last N days"
                        ]
                        == "N/A"
                        else long_term_high_low[unique_id][
                            "Avg chg In Price For Last N days"
                        ]
                    )
                else:
                    (
                        n_day_high,
                        n_day_low,
                        atr,
                        last_close_price,
                        correlation,
                        last_day_close_price_for_leg_list,
                        beta_value,
                    ) = (None, None, None, None, None, "N/A", "N/A")
                    avg_chg_in_price_for_n_days = None

            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Exception in getting long term values, Exp: {e}")

                (
                    n_day_high,
                    n_day_low,
                    atr,
                    last_close_price,
                    correlation,
                    last_day_close_price_for_leg_list,
                    beta_value,
                ) = (None, None, None, None, None, "N/A", "N/A")
                avg_chg_in_price_for_n_days = None

            try:
                # Current Day Open High Low
                if unique_id in intraday_open_high_low:
                    day_open = (
                        None
                        if intraday_open_high_low[unique_id]["1-Day Open"] == "N/A"
                        else intraday_open_high_low[unique_id]["1-Day Open"]
                    )
                    day_high = (
                        None
                        if intraday_open_high_low[unique_id]["1-Day High"] == "N/A"
                        else intraday_open_high_low[unique_id]["1-Day High"]
                    )
                    day_low = (
                        None
                        if intraday_open_high_low[unique_id]["1-Day Low"] == "N/A"
                        else intraday_open_high_low[unique_id]["1-Day Low"]
                    )
                    low_timestamp = intraday_open_high_low[unique_id][
                        "Lowest Value TimeStamp"
                    ]
                    high_timestamp = intraday_open_high_low[unique_id][
                        "Highest Value TimeStamp"
                    ]
                    intraday_support = (
                        "N/A"
                        if intraday_open_high_low[unique_id]["Intraday Support"]
                        == "N/A"
                        else f"{intraday_open_high_low[unique_id]['Intraday Support']:,.2f}"
                    )
                    intraday_resistance = (
                        "N/A"
                        if intraday_open_high_low[unique_id]["Intraday Resistance"]
                        == "N/A"
                        else f"{intraday_open_high_low[unique_id]['Intraday Resistance']:,.2f}"
                    )
                    intraday_support_count = (
                        "N/A"
                        if intraday_open_high_low[unique_id]["Intraday Support Count"]
                        == "N/A"
                        else f"{intraday_open_high_low[unique_id]['Intraday Support Count']:,}"
                    )
                    intraday_resistance_count = (
                        "N/A"
                        if intraday_open_high_low[unique_id][
                            "Intraday Resistance Count"
                        ]
                        == "N/A"
                        else f"{intraday_open_high_low[unique_id]['Intraday Resistance Count']:,}"
                    )
                    current_day_open_for_legs_list = (
                        "N/A"
                        if intraday_open_high_low[unique_id][
                            "Current Day Open Price For Legs"
                        ]
                        == "N/A"
                        else intraday_open_high_low[unique_id][
                            "Current Day Open Price For Legs"
                        ]
                    )
                    highest_price_comparison_intraday = (
                        "N/A"
                        if intraday_open_high_low[unique_id]["Highest Price Comparison"]
                        == "N/A"
                        else str(
                            intraday_open_high_low[unique_id][
                                "Highest Price Comparison"
                            ]
                        )
                    )
                    lowest_price_comparison_intraday = (
                        "N/A"
                        if intraday_open_high_low[unique_id]["Lowest Price Comparison"]
                        == "N/A"
                        else str(
                            intraday_open_high_low[unique_id]["Lowest Price Comparison"]
                        )
                    )
                    intraday_price_range_ratio = (
                        "N/A"
                        if intraday_open_high_low[unique_id][
                            "Intraday Price Range Ratio"
                        ]
                        == "N/A"
                        else f"{intraday_open_high_low[unique_id]['Intraday Price Range Ratio']:,.2f}"
                    )
                    price_at_highest_combo_price_time_for_legs_list = (
                        "N/A"
                        if intraday_open_high_low[unique_id][
                            "Current Day Highest Price For Legs"
                        ]
                        == "N/A"
                        else intraday_open_high_low[unique_id][
                            "Current Day Highest Price For Legs"
                        ]
                    )
                    price_at_lowest_combo_price_time_for_legs_list = (
                        "N/A"
                        if intraday_open_high_low[unique_id][
                            "Current Day Lowest Price For Legs"
                        ]
                        == "N/A"
                        else intraday_open_high_low[unique_id][
                            "Current Day Lowest Price For Legs"
                        ]
                    )
                    values_to_calculate_change_from_open_value = (
                        "N/A"
                        if intraday_open_high_low[unique_id][
                            "Current Day Current Candle For Legs"
                        ]
                        == "N/A"
                        else intraday_open_high_low[unique_id][
                            "Current Day Current Candle For Legs"
                        ]
                    )
                    day_open_or_current_candle_price = (
                        "N/A"
                        if intraday_open_high_low[unique_id][
                            "Day Open Or Current Candle"
                        ]
                        == "N/A"
                        else intraday_open_high_low[unique_id][
                            "Day Open Or Current Candle"
                        ]
                    )
                    support_price_ration_in_range_intraday = (
                        "N/A"
                        if intraday_open_high_low[unique_id]["Price Support Ratio"]
                        == "N/A"
                        else f"{intraday_open_high_low[unique_id]['Price Support Ratio']:,.4f}"
                    )
                    resistance_price_ration_in_range_intraday = (
                        "N/A"
                        if intraday_open_high_low[unique_id]["Price Resistance Ratio"]
                        == "N/A"
                        else f"{intraday_open_high_low[unique_id]['Price Resistance Ratio']:,.4f}"
                    )
                else:
                    (
                        day_open,
                        day_high,
                        day_low,
                        low_timestamp,
                        high_timestamp,
                        price_at_highest_combo_price_time_for_legs_list,
                        price_at_lowest_combo_price_time_for_legs_list,
                    ) = (None, None, None, "N/A", "N/A", "N/A", "N/A")
                    (
                        intraday_support,
                        intraday_resistance,
                        intraday_support_count,
                        intraday_resistance_count,
                        current_day_open_for_legs_list,
                    ) = ("N/A", "N/A", "N/A", "N/A", "N/A")
                    (
                        highest_price_comparison_intraday,
                        lowest_price_comparison_intraday,
                        intraday_price_range_ratio,
                        values_to_calculate_change_from_open_value,
                    ) = ("N/A", "N/A", "N/A", "N/A")
                    (
                        day_open_or_current_candle_price,
                        support_price_ration_in_range_intraday,
                        resistance_price_ration_in_range_intraday,
                    ) = ("N/A", "N/A", "N/A")
            except Exception as e:
                if variables.flag_debug_mode:
                    print(f"Exception in getting long term values, Exp: {e}")

                (
                    day_open,
                    day_high,
                    day_low,
                    low_timestamp,
                    high_timestamp,
                    price_at_highest_combo_price_time_for_legs_list,
                    price_at_lowest_combo_price_time_for_legs_list,
                ) = (None, None, None, "N/A", "N/A", "N/A", "N/A")
                (
                    intraday_support,
                    intraday_resistance,
                    intraday_support_count,
                    intraday_resistance_count,
                    current_day_open_for_legs_list,
                ) = ("N/A", "N/A", "N/A", "N/A", "N/A")
                (
                    highest_price_comparison_intraday,
                    lowest_price_comparison_intraday,
                    intraday_price_range_ratio,
                    values_to_calculate_change_from_open_value,
                ) = ("N/A", "N/A", "N/A", "N/A")
                (
                    day_open_or_current_candle_price,
                    support_price_ration_in_range_intraday,
                    resistance_price_ration_in_range_intraday,
                ) = ("N/A", "N/A", "N/A")

            try:
                # HV Related Coulmns
                if unique_id in hv_related_values:
                    # HV Val for the unique ID
                    data = hv_related_values[unique_id]
                    hv_value = (
                        "N/A" if data["H. V."] == "N/A" else f"{data['H. V.']:,.2f}%"
                    )
                    hv_value_without_annualized = (
                        "N/A"
                        if data["H.V. Without Annualized"] == "N/A"
                        else data["H.V. Without Annualized"]
                    )
                    candle_volatility_val = (
                        "N/A"
                        if data["Candle Volatility"] == "N/A"
                        else data["Candle Volatility"]
                    )

                else:
                    (hv_value, candle_volatility_val, hv_value_without_annualized) = (
                        "N/A",
                        "N/A",
                        "N/A",
                    )
            except Exception as e:
                (hv_value, candle_volatility_val, hv_value_without_annualized) = (
                    "N/A",
                    "N/A",
                    "N/A",
                )

                if variables.flag_debug_mode:
                    print(e)

            try:
                # Volume Related Coulmns
                if unique_id in volume_related_column_values:
                    # Volume Related Values for the unique ID
                    data = volume_related_column_values[unique_id]

                    mean_of_net_volume = (
                        "N/A"
                        if data["Mean of Net Volume"] == "N/A"
                        else f"{data['Mean of Net Volume']:,.2f}"
                    )
                    std_plus_1 = (
                        "N/A" if data["STD +1"] == "N/A" else f"{data['STD +1']:,.2f}"
                    )
                    std_negative_1 = (
                        "N/A" if data["STD -1"] == "N/A" else f"{data['STD -1']:,.2f}"
                    )
                    std_plus_2 = (
                        "N/A" if data["STD +2"] == "N/A" else f"{data['STD +2']:,.2f}"
                    )
                    std_negative_2 = (
                        "N/A" if data["STD -2"] == "N/A" else f"{data['STD -2']:,.2f}"
                    )
                    std_plus_3 = (
                        "N/A" if data["STD +3"] == "N/A" else f"{data['STD +3']:,.2f}"
                    )
                    std_negative_3 = (
                        "N/A" if data["STD -3"] == "N/A" else f"{data['STD -3']:,.2f}"
                    )
                else:
                    (
                        mean_of_net_volume,
                        std_plus_1,
                        std_negative_1,
                        std_plus_2,
                        std_negative_2,
                        std_plus_3,
                        std_negative_3,
                    ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")
            except Exception as e:
                (
                    mean_of_net_volume,
                    std_plus_1,
                    std_negative_1,
                    std_plus_2,
                    std_negative_2,
                    std_plus_3,
                    std_negative_3,
                ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

            try:
                # Both price and Volume Related Coulmns
                if unique_id in support_resistance_and_relative_fields_values:
                    # Both price and Volume Related value for the unique ID
                    data = support_resistance_and_relative_fields_values[unique_id]

                    resistance = (
                        "N/A"
                        if data["Resistance"] == "N/A"
                        else f"{data['Resistance']:,.2f}"
                    )
                    support = (
                        "N/A" if data["Support"] == "N/A" else f"{data['Support']:,.2f}"
                    )
                    resitance_count = (
                        "N/A"
                        if data["Resistance Count"] == "N/A"
                        else f"{data['Resistance Count']:,}"
                    )
                    support_count = (
                        "N/A"
                        if data["Support Count"] == "N/A"
                        else f"{data['Support Count']:,}"
                    )
                    avg_of_abs_changes_in_prices_for_lookback = (
                        "N/A"
                        if data["Avg of Abs Changes in Prices"] == "N/A"
                        else data["Avg of Abs Changes in Prices"]
                    )
                    relative_atr_derivative = (
                        "N/A"
                        if data["Relative ATR Derivative"] == "N/A"
                        else f"{data['Relative ATR Derivative']:,.2f}"
                    )
                    avg_bid_ask_spread = (
                        None
                        if data["Average Bid Ask"] == "N/A"
                        else data["Average Bid Ask"]
                    )
                    relative_atr_on_positive_candles = (
                        "N/A"
                        if data["Relative ATR on Positive Candles"] == "N/A"
                        else f"{data['Relative ATR on Positive Candles']:,.2f}"
                    )
                    relative_atr_on_negative_candles = (
                        "N/A"
                        if data["Relative ATR on Negative Candles"] == "N/A"
                        else f"{data['Relative ATR on Negative Candles']:,.2f}"
                    )
                    relative_volume_derivative = (
                        "N/A"
                        if data["Relative Volume Derivative"] == "N/A"
                        else f"{data['Relative Volume Derivative']:,.2f}"
                    )
                    relative_volume_on_positive_candles = (
                        "N/A"
                        if data["Relative Volume on Positive Candles"] == "N/A"
                        else f"{data['Relative Volume on Positive Candles']:,.2f}"
                    )
                    relative_volume_on_negative_candles = (
                        "N/A"
                        if data["Relative Volume on Negative Candles"] == "N/A"
                        else f"{data['Relative Volume on Negative Candles']:,.2f}"
                    )
                    relative_atr = (
                        "N/A" if data["Relative ATR"] == "N/A" else data["Relative ATR"]
                    )
                    relative_volume = (
                        "N/A"
                        if data["Relative Volume"] == "N/A"
                        else data["Relative Volume"]
                    )
                    relative_volume_last_n_minutes = (
                        "N/A"
                        if data["Relative Volume Last N Minutes"] == "N/A"
                        else data["Relative Volume Last N Minutes"]
                    )
                    relative_change_last_n_minutes = (
                        "N/A"
                        if data["Relative Change Last N Minutes"] == "N/A"
                        else data["Relative Change Last N Minutes"]
                    )
                    support_price_ration_in_range = (
                        "N/A"
                        if data["Price Support Ratio"] == "N/A"
                        else f"{data['Price Support Ratio']:,.4f}"
                    )
                    resistance_price_ration_in_range = (
                        "N/A"
                        if data["Price Resistance Ratio"] == "N/A"
                        else f"{data['Price Resistance Ratio']:,.4f}"
                    )
                    volume_magnet = (
                        "N/A"
                        if data["Volume Magnet"] == "N/A"
                        else f"{data['Volume Magnet']:,.2f}"
                    )
                    relative_atr_lower = (
                        "N/A"
                        if data["Relative ATR Lower"] == "N/A"
                        else f"{data['Relative ATR Lower']:,.2f}"
                    )
                    relative_atr_higher = (
                        "N/A"
                        if data["Relative ATR Higher"] == "N/A"
                        else data["Relative ATR Higher"]
                    )
                    relative_volume_lower = (
                        "N/A"
                        if data["Relative Volume on Lower Range"] == "N/A"
                        else data["Relative Volume on Lower Range"]
                    )
                    relative_volume_higher = (
                        "N/A"
                        if data["Relative Volume on Higher Range"] == "N/A"
                        else data["Relative Volume on Higher Range"]
                    )

                else:
                    (
                        resistance,
                        support,
                        resitance_count,
                        support_count,
                        avg_of_abs_changes_in_prices_for_lookback,
                        relative_atr,
                        relative_volume,
                        relative_volume_last_n_minutes,
                        relative_change_last_n_minutes,
                    ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

                    (
                        relative_atr_derivative,
                        relative_atr_on_positive_candles,
                        relative_atr_on_negative_candles,
                        relative_volume_derivative,
                        relative_volume_on_positive_candles,
                        relative_volume_on_negative_candles,
                        avg_bid_ask_spread,
                        support_price_ration_in_range,
                        resistance_price_ration_in_range,
                        volume_magnet,
                    ) = (
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                    )

                    (
                        relative_atr_lower,
                        relative_atr_higher,
                        relative_volume_lower,
                        relative_volume_higher,
                    ) = ("N/A", "N/A", "N/A", "N/A")

            except Exception as e:
                if variables.flag_debug_mode:
                    print(e)

                (
                    resistance,
                    support,
                    resitance_count,
                    support_count,
                    avg_of_abs_changes_in_prices_for_lookback,
                    relative_atr,
                    relative_volume,
                    relative_volume_last_n_minutes,
                    relative_change_last_n_minutes,
                ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

                (
                    relative_atr_derivative,
                    relative_atr_on_positive_candles,
                    relative_atr_on_negative_candles,
                    relative_volume_derivative,
                    relative_volume_on_positive_candles,
                    relative_volume_on_negative_candles,
                    avg_bid_ask_spread,
                    support_price_ration_in_range,
                    resistance_price_ration_in_range,
                    volume_magnet,
                ) = (
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                    "N/A",
                )

                (
                    relative_atr_lower,
                    relative_atr_higher,
                    relative_volume_lower,
                    relative_volume_higher,
                ) = ("N/A", "N/A", "N/A", "N/A")

            # update the value of the 'Sell Price' column of 'Unique ID' to SELL price
            sell_price = "N/A" if prices["SELL"] == None else f"{prices['SELL']:,.2f}"

            # update the value of the 'Buy Price' column of 'Unique ID' to BUY price
            buy_price = "N/A" if prices["BUY"] == None else f"{prices['BUY']:,.2f}"

            # update the value of the 'Total Absolute Cost' column of 'Unique ID' to total_abs_cost_value
            total_abs_cost_value = (
                "N/A" if prices["Total Abs Cost"] == None else prices["Total Abs Cost"]
            )

            try:
                # Calculate average price of combo
                avg_price_combo = (prices["SELL"] + prices["BUY"]) / 2

                # Calculate bid ask spread
                bid_ask_spread = prices["BUY"] - prices["SELL"]
            except Exception as e:
                # set value to none
                avg_price_combo = None
                bid_ask_spread = None

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Inside CAS Price Update: {prices['SELL']=} {prices['BUY']=}, Exception: {e} "
                    )

            # Calcualte bid ask related columns
            try:
                # check if values are valid
                if avg_chg_in_price_for_n_days not in [
                    0,
                    None,
                    "N/A",
                ] and avg_bid_ask_spread not in [None, "N/A"]:
                    avg_bid_ask_div_by_avg_chg = (
                        avg_bid_ask_spread / avg_chg_in_price_for_n_days
                    )

                    # check if value is valid and if yes then format it
                    if avg_bid_ask_div_by_avg_chg not in [None, "N/A", "None"]:
                        avg_bid_ask_div_by_avg_chg = (
                            f"{avg_bid_ask_div_by_avg_chg:,.2f}"
                        )

                else:
                    # Set value to N/A
                    avg_bid_ask_div_by_avg_chg = "N/A"

                # check if values are valid
                if avg_chg_in_price_for_n_days not in [
                    0,
                    None,
                    "N/A",
                ] and bid_ask_spread not in [None, "N/A"]:
                    bid_ask_div_by_avg_chg = (
                        bid_ask_spread / avg_chg_in_price_for_n_days
                    )

                    # check if value is valid and if yes then format it
                    if bid_ask_div_by_avg_chg not in [None, "N/A", "None"]:
                        bid_ask_div_by_avg_chg = f"{bid_ask_div_by_avg_chg:,.2f}"

                else:
                    # Set value to N/A
                    bid_ask_div_by_avg_chg = "N/A"

            except Exception as e:
                # Set value to N/A
                avg_bid_ask_div_by_avg_chg = "N/A"
                bid_ask_div_by_avg_chg = "N/A"

            # Calculate change open dollar value
            if day_open not in ["N/A", None, "None"] and avg_price_combo not in [
                "N/A",
                None,
                "None",
            ]:
                # Calcualtion for change open dollar value
                chg_open = avg_price_combo - day_open

                # check value is valid
                if chg_open not in ["N/A", None, "None"]:
                    chg_open = f"{chg_open:,.2f}"

            else:
                chg_open = "N/A"

            # Calculate change close dollar value
            if last_close_price not in [
                "N/A",
                None,
                "None",
            ] and avg_price_combo not in ["N/A", None, "None"]:
                # Calcualtion for change close dollar value
                chg_close = avg_price_combo - last_close_price

                # check value is valid
                if chg_close not in ["N/A", None, "None"]:
                    chg_close = f"{chg_close:,.2f}"

            else:
                chg_close = "N/A"

            # Calculate Relative volume div by relative cange for last n minutes in lookback days
            if (
                relative_volume_last_n_minutes != "N/A"
                and relative_change_last_n_minutes not in ["N/A", 0]
            ):
                # Relative volume div by relative cange for last n minutes in lookback days
                rel_volume_div_by_rel_chg_last_n_minutes = (
                    relative_volume_last_n_minutes / relative_change_last_n_minutes
                )

                # Format value of change from lowest price percent
                rel_volume_div_by_rel_chg_last_n_minutes = (
                    f"{rel_volume_div_by_rel_chg_last_n_minutes:,.2f}"
                )

            else:
                # set value to N/A
                rel_volume_div_by_rel_chg_last_n_minutes = "N/A"

            # Init
            change_from_open_percent = "N/A"
            change_from_high_percent = "N/A"
            change_from_low_percent = "N/A"
            change_from_open_for_rel_chg = "N/A"

            # Getting combo objects mapped to unique ids
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )

            # Update From Open if the flag_weighted_change_in_price is False
            if (
                (avg_price_combo != None)
                and (day_open != None)
                and not variables.flag_weighted_change_in_price
            ):
                # Change from open percent
                change_from_open_percent = math.log(
                    abs(avg_price_combo) + 1
                ) * math.copysign(1, avg_price_combo) - math.log(
                    abs(day_open) + 1
                ) * math.copysign(1, day_open)

            # Update From Open if the flag_weighted_change_in_price is True
            if (
                current_day_open_for_legs_list != "N/A"
                and variables.flag_weighted_change_in_price
            ):
                # print(f"Unique ID: {unique_id} Change From Open")
                change_from_open_percent = calc_weighted_change_legs_based(
                    local_unique_id_to_combo_obj[unique_id],
                    current_day_open_for_legs_list,
                )

            # Update From Open if the flag_weighted_change_in_price is False
            if (
                (avg_price_combo != None)
                and (day_open != None)
                and not variables.flag_weighted_change_in_price
            ):
                # Change from open percent
                change_from_open_for_rel_chg = math.log(
                    abs(avg_price_combo) + 1
                ) * math.copysign(1, avg_price_combo) - math.log(
                    abs(day_open_or_current_candle_price) + 1
                ) * math.copysign(1, day_open_or_current_candle_price)

            # Update From Open if the flag_weighted_change_in_price is True
            if (
                current_day_open_for_legs_list not in ["N/A", "None", None]
                and variables.flag_weighted_change_in_price
            ):
                # print(f"Unique ID: {unique_id} Change From Open")
                change_from_open_for_rel_chg = calc_weighted_change_legs_based(
                    local_unique_id_to_combo_obj[unique_id],
                    values_to_calculate_change_from_open_value,
                )  # func name ask karan

            # Calculate change from high
            if price_at_highest_combo_price_time_for_legs_list not in [
                "N/A",
                "None",
                None,
            ]:
                # Get value of change from high percent
                change_from_high_percent = calc_weighted_change_legs_based(
                    local_unique_id_to_combo_obj[unique_id],
                    price_at_highest_combo_price_time_for_legs_list,
                    unique_id=unique_id,
                )

                if change_from_high_percent not in ["N/A", "None", None]:
                    # Format value of change from highest price percent
                    change_from_high_percent = f"{change_from_high_percent * 100:,.2f}%"

            # Calculate change from low
            if price_at_lowest_combo_price_time_for_legs_list not in [
                "N/A",
                "None",
                None,
            ]:
                # Get value of change from low percent
                change_from_low_percent = calc_weighted_change_legs_based(
                    local_unique_id_to_combo_obj[unique_id],
                    price_at_lowest_combo_price_time_for_legs_list,
                    unique_id=unique_id,
                )

                if change_from_low_percent not in ["N/A", "None", None]:
                    # Format value of change from lowest price percent
                    change_from_low_percent = f"{change_from_low_percent * 100:,.2f}%"

            # Net change since market opened divided by historical volatility value
            try:
                if (
                    hv_value_without_annualized != 0
                    and hv_value_without_annualized not in ["N/A", "None", None]
                    and change_from_open_percent not in ["N/A", "None", None]
                ):
                    net_change_from_open_by_hv = round(
                        change_from_open_percent / hv_value_without_annualized, 4
                    )
                else:
                    net_change_from_open_by_hv = "N/A"
            except Exception as e:
                net_change_from_open_by_hv = "N/A"

                # Print to console:
                if variables.flag_debug_mode:
                    print(
                        f"Inside net_change_since_market_opened_divided_by_hv_value, Exception : {e}"
                    )

            # Candle volatility divided by net change since market opened
            try:
                if (
                    change_from_open_percent != 0
                    and change_from_open_percent not in ["N/A"]
                    and candle_volatility_val not in ["N/A"]
                ):
                    cv_by_net_chng_from_open = (
                        candle_volatility_val / change_from_open_percent
                    )
                    cv_by_net_chng_from_open = round(cv_by_net_chng_from_open, 4)
                else:
                    cv_by_net_chng_from_open = "N/A"
            except Exception as e:
                cv_by_net_chng_from_open = "N/A"

                # Print to console:
                if variables.flag_debug_mode:
                    print(
                        f"Inside candle_volatility_div_by_net_change_since_open_value, Exception : {e}"
                    )

            try:
                # print(f"{avg_of_abs_changes_in_prices_for_lookback=}{change_from_open_percent=}")
                if avg_of_abs_changes_in_prices_for_lookback not in [
                    0,
                    "N/A",
                    None,
                ] and change_from_open_for_rel_chg not in ["N/A", None]:
                    # Calculating Relative Change
                    relative_change_in_price = (
                        abs(change_from_open_for_rel_chg)
                        / avg_of_abs_changes_in_prices_for_lookback
                    )  # change_from_open_percent been in use for many things

                else:
                    relative_change_in_price = "N/A"

            except Exception as e:
                print(
                    f" Inside calculating final values for relative_change_value, error is {e}"
                )
                relative_change_in_price = "N/A"
            try:
                if relative_atr not in [
                    0,
                    "N/A",
                    None,
                ] and relative_change_in_price not in ["N/A", None]:
                    # Calculate relative chnage in price divided by relative ATR
                    relative_change_div_by_relative_atr = (
                        relative_change_in_price / relative_atr
                    )
                else:
                    relative_change_div_by_relative_atr = "N/A"
            except Exception as e:
                print(
                    f" Inside calculating final values for relative_change_div_by_relative_atr, error is {e}"
                )
                relative_change_div_by_relative_atr = "N/A"

            # Calculate Relative change in price divided by Relative volume
            if (
                (relative_change_in_price != "N/A")
                and (relative_volume != "N/A")
                and (relative_volume != 0)
            ):
                relative_change_in_price_div_by_relative_volume = (
                    relative_change_in_price / relative_volume
                )

                relative_change_in_price_div_by_relative_volume = (
                    f"{(relative_change_in_price_div_by_relative_volume):,.2f}"
                )
            else:
                relative_change_in_price_div_by_relative_volume = "N/A"

            # Calculate [ATR/Total absolute cost] / points from lowest price (intraday prices)
            if (
                (total_abs_cost_value != "N/A")
                and (atr != "N/A")
                and (avg_price_combo != None)
                and (day_low != None)
            ):
                try:
                    atr_div_by_total_abs_cost_div_by_point_from_lowest_price = (
                        atr / total_abs_cost_value
                    ) / (avg_price_combo - day_low)

                    atr_div_by_total_abs_cost_div_by_point_from_lowest_price = f"{float(atr_div_by_total_abs_cost_div_by_point_from_lowest_price):,.2f}"
                except Exception as e:
                    atr_div_by_total_abs_cost_div_by_point_from_lowest_price = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Inside calculating 'atr_div_by_total_abs_cost_div_by_point_from_lowest_price', error is {e} "
                        )
            else:
                atr_div_by_total_abs_cost_div_by_point_from_lowest_price = "N/A"

            # Calculate Relative volume / Relative ATR
            if (
                (relative_volume != "N/A")
                and (relative_atr != "N/A")
                and (relative_atr != 0)
            ):
                relative_volume_div_by_relative_atr = relative_volume / relative_atr

                relative_volume_div_by_relative_atr = (
                    f"{(relative_volume_div_by_relative_atr):,.2f}"
                )
            else:
                relative_volume_div_by_relative_atr = "N/A"

            # Calculate [ATR/Total absolute cost] / points from highest price (intraday prices)
            if (
                (total_abs_cost_value != "N/A")
                and (atr != "N/A")
                and (avg_price_combo != None)
                and (day_high != None)
            ):
                try:
                    atr_div_by_total_abs_cost_div_by_point_from_highest_price = (
                        atr / total_abs_cost_value
                    ) / (avg_price_combo - day_high)

                    atr_div_by_total_abs_cost_div_by_point_from_highest_price = f"{(atr_div_by_total_abs_cost_div_by_point_from_highest_price):,.2f}"
                except Exception as e:
                    atr_div_by_total_abs_cost_div_by_point_from_highest_price = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Inside calculating 'atr_div_by_total_abs_cost_div_by_point_from_highest_price', error is {e} "
                        )

            else:
                atr_div_by_total_abs_cost_div_by_point_from_highest_price = "N/A"

            rel_vol_div_by_opening_gap = "N/A"

            # Calculate Size of Opening Gap as a %
            if (
                day_open != None
                and last_close_price != None
                and not variables.flag_weighted_change_in_price
            ):
                size_of_opening_gap_value = math.log(abs(day_open) + 1) * math.copysign(
                    1, day_open
                ) - math.log(abs(last_close_price) + 1) * math.copysign(
                    1, last_close_price
                )

                if size_of_opening_gap_value not in ["N/A", "None", None]:
                    size_of_opening_gap_value = (
                        f"{(size_of_opening_gap_value * 100):,.2f}%"
                    )

                else:
                    size_of_opening_gap_value = "N/A"

            elif variables.flag_weighted_change_in_price:
                size_of_opening_gap_value = calc_weighted_change_legs_based(
                    local_unique_id_to_combo_obj[unique_id],
                    last_day_close_price_for_leg_list,
                    current_day_open_for_legs_list,
                )

                if size_of_opening_gap_value not in ["N/A", "None", None]:
                    # check if values are vlaid
                    if size_of_opening_gap_value not in [
                        0,
                        "N/A",
                        "None",
                        None,
                    ] and relative_volume not in ["N/A", "None", None]:
                        # calculate indicator value
                        rel_vol_div_by_opening_gap = (
                            relative_volume / size_of_opening_gap_value
                        )

                        # check if values are valid
                        if rel_vol_div_by_opening_gap not in ["N/A", "None", None]:
                            # Format value
                            rel_vol_div_by_opening_gap = (
                                f"{(rel_vol_div_by_opening_gap):,.2f}"
                            )

                        else:
                            # set value to N/A
                            rel_vol_div_by_opening_gap = "N/A"

                    else:
                        # set value to N/A
                        rel_vol_div_by_opening_gap = "N/A"

                    size_of_opening_gap_value = (
                        f"{(size_of_opening_gap_value * 100):,.2f}%"
                    )
            else:
                size_of_opening_gap_value = "N/A"

            # Formatting relative_change_in_price
            if relative_change_in_price != "N/A":
                relative_change_in_price = f"{(float(relative_change_in_price)):,.2f}"
            else:
                relative_change_in_price = "N/A"

            # Formatting relative_volume
            if relative_volume != "N/A":
                relative_volume = f"{(float(relative_volume)):,.2f}"
            else:
                relative_volume = "N/A"

            # Formatting relative_atr
            if relative_atr != "N/A":
                relative_atr = f"{(relative_atr):,.2f}"
            else:
                relative_atr = "N/A"

            # Formatting total_abs_cost_value
            if total_abs_cost_value != "N/A":
                total_abs_cost_value = f"{(float(total_abs_cost_value)):,.2f}"
            else:
                total_abs_cost_value = "N/A"

            # Update High- Low Range N %, and Update High - Low Abs N-Days
            if (
                (avg_price_combo != None)
                and (n_day_low != None)
                and (n_day_high != None)
            ):
                # To Avoid by Zero error
                try:
                    # HL range N-Days
                    hl_range_n_day_percent = (avg_price_combo - n_day_low) / (
                        n_day_high - n_day_low
                    )
                    hl_range_n_day_percent = f"{(hl_range_n_day_percent * 100):,.2f}%"
                except Exception as e:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Unique ID: {unique_id} Got Error for N Day HL Range Percent: {e}"
                        )

                    # Setting as N/A
                    hl_range_n_day_percent = "N/A"

                # ABS of N-day high low
                abs_hl_n_day = int(abs(n_day_high - n_day_low) * 100) / 100

                # Format the Value
                n_day_high = f"{(int(n_day_high * 100) / 100):,.2f}"
                n_day_low = f"{(int(n_day_low * 100) / 100):,.2f}"
                abs_hl_n_day = f"{abs_hl_n_day:,.2f}"
            else:
                n_day_low = "N/A"
                n_day_high = "N/A"
                hl_range_n_day_percent = "N/A"
                abs_hl_n_day = "N/A"

            # ATR
            if atr != None:
                atr = f"{(int(atr * 100) / 100):,.2f}"
            else:
                atr = "N/A"

            # Init change from close% value
            change_from_close_percent = "N/A"

            # Update From Close if the flag_weighted_change_in_price is False
            if (
                (avg_price_combo != None)
                and (last_close_price != None)
                and not variables.flag_weighted_change_in_price
            ):
                change_from_close_percent = math.log(
                    abs(avg_price_combo) + 1
                ) * math.copysign(1, avg_price_combo) - math.log(
                    abs(last_close_price) + 1
                ) * math.copysign(1, last_close_price)

                # Format the Value
                if not isinstance(change_from_close_percent, str):
                    change_from_close_percent = (
                        f"{(change_from_close_percent * 100):,.2f}%"
                    )

            # Update From Open if the flag_weighted_change_in_price is True
            if (
                last_day_close_price_for_leg_list != "N/A"
            ) and variables.flag_weighted_change_in_price:
                # print(f"Unique ID: {unique_id} Change From Close")
                change_from_close_percent = calc_weighted_change_legs_based(
                    local_unique_id_to_combo_obj[unique_id],
                    last_day_close_price_for_leg_list,
                )

                # Format the Value
                if change_from_close_percent not in ["N/A"]:
                    change_from_close_percent = float(change_from_close_percent)
                    change_from_close_percent = (
                        f"{(change_from_close_percent * 100):,.2f}%"
                    )

            # Last Close Price
            if last_close_price != None:
                last_close_price = f"{(int(last_close_price * 100) / 100):,.2f}"
            else:
                last_close_price = "N/A"

            # Correlation
            if correlation != None:
                correlation = f"{(int(correlation * 10000) / 10000):,.4f}"
            else:
                correlation = "N/A"

            # Update High Low Range 1 %
            if (avg_price_combo != None) and (day_low != None) and (day_high != None):
                # To Avoid by Zero error
                try:
                    # HL range N-Days
                    hl_range_current_day_percent = (avg_price_combo - day_low) / (
                        day_high - day_low
                    )
                    hl_range_current_day_percent = (
                        f"{int(hl_range_current_day_percent * 100):,.2f}%"
                    )
                except Exception as e:
                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Unique ID: {unique_id} Got Error for Current Day HL Range Percent: {e}"
                        )

                    # Setting None
                    hl_range_current_day_percent = "N/A"

                # ABS of 1-day high low
                abs_hl_current_day = int(abs(day_high - day_low) * 100) / 100

                # Format the Value
                abs_hl_current_day = f"{(int(abs_hl_current_day * 100) / 100):,.2f}"
                day_high = f"{(int(day_high * 100) / 100):,.2f}"
                day_low = f"{(int(day_low * 100) / 100):,.2f}"
            else:
                day_high = "N/A"
                day_low = "N/A"
                hl_range_current_day_percent = "N/A"
                abs_hl_current_day = "N/A"

            # Last Close Price
            if change_from_open_percent not in ["N/A", None]:
                change_from_open_percent = f"{change_from_open_percent * 100:,.2f}%"
            else:
                change_from_open_percent = "N/A"

            if net_change_from_open_by_hv not in ["N/A", None]:
                net_change_from_open_by_hv = f"{net_change_from_open_by_hv:,.4f}"
            else:
                net_change_from_open_by_hv = "N/A"

            if candle_volatility_val not in ["N/A", None]:
                candle_volatility_val = f"{candle_volatility_val:,.2f}%"
            else:
                candle_volatility_val = "N/A"

            if cv_by_net_chng_from_open not in ["N/A", None]:
                cv_by_net_chng_from_open = f"{cv_by_net_chng_from_open:,.4f}"
            else:
                cv_by_net_chng_from_open = "N/A"

            if relative_change_div_by_relative_atr not in ["N/A", None]:
                relative_change_div_by_relative_atr = (
                    f"{relative_change_div_by_relative_atr:,.2f}"
                )
            else:
                relative_change_div_by_relative_atr = "N/A"

            # Combo_object
            combination_obj = variables.unique_id_to_combo_obj[unique_id]

            # Ticker String
            ticker_string = make_informative_combo_string(combination_obj)

            # If Cache is Enabled, set the primary indicators to the "N/A"
            if variables.flag_cache_data:
                # Current Time
                current_time = datetime.datetime.now(variables.target_timezone_obj)

                if (
                    variables.lut_for_long_term_values is not None
                    and current_time
                    >= variables.lut_for_long_term_values
                    + datetime.timedelta(
                        minutes=variables.time_buffer_for_keep_updating_lut_time_for_fetched_values
                    )
                ):
                    n_day_high, n_day_low, atr, last_close_price, beta_value = (
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                    )

                if (
                    variables.lut_for_intraday_values is not None
                    and current_time
                    >= variables.lut_for_intraday_values
                    + datetime.timedelta(
                        minutes=variables.time_buffer_for_keep_updating_lut_time_for_fetched_values
                    )
                ):
                    day_open, day_high, day_low, low_timestamp, high_timestamp = (
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                    )
                    (
                        intraday_support,
                        intraday_resistance,
                        intraday_support_count,
                        intraday_resistance_count,
                    ) = (
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                    )
                    (
                        highest_price_comparison_intraday,
                        lowest_price_comparison_intraday,
                        intraday_price_range_ratio,
                    ) = ("N/A", "N/A", "N/A")

                if (
                    variables.lut_for_hv_related_columns is not None
                    and current_time
                    >= variables.lut_for_hv_related_columns
                    + datetime.timedelta(
                        minutes=variables.time_buffer_for_keep_updating_lut_time_for_fetched_values
                    )
                ):
                    (
                        hv_value,
                        candle_volatility_val,
                    ) = (
                        "N/A",
                        "N/A",
                    )

                if (
                    variables.lut_for_volume_related_fields is not None
                    and current_time
                    >= variables.lut_for_volume_related_fields
                    + datetime.timedelta(
                        minutes=variables.time_buffer_for_keep_updating_lut_time_for_fetched_values
                    )
                ):
                    (
                        mean_of_net_volume,
                        std_plus_1,
                        std_negative_1,
                        std_plus_2,
                        std_negative_2,
                        std_plus_3,
                        std_negative_3,
                    ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

                if (
                    variables.lut_for_price_based_relative_indicators_values is not None
                    and current_time
                    >= variables.lut_for_price_based_relative_indicators_values
                    + datetime.timedelta(
                        minutes=variables.time_buffer_for_keep_updating_lut_time_for_fetched_values
                    )
                ):
                    (
                        resistance,
                        support,
                        resitance_count,
                        support_count,
                        relative_atr,
                        relative_volume,
                        rel_volume_div_by_rel_chg_last_n_minutes,
                    ) = ("N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A")

                    (
                        relative_atr_derivative,
                        relative_atr_on_positive_candles,
                        relative_atr_on_negative_candles,
                        relative_volume_derivative,
                        relative_volume_on_positive_candles,
                        relative_volume_on_negative_candles,
                        avg_bid_ask_spread,
                        support_price_ration_in_range,
                        resistance_price_ration_in_range,
                        volume_magnet,
                    ) = (
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                    )

                    (
                        relative_atr_lower,
                        relative_atr_higher,
                        relative_volume_lower,
                        relative_volume_higher,
                    ) = ("N/A", "N/A", "N/A", "N/A")

            # List of values to check if it is 'N/A'
            values_for_cas_table = (
                unique_id,
                ticker_string,
                buy_price,
                sell_price,
                total_abs_cost_value,
                day_high,
                high_timestamp,
                day_low,
                low_timestamp,
                abs_hl_current_day,
                hl_range_current_day_percent,
                last_close_price,
                change_from_close_percent,
                change_from_open_percent,
                chg_close,
                chg_open,
                size_of_opening_gap_value,
                n_day_high,
                n_day_low,
                abs_hl_n_day,
                hl_range_n_day_percent,
                atr,
                hv_value,
                candle_volatility_val,
                net_change_from_open_by_hv,
                cv_by_net_chng_from_open,
                resistance,
                support,
                resitance_count,
                support_count,
                intraday_resistance,
                intraday_support,
                intraday_resistance_count,
                intraday_support_count,
                mean_of_net_volume,
                std_plus_1,
                std_negative_1,
                std_plus_2,
                std_negative_2,
                std_plus_3,
                std_negative_3,
                relative_atr,
                relative_change_in_price,
                relative_volume,
                relative_volume_div_by_relative_atr,
                relative_change_in_price_div_by_relative_volume,
                relative_change_div_by_relative_atr,
                atr_div_by_total_abs_cost_div_by_point_from_lowest_price,
                atr_div_by_total_abs_cost_div_by_point_from_highest_price,
                beta_value,
                change_from_high_percent,
                change_from_low_percent,
                highest_price_comparison_intraday,
                lowest_price_comparison_intraday,
                intraday_price_range_ratio,
                rel_volume_div_by_rel_chg_last_n_minutes,
                relative_volume_on_positive_candles,
                relative_volume_on_negative_candles,
                relative_atr_on_positive_candles,
                relative_atr_on_negative_candles,
                avg_bid_ask_div_by_avg_chg,
                bid_ask_div_by_avg_chg,
                relative_volume_derivative,
                relative_atr_derivative,
                support_price_ration_in_range,
                resistance_price_ration_in_range,
                support_price_ration_in_range_intraday,
                resistance_price_ration_in_range_intraday,
                rel_vol_div_by_opening_gap,
                volume_magnet,
                relative_atr_lower,
                relative_atr_higher,
                relative_volume_lower,
                relative_volume_higher,
            )

            # Passing values for cas table
            cas_table_update_values.append(values_for_cas_table)

            unique_id_correlation = (unique_id, correlation)
            cas_condition_table_update_values.append(unique_id_correlation)

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print("Error in updating cas Values and price", e)

    # If Caching is enabled
    if variables.flag_cache_data:
        # Update values in DB cache table
        update_cache_data_in_db(cas_table_update_values)

        # Get all cache values dataframe
        cache_table_df = get_primary_vars_db(table_name=f"{variables.sql_table_cache}")

        # Convert all rows in cache table dataframe into tuple
        cache_table_values_in_tuples = cache_table_df.apply(tuple, axis=1).tolist()

        # Get final values to be displayed in cas table
        cas_table_update_values = (
            process_the_latest_cas_indicator_values_fetched_from_cache_table_db(
                cache_table_values_in_tuples
            )
        )

    # Get values for secondary columns
    cas_table_update_values = get_dataframe_for_seconday_columns_in_cas_table(
        cas_table_update_values
    )

    try:
        # Sort Values Based on user selection
        cas_table_update_values = sort_cas_row_values_by_column(cas_table_update_values)

        # Get secondary columns mapped to expression dictionary
        local_map_secondary_columns_to_expression_in_cas_table = copy.deepcopy(
            variables.map_secondary_columns_to_expression_in_cas_table
        )

        # Get secondary columns
        secondary_columns_in_cas_table = list(
            local_map_secondary_columns_to_expression_in_cas_table.keys()
        )

        # create dataframe
        cas_table_update_values_df = pd.DataFrame(
            cas_table_update_values,
            columns=variables.cas_table_columns + secondary_columns_in_cas_table,
        )

        # new Indicator -> sorting.
        # here <- add col in data (col for each indicator)

        # Update the Values in Table
        variables.screen.screen_cas_obj.update_cas_table_rows_value(
            cas_table_update_values_df
        )

        # Update the correlation value
        variables.screen.screen_cas_obj.update_cas_condition_table_rows_value(
            cas_condition_table_update_values, 12
        )

        # Adding Correlation to the DataFrame
        corr_dict = dict(cas_condition_table_update_values)
        cas_table_update_values_df["Correlation"] = cas_table_update_values_df[
            "Unique ID"
        ].map(corr_dict)
    except Exception as e:
        if variables.flag_debug_mode:
            print(f"Error Price 724 ", e)

    # Make the dataframe available to class
    variables.cas_table_values_df = cas_table_update_values_df
