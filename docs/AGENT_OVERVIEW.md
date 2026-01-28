# Agent Overview: Kubernetes Comprehensive Security Auditor

## What This Agent Does

### Value Proposition

This AI-powered security auditing agent delivers **comprehensive visibility into your Kubernetes cluster's actual security posture**—something admission controllers like OPA fundamentally cannot provide. By analyzing all 53+ existing pods, services, and policies across your cluster in minutes, it identifies critical gaps such as workloads running without NetworkPolicies, privileged containers bypassing controls, and missing mesh-wide mTLS enforcement. The agent excels at **cross-resource correlation** (detecting pods in namespaces lacking NetworkPolicies), **cluster-wide policy validation** (confirming STRICT mTLS across all namespaces), and **compliance evidence generation** with findings mapped to NIST, CIS, and NSA/CISA standards. Its read-only, non-disruptive operation makes it safe to run in production anytime, while AI-driven contextual analysis prioritizes risks based on namespace criticality and workload sensitivity. Most importantly, it **audits the past** (legacy resources pre-dating OPA policies), **validates the present** (current security posture with trend analysis), and **guides the future** (identifies exactly where to strengthen OPA policies), making it the essential detective control that complements OPA's preventive enforcement for truly comprehensive security.

### Primary Function
This is an **AI-powered Kubernetes security auditing agent** that performs comprehensive, automated security assessments of Kubernetes clusters. It analyzes workloads, network policies, RBAC, service mesh configurations, and provides risk-based findings with compliance mapping.

### Key Capabilities

1. **Automated Security Audit**
   - Discovers all namespaces in the cluster
   - Queries 12+ resource types per namespace (pods, deployments, services, ingresses, networkpolicies, etc.)
   - Analyzes cluster-wide resources (RBAC, mesh policies)
   - Executes 268 queries across a typical 22-namespace cluster

2. **Per-Namespace Security Analysis**
   - NetworkPolicy coverage assessment
   - Service/Ingress exposure detection (LoadBalancer, NodePort, missing TLS)
   - Workload security context evaluation (privileged containers, root users, hostNetwork)
   - Istio mesh configuration validation (VirtualServices, DestinationRules, Gateways)

3. **Cluster-Wide Policy Evaluation**
   - mTLS enforcement check (PeerAuthentication)
   - Service-to-service authorization (AuthorizationPolicy)
   - RBAC over-privilege detection (cluster-admin bindings)

4. **Risk-Based Reporting**
   - **🔴 HIGH RISK** - Critical security gaps (no NetworkPolicies, privileged containers, missing mTLS)
   - **🟠 MEDIUM RISK** - Important issues (missing TLS, permissive configs, root users)
   - **🟡 LOW RISK** - Best practice violations (latest tags, missing TLS on DestinationRules)
   - **💡 RECOMMENDATIONS** - Actionable remediation steps

5. **Compliance Mapping**
   - NIST controls (AC-3, AC-4, SC-7, SC-8, SC-13, CM-7, CM-8)
   - CIS Kubernetes Benchmark (1.x, 2.x, 5.x)
   - NSA/CISA Kubernetes Hardening Guidance

---

## Intelligence Architecture

### Hybrid AI Approach

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT INTELLIGENCE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Stage 1: LLM-Driven Discovery (LangGraph)                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │ • Uses LLM to interpret "get all namespaces"       │    │
│  │ • Dynamically calls kubectl_get tool               │    │
│  │ • Adapts to cluster responses                      │    │
│  │ • Handles ambiguity in requests                    │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Stage 2: Deterministic Resource Querying                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │ • Direct MCP API calls (no LLM)                    │    │
│  │ • Programmatic loops over namespaces/resources     │    │
│  │ • Structured data collection                       │    │
│  │ • Error handling for missing CRDs                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  Stage 3: Rule-Based Security Analysis                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │ • Python-based security checks                     │    │
│  │ • Deterministic risk scoring                       │    │
│  │ • Standards mapping (NIST, CIS, NSA/CISA)         │    │
│  │ • Contextual recommendations                       │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Why Hybrid?
- **LLM for Discovery** - Natural language understanding, flexible namespace query
- **Deterministic for Collection** - Fast, reliable, predictable resource queries
- **Rule-Based for Analysis** - Auditable, consistent security findings

### LLM Provider
- **LangGraph** framework for agent orchestration
- **Ollama** as default LLM backend (can use GPT-4, Claude, etc.)
- **LangChain MCP Adapters** for tool integration

---

## Tools & Access

### 1. Model Context Protocol (MCP) Kubernetes Server

**What it is:**
- REST API wrapper around kubectl
- Exposes `kubectl_get` tool to the agent
- Hosted at: `http://48.194.37.51:3001/mcp`

**Tool Signature:**
```python
kubectl_get(
    resourceType: str,      # e.g., "pods", "deployments", "services"
    namespace: str = None,  # Optional: omit for cluster-wide resources
    output: str = "json"    # Always JSON for parsing
)
```

**Example Calls:**
```bash
# Namespace-scoped
kubectl_get(resourceType="pods", namespace="default", output="json")
→ kubectl get pods -n default -o json

# Cluster-scoped
kubectl_get(resourceType="clusterroles", output="json")
→ kubectl get clusterroles -o json
```

### 2. Access Requirements

**Kubernetes RBAC Permissions (Read-Only)**

