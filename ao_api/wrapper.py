import logging

from ao_api.contract import AOContractDetails, Contract
from ao_api.execution import Execution
from ao_api.order import Order, OrderState

logger = logging.getLogger(__name__)


class EWrapper:
    def __init__(self):
        pass

    def error(
        self,
        request_id: int,
        error_code: int,
        error_msg: str,
        advance_order_reject_json="",
    ):
        """This event is called when error response is received."""
        pass

    def warning(self, request_id: int, warning_msg: str):
        """Called when warning response is received."""
        pass

    def historical_data(self, request_id: int, historical_bars: dict):
        """Returns the requested historical bars."""
        pass

    def historical_data_end(self, request_id: int):
        """Marks the ending of the historical bars reception."""
        pass

    def option_contracts_data(self,  request_id: int, underlyingConId: int, exchange: str, trading_class: str, multiplier: int, expirations: set, strikes: set):
        """Returns the requested historical option contracts"""
        pass

    def option_contracts_data_end(self, request_id: int):
        """Returns the requested historical option contracts"""
        pass

    def real_time_quotes(self, request_id: int, quote_data: dict):
        """Returns the real time quotes"""
        pass

    def real_time_quotes_end(self, request_id: int):
        """Marks the ending of real time quotes"""
        pass

    def tick_price(self, request_id: int, tick_type: str, price: float):
        """Return the Tick price"""
        pass

    def tick_size(self, request_id: int, tick_type: str, size: float):
        """Return the Tick size"""
        pass

    def tick_option_computation(
        self,
        request_id: int,
        tick_type: str,
        delta: float,
        gamma: float,
        vega: float,
        theta: float,
        iv: float,
        underlying_price: float, 
        option_price: float,
        pvDividend: float
    ):
        """Return the requested option computation data.
        (Values are None if not available)"""
        pass

    def tick_generic(self, request_id: int, tick_type: str, value: float):
        """Return the requested generic tick data"""
        pass

    def market_snapshot_end(self, request_id: int):
        """Marks the ending of market snapshot data"""
        pass

    def contract_details(self, request_id: int, contract_details: AOContractDetails):
        """Return the requested contract details data"""
        pass

    def contract_details_end(self, request_id: int):
        """Marks the ending of contract details data"""
        pass

    def order_status(self, request_id: int, status: str, filled: float, remaining: float, avg_fill_price: float, last_fill_price: float, why_held: str, mkt_cap_price: float):
        """Return the order status data"""
        pass

    def open_order(self, request_id: int, contract: Contract, order: Order, order_state: OrderState):
        """Return the open order data"""
        pass

    def executions(self, request_id: int, contract: Contract, execution: Execution):
        """Return the executions data"""
        pass

    def executions_end(self, request_id: int):
        """Marks the ending of executions data"""
        pass

    def positions(self, request_id: int, account: str, contract: Contract, position: float, avg_cost: float):
        """Return the positions data"""
        pass

    def positions_end(self, request_id: int):
        """Marks the ending of positions data"""
        pass

    def next_valid_request_id(self, next_request_id: int):
        """Return the next valid request id"""
        pass

    def all_accounts_data(
        self, request_id: int, readAccountsList: str, writeAccountsList: str
    ):
        """Give All Accounts for a user with permission(DB)"""
        pass

    def managed_accounts(
        self, request_id: int, readAccountsList: str, writeAccountsList: str
    ):
        """Give intersection of All Accounts and All Active Accounts"""
        pass

    def account_updates(self, request_id: int, key: str, val: str, currency: str, account: str):
        """Return the account updates data"""
        pass

    def account_updates_end(self, request_id: int, account: str):
        """Marks the ending of account updates data"""
        pass

    def pnl(self, request_id: int, daily_pnl: float, unrealized_pnl: float, realized_pnl: float):
        """Return the PnL data"""
        pass

    def pnl_single(self, request_id: int, pos: float, daily_pnl: float, unrealized_pnl: float, realized_pnl: float, value: float):
        """Return the PnL data"""
        pass

    def market_rule(self, request_id: int, market_rule_id: str, price_increments: list):
        """Return the requested market rule"""
        pass
