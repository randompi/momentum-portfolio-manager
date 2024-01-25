from src.models.portfolio import Portfolio

def test_total_value():
    """
    GIVEN: a portfolio with no assets
    WHEN: total_value is called
    THEN: expect 0 is returned
    """
    test_portfolio = Portfolio()

    portfolio_total_value = test_portfolio.total_value()

    assert portfolio_total_value == 0