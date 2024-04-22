from enum import Enum

from pydantic import BaseModel


class ContractType(str, Enum):
    STK = "STK"
    OPT = "OPT"
    FUT = "FUT"
    FOP = "FOP"
    CUR = "CUR"
    IND = "IND"


class Contract(BaseModel):
    contract_type: ContractType
    ticker: str
    right: str | None = None  # C or P
    expiry: str | None = None  # Format: YYYYMMDD
    strike: float | None = None
    currency: str | None = None
    trading_class: str | None = None
    exchange: str | None = None
    multiplier: int | None = None


def get_contract_obj(contract: dict) -> Contract:

    contract_obj = Contract.model_validate_json(contract)

    return contract_obj


def contract_to_dict(contract: Contract) -> dict:
    
    contract_json = contract.model_dump_json(exclude_none=True)

    return contract_json
