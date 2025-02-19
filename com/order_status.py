"""
Created on 06-Apr-2023

@author: Karan
"""

from com import *
from com.variables import *


# In recovery mode, getting execution details of all the orders with "executionFilter"
def get_execution_details(executionFilter):
    reqId = variables.nextorderId
    variables.execution_details[reqId] = list([])
    variables.bool_execution_details = False

    # Requesting Execution Details
    if variables.flag_debug_mode:
        print("\nFetching Query from TWS....", variables.nextorderId)
    variables.app.reqExecutions(reqId, executionFilter)
    variables.nextorderId += 1

    counter = 0

    # Error checking loop - breaks from loop once execution details is obtained
    while True:
        if not variables.bool_execution_details:
            counter += 1
            time.sleep(0.1)
            if counter >= 50:
                return
        else:
            if variables.flag_debug_mode:
                print("Successfully got answer from TWS....", reqId)
            break


# In recovery mode, After getting the latest order execDetails, This function marks the status = cancelled for all the order which did not get any update
def mark_order_cancelled(module_start_time):
    try:
        # SQL Query to get the all the 'Order Id' which didnot get any update.
        query_to_get_old_order_id = text(
            f"SELECT `Order ID` FROM `{variables.sql_table_order_status}` Where `Last Update Time` < '{module_start_time}'"
        )

        result_order_ids = variables.sqlalchemy_connection.execute(
            query_to_get_old_order_id
        )
        time.sleep(variables.sleep_time_db)

        # Contains a list of tuple with all the 'Order ID' which didnot get the latest update : [(2115,), (2118,)]
        order_ids_mark_cancel = result_order_ids.fetchall()

        print(f"ORDER IDS TO MARK CANCEL")
        # Marking Status = Cancelled for all the 'Order ID's in order_ids_mark_cancel
        for query_result in order_ids_mark_cancel:
            order_id = query_result[0]
            query_to_cancel_order = text(
                f"UPDATE `{variables.sql_table_order_status}` SET `Status` = 'Cancelled' Where `Order ID` = '{order_id}'"
            )
            print(f"     {order_id}")
            result = variables.sqlalchemy_connection.execute(query_to_cancel_order)
            time.sleep(variables.sleep_time_db)

            if variables.flag_debug_mode:
                print(f"Marked Order ID: {order_id}, Status => 'Cancelled'")

    except Exception as e:
        if variables.flag_debug_mode:
            print("Could Not Mark Order Cancelled. Exception =>", e)
