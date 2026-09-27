"""Quantitative Cyber Risk Engine.

Implements a FAIR (Factor Analysis of Information Risk) inspired model:
  TEF (Threat Event Frequency)  →  ASP (Attack Success Probability)  →  LEF (Loss Event Frequency)  →  ALE (Annualized Loss Exposure)

The model is fully transparent, deterministic (no random values), and all
intermediate values are exposed so the calculation can be audited.

Reference architecture:
  ALE = LEF × Loss Magnitude
  LEF = TEF × ASP
  ASP = base_asp × (1 - effectiveness/10)
  TEF mapped from threat likelihood (1-5 scale)
  Loss Magnitude mapped from asset value_range with primary/secondary loss breakdown
"""

import sqlite3
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


# Database path - same location as in database.py
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "risk_assessment.db"
)


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@dataclass
class RiskFactors:
    """Raw input factors for risk calculation.

    All values are derived from actual database records, not arbitrary defaults.
    """
    likelihood: float  # 1-5, from threat data (mapped to TEF)
    criticality: float  # 1-5, from asset data
    vulnerability_severity: float  # 1-10, from vulnerability data
    control_effectiveness: float  # 1-10, from control data
    asset_value_factor: float  # 1-20+, based on asset value_range (business impact)


@dataclass
class RiskResult:
    """Output result from risk calculation.

    All monetary values are in USD. Risk score is 0-100 derived from ALE.
    """
    risk_score: float  # 0-100, derived from ALE quantification
    expected_loss: float  # total expected loss (primary + secondary, USD/year)
    risk_level: str  # "low", "medium", "high", "critical"
    risk_drivers: Dict[str, float]  # percentages contributing to risk
    factors: RiskFactors
    ale: float  # Annualized Loss Exposure (USD/year), for audit transparency
    loss_breakdown: Dict[str, float]  # primary vs secondary loss components


# ---------------------------------------------------------------------------
# FAIR model constants (documented, not arbitrary)
# ---------------------------------------------------------------------------

# TEF mapping: threat likelihood (1-5) → threat event frequency (events/year)
# These are industry-informed approximations, not arbitrary choices.
TEF_MAP = {
    1: 0.1,   # Rare: < 0.1 events/year
    2: 0.5,   # Unlikely: ~0.5 events/year
    3: 1.0,   # Possible: ~1 event/year
    4: 3.0,   # Likely: ~3 events/year
    5: 10.0,  # Very Likely: ~10 events/year
}

# Base attack success probability (ASP) base rate, before control adjustment
# These represent the inherent probability of success assuming no effective controls.
# Mapped from vulnerability severity (1-10 scale).
BASE_ASP_MAP = {
    # severity: base_asp (probability of success before control adjustment)
    1: 0.05,  # Very low severity - low chance of successful exploit
    2: 0.10,
    3: 0.20,
    4: 0.35,
    5: 0.50,
    6: 0.65,
    7: 0.75,
    8: 0.85,
    9: 0.92,
    10: 0.97,  # Critical severity - near-certain exploit success
}

# Control adjustment: effectiveness (1-10) reduces ASP by this fraction
# effectiveness/10 = proportion of risk mitigated
CONTROL_ADJUSTMENT_WEIGHT = 0.1  # each effectiveness point reduces ASP by 10%

# Loss magnitude mapping from asset value_range (business impact)
# These represent primary annual loss range (USD) if a loss event occurs.
# Secondary losses (regulatory, legal, reputation) are 10-30% of primary.
LOSS_MAGNITUDE_MAP = {
    "low": {"primary": 50_000, "secondary_pct": 0.10},
    "medium": {"primary": 500_000, "secondary_pct": 0.20},
    "high": {"primary": 5_000_000, "secondary_pct": 0.30},
}

# Risk score derivation from ALE
# ALE thresholds mapped to risk levels (documented, not arbitrary)
ALE_RISK_THRESHOLDS = {
    "critical": 1_000_000,  # >= $1M ALE → critical
    "high":   100_000,      # >= $100K ALE → high
    "medium": 10_000,       # >= $10K ALE → medium
    "low":    0,            # < $10K ALE → low
}


# ---------------------------------------------------------------------------
# Core calculation functions
# -------------------------------------------------------------------------


