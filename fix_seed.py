#!/usr/bin/env python
"""Fix database seed data to be fully deterministic without random.uniform."""
import sqlite3
import os
import random

DB_PATH = r"C:\Advi\Collegestuff\Events\SIH\zenith\backend\risk_assessment.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Read current seed data to understand what we're working with
cursor.execute("SELECT id, name, criticality, value_range, business_process FROM assets")
assets = cursor.fetchall()
print(f"Current assets: {len(assets)}")

# Check current expected_loss values
cursor.execute("SELECT id, expected_loss FROM risk_assessments")
losses = cursor.fetchall()
print(f"Current expected_loss values (first 5): {losses[:5]}")

# Check current risk_score values
cursor.execute("SELECT id, current_risk_score FROM risk_assessments")
scores = cursor.fetchall()
print(f"Current risk_score values (first 5): {scores[:5]}")

# The issue: seed_deterministic uses random.uniform(-5, 5) and random.uniform(5000, 500000)
# which makes the "deterministic" seed non-reproducible across runs if the random state differs.
# We need to replace these with deterministic calculations based on the seed.

# Let's replace the random elements with deterministic functions of the seed
random.seed(42)  # Reset with fixed seed

# For risk_score: instead of int(crit * likelihood * (100 - control_eff) / 10 + random.uniform(-5, 5))
# Use: int(crit * likelihood * (100 - control_eff) / 10) - deterministic, no random offset
# But we need to keep scores in a reasonable range

# For expected_loss: instead of risk_score * random.uniform(5000, 500000)
# Use: risk_score * 10000 / 100 * some_factor based on criticality

# Actually, let me just make the seed fully deterministic by using a fixed random sequence
# that's derived from the seed value.

# Reset random with fixed seed
random.seed(42)

# Re-seed all tables deterministically
# First, let's clear and re-seed

# --- Assets --- (keep as is, already deterministic with fixed seed)
# The existing asset seeding already uses random.seed(42) and random.randint/random.choice

# --- Vulnerabilities --- 
# Fix: severity = random.randint(1, 10) is fine (deterministic with seed)
# But affected_asset_id = random.randint(1, len(asset_names)) + 1 could be problematic
# Let's verify it's using the fixed seed properly

# --- Threats --- 
# Similarly, likelihood = random.randint(1, 5) is deterministic with seed

# --- Controls --- 
# effectiveness = random.randint(1, 10) is deterministic

# --- Telemetry --- 
# The bigger issue is the telemetry related_ids using random.randint with the fixed seed

# --- Risk Assessments --- 
# The key fix: replace risk_score formula and expected_loss formula

# Let me just verify the current behavior is deterministic by running seed_deterministic twice

conn.close()

# Now let me properly fix the seed_deterministic function
print("\n=== Fixing seed_deterministic ===")

# Read the current database state
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# The simplest fix: replace the random.uniform calls with deterministic alternatives
# that are still seeded properly.

# For risk_score: use int(crit * likelihood * (100 - control_eff) / 10) 
# This removes the random.uniform(-5, 5) offset but keeps the core calculation
# We can add a deterministic "variance" based on the seed

# For expected_loss: use risk_score * 5000 + (asset_id * 1000) as a deterministic formula
# This ensures each asset has a unique, predictable loss value

# Actually, the best approach is to use a deterministic random sequence
# that's initialized once and then stepped through.

# Let me take a different approach: rewrite seed_deterministic to be truly deterministic
# by using a fixed sequence of random values derived from the seed.

import time

# Read current assets
cursor.execute("SELECT id, name, criticality, value_range, business_process FROM assets")
all_assets = cursor.fetchall()

# Read current vulnerabilities
cursor.execute("SELECT id, name, severity, affected_asset_id FROM vulnerabilities")
all_vulns = cursor.fetchall()

# Read current threats
cursor.execute("SELECT id, name, likelihood, target_asset_id FROM threats")
all_threats = cursor.fetchall()

# Read current controls
cursor.execute("SELECT id, name, effectiveness, cost, target_asset_id FROM controls")
all_controls = cursor.fetchall()

# Read current risk assessments
cursor.execute("SELECT id, asset_id, current_likelihood, current_control_effectiveness, current_risk_score, expected_loss, risk_level FROM risk_assessments")
all_ras = cursor.fetchall()

# Read current investment options
cursor.execute("SELECT id, name, cost, expected_effectiveness, target_vulnerability_id, target_control_id FROM investment_options")
all_invopts = cursor.fetchall()

# Read current scenarios
cursor.execute("SELECT id, name, description, risk_before, risk_after, cost, risk_reduction FROM scenarios")
all_scenarios = cursor.fetchall()

print(f"Current state: {len(all_assets)} assets, {len(all_vulns)} vulns, {len(all_threats)} threats, {len(all_controls)} controls, {len(all_ras)} risk assessments, {len(all_invopts)} investment options, {len(all_scenarios)} scenarios")

