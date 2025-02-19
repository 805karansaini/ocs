"""
Created on 15-Mar-2023

@author: Karan
"""

from com.contracts import *
from com.variables import *


class Leg(object):
    """
    classdocs
    """

    # Constructor method
    def __init__(
        self,
        action=None,
        symbol=None,
        sec_type=None,
        dte=None,
        delta=None,
        exchange=None,
        currency=None,
        quantity=None,
        expiry_date=None,
        strike_price=None,
        right=None,
        multiplier=None,
        con_id=None,
        primary_exchange=None,
        trading_class=None,
        contract=None,
    ):
        self.action = action
        self.symbol = symbol
        self.sec_type = sec_type
        self.dte = dte
        self.delta = delta
        self.exchange = exchange
        self.currency = currency
        self.quantity = quantity
        self.expiry_date = expiry_date
        self.strike_price = strike_price
        self.right = right
        self.multiplier = int(multiplier)
        self.con_id = con_id
        self.primary_exchange = primary_exchange
        self.trading_class = trading_class
        self.contract = contract

        if self.con_id is not None:
            variables.map_con_id_to_contract[int(self.con_id)] = self.contract

    # Get all attributes of leg object
    def __str__(self):
        return f"Leg(action={self.action}, symbol={self.symbol}, sec_type={self.sec_type}, exchange={self.exchange}, currency={self.currency},quantity={self.quantity},\
expiry_date={self.expiry_date}, strike_price={self.strike_price}, right={self.right}, multiplier={self.multiplier},\
con_id={self.con_id}, primary_exchange={self.primary_exchange}, trading_class={self.trading_class}, contract: {self.contract})"
