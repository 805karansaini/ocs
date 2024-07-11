from ao_api.common import AOPriceIncrement
from ao_api.contract import AOContractDetails, Contract, ContractType
from ao_api.enums import BarType, BarUnit, DurationUnit, OptionRightType
from ao_api.execution import Execution, ExecutionFilter
from ao_api.order import Order, OrderAction, OrderState, OrderType, TagValue
from ibapi.common import UNSET_DECIMAL, PriceIncrement
from ibapi.contract import Contract as IbapiContract
from ibapi.contract import ContractDetails
from ibapi.execution import Execution as IbapiExecution
from ibapi.execution import ExecutionFilter as IbapiExecutionFilter
from ibapi.order import Order as IbapiOrder
from ibapi.order_state import OrderState as IbapiOrderState


class IBkrAlgoOneAdapter:

    @staticmethod
    def duration(duration_string: str):
        """
        returns: duration, duration_unit
        """
        duration, duration_unit = duration_string.split(" ")
        duration = int(duration)

        # TODO: Also Supports Duration Unit in Mins, hours, but since in TWS mins,  hours are not supported.
        # so we are not implementing those in IBkrAlgoOneAdapter
        if "S" in duration_unit.upper():
            return duration, DurationUnit.SECOND
        elif "D" in duration_unit.upper():
            return duration, DurationUnit.DAY
        elif "W" in duration_unit.upper():
            return duration * 5, DurationUnit.DAY
        elif "M" in duration_unit.upper():
            return duration * 22, DurationUnit.DAY
        elif "Y" in duration_unit.upper():
            return duration * 252, DurationUnit.DAY
        else:
            print(f"Invalid duration_string: {duration_string}")

        return None, None

    @staticmethod
    def bar_size(bar_size: str):
        bar_size, bar_unit = bar_size.split(" ")
        bar_size = int(bar_size)

        if "sec" in bar_unit:
            bar_unit = BarUnit.SECOND
        elif "min" in bar_unit:
            bar_unit = BarUnit.MINUTE
        elif "hour" in bar_unit:
            bar_unit = BarUnit.HOUR
        elif "day" in bar_unit:
            bar_unit = BarUnit.DAY
        elif "week" in bar_unit:
            bar_unit = BarUnit.WEEK
        elif "month" in bar_unit:
            bar_unit = BarUnit.MONTH
        else:
            print(f"Invalid Bar Unit in Adapted: {bar_unit}")

        return bar_size, bar_unit

    @staticmethod
    def flag_rth_only(flag_rth):
        return bool(flag_rth)

    @staticmethod
    def bar_type(what_to_show):

        what_to_show = what_to_show.upper()
        bar_type = BarType(what_to_show)

        return bar_type

    @staticmethod
    def right(right):

        if "P" in right.upper():
            right = OptionRightType.PUT
        elif "C" in right.upper():
            right = OptionRightType.CALL
        else:
            right = ""

        return right

    @staticmethod
    def contract(contract_object):

        ticker = contract_object.symbol
        contract_type = ContractType(contract_object.secType)
        exchange = contract_object.exchange
        currency = contract_object.currency
        expiry = contract_object.lastTradeDateOrContractMonth
        strike = None if float(contract_object.strike) == 0 else contract_object.strike
        right = IBkrAlgoOneAdapter.right(contract_object.right)
        multiplier = (
            None if contract_object.multiplier == "" else contract_object.multiplier
        )
        trading_class = contract_object.tradingClass

        ao_contract = Contract(
            contract_type=contract_type,
            ticker=ticker,
            right=right,
            expiry=expiry,
            strike=strike,
            currency=currency,
            trading_class=trading_class,
            exchange=exchange,
            multiplier=multiplier,
        )

        return ao_contract

    @staticmethod
    def convert_ibapi_to_ao_contract(ibapi_contract: IbapiContract) -> Contract:

        contract = Contract(
            contract_type=ContractType(ibapi_contract.secType),
            ticker=ibapi_contract.symbol,

            conId = ibapi_contract.conId,
            right = IBkrAlgoOneAdapter.right(ibapi_contract.right),
            expiry = ibapi_contract.lastTradeDateOrContractMonth,
            strike = ibapi_contract.strike,
            currency = ibapi_contract.currency,
            trading_class = ibapi_contract.tradingClass,
            exchange = ibapi_contract.exchange,

            primaryExchange = ibapi_contract.primaryExchange,
            localSymbol = ibapi_contract.localSymbol,
            includeExpired = ibapi_contract.includeExpired,
            secIdType = ibapi_contract.secIdType,
            secId = ibapi_contract.secId,
            description = ibapi_contract.description,
            issuerId = ibapi_contract.issuerId,

            # combos
            comboLegsDescrip = ibapi_contract.comboLegsDescrip,
            comboLegs = ibapi_contract.comboLegs,
            deltaNeutralContract = ibapi_contract.deltaNeutralContract,
        )

        # # TODO: check if multiplier should be int
        try:
            contract.multiplier = int(float(ibapi_contract.multiplier))
        except Exception as e:
            # print("Error in converting multiplier to int", e)
            pass

        return contract

    @staticmethod
    def convert_ibapi_to_ao_order(order: IbapiOrder) -> Order:

        return Order(
            action=OrderAction(order.action),
            totalQuantity=(
                float(order.totalQuantity)
                if order.totalQuantity != UNSET_DECIMAL
                else 0.0
            ),
            orderType=OrderType(order.orderType),
            lmtPrice=(
                float(order.lmtPrice) if order.totalQuantity != UNSET_DECIMAL else 0.0
            ),
            auxPrice=(
                float(order.auxPrice) if order.totalQuantity != UNSET_DECIMAL else 0.0
            ),
            orderId=order.orderId,
            clientId=order.clientId,
            permId=order.permId,
            tif=order.tif,
            activeStartTime=order.activeStartTime,
            activeStopTime=order.activeStopTime,
            orderRef=order.orderRef,
            transmit=order.transmit,
            parentId=order.parentId,
            outsideRth=order.outsideRth,
            triggerMethod=order.triggerMethod,
            algoStrategy=order.algoStrategy,
            algoParams=[TagValue(tag=param.tag, value=param.value) for param in order.algoParams] if order.algoParams else [],  # type: ignore
            smartComboRoutingParams=[TagValue(tag=param.tag, value=param.value) for param in order.smartComboRoutingParams] if order.smartComboRoutingParams else [],  # type: ignore
            algoId=order.algoId,
            whatIf=order.whatIf,
            cashQty=float(order.cashQty) if order.cashQty != UNSET_DECIMAL else 0.0,
        )

    @staticmethod
    def convert_ibapi_to_ao_execution_filter(
        execution_filter: IbapiExecutionFilter,
    ) -> ExecutionFilter:
        return ExecutionFilter(
            clientId=execution_filter.clientId,
            acctCode=execution_filter.acctCode,
            time=execution_filter.time,
            symbol=execution_filter.symbol,
            secType=execution_filter.secType,
            exchange=execution_filter.exchange,
            side=execution_filter.side,
        )

    @staticmethod
    def convert_ibapi_to_ao_execution(
        execution: IbapiExecution,
    ) -> Execution:
        """
        Convert an ibapi Execution instance to a Execution instance.
        """
        return Execution(
            execId=execution.execId,
            time=execution.time,
            acctNumber=execution.acctNumber,
            exchange=execution.exchange,
            side=execution.side,
            shares=(
                float(execution.shares) if execution.shares != UNSET_DECIMAL else 0.0
            ),
            price=execution.price,
            permId=execution.permId,
            clientId=execution.clientId,
            orderId=execution.orderId,
            liquidation=execution.liquidation,
            cumQty=(
                float(execution.cumQty) if execution.cumQty != UNSET_DECIMAL else 0.0
            ),
            avgPrice=execution.avgPrice,
            orderRef=execution.orderRef,
            evRule=execution.evRule,
            evMultiplier=execution.evMultiplier,
            modelCode=execution.modelCode,
            lastLiquidity=execution.lastLiquidity,
        )

    @staticmethod
    def convert_ibapi_to_ao_order_state(
        order_state: IbapiOrderState,
    ) -> OrderState:
        """
        Convert an ibapi OrderState instance to an OrderState instance.
        """
        algo_order_state = OrderState(
            status=order_state.status,
            initMarginBefore=order_state.initMarginBefore,
            maintMarginBefore=order_state.maintMarginBefore,
            equityWithLoanBefore=order_state.equityWithLoanBefore,
            initMarginChange=order_state.initMarginChange,
            maintMarginChange=order_state.maintMarginChange,
            equityWithLoanChange=order_state.equityWithLoanChange,
            initMarginAfter=order_state.initMarginAfter,
            maintMarginAfter=order_state.maintMarginAfter,
            equityWithLoanAfter=order_state.equityWithLoanAfter,
            commission=order_state.commission,
            minCommission=order_state.minCommission,
            maxCommission=order_state.maxCommission,
            commissionCurrency=order_state.commissionCurrency,
            warningText=order_state.warningText,
            completedTime=order_state.completedTime,
            completedStatus=order_state.completedStatus,
        )

        return algo_order_state

    @staticmethod
    def convert_ao_to_ibapi_execution_filter(
        execution_filter: ExecutionFilter,
    ) -> IbapiExecutionFilter:
        ibapi_execution_filter = IbapiExecutionFilter()
        ibapi_execution_filter.clientId = execution_filter.clientId
        ibapi_execution_filter.acctCode = execution_filter.acctCode
        ibapi_execution_filter.time = execution_filter.time
        ibapi_execution_filter.symbol = execution_filter.symbol
        ibapi_execution_filter.secType = execution_filter.secType
        ibapi_execution_filter.exchange = execution_filter.exchange
        ibapi_execution_filter.side = execution_filter.side

        return ibapi_execution_filter

    @staticmethod
    def convert_ao_to_ibapi_contract(
        contract: Contract,
    ) -> IbapiContract:

        ibapi_contract = IbapiContract()
        ibapi_contract.secType = contract.contract_type.value
        ibapi_contract.symbol = contract.ticker
        ibapi_contract.conId = contract.conId
        # Optional fields
        ibapi_contract.right = contract.right
        ibapi_contract.lastTradeDateOrContractMonth = contract.expiry
        ibapi_contract.strike = contract.strike
        ibapi_contract.currency = contract.currency
        ibapi_contract.tradingClass = contract.trading_class
        ibapi_contract.exchange = contract.exchange
        ibapi_contract.primaryExchange = contract.primaryExchange
        ibapi_contract.localSymbol = contract.localSymbol
        ibapi_contract.includeExpired = contract.includeExpired
        ibapi_contract.secIdType = contract.secIdType
        ibapi_contract.secId = contract.secId
        ibapi_contract.description = contract.description
        ibapi_contract.issuerId = contract.issuerId

        if contract.multiplier:
            ibapi_contract.multiplier = str(contract.multiplier)

        return ibapi_contract

    @staticmethod
    def convert_ibapi_to_ao_contract_details(
        contract_details: ContractDetails,
    ) -> AOContractDetails:

        contract_details_dict = contract_details.__dict__.copy()

        # Convert nested Contract object
        contract_details_dict["contract"] = (
            IBkrAlgoOneAdapter.convert_ibapi_to_ao_contract(contract_details.contract)
        )

        # Convert secIdList to list of TagValue if it exists
        if contract_details_dict.get("secIdList"):
            contract_details_dict["secIdList"] = [TagValue(tag=sec_id.tag, value=sec_id.value) for sec_id in contract_details.secIdList]  # type: ignore
        else:
            contract_details_dict["secIdList"] = [] 

        # Handle UNSET_DECIMAL conversion
        for key in ["minSize", "sizeIncrement", "suggestedSizeIncrement"]:
            if contract_details_dict[key] == UNSET_DECIMAL:
                contract_details_dict[key] = 0.0

        return AOContractDetails(**contract_details_dict)

    @staticmethod
    def convert_ibapi_to_ao_price_increment(price_increment: PriceIncrement) -> AOPriceIncrement:
        return AOPriceIncrement(
            lowEdge=price_increment.lowEdge,
            increment=price_increment.increment,
        )