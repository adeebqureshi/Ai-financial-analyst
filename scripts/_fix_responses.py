import pathlib

p = pathlib.Path("app/schemas/responses.py")
t = p.read_text()

old = '''    model_config = ConfigDict(populate_by_name=True)

    intrinsic_value: float = Field(..., description="Estimated intrinsic value per share ($).")
    upside: float = Field(..., description="Upside percentage.")
    recommendation: str = Field(..., description="Investment recommendation (STRONG BUY/BUY/HOLD/SELL).")
    current_price: float = Field(..., description="Current market price per share ($).")
    discount_rate: float = Field(..., description="WACC discount rate used in the DCF.")
'''

new = '''    model_config = ConfigDict(populate_by_name=True)

    intrinsic_value: float = Field(..., description="Estimated intrinsic value per share ($).")
    upside: float = Field(..., description="Upside percentage.")
    recommendation: str = Field(..., description="Investment recommendation (STRONG BUY/BUY/HOLD/SELL).")
    current_price: float | None = Field(
        default=None,
        ge=0,
        description="Current market price per share ($); null when unavailable.",
    )
    discount_rate: float = Field(..., description="WACC discount rate used in the DCF.")

    # -- Assumption provenance ------------------------------------------------
    assumptions_source: str | None = Field(
        default=None,
        description=(
            "Where the valuation inputs came from: 'default' (built-in "
            "assumptions), 'configured' (deployment settings), or 'request' "
            "(client-supplied parameters)."
        ),
    )
    assumptions_as_of: date | None = Field(
        default=None,
        description="Date the valuation assumptions were set/validated.",
    )
    risk_free_rate: float | None = Field(
        default=None,
        ge=0,
        description="Risk-free rate used (decimal). An assumption, not live data.",
    )
    market_return: float | None = Field(
        default=None,
        ge=0,
        description="Expected market return used (decimal). An assumption, not live data.",
    )
    cost_of_debt: float | None = Field(
        default=None,
        ge=0,
        description="Pre-tax cost of debt used (decimal). An assumption, not live data.",
    )
'''

assert old in t, "ValuationResultData block not found"
t = t.replace(old, new, 1)
p.write_text(t)
print("ValuationResultData updated")
