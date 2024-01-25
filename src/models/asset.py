from src.models.position import Position

class Asset:
    """Represents a monetary asset such as a stock, cash, bond, etc. with 1 or more positions"""
    asset_type: str
    display_name: str
    ticker_symbol: str
    positions: list[Position]

    def __init__(self):
        self.positions = []

    def add_position(self, position: Position):
        self.positions.append(position)

    def total_usd_value(self) -> float:
        return sum(p.total_usd_value() for p in self.positions)