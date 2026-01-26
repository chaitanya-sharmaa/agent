# Comprehensive Security & Compliance Audit Guide

## Overview

The **Comprehensive Security Auditor** performs an in-depth analysis of your Kubernetes cluster including all namespaces, resources, security configurations, compliance status, and detailed recommendations.

## What It Analyzes

### 1. **Resource Inventory**
- **Pods**: Count and distribution by namespace, resource usage, security contexts
- **Deployments**: Replication, resource limits, health checks
- **StatefulSets**: Persistence, ordering guarantees
- **DaemonSets**: System-level services, update strategies
- **Services**: Types, selectors, exposure risks
- **ConfigMaps & Secrets**: Data protection, access controls
- **RBAC**: Roles, RoleBindings, service accounts, permissions

### 2. **Security Posture Analysis**

#### Pod Security
- ✅ Container privilege levels (root vs non-root)
- ✅ Privileged container detection
- ✅ Linux capability restrictions
- ✅ Read-only filesystem enforcement
- ✅ Security context configuration
- ✅ Service account token auto-mounting

#### RBAC (Role-Based Access Control)
- ✅ Over-privileged roles (wildcard permissions)
- ✅ Unauthenticated/anonymous access
- ✅ Service account permissions
- ✅ ClusterRole vs Role usage
- ✅ Least privilege violations

#### Network Security
- ✅ Network policy coverage
- ✅ Default deny rules
- ✅ Ingress/egress restrictions
- ✅ Service mesh integration (Istio)
- ✅ mTLS enforcement

#### Supply Chain Security
- ✅ Image registry security
- ✅ Image pull policies
- ✅ Container image versions
- ✅ Admission controllers

### 3. **Compliance Standards**

#### CIS Kubernetes Benchmark
- 1.1 - RBAC and Service Accounts
- 1.2 - Pod Security
- 1.3 - Network Policies
- 1.4 - Secrets Management
- And more...

#### NIST Cybersecurity Framework
- Identify: Asset inventory, threat modeling
- Protect: Access controls, data protection
- Detect: Monitoring, logging
- Respond: Incident response procedures
- Recover: Backup and disaster recovery

#### PCI-DSS for Kubernetes
- Encryption at rest and in transit
- Access controls and authentication
- Regular security assessments

### 4. **Configuration Issues**

Detects problems like:
- Missing resource limits/requests
- Single replica deployments
- No pod disruption budgets
- Missing liveness/readiness probes
- Outdated base images
- Missing health checks

## Running the Audit

### Option 1: CLI Mode (Recommended for Reports)

```bash
python -m src.langgraphagenticai.main --no-ui comprehensive_auditor
```

Output will show:
- Real-time progress as namespaces are analyzed
- Summary of findings
- Detailed security report with recommendations

### Option 2: Streamlit UI

```bash
python -m src.langgraphagenticai.main
```

1. Select "Comprehensive Security Auditor" from the workflow dropdown
2. Click "Execute"
3. View results with interactive filtering by severity/category

### Option 3: Using Test Script

```bash
python run_comprehensive_audit.py
```

## Output Report Structure

### 1. Executive Summary
```
- Total Namespaces: X
- Namespaces Analyzed: [list]
- Critical Issues: X
- High Issues: Y
- Medium Issues: Z
```

### 2. Resource Inventory
```
- Pods: XX in default, YY in kube-system, ...
- Deployments: XX total
- Services: XX total
- Secrets: XX total
- RBAC Rules: XX total
```

### 3. Security Findings (Categorized)

#### Pod Security Issues
```
🔴 CRITICAL - Privileged container detected
   Resource: Pod 'app-pod' in default namespace
   Issue: Container runs with privileged: true
   Fix: Remove privileged mode or use capabilities instead

🟠 HIGH - Container runs as root
   Resource: Pod 'api-service' in default namespace
   Issue: No runAsUser specified
   Fix: Add securityContext.runAsUser: 1000
```

#### RBAC Issues
```
🔴 CRITICAL - Unauthenticated access granted
   Resource: RoleBinding 'public-access' in default
   Issue: Bound to system:unauthenticated
   Fix: Remove unauthenticated bindings; use strong auth

🟠 HIGH - Wildcard permissions
   Resource: Role 'admin' in default
   Issue: Rules allow verbs: ["*"] on resources: ["*"]
   Fix: Specify exact verbs (get, list) and resources
```

#### Network Security Issues
```
🟡 MEDIUM - No network policies defined
   Resource: Namespace 'default'
   Issue: No network policies restrict traffic
   Fix: Create default-deny NetworkPolicy and add specific allow rules
```

### 4. Compliance Status
```
CIS Kubernetes Benchmark v1.24
- 1.1 RBAC and Service Accounts: FAILED
  Gap: Service accounts found with wildcard permissions
  
- 1.2 Pod Security: PARTIAL
  Gap: Some pods missing security contexts

- 1.3 Network Policies: WARNING
  Only 2/10 namespaces have network policies
```

### 5. Top 10 Recommendations (Prioritized)