The agent requires a **ServiceAccount with ClusterRole** granting:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: security-auditor
rules:
  # Namespace-scoped resources
  - apiGroups: [""]
    resources:
      - pods
      - services
      - configmaps
    verbs: ["get", "list"]
  
  - apiGroups: ["apps"]
    resources:
      - deployments
      - daemonsets
      - statefulsets
    verbs: ["get", "list"]
  
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources:
      - rolebindings
      - clusterrolebindings
      - clusterroles
    verbs: ["get", "list"]
  
  - apiGroups: ["networking.k8s.io"]
    resources:
      - networkpolicies
      - ingresses
    verbs: ["get", "list"]
  
  # Istio resources (if present)
  - apiGroups: ["networking.istio.io"]
    resources:
      - virtualservices
      - destinationrules
      - gateways
    verbs: ["get", "list"]
  
  - apiGroups: ["security.istio.io"]
    resources:
      - peerauthentications
      - authorizationpolicies
    verbs: ["get", "list"]
  
  # Namespaces (cluster-scoped)
  - apiGroups: [""]
    resources:
      - namespaces
    verbs: ["get", "list"]
```

**Network Access:**
- Outbound HTTPS to MCP server (port 3001)
- No direct kubectl/kubeconfig access required
- Agent runs outside cluster, communicates via MCP API

**No Write Access:**
- Agent is **read-only** - cannot modify cluster state
- Cannot create, update, or delete resources
- Safe to run in production

### 3. Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Agent Framework** | LangGraph | Multi-stage orchestration |
| **LLM Backend** | Ollama (default) | Natural language understanding |
| **Tool Integration** | LangChain MCP Adapters | Connect LLM to kubectl |
| **K8s Access** | MCP Kubernetes Server | REST API for kubectl |
| **Security Analysis** | Python (deterministic) | Rule-based checks |
| **CLI Interface** | asyncio + argparse | Command-line execution |
| **UI Interface** | Streamlit | Web-based dashboard |

---

## How It Differs from OPA (Open Policy Admission)

### High-Level Comparison

| Aspect | **This Agent** | **OPA** |
|--------|----------------|---------|
| **Primary Purpose** | **Security Audit & Assessment** | **Policy Enforcement** |
| **When It Runs** | On-demand (manual trigger) | Real-time (admission control) |
| **Action** | **Reads** cluster state | **Blocks/Allows** API requests |
| **Deployment** | External CLI/UI tool | In-cluster admission webhook |
| **Scope** | Historical/current state analysis | Future resource creation/updates |
| **Outcome** | Reports with findings | Accept/Reject decisions |
| **Intelligence** | AI + rule-based analysis | Rego policy rules |

### Detailed Differences

#### 1. **Purpose & Timing**

**This Agent (Audit)**
```
User Runs Audit
     ↓
Query Existing Resources
     ↓
Analyze Security Posture
     ↓
Generate Report with Risks
     ↓
User Takes Action (manual)
```

**OPA (Enforcement)**
```
User Creates/Updates Resource
     ↓
K8s API Calls OPA Webhook
     ↓
OPA Evaluates Rego Policies
     ↓
Accept ✅ or Reject ❌
     ↓
Resource Allowed/Blocked (automatic)
```

#### 2. **Access Pattern**

| Aspect | This Agent | OPA |
|--------|-----------|-----|
| **Cluster Access** | Read-only GET operations | Webhook receives AdmissionReview |
| **Data Source** | kubectl list/get via MCP | API server admission request |
| **Write Operations** | ❌ No write access | ✅ Can mutate resources (via mutating webhook) |

#### 3. **Analysis Approach**

**This Agent**
- **Hybrid Intelligence**: LLM for discovery + Python rules for analysis
- **Contextual**: Considers namespace, workload type, Istio presence
- **Risk-Based**: HIGH/MEDIUM/LOW with compliance mapping
- **Comprehensive**: Cross-resource correlation (e.g., pods without NetworkPolicies)

**OPA**
- **Declarative Rego**: Policy-as-code rules
- **Single-Resource**: Evaluates one resource at a time
- **Binary**: Allow/Deny decisions
- **Lightweight**: Fast, low-latency admission control

#### 4. **Use Case Alignment**

**When to Use This Agent**
- 📊 **Periodic Security Audits** - Monthly/quarterly assessments
- 🔍 **Compliance Reporting** - NIST, CIS, NSA/CISA evidence
- 🚨 **Incident Response** - Assess blast radius of breach
- 📈 **Security Posture Tracking** - Trend analysis over time
- 🏗️ **Pre-Production Validation** - Audit before go-live
- 🔧 **Troubleshooting** - Why was policy violation missed?

**When to Use OPA**
- 🛡️ **Real-Time Policy Enforcement** - Block non-compliant resources
- ⚡ **Admission Control** - Prevent privilege escalation, enforce labels
- 🔒 **Zero Trust Enforcement** - Require mTLS, deny hostNetwork
- 🚫 **Preventive Controls** - Stop misconfiguration at creation
- 📝 **Policy-as-Code** - Version-controlled security rules
- 🤖 **Automated Remediation** - Mutate resources to compliance

#### 5. **Complementary Usage**

**Ideal Combined Workflow:**

```
1. OPA Enforces Policies (Real-Time)
   └─ Blocks pod with hostNetwork=true
   └─ Requires NetworkPolicies in labeled namespaces

2. This Agent Audits Compliance (Periodic)
   └─ Discovers 3 namespaces lacking NetworkPolicies
   └─ Reports OPA bypass via legacy resources
   └─ Identifies cluster-admin RBAC over-privilege
   └─ Checks mesh-wide mTLS enforcement

3. Security Team Acts
   └─ Tighten OPA policies based on audit findings
   └─ Remediate pre-existing resources not caught by OPA
