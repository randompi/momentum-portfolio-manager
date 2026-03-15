"""
Portfolio JSON importer supporting common formats used by brokers such as
E-Trade (PortfolioResponse) and Fidelity (accounts/positions).

Normalized format (primary):
{
    "account_id": "optional",
    "positions": [
        {
            "symbol": "AAPL",
            "description": "Apple Inc",
            "asset_type": "Stock",
            "quantity": 10.0,
            "cost_basis_per_share": 130.00,
            "current_price": 150.25,
            "acquisition_date": "2023-01-15"
        }
    ]
}

E-Trade PortfolioResponse format:
{
    "PortfolioResponse": {
        "AccountPortfolio": [
            {
                "accountId": "12345",
                "Position": [
                    {
                        "symbolDescription": "Apple Inc",
                        "symbol": "AAPL",
                        "typeDescription": "EQ",
                        "quantity": 10,
                        "currentPrice": 150.25,
                        "dateAcquired": "01/15/2023",
                        "costPerShare": 130.00
                    }
                ]
            }
        ]
    }
}

Fidelity accounts format:
{
    "accounts": [
        {
            "accountId": "Z12345678",
            "positions": [
                {
                    "description": "APPLE INC",
                    "symbol": "AAPL",
                    "type": "Stock",
                    "quantity": 10.0,
                    "lastPrice": 150.25,
                    "acquisitionDate": "2023-01-15",
                    "costBasisPerShare": 130.00
                }
            ]
        }
    ]
}
"""

import json
import datetime as dt

from src.models.asset import Asset
from src.models.portfolio import Portfolio
from src.models.position import Position


_DATE_FORMATS = ["%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%Y%m%d"]


def _parse_date(date_str: str) -> dt.datetime:
    for fmt in _DATE_FORMATS:
        try:
            return dt.datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(
        f"Unable to parse date: {date_str!r}. "
        f"Supported formats: YYYY-MM-DD, MM/DD/YYYY, MM/DD/YY, YYYYMMDD"
    )


def _get_field(data: dict, *keys, default=None):
    """Return the value of the first matching key found in data."""
    for key in keys:
        if key in data:
            return data[key]
    return default


def _parse_position_entry(pos_data: dict) -> tuple[Asset, Position]:
    """Parse a single position dict into an (Asset, Position) pair."""
    symbol = _get_field(
        pos_data,
        "symbol", "ticker", "ticker_symbol",
        "Symbol", "SYMBOL",
    )
    if not symbol:
        raise ValueError(f"Position entry is missing a symbol field: {pos_data}")

    description = _get_field(
        pos_data,
        "description", "display_name", "name",
        "symbolDescription", "securityDescription",
        default=symbol,
    )

    asset_type = _get_field(
        pos_data,
        "asset_type", "assetType", "type", "typeDescription",
        "securityType", "instrumentType",
        default="Unknown",
    )

    quantity = float(_get_field(
        pos_data,
        "quantity", "units", "shares",
        "Quantity", "Shares",
        default=0.0,
    ))

    cost_basis = _get_field(
        pos_data,
        "cost_basis_per_share", "costBasisPerShare", "costPerShare",
        "avgCostBasis", "averageCostBasis", "purchasePrice", "pricePaid",
    )

    current_price = _get_field(
        pos_data,
        "current_price", "currentPrice", "lastPrice",
        "marketPrice", "price", "Last Price",
    )

    if cost_basis is not None:
        usd_price = float(cost_basis)
    elif current_price is not None:
        usd_price = float(current_price)
    else:
        raise ValueError(
            f"Position for {symbol!r} has no price information "
            "(expected 'cost_basis_per_share' or 'current_price')"
        )

    current_price_val = float(current_price) if current_price is not None else None

    date_str = _get_field(
        pos_data,
        "acquisition_date", "acquisitionDate", "dateAcquired",
        "purchaseDate", "openDate", "date",
    )
    purchase_dt = _parse_date(str(date_str)) if date_str else dt.datetime(1970, 1, 1)

    asset = Asset(
        ticker_symbol=str(symbol),
        display_name=str(description),
        asset_type=str(asset_type),
    )
    position = Position(
        units=quantity,
        usd_price=usd_price,
        purchase_datetime=purchase_dt,
        current_price=current_price_val,
    )
    return asset, position


def _build_portfolio_from_positions(positions_data: list) -> Portfolio:
    """Convert a flat list of position dicts into a Portfolio, merging lots by ticker."""
    portfolio = Portfolio()
    assets_by_ticker: dict[str, Asset] = {}

    for pos_data in positions_data:
        asset, position = _parse_position_entry(pos_data)
        ticker = asset.ticker_symbol

        if ticker not in assets_by_ticker:
            assets_by_ticker[ticker] = asset
            portfolio.add_asset(asset)

        assets_by_ticker[ticker].add_position(position)

    return portfolio


def _extract_positions(data: dict) -> list:
    """Extract a flat list of raw position dicts from any supported top-level format."""
    # Normalized: { "positions": [...] }
    if "positions" in data:
        return data["positions"]

    # E-Trade: { "PortfolioResponse": { "AccountPortfolio": [{ "Position": [...] }] } }
    if "PortfolioResponse" in data:
        positions = []
        for account in data["PortfolioResponse"].get("AccountPortfolio", []):
            positions.extend(account.get("Position", []))
        return positions

    # Fidelity multi-account: { "accounts": [{ "positions": [...] }] }
    if "accounts" in data:
        positions = []
        for account in data["accounts"]:
            positions.extend(account.get("positions", []))
        return positions

    # Single account wrapper: { "account": { "positions": [...] } }
    if "account" in data:
        return data["account"].get("positions", [])

    raise ValueError(
        "Unrecognized JSON format. Expected one of the following top-level keys: "
        "'positions', 'PortfolioResponse', 'accounts', or 'account'."
    )


def import_from_dict(data: dict) -> Portfolio:
    """Import a Portfolio from an already-parsed JSON dictionary."""
    positions_data = _extract_positions(data)
    return _build_portfolio_from_positions(positions_data)


def import_from_json(json_str: str) -> Portfolio:
    """Import a Portfolio from a JSON string."""
    data = json.loads(json_str)
    return import_from_dict(data)


def import_from_file(file_path: str) -> Portfolio:
    """Import a Portfolio from a JSON file on disk."""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return import_from_dict(data)
