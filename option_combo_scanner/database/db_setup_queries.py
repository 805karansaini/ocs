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
            `description` VARCHAR(255),
            `status` VARCHAR(35),
            `config_name` VARCHAR(45)
            
        );"""

query4 = """CREATE TABLE IF NOT EXISTS `config_legs_table` (
            `config_leg_id` INT AUTO_INCREMENT PRIMARY KEY,
            `instrument_id` INT,
            `config_id` INT, 
            `leg_number` INT,
            `quantity` INT,
            `right` VARCHAR(50),
            `action` VARCHAR(50),
            `delta_range_min` DECIMAL(10, 8),
            `delta_range_max` DECIMAL(10, 8),
            `dte_range_min` INT,
            `dte_range_max` INT,
            FOREIGN KEY (`config_id`) REFERENCES `config_table`(`config_id`) ON DELETE CASCADE
        );"""

query5 = """CREATE TABLE IF NOT EXISTS `combination_table` (
            `combo_id` INT AUTO_INCREMENT PRIMARY KEY,
            `config_id` INT,
            `number_of_legs` INT,
            `combo_net_delta` DECIMAL(8, 2),
            `max_profit` VARCHAR(20),
            `max_loss` VARCHAR(20),
            `vega` VARCHAR(20),
            `theta` VARCHAR(20),
            `gamma` VARCHAR(20),
            `vanna` VARCHAR(20),
            `charm` VARCHAR(20),
            `vomma` VARCHAR(20),
            `veta` VARCHAR(20),
            `speed` VARCHAR(20),
            `zomma` VARCHAR(20),
            `color` VARCHAR(20),
            `ultima` VARCHAR(20),
            `correlation_delta` VARCHAR(20),
            `cross_gamma` VARCHAR(20),
            `cross_vanna` VARCHAR(20),
            `cross_volga` VARCHAR(20),
            FOREIGN KEY (`config_id`) REFERENCES `config_table`(`config_id`) ON DELETE CASCADE
    );"""

query6 = """CREATE TABLE IF NOT EXISTS `legs_table` (
            `leg_id` INT AUTO_INCREMENT PRIMARY KEY,
            `combo_id` INT,
            `leg_number` INT,
            `qty` INT,
            `action` VARCHAR(15),
            `symbol` VARCHAR(50),
            `sec_type` VARCHAR(20),
            `exchange` VARCHAR(20),
            `currency` VARCHAR(20),
            `expiry` VARCHAR(20),
            `strike` DECIMAL(10, 2),
            `right` VARCHAR(10),
            `multiplier` INT,
            `trading_class` VARCHAR(20),
            `primary_exchange` VARCHAR(20),
            `con_id` VARCHAR(20),
            `underlying_conid` VARCHAR(20),
            `delta_found` DECIMAL(10, 8),
            FOREIGN KEY (`combo_id`) REFERENCES `combination_table`(`combo_id`) ON DELETE CASCADE
        );"""

query7 = """CREATE TABLE IF NOT EXISTS `config_indicator_relation` (
            `leg_number` INT,
            `config_id` INT,
            `instrument_id` INT,
            `expiry` VARCHAR(15),
            `unix_time` BIGINT,
            PRIMARY KEY (`config_id`, `leg_number`, `instrument_id`, `expiry`, `unix_time`),
            FOREIGN KEY (`config_id`) REFERENCES `config_table`(`config_id`) ON DELETE CASCADE,
            FOREIGN KEY (`instrument_id`) REFERENCES `instrument_table`(`instrument_id`) ON DELETE CASCADE
        );"""

query8 = """CREATE TABLE IF NOT EXISTS `indicator_table` (
        `indicator_id` INT AUTO_INCREMENT PRIMARY KEY,
        `instrument_id` INT,
        `expiry` VARCHAR(15), 
        
        `underlying_conid` VARCHAR(20),
        `symbol` VARCHAR(15),
        `sec_type` VARCHAR(15), 
        `exchange` VARCHAR(20),
        `multiplier` INT,
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


all_queries = [query2, query3, query4, query5, query6, query7, query8]
