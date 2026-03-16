"""Master registry of all economic indicators tracked by the monitor."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Indicator:
    name: str           # Human-readable name
    fred_id: str        # FRED series identifier
    category: str       # Grouping category
    frequency: str      # monthly | weekly | quarterly | daily
    unit: str           # index | percent | thousands | millions | billions | ratio
    release_url: str    # Government page to monitor for changes
    transform: str      # How to display: level | yoy_pct | mom_pct | net_change | annualized
    higher_is: str      # inflationary | expansionary | contractionary | neutral
    description: str    # Short description


# ---------------------------------------------------------------------------
# Full indicator registry
# ---------------------------------------------------------------------------

INDICATORS: dict[str, Indicator] = {}


def _register(*indicators: Indicator) -> None:
    for ind in indicators:
        INDICATORS[ind.fred_id] = ind


# ── Inflation ──────────────────────────────────────────────────────────────
_register(
    Indicator(
        name="CPI (All Urban)",
        fred_id="CPIAUCSL",
        category="Inflation",
        frequency="monthly",
        unit="index",
        release_url="https://www.bls.gov/cpi/",
        transform="yoy_pct",
        higher_is="inflationary",
        description="Consumer Price Index for All Urban Consumers, seasonally adjusted",
    ),
    Indicator(
        name="Core CPI",
        fred_id="CPILFESL",
        category="Inflation",
        frequency="monthly",
        unit="index",
        release_url="https://www.bls.gov/cpi/",
        transform="yoy_pct",
        higher_is="inflationary",
        description="CPI excluding food and energy, seasonally adjusted",
    ),
    Indicator(
        name="PPI (Final Demand)",
        fred_id="PPIFIS",
        category="Inflation",
        frequency="monthly",
        unit="index",
        release_url="https://www.bls.gov/ppi/",
        transform="yoy_pct",
        higher_is="inflationary",
        description="Producer Price Index for Final Demand, seasonally adjusted",
    ),
    Indicator(
        name="PCE Price Index",
        fred_id="PCEPI",
        category="Inflation",
        frequency="monthly",
        unit="index",
        release_url="https://www.bea.gov/data/personal-consumption-expenditures-price-index",
        transform="yoy_pct",
        higher_is="inflationary",
        description="Personal Consumption Expenditures Price Index",
    ),
    Indicator(
        name="Core PCE",
        fred_id="PCEPILFE",
        category="Inflation",
        frequency="monthly",
        unit="index",
        release_url="https://www.bea.gov/data/personal-consumption-expenditures-price-index",
        transform="yoy_pct",
        higher_is="inflationary",
        description="PCE excluding food and energy (Fed's preferred inflation gauge)",
    ),
)

# ── Labor ──────────────────────────────────────────────────────────────────
_register(
    Indicator(
        name="Nonfarm Payrolls",
        fred_id="PAYEMS",
        category="Labor",
        frequency="monthly",
        unit="thousands",
        release_url="https://www.bls.gov/ces/",
        transform="net_change",
        higher_is="expansionary",
        description="Total nonfarm employees, seasonally adjusted",
    ),
    Indicator(
        name="Unemployment Rate",
        fred_id="UNRATE",
        category="Labor",
        frequency="monthly",
        unit="percent",
        release_url="https://www.bls.gov/cps/",
        transform="level",
        higher_is="contractionary",
        description="Civilian unemployment rate, seasonally adjusted",
    ),
    Indicator(
        name="Initial Jobless Claims",
        fred_id="ICSA",
        category="Labor",
        frequency="weekly",
        unit="thousands",
        release_url="https://www.dol.gov/ui/data.pdf",
        transform="level",
        higher_is="contractionary",
        description="Initial claims for unemployment insurance, seasonally adjusted",
    ),
    Indicator(
        name="JOLTS Job Openings",
        fred_id="JTSJOL",
        category="Labor",
        frequency="monthly",
        unit="thousands",
        release_url="https://www.bls.gov/jlt/",
        transform="level",
        higher_is="expansionary",
        description="Total job openings, seasonally adjusted",
    ),
    Indicator(
        name="Labor Force Participation",
        fred_id="CIVPART",
        category="Labor",
        frequency="monthly",
        unit="percent",
        release_url="https://www.bls.gov/cps/",
        transform="level",
        higher_is="expansionary",
        description="Labor force participation rate",
    ),
    Indicator(
        name="Average Hourly Earnings",
        fred_id="CES0500000003",
        category="Labor",
        frequency="monthly",
        unit="dollars",
        release_url="https://www.bls.gov/ces/",
        transform="yoy_pct",
        higher_is="inflationary",
        description="Average hourly earnings of all private employees",
    ),
)

# ── Output ─────────────────────────────────────────────────────────────────
_register(
    Indicator(
        name="Real GDP",
        fred_id="GDPC1",
        category="Output",
        frequency="quarterly",
        unit="billions",
        release_url="https://www.bea.gov/data/gdp/gross-domestic-product",
        transform="annualized",
        higher_is="expansionary",
        description="Real Gross Domestic Product, seasonally adjusted annual rate",
    ),
    Indicator(
        name="Industrial Production",
        fred_id="INDPRO",
        category="Output",
        frequency="monthly",
        unit="index",
        release_url="https://www.federalreserve.gov/releases/g17/current/",
        transform="yoy_pct",
        higher_is="expansionary",
        description="Industrial Production Index, seasonally adjusted",
    ),
    Indicator(
        name="Capacity Utilization",
        fred_id="TCU",
        category="Output",
        frequency="monthly",
        unit="percent",
        release_url="https://www.federalreserve.gov/releases/g17/current/",
        transform="level",
        higher_is="expansionary",
        description="Total industry capacity utilization rate",
    ),
)

# ── Consumer ───────────────────────────────────────────────────────────────
_register(
    Indicator(
        name="Retail Sales",
        fred_id="RSAFS",
        category="Consumer",
        frequency="monthly",
        unit="millions",
        release_url="https://www.census.gov/retail/index.html",
        transform="mom_pct",
        higher_is="expansionary",
        description="Advance retail sales, seasonally adjusted",
    ),
    Indicator(
        name="UMich Consumer Sentiment",
        fred_id="UMCSENT",
        category="Consumer",
        frequency="monthly",
        unit="index",
        release_url="http://www.sca.isr.umich.edu/",
        transform="level",
        higher_is="expansionary",
        description="University of Michigan Consumer Sentiment Index",
    ),
    Indicator(
        name="Personal Income",
        fred_id="PI",
        category="Consumer",
        frequency="monthly",
        unit="billions",
        release_url="https://www.bea.gov/data/income-saving/personal-income",
        transform="mom_pct",
        higher_is="expansionary",
        description="Personal income, seasonally adjusted annual rate",
    ),
    Indicator(
        name="Personal Spending (PCE)",
        fred_id="PCE",
        category="Consumer",
        frequency="monthly",
        unit="billions",
        release_url="https://www.bea.gov/data/income-saving/personal-income",
        transform="mom_pct",
        higher_is="expansionary",
        description="Personal consumption expenditures, seasonally adjusted annual rate",
    ),
    Indicator(
        name="Personal Saving Rate",
        fred_id="PSAVERT",
        category="Consumer",
        frequency="monthly",
        unit="percent",
        release_url="https://www.bea.gov/data/income-saving/personal-income",
        transform="level",
        higher_is="neutral",
        description="Personal saving as a percentage of disposable income",
    ),
)

# ── Business Surveys ───────────────────────────────────────────────────────
_register(
    Indicator(
        name="ISM Manufacturing PMI",
        fred_id="MANEMP",
        category="Business",
        frequency="monthly",
        unit="index",
        release_url="https://www.ismworld.org/supply-management-news-and-reports/reports/ism-report-on-business/",
        transform="level",
        higher_is="expansionary",
        description="ISM Manufacturing Employment Index (PMI proxy)",
    ),
    Indicator(
        name="Durable Goods Orders",
        fred_id="DGORDER",
        category="Business",
        frequency="monthly",
        unit="millions",
        release_url="https://www.census.gov/manufacturing/m3/index.html",
        transform="mom_pct",
        higher_is="expansionary",
        description="Manufacturers' new orders for durable goods, seasonally adjusted",
    ),
)

# ── Housing ────────────────────────────────────────────────────────────────
_register(
    Indicator(
        name="Housing Starts",
        fred_id="HOUST",
        category="Housing",
        frequency="monthly",
        unit="thousands",
        release_url="https://www.census.gov/construction/nrc/index.html",
        transform="level",
        higher_is="expansionary",
        description="New privately-owned housing units started, SAAR",
    ),
    Indicator(
        name="Building Permits",
        fred_id="PERMIT",
        category="Housing",
        frequency="monthly",
        unit="thousands",
        release_url="https://www.census.gov/construction/nrc/index.html",
        transform="level",
        higher_is="expansionary",
        description="New private housing units authorized by building permits, SAAR",
    ),
    Indicator(
        name="Existing Home Sales",
        fred_id="EXHOSLUSM495S",
        category="Housing",
        frequency="monthly",
        unit="units",
        release_url="https://www.nar.realtor/research-and-statistics/housing-statistics/existing-home-sales",
        transform="level",
        higher_is="expansionary",
        description="Existing home sales, seasonally adjusted",
    ),
    Indicator(
        name="New Home Sales",
        fred_id="HSN1F",
        category="Housing",
        frequency="monthly",
        unit="thousands",
        release_url="https://www.census.gov/construction/nrs/index.html",
        transform="level",
        higher_is="expansionary",
        description="New one-family houses sold, SAAR",
    ),
    Indicator(
        name="Case-Shiller Home Price Index",
        fred_id="CSUSHPINSA",
        category="Housing",
        frequency="monthly",
        unit="index",
        release_url="https://www.spglobal.com/spdji/en/index-family/indicators/sp-corelogic-case-shiller/",
        transform="yoy_pct",
        higher_is="inflationary",
        description="S&P/Case-Shiller U.S. National Home Price Index, not seasonally adjusted",
    ),
)

# ── Trade ──────────────────────────────────────────────────────────────────
_register(
    Indicator(
        name="Trade Balance",
        fred_id="BOPGSTB",
        category="Trade",
        frequency="monthly",
        unit="millions",
        release_url="https://www.bea.gov/data/intl-trade-investment/international-trade-goods-and-services",
        transform="level",
        higher_is="neutral",
        description="Balance on goods and services, BOP basis",
    ),
    Indicator(
        name="Net Exports (Real)",
        fred_id="NETEXP",
        category="Trade",
        frequency="quarterly",
        unit="billions",
        release_url="https://www.bea.gov/data/gdp/gross-domestic-product",
        transform="level",
        higher_is="neutral",
        description="Real net exports of goods and services",
    ),
)

# ── Monetary Policy ───────────────────────────────────────────────────────
_register(
    Indicator(
        name="Federal Funds Rate",
        fred_id="FEDFUNDS",
        category="Monetary",
        frequency="monthly",
        unit="percent",
        release_url="https://www.federalreserve.gov/monetarypolicy/openmarket.htm",
        transform="level",
        higher_is="contractionary",
        description="Effective federal funds rate",
    ),
    Indicator(
        name="M2 Money Supply",
        fred_id="M2SL",
        category="Monetary",
        frequency="monthly",
        unit="billions",
        release_url="https://www.federalreserve.gov/releases/h6/current/",
        transform="yoy_pct",
        higher_is="inflationary",
        description="M2 money stock, seasonally adjusted",
    ),
)

# ── Fixed Income / Yield Curve ─────────────────────────────────────────────
_register(
    Indicator(
        name="10Y-2Y Treasury Spread",
        fred_id="T10Y2Y",
        category="Fixed Income",
        frequency="daily",
        unit="percent",
        release_url="https://fred.stlouisfed.org/series/T10Y2Y",
        transform="level",
        higher_is="expansionary",
        description="10-Year minus 2-Year Treasury constant maturity spread",
    ),
    Indicator(
        name="10Y-3M Treasury Spread",
        fred_id="T10Y3M",
        category="Fixed Income",
        frequency="daily",
        unit="percent",
        release_url="https://fred.stlouisfed.org/series/T10Y3M",
        transform="level",
        higher_is="expansionary",
        description="10-Year minus 3-Month Treasury constant maturity spread",
    ),
    Indicator(
        name="HY Credit Spread (ICE BofA)",
        fred_id="BAMLH0A0HYM2",
        category="Fixed Income",
        frequency="daily",
        unit="percent",
        release_url="https://fred.stlouisfed.org/series/BAMLH0A0HYM2",
        transform="level",
        higher_is="contractionary",
        description="ICE BofA US High Yield Option-Adjusted Spread",
    ),
    Indicator(
        name="10-Year Treasury Yield",
        fred_id="DGS10",
        category="Fixed Income",
        frequency="daily",
        unit="percent",
        release_url="https://www.treasury.gov/resource-center/data-chart-center/interest-rates/",
        transform="level",
        higher_is="neutral",
        description="Market yield on U.S. Treasury securities at 10-year constant maturity",
    ),
    Indicator(
        name="2-Year Treasury Yield",
        fred_id="DGS2",
        category="Fixed Income",
        frequency="daily",
        unit="percent",
        release_url="https://www.treasury.gov/resource-center/data-chart-center/interest-rates/",
        transform="level",
        higher_is="neutral",
        description="Market yield on U.S. Treasury securities at 2-year constant maturity",
    ),
)

# ── Market Stress ──────────────────────────────────────────────────────────
_register(
    Indicator(
        name="VIX",
        fred_id="VIXCLS",
        category="Market",
        frequency="daily",
        unit="index",
        release_url="https://www.cboe.com/tradable_products/vix/",
        transform="level",
        higher_is="contractionary",
        description="CBOE Volatility Index",
    ),
    Indicator(
        name="Trade-Weighted Dollar Index",
        fred_id="DTWEXBGS",
        category="Market",
        frequency="daily",
        unit="index",
        release_url="https://www.federalreserve.gov/releases/h10/summary/",
        transform="level",
        higher_is="neutral",
        description="Nominal Broad U.S. Dollar Index",
    ),
)

# ── Recession Indicator ───────────────────────────────────────────────────
_register(
    Indicator(
        name="NBER Recession Indicator",
        fred_id="USREC",
        category="Regime",
        frequency="monthly",
        unit="binary",
        release_url="https://fred.stlouisfed.org/series/USREC",
        transform="level",
        higher_is="contractionary",
        description="NBER based recession indicator (1 = recession, 0 = expansion)",
    ),
)


# ---------------------------------------------------------------------------
# Plain-English explainers — what it is, why it matters, what to watch for
# ---------------------------------------------------------------------------

WHY_IT_MATTERS: dict[str, str] = {
    # Inflation
    "CPIAUCSL": (
        "**CPI** measures the average change in prices paid by consumers for goods and services. "
        "It's the most widely followed inflation gauge. Rising CPI means your purchasing power is "
        "shrinking. The Fed watches this closely — persistently high CPI leads to rate hikes."
    ),
    "CPILFESL": (
        "**Core CPI** strips out volatile food and energy prices to reveal the underlying inflation "
        "trend. It's what the Fed really focuses on because food/gas prices swing wildly month-to-month. "
        "Core above 3% is uncomfortable; above 4% is alarm territory."
    ),
    "PPIFIS": (
        "**PPI** measures prices at the wholesale/producer level before goods reach consumers. "
        "It's a leading indicator of consumer inflation — if producers pay more, those costs "
        "eventually get passed to you. Rising PPI today often means rising CPI tomorrow."
    ),
    "PCEPI": (
        "**PCE Price Index** is the Fed's officially preferred inflation measure. It's broader than "
        "CPI and accounts for consumers substituting between goods. The Fed's 2% inflation target "
        "is based on this measure, not CPI."
    ),
    "PCEPILFE": (
        "**Core PCE** is the single most important inflation number for markets. It's the Fed's "
        "preferred gauge excluding food and energy. Every Fed decision and dot plot projection "
        "references this. Below 2% = dovish Fed; above 3% = hawkish Fed."
    ),
    # Labor
    "PAYEMS": (
        "**Nonfarm Payrolls** (the \"jobs report\") is the single most market-moving economic release. "
        "It counts how many jobs the economy added or lost last month. Strong job growth = strong "
        "economy. Below 100K/month signals concern; above 250K signals strength."
    ),
    "UNRATE": (
        "**Unemployment Rate** shows the percentage of people actively looking for work who can't "
        "find it. Below 4% is historically \"full employment.\" Rising unemployment is one of the "
        "most reliable recession signals — the Sahm Rule triggers when it rises 0.5% from its low."
    ),
    "ICSA": (
        "**Initial Jobless Claims** counts newly filed unemployment insurance claims each week. "
        "It's the most timely labor market indicator (weekly, only 5 days delayed). Below 250K is "
        "healthy; above 300K signals trouble. Sharp spikes often foreshadow recessions."
    ),
    "JTSJOL": (
        "**JOLTS Job Openings** measures unfilled positions across the economy. High openings mean "
        "employers are desperate to hire (tight labor market). The ratio of openings-to-unemployed "
        "workers is a key metric — above 1.0 means more jobs than jobseekers."
    ),
    "CIVPART": (
        "**Labor Force Participation** shows what percentage of working-age adults are either "
        "employed or actively job-hunting. It fell sharply in COVID and hasn't fully recovered. "
        "Low participation with low unemployment can mask true labor market weakness."
    ),
    "CES0500000003": (
        "**Average Hourly Earnings** tracks wage growth for private-sector workers. It feeds "
        "directly into the inflation picture — strong wage growth can fuel a wage-price spiral. "
        "The Fed wants wages growing around 3-3.5% (consistent with 2% inflation + productivity)."
    ),
    # Output
    "GDPC1": (
        "**Real GDP** is the broadest measure of economic output, adjusted for inflation. "
        "Two consecutive quarters of negative GDP growth is the informal recession definition. "
        "Normal growth is 2-3% annualized; below 1% is stall speed; negative means contraction."
    ),
    "INDPRO": (
        "**Industrial Production** measures output from manufacturing, mining, and utilities. "
        "While the service sector dominates the modern economy, industrial production is still a "
        "key cyclical indicator. Declines often lead broader economic downturns."
    ),
    "TCU": (
        "**Capacity Utilization** shows how much of the economy's production capacity is being used. "
        "Above 80% signals potential inflation pressure (factories running hot). Below 75% signals "
        "significant slack. It's a barometer of how close the economy is to overheating."
    ),
    # Consumer
    "RSAFS": (
        "**Retail Sales** measures consumer spending at stores and online. Consumer spending drives "
        "~70% of U.S. GDP, so this is critical. Month-over-month swings matter — negative readings "
        "signal consumers are pulling back, which can cascade through the economy."
    ),
    "UMCSENT": (
        "**Consumer Sentiment** (University of Michigan survey) gauges how optimistic consumers feel "
        "about the economy and their finances. While sentiment doesn't always predict spending, sharp "
        "drops often precede economic slowdowns. It also captures inflation expectations."
    ),
    "PI": (
        "**Personal Income** tracks total income received by individuals from all sources (wages, "
        "investments, transfers). Growing income supports consumer spending. When income growth "
        "trails inflation, consumers' real purchasing power declines."
    ),
    "PCE": (
        "**Personal Consumption Expenditures** is the most comprehensive consumer spending measure, "
        "covering services (healthcare, rent) and goods. It's broader than retail sales and is the "
        "\"C\" in the GDP equation (C + I + G + NX). Weakness here hits GDP directly."
    ),
    "PSAVERT": (
        "**Personal Saving Rate** shows what fraction of disposable income households are saving. "
        "High savings = cautious consumers (potential drag on growth). Very low savings = consumers "
        "are stretched (vulnerability to shocks). Historical average is around 6-8%."
    ),
    # Business
    "MANEMP": (
        "**ISM Manufacturing PMI** is a survey of purchasing managers at manufacturing firms. "
        "Above 50 = expansion; below 50 = contraction. It's one of the earliest signals of "
        "turning points in the business cycle. Markets react strongly to surprise readings."
    ),
    "DGORDER": (
        "**Durable Goods Orders** tracks new orders for products designed to last 3+ years "
        "(machinery, vehicles, appliances). It's a leading indicator of business investment. "
        "Excluding transportation (volatile aircraft orders) gives a cleaner signal."
    ),
    # Housing
    "HOUST": (
        "**Housing Starts** counts new residential construction projects begun each month. "
        "Housing is one of the most interest-rate-sensitive sectors, so starts often lead the "
        "broader economy. A drop signals builders expect weaker demand ahead."
    ),
    "PERMIT": (
        "**Building Permits** are approved before construction begins, making them a leading "
        "indicator of future housing starts. A gap between permits and starts means builders are "
        "holding back despite demand — often due to cost or financing concerns."
    ),
    "EXHOSLUSM495S": (
        "**Existing Home Sales** measures completed transactions for previously owned homes. "
        "It reflects housing demand and is heavily influenced by mortgage rates and inventory. "
        "This is the largest segment of the housing market by volume."
    ),
    "HSN1F": (
        "**New Home Sales** tracks sales of newly constructed homes. Unlike existing home sales, "
        "it's counted at contract signing (more timely). New home sales drive construction jobs, "
        "appliance purchases, and local economic activity."
    ),
    "CSUSHPINSA": (
        "**Case-Shiller Home Price Index** is the gold standard for tracking U.S. home prices. "
        "Rising home prices create a wealth effect (homeowners feel richer and spend more) but "
        "also worsen affordability. Double-digit YoY gains are unsustainable."
    ),
    # Trade
    "BOPGSTB": (
        "**Trade Balance** is exports minus imports. The U.S. typically runs a deficit (imports > exports). "
        "A widening deficit can drag on GDP growth. Trade policy, dollar strength, and global demand "
        "all influence this. Tariff announcements often move it sharply."
    ),
    "NETEXP": (
        "**Net Exports** is the trade component of GDP (exports minus imports in real terms). "
        "A growing deficit subtracts from GDP growth, while a shrinking deficit adds to it. "
        "Dollar strength and foreign demand are key drivers."
    ),
    # Monetary
    "FEDFUNDS": (
        "**Federal Funds Rate** is the interest rate banks charge each other for overnight loans — "
        "the Fed's primary policy tool. Higher rates slow the economy and fight inflation; lower "
        "rates stimulate growth. Every asset class is priced off this rate."
    ),
    "M2SL": (
        "**M2 Money Supply** includes cash, checking deposits, savings, and money market funds. "
        "Rapid M2 growth can signal future inflation (more money chasing same goods). The sharp "
        "M2 surge in 2020-21 preceded the 2022 inflation spike. Contraction is deflationary."
    ),
    # Fixed Income
    "T10Y2Y": (
        "**10Y-2Y Yield Spread** is the most watched recession indicator on Wall Street. When "
        "negative (inverted), it means markets expect economic weakness ahead. Every U.S. recession "
        "since 1970 was preceded by an inversion. The un-inversion can also signal recession is imminent."
    ),
    "T10Y3M": (
        "**10Y-3M Yield Spread** is another key curve indicator, often considered even more "
        "reliable than 10Y-2Y. The 3-month rate closely tracks Fed policy, so this spread captures "
        "the gap between Fed tightness and long-term growth expectations."
    ),
    "BAMLH0A0HYM2": (
        "**High Yield Credit Spread** measures the extra yield investors demand to hold risky "
        "corporate bonds vs. safe Treasuries. It's a real-time fear gauge for credit markets. "
        "Below 3% = extreme complacency; above 5% = stress; above 8% = crisis territory."
    ),
    "DGS10": (
        "**10-Year Treasury Yield** is the benchmark rate for the global financial system. "
        "It influences mortgage rates, corporate borrowing costs, and stock valuations. Rising "
        "yields compress equity P/E ratios; falling yields support growth stocks."
    ),
    "DGS2": (
        "**2-Year Treasury Yield** is the market's best guess for where the Fed funds rate will "
        "be in two years. It moves sharply on Fed guidance and inflation data. When it spikes "
        "above the 10Y yield, the curve inverts — historically a recession warning."
    ),
    # Market
    "VIXCLS": (
        "**VIX** (the \"Fear Index\") measures expected stock market volatility over the next 30 days, "
        "derived from S&P 500 option prices. Below 15 = calm markets. 15-25 = normal. "
        "Above 25 = elevated fear. Above 35 = panic. It tends to spike sharply during selloffs."
    ),
    "DTWEXBGS": (
        "**Trade-Weighted Dollar Index** measures the dollar's value against a broad basket of "
        "foreign currencies weighted by trade volume. A strong dollar makes imports cheaper (disinflationary) "
        "but hurts U.S. exporters and emerging markets with dollar-denominated debt."
    ),
    # Regime
    "USREC": (
        "**NBER Recession Indicator** is a binary flag: 1 = the U.S. is officially in a recession "
        "as determined by the National Bureau of Economic Research. 0 = expansion. Note: NBER "
        "declares recessions retroactively (often 6-12 months after they start)."
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_indicators_by_category() -> dict[str, list[Indicator]]:
    """Return indicators grouped by category, preserving insertion order."""
    groups: dict[str, list[Indicator]] = {}
    for ind in INDICATORS.values():
        groups.setdefault(ind.category, []).append(ind)
    return groups


def get_release_urls() -> dict[str, list[str]]:
    """Map each unique release URL to the FRED IDs that share it."""
    url_map: dict[str, list[str]] = {}
    for ind in INDICATORS.values():
        url_map.setdefault(ind.release_url, []).append(ind.fred_id)
    return url_map


# Category display order for the dashboard
CATEGORY_ORDER = [
    "Inflation",
    "Labor",
    "Output",
    "Consumer",
    "Business",
    "Housing",
    "Trade",
    "Monetary",
    "Fixed Income",
    "Market",
    "Regime",
]