```

**Why Both?**
- **OPA** = Preventive control (blocks future violations)
- **This Agent** = Detective control (finds existing violations + gaps in OPA coverage)

#### 6. **Example Scenario**

**Scenario: Pod Running as Root**

| Tool | What Happens |
|------|--------------|
| **OPA** | User tries to create pod with `runAsUser: 0` → **OPA blocks creation** → Pod never exists |
| **This Agent** | Audit discovers pod created before OPA was deployed → **Agent reports finding** → Security team manually remediates |

**OPA can't catch:**
- Resources created before OPA was deployed
- Resources in namespaces excluded from OPA
- Cluster-wide policies OPA doesn't evaluate (e.g., missing mesh-wide mTLS)
- Correlation issues (pods without NetworkPolicies - both exist, but relationship is wrong)

**This Agent can't prevent:**
- Future misconfigurations (runs after-the-fact)
- Real-time violations (no admission control)

---

## "But OPA Blocks Non-Compliant Resources... Why Do I Need This?"

### Critical Reality: OPA Doesn't See Everything

**Your assumption:** "If OPA blocks bad deployments, my cluster must be secure"  
**The reality:** OPA has blind spots this agent exposes

### 5 Scenarios Where OPA Won't Help (But This Agent Will)

#### 1. **Resources Created Before OPA Was Deployed**

```
Timeline:
  2023: Cluster created, 50 pods deployed with hostNetwork=true, runAsRoot=0
  2024: OPA deployed with strict security policies
  2025: This agent audits cluster

OPA's view:     "Blocking all new privileged pods ✅"
This agent:     "🔴 FOUND: 23 privileged pods still running from 2023"
                "🔴 FOUND: 15 pods running as root from 2023"
                "💡 These pre-date your OPA policies - OPA never saw them"
```

**Real Impact:** Your cluster has 2+ years of legacy workloads OPA never validated.

---

#### 2. **OPA Exemptions & Bypasses**

```yaml
# Common OPA configuration
apiVersion: config.gatekeeper.sh/v1alpha1
kind: Config
metadata:
  name: config
spec:
  match:
    - excludedNamespaces: ["kube-system", "istio-system", "monitoring"]
    - processes: ["audit", "webhook"]
```

**What happens:**
- **OPA:** Allows deployments in exempted namespaces
- **This Agent:** Audits ALL namespaces including exemptions

```
This agent finds:
🔴 HIGH RISK: kube-system has 12 pods without NetworkPolicies
🔴 HIGH RISK: istio-system has 3 privileged containers
💡 These namespaces are excluded from OPA validation
```

**Real Impact:** Exempted namespaces are blind spots. Attackers target kube-system.

---

#### 3. **OPA Policy Gaps**

**Your OPA policies might enforce:**
- ✅ No privileged containers
- ✅ Must have resource limits
- ✅ Image pull policy = Always

**Your OPA policies might NOT enforce:**
- ❌ NetworkPolicies required per namespace
- ❌ TLS required on Ingresses
- ❌ AuthorizationPolicies in service mesh
- ❌ ClusterRoleBindings can't grant cluster-admin

```
This agent discovers:
🔴 HIGH RISK: 8/22 namespaces have workloads but NO NetworkPolicies
🟠 MEDIUM RISK: 5 Ingresses missing TLS
🔴 HIGH RISK: 3 ClusterRoleBindings grant cluster-admin

💡 ACTIONABLE: "Create OPA policies for these findings"
```

**Real Impact:** OPA only enforces what you told it to. This agent finds what you forgot.

---

#### 4. **Cluster-Wide Policies OPA Can't Validate**

**OPA limitation:** Validates one resource per admission request

**This agent checks:**

```
Cluster-Wide Security Posture:
🔴 HIGH RISK: No PeerAuthentication found - mTLS NOT enforced mesh-wide
   └─ OPA can validate individual pod specs, but can't check if PeerAuth exists
   
🟠 MEDIUM RISK: No AuthorizationPolicy found - zero-trust NOT implemented
   └─ OPA can't correlate "Does cluster have AuthZ policies?"
   
🔴 HIGH RISK: ClusterRoleBinding 'cluster-admins' grants cluster-admin to 15 users
   └─ OPA allowed the binding creation, but can't audit if it's appropriate
```

**Real Impact:** OPA operates at resource-level. This agent operates at cluster-level.

---

#### 5. **Drift & Configuration Changes Over Time**

```
Week 1: Developer deploys app with NetworkPolicy → OPA allows (compliant)
Week 2: Developer deletes NetworkPolicy to debug connectivity
        └─ kubectl delete networkpolicy app-netpol
        └─ OPA does NOT block this (deletion uses different admission path)

Week 3: Developer forgets to recreate NetworkPolicy
        └─ App now runs WITHOUT network segmentation
        └─ OPA never blocks (no new admission request)

Month 3: This agent runs audit
         └─ 🔴 "Namespace 'production' has 23 pods but NO NetworkPolicies"
```

**Real Impact:** Compliance drift happens. OPA only sees creates/updates, not deletions or drift.

---

### Real-World Example: Production Incident

**Company:** FinTech (PCI-DSS regulated)  
**Assumption:** "We have OPA, we're compliant"

**What Happened:**

```
1️⃣ 2022: OPA deployed, blocks privileged containers
2️⃣ 2023: Auditor asks: "Prove no privileged containers in production"
3️⃣ Security team shows OPA policies
4️⃣ Auditor says: "Show me actual cluster state, not policies"
5️⃣ Manual kubectl check finds: 8 privileged pods in 'payments' namespace
   └─ Created in 2021 before OPA
   └─ Namespace exempted from OPA for "operational reasons"
