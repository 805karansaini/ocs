import datetime
import threading
import time

from option_combo_scanner.ibapi_ao.executions import get_execution_details
from option_combo_scanner.ibapi_ao.variables import Variables as variables


class ReconnectionHandler:
    def __init__(self, app):
        self.app = app
        self.flag_for_loop = True

    def retry_connection(self):
        variables.all_active_trading_accounts = set()

        try:
            self.app.disconnect()
        except Exception as exp:
            print("Trying to disconnect", exp)

        # Trying to reconnect
        try:
            self.app.nextorderId = None
            self.app.connect(
                variables.tws_host,
                variables.tws_port,
                variables.tws_client_id,
            )

            self.app.run_loop()

            c = 0

            # Check if the API is connected via order id
            while self.flag_for_loop:
                c += 1

                if isinstance(self.app.nextorderId, int):
                    print("User APP Connected, Requesting the all Trading accounts")

                    # Get Current Active Accounts
                    self.app.reqManagedAccts()
                    time.sleep(5)

                    # Order Status and Get Latest Executions
                    self.app.reqAllOpenOrders()
                    get_execution_details()
                    break

                else:
                    if c % 5 == 0:
                        print(f"User APP waiting for connection... {c} seconds")
                    time.sleep(1)

                if c >= 30:
                    break

        except Exception as exp:
            print("Exception while trying to connect User TWS.", exp)

    def monitor_api_connection(self):
        while self.flag_for_loop:
            try:
                time.sleep(10)

                # Updates the Status in the Database
                user_tws_status = self.app.isConnected()

                trading_account_exits_in_all_active_trading_accounts = False

                if (
                    variables.user_trading_account
                    in variables.all_active_trading_accounts
                ):
                    trading_account_exits_in_all_active_trading_accounts = True

                # If the correct connection is conneccted ok. else Retry the connection
                if (
                    user_tws_status
                    and trading_account_exits_in_all_active_trading_accounts
                ):
                    pass
                else:
                    self.retry_connection()
            except Exception as exp:
                print("Monitor API Connection: ", exp)

    def run(
        self,
    ):
        # Start the web socket in a thread
        self.monitor_connection_thread = threading.Thread(
            target=self.monitor_api_connection, daemon=True
        )
        self.monitor_connection_thread.start()

    def stop(self):
        self.flag_for_loop = False
        self.monitor_connection_thread.join()
