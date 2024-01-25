from src.models.position import Position
import datetime as dt

def test_total_usd_value_1x1_is_1():
    """
    GIVEN: a position with no 1 unit at 1 usd
    WHEN: total_usd_value is called
    THEN: expect 1 is returned
    """
    test_position = Position(1, 1.0, dt.datetime.now())

    position_total_usd_value = test_position.total_usd_value()

    assert position_total_usd_value == 1

def test_total_usd_value_2x3_is_6():
    """
    GIVEN: a position with no 2 units at 3 usd
    WHEN: total_usd_value is called
    THEN: expect 6 is returned
    """
    test_position = Position(2, 3.0, dt.datetime.now())

    position_total_usd_value = test_position.total_usd_value()

    assert position_total_usd_value == 6