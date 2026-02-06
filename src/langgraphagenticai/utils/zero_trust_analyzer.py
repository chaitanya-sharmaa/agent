"""Zero Trust Analysis Module for processing kubectl outputs and generating assessment tables."""

import json
import yaml
import logging
from typing import Dict, List, Any, Tuple
from tabulate import tabulate
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Security risk severity levels."""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1


class ZeroTrustAnalyzer:
    """Analyzes Kubernetes resources for Zero Trust compliance."""
    
    def __init__(self):
        self.resources = {
            "namespaces": [],
            "istio_pods": [],
            "daemonsets": [],
            "peer_authentications": [],
            "authorization_policies": [],
            "network_policies": [],
            "cluster_roles": [],
            "cluster_role_bindings": []
        }
        self.assessment_results = []
        self.risk_findings = []  # Track findings with risk scores
        self.namespace_inventory: Dict[str, Dict[str, int]] = {}
    
    def parse_kubectl_output(self, output: Any) -> Dict[str, Any]:
        """Parse kubectl output from YAML/JSON format."""
        normalized_output: Any = output

        # MCP tools may return a list of content blocks or dicts; normalize to text
        if isinstance(output, dict) and "items" in output:
            return output
        if isinstance(output, list):
            texts: List[str] = []
            for part in output:
                if isinstance(part, dict) and "text" in part:
                    texts.append(str(part.get("text", "")))
                elif isinstance(part, str):
                    texts.append(part)
            normalized_output = "\n".join([t for t in texts if t])
        elif isinstance(output, dict) and "text" in output:
            normalized_output = output.get("text", "")
        elif isinstance(output, (bytes, bytearray)):
            normalized_output = output.decode("utf-8", errors="ignore")
        elif not isinstance(output, str):
            normalized_output = str(output)

        if isinstance(normalized_output, str) and not normalized_output.strip():
            return {"items": []}

        try:
            # Try parsing as YAML first (kubectl default)
            data = yaml.safe_load(normalized_output)
            if data is None:
                raise ValueError("Empty YAML output")
            return data
        except Exception as yaml_err:
            try:
                # Try JSON as fallback
                data = json.loads(normalized_output)
                if not data:
                    raise ValueError("Empty JSON output")
                return data
            except Exception as json_err:
                snippet = str(normalized_output)[:100]
                logger.error(
                    f"Failed to parse tool output (YAML: {yaml_err}, JSON: {json_err}): {snippet}"
                )
                return {"items": []}
    
    def _get_item_name(self, item: Dict[str, Any]) -> str:
        """Return the name of a resource item handling different output shapes."""
        if not isinstance(item, dict):
            return ""
        # Prefer metadata.name -> name
        return (
            item.get("metadata", {}).get("name")
            or item.get("name")
            or ""
        )

    def _get_item_namespace(self, item: Dict[str, Any]) -> str:
        """Return namespace of a resource item if present."""
        if not isinstance(item, dict):
            return ""
        return (
            item.get("metadata", {}).get("namespace")
            or item.get("namespace")
            or ""
        )

    def _get_item_kind(self, item: Dict[str, Any]) -> str:
        """Return kind of a resource item if present."""
        if not isinstance(item, dict):
            return ""
        return (
            item.get("kind")
            or item.get("metadata", {}).get("kind")
            or ""
        )

    def _resource_kind_from_type(self, resource_type: str) -> str:
        """Map resourceType to Kubernetes kind name."""
        mapping = {
            "namespaces": "Namespace",
            "pods": "Pod",
            "deployments": "Deployment",
            "daemonsets": "DaemonSet",
            "statefulsets": "StatefulSet",
            "rolebindings": "RoleBinding",
            "networkpolicies": "NetworkPolicy",
            "clusterroles": "ClusterRole",
            "clusterrolebindings": "ClusterRoleBinding",
            "peerauthentication": "PeerAuthentication",
            "authorizationpolicy": "AuthorizationPolicy",
        }
        return mapping.get(str(resource_type).lower(), str(resource_type))

    def _merge_resources(self, key: str, new_items: List[Dict[str, Any]]):
        """Merge new_items into self.resources[key], deduplicating by (name, namespace, kind)."""
        if not isinstance(new_items, list):
            return
        existing = self.resources.get(key, []) or []
        seen = {(self._get_item_name(it), self._get_item_namespace(it), self._get_item_kind(it)) for it in existing if isinstance(it, dict)}
        for it in new_items:
            if not isinstance(it, dict):
                continue
            key_tuple = (self._get_item_name(it), self._get_item_namespace(it), self._get_item_kind(it))
            if key_tuple not in seen:
                existing.append(it)
                seen.add(key_tuple)
        self.resources[key] = existing

    def _ensure_namespace_entry(self, namespace: str) -> None:
        """Ensure a namespace entry exists in the inventory."""
        import re
        # Only track valid Kubernetes namespace names
        if namespace and re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', str(namespace)):
            self.namespace_inventory.setdefault(namespace, {})

    def _track_namespace_resource_item(self, resource_type: str, item: Dict[str, Any]) -> None:
        """Track a resource item against its namespace for per-namespace reporting."""
        import re
        if not isinstance(item, dict):
            return
        namespace = self._get_item_namespace(item) or "cluster-scope"
        # Only track resources in valid Kubernetes namespaces
        if namespace != "cluster-scope" and not re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', str(namespace)):
            return
        entry = self.namespace_inventory.setdefault(namespace, {})
        entry[resource_type] = entry.get(resource_type, 0) + 1

    def process_tool_results(self, tool_results: List[Any]):
        """Process tool results and categorize them robustly across different kubectl outputs."""
        # Keep track of which resource type we're expecting based on order
        resource_order = [
            "namespaces",
            "istio_pods",
            "daemonsets",
            "peer_authentications",
            "authorization_policies",
            "network_policies",
        ]

        for idx, result in enumerate(tool_results):
            if not (isinstance(result, dict) and "output" in result):
                continue
            output = result["output"]
            resource_type = result.get("resource_type") if isinstance(result, dict) else None
            namespace = result.get("namespace") if isinstance(result, dict) else None

            # Fast-path: handle `-o name` outputs without YAML/JSON parsing
            if resource_type and isinstance(output, list):
                texts: List[str] = []
                for part in output:
                    if isinstance(part, dict) and "text" in part:
                        texts.append(str(part.get("text", "")))
                    elif isinstance(part, str):
                        texts.append(part)
                combined = "\n".join([t for t in texts if t]).strip()
                if combined:
                    kind = self._resource_kind_from_type(resource_type)
                    items = []
                    for line in combined.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        name = line.split("/", 1)[-1]
                        items.append(
                            {
                                "kind": kind,
                                "metadata": {
                                    "name": name,
                                    "namespace": namespace or "",
                                },
                            }
                        )
                    parsed = {"items": items}
                else:
                    parsed = {"items": []}
            elif resource_type and isinstance(output, dict) and "text" in output:
                text = str(output.get("text", "")).strip()
                if text:
                    kind = self._resource_kind_from_type(resource_type)
                    items = []
                    for line in text.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        name = line.split("/", 1)[-1]
                        items.append(
                            {
                                "kind": kind,
                                "metadata": {
                                    "name": name,
                                    "namespace": namespace or "",
                                },
                            }
                        )
                    parsed = {"items": items}
                else:
                    parsed = {"items": []}
            else:
                parsed = self.parse_kubectl_output(output)

            # Normalize to a list of items
            items = []
            if isinstance(parsed, dict):
                if parsed.get("items") and isinstance(parsed.get("items"), list):
                    items = parsed.get("items")
                elif parsed.get("kind"):
                    items = [parsed]
            elif isinstance(parsed, list):
                items = parsed

            # Handle plain name lists from `kubectl get -o name`
            if not items:
                resource_type = result.get("resource_type") if isinstance(result, dict) else None
                namespace = result.get("namespace") if isinstance(result, dict) else None
                if isinstance(parsed, str) and resource_type:
                    lines = [ln.strip() for ln in parsed.splitlines() if ln.strip()]
                    kind = self._resource_kind_from_type(resource_type)
                    for line in lines:
                        name = line.split("/")[-1]
                        item = {
                            "kind": kind,
                            "metadata": {
                                "name": name,
                                "namespace": namespace or "",
                            },
                        }
                        items.append(item)

            if not items:
                continue

            # Attach provenance metadata from the tool result (if present) to each item
            src_tool_name = result.get("tool_name") if isinstance(result, dict) else None
            src_tool_call_id = result.get("tool_call_id") if isinstance(result, dict) else None
            for it in items:
                if isinstance(it, dict):
                    md = it.setdefault("metadata", {})
                    # add source fields but do not overwrite existing fields
                    if src_tool_name:
                        md.setdefault("_evidence_source", src_tool_name)
                    if src_tool_call_id:
                        md.setdefault("_evidence_tool_call_id", src_tool_call_id)

            # Track per-namespace inventory for supported resource kinds
            kind_to_resource = {
                "pod": "pods",
                "deployment": "deployments",
                "daemonset": "daemonsets",
                "statefulset": "statefulsets",
                "rolebinding": "rolebindings",
                "networkpolicy": "networkpolicies",
            }
            for it in items:
                if not isinstance(it, dict):
                    continue
                kind = self._get_item_kind(it).lower()
                resource_type = kind_to_resource.get(kind)
                if resource_type:
                    self._track_namespace_resource_item(resource_type, it)

            # Inspect sample to infer type but always scan all items for evidence (e.g., istio pods anywhere)
            kinds = { (it.get("kind") or "").lower() for it in items if isinstance(it, dict) }

            # Namespaces
            if any(k == "namespace" for k in kinds) or all("name" in it and it.get("kind", "").lower() == "namespace" for it in items if isinstance(it, dict)):
                self._merge_resources("namespaces", items)
                for it in items:
                    if isinstance(it, dict):
                        name = self._get_item_name(it)
                        if name:
                            self._ensure_namespace_entry(name)
                continue

            # Pods: mark istio_pods if any item is in istio-system or name contains 'istio'
            if any(k == "pod" for k in kinds) or any("pod" in (it.get("kind", "").lower()) for it in items if isinstance(it, dict)):
                # Find istio-specific pods across namespaces and add them to istio_pods
                istio_like = []
                for it in items:
                    name = self._get_item_name(it)
                    namespace = (it.get("metadata", {}).get("namespace") or it.get("namespace") or "")
                    if "istio" in name.lower() or namespace == "istio-system":
                        istio_like.append(it)
                if istio_like:
                    self._merge_resources("istio_pods", istio_like)
                else:
                    # Keep generic pods available if needed later
                    self._merge_resources("pods", items)
                continue

            # Daemonsets
            if any(k == "daemonset" for k in kinds) or "ztunnel" in str(items).lower():
                self._merge_resources("daemonsets", items)
                continue

            # PeerAuthentication
            if any(k in ("peerauthentication",) for k in kinds) or any("peerauthentication" in (it.get("kind", "").lower()) for it in items if isinstance(it, dict)):
                self._merge_resources("peer_authentications", items)
                continue

            # AuthorizationPolicy
            if any(k in ("authorizationpolicy",) for k in kinds) or any("authorizationpolicy" in (it.get("kind", "").lower()) for it in items if isinstance(it, dict)):
                self._merge_resources("authorization_policies", items)
                continue

            # NetworkPolicy
            if any(k in ("networkpolicy",) for k in kinds) or any("networkpolicy" in (it.get("kind", "").lower()) for it in items if isinstance(it, dict)):
                self._merge_resources("network_policies", items)
                continue

            # ClusterRole
            if any(k in ("clusterrole",) for k in kinds) or any("clusterrole" in (it.get("kind", "").lower()) for it in items if isinstance(it, dict)):
                self._merge_resources("cluster_roles", items)
                continue

            # ClusterRoleBinding
            if any(k in ("clusterrolebinding",) for k in kinds) or any("clusterrolebinding" in (it.get("kind", "").lower()) for it in items if isinstance(it, dict)):
                self._merge_resources("cluster_role_bindings", items)
                continue

            # If unable to categorize, log warning and attempt position-based assignment as last resort
            if idx < len(resource_order):
                resource_key = resource_order[idx]
                self.resources[resource_key] = items
    
    def _is_verified(self, item: Dict[str, Any]) -> bool:
        """Return True if the item has provenance from a tool execution."""
        if not isinstance(item, dict):
            return False
        md = item.get("metadata", {})
        return bool(md.get("_evidence_source") or md.get("_evidence_tool_call_id"))

    def check_istio_installed(self) -> Tuple[str, str]:
        """Check if Istio is installed using verified evidence only.

        We prefer verified evidence (items derived from tool executions). If only unverified
        evidence exists, report that the installation is unverified to avoid hallucination.
        """
        # Pods reported from istio-specific queries or discovered heuristically
        istio_pods = self.resources.get("istio_pods", [])
        # istiod detection (handle nested shapes or top-level name fields)
        istiod_pods = [p for p in istio_pods if "istiod" in self._get_item_name(p).lower() and self._is_verified(p)]

        # Namespaces may indicate istio-system presence (support both metadata.name and top-level name)
        namespaces = self.resources.get("namespaces", [])
        ns_names = { (ns.get("metadata", {}).get("name") or ns.get("name") or "") for ns in namespaces }
        has_istio_ns_verified = any((ns.get("metadata", {}).get("name") or ns.get("name") or "") == "istio-system" and self._is_verified(ns) for ns in namespaces if isinstance(ns, dict))

        # Also check for ztunnel daemonsets (Ambient mode)
        daemonsets = self.resources.get("daemonsets", [])
        ztunnel_ds_verified = [ds for ds in daemonsets if ("ztunnel" in str(ds).lower() or "ztunnel" in self._get_item_name(ds).lower()) and self._is_verified(ds)]

        # Also detect ztunnel pods (may appear as pods in istio-system)
        ztunnel_pods_verified = [p for p in istio_pods if "ztunnel" in self._get_item_name(p).lower() and self._is_verified(p)]

        # Prefer verified ztunnel (Ambient) evidence first, then verified istiod
        if ztunnel_ds_verified or ztunnel_pods_verified:
            if ztunnel_ds_verified:
                return "Yes", "Found ztunnel daemonset (Ambient mode) [verified]"
            return "Yes", f"Found {len(ztunnel_pods_verified)} verified ztunnel pod(s) (Ambient mode)"
        if istiod_pods:
            return "Yes", f"Found {len(istiod_pods)} verified istiod pod(s)"

        # If we have verified istio-related pods (not istiod/ztunnel), report presence
        istio_pods_verified = [p for p in istio_pods if self._is_verified(p)]
        if istio_pods_verified:
            return "Yes", f"Found {len(istio_pods_verified)} verified istio-related pod(s)"

        if has_istio_ns_verified:
            return "Yes", "Found istio-system namespace [verified]"

        # If there is unverified evidence only, indicate it's unverified rather than asserting
        # installation to avoid hallucinations
        # Check for unverified evidence specifically (pods/daemonsets/namespaces present but not verified)
        unverified_ztunnel_ds = [ds for ds in daemonsets if ("ztunnel" in str(ds).lower() or "ztunnel" in self._get_item_name(ds).lower()) and not self._is_verified(ds)]
        # Consider both 'istio_pods' and generic 'pods' for unverified detection
        all_pods = (self.resources.get("istio_pods") or []) + (self.resources.get("pods") or [])
        unverified_ztunnel_pods = [p for p in all_pods if "ztunnel" in self._get_item_name(p).lower() and not self._is_verified(p)]
        unverified_istiod_pods = [p for p in all_pods if "istiod" in self._get_item_name(p).lower() and not self._is_verified(p)]
        unverified_istio_pods_any = [p for p in all_pods if (self._get_item_namespace(p) == "istio-system" or "istio" in self._get_item_name(p).lower()) and not self._is_verified(p)]
        unverified_ns = [ns for ns in namespaces if (ns.get("metadata", {}).get("name") or ns.get("name") or "") == "istio-system" and not self._is_verified(ns)]

        if unverified_ztunnel_ds or unverified_ztunnel_pods or unverified_istiod_pods or unverified_istio_pods_any or unverified_ns:
            # Decide minimal status from unverified evidence (prefer ztunnel -> istiod -> pods -> namespace)
            if unverified_ztunnel_ds:
                return "Yes", "Only unverified ztunnel evidence found (Ambient mode) — please verify with real tool outputs"
            if unverified_ztunnel_pods:
                return "Yes", f"Found {len(unverified_ztunnel_pods)} unverified ztunnel pod(s) (Ambient mode) — please verify with real tool outputs"
            if unverified_istiod_pods:
                return "Yes", "Only unverified istiod pod(s) found — please verify with real tool outputs"
            if unverified_istio_pods_any:
                return "Yes", "Only unverified istio-related pods found; please verify with real tool outputs"
            if unverified_ns:
                return "Yes", "Found istio-system namespace (unverified) — please verify with real tool outputs"

        return "No", "No Istio components found"
    
    def check_istio_mode(self) -> Tuple[str, str]:
        """Check Istio mode (ambient vs sidecar) using verified evidence only.

        This mirrors `check_istio_installed` semantics: prefer verified evidence and avoid
        declaring a mode if only unverified evidence exists.
        """
        daemonsets = self.resources.get("daemonsets", [])
        
        # Check for verified ztunnel daemonsets
        ztunnel_ds_verified = [ds for ds in daemonsets if ("ztunnel" in str(ds).lower() or "ztunnel" in self._get_item_name(ds).lower()) and self._is_verified(ds)]
        if ztunnel_ds_verified:
            return "Ambient", "ztunnel daemonset found (Ambient mode) [verified]"

        # Check for verified ztunnel pods
        istio_pods = self.resources.get("istio_pods", [])
        ztunnel_pods_verified = [p for p in istio_pods if "ztunnel" in self._get_item_name(p).lower() and self._is_verified(p)]
        if ztunnel_pods_verified:
            return "Ambient", f"Found {len(ztunnel_pods_verified)} verified ztunnel pod(s) (Ambient mode)"

        # Check for verified pods in istio-system for sidecar
        istio_pods_verified = [p for p in istio_pods if self._is_verified(p)]
        if istio_pods_verified:
            return "Sidecar", f"Found {len(istio_pods_verified)} verified pod(s) in istio-system (likely sidecar mode)"

        # If only unverified evidence exists, indicate unknown rather than assume
        unverified_exists = any([
            any("ztunnel" in self._get_item_name(p).lower() for p in istio_pods if not self._is_verified(p)),
            any("ztunnel" in str(ds).lower() or "ztunnel" in self._get_item_name(ds).lower() for ds in daemonsets if not self._is_verified(ds)),
            any(self._get_item_namespace(p) == "istio-system" and not self._is_verified(p) for p in istio_pods)
        ])
        if unverified_exists:
            # Prefer Ambient if unverified ztunnel evidence exists, else Sidecar if unverified pods exist
            if any("ztunnel" in self._get_item_name(ds).lower() or "ztunnel" in str(ds).lower() for ds in daemonsets if not self._is_verified(ds)):
                return "Ambient", "Only unverified ztunnel evidence found (Ambient mode, unverified) — please verify with tool outputs"
            if any("ztunnel" in self._get_item_name(p).lower() for p in istio_pods if not self._is_verified(p)):
                return "Ambient", "Only unverified ztunnel pod evidence found (Ambient mode, unverified) — please verify with tool outputs"
            if any(self._get_item_namespace(p) == "istio-system" and not self._is_verified(p) for p in istio_pods):
                return "Sidecar", "Only unverified pods found in istio-system (likely sidecar mode, unverified) — please verify with tool outputs"

        return "None/Default", "No specific Istio mode detected"    
    def check_strict_mtls(self) -> Tuple[str, str]:
        """Check for strict mTLS enforcement."""
        peer_auths = self.resources.get("peer_authentications", [])
        strict_mtls = []
        
        for pa in peer_auths:
            spec = pa.get("spec", {})
            if spec.get("mtls", {}).get("mode") == "STRICT":
                ns = pa.get("metadata", {}).get("namespace", "cluster-wide")
                strict_mtls.append(ns)
        
        if strict_mtls:
            return "Yes", f"Strict mTLS in: {', '.join(strict_mtls)}"
        return "No", "No strict mTLS PeerAuthentication found"
    
    def check_default_deny_authz(self) -> Tuple[str, str]:
        """Check for default-deny AuthorizationPolicy."""
        authz_policies = self.resources.get("authorization_policies", [])
        deny_policies = []
        
        for ap in authz_policies:
            spec = ap.get("spec", {})
            if spec.get("action") == "DENY":
                ns = ap.get("metadata", {}).get("namespace", "cluster-wide")
                deny_policies.append(ns)
        
        if deny_policies:
            return "Yes", f"Default-deny in: {', '.join(deny_policies)}"
        return "No", "No default-deny AuthorizationPolicy found"
    
    def check_allow_authz(self) -> Tuple[str, str]:
        """Check for allow-only AuthorizationPolicy."""
        authz_policies = self.resources.get("authorization_policies", [])
        allow_policies = []
        
        for ap in authz_policies:
            spec = ap.get("spec", {})
            if spec.get("action") == "ALLOW":
                ns = ap.get("metadata", {}).get("namespace", "cluster-wide")
                allow_policies.append(ns)
        
        if allow_policies:
            return "Yes", f"Allow policies in: {', '.join(allow_policies)}"
        return "No", "No explicit ALLOW AuthorizationPolicy found"
    
    def check_network_policy_deny(self) -> Tuple[str, str]:
        """Check for default-deny NetworkPolicy."""
        net_policies = self.resources.get("network_policies", [])
        deny_all = []

        for np in net_policies:
            spec = np.get("spec", {})
            # Check if it's a deny-all policy (empty ingress/egress)
            if not spec.get("ingress") or not spec.get("egress"):
                ns = np.get("metadata", {}).get("namespace", "")
                if ns:
                    deny_all.append(ns)

        if deny_all:
            return "Yes", f"Default-deny NetworkPolicy in: {', '.join(sorted(set(deny_all)))}"
        return "No", "No default-deny NetworkPolicy found"

    def check_network_policies_coverage(self) -> Tuple[str, str]:
        """Check NetworkPolicy coverage across namespaces."""
        namespaces = self.resources.get("namespaces", [])
        net_policies = self.resources.get("network_policies", [])

        # Normalize namespace names from different shapes
        ns_names = { (ns.get("metadata", {}).get("name") or ns.get("name") or "") for ns in namespaces }
        # Filter out empty or falsy namespace values
        ns_names = {n for n in ns_names if n}

        np_namespaces = { (np.get("metadata", {}).get("namespace") or np.get("namespace") or "") for np in net_policies }
        np_namespaces = {n for n in np_namespaces if n}

        coverage = (len(np_namespaces) / len(ns_names) * 100) if ns_names else 0

        if coverage >= 80:
            return "Yes", f"{len(np_namespaces)}/{len(ns_names)} namespaces have NetworkPolicies ({coverage:.0f}%)"
        elif coverage > 0:
            return "Partial", f"{len(np_namespaces)}/{len(ns_names)} namespaces have NetworkPolicies ({coverage:.0f}%)"
        return "No", "No NetworkPolicies found in any namespace"    
    def _evidence_summary(self) -> str:
        """Return a short evidence summary string listing key found resources."""
        import re
        
        # Get valid namespace names
        def is_valid_ns(name: str) -> bool:
            return bool(re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', str(name)))
        
        ns = { (n.get("metadata", {}).get("name") or n.get("name") or "") for n in (self.resources.get("namespaces") or []) }
        ns = sorted([n for n in ns if is_valid_ns(n)])

        def _format_with_source(item):
            name = self._get_item_name(item)
            ns_name = self._get_item_namespace(item)
            src = (item.get("metadata", {}).get("_evidence_source") or "").strip()
            tcid = (item.get("metadata", {}).get("_evidence_tool_call_id") or "").strip()
            base = name + (f" ({ns_name})" if ns_name else "")
            if src or tcid:
                return f"{base} [{src}:{tcid}]"
            return f"{base} [unverified]"

        istio_pods = [_format_with_source(p) for p in (self.resources.get("istio_pods") or [])]
        istiod_pods = [name for name in istio_pods if "istiod" in name.lower()]
        ztunnel_ds = []
        for ds in (self.resources.get("daemonsets") or []):
            if "ztunnel" in str(ds).lower() or "ztunnel" in self._get_item_name(ds).lower():
                # Format daemonset name and source
                name = self._get_item_name(ds)
                src = (ds.get("metadata", {}).get("_evidence_source") or "").strip() if isinstance(ds, dict) else ""
                tcid = (ds.get("metadata", {}).get("_evidence_tool_call_id") or "").strip() if isinstance(ds, dict) else ""
                if src or tcid:
                    ztunnel_ds.append(f"{name} [{src}:{tcid}]")
                else:
                    ztunnel_ds.append(f"{name} [unverified]")

        peer_auth_ns = [ (pa.get("metadata", {}).get("namespace") or "cluster-wide") for pa in (self.resources.get("peer_authentications") or []) ]
        netpol_ns = sorted({ (np.get("metadata", {}).get("namespace") or np.get("namespace") or "") for np in (self.resources.get("network_policies") or []) if (np.get("metadata", {}).get("namespace") or np.get("namespace")) })
        # Filter netpol_ns to only valid namespace names
        netpol_ns = [n for n in netpol_ns if is_valid_ns(n)]

        lines = []
        lines.append(f"✅ Namespaces discovered: {len(ns)} total")
        if ns:
            lines.append(f"   Sample: {', '.join(ns[:5])}" + (f" ... and {len(ns) - 5} more" if len(ns) > 5 else ""))
        lines.append(f"🔍 Istio components: {len(istio_pods)} pods found" if istio_pods else "🔍 Istio components: none detected")
        lines.append(f"📊 Istiod instances: {len(istiod_pods)} found" if istiod_pods else "📊 Istiod instances: none")
        lines.append(f"🚀 ztunnel daemonsets: {len(ztunnel_ds)} found" if ztunnel_ds else "🚀 ztunnel daemonsets: none")
        lines.append(f"🔐 PeerAuthentication policies: {len(set(peer_auth_ns))} namespaces" if peer_auth_ns and peer_auth_ns != ["cluster-wide"] else "🔐 PeerAuthentication policies: none")
        lines.append(f"🛡️  NetworkPolicies: {len(netpol_ns)} namespaces have policies" if netpol_ns else "🛡️  NetworkPolicies: none configured")
        if netpol_ns:
            lines.append(f"   Protected: {', '.join(netpol_ns)}")

        return "\n".join(lines)

    def _score_finding(self, check_name: str, status: str) -> Dict[str, Any]:
        """
        Score a security finding and assign risk level.
        
        Args:
            check_name: Name of the security check
            status: "Yes", "No", "Partial", etc.
            
        Returns:
            Dict with finding details, risk score, and remediation info
        """
        # Risk scoring matrix: check_name -> (passed_status -> risk_level)
        risk_matrix = {
            "Istio installed": {
                "Yes": RiskLevel.INFO,
                "No": RiskLevel.CRITICAL,
            },
            "Istio mode/profile": {
                "Ambient": RiskLevel.INFO,
                "Sidecar": RiskLevel.INFO,
                "None/Default": RiskLevel.CRITICAL,
            },
            "Strict mTLS enforced": {
                "Yes": RiskLevel.INFO,
                "No": RiskLevel.CRITICAL,
            },
            "Default-deny AuthorizationPolicy": {
                "Yes": RiskLevel.INFO,
                "No": RiskLevel.HIGH,
                "Partial": RiskLevel.MEDIUM,
            },
            "Allow-only AuthorizationPolicy defined": {
                "Yes": RiskLevel.INFO,
                "No": RiskLevel.HIGH,
                "Partial": RiskLevel.MEDIUM,
            },
            "Kubernetes NetworkPolicy default-deny exists": {
                "Yes": RiskLevel.INFO,
                "No": RiskLevel.HIGH,
            },
            "NetworkPolicies present in all namespaces": {
                "Yes": RiskLevel.INFO,
                "Partial": RiskLevel.MEDIUM,
                "No": RiskLevel.HIGH,
            },
        }
        
        # Get risk level
        check_matrix = risk_matrix.get(check_name, {})
        risk_level = check_matrix.get(status, RiskLevel.MEDIUM)
        
        finding = {
            "check": check_name,
            "status": status,
            "risk_level": risk_level.name,
            "risk_score": risk_level.value,
            "finding_type": self._get_finding_type(check_name, status),
        }
        
        return finding
    
    def _get_finding_type(self, check_name: str, status: str) -> str:
        """Map check results to finding types for remediation."""
        if "Istio installed" in check_name and status == "No":
            return "no_istio"
        elif "Strict mTLS" in check_name and status == "No":
            return "no_strict_mtls"
        elif "AuthorizationPolicy" in check_name and status == "No":
            return "no_authz_policy"
        elif "NetworkPolicy" in check_name and "default-deny" in check_name and status == "No":
            return "no_default_deny_network"
        elif "NetworkPolicy" in check_name and status in ("No", "Partial"):
            return "no_network_policy"
        return "unknown"
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """
        Generate a risk summary from all findings.
        
        Returns:
            Dict with total risk score, critical findings count, and summary by severity
        """
        if not self.risk_findings:
            return {
                "total_risk_score": 0,
                "risk_rating": "PASS",
                "critical_count": 0,
                "high_count": 0,
                "medium_count": 0,
                "low_count": 0,
                "findings": []
            }
        
        total_score = sum(f.get("risk_score", 0) for f in self.risk_findings)
        max_possible = 5 * len(self.risk_findings)
        
        # Determine overall rating
        severity_counts = {
            "CRITICAL": sum(1 for f in self.risk_findings if f.get("risk_level") == "CRITICAL"),
            "HIGH": sum(1 for f in self.risk_findings if f.get("risk_level") == "HIGH"),
            "MEDIUM": sum(1 for f in self.risk_findings if f.get("risk_level") == "MEDIUM"),
            "LOW": sum(1 for f in self.risk_findings if f.get("risk_level") == "LOW"),
        }
        
        if severity_counts["CRITICAL"] > 0:
            risk_rating = "CRITICAL"
        elif severity_counts["HIGH"] > 2:
            risk_rating = "HIGH"
        elif severity_counts["HIGH"] > 0 or severity_counts["MEDIUM"] > 3:
            risk_rating = "MEDIUM"
        elif severity_counts["MEDIUM"] > 0 or severity_counts["LOW"] > 0:
            risk_rating = "LOW"
        else:
            risk_rating = "PASS"
        
        return {
            "total_risk_score": total_score,
            "max_risk_score": max_possible,
            "risk_percentage": (total_score / max_possible * 100) if max_possible > 0 else 0,
            "risk_rating": risk_rating,
            "critical_count": severity_counts["CRITICAL"],
            "high_count": severity_counts["HIGH"],
            "medium_count": severity_counts["MEDIUM"],
            "low_count": severity_counts["LOW"],
            "findings": self.risk_findings
        }

    def _generate_risk_summary_table(self) -> str:
        """Generate a visual risk summary table."""
        summary = self.get_risk_summary()
        
        risk_rating = summary.get("risk_rating", "UNKNOWN")
        risk_emoji = {
            "CRITICAL": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "LOW": "🟢",
            "PASS": "✅"
        }.get(risk_rating, "❓")
        
        summary_data = [
            ["Overall Risk Rating", f"{risk_emoji} {risk_rating}"],
            ["Risk Score", f"{summary.get('total_risk_score', 0)}/{summary.get('max_risk_score', 0)}"],
            ["Risk Percentage", f"{summary.get('risk_percentage', 0):.1f}%"],
            ["CRITICAL Findings", summary.get("critical_count", 0)],
            ["HIGH Findings", summary.get("high_count", 0)],
            ["MEDIUM Findings", summary.get("medium_count", 0)],
            ["LOW Findings", summary.get("low_count", 0)],
        ]
        
        headers = ["Metric", "Value"]
        table = tabulate(summary_data, headers=headers, tablefmt="grid")
        return table

    def _generate_findings_by_severity_table(self) -> str:
        """Generate findings sorted by severity."""
        summary = self.get_risk_summary()
        findings = summary.get("findings", [])
        
        if not findings:
            return "No security findings detected (all checks passed)."
        
        # Sort by risk score descending
        sorted_findings = sorted(findings, key=lambda f: f.get("risk_score", 0), reverse=True)
        
        table_data = []
        for finding in sorted_findings:
            risk_emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢",
                "INFO": "ℹ️"
            }.get(finding.get("risk_level", "UNKNOWN"), "❓")
            
            table_data.append([
                f"{risk_emoji} {finding.get('risk_level', 'UNKNOWN')}",
                finding.get("check", "Unknown"),
                finding.get("status", "Unknown"),
                f"{finding.get('risk_score', 0)}/5"
            ])
        
        headers = ["Severity", "Check", "Status", "Risk Score"]
        table = tabulate(table_data, headers=headers, tablefmt="grid")
        return table

    def _is_valid_namespace_name(self, name: str) -> bool:
        """Check if a string is a valid Kubernetes namespace name."""
        if not isinstance(name, str):
            return False
        # Valid namespace names are alphanumeric, hyphens, lowercase only
        # They should not contain special chars like quotes, braces, colons, etc.
        import re
        # Valid format: lowercase alphanumeric and hyphens, 1-63 chars
        return bool(re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$', name))

    def _generate_namespace_summary_table(self) -> str:
        """Generate a per-namespace resource coverage and risk table."""
        if not self.namespace_inventory:
            return "No namespace inventory available."

        rows = []
        critical_ns = 0
        high_risk_ns = 0
        medium_risk_ns = 0
        secure_ns = 0
        
        # Filter out invalid namespace names (JSON keys, fragments, etc.)
        valid_namespaces = {
            ns: counts 
            for ns, counts in self.namespace_inventory.items() 
            if self._is_valid_namespace_name(ns)
        }
        
        if not valid_namespaces:
            return "No valid namespaces found in inventory."
        
        for namespace in sorted(valid_namespaces.keys()):
            counts = valid_namespaces.get(namespace, {})
            pods = counts.get("pods", 0)
            deployments = counts.get("deployments", 0)
            daemonsets = counts.get("daemonsets", 0)
            statefulsets = counts.get("statefulsets", 0)
            rolebindings = counts.get("rolebindings", 0)
            networkpolicies = counts.get("networkpolicies", 0)
            
            has_workloads = pods + deployments + daemonsets + statefulsets > 0

            # Risk assessment
            risk_level = "✅ SECURE"
            if has_workloads and networkpolicies == 0:
                risk_level = "🔴 CRITICAL"
                critical_ns += 1
            elif not has_workloads and networkpolicies == 0:
                risk_level = "🟠 HIGH"
                high_risk_ns += 1
            elif rolebindings == 0:
                risk_level = "🟡 MEDIUM"
                medium_risk_ns += 1
            else:
                secure_ns += 1

            rows.append(
                [
                    namespace,
                    pods,
                    deployments,
                    daemonsets,
                    statefulsets,
                    rolebindings,
                    networkpolicies,
                    risk_level,
                ]
            )

        headers = [
            "Namespace",
            "Pods",
            "Deploy",
            "DS",
            "SS",
            "RoleBindings",
            "NetPolicies",
            "Security Status",
        ]
        table = tabulate(rows, headers=headers, tablefmt="grid")
        
        # Add summary stats
        total_ns = len(rows)
        summary = f"\n📊 Namespace Summary: {total_ns} total | 🔴 {critical_ns} critical | 🟠 {high_risk_ns} high risk | 🟡 {medium_risk_ns} medium | ✅ {secure_ns} secure\n"
        
        return summary + table

    def generate_assessment_table(self, elapsed_time: float = None) -> str:
        """Generate the final Zero Trust assessment table with risk scoring and evidence."""
        # Run all checks
        checks = [
            ("Istio installed", self.check_istio_installed()),
            ("Istio mode/profile", self.check_istio_mode()),
            ("Strict mTLS enforced", self.check_strict_mtls()),
            ("Default-deny AuthorizationPolicy", self.check_default_deny_authz()),
            ("Allow-only AuthorizationPolicy defined", self.check_allow_authz()),
            ("Kubernetes NetworkPolicy default-deny exists", self.check_network_policy_deny()),
            ("NetworkPolicies present in all namespaces", self.check_network_policies_coverage())
        ]
        
        # Score all findings and build table data
        self.risk_findings = []
        table_data = []
        for check_name, (status, details) in checks:
            finding = self._score_finding(check_name, status)
            self.risk_findings.append(finding)
            
            risk_emoji = {
                "CRITICAL": "🔴",
                "HIGH": "🟠",
                "MEDIUM": "🟡",
                "LOW": "🟢",
                "INFO": "ℹ️"
            }.get(finding.get("risk_level", "UNKNOWN"), "❓")
            
            table_data.append([
                check_name,
                status,
                details,
                f"{risk_emoji} {finding.get('risk_level', 'UNKNOWN')}"
            ])
        
        # Generate tables
        headers = ["Check Description", "Status", "Details", "Risk Level"]
        assessment_table = tabulate(table_data, headers=headers, tablefmt="grid")
        
        # Risk summary
        risk_summary_table = self._generate_risk_summary_table()
        findings_by_severity = self._generate_findings_by_severity_table()
        
        # Evidence summary
        evidence = self._evidence_summary()
        evidence_block = f"\n📋 Evidence Summary:\n{evidence}\n"

        namespace_summary = self._generate_namespace_summary_table()
        
        # Execution stats
        exec_stats = ""
        if elapsed_time:
            exec_stats = f"\n⏱️  Execution Time: {elapsed_time:.2f}s\n"
        
        return f"""

╔{'═' * 78}╗
║{'🛡️  ZERO TRUST SECURITY ASSESSMENT REPORT'.center(78)}║
╚{'═' * 78}╝
{exec_stats}
{'─' * 80}
🎯 OVERALL RISK SUMMARY
{'─' * 80}

{risk_summary_table}

{'─' * 80}
📋 DETAILED ASSESSMENT CHECKS
{'─' * 80}

{assessment_table}

{'─' * 80}
⚠️  FINDINGS BY SEVERITY
{'─' * 80}

{findings_by_severity}

{'─' * 80}
🔍 NAMESPACE-LEVEL ANALYSIS
{'─' * 80}

{namespace_summary}

{'─' * 80}
{evidence_block}
{'═' * 80}
"""

    
    def analyze_and_generate_report(self, tool_results: List[Any], elapsed_time: float = None) -> str:
        """Main method to analyze tool results and generate report."""
        self.process_tool_results(tool_results)
        return self.generate_assessment_table(elapsed_time)
