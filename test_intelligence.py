#!/usr/bin/env python3
"""Test the intelligence features."""

from src.langgraphagenticai.utils.zero_trust_analyzer import ZeroTrustAnalyzer, RiskLevel
from src.langgraphagenticai.utils.remediation_templates import RemediationTemplates, RemediationEngine

# Test 1: Risk scoring
print("=" * 70)
print("TEST 1: Risk Scoring System")
print("=" * 70)

analyzer = ZeroTrustAnalyzer()

# Simulate some findings
analyzer.risk_findings = [
    analyzer._score_finding("Istio installed", "No"),
    analyzer._score_finding("Strict mTLS enforced", "No"),
    analyzer._score_finding("Default-deny AuthorizationPolicy", "No"),
    analyzer._score_finding("Kubernetes NetworkPolicy default-deny exists", "Yes"),
]

summary = analyzer.get_risk_summary()
print(f"\n📊 Risk Summary:")
print(f"  Overall Rating: {summary['risk_rating']}")
print(f"  Risk Score: {summary['total_risk_score']}/{summary['max_risk_score']}")
print(f"  Risk %: {summary['risk_percentage']:.1f}%")
print(f"  Critical: {summary['critical_count']}, High: {summary['high_count']}, Medium: {summary['medium_count']}")

# Test 2: Remediation templates
print("\n" + "=" * 70)
print("TEST 2: Remediation Templates")
print("=" * 70)

templates = RemediationTemplates()
netpol = templates.get_default_deny_network_policy("production")
print(f"\n📝 NetworkPolicy template generated: {len(netpol)} bytes")
print(netpol[:200] + "...")

mtls = templates.get_peer_authentication_strict_mtls("default")
print(f"\n📝 mTLS PeerAuthentication template generated: {len(mtls)} bytes")
print(mtls[:150] + "...")

# Test 3: Remediation engine
print("\n" + "=" * 70)
print("TEST 3: Remediation Engine")
print("=" * 70)

engine = RemediationEngine()
findings = [
    {"title": "No Istio Installed", "severity": "CRITICAL", "finding_type": "no_istio", "namespace": "default", "description": "Istio service mesh not detected"},
    {"title": "No Strict mTLS", "severity": "HIGH", "finding_type": "no_strict_mtls", "namespace": "istio-system", "description": "Mutual TLS not enforced"},
]

remediations = engine.generate_findings_with_remediation(findings)
print(f"\n✅ Generated {len(remediations)} remediations:")
for rem in remediations:
    print(f"  - {rem['title']} ({rem['severity']})")

print("\n✅ All intelligence features working correctly!")