6️⃣ Failed PCI-DSS audit
```

**If they ran this agent:**
```
Monthly audit would have shown:
🔴 HIGH RISK: 8 privileged containers in 'payments' namespace
   [Created: 2021-03-15 - Pre-dates OPA deployment]
   [PCI-DSS 2.2.4, NIST CM-7]
💡 Remediate before next audit
```

---

### How This Agent Complements OPA (Not Replaces)

```
┌─────────────────────────────────────────────────────────────┐
│                    Security Strategy                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  OPA (Prevention)              This Agent (Detection)        │
│  ├─ Block future violations    ├─ Find existing violations  │
│  ├─ Real-time enforcement      ├─ Periodic audit (monthly)  │
│  ├─ Admission control          ├─ Comprehensive scan        │
│  └─ "Firewall"                 └─ "Vulnerability scanner"   │
│                                                              │
│  Example Flow:                                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Month 1: Run Agent → Find 23 policy violations      │    │
│  │ Month 1: Deploy OPA → Block future violations       │    │
│  │ Month 1: Fix 23 existing issues manually            │    │
│  │ Month 2: Run Agent → Verify: 0 violations ✅        │    │
│  │ Month 3: Run Agent → Detect: 2 new (OPA bypass)     │    │
│  │ Month 3: Investigate & fix bypass                   │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

### What This Agent Tells You (That OPA Can't)

| Question | OPA's Answer | This Agent's Answer |
|----------|--------------|---------------------|
| **"Are we compliant?"** | "My policies block violations" | "✅ 14/15 namespaces compliant<br/>🔴 1 namespace needs remediation" |
| **"What's our risk?"** | "I reject non-compliant deploys" | "🔴 3 HIGH, 🟠 7 MEDIUM, 🟡 2 LOW<br/>Prioritized by impact" |
| **"Prove compliance"** | "Here's my policy code" | "Evidence report: 268 queries<br/>Mapped to NIST/CIS/NSA standards" |
| **"What do I fix first?"** | "I just block things" | "Fix 'payments' namespace first<br/>(PCI-DSS critical)" |
| **"Is OPA working?"** | "I think so?" | "Found 8 violations OPA should've blocked<br/>Check exemptions/bypasses" |
| **"Did we improve?"** | "No historical data" | "Jan: 10 issues → Mar: 3 issues<br/>70% improvement ✅" |

---

### Bottom Line: You Need Both

**OPA is essential** - prevents new problems  
**This agent is essential** - finds existing problems OPA missed

```
Security Without This Agent:
  └─ OPA blocks new violations
  └─ Legacy violations remain hidden
  └─ Policy gaps undiscovered
  └─ Compliance audits fail
  └─ "We thought OPA made us secure" ❌

Security With Both:
  └─ OPA blocks new violations ✅
  └─ Agent finds legacy violations ✅
  └─ Agent exposes policy gaps ✅
  └─ Compliance evidence ready ✅
  └─ "We have comprehensive security" ✅
```

**Question to ask:** *"If OPA is deployed, why do vulnerabilities still exist in our cluster?"*  
**Answer:** Because OPA can't audit the past. This agent can.

---

## Can I Use This to Scan Manifests in My Repo (Pre-Deployment)?

### Short Answer: Not Currently, But You Should

**Current Capability:**
- ❌ This agent scans **live cluster state** via kubectl
- ❌ Cannot directly scan YAML files in Git repos
- ❌ Not designed for CI/CD pipeline integration

**What You're Asking For:**
- ✅ Scan Kubernetes YAML manifests **before** git push
- ✅ Validate deployments **before** they reach the cluster
- ✅ CI/CD pipeline security gates

### Why You Need BOTH Approaches

```
┌─────────────────────────────────────────────────────────────────┐
│               Complete Security Coverage                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Pre-Deployment (Repo Scanning)    Post-Deployment (This Agent) │
│  ├─ Scan YAML manifests            ├─ Scan live cluster state  │
│  ├─ Catch issues in PR review      ├─ Find runtime drift       │
│  ├─ Block bad commits              ├─ Audit exemptions         │
│  ├─ Developer feedback (fast)      ├─ Compliance evidence      │
│  └─ "Left shift" security          └─ "Runtime validation"     │
│                                                                  │
│  Example:                                                        │
│  1️⃣ Developer commits deployment.yaml with privileged: true     │
│  2️⃣ CI/CD scanner catches it → PR blocked ❌                    │
│  3️⃣ Developer fixes, commits again                              │
│  4️⃣ CI/CD scanner passes → PR merged ✅                         │
│  5️⃣ OPA validates at admission → Deployed ✅                    │
│  6️⃣ This agent audits monthly → Confirms compliance ✅          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Tools for Pre-Deployment Scanning

| Tool | Purpose | Integration |
|------|---------|-------------|
| **Kyverno CLI** | Validate manifests against policies | `kyverno apply policy.yaml --resource deployment.yaml` |
| **Conftest** | OPA Rego for manifest testing | `conftest test deployment.yaml` |
| **Datree** | Policy engine for K8s configs | `datree test deployment.yaml` |
| **Kubesec** | Security risk analysis | `kubesec scan deployment.yaml` |
| **Trivy** | Misconfiguration scanning | `trivy config .` |
| **Checkov** | IaC security scanning | `checkov -d ./k8s` |

### Recommended CI/CD Pipeline

```yaml
# .github/workflows/k8s-security.yml
name: Kubernetes Security

on: [pull_request]

