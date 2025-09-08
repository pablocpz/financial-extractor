from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, ConfigDict, RootModel, field_validator

# ----------------------------- Enums -----------------------------

class InstrumentStrategy(Enum):
    EQUITY = "Equity"
    CORPORATE_DEBT = "Corporate Debt"


class HedgingStrategy(Enum):
    YES = "Yes"
    NO = "No"
    EXPECTED = "Expected"


class UnderlyingFundStrategy(Enum):
    VC = "V.C."
    GROWTH = "Growth"
    BUYOUT = "Buyout"
    L_BUYOUT = "L. Buyout"
    ASIA = "Asia"
    DIRETTO = "Diretto"
    SENIOR = "Senior"
    UNI_TRANCHE = "Uni-Tranche"
    MEZZANINE = "Mezzanine"
    JUNIOR = "Junior"
    PREFERRED_EQUITY = "Preferred Equity"
    REFIN = "ReFin"
    EQUITY = "Equity"
    PIK = "PIK"
    NAV_LENDING = "NAV Lending"
    CLO = "CLO"
    CORE = "Core"
    CORE_PLUS = "Core+"
    VALUE_ADDED = "Value Added"
    OPPORTUNISTIC = "Opportunistic"
    RE_CREDIT = "RE Credit"
    OTHER = "Other"


class GeographyMacroarea(Enum):
    EUROPE = "Europe"
    UK = "UK"
    N_AMERICA = "N. America"
    LATAM = "LatAm"
    CHINA = "China"
    SEA_OCEANIA = "SEA & Oceania"
    OTHER = "Other"


class MacroSector(Enum):
    EDUCATION = "Education"
    FIN_SERVICES = "Financial Services"
    HEALTH_PHARMA = "Health & Pharma"
    INDUSTRIAL_BUSINESS = "Industrial & Business Services"
    CONSUMER_RETAIL = "Consumer & Retail"
    TRAVEL_HOSPITALITY = "Travel & Hospitality"
    SOFTWARE_TECH = "Software & Technol."
    REAL_ESTATE = "Real estate"
    OTHER = "Other"


class InvestmentType(Enum):
    PRIMARY = "Primary"
    SECONDARY = "Secondary"
    CO_INV = "Co-Inv"


class RealizationStatus(Enum):
    REALIZED = "Realized"
    UNREALIZED = "Unrealized"


class RealEstateSegment(Enum):
    RESIDENTIAL = "Residential"
    OFFICE = "Office"
    RETAIL = "Retail"
    INDUSTRIAL_LOGISTICS = "Industrial & Logistics"
    HOTEL = "Hotel"
    MIXED_USE = "Mixed Use"
    OTHER = "Other"


# ------------------------ Asset-specific row ------------------------

