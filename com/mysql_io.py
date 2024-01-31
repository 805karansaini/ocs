"""
Created on 14-Mar-2023

@author: Karan
"""

from com.variables import *


# Returns the last saved unique ID from both the tables.
def get_unique_id_db():

    max_unique_id = 0

    # Get the max present unique ID from combination table
    for sql_database_name in variables.all_sql_databases:

        # Init active_sqlalchemy_connection for active and archive DB
        active_sqlalchemy_connection = (
            variables.active_sqlalchemy_connection
            if sql_database_name == variables.active_sql_db_name
            else variables.archive_sqlalchemy_connection
        )

        try:

            # get_max unique ID SQL query
            get_max_unique_id_query = text(
                f"SELECT MAX(`Unique ID`) FROM {variables.sql_table_combination}"
            )
            result = active_sqlalchemy_connection.execute(get_max_unique_id_query)
            time.sleep(variables.sleep_time_db)

            result = int(result.fetchone()[0])
            max_unique_id = max(max_unique_id, result)

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Successfuly got the max present unique ID from {sql_database_name}.{variables.sql_table_combination}"
                )

        except:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Unable to get the max present unique ID from {sql_database_name}.{variables.sql_table_combination}"
                )

    return max_unique_id


# Drop all DB tables
def drop_tables():

    # Dropping table one at a time
    for sql_database_name in variables.all_sql_databases:

        # Init active_sqlalchemy_connection for active and archive DB
        active_sqlalchemy_connection = (
            variables.active_sqlalchemy_connection
            if sql_database_name == variables.active_sql_db_name
            else variables.archive_sqlalchemy_connection
        )

        for table_name in variables.all_sql_tables_in_db_with_correct_dropping_order:
            try:

                # Drop_table SQL query
                drop_table = text(f"Drop TABLE `{sql_database_name}`.`{table_name}`")
                result = active_sqlalchemy_connection.execute(drop_table)
                time.sleep(variables.sleep_time_db)

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Database = {sql_database_name}, Dropped table = {table_name}"
                    )

            except Exception as e:

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Database = {sql_database_name}, Unable to drop table = {table_name}, Exception: {e}"
                    )

    # DROP THE META DATA TABLE
    try:

        # Drop_table SQL query
        drop_table = text(f"Drop TABLE `{variables.sql_table_meta_data}`")
        result = variables.active_sqlalchemy_connection.execute(drop_table)
        time.sleep(variables.sleep_time_db)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Dropped table = {variables.sql_table_meta_data}")

    except:

        # Print to console
        if variables.flag_debug_mode:
            print(f"Unable to drop table = {variables.sql_table_meta_data}")

    # DROP THE Watchlist DATA TABLE
    try:

        # Drop_table SQL query
        drop_table = text(f"Drop TABLE `{variables.sql_table_watchlist}`")
        result = variables.active_sqlalchemy_connection.execute(drop_table)
        time.sleep(variables.sleep_time_db)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Dropped table = {variables.sql_table_watchlist}")

    except:

        # Print to console
        if variables.flag_debug_mode:
            print(f"Unable to drop table = {variables.sql_table_watchlist}")

    # DROP THE Accounts group DATA TABLE
    try:

        # Drop_table SQL query
        drop_table = text(f"Drop TABLE `{variables.sql_table_account_group}`")
        result = variables.active_sqlalchemy_connection.execute(drop_table)
        time.sleep(variables.sleep_time_db)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Dropped table = {variables.sql_table_account_group}")

    except:

        # Print to console
        if variables.flag_debug_mode:
            print(f"Unable to drop table = {variables.sql_table_account_group}")

    # DROP THE Watchlist DATA TABLE
    try:

        # Drop_table SQL query
        drop_table = text(f"Drop TABLE `{variables.sql_table_account_conditions}`")
        result = variables.active_sqlalchemy_connection.execute(drop_table)
        time.sleep(variables.sleep_time_db)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Dropped table = {variables.sql_table_account_conditions}")

    except:

        # Print to console
        if variables.flag_debug_mode:
            print(f"Unable to drop table = {variables.sql_table_account_conditions}")

    try:

        # Drop_table SQL query
        drop_table = text(f"Drop TABLE `{variables.sql_table_filter_table}`")
        result = variables.active_sqlalchemy_connection.execute(drop_table)
        time.sleep(variables.sleep_time_db)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Dropped table = {variables.sql_table_filter_table}")

    except:

        # Print to console
        if variables.flag_debug_mode:
            print(f"Unable to drop table = {variables.sql_table_filter_table}")

# Method to insert combination in DB table
def insert_combination_db(active_flag, combination_obj, insert_in_cas_table=False):

    # Init
    unique_id = combination_obj.unique_id
    buy_legs = combination_obj.buy_legs
    sell_legs = combination_obj.sell_legs
    current_time = datetime.datetime.now(variables.target_timezone_obj)

    # Init Database name and Sql connection
    if active_flag == True:
        sql_database_name = variables.active_sql_db_name
        active_sqlalchemy_connection = variables.active_sqlalchemy_connection
    else:
        sql_database_name = variables.archive_sql_db_name
        active_sqlalchemy_connection = variables.archive_sqlalchemy_connection

    # In which table legs must be inserted
    if insert_in_cas_table:
        insert_in_table = variables.sql_table_cas_legs

    else:
        insert_in_table = variables.sql_table_combination

    # Loop over leg object and insert it into the database
    for leg_obj in buy_legs + sell_legs:

        action = leg_obj.action
        symbol = leg_obj.symbol
        sec_type = leg_obj.sec_type
        exchange = leg_obj.exchange
        currency = leg_obj.currency
        quantity = leg_obj.quantity
        expiry_date = leg_obj.expiry_date
        strike_price = leg_obj.strike_price
        right = leg_obj.right
        multiplier = leg_obj.multiplier
        con_id = leg_obj.con_id
        primary_exchange = leg_obj.primary_exchange
        trading_class = leg_obj.trading_class
        dte = leg_obj.dte
        delta = leg_obj.delta

        insr_query = text(
            f"INSERT INTO `{sql_database_name}`.`{insert_in_table}` \
                    ( `Unique ID`, `Action`,`Symbol`, `SecType`,`Exchange`, `Currency`, `#Lots`,`Strike`, `Expiry`,`Lot Size`,`Right`, `Trading Class`,`ConId`, `Primary Exchange`, `Time`, `DTE`, `Delta`) \
                    VALUES ('{str(unique_id)}','{action}','{str(symbol)}','{str(sec_type)}','{str(exchange)}','{str(currency)}','{str(quantity)}','{str(strike_price)}',\
                    '{str(expiry_date)}','{str(multiplier)}', '{str(right)}', '{str(trading_class)}', '{str(con_id)}','{str(primary_exchange)}', '{str(current_time)}', '{str(dte)}', '{str(delta)}' )"
        )

        try:
            result = active_sqlalchemy_connection.execute(insr_query)
            time.sleep(variables.sleep_time_db)
        except Exception as e:
            if variables.flag_debug_mode:
                print(
                    f"Unable to insert the identified butterfly in to database, Unique ID: {unique_id}"
                )

# Method to drop cache table
def drop_cache_table():

    # Drop Cache Table query
    query_drop_cache_table = f"""DROP TABLE `{variables.sql_table_cache}`"""

    # Run the query for both active and archive DB
    for active_sqlalchemy_connection in [
        variables.active_sqlalchemy_connection,
        variables.archive_sqlalchemy_connection,
    ]:

        try:
            active_sqlalchemy_connection.execute(query_drop_cache_table)

            # Print to console
            if variables.flag_debug_mode:
                print("Query successfully executed: ", query_drop_cache_table)
        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:
                print("Query failed: ", query_drop_cache_table, "Exception: ", e)


# Method to get query to create ladder table
def get_query_to_create_ladder_table():

    try:
        # Get columns of ladder table
        local_scale_trader_table_columns = copy.deepcopy(
            variables.scale_trader_table_columns
        )

        # Create ladder table query
        query_create_ladder_table = (
            rf"""CREATE TABLE `{variables.sql_table_ladder}` ("""
        )

        # Add ladder id and unique id fields (have datatype INT NOT NULL) to table
        for column_name in local_scale_trader_table_columns[0:2]:

            query_create_ladder_table += rf" `{column_name}` INT NOT NULL,"

        # Add columns to create DB ladder table query
        for column_name in local_scale_trader_table_columns[2:]:

            query_create_ladder_table += rf" `{column_name}` VARCHAR(40),"

        # Add closing bracket to complete query
        query_create_ladder_table = (
            query_create_ladder_table + " PRIMARY KEY (`Ladder ID`) )"
        )

        # Return query to create ladder table
        return query_create_ladder_table

    except Exception as e:

        # Return None if exception occurs
        return None


