import pytest
from app.portfolio.cagr import CAGR


def test_cagr_positive_growth():
    """Normal positive CAGR: 100 to 200 over 5 years ≈ 14.87%."""
    cagr = CAGR()
    result = cagr.calculate(100, 200, 5)
    assert result == pytest.approx(0.148698, rel=1e-4)


def test_cagr_zero_years():
    """Years <= 0 returns 0.0 (safe fallback, no exception)."""
    cagr = CAGR()
    assert cagr.calculate(100, 200, 0) == 0.0
    assert cagr.calculate(100, 200, -1) == 0.0


def test_cagr_zero_beginning():
    """Beginning value <= 0 returns 0.0 (safe fallback, no exception)."""
    cagr = CAGR()
    assert cagr.calculate(0, 200, 5) == 0.0
    assert cagr.calculate(-100, 200, 5) == 0.0


def test_cagr_equal_start_end():
    """Equal beginning and ending values yields 0% CAGR."""
    cagr = CAGR()
    assert cagr.calculate(100, 100, 5) == 0.0


def test_cagr_declining_value():
    """Declining value produces negative CAGR."""
    cagr = CAGR()
    # 200 to 100 over 5 years: (0.5)^(1/5) - 1
    result = cagr.calculate(200, 100, 5)
    assert result == pytest.approx(-0.129449, rel=1e-4)


def test_cagr_one_year():
    """One-year period equals simple growth rate."""
    cagr = CAGR()
    assert cagr.calculate(100, 120, 1) == pytest.approx(0.20, abs=1e-10)


def test_cagr_large_growth():
    """High growth over multiple years."""
    cagr = CAGR()
    # 100 to 10000 over 10 years
    result = cagr.calculate(100, 10000, 10)
    assert result == pytest.approx(0.584893, rel=1e-4)


def test_cagr_fractional_years():
    """Fractional years are supported (e.g., 2.5 years)."""
    cagr = CAGR()
    # 100 to 200 over 2.5 years
    result = cagr.calculate(100, 200, 2.5)
    assert result == pytest.approx(0.3195, rel=1e-3)