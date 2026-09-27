"""Scenario Analysis Module.

Allows comparison of multiple security investment scenarios.

Each scenario compares:
- Risk before investment
- Investment cost
- Risk after investment
- Risk reduction
- Residual risk

Scenarios can include: current state, patching critical vulnerability,
improving endpoint protection, increasing monitoring, combined investments, etc.
"""

import sqlite3
import os
import json
from typing import Dict, List, Any, Optional

DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "risk_assessment.db"
)

# Optional LLM integration
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def get_connection():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_scenario(name: str, description: str, investment_option_id: int = None,
                    risk_before: int = None, risk_after: int = None,
                    cost: int = None, risk_reduction: int = None) -> int:
    """Create a new scenario in the database.

    Returns the scenario ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO scenarios (name, description, investment_option_id, risk_before, "
        "risk_after, cost, risk_reduction) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, description, investment_option_id, risk_before, risk_after, cost, risk_reduction),
    )
    scenario_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return scenario_id


def get_scenarios() -> list:
    """Get all scenarios."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, risk_before, risk_after, cost, risk_reduction, created_at FROM scenarios")
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "name": r[1],
            "description": r[2],
            "risk_before": r[3],
            "risk_after": r[4],
            "cost": r[5],
            "risk_reduction": r[6],
            "created_at": r[7],
        }
        for r in rows
    ]


def delete_scenario(scenario_id: int) -> bool:
    """Delete a scenario by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM scenarios WHERE id = ?", (scenario_id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception:
        conn.close()
        return False


def compare_scenarios(scenario_ids: List[int]) -> Dict[str, Any]:
    """Compare multiple scenarios side by side.

    Returns a comparison showing risk before/after, costs, and risk reduction
    for each scenario, plus aggregate insights.
    """
    conn = get_connection()
    cursor = conn.cursor()

    scenarios = []
    for sid in scenario_ids:
        cursor.execute("SELECT id, name, description, risk_before, risk_after, cost, risk_reduction FROM scenarios WHERE id = ?",
                       (sid,))
        row = cursor.fetchone()
        if row:
            scenarios.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "risk_before": row[3],  # Fixed: SELECT id(0), name(1), description(2), risk_before(3)
                "risk_after": row[4],
                "cost": row[5],
                "risk_reduction": row[6],
            })
    conn.close()

    if not scenarios:
        return {"error": "No scenarios found"}

    # Calculate aggregate metrics
    total_cost = sum(s["cost"] for s in scenarios if s.get("cost"))
    total_risk_reduction = sum(s["risk_reduction"] for s in scenarios if s.get("risk_reduction"))

    # Find the scenario with the best risk reduction
    best_rr_scenario = max(scenarios, key=lambda s: s.get("risk_reduction", 0) or 0) if scenarios else None
    lowest_cost_scenario = min(scenarios, key=lambda s: s.get("cost", float('inf')) or float('inf')) if scenarios else None

    # Determine the scenario with risk after closest to zero
    lowest_risk_scenario = min(
        [s for s in scenarios if s.get("risk_after") is not None],
        key=lambda s: s.get("risk_after", 999) or 999,
    ) if scenarios else None

    return {
        "scenarios": scenarios,
        "total_cost": total_cost,
        "total_risk_reduction": total_risk_reduction,
        "best_risk_reduction_scenario": best_rr_scenario["name"] if best_rr_scenario else None,
        "best_risk_reduction": best_rr_scenario["risk_reduction"] if best_rr_scenario else 0,
        "lowest_cost_scenario": lowest_cost_scenario["name"] if lowest_cost_scenario else None,
        "lowest_cost": lowest_cost_scenario["cost"] if lowest_cost_scenario else None,
        "lowest_risk_scenario": lowest_risk_scenario["name"] if lowest_risk_scenario else None,
        "lowest_risk_after": lowest_risk_scenario["risk_after"] if lowest_risk_scenario else None,
    }


def get_llm_scenario_recommendations(budget: int = None, asset_id: int = None) -> Dict[str, Any]:
    """Get LLM-enhanced scenario recommendations for security investment.

    This function:
    1. Runs the investment optimization knapsack algorithm within the given budget
    2. Calculates risk before/after using the FAIR risk engine
    3. Uses an LLM to generate natural language insights and recommendations
       based on the calculated risk reductions and control selections

    Args:
        budget: Maximum investment budget (USD). If None, uses default optimization.
        asset_id: Specific asset to optimize for. If None, optimizes across all assets.

    Returns:
        Dict with selected controls, cost, risk reduction, residual risk,
        and LLM-generated narrative insights.
    """
    from zenith_backend.risk_engine import assess_asset_risk, calculate_risk, RiskFactors
    from zenith_backend.investment_optimizer import optimize_investment

    conn = get_connection()
    cursor = conn.cursor()

    # Get current risk state
    if asset_id:
        try:
            current_risk = assess_asset_risk(asset_id)
            current_score = current_risk.risk_score
            current_level = current_risk.risk_level
        except ValueError:
            conn.close()
            return {"error": f"Asset {asset_id} not found"}
    else:
        # Get average risk across all assets
        cursor.execute("SELECT current_risk_score FROM risk_assessments")
        risk_rows = cursor.fetchall()
        current_score = max(r[0] for r in risk_rows) if risk_rows else 50
        current_level = "medium"

    # Run investment optimization
    opt_result = optimize_investment(budget) if budget else optimize_investment(50000)

    # Get control details
    selected_controls = opt_result["selected_controls"]
    total_cost = opt_result["total_cost"]
    risk_reduction = opt_result["risk_reduction"]
    residual_risk = opt_result["residual_risk"]

    # Calculate LLM-enhanced insights
    if OPENAI_AVAILABLE:
        try:
            # Prepare context for LLM
            control_names = ", ".join([c["name"] for c in selected_controls])
            risk_change = current_score - residual_risk
            risk_change_pct = round((risk_change / current_score) * 100, 1) if current_score > 0 else 0

            # Generate LLM insight
            prompt = f"""You are a cybersecurity risk analyst. Based on the following quantitative risk assessment, provide strategic recommendations.