# Method to get query to create sequence table - ask karana bout foriegn key use
def get_query_to_create_sequence_table():

    try:
        # Get columns of sequence table
        local_sequence_table_columns = copy.deepcopy(variables.sequence_table_columns)

        # Create sequence table query
        query_create_sequence_table = (
            rf"""CREATE TABLE `{variables.sql_table_sequence}` ("""
        )

        # Add columns in query of creating sequence table
        for column_name in local_sequence_table_columns:

            # For ID columns datatype will be INT NOT NULL
            if column_name in ["Sequence ID", "Ladder ID"]:

                query_create_sequence_table += rf"`{column_name}` INT NOT NULL,"

            # For rest of columns datatype will be VARCHAR()
            else:

                query_create_sequence_table += rf"`{column_name}` VARCHAR(40),"

        # Add closing bracket to complete query
        query_create_sequence_table = (
            query_create_sequence_table
            + f" FOREIGN KEY (`Ladder ID`) REFERENCES {variables.sql_table_ladder} (`Ladder ID`) )"
        )

        # Return query to create sequence table
        return query_create_sequence_table

    except Exception as e:

        # Return None if exception occurs
        return None

# Method to create cache db table
def create_cache_table(
    flag_recovery_mode=True,
):

    # Drop preexisting table if recover_mode is True
    if flag_recovery_mode:
        drop_cache_table()

    # Get list of columns to be put in cache db table
    cache_table_columns = copy.deepcopy(variables.cache_data_table_columns)

    # Cache Table query
    query_create_cache_table = rf"""CREATE TABLE `{variables.sql_table_cache}` ( """

    # Create part of query where we put column name and datatype
    for column_name in cache_table_columns:

        if column_name == variables.unqiue_id_col_name_for_cache:
            query_create_cache_table += rf"`{column_name}` INT NOT NULL,"
        elif column_name == variables.tickers_col_name_for_cache:
            query_create_cache_table += rf"`{column_name}` VARCHAR(400),"
        else:
            # Concatenating all cache columns excpet Unique ID
            query_create_cache_table += rf"`{column_name}` VARCHAR(100),"

    query_create_cache_table = query_create_cache_table[:-1] + " )"

    query_create_cache_table = query_create_cache_table.replace(
        "%",
        "%%",
    )

    if not flag_recovery_mode:
        return query_create_cache_table

    else:
        # Run the query for both the active and archive DB
        for active_sqlalchemy_connection in [
            variables.active_sqlalchemy_connection,
            variables.archive_sqlalchemy_connection,
        ]:

            try:
                result = active_sqlalchemy_connection.execute(query_create_cache_table)
                time.sleep(variables.sleep_time_db)

                # Print to console
                if variables.flag_debug_mode:
                    print("Query successfully executed: ", query_create_cache_table)
            except Exception as e:

                # Print to console
                if variables.flag_debug_mode:
                    print("Query failed: ", query_create_cache_table, "Exception: ", e)

# Check if db table needs to be recreated
def check_if_cache_table_needs_to_be_recreated():

    # Active DB
    sql_database_name = variables.active_sql_db_name

    # Init active_sqlalchemy_connection for active and archive DB
    active_sqlalchemy_connection = (
        variables.active_sqlalchemy_connection
        if sql_database_name == variables.active_sql_db_name
        else variables.archive_sqlalchemy_connection
    )

    # Query to get columns in current cache table
    query_get_cache_table_desc = (
        f"DESC `{sql_database_name}`.`{variables.sql_table_cache}`"
    )

    try:
        # Run query to get columns in current cache table
        result = active_sqlalchemy_connection.execute(query_get_cache_table_desc)

        # Fetching all the results. (list of tuples)
        description_of_cache_table = result.fetchall()

        # Print to console
        if variables.flag_debug_mode:
            print("Query successfully executed: ", query_get_cache_table_desc)

        # Extract the column names from the query result
        column_names_in_current_cache_table = [
            column[0] for column in description_of_cache_table
        ]

        # Get list of columns to be put in cache db table
        cache_table_columns = copy.deepcopy(variables.cache_data_table_columns)

        # Check if columns in cache table and cas table are same
        if column_names_in_current_cache_table == cache_table_columns:

            # It will indicate that columns in both tables are same
            return False
        else:
            # It will indicate that columns in both tables are not same
            return True

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(f"Query failed: {query_get_cache_table_desc} Exp: {e}")

        return True

# Method to create query to create conditional series db table
def get_query_to_create_conditional_series_table():
    try:
        # Get columns of conditional series table
        local_conditional_series_table_columns = copy.deepcopy(
            variables.conditional_series_table_columns
        )

        # Create ladder table query
        query = rf"""CREATE TABLE `{variables.sql_table_conditional_series}` ("""

        # Add series id and unique id fields (have datatype INT NOT NULL) to table
        for column_name in local_conditional_series_table_columns[0:2]:
            query += rf" `{column_name}` INT NOT NULL,"
            # print(column_name)

        # Add columns to create DB conditional series table query
        for column_name in local_conditional_series_table_columns[2:]:
            query += rf" `{column_name}` VARCHAR(400),"

        query = query[:-1] + ")"

        # Return query to create ladder table
        return query

    except Exception as e:

        # Return None if exception occurs
        return None

# Method to get query to create conditional series sequence table
def get_query_to_create_conditional_series_sequence_table():
    try:
        # Get columns of conditional series table
        local_conditional_series_sequence_table_columns = copy.deepcopy(
            variables.conditional_series_sequence_table_columns
        )

        # Create ladder table query
        query = (
            rf"""CREATE TABLE `{variables.sql_table_conditional_series_sequence}` ("""
        )

        # Add series id and unique id fields (have datatype INT NOT NULL) to table
        for column_name in local_conditional_series_sequence_table_columns[0:3]:
            query += rf" `{column_name}` INT NOT NULL,"

        # Add columns to create DB conditional series table query
        for column_name in local_conditional_series_sequence_table_columns[3:]:
            query += rf" `{column_name}` VARCHAR(400),"

        query = query[:-1] + ")"

        # Return query to create ladder table
        return query

    except Exception as e:

        # Return None if exception occurs
        return None


