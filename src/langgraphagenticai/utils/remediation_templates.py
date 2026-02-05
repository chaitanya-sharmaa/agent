"""
Remediation Templates - Pre-built YAML templates for common Kubernetes security issues.

Provides ready-to-apply Kubernetes resource definitions for security findings.
"""

from typing import Dict, List, Any, Optional


class RemediationTemplates:
    """Generate remediation templates for security findings."""
    
    @staticmethod
    def get_default_deny_network_policy(namespace: str) -> str:
        """
        Return a default-deny NetworkPolicy template.
        
        Denies all ingress and egress traffic by default, then allows explicit policies.
        
        Args:
            namespace: Target namespace for the policy
            
        Returns:
            YAML string for NetworkPolicy
        """
        return f"""apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes:
  - Ingress
  - Egress
---
# Allow DNS for all pods to resolve services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes:
  - Egress
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
"""

    @staticmethod
    def get_peer_authentication_strict_mtls(namespace: str) -> str:
        """
        Return a PeerAuthentication policy for strict mTLS.
        
        Enforces mutual TLS for all traffic in the namespace.
        
        Args:
            namespace: Target namespace for the policy
            
        Returns:
            YAML string for PeerAuthentication
        """
        return f"""apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: {namespace}
spec:
  mtls:
    mode: STRICT
"""

    @staticmethod
    def get_authorization_policy_default_deny(namespace: str) -> str:
        """
        Return an AuthorizationPolicy for default-deny access.
        
        Denies all traffic by default, requires explicit ALLOW policies.
        
        Args:
            namespace: Target namespace for the policy
            
        Returns:
            YAML string for AuthorizationPolicy
        """
        return f"""apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: default-deny
  namespace: {namespace}
spec:
  action: DENY
  rules:
  - from:
    - source:
        principals: ["*"]
    to:
    - operation:
        methods: ["*"]
"""

    @staticmethod
    def get_authorization_policy_allow_mesh(namespace: str) -> str:
        """
        Return an AuthorizationPolicy allowing mesh-internal traffic.
        
        Allows traffic from any authenticated service account in the mesh.
        
        Args:
            namespace: Target namespace for the policy
            
        Returns:
            YAML string for AuthorizationPolicy
        """
        return f"""apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-mesh
  namespace: {namespace}
spec:
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/*/sa/*"]
    to:
    - operation:
        methods: ["*"]
"""

    @staticmethod
    def get_authorization_policy_allow_specific(
        namespace: str,
        source_namespace: str,
        source_sa: str,
        target_port: int = None
    ) -> str:
        """
        Return an AuthorizationPolicy allowing traffic from specific source.
        
        Args:
            namespace: Target namespace for the policy
            source_namespace: Source namespace (use "*" for any)
            source_sa: Source service account (use "*" for any)
            target_port: Optional target port to restrict to
            
        Returns:
            YAML string for AuthorizationPolicy
        """
        port_section = ""
        if target_port:
            port_section = f"\n    ports:\n    - {target_port}"
        
        return f"""apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-from-{source_namespace}
  namespace: {namespace}
spec:
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/{source_namespace}/sa/{source_sa}"]
    to:
    - operation:
        methods: ["*"]{port_section}
"""

    @staticmethod
    def get_pod_security_policy_restricted() -> str:
        """
        Return a restrictive PodSecurityPolicy template.
        
        NOTE: PodSecurityPolicy is deprecated (removed in K8s 1.25+).
        Prefer PodSecurityStandards (labels on namespaces).
        
        Returns:
            YAML string for PodSecurityPolicy
        """
        return """apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: restricted
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
  - ALL
  volumes:
  - configMap
  - emptyDir
  - projected
  - secret
  - downwardAPI
  - persistentVolumeClaim
  hostNetwork: false
  hostIPC: false
  hostPID: false
  runAsUser:
    rule: MustRunAsNonRoot
  seLinux:
    rule: MustRunAs
    seLinuxOptions:
      level: "s0:c123,c456"
  supplementalGroups:
    rule: MustRunAs
    ranges:
    - min: 100
      max: 65535
  fsGroup:
    rule: MustRunAs
    ranges:
    - min: 100
      max: 65535
  readOnlyRootFilesystem: true
"""

    @staticmethod
    def get_network_policy_allow_specific(
        namespace: str,
        source_pod_label: str,
        source_namespace: str = None,
        target_port: int = None
    ) -> str:
        """
        Return a NetworkPolicy allowing traffic from specific source.
        
        Args:
            namespace: Target namespace for the policy
            source_pod_label: Pod label selector (e.g., "app=frontend")
            source_namespace: Source namespace label (optional)
            target_port: Target port number (optional)
            
        Returns:
            YAML string for NetworkPolicy
        """
        source_ns_section = ""
        if source_namespace:
            source_ns_section = f"""  - podSelector: {{}}
    namespaceSelector:
      matchLabels:
        name: {source_namespace}
"""
        else:
            source_ns_section = f"""  - podSelector:
      matchLabels:
        {source_pod_label.replace('=', ': ')}
"""
        
        port_section = ""
        if target_port:
            port_section = f"""  ports:
  - protocol: TCP
    port: {target_port}
"""
        
        return f"""apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-from-{source_pod_label.replace('=', '-')}
  namespace: {namespace}
spec:
  podSelector: {{}}
  policyTypes:
  - Ingress
  ingress:
{source_ns_section}{port_section}
"""

    @staticmethod
    def get_rbac_restrict_service_account(
        namespace: str,
        service_account: str
    ) -> str:
        """
        Return RBAC templates restricting service account permissions.
        
        Creates a minimalist Role and RoleBinding.
        
        Args:
            namespace: Target namespace
            service_account: Service account name
            
        Returns:
            YAML string with Role and RoleBinding
        """
        return f"""apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: {service_account}-minimal
  namespace: {namespace}
rules:
- apiGroups: [""]
  resources: ["pods", "pods/log"]
  verbs: ["get", "list"]
- apiGroups: [""]
  resources: ["configmaps"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: {service_account}-minimal
  namespace: {namespace}
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: {service_account}-minimal
subjects:
- kind: ServiceAccount
  name: {service_account}
  namespace: {namespace}
"""

    @staticmethod
    def get_pod_security_standards_label(enforce_level: str = "restricted") -> str:
        """
        Return namespace labels for Pod Security Standards (K8s 1.25+).
        
        Modern alternative to deprecated PodSecurityPolicy.
        
        Args:
            enforce_level: "baseline", "restricted", or "privileged"
            
        Returns:
            YAML snippet for namespace labels
        """
        return f"""apiVersion: v1
kind: Namespace
metadata:
  name: my-namespace
  labels:
    pod-security.kubernetes.io/enforce: {enforce_level}
    pod-security.kubernetes.io/audit: {enforce_level}
    pod-security.kubernetes.io/warn: {enforce_level}
"""

    @staticmethod
    def format_finding_with_remediation(
        finding_title: str,
        severity: str,
        description: str,
        remediation_yaml: str
    ) -> str:
        """
        Format a finding with its remediation template.
        
        Args:
            finding_title: Title of the security finding
            severity: "CRITICAL", "HIGH", "MEDIUM", "LOW"
            description: Detailed description
            remediation_yaml: YAML template to apply
            
        Returns:
            Formatted string with finding and remediation
        """
        severity_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢"
        }.get(severity, "⚪")
        
        return f"""{severity_emoji} {severity}: {finding_title}

Description:
{description}

Remediation:
Apply the following Kubernetes resource:

```yaml
{remediation_yaml}
```

Apply with:
kubectl apply -f remediation.yaml
"""


