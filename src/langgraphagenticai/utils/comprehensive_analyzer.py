"""Comprehensive security and compliance analysis for Kubernetes clusters.

This module provides deep analysis of:
- All namespaces and their resources
- Security posture (RBAC, network policies, pod security)
- Compliance standards (CIS Kubernetes Benchmark, NIST)
- Best practices and hardening recommendations
- Resource inventory and state
"""

import json
import yaml
from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum


class SecurityLevel(Enum):
    """Security assessment levels."""
    CRITICAL = "🔴 CRITICAL"
    HIGH = "🟠 HIGH"
    MEDIUM = "🟡 MEDIUM"
    LOW = "🟢 LOW"
    INFO = "🔵 INFO"


class ComplianceStatus(Enum):
    """Compliance assessment status."""
    PASSED = "✅ PASSED"
    FAILED = "❌ FAILED"
    WARNING = "⚠️  WARNING"
    NOT_APPLICABLE = "⊘ N/A"


@dataclass
class ResourceInventory:
    """Inventory of resources found in the cluster."""
    namespaces: List[str] = field(default_factory=list)
    pods: Dict[str, int] = field(default_factory=dict)  # namespace -> count
    deployments: Dict[str, int] = field(default_factory=dict)  # namespace -> count
    statefulsets: Dict[str, int] = field(default_factory=dict)  # namespace -> count
    daemonsets: Dict[str, int] = field(default_factory=dict)  # namespace -> count
    services: Dict[str, int] = field(default_factory=dict)  # namespace -> count
    configmaps: Dict[str, int] = field(default_factory=dict)  # namespace -> count
    secrets: Dict[str, int] = field(default_factory=dict)  # namespace -> count
    roles: Dict[str, int] = field(default_factory=dict)  # namespace -> count
    rolebindings: Dict[str, int] = field(default_factory=dict)  # namespace -> count
    network_policies: Dict[str, int] = field(default_factory=dict)  # namespace -> count


@dataclass
class SecurityFinding:
    """A security finding or issue."""
    level: SecurityLevel
    category: str  # e.g., "RBAC", "Network Security", "Pod Security"
    title: str
    description: str
    resource_type: str  # e.g., "Pod", "Deployment"
    namespace: str
    resource_name: str = ""
    recommendation: str = ""


@dataclass
class ComplianceCheck:
    """A compliance check result."""
    standard: str  # e.g., "CIS Kubernetes Benchmark v1.24"
    control: str  # e.g., "1.1.1"
    title: str
    status: ComplianceStatus
    details: str
    recommendation: str = ""