# Create fresh tables
def create_tables():

    # Loop over the archive and active database to create tables
    for sql_database_name in variables.all_sql_databases:

        # Create fresh 'Combination table' table - no rows are being added here
        query_create_combination_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_combination}` \
                        ( `Unique ID` INT NOT NULL, `Action` VARCHAR(40) NOT NULL, `Symbol` VARCHAR(40), `SecType` VARCHAR(40), `DTE` VARCHAR(40), `Delta` VARCHAR(40), \
                         `Exchange` VARCHAR(40),`Currency` VARCHAR(40),`#Lots` VARCHAR(40), `Strike` VARCHAR(40), `Expiry` VARCHAR(40),\
                          `Lot Size` VARCHAR(40), `Right` VARCHAR(40), `Trading Class` VARCHAR(40), `ConID` VARCHAR(40), `Primary Exchange` VARCHAR(40), `Time` VARCHAR(40)) ENGINE = InnoDB "
        )

        # Create fresh 'CAS Legs' table - no rows are being added here
        query_create_cas_legs_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_cas_legs}` \
                        ( `Unique ID` INT NOT NULL, `Action` VARCHAR(40) NOT NULL, `Symbol` VARCHAR(40), `SecType` VARCHAR(40), `DTE` VARCHAR(40), `Delta` VARCHAR(40), \
                         `Exchange` VARCHAR(40),`Currency` VARCHAR(40),`#Lots` VARCHAR(40), `Strike` VARCHAR(40), `Expiry` VARCHAR(40),\
                          `Lot Size` VARCHAR(40), `Right` VARCHAR(40), `Trading Class` VARCHAR(40), `ConID` VARCHAR(40), `Primary Exchange` VARCHAR(40), `Time` VARCHAR(40)) ENGINE = InnoDB "
        )

        # Create fresh 'Combination Status' table - no rows are being added here
        query_create_combination_status_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_combination_status}` \
                        ( `Unique ID` INT, `Account ID` VARCHAR(40), `Tickers` VARCHAR(40),`Action` VARCHAR(40) NOT NULL, `#Lots` VARCHAR(40), `Order Type` VARCHAR(40), `Order Time` VARCHAR(40), `Order IDs` VARCHAR(100),\
                         `Last Update Time` VARCHAR(40), `Entry Price` VARCHAR(40), `Limit Price` VARCHAR(40), `Trigger Price` VARCHAR(40), `Reference Price` VARCHAR(40), \
                         `Trail Value` VARCHAR(40), `Status` VARCHAR(40), `Reason For Failed` VARCHAR(100),`Ladder ID` VARCHAR(40), `Sequence ID` VARCHAR(40), \
                         `ATR Multiple` VARCHAR(40), `ATR` VARCHAR(40), `Bypass RM Check`  VARCHAR(40), `Execution Engine`  VARCHAR(40), `Limit IV` VARCHAR(40), "
            f"`Trigger IV` VARCHAR(40), `Actual Entry Price` VARCHAR(40)) ENGINE = InnoDB "
        )

        # Create fresh 'Order Status' table - no rows are being added here
        query_create_order_status_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_order_status}` \
                        ( `Account ID` VARCHAR(40), `Unique ID` INT, `Order ID` VARCHAR(40) NOT NULL, `Parent Order ID` VARCHAR(40) NOT NULL, `Order Action` VARCHAR(40) NOT NULL, `Target Fill` VARCHAR(40),\
                         `Current Fill` VARCHAR(40), `Avg Fill Price` VARCHAR(40), `Order Time` VARCHAR(40),`Order Sent Time` VARCHAR(40), `Last Update Time` VARCHAR(40), `Order Type` VARCHAR(25), `Status` VARCHAR(40), `Ticker` VARCHAR(40)) ENGINE = InnoDB "
        )

        # Create Meta-Data Table, will be used to store user last removed time.
        query_create_meta_data_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_meta_data}` \
                        ( `Order Book Cleaned Time` VARCHAR(50) NOT NULL, `CAS Longterm Updated Time`  VARCHAR(50) NOT NULL, `CAS Intraday Updated Time` VARCHAR(50) NOT NULL) ENGINE = InnoDB "
        )

        # Get query to create cache table
        query_create_cache_table = create_cache_table(
            flag_recovery_mode=False,
        )

        # Get query to create ladder table
        query_create_ladder_table = get_query_to_create_ladder_table()

        # Get query to create sequence table
        query_create_sequence_table = get_query_to_create_sequence_table()

        # CAS Status
        query_create_cas_status_tables = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_cas_status}` \
                        ( `Unique ID` INT NOT NULL, `Trading Combination Unique ID` INT NOT NULL, `Evaluation Unique ID` VARCHAR(40), `Condition` VARCHAR(1000), `CAS Condition Type` VARCHAR(40), \
                         `Condition Reference Price` VARCHAR(40), `Reference Position` VARCHAR(40), `Target Position` VARCHAR(40), `Condition Trigger Price` VARCHAR(40), `Order Type` VARCHAR(40),\
                         `#Lots` VARCHAR(40), `Limit Price` VARCHAR(40), `Order Trigger Price` VARCHAR(40), `Trail Value` VARCHAR(40),\
                          `Status` VARCHAR(40), `Reason For Failed` VARCHAR(200) , `ATR Multiple` VARCHAR(40), `ATR` VARCHAR(40), `Account ID` VARCHAR(40), `Bypass RM Check` VARCHAR(40), `Execution Engine` VARCHAR(40), `Series ID` VARCHAR(40))"
        )

        # Watchlist Status
        query_create_watchlist_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_watchlist}` \
                        ( `Watchlist ID` INT NOT NULL AUTO_INCREMENT, `Watchlist Name` VARCHAR(1000), `Unique IDs` VARCHAR(1000), PRIMARY KEY (`Watchlist ID`))"
        )

        # Account groups
        query_create_account_groups_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_account_group}` \
                        ( `Group ID` INT NOT NULL AUTO_INCREMENT, `Group Name` VARCHAR(1000), `Account IDs` VARCHAR(1000), PRIMARY KEY (`Group ID`))"
        )

        # Account conditions
        query_create_account_conditions_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_account_conditions}` \
                        ( `Account ID` VARCHAR(40), `Condition` VARCHAR(200))"
        )

        # Filter conditions
        query_create_filter_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_filter_table}` \
                                ( `Condition Name` VARCHAR(40), `Condition Expression` VARCHAR(200), `Active` VARCHAR(40))"
        )

        # conditional series
        query_create_conditional_series_table = (
            get_query_to_create_conditional_series_table()
        )

        # conditional series sequence
        query_create_conditional_series_sequence_table = (
            get_query_to_create_conditional_series_sequence_table()
        )

        # Create fresh 'series CAS Legs' table - no rows are being added here
        query_create_series_cas_legs_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_series_cas_legs}` \
                               (`Sequence ID` INT NOT NULL, `Series ID` INT NOT NULL, `Unique ID` INT NOT NULL,`Action` VARCHAR(40) NOT NULL, `Symbol` VARCHAR(40), `SecType` VARCHAR(40), `DTE` VARCHAR(40), `Delta` VARCHAR(40), \
                                `Exchange` VARCHAR(40),`Currency` VARCHAR(40),`#Lots` VARCHAR(40), `Strike` VARCHAR(40), `Expiry` VARCHAR(40),\
                                 `Lot Size` VARCHAR(40), `Right` VARCHAR(40), `Trading Class` VARCHAR(40), `ConID` VARCHAR(40), `Primary Exchange` VARCHAR(40), `Time` VARCHAR(40)) ENGINE = InnoDB "
        )

        # Create fresh 'series positions' table
        query_create_series_positions_table = text(
            f"CREATE TABLE `{sql_database_name}`.`{variables.sql_table_series_positions}` \
                                       (`Sequence ID` INT NOT NULL, `Series ID` INT NOT NULL, `Unique ID` INT NOT NULL, `Account ID` VARCHAR(40), `Reference Position` VARCHAR(40), `Target Position` VARCHAR(40)) ENGINE = InnoDB "
        )

        # Created a list of all the 'Table Creation Query'
        list_query_to_create_table = [
            query_create_combination_table,
            query_create_cas_legs_table,
            query_create_combination_status_table,
            query_create_order_status_table,
            query_create_cache_table,
            query_create_cas_status_tables,
            query_create_meta_data_table,
            query_create_watchlist_table,
            query_create_account_groups_table,
            query_create_account_conditions_table,
            query_create_filter_table,
            query_create_conditional_series_table,
            query_create_conditional_series_sequence_table,
            query_create_series_cas_legs_table,
            query_create_series_positions_table,
            query_create_ladder_table,
            query_create_sequence_table,
        ]

        # Init active_sqlalchemy_connection for active and archive DB
        active_sqlalchemy_connection = (
            variables.active_sqlalchemy_connection
            if sql_database_name == variables.active_sql_db_name
            else variables.archive_sqlalchemy_connection
        )

        # Execute all the query to create tables
        for query_num, table_creation_query in enumerate(list_query_to_create_table):

            # Do not create metadata table in Archive DB
            if (query_num in [6, 7]) and (
                sql_database_name == variables.archive_sql_db_name
            ):
                continue

            try:
                result = active_sqlalchemy_connection.execute(table_creation_query)
                time.sleep(variables.sleep_time_db)

                # Print to console
                if variables.flag_debug_mode:
                    print("Query successfully executed: ", table_creation_query)
            except Exception as e:

                # Print to console
                if variables.flag_debug_mode:
                    print("Query failed: ", table_creation_query, e)

    # Insert Current time in metadata DB
    current_time = datetime.datetime.now(variables.target_timezone_obj)

    # Insert Query inserting current time for 1st time.
    query_insrt_time_in_meta_data_table = text(
        f"INSERT INTO `{variables.sql_table_meta_data}` \
                        ( `Order Book Cleaned Time`, `CAS Longterm Updated Time`, `CAS Intraday Updated Time`) VALUES ('{current_time}', '{current_time}', '{current_time}')"
    )

    query_insrt_default_watchlist_in_watchlist_table = text(
        f"INSERT INTO `{variables.sql_table_watchlist}` \
                        ( `Watchlist Name`, `Unique IDs`) VALUES ('ALL', 'ALL')"
    )

    all_insertion_query = [
        query_insrt_time_in_meta_data_table,
        query_insrt_default_watchlist_in_watchlist_table,
    ]

    for insertion_query in all_insertion_query:

        try:
            result = variables.active_sqlalchemy_connection.execute(insertion_query)
            time.sleep(variables.sleep_time_db)

            # Print to console
            if variables.flag_debug_mode:
                print("Query successfully executed: ", insertion_query)
        except Exception as e:
            # print(e)

            # Print to console
            if variables.flag_debug_mode:
                print("Query failed: ", insertion_query, e)


