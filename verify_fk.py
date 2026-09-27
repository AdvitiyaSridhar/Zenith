#!/usr/bin/env python
"""Fix and verify database seed data determinism and FK validity."""
import sqlite3
import os

DB_PATH = r"C:\Advi\Collegestuff\Events\SIH\zenith\backend\risk_assessment.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Step 1: Check all asset IDs referenced by FK tables
print("=== Checking FK validity ===")

# Get all valid asset IDs
cursor.execute("SELECT id FROM assets")
valid_asset_ids = set(row[0] for row in cursor.fetchall())
print(f"Valid asset IDs: {sorted(valid_asset_ids)}")

# Check vulnerabilities FK
cursor.execute("SELECT affected_asset_id FROM vulnerabilities")
vuln_asset_ids = set(row[0] for row in cursor.fetchall())
print(f"Vulnerability asset IDs: {sorted(vuln_asset_ids)}")
print(f"  Invalid vuln FKs: {vuln_asset_ids - valid_asset_ids}")

# Check threats FK
cursor.execute("SELECT target_asset_id FROM threats")
threat_asset_ids = set(row[0] for row in cursor.fetchall())
print(f"Threat asset IDs: {sorted(threat_asset_ids)}")
print(f"  Invalid threat FKs: {threat_asset_ids - valid_asset_ids}")

# Check controls FK
cursor.execute("SELECT target_asset_id FROM controls")
ctrl_asset_ids = set(row[0] for row in cursor.fetchall())
print(f"Control asset IDs: {sorted(ctrl_asset_ids)}")
print(f"  Invalid control FKs: {ctrl_asset_ids - valid_asset_ids}")

# Check risk_assessments FK
cursor.execute("SELECT asset_id FROM risk_assessments")
ra_asset_ids = set(row[0] for row in cursor.fetchall())
print(f"Risk assessment asset IDs: {sorted(ra_asset_ids)}")
print(f"  Invalid risk assessment FKs: {ra_asset_ids - valid_asset_ids}")

# Check telemetry FKs
cursor.execute("SELECT related_asset_id FROM telemetry")
tele_asset_ids = set(row[0] for row in cursor.fetchall())
print(f"Telemetry asset IDs: {sorted(tele_asset_ids)}")
print(f"  Invalid telemetry FKs: {tele_asset_ids - valid_asset_ids}")

# Check investment options FKs
cursor.execute("SELECT target_vulnerability_id FROM investment_options WHERE target_vulnerability_id IS NOT NULL")
inv_vuln_ids = set(row[0] for row in cursor.fetchall())
print(f"Investment vuln IDs: {sorted(inv_vuln_ids)}")
print(f"  Invalid investment vuln FKs: {inv_vuln_ids - valid_asset_ids}")

cursor.execute("SELECT target_control_id FROM investment_options WHERE target_control_id IS NOT NULL")
inv_ctrl_ids = set(row[0] for row in cursor.fetchall())
print(f"Investment control IDs: {sorted(inv_ctrl_ids)}")
print(f"  Invalid investment control FKs: {inv_ctrl_ids - valid_asset_ids}")

conn.close()

print()
print("=== All FK checks complete ===")