#!/usr/bin/env python3
"""
Comprehensive Kubernetes Security Audit Test

This script demonstrates the comprehensive security analyzer by:
1. Running the comprehensive_auditor workflow
2. Analyzing all namespaces and resources
3. Generating a full security report with findings and recommendations
"""

import asyncio
import sys
import os

# Fix encoding early - before Crew AI wraps stdout (Windows compatibility)
if sys.stdout.encoding and 'utf' not in sys.stdout.encoding.lower():
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add repo to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from src.langgraphagenticai.main import _initialize_and_run


def print_header():
    """Print header for the test."""
    print("\n" + "=" * 80)
    print("COMPREHENSIVE KUBERNETES SECURITY & COMPLIANCE AUDIT")
    print("=" * 80)
    print("\nThis will perform a detailed analysis of:")
    print("  [*] All namespaces in the cluster")
    print("  [*] Resource inventory (pods, deployments, services, etc.)")
    print("  [*] Security posture (RBAC, network policies, pod security)")
    print("  [*] Compliance status (CIS Kubernetes Benchmark, standards)")
    print("  [*] Configuration issues and best practices")
    print("  [*] Detailed recommendations for remediation")
    print("\nStarting comprehensive audit...\n")


def print_usage():
    """Print usage information."""
    print("""
COMPREHENSIVE SECURITY AUDIT USAGE:

To run the comprehensive security audit:

  1. Using CLI (no UI):
     python -m src.langgraphagenticai.main --no-ui comprehensive_auditor

  2. Using Streamlit UI:
     streamlit run app.py
     Then select "Comprehensive Security Auditor" from dropdown

OUTPUT:
  The audit will generate a detailed report including:
  - Executive summary with key metrics
  - Complete resource inventory by namespace
  - Security findings categorized by severity and type
  - Compliance assessment results
  - Top 10 prioritized recommendations
  - Best practices checklist

REPORT INCLUDES:
  🔴 CRITICAL: Immediate action required
  🟠 HIGH: Address within days
  🟡 MEDIUM: Address within weeks
  🟢 LOW: Consider for future improvements

The report will show:
  - What resources are deployed
  - Their current security state
  - Specific issues found
  - How to fix each issue
  - Industry best practices
""")


if __name__ == "__main__":
    if "--help" in sys.argv or "-h" in sys.argv:
        print_usage()
        sys.exit(0)
    
    print_header()
    
    # Run the comprehensive audit via application initialization
    asyncio.run(_initialize_and_run(usecase="comprehensive_auditor"))
