class Portfolio:
    """Represents the combination of assets that make up an investor's portfolio"""
    assets = []

    def total_value(self):
        return sum(asset.value() for asset in self.assets)