from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.ibapi.order import Order
from option_combo_scanner.ibapi_ao.variables import Variables as variables

logger = CustomLogger.logger


# Sends the Order to TWS
def send_order_to_tws(
    contract,
    order,
):
    order_id = int(order.orderId)

    # Log
    logger.info(
        f"Sending Order ID: {order_id}, to TWS. Contract: {contract}, Order: {order}"
    )

    variables.map_order_id_to_order_status[order_id] = "Sent"

    # Placing Order
    variables.app.placeOrder(order_id, contract, order)


def create_market_order(
    action, total_qty, account_id, order_ref="", order_type="MKT", transmit=True
):
    # Handle Case where TWS is not available
    if variables.app.nextorderId is None:
        return None

    order_id = variables.app.nextorderId
    variables.app.nextorderId += 1

    # Creating Order
    order = Order()
    order.action = action
    order.totalQuantity = total_qty
    order.account = account_id
    order.orderId = order_id
    order.orderRef = order_ref
    # order.outsideRth = True

    order.orderType = order_type
    order.transmit = transmit

    return order
