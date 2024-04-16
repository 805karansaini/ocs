import datetime

from ao_api.contract import Contract, ContractType
from ao_api.enums import BarType, BarUnit, OptionRightType


class IBkrAlgoOneAdapter:

    @staticmethod
    def duration(duration_string):
        """
        returns: duration, start datetime, end datetime
        """
        duration, duration_unit = duration_string.split(" ")
        duration = int(duration)

        if "S" in duration_unit.upper():
            # Get current time in utc
            end_datetime = datetime.datetime.now(datetime.timezone.utc)
            # Subtract the seconds from the time
            start_datetime = end_datetime - datetime.timedelta(seconds=duration)

            # Convert start_datetime and end_datetime to appropriate server format
            start_datetime = start_datetime.strftime("%Y%m%d %H%M%S")
            end_datetime = end_datetime.strftime("%Y%m%d %H%M%S")

            return None, start_datetime, end_datetime
        elif "D" in duration_unit.upper():
            duration = duration
        elif "W" in duration_unit.upper():
            duration = duration * 5
        elif "M" in duration_unit.upper():
            duration = duration * 22
        elif "Y" in duration_unit.upper():
            duration = duration * 252
        else:
            print(f"duration_string: {duration_string}")

        return int(duration), None, None

    @staticmethod
    def bar_size(bar_size):
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
        elif right == "":
            pass
        else:
            print("Error Invalid Right Type in Adapter", right)

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