jobs:
  pre-deployment-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      # Stage 1: Scan manifests in repo
      - name: Scan with Kyverno
        run: |
          kyverno apply policies/ --resource k8s/
      
      - name: Scan with Trivy
        run: |
          trivy config k8s/ --severity HIGH,CRITICAL
      
      - name: Scan with Datree
        run: |
          datree test k8s/*.yaml
      
      # Stage 2: Deploy to staging (if scans pass)
      - name: Deploy to staging
        run: |
          kubectl apply -f k8s/ --dry-run=server
      
      # Stage 3: Validate staging with this agent
      - name: Run Comprehensive Audit
        run: |
          python -m src.langgraphagenticai.main --no-ui comprehensive_auditor
      
      # Stage 4: Parse audit results
      - name: Check for HIGH RISK findings
        run: |
          if grep -q "HIGH RISK" audit_output.txt; then
            echo "HIGH RISK findings detected - deployment blocked"
            exit 1
          fi
```

### What Each Layer Catches

```
Layer 1: Repo Scanning (Kyverno/Trivy)
├─ Syntax errors in YAML
├─ Missing required fields
├─ Privileged containers in manifest
├─ Missing resource limits
└─ Image vulnerabilities

Layer 2: OPA Admission Control
├─ Runtime policy enforcement
├─ Validates actual deployment request
├─ Blocks non-compliant resources
└─ Can mutate resources (add defaults)

Layer 3: This Agent (Runtime Audit)
├─ Validates ACTUAL cluster state
├─ Finds resources that bypassed OPA
├─ Detects configuration drift
├─ Cross-resource correlation
└─ Compliance evidence

Example of what each layer misses:
┌────────────────────────────────────────────────────┐
│ Issue: Pod with hostNetwork=true                   │
├────────────────────────────────────────────────────┤
│ Repo Scanner:  ✅ CATCHES (if policy configured)   │
│ OPA:           ✅ CATCHES (if policy configured)   │
│ This Agent:    ✅ CATCHES (always)                 │
├────────────────────────────────────────────────────┤
│ Issue: NetworkPolicy deleted after deployment      │
├────────────────────────────────────────────────────┤
│ Repo Scanner:  ❌ MISSES (only scans manifests)    │
│ OPA:           ❌ MISSES (doesn't block deletions) │
│ This Agent:    ✅ CATCHES (audits actual state)    │
├────────────────────────────────────────────────────┤
│ Issue: Resource created before policies deployed   │
├────────────────────────────────────────────────────┤
│ Repo Scanner:  ❌ MISSES (not in current PR)       │
│ OPA:           ❌ MISSES (created before OPA)      │
│ This Agent:    ✅ CATCHES (audits all resources)   │
└────────────────────────────────────────────────────┘
```

### Could This Agent Be Adapted for Repo Scanning?

**Yes, But Not Recommended** - Here's why:

**Technical Feasibility:**
```python
# Hypothetical modification
async def scan_yaml_files(directory: str):
    """Scan YAML manifests instead of live cluster"""
    for yaml_file in Path(directory).glob("**/*.yaml"):
        manifest = yaml.safe_load(yaml_file.read_text())
        # Apply same security checks as live cluster
        check_security_context(manifest)
        check_network_policies(manifest)
        # But... can't do cross-resource correlation!
```

**Limitations:**
- ❌ Can't validate cluster-wide policies (no PeerAuthentication in repo)
- ❌ Can't correlate across resources (are there NetworkPolicies for this pod?)
- ❌ Can't check RBAC relationships (ClusterRoleBindings not in app repo)
- ❌ Can't detect drift (repo ≠ actual cluster state)

**Better Approach:**
Use **purpose-built tools** for repo scanning, keep this agent for runtime auditing.

### Recommended Architecture

```
┌─────────────────────────────────────────────────────┐
│                Git Repository                        │
│  ├─ k8s/deployments/                                │
│  ├─ k8s/services/                                   │
│  └─ .github/workflows/security.yml                  │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│            CI/CD Pipeline (GitHub Actions)           │
│  ├─ Kyverno: Validate manifests                    │
│  ├─ Trivy: Scan for misconfigs                     │
│  ├─ Kubesec: Risk analysis                         │
│  └─ If pass → Deploy to staging                    │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│            Staging Cluster                           │
│  ├─ OPA validates admission                         │
│  └─ This Agent runs audit (post-deploy)             │
└──────────────┬──────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────┐
│            Production Cluster                        │
│  ├─ OPA validates admission                         │
│  └─ This Agent runs monthly audit                   │
└─────────────────────────────────────────────────────┘
```

### Quick Start: Add Repo Scanning Today

**Option 1: Kyverno CLI (Recommended)**
```bash
# Install
brew install kyverno

# Create policy
cat <<EOF > require-non-root.yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-non-root
spec:
  validationFailureAction: enforce
  rules:
  - name: check-runAsNonRoot
    match:
      resources:
        kinds:
        - Pod
    validate:
      message: "Pods must run as non-root"
      pattern:
        spec:
          securityContext:
            runAsNonRoot: true
EOF

# Scan your repo
kyverno apply require-non-root.yaml --resource k8s/
```

**Option 2: Trivy (Easiest)**
```bash
# Install
brew install trivy

# Scan repo
trivy config ./k8s --severity HIGH,CRITICAL

# Example output:
# deployment.yaml (kubernetes)
# ════════════════════════════════════════
# Tests: 28 (SUCCESSES: 24, FAILURES: 4)
# Failures: 4 (HIGH: 2, CRITICAL: 2)
#
# HIGH: Container 'app' runs as root
# ──────────────────────────────────────
# Set securityContext.runAsNonRoot: true
```

**Option 3: Conftest (Most Flexible)**
```bash
# Install
brew install conftest

# Write Rego policy
cat <<EOF > policy.rego
package main

