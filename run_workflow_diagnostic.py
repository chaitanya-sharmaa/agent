#!/usr/bin/env python3
"""
Diagnostic tool to show which workflow is being used and how to run comprehensive audit.
"""

import sys
sys.path.insert(0, '.')

from src.langgraphagenticai.config.config_loader import get_config

def main():
    print("\n" + "="*80)
    print("KUBERNETES SECURITY AUDIT - WORKFLOW DIAGNOSTIC")
    print("="*80 + "\n")
    
    # Load configuration
    config = get_config()
    workflows = config.get_workflows()
    
    print("📋 AVAILABLE WORKFLOWS:\n")
    
    for workflow_id, workflow_config in workflows.items():
        name = workflow_config.get('name', 'Unknown')
        description = workflow_config.get('description', 'No description')
        
        print(f"  {workflow_id}:")
        print(f"    Name: {name}")
        print(f"    Description: {description}")
        print()
    
    print("\n" + "="*80)
    print("WORKFLOW COMPARISON")
    print("="*80 + "\n")
    
    print("┌─────────────────────────────────────────────────────────────────────────┐")
    print("│ WORKFLOW: auditor                                                       │")
    print("├─────────────────────────────────────────────────────────────────────────┤")
    print("│ Scope: Basic security checks                                            │")
    print("│ Checks: ~9 essential checks                                             │")
    print("│ Focus: Istio, mTLS, AuthorizationPolicy, NetworkPolicy                  │")
    print("│ Output: Simple assessment table                                         │")
    print("│                                                                         │")
    print("│ Run with:                                                               │")
    print("│   python3 -m src.langgraphagenticai.main --no-ui auditor               │")
    print("│   OR select 'auditor' in Streamlit UI                                   │")
    print("└─────────────────────────────────────────────────────────────────────────┘")
    
    print("\n")
    
    print("┌─────────────────────────────────────────────────────────────────────────┐")
    print("│ WORKFLOW: comprehensive_auditor (⭐ RECOMMENDED FOR DETAILED ANALYSIS)   │")
    print("├─────────────────────────────────────────────────────────────────────────┤")
    print("│ Scope: ENTIRE cluster analysis                                          │")
    print("│ Checks: 100+ security checks                                            │")
    print("│ Coverage:                                                               │")
    print("│   ✓ All namespaces                                                      │")
    print("│   ✓ Pod security (privileges, root user, capabilities)                 │")
    print("│   ✓ RBAC (roles, bindings, least privilege)                            │")
    print("│   ✓ Network policies (segmentation, defaults)                          │")
    print("│   ✓ Deployments (HA, resource limits, health checks)                   │")
    print("│   ✓ Services, ConfigMaps, Secrets                                      │")
    print("│   ✓ Service accounts and tokens                                        │")
    print("│   ✓ Istio components (if installed)                                    │")
    print("│   ✓ CIS Benchmark compliance                                           │")
    print("│   ✓ NIST framework alignment                                           │")
    print("│   ✓ Pod Security Standards                                             │")
    print("│                                                                         │")
    print("│ Output: Comprehensive report with:                                      │")
    print("│   • Executive summary                                                   │")
    print("│   • Resource inventory by namespace                                     │")
    print("│   • Security findings by category                                       │")
    print("│   • Compliance assessment                                               │")
    print("│   • Top 10 prioritized recommendations                                  │")
    print("│   • Best practices checklist                                            │")
    print("│                                                                         │")
    print("│ Run with:                                                               │")
    print("│   python3 -m src.langgraphagenticai.main --no-ui comprehensive_auditor │")
    print("│   OR select 'Comprehensive Security Auditor' in Streamlit UI            │")
    print("└─────────────────────────────────────────────────────────────────────────┘")
    
    print("\n")
    
    print("┌─────────────────────────────────────────────────────────────────────────┐")
    print("│ WORKFLOW: creator                                                       │")
    print("├─────────────────────────────────────────────────────────────────────────┤")
    print("│ Scope: Audit + Deploy + Verify                                          │")
    print("│ Actions:                                                                │")
    print("│   1. Run auditor (basic security assessment)                            │")
    print("│   2. Deploy security policies (Helm chart)                              │")
    print("│   3. Verify post-deployment                                             │")
    print("│                                                                         │")
    print("│ Run with:                                                               │")
    print("│   python3 -m src.langgraphagenticai.main --no-ui creator               │")
    print("│   OR select 'creator' in Streamlit UI                                   │")
    print("└─────────────────────────────────────────────────────────────────────────┘")
    
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80 + "\n")
    
    print("❌ If you ran 'auditor' and got basic checks like:")
    print("   • Istio installed: No")
    print("   • Strict mTLS enforced: No")
    print("   • Default-deny AuthorizationPolicy: No")
    print("   ↓")
    print("   This is EXPECTED - 'auditor' only does basic checks\n")
    
    print("✅ For COMPREHENSIVE analysis showing:")
    print("   • All resources in all namespaces")
    print("   • Pod security issues (privileged containers, running as root, etc.)")
    print("   • RBAC issues (wildcard permissions, least privilege violations)")
    print("   • Network segmentation issues")
    print("   • Compliance gaps (CIS, NIST)")
    print("   • Specific resources and fix recommendations")
    print("   ↓")
    print("   USE THIS COMMAND:\n")
    
    print("   🚀 " + "─"*76)
    print("   python3 -m src.langgraphagenticai.main --no-ui comprehensive_auditor")
    print("   🚀 " + "─"*76 + "\n")
    
    print("="*80)
    print("EXAMPLE OUTPUT DIFFERENCE")
    print("="*80 + "\n")
    
    print("AUDITOR output (basic):")
    print("  Istio installed: No")
    print("  Strict mTLS enforced: No")
    print("  Default-deny AuthorizationPolicy: No\n")
    
    print("COMPREHENSIVE_AUDITOR output (detailed):")
    print("  ✓ Executive Summary")
    print("    - Total Namespaces: 20")
    print("    - Critical Issues: 5")
    print("    - High Issues: 12")
    print("    - Medium Issues: 28\n")
    
    print("  ✓ Resource Inventory")
    print("    - Pods: 84 total (namespace breakdown)")
    print("    - Deployments: 12 total (namespace breakdown)")
    print("    - Services: 23 total (namespace breakdown)\n")
    
    print("  ✓ Security Findings")
    print("    Pod Security Issues:")
    print("      - Pod 'kafka-broker' running with privileged: true")
    print("      - Pod 'mongo-0' running as root (uid: 0)")
    print("      - Pod 'api-server' missing resource limits\n")
    
    print("    RBAC Issues:")
    print("      - Role 'admin' in default has wildcard permissions")
    print("      - ClusterRole 'view' bound to system:unauthenticated\n")
    
    print("    Network Issues:")
    print("      - Namespace 'default' has no NetworkPolicy\n")
    
    print("  ✓ Recommendations")
    print("    1. [CRITICAL] Remove privileged containers")
    print("    2. [HIGH] Implement default-deny NetworkPolicy")
    print("    3. [HIGH] Restrict RBAC wildcard permissions")
    print("    ... (and 7 more)\n")
    
    print("="*80)
    print()

if __name__ == "__main__":
    main()
