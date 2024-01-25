import datetime as dt

class Position:
    """The unique instance of a purchase date, quantity, and value of an asset"""
    units: int
    usd_price: float
    purchase_datetime: dt.datetime

    def __init__(self, units: int, usd_price: float, purchase_datetime: dt.datetime):
        self.units = units
        self.usd_price = usd_price
        self.purchase_datetime = purchase_datetime

    def total_usd_value(self):
        return self.units * self.usd_price