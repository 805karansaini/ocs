import configparser

# Read the config file
config = configparser.ConfigParser()
config.read("config.ini")

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
        `config_id`  INT, 
        `leg_number` INT,
        `action` VARCHAR(50),
        `delta_range_min` DECIMAL(10, 8),
        `delta_range_max` DECIMAL(10, 8),
        FOREIGN KEY (`config_id`) REFERENCES `config_table`(`config_id`) ON DELETE CASCADE
    );"""

query5 = """CREATE TABLE IF NOT EXISTS `combination_table` (
        `combo_id` INT AUTO_INCREMENT PRIMARY KEY,
        `instrument_id` INT,
        `number_of_legs` INT,
        `symbol` VARCHAR(50),
        `sec_type` VARCHAR(20),
        `expiry` VARCHAR(20),
        `right` VARCHAR(20),
        `multiplier` INT,
        `trading_class` VARCHAR(20),
        `currency` VARCHAR(20),
        `exchange` VARCHAR(20),
        `combo_net_delta` DECIMAL(8, 8),
        `max_profit` DECIMAL(8, 8),
        `max_loss` DECIMAL(8, 8),
        `max_profit_max_loss_ratio` DECIMAL(8, 8),
        `primary_exchange` VARCHAR(10),
        FOREIGN KEY (`instrument_id`) REFERENCES `instrument_table`(`instrument_id`) ON DELETE CASCADE
    );"""

query6 = """CREATE TABLE IF NOT EXISTS `legs_table` (
        `leg_id` INT AUTO_INCREMENT PRIMARY KEY,
        `combo_id` INT,
        `leg_number` INT,
        `con_id` VARCHAR(15),
        `strike` VARCHAR(15),
        `qty` VARCHAR(15),
        `delta_found` DECIMAL(10, 8),
        `action` VARCHAR(15),
        `delta_range_min` DECIMAL(10, 8),
        `delta_range_max` DECIMAL(10, 8),
        FOREIGN KEY (`combo_id`) REFERENCES `combination_table`(`combo_id`) ON DELETE CASCADE
    );"""

query7 = """CREATE TABLE IF NOT EXISTS `indicator_table` (
        `indicator_id` INT AUTO_INCREMENT PRIMARY KEY,
        `symbol` VARCHAR(15),
        `sec_type` VARCHAR(15), 
        `expiry` VARCHAR(15), 
        `hv` VARCHAR(15),
        `iv` VARCHAR(15),
        `hv_iv` VARCHAR(15),
        `rr_25` VARCHAR(15),
        `rr_50` VARCHAR(15),
        `rr_25_50` VARCHAR(15),
        `rr_change_last_close` VARCHAR(15),
        `max_pain` VARCHAR(15),
        `min_pain` VARCHAR(15),
        `avg_iv` VARCHAR(15),
        `avg_hv` VARCHAR(15),
        `open_interest_support` VARCHAR(15),
        `open_interest_resistance` VARCHAR(15),
        `put_volume` VARCHAR(15),
        `call_volume` VARCHAR(15),
        `put_call_volume_ratio` VARCHAR(15),
        `put_call_volume_average` VARCHAR(15),
        `change_underlying_option_price` VARCHAR(15),
        `change_underlying_option_price_14_days` VARCHAR(15),
        `pc_change` VARCHAR(15),
        `iv_change` VARCHAR(15),
        `pc_change_iv_change` VARCHAR(15)
    );"""

all_queries = [query2, query3, query4, query5, query6, query7]