# Inserts the unique id into cache table once a combo is created
def insert_combination_unique_id_to_cache_table_db(unique_id):

    try:
        # Create insert query for unique id
        insert_query = f"INSERT INTO {variables.sql_table_cache} (`Unique ID`) VALUES ('{unique_id}');"

        # Run query
        result = variables.active_sqlalchemy_connection.execute(insert_query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, Query successfully executed for inserting new combination unique id: ",
                insert_query,
            )

        return True, "No Error", "No Error"
    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(
                f"Unique ID= {unique_id}, Query failed for inserting new combination unique id: ",
                insert_query,
                e,
            )
        return False, "Query failed", f"Unique ID= {unique_id}, Query failed: "


# Updates the cache table data for CAS indicators
def update_cas_table_combination_data_to_cache_table_db(
    unique_id,
    dict_of_col_name_and_values_to_be_updated_in_cache_table,
):

    # Create column part of query
    update_query = f"UPDATE {variables.sql_table_cache} SET"

    # Current time in the target time zone
    current_time_in_target_time_zone = datetime.datetime.now(
        variables.target_timezone_obj
    )

    # Formatting current time in target timezone to remove milliseconds and convert it into string
    current_time_in_target_time_zone = current_time_in_target_time_zone.strftime(
        "%Y-%m-%d %H:%M:%S %z"
    )

    try:
        for (
            col_name,
            col_value,
        ) in dict_of_col_name_and_values_to_be_updated_in_cache_table.items():

            col_name = str(col_name)
            col_value = str(col_value)

            # Formatting the values for the sql query (Escape seq % needs to be %%)
            col_name = col_name.replace("%", "%%")
            col_value = col_value.replace("%", "%%")

            # Appending the time in the indicator value
            col_value = f"{col_value}|{current_time_in_target_time_zone}"

            # Combine column name and value in query
            update_query += f" `{col_name}` = '{col_value}',"

        update_query = update_query[:-1] + f" WHERE `Unique ID` = {unique_id};"
    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(f"Error in updating vaues in combo prices, {e}")

        return

    try:
        # Run query
        result = variables.active_sqlalchemy_connection.execute(update_query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, Query successfully executed: ",
                update_query,
            )

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(
                f"Unique ID= {unique_id}, Query failed: ",
                update_query,
                e,
            )


# Gettting the row of cache values for unique id from the cache table # TODO - Get whole DF at once
def get_cache_values_for_combo_from_db(unique_id):

    # Query to get all rows from the DB
    query_get_all_rows = text(
        f"SELECT * FROM `{variables.sql_table_cache}` WHERE `Unique ID` = {unique_id}"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query_get_all_rows)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the cache values for Combinations, Query successfully executed: {query_get_all_rows}"
            )

        return all_rows_df
    except Exception as e:
        # print(e)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get cache values for Combinations, Query Failed: {query_get_all_rows}"
            )

        return pd.DataFrame()

# Method to terminate series in db table
def terminate_series(unique_id, series_id=None):

    try:

        query = text(
            f"UPDATE `{variables.sql_table_conditional_series}` SET `Status` = 'Terminated',`Is Started Once` = 'Yes' WHERE `Unique ID` = '{unique_id}' AND `Status`<>'Completed';"
        )

        if series_id != None:
            query = text(
                f"UPDATE `{variables.sql_table_conditional_series}` SET `Status` = 'Terminated',`Is Started Once` = 'Yes' WHERE `Unique ID` = '{unique_id}' AND `Series ID`='{series_id}';"
            )

        result = variables.active_sqlalchemy_connection.execute(query)

        variables.screen.screen_conditional_series_tab.update_conditional_series_table()

    except Exception as e:

        if variables.flag_debug_mode:

            print(f"Failed execution for terminating series, {e}")


# It move whole data for a unique id from active db to archive db.(when the combo is deleted from the system)
def move_active_data_to_archive_db(
    unique_id, flag_move_cas_condition_table_row=False, account_id=None
):

    # check if flag to move only row in table is true
    if flag_move_cas_condition_table_row:
        local_sql_tables_to_edit = [copy.deepcopy(variables.sql_table_cas_status)]
    else:
        local_sql_tables_to_edit = copy.deepcopy(variables.all_sql_tables_in_db)

    # Get all ladder ids for unique ids dataframe
    local_scale_trade_table_dataframe = get_primary_vars_db(variables.sql_table_ladder)

    # Initialize ladder ids for unique id to none
    ladder_ids_filter_string = "'None'"

    # check if dataframe is empty
    if not local_scale_trade_table_dataframe.empty:

        # Use the query method to get the value of ladder ids for unique id
        ladder_ids_for_unique_id = list(
            variables.scale_trade_table_dataframe.loc[
                variables.scale_trade_table_dataframe["Unique ID"] == unique_id,
                "Ladder ID",
            ].values
        )

        # Get string of ladder ids separated by commas
        ladder_ids_for_unique_id = [str(item) for item in ladder_ids_for_unique_id]

        # Join the elements with a comma separator
        ladder_ids_filter_string = ", ".join(ladder_ids_for_unique_id)

    # If no ladder ids found for unique id then set ladder_ids_filter_string to None
    if ladder_ids_filter_string == "":

        # Initialize ladder ids for unique id to none
        ladder_ids_filter_string = "'None'"

    # It should work as we controlled list of table names
    # Process the tables. Move the data from active to archive and delete data from the active table
    for sql_table_name in local_sql_tables_to_edit:

        # Get All the Data for unique_id from the table(Active DB)

        # Query to get all rows from the DB
        query_get_all_rows_unique_id = text(
            f"SELECT * FROM `{sql_table_name}` WHERE `Unique ID` = {unique_id}"
        )

        # If table name is same as sequence table name
        if sql_table_name == variables.sql_table_sequence:

            query_get_all_rows_unique_id = text(
                f"SELECT * FROM `{sql_table_name}` WHERE `Ladder ID` IN ({ladder_ids_filter_string})"
            )

        # If table name is same as cas status table name
        if sql_table_name == variables.sql_table_cas_status and account_id == None:

            query_get_all_rows_unique_id = text(
                f"SELECT * FROM `{sql_table_name}` WHERE `Unique ID` = {unique_id} AND `Status` <> 'Failed'"
            )
        # If table name is same as cas status table name
        elif sql_table_name == variables.sql_table_cas_status and account_id != None:

            query_get_all_rows_unique_id = text(
                f"SELECT * FROM `{sql_table_name}` WHERE `Unique ID` = {unique_id} AND `Status` <> 'Failed' AND `Account ID` = '{account_id}'"
            )

        try:
            result = variables.active_sqlalchemy_connection.execute(
                query_get_all_rows_unique_id
            )

            # Fetching all the results. (list of tuples)
            all_rows = result.fetchall()

            # Making DataFrame
            all_rows_df = pd.DataFrame(all_rows)

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Unique ID= {unique_id}, Query successfully executed: ",
                    query_get_all_rows_unique_id,
                )
        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:
                # print(e)
                print(
                    f"Unique ID= {unique_id}, Query failed: ",
                    query_get_all_rows_unique_id,
                )

        try:

            if variables.flag_debug_mode:
                print(f"Moving data unique Id = {unique_id}")
                print(all_rows)

            # Move data
            all_rows_df.to_sql(
                sql_table_name,
                con=variables.archive_sqlalchemy_connection,
                if_exists="append",
                index=False,
            )

        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:
                # print(e)
                print(
                    f"Unique ID = {unique_id}, Could not move data to archive {sql_table_name=}"
                )

    if not flag_move_cas_condition_table_row:

        # Bring sequence table before ladder table
        local_sql_tables_to_edit = [
            variables.sql_table_sequence
        ] + local_sql_tables_to_edit[:-1]

    # It should work as we controlled list of table names
    # Delete data from the active table
    for sql_table_name in local_sql_tables_to_edit:

        try:

            # Delete data from active table
            query_delete_rows = text(
                f"DELETE FROM `{sql_table_name}` WHERE `Unique ID` = {unique_id}"
            )

            # If table name is same as sequence table name
            if sql_table_name == variables.sql_table_sequence:

                # Delete data from active table
                query_delete_rows = text(
                    f"DELETE FROM `{sql_table_name}` WHERE `Ladder ID` IN ({ladder_ids_filter_string})"
                )

            # If table name is same as sequence table name
            if sql_table_name == variables.sql_table_cas_status and account_id == None:

                # Delete data from active table
                query_delete_rows = text(
                    f"DELETE FROM `{sql_table_name}` WHERE `Unique ID` = {unique_id} AND `Status` <> 'Failed'"
                )
            elif (
                sql_table_name == variables.sql_table_cas_status and account_id != None
            ):

                # Delete data from active table
                query_delete_rows = text(
                    f"DELETE FROM `{sql_table_name}` WHERE `Unique ID` = {unique_id} AND `Status` <> 'Failed' AND `Account ID` = '{account_id}'"
                )

            result = variables.active_sqlalchemy_connection.execute(query_delete_rows)
            time.sleep(variables.sleep_time_db)
        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:
                # print(e)
                print(
                    f"Unique ID = {unique_id}, Could not delete data from active table {sql_table_name=}"
                )


