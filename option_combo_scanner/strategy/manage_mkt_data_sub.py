import asyncio

from option_combo_scanner.ibapi_ao.market_data import RequestMarketData
from option_combo_scanner.ibapi_ao.variables import Variables as variables


class ManageMktDataSubscription:
    def __init__(
        self,
    ):
        pass

    @staticmethod
    def unsubscribe_market_data(conid: int):
        # Reduce subscription count
        variables.map_conid_to_subscription_count[conid] -= 1

        # If subscription count is still greater than 0, return
        if variables.map_conid_to_subscription_count[conid] > 0:
            return

        # Get req_id, and detele from map
        req_id = variables.map_conid_to_subscripiton_req_id[conid]
        del variables.map_conid_to_subscripiton_req_id[conid]

        # Unsubscribe from market data
        variables.app.cancelMktData(req_id)

    @staticmethod
    def subscribe_market_data(conid: int):
        # Map conid to subscription count
        if (conid not in variables.map_conid_to_subscription_count) or (
            variables.map_conid_to_subscription_count[conid] == 0
        ):
            # Increment subscription count
            variables.map_conid_to_subscription_count[conid] = 1

        else:
            # Increment subscription count
            variables.map_conid_to_subscription_count[conid] += 1
            # Don't subscribe again, return
            return None

        # Get contract
        contract = variables.map_conid_to_contract[conid]

        # Getting req_id
        req_id = variables.app.nextorderId
        variables.app.nextorderId += 1

        # Map conid to req_id
        variables.map_conid_to_subscripiton_req_id[conid] = req_id

        asyncio.run(
            RequestMarketData.get_market_data_for_contract_async(
                contract,
                snapshot=False,
                cancel_request=False,
                req_id=req_id,
                max_wait_time=1,
            )
        )
