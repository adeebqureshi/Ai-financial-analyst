from __future__ import annotations
from dataclasses import dataclass
from typing import Final
@dataclass(slots=True, frozen=True)
class MultiPeriodFinancialData:
    revenue_t: float
    operating_income_t: float
    net_income_t: float
    total_assets_t: float
    total_liabilities_t: float
    cash_t: float
    debt_t: float
    shares_t: float
    free_cash_flow_t: float
    gross_profit_t: float
    current_assets_t: float
    current_liabilities_t: float
    retained_earnings_t: float
    long_term_debt_t: float
    receivables_t: float
    cogs_t: float
    sga_t: float
    depreciation_t: float
    net_ppe_t: float
    operating_cash_flow_t: float
    tax_provision_t: float
    pretax_income_t: float
    revenue_p: float
    operating_income_p: float
    net_income_p: float
    total_assets_p: float
    total_liabilities_p: float
    cash_p: float
    debt_p: float
    shares_p: float
    free_cash_flow_p: float
    gross_profit_p: float
    current_assets_p: float
    current_liabilities_p: float
    retained_earnings_p: float
    long_term_debt_p: float
    receivables_p: float
    cogs_p: float
    sga_p: float
    depreciation_p: float
    net_ppe_p: float
    operating_cash_flow_p: float
    market_price: float
    beta: float
    expected_piotroski: int
    expected_altman: float
    expected_beneish: float
    expected_dcf_intrinsic: float