# delete failed cas conditions
def purge_cas_conditions():

    try:
        # Delete data from active table
        query_delete_rows = text(
            f"DELETE FROM `{variables.sql_table_cas_status}` WHERE `Status` <> 'Pending'"
        )

        result = variables.active_sqlalchemy_connection.execute(query_delete_rows)

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(
                f" Could not failed cas conditions data from active table {variables.sql_table_cas_status}"
            )


# Get all the primary variables from DB. (Used in Recovery Mode) Also Used in Cache
def get_primary_vars_db(table_name):

    # Query to get all rows from the DB
    query_get_all_rows = text(f"SELECT * FROM `{table_name}`")

    try:
        result = variables.active_sqlalchemy_connection.execute(query_get_all_rows)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the Active Combinations, Query successfully executed: {query_get_all_rows}"
            )

        return all_rows_df
    except Exception as e:
        # print(e)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Could not get Active Combinations, Query Failed: {query_get_all_rows}"
            )

        return pd.DataFrame()

# Method to get all pending trailing stop loss orders
def get_all_pending_trailing_sl_orders():

    query_all_pending_trailing_sl = text(
        f"SELECT * FROM `{variables.sql_table_combination_status}` WHERE (`Order Type` = 'Trailing Stop Loss' AND `Status` = 'Pending')"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(
            query_all_pending_trailing_sl
        )
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Got all the Trailing Stop Loss Combination Orders Where Status Pending, Query successfully executed: {query_all_pending_trailing_sl}"
            )

        return all_rows_df
    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            # print(e)
            print(
                f"Could not get all the Trailing Stop Loss Combination Orders Where Status Pending, Query Failed: {query_all_pending_trailing_sl}"
            )

        return pd.DataFrame()

# Method to update references price in db table
def update_reference_price_in_db_and_order_book(prices_unique_id):

    # Get all the pending trailing sl order
    all_pending_trailing_sl_orders = get_all_pending_trailing_sl_orders()

    # Update Reference value in DB
    for _, row in all_pending_trailing_sl_orders.iterrows():
        # Init Variables
        unique_id = row["Unique ID"]
        action = row["Action"].strip()
        order_type = row["Order Type"].strip()
        order_time = row["Order Time"]
        entry_price = row["Entry Price"]
        trail_value = row["Trail Value"]
        trigger_price = row["Trigger Price"]

        last_update_time = datetime.datetime.now(variables.target_timezone_obj)
        reference_price = float(row["Reference Price"].strip())
        status = row["Status"]

        if action == "BUY" and (prices_unique_id[unique_id]["BUY"] != None):

            if (float(prices_unique_id[unique_id]["BUY"]) < reference_price) or (
                trigger_price == "None"
            ):
                try:
                    trigger_price = prices_unique_id[unique_id]["BUY"] + float(
                        trail_value
                    )
                    query = text(
                        f"UPDATE `{variables.sql_table_combination_status}` SET `Reference Price` = '{prices_unique_id[unique_id]['BUY']}', \
                    `Trigger Price` = '{trigger_price}', `Last Update Time` = '{last_update_time}' WHERE (`Order Type` = 'Trailing Stop Loss' AND `Order Time` = '{order_time}')"
                    )

                    result = variables.active_sqlalchemy_connection.execute(query)

                    variables.screen.update_combo_order_status_in_order_book(
                        order_time,
                        last_update_time,
                        entry_price,
                        prices_unique_id[unique_id]["BUY"],
                        status,
                        trigger_price=trigger_price,
                    )

                    # Sleep Time for DB
                    time.sleep(variables.sleep_time_db)

                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Successfully Update Reference Price, Query successfully executed: {query}"
                        )
                except Exception as e:
                    # print(e)

                    if variables.flag_debug_mode:
                        print(
                            f"Unable to Update Reference Price, Failed Query: {query}"
                        )

        elif action == "SELL" and (prices_unique_id[unique_id]["SELL"] != None):

            if (float(prices_unique_id[unique_id]["SELL"]) > reference_price) or (
                trigger_price == "None"
            ):
                try:
                    trigger_price = prices_unique_id[unique_id]["SELL"] - float(
                        trail_value
                    )

                    query = text(
                        f"UPDATE `{variables.sql_table_combination_status}` SET `Reference Price` = '{prices_unique_id[unique_id]['SELL']}', \
                        `Trigger Price` = '{trigger_price}',  `Last Update Time` = '{last_update_time}' WHERE (`Order Type` = 'Trailing Stop Loss' AND `Order Time` = '{order_time}')"
                    )

                    result = variables.active_sqlalchemy_connection.execute(query)

                    variables.screen.update_combo_order_status_in_order_book(
                        order_time,
                        last_update_time,
                        entry_price,
                        prices_unique_id[unique_id]["SELL"],
                        status,
                        trigger_price=trigger_price,
                    )

                    # Sleep Time for DB
                    time.sleep(variables.sleep_time_db)

                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Successfully Update Reference Price, Query successfully executed: {query}"
                        )
                except Exception as e:

                    if variables.flag_debug_mode:

                        print(
                            f"Unable to Update Reference Price, Failed Query: {query}"
                        )