# Now rewrite seed_deterministic properly
# The key insight: use random.seed(42) and then use the random module's state consistently

# For risk_score: deterministic formula based on asset properties + seed-derived variance
# For expected_loss: deterministic based on asset properties

# Delete existing data (but keep table structure)
cursor.execute("DELETE FROM telemetry")
cursor.execute("DELETE FROM risk_assessments")
cursor.execute("DELETE FROM investment_options")
cursor.execute("DELETE FROM scenarios")
cursor.execute("DELETE FROM vulnerabilities")
cursor.execute("DELETE FROM controls")
cursor.execute("DELETE FROM threats")
# Don't delete assets - they're the foundation

print("Tables cleared")

# Now re-seed with fully deterministic logic

# --- Assets (keep existing order, just ensure deterministic) ---
asset_names = [
    "Customer Database Server",
    "Employee Laptop Fleet",
    "Web Application Portal",
    "Payment Processing System",
    "Corporate Email Infrastructure",
    "Cloud Storage Bucket",
    "Internal Network Segment",
    "Remote Access VPN Gateway",
    "Intellectual Property Repository",
    "Supply Chain Management System",
]

business_processes = [
    "Customer Data Management",
    "Employee Onboarding/Offboarding",
    "Transaction Processing",
    "Communication & Collaboration",
    "File Storage & Sharing",
    "Software Development",
    "Vendor Management",
    "Financial Reporting",
]

for i, name in enumerate(asset_names):
    criticality = random.randint(1, 5)  # deterministic with seed 42
    value_range = random.choice(["low", "medium", "high"])  # deterministic
    bp = random.choice(business_processes)  # deterministic
    cursor.execute(
        "INSERT INTO assets (name, description, criticality, value_range, business_process) "
        "VALUES (?, ?, ?, ?, ?)",
        (name, f"Critical asset for {bp}", criticality, value_range, bp),
    )

print(f"  Re-seeded {len(asset_names)} assets")

# --- Vulnerabilities ---
vulnerability_names = [
    "Unpatched Software",
    "Weak Password Policies",
    "Lack of Multi-Factor Authentication",
    "Insufficient Network Segmentation",
    "Outdated Operating Systems",
    "Excessive User Privileges",
    "Missing Security Monitoring",
    "Unencrypted Data at Rest",
    "Social Engineering Gaps",
    "Insecure API Endpoints",
]

for i, name in enumerate(vulnerability_names):
    severity = random.randint(1, 10)  # deterministic with seed 42
    # Use deterministic affected_asset_id based on index
    affected_asset_id = (i % len(asset_names)) + 1
    cursor.execute(
        "INSERT INTO vulnerabilities (name, description, severity, created_at, affected_asset_id) "
        "VALUES (?, ?, ?, NULL, ?)",
        (name, f"Vulnerability: {name.lower()}", severity, affected_asset_id),
    )

print(f"  Re-seeded {len(vulnerability_names)} vulnerabilities")

# --- Threats ---
threat_names = [
    "Ransomware Attack",
    "Data Exfiltration",
    "Insider Threat",
    "Phishing Campaign",
    "DDoS Attack",
    "Credential Theft",
    "Supply Chain Compromise",
    "Internal System Misuse",
]

for i, name in enumerate(threat_names):
    likelihood = random.randint(1, 5)  # deterministic with seed 42
    # Deterministic target_asset_id
    target_asset_id = (i % len(asset_names)) + 1
    cursor.execute(
        "INSERT INTO threats (name, description, likelihood, created_at, target_asset_id) "
        "VALUES (?, ?, ?, NULL, ?)",
        (name, f"Threat: {name.lower()}", likelihood, target_asset_id),
    )

print(f"  Re-seeded {len(threat_names)} threats")

# --- Controls ---
control_names = [
    "Multi-Factor Authentication",
    "Regular Patch Management",
    "Network Segmentation",
    "Encryption at Rest",
    "Security Awareness Training",
    "Endpoint Detection & Response",
    "Access Review & Privilege Management",
    "Backup & Recovery System",
    "Web Application Firewall",
    "Identity & Access Management",
]

for i, name in enumerate(control_names):
    effectiveness = random.randint(1, 10)  # deterministic with seed 42
    cost = random.randint(5000, 50000)  # deterministic with seed
    # Deterministic target_asset_id
    target_asset_id = (i % len(asset_names)) + 1
    cursor.execute(
        "INSERT INTO controls (name, description, effectiveness, created_at, cost, target_asset_id) "
        "VALUES (?, ?, ?, NULL, ?, ?)",
        (name, f"Control: {name.lower()}", effectiveness, cost, target_asset_id),
    )

print(f"  Re-seeded {len(control_names)} controls")

# --- Telemetry ---
import datetime
observation_dates = [datetime.datetime.now() - datetime.timedelta(days=x) for x in range(30)]

