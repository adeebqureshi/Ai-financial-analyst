import pytest
from app.portfolio.beta import Beta


def test_beta_positive():
    """Normal positive beta: covariance=0.2, market_variance=0.1 => beta=2.0."""
    beta = Beta()
    assert beta.calculate(0.2, 0.1) == 2.0


def test_beta_negative_covariance():
    """Negative covariance with positive market variance yields negative beta."""
    beta = Beta()
    # covariance = -0.15, market_variance = 0.1 => beta = -1.5
    assert beta.calculate(-0.15, 0.1) == pytest.approx(-1.5, abs=1e-10)


def test_beta_zero_market_variance():
    """Zero market variance returns 0.0 (safe fallback, no division by zero)."""
    beta = Beta()
    assert beta.calculate(0.2, 0.0) == 0.0
    assert beta.calculate(-0.2, 0.0) == 0.0
    assert beta.calculate(0.0, 0.0) == 0.0


def test_beta_zero_covariance():
    """Zero covariance yields zero beta (uncorrelated with market)."""
    beta = Beta()
    assert beta.calculate(0.0, 0.1) == 0.0


def test_beta_small_market_variance():
    """Very small market variance produces large beta magnitude."""
    beta = Beta()
    # covariance=0.01, market_variance=0.0001 => beta=100
    assert beta.calculate(0.01, 0.0001) == 100.0


def test_beta_large_market_variance():
    """Large market variance produces small beta magnitude."""
    beta = Beta()
    # covariance=0.2, market_variance=10.0 => beta=0.02
    assert beta.calculate(0.2, 10.0) == 0.02


def test_beta_negative_market_variance():
    """Negative market variance (invalid) - returns negative beta per formula."""
    beta = Beta()
    # covariance=0.2, market_variance=-0.1 => beta=-2.0
    # Note: variance cannot be negative in practice, but function handles it mathematically
    assert beta.calculate(0.2, -0.1) == -2.0


def test_beta_approximately_zero():
    """Beta near zero for near-zero covariance."""
    beta = Beta()
    result = beta.calculate(0.0001, 0.1)
    assert result == pytest.approx(0.001, abs=1e-6)