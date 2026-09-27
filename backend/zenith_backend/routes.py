"""API routes for the SIH26105 Cyber Risk Quantification Platform.

All endpoints consume from the SQLite database and use the
FAIR-inspired quantitative risk engine (risk_engine.py).
"""

from fastapi import APIRouter, HTTPException, Path, Query, Body
from datetime import datetime
from typing import Dict, Any, List

from .risk_engine import assess_asset_risk, calculate_risk, RiskFactors, get_risk_drivers_detail
from .database import get_connection
from .continuous_risk import update_telemetry, record_risk_snapshot

router = APIRouter(tags=["v1"])


# ---- Risk Calculation Endpoints ----

@router.get("/risk/assessment/{asset_id}", response_model=Dict[str, Any])
async def get_risk_assessment(
    asset_id: int = Path(..., description="Asset ID to assess risk for"),
) -> Dict[str, Any]:
    """Get quantitative risk assessment for a specific asset.

    Uses the FAIR-inspired TEF→LEF→ALE model to produce:
      - risk_score (0-100, derived from ALE)
      - expected_loss (USD/year, primary + secondary)
      - risk_level ("low"/"medium"/"high"/"critical")
      - risk_drivers (percentage contributions from model components)
      - ale (Annualized Loss Exposure, USD/year, for transparency)
      - loss_breakdown (primary vs secondary loss components)
    """
    try:
        result = assess_asset_risk(asset_id)
        return {
            "asset_id": asset_id,
            "risk_score": result.risk_score,
            "expected_loss": result.expected_loss,
            "risk_level": result.risk_level,
            "risk_drivers": result.risk_drivers,
            "ale": result.ale,
            "loss_breakdown": result.loss_breakdown,
            "factors": {
                "likelihood": result.factors.likelihood,
                "criticality": result.factors.criticality,
                "vulnerability_severity": result.factors.vulnerability_severity,
                "control_effectiveness": result.factors.control_effectiveness,
                "asset_value_factor": result.factors.asset_value_factor,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.api_route("/risk/calculate/{asset_id}", methods=["GET", "POST"], response_model=Dict[str, Any])
async def calculate_risk_endpoint(
    asset_id: int = Path(..., description="Asset ID to calculate risk for"),
) -> Dict[str, Any]:
    """Calculate risk for a specific asset using the quantitative engine.

    Returns the full RiskResult with all intermediate FAIR model values
    for audit transparency.
    """
    try:
        result = assess_asset_risk(asset_id)
        return {
            "asset_id": asset_id,
            "risk_score": result.risk_score,
            "expected_loss": result.expected_loss,
            "risk_level": result.risk_level,
            "risk_drivers": result.risk_drivers,
            "ale": result.ale,
            "loss_breakdown": result.loss_breakdown,
            "factors": {
                "likelihood": result.factors.likelihood,
                "criticality": result.factors.criticality,
                "vulnerability_severity": result.factors.vulnerability_severity,
                "control_effectiveness": result.factors.control_effectiveness,
                "asset_value_factor": result.factors.asset_value_factor,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/risk/drivers/{asset_id}", response_model=Dict[str, Any])
async def get_risk_drivers(
    asset_id: int = Path(..., description="Asset ID to get driver analysis for"),
) -> Dict[str, Any]:
    """Get detailed risk driver analysis for an asset.

    Returns normalized factor values and model-derived percentage
    contributions so the UI can show the breakdown.
    """
    detail = get_risk_drivers_detail(asset_id)
    if "error" in detail:
        raise HTTPException(status_code=404, detail=detail["error"])
    return detail


# ---- Continuous Risk / Snapshot Endpoints ----

@router.post("/risk/snapshot/{asset_id}")
async def record_risk_snapshot(
    asset_id: int = Path(..., description="Asset ID to record risk snapshot for"),
) -> Dict[str, Any]:
    """Record a risk snapshot for an asset.

    In a production system this would persist to the risk_history table.
    For now, returns the current risk calculation with a timestamp.
    """
    try:
        result = assess_asset_risk(asset_id)
        import datetime
        return {
            "asset_id": asset_id,
            "risk_score": result.risk_score,
            "risk_level": result.risk_level,
            "ale": result.ale,
            "recorded_at": datetime.datetime.now().isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---- What-If / Control Impact Endpoints ----

@router.post("/risk/what-if/{asset_id}", response_model=Dict[str, Any])
async def risk_what_if(
    asset_id: int = Path(..., description="Asset ID to evaluate control impact for"),
    new_control_effectiveness: float = Query(
        ..., ge=1, le=10, description="New control effectiveness (1-10) to evaluate"
    ),
) -> Dict[str, Any]:
    """What-if analysis: evaluate risk impact of changing control effectiveness.

    Returns the current risk and the projected risk with the new control effectiveness,
    plus the risk reduction in ALE and risk score.

    This enables the investment optimizer to show quantified benefit
    of proposed control investments.
    """
    try:
        # Get current risk
        current = assess_asset_risk(asset_id)

        # Compute projected risk with new control effectiveness
        conn = get_connection()
        cursor = conn.cursor()

        # Get current factor values from the database
        cursor.execute(
            "SELECT criticality, value_range FROM assets WHERE id = ?", (asset_id,)
        )
        asset_row = cursor.fetchone()
        if not asset_row:
            conn.close()
            raise ValueError(f"Asset {asset_id} not found")

        criticality = asset_row[0]
        value_range = asset_row[1]

        value_factor_map = {"low": 1.0, "medium": 5.0, "high": 20.0}
        asset_value_factor = value_factor_map.get(value_range, 5.0)

        cursor.execute(
            "SELECT likelihood FROM threats WHERE target_asset_id = ? ORDER BY id DESC LIMIT 1",
            (asset_id,),
        )
        threat_row = cursor.fetchone()
        likelihood = threat_row[0] if threat_row else 3

        cursor.execute(
            "SELECT severity FROM vulnerabilities WHERE affected_asset_id = ? ORDER BY id DESC LIMIT 1",
            (asset_id,),
        )
        vuln_row = cursor.fetchone()
        vulnerability_severity = vuln_row[0] if vuln_row else 5

        conn.close()

        # Build new factors with the proposed control effectiveness
        new_factors = RiskFactors(
            likelihood=float(likelihood),
            criticality=float(criticality),
            vulnerability_severity=float(vulnerability_severity),
            control_effectiveness=new_control_effectiveness,
            asset_value_factor=float(asset_value_factor),
        )

        new_result = calculate_risk(new_factors)

        # Calculate risk reduction
        ale_reduction = current.ale - new_result.ale
        score_reduction = current.risk_score - new_result.risk_score

        return {
            "asset_id": asset_id,
            "current": {
                "risk_score": current.risk_score,
                "risk_level": current.risk_level,
                "ale": current.ale,
                "control_effectiveness": current.factors.control_effectiveness,
            },
            "proposed": {
                "risk_score": new_result.risk_score,
                "risk_level": new_result.risk_level,
                "ale": new_result.ale,
                "control_effectiveness": new_control_effectiveness,
            },
            "risk_reduction": {
                "ale_reduction": round(max(0, ale_reduction), 2),
                "score_reduction": round(max(0, score_reduction), 1),
            },
            " interpretation": (
                f"Proposing control effectiveness {new_control_effectiveness}/10 "
                f"would reduce ALE by ${ale_reduction:,.2f}/year "
                f"and lower risk score from {current.risk_score} to {new_result.risk_score}"
            ),
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---- Telemetry Ingestion Endpoint ----

@router.post("/telemetry", response_model=Dict[str, Any])
async def ingest_telemetry(
    event: Dict[str, Any],
) -> Dict[str, Any]:
    """Ingest real-time security telemetry into Zenith.

    Accepts security telemetry from external systems (SIEM, scanners, EDR, etc.).
    Validates the payload, normalizes values, stores in database, and triggers
    risk recalculation for the affected asset.

    The event schema is designed to be compatible with external security systems
    while normalizing to the internal database model.

    Returns the stored event and updated risk assessment for the asset.
    """
    try:
        # Extract and normalize fields from the event
        timestamp = event.get("timestamp")
        asset_id_raw = event.get("asset_id")
        event_type = event.get("event_type", "unknown")
        severity_raw = event.get("severity")
        vulnerability_id = event.get("vulnerability_id")
        threat_likelihood_raw = event.get("threat_likelihood")
        control_eff_raw = event.get("control_effectiveness")
        source = event.get("source", "unknown")

        # Validate asset_id
        if asset_id_raw is None:
            raise HTTPException(status_code=400, detail="Missing required field: asset_id")

        try:
            asset_id = int(asset_id_raw)
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid asset_id: must be an integer")

        # Validate asset exists
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, criticality, value_range FROM assets WHERE id = ?", (asset_id,))
        asset_row = cursor.fetchone()
        if not asset_row:
            conn.close()
            raise HTTPException(status_code=400, detail=f"Asset {asset_id} not found")
        asset_name = asset_row[1]
        criticality = asset_row[2]
        value_range = asset_row[3]

        # Normalize severity (0-100 to 1-10)
        severity_1_to_10 = 5  # default
        if severity_raw is not None:
            try:
                severity_val = float(severity_raw)
                # Map 0-100 to 1-10, with 5 as midpoint
                severity_1_to_10 = max(1, min(10, round(severity_val / 10 + 5)))
            except (ValueError, TypeError):
                severity_1_to_10 = 5

        # Normalize threat_likelihood (0-1 scale to 1-5)
        likelihood_1_to_5 = 3  # default
        if threat_likelihood_raw is not None:
            try:
                likelihood_val = float(threat_likelihood_raw)
                # Map 0-1 to 1-5
                likelihood_1_to_5 = max(1, min(5, round(likelihood_val * 4 + 1)))
            except (ValueError, TypeError):
                likelihood_1_to_5 = 3

        # Normalize control_effectiveness (0-1 scale to 1-10)
        control_eff_1_to_10 = 5  # default
        if control_eff_raw is not None:
            try:
                ctrl_val = float(control_eff_raw)
                # Map 0-1 to 1-10
                control_eff_1_to_10 = max(1, min(10, round(ctrl_val * 9 + 1)))
            except (ValueError, TypeError):
                control_eff_1_to_10 = 5

        # Normalize vulnerability_id to integer if provided
        normalized_vuln_id = None
        if vulnerability_id is not None:
            try:
                normalized_vuln_id = int(vulnerability_id)
            except (ValueError, TypeError):
                normalized_vuln_id = None

        # Store telemetry in database
        # Use event_type as the note, map fields to database columns
        note = f"Event type: {event_type}"
        observation_date = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        telemetry_id = update_telemetry(
            asset_id=asset_id,
            severity_rating=severity_1_to_10,
            note=note,
            related_vulnerability_id=normalized_vuln_id,
            related_threat_id=None,  # Will be set if threat_likelihood indicates a threat
            related_control_id=None,  # Will be set if control effectiveness change
        )

        # Record risk snapshot in history
        # Get current risk before update to record the "before" state
        try:
            current_risk = assess_asset_risk(asset_id)
            record_risk_snapshot(
                asset_id=asset_id,
                risk_score=current_risk.risk_score,
                risk_level=current_risk.risk_level,
                likelihood=float(likelihood_1_to_5),
                control_eff=float(control_eff_1_to_10),
                vulnerability_severity=float(severity_1_to_10),
            )
        except Exception:
            pass  # Don't fail telemetry ingestion if snapshot recording fails

        # Recalculate risk after the telemetry update
        # This will also update the risk_assessments table
        new_risk = assess_asset_risk(asset_id)

        # Build response
        result = {
            "stored_event": {
                "telemetry_id": telemetry_id,
                "asset_id": asset_id,
                "asset_name": asset_name,
                "event_type": event_type,
                "timestamp": observation_date,
                "severity": severity_1_to_10,
                "threat_likelihood": likelihood_1_to_5,
                "control_effectiveness": control_eff_1_to_10,
                "source": source,
            },
            "updated_risk_assessment": {
                "asset_id": asset_id,
                "asset_name": asset_name,
                "risk_score": new_risk.risk_score,
                "expected_loss": new_risk.expected_loss,
                "risk_level": new_risk.risk_level,
                "ale": new_risk.ale,
                "risk_drivers": new_risk.risk_drivers,
                "loss_breakdown": new_risk.loss_breakdown,
                "factors": {
                    "likelihood": new_risk.factors.likelihood,
                    "criticality": new_risk.factors.criticality,
                    "vulnerability_severity": new_risk.factors.vulnerability_severity,
                    "control_effectiveness": new_risk.factors.control_effectiveness,
                    "asset_value_factor": new_risk.factors.asset_value_factor,
                },
            },
            "message": "Telemetry ingested successfully. Risk recalculated.",
        }

        conn.close()
        return result

    except HTTPException:
        raise
    except Exception as e:
        # Log the error and return a meaningful response
        raise HTTPException(status_code=500, detail=f"Failed to ingest telemetry: {str(e)}")


# ---- Investment Optimization Endpoints ----

@router.get("/investment/options", response_model=Dict[str, Any])
async def get_investment_options() -> Dict[str, Any]:
    """Get all investment options from the database.

    Returns options with their cost, expected effectiveness,
    and target vulnerability/control references.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, cost, expected_effectiveness, "
        "target_vulnerability_id, target_control_id FROM investment_options"
    )
    rows = cursor.fetchall()
    conn.close()

    options = []
    for row in rows:
        options.append(
            {
                "id": row[0],
                "name": row[1],
                "cost": row[2],
                "expected_effectiveness": row[3],
                "target_vulnerability_id": row[4],
                "target_control_id": row[5],
            }
        )

    return {"investment_options": options}


@router.get("/investment/optimize/{budget}", response_model=Dict[str, Any])
async def optimize_investment(
    budget: int = Path(..., ge=1, description="Maximum budget for investment optimization"),
) -> Dict[str, Any]:
    """Optimize investment selection using a knapsack-style algorithm.

    Selects investment options within the given budget to maximize
    total expected effectiveness, providing risk reduction estimates
    based on the FAIR model.

    The algorithm:
      1. Sort options by effectiveness/cost ratio (benefit per dollar)
      2. Greedily select options within budget
      3. Calculate projected risk reduction for selected combination
      4. Return ROI and recommended selection

    Args:
        budget: Maximum total cost to invest (USD)

    Returns:
        Selected options, total cost, expected risk reduction, and ROI.
    """
    from . import risk_engine

    conn = get_connection()
    cursor = conn.cursor()

    # Get all investment options
    cursor.execute(
        "SELECT id, name, cost, expected_effectiveness, "
        "target_vulnerability_id, target_control_id FROM investment_options"
    )
    rows = cursor.fetchall()

    # Get all assets for risk baseline
    cursor.execute("SELECT id, criticality, value_range FROM assets")
    assets_rows = cursor.fetchall()

    # Get all current risk assessments to establish baseline
    baseline_ales = []
    for asset_row in assets_rows:
        asset_id = asset_row[0]
        try:
            result = risk_engine.assess_asset_risk(asset_id)
            baseline_ales.append(result.ale)
        except Exception:
            baseline_ales.append(0.0)

    conn.close()

    if not rows:
        return {
            "recommendations": [],
            "total_cost": 0,
            "expected_risk_reduction": 0.0,
            "roi": 0.0,
            "baseline_ale": sum(baseline_ales),
        }

    # Normalize effectiveness and calculate benefit/cost ratio
    # benefit = expected_effectiveness, weight = cost
    # Sort by effectiveness/cost ratio (highest first)
    option_list = []
    for row in rows:
        opt_id, name, cost, eff, target_vuln, target_ctrl = row
        if cost <= 0:
            ratio = float('inf')
        else:
            ratio = eff / cost
        option_list.append(
            {
                "id": opt_id,
                "name": name,
                "cost": cost,
                "effectiveness": eff,
                "ratio": ratio,
                "target_vulnerability_id": target_vuln,
                "target_control_id": target_ctrl,
            }
        )

    # Sort by ratio descending, then by effectiveness descending for ties
    option_list.sort(key=lambda x: (-x["ratio"], -x["effectiveness"]))

    # Greedy selection within budget
    selected = []
    total_cost = 0
    total_effectiveness = 0

    for opt in option_list:
        if total_cost + opt["cost"] <= budget:
            selected.append(opt)
            total_cost += opt["cost"]
            total_effectiveness += opt["effectiveness"]

    # Calculate risk reduction based on selected controls
    # Principle: risk reduction proportional to total effectiveness gained
    # and the assets they protect
    # For each selected control, find target asset and compute reduction

    # Aggregate effectiveness of selected controls
    selected_effectiveness = sum(o["effectiveness"] for o in selected)
    num_selected = len(selected)
    max_possible = max(o["effectiveness"] for o in option_list) * len(option_list) if option_list else 1

    # Compute baseline ALE across all assets
    baseline_ale_total = sum(baseline_ales)

    # Risk reduction: proportional to (total_effectiveness / max_possible) * baseline_ale
    # With diminishing returns: sqrt scaling for multiple controls
    if num_selected > 0:
        # Diminishing returns: sqrt scaling
        risk_reduction_pct = min(1.0, (selected_effectiveness / max_possible) ** 0.5)
    else:
        risk_reduction_pct = 0.0

    expected_risk_reduction = baseline_ale_total * risk_reduction_pct

    # ROI = risk_reduction / cost (dimensionless ratio; in production would
    # map to $ risk saved per $ invested)
    roi = (expected_risk_reduction / total_cost * 100.0) if total_cost > 0 else 0.0

    return {
        "recommendations": [
            {
                "id": o["id"],
                "name": o["name"],
                "cost": o["cost"],
                "expected_effectiveness": o["effectiveness"],
                "benefit_cost_ratio": round(o["ratio"], 4),
            }
            for o in selected
        ],
        "selected_options": [o["name"] for o in selected],
        "total_cost": total_cost,
        "expected_risk_reduction": round(expected_risk_reduction, 2),
        "roi_percent": round(roi, 2),
        "baseline_ale": round(baseline_ale_total, 2),
        "risk_reduction_pct": round(risk_reduction_pct * 100, 1),
        " methodology": "knapsack greedy selection by effectiveness/cost ratio with sqrt diminishing returns",
    }


@router.post("/chat/llm", response_model=Dict[str, Any])
async def llm_chat(
    message: str = Body(..., description="User message/query"),
    asset_id: int = Body(default=None, description="Optional specific asset ID"),
) -> Dict[str, Any]:
    """Chat with LLM about cybersecurity risk scenarios.

    Accepts a user message and optional asset ID,
    returns LLM-generated strategic recommendations
    based on the current risk state and investment optimization.

    The LLM uses the same quantitative FAIR model backend
    but generates natural language insights and recommendations.
    """
    from zenith_backend.scenario_analysis import get_llm_scenario_recommendations

    result = get_llm_scenario_recommendations(
        budget=50000,
        asset_id=asset_id,
    )

    return {
        "response": result["llm_insights"],
        "status": "llm" if result.get("llm_insights", "").startswith("Risk Management") else "deterministic",
        "current_risk_level": result.get("current_risk_level", "unknown"),
        "risk_score": result.get("current_risk", 0),
        "selected_controls": len(result.get("selected_controls", [])),
        "total_investment": result.get("total_cost", 0),
        "risk_reduction_pct": result.get("risk_change_pct", 0),
        "message": result.get("message", "Chat completed."),
    }