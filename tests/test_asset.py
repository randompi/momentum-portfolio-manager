from src.models.asset import Asset
from src.models.position import Position
import datetime as dt

def test_total_usd_value_no_positions_is_0():
    """
    GIVEN: an asset with 0 positions
    WHEN: total_usd_value is called
    THEN: expect 0 is returned
    """
    test_asset = Asset()
    
    asset_total_usd_value = test_asset.total_usd_value()

    assert asset_total_usd_value == 0

def test_total_usd_value_1x1_is_1():
    """
    GIVEN: an asset with 1 position unit at 1 usd
    WHEN: total_usd_value is called
    THEN: expect 1 is returned
    """
    test_asset = Asset()
    test_position = Position(1, 1.0, dt.datetime.now())
    test_asset.add_position(test_position)

    asset_total_usd_value = test_asset.total_usd_value()

    assert asset_total_usd_value == 1