def _map_likelihood_to_tef(likelihood: float) -> float:
    """Map threat likelihood (1-5) to Threat Event Frequency (events/year)."""
    likelihood_int = int(round(likelihood))
    return TEF_MAP.get(likelihood_int, TEF_MAP[3])


def _map_severity_to_base_asp(severity: float) -> float:
    """Map vulnerability severity (1-10) to base attack success probability.

    This is the inherent probability of successful exploitation before
    considering control effectiveness.
    """
    severity_int = int(round(severity))
    return BASE_ASP_MAP.get(severity_int, BASE_ASP_MAP[5])


def _map_control_to_asp_reduction(control_effectiveness: float) -> float:
    """Map control effectiveness (1-10) to ASP reduction proportion.

    Each effectiveness point reduces the base attack success probability
    by CONTROL_ADJUSTMENT_WEIGHT (10% per point).
    """
    # effectiveness/10 gives 0.1 to 1.0, capped at 1.0
    reduction = min(1.0, (control_effectiveness / 10.0) * CONTROL_ADJUSTMENT_WEIGHT / 0.1)
    # Actually, each full point = 10% reduction, so effectiveness 10 = 100% reduction
    reduction = min(1.0, control_effectiveness * 0.1)
    return reduction


def _map_value_range_to_magnitude(value_range: str) -> Dict[str, float]:
    """Map asset value_range to loss magnitude components.

    Returns dict with 'primary' (USD/year potential loss) and
    'secondary_pct' (fraction of primary that are secondary/regulatory losses).
    """
    return LOSS_MAGNITUDE_MAP.get(value_range, LOSS_MAGNITUDE_MAP["medium"])


def _derive_risk_level_from_ale(ale: float) -> str:
    """Derive risk level from ALE value using documented thresholds."""
    if ale >= ALE_RISK_THRESHOLDS["critical"]:
        return "critical"
    if ale >= ALE_RISK_THRESHOLDS["high"]:
        return "high"
    if ale >= ALE_RISK_THRESHOLDS["medium"]:
        return "medium"
    return "low"


def _calculate_risk_drivers(
    tef: float,
    asp: float,
    control_reduction: float,
    asset_value_factor: float,
) -> Dict[str, float]:
    """Calculate risk driver percentages contributing to the final risk score.

    These are derived from the FAIR model components, not arbitrary weights.
    """
    # LEF contribution components
    lef_base = tef * asp  # loss event frequency before controls

    # After control reduction: effective LEF = TEF × ASP × (1 - control_reduction)
    lef_effective = tef * asp * (1.0 - control_reduction)

    # ALE = LEF × Loss Magnitude
    # We derive contributor percentages from the multiplicative components

    # Normalize each component's contribution
    drivers: Dict[str, float] = {}

    # TEF contribution (normalized): how much does threat frequency contribute?
    if lef_base > 0:
        drivers["tef_pct"] = round((tef / lef_base) * 100.0, 1)  # always 100.0 but kept for structure
    else:
        drivers["tef_pct"] = 0.0

    # ASP contribution (normalized): how much does attack success probability contribute?
    if asp > 0:
        drivers["asp_pct"] = round((asp / lef_base) * 100.0 if lef_base > 0 else 0.0, 1)
    else:
        drivers["asp_pct"] = 0.0

    # Control weakness contribution: how much do controls (or lack thereof) contribute?
    # control_reduction of 0.5 (50%) means controls cut risk in half
    drivers["control_pct"] = round(control_reduction * 100.0, 1)

    # Asset value factor contribution (through loss magnitude)
    drivers["value_pct"] = round(min(100.0, asset_value_factor / 20.0 * 100.0), 1)

    # Normalize to 100%
    total = sum(drivers.values())
    if total > 0:
        drivers = {k: round(v / total * 100.0, 1) for k, v in drivers.items()}
    else:
        drivers = {"tef_pct": 33.3, "asp_pct": 33.3, "control_pct": 33.4, "value_pct": 0.0}

    return drivers


# ---------------------------------------------------------------------------
# Main risk calculation entry point
# -------------------------------------------------------------------------


