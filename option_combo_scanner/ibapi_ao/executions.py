import datetime
import time

from dateutil.relativedelta import relativedelta

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.ibapi.execution import ExecutionFilter
from option_combo_scanner.ibapi_ao.variables import Variables as variables

logger = CustomLogger.logger


def get_execution_details(module_start_time=None):
    """
    Gets the executions details from IBAPI

    :param executionFilter: The filter object created
    :return: None
    """

    if module_start_time is None:
        # Record module start time
        module_start_time = datetime.datetime.now(variables.target_timezone_obj)

    # Setup filter: all trades executed after strategy_start_time
    executionFilter = ExecutionFilter()
    fifteen_days_old_time = module_start_time - relativedelta(days=15)
    executionFilter.time = fifteen_days_old_time.strftime("%Y%m%d-%H:%M:%S")

    # Log and Print
    logger.info(f"executionFilter.time = {executionFilter.time}")
    print("executionFilter.time = ", executionFilter.time)

    if variables.app.nextorderId is None:
        return

    # Get reqId
    reqId = variables.app.nextorderId
    variables.app.nextorderId += 1

    # Log
    logger.info(f"Fetching execution details from TWS for reqId = {reqId}")

    # Init
    variables.bool_execution_details = False
    variables.app.reqExecutions(reqId, executionFilter)

    counter = 1

    # Error checking loop - breaks from loop once execution details is obtained
    while True:
        if not variables.bool_execution_details:
            time.sleep(variables.sleep_time_waiting_for_tws_response)

        else:
            # Log
            logger.info(f"Successfully got Executions from TWS for reqId = {reqId}")

            # Return since we got all the execution details
            return

        counter += 1

        # Waiting for max time, so that we are not stuck on there forever
        if counter >= int(
            variables.max_wait_time_for_executions
            / variables.sleep_time_waiting_for_tws_response
        ):
            # Log
            logger.erro(
                f"Max Time for getting Execution Details from TWS  Elapsed returning.... reqId = {reqId}"
            )

            # Return since max wait time elapsed
            return