# Method to insert dummy order in db table
def insert_dummy_order_in_order_status(unique_id,
                                        combo_contract,
                                        order_action,
                                        order_total_quantity,
                                        account_id,
                                        order_time, current_price):


    try:

        # ticker string
        ticker_str = combo_contract.symbol + "," + str(order_total_quantity) + "," + str(combo_contract.con_id)

    except Exception as e:

        pass


    # Query to insert the order into Order Status Table in DB
    insr_query = text(
        f"INSERT INTO `{variables.active_sql_db_name}`.`{variables.sql_table_order_status}` \
                    ( `Account ID`, `Unique ID`, `Order ID`, `Parent Order ID`, `Order Action`, `Target Fill`, `Current Fill`, `Avg Fill Price`,  `Order Time`,`Order Sent Time`, `Last Update time`, `Order Type`, `Status`, `Ticker`) \
                    VALUES ('{account_id}', '{unique_id}','pass','pass','{order_action}','{order_total_quantity}','{order_total_quantity}','{current_price}','{str(order_time)}','{str(order_time)}','{str(order_time)}','{str('Market' + ' ' + order_action)}', 'Filled', '{ticker_str}' )"
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



# Insert all  the information regarding one butterfly order in DB. (Used when we are placing entry order)
def insert_combination_order_in_combo_status_db(
    unique_id,
    action,
    quantity,
    order_type,
    entry_price,
    limit_price,
    trigger_price,
    reference_price,
    trail_value,
    status,
    order_time,
    ladder_id=None,
    sequence_id=None,
    atr_multiple=None,
    atr=None,
    reason_for_failed=None,
    account_id=None,
    ticker_string=None,
    bypass_rm_check=None,
    execution_engine=False,
    limit_iv=None,
    trigger_iv=None,
        actual_entry_price=None,
):
    # (unique_id, action, quantity, order_type, entry_price, tp_price, sl_price, trailing_sl,status):

    # Unique ID    Action    Quantity    Order Time    Order IDs    Last Update Time    Entry Price    Limit Price    Trigger Price    Trail Value    Status    Ladder ID    Sequence ID

    insr_query = text(
        f"INSERT INTO `{variables.active_sql_db_name}`.`{variables.sql_table_combination_status}` \
        ( `Unique ID`, `Action`, `#Lots`, `Order Time`, `Order Type`, `Order IDs`, `Last Update Time`, `Entry Price`, `Limit Price`, `Trigger Price`, `Reference Price`, `Trail Value`,\
         `Status`, `Ladder ID`, `Sequence ID`, `ATR Multiple`, `ATR`, `Reason For Failed`, `Account ID`, `Tickers`, `Bypass RM Check`, `Execution Engine`, `Limit IV`, `Trigger IV`, `Actual Entry Price` ) \
        VALUES ('{str(unique_id)}','{str(action)}','{str(quantity)}','{str(order_time)}', '{str(order_type)}', 'pass', '{str(order_time)}','{str(entry_price)}', \
        '{str(limit_price)}','{str(trigger_price)}', '{str(reference_price)}', '{str(trail_value)}', '{str(status)}', '{str(ladder_id)}', '{str(sequence_id)}', \
        '{str(atr_multiple)}', '{str(atr)}', '{reason_for_failed}', '{account_id}', '{ticker_string}', '{bypass_rm_check}', '{execution_engine}', '{limit_iv}', '{trigger_iv}', '{actual_entry_price}' ) "
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(insr_query)
        time.sleep(variables.sleep_time_db)
    except Exception as e:
        # print(e)

        if variables.flag_debug_mode:
            print(
                f"Unable to insert the identified butterfly in to database, Unique ID: {unique_id}"
            )

# Method to fetch order status from db table
def get_ticker_order_status_db(order_id):

    try:
        query_get_order_ids = text(
            f"SELECT `Ticker` FROM `{variables.sql_table_order_status}` WHERE (`Order ID` = '{order_id}')"
        )

        result = variables.active_sqlalchemy_connection.execute(query_get_order_ids)
        time.sleep(variables.sleep_time_db)
        ticker = result.fetchall()

        return ticker[0][0]
    except Exception as e:

        if variables.flag_debug_mode:
            print(e)

        return None

# Method to insert order ids in order in db able
def insert_order_ids_in_combo_status(unique_id, order_time):

    try:
        query_get_order_ids = text(
            f"SELECT `Order ID` FROM `{variables.sql_table_order_status}` WHERE (`Order Time` = '{order_time}' AND `Unique ID` = '{unique_id}')"
        )

        result = variables.active_sqlalchemy_connection.execute(query_get_order_ids)
        time.sleep(variables.sleep_time_db)
        order_ids_list = result.fetchall()

        order_ids = [order_id[0] for order_id in order_ids_list]

        order_ids = ", ".join(order_ids)

        query_insert_order_id = text(
            f"UPDATE `{variables.sql_table_combination_status}` SET `Order IDs` = '{order_ids}' WHERE (`Order Time` = '{order_time}' AND `Unique ID` = '{unique_id}')"
        )
        result = variables.active_sqlalchemy_connection.execute(query_insert_order_id)
        time.sleep(variables.sleep_time_db)
    except Exception as e:
        if variables.flag_debug_mode:
            print(e)

# Method fetch fill price of leg orders from db table
def get_avg_fill_prices_for_order_ids_db(order_time, column_name):

    try:
        query_get_order_ids = text(
            f"SELECT `{column_name}` FROM `{variables.sql_table_order_status}` WHERE (`Order Time` = '{order_time}')"
        )

        result = variables.active_sqlalchemy_connection.execute(query_get_order_ids)
        time.sleep(variables.sleep_time_db)
        values = result.fetchall()

        values_list = [values[0] for values in values]

        return values_list

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:

            print(f"Exception inside 'get_avg_fill_prices_for_order_ids_db', Exp: {e}")

        return None

# Method to get all pending orders.
def get_pending_orders():

    try:
        query_pending_orders = text(
            f"SELECT * FROM `{variables.sql_table_combination_status}` WHERE `Status` = 'Pending'"
        )
        result = variables.active_sqlalchemy_connection.execute(query_pending_orders)
        time.sleep(variables.sleep_time_db)

        df_pending_orders = pd.DataFrame(result.fetchall())

        return df_pending_orders
    except Exception as e:

        if variables.flag_debug_mode:
            print(e)
        return None

# Method to fetch sent orders in db table
def get_sent_combo_orders():
    try:
        query_pending_orders = text(
            f"SELECT * FROM `{variables.sql_table_combination_status}` WHERE `Status` = 'Sent'"
        )
        result = variables.active_sqlalchemy_connection.execute(query_pending_orders)
        time.sleep(variables.sleep_time_db)

        df_pending_orders = pd.DataFrame(result.fetchall())

        return df_pending_orders
    except Exception as e:

        if variables.flag_debug_mode:
            print(e)
        return None

# Method to get status for order ids
def get_all_order_ids_status_not_equal_filled():

    try:
        query_order_id_status_not_equal_filled = text(
            f"SELECT `Order ID` FROM `{variables.sql_table_order_status}` WHERE (NOT (`Status` = 'Filled'))"
        )
        result = variables.active_sqlalchemy_connection.execute(
            query_order_id_status_not_equal_filled
        )
        time.sleep(variables.sleep_time_db)

    except Exception as e:

        if variables.flag_debug_mode:
            print(e)

    try:
        df_order_id = pd.DataFrame(result.fetchall())

        return list(df_order_id["Order ID"])

    except Exception as e:
        return []

# Method to update status for combo orders.
def update_combination_order_status_in_db(
    unique_id,
    original_order_time,
    last_update_time,
    entry_price,
    status,
    exit_position_qty=None,
    exit_type=None,
        actual_entry_price = None,
):

    try:

        if exit_type == None:
            query_update = text(
                f"UPDATE `{variables.sql_table_combination_status}` SET `Last Update Time` = '{last_update_time}', `Entry Price` = '{entry_price}', `Status` = '{status}', `Actual Entry Price` = '{actual_entry_price}' WHERE (`Unique ID` = '{unique_id}' AND `Order Time`= '{original_order_time}') "
            )
        else:
            query_update = text(
                f"UPDATE `{variables.sql_table_combination_status}` SET `Action` = '{exit_type}', `#Lots` = '{exit_position_qty}', `Last Update Time` = '{last_update_time}', `Entry Price` = '{entry_price}', `Status` = '{status}', `Actual Entry Price` = '{actual_entry_price}' WHERE (`Unique ID` = '{unique_id}' AND `Order Time`= '{original_order_time}') "
            )
        result = variables.active_sqlalchemy_connection.execute(query_update)

        # Sleep Time for DB
        time.sleep(variables.sleep_time_db)

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print("Inside update_combination_order_status_in_db (My Sql IO) error:", e)

# Method to get order times for combo
def get_order_times_for_combination(unique_id):

    query = text(
        f"SELECT `Order Time` FROM `{variables.sql_table_combination_status}` WHERE `Unique ID` = '{unique_id}'"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_order_times = result.fetchall()

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID: {unique_id}, Successfully executed query: {query}, to get_order_times_for_combination."
            )
    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            pass
        print(
            f"Unique ID: {unique_id}, Inside MySql IO get_order_times_for_combination unable to execute the query: {query}, Exception : {e}"
        )

    try:
        # Making DataFrame
        all_order_times_df = pd.DataFrame(all_order_times)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Unique ID= {unique_id}, Got order times: {all_order_times_df}")
        return list(all_order_times_df["Order Time"])

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID: {unique_id}, Inside MySql IO get_order_times_for_combination No orders were found. Exception : {e} "
            )

        return pd.DataFrame()

# Method to get order book cleaned time
def get_order_book_cleaned_time():

    query = text(
        f"SELECT `Order Book Cleaned Time` FROM `{variables.sql_table_meta_data}`"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        order_book_cleaned_time = result.fetchone()[0]

        return order_book_cleaned_time
    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Inside MySql IO get_order_book_cleaned_time Exception : {e} ")

        return None

# Method to update order book cleaned time
def update_order_book_cleaned_time(update_time):

    query = text(
        f"UPDATE `{variables.sql_table_meta_data}` SET `Order Book Cleaned Time`='{update_time}'"
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Inside MySql IO update_order_book_cleaned_time Exception : {e} ")

# Method to get all combo orders form db table
def get_all_combinaiton_orders_from_db(order_book_cleaned_time=None):

    # When Order Book Cleaned Time is given and Not Given
    if order_book_cleaned_time == None:
        query = text(f"SELECT * FROM `{variables.sql_table_combination_status}`")
    else:
        query = text(
            f"SELECT * FROM `{variables.sql_table_combination_status}` WHERE NOT ( (`Status`='Filled' OR `Status`='Cancelled' OR `Status`='Failed')  AND (`Last Update Time` <= '{order_book_cleaned_time}'))"
        )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Query successfully executed: ", query)

        return all_rows_df
    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Inside MySql IO update_order_book_cleaned_time Exception : {e} ")
        return pd.DataFrame()


################ Old code not For this project ######################

# Fetches and Returns the last saved 'State' from {variables.sql_table_identified_butterfly}, otherwise returns 'None'
def get_state_db(unique_id):

    try:

        # Query to get State from 'variables.sql_table_identified_butterfly'  in DB
        query = text(
            f"SELECT `State` FROM {variables.sql_table_identified_butterfly} WHERE `Unique ID` = '{unique_id}'"
        )
        result = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        current_state = result.fetchone()[0]
        current_state = int(current_state)
        return current_state

    except:
        if variables.flag_debug_mode:
            print(
                f"Could not get the last saved 'State' from {variables.sql_table_identified_butterfly} table"
            )
        return None


# Update the last saved 'State' in {variables.sql_table_identified_butterfly} for {unique_id} table
def update_state_db(unique_id, state):

    try:
        update_state_query = text(
            f"UPDATE {variables.sql_table_identified_butterfly} SET `State` = '{state}' WHERE `Unique ID` = '{unique_id}'"
        )
        result = variables.active_sqlalchemy_connection.execute(update_state_query)
        time.sleep(variables.sleep_time_db)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID = {unique_id}, State Updated in Table '{variables.sql_table_identified_butterfly}' to {state}"
            )

    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Inside MySql IO update_state_db (Unable to Update State in Database)Exception : {e} "
            )


# Get list of orderid present in database
def order_id_database():

    # Print to console
    if variables.flag_debug_mode:
        print(f"Getting all the Order IDs from Database")

    query_orderId_database = text(
        f"SELECT `Order ID` FROM `{variables.sql_table_order_status}`"
    )
    result_order_id_database = variables.active_sqlalchemy_connection.execute(
        query_orderId_database
    )
    order_id_db = result_order_id_database.fetchall()
    order_id_db = [int(a[0]) for a in order_id_db]

    # Print to console
    if variables.flag_debug_mode:
        print(f"All Order IDs in Database = {order_id_db}")

    return order_id_db

# Method to get open order ids
def get_open_order_ids(unique_id):

    query = text(
        f"SELECT `Order ID` from `{variables.sql_table_order_status}` WHERE ((`Unique ID` = '{unique_id}') AND (`Status`='Submitted' or `Status`='PreSubmitted'))"
    )

    result_query = variables.active_sqlalchemy_connection.execute(query)
    time.sleep(variables.sleep_time_db)

    try:
        df_open_orders = pd.DataFrame(result_query.fetchall())
        df_open_orders.columns = result_query.keys()
        return list(df_open_orders["Order ID"])
    except:
        if variables.flag_debug_mode:
            print("No open orders found")
        return []

# Method to check if all sub order got filled or not for unique id
def check_all_orders_filled(unique_id, order_time):

    query = text(
        f"SELECT COUNT(`Status`) FROM `{variables.sql_table_order_status}` WHERE ( (`Unique ID` = '{unique_id}') AND (`Order Time` ='{order_time}') AND (NOT (`Status` = 'Filled' OR `Status` = 'Inactive' OR `Status` = 'Cancelled')))"
    )

    result_query = variables.active_sqlalchemy_connection.execute(query)
    time.sleep(variables.sleep_time_db)

    try:
        result = result_query.fetchone()[0]
        return result
    except:
        if variables.flag_debug_mode:
            print("Unable to check orders status for sending next orders")
        return None

# Method to update pending order as cancelled
def mark_pending_combo_order_cancelled(
    unique_id, order_time, status, last_update_time, updated_status, reason_for_failed
):

    query = text(
        f"UPDATE `{variables.sql_table_combination_status}` SET `Status`='{updated_status}', `Reason For Failed`='{reason_for_failed}', `Last Update Time`='{last_update_time}' WHERE `Unique ID` = '{unique_id}' AND `Order Time` = '{order_time}' AND `Status` = '{status}' "
    )

    try:
        result_query = variables.active_sqlalchemy_connection.execute(query)

        time.sleep(variables.sleep_time_db)

    except:
        if variables.flag_debug_mode:
            print(
                f"Unable to mark 'Pending' combo orders 'Cancelled' in DB, Unique ID: {unique_id}, Order Time :{order_time}"
            )
        return None

# Method to get all cancelled or filled orders
def get_all_cancelled_or_filled_combo_order():

    query = text(
        f"SELECT `Order Time` FROM `{variables.sql_table_combination_status}` WHERE (`Status`='Filled' OR `Status`='Cancelled' OR `Status`='Failed') "
    )

    try:
        result_query = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        order_ids_list = result_query.fetchall()
        order_ids = [order_id[0] for order_id in order_ids_list]

        return order_ids

    except:
        # Print to console
        if variables.flag_debug_mode:
            print("Unable to get filled or cancelled combination orders")
        return []

# Method to update highest and lowest price in cache tble
def update_high_low_price_in_db(unique_id, high, low, is_intraday):

    if is_intraday:
        high_col = "1-Day High"
        low_col = "1-Day Low"
    else:
        high_col = "N-Day High"
        low_col = "N-Day Low"

    query = text(
        f"UPDATE `{variables.sql_table_cache}` SET `{high_col}` = '{high}', `{low_col}` = '{low}' \
                    WHERE `Unique ID` = '{unique_id}'"
    )

    try:
        result_query = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        if variables.flag_debug_mode:
            print("Updated {unique_id} {is_intraday=} High Low price in db.")
    except Exception as e:
        if variables.flag_debug_mode:
            print("Unable to update high low price for {unique_id=} {is_intraday=}")
            print(e)

# Method to insert highest lowest prices in db table
def insert_high_low_prices_in_db(
    unique_id, n_day_high="N/A", n_day_low="N/A", day_high="N/A", day_low="N/A"
):

    query = text(
        f"INSERT INTO `{variables.sql_table_cache}` ( `Unique ID` , `N-Day High` , `N-Day Low`, \
                         `1-Day High`, `1-Day Low` ) VALUES ( '{unique_id}', '{n_day_high}', '{n_day_low}', '{day_high}', '{day_low}') "
    )

    try:
        result_query = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        if variables.flag_debug_mode:
            print("Inserted Price for {unique_id} in db.")
    except Exception as e:

        if variables.flag_debug_mode:
            print(e)

# Method to update last updated time
def update_last_longterm_or_intraday_updated_time(is_intraday):

    # Init
    if is_intraday:
        col_name = "CAS Intraday Updated Time"
    else:
        col_name = "CAS Longterm Updated Time"

    # Current Time
    current_time = datetime.datetime.now(variables.target_timezone_obj)

    # Query to update time
    query = text(
        f"UPDATE `{variables.sql_table_meta_data}` SET `{col_name}` = '{str(current_time)}' "
    )

    try:
        result_query = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        if variables.flag_debug_mode:
            print(f"Updated Last update time for {col_name} in db.")
    except Exception as e:

        if variables.flag_debug_mode:

            print(e)

# Method to replace evaluation unique id for cas condition in db table
def replace_eval_unique_id_cas_condition_db(
    old_eval_unique_id, new_eval_unique_id, table_name
):
    # Query to update time
    query = text(
        f"UPDATE `{table_name}` SET `Evaluation Unique ID` = '{str(new_eval_unique_id)}' WHERE `Evaluation Unique ID` = {old_eval_unique_id}"
    )

    try:
        result_query = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        if variables.flag_debug_mode:
            print(f"Query Executed successfully : {query}")
    except Exception as e:

        if variables.flag_debug_mode:
            print(f"Query Failed : {query}")

    column_name = None

    # if table is cas status then set column for it
    if table_name == variables.sql_table_cas_status:

        column_name = "Trading Combination Unique ID"

    else:

        column_name = "Trading Unique ID"

    # Query to update time
    query = text(
        f"UPDATE `{table_name}` SET `{column_name}` = '{str(new_eval_unique_id)}' WHERE `{column_name}` = {old_eval_unique_id}"
    )

    try:
        result_query = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        if variables.flag_debug_mode:
            print(f"Query Executed successfully : {query}")
    except Exception as e:

        if variables.flag_debug_mode:
            print(f"Query Failed : {query}")

# # Method to update cas condition table as failed
def failed_eval_unique_id_cas_condition_db(eval_unique_id):
    # Query to update time
    query = text(
        f"UPDATE `{variables.sql_table_cas_status}` SET `Status` = 'Failed', `Reason For Failed` = 'Evaluation Unique ID Deleted' WHERE `Evaluation Unique ID` = '{eval_unique_id}' OR `Trading Combination Unique ID`='{eval_unique_id}'"
    )

    try:
        result_query = variables.active_sqlalchemy_connection.execute(query)
        time.sleep(variables.sleep_time_db)

        if variables.flag_debug_mode:
            print(f"Query Executed successfully : {query}")
    except Exception as e:

        if variables.flag_debug_mode:
            print(f"Query Failed : {query}")

# Method to insert cas condition order in db table
def insert_cas_condition_in_db(
    unique_id,
    cas_type,
    condition,
    condition_reference_price,
    condition_reference_position,
    condition_trigger_price,
    status,
    order_type=None,
    order_lots=None,
    order_limit_price=None,
    order_trigger_price=None,
    order_trail_value=None,
    trading_combination_unique_id=None,
    atr_multiple=None,
    atr=None,
    target_position=None,
    account_id=None,
    reason_for_failed=None,
    bypass_rm_check=None,
    flag_execution_engine=None,
    evalaution_unique_id=None,
    series_id=None,
):

    # Query to insert
    insr_query = text(
        f"INSERT INTO `{variables.active_sql_db_name}`.`{variables.sql_table_cas_status}` \
        ( `Unique ID`, `Trading Combination Unique ID`, `Condition`, `CAS Condition Type`, `Condition Reference Price`, `Reference Position` , `Target Position`, `Condition Trigger Price`, `Order Type`, \
        `#Lots`, `Limit Price`, `Order Trigger Price`, `Trail Value`, `Status`, `ATR Multiple`, `ATR`, `Account ID`, `Reason For Failed`, `Bypass RM check`, `Execution Engine`, `Evaluation Unique ID`, `Series ID` ) \
        VALUES ('{str(unique_id)}','{str(trading_combination_unique_id)}','{str(condition)}','{str(cas_type)}','{str(condition_reference_price)}', '{str(condition_reference_position)}', \
         '{str(target_position)}', '{str(condition_trigger_price)}', '{str(order_type)}', '{str(order_lots)}','{str(order_limit_price)}', \
         '{str(order_trigger_price)}',  '{str(order_trail_value)}', '{str(status)}', '{str(atr_multiple)}', '{str(atr)}', '{account_id}', '{reason_for_failed}', \
         '{bypass_rm_check}', '{flag_execution_engine}', '{evalaution_unique_id}', '{series_id}' ) "
    )

    # Executing Query
    try:
        result = variables.active_sqlalchemy_connection.execute(insr_query)
        time.sleep(variables.sleep_time_db)
    except Exception as e:
        if variables.flag_debug_mode:

            print(
                f"Unable to insert the CAS condition {unique_id=} {cas_type} {condition=} {status=} in to database, Unique ID: {unique_id}"
            )
            print(insr_query)

# Method to check if cas conditional order exist for unique id or not
def do_cas_condition_exists_for_unique_id_in_db(unique_id, condition_type=None):

    get_count_query = text(
        f"SELECT COUNT(*) FROM `{variables.active_sql_db_name}`.`{variables.sql_table_cas_status}` \
         WHERE (`Unique ID` = '{unique_id}'  AND (`Status` = 'Pending' OR `Status` = 'Failed')) "
    )

    if condition_type != None:
        get_count_query = text(
            f"SELECT COUNT(*) FROM `{variables.active_sql_db_name}`.`{variables.sql_table_cas_status}` \
                 WHERE (`Unique ID` = '{unique_id}'  AND (`Status` = 'Pending') AND `CAS Condition Type`='{condition_type}') "
        )

    try:
        result = variables.active_sqlalchemy_connection.execute(get_count_query)
        time.sleep(variables.sleep_time_db)

        # Get count
        result = result.fetchone()[0]

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, Query successfully executed: {get_count_query}"
            )

        return result
    except Exception as e:
        if variables.flag_debug_mode:

            print(e)
            print(
                f"Unable to Execute the query to check if condition exists in CAS Status Table for Unique ID: {unique_id}, Query : {get_count_query}"
            )

        # Returning 100 so the condition can not be added in CAS Add or Switch
        return 100