```
CRITICAL (DO IMMEDIATELY):
1. Remove privileged containers from production workloads
2. Implement default deny network policies
3. Restrict RBAC wildcard permissions

HIGH (NEXT WEEK):
4. Enforce runAsUser on all containers
5. Implement resource limits on all pods
6. Enable mTLS via Istio PeerAuthentication

MEDIUM (NEXT MONTH):
7. Deploy pod disruption budgets for HA
8. Implement image scanning in CI/CD
9. Rotate service account credentials
10. Enable audit logging
```

### 6. Best Practices Checklist

```
Security Best Practices:
- [ ] All pods have resource limits (memory, CPU)
- [ ] No privileged containers
- [ ] Network policies defined in all namespaces
- [ ] RBAC follows least privilege principle
- [ ] Service accounts not automounting tokens
- [ ] Secrets encrypted at rest
- [ ] Pod security standards enforced (restricted)
- [ ] Service mesh with mTLS enabled
- [ ] Regularly patched base images
- [ ] Security scanning in deployment pipeline
```

## Severity Levels

| Level | Color | Meaning | Action |
|-------|-------|---------|--------|
| CRITICAL | 🔴 | Immediate security risk | Fix immediately |
| HIGH | 🟠 | Important security issue | Fix within days |
| MEDIUM | 🟡 | Should be addressed | Fix within weeks |
| LOW | 🟢 | Nice to have | Consider for improvements |
| INFO | 🔵 | Informational | For awareness |

## Categories Analyzed

1. **Pod Security** - Container security, runtime configurations
2. **RBAC** - Role-based access control, permissions
3. **Network Security** - Network policies, service mesh
4. **Resource Management** - Limits, requests, quotas
5. **Compliance** - Standards, benchmarks, regulations
6. **Supply Chain** - Images, registries, scanning
7. **Secrets Management** - Encryption, rotation, access
8. **Audit & Logging** - Event tracking, compliance logging
9. **High Availability** - Replicas, disruption budgets
10. **Configuration** - Best practices, hardening

## Customization

To customize the audit for your organization:

1. **Edit prompts.yaml**: Modify the `comprehensive_auditor.system_prompt` to add custom checks
2. **Edit comprehensive_analyzer.py**: Add organization-specific security rules
3. **Add custom workflows**: Create specialized audits for compliance frameworks (HIPAA, SOC2, etc.)

Example: Add HIPAA checks
```yaml
workflows:
  hipaa_auditor:
    name: "HIPAA Compliance Auditor"
    description: "Analyze cluster for HIPAA compliance"
    system_prompt: |
      Perform HIPAA-specific security audit...
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Security Audit
on: [push, pull_request]
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Comprehensive Audit
        run: |
          python -m src.langgraphagenticai.main --no-ui comprehensive_auditor > audit_report.txt
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: security-audit-report
          path: audit_report.txt
```

## Interpretation Guide

### Common Findings

**Finding**: Pod runs as root
- **Risk**: Privilege escalation, lateral movement
- **Fix**: Add `securityContext.runAsUser: 1000` to pod spec
- **Priority**: HIGH

**Finding**: No network policies
- **Risk**: East-west traffic, container escape
- **Fix**: Implement default-deny and whitelist rules
- **Priority**: HIGH

**Finding**: Wildcard RBAC permissions
- **Risk**: Over-privilege, compromise impact
- **Fix**: Use specific verbs and resources in roles
- **Priority**: HIGH

**Finding**: No resource limits
- **Risk**: Resource starvation, DoS
- **Fix**: Define resources.limits and requests
- **Priority**: MEDIUM

## Frequency

Recommended audit frequency:
- **Weekly**: For active development clusters
- **Monthly**: For stable production clusters
- **Daily**: For highly sensitive environments
- **On-demand**: Before deployments, after incidents

## Related Commands

```bash
# Run specific workflow
python -m src.langgraphagenticai.main --no-ui comprehensive_auditor

# Run with debug output
DEBUG=1 python -m src.langgraphagenticai.main --no-ui comprehensive_auditor

# Run with streaming output
python -m src.langgraphagenticai.main --no-ui comprehensive_auditor 2>&1 | tee audit.log

# Run Streamlit UI for interactive mode
python -m src.langgraphagenticai.main
```

## Support & Documentation

- **Full Guide**: See `docs/COMPREHENSIVE_SECURITY_AUDIT.md`
- **Configuration**: See `CONFIG_GUIDE.md`
- **Examples**: See `config/examples/`
- **Troubleshooting**: See `docs/TROUBLESHOOTING_GUIDE.md`

## Next Steps

1. Run the comprehensive audit on your cluster
2. Review findings by severity
3. Create action plan for critical/high issues
4. Implement recommendations from lowest cost (policy enforcement) to highest
5. Re-run audit weekly to track progress
6. Integrate into CI/CD for continuous compliance

---

**Note**: The comprehensiveness of the audit depends on:
- Cluster size and complexity
- Number of namespaces
- Number and types of resources
- MCP server connectivity
- LLM context window size (may need to increase for very large clusters)
