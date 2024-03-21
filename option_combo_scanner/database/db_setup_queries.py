import configparser

# Read the config file
config = configparser.ConfigParser()
config.read("option_scanner_user_inputs.ini")

dbconfig = config["Database"]

DB_NAME = dbconfig["database"]
query0 = f"DROP DATABASE IF EXISTS {DB_NAME};"
query1 = f"CREATE DATABASE IF NOT EXISTS {DB_NAME};"

query2 = """CREATE TABLE IF NOT EXISTS `instrument_table` (
        `instrument_id` INT AUTO_INCREMENT PRIMARY KEY,
        `symbol` VARCHAR(50),
        `sec_type` VARCHAR(20),
        `multiplier` INT,
        `exchange` VARCHAR(20),
        `trading_class` VARCHAR(20),
        `currency` VARCHAR(20),
        `conid` VARCHAR(20),
        `primary_exchange` VARCHAR(20)
    );"""

query3 = """CREATE TABLE IF NOT EXISTS `config_table` (
        `config_id` INT AUTO_INCREMENT PRIMARY KEY,
        `no_of_leg` INT,
        `right` VARCHAR(50),
        `list_of_dte` VARCHAR(50)
    );"""

query4 = """CREATE TABLE IF NOT EXISTS `config_legs_table` (
        `config_leg_id` INT AUTO_INCREMENT PRIMARY KEY,
        `instrument_id` INT,
        `config_id`  INT, 
        `leg_number` INT,
        `right` VARCHAR(50),
        `action` VARCHAR(50),
        `delta_range_min` DECIMAL(10, 8),
        `delta_range_max` DECIMAL(10, 8),
        `dte_range_min` DECIMAL(10, 8),
        `dte_range_max` DECIMAL(10, 8),
        FOREIGN KEY (`instrument_id`) REFERENCES `instrument_table`(`instrument_id`) ON DELETE CASCADE,
        FOREIGN KEY (`config_id`) REFERENCES `config_table`(`config_id`) ON DELETE CASCADE
    );"""

query5 = """CREATE TABLE IF NOT EXISTS `combination_table` (
        `combo_id` INT AUTO_INCREMENT PRIMARY KEY,
        `instrument_id` INT,
        `config_id` INT,
        `number_of_legs` INT,
        `symbol` VARCHAR(50),
        `sec_type` VARCHAR(20),
        `expiry` VARCHAR(20),
        `right` VARCHAR(20),
        `multiplier` INT,
        `trading_class` VARCHAR(20),
        `currency` VARCHAR(20),
        `exchange` VARCHAR(20),
        `combo_net_delta` DECIMAL(8, 6),
        `max_profit` VARCHAR(20),
        `max_loss` VARCHAR(20),
        `max_profit_max_loss_ratio` VARCHAR(20),
        `primary_exchange` VARCHAR(10),
        FOREIGN KEY (`instrument_id`) REFERENCES `instrument_table`(`instrument_id`) ON DELETE CASCADE,
        FOREIGN KEY (`config_id`) REFERENCES `config_table`(`config_id`) ON DELETE CASCADE
    );"""

query6 = """CREATE TABLE IF NOT EXISTS `legs_table` (
        `leg_id` INT AUTO_INCREMENT PRIMARY KEY,
        `instrument_id` INT,
        `combo_id` INT,
        `leg_number` INT,
        `con_id` VARCHAR(15),
        `strike` VARCHAR(15),
        `qty` VARCHAR(15),
        `delta_found` DECIMAL(10, 8),
        `right` VARCHAR(50),
        `action` VARCHAR(15),
        `delta_range_min` DECIMAL(10, 8),
        `delta_range_max` DECIMAL(10, 8),
        `dte_range_min` DECIMAL(10, 8),
        `dte_range_max` DECIMAL(10, 8),
        FOREIGN KEY (`instrument_id`) REFERENCES `instrument_table`(`instrument_id`) ON DELETE CASCADE,
        FOREIGN KEY (`combo_id`) REFERENCES `combination_table`(`combo_id`) ON DELETE CASCADE
    );"""