# Method to check if conditional series exist for unique id
def do_cas_condition_series_exists_for_unique_id_in_db(unique_id):

    get_count_query = text(
        f"SELECT COUNT(*) FROM `{variables.active_sql_db_name}`.`{variables.sql_table_conditional_series}` \
         WHERE (`Unique ID` = '{unique_id}'  AND (`Status` <> 'Completed') AND (`Status` <> 'Terminated') AND (`Status` <> 'Parked')) "
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(get_count_query)
        time.sleep(variables.sleep_time_db)

        # Get count
        result = result.fetchone()[0]

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, Query successfully executed: {get_count_query}"
            )

        return result
    except Exception as e:
        if variables.flag_debug_mode:

            print(e)
            print(
                f"Unable to Execute the query to check if condition exists in CAS Status Table for Unique ID: {unique_id}, Query : {get_count_query}"
            )

        # Returning 100 so the condition can not be added in CAS Add or Switch
        return 100

# Method to get all cas conditional order from db table
def get_all_cas_conditions_from_db(only_pending=False):

    # Only want the pending conditions
    if only_pending:
        query = text(
            f"SELECT * FROM `{variables.active_sql_db_name}`.`{variables.sql_table_cas_status}` WHERE `Status` = 'Pending' OR `Status` = 'Failed'"
        )

    else:
        query = text(
            f"SELECT * FROM `{variables.active_sql_db_name}`.`{variables.sql_table_cas_status}`"
        )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Fetching all the results. (list of tuples)
        all_rows = result.fetchall()

        # Making DataFrame
        all_rows_df = pd.DataFrame(all_rows)

        # Print to console
        if variables.flag_debug_mode:
            print(f"Query successfully executed: {query}")

        return all_rows_df
    except Exception as e:
        if variables.flag_debug_mode:

            print(e)
            print(
                f"Unable to Execute the query to check if condition exists in CAS Status Table for Query : {query}"
            )

        # Returning Empty DF
        return pd.DataFrame()


