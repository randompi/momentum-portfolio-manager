import json
import datetime as dt
import pytest

from src.importers.portfolio_json_importer import (
    import_from_dict,
    import_from_json,
    import_from_file,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalized_payload(positions: list) -> dict:
    return {"account_id": "TEST-001", "positions": positions}


AAPL_POSITION = {
    "symbol": "AAPL",
    "description": "Apple Inc",
    "asset_type": "Stock",
    "quantity": 10.0,
    "cost_basis_per_share": 130.00,
    "current_price": 150.25,
    "acquisition_date": "2023-01-15",
}

FXAIX_POSITION = {
    "symbol": "FXAIX",
    "description": "Fidelity 500 Index Fund",
    "asset_type": "Mutual Fund",
    "quantity": 5.5,
    "cost_basis_per_share": 120.00,
    "current_price": 140.00,
    "acquisition_date": "2022-06-20",
}


# ---------------------------------------------------------------------------
# Normalized format
# ---------------------------------------------------------------------------

class TestNormalizedFormat:
    def test_single_position_creates_one_asset(self):
        portfolio = import_from_dict(_normalized_payload([AAPL_POSITION]))

        assert len(portfolio.assets) == 1
        asset = portfolio.assets[0]
        assert asset.ticker_symbol == "AAPL"
        assert asset.display_name == "Apple Inc"
        assert asset.asset_type == "Stock"

    def test_single_position_values(self):
        portfolio = import_from_dict(_normalized_payload([AAPL_POSITION]))

        position = portfolio.assets[0].positions[0]
        assert position.units == 10.0
        assert position.usd_price == 130.00
        assert position.current_price == 150.25

    def test_position_cost_basis_total(self):
        portfolio = import_from_dict(_normalized_payload([AAPL_POSITION]))

        assert portfolio.assets[0].total_usd_value() == pytest.approx(1300.00)

    def test_position_market_value(self):
        portfolio = import_from_dict(_normalized_payload([AAPL_POSITION]))

        assert portfolio.assets[0].positions[0].current_market_value() == pytest.approx(1502.50)

    def test_multiple_positions_create_multiple_assets(self):
        portfolio = import_from_dict(_normalized_payload([AAPL_POSITION, FXAIX_POSITION]))

        assert len(portfolio.assets) == 2
        tickers = {a.ticker_symbol for a in portfolio.assets}
        assert tickers == {"AAPL", "FXAIX"}

    def test_portfolio_total_value_is_sum_of_cost_bases(self):
        portfolio = import_from_dict(_normalized_payload([AAPL_POSITION, FXAIX_POSITION]))

        # AAPL: 10 * 130 = 1300; FXAIX: 5.5 * 120 = 660
        assert portfolio.total_value() == pytest.approx(1960.00)

    def test_duplicate_tickers_merged_as_separate_lots(self):
        """Two entries with the same symbol represent two purchase lots of one asset."""
        second_lot = {**AAPL_POSITION, "quantity": 5.0, "cost_basis_per_share": 145.00, "acquisition_date": "2024-03-01"}
        portfolio = import_from_dict(_normalized_payload([AAPL_POSITION, second_lot]))

        assert len(portfolio.assets) == 1
        assert len(portfolio.assets[0].positions) == 2

    def test_empty_positions_list_creates_empty_portfolio(self):
        portfolio = import_from_dict(_normalized_payload([]))

        assert len(portfolio.assets) == 0
        assert portfolio.total_value() == 0

    def test_acquisition_date_parsed_iso_format(self):
        portfolio = import_from_dict(_normalized_payload([AAPL_POSITION]))

        assert portfolio.assets[0].positions[0].purchase_datetime == dt.datetime(2023, 1, 15)

    def test_acquisition_date_parsed_us_slash_format(self):
        pos = {**AAPL_POSITION, "acquisition_date": "01/15/2023"}
        portfolio = import_from_dict(_normalized_payload([pos]))

        assert portfolio.assets[0].positions[0].purchase_datetime == dt.datetime(2023, 1, 15)

    def test_missing_acquisition_date_uses_epoch(self):
        pos = {k: v for k, v in AAPL_POSITION.items() if k != "acquisition_date"}
        portfolio = import_from_dict(_normalized_payload([pos]))

        assert portfolio.assets[0].positions[0].purchase_datetime == dt.datetime(1970, 1, 1)

    def test_fallback_to_current_price_when_no_cost_basis(self):
        pos = {k: v for k, v in AAPL_POSITION.items() if k != "cost_basis_per_share"}
        portfolio = import_from_dict(_normalized_payload([pos]))

        assert portfolio.assets[0].positions[0].usd_price == 150.25

    def test_missing_symbol_raises_value_error(self):
        pos = {k: v for k, v in AAPL_POSITION.items() if k != "symbol"}
        with pytest.raises(ValueError, match="missing a symbol"):
            import_from_dict(_normalized_payload([pos]))

    def test_missing_price_raises_value_error(self):
        pos = {k: v for k, v in AAPL_POSITION.items() if k not in ("cost_basis_per_share", "current_price")}
        with pytest.raises(ValueError, match="no price information"):
            import_from_dict(_normalized_payload([pos]))

    def test_import_from_json_string(self):
        payload = json.dumps(_normalized_payload([AAPL_POSITION]))
        portfolio = import_from_json(payload)

        assert len(portfolio.assets) == 1
        assert portfolio.assets[0].ticker_symbol == "AAPL"

    def test_import_from_file(self, tmp_path):
        payload = _normalized_payload([AAPL_POSITION, FXAIX_POSITION])
        filepath = tmp_path / "portfolio.json"
        filepath.write_text(json.dumps(payload), encoding="utf-8")

        portfolio = import_from_file(str(filepath))

        assert len(portfolio.assets) == 2


# ---------------------------------------------------------------------------
# E-Trade PortfolioResponse format
# ---------------------------------------------------------------------------

class TestETradeFormat:
    def _payload(self):
        return {
            "PortfolioResponse": {
                "AccountPortfolio": [
                    {
                        "accountId": "ETRD-12345",
                        "Position": [
                            {
                                "symbolDescription": "Apple Inc",
                                "symbol": "AAPL",
                                "typeDescription": "EQ",
                                "quantity": 10,
                                "currentPrice": 150.25,
                                "dateAcquired": "01/15/2023",
                                "costPerShare": 130.00,
                            },
                            {
                                "symbolDescription": "Vanguard Total Stock Market ETF",
                                "symbol": "VTI",
                                "typeDescription": "ETF",
                                "quantity": 3,
                                "currentPrice": 220.00,
                                "dateAcquired": "03/10/2022",
                                "costPerShare": 200.00,
                            },
                        ],
                    }
                ]
            }
        }

    def test_imports_all_positions(self):
        portfolio = import_from_dict(self._payload())

        assert len(portfolio.assets) == 2

    def test_symbol_and_type_mapped(self):
        portfolio = import_from_dict(self._payload())
        tickers = {a.ticker_symbol for a in portfolio.assets}

        assert "AAPL" in tickers
        assert "VTI" in tickers

    def test_cost_per_share_used_as_usd_price(self):
        portfolio = import_from_dict(self._payload())
        aapl = next(a for a in portfolio.assets if a.ticker_symbol == "AAPL")

        assert aapl.positions[0].usd_price == 130.00

    def test_current_price_stored(self):
        portfolio = import_from_dict(self._payload())
        aapl = next(a for a in portfolio.assets if a.ticker_symbol == "AAPL")

        assert aapl.positions[0].current_price == 150.25

    def test_multiple_accounts_merged(self):
        data = {
            "PortfolioResponse": {
                "AccountPortfolio": [
                    {"accountId": "A1", "Position": [{"symbol": "AAPL", "quantity": 5, "costPerShare": 130.00, "currentPrice": 150.00, "dateAcquired": "2023-01-01"}]},
                    {"accountId": "A2", "Position": [{"symbol": "MSFT", "quantity": 3, "costPerShare": 300.00, "currentPrice": 350.00, "dateAcquired": "2022-06-01"}]},
                ]
            }
        }
        portfolio = import_from_dict(data)

        assert len(portfolio.assets) == 2


# ---------------------------------------------------------------------------
# Fidelity accounts format
# ---------------------------------------------------------------------------

class TestFidelityFormat:
    def _payload(self):
        return {
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
                            "costBasisPerShare": 130.00,
                        },
                        {
                            "description": "ISHARES CORE S&P 500 ETF",
                            "symbol": "IVV",
                            "type": "ETF",
                            "quantity": 2.0,
                            "lastPrice": 500.00,
                            "acquisitionDate": "2021-09-30",
                            "costBasisPerShare": 430.00,
                        },
                    ],
                }
            ]
        }

    def test_imports_all_positions(self):
        portfolio = import_from_dict(self._payload())

        assert len(portfolio.assets) == 2

    def test_last_price_stored_as_current_price(self):
        portfolio = import_from_dict(self._payload())
        aapl = next(a for a in portfolio.assets if a.ticker_symbol == "AAPL")

        assert aapl.positions[0].current_price == 150.25

    def test_cost_basis_per_share_used_as_usd_price(self):
        portfolio = import_from_dict(self._payload())
        aapl = next(a for a in portfolio.assets if a.ticker_symbol == "AAPL")

        assert aapl.positions[0].usd_price == 130.00

    def test_acquisition_date_parsed(self):
        portfolio = import_from_dict(self._payload())
        aapl = next(a for a in portfolio.assets if a.ticker_symbol == "AAPL")

        assert aapl.positions[0].purchase_datetime == dt.datetime(2023, 1, 15)

    def test_multiple_fidelity_accounts_merged(self):
        data = {
            "accounts": [
                {"accountId": "A1", "positions": [{"symbol": "AAPL", "quantity": 5, "costBasisPerShare": 130.00, "lastPrice": 150.00, "acquisitionDate": "2023-01-01"}]},
                {"accountId": "A2", "positions": [{"symbol": "MSFT", "quantity": 3, "costBasisPerShare": 300.00, "lastPrice": 350.00, "acquisitionDate": "2022-06-01"}]},
            ]
        }
        portfolio = import_from_dict(data)

        assert len(portfolio.assets) == 2


# ---------------------------------------------------------------------------
# Single-account wrapper format
# ---------------------------------------------------------------------------

class TestSingleAccountFormat:
    def test_account_wrapper_parsed(self):
        data = {
            "account": {
                "id": "ACC-001",
                "positions": [
                    {"symbol": "TSLA", "quantity": 2, "cost_basis_per_share": 200.00, "current_price": 250.00, "acquisition_date": "2023-07-01"}
                ],
            }
        }
        portfolio = import_from_dict(data)

        assert len(portfolio.assets) == 1
        assert portfolio.assets[0].ticker_symbol == "TSLA"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    def test_unrecognized_format_raises_value_error(self):
        with pytest.raises(ValueError, match="Unrecognized JSON format"):
            import_from_dict({"something_unknown": []})

    def test_invalid_json_string_raises_json_decode_error(self):
        with pytest.raises(json.JSONDecodeError):
            import_from_json("not valid json {{{")

    def test_invalid_date_raises_value_error(self):
        pos = {**AAPL_POSITION, "acquisition_date": "not-a-date"}
        with pytest.raises(ValueError, match="Unable to parse date"):
            import_from_dict(_normalized_payload([pos]))
