import json
from enum import Enum

from pydantic import BaseModel


class ContractType(str, Enum):
    STK = "STK"
    OPT = "OPT"
    FUT = "FUT"
    FOP = "FOP"
    CUR = "CASH"
    IND = "IND"


class Contract(BaseModel):
    contract_type: ContractType
    ticker: str
    conId: int = 0
    right: str = ""  # C or P
    expiry: str = ""  # Format: YYYYMMDD
    strike: float = 0.0
    currency: str = ""
    trading_class: str = ""
    exchange: str = ""
    # pick an actual (ie non-aggregate) exchange that the contract trades on.  DO NOT SET TO SMART.
    primaryExchange: str = ""
    multiplier: int = 1
    localSymbol: str = ""
    includeExpired: bool = False
    secIdType: str = ""  # CUSIP;SEDOL;ISIN;RIC
    secId: str = ""
    description: str = ""
    issuerId: str = ""

    # combos
    comboLegsDescrip: str = ""
    comboLegs: None = None
    deltaNeutralContract: str | None = None

    @property
    def symbol(self):
        return self.ticker

    @property
    def secType(self):
        return self.contract_type.value

    @property
    def tradingClass(self):
        return self.trading_class

    @property
    def lastTradeDateOrContractMonth(self):
        return self.expiry


def get_contract_obj(contract: str) -> Contract:
    """Converts a contract json string to a Contract object."""
    contract_obj = Contract.model_validate_json(contract)

    return contract_obj


def contract_to_json(contract: Contract) -> str:
    """Converts a Contract object to a json string."""
    contract_json = contract.model_dump_json(
        exclude_none=True, exclude_defaults=True, exclude_unset=True
    )

    return contract_json


class AOContractDetails(BaseModel):
    contract: Contract
    marketName: str = ""
    minTick: float = 0.0
    orderTypes: str = ""
    validExchanges: str = ""
    priceMagnifier: int = 0
    underConId: int = 0
    longName: str = ""
    contractMonth: str = ""
    industry: str = ""
    category: str = ""
    subcategory: str = ""
    timeZoneId: str = ""
    tradingHours: str = ""
    liquidHours: str = ""
    evRule: str = ""
    evMultiplier: int = 0
    aggGroup: int = 0
    underSymbol: str = ""
    underSecType: str = ""
    marketRuleIds: str = ""
    secIdList: list = []
    realExpirationDate: str = ""
    lastTradeTime: str = ""
    stockType: str = ""
    minSize: float = 0.0
    sizeIncrement: float = 0.0
    suggestedSizeIncrement: float = 0.0
    # BOND values
    cusip: str = ""
    ratings: str = ""
    descAppend: str = ""
    bondType: str = ""
    couponType: str = ""
    callable: bool = False
    putable: bool = False
    coupon: float = 0.0
    convertible: bool = False
    maturity: str = ""
    issueDate: str = ""
    nextOptionDate: str = ""
    nextOptionType: str = ""
    nextOptionPartial: bool = False
    notes: str = ""


def get_contract_details_obj(contract_details: str) -> AOContractDetails:
    """Converts a contract_details json string to a AOContractDetails object."""

    contract_details_dict = json.loads(contract_details)
    contract_details_dict["contract"] = get_contract_obj(
        json.dumps(contract_details_dict["contract"])
    )
    contract_details_obj = AOContractDetails(**contract_details_dict)

    return contract_details_obj


def contract_details_to_json(contract_details: AOContractDetails) -> str:
    """Converts a AOContractDetails object to a json string."""
    contract_details_json = contract_details.model_dump_json(
        exclude_none=True, exclude_defaults=True, exclude_unset=True
    )

    return contract_details_json
