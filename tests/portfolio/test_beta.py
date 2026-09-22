import pytest
from app.portfolio.beta import Beta
def test_beta_positive():
    beta = Beta()
    assert beta.calculate(0.2, 0.1) == 2.0
def test_beta_negative_covariance():
    beta = Beta()
    assert beta.calculate(-0.15, 0.1) == pytest.approx(-1.5, abs=1e-10)
def test_beta_zero_market_variance():
    beta = Beta()
    assert beta.calculate(0.2, 0.0) == 0.0
    assert beta.calculate(-0.2, 0.0) == 0.0
    assert beta.calculate(0.0, 0.0) == 0.0
def test_beta_zero_covariance():
    beta = Beta()
    assert beta.calculate(0.0, 0.1) == 0.0
def test_beta_small_market_variance():
    beta = Beta()
    assert beta.calculate(0.01, 0.0001) == 100.0
def test_beta_large_market_variance():
    beta = Beta()
    assert beta.calculate(0.2, 10.0) == 0.02
def test_beta_negative_market_variance():
    beta = Beta()
    assert beta.calculate(0.2, -0.1) == -2.0
def test_beta_approximately_zero():
    beta = Beta()
    result = beta.calculate(0.0001, 0.1)
    assert result == pytest.approx(0.001, abs=1e-6)