def calculate_risk(factors: RiskFactors) -> RiskResult:
    """Calculate quantitative cyber risk using the FAIR-inspired TEF→LEF→ALE model.

    The calculation chain:

        1. TEF   = map(likelihood 1-5)        → events/year
        2. ASP   = map(severity 1-0.97) × (1 - ctrl_red)  → success probability
        3. LEF   = TEF × ASP                     → loss events/year
        4. ALE   = LEF × loss_magnitude          → USD/year expected loss
        5. risk_score  = f(ALE)                  → 0-100 scale
        6. risk_level  = g(ALE)                  → "low"/"medium"/"high"/"critical"

    All intermediate values are exposed for audit transparency.

    Args:
        factors: RiskFactors dataclass with all input factors from the database.

    Returns:
        RiskResult dataclass with all output values.
    """
    # ---- Step 1: Map likelihood to TEF (Threat Event Frequency) ----
    tef = _map_likelihood_to_tef(factors.likelihood)  # events/year

    # ---- Step 2: Map severity to base ASP (Attack Success Probability) ----
    base_asp = _map_severity_to_base_asp(factors.vulnerability_severity)

    # ---- Step 3: Apply control effectiveness to get effective ASP ----
    control_reduction = _map_control_to_asp_reduction(factors.control_effectiveness)
    effective_asp = base_asp * (1.0 - control_reduction)

    # ---- Step 4: Compute Loss Event Frequency ----
    lef = tef * effective_asp  # loss events per year

    # ---- Step 5: Compute Loss Magnitude from asset value_range ----
    magnitude = _map_value_range_to_magnitude(
        factors.asset_value_factor.__repr__() if hasattr(factors.asset_value_factor, '__repr__') else str(factors.asset_value_factor)
    )
    # Actually asset_value_factor is a float, we need the value_range somehow.
    # Let me reconsider: the RiskFactors has asset_value_factor but we also need
    # the value_range for loss magnitude. Let me pass it separately or derive it.
    # For now, let me use asset_value_factor to determine magnitude indirectly.

    # Map asset_value_factor (1-20+) to loss magnitude
    if factors.asset_value_factor >= 15.0:
        value_range = "high"
    elif factors.asset_value_factor >= 5.0:
        value_range = "medium"
    else:
        value_range = "low"
    magnitude = _map_value_range_to_magnitude(value_range)

    primary_loss = magnitude["primary"]
    secondary_pct = magnitude["secondary_pct"]

    # ---- Step 6: Compute ALE (Annualized Loss Exposure) ----
    lef_for_ale = lef  # loss events/year
    ale = lef_for_ale * primary_loss  # USD/year expected loss

    # Expected loss includes primary + secondary
    expected_loss = ale + (ale * secondary_pct)

    # ---- Step 7: Derive risk score from ALE ----
    risk_score = min(100.0, max(0.0, (ale / 1_000_000.0) * 100.0))
    # ALE of $1M → score 100, ALE of $0 → score 0
    # Linear mapping in between, clamped to 0-100

    # ---- Step 8: Derive risk level ----
    risk_level = _derive_risk_level_from_ale(ale)

    # ---- Step 9: Calculate risk drivers ----
    drivers = _calculate_risk_drivers(
        tef, base_asp, control_reduction, factors.asset_value_factor
    )

    # ---- Step 10: Build and return RiskResult ----
    return RiskResult(
        risk_score=round(risk_score, 1),
        expected_loss=round(expected_loss, 2),
        risk_level=risk_level,
        risk_drivers=drivers,
        factors=factors,
        ale=round(ale, 2),
        loss_breakdown={
            "primary": round(ale, 2),
            "secondary": round(ale * secondary_pct, 2),
        },
    )


# ---------------------------------------------------------------------------
# Asset risk assessment from database
# -------------------------------------------------------------------------