_KMB = {"K": Decimal("1e3"), "M": Decimal("1e6"), "B": Decimal("1e9")}
def _to_decimal(v) -> Optional[Decimal]:
    """Coerce strings like '4,570M', '$174M', '2.7x', '12%', '250 bp' to Decimal base units/ratios."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float, Decimal)):
        return Decimal(str(v))
    s = str(v).strip()
    # Percent or basis points -> decimal fraction
    if s.endswith("%"):
        num = s[:-1].strip().replace(",", "")
        return Decimal(num) / Decimal("100")
    if s.lower().endswith("bp"):
        num = s[:-2].strip().replace(",", "")
        return Decimal(num) / Decimal("10000")
    # Multiples like '2.7x'
    if s.lower().endswith("x"):
        num = s[:-1].strip().replace(",", "")
        return Decimal(num)
    # Remove currency symbols and commas
    s2 = s.replace(",", "").replace("$", "").replace("€", "").replace("£", "")
    # Magnitude suffix K/M/B
    if s2 and s2[-1].upper() in _KMB:
        mult = _KMB[s2[-1].upper()]
        num = s2[:-1]
        return Decimal(num) * mult
    # Plain number
    try:
        return Decimal(s2)
    except InvalidOperation:
        return None

def _parse_iso_or_quarter(v) -> Optional[date]:
    """Accept 'YYYY-MM-DD', 'YYYY-MM', 'DD/MM/YYYY', 'MM/DD/YYYY', 'Q2 2023', 'as of 30 June 2023'."""
    if v is None or v == "":
        return None
    s = str(v).strip()
    # Quarter forms
    import re, calendar
    m = re.match(r"Q([1-4])\s+(\d{4})", s, re.I)
    if m:
        q, y = int(m.group(1)), int(m.group(2))
        month = {1:3, 2:6, 3:9, 4:12}[q]
        last_day = calendar.monthrange(y, month)[1]
        return date(y, month, last_day)
    # "as of ..." -> try to extract a date-ish tail
    s = re.sub(r"(?i)\bas of\b", "", s).strip()

    # Try a battery of formats
    fmts = ["%Y-%m-%d", "%Y-%m", "%d/%m/%Y", "%m/%d/%Y", "%B %d, %Y", "%d %B %Y"]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f).date()
            # If only YYYY-MM given, use last day of month
            if f == "%Y-%m":
                import calendar
                last = calendar.monthrange(dt.year, dt.month)[1]
                return date(dt.year, dt.month, last)
            return dt
        except ValueError:
            continue
    return None


# ------------------------ Asset-specific row (add validators) ------------------------

class AssetSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    # --- your fields (unchanged declarations) ---
    possesso_entry: Optional[Decimal] = Field(default=None, alias="Possesso_Entry")
    ev_entry: Optional[Decimal] = Field(default=None, alias="EV_Entry")
    ebitda_entry: Optional[Decimal] = Field(default=None, alias="EBITDA_Entry")
    margin_entry: Optional[Decimal] = Field(default=None, alias="Margin_Entry")
    net_revenue_entry: Optional[Decimal] = Field(default=None, alias="Net_Revenue_Entry")
    net_debt_entry: Optional[Decimal] = Field(default=None, alias="Net_Debt_Entry")
    fcf_entry: Optional[Decimal] = Field(default=None, alias="FCF_Entry")
    net_result_entry: Optional[Decimal] = Field(default=None, alias="Net_Result_Entry")
    ev_ebitda_entry: Optional[Decimal] = Field(default=None, alias="EVEbitda_Entry")
    ev_revenue_entry: Optional[Decimal] = Field(default=None, alias="EVRevenue_Entry")
    net_debt_ebitda_entry: Optional[Decimal] = Field(default=None, alias="Net_DebtEbitda_Entry")
    economics_reporting_date: Optional[date] = Field(default=None, alias="Economics_Reporting_Date")
    possesso: Optional[Decimal] = Field(default=None, alias="Possesso")
    ev: Optional[Decimal] = Field(default=None, alias="EV")
    ltm_ebitda: Optional[Decimal] = Field(default=None, alias="LTM_EBITDA")
    ltm_margin: Optional[Decimal] = Field(default=None, alias="LTM_Margin")
    ltm_net_revenues: Optional[Decimal] = Field(default=None, alias="LTM_Net_Revenues")
    ltm_net_equity: Optional[Decimal] = Field(default=None, alias="LTM_Net_Equity")
    ltm_net_debt: Optional[Decimal] = Field(default=None, alias="LTM_Net_Debt")
    ltm_fcf: Optional[Decimal] = Field(default=None, alias="LTM_FCF")
    ltm_gross_profit: Optional[Decimal] = Field(default=None, alias="LTM_Gross_Profit")
    ltm_net_result: Optional[Decimal] = Field(default=None, alias="LTM_Net_Result")
    target_company_de_ratio: Optional[Decimal] = Field(default=None, alias="Target_Companys_Debt_Equity_Ratio")
    discount_rate: Optional[Decimal] = Field(default=None, alias="Discount_Rate")
    beta: Optional[Decimal] = Field(default=None, alias="Beta")
    cost_of_equity: Optional[Decimal] = Field(default=None, alias="Cost_of_Equity")
    cost_of_debt: Optional[Decimal] = Field(default=None, alias="Cost_of_Debt")
    ev_ebitda: Optional[Decimal] = Field(default=None, alias="EVEBITDA")
    ev_revenue: Optional[Decimal] = Field(default=None, alias="EVRevenue")
    net_debt_ebitda: Optional[Decimal] = Field(default=None, alias="Net_DebtEbitda")
    maturity_date: Optional[date] = Field(default=None, alias="Maturity_Date")
    price: Optional[Decimal] = Field(default=None, alias="Price")
    coupon: Optional[Decimal] = Field(default=None, alias="Coupon")
    spread: Optional[Decimal] = Field(default=None, alias="Spread")
    watchlist_position: Optional[str] = Field(default=None, alias="Watchlist_position")
    ltv: Optional[Decimal] = Field(default=None, alias="Ltv")
    leverage_entry: Optional[Decimal] = Field(default=None, alias="Leverage_Entry")
    leverage: Optional[Decimal] = Field(default=None, alias="Leverage")
    duration: Optional[Decimal] = Field(default=None, alias="Duration")
    credit_sensitivity: Optional[Decimal] = Field(default=None, alias="Credit_Sensitivity")
    risk_free_rate_applied: Optional[Decimal] = Field(default=None, alias="Risk_Free_Rate_applied_to_Valuation")
    credit_rating: Optional[str] = Field(default=None, alias="Credit_Rating")
    credit_rating_source: Optional[str] = Field(default=None, alias="Credit_Rating_Source")
    credit_spread_pct: Optional[Decimal] = Field(default=None, alias="Credit_Spread")
    country_premium_pct: Optional[Decimal] = Field(default=None, alias="Country_Premium")
    liquidity_premium_pct: Optional[Decimal] = Field(default=None, alias="Liquidity_Premium")
    other_premia_pct: Optional[Decimal] = Field(default=None, alias="Other_premia")
    total_discount_rate_applied_pct: Optional[Decimal] = Field(default=None, alias="Total_Discount_Rate_applied_to_Valuation")
    area: Optional[str] = Field(default=None, alias="Area")
    real_estate_segment: Optional['RealEstateSegment'] = Field(default=None, alias="Real_Estate_Segment")

    # --- Validators ---
    _coerce_decimals = field_validator(
        "possesso_entry","ev_entry","ebitda_entry","margin_entry","net_revenue_entry",
        "net_debt_entry","fcf_entry","net_result_entry","ev_ebitda_entry","ev_revenue_entry",
        "net_debt_ebitda_entry","possesso","ev","ltm_ebitda","ltm_margin","ltm_net_revenues",
        "ltm_net_equity","ltm_net_debt","ltm_fcf","ltm_gross_profit","ltm_net_result",
        "target_company_de_ratio","discount_rate","beta","cost_of_equity","cost_of_debt",
        "ev_ebitda","ev_revenue","net_debt_ebitda","price","coupon","spread","ltv",
        "leverage_entry","leverage","duration","credit_sensitivity","risk_free_rate_applied",
        "credit_spread_pct","country_premium_pct","liquidity_premium_pct","other_premia_pct",
        "total_discount_rate_applied_pct",
        mode="before"
    )(lambda v: _to_decimal(v))

    _coerce_dates = field_validator("economics_reporting_date","maturity_date", mode="before")(
        lambda v: _parse_iso_or_quarter(v)
    )


# ------------------------- Top-level stats (add validators) -------------------------
class FundExposure(BaseModel):
    model_config = ConfigDict(populate_by_name=True, use_enum_values=True)

    nav_date: date = Field(alias="NAV_Date")
    valuation_date: Optional[date] = Field(default=None, alias="Valuation_Date")
    fondo_target_asset: str = Field(alias="FONDO_TARGET_ASSET")
    oicr_fondo_target: str = Field(alias="OICR_FONDO_TARGET")
    oicr: str = Field(alias="OICR")
    isin_oicr: Optional[str] = Field(default=None, alias="ISIN_OICR")
    nome_fondo_target: str = Field(alias="Nome_Fondo_Target")
    isin_fondo_target: Optional[str] = Field(default=None, alias="ISIN_Fondo_Target")
    tipologia_strumento: Optional['InstrumentStrategy'] = Field(default=None, alias="Tipologia_Strumento")
    currency_fondo_target: Optional[str] = Field(default=None, alias="Currency_Fondo_Target")
    country_fondo_target: Optional[str] = Field(default=None, alias="Country_Fondo_Target")
    hedging_strategy_fondo_target: Optional['HedgingStrategy'] = Field(default=None, alias="Hedging_Strategy_Fondo_Target")
    strategia_fondo_target: Optional['UnderlyingFundStrategy'] = Field(default=None, alias="Strategia_Fondo_Target")
    nome_asset: Optional[str] = Field(default=None, alias="Nome_Asset")
    nome_asset_sintetico: Optional[str] = Field(default=None, alias="Nome_Asset_Sintetico")
    area_geo_asset: Optional['GeographyMacroarea'] = Field(default=None, alias="Area_Geo_Asset")
    paese_asset: Optional[str] = Field(default=None, alias="Paese_Asset")
    indirizzo_asset: Optional[str] = Field(default=None, alias="Indirizzo_Asset")
    currency_asset: Optional[str] = Field(default=None, alias="Currency_Asset")
    macrosettore_attivita_asset: Optional['MacroSector'] = Field(default=None, alias="Macrosettore_Attivita_Asset")
    settore_attivita_asset: Optional[str] = Field(default=None, alias="Settore_Attivita_Asset")
    tipologia_investimento: Optional['InvestmentType'] = Field(default=None, alias="Tipologia_Investimento")
    investment_date: Optional[date] = Field(default=None, alias="Investment_Date")
    exit_date: Optional[date] = Field(default=None, alias="Exit_Date")
    valuation_methodology: Optional[str] = Field(default=None, alias="Valuation_Methodology")
    realized_unrealized: Optional['RealizationStatus'] = Field(default=None, alias="Realized_Unrealized")
    commitment_fondo_target: Optional[Decimal] = Field(default=None, alias="Commitment_Fondo_Target")
    capitale_investito_lordo_loc_curr: Optional[Decimal] = Field(default=None, alias="Capitale_Investito_Lordo_Loc_Curr")
    distribuzioni_loc_curr: Optional[Decimal] = Field(default=None, alias="Distribuzioni_Loc_Curr")
    fmv_loc_curr: Optional[Decimal] = Field(default=None, alias="FMV_Loc_Curr")
    tvpi: Optional[Decimal] = Field(default=None, alias="TVPI")
    irr: Optional[Decimal] = Field(default=None, alias="IRR")
    cap_inv_fondo_target_pct: Optional[Decimal] = Field(default=None, alias="Cap_Inv_Fondo_Target")
    fmv_fondo_target_pct: Optional[Decimal] = Field(default=None, alias="FMV_Fondo_Target")
    cap_inv_ripartito_fof_eur: Optional[Decimal] = Field(default=None, alias="Cap_Inv_Ripartito_FOF")
    nav_ripartito_fof_eur: Optional[Decimal] = Field(default=None, alias="NAV_Ripartito_FOF")
    capitale_investito_fof_pct: Optional[Decimal] = Field(default=None, alias="Capitale_Investito_Fof")
    fmv_fof_pct: Optional[Decimal] = Field(default=None, alias="FMV_Fof")
    asset_snapshots: List[AssetSnapshot] = Field(default_factory=list, description="Per-asset snapshots.")

    # --- Validators ---
    _coerce_amounts = field_validator(
        "commitment_fondo_target","capitale_investito_lordo_loc_curr","distribuzioni_loc_curr",
        "fmv_loc_curr","tvpi","irr","cap_inv_fondo_target_pct","fmv_fondo_target_pct",
        "cap_inv_ripartito_fof_eur","nav_ripartito_fof_eur","capitale_investito_fof_pct","fmv_fof_pct",
        mode="before"
    )(lambda v: _to_decimal(v))

    _coerce_dates = field_validator("nav_date","valuation_date","investment_date","exit_date", mode="before")(
        lambda v: _parse_iso_or_quarter(v)
    )


# ---------------------- List wrapper to enforce array output -----------------------

from typing import List

class FundExposureBatch(BaseModel):
    items: List[FundExposure] = Field(default_factory=list, description="List of FundExposure objects")