from src.models.asset import Asset


class Portfolio:
    """Represents the combination of assets that make up an investor's portfolio"""

    def __init__(self):
        self.assets: list[Asset] = []

    def add_asset(self, asset: Asset):
        self.assets.append(asset)

    def total_value(self) -> float:
        return sum(asset.total_usd_value() for asset in self.assets)