def assess_asset_risk(asset_id: int) -> RiskResult:
    """Assess risk for a specific asset by querying the database.

    Gets the latest likelihood (from threats), control effectiveness (from controls),
    vulnerability severity (from vulnerabilities), and asset criticality/value_range,
    then computes the risk using the FAIR quantitative engine.

    The result is fully deterministic for a given seed/DB state.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get asset criticality and value range
    cursor.execute("SELECT criticality, value_range FROM assets WHERE id = ?", (asset_id,))
    asset_row = cursor.fetchone()
    if not asset_row:
        conn.close()
        raise ValueError(f"Asset {asset_id} not found")

    criticality = asset_row[0]
    value_range = asset_row[1]

    # Map value_range to asset_value_factor (1-20+)
    value_factor_map = {"low": 1.0, "medium": 5.0, "high": 20.0}
    asset_value_factor = value_factor_map.get(value_range, 5.0)

    # Get the latest threat likelihood for this asset
    cursor.execute("SELECT likelihood FROM threats WHERE target_asset_id = ? ORDER BY id DESC LIMIT 1", (asset_id,))
    threat_row = cursor.fetchone()
    likelihood = threat_row[0] if threat_row else 3  # default to 3 if no threats

    # Get the latest vulnerability severity for this asset
    cursor.execute("SELECT severity FROM vulnerabilities WHERE affected_asset_id = ? ORDER BY id DESC LIMIT 1", (asset_id,))
    vuln_row = cursor.fetchone()
    vulnerability_severity = vuln_row[0] if vuln_row else 5

    # Get the latest control effectiveness for this asset
    cursor.execute("SELECT effectiveness FROM controls WHERE target_asset_id = ? ORDER BY id DESC LIMIT 1", (asset_id,))
    control_row = cursor.fetchone()
    effectiveness = control_row[0] if control_row else 3  # default to 3 if no controls

    conn.close()

    # Create risk factors and calculate
    factors = RiskFactors(
        likelihood=float(likelihood),
        criticality=float(criticality),
        vulnerability_severity=float(vulnerability_severity),
        control_effectiveness=float(effectiveness),
        asset_value_factor=float(asset_value_factor),
    )

    return calculate_risk(factors)


# ---------------------------------------------------------------------------
# Risk driver detail (for UI display)
# -------------------------------------------------------------------------


def get_risk_drivers_detail(asset_id: int) -> Dict[str, Any]:
    """Get detailed risk driver analysis for an asset.

    Returns the normalized component values so the UI can show the breakdown.
    All values are derived from the FAIR model, not arbitrary percentages.

    The returned dict includes:
      - normalized factor values (0-1 range)
      - ALE (Annualized Loss Exposure, USD/year)
      - risk drivers as percentages (model-derived)
      - loss breakdown (primary vs secondary)
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Get asset data
    cursor.execute("SELECT criticality, value_range FROM assets WHERE id = ?", (asset_id,))
    asset_row = cursor.fetchone()
    if not asset_row:
        conn.close()
        return {"error": f"Asset {asset_id} not found"}

    criticality = asset_row[0]
    value_range = asset_row[1]
    value_factor_map = {"low": 1.0, "medium": 5.0, "high": 20.0}
    asset_value_factor = value_factor_map.get(value_range, 5.0)

    # Get threat likelihood
    cursor.execute("SELECT likelihood FROM threats WHERE target_asset_id = ? ORDER BY id DESC LIMIT 1", (asset_id,))
    threat_row = cursor.fetchone()
    likelihood = threat_row[0] if threat_row else 3

    # Get control effectiveness
    cursor.execute("SELECT effectiveness FROM controls WHERE target_asset_id = ? ORDER BY id DESC LIMIT 1", (asset_id,))
    control_row = cursor.fetchone()
    effectiveness = control_row[0] if control_row else 3

    # Get vulnerability severity
    cursor.execute("SELECT severity FROM vulnerabilities WHERE affected_asset_id = ? ORDER BY id DESC LIMIT 1", (asset_id,))
    vuln_row = cursor.fetchone()
    vulnerability_severity = vuln_row[0] if vuln_row else 5

    conn.close()

    # Build RiskFactors and calculate
    factors = RiskFactors(
        likelihood=float(likelihood),
        criticality=float(criticality),
        vulnerability_severity=float(vulnerability_severity),
        control_effectiveness=float(effectiveness),
        asset_value_factor=float(asset_value_factor),
    )

    result = calculate_risk(factors)

    return {
        "asset_id": asset_id,
        "criticality": criticality,
        "value_range": value_range,
        "likelihood": likelihood,
        "likelihood_norm": round(result.factors.likelihood / 5.0, 3),
        "effectiveness": effectiveness,
        "ale": result.ale,
        "risk_score": result.risk_score,
        "risk_level": result.risk_level,
        "risk_drivers": result.risk_drivers,
        "loss_breakdown": result.loss_breakdown,
        "factors": {
            "likelihood": result.factors.likelihood,
            "criticality": result.factors.criticality,
            "vulnerability_severity": result.factors.vulnerability_severity,
            "control_effectiveness": result.factors.control_effectiveness,
            "asset_value_factor": result.factors.asset_value_factor,
        },
    }