query7 = """CREATE TABLE IF NOT EXISTS `indicator_table` (
        `indicator_id` INT AUTO_INCREMENT PRIMARY KEY,
        `instrument_id` INT,
        `underlying_conid` VARCHAR(20),
        `symbol` VARCHAR(15),
        `sec_type` VARCHAR(15), 
        `expiry` VARCHAR(15), 
        `multiplier` INT,
        `exchange` VARCHAR(20),
        `trading_class` VARCHAR(20),

        `hv` VARCHAR(15),
        `iv_d1` VARCHAR(15),
        `iv_d2` VARCHAR(15),
        `avg_iv` VARCHAR(15),
        `rr_d1` VARCHAR(15),
        `rr_d2` VARCHAR(15),
        `avg_iv_avg_14d` VARCHAR(15),
        `change_rr_d1_1D` VARCHAR(15),
        `change_rr_d2_1D` VARCHAR(15),
        `change_rr_d1_14D` VARCHAR(15),
        `change_rr_d2_14D` VARCHAR(15),
        `hv_14d_avg_14d` VARCHAR(15),
        `put_call_ratio_current` VARCHAR(15),
        `put_call_ratio_avg` VARCHAR(15),
        `pc_change` VARCHAR(15),

        `hv_14d_avg_iv` VARCHAR(15),


        `rr_25_50` VARCHAR(15),
        `rr_change_last_close` VARCHAR(15),
        `max_pain` VARCHAR(15),
        `min_pain` VARCHAR(15),
        `avg_hv` VARCHAR(15),
        `open_interest_support` VARCHAR(15),
        `open_interest_resistance` VARCHAR(15),
        `put_volume` VARCHAR(15),
        `call_volume` VARCHAR(15),
        
        `Change_underlying_options_price_today` VARCHAR(15),
        `chg_uderlying_opt_price_14d` VARCHAR(15),
        
        `change_in_iv` VARCHAR(15),
        `pc_change_iv_change` VARCHAR(15),
        FOREIGN KEY (`instrument_id`) REFERENCES `instrument_table`(`instrument_id`) ON DELETE CASCADE
    );"""




# TODO exchange
query7 = """CREATE TABLE IF NOT EXISTS `indicator_table` (

        `indicator_id` INT AUTO_INCREMENT PRIMARY KEY,
        `instrument_id` INT,
        `underlying_conid` VARCHAR(20),
        `symbol` VARCHAR(15),
        `sec_type` VARCHAR(15), 
        `expiry` VARCHAR(15), 
        `multiplier` INT,
        `exchange` VARCHAR(20),
        `trading_class` VARCHAR(20),

        `current_underlying_hv_value` VARCHAR(80),
        `average_underlying_hv_over_n_days` VARCHAR(80),
        `absoulte_change_in_underlying_over_one_day` VARCHAR(80),
        `absoulte_change_in_underlying_over_n_days` VARCHAR(80),
        `percentage_change_in_underlying_over_n_days` VARCHAR(80),
        
        `current_iv_d1` VARCHAR(80),
        `current_iv_d2` VARCHAR(80),
        `current_avg_iv` VARCHAR(80),
        `absolute_change_in_avg_iv_since_yesterday` VARCHAR(80),
        `percentage_change_in_avg_iv_since_yesterday` VARCHAR(80),
        `avg_iv_over_n_days` VARCHAR(80), 

        `current_rr_d1` VARCHAR(80), 
        `current_rr_d2` VARCHAR(80), 
        `percentage_change_in_rr_since_yesterday_d1` VARCHAR(80), 
        `percentage_change_in_rr_since_yesterday_d2` VARCHAR(80), 
        `percentage_change_in_rr_since_14_day_d1` VARCHAR(80), 
        `percentage_change_in_rr_since_14_day_d2` VARCHAR(80), 
        
        `max_pain_strike` VARCHAR(80),
        `min_pain_strike` VARCHAR(80),
        `oi_support_strike` VARCHAR(80),
        `oi_resistance_strike` VARCHAR(80),

        `chg_in_call_opt_price_since_yesterday_d1` VARCHAR(80), 
        `chg_in_call_opt_price_since_yesterday_d2` VARCHAR(80), 
        `chg_in_put_opt_price_since_yesterday_d1` VARCHAR(80), 
        `chg_in_put_opt_price_since_yesterday_d2` VARCHAR(80), 
        
        `chg_in_call_opt_price_since_nth_day_d1` VARCHAR(80), 
        `chg_in_call_opt_price_since_nth_day_d2` VARCHAR(80), 
        `chg_in_put_opt_price_since_nth_day_d1` VARCHAR(80), 
        `chg_in_put_opt_price_since_nth_day_d2` VARCHAR(80), 
        
        `put_call_volume_ratio_current_day` VARCHAR(80),
        `put_call_volume_ratio_average_over_n_days` VARCHAR(80),
        `absolute_pc_change_since_yesterday` VARCHAR(80),

        FOREIGN KEY (`instrument_id`) REFERENCES `instrument_table`(`instrument_id`) ON DELETE CASCADE
    );"""

# TODO ARYAN:  DELTEE all indicators row when instrument is deete
all_queries = [query2, query3, query4, query5, query6, query7]