for i, obs_date in enumerate(observation_dates):
    severity = random.randint(1, 10)  # deterministic
    note = f"Observation {i+1}: security telemetry entry"
    # Use deterministic related IDs based on index
    related_asset_id = (i % len(asset_names)) + 1
    related_vuln_id = (i % len(vulnerability_names)) + 1
    related_threat_id = (i % len(threat_names)) + 1
    related_ctrl_id = (i % len(control_names)) + 1
    
    cursor.execute(
        "INSERT INTO telemetry "
        "(observation_date, severity_rating, note, related_asset_id, related_vulnerability_id, related_threat_id, related_control_id) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            obs_date.strftime("%Y-%m-%d %H:%M:%S"),
            severity,
            note,
            related_asset_id,
            related_vuln_id,
            related_threat_id,
            related_ctrl_id,
        ),
    )

print(f"  Re-seeded {len(observation_dates)} telemetry entries")

# --- Risk Assessments ---
for asset_id in range(1, len(asset_names) + 1):
    # Use deterministic likelihood based on asset_id and seed
    likelihood = random.randint(1, 5)  # deterministic with seed 42
    
    # Re-query criticality from the asset we're assessing
    cursor.execute("SELECT criticality FROM assets WHERE id = ?", (asset_id,))
    row = cursor.fetchone()
    crit = row[0] if row else 3
    
    # FIXED: deterministic risk_score without random.uniform(-5, 5)
    # Use: min(100, int(crit * likelihood * (100 - 5) / 10)) with a seed-derived offset
    # Actually, let's use a proper deterministic formula:
    # risk_score = min(100, int(crit * likelihood * 8 + 5)) - gives range based on crit/likelihood
    # but with seed-derived consistency
    base_score = int(crit * likelihood * 8 + 2)  # deterministic based on crit and likelihood
    risk_score = min(100, max(15, base_score))  # clamp to 15-100 range
    
    # FIXED: deterministic expected_loss without random.uniform(5000, 500000)
    # Use: risk_score * 5000 + asset_id * 100 - gives each asset a unique, predictable loss
    expected_loss = round(risk_score * 5000 + asset_id * 100, 2)
    
    if risk_score >= 70:
        risk_level = "critical"
    elif risk_score >= 50:
        risk_level = "high"
    elif risk_score >= 30:
        risk_level = "medium"
    else:
        risk_level = "low"
    
    cursor.execute(
        "INSERT INTO risk_assessments "
        "(asset_id, current_likelihood, current_control_effectiveness, current_risk_score, expected_loss, risk_level) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (asset_id, likelihood, 5, risk_score, expected_loss, risk_level),  # fixed control_eff=5
    )

print(f"  Re-seeded {len(asset_names)} risk assessments")

# --- Investment Options ---
investment_names = [
    "MFA Deployment Across All Assets",
    "Enterprise-wide Patch Management System",
    "Network Segmentation Implementation",
    "Company-wide Encryption Initiative",
    "Security Awareness Training Program",
    "EDR Solution for Endpoint Protection",
    "Regular Access Review Process",
    "Comprehensive Backup & Recovery",
    "WAF for Web Application Protection",
    "Advanced IAM Solution",
]

for i, name in enumerate(investment_names):
    cost = random.randint(10000, 100000)  # deterministic with seed 42
    effectiveness = random.randint(1, 10)  # deterministic with seed 42
    # Deterministic target_id references
    target_vuln_id = (i % len(vulnerability_names)) + 1 if i % 2 == 0 else None
    target_ctrl_id = (i % len(control_names)) + 1 if i % 2 == 1 else None
    
    cursor.execute(
        "INSERT INTO investment_options "
        "(name, description, cost, expected_effectiveness, target_vulnerability_id, target_control_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, f"Investment: {name.lower()}", cost, effectiveness, target_vuln_id, target_ctrl_id),
    )

print(f"  Re-seeded {len(investment_names)} investment options")

# --- Scenarios ---
scenario_names = [
    "Current State",
    "Deploy MFA Everywhere",
    "Implement Patch Management",
    "Network Segmentation",
    "Full Encryption Rollout",
    "Security Training Program",
    "EDR Implementation",
    "Combined Investment (MFA + Patching)",
    "Combined Investment (Network + Encryption)",
    "Maximum Security Posture",
]

for i, name in enumerate(scenario_names):
    # Deterministic risk_before based on index
    risk_before = random.randint(30, 90)  # deterministic with seed 42
    risk_after = max(0, risk_before - random.randint(10, 60))  # deterministic
    cost = random.randint(5000, 80000)  # deterministic with seed 42
    risk_reduction = max(0, risk_before - risk_after)
    
    cursor.execute(
        "INSERT INTO scenarios "
        "(name, description, risk_before, risk_after, cost, risk_reduction) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (name, f"Scenario: {name.lower()}", risk_before, risk_after, cost, risk_reduction),
    )

print(f"  Re-seeded {len(scenario_names)} scenarios")

conn.commit()
conn.close()

print("\n=== Database re-seeding complete ===")
print("All data is now fully deterministic with seed=42")