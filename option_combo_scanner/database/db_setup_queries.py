import configparser

# Read the config file
config = configparser.ConfigParser()
config.read("config.ini")

dbconfig = config["Database"]

DB_NAME = dbconfig["database"]
query0 = f"""DROP DATABASE IF EXISTS {DB_NAME};"""
query1 = f"""CREATE DATABASE IF NOT EXISTS {DB_NAME};"""
query2 = f"""CREATE TABLE IF NOT EXISTS `order_specs` (
        `UniqueID` INT AUTO_INCREMENT PRIMARY KEY,
        `AccountID` VARCHAR(50),
        `Ticker` VARCHAR(50),
        `SecType` VARCHAR(20),
        `Exchange` VARCHAR(20),
        `Currency` VARCHAR(20),
        `Conid` VARCHAR(20),
        `RiskPercentage` VARCHAR(50),
        `RiskDollar` VARCHAR(50),
        `NetLiquidationValue` VARCHAR(50),
        `EntryPrice` DECIMAL(18, 2),
        `TP1Price` DECIMAL(18, 2),
        `TP2Price` VARCHAR(50),
        `SL1Price` DECIMAL(18, 2),
        `SL2Price` VARCHAR(50),
        
        `EntryQuantity` VARCHAR(20),

        `Status` VARCHAR(50),

        `EntryQuantityFilled` VARCHAR(20),
        `AverageEntryPrice` DECIMAL(18, 2),
        `ExitQuantityFilled` VARCHAR(20),
        `AverageExitPrice` DECIMAL(18, 2),
        `PNL` VARCHAR(50),
        `EntryOrderID` VARCHAR(20),
        `FlagEntryOrderSent` INT,
        `FlagExitOrderSent` INT,
        `FailureReason` VARCHAR(160)
    );"""
query3 = f"""CREATE TABLE IF NOT EXISTS `orders` (
        `OrderID` INT PRIMARY KEY,
        `UniqueID` INT,
        `AccountID` VARCHAR(50),
        `Ticker` VARCHAR(50),
        `Action` VARCHAR(50),
        `OrderType` VARCHAR(50),
        
        `OrderPrice` DECIMAL(18, 2),
        `OrderQuantity` VARCHAR(20),
        `OrderTime` VARCHAR(100),
        `LastUpdateTime` VARCHAR(100),

        `OrderStatus` VARCHAR(50),
        
        `FilledQuantity` VARCHAR(20),
        `AverageFillPrice` VARCHAR(20),
        
        `OrderRef` VARCHAR(255),
        `OCAGroup` VARCHAR(255),
        `OCAType` VARCHAR(255),
        `FailureReason` VARCHAR(500),
        `FlagPurged` INT,
        FOREIGN KEY (`UniqueID`) REFERENCES `order_specs`(`UniqueID`) ON DELETE CASCADE
        );"""
query4 = f"""CREATE TABLE IF NOT EXISTS `executions` (
        `ExecutionID` VARCHAR(255) PRIMARY KEY,
        `OrderID` INT,
        `AccountID` VARCHAR(50),
        `ExecutionPrice` DECIMAL(18, 2),
        `ExecutionQuantity` VARCHAR(20),
        `ExecutionTime` VARCHAR(255),
        `PermID` VARCHAR(255),
        `CumExecutionQuantity` DECIMAL(18, 2),
        `AverageExecutionPrice` DECIMAL(18, 2),
        FOREIGN KEY (`OrderID`) REFERENCES `orders`(`OrderID`) ON DELETE CASCADE
        );"""

query5 = f"""
    CREATE TRIGGER update_order_status_and_price_from_executions
    AFTER INSERT ON executions
    FOR EACH ROW
    BEGIN        
    IF NEW.CumExecutionQuantity = (SELECT OrderQuantity FROM Orders WHERE OrderID = NEW.OrderID AND AccountID = NEW.AccountID) THEN
        UPDATE Orders
        SET OrderStatus = 'Filled',
            AverageFillPrice = NEW.AverageExecutionPrice,
            FilledQuantity = NEW.CumExecutionQuantity,
            LastUpdateTime = NEW.ExecutionTime
        WHERE AccountID = NEW.AccountID AND OrderID = NEW.OrderID;
    END IF;
    END;"""

all_queries = [query2, query3, query4, query5]
