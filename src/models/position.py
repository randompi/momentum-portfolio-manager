import datetime as dt

class Position:
    """The unique instance of a purchase date, quantity, and value of an asset"""
    units: int
    usd_price: float
    purchase_datetime: dt.datetime

    def __init__(self, units: float, usd_price: float, purchase_datetime: dt.datetime, current_price: float = None):
        self.units = units
        self.usd_price = usd_price
        self.purchase_datetime = purchase_datetime
        self.current_price = current_price

    def total_usd_value(self) -> float:
        return self.units * self.usd_price

    def current_market_value(self) -> float:
        """Returns market value using current_price if available, otherwise falls back to cost basis."""
        price = self.current_price if self.current_price is not None else self.usd_price
        return self.units * price