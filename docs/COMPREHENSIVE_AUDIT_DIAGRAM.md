# Comprehensive Security Audit - Architecture Diagram

## High-Level Flow

```mermaid
graph TD
    A["🚀 START: run_comprehensive_auditor"] --> B["STAGE 1: Namespace Discovery"]
    
    B --> B1["Initialize LLM Graph"]
    B1 --> B2["Send Query: 'Get all namespaces'"]
    B2 --> B3["LLM calls kubectl_get tool"]
    B3 --> B4["Parse response → Extract namespace list"]
    B4 --> B5["✅ Found 22 namespaces"]
    
    B5 --> C["STAGE 2: Resource Inventory Query"]
    
    C --> C1["Initialize MCP Client"]
    C1 --> C2["For each namespace..."]
    C2 --> C3["Query 12 resource types per namespace"]
    C3 --> C4["Gather: pods, deployments, services, ingresses, etc."]
    
    C4 --> C5["Query cluster-wide resources"]
    C5 --> C6["Gather: clusterroles, clusterrolebindings, peerauthentication, authorizationpolicy"]
    C6 --> C7["✅ Executed 268 total queries"]
    
    C7 --> D["PER-NAMESPACE ANALYSIS"]
    D --> D1["For each namespace..."]
    D1 --> D2["Analyze NetworkPolicy coverage"]
    D2 --> D3["Check Ingress/Service exposure"]
    D3 --> D4["Inspect workload security contexts"]
    D4 --> D5["Detect Istio misconfigs"]
    D5 --> D6["Collect findings"]
    D6 --> D7["Display per-namespace report"]
    
    D7 --> E["CLUSTER-WIDE ANALYSIS"]
    E --> E1["Check mTLS/PeerAuthentication"]
    E1 --> E2["Check AuthorizationPolicy"]
    E2 --> E3["Check RBAC (cluster-admin)"]
    E3 --> E4["Collect cluster findings"]
    E4 --> E5["Display cluster report"]
    
    E5 --> F["✅ COMPREHENSIVE AUDIT COMPLETE"]
    
    style A fill:#90EE90
    style B fill:#87CEEB
    style C fill:#87CEEB
    style D fill:#FFB6C1
    style E fill:#FFB6C1
    style F fill:#90EE90
```

## Detailed Query Flow

```mermaid
graph LR
    MCP["MCP Kubernetes Server<br/>(http://48.194.37.51:3001/mcp)"]
    
    NS1["Namespace 1<br/>default"]
    NS2["Namespace 2<br/>kube-system"]
    NSN["Namespace N<br/>weaviate"]
    
    RT1["pods"]
    RT2["deployments"]
    RT3["services"]
    RTN["configmaps"]
    
    CRTS["Cluster Resources<br/>clusterroles<br/>clusterrolebindings<br/>peerauthentication<br/>authorizationpolicy"]
    
    MCP --> NS1
    MCP --> NS2
    MCP --> NSN
    
    NS1 --> RT1
    NS1 --> RT2
    NS1 --> RT3
    NS1 --> RTN
    
    NS2 --> RT1
    NS2 --> RT2
    NS2 --> RT3
    NS2 --> RTN
    
    NSN --> RT1
    NSN --> RT2
    NSN --> RT3
    NSN --> RTN
    
    MCP --> CRTS
    
    style MCP fill:#FFE4B5
    style NS1 fill:#B0E0E6
    style NS2 fill:#B0E0E6
    style NSN fill:#B0E0E6
    style RT1 fill:#DDA0DD
    style RT2 fill:#DDA0DD
    style RT3 fill:#DDA0DD
    style RTN fill:#DDA0DD
    style CRTS fill:#F0E68C
```

## Per-Namespace Security Analysis

```mermaid
graph TD
    NS["Namespace Analysis<br/>(e.g., 'default')"]
    
    NS --> NP["NetworkPolicy Check"]
    NP --> NP1["Pods found?"]
    NP1 -->|Yes| NP2["NetworkPolicies found?"]
    NP2 -->|No| NP3["🔴 HIGH RISK:<br/>Workloads without segmentation"]
    NP2 -->|Yes| NP4["✅ Segmentation OK"]
    
    NS --> ING["Ingress/Service Check"]
    ING --> ING1["LoadBalancer/NodePort?"]
    ING1 -->|Yes| ING2["TLS enabled?"]
    ING2 -->|No| ING3["🟠 MEDIUM RISK:<br/>Exposed without TLS"]
    ING2 -->|Yes| ING4["✅ TLS OK"]
    
    NS --> WL["Workload Security Check"]
    WL --> WL1["Privileged containers?"]
    WL1 -->|Yes| WL2["🔴 HIGH RISK:<br/>Privilege escalation"]
    WL1 -->|No| WL3["Runs as root?"]
    WL3 -->|Yes| WL4["🟠 MEDIUM RISK:<br/>Root user"]
    WL3 -->|No| WL5["✅ Security OK"]
    
    NS --> IST["Istio Check (if present)"]
    IST --> IST1["VirtualServices OK?"]
    IST1 -->|No| IST2["🟠 MEDIUM RISK:<br/>Misconfigured routing"]
    IST1 -->|Yes| IST3["✅ Istio OK"]
    
    NP3 --> REC["Recommendations"]
    ING3 --> REC
    WL2 --> REC
    IST2 --> REC
    REC --> REPORT["Display Findings<br/>per namespace"]
    
    style NS fill:#87CEEB
    style NP3 fill:#FF6B6B
    style ING3 fill:#FFA500
    style WL2 fill:#FF6B6B
    style IST2 fill:#FFA500
    style REPORT fill:#98FB98
```

## Cluster-Wide Security Analysis