EVAL_AAPL = MultiPeriodFinancialData(
    revenue_t=383_285.0,
    operating_income_t=114_301.0,
    net_income_t=96_995.0,
    total_assets_t=352_755.0,
    total_liabilities_t=290_437.0,
    cash_t=62_639.0,
    debt_t=109_106.0,
    shares_t=15_550.0,
    free_cash_flow_t=110_543.0,
    gross_profit_t=169_148.0,
    current_assets_t=135_405.0,
    current_liabilities_t=145_308.0,
    retained_earnings_t=55_000.0,
    long_term_debt_t=95_000.0,
    receivables_t=35_000.0,
    cogs_t=214_137.0,
    sga_t=25_000.0,
    depreciation_t=11_000.0,
    net_ppe_t=45_000.0,
    operating_cash_flow_t=115_000.0,
    tax_provision_t=18_500.0,
    pretax_income_t=115_500.0,
    revenue_p=383_927.0,
    operating_income_p=114_301.0,
    net_income_p=96_995.0,
    total_assets_p=352_583.0,
    total_liabilities_p=290_000.0,
    cash_p=61_000.0,
    debt_p=110_000.0,
    shares_p=15_600.0,
    free_cash_flow_p=109_000.0,
    gross_profit_p=168_000.0,
    current_assets_p=134_000.0,
    current_liabilities_p=144_000.0,
    retained_earnings_p=52_000.0,
    long_term_debt_p=98_000.0,
    receivables_p=34_000.0,
    cogs_p=215_000.0,
    sga_p=24_500.0,
    depreciation_p=10_800.0,
    net_ppe_p=44_000.0,
    operating_cash_flow_p=114_000.0,
    market_price=180.0,
    beta=1.25,
    expected_piotroski=7,
    expected_altman=8.1227,
    expected_beneish=-2.7020,
    expected_dcf_intrinsic=93.9189,
)
EVAL_MSFT = MultiPeriodFinancialData(
    revenue_t=211_915.0,
    operating_income_t=88_523.0,
    net_income_t=72_361.0,
    total_assets_t=411_976.0,
    total_liabilities_t=205_753.0,
    cash_t=81_054.0,
    debt_t=47_032.0,
    shares_t=7_430.0,
    free_cash_flow_t=74_072.0,
    gross_profit_t=146_048.0,
    current_assets_t=187_475.0,
    current_liabilities_t=110_268.0,
    retained_earnings_t=185_000.0,
    long_term_debt_t=40_000.0,
    receivables_t=45_000.0,
    cogs_t=65_867.0,
    sga_t=25_000.0,
    depreciation_t=13_000.0,
    net_ppe_t=60_000.0,
    operating_cash_flow_t=85_000.0,
    tax_provision_t=16_000.0,
    pretax_income_t=88_500.0,
    revenue_p=198_270.0,
    operating_income_p=83_383.0,
    net_income_p=72_738.0,
    total_assets_p=364_840.0,
    total_liabilities_p=198_000.0,
    cash_p=78_000.0,
    debt_p=45_000.0,
    shares_p=7_450.0,
    free_cash_flow_p=70_000.0,
    gross_profit_p=135_000.0,
    current_assets_p=180_000.0,
    current_liabilities_p=105_000.0,
    retained_earnings_p=175_000.0,
    long_term_debt_p=42_000.0,
    receivables_p=42_000.0,
    cogs_p=63_000.0,
    sga_p=24_000.0,
    depreciation_p=12_500.0,
    net_ppe_p=58_000.0,
    operating_cash_flow_p=82_000.0,
    market_price=390.0,
    beta=0.92,
    expected_piotroski=6,
    expected_altman=10.5271,
    expected_beneish=-2.4478,
    expected_dcf_intrinsic=172.8117,
)
EVAL_GOOGL = MultiPeriodFinancialData(
    revenue_t=307_394.0,
    operating_income_t=84_293.0,
    net_income_t=73_795.0,
    total_assets_t=365_264.0,
    total_liabilities_t=109_120.0,
    cash_t=110_916.0,
    debt_t=14_798.0,
    shares_t=12_530.0,
    free_cash_flow_t=69_505.0,
    gross_profit_t=172_224.0,
    current_assets_t=169_126.0,
    current_liabilities_t=78_006.0,
    retained_earnings_t=230_000.0,
    long_term_debt_t=12_000.0,
    receivables_t=40_000.0,
    cogs_t=135_170.0,
    sga_t=30_000.0,
    depreciation_t=14_000.0,
    net_ppe_t=80_000.0,
    operating_cash_flow_t=85_000.0,
    tax_provision_t=15_000.0,
    pretax_income_t=89_000.0,
    revenue_p=282_836.0,
    operating_income_p=74_842.0,
    net_income_p=59_972.0,
    total_assets_p=340_000.0,
    total_liabilities_p=105_000.0,
    cash_p=108_000.0,
    debt_p=14_000.0,
    shares_p=12_600.0,
    free_cash_flow_p=65_000.0,
    gross_profit_p=160_000.0,
    current_assets_p=162_000.0,
    current_liabilities_p=75_000.0,
    retained_earnings_p=215_000.0,
    long_term_debt_p=13_000.0,
    receivables_p=38_000.0,
    cogs_p=122_000.0,
    sga_p=29_000.0,
    depreciation_p=13_500.0,
    net_ppe_p=78_000.0,
    operating_cash_flow_p=80_000.0,
    market_price=142.0,
    beta=1.05,
    expected_piotroski=8,
    expected_altman=12.5673,
    expected_beneish=-2.5293,
    expected_dcf_intrinsic=103.6049,
)
EVAL_AMZN = MultiPeriodFinancialData(
    revenue_t=574_785.0,
    operating_income_t=36_852.0,
    net_income_t=30_425.0,
    total_assets_t=527_854.0,
    total_liabilities_t=320_111.0,
    cash_t=86_820.0,
    debt_t=84_328.0,
    shares_t=10_350.0,
    free_cash_flow_t=50_149.0,
    gross_profit_t=270_051.0,
    current_assets_t=187_390.0,
    current_liabilities_t=184_863.0,
    retained_earnings_t=180_000.0,
    long_term_debt_t=75_000.0,
    receivables_t=55_000.0,
    cogs_t=304_734.0,
    sga_t=180_000.0,
    depreciation_t=55_000.0,
    net_ppe_t=200_000.0,
    operating_cash_flow_t=85_000.0,
    tax_provision_t=5_000.0,
    pretax_income_t=35_500.0,
    revenue_p=513_983.0,
    operating_income_p=12_248.0,
    net_income_p=-2_722.0,
    total_assets_p=462_675.0,
    total_liabilities_p=295_000.0,
    cash_p=84_000.0,
    debt_p=80_000.0,
    shares_p=10_300.0,
    free_cash_flow_p=30_000.0,
    gross_profit_p=240_000.0,
    current_assets_p=175_000.0,
    current_liabilities_p=170_000.0,
    retained_earnings_p=155_000.0,
    long_term_debt_p=72_000.0,
    receivables_p=50_000.0,
    cogs_p=273_000.0,
    sga_p=170_000.0,
    depreciation_p=50_000.0,
    net_ppe_p=190_000.0,
    operating_cash_flow_p=60_000.0,
    market_price=145.0,
    beta=1.15,
    expected_piotroski=6,
    expected_altman=4.6154,
    expected_beneish=-2.7377,
    expected_dcf_intrinsic=102.8875,
)
EVAL_TSLA = MultiPeriodFinancialData(
    revenue_t=96_773.0,
    operating_income_t=8_891.0,
    net_income_t=12_556.0,
    total_assets_t=106_618.0,
    total_liabilities_t=50_360.0,
    cash_t=29_089.0,
    debt_t=5_748.0,
    shares_t=3_180.0,
    free_cash_flow_t=4_410.0,
    gross_profit_t=17_620.0,
    current_assets_t=57_072.0,
    current_liabilities_t=34_041.0,
    retained_earnings_t=50_000.0,
    long_term_debt_t=5_000.0,
    receivables_t=8_000.0,
    cogs_t=79_153.0,
    sga_t=8_000.0,
    depreciation_t=3_500.0,
    net_ppe_t=35_000.0,
    operating_cash_flow_t=10_000.0,
    tax_provision_t=1_000.0,
    pretax_income_t=13_500.0,
    revenue_p=81_462.0,
    operating_income_p=13_656.0,
    net_income_p=12_556.0,
    total_assets_p=82_338.0,
    total_liabilities_p=36_000.0,
    cash_p=25_000.0,
    debt_p=6_000.0,
    shares_p=3_150.0,
    free_cash_flow_p=7_500.0,
    gross_profit_p=15_000.0,
    current_assets_p=50_000.0,
    current_liabilities_p=30_000.0,
    retained_earnings_p=45_000.0,
    long_term_debt_p=5_500.0,
    receivables_p=7_000.0,
    cogs_p=66_000.0,
    sga_p=7_500.0,
    depreciation_p=3_200.0,
    net_ppe_p=33_000.0,
    operating_cash_flow_p=12_000.0,
    market_price=250.0,
    beta=2.15,
    expected_piotroski=4,
    expected_altman=11.5704,
    expected_beneish=-9.4871,
    expected_dcf_intrinsic=38.7622,
)
EVAL_TICKERS: Final[list[str]] = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
EVAL_DATA: Final[dict[str, MultiPeriodFinancialData]] = {
    "AAPL": EVAL_AAPL,
    "MSFT": EVAL_MSFT,
    "GOOGL": EVAL_GOOGL,
    "AMZN": EVAL_AMZN,
    "TSLA": EVAL_TSLA,
}