class RemediationEngine:
    """Generate remediation recommendations based on security findings."""
    
    def __init__(self):
        self.templates = RemediationTemplates()
        self.remediation_map = self._build_remediation_map()
    
    def _build_remediation_map(self) -> Dict[str, callable]:
        """Map security findings to remediation template generators."""
        return {
            "no_istio": lambda ns: self.templates.get_peer_authentication_strict_mtls(ns),
            "no_strict_mtls": lambda ns: self.templates.get_peer_authentication_strict_mtls(ns),
            "no_authz_policy": lambda ns: self.templates.get_authorization_policy_default_deny(ns),
            "no_network_policy": lambda ns: self.templates.get_default_deny_network_policy(ns),
            "no_default_deny_authz": lambda ns: self.templates.get_authorization_policy_default_deny(ns),
            "no_default_deny_network": lambda ns: self.templates.get_default_deny_network_policy(ns),
        }
    
    def get_remediation(self, finding_type: str, namespace: str = "default") -> Optional[str]:
        """
        Get remediation template for a specific finding type.
        
        Args:
            finding_type: Type of finding (key from remediation_map)
            namespace: Target namespace (default: "default")
            
        Returns:
            YAML remediation template or None if not found
        """
        generator = self.remediation_map.get(finding_type)
        if generator:
            return generator(namespace)
        return None
    
    def generate_findings_with_remediation(
        self,
        findings: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """
        Generate remediation for a list of security findings.
        
        Args:
            findings: List of finding dicts with 'title', 'severity', 'finding_type', 'namespace'
            
        Returns:
            List of dicts with 'title', 'severity', 'description', 'remediation'
        """
        result = []
        for finding in findings:
            remediation_yaml = self.get_remediation(
                finding.get("finding_type", "unknown"),
                finding.get("namespace", "default")
            )
            
            if remediation_yaml:
                result.append({
                    "title": finding.get("title", "Unknown Finding"),
                    "severity": finding.get("severity", "MEDIUM"),
                    "description": finding.get("description", ""),
                    "remediation": remediation_yaml,
                    "formatted": self.templates.format_finding_with_remediation(
                        finding.get("title", "Unknown"),
                        finding.get("severity", "MEDIUM"),
                        finding.get("description", ""),
                        remediation_yaml
                    )
                })
        
        return result