deny[msg] {
  input.kind == "Deployment"
  not input.spec.template.spec.securityContext.runAsNonRoot
  msg = "Deployments must run as non-root"
}
EOF

# Test manifests
conftest test k8s/*.yaml
```

### Integration Example

```yaml
# .github/workflows/security.yml
name: Security Checks

on:
  pull_request:
    paths:
      - 'k8s/**'

jobs:
  scan-manifests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'config'
          scan-ref: 'k8s/'
          severity: 'HIGH,CRITICAL'
          exit-code: '1'  # Fail PR if issues found
      
      - name: Run Kyverno
        uses: nirmata/action-kyverno@main
        with:
          policies: policies/
          resources: k8s/
      
      - name: Comment Results on PR
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '✅ Security scans passed!'
            })
```

### Summary

**For Repository Scanning:**
- ✅ Use Kyverno CLI, Trivy, or Conftest
- ✅ Integrate into CI/CD (GitHub Actions, GitLab CI)
- ✅ Block PRs with security issues

**For Runtime Auditing:**
- ✅ Use this agent (comprehensive cluster audit)
- ✅ Run monthly/quarterly for compliance
- ✅ Validates actual state vs. desired state

**Best Practice:**
```
Pre-commit hooks → Repo scanning → CI/CD gates → OPA admission → This agent audit
     ↓                  ↓              ↓              ↓                ↓
   Catch           Catch early    Catch before   Catch at      Catch everything
   obvious         in PR review   staging        runtime       else + compliance
```

You need **all layers** for defense in depth. This agent is the final validation layer.

---

## Why Use This Agent? (Advantages Over OPA)

### Not "Better" - Different Purpose, Complementary Tools

**Critical Understanding:** This agent doesn't replace OPA - they solve different problems. However, there are scenarios where this agent provides capabilities OPA **cannot** offer.

### 10 Things This Agent Does That OPA Can't

#### 1. **Audit Pre-Existing Resources**

**OPA Limitation:**
- Only evaluates resources at creation/update time
- Cannot see resources created before OPA was deployed
- Cannot audit legacy workloads

**This Agent:**
```
✅ Discovers all 53 existing pods across 22 namespaces
✅ Identifies 12 pods created before OPA was installed running as root
✅ Reports 8 namespaces with workloads but no NetworkPolicies
```

**Real-World Impact:** Most clusters have years of legacy resources. OPA can't audit them.

---

#### 2. **Cross-Resource Correlation Analysis**

**OPA Limitation:**
- Evaluates one resource at a time (single AdmissionReview)
- Cannot correlate: "Does this pod's namespace have NetworkPolicies?"
- Cannot answer: "Are all LoadBalancer services behind NetworkPolicies?"

**This Agent:**
```python
# Example correlation this agent performs:
if namespace_has_pods AND namespace_lacks_networkpolicies:
    HIGH_RISK: "10 workloads exposed without network segmentation"

if service_type == "LoadBalancer" AND no_networkpolicy_in_namespace:
    MEDIUM_RISK: "External service without network restrictions"
```

**Real-World Impact:** Most security issues involve relationships between resources, not single resources in isolation.

---

#### 3. **Cluster-Wide Policy Assessment**

**OPA Limitation:**
- Operates at namespace or resource level
- Hard to enforce "cluster must have PeerAuthentication with STRICT mode"
- Cannot validate: "Is mTLS enabled mesh-wide?"

**This Agent:**
```
✅ Checks if ANY PeerAuthentication exists cluster-wide
✅ Validates mTLS mode is STRICT (not PERMISSIVE)
✅ Detects missing AuthorizationPolicy for zero-trust
✅ Identifies cluster-admin RBAC over-privilege
```

**Real-World Impact:** Mesh-wide security posture is invisible to OPA's admission-control view.

---

#### 4. **Gap Analysis & OPA Coverage Testing**

**OPA Limitation:**
- Assumes policies are complete
- Cannot self-audit for gaps
- No visibility into what policies are missing

**This Agent:**
```
Example Output:
🔴 HIGH RISK: Namespace 'payments' has 15 pods but NO NetworkPolicies
💡 RECOMMENDATION: Add OPA policy to require NetworkPolicies in production namespaces

🟠 MEDIUM RISK: 3 ingresses missing TLS across 2 namespaces
💡 RECOMMENDATION: Create OPA policy to enforce spec.tls on all Ingresses
```

**Real-World Impact:** Tells you **where your OPA policies are incomplete**.

---

#### 5. **Compliance Reporting & Evidence Collection**

**OPA Limitation:**
- No built-in reporting
- Cannot generate audit trails for compliance
- No mapping to NIST/CIS/ISO standards

**This Agent:**
```
✅ Per-namespace security posture reports
✅ Risk-scored findings (HIGH/MEDIUM/LOW)
✅ Mapped to standards:
   - NIST AC-3 (Access Control)
   - CIS 5.x (Network Policies)
   - NSA/CISA Kubernetes Hardening Guide
✅ Exportable reports for auditors
```

**Real-World Impact:** SOC 2, PCI-DSS, FedRAMP audits require evidence of security posture, not just policies.

---

#### 6. **Istio Service Mesh Validation**

**OPA Limitation:**
- Can validate individual VirtualService syntax
- Cannot validate mesh-wide mTLS enforcement
- Cannot check PeerAuthentication STRICT mode at mesh level

**This Agent:**
```
✅ Checks PeerAuthentication exists and mode=STRICT
✅ Validates AuthorizationPolicy for zero-trust
✅ Detects DestinationRules without TLS settings
✅ Identifies VirtualServices with wildcard hosts
✅ Checks Gateway TLS configuration
```

**Real-World Impact:** Mesh security requires cluster-wide view, not per-resource admission control.

---

#### 7. **Security Context Deep Analysis**

**OPA Limitation:**
- Can block `privileged: true` at creation
- Cannot audit multiple securityContext fields holistically
- No risk scoring across security dimensions

**This Agent:**
```
Analyzes per-pod:
✅ privileged containers        → HIGH RISK
✅ allowPrivilegeEscalation     → MEDIUM RISK
✅ runAsUser: 0 (root)          → MEDIUM RISK
✅ hostNetwork: true            → MEDIUM RISK
✅ image tag: latest            → LOW RISK

Aggregate risk scoring:
"Namespace 'default' has 5 HIGH RISK pods (privileged containers)"
```

**Real-World Impact:** Security context is complex - this agent provides holistic risk assessment OPA cannot.

---

#### 8. **Trend Analysis & Change Detection**

**OPA Limitation:**
- No historical data
- Cannot track: "Did security posture improve this quarter?"
- No baseline comparison

**This Agent (Run Monthly):**
```
January:  10 namespaces without NetworkPolicies
February: 7 namespaces without NetworkPolicies  ✅ 30% improvement
March:    3 namespaces without NetworkPolicies  ✅ 70% improvement

January:  15 pods running as root
February: 8 pods running as root               ✅ Progress
```

**Real-World Impact:** Security teams need metrics to prove improvement. OPA has no memory.

---

#### 9. **Non-Disruptive Auditing**

**OPA Challenge:**
- Admission control can block legitimate deployments
- Policy updates require careful testing
- False positives disrupt developer workflows

**This Agent:**
```
✅ Read-only access - cannot break anything
✅ Safe to run in production anytime
✅ Findings are advisory, not blocking
✅ Developers can review before enforcing
```

**Real-World Impact:** Can audit production without risk. OPA policy changes can cause outages.

---

#### 10. **AI-Powered Discovery & Contextual Recommendations**

**OPA Limitation:**
- Rego policies are static rules
- No natural language understanding
- No contextual recommendations

**This Agent:**
```
LLM-driven:
✅ "Query all namespaces" → Agent interprets and executes
✅ Contextual recommendations:
   "Namespace 'payments' (PCI-DSS critical) lacks NetworkPolicies"
   vs.
   "Namespace 'dev' (non-production) lacks NetworkPolicies"

AI can prioritize based on:
- Namespace criticality (prod vs dev)
- Workload type (databases vs frontends)
- Compliance requirements (PCI, HIPAA, etc.)
```

**Real-World Impact:** Context-aware risk assessment, not just binary pass/fail.

---

### Summary: When This Agent Shines

| Scenario | This Agent | OPA |
|----------|-----------|-----|
| **Audit existing resources** | ✅ Perfect | ❌ Cannot |
| **Find policy gaps** | ✅ Identifies what to add to OPA | ❌ Assumes complete |
| **Compliance reporting** | ✅ NIST/CIS mapped reports | ❌ No reporting |
| **Cluster-wide validation** | ✅ Mesh mTLS, RBAC posture | ⚠️ Limited visibility |
| **Cross-resource analysis** | ✅ NetworkPolicy coverage per namespace | ❌ Single resource only |
| **Historical trends** | ✅ Run monthly for metrics | ❌ No memory |
| **Non-disruptive** | ✅ Read-only, safe | ⚠️ Admission control can block |
| **Risk scoring** | ✅ HIGH/MEDIUM/LOW with context | ❌ Binary allow/deny |
| **Real-time enforcement** | ❌ No admission control | ✅ Perfect |
| **Prevent future violations** | ❌ Audit only | ✅ Perfect |

### The Ideal Workflow

```
1️⃣ Run This Agent → Identify 10 security gaps
   Example findings:
   - 8 namespaces lack NetworkPolicies
   - 5 pods running privileged
   - No mesh-wide mTLS

2️⃣ Create/Update OPA Policies → Enforce rules for future
   - Require NetworkPolicies in labeled namespaces
   - Block privileged containers
   - Require pod security standards

3️⃣ Manually Remediate Existing Issues
   - Add NetworkPolicies to 8 namespaces
   - Recreate 5 pods without privilege
   - Deploy PeerAuthentication with STRICT mode

4️⃣ Run This Agent Again → Verify compliance
   ✅ All namespaces now have NetworkPolicies
   ✅ No privileged pods remaining
   ✅ mTLS enforced

5️⃣ Ongoing: OPA prevents regressions, This Agent audits quarterly
```

---

### Real-World Example: Why You Need Both

**Scenario: PCI-DSS Compliance Audit**

**Auditor Question:** *"Prove that all production workloads have network segmentation"*

**OPA's Answer:**
```
"Our policy blocks new pods in 'prod-*' namespaces without NetworkPolicies"
└─ Shows policy code
```

**Problem:**
- Doesn't prove existing pods are compliant
- Doesn't show actual namespace coverage
- Doesn't map to PCI-DSS requirements

**This Agent's Answer:**
```
📊 Audit Results (2026-01-26):
✅ 15 production namespaces analyzed
✅ 14/15 have NetworkPolicies (93% coverage)
🔴 HIGH RISK: Namespace 'prod-legacy' has 23 pods WITHOUT NetworkPolicies
   [Mapped to: PCI-DSS 1.2.1, NIST SC-7, CIS 5.3.2]

💡 RECOMMENDATION: Deploy default-deny NetworkPolicy to prod-legacy

Historical Trend:
  Dec 2025: 5/15 namespaces compliant (33%)
  Jan 2026: 14/15 namespaces compliant (93%)  ← Show this to auditor
```

**Which answer satisfies the auditor?** The agent's comprehensive, evidence-based report.

---

### Bottom Line

**This Agent is "Better" When:**
- You need to **audit existing state** (OPA can't see the past)
- You need **compliance evidence** (OPA has no reporting)
- You need **cluster-wide visibility** (OPA sees one resource at a time)
- You need to **find OPA policy gaps** (OPA assumes it's complete)
- You need **risk-based prioritization** (OPA is binary allow/deny)

**OPA is "Better" When:**
- You need to **prevent future violations** (Agent can't block)
- You need **real-time enforcement** (Agent runs on-demand)
- You need **automated remediation** (OPA can mutate resources)
- You need **sub-second decisions** (Agent takes minutes)

**Use Both:**
- OPA = Your firewall (preventive control)
- This Agent = Your security scanner (detective control)

Every secure cluster needs **both prevention AND detection**.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION                               │
│  ┌────────────────────┐              ┌────────────────────┐          │
│  │  CLI Command       │              │  Streamlit UI      │          │
│  │  $ python -m ...   │              │  http://localhost  │          │
│  │  comprehensive_... │              │  :8501             │          │
│  └────────────────────┘              └────────────────────┘          │
└───────────────────┬──────────────────────────┬───────────────────────┘
                    │                          │
                    ▼                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     CLI/UI ORCHESTRATOR                               │
│  ┌─────────────────────────────────────────────────────────┐         │
│  │  src/langgraphagenticai/core/cli_orchestrator.py        │         │
│  │  src/langgraphagenticai/ui/streamlitui/display_result.py│         │
│  └─────────────────────────────────────────────────────────┘         │
└───────────────────┬──────────────────────────┬───────────────────────┘
                    │                          │
         ┌──────────┴──────────┐               │
         │ Stage 1: Discovery  │               │ Stage 2: Direct Queries
         │ (LangGraph + LLM)   │               │ (MCP Client)
         └──────────┬──────────┘               │
                    │                          │
                    ▼                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                   MODEL CONTEXT PROTOCOL (MCP)                        │
│  ┌─────────────────────────────────────────────────────────┐         │
│  │  MCP Kubernetes Server                                   │         │
│  │  http://48.194.37.51:3001/mcp                           │         │
│  │                                                          │         │
│  │  Tools:                                                  │         │
│  │  - kubectl_get(resourceType, namespace, output)         │         │
│  └─────────────────────────────────────────────────────────┘         │
└───────────────────┬──────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     KUBERNETES CLUSTER                                │
│  ┌─────────────────────────────────────────────────────────┐         │
│  │  Namespaces: default, kube-system, argocd, ...         │         │
│  │  Resources: pods, deployments, services, ...            │         │
│  │  Policies: NetworkPolicies, RBAC, PeerAuth, ...        │         │
│  └─────────────────────────────────────────────────────────┘         │
└───────────────────┬──────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    SECURITY ANALYSIS ENGINE                           │
│  ┌─────────────────────────────────────────────────────────┐         │
│  │  Rule-Based Checks:                                      │         │
│  │  - NetworkPolicy coverage                                │         │
│  │  - Workload security contexts                            │         │
│  │  - Service/Ingress exposure                              │         │
│  │  - Mesh policy validation                                │         │
│  │  - RBAC over-privilege detection                         │         │
│  └─────────────────────────────────────────────────────────┘         │
└───────────────────┬──────────────────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       OUTPUT / REPORTING                              │
│  ┌─────────────────────────────────────────────────────────┐         │
│  │  Per-Namespace Findings:                                 │         │
│  │  🔴 HIGH RISK   🟠 MEDIUM RISK   🟡 LOW RISK            │         │
│  │  💡 RECOMMENDATIONS                                      │         │
│  │                                                          │         │
│  │  Cluster-Wide Findings:                                  │         │
│  │  mTLS, AuthZ, RBAC issues                               │         │
│  │                                                          │         │
│  │  Compliance Mapping:                                     │         │
│  │  NIST AC-3, CIS 5.x, NSA/CISA                           │         │
│  └─────────────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Key Takeaways

✅ **What This Agent Does**
- AI-powered comprehensive Kubernetes security auditing
- Per-namespace risk analysis with compliance mapping
- Read-only, safe to run in production

✅ **Intelligence**
- Hybrid: LLM discovery + deterministic queries + rule-based analysis
- LangGraph orchestration, Ollama LLM backend

✅ **Tools**
- MCP Kubernetes Server (kubectl_get API)
- 16 resource types queried (12 per namespace + 4 cluster-wide)

✅ **Access**
- Read-only ClusterRole (list/get on pods, services, policies, RBAC, etc.)
- No write permissions, no admission control

✅ **vs. OPA**
- **Detective** control (audit existing state) vs. **Preventive** (enforce future state)
- **Complementary**: OPA blocks violations, this agent finds gaps/pre-existing issues
- **Scope**: Comprehensive cluster-wide analysis vs. single-resource admission decisions

---

## Quick Reference

| Question | Answer |
|----------|--------|
| **Can it modify my cluster?** | ❌ No - read-only access only |
| **Does it need in-cluster deployment?** | ❌ No - runs externally via MCP |
| **Can it replace OPA?** | ❌ No - different purposes, use both |
| **Does it require Istio?** | ⚠️ Optional - checks Istio if installed |
| **How long does an audit take?** | ~2-5 minutes for 22 namespaces |
| **Can I customize checks?** | ✅ Yes - Python-based rules |
| **Does it support policy-as-code?** | ⚠️ Partial - checks against hardcoded standards |