# Delete CAS Condition from cas_condition_table_dbs for unique id
def delete_cas_condition_from_db_for_unique_id(unique_id):

    query = text(
        f"DELETE FROM `{variables.sql_table_cas_status}` WHERE `Unique ID` = '{unique_id}' "
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, Removed CAS Condition from DB. Query successfully executed: {query}"
            )

    except Exception as e:
        if variables.flag_debug_mode:

            print(e)
            print(
                f"Unable to Execute the query to DELETE the CAS Condition from CAS Status Table for Unique ID: {unique_id}, Query : {query}"
            )


# Delete all cas legs for unique id
def delete_cas_legs_from_db_for_unique_id(unique_id):

    query = text(
        f"DELETE FROM `{variables.sql_table_cas_legs}` WHERE `Unique ID` = '{unique_id}' "
    )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, Removed CAS Legs from DB. Query successfully executed: {query}"
            )

    except Exception as e:
        if variables.flag_debug_mode:

            print(e)
            print(
                f"Unable to Execute the query to DELETE the CAS Legs from CAS Legs Table for Unique ID: {unique_id}, Query : {query}"
            )


# Update CAS condition status for unique id
def update_cas_condition_status(unique_id, status, account_id=None):

    # Checking if account id is not none
    if account_id == None:

        query = text(
            f"UPDATE `{variables.sql_table_cas_status}` SET `Status` = '{status}' WHERE `Unique ID` = '{unique_id}' AND `Status` <> 'Failed'"
        )

    else:

        query = text(
            f"UPDATE `{variables.sql_table_cas_status}` SET `Status` = '{status}' WHERE `Unique ID` = '{unique_id}' AND `Status` <> 'Failed' AND `Account ID` = '{account_id}'"
        )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, updated the CAS condition status to {status}. Query successfully executed: {query}"
            )

    except Exception as e:
        if variables.flag_debug_mode:

            print(e)
            print(
                f"Unable to Execute the query to UPDATE the CAS status for Unique ID: {unique_id}, Query : {query}"
            )


# Update CAS condition status for unique id
def update_cas_condition_reason_for_failed(unique_id, reason, account_id=None):

    # Checking if account id is not none
    if account_id == None:

        query = text(
            f"UPDATE `{variables.sql_table_cas_status}` SET `Reason For Failed` = '{reason}' WHERE `Unique ID` = '{unique_id}' AND `Status` = 'Failed'"
        )

    else:

        query = text(
            f"UPDATE `{variables.sql_table_cas_status}` SET `Reason For Failed` = '{reason}' WHERE `Unique ID` = '{unique_id}' AND `Status` = 'Failed' AND `Account ID` = '{account_id}'"
        )

    try:
        result = variables.active_sqlalchemy_connection.execute(query)

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Unique ID= {unique_id}, updated the CAS condition reason for failed to {reason}. Query successfully executed: {query}"
            )

    except Exception as e:
        if variables.flag_debug_mode:

            print(e)
            print(
                f"Unable to Execute the query to UPDATE the CAS reason for failed for Unique ID: {unique_id}, Query : {query}"
            )
