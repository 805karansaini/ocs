from pydantic import BaseModel


class Execution(BaseModel):
    execId: str = ""
    time: str = ""
    acctNumber: str = ""
    exchange: str = ""
    side: str = ""
    shares: float = 0.0
    price: float = 0.0
    permId: int = 0
    clientId: int = 0
    orderId: int = 0
    liquidation: int = 0
    cumQty: float = 0.0
    avgPrice: float = 0.0
    orderRef: str = ""
    evRule: str = ""
    evMultiplier: float = 0.0
    modelCode: str = ""
    lastLiquidity: int = 0


def json_to_algo_execution(json_data) -> Execution:
    execution_obj = Execution.model_validate_json(json_data)

    return execution_obj


def algo_execution_to_json(execution: Execution):
    execution_json = execution.model_dump_json(
        exclude_none=True, exclude_unset=True, exclude_defaults=True
    )

    return execution_json


class ExecutionFilter(BaseModel):
    # Filter fields
    clientId: int = 0
    acctCode: str = ""
    time: str = ""
    symbol: str = ""
    secType: str = ""
    exchange: str = ""
    side: str = ""


def json_to_algo_execution_filter(json_data) -> ExecutionFilter:
    execution_filter_obj = ExecutionFilter.model_validate_json(json_data)

    return execution_filter_obj


def execution_filter_to_json(execution_filter: ExecutionFilter):
    execution_filter_json = execution_filter.model_dump_json(
        exclude_none=True, exclude_unset=True, exclude_defaults=True
    )

    return execution_filter_json