```mermaid
graph TD
    CLUSTER["Cluster-Wide Analysis"]
    
    CLUSTER --> MTLS["mTLS Check"]
    MTLS --> PA["PeerAuthentication exists?"]
    PA -->|No| PA1["🔴 HIGH RISK:<br/>mTLS not enforced"]
    PA -->|Yes| PA2["Check mode: STRICT?"]
    PA2 -->|Permissive| PA3["🟠 MEDIUM RISK:<br/>mTLS permissive"]
    PA2 -->|STRICT| PA4["✅ mTLS enforced"]
    
    CLUSTER --> AUTHZ["AuthorizationPolicy Check"]
    AUTHZ --> AP["AuthorizationPolicy exists?"]
    AP -->|No| AP1["🟠 MEDIUM RISK:<br/>No access control"]
    AP -->|Yes| AP2["✅ AuthZ OK"]
    
    CLUSTER --> RBAC["RBAC Check"]
    RBAC --> CRB["ClusterRoleBindings<br/>with cluster-admin?"]
    CRB -->|Yes| CRB1["🔴 HIGH RISK:<br/>Over-privileged RBAC"]
    CRB -->|No| CRB2["✅ RBAC OK"]
    
    PA1 --> SUGG["Cluster Recommendations"]
    PA3 --> SUGG
    AP1 --> SUGG
    CRB1 --> SUGG
    SUGG --> SUMMARY["Final Report:<br/>Resource Inventory +<br/>Cluster Findings"]
    
    style CLUSTER fill:#FFE4B5
    style PA1 fill:#FF6B6B
    style PA3 fill:#FFA500
    style AP1 fill:#FFA500
    style CRB1 fill:#FF6B6B
    style SUMMARY fill:#98FB98
```

## Query Count Tracking

```mermaid
graph TD
    TOTAL["Total Queries = 268"]
    
    NS["Namespace Queries"]
    NS --> NS_CALC["22 namespaces ×<br/>12 resource types<br/>= 264 queries"]
    
    CW["Cluster-Wide Queries"]
    CW --> CW_CALC["4 resource types<br/>= 4 queries"]
    
    NS_CALC --> TOTAL
    CW_CALC --> TOTAL
    
    TOTAL --> SUCCESS["✅ Expected = Actual<br/>268 = 268<br/>All queries executed"]
    
    style TOTAL fill:#90EE90
    style SUCCESS fill:#98FB98
```

## Error Handling

```mermaid
graph TD
    QUERY["Execute MCP Query"]
    
    QUERY -->|Success| SUCCESS["Parse JSON<br/>Extract items<br/>Count resources"]
    
    QUERY -->|CRD Not Found| ERROR["MCP Error<br/>e.g., 'virtualservices'<br/>not installed"]
    
    ERROR --> HANDLE["✅ Error Handled:<br/>- Still counts as query attempt<br/>- Logged but doesn't fail<br/>- Continues to next resource"]
    
    QUERY -->|MCP Connection Error| ERROR2["Connection Error"]
    ERROR2 --> HANDLE2["❌ Audit fails<br/>Check MCP server"]
    
    SUCCESS --> CONTINUE["Continue to<br/>next namespace/resource"]
    HANDLE --> CONTINUE
    
    style SUCCESS fill:#90EE90
    style ERROR fill:#FFD700
    style HANDLE fill:#FFD700
    style HANDLE2 fill:#FF6B6B
    style CONTINUE fill:#B0E0E6
```

## Resource Types Queried

```
Per-Namespace (12 types):
├── Workloads
│   ├── pods
│   ├── deployments
│   ├── daemonsets
│   └── statefulsets
├── Security
│   ├── rolebindings
│   └── networkpolicies
├── Networking
│   ├── services
│   └── ingresses
├── Istio (if installed)
│   ├── virtualservices
│   ├── destinationrules
│   └── gateways
└── Config
    └── configmaps

Cluster-Wide (4 types):
├── clusterroles
├── clusterrolebindings
├── peerauthentication
└── authorizationpolicy
```

## Output Structure

```
📊 COMPREHENSIVE SECURITY AUDIT
│
├── 📦 NAMESPACE: default
│   ├── Resource Table (counts & status)
│   ├── Resource Details (pods, deployments, etc.)
│   ├── 🔒 SECURITY FINDINGS (per namespace)
│   │   ├── 🔴 HIGH RISK (e.g., no NetworkPolicies)
│   │   ├── 🟠 MEDIUM RISK (e.g., missing TLS)
│   │   └── 💡 RECOMMENDATIONS (e.g., add default-deny policies)
│   └── ---
│
├── 📦 NAMESPACE: kube-system
│   └── (same structure as above)
│
├── ... (20 more namespaces)
│
├── 🔒 CLUSTER-WIDE SECURITY ASSESSMENT
│   ├── 🔴 HIGH RISK (e.g., no mTLS)
│   ├── 🟠 MEDIUM RISK (e.g., no AuthorizationPolicy)
│   └── 💡 RECOMMENDATIONS
│
└── SUMMARY
    ├── Namespaces found: 22
    ├── Expected queries: 268
    ├── Actual queries: 268
    └── ✅ SUCCESS!
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Stage 1** | LLM-driven namespace discovery via MCP |
| **Stage 2** | Direct MCP queries for all resources |
| **Per-Namespace** | Individual security analysis with findings |
| **Cluster-Wide** | Mesh/cluster-level policy checks |
| **Error Handling** | Missing CRDs logged, audit continues |
| **Resource Coverage** | 12 namespace + 4 cluster resources = 268 total queries |
| **Standards Mapping** | NIST, CIS, NSA/CISA compliance references |
| **Findings** | HIGH/MEDIUM/LOW risk with recommendations |

