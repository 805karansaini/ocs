import asyncio
import threading
import time

from ao_api.contract import Contract, ContractType
from ao_api.enums import BarType, BarUnit, OptionRightType
from option_combo_scanner.client_app.app import AlgoOneAPI

if __name__ == "__main__":

    def start_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()
        print("End in loop")

    # Create a new event loop and start it in a new thread
    new_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_loop, args=(new_loop,))
    t.start()

    time.sleep(1)

    # Creating the Data Server Client
    ds_client = AlgoOneAPI(data_server_host="25.38.187.70", data_server_port=8765, data_server_client_id=123, loop=new_loop)

    ds_client.start()

    # test_wrapper_thread = threading.Thread(target=ds_client.start)
    # test_wrapper_thread.start()

    # Wait for the connection
    while not ds_client.is_connected():
        time.sleep(0.2)


    # Request 1
    aapl_stk = Contract(
        contract_type=ContractType.STK,
        ticker="AAPL",
        exchange="SMART",
        currency="USD",
    )

    # List Of List of Call [170.0, 167.5] and Put [165.0, 167.5]
    amzn_call_opt = Contract(
        contract_type=ContractType.OPT,
        ticker="AAPL",
        exchange="SMART",
        currency="USD",
        multiplier=100,
        expiry="20240412",
        strike="170",
        right=OptionRightType.CALL,
    )

    amzn_stk = Contract(
        contract_type=ContractType.STK,
        ticker="AMZN",
        exchange="SMART",
        currency="USD",
        multiplier=1,
    )

    es_fut = Contract(
        contract_type=ContractType.FUT,
        ticker="ES",
        exchange="CME",
        currency="USD",
        multiplier=50,
        expiry="202406",
    )

    # Request ID
    req_id = 100

    # Request 1
    print("Sending Requests")

    for bar_unit in [
        BarUnit.MINUTE,
        # BarUnit.HOUR,
        # BarUnit.DAY,
        # BarUnit.WEEK,
        # BarUnit.MONTH,
        # BarUnit.QUARTER,
        # BarUnit.YEAR,
    ]:
        ds_client.get_historical_bars(
            req_id,
            amzn_call_opt,  # Contract
            duration=10,
            bar_unit=bar_unit,
            bar_size=3,
            flag_rth_only=True,
            bar_type="TRADES"
        )
        req_id += 1

    

    print("Sent Requests")