Current Risk: {current_level} (score: {current_score}/100)
Investment Budget: ${total_cost:,}
Selected Controls: {control_names}
Risk Reduction: {risk_change:.1f} points ({risk_change_pct}% reduction)
Residual Risk: {residual_risk:.1f}/100

Provide:
1. A brief executive summary of the risk situation
2. Strategic rationale for the selected controls
3. Priority actions if budget increases
4. Expected business impact in plain language

Keep the response professional, concise (under 200 words), and focused on cybersecurity risk management. Do not make up specific risk scores or probabilities - use only the values provided above."""

            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            llm_insights = response.choices[0].message.content
        except Exception as e:
            llm_insights = f"LLM analysis unavailable: {str(e)[:100]}. Using deterministic analysis below."
    else:
        # Fallback deterministic insights when LLM not available
        risk_change = current_score - residual_risk
        risk_change_pct = round((risk_change / current_score) * 100, 1) if current_score > 0 else 0
        llm_insights = f"""Risk Management Analysis:
- Current risk level: {current_level} (score: {current_score}/100)
- Investing ${total_cost:,} in {len(selected_controls)} control(s) reduces risk by {risk_change_pct}%
- Residual risk after investment: {residual_risk:.1f}/100
- Selected controls: {', '.join([c['name'] for c in selected_controls])}
- Risk reduction per dollar: {round(risk_reduction/total_cost, 4) if total_cost > 0 else 0:.4f}

Recommendation: The selected controls provide measurable risk reduction within budget. Consider additional investments for layered security improvement."""

    conn.close()

    return {
        "selected_controls": selected_controls,
        "total_cost": total_cost,
        "risk_reduction": round(risk_reduction, 1),
        "residual_risk": round(residual_risk, 1),
        "current_risk": current_score,
        "current_risk_level": current_level,
        "risk_change_pct": risk_change_pct,
        "llm_insights": llm_insights,
        "optimization_method": "knapsack greedy by effectiveness/cost ratio",
        "message": "LLM-enhanced scenario analysis completed.",
    }