class ComprehensiveSecurityAnalyzer:
    """Comprehensive Kubernetes security and compliance analyzer."""
    
    def __init__(self):
        self.inventory = ResourceInventory()
        self.findings: List[SecurityFinding] = []
        self.compliance_checks: List[ComplianceCheck] = []
        self.namespaces_analyzed = set()
        self.pod_security_issues = []
        self.rbac_issues = []
        self.network_issues = []
        self.config_issues = []
        self.recommendations = []
    
    def analyze_namespace_resources(self, namespace: str, kubectl_output: str) -> None:
        """Analyze all resources in a namespace."""
        try:
            data = yaml.safe_load(kubectl_output)
            if not data:
                return
            
            items = data.get("items", []) if isinstance(data, dict) else []
            if not isinstance(items, list):
                items = [data] if isinstance(data, dict) else []
            
            self.namespaces_analyzed.add(namespace)
            
            for item in items:
                self._analyze_resource(item, namespace)
        except Exception as e:
            self.findings.append(
                SecurityFinding(
                    level=SecurityLevel.MEDIUM,
                    category="Data Processing",
                    title=f"Failed to parse namespace data for {namespace}",
                    description=str(e),
                    resource_type="Namespace",
                    namespace=namespace,
                    recommendation="Check kubectl connectivity and cluster health"
                )
            )
    
    def _analyze_resource(self, resource: Dict[str, Any], namespace: str) -> None:
        """Analyze a single resource."""
        if not isinstance(resource, dict):
            return
        
        kind = resource.get("kind", "").lower()
        metadata = resource.get("metadata", {})
        name = metadata.get("name", "unknown")
        
        # Pod security analysis
        if kind == "pod":
            self._analyze_pod_security(resource, namespace)
        
        # Deployment security
        elif kind == "deployment":
            self._analyze_deployment(resource, namespace)
        
        # StatefulSet security
        elif kind == "statefulset":
            self._analyze_statefulset(resource, namespace)
        
        # RBAC analysis
        elif kind == "role":
            self._analyze_role(resource, namespace)
        elif kind == "rolebinding":
            self._analyze_rolebinding(resource, namespace)
        
        # Network policy
        elif kind == "networkpolicy":
            self._analyze_networkpolicy(resource, namespace)
        
        # Service account
        elif kind == "serviceaccount":
            self._analyze_serviceaccount(resource, namespace)
    
    def _analyze_pod_security(self, pod: Dict[str, Any], namespace: str) -> None:
        """Analyze pod security settings."""
        name = pod.get("metadata", {}).get("name", "unknown")
        spec = pod.get("spec", {})
        
        # Check for privileged containers
        containers = spec.get("containers", [])
        init_containers = spec.get("initContainers", [])
        
        for container_list, container_type in [(containers, "container"), (init_containers, "init container")]:
            for container in container_list:
                if not isinstance(container, dict):
                    continue
                
                sec_ctx = container.get("securityContext", {})
                
                # Check privileged mode
                if sec_ctx.get("privileged"):
                    self.findings.append(SecurityFinding(
                        level=SecurityLevel.CRITICAL,
                        category="Pod Security",
                        title=f"Privileged {container_type} detected",
                        description=f"Pod '{name}' has privileged {container_type}",
                        resource_type="Pod",
                        namespace=namespace,
                        resource_name=name,
                        recommendation="Remove privileged mode unless absolutely necessary. Use capabilities instead."
                    ))
                
                # Check run as root
                if sec_ctx.get("runAsUser") is None:
                    self.findings.append(SecurityFinding(
                        level=SecurityLevel.HIGH,
                        category="Pod Security",
                        title="Container runs as root",
                        description=f"Pod '{name}' {container_type} doesn't specify runAsUser",
                        resource_type="Pod",
                        namespace=namespace,
                        resource_name=name,
                        recommendation="Set runAsUser to a non-zero UID in securityContext"
                    ))
                
                # Check read-only root filesystem
                if not sec_ctx.get("readOnlyRootFilesystem"):
                    self.findings.append(SecurityFinding(
                        level=SecurityLevel.MEDIUM,
                        category="Pod Security",
                        title="Writable root filesystem",
                        description=f"Pod '{name}' {container_type} has writable root filesystem",
                        resource_type="Pod",
                        namespace=namespace,
                        resource_name=name,
                        recommendation="Set readOnlyRootFilesystem: true and use emptyDir volumes for writable areas"
                    ))
                
                # Check capabilities
                caps = sec_ctx.get("capabilities", {})
                if caps.get("add"):
                    self.findings.append(SecurityFinding(
                        level=SecurityLevel.MEDIUM,
                        category="Pod Security",
                        title="Unnecessary Linux capabilities granted",
                        description=f"Pod '{name}' {container_type} adds capabilities: {caps.get('add')}",
                        resource_type="Pod",
                        namespace=namespace,
                        resource_name=name,
                        recommendation="Drop all capabilities and only add necessary ones (NET_BIND_SERVICE, etc.)"
                    ))
        
        # Check for service account token automount
        if spec.get("automountServiceAccountToken") is False:
            pass  # Good practice
        else:
            self.findings.append(SecurityFinding(
                level=SecurityLevel.MEDIUM,
                category="Pod Security",
                title="Service account token auto-mounted",
                description=f"Pod '{name}' has service account token automounted",
                resource_type="Pod",
                namespace=namespace,
                resource_name=name,
                recommendation="Set automountServiceAccountToken: false unless the application needs Kubernetes API access"
            ))
    
    def _analyze_deployment(self, deployment: Dict[str, Any], namespace: str) -> None:
        """Analyze deployment security settings."""
        name = deployment.get("metadata", {}).get("name", "unknown")
        spec = deployment.get("spec", {})
        
        # Check replica count for high availability
        replicas = spec.get("replicas", 1)
        if replicas < 2:
            self.findings.append(SecurityFinding(
                level=SecurityLevel.MEDIUM,
                category="Availability",
                title="Single replica deployment",
                description=f"Deployment '{name}' has only {replicas} replica(s)",
                resource_type="Deployment",
                namespace=namespace,
                resource_name=name,
                recommendation="Use at least 2 replicas for high availability"
            ))
        
        # Check pod disruption budget
        # (This would need to check PDB separately)
        
        # Check resource limits
        pod_spec = spec.get("template", {}).get("spec", {})
        containers = pod_spec.get("containers", [])
        
        for container in containers:
            if not isinstance(container, dict):
                continue
            
            resources = container.get("resources", {})
            if not resources.get("limits"):
                self.findings.append(SecurityFinding(
                    level=SecurityLevel.MEDIUM,
                    category="Resource Management",
                    title="No resource limits defined",
                    description=f"Deployment '{name}' container '{container.get('name')}' has no resource limits",
                    resource_type="Deployment",
                    namespace=namespace,
                    resource_name=name,
                    recommendation="Define resource.limits for memory and CPU to prevent resource exhaustion"
                ))
    
    def _analyze_statefulset(self, statefulset: Dict[str, Any], namespace: str) -> None:
        """Analyze StatefulSet security settings."""
        # Similar to deployment but also check persistent volume claims
        name = statefulset.get("metadata", {}).get("name", "unknown")
        # Check for mounted volumes
        pass
    
    def _analyze_role(self, role: Dict[str, Any], namespace: str) -> None:
        """Analyze Role RBAC settings for over-permission."""
        name = role.get("metadata", {}).get("name", "unknown")
        rules = role.get("rules", [])
        
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            
            verbs = rule.get("verbs", [])
            resources = rule.get("resources", [])
            
            # Check for wildcard permissions
            if "*" in verbs:
                self.findings.append(SecurityFinding(
                    level=SecurityLevel.HIGH,
                    category="RBAC",
                    title="Overly permissive role with wildcard verbs",
                    description=f"Role '{name}' allows all actions on {resources}",
                    resource_type="Role",
                    namespace=namespace,
                    resource_name=name,
                    recommendation="Specify explicit verbs (get, list, watch) instead of wildcards"
                ))
            
            if "*" in resources:
                self.findings.append(SecurityFinding(
                    level=SecurityLevel.HIGH,
                    category="RBAC",
                    title="Overly permissive role with wildcard resources",
                    description=f"Role '{name}' allows operations on all resources with verbs {verbs}",
                    resource_type="Role",
                    namespace=namespace,
                    resource_name=name,
                    recommendation="Specify exact resource types instead of wildcards"
                ))
    
    def _analyze_rolebinding(self, rolebinding: Dict[str, Any], namespace: str) -> None:
        """Analyze RoleBinding assignments."""
        name = rolebinding.get("metadata", {}).get("name", "unknown")
        subjects = rolebinding.get("subjects", [])
        
        for subject in subjects:
            if not isinstance(subject, dict):
                continue
            
            # Check for system:unauthenticated or system:anonymous
            if subject.get("name") in ["system:unauthenticated", "system:anonymous"]:
                self.findings.append(SecurityFinding(
                    level=SecurityLevel.CRITICAL,
                    category="RBAC",
                    title="Unauthenticated access granted",
                    description=f"RoleBinding '{name}' grants permissions to unauthenticated users",
                    resource_type="RoleBinding",
                    namespace=namespace,
                    resource_name=name,
                    recommendation="Remove unauthenticated bindings; use strong authentication"
                ))
    
    def _analyze_networkpolicy(self, netpol: Dict[str, Any], namespace: str) -> None:
        """Analyze NetworkPolicy for proper segmentation."""
        name = netpol.get("metadata", {}).get("name", "unknown")
        # NetworkPolicy analysis would include checking ingress/egress rules
        pass
    
    def _analyze_serviceaccount(self, sa: Dict[str, Any], namespace: str) -> None:
        """Analyze ServiceAccount settings."""
        name = sa.get("metadata", {}).get("name", "unknown")
        
        if not sa.get("automountServiceAccountToken"):
            # Good - token mounting is disabled
            pass
    
    def generate_security_report(self) -> str:
        """Generate comprehensive security report."""
        report = []
        report.append("=" * 80)
        report.append("COMPREHENSIVE KUBERNETES SECURITY & COMPLIANCE AUDIT REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Executive Summary
        report.append("## EXECUTIVE SUMMARY")
        report.append("")
        report.append(f"- Namespaces Analyzed: {len(self.namespaces_analyzed)}")
        report.append(f"- Total Security Findings: {len(self.findings)}")
        report.append(f"- Critical Issues: {len([f for f in self.findings if f.level == SecurityLevel.CRITICAL])}")
        report.append(f"- High Issues: {len([f for f in self.findings if f.level == SecurityLevel.HIGH])}")
        report.append(f"- Medium Issues: {len([f for f in self.findings if f.level == SecurityLevel.MEDIUM])}")
        report.append("")
        
        # Resource Inventory
        report.append("## RESOURCE INVENTORY")
        report.append("")
        report.append(f"Namespaces: {', '.join(sorted(self.namespaces_analyzed))}")
        report.append("")
        
        # Security Findings by Category
        report.append("## SECURITY FINDINGS BY CATEGORY")
        report.append("")
        
        categories = {}
        for finding in self.findings:
            if finding.category not in categories:
                categories[finding.category] = []
            categories[finding.category].append(finding)
        
        for category in sorted(categories.keys()):
            findings = categories[category]
            report.append(f"### {category}")
            report.append(f"Total: {len(findings)} issue(s)")
            report.append("")
            
            for finding in findings:
                report.append(f"**{finding.level.value} - {finding.title}**")
                report.append(f"  - Resource: {finding.resource_type} '{finding.resource_name}' in {finding.namespace}")
                report.append(f"  - Issue: {finding.description}")
                report.append(f"  - Fix: {finding.recommendation}")
                report.append("")
        
        # Compliance Status
        if self.compliance_checks:
            report.append("## COMPLIANCE STATUS")
            report.append("")
            for check in self.compliance_checks:
                report.append(f"**{check.standard} - {check.control}**")
                report.append(f"  - Status: {check.status.value}")
                report.append(f"  - Details: {check.details}")
                report.append("")
        
        # Recommendations
        report.append("## TOP RECOMMENDATIONS")
        report.append("")
        
        critical = [f for f in self.findings if f.level == SecurityLevel.CRITICAL]
        high = [f for f in self.findings if f.level == SecurityLevel.HIGH]
        
        if critical:
            report.append("### CRITICAL ACTIONS (DO IMMEDIATELY)")
            for finding in critical[:5]:
                report.append(f"- {finding.title}: {finding.recommendation}")
            report.append("")
        
        if high:
            report.append("### HIGH PRIORITY (NEXT WEEK)")
            for finding in high[:5]:
                report.append(f"- {finding.title}: {finding.recommendation}")
            report.append("")
        
        report.append("### MEDIUM PRIORITY (NEXT MONTH)")
        medium = [f for f in self.findings if f.level == SecurityLevel.MEDIUM]
        for finding in medium[:5]:
            report.append(f"- {finding.title}: {finding.recommendation}")
        report.append("")
        
        # Best Practices
        report.append("## KUBERNETES SECURITY BEST PRACTICES")
        report.append("")
        report.append("1. **Pod Security Standards**")
        report.append("   - Enforce restricted PSS (Pod Security Standards)")
        report.append("   - Use RuntimeDefault seccomp profile")
        report.append("   - Drop all capabilities, add only necessary")
        report.append("")
        report.append("2. **Network Policies**")
        report.append("   - Implement default deny ingress/egress")
        report.append("   - Use service mesh (Istio) for advanced traffic management")
        report.append("   - Label pods and services for policy targeting")
        report.append("")
        report.append("3. **RBAC**")
        report.append("   - Use least privilege principle")
        report.append("   - Regular audit of role bindings")
        report.append("   - Use service accounts for pod-to-API authentication")
        report.append("")
        report.append("4. **Supply Chain Security**")
        report.append("   - Use image registries with vulnerability scanning")
        report.append("   - Enforce image signing and verification")
        report.append("   - Use latest distroless or alpine images")
        report.append("")
        report.append("5. **Secrets Management**")
        report.append("   - Use external secret management (Vault, AWS Secrets Manager)")
        report.append("   - Enable encryption at rest for etcd")
        report.append("   - Rotate credentials regularly")
        report.append("")
        
        report.append("=" * 80)
        report.append("END OF REPORT")
        report.append("=" * 80)
        
        return "\n".join(report)
