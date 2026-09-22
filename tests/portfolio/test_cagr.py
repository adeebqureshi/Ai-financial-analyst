import pytest
from app.portfolio.cagr import CAGR
def test_cagr_positive_growth():
    cagr = CAGR()
    result = cagr.calculate(100, 200, 5)
    assert result == pytest.approx(0.148698, rel=1e-4)
def test_cagr_zero_years():
    cagr = CAGR()
    assert cagr.calculate(100, 200, 0) == 0.0
    assert cagr.calculate(100, 200, -1) == 0.0
def test_cagr_zero_beginning():
    cagr = CAGR()
    assert cagr.calculate(0, 200, 5) == 0.0
    assert cagr.calculate(-100, 200, 5) == 0.0
def test_cagr_equal_start_end():
    cagr = CAGR()
    assert cagr.calculate(100, 100, 5) == 0.0
def test_cagr_declining_value():
    cagr = CAGR()
    result = cagr.calculate(200, 100, 5)
    assert result == pytest.approx(-0.129449, rel=1e-4)
def test_cagr_one_year():
    cagr = CAGR()
    assert cagr.calculate(100, 120, 1) == pytest.approx(0.20, abs=1e-10)
def test_cagr_large_growth():
    cagr = CAGR()
    result = cagr.calculate(100, 10000, 10)
    assert result == pytest.approx(0.584893, rel=1e-4)
def test_cagr_fractional_years():
    cagr = CAGR()
    result = cagr.calculate(100, 200, 2.5)
    assert result == pytest.approx(0.3195, rel=1e-3)