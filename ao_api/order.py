from enum import Enum
from typing import List

from pydantic import BaseModel


# Create enum class for order types
class OrderType(str, Enum):
    MKT = "MKT"
    LMT = "LMT"
    STP = "STP"


# Create enum class for order action
class OrderAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class TagValue(BaseModel):
    tag: str
    value: str


class Order(BaseModel):
    # Main order fields
    action: OrderAction  # BUY or SELL
    totalQuantity: float
    orderType: OrderType  # eg. MKT, LMT, STP
    lmtPrice: float = 0.0
    auxPrice: float = 0.0

    # Order identifer
    orderId: int = 0
    clientId: int = 0
    permId: int = 0

    # extended order fields
    tif: str = ""  # "Time in Force" - DAY, GTC, etc.
    activeStartTime: str = ""  # for GTC orders
    activeStopTime: str = ""  # for GTC orders
    orderRef: str = ""
    transmit: bool = True  # if false, order will be created but not transmitted
    parentId: int = 0  # Parent order Id, to associate Auto STP or TRAIL orders with the original order.
    outsideRth: bool = False
    triggerMethod: int = 0  # 0=Default, 1=Double_Bid_Ask, 2=Last, 3=Double_Last, 4=Bid_Ask, 7=Last_or_Bid_Ask, 8=Mid-point

    # ALGO ORDERS ONLY
    algoStrategy: str = ""
    algoParams: List[TagValue] = []  # TagValueList
    smartComboRoutingParams: List[TagValue] = []  # TagValueList
    algoId: str = ""

    # What-if
    whatIf: bool = False

    # native cash quantity
    cashQty: float = 0.0


def json_to_order(json_data) -> Order:
    order_obj = Order.model_validate_json(json_data)

    return order_obj


def order_to_json(order: Order):
    order_json = order.model_dump_json(exclude_none=True, exclude_unset=True)

    return order_json


class OrderState(BaseModel):
    status: str = ""
    initMarginBefore: str = ""
    maintMarginBefore: str = ""
    equityWithLoanBefore: str = ""
    initMarginChange: str = ""
    maintMarginChange: str = ""
    equityWithLoanChange: str = ""
    initMarginAfter: str = ""
    maintMarginAfter: str = ""
    equityWithLoanAfter: str = ""
    commission: float = 0
    minCommission: float = 0
    maxCommission: float = 0
    commissionCurrency: str = ""
    warningText: str = ""
    completedTime: str = ""
    completedStatus: str = ""


def json_to_order_state(json_data) -> OrderState:
    order_state_obj = OrderState.model_validate_json(json_data)

    return order_state_obj


def order_state_to_json(order_state: OrderState):
    order_state_json = order_state.model_dump_json(
        exclude_none=True, exclude_unset=True, exclude_defaults=True
    )

    return order